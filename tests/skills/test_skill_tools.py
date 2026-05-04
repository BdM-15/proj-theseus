import asyncio

import pytest

from src.core import reset_settings
from src.skills.tools import ToolContext, ToolError, tool_kg_query


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def test_kg_query_reports_unavailable_when_neo4j_is_not_active(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("GRAPH_STORAGE", "NetworkXStorage")
    reset_settings()
    try:
        ctx = ToolContext(
            skill_name="test",
            skill_dir=tmp_path,
            run_dir=tmp_path,
            workspace_dir=tmp_path,
            workspace_name="demo",
        )

        result = _run(tool_kg_query(ctx, "MATCH (n) RETURN n"))

        assert result.payload == {
            "available": False,
            "reason": (
                "GRAPH_STORAGE=NetworkXStorage; kg_query requires Neo4JStorage. "
                "Use kg_entities or kg_chunks instead."
            ),
            "rows": [],
        }
    finally:
        reset_settings()


def test_kg_query_rejects_mutating_cypher_before_config_lookup(tmp_path) -> None:
    ctx = ToolContext(
        skill_name="test",
        skill_dir=tmp_path,
        run_dir=tmp_path,
        workspace_dir=tmp_path,
        workspace_name="demo",
    )

    with pytest.raises(ToolError, match="read-only"):
        _run(tool_kg_query(ctx, "CREATE (n) RETURN n"))

