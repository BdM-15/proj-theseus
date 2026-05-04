"""Runtime settings helpers for the skills subsystem."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from src.core.env import env_float, env_int

logger = logging.getLogger(__name__)

VALID_SKILL_RUNTIME_MODES = {"tools", "legacy"}
VALID_SKILL_RETRIEVAL_MODES = {"hybrid", "local", "global", "naive", "mix", "off"}


DEFAULT_SKILL_MAX_PAYLOAD_CHARS = env_int("SKILL_MAX_PAYLOAD_CHARS", 200_000)


def resolve_skill_runtime_mode(
    frontmatter_mode: str,
    *,
    runtime_mode_override: Optional[str] = None,
) -> str:
    """Resolve skill runtime mode using override, env, then frontmatter."""
    env_override = os.getenv("SKILL_RUNTIME_MODE", "").strip().lower()
    requested = (runtime_mode_override or "").strip().lower()
    if requested in VALID_SKILL_RUNTIME_MODES:
        return requested
    if env_override in VALID_SKILL_RUNTIME_MODES:
        return env_override
    normalized = (frontmatter_mode or "").strip().lower()
    return "tools" if normalized == "tools" else "legacy"


def skill_tools_max_turns(metadata: Mapping[str, Any]) -> int:
    """Return the effective tools-mode turn budget for one skill."""
    env_max_turns = env_int("SKILL_TOOLS_MAX_TURNS", 12)
    raw = metadata.get("max_turns")
    if isinstance(raw, int) and raw > env_max_turns:
        return raw
    return env_max_turns


def mcp_handshake_timeout() -> float:
    """Timeout in seconds for MCP handshake and tool listing."""
    return env_float("MCP_HANDSHAKE_TIMEOUT", 10.0, 0.1)


def mcp_tool_call_timeout() -> float:
    """Timeout in seconds for one MCP tool call."""
    return env_float("MCP_TOOL_CALL_TIMEOUT", 30.0, 0.1)


def mcp_shutdown_timeout() -> float:
    """Timeout in seconds for graceful MCP subprocess shutdown."""
    return env_float("MCP_SHUTDOWN_TIMEOUT", 3.0, 0.1)


class SkillSettingsStore:
    """Per-workspace skill invocation settings backed by JSON files."""

    def __init__(self, workspace_dir: Callable[[], Path]) -> None:
        self._workspace_dir = workspace_dir

    @staticmethod
    def _env_skill_mode() -> str:
        raw = (os.getenv("SKILL_RETRIEVAL_MODE") or "mix").strip().lower()
        return raw if raw in VALID_SKILL_RETRIEVAL_MODES else "mix"

    def path(self) -> Path:
        return self._workspace_dir() / "ui_skill_settings.json"

    def defaults(self) -> dict[str, Any]:
        return {
            "max_entities_per_type": env_int(
                "SKILL_MAX_ENTITIES_PER_TYPE", 40, 1, 500
            ),
            "max_chunks_per_entity": env_int(
                "SKILL_MAX_CHUNKS_PER_ENTITY", 2, 0, 10
            ),
            "max_relationships_per_entity": env_int(
                "SKILL_MAX_RELATIONSHIPS_PER_ENTITY", 5, 0, 50
            ),
            "retrieval_mode": self._env_skill_mode(),
            "retrieval_top_k": env_int("SKILL_RETRIEVAL_TOP_K", 60, 5, 500),
        }

    def read(self) -> dict[str, Any]:
        merged = self.defaults()
        path = self.path()
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
        path = self.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
