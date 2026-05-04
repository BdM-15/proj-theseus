"""Workspace management routes for the Project Theseus UI."""

from __future__ import annotations

import asyncio
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.core import reset_settings

logger = logging.getLogger(__name__)

_SAFE_WS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_COUNT_CACHE: dict[tuple[str, int, int], int] = {}


class WorkspaceSwitch(BaseModel):
    """Body for POST /api/ui/workspaces/switch."""

    name: str = Field(..., min_length=1, max_length=64)
    create: bool = Field(
        default=False,
        description="Create the folder if it does not exist.",
    )


class WorkspaceDeleteScope(BaseModel):
    """Which buckets of a workspace to delete. At least one must be true."""

    neo4j: bool = Field(
        default=False,
        description="Delete the workspace's Neo4j subgraph.",
    )
    rag_storage: bool = Field(
        default=False,
        description="Delete rag_storage/<ws>/ (KV stores, VDBs, chats, log).",
    )
    inputs: bool = Field(
        default=False,
        description="Delete inputs/<ws>/ source documents (irrecoverable).",
    )


class WipeAllScope(BaseModel):
    """Clean-slate wipe. Requires the literal confirmation phrase."""

    neo4j: bool = Field(default=False)
    rag_storage: bool = Field(default=False)
    inputs: bool = Field(default=False)
    confirm: str = Field(..., description="Must equal 'DELETE ALL'.")


def safe_count_json_keys(path: Path) -> int:
    """Count records in a LightRAG storage JSON file, returning 0 on errors."""
    import json

    try:
        if not path.exists():
            return 0
        stat = path.stat()
        key = (str(path), stat.st_mtime_ns, stat.st_size)
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
        for old_key in [old_key for old_key in _COUNT_CACHE if old_key[0] == str(path)]:
            _COUNT_CACHE.pop(old_key, None)
        _COUNT_CACHE[key] = count
        return count
    except Exception:  # noqa: BLE001
        return 0


def discover_workspaces(working_dir: Path) -> list[dict[str, Any]]:
    """List candidate workspaces under the configured working directory."""
    if not working_dir.exists():
        return []
    signature_files = (
        "kv_store_doc_status.json",
        "vdb_entities.json",
        "vdb_chunks.json",
    )
    workspaces: list[dict[str, Any]] = []
    for child in sorted(working_dir.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        has_data = any((child / filename).exists() for filename in signature_files)
        workspaces.append(
            {
                "name": child.name,
                "has_data": has_data,
                "documents": safe_count_json_keys(child / "kv_store_doc_status.json"),
                "entities": safe_count_json_keys(child / "vdb_entities.json"),
                "chats": (
                    sum(1 for _ in (child / "chats").glob("*.json"))
                    if (child / "chats").exists()
                    else 0
                ),
            }
        )
    return workspaces


def set_env_var(key: str, value: str) -> None:
    """Update or append KEY=value in the project .env file."""
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


def self_restart() -> None:
    """Re-exec the current python process with the same argv."""
    logger.warning("Re-execing process: %s %s", sys.executable, sys.argv)
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as exc:  # pragma: no cover
        logger.exception("Self-restart failed: %s", exc)
        os._exit(1)


def workspace_inventory(
    *,
    active_workspace: str,
    graph_storage: str,
) -> dict[str, Any]:
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

    neo4j_ws: dict[str, int] = {}
    backend = (graph_storage or "").lower()
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

    all_names = sorted(set(neo4j_ws) | set(storage_ws) | set(inputs_ws))
    rows: list[dict[str, Any]] = []
    for name in all_names:
        inputs = inputs_ws.get(name)
        rows.append(
            {
                "name": name,
                "is_active": name == active_workspace,
                "neo4j_nodes": neo4j_ws.get(name, 0),
                "storage_mb": storage_ws.get(name),
                "inputs_files": inputs[0] if inputs else 0,
                "inputs_mb": inputs[1] if inputs else 0.0,
            }
        )
    return {
        "active": active_workspace,
        "rag_storage_root": str(rag_root),
        "inputs_root": str(inputs_root),
        "neo4j_available": "neo4j" in backend,
        "workspaces": rows,
    }


def delete_workspace_sync(
    name: str,
    scope: WorkspaceDeleteScope,
    *,
    graph_storage: str,
) -> dict[str, Any]:
    """Delete one workspace's selected storage buckets."""
    from tools.workspace_cleanup import (
        _delete_inputs_workspace,
        _delete_neo4j_workspace,
        _delete_storage_workspace,
        _inputs_root,
        _rag_storage_root,
    )

    result: dict[str, Any] = {"workspace": name, "deleted": {}}

    if scope.neo4j:
        backend = (graph_storage or "").lower()
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
            workspace_inputs = _inputs_root() / name
            if (
                workspace_inputs.exists()
                and workspace_inputs.is_dir()
                and not any(workspace_inputs.iterdir())
            ):
                try:
                    workspace_inputs.rmdir()
                except OSError:
                    pass
            result["deleted"]["inputs_files"] = count
            result["deleted"]["inputs_mb"] = mb
        except Exception as exc:  # noqa: BLE001
            result["deleted"]["inputs_error"] = str(exc)

    return result


def ensure_active_storage_workspace(active_workspace: str) -> None:
    """Ensure the active rag_storage workspace exists after a clean-slate wipe."""
    from tools.workspace_cleanup import _rag_storage_root

    (_rag_storage_root() / active_workspace).mkdir(parents=True, exist_ok=True)


def register_workspace_ui_routes(
    app: FastAPI,
    *,
    workspace_name: Callable[[], str],
    working_dir: Callable[[], Path],
    graph_storage: Callable[[], str],
    set_env_var_func: Callable[[str, str], None] = set_env_var,
    schedule_restart: Callable[[float], None] | None = None,
    inventory_func: Callable[..., dict[str, Any]] = workspace_inventory,
    delete_workspace_func: Callable[..., dict[str, Any]] = delete_workspace_sync,
    ensure_active_workspace: Callable[[str], None] = ensure_active_storage_workspace,
) -> None:
    """Register workspace list, switch, inventory, delete, wipe, and restart routes."""

    def _schedule_restart(delay: float) -> None:
        if schedule_restart is not None:
            schedule_restart(delay)
        else:
            asyncio.get_event_loop().call_later(delay, self_restart)

    @app.get("/api/ui/workspaces", tags=["theseus-ui"])
    async def list_workspaces() -> JSONResponse:
        """List discovered workspace directories under rag_storage/."""
        return JSONResponse(
            {
                "active": workspace_name(),
                "workspaces": discover_workspaces(working_dir()),
            }
        )

    @app.post("/api/ui/workspaces/switch", tags=["theseus-ui"])
    async def switch_workspace(payload: WorkspaceSwitch) -> JSONResponse:
        """Persist WORKSPACE=<name> and schedule a graceful restart."""
        name = payload.name.strip()
        if not _SAFE_WS.match(name):
            raise HTTPException(400, "Invalid workspace name (use alphanumerics, _, -)")
        existing = {workspace["name"] for workspace in discover_workspaces(working_dir())}
        if not payload.create and name not in existing:
            raise HTTPException(404, f"Workspace '{name}' does not exist")
        working_dir().mkdir(parents=True, exist_ok=True)
        (working_dir() / name).mkdir(parents=True, exist_ok=True)
        try:
            set_env_var_func("WORKSPACE", name)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(500, f"Failed updating .env: {exc}") from exc
        _schedule_restart(0.75)
        logger.warning("Workspace switch requested -> '%s'. Restarting server...", name)
        return JSONResponse(
            {
                "status": "restarting",
                "workspace": name,
                "message": "Server is restarting. The UI will reconnect automatically.",
            }
        )

    @app.get("/api/ui/workspaces/inventory", tags=["theseus-ui"])
    async def workspaces_inventory() -> JSONResponse:
        """Per-workspace inventory: Neo4j node count, rag_storage size, inputs files."""
        result = await asyncio.to_thread(
            inventory_func,
            active_workspace=workspace_name(),
            graph_storage=graph_storage(),
        )
        return JSONResponse(result)

    @app.post("/api/ui/workspaces/{name}/delete", tags=["theseus-ui"])
    async def delete_workspace(name: str, scope: WorkspaceDeleteScope) -> JSONResponse:
        """Delete one workspace's selected buckets."""
        if not _SAFE_WS.match(name):
            raise HTTPException(400, "Invalid workspace name (use alphanumerics, _, -)")
        if not (scope.neo4j or scope.rag_storage or scope.inputs):
            raise HTTPException(
                400,
                "At least one scope (neo4j/rag_storage/inputs) must be true.",
            )
        if name == workspace_name():
            raise HTTPException(
                409,
                "Cannot delete the active workspace. Switch to another workspace first.",
            )
        logger.warning(
            "Deleting workspace '%s' (neo4j=%s, rag_storage=%s, inputs=%s)",
            name,
            scope.neo4j,
            scope.rag_storage,
            scope.inputs,
        )
        result = await asyncio.to_thread(
            delete_workspace_func,
            name,
            scope,
            graph_storage=graph_storage(),
        )
        return JSONResponse(result)

    @app.post("/api/ui/workspaces/wipe-all", tags=["theseus-ui"])
    async def wipe_all_workspaces(scope: WipeAllScope) -> JSONResponse:
        """Clean-slate wipe across every workspace. Requires confirm='DELETE ALL'."""
        if scope.confirm != "DELETE ALL":
            raise HTTPException(400, "Confirmation phrase must equal 'DELETE ALL'.")
        if not (scope.neo4j or scope.rag_storage or scope.inputs):
            raise HTTPException(
                400,
                "At least one scope (neo4j/rag_storage/inputs) must be true.",
            )

        def wipe_all_sync() -> dict[str, Any]:
            inventory = inventory_func(
                active_workspace=workspace_name(),
                graph_storage=graph_storage(),
            )
            names = [row["name"] for row in inventory["workspaces"]]
            results = [
                delete_workspace_func(
                    name,
                    WorkspaceDeleteScope(
                        neo4j=scope.neo4j,
                        rag_storage=scope.rag_storage,
                        inputs=scope.inputs,
                    ),
                    graph_storage=graph_storage(),
                )
                for name in names
            ]
            try:
                ensure_active_workspace(workspace_name())
            except Exception:  # noqa: BLE001
                pass
            return {"deleted": results, "workspaces": len(results)}

        logger.warning(
            "Wipe all workspaces requested (neo4j=%s, rag_storage=%s, inputs=%s)",
            scope.neo4j,
            scope.rag_storage,
            scope.inputs,
        )
        result = await asyncio.to_thread(wipe_all_sync)
        _schedule_restart(0.75)
        result["restarting"] = True
        return JSONResponse(result)

    @app.post("/api/ui/restart", tags=["theseus-ui"])
    async def restart_server() -> JSONResponse:
        """Schedule a graceful self-restart of the server process."""
        _schedule_restart(0.75)
        logger.warning("Manual restart requested via Settings page.")
        return JSONResponse(
            {
                "status": "restarting",
                "workspace": workspace_name(),
                "message": "Server is restarting. The UI will reconnect automatically.",
            }
        )
