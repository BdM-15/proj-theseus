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
import time
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from lightrag.api.config import global_args

# query_func signature: (text, mode, history, stream, overrides) -> str | AsyncIterator[str]
# - history: list of {"role": "user"|"assistant", "content": str}
# - overrides: dict of QueryParam tunables (top_k, chunk_top_k, max_*_tokens,
#   enable_rerank, only_need_context, only_need_prompt, response_type, user_prompt)
#   plus an optional "min_rerank_score" applied to the LightRAG instance for the call.
# - stream=False returns awaitable str; stream=True returns awaitable AsyncIterator[str]
QueryFunc = Callable[
    [str, str, list[dict], bool, dict],
    Awaitable[Union[str, AsyncIterator[str]]],
]

# data_func signature: (text, mode, history, overrides) -> dict
# Returns LightRAG aquery_data shape: {status, message, data: {chunks, entities, relationships, references}}.
QueryDataFunc = Callable[
    [str, str, list[dict], dict],
    Awaitable[dict],
]

from src.core import get_settings
from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES
from src.server.chat_store import ChatStore
from src.server.chat_ui_routes import register_chat_ui_routes
from src.server.graph_snapshot import register_graph_routes
from src.server.mcp_ui_routes import register_mcp_ui_routes
from src.server.processing_log_routes import register_processing_log_routes
from src.server.prompt_library import PROMPT_LIBRARY
from src.server.rfp_intelligence import register_intelligence_routes
from src.server.query_settings import (
    QuerySettingsStore,
    register_query_settings_routes,
)
from src.server.skill_ui_routes import register_skill_ui_routes
from src.server.workspace_ui_routes import (
    register_workspace_ui_routes,
    safe_count_json_keys,
    self_restart as _self_restart,
    set_env_var as _set_env_var,
)

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
# Helpers
# ---------------------------------------------------------------------------

from src.utils.time_utils import now_local_iso as _now_local_iso


def _now_iso() -> str:
    """ISO timestamp in America/Chicago (CST/CDT)."""
    return _now_local_iso(timespec="seconds")


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _stack_versions() -> dict[str, Optional[str]]:
    """Read installed package versions for the engine stack. Cached at import."""
    global _STACK_CACHE  # noqa: PLW0603
    if _STACK_CACHE is not None:
        return _STACK_CACHE
    from importlib.metadata import PackageNotFoundError, version  # local

    out: dict[str, Optional[str]] = {}
    for key, dist in (
        ("lightrag", "lightrag-hku"),
        ("raganything", "raganything"),
        ("mineru", "mineru"),
        ("transformers", "transformers"),
    ):
        try:
            out[key] = version(dist)
        except PackageNotFoundError:
            try:
                out[key] = version(key)  # fall back to bare name
            except PackageNotFoundError:
                out[key] = None
    _STACK_CACHE = out
    return out


_STACK_CACHE: Optional[dict[str, Optional[str]]] = None


def _ui_chat_history_pairs() -> int:
    """Resolve the per-query conversation_history cap (in user+assistant pairs)."""
    try:
        return max(0, int(os.getenv("UI_CHAT_HISTORY_TURNS", "20")))
    except ValueError:
        return 20


def _gather_stats() -> dict[str, Any]:
    settings = get_settings()
    ws = _workspace_dir()
    inference_only_relationship_types = {"REQUIRES", "ENABLED_BY", "RESPONSIBLE_FOR"}
    return {
        "workspace": settings.workspace,
        "graph_storage": getattr(global_args, "graph_storage", "NetworkXStorage"),
        "working_dir": str(ws),
        "documents": safe_count_json_keys(ws / "kv_store_doc_status.json"),
        "entities": safe_count_json_keys(ws / "vdb_entities.json"),
        "relationships": safe_count_json_keys(ws / "vdb_relationships.json"),
        "chunks": safe_count_json_keys(ws / "vdb_chunks.json"),
        "chats": sum(1 for _ in _chats_dir().glob("*.json")),
        "chat": {
            # How many recent user+assistant pairs travel with each query.
            # Mirrored from UI_CHAT_HISTORY_TURNS so the chat header can render
            # an accurate "N turns in context" indicator.
            "history_pairs_cap": _ui_chat_history_pairs(),
        },
        "ontology": {
            "entity_type_count": len(VALID_ENTITY_TYPES),
            "relationship_type_count": len(VALID_RELATIONSHIP_TYPES),
            "extraction_relationship_type_count": len(
                VALID_RELATIONSHIP_TYPES - inference_only_relationship_types
            ),
        },
        "models": {
            "extraction": settings.extraction_llm_name,
            "reasoning": settings.reasoning_llm_name,
            "embedding": settings.embedding_model,
            "rerank": settings.rerank_model if settings.enable_rerank else None,
            "rerank_enabled": settings.enable_rerank,
        },
        "stack": _stack_versions(),
        "timestamp": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

LlmFunc = Callable[[str], Awaitable[str]]


def register_ui(
    app: FastAPI,
    query_func: QueryFunc,
    data_func: QueryDataFunc | None = None,
    llm_func: LlmFunc | None = None,
) -> None:
    """
    Register the Project Theseus UI routes on an existing FastAPI app.

    Args:
        app: The FastAPI app produced by lightrag.api.lightrag_server.create_app.
        query_func: Async callable (query_text, mode, history, stream, overrides)
                    -> str | AsyncIterator[str]. The conversation_history is a
                    list of {role, content} dicts; when stream=True the return
                    is an async iterator of token chunks.
        data_func: Optional async callable (query_text, mode, history, overrides)
                    -> dict that returns LightRAG aquery_data structured retrieval
                    (chunks/entities/relationships/references). Used by the chat
                    SSE endpoint to emit a `sources` event before streaming the
                    answer. If None, no sources event is emitted.
    """
    if not _STATIC_DIR.exists():
        logger.warning("UI static dir missing: %s — UI will not be mounted", _STATIC_DIR)
        return

    query_settings = QuerySettingsStore(
        workspace_dir=_workspace_dir,
        settings_provider=get_settings,
    )
    chat_store = ChatStore(
        workspace_dir=_workspace_dir,
        now=_now_iso,
        history_pairs=_ui_chat_history_pairs,
    )

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

    register_processing_log_routes(app)


    # ---- Prompt library ---------------------------------------------------
    @app.get("/api/ui/prompt-library", tags=["theseus-ui"])
    async def ui_prompt_library() -> JSONResponse:
        """Return the curated Shipley phase 4-6 suggested-prompt catalog."""
        return JSONResponse({"prompts": PROMPT_LIBRARY})

    register_chat_ui_routes(
        app,
        chat_store=chat_store,
        query_settings=query_settings,
        query_func=query_func,
        data_func=data_func,
        now=_now_iso,
    )

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

    register_intelligence_routes(app, workspace_dir=_workspace_dir)

    register_graph_routes(
        app,
        workspace_name=lambda: get_settings().workspace,
        graph_storage=lambda: getattr(global_args, "graph_storage", "") or "",
        working_dir=lambda: Path(global_args.working_dir),
    )

    register_workspace_ui_routes(
        app,
        workspace_name=lambda: get_settings().workspace,
        working_dir=lambda: Path(global_args.working_dir),
        graph_storage=lambda: getattr(global_args, "graph_storage", "") or "",
        set_env_var_func=_set_env_var,
        schedule_restart=lambda delay: asyncio.get_event_loop().call_later(
            delay, _self_restart
        ),
    )

    register_query_settings_routes(
        app,
        workspace_name=lambda: get_settings().workspace,
        store=query_settings,
    )

    register_skill_ui_routes(
        app,
        workspace_dir=_workspace_dir,
        data_func=data_func,
        llm_func=llm_func,
    )

    register_mcp_ui_routes(
        app,
        set_env_var=lambda key, value: _set_env_var(key, value),
        schedule_restart=lambda delay: asyncio.get_event_loop().call_later(
            delay, _self_restart
        ),
    )

    logger.info("✅ Project Theseus UI mounted at /ui (static: %s)", _STATIC_DIR)
