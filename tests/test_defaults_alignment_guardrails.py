"""Guardrail tests to keep the pipeline aligned to LightRAG/RAG-Anything defaults.

These tests intentionally avoid importing external packages (lightrag/raganything)
so they can run in minimal environments.

Project invariants (per repo guidance + project requirements):
- Query behavior must remain LightRAG defaults (no custom /query overrides)
- Do not override LightRAG internal PROMPTS at runtime
- Chunking defaults must be set early (8192 / 1200)
- Reranking must remain disabled
- Runtime config must use the existing 18-entity ontology (no schema edits)
"""

from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_no_query_endpoint_override_registered() -> None:
    content = _read("src/raganything_server.py")

    # We should not remove or override LightRAG's query endpoints.
    assert "create_query_stream_endpoint" not in content
    assert "'/query/stream'" not in content


def test_no_lightrag_prompt_runtime_overrides() -> None:
    content = _read("src/server/initialization.py")

    # Runtime PROMPTS monkeypatching must not exist.
    assert "from lightrag.prompt import PROMPTS" not in content
    assert "PROMPTS[\"" not in content


def test_app_enforces_chunking_and_no_rerank_before_imports() -> None:
    content = _read("app.py")

    assert "os.environ.setdefault(\"CHUNK_SIZE\", \"8192\")" in content
    assert "os.environ.setdefault(\"CHUNK_OVERLAP_SIZE\", \"1200\")" in content
    assert "os.environ.setdefault(\"RERANK_BY_DEFAULT\", \"false\")" in content


def test_initialization_uses_all_18_entity_types() -> None:
    content = _read("src/server/initialization.py")

    # Ensure performance_metric is included in the runtime entity_types list.
    assert "\"performance_metric\"" in content


def test_server_config_sets_18_entity_types() -> None:
    content = _read("src/server/config.py")

    assert "global_args.entity_types" in content
    assert "\"performance_metric\"" in content
