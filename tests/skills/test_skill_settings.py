import json
from pathlib import Path

from src.skills.settings import (
    SkillSettingsStore,
    env_float,
    env_int,
    mcp_handshake_timeout,
    mcp_shutdown_timeout,
    mcp_tool_call_timeout,
    resolve_skill_runtime_mode,
    skill_tools_max_turns,
)


def test_env_int_clamps_and_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("X_INT", "999")
    assert env_int("X_INT", 10, 1, 100) == 100

    monkeypatch.setenv("X_INT", "nope")
    assert env_int("X_INT", 10, 1, 100) == 10


def test_env_float_clamps_and_falls_back(monkeypatch) -> None:
    monkeypatch.setenv("X_FLOAT", "999.5")
    assert env_float("X_FLOAT", 10.0, 1.0, 100.0) == 100.0

    monkeypatch.setenv("X_FLOAT", "nope")
    assert env_float("X_FLOAT", 10.0, 1.0, 100.0) == 10.0

    monkeypatch.delenv("X_FLOAT", raising=False)
    assert env_float("X_FLOAT", 10.0, 1.0, 100.0) == 10.0


def test_mcp_timeouts_are_read_from_skill_settings(monkeypatch) -> None:
    monkeypatch.setenv("MCP_HANDSHAKE_TIMEOUT", "1.5")
    monkeypatch.setenv("MCP_TOOL_CALL_TIMEOUT", "2.5")
    monkeypatch.setenv("MCP_SHUTDOWN_TIMEOUT", "3.5")

    assert mcp_handshake_timeout() == 1.5
    assert mcp_tool_call_timeout() == 2.5
    assert mcp_shutdown_timeout() == 3.5

    monkeypatch.delenv("X_INT", raising=False)
    assert env_int("X_INT", 10, 1, 100) == 10


def test_resolve_skill_runtime_mode_precedence(monkeypatch) -> None:
    monkeypatch.setenv("SKILL_RUNTIME_MODE", "legacy")
    assert resolve_skill_runtime_mode("tools") == "legacy"
    assert resolve_skill_runtime_mode("legacy", runtime_mode_override="tools") == "tools"

    monkeypatch.setenv("SKILL_RUNTIME_MODE", "bogus")
    assert resolve_skill_runtime_mode("tools") == "tools"
    assert resolve_skill_runtime_mode("bogus") == "legacy"


def test_skill_tools_max_turns_uses_larger_skill_budget(monkeypatch) -> None:
    monkeypatch.setenv("SKILL_TOOLS_MAX_TURNS", "8")
    assert skill_tools_max_turns({"max_turns": 12}) == 12
    assert skill_tools_max_turns({"max_turns": 4}) == 8
    assert skill_tools_max_turns({"max_turns": "12"}) == 8


def test_skill_settings_store_merges_workspace_overrides(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("SKILL_MAX_ENTITIES_PER_TYPE", "5000")
    monkeypatch.setenv("SKILL_RETRIEVAL_MODE", "hybrid")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    path = workspace / "ui_skill_settings.json"
    path.write_text(
        json.dumps(
            {
                "max_entities_per_type": 7,
                "retrieval_top_k": 9,
                "ignored": "value",
            }
        ),
        encoding="utf-8",
    )

    store = SkillSettingsStore(lambda: workspace)
    settings = store.read()

    assert settings["max_entities_per_type"] == 7
    assert settings["max_chunks_per_entity"] == 2
    assert settings["retrieval_mode"] == "hybrid"
    assert settings["retrieval_top_k"] == 9
    assert "ignored" not in settings
    assert store.defaults()["max_entities_per_type"] == 500


def test_skill_settings_store_writes_atomically(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    store = SkillSettingsStore(lambda: workspace)

    store.write({"retrieval_mode": "off", "retrieval_top_k": 12})

    assert store.path().exists()
    assert json.loads(store.path().read_text(encoding="utf-8")) == {
        "retrieval_mode": "off",
        "retrieval_top_k": 12,
    }
