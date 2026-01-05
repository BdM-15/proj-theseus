"""
Trace LightRAG Keyword Extraction → VDB Search
================================================

Tests what keywords are extracted from workload queries
and whether they would match table entity content.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()  # MUST load before importing LightRAG

from lightrag import LightRAG
from lightrag.utils import EmbeddingFunc


async def trace_keyword_extraction():
    """Trace what keywords are extracted for workload queries."""
    
    # Initialize LightRAG to get its query infrastructure
    workspace = os.getenv("WORKSPACE", "swa_tas")
    working_dir = f"./rag_storage/{workspace}"
    
    print("=" * 80)
    print("KEYWORD EXTRACTION TRACE - What LightRAG searches for")
    print("=" * 80)
    print(f"\nWorkspace: {workspace}")
    
    # Setup embedding function (same as server does)
    from openai import AsyncOpenAI
    embed_client = AsyncOpenAI(
        api_key=os.getenv("EMBEDDING_BINDING_API_KEY"),
        base_url=os.getenv("EMBEDDING_BINDING_HOST")
    )
    embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    async def openai_embed(texts: list[str], **kwargs) -> list[list[float]]:
        response = await embed_client.embeddings.create(
            model=embedding_model,
            input=texts,
            dimensions=embedding_dim
        )
        return [r.embedding for r in response.data]
    
    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,
        func=openai_embed
    )
    
    # Test queries
    test_queries = [
        "What is the workload at ADAB?",
        "What are the aircraft quantities?",
        "How many C-17 and C-130 visits per month?",
        "What's in Appendix H workload data?",
        "What are the estimated monthly aircraft visits at Al Dhafra?",
    ]
    
    # Initialize RAG
    rag = LightRAG(working_dir=working_dir, embedding_func=embedding_func)
    await rag.initialize_storages()
    
    # Get the keyword extraction function
    from lightrag.operate import get_keywords_from_query
    from lightrag.base import QueryParam
    
    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Query: '{query}'")
        print(f"{'─'*80}")
        
        query_param = QueryParam(mode="local")
        
        try:
            # Extract keywords the same way LightRAG does
            hl_keywords, ll_keywords = await get_keywords_from_query(
                query,
                query_param,
                rag.global_config,
                None  # No cache
            )
            
            print(f"\nHigh-level keywords: {hl_keywords}")
            print(f"Low-level keywords:  {ll_keywords}")
            
            # Test what VDB would return for these keywords
            print(f"\n→ VDB searches for entities matching: '{ll_keywords}'")
            
            # Actually query the VDB
            results = await rag.entities_vdb.query(ll_keywords, top_k=10)
            
            print(f"\nTop 10 Entity Matches:")
            for i, r in enumerate(results, 1):
                entity_name = r.get("entity_name", "?")
                distance = r.get("distance", "?")
                content_preview = r.get("content", "")[:100] + "..."
                print(f"  {i}. {entity_name} (score: {distance:.4f})")
                
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    await rag.finalize_storages()
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(trace_keyword_extraction())
