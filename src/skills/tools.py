"""Tool registry for the skill runtime.

Skills run as multi-turn tool-calling agents. The runtime exposes six tools
to the model:

* ``read_file(path)`` — read a text file inside the skill folder
* ``run_script(path, stdin=None, timeout=60)`` — execute a script in the
  skill's ``scripts/`` folder under a sandboxed subprocess
* ``write_file(path, content)`` — persist an artifact to the run's
  ``artifacts/`` folder
* ``kg_query(cypher)`` — run a read-only Cypher query against the active
  workspace's Neo4j graph (no-op if Neo4j is not the active backend)
* ``kg_entities(types, limit, max_chunks_per_entity, max_relationships_per_entity)``
  — slice the workspace KG by entity type (Phase 1.5 bulk slice)
* ``kg_chunks(query, top_k, mode)`` — Phase 1.6 chat-grade hybrid retrieval

Every tool call is captured in the run transcript along with timing,
arguments, and a truncated preview of the result. Tools are designed to be
mechanical and bounded — model "thinking" stays in the assistant turns,
tools just fetch / execute / persist.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared types
# ---------------------------------------------------------------------------


# Async slice fn (matches `_slice_workspace_entities` shape but returns dict).
SliceFn = Callable[
    [Optional[list[str]], int, int, int, Optional[set[str]]],
    dict[str, Any],
]

# Async retrieval fn (matches `_retrieve_relevant_entities_for_skill`).
RetrieveFn = Callable[
    [str, str, str, int],
    Awaitable[dict[str, Any]],
]


@dataclass
class ToolContext:
    """Per-invocation context wired by the route layer.

    The route layer constructs this once per ``invoke`` call and passes it
    into the runtime. Tool handlers close over it to perform their work
    without needing global state.
    """

    skill_name: str
    skill_dir: Path
    run_dir: Path
    workspace_dir: Path
    workspace_name: str
    # Optional KG/retrieval bindings — provided by the route layer. When
    # absent (e.g., server started without ``data_func``), kg_chunks degrades
    # gracefully and returns an explanatory error to the model.
    slice_fn: Optional[SliceFn] = None
    retrieve_fn: Optional[RetrieveFn] = None
    # Hard caps to protect the model + caller from unbounded payloads.
    max_read_bytes: int = 200_000
    max_write_bytes: int = 1_000_000
    max_script_seconds: int = 60
    max_kg_entities_per_type: int = 50
    max_kg_chunks: int = 30
    # Filled by the runtime each call so artifacts/tool_outputs land in order.
    call_seq: list[int] = field(default_factory=lambda: [0])


@dataclass
class ToolResult:
    """A single tool invocation result.

    ``payload`` is what the model sees (already JSON-serialized below).
    ``transcript_extra`` is metadata persisted with the transcript entry but
    not shown to the model (e.g., file paths of full outputs that were
    truncated for the model view).
    """

    payload: Any
    truncated: bool = False
    transcript_extra: dict[str, Any] = field(default_factory=dict)


class ToolError(Exception):
    """Raised when a tool call fails (path violation, timeout, etc.).

    The runtime catches this, formats the message, and feeds it back to the
    model as the tool's response so the agent can recover (try a different
    path, smaller limit, etc.).
    """


# ---------------------------------------------------------------------------
# Path sandboxing
# ---------------------------------------------------------------------------


def _safe_join(base: Path, rel: str) -> Path:
    """Resolve ``rel`` under ``base`` and reject any escape attempts.

    Empty or absolute paths, ``..`` traversal, and symlinks pointing outside
    ``base`` all raise ``ToolError``.
    """
    if not rel or not isinstance(rel, str):
        raise ToolError("path must be a non-empty string")
    p = Path(rel)
    if p.is_absolute():
        raise ToolError(f"path must be relative, got absolute: {rel!r}")
    candidate = (base / p).resolve()
    base_resolved = base.resolve()
    try:
        candidate.relative_to(base_resolved)
    except ValueError as exc:
        raise ToolError(
            f"path {rel!r} escapes sandbox {base_resolved}"
        ) from exc
    return candidate


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


async def tool_read_file(ctx: ToolContext, path: str) -> ToolResult:
    """Read a UTF-8 text file from the skill folder.

    Allowed roots inside the skill: ``references/``, ``assets/``,
    ``scripts/``, plus the top-level ``SKILL.md``. Any other path is
    rejected.
    """
    target = _safe_join(ctx.skill_dir, path)
    if not target.exists():
        raise ToolError(f"file not found: {path}")
    if not target.is_file():
        raise ToolError(f"not a regular file: {path}")
    rel = target.relative_to(ctx.skill_dir.resolve()).as_posix()
    if rel != "SKILL.md" and not rel.startswith(("references/", "assets/", "scripts/")):
        raise ToolError(
            f"read_file is restricted to SKILL.md / references/ / assets/ / scripts/ — got {rel!r}"
        )
    size = target.stat().st_size
    truncated = False
    try:
        text = target.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Fall back to latin-1 so we can at least show binary-ish content
        text = target.read_text(encoding="latin-1", errors="replace")
    if len(text) > ctx.max_read_bytes:
        text = text[: ctx.max_read_bytes]
        truncated = True
    return ToolResult(
        payload={
            "path": rel,
            "size_bytes": size,
            "truncated": truncated,
            "content": text,
        },
        truncated=truncated,
    )


async def tool_run_script(
    ctx: ToolContext,
    path: str,
    stdin: Optional[str] = None,
    timeout: Optional[int] = None,
) -> ToolResult:
    """Execute a script under the skill's ``scripts/`` folder.

    Python scripts (``.py``) run with the active interpreter. Shell scripts
    (``.sh``) require ``bash`` on PATH. The subprocess inherits no env vars
    beyond what the parent process has, runs with cwd locked to the skill
    folder, and is killed on timeout.
    """
    target = _safe_join(ctx.skill_dir, path)
    rel = target.relative_to(ctx.skill_dir.resolve()).as_posix()
    if not rel.startswith("scripts/"):
        raise ToolError(f"run_script is restricted to scripts/ — got {rel!r}")
    if not target.is_file():
        raise ToolError(f"script not found: {rel}")

    suffix = target.suffix.lower()
    if suffix == ".py":
        import sys as _sys
        cmd = [_sys.executable, str(target)]
    elif suffix == ".sh":
        cmd = ["bash", str(target)]
    else:
        raise ToolError(
            f"unsupported script type {suffix!r}; only .py and .sh are allowed"
        )

    effective_timeout = min(
        ctx.max_script_seconds,
        max(1, int(timeout)) if timeout is not None else ctx.max_script_seconds,
    )

    def _run() -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            cmd,
            input=stdin or "",
            capture_output=True,
            text=True,
            timeout=effective_timeout,
            cwd=str(ctx.skill_dir),
            check=False,
        )

    try:
        proc = await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired as exc:
        raise ToolError(
            f"script timed out after {effective_timeout}s: {rel}"
        ) from exc
    except FileNotFoundError as exc:
        raise ToolError(f"script interpreter not found: {exc}") from exc

    # Persist full stdout/stderr to disk so the transcript has a pointer
    # even if we truncate for the model view.
    seq = ctx.call_seq[0]
    out_dir = ctx.run_dir / "tool_outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    safe_label = re.sub(r"[^A-Za-z0-9._-]+", "_", rel)
    stdout_path = out_dir / f"{seq:03d}_run_script_{safe_label}.stdout.txt"
    stderr_path = out_dir / f"{seq:03d}_run_script_{safe_label}.stderr.txt"
    stdout_path.write_text(proc.stdout or "", encoding="utf-8")
    stderr_path.write_text(proc.stderr or "", encoding="utf-8")

    cap = 4000
    return ToolResult(
        payload={
            "script": rel,
            "exit_code": proc.returncode,
            "timeout_seconds": effective_timeout,
            "stdout": (proc.stdout or "")[:cap],
            "stderr": (proc.stderr or "")[:cap],
            "stdout_truncated": len(proc.stdout or "") > cap,
            "stderr_truncated": len(proc.stderr or "") > cap,
        },
        transcript_extra={
            "stdout_file": str(stdout_path),
            "stderr_file": str(stderr_path),
        },
    )


async def tool_write_file(ctx: ToolContext, path: str, content: str) -> ToolResult:
    """Write a UTF-8 text artifact to the run's ``artifacts/`` folder.

    Path must be relative and stay inside ``<run_dir>/artifacts/``. Existing
    files are overwritten silently — this is the model's working scratchpad.
    """
    if not isinstance(content, str):
        raise ToolError("content must be a string")
    if len(content.encode("utf-8")) > ctx.max_write_bytes:
        raise ToolError(
            f"content exceeds max_write_bytes ({ctx.max_write_bytes}); split into smaller artifacts"
        )
    artifacts_root = ctx.run_dir / "artifacts"
    artifacts_root.mkdir(parents=True, exist_ok=True)
    target = _safe_join(artifacts_root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    rel = target.relative_to(ctx.run_dir.resolve()).as_posix()
    return ToolResult(
        payload={
            "path": rel,
            "bytes_written": len(content.encode("utf-8")),
        }
    )


# Allowlist for kg_query: only true read-only Cypher. Anything else is rejected.
_KG_QUERY_ALLOWED_PREFIX = re.compile(r"^\s*(MATCH|OPTIONAL MATCH|WITH|UNWIND|CALL|RETURN)\b", re.I)
_KG_QUERY_DENY = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|FOREACH|LOAD\s+CSV)\b",
    re.I,
)


async def tool_kg_query(ctx: ToolContext, cypher: str) -> ToolResult:
    """Run a read-only Cypher query against the active workspace's Neo4j DB.

    Returns up to 100 rows. Mutating clauses are rejected. If the active
    backend is NetworkX (no Neo4j configured), returns a structured error
    so the model can fall back to ``kg_query`` alternatives.
    """
    if not isinstance(cypher, str) or not cypher.strip():
        raise ToolError("cypher must be a non-empty string")
    if _KG_QUERY_DENY.search(cypher):
        raise ToolError("kg_query is read-only; mutating clauses are not allowed")
    if not _KG_QUERY_ALLOWED_PREFIX.match(cypher):
        raise ToolError(
            "cypher must start with MATCH/OPTIONAL MATCH/WITH/UNWIND/CALL/RETURN"
        )

    graph_storage = os.getenv("GRAPH_STORAGE", "").strip()
    if graph_storage != "Neo4JStorage":
        return ToolResult(
            payload={
                "available": False,
                "reason": (
                    f"GRAPH_STORAGE={graph_storage or 'NetworkXStorage'}; "
                    "kg_query requires Neo4JStorage. Use kg_entities or kg_chunks instead."
                ),
                "rows": [],
            }
        )

    try:
        from neo4j import AsyncGraphDatabase  # local import — optional dep
    except ImportError as exc:  # pragma: no cover
        raise ToolError("neo4j driver not installed") from exc

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", ctx.workspace_name) or "neo4j"

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    rows: list[dict[str, Any]] = []
    try:
        async with driver.session(database=database) as session:
            result = await session.run(cypher)
            async for record in result:
                rows.append({k: _jsonable(v) for k, v in record.items()})
                if len(rows) >= 100:
                    break
    except Exception as exc:  # noqa: BLE001
        await driver.close()
        raise ToolError(f"kg_query failed: {exc}") from exc
    await driver.close()

    return ToolResult(
        payload={
            "available": True,
            "row_count": len(rows),
            "truncated": len(rows) >= 100,
            "rows": rows,
        },
        truncated=len(rows) >= 100,
    )


def _jsonable(value: Any) -> Any:
    """Best-effort conversion of Neo4j record values to JSON-serializable shapes."""
    # Neo4j Node / Relationship expose dict-like .items()
    items = getattr(value, "items", None)
    if callable(items):
        try:
            return {k: _jsonable(v) for k, v in items()}
        except Exception:  # noqa: BLE001
            pass
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


async def tool_kg_entities(
    ctx: ToolContext,
    types: Optional[list[str]] = None,
    limit: int = 25,
    max_chunks_per_entity: int = 2,
    max_relationships_per_entity: int = 5,
) -> ToolResult:
    """Slice the workspace KG by entity type.

    Reuses the route layer's Phase 1.5 bulk slice (``_slice_workspace_entities``).
    """
    if ctx.slice_fn is None:
        raise ToolError("kg_entities is unavailable (no slice_fn wired)")
    safe_limit = max(1, min(int(limit or 25), ctx.max_kg_entities_per_type))
    safe_chunks = max(0, min(int(max_chunks_per_entity or 0), 5))
    safe_rels = max(0, min(int(max_relationships_per_entity or 0), 20))
    types_list: Optional[list[str]] = None
    if types:
        if not isinstance(types, list):
            raise ToolError("types must be a list of strings")
        types_list = [str(t) for t in types if t]
    data = ctx.slice_fn(types_list, safe_limit, safe_chunks, safe_rels, None)
    return ToolResult(payload=data)


async def tool_kg_chunks(
    ctx: ToolContext,
    query: str,
    top_k: int = 15,
    mode: str = "hybrid",
) -> ToolResult:
    """Run chat-grade hybrid retrieval and return ranked entities + chunks.

    Reuses the route layer's Phase 1.6 helper (``_retrieve_relevant_entities_for_skill``).
    The model can then call ``kg_entities`` with a filter or just consume the
    retrieval payload directly.
    """
    if ctx.retrieve_fn is None:
        raise ToolError("kg_chunks is unavailable (no retrieve_fn wired)")
    if not isinstance(query, str) or not query.strip():
        raise ToolError("query must be a non-empty string")
    safe_top_k = max(1, min(int(top_k or 15), ctx.max_kg_chunks))
    valid_modes = {"hybrid", "local", "global", "naive", "mix"}
    safe_mode = mode if mode in valid_modes else "hybrid"
    payload = await ctx.retrieve_fn(query, "", safe_mode, safe_top_k)
    # `payload` is {names: set, chunk_ids: set, metadata: dict} — sets aren't
    # JSON-safe, so coerce.
    return ToolResult(
        payload={
            "matched_entity_names": sorted(payload.get("names") or []),
            "matched_chunk_ids": sorted(payload.get("chunk_ids") or []),
            "metadata": payload.get("metadata") or {},
        }
    )


# ---------------------------------------------------------------------------
# Tool registry — used by the runtime to drive the model's tool_choice list
# ---------------------------------------------------------------------------


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict[str, Any]
    handler: Callable[..., Awaitable[ToolResult]]

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def build_tool_specs() -> list[ToolSpec]:
    """Return the canonical six-tool registry.

    Order matters only for transcript readability; the model is free to call
    them in any order.
    """
    return [
        ToolSpec(
            name="read_file",
            description=(
                "Read a UTF-8 text file from the skill folder. Allowed roots: "
                "SKILL.md, references/, assets/, scripts/. Use this to load "
                "schemas, prompt templates, or example payloads bundled with "
                "the skill."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Skill-relative path, e.g. 'references/methodology.md'.",
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            handler=tool_read_file,
        ),
        ToolSpec(
            name="run_script",
            description=(
                "Execute a Python (.py) or Bash (.sh) script under the skill's "
                "scripts/ folder. Subprocess sandboxed: cwd locked to the "
                "skill folder, time-limited. Returns stdout, stderr, exit code."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "scripts/<file> path."},
                    "stdin": {
                        "type": "string",
                        "description": "Optional stdin to pipe to the script.",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max seconds before SIGKILL. Capped by the runtime.",
                        "minimum": 1,
                        "maximum": 60,
                    },
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            handler=tool_run_script,
        ),
        ToolSpec(
            name="write_file",
            description=(
                "Persist a UTF-8 text artifact to <run_dir>/artifacts/. Use "
                "this for proposal drafts, compliance matrices, infographic "
                "HTML, or any deliverable the user should download. Path is "
                "relative to the artifacts/ root."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Artifact path relative to artifacts/, e.g. 'volume-1-outline.md'.",
                    },
                    "content": {"type": "string", "description": "File body."},
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            handler=tool_write_file,
        ),
        ToolSpec(
            name="kg_query",
            description=(
                "Run a read-only Cypher query against the active workspace's "
                "Neo4j graph. Mutating clauses (CREATE/MERGE/DELETE/SET) are "
                "rejected. Returns up to 100 rows. If the workspace uses "
                "NetworkXStorage instead of Neo4j, the call returns "
                "available=false and the model should use kg_entities or "
                "kg_chunks instead."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "cypher": {
                        "type": "string",
                        "description": "Read-only Cypher query (MATCH/RETURN style).",
                    },
                },
                "required": ["cypher"],
                "additionalProperties": False,
            },
            handler=tool_kg_query,
        ),
        ToolSpec(
            name="kg_entities",
            description=(
                "Slice the active workspace's knowledge graph by entity type. "
                "Returns a deterministic bucket of entities with their "
                "descriptions, source chunk IDs, and connecting relationships. "
                "Use when you know which entity types you need (e.g. "
                "['proposal_instruction', 'evaluation_factor'])."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "types": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Entity types to include. Omit to get all non-noise types.",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max entities per type (capped by runtime).",
                        "minimum": 1,
                        "maximum": 50,
                    },
                    "max_chunks_per_entity": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 5,
                        "description": "Per-entity cap on returned source chunk IDs.",
                    },
                    "max_relationships_per_entity": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 20,
                        "description": "Per-entity cap on returned KG relationships.",
                    },
                },
                "additionalProperties": False,
            },
            handler=tool_kg_entities,
        ),
        ToolSpec(
            name="kg_chunks",
            description=(
                "Run chat-grade hybrid retrieval (Phase 1.6) over the active "
                "workspace. Returns ranked entity names + chunk IDs scored "
                "against the query. Use when you don't know which entity "
                "types to ask for, or when answering a free-text user question."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural-language retrieval query.",
                    },
                    "top_k": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 30,
                        "description": "Number of entity hits to return.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["hybrid", "local", "global", "naive", "mix"],
                        "description": "Retrieval mode (default 'hybrid').",
                    },
                },
                "required": ["query"],
                "additionalProperties": False,
            },
            handler=tool_kg_chunks,
        ),
    ]


def serialize_tool_payload_for_model(result: ToolResult, *, char_cap: int = 12_000) -> str:
    """Serialize a tool result into the JSON string fed back to the model.

    OpenAI's chat protocol expects the ``content`` of a ``role: tool`` message
    to be a string; we use compact JSON. Long payloads are truncated with a
    sentinel so the model knows it's incomplete.
    """
    try:
        text = json.dumps(result.payload, ensure_ascii=False, default=str)
    except (TypeError, ValueError) as exc:
        text = json.dumps({"error": f"unable to serialize payload: {exc}"})
    if len(text) > char_cap:
        text = text[:char_cap] + f'\n…[truncated at {char_cap} chars]'
    return text
