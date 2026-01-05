"""Test when RAGAnything creates its context_extractor."""
import asyncio
import os
from raganything import RAGAnything, RAGAnythingConfig

os.environ["CONTEXT_WINDOW"] = "2"
os.environ["CONTEXT_MODE"] = "page"

async def test():
    config = RAGAnythingConfig(
        working_dir='./rag_storage/test_ctx',
    )
    
    async def dummy_llm(prompt, **kwargs):
        return 'test'
    
    async def dummy_embed(texts):
        return [[0.0] * 3072 for _ in texts]
    
    from lightrag.utils import EmbeddingFunc
    embed_func = EmbeddingFunc(embedding_dim=3072, max_token_size=8192, func=dummy_embed)
    
    rag = RAGAnything(config=config, llm_model_func=dummy_llm, embedding_func=embed_func)
    
    print('Before _ensure_lightrag_initialized():')
    print(f'  context_extractor: {rag.context_extractor}')
    print(f'  modal_processors: {list(rag.modal_processors.keys()) if rag.modal_processors else None}')
    
    await rag._ensure_lightrag_initialized()
    
    print('\nAfter _ensure_lightrag_initialized():')
    print(f'  context_extractor: {rag.context_extractor}')
    print(f'  modal_processors: {list(rag.modal_processors.keys()) if rag.modal_processors else None}')
    
    # Check if context_extractor has config
    if rag.context_extractor:
        print(f'  context_config: window={rag.context_extractor.config.context_window}, mode={rag.context_extractor.config.context_mode}')
    
    # Check table processor
    if 'table' in rag.modal_processors:
        tp = rag.modal_processors['table']
        print(f'\nTable processor context_extractor: {tp.context_extractor}')
        if tp.context_extractor:
            print(f'  Has tokenizer: {tp.context_extractor.tokenizer is not None}')

asyncio.run(test())
