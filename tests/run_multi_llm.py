import sys
import types
import os
import asyncio
import pathlib

# Ensure project root is on sys.path so `import src.server.initialization` works
PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def make_fake_lightrag(calls):
    # top-level package
    lightrag = types.ModuleType("lightrag")

    # api.config.global_args
    api = types.ModuleType("lightrag.api")
    config = types.ModuleType("lightrag.api.config")

    class GlobalArgs:
        def __init__(self):
            self.working_dir = os.getenv("WORKING_DIR", "./rag_storage")

    config.global_args = GlobalArgs()
    api.config = config
    lightrag.api = api

    # llm.openai
    llm = types.ModuleType("lightrag.llm")
    openai_mod = types.ModuleType("lightrag.llm.openai")

    async def openai_complete_if_cache(model, prompt, **kwargs):
        calls.append(model)
        return f"fake-result:{model}"

    async def openai_embed(texts, model="text-embedding-3-large", **kwargs):
        return [[0.0] * int(os.getenv("EMBEDDING_DIM", "3072")) for _ in texts]

    openai_mod.openai_complete_if_cache = openai_complete_if_cache
    openai_mod.openai_embed = openai_embed
    llm.openai = openai_mod
    lightrag.llm = llm

    # base.QueryParam (simple placeholder)
    base = types.ModuleType("lightrag.base")

    class QueryParam:
        def __init__(self, **kwargs):
            self.model_func = kwargs.get("model_func")

    base.QueryParam = QueryParam
    # Minimal DocStatus enum-like class expected by initialization compatibility wrapper
    class _StatusObj:
        def __init__(self, value):
            self.value = value

    class DocStatus:
        PENDING = _StatusObj("pending")
        PROCESSING = _StatusObj("processing")
        PREPROCESSED = _StatusObj("multimodal_processed")
        PROCESSED = _StatusObj("processed")
        FAILED = _StatusObj("failed")

    base.DocStatus = DocStatus
    lightrag.base = base

    # utils.EmbeddingFunc
    utils = types.ModuleType("lightrag.utils")

    class EmbeddingFunc:
        def __init__(self, embedding_dim, max_token_size, func):
            self.embedding_dim = embedding_dim
            self.max_token_size = max_token_size
            self.func = func

        async def __call__(self, texts):
            return await self.func(texts)

    utils.EmbeddingFunc = EmbeddingFunc
    lightrag.utils = utils

    sys.modules["lightrag"] = lightrag
    sys.modules["lightrag.api"] = api
    sys.modules["lightrag.api.config"] = config
    sys.modules["lightrag.llm"] = llm
    sys.modules["lightrag.llm.openai"] = openai_mod
    sys.modules["lightrag.utils"] = utils
    sys.modules["lightrag.base"] = base


def make_fake_raganything():
    rag = types.ModuleType("raganything")

    class DummyRAGAnything:
        def __init__(self, config=None, llm_model_func=None, vision_model_func=None, embedding_func=None, lightrag_kwargs=None):
            self.config = config
            self.llm_model_func = llm_model_func
            self.vision_model_func = vision_model_func
            self.embedding_func = embedding_func
            class DocStatus:
                async def upsert(self, data):
                    return True

                async def get_by_id(self, doc_id):
                    return {}

                async def get_docs_paginated(self, *args, **kwargs):
                    return ([], 0)

            class LightRAG:
                def __init__(self):
                    self.doc_status = DocStatus()

                async def aquery(self, query, param=None):
                    mf = getattr(param, "model_func", None)
                    if mf:
                        return await mf("test-prompt")
                    return "no-model"

            self.lightrag = LightRAG()

        async def _ensure_lightrag_initialized(self):
            return {"success": True}

    class DummyConfig:
        def __init__(self, **kwargs):
            # accept any config kwargs
            for k, v in kwargs.items():
                setattr(self, k, v)

    rag.RAGAnything = DummyRAGAnything
    rag.RAGAnythingConfig = DummyConfig
    sys.modules["raganything"] = rag


def run_test():
    calls = []

    make_fake_lightrag(calls)
    make_fake_raganything()

    os.environ.setdefault("EXTRACTION_LLM_NAME", "grok-4-fast-non-reasoning")
    os.environ.setdefault("REASONING_LLM_NAME", "grok-4-fast-reasoning")

    from src.server.initialization import initialize_raganything, get_rag_instance

    asyncio.run(initialize_raganything())

    rag = get_rag_instance()
    if rag is None:
        raise SystemExit("RAG-Anything not initialized")

    res_extraction = asyncio.run(rag.llm_model_func("dummy prompt"))
    expected_extraction = f"fake-result:{os.environ['EXTRACTION_LLM_NAME']}"
    print("extraction ->", res_extraction)
    if res_extraction != expected_extraction:
        raise SystemExit(f"Extraction model mismatch: {res_extraction} != {expected_extraction}")

    res_query = asyncio.run(rag.lightrag.aquery("what's up?"))
    expected_query = f"fake-result:{os.environ['REASONING_LLM_NAME']}"
    print("query ->", res_query)
    if res_query != expected_query:
        raise SystemExit(f"Query model mismatch: {res_query} != {expected_query}")

    if os.environ["EXTRACTION_LLM_NAME"] not in calls or os.environ["REASONING_LLM_NAME"] not in calls:
        raise SystemExit(f"Calls missing: {calls}")

    print("OK: dual-LLM wiring validated")


if __name__ == "__main__":
    run_test()
