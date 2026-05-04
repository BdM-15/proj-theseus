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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from lightrag.api.config import global_args
from pydantic import BaseModel, Field

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

from src.core import get_settings, reset_settings
from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES
from src.server.chat_store import ChatStore
from src.server.graph_snapshot import register_graph_routes
from src.server.mcp_ui_routes import register_mcp_ui_routes
from src.server.processing_log_routes import register_processing_log_routes
from src.server.prompt_library import PROMPT_LIBRARY
from src.server.rfp_intelligence import register_intelligence_routes
from src.server.query_settings import (
    QuerySettingsStore,
    register_query_settings_routes,
)
from src.server.reasoning_filter import ThinkStripper, strip_think
from src.server.skill_ui_routes import register_skill_ui_routes

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
    mode: str = Field(default="mix")
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


class WorkspaceDeleteScope(BaseModel):
    """Which buckets of a workspace to delete. At least one must be true."""

    neo4j: bool = Field(default=False, description="Delete the workspace's Neo4j subgraph.")
    rag_storage: bool = Field(default=False, description="Delete rag_storage/<ws>/ (KV stores, VDBs, chats, log).")
    inputs: bool = Field(default=False, description="Delete inputs/<ws>/ source documents (irrecoverable).")


class WipeAllScope(BaseModel):
    """Clean-slate wipe. Requires the literal confirmation phrase."""

    neo4j: bool = Field(default=False)
    rag_storage: bool = Field(default=False)
    inputs: bool = Field(default=False)
    confirm: str = Field(..., description="Must equal 'DELETE ALL'.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_WS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


from src.utils.time_utils import now_local_iso as _now_local_iso


def _now_iso() -> str:
    """ISO timestamp in America/Chicago (CST/CDT)."""
    return _now_local_iso(timespec="seconds")


# Maximum characters per chunk preview shipped to the UI. Keeps the SSE event
# small and the chat-file footprint reasonable on long conversations.
_SOURCE_PREVIEW_CHARS = 800


def _trim_sources(data: dict) -> dict:
    """Project LightRAG aquery_data['data'] into a compact UI payload.

    Keeps only the fields the Sources panel needs and truncates chunk text to
    `_SOURCE_PREVIEW_CHARS`. The full chunk content already lives in LightRAG
    storage; the UI only needs enough to preview and link back.
    """
    chunks_in = data.get("chunks") or []
    refs_in = data.get("references") or []
    ents_in = data.get("entities") or []
    rels_in = data.get("relationships") or []

    chunks_out = []
    for c in chunks_in:
        if not isinstance(c, dict):
            continue
        content = str(c.get("content") or "")
        truncated = len(content) > _SOURCE_PREVIEW_CHARS
        preview = content[:_SOURCE_PREVIEW_CHARS] + ("\u2026" if truncated else "")
        chunks_out.append(
            {
                "reference_id": str(c.get("reference_id") or ""),
                "chunk_id": str(c.get("chunk_id") or ""),
                "file_path": str(c.get("file_path") or ""),
                "preview": preview,
                "char_count": len(content),
                "truncated": truncated,
            }
        )

    refs_out = [
        {
            "reference_id": str(r.get("reference_id") or ""),
            "file_path": str(r.get("file_path") or ""),
        }
        for r in refs_in
        if isinstance(r, dict)
    ]

    return {
        "chunks": chunks_out,
        "references": refs_out,
        "counts": {
            "chunks": len(chunks_out),
            "entities": len(ents_in),
            "relationships": len(rels_in),
            "references": len(refs_out),
        },
    }


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
        "documents": _safe_count_json_keys(ws / "kv_store_doc_status.json"),
        "entities": _safe_count_json_keys(ws / "vdb_entities.json"),
        "relationships": _safe_count_json_keys(ws / "vdb_relationships.json"),
        "chunks": _safe_count_json_keys(ws / "vdb_chunks.json"),
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

    # ---- Chats: list/create ----------------------------------------------
    @app.get("/api/ui/chats", tags=["theseus-ui"])
    async def list_chats() -> JSONResponse:
        """List all saved chats for the active workspace, newest first."""
        return JSONResponse({"chats": chat_store.list_summaries()})

    @app.post("/api/ui/chats", tags=["theseus-ui"])
    async def create_chat(payload: ChatCreate) -> JSONResponse:
        """Create a new persistent chat session."""
        chat = chat_store.create(
            title=payload.title,
            mode=payload.mode,
            rfp_context=payload.rfp_context,
        )
        return JSONResponse(chat_store.summary(chat), status_code=201)

    # ---- Chats: read/update/delete ---------------------------------------
    @app.get("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def get_chat(chat_id: str) -> JSONResponse:
        """Return full chat including all messages."""
        return JSONResponse(chat_store.read(chat_id))

    @app.patch("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def update_chat(chat_id: str, payload: ChatUpdate) -> JSONResponse:
        """Rename a chat or update its mode / RFP context."""
        chat = chat_store.update(
            chat_id,
            title=payload.title,
            mode=payload.mode,
            rfp_context=payload.rfp_context,
        )
        return JSONResponse(chat_store.summary(chat))

    @app.delete("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def delete_chat(chat_id: str) -> JSONResponse:
        """Permanently delete a chat."""
        chat_store.delete(chat_id)
        return JSONResponse({"status": "deleted", "id": chat_id})

    # ---- Chats: send message (calls LightRAG /query under the hood) ------
    # LightRAG itself does NOT trim conversation_history (operate.py forwards
    # it raw to the LLM), so we cap here. The cap lives in
    # ``_ui_chat_history_pairs`` and is also surfaced via /api/ui/stats so the
    # chat header can render an accurate "N turns in context" indicator.

    @app.post("/api/ui/chats/{chat_id}/messages", tags=["theseus-ui"])
    async def post_message(chat_id: str, payload: ChatMessageCreate) -> JSONResponse:
        """Append a user message, invoke RAG query, persist the assistant reply."""
        chat = chat_store.read(chat_id)
        user_msg = {
            "role": "user",
            "content": payload.content,
            "ts": _now_iso(),
        }
        chat["messages"].append(user_msg)

        history = chat_store.build_history(chat, exclude_last=True)
        overrides = query_settings.build_overrides()
        try:
            answer = await query_func(
                payload.content, chat.get("mode", "mix"), history, False, overrides
            )
        except Exception as exc:
            logger.exception("Query failed for chat %s: %s", chat_id, exc)
            answer = f"⚠️ Query failed: {exc}"

        assistant_msg = {
            "role": "assistant",
            "content": strip_think(str(answer)),
            "ts": _now_iso(),
            "mode": chat.get("mode", "mix"),
        }
        chat["messages"].append(assistant_msg)
        chat["updated_at"] = _now_iso()

        # Auto-title the chat from the first user prompt.
        if chat.get("title") in (None, "", "New chat") and len(chat["messages"]) <= 2:
            chat_store.maybe_autotitle(chat, payload.content)

        chat_store.write(chat)
        return JSONResponse({
            "user": user_msg,
            "assistant": assistant_msg,
            "chat": chat_store.summary(chat),
        })

    # ---- Chats: streaming variant (Server-Sent Events) -------------------
    @app.post("/api/ui/chats/{chat_id}/messages/stream", tags=["theseus-ui"])
    async def post_message_stream(chat_id: str, payload: ChatMessageCreate):
        """Stream the assistant reply token-by-token via SSE.

        Event format (one SSE event per chunk):
            event: token
            data: {"text": "..."}

        Final event when complete:
            event: done
            data: {"assistant": {...full message...}, "chat": {...summary...}}

        Error event (terminal):
            event: error
            data: {"message": "..."}
        """
        chat = chat_store.read(chat_id)
        user_msg = {
            "role": "user",
            "content": payload.content,
            "ts": _now_iso(),
        }
        chat["messages"].append(user_msg)
        # Persist the user turn immediately so a dropped connection doesn't lose it.
        if chat.get("title") in (None, "", "New chat") and len(chat["messages"]) <= 1:
            chat_store.maybe_autotitle(chat, payload.content)
        chat_store.write(chat)

        history = chat_store.build_history(chat, exclude_last=True)
        mode = chat.get("mode", "mix")
        overrides = query_settings.build_overrides()

        async def event_stream():
            # SSE preamble keeps proxies from buffering and signals the client
            # that the stream is alive even before the first model token.
            yield "event: open\ndata: {}\n\n"
            # Tell the UI we're working on retrieval/rerank. LightRAG's aquery
            # does retrieval + rerank + first-token-prefill *before* it returns
            # the iterator, so this status covers that whole prep window.
            yield (
                "event: status\ndata: "
                + json.dumps({"phase": "retrieving", "label": "Retrieving context\u2026"})
                + "\n\n"
            )
            collected: list[str] = []
            stripper = ThinkStripper()
            t_start = time.perf_counter()
            t_first_token: float | None = None
            token_count = 0
            error_message: str | None = None
            sources_payload: dict | None = None
            try:
                # Pre-flight: fetch retrieved chunks/entities/relationships so
                # the UI can render a Sources panel and wire the inline citation
                # chips to actual source content. Failures here are non-fatal —
                # the answer still streams normally.
                if data_func is not None and mode != "bypass":
                    try:
                        data_result = await data_func(payload.content, mode, history, overrides)
                        if isinstance(data_result, dict) and data_result.get("status") == "success":
                            sources_payload = _trim_sources(data_result.get("data", {}))
                            yield (
                                "event: sources\ndata: "
                                + json.dumps(sources_payload)
                                + "\n\n"
                            )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Sources pre-flight failed for chat %s: %s", chat_id, exc
                        )
                result = await query_func(payload.content, mode, history, True, overrides)
                retrieve_ms = int((time.perf_counter() - t_start) * 1000)
                # Iterator is in hand \u2014 LLM has started generating.
                yield (
                    "event: status\ndata: "
                    + json.dumps(
                        {
                            "phase": "generating",
                            "label": "Generating response\u2026",
                            "retrieve_ms": retrieve_ms,
                        }
                    )
                    + "\n\n"
                )
                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        if not chunk:
                            continue
                        text = stripper.feed(str(chunk))
                        if not text:
                            continue
                        if t_first_token is None:
                            t_first_token = time.perf_counter()
                        collected.append(text)
                        token_count += 1
                        yield f"event: token\ndata: {json.dumps({'text': text})}\n\n"
                    # Emit any trailing buffered text (e.g. final close tag absent).
                    tail = stripper.flush()
                    if tail:
                        if t_first_token is None:
                            t_first_token = time.perf_counter()
                        collected.append(tail)
                        token_count += 1
                        yield f"event: token\ndata: {json.dumps({'text': tail})}\n\n"
                else:
                    text = strip_think(str(result))
                    collected.append(text)
                    token_count = 1
                    t_first_token = time.perf_counter()
                    yield f"event: token\ndata: {json.dumps({'text': text})}\n\n"
            except Exception as exc:
                logger.exception("Streaming query failed for chat %s", chat_id)
                error_message = str(exc)
                yield f"event: error\ndata: {json.dumps({'message': error_message})}\n\n"
                # Persist the error so the chat reflects what the user saw.
                collected.append(f"\u26a0\ufe0f Query failed: {exc}")

            t_end = time.perf_counter()
            total_ms = int((t_end - t_start) * 1000)
            ttft_ms = (
                int((t_first_token - t_start) * 1000) if t_first_token else None
            )
            generate_ms = (
                int((t_end - t_first_token) * 1000) if t_first_token else None
            )

            full_text = "".join(collected)
            timing = {
                "total_ms": total_ms,
                "ttft_ms": ttft_ms,
                "generate_ms": generate_ms,
                "chunk_count": token_count,
                "char_count": len(full_text),
            }
            assistant_msg = {
                "role": "assistant",
                "content": full_text,
                "ts": _now_iso(),
                "mode": mode,
                "timing": timing,
            }
            if sources_payload is not None:
                assistant_msg["sources"] = sources_payload
            # Re-read so we don't clobber concurrent edits to the same chat file.
            try:
                latest = chat_store.read(chat_id)
            except HTTPException:
                latest = chat
            latest["messages"].append(assistant_msg)
            latest["updated_at"] = _now_iso()
            chat_store.write(latest)

            logger.info(
                "[chat] mode=%s ttft=%sms total=%sms chunks=%s chars=%s%s",
                mode,
                ttft_ms if ttft_ms is not None else "-",
                total_ms,
                token_count,
                len(full_text),
                f" error={error_message!r}" if error_message else "",
            )

            yield (
                "event: done\ndata: "
                + json.dumps(
                    {
                        "assistant": assistant_msg,
                        "chat": chat_store.summary(latest),
                        "timing": timing,
                    }
                )
                + "\n\n"
            )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",  # disable nginx buffering if proxied
                "Connection": "keep-alive",
            },
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

    # ---- Workspace inventory + deletion (Settings → Danger Zone) ---------
    #
    # The deletion paths intentionally reuse the same helpers as the
    # `tools/workspace_cleanup.py` CLI — no second implementation. That
    # keeps the two surfaces (CLI for ops, UI for end-users) in lockstep.

    def _ws_inventory() -> dict[str, Any]:
        """Combine rag_storage, Neo4j, and inputs/ views into one table."""
        from tools.workspace_cleanup import (
            _inputs_root,
            _inputs_workspaces,
            _neo4j_workspaces,
            _rag_storage_root,
            _storage_workspaces,
        )

        rag_root = _rag_storage_root()
        inputs_root = _inputs_root()
        storage_ws = _storage_workspaces(rag_root)
        inputs_ws = _inputs_workspaces(inputs_root)

        # Neo4j enumeration is best-effort — the driver may be unreachable in
        # NetworkX-only deployments. Fall back to an empty map so the UI can
        # still render rag_storage + inputs columns.
        neo4j_ws: dict[str, int] = {}
        backend = (getattr(global_args, "graph_storage", "") or "").lower()
        if "neo4j" in backend:
            try:
                from src.inference.neo4j_graph_io import Neo4jGraphIO

                io = Neo4jGraphIO()
                try:
                    neo4j_ws = _neo4j_workspaces(io)
                finally:
                    io.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Neo4j inventory failed: %s", exc)

        all_names = sorted(
            set(neo4j_ws) | set(storage_ws) | set(inputs_ws)
        )
        active = get_settings().workspace
        rows: list[dict[str, Any]] = []
        for name in all_names:
            inp = inputs_ws.get(name)
            rows.append({
                "name": name,
                "is_active": name == active,
                "neo4j_nodes": neo4j_ws.get(name, 0),
                "storage_mb": storage_ws.get(name),
                "inputs_files": inp[0] if inp else 0,
                "inputs_mb": inp[1] if inp else 0.0,
            })
        return {
            "active": active,
            "rag_storage_root": str(rag_root),
            "inputs_root": str(inputs_root),
            "neo4j_available": "neo4j" in backend,
            "workspaces": rows,
        }

    @app.get("/api/ui/workspaces/inventory", tags=["theseus-ui"])
    async def workspaces_inventory() -> JSONResponse:
        """Per-workspace inventory: Neo4j node count, rag_storage size, inputs/ files."""
        return JSONResponse(await asyncio.to_thread(_ws_inventory))

    def _delete_workspace_sync(
        name: str, scope: WorkspaceDeleteScope
    ) -> dict[str, Any]:
        """Worker thread: run the actual deletion using cleanup-tool helpers."""
        from tools.workspace_cleanup import (
            _delete_inputs_workspace,
            _delete_neo4j_workspace,
            _delete_storage_workspace,
            _inputs_root,
            _rag_storage_root,
        )

        result: dict[str, Any] = {"workspace": name, "deleted": {}}

        if scope.neo4j:
            backend = (getattr(global_args, "graph_storage", "") or "").lower()
            if "neo4j" in backend:
                try:
                    from src.inference.neo4j_graph_io import Neo4jGraphIO

                    io = Neo4jGraphIO()
                    try:
                        nodes = _delete_neo4j_workspace(io, name)
                        result["deleted"]["neo4j_nodes"] = nodes
                    finally:
                        io.close()
                except Exception as exc:  # noqa: BLE001
                    result["deleted"]["neo4j_error"] = str(exc)
            else:
                result["deleted"]["neo4j_skipped"] = "backend is not Neo4j"

        if scope.rag_storage:
            try:
                existed = _delete_storage_workspace(name, _rag_storage_root())
                result["deleted"]["rag_storage"] = existed
            except Exception as exc:  # noqa: BLE001
                result["deleted"]["rag_storage_error"] = str(exc)

        if scope.inputs:
            try:
                count, mb = _delete_inputs_workspace(name, _inputs_root())
                # Also drop the now-empty inputs/<ws>/ dir so it disappears
                # from the workspace list entirely.
                ws_inputs = _inputs_root() / name
                if ws_inputs.exists() and ws_inputs.is_dir() and not any(ws_inputs.iterdir()):
                    try:
                        ws_inputs.rmdir()
                    except OSError:
                        pass
                result["deleted"]["inputs_files"] = count
                result["deleted"]["inputs_mb"] = mb
            except Exception as exc:  # noqa: BLE001
                result["deleted"]["inputs_error"] = str(exc)

        return result

    @app.post("/api/ui/workspaces/{name}/delete", tags=["theseus-ui"])
    async def delete_workspace(
        name: str, scope: WorkspaceDeleteScope
    ) -> JSONResponse:
        """Delete one workspace's selected buckets (Neo4j / rag_storage / inputs).

        Refuses to delete the currently-active workspace — switch first.
        Source documents (`inputs/<ws>/`) are irrecoverable; the UI is
        responsible for surfacing a type-to-confirm guard before calling
        this endpoint with `inputs=true`.
        """
        if not _SAFE_WS.match(name):
            raise HTTPException(400, "Invalid workspace name (use alphanumerics, _, -)")
        if not (scope.neo4j or scope.rag_storage or scope.inputs):
            raise HTTPException(400, "At least one scope (neo4j/rag_storage/inputs) must be true.")
        if name == get_settings().workspace:
            raise HTTPException(
                409,
                "Cannot delete the active workspace. Switch to another workspace first.",
            )
        logger.warning(
            "🗑️  Deleting workspace '%s' (neo4j=%s, rag_storage=%s, inputs=%s)",
            name, scope.neo4j, scope.rag_storage, scope.inputs,
        )
        result = await asyncio.to_thread(_delete_workspace_sync, name, scope)
        return JSONResponse(result)

    @app.post("/api/ui/workspaces/wipe-all", tags=["theseus-ui"])
    async def wipe_all_workspaces(scope: WipeAllScope) -> JSONResponse:
        """Clean-slate wipe across every workspace. Requires confirm='DELETE ALL'.

        Triggers a server self-restart afterwards so the next boot lands on a
        clean state. The active workspace folder is recreated empty so the
        next process can start without crashing on a missing working dir.
        """
        if scope.confirm != "DELETE ALL":
            raise HTTPException(400, "Confirmation phrase must equal 'DELETE ALL'.")
        if not (scope.neo4j or scope.rag_storage or scope.inputs):
            raise HTTPException(400, "At least one scope (neo4j/rag_storage/inputs) must be true.")

        def _wipe_all_sync() -> dict[str, Any]:
            inv = _ws_inventory()
            names = [row["name"] for row in inv["workspaces"]]
            results: list[dict[str, Any]] = []
            per_scope = WorkspaceDeleteScope(
                neo4j=scope.neo4j,
                rag_storage=scope.rag_storage,
                inputs=scope.inputs,
            )
            for nm in names:
                results.append(_delete_workspace_sync(nm, per_scope))
            # Make sure the active workspace's rag_storage folder still
            # exists — LightRAG's storages assume it on next boot.
            try:
                from tools.workspace_cleanup import _rag_storage_root

                (_rag_storage_root() / get_settings().workspace).mkdir(
                    parents=True, exist_ok=True
                )
            except Exception:  # noqa: BLE001
                pass
            return {"deleted": results, "workspaces": len(results)}

        logger.warning(
            "🚨 WIPE ALL WORKSPACES requested (neo4j=%s, rag_storage=%s, inputs=%s)",
            scope.neo4j, scope.rag_storage, scope.inputs,
        )
        result = await asyncio.to_thread(_wipe_all_sync)
        # Restart so the UI reconnects to a clean process state.
        asyncio.get_event_loop().call_later(0.75, _self_restart)
        result["restarting"] = True
        return JSONResponse(result)

    @app.post("/api/ui/restart", tags=["theseus-ui"])
    async def restart_server() -> JSONResponse:
        """Schedule a graceful self-restart of the server process.

        Identical mechanism to the workspace switch: re-execs ~750ms after
        responding so the HTTP reply can flush. Browser polls /api/ui/stats
        and reconnects automatically.
        """
        asyncio.get_event_loop().call_later(0.75, _self_restart)
        logger.warning("🔄 Manual restart requested via Settings page.")
        return JSONResponse({
            "status": "restarting",
            "workspace": get_settings().workspace,
            "message": "Server is restarting. The UI will reconnect automatically.",
        })

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
