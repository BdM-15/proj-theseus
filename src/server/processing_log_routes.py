"""Processing-log snapshot and stream routes for the Theseus UI."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse

from src.server.workspace_log_tailer import read_snapshot, stream_events

ReadSnapshot = Callable[..., dict[str, Any]]
StreamEvents = Callable[..., AsyncIterator[dict[str, Any]]]


def register_processing_log_routes(
    app: FastAPI,
    *,
    read_log_snapshot: ReadSnapshot = read_snapshot,
    stream_log_events: StreamEvents = stream_events,
) -> None:
    """Register processing-log snapshot and SSE routes."""

    @app.get("/api/ui/processing-log", tags=["theseus-ui"])
    async def ui_processing_log_snapshot(limit: int = 500) -> JSONResponse:
        """Return the most-recent events from the workspace activity log."""
        return JSONResponse(read_log_snapshot(limit=limit))

    @app.get("/api/ui/processing-log/stream", tags=["theseus-ui"])
    async def ui_processing_log_stream(limit: int = 200) -> StreamingResponse:
        """Stream new workspace-log events to the Documents tab via SSE."""

        async def event_stream() -> AsyncIterator[str]:
            try:
                yield "event: open\ndata: {}\n\n"
                async for item in stream_log_events(initial_limit=limit):
                    if item["type"] == "snapshot":
                        yield (
                            "event: snapshot\ndata: "
                            + json.dumps(
                                {"events": item["events"], "path": item.get("path")}
                            )
                            + "\n\n"
                        )
                    elif item["type"] == "event":
                        yield (
                            "event: event\ndata: "
                            + json.dumps(item["event"])
                            + "\n\n"
                        )
                    else:
                        yield ": ping\n\n"
            except asyncio.CancelledError:
                raise

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )
