"""SkillManager — discover, install, and invoke agent skills.

Skills live in ``.github/skills/<name>/SKILL.md`` (the official agentskills.io
location). Each ``SKILL.md`` is a Markdown file with YAML frontmatter:

    ---
    name: <slug>
    description: <pushy, precise trigger sentence>
    category: <design|ontology|proposal|compliance|intel|other>
    version: <semver>
    license: <spdx>
    ---

    # <Skill Title>
    <imperative instructions...>

The manager:
  * Walks ``.github/skills/`` at startup (and on demand) to register skills
  * Stores install metadata in ``rag_storage/_platform/skills.json`` (a single
    workspace-independent JSON file — installed skills are global to the
    Theseus instance, not per-RFP)
  * Pulls relevant entity slices from the active workspace KG when a skill is
    invoked, then dispatches the SKILL.md instructions + entity payload to
    the configured LLM
  * Supports installation from a GitHub URL via ``git clone --depth=1`` into
    ``.github/skills/`` (no PyPI / no archive fetch — git is the contract)

Design choices:
  * No SQLite, no PyYAML, no extra deps — small inline YAML frontmatter
    parser handles only what skill files actually use (str/int/bool keys at
    top level).
  * Workspace context injection is deliberately conservative: we pull entity
    *names* and *types*, never raw chunk text, into the prompt. The skill
    can ask for chunk-level evidence via the standard query endpoints.
  * Invocation never blocks the main event loop — long LLM calls use
    ``asyncio.to_thread`` if a sync LLM client is the only option available.
"""

from __future__ import annotations

import asyncio
import json
import logging
import mimetypes
import os
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional


def _env_int(name: str, default: int) -> int:
    """Read an int from the environment with a safe fallback."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        logger_ = logging.getLogger(__name__)
        logger_.warning(
            "Invalid %s=%r; using default %d", name, raw, default
        )
        return default


# Default char-budget for the JSON-serialized entity_payload block injected
# into the skill prompt. xAI Grok and most modern frontier models comfortably
# handle 200k+ chars; tune via SKILL_MAX_PAYLOAD_CHARS in .env if you switch
# models or hit token-cost concerns. The cap protects against an unbounded KG
# slice exploding the request payload, not against model context limits.
DEFAULT_SKILL_MAX_PAYLOAD_CHARS = _env_int("SKILL_MAX_PAYLOAD_CHARS", 200_000)

logger = logging.getLogger(__name__)


# Mimetypes the stdlib ``mimetypes`` module misses on Windows / fresh installs.
# Used by ``SkillManager.list_deliverables`` to label rows for the Studio UI.
_STUDIO_EXTRA_MIME: dict[str, str] = {
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "md": "text/markdown",
    "json": "application/json",
    "gif": "image/gif",
    "mp4": "video/mp4",
    "pdf": "application/pdf",
}


def resolve_artifact_mime(filename: str) -> str:
    """Resolve a stable mime type for a skill artifact filename.

    Precedence: explicit ``_STUDIO_EXTRA_MIME`` map > ``mimetypes.guess_type``
    > ``application/octet-stream``. The explicit map wins because Windows'
    registry mislabels common office / markdown formats (e.g. ``.md`` ->
    ``application/text``) and we want listing + download responses to agree.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in _STUDIO_EXTRA_MIME:
        return _STUDIO_EXTRA_MIME[ext]
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_DIR = _REPO_ROOT / ".github" / "skills"
_PLATFORM_DIR = _REPO_ROOT / "rag_storage" / "_platform"
_INSTALL_LEDGER = _PLATFORM_DIR / "skills.json"


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------


@dataclass
class SkillFrontmatter:
    """Parsed YAML frontmatter from a SKILL.md file.

    Spec-conformant top-level fields (per agentskills.io): ``name``,
    ``description``, ``license``, ``compatibility``, ``metadata``,
    ``allowed-tools``. The legacy fields ``category``, ``version``,
    ``upstream``, ``status`` are still parsed at the top level for
    backward compatibility with our pre-2.0 skills, but new skills MUST
    nest those under ``metadata:`` per the spec (see
    ``docs/SKILL_SPEC_COMPLIANCE.md``).
    """

    name: str
    description: str
    category: str = "other"
    version: str = "0.0.0"
    license: str = ""
    upstream: str = ""
    status: str = ""
    # Spec-only fields (may be absent in legacy skills)
    compatibility: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    allowed_tools: list[str] = field(default_factory=list)
    # Anything else parsed but not recognised
    extras: dict[str, Any] = field(default_factory=dict)

    @property
    def runtime_mode(self) -> str:
        """Skill runtime mode: ``"tools"`` (multi-turn tool-calling) or
        ``"legacy"`` (single-shot prompt stuffing). Default ``legacy`` until a
        skill opts in via ``metadata.runtime: tools``.
        """
        raw = str(self.metadata.get("runtime", "")).strip().lower()
        return "tools" if raw == "tools" else "legacy"

    @property
    def required_mcps(self) -> list[str]:
        """MCP server aliases the skill is allowed to talk to.

        Phase 4b: declared via ``metadata.mcps: [usaspending, sam_gov]`` in
        the SKILL.md frontmatter. Default is empty (closed) — a skill that
        does not declare ``metadata.mcps`` gets zero MCP tools, mirroring the
        opt-in security shape of ``metadata.script_paths``. Accepts either a
        flow-style list or a single string for ergonomics.
        """
        raw = self.metadata.get("mcps")
        if raw is None:
            return []
        if isinstance(raw, str):
            return [raw.strip()] if raw.strip() else []
        if isinstance(raw, list):
            return [str(x).strip() for x in raw if str(x).strip()]
        return []


@dataclass
class Skill:
    """A discovered or installed skill."""

    name: str
    path: str  # absolute path to skill directory
    skill_md_path: str
    frontmatter: SkillFrontmatter
    body_md: str
    has_scripts: bool = False
    has_templates: bool = False  # deprecated alias for has_assets (templates/ -> assets/ rename per spec)
    has_assets: bool = False
    has_references: bool = False
    has_evals: bool = False
    installed_at: str = ""
    last_invoked_at: str = ""
    source: str = "builtin"  # "builtin" (in-repo) or "installed" (cloned)
    source_url: str = ""

    def to_summary(self) -> dict[str, Any]:
        """Trimmed dict for /api/ui/skills list endpoint."""
        fm = self.frontmatter
        meta = fm.metadata or {}
        # Phase 4j taxonomy — see docs/SKILL_TAXONOMY.md.
        # Closed vocabularies; UI groups by personas_primary and filters by
        # shipley_phases / capability. Default values keep legacy skills
        # discoverable as "Utility" until backfilled.
        personas_primary_raw = meta.get("personas_primary")
        personas_primary = (
            str(personas_primary_raw).strip()
            if personas_primary_raw not in (None, "", "None")
            else "none"
        )
        personas_secondary_raw = meta.get("personas_secondary", []) or []
        if isinstance(personas_secondary_raw, str):
            personas_secondary = [personas_secondary_raw.strip()] if personas_secondary_raw.strip() else []
        elif isinstance(personas_secondary_raw, list):
            personas_secondary = [str(x).strip() for x in personas_secondary_raw if str(x).strip()]
        else:
            personas_secondary = []
        shipley_phases_raw = meta.get("shipley_phases", []) or []
        if isinstance(shipley_phases_raw, str):
            shipley_phases = [shipley_phases_raw.strip()] if shipley_phases_raw.strip() else []
        elif isinstance(shipley_phases_raw, list):
            shipley_phases = [str(x).strip() for x in shipley_phases_raw if str(x).strip()]
        else:
            shipley_phases = []
        capability_raw = meta.get("capability")
        capability = str(capability_raw).strip() if capability_raw else ""
        return {
            "name": self.name,
            "description": fm.description,
            "category": fm.category,
            "version": fm.version,
            "license": fm.license,
            "upstream": fm.upstream,
            "status": fm.status,
            "has_scripts": self.has_scripts,
            "has_templates": self.has_templates,
            "has_assets": self.has_assets,
            "has_references": self.has_references,
            "has_evals": self.has_evals,
            "runtime_mode": fm.runtime_mode,
            "source": self.source,
            "source_url": self.source_url,
            "installed_at": self.installed_at,
            "last_invoked_at": self.last_invoked_at,
            # Phase 4j taxonomy fields (closed vocabularies).
            "personas_primary": personas_primary,
            "personas_secondary": personas_secondary,
            "shipley_phases": shipley_phases,
            "capability": capability,
        }


@dataclass
class SkillInvocationResult:
    """Returned by ``SkillManager.invoke``."""

    skill: str
    workspace: str
    response: str
    entities_used: list[str]
    warnings: list[str]
    elapsed_ms: int
    prompt_tokens_estimate: int
    run_id: str = ""
    run_dir: str = ""


@dataclass
class SkillRunSummary:
    """Lightweight summary of a persisted skill run (for list views)."""

    run_id: str
    skill: str
    workspace: str
    created_at: str
    elapsed_ms: int
    prompt_preview: str
    response_chars: int
    entities_used: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Frontmatter parsing (tiny, intentional — no PyYAML dep)
# ---------------------------------------------------------------------------

_FRONTMATTER_FENCE = "---"
# Spec-conformant top-level fields per agentskills.io. We continue to recognise
# the legacy fields (category/version/upstream/status) at the top level for
# backward compatibility; new skills should nest those under ``metadata:``.
_SPEC_TOP_LEVEL = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}
_LEGACY_TOP_LEVEL = {"category", "version", "upstream", "status"}
_KNOWN_KEYS = _SPEC_TOP_LEVEL | _LEGACY_TOP_LEVEL


def _coerce_scalar(val: str) -> Any:
    """Best-effort scalar coercion for our minimal YAML dialect."""
    s = val.strip()
    if not s:
        return ""
    if (s.startswith('"') and s.endswith('"')) or (
        s.startswith("'") and s.endswith("'")
    ):
        return s[1:-1]
    low = s.lower()
    if low in {"true", "false"}:
        return low == "true"
    if low in {"null", "none", "~"}:
        return None
    try:
        if "." not in s and "e" not in low:
            return int(s)
        return float(s)
    except ValueError:
        return s


def _parse_inline_list(val: str) -> list[Any]:
    """Parse a flow-style YAML list ``[a, b, c]``. Falls back to whitespace-split."""
    s = val.strip()
    if s.startswith("[") and s.endswith("]"):
        inner = s[1:-1].strip()
        if not inner:
            return []
        return [_coerce_scalar(p) for p in re.split(r"\s*,\s*", inner)]
    return [_coerce_scalar(p) for p in s.split() if p]


def _parse_frontmatter(text: str) -> tuple[SkillFrontmatter, str]:
    """Split a SKILL.md into frontmatter and body.

    Supports the subset of YAML our skills actually use:

    * Top-level scalar ``key: value`` pairs (strings, ints, floats, bools).
    * A single nested block under ``metadata:`` whose immediate children are
      either scalars or single-level lists. The spec uses ``metadata:`` as
      the escape hatch for custom keys, so this is the only nesting we need.
    * Flow-style inline lists (``allowed-tools: [Read, Write]``).

    Multi-line strings, deeply nested mappings, and YAML anchors are NOT
    supported. Encountered unparseable lines are stored under
    ``extras['_unparsed']`` so the loader can warn but still succeed.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != _FRONTMATTER_FENCE:
        return SkillFrontmatter(name="", description=""), text

    end_idx = -1
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONTMATTER_FENCE:
            end_idx = i
            break
    if end_idx == -1:
        logger.warning("Frontmatter fence not closed — treating as no frontmatter")
        return SkillFrontmatter(name="", description=""), text

    front_lines = lines[1:end_idx]
    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")

    parsed: dict[str, Any] = {}
    extras: dict[str, Any] = {}
    metadata: dict[str, Any] = {}
    in_metadata_block = False
    metadata_indent = -1
    pending_list_key: Optional[str] = None
    pending_list_indent = -1
    pending_list_target: Optional[dict[str, Any]] = None

    for raw in front_lines:
        # Comment / blank
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue

        stripped = raw.lstrip()
        indent = len(raw) - len(stripped)

        # Continuation of a block-style YAML list "key:\n  - item\n  - item"
        if pending_list_key is not None and stripped.startswith("-") and indent > pending_list_indent:
            item = stripped[1:].strip()
            if pending_list_target is not None:
                pending_list_target.setdefault(pending_list_key, []).append(_coerce_scalar(item))
            continue
        else:
            pending_list_key = None
            pending_list_target = None

        # Inside metadata: block (any line indented past metadata_indent)
        if in_metadata_block and indent > metadata_indent:
            m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", stripped)
            if not m:
                extras.setdefault("_unparsed", []).append(raw)
                continue
            key, val = m.group(1), m.group(2)
            if not val.strip():
                # Block-style list follows
                pending_list_key = key
                pending_list_indent = indent
                pending_list_target = metadata
                metadata.setdefault(key, [])
                continue
            if val.strip().startswith("["):
                metadata[key] = _parse_inline_list(val)
            else:
                metadata[key] = _coerce_scalar(val)
            continue

        # Returned to top level
        in_metadata_block = False
        metadata_indent = -1

        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", raw)
        if not m:
            extras.setdefault("_unparsed", []).append(raw)
            continue
        key, val = m.group(1), m.group(2)

        if key == "metadata" and not val.strip():
            in_metadata_block = True
            metadata_indent = indent
            continue

        if key == "metadata" and val.strip().startswith("{"):
            # Inline mapping — minimal support
            inner = val.strip()[1:-1].strip() if val.strip().endswith("}") else ""
            for pair in re.split(r"\s*,\s*", inner) if inner else []:
                if ":" in pair:
                    k2, v2 = pair.split(":", 1)
                    metadata[k2.strip()] = _coerce_scalar(v2)
            continue

        if key == "allowed-tools":
            parsed[key] = _parse_inline_list(val) if val.strip().startswith("[") else val.strip().split()
            continue

        if not val.strip():
            # Block-style list at top level (only allowed-tools really uses this)
            pending_list_key = key
            pending_list_indent = indent
            pending_list_target = parsed
            parsed.setdefault(key, [])
            continue

        coerced = _coerce_scalar(val)
        if key in _KNOWN_KEYS:
            parsed[key] = coerced
        else:
            extras[key] = coerced

    # Promote legacy fields nested under metadata to the dataclass attrs so
    # consumers (UI summary, copilot-instructions audit) see a single source
    # of truth, while keeping the metadata dict intact for the runtime.
    def _meta_or_top(key: str, default: Any) -> Any:
        if key in metadata:
            return metadata[key]
        return parsed.get(key, default)

    fm = SkillFrontmatter(
        name=str(parsed.get("name", "")),
        description=str(parsed.get("description", "")),
        category=str(_meta_or_top("category", "other")),
        version=str(_meta_or_top("version", "0.0.0")),
        license=str(parsed.get("license", "")),
        upstream=str(_meta_or_top("upstream", "")),
        status=str(_meta_or_top("status", "")),
        compatibility=str(parsed.get("compatibility", "")),
        metadata=metadata,
        allowed_tools=list(parsed.get("allowed-tools", []) or []),
        extras=extras,
    )
    return fm, body


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class SkillManager:
    """Discover and invoke agent skills.

    The manager is a singleton (see :func:`get_skill_manager`) and is safe to
    call concurrently — discovery and ledger writes are guarded by a lock.
    """

    def __init__(
        self,
        skills_dir: Path = _SKILLS_DIR,
        ledger_path: Path = _INSTALL_LEDGER,
        mcps_root: Optional[Path] = None,
    ) -> None:
        self.skills_dir = skills_dir
        self.ledger_path = ledger_path
        self._skills: dict[str, Skill] = {}
        self._lock = asyncio.Lock()
        self._ledger: dict[str, dict[str, Any]] = {}
        # Phase 4a: MCP client subsystem. Lazy-imported so legacy-mode
        # deployments without any MCPs installed pay zero cost.
        from src.skills.mcp_client import MCPRegistry

        if mcps_root is None:
            mcps_root = _REPO_ROOT / "tools" / "mcps"
        self._mcp_registry = MCPRegistry.from_root(mcps_root)

    # ---- Discovery ----------------------------------------------------

    def discover(self) -> dict[str, Skill]:
        """Walk ``.github/skills/`` and register every ``SKILL.md`` found."""
        self._load_ledger()
        registered: dict[str, Skill] = {}
        if not self.skills_dir.exists():
            logger.info("Skills directory missing: %s", self.skills_dir)
            self._skills = registered
            return registered

        for child in sorted(self.skills_dir.iterdir()):
            if not child.is_dir():
                continue
            skill_md = child / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                skill = self._load_skill(child, skill_md)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to load skill at %s: %s", child, exc)
                continue
            registered[skill.name] = skill

        self._skills = registered
        logger.info("Discovered %d agent skills under %s", len(registered), self.skills_dir)
        return registered

    def _load_skill(self, folder: Path, skill_md: Path) -> Skill:
        text = skill_md.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)
        name = fm.name or folder.name
        ledger_entry = self._ledger.get(name, {})
        return Skill(
            name=name,
            path=str(folder.resolve()),
            skill_md_path=str(skill_md.resolve()),
            frontmatter=fm,
            body_md=body,
            has_scripts=(folder / "scripts").is_dir(),
            has_templates=(folder / "templates").is_dir(),
            has_assets=(folder / "assets").is_dir(),
            has_references=(folder / "references").is_dir(),
            has_evals=(folder / "evals").is_dir(),
            installed_at=ledger_entry.get("installed_at", ""),
            last_invoked_at=ledger_entry.get("last_invoked_at", ""),
            source=ledger_entry.get("source", "builtin"),
            source_url=ledger_entry.get("source_url", ""),
        )

    # ---- Public read API ---------------------------------------------

    def list_skills(self, include_developer: bool = False) -> list[dict[str, Any]]:
        if not self._skills:
            self.discover()
        return [
            s.to_summary()
            for s in self._skills.values()
            if include_developer or not (s.frontmatter.metadata or {}).get("developer_only", False)
        ]

    def get_skill(self, name: str) -> Optional[Skill]:
        if not self._skills:
            self.discover()
        return self._skills.get(name)

    def get_skill_detail(self, name: str) -> Optional[dict[str, Any]]:
        skill = self.get_skill(name)
        if not skill:
            return None
        detail = skill.to_summary()
        detail["body_md"] = skill.body_md
        detail["references"] = self._list_subdir(Path(skill.path) / "references", ".md")
        detail["assets"] = self._list_subdir(
            Path(skill.path) / "assets",
            ".md", ".html", ".txt", ".css", ".svg", ".png", ".jpg", ".jpeg",
            ".json", ".jsx", ".js", ".mjs", ".mp3", ".mp4", ".gif",
        )
        # Deprecated alias for back-compat — spec renamed templates/ -> assets/.
        # Kept so any pre-2.3 skill that still ships a templates/ folder is still
        # listed in /api/ui/skills/{name} until it migrates.
        detail["templates"] = self._list_subdir(
            Path(skill.path) / "templates", ".md", ".html", ".txt"
        )
        detail["scripts"] = self._list_subdir(
            Path(skill.path) / "scripts", ".py", ".js", ".sh"
        )
        return detail

    @staticmethod
    def _list_subdir(folder: Path, *exts: str) -> list[dict[str, str]]:
        if not folder.is_dir():
            return []
        out: list[dict[str, str]] = []
        for p in sorted(folder.iterdir()):
            if not p.is_file():
                continue
            if exts and p.suffix.lower() not in exts:
                continue
            out.append({"name": p.name, "size": str(p.stat().st_size)})
        return out

    # ---- Install / uninstall -----------------------------------------

    async def install_from_github(self, url: str, name: Optional[str] = None) -> Skill:
        """Clone a GitHub repo into ``.github/skills/<name>``.

        The repo MUST contain a ``SKILL.md`` at its root. URL must be HTTPS to
        github.com (we refuse other hosts and any non-https scheme to limit
        SSRF / supply-chain blast radius). The clone is shallow and the .git
        directory is removed after success.
        """
        if not url.startswith("https://github.com/"):
            raise ValueError(
                "Only https://github.com/ URLs are accepted for skill install"
            )
        target_name = name or _slug_from_github_url(url)
        if not _SAFE_SLUG.match(target_name):
            raise ValueError(f"Invalid target skill name: {target_name!r}")

        target_dir = self.skills_dir / target_name
        if target_dir.exists():
            raise FileExistsError(f"Skill already installed: {target_name}")

        async with self._lock:
            self.skills_dir.mkdir(parents=True, exist_ok=True)
            # git is run in a worker thread to avoid blocking the loop.
            await asyncio.to_thread(_git_clone_shallow, url, target_dir)
            try:
                skill_md = target_dir / "SKILL.md"
                if not skill_md.exists():
                    raise ValueError("Cloned repo has no SKILL.md at the root")
                shutil.rmtree(target_dir / ".git", ignore_errors=True)
                self._record_install(target_name, url)
            except Exception:
                shutil.rmtree(target_dir, ignore_errors=True)
                raise

        self.discover()
        skill = self._skills.get(target_name)
        if skill is None:
            raise RuntimeError("Install completed but skill not discoverable")
        return skill

    async def uninstall(self, name: str) -> bool:
        """Remove an installed (non-builtin) skill."""
        skill = self.get_skill(name)
        if skill is None:
            return False
        if skill.source == "builtin":
            raise PermissionError(
                f"Refusing to remove built-in skill {name!r} — edit the source instead"
            )
        async with self._lock:
            shutil.rmtree(skill.path, ignore_errors=True)
            self._ledger.pop(name, None)
            self._save_ledger()
        self.discover()
        return True

    # ---- Invocation ---------------------------------------------------

    async def invoke(
        self,
        name: str,
        *,
        workspace: str,
        user_prompt: str,
        entity_payload: dict[str, Any],
        llm: Callable[[str], Awaitable[str]],
        max_payload_chars: Optional[int] = None,
        workspace_root: Optional[Path] = None,
        slice_fn: Optional[Callable[..., dict[str, Any]]] = None,
        retrieve_fn: Optional[Callable[..., Awaitable[dict[str, Any]]]] = None,
        runtime_mode_override: Optional[str] = None,
    ) -> SkillInvocationResult:
        """Run a skill against an injected workspace context.

        Args:
            name: Skill slug.
            workspace: Active workspace name (for telemetry / output envelope).
            user_prompt: Free-text user instruction (may be empty for
                "use defaults" mode).
            entity_payload: Briefing book dict produced by the route layer
                (Phase 1.5 contract). Expected top-level keys:
                ``entities`` (``{entity_type: [{name, description,
                source_chunks}]}``), ``source_chunks`` (verbatim RFP text
                blocks the model is required to quote from), and
                ``relationships`` (typed KG edges between sliced entities).
                Falls back gracefully if older callers pass a flat
                ``{entity_type: [...]}`` dict.
            llm: Async callable that takes a single composed prompt string
                and returns the model's response. Lets the caller decide which
                model / temperature to use.
            max_payload_chars: Hard cap on the JSON-serialized entity payload
                included in the prompt (truncated with a marker if exceeded).
            slice_fn: Optional Phase 1.5 KG slice callable (route layer's
                ``_slice_workspace_entities``). Required for tools-mode skills
                that call ``kg_entities``.
            retrieve_fn: Optional Phase 1.6 retrieval callable (route layer's
                ``_retrieve_relevant_entities_for_skill``). Required for
                tools-mode skills that call ``kg_chunks``.
            runtime_mode_override: Force ``"tools"`` or ``"legacy"`` regardless
                of what the skill's ``metadata.runtime`` declares. Used by the
                env var ``SKILL_RUNTIME_MODE`` and tests.
        """
        skill = self.get_skill(name)
        if skill is None:
            raise KeyError(f"Unknown skill: {name}")

        # Resolve runtime mode: explicit override > env var > frontmatter > default.
        env_override = os.getenv("SKILL_RUNTIME_MODE", "").strip().lower()
        if runtime_mode_override in {"tools", "legacy"}:
            mode = runtime_mode_override
        elif env_override in {"tools", "legacy"}:
            mode = env_override
        else:
            mode = skill.frontmatter.runtime_mode

        if mode == "tools":
            return await self._invoke_tools_mode(
                skill=skill,
                workspace=workspace,
                user_prompt=user_prompt,
                workspace_root=workspace_root,
                slice_fn=slice_fn,
                retrieve_fn=retrieve_fn,
            )
        return await self._invoke_legacy_mode(
            skill=skill,
            workspace=workspace,
            user_prompt=user_prompt,
            entity_payload=entity_payload,
            llm=llm,
            max_payload_chars=max_payload_chars,
            workspace_root=workspace_root,
        )

    # ---- Legacy single-shot path (pre-2.1) ---------------------------

    async def _invoke_legacy_mode(
        self,
        *,
        skill: "Skill",
        workspace: str,
        user_prompt: str,
        entity_payload: dict[str, Any],
        llm: Callable[[str], Awaitable[str]],
        max_payload_chars: Optional[int],
        workspace_root: Optional[Path],
    ) -> SkillInvocationResult:
        """Original single-shot dispatch — pre-builds briefing book and calls llm once."""
        name = skill.name
        warnings: list[str] = []
        budget = max_payload_chars if max_payload_chars is not None else DEFAULT_SKILL_MAX_PAYLOAD_CHARS
        payload_json = json.dumps(entity_payload, ensure_ascii=False, indent=2)
        if len(payload_json) > budget:
            payload_json = payload_json[:budget] + "\n…[truncated]"
            warnings.append(
                f"briefing book truncated at {budget} chars (SKILL_MAX_PAYLOAD_CHARS); "
                "raise the env var, narrow entity_types, or lower max_chunks_per_entity"
            )

        # Phase 1.5: ``entity_payload`` is now a briefing-book dict whose
        # ``entities`` sub-dict holds the type buckets. Older callers may pass
        # the flat shape — detect both and surface a single, accurate list.
        if isinstance(entity_payload.get("entities"), dict):
            entities_used = sorted(entity_payload["entities"].keys())
        else:
            entities_used = sorted(
                k for k in entity_payload.keys()
                if k not in {"source_chunks", "relationships", "retrieval_metadata"}
            )
        composed = self._compose_prompt(skill, workspace, user_prompt, payload_json)

        started = datetime.now(timezone.utc)
        response = await llm(composed)
        elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)

        # Telemetry: stamp last-invoked timestamp.
        self._touch_invocation(name)

        run_id = ""
        run_dir = ""
        if workspace_root is not None:
            try:
                run_id, run_dir = self._persist_run(
                    workspace_root=workspace_root,
                    skill_name=name,
                    workspace=workspace,
                    user_prompt=user_prompt,
                    composed_prompt=composed,
                    response=response,
                    entities_used=entities_used,
                    warnings=warnings,
                    elapsed_ms=elapsed_ms,
                    started_at=started,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to persist skill run for %s: %s", name, exc)
                warnings.append(f"persistence failed: {exc}")

        return SkillInvocationResult(
            skill=name,
            workspace=workspace,
            response=response,
            entities_used=entities_used,
            warnings=warnings,
            elapsed_ms=elapsed_ms,
            prompt_tokens_estimate=len(composed) // 4,  # rough
            run_id=run_id,
            run_dir=run_dir,
        )

    # ---- Tools-mode multi-turn loop (2.1) -----------------------------

    async def _invoke_tools_mode(
        self,
        *,
        skill: "Skill",
        workspace: str,
        user_prompt: str,
        workspace_root: Optional[Path],
        slice_fn: Optional[Callable[..., dict[str, Any]]],
        retrieve_fn: Optional[Callable[..., Awaitable[dict[str, Any]]]],
    ) -> SkillInvocationResult:
        """Multi-turn tool-calling dispatch.

        The skill body is the workflow contract. The runtime gives the model
        six tools (read_file, run_script, write_file, kg_query, kg_entities,
        kg_chunks) and lets it drive itself to a final answer. Every tool call
        is captured in ``transcript.json`` for grounding audit.

        Requires ``workspace_root`` so the run folder (with artifacts/ and
        tool_outputs/) can be created up front; the runtime writes
        ``transcript.json`` after every turn so a crash leaves a usable
        partial trace.
        """
        # Local imports keep the openai dep optional for legacy-mode users.
        from src.skills.runtime import run_tool_loop
        from src.skills.tools import ToolContext

        if workspace_root is None:
            raise RuntimeError(
                "tools-mode skills require workspace_root for run persistence"
            )

        warnings: list[str] = []
        started = datetime.now(timezone.utc)
        ts = started.strftime("%Y%m%d_%H%M%S")
        slug = _slugify_for_filename(user_prompt) or "run"
        run_id = f"{ts}_{slug}"
        run_dir = self._runs_root(workspace_root, skill.name) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(exist_ok=True)
        (run_dir / "tool_outputs").mkdir(exist_ok=True)

        # Honour an env-tunable turn cap so operators can throttle cost.
        # A skill MAY also declare ``metadata.max_turns`` to claim a larger
        # budget for itself when its workflow legitimately needs it (e.g.,
        # ``competitive-intel`` walks 10 numbered steps with multiple MCP
        # calls each). The skill's value wins when it is a positive int and
        # exceeds the env baseline; otherwise the env value is used. This
        # keeps the global throttle as a floor, not a ceiling, so operators
        # can still raise it across the board without editing every skill.
        env_max_turns = _env_int("SKILL_TOOLS_MAX_TURNS", 12)
        max_turns = env_max_turns
        skill_max_turns_raw = skill.frontmatter.metadata.get("max_turns")
        if isinstance(skill_max_turns_raw, int) and skill_max_turns_raw > max_turns:
            max_turns = skill_max_turns_raw

        # Phase 3b: opt-in cross-skill script roots. The skill declares
        # ``metadata.script_paths`` as a list of directories (relative to its
        # own folder) that ``run_script`` may execute from. Typical use is
        # pointing at a sibling utility skill's scripts/ dir (e.g.,
        # ``../huashu-design/scripts``) so PPTX/PDF renderers can be
        # invoked without per-skill wrapper shims. We resolve, validate
        # existence, and pass absolute paths to the tool runtime.
        extra_script_roots: list[Path] = []
        raw_paths = skill.frontmatter.metadata.get("script_paths") or []
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
        skill_dir_resolved = Path(skill.path).resolve()
        for entry in raw_paths:
            if not isinstance(entry, str) or not entry.strip():
                warnings.append(
                    f"script_paths: skipping non-string entry {entry!r}"
                )
                continue
            candidate = (Path(skill.path) / entry).resolve()
            if not candidate.is_dir():
                warnings.append(
                    f"script_paths: directory does not exist or is not a dir: {entry}"
                )
                continue
            # Don't allow declaring your own skill_dir as an extra root (no-op);
            # also reject ascending past the skills container root.
            if candidate == skill_dir_resolved:
                continue
            extra_script_roots.append(candidate)

        ctx = ToolContext(
            skill_name=skill.name,
            skill_dir=Path(skill.path),
            run_dir=run_dir,
            workspace_dir=workspace_root,
            workspace_name=workspace,
            slice_fn=slice_fn,
            retrieve_fn=retrieve_fn,
            extra_script_roots=extra_script_roots,
        )

        # Phase 4a: spawn one subprocess per declared MCP for this run.
        # The registry handles unknown / failed MCPs gracefully (warns and
        # omits them) so partial failures do not abort the run.
        requested_mcps = skill.frontmatter.required_mcps
        if requested_mcps:
            try:
                ctx.mcp_sessions = await self._mcp_registry.start_run_sessions(
                    run_id=run_id, requested=requested_mcps
                )
                started_names = sorted(ctx.mcp_sessions)
                missing = [m for m in requested_mcps if m not in ctx.mcp_sessions]
                if missing:
                    warnings.append(
                        f"MCP servers requested but not started: {missing}"
                    )
                if started_names:
                    logger.info(
                        "skill %s run %s: MCP sessions live: %s",
                        skill.name,
                        run_id,
                        started_names,
                    )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "MCP startup failed for skill %s run %s: %s",
                    skill.name,
                    run_id,
                    exc,
                )
                warnings.append(f"MCP startup failed: {exc}")

        try:
            loop_result = await run_tool_loop(
                skill_name=skill.name,
                skill_body=skill.body_md,
                user_prompt=user_prompt,
                ctx=ctx,
                max_turns=max_turns,
            )
        finally:
            # Phase 4a: reap MCP subprocesses. Must run on every exit path
            # (success, exception, turn-cap forced summary) so abandoned
            # Node/Python child procs don't accumulate across runs.
            if ctx.mcp_sessions:
                try:
                    await self._mcp_registry.shutdown_run(run_id)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "MCP shutdown failed for run %s: %s", run_id, exc
                    )
        warnings.extend(loop_result.warnings)
        elapsed_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)

        # Persist the run envelope. The transcript itself is already written
        # incrementally by the runtime; we just stamp the human-readable
        # summary here.
        try:
            self._persist_tools_run(
                run_dir=run_dir,
                run_id=run_id,
                skill_name=skill.name,
                workspace=workspace,
                user_prompt=user_prompt,
                response=loop_result.response,
                turns=loop_result.turns,
                tool_calls=loop_result.tool_calls,
                finish_reason=loop_result.finish_reason,
                usage_total=loop_result.usage_total,
                warnings=warnings,
                elapsed_ms=elapsed_ms,
                started_at=started,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist tools-mode run for %s: %s", skill.name, exc)
            warnings.append(f"persistence failed: {exc}")

        self._touch_invocation(skill.name)

        return SkillInvocationResult(
            skill=skill.name,
            workspace=workspace,
            response=loop_result.response,
            entities_used=[],  # tools-mode discovers entities through tool calls
            warnings=warnings,
            elapsed_ms=elapsed_ms,
            prompt_tokens_estimate=int(loop_result.usage_total.get("total_tokens", 0)),
            run_id=run_id,
            run_dir=str(run_dir.resolve()),
        )

    @staticmethod
    def _persist_tools_run(
        *,
        run_dir: Path,
        run_id: str,
        skill_name: str,
        workspace: str,
        user_prompt: str,
        response: str,
        turns: int,
        tool_calls: int,
        finish_reason: str,
        usage_total: dict[str, int],
        warnings: list[str],
        elapsed_ms: int,
        started_at: datetime,
    ) -> None:
        """Write run.md + response.md for a tools-mode invocation.

        ``transcript.json`` is owned by the runtime (so it survives crashes),
        but we cross-reference it from the envelope for the UI.
        """
        envelope = (
            "---\n"
            f"run_id: {run_id}\n"
            f"skill: {skill_name}\n"
            f"workspace: {workspace}\n"
            f"runtime: tools\n"
            f"created_at: {started_at.isoformat()}\n"
            f"elapsed_ms: {elapsed_ms}\n"
            f"turns: {turns}\n"
            f"tool_calls: {tool_calls}\n"
            f"finish_reason: {finish_reason}\n"
            f"prompt_tokens: {usage_total.get('prompt_tokens', 0)}\n"
            f"completion_tokens: {usage_total.get('completion_tokens', 0)}\n"
            f"total_tokens: {usage_total.get('total_tokens', 0)}\n"
            f"response_chars: {len(response)}\n"
            "---\n\n"
            "# Skill Run (tools mode)\n\n"
            "## User Prompt\n\n"
            f"{user_prompt.strip() or '(skill defaults)'}\n\n"
            "## Warnings\n\n"
            + ("\n".join(f"- {w}" for w in warnings) if warnings else "- (none)")
            + "\n\n## See also\n\n"
            "- `response.md` — final assistant message\n"
            "- `transcript.json` — full turn-by-turn record (tool calls + results)\n"
            "- `tool_outputs/` — raw stdout/stderr from `run_script` calls\n"
            "- `artifacts/` — files the skill wrote with `write_file`\n"
        )
        (run_dir / "run.md").write_text(envelope, encoding="utf-8")
        (run_dir / "response.md").write_text(response or "", encoding="utf-8")

    @staticmethod
    def _compose_prompt(
        skill: Skill, workspace: str, user_prompt: str, payload_json: str
    ) -> str:
        """Compose the final LLM prompt: instructions + workspace + user ask.

        The Workspace Briefing Book block (Phase 1.5 + 1.6) packages four things:

        * ``entities``           — typed entity buckets, each item carries the
                                    ``source_chunks`` IDs that produced it.
        * ``source_chunks``      — verbatim RFP text the model MUST quote from
                                    (never paraphrase) when citing requirements,
                                    proposal_instruction items (Section L or
                                    equivalent), evaluation_factor items
                                    (Section M or equivalent), deliverables, or
                                    clauses.
        * ``relationships``      — typed KG edges between the entities.
        * ``retrieval_metadata`` — Phase 1.6 provenance: tells the model whether
                                    the briefing book was query-targeted (chat-
                                    grade hybrid retrieval) or a bulk slice, and
                                    how many entities/chunks the retriever ranked
                                    as relevant. The model uses this to decide
                                    when to emit `GAP` for out-of-coverage asks.

        Citation discipline is enforced in the rendered envelope so every
        skill inherits the same source-of-truth contract.
        """
        return (
            f"# Agent Skill: {skill.name} ({skill.frontmatter.version})\n"
            f"Active workspace: {workspace}\n\n"
            "## Skill Instructions\n"
            f"{skill.body_md.strip()}\n\n"
            "## Workspace Briefing Book (JSON)\n"
            "This briefing book is the authoritative source of truth for the "
            "active RFP workspace. It contains four sections:\n"
            "  * `entities`           — typed entities (each carries `source_chunks`)\n"
            "  * `source_chunks`      — verbatim RFP text blocks (quote from these)\n"
            "  * `relationships`      — typed KG edges between entities\n"
            "  * `retrieval_metadata` — how this slice was selected (chat-grade\n"
            "    hybrid retrieval vs. bulk fallback); use it to gauge coverage.\n\n"
            "### Citation Discipline (MANDATORY)\n"
            "When you reference a requirement, deliverable, clause, "
            "`proposal_instruction` (UCF Section L or equivalent — e.g. an "
            "\"Instructions to Offerors\" section in a FAR 16 task order, FOPR, "
            "BPA call, OTA, or agency-specific format), `evaluation_factor` "
            "(UCF Section M or equivalent — e.g. \"Evaluation Criteria\", "
            "adjectival rating scheme, or LPTA basis), or any other RFP "
            "obligation:\n"
            "  1. **Quote verbatim** from the matching `source_chunks[*].content` — "
            "never paraphrase the RFP wording.\n"
            "  2. **Cite the chunk_id inline** in the form `[chunk-xxxxxxxx]` so "
            "the reader can trace any claim back to the source document.\n"
            "  3. If a needed source chunk is missing from the briefing book, "
            "emit a `GAP` marker rather than fabricating language.\n"
            "  4. Use the `relationships` block to confirm "
            "`proposal_instruction` ↔ `evaluation_factor` ↔ `requirement` "
            "traceability — do not invent links the KG does not show.\n\n"
            "### Coverage Discipline (Phase 1.6)\n"
            "The briefing book was assembled by chat-grade hybrid retrieval over "
            "the user request + skill description. Treat it as the *complete* "
            "evidence set for this invocation:\n"
            "  * Do **not** invent entities, factors, requirements, deliverables, "
            "or clauses that are absent from the briefing book.\n"
            "  * **This solicitation may use UCF or non-UCF format.** Map to the "
            "actual `proposal_instruction` and `evaluation_factor` entities "
            "regardless of section heading. Only emit `GAP` when no matching "
            "instruction or evaluation criterion exists *anywhere* in the "
            "briefing book — never because the entity lacks a literal \"Section "
            "L\" or \"Section M\" label. Many federal task orders, FOPRs, BPA "
            "calls, and OTAs put instructions inline in the PWS or in named "
            "attachments.\n"
            "  * If the user asks about a topic that is not represented in the "
            "`entities` / `source_chunks` blocks (check `retrieval_metadata` for "
            "coverage signals like low `matched_entities`), say so explicitly with "
            "`GAP: insufficient retrieval coverage for <topic>` instead of "
            "substituting unrelated content from another factor or section.\n"
            "  * Stay inside the slice. If the user asks for the small business "
            "participation outline, do not bleed in cybersecurity, transition, or "
            "other factors unless the briefing book actually surfaces them.\n\n"
            "```json\n"
            f"{payload_json}\n"
            "```\n\n"
            "## User Request\n"
            f"{user_prompt.strip() if user_prompt.strip() else '(use skill defaults)'}\n\n"
            "## Output\n"
            "Follow the skill's Output Contract section exactly. If a JSON "
            "envelope is specified, return only the JSON envelope. Inline "
            "chunk-ID citations are required wherever you quote RFP text.\n"
        )

    # ---- Run persistence ----------------------------------------------

    @staticmethod
    def _runs_root(workspace_root: Path, skill_name: str) -> Path:
        return workspace_root / "skill_runs" / skill_name

    @staticmethod
    def _is_safe_run_id(run_id: str) -> bool:
        return bool(re.match(r"^[0-9]{8}_[0-9]{6}_[a-z0-9_-]+$", run_id))

    def _persist_run(
        self,
        *,
        workspace_root: Path,
        skill_name: str,
        workspace: str,
        user_prompt: str,
        composed_prompt: str,
        response: str,
        entities_used: list[str],
        warnings: list[str],
        elapsed_ms: int,
        started_at: datetime,
    ) -> tuple[str, str]:
        """Write run.md (envelope) + response.md (raw output) + prompt.md (composed prompt).

        Layout:
            <workspace_root>/skill_runs/<skill_name>/<YYYYMMDD_HHMMSS_slug>/
                ├── run.md       — frontmatter + metadata + user prompt + warnings
                ├── response.md  — raw LLM response (the "product")
                ├── prompt.md    — full composed prompt (debug/repro)
                └── artifacts/   — reserved for future renderers (XLSX, PPTX, …)
        """
        ts = started_at.strftime("%Y%m%d_%H%M%S")
        slug = _slugify_for_filename(user_prompt) or "run"
        run_id = f"{ts}_{slug}"
        run_dir = self._runs_root(workspace_root, skill_name) / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "artifacts").mkdir(exist_ok=True)

        envelope = (
            "---\n"
            f"run_id: {run_id}\n"
            f"skill: {skill_name}\n"
            f"workspace: {workspace}\n"
            f"created_at: {started_at.isoformat()}\n"
            f"elapsed_ms: {elapsed_ms}\n"
            f"entities_used: [{', '.join(entities_used)}]\n"
            f"response_chars: {len(response)}\n"
            "---\n\n"
            "# Skill Run\n\n"
            "## User Prompt\n\n"
            f"{user_prompt.strip() or '(skill defaults)'}\n\n"
            "## Warnings\n\n"
            + ("\n".join(f"- {w}" for w in warnings) if warnings else "- (none)")
            + "\n\n## See also\n\n"
            "- `response.md` — raw LLM response\n"
            "- `prompt.md` — full composed prompt sent to the model\n"
            "- `artifacts/` — rendered files (when renderers are wired)\n"
        )
        (run_dir / "run.md").write_text(envelope, encoding="utf-8")
        (run_dir / "response.md").write_text(response, encoding="utf-8")
        (run_dir / "prompt.md").write_text(composed_prompt, encoding="utf-8")
        return run_id, str(run_dir.resolve())

    def list_runs(
        self, workspace_root: Path, skill_name: Optional[str] = None, limit: int = 50
    ) -> list[dict[str, Any]]:
        """List persisted skill runs, newest first.

        If ``skill_name`` is None, walks every skill under
        ``<workspace_root>/skill_runs/``.
        """
        base = workspace_root / "skill_runs"
        if not base.is_dir():
            return []
        targets = (
            [base / skill_name] if skill_name else [p for p in base.iterdir() if p.is_dir()]
        )
        runs: list[dict[str, Any]] = []
        for skill_root in targets:
            if not skill_root.is_dir():
                continue
            for run_dir in skill_root.iterdir():
                if not run_dir.is_dir():
                    continue
                envelope = run_dir / "run.md"
                response_path = run_dir / "response.md"
                if not envelope.exists():
                    continue
                meta = _parse_run_envelope(envelope.read_text(encoding="utf-8"))
                meta["run_id"] = meta.get("run_id") or run_dir.name
                meta["skill"] = meta.get("skill") or skill_root.name
                if response_path.exists():
                    try:
                        meta["response_chars"] = response_path.stat().st_size
                    except OSError:
                        pass
                runs.append(meta)
        runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return runs[:limit]

    def get_run(
        self, workspace_root: Path, skill_name: str, run_id: str
    ) -> Optional[dict[str, Any]]:
        """Return the full content of a single persisted run, or None."""
        if not self._is_safe_run_id(run_id):
            return None
        run_dir = self._runs_root(workspace_root, skill_name) / run_id
        if not run_dir.is_dir():
            return None
        envelope_path = run_dir / "run.md"
        response_path = run_dir / "response.md"
        prompt_path = run_dir / "prompt.md"
        meta = (
            _parse_run_envelope(envelope_path.read_text(encoding="utf-8"))
            if envelope_path.exists()
            else {}
        )
        artifacts: list[dict[str, str]] = []
        artifacts_dir = run_dir / "artifacts"
        if artifacts_dir.is_dir():
            for p in sorted(artifacts_dir.iterdir()):
                if p.is_file():
                    artifacts.append({
                        "name": p.name,
                        "size": str(p.stat().st_size),
                        "mime": resolve_artifact_mime(p.name),
                    })
        # Tools-mode runs persist a structured transcript (assistant turns +
        # tool calls + tool results) and may write tool_outputs/* sidecar files.
        # Surface both so the UI drawer can replay the run for grounding audit.
        transcript: list[dict[str, Any]] = []
        transcript_path = run_dir / "transcript.json"
        if transcript_path.exists():
            try:
                loaded = json.loads(transcript_path.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    transcript = loaded
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Unreadable transcript at %s: %s", transcript_path, exc)
        tool_outputs: list[dict[str, str]] = []
        tool_outputs_dir = run_dir / "tool_outputs"
        if tool_outputs_dir.is_dir():
            for p in sorted(tool_outputs_dir.iterdir()):
                if p.is_file():
                    tool_outputs.append({"name": p.name, "size": str(p.stat().st_size)})
        return {
            "run_id": run_id,
            "skill": skill_name,
            "run_dir": str(run_dir.resolve()),
            "metadata": meta,
            "response": response_path.read_text(encoding="utf-8")
            if response_path.exists()
            else "",
            "prompt": prompt_path.read_text(encoding="utf-8")
            if prompt_path.exists()
            else "",
            "artifacts": artifacts,
            "transcript": transcript,
            "tool_outputs": tool_outputs,
        }

    def delete_run(
        self, workspace_root: Path, skill_name: str, run_id: str
    ) -> bool:
        if not self._is_safe_run_id(run_id):
            return False
        run_dir = self._runs_root(workspace_root, skill_name) / run_id
        if not run_dir.is_dir():
            return False
        shutil.rmtree(run_dir, ignore_errors=True)
        return not run_dir.exists()

    def list_deliverables(
        self, workspace_root: Path, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Flatten every artifact across every skill run into one feed.

        Walks ``<workspace_root>/skill_runs/<skill>/<run_id>/artifacts/*`` and
        emits one row per file. Pure index over the Phase 3 layout — no new
        on-disk schema. Powers the Studio sidebar entry (Phase 6a).

        Each row carries enough to render a table row + deep-link back to the
        originating run drawer:

            {
                "skill":      <skill name>,
                "run_id":     <YYYYMMDD_HHMMSS_slug>,
                "filename":   <basename>,
                "mime":       <mimetype or None>,
                "size":       <bytes>,
                "created_at": <ISO timestamp from run envelope, or file mtime>,
                "title":      <run envelope title, or None>,
                "ext":        <lowercase extension without dot, or "">,
            }

        Sorted newest-first by ``created_at``. Capped at ``limit`` rows.
        """
        import mimetypes as _mt
        from datetime import datetime as _dt, timezone as _tz

        base = workspace_root / "skill_runs"
        if not base.is_dir():
            return []

        rows: list[dict[str, Any]] = []
        for skill_root in base.iterdir():
            if not skill_root.is_dir():
                continue
            skill_name = skill_root.name
            for run_dir in skill_root.iterdir():
                if not run_dir.is_dir() or not self._is_safe_run_id(run_dir.name):
                    continue
                run_id = run_dir.name
                artifacts_dir = run_dir / "artifacts"
                if not artifacts_dir.is_dir():
                    continue

                # Pull created_at + title from the run envelope (cheap parse).
                envelope_path = run_dir / "run.md"
                meta: dict[str, Any] = {}
                if envelope_path.exists():
                    try:
                        meta = _parse_run_envelope(
                            envelope_path.read_text(encoding="utf-8")
                        )
                    except Exception:  # noqa: BLE001
                        meta = {}
                created_at = meta.get("created_at") or ""
                title = meta.get("title")  # optional; envelope may not carry one

                for artifact in sorted(artifacts_dir.iterdir()):
                    if not artifact.is_file():
                        continue
                    try:
                        stat = artifact.stat()
                    except OSError:
                        continue
                    mime = resolve_artifact_mime(artifact.name)
                    ext = artifact.suffix.lstrip(".").lower()
                    rows.append(
                        {
                            "skill": skill_name,
                            "run_id": run_id,
                            "filename": artifact.name,
                            "mime": mime,
                            "size": stat.st_size,
                            "created_at": created_at
                            or _dt.fromtimestamp(
                                stat.st_mtime, tz=_tz.utc
                            ).isoformat(),
                            "title": title,
                            "ext": ext,
                        }
                    )

        rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return rows[:limit]

    def get_artifact_path(
        self,
        workspace_root: Path,
        skill_name: str,
        run_id: str,
        filename: str,
    ) -> Optional[Path]:
        """Resolve an artifact filename inside a run's artifacts/ folder.

        Defends against path traversal: rejects unsafe run IDs, rejects
        filenames containing path separators or '..', and verifies the
        resolved path is still under the artifacts directory. Returns None
        if any check fails or the file does not exist.
        """
        if not self._is_safe_run_id(run_id):
            return None
        if not filename or "/" in filename or "\\" in filename or filename in (".", ".."):
            return None
        artifacts_dir = (
            self._runs_root(workspace_root, skill_name) / run_id / "artifacts"
        ).resolve()
        if not artifacts_dir.is_dir():
            return None
        candidate = (artifacts_dir / filename).resolve()
        try:
            candidate.relative_to(artifacts_dir)
        except ValueError:
            return None
        if not candidate.is_file():
            return None
        return candidate

    # ---- Ledger persistence -------------------------------------------

    def _load_ledger(self) -> None:
        if not self.ledger_path.exists():
            self._ledger = {}
            return
        try:
            self._ledger = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Skills ledger unreadable, resetting: %s", exc)
            self._ledger = {}

    def _save_ledger(self) -> None:
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.ledger_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._ledger, indent=2), encoding="utf-8")
        tmp.replace(self.ledger_path)

    def _record_install(self, name: str, url: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._ledger[name] = {
            "source": "installed",
            "source_url": url,
            "installed_at": now,
            "last_invoked_at": "",
        }
        self._save_ledger()

    def _touch_invocation(self, name: str) -> None:
        entry = self._ledger.setdefault(
            name, {"source": "builtin", "source_url": "", "installed_at": ""}
        )
        entry["last_invoked_at"] = datetime.now(timezone.utc).isoformat()
        try:
            self._save_ledger()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to persist skill invocation timestamp: %s", exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def _slugify_for_filename(text: str, max_len: int = 32) -> str:
    """Lowercase + non-alnum→underscore + length cap. Empty input → empty string."""
    if not text:
        return ""
    cleaned = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return cleaned[:max_len].rstrip("_")


def _parse_run_envelope(text: str) -> dict[str, Any]:
    """Extract the YAML-ish frontmatter from a run.md envelope."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, Any] = {}
    for raw in lines[1:]:
        if raw.strip() == "---":
            break
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*)\s*:\s*(.*)$", raw)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "elapsed_ms" or key == "response_chars":
            try:
                out[key] = int(val)
                continue
            except ValueError:
                pass
        if key == "entities_used" and val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            out[key] = [t.strip() for t in inner.split(",") if t.strip()] if inner else []
            continue
        out[key] = val
    # Pull a short prompt preview from the body.
    try:
        body_start = text.find("\n## User Prompt\n")
        if body_start >= 0:
            tail = text[body_start + len("\n## User Prompt\n") :].strip()
            preview = tail.split("\n## ", 1)[0].strip()
            out["prompt_preview"] = (preview[:160] + "…") if len(preview) > 160 else preview
    except Exception:  # noqa: BLE001
        pass
    return out


def _slug_from_github_url(url: str) -> str:
    """Derive a default skill slug from a GitHub repo URL."""
    tail = url.rstrip("/").rsplit("/", 1)[-1]
    if tail.endswith(".git"):
        tail = tail[:-4]
    slug = re.sub(r"[^a-z0-9_-]+", "-", tail.lower()).strip("-")
    return slug or "skill"


def _git_clone_shallow(url: str, target_dir: Path) -> None:
    """Run ``git clone --depth=1`` synchronously. Raises on non-zero exit."""
    cmd = ["git", "clone", "--depth=1", "--quiet", url, str(target_dir)]
    proc = subprocess.run(  # noqa: S603 — args are constructed from validated input
        cmd, capture_output=True, text=True, check=False, timeout=60
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git clone failed (exit {proc.returncode}): {proc.stderr.strip()}"
        )


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_SINGLETON: Optional[SkillManager] = None


def get_skill_manager() -> SkillManager:
    """Return the process-wide SkillManager, discovering on first use."""
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = SkillManager()
        _SINGLETON.discover()
    return _SINGLETON
