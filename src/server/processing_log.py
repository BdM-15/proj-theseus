"""
Processing-log capture for the Theseus Documents tab.

Background
----------
Document ingestion fans out across several modules:

* ``src.server.routes`` — upload + RAG-Anything dispatch + ``GovConProcessingCallback``
* ``raganything.parser`` — MinerU subprocess driver
* ``lightrag.lightrag`` / ``lightrag.operate`` — chunking, entity extraction
* ``src.inference.semantic_post_processor`` — phase 1-6 post-processing
* ``src.extraction.*`` — multimodal analysis hooks

All of these write to ``logs/server.log``. Tailing that file from the UI works
but mixes in unrelated noise (uvicorn requests, neo4j driver chatter, etc.).
This module installs a :class:`logging.Handler` that captures only the records
relevant to document processing into an in-memory rolling buffer and fans them
out to live SSE subscribers.

The buffer is process-wide and unfiltered by workspace at the source — events
are stamped with the workspace that was active at emission time and the UI
filters client-side. Workspace switches require a server restart anyway, so a
single buffer is sufficient.

Public API
----------
:func:`get_log_buffer` — singleton accessor.
:func:`install_log_capture_handler` — install the logging handler (idempotent).
"""
from __future__ import annotations

import asyncio
import logging
import re
import threading
import time
from collections import deque
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Cap in-memory history. 500 lines comfortably covers a multi-document batch
# (each doc emits ~10-30 events) without growing unbounded across long sessions.
_MAX_EVENTS = 500

# Per-subscriber queue depth. The fanout is fire-and-forget; if a slow client
# can't drain in time we drop oldest events on its queue rather than block.
_SUBSCRIBER_QUEUE_DEPTH = 200

# Loggers we always capture (everything emitted under these names flows in).
_INCLUDE_LOGGERS = (
    "src.server.routes",
    "src.inference",
    "src.extraction",
    "src.server.initialization",
    "raganything",
)

# Loggers we sometimes care about — capture only when the message contains one
# of the marker substrings below. Keeps uvicorn/neo4j chatter out.
_CONDITIONAL_LOGGERS = ("lightrag",)
_MARKER_SUBSTRINGS = (
    "Phase ",
    "extracted",
    "Entity extraction",
    "Relationship extraction",
    "chunk",
    "MinerU",
    "doc_id",
)

# Recognize "Phase 1 · Data Loading" / "Phase 4 · Relationship Inference" etc.
# so the UI can render a progress chip without re-parsing text.
_PHASE_RE = re.compile(r"Phase\s+(\d+)\s*[·:.\-]?\s*([A-Za-z][A-Za-z &/\-]*)")


def _classify_event(record: logging.LogRecord, message: str) -> dict[str, Any]:
    """Tag a record with high-level kind hints used by the UI."""
    kind = "info"
    phase: Optional[dict[str, Any]] = None
    if record.levelno >= logging.ERROR:
        kind = "error"
    elif record.levelno >= logging.WARNING:
        kind = "warning"
    elif "✅" in message or "complete" in message.lower():
        kind = "success"
    elif "⚙️" in message or "Phase " in message or "🚀" in message:
        kind = "phase"
    elif "📥" in message or "🏁" in message:
        kind = "queue"
    elif "🎯" in message:
        kind = "batch"

    m = _PHASE_RE.search(message)
    if m:
        phase = {"index": int(m.group(1)), "label": m.group(2).strip()}

    return {"kind": kind, "phase": phase}


class ProcessingLogBuffer:
    """In-memory rolling buffer + SSE fanout for document processing logs.

    Thread-safe: ``append`` may be called from any thread (logging handlers run
    on whichever thread emitted the log call). Subscribers are asyncio Queues
    drained by SSE handlers running on the event loop.
    """

    def __init__(self, maxlen: int = _MAX_EVENTS) -> None:
        self._events: deque[dict[str, Any]] = deque(maxlen=maxlen)
        self._lock = threading.Lock()
        self._next_id = 1
        # Subscribers live on the asyncio loop; we capture the loop at subscribe
        # time so cross-thread ``call_soon_threadsafe`` works from logging
        # threads. ``(loop, queue)`` tuples.
        self._subscribers: list[tuple[asyncio.AbstractEventLoop, asyncio.Queue]] = []

    def append(self, event: dict[str, Any]) -> None:
        """Record an event and fan it out to live subscribers."""
        with self._lock:
            event = {"id": self._next_id, **event}
            self._next_id += 1
            self._events.append(event)
            subs = list(self._subscribers)

        # Fanout outside the lock. Use call_soon_threadsafe because the logging
        # handler may fire from any thread (MinerU subprocess driver, batch
        # timer callback, etc.).
        for loop, queue in subs:
            try:
                loop.call_soon_threadsafe(self._safe_put, queue, event)
            except RuntimeError:
                # Loop is closed; clean up on next subscribe call.
                pass

    @staticmethod
    def _safe_put(queue: asyncio.Queue, event: dict[str, Any]) -> None:
        if queue.full():
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
        queue.put_nowait(event)

    def snapshot(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Return up to ``limit`` most-recent events in chronological order."""
        with self._lock:
            data = list(self._events)
        if limit is not None and limit > 0:
            data = data[-limit:]
        return data

    def subscribe(self) -> asyncio.Queue:
        """Register a new subscriber queue tied to the current event loop."""
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=_SUBSCRIBER_QUEUE_DEPTH)
        with self._lock:
            self._subscribers.append((loop, queue))
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers = [
                (loop, q) for (loop, q) in self._subscribers if q is not queue
            ]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


_BUFFER = ProcessingLogBuffer()


def get_log_buffer() -> ProcessingLogBuffer:
    """Singleton accessor for the processing-log buffer."""
    return _BUFFER


class _ProcessingLogHandler(logging.Handler):
    """Filters log records into the processing-log buffer.

    Only attaches to the root logger; relies on Python's logger name hierarchy
    to decide which records to keep.
    """

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D401 - logging API
        try:
            name = record.name or ""
            if not (
                any(name == n or name.startswith(n + ".") for n in _INCLUDE_LOGGERS)
                or (
                    any(name == n or name.startswith(n + ".") for n in _CONDITIONAL_LOGGERS)
                    and any(marker in record.getMessage() for marker in _MARKER_SUBSTRINGS)
                )
            ):
                return

            message = record.getMessage()
            classification = _classify_event(record, message)

            # Resolve the active workspace lazily so we don't pay for it on
            # records that get filtered out.
            workspace = None
            try:
                from src.core import get_settings  # local import to avoid cycles

                workspace = get_settings().workspace
            except Exception:  # noqa: BLE001 - never let logging crash the app
                workspace = None

            event = {
                "ts": record.created,
                "ts_iso": time.strftime(
                    "%Y-%m-%dT%H:%M:%S", time.localtime(record.created)
                )
                + f".{int(record.msecs):03d}",
                "level": record.levelname,
                "logger": name,
                "message": message,
                "workspace": workspace,
                **classification,
            }
            _BUFFER.append(event)
        except Exception:  # noqa: BLE001 - logging handlers must never raise
            pass


_HANDLER_INSTALLED = False


def install_log_capture_handler() -> None:
    """Attach the capture handler to the root logger (idempotent)."""
    global _HANDLER_INSTALLED
    if _HANDLER_INSTALLED:
        return
    handler = _ProcessingLogHandler(level=logging.INFO)
    # Don't touch formatters — we read the structured fields, not the format.
    logging.getLogger().addHandler(handler)
    _HANDLER_INSTALLED = True
    logger.info("📡 Processing-log capture handler installed")
