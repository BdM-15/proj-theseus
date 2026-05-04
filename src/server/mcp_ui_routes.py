"""MCP Settings panel routes for the Project Theseus UI."""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class McpKeyUpdate(BaseModel):
    """Body for POST /api/ui/mcps/{name}/keys."""

    keys: dict[str, str] = Field(
        default_factory=dict,
        description="env-var name -> value pairs (must be declared by the MCP)",
    )
    restart: bool = Field(
        default=True,
        description="Schedule a graceful self-restart so subprocess env updates",
    )


_SAFE_MCP_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_SAFE_ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")


def _mcps_root() -> Path:
    return Path.cwd() / "tools" / "mcps"


def _mask_secret(value: str) -> str:
    """Show first 4 + last 2, never the middle. Empty stays empty."""
    if not value:
        return ""
    if len(value) <= 8:
        return value[0] + "***"
    return f"{value[:4]}***{value[-2:]}"


def _env_status(name: str) -> dict[str, Any]:
    value = os.environ.get(name, "")
    return {"name": name, "set": bool(value), "masked": _mask_secret(value)}


def register_mcp_ui_routes(
    app: FastAPI,
    *,
    set_env_var: Callable[[str, str], None],
    schedule_restart: Callable[[float], None],
) -> None:
    """Register MCP inventory, key-management, and test-connection routes."""

    @app.get("/api/ui/mcps", tags=["theseus-ui"])
    async def list_mcps_route() -> JSONResponse:
        """List vendored MCP servers + their env-var status."""
        from src.skills.mcp_client import discover_manifests

        manifests = discover_manifests(_mcps_root())
        items: list[dict[str, Any]] = []
        for name in sorted(manifests):
            manifest = manifests[name]
            items.append(
                {
                    "name": manifest.name,
                    "description": manifest.description,
                    "command": manifest.command,
                    "env_required": [
                        _env_status(key) for key in manifest.env_required
                    ],
                    "env_optional": [
                        _env_status(key) for key in manifest.env_optional
                    ],
                    "missing_env": manifest.missing_env(),
                    "vendored_from": manifest.vendored_from,
                    "vendored_commit": manifest.vendored_commit,
                    "vendored_at": manifest.vendored_at,
                    "license": manifest.license,
                }
            )
        return JSONResponse({"mcps": items})

    @app.post("/api/ui/mcps/{name}/keys", tags=["theseus-ui"])
    async def update_mcp_keys_route(
        name: str, payload: McpKeyUpdate
    ) -> JSONResponse:
        """Persist env vars for one MCP into .env, then schedule restart."""
        from src.skills.mcp_client import discover_manifests

        if not _SAFE_MCP_NAME.match(name):
            raise HTTPException(400, "Invalid MCP name")
        manifests = discover_manifests(_mcps_root())
        if name not in manifests:
            raise HTTPException(404, f"Unknown MCP: {name}")
        manifest = manifests[name]
        allowed = set(manifest.env_required) | set(manifest.env_optional)
        if not allowed:
            raise HTTPException(400, f"MCP {name!r} declares no env vars")
        bad = [key for key in payload.keys if key not in allowed]
        if bad:
            raise HTTPException(
                400,
                f"Keys not declared by MCP {name!r}: {bad}. "
                f"Allowed: {sorted(allowed)}",
            )
        invalid = [key for key in payload.keys if not _SAFE_ENV_KEY.match(key)]
        if invalid:
            raise HTTPException(400, f"Malformed env-var names: {invalid}")
        written: list[str] = []
        for key, value in payload.keys.items():
            try:
                set_env_var(key, value)
                written.append(key)
            except Exception as exc:
                raise HTTPException(
                    500, f"Failed updating .env for {key}: {exc}"
                ) from exc
        if payload.restart and written:
            schedule_restart(0.75)
            logger.warning(
                "MCP %s keys updated (%s) - restarting...", name, written
            )
            return JSONResponse(
                {
                    "status": "restarting",
                    "written": written,
                    "mcp": name,
                    "message": "Keys saved. Server is restarting; UI will reconnect.",
                }
            )
        return JSONResponse(
            {
                "status": "saved",
                "written": written,
                "mcp": name,
            }
        )

    @app.post("/api/ui/mcps/{name}/test", tags=["theseus-ui"])
    async def test_mcp_route(name: str) -> JSONResponse:
        """Spawn the MCP, complete handshake, and return tool inventory."""
        from src.skills.mcp_client import MCPError, MCPSession, discover_manifests

        if not _SAFE_MCP_NAME.match(name):
            raise HTTPException(400, "Invalid MCP name")
        manifests = discover_manifests(_mcps_root())
        if name not in manifests:
            raise HTTPException(404, f"Unknown MCP: {name}")
        session = MCPSession(manifests[name])
        try:
            try:
                await session.start()
            except MCPError as exc:
                return JSONResponse(
                    {"ok": False, "mcp": name, "error": str(exc)}
                )
            tools = list(session.tools)
            return JSONResponse(
                {
                    "ok": True,
                    "mcp": name,
                    "tool_count": len(tools),
                    "sample_tools": [tool.name for tool in tools[:8]],
                }
            )
        finally:
            try:
                await session.shutdown()
            except Exception:  # noqa: BLE001 - best-effort reap
                logger.debug("MCP %s test shutdown raised", name, exc_info=True)
