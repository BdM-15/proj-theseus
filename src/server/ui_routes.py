"""
Custom Project Theseus UI routes.

Mounts a single-page cyberpunk capture-management UI at /ui and exposes a
small set of JSON endpoints under /api/ui/* for things the upstream
LightRAG WebUI does not provide:

- Dashboard rollups
- File-based chat persistence (one JSON file per chat,
  rag_storage/<workspace>/chats/<chat_id>.json)
- Shipley phase 4-6 suggested-prompt library

All RAG/graph/document data continues to flow through the upstream
LightRAG endpoints (`/query`, `/graphs`, `/documents`, etc.) plus our
custom `/insert`, `/documents/upload`, and `/scan-rfp`. This module
intentionally adds zero new Python dependencies.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from lightrag.api.config import global_args
from pydantic import BaseModel, Field

from src.core import get_settings, reset_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
_STATIC_DIR = (_THIS_DIR.parent / "ui" / "static").resolve()


def _workspace_dir() -> Path:
    """Return the active workspace directory under rag_storage/."""
    settings = get_settings()
    return Path(global_args.working_dir) / settings.workspace


def _chats_dir() -> Path:
    """Return (and create) the chats persistence directory for this workspace."""
    folder = _workspace_dir() / "chats"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatCreate(BaseModel):
    title: str = Field(default="New chat", max_length=120)
    mode: str = Field(default="hybrid")
    rfp_context: Optional[str] = Field(default=None, max_length=200)


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    mode: Optional[str] = Field(default=None)
    rfp_context: Optional[str] = Field(default=None, max_length=200)


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)


class WorkspaceSwitch(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    create: bool = Field(default=False, description="Create the folder if it does not exist.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{6,64}$")
_SAFE_WS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_chat_id() -> str:
    return uuid.uuid4().hex[:16]


def _chat_path(chat_id: str) -> Path:
    if not _SAFE_ID.match(chat_id):
        raise HTTPException(status_code=400, detail="Invalid chat id")
    return _chats_dir() / f"{chat_id}.json"


def _read_chat(chat_id: str) -> dict[str, Any]:
    path = _chat_path(chat_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("Corrupt chat file %s: %s", path, exc)
        raise HTTPException(status_code=500, detail="Chat file corrupt") from exc


def _write_chat(chat: dict[str, Any]) -> None:
    path = _chat_path(chat["id"])
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(chat, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def _summary(chat: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": chat["id"],
        "title": chat.get("title", "Untitled"),
        "mode": chat.get("mode", "hybrid"),
        "rfp_context": chat.get("rfp_context"),
        "message_count": len(chat.get("messages", [])),
        "created_at": chat.get("created_at"),
        "updated_at": chat.get("updated_at"),
    }


# ---------------------------------------------------------------------------
# Suggested prompt library (Shipley phases 4-6)
# ---------------------------------------------------------------------------

_PROMPT_LIBRARY: list[dict[str, str]] = [
    # Phase 4 — Proposal Planning
    {"phase": "4", "category": "Compliance", "title": "Full L↔M Compliance Matrix",
     "prompt": "Generate a full Section L ↔ Section M compliance matrix for this RFP. For every Section L instruction, list the linked Section M evaluation criterion, the responsible proposal volume, page-limit constraints, and any unmatched items as gaps."},
    {"phase": "4", "category": "Compliance", "title": "Page-limit & format constraints",
     "prompt": "List every page limit, font, margin, file-format, and submission-mechanic constraint stated in Section L or anywhere else in the RFP. Cite the source clause for each."},
    {"phase": "4", "category": "Strategy", "title": "Win themes & discriminators",
     "prompt": "Identify candidate win themes, discriminators, and proof points implied by the RFP language. Map each to the customer priority or pain point it addresses, and to the evaluation factor it would influence."},
    # Phase 5 — Proposal Development
    {"phase": "5", "category": "Traceability", "title": "Requirements → Deliverables → BOE",
     "prompt": "Trace every shall/will requirement to its satisfying deliverable, performance standard, and workload metric. Flag any requirement with no satisfying deliverable as a coverage gap."},
    {"phase": "5", "category": "Writing", "title": "Volume outline (Shipley-aligned)",
     "prompt": "Produce a Shipley-aligned proposal volume outline. For each volume, list sections, page budgets derived from Section L, and the evaluation factors it must answer."},
    {"phase": "5", "category": "Writing", "title": "FAB chain for top discriminator",
     "prompt": "For the most defensible discriminator, write a Feature → Advantage → Benefit chain grounded in cited proof points and tied to the relevant evaluation factor."},
    {"phase": "5", "category": "Risk", "title": "Ghost competitor weaknesses",
     "prompt": "Identify language we can ghost to highlight likely competitor weaknesses without naming them, anchored in customer pain points and evaluation factors."},
    # Phase 6 — Post-submittal
    {"phase": "6", "category": "Review", "title": "Gap analysis vs Section M",
     "prompt": "Run a gap analysis: for each Section M evaluation factor and subfactor, list the proposal sections, deliverables, and proof points that respond to it. Highlight unanswered factors."},
    {"phase": "6", "category": "Review", "title": "Compliance review checklist",
     "prompt": "Generate a compliance review checklist a Pink/Red team can execute, organized by Section L instruction with pass/fail criteria from Section M."},
]


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _safe_count_json_keys(path: Path) -> int:
    """Count records in a LightRAG storage JSON file. Returns 0 on any error.

    Handles two on-disk shapes used by LightRAG:
    - kv_store_*.json: top-level dict keyed by record id -> count via len(dict)
    - vdb_*.json:      {"embedding_dim": N, "data": [...records...], "matrix": "..."}
                       -> count via len(data)

    Results are cached by (path, mtime, size) so the multi-MB vdb files are
    only re-read when they actually change.
    """
    try:
        if not path.exists():
            return 0
        st = path.stat()
        key = (str(path), st.st_mtime_ns, st.st_size)
        cached = _COUNT_CACHE.get(key)
        if cached is not None:
            return cached
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            inner = data.get("data")
            count = len(inner) if isinstance(inner, list) else len(data)
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 0
        # Drop any prior cached entries for this path before storing the new one
        for k in [k for k in _COUNT_CACHE if k[0] == str(path)]:
            _COUNT_CACHE.pop(k, None)
        _COUNT_CACHE[key] = count
        return count
    except Exception:
        return 0


_COUNT_CACHE: dict[tuple[str, int, int], int] = {}


def _gather_stats() -> dict[str, Any]:
    settings = get_settings()
    ws = _workspace_dir()
    return {
        "workspace": settings.workspace,
        "graph_storage": getattr(global_args, "graph_storage", "NetworkXStorage"),
        "working_dir": str(ws),
        "documents": _safe_count_json_keys(ws / "kv_store_doc_status.json"),
        "entities": _safe_count_json_keys(ws / "vdb_entities.json"),
        "relationships": _safe_count_json_keys(ws / "vdb_relationships.json"),
        "chunks": _safe_count_json_keys(ws / "vdb_chunks.json"),
        "chats": sum(1 for _ in _chats_dir().glob("*.json")),
        "models": {
            "extraction": settings.extraction_llm_name,
            "reasoning": settings.reasoning_llm_name,
            "embedding": settings.embedding_model,
        },
        "timestamp": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Workspace discovery & switching
# ---------------------------------------------------------------------------

def _discover_workspaces() -> list[dict[str, Any]]:
    """List candidate workspaces under the configured working_dir.

    A directory is considered a valid workspace if it contains at least one
    of the LightRAG storage signature files. We also report empty/new
    directories so the UI can show them.
    """
    root = Path(global_args.working_dir)
    if not root.exists():
        return []
    sig_files = ("kv_store_doc_status.json", "vdb_entities.json", "vdb_chunks.json")
    out: list[dict[str, Any]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        has_data = any((child / f).exists() for f in sig_files)
        out.append({
            "name": child.name,
            "has_data": has_data,
            "documents": _safe_count_json_keys(child / "kv_store_doc_status.json"),
            "entities": _safe_count_json_keys(child / "vdb_entities.json"),
            "chats": sum(1 for _ in (child / "chats").glob("*.json")) if (child / "chats").exists() else 0,
        })
    return out


def _set_env_var(key: str, value: str) -> None:
    """Update or append KEY=value in the project .env file (atomic)."""
    env_path = Path.cwd() / ".env"
    lines: list[str] = []
    found = False
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            stripped = raw.lstrip()
            if stripped.startswith(f"{key}=") and not stripped.startswith("#"):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(raw)
    if not found:
        lines.append(f"{key}={value}")
    tmp = env_path.with_suffix(".env.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(env_path)
    os.environ[key] = value
    reset_settings()


def _self_restart() -> None:
    """Re-exec the current python process with the same argv."""
    logger.warning("♻️  Re-execing process: %s %s", sys.executable, sys.argv)
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as exc:  # pragma: no cover
        logger.exception("Self-restart failed: %s", exc)
        os._exit(1)


# ---------------------------------------------------------------------------
# RFP Intelligence — L↔M matrix, traceability, coverage, gaps
# ---------------------------------------------------------------------------

def _load_vdb(name: str) -> list[dict[str, Any]]:
    """Load a vdb_*.json file's `data` array. Returns [] on any failure."""
    path = _workspace_dir() / name
    try:
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw.get("data") or []
    except Exception as exc:
        logger.warning("Failed reading %s: %s", path, exc)
        return []


def _split_keywords(value: Any) -> list[str]:
    """Relationship `keywords` is sometimes a comma/space-joined string."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip().upper() for v in value if v]
    return [tok.strip().upper() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()]


def _compute_intel() -> dict[str, Any]:
    """
    Build the RFP Intelligence rollup from the workspace's VDB JSON stores.

    Returns:
        {
            "lm_matrix":     [{instruction, evaluator, factor_id, ...}],
            "traceability":  [{requirement, deliverable, standard, metric}],
            "coverage":      [{factor, subfactors, instructions, deliverables, score}],
            "gaps":          {requirements_no_satisfaction: [...], factors_no_instruction: [...], deliverables_no_measure: [...]},
            "totals":        {entities, relationships, by_type: {...}},
        }
    """
    entities = _load_vdb("vdb_entities.json")
    relations = _load_vdb("vdb_relationships.json")

    # name → entity record (entity_id stored in `entity_name` or top-level keys)
    by_name: dict[str, dict[str, Any]] = {}
    for e in entities:
        name = e.get("entity_name") or e.get("entity_id") or e.get("__id__")
        if not name:
            continue
        by_name[str(name).strip()] = e

    # type buckets (lowercased entity_type)
    buckets: dict[str, list[str]] = {}
    for name, ent in by_name.items():
        t = (ent.get("entity_type") or "concept").lower()
        buckets.setdefault(t, []).append(name)

    # adjacency keyed by (src, tgt) → set of canonical relation types
    out_edges: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    in_edges: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for r in relations:
        s, t = r.get("src_id"), r.get("tgt_id")
        if not s or not t:
            continue
        types = _split_keywords(r.get("keywords") or r.get("relationship_type"))
        for rt in types:
            out_edges.setdefault(s, []).append((rt, t, r))
            in_edges.setdefault(t, []).append((rt, s, r))

    def _outgoing(name: str, rel: str) -> list[str]:
        return [t for (rt, t, _) in out_edges.get(name, []) if rt == rel]

    def _incoming(name: str, rel: str) -> list[str]:
        return [s for (rt, s, _) in in_edges.get(name, []) if rt == rel]

    def _summarize(name: str, n: int = 110) -> dict[str, Any]:
        ent = by_name.get(name) or {}
        desc = (ent.get("description") or ent.get("content") or "").strip().replace("\n", " ")
        return {
            "id": name,
            "type": (ent.get("entity_type") or "concept").lower(),
            "description": (desc[:n] + "…") if len(desc) > n else desc,
        }

    # --- L ↔ M matrix ----------------------------------------------------
    # Instructions GUIDES factors; factors EVALUATED_BY their evidence.
    # We surface: instruction → linked factor (or factor → guiding instruction).
    lm_rows: list[dict[str, Any]] = []
    instructions = sorted(buckets.get("proposal_instruction", []))
    for instr in instructions:
        guided = sorted(set(_outgoing(instr, "GUIDES") + _outgoing(instr, "EVALUATED_BY")))
        lm_rows.append({
            "instruction": _summarize(instr),
            "factors": [_summarize(f) for f in guided],
            "covered": bool(guided),
        })
    # Also surface factors with NO inbound instruction (gap signal)
    factor_names = sorted(set(buckets.get("evaluation_factor", []) + buckets.get("subfactor", [])))
    factor_rows: list[dict[str, Any]] = []
    for f in factor_names:
        guides = sorted(set(_incoming(f, "GUIDES") + _incoming(f, "EVALUATED_BY")))
        factor_rows.append({
            "factor": _summarize(f),
            "instructions": [_summarize(i) for i in guides],
            "covered": bool(guides),
        })

    # --- Traceability: requirement → deliverable → standard / metric -----
    trace_rows: list[dict[str, Any]] = []
    for req in sorted(buckets.get("requirement", [])):
        delivs = sorted(set(_outgoing(req, "SATISFIED_BY")))
        if not delivs:
            trace_rows.append({
                "requirement": _summarize(req),
                "deliverables": [],
                "standards": [],
                "metrics": [],
                "complete": False,
            })
            continue
        for d in delivs:
            stds = sorted(set(_outgoing(d, "MEASURED_BY")))
            mets = sorted(set(_outgoing(d, "TRACKED_BY") + _outgoing(d, "QUANTIFIES")))
            trace_rows.append({
                "requirement": _summarize(req),
                "deliverables": [_summarize(d)],
                "standards": [_summarize(s) for s in stds],
                "metrics": [_summarize(m) for m in mets],
                "complete": bool(stds or mets),
            })

    # --- Coverage heatmap by evaluation factor ---------------------------
    coverage_rows: list[dict[str, Any]] = []
    for f in sorted(buckets.get("evaluation_factor", [])):
        subs = sorted(set(_outgoing(f, "HAS_SUBFACTOR") + _outgoing(f, "CHILD_OF")))
        instrs = sorted(set(_incoming(f, "GUIDES")))
        # walk: factor → instruction → SATISFIED_BY deliverable
        delivs: set[str] = set()
        for i in instrs:
            for r in (by_name.get(i, {}),):  # placeholder
                pass
        # broader: any deliverable mentioning the factor via SUPPORTS / EVIDENCES / ADDRESSES
        for rel in ("SUPPORTS", "EVIDENCES", "ADDRESSES"):
            delivs.update(_incoming(f, rel))
        score = (1 if instrs else 0) + (1 if subs else 0) + (1 if delivs else 0)  # 0..3
        coverage_rows.append({
            "factor": _summarize(f),
            "subfactor_count": len(subs),
            "instruction_count": len(instrs),
            "evidence_count": len(delivs),
            "score": score,  # 0=red, 1=amber, 2=cyan, 3=lime
        })

    # --- Gaps -------------------------------------------------------------
    gaps_req: list[dict[str, Any]] = [
        _summarize(r) for r in sorted(buckets.get("requirement", []))
        if not _outgoing(r, "SATISFIED_BY")
    ]
    gaps_factor: list[dict[str, Any]] = [
        _summarize(f) for f in factor_names
        if not (_incoming(f, "GUIDES") or _incoming(f, "EVALUATED_BY"))
    ]
    gaps_deliv: list[dict[str, Any]] = [
        _summarize(d) for d in sorted(buckets.get("deliverable", []))
        if not (_outgoing(d, "MEASURED_BY") or _outgoing(d, "TRACKED_BY"))
    ]

    return {
        "generated_at": _now_iso(),
        "totals": {
            "entities": len(by_name),
            "relationships": len(relations),
            "by_type": {k: len(v) for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1]))},
        },
        "lm_matrix": {
            "instructions": lm_rows,
            "factors": factor_rows,
        },
        "traceability": trace_rows,
        "coverage": coverage_rows,
        "gaps": {
            "requirements_no_satisfaction": gaps_req,
            "factors_no_instruction": gaps_factor,
            "deliverables_no_measure": gaps_deliv,
        },
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

def register_ui(
    app: FastAPI,
    query_func: Callable[[str, str], Awaitable[str]],
) -> None:
    """
    Register the Project Theseus UI routes on an existing FastAPI app.

    Args:
        app: The FastAPI app produced by lightrag.api.lightrag_server.create_app.
        query_func: Async callable (query_text, mode) -> answer_text.
                    Typically rag_instance.lightrag.aquery.
    """
    if not _STATIC_DIR.exists():
        logger.warning("UI static dir missing: %s — UI will not be mounted", _STATIC_DIR)
        return

    # ---- Static SPA at /ui ------------------------------------------------
    app.mount(
        "/ui",
        StaticFiles(directory=str(_STATIC_DIR), html=True),
        name="theseus-ui",
    )

    # ---- Dashboard stats --------------------------------------------------
    @app.get("/api/ui/stats", tags=["theseus-ui"])
    async def ui_stats() -> JSONResponse:
        """Return dashboard rollup metrics for the active workspace."""
        return JSONResponse(_gather_stats())

    # ---- Prompt library ---------------------------------------------------
    @app.get("/api/ui/prompt-library", tags=["theseus-ui"])
    async def ui_prompt_library() -> JSONResponse:
        """Return the curated Shipley phase 4-6 suggested-prompt catalog."""
        return JSONResponse({"prompts": _PROMPT_LIBRARY})

    # ---- Chats: list/create ----------------------------------------------
    @app.get("/api/ui/chats", tags=["theseus-ui"])
    async def list_chats() -> JSONResponse:
        """List all saved chats for the active workspace, newest first."""
        items = []
        for path in _chats_dir().glob("*.json"):
            try:
                items.append(_summary(json.loads(path.read_text(encoding="utf-8"))))
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Skipping corrupt chat %s: %s", path, exc)
        items.sort(key=lambda c: c.get("updated_at") or "", reverse=True)
        return JSONResponse({"chats": items})

    @app.post("/api/ui/chats", tags=["theseus-ui"])
    async def create_chat(payload: ChatCreate) -> JSONResponse:
        """Create a new persistent chat session."""
        chat_id = _new_chat_id()
        now = _now_iso()
        chat = {
            "id": chat_id,
            "title": payload.title.strip() or "New chat",
            "mode": payload.mode,
            "rfp_context": payload.rfp_context,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        _write_chat(chat)
        return JSONResponse(_summary(chat), status_code=201)

    # ---- Chats: read/update/delete ---------------------------------------
    @app.get("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def get_chat(chat_id: str) -> JSONResponse:
        """Return full chat including all messages."""
        return JSONResponse(_read_chat(chat_id))

    @app.patch("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def update_chat(chat_id: str, payload: ChatUpdate) -> JSONResponse:
        """Rename a chat or update its mode / RFP context."""
        chat = _read_chat(chat_id)
        if payload.title is not None:
            chat["title"] = payload.title.strip() or chat["title"]
        if payload.mode is not None:
            chat["mode"] = payload.mode
        if payload.rfp_context is not None:
            chat["rfp_context"] = payload.rfp_context or None
        chat["updated_at"] = _now_iso()
        _write_chat(chat)
        return JSONResponse(_summary(chat))

    @app.delete("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def delete_chat(chat_id: str) -> JSONResponse:
        """Permanently delete a chat."""
        path = _chat_path(chat_id)
        if not path.exists():
            raise HTTPException(status_code=404, detail="Chat not found")
        path.unlink()
        return JSONResponse({"status": "deleted", "id": chat_id})

    # ---- Chats: send message (calls LightRAG /query under the hood) ------
    @app.post("/api/ui/chats/{chat_id}/messages", tags=["theseus-ui"])
    async def post_message(chat_id: str, payload: ChatMessageCreate) -> JSONResponse:
        """Append a user message, invoke RAG query, persist the assistant reply."""
        chat = _read_chat(chat_id)
        user_msg = {
            "role": "user",
            "content": payload.content,
            "ts": _now_iso(),
        }
        chat["messages"].append(user_msg)

        try:
            answer = await query_func(payload.content, chat.get("mode", "hybrid"))
        except Exception as exc:
            logger.exception("Query failed for chat %s: %s", chat_id, exc)
            answer = f"⚠️ Query failed: {exc}"

        assistant_msg = {
            "role": "assistant",
            "content": str(answer),
            "ts": _now_iso(),
            "mode": chat.get("mode", "hybrid"),
        }
        chat["messages"].append(assistant_msg)
        chat["updated_at"] = _now_iso()

        # Auto-title the chat from the first user prompt.
        if chat.get("title") in (None, "", "New chat") and len(chat["messages"]) <= 2:
            chat["title"] = (payload.content[:60] + "…") if len(payload.content) > 60 else payload.content

        _write_chat(chat)
        return JSONResponse({"user": user_msg, "assistant": assistant_msg, "chat": _summary(chat)})

    # ---- Entity → source chunks (for KG explorer click-through) ----------
    @app.get("/api/ui/entity/{name}/chunks", tags=["theseus-ui"])
    async def entity_chunks(name: str, limit: int = 8) -> JSONResponse:
        """Return the source text chunks that mention an entity, for KG drill-down."""
        ws = _workspace_dir()
        ec_path = ws / "kv_store_entity_chunks.json"
        tc_path = ws / "kv_store_text_chunks.json"
        if not ec_path.exists() or not tc_path.exists():
            return JSONResponse({"entity": name, "chunks": []})
        try:
            entity_chunks_map = json.loads(ec_path.read_text(encoding="utf-8"))
            text_chunks = json.loads(tc_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed reading chunk stores: %s", exc)
            return JSONResponse({"entity": name, "chunks": []})

        # entity_chunks_map can key by raw name or by quoted variants
        chunk_ids = (
            entity_chunks_map.get(name)
            or entity_chunks_map.get(name.strip('"'))
            or []
        )
        if isinstance(chunk_ids, dict):
            chunk_ids = list(chunk_ids.keys())

        out = []
        for cid in list(chunk_ids)[:limit]:
            chunk = text_chunks.get(cid) or {}
            content = chunk.get("content") or chunk.get("text") or ""
            out.append({
                "chunk_id": cid,
                "file_path": chunk.get("file_path") or chunk.get("full_doc_id"),
                "chunk_order_index": chunk.get("chunk_order_index"),
                "snippet": content[:600] + ("…" if len(content) > 600 else ""),
            })
        return JSONResponse({"entity": name, "chunks": out})

    # ---- RFP Intelligence (L↔M matrix, traceability, coverage, gaps) -----
    @app.get("/api/ui/intel/summary", tags=["theseus-ui"])
    async def intel_summary() -> JSONResponse:
        """Compute L↔M matrix, traceability chains, factor coverage, and gaps."""
        return JSONResponse(_compute_intel())

    # ---- Workspaces (list / switch / restart) ------------------------------
    @app.get("/api/ui/workspaces", tags=["theseus-ui"])
    async def list_workspaces() -> JSONResponse:
        """List discovered workspace directories under rag_storage/."""
        return JSONResponse({
            "active": get_settings().workspace,
            "workspaces": _discover_workspaces(),
        })

    @app.post("/api/ui/workspaces/switch", tags=["theseus-ui"])
    async def switch_workspace(payload: WorkspaceSwitch) -> JSONResponse:
        """Persist WORKSPACE=<name> in .env and schedule a graceful self-restart.

        The server returns immediately and re-execs the python process ~750ms
        later so the response can flush. The browser polls /health and will
        reconnect when the new process is up.
        """
        name = payload.name.strip()
        if not _SAFE_WS.match(name):
            raise HTTPException(400, "Invalid workspace name (use alphanumerics, _, -)")
        existing = {w["name"] for w in _discover_workspaces()}
        if not payload.create and name not in existing:
            raise HTTPException(404, f"Workspace '{name}' does not exist")
        # Create folder if requested
        ws_root = Path(global_args.working_dir)
        ws_root.mkdir(parents=True, exist_ok=True)
        (ws_root / name).mkdir(parents=True, exist_ok=True)
        # Persist
        try:
            _set_env_var("WORKSPACE", name)
        except Exception as exc:
            raise HTTPException(500, f"Failed updating .env: {exc}") from exc
        # Schedule restart
        asyncio.get_event_loop().call_later(0.75, _self_restart)
        logger.warning("🔄 Workspace switch requested → '%s'. Restarting server…", name)
        return JSONResponse({
            "status": "restarting",
            "workspace": name,
            "message": "Server is restarting. The UI will reconnect automatically.",
        })

    logger.info("✅ Project Theseus UI mounted at /ui (static: %s)", _STATIC_DIR)
