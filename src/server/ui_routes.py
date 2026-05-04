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

from src.core import get_settings
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
