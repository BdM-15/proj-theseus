"""Per-workspace LightRAG query settings for the Project Theseus UI."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core.env import env_int

logger = logging.getLogger(__name__)

VALID_QUERY_MODES = {"local", "global", "hybrid", "naive", "mix", "bypass"}

# QueryParam fields forwarded to the bridge. `min_rerank_score` is applied
# directly to the LightRAG instance, and `mode` / `stream` are per-chat.
# `response_type` is intentionally omitted because upstream LightRAG WebUI
# dropped the picker and uses QueryParam's default.
QUERY_PARAM_FIELDS = (
    "top_k",
    "chunk_top_k",
    "max_entity_tokens",
    "max_relation_tokens",
    "max_total_tokens",
    "enable_rerank",
    "only_need_context",
    "only_need_prompt",
    "user_prompt",
)


class QuerySettingsUpdate(BaseModel):
    """Per-workspace LightRAG query parameter overrides."""

    mode: str | None = Field(default=None, max_length=20)
    top_k: int | None = Field(default=None, ge=1, le=500)
    chunk_top_k: int | None = Field(default=None, ge=1, le=500)
    max_entity_tokens: int | None = Field(default=None, ge=100, le=200000)
    max_relation_tokens: int | None = Field(default=None, ge=100, le=200000)
    max_total_tokens: int | None = Field(default=None, ge=100, le=500000)
    enable_rerank: bool | None = None
    min_rerank_score: float | None = Field(default=None, ge=0.0, le=1.0)
    only_need_context: bool | None = None
    only_need_prompt: bool | None = None
    stream: bool | None = None
    user_prompt: str | None = Field(default=None, max_length=20000)


class QuerySettingsStore:
    """JSON-backed query settings for the active workspace."""

    def __init__(
        self,
        *,
        workspace_dir: Callable[[], Path],
        settings_provider: Callable[[], Any],
    ) -> None:
        self._workspace_dir = workspace_dir
        self._settings_provider = settings_provider

    def defaults(self) -> dict[str, Any]:
        """Build defaults from env-driven server settings."""
        settings = self._settings_provider()
        return {
            "mode": "mix",
            "top_k": env_int("TOP_K", 40, 1, 500),
            "chunk_top_k": env_int("CHUNK_TOP_K", 20, 1, 500),
            "max_entity_tokens": env_int("MAX_ENTITY_TOKENS", 6000, 100, 200000),
            "max_relation_tokens": env_int("MAX_RELATION_TOKENS", 8000, 100, 200000),
            "max_total_tokens": env_int("MAX_TOTAL_TOKENS", 60000, 100, 500000),
            "enable_rerank": bool(settings.enable_rerank),
            "min_rerank_score": float(settings.min_rerank_score),
            "only_need_context": False,
            "only_need_prompt": False,
            "stream": True,
            "user_prompt": "",
        }

    def path(self) -> Path:
        return self._workspace_dir() / "ui_query_settings.json"

    def read(self) -> dict[str, Any]:
        """Return active query settings merged over env-driven defaults."""
        path = self.path()
        merged = self.defaults()
        if not path.exists():
            return merged
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for key in list(merged.keys()):
                    if key in loaded:
                        merged[key] = loaded[key]
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Failed reading %s, using defaults: %s", path, exc)
        return merged

    def write(self, data: dict[str, Any]) -> None:
        """Persist query settings atomically."""
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)

    def reset(self) -> dict[str, Any]:
        """Remove overrides and return fresh defaults."""
        path = self.path()
        if path.exists():
            path.unlink()
        return self.defaults()

    def build_overrides(self) -> dict[str, Any]:
        """Build the dict passed to the bridge QueryParam layer."""
        settings = self.read()
        overrides: dict[str, Any] = {
            key: settings[key] for key in QUERY_PARAM_FIELDS if key in settings
        }
        overrides["min_rerank_score"] = settings.get("min_rerank_score", 0.0)
        return overrides


def register_query_settings_routes(
    app: FastAPI,
    *,
    workspace_name: Callable[[], str],
    store: QuerySettingsStore,
) -> None:
    """Register query settings routes for the Theseus UI."""

    @app.get("/api/ui/settings/query", tags=["theseus-ui"])
    async def get_query_settings() -> JSONResponse:
        """Return active per-workspace query settings and defaults."""
        return JSONResponse(
            {
                "workspace": workspace_name(),
                "settings": store.read(),
                "defaults": store.defaults(),
            }
        )

    @app.put("/api/ui/settings/query", tags=["theseus-ui"])
    async def update_query_settings(payload: QuerySettingsUpdate) -> JSONResponse:
        """Patch one or more query settings."""
        current = store.read()
        updates = payload.model_dump(exclude_none=True)
        if "mode" in updates and updates["mode"] not in VALID_QUERY_MODES:
            raise HTTPException(400, f"Unsupported mode: {updates['mode']}")
        current.update(updates)
        try:
            store.write(current)
        except OSError as exc:
            raise HTTPException(500, f"Failed writing settings: {exc}") from exc
        return JSONResponse({"settings": current})

    @app.post("/api/ui/settings/query/reset", tags=["theseus-ui"])
    async def reset_query_settings() -> JSONResponse:
        """Restore defaults by removing per-workspace overrides."""
        try:
            settings = store.reset()
        except OSError as exc:
            raise HTTPException(500, f"Failed resetting settings: {exc}") from exc
        return JSONResponse({"settings": settings})
