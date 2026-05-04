from types import SimpleNamespace

import pytest

from src.skills.llm_chat import _client_kwargs, _resolve_model


def test_client_kwargs_uses_centralized_llm_settings() -> None:
    settings = SimpleNamespace(
        llm_binding_api_key=" key ",
        llm_binding_host=" https://example.test/v1 ",
    )

    assert _client_kwargs(lambda: settings) == {
        "api_key": "key",
        "base_url": "https://example.test/v1",
    }


def test_client_kwargs_requires_api_key() -> None:
    settings = SimpleNamespace(
        llm_binding_api_key="",
        llm_binding_host="https://example.test/v1",
    )

    with pytest.raises(RuntimeError, match="LLM_BINDING_API_KEY"):
        _client_kwargs(lambda: settings)


def test_resolve_model_uses_reasoning_model_setting() -> None:
    settings = SimpleNamespace(reasoning_llm_name=" grok-reasoning ")

    assert _resolve_model(lambda: settings) == "grok-reasoning"


def test_resolve_model_requires_reasoning_model_setting() -> None:
    settings = SimpleNamespace(reasoning_llm_name="")

    with pytest.raises(RuntimeError, match="QUERY_LLM_MODEL"):
        _resolve_model(lambda: settings)
