import os
import asyncio
import pytest


def test_llm_extraction_and_query_override(monkeypatch):
    async def _inner():
        """
        Async inner function so the test runner doesn't require pytest-asyncio.
        """

        calls = []

        async def fake_openai_complete_if_cache(model, prompt, **kwargs):
            # record model names called
            calls.append(model)
            return f"fake-result:{model}"

        # Patch the LLM helper used by our initialization module
        monkeypatch.setattr("lightrag.llm.openai.openai_complete_if_cache", fake_openai_complete_if_cache)

        # Dummy doc status used by compatibility wrappers
        class DummyDocStatus:
            async def upsert(self, data):
                return True

            async def get_by_id(self, doc_id):
                return {}

            async def get_docs_paginated(self, *args, **kwargs):
                return ([], 0)

        # Dummy LightRAG instance with aquery that will call the provided model_func
        class DummyLightRAG:
            def __init__(self):
                self.doc_status = DummyDocStatus()

            async def aquery(self, query, param=None):
                # If a QueryParam with model_func is provided, call it to simulate LLM use
                mf = getattr(param, "model_func", None)
                if mf:
                    return await mf("test-prompt")
                return "no-model"

        # Dummy RAGAnything that stores the callables passed during construction
        class DummyRAGAnything:
            def __init__(self, config=None, llm_model_func=None, vision_model_func=None, embedding_func=None, lightrag_kwargs=None):
                self.config = config
                self.llm_model_func = llm_model_func
                self.vision_model_func = vision_model_func
                self.embedding_func = embedding_func
                self.lightrag = DummyLightRAG()

            async def _ensure_lightrag_initialized(self):
                return {"success": True}

        # Dummy config placeholder
        class DummyConfig:
            pass

        # Patch raganything classes to our dummies
        monkeypatch.setattr("raganything.RAGAnything", DummyRAGAnything)
        monkeypatch.setattr("raganything.RAGAnythingConfig", DummyConfig)

        # Ensure env vars are set for the test
        os.environ.setdefault("EXTRACTION_LLM_NAME", "grok-4-fast-non-reasoning")
        os.environ.setdefault("REASONING_LLM_NAME", "grok-4-fast-reasoning")

        # Import and run initialization
        from src.server.initialization import initialize_raganything, get_rag_instance

        await initialize_raganything()

        rag = get_rag_instance()
        assert rag is not None, "RAG-Anything instance should be initialized"

        # Test: call the stored extraction callable directly
        # The DummyRAGAnything stored the extraction callable on attribute llm_model_func
        assert hasattr(rag, "llm_model_func")
        res_extraction = await rag.llm_model_func("dummy prompt")
        assert res_extraction == f"fake-result:{os.environ['EXTRACTION_LLM_NAME']}"

        # Test: calling aquery without providing a per-query model should use reasoning LLM
        # This will trigger our wrapped aquery which injects the reasoning model as param.model_func
        result_query = await rag.lightrag.aquery("what's up?")
        assert result_query == f"fake-result:{os.environ['REASONING_LLM_NAME']}"

        # Verify the sequence of model calls recorded
        assert os.environ["EXTRACTION_LLM_NAME"] in calls
        assert os.environ["REASONING_LLM_NAME"] in calls

    asyncio.run(_inner())
