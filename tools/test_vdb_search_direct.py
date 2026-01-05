"""
Direct VDB Semantic Search Test
================================

Directly test what entities are retrieved for workload queries
without full LightRAG initialization.
"""

import asyncio
import json
import os
import sys
import zlib
import base64
from pathlib import Path
import numpy as np

from dotenv import load_dotenv
load_dotenv()

# Setup embedding
from openai import AsyncOpenAI

embed_client = AsyncOpenAI(
    api_key=os.getenv("EMBEDDING_BINDING_API_KEY"),
    base_url=os.getenv("EMBEDDING_BINDING_HOST")
)
embedding_model = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))


async def embed_query(text: str) -> list[float]:
    """Embed a query string."""
    response = await embed_client.embeddings.create(
        model=embedding_model,
        input=[text],
        dimensions=embedding_dim
    )
    return response.data[0].embedding


def decode_embedding(encoded: str) -> np.ndarray:
    """Decode VDB embedding from compressed format."""
    decoded = base64.b64decode(encoded)
    decompressed = zlib.decompress(decoded)
    return np.frombuffer(decompressed, dtype=np.float16).astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


async def test_semantic_search():
    """Test semantic search against entity embeddings."""
    
    workspace = os.getenv("WORKSPACE", "swa_tas")
    vdb_path = f"./rag_storage/{workspace}/vdb_entities.json"
    
    print("=" * 80)
    print("DIRECT VDB SEMANTIC SEARCH TEST")
    print("=" * 80)
    print(f"\nWorkspace: {workspace}")
    print(f"VDB Path: {vdb_path}")
    
    # Load VDB
    with open(vdb_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    data_points = vdb_data.get("data", [])
    print(f"Total entities: {len(data_points)}")
    
    # Pre-decode all embeddings
    print("\nDecoding entity embeddings...")
    entities = []
    for dp in data_points:
        try:
            embedding = decode_embedding(dp["vector"])
            entities.append({
                "entity_name": dp.get("entity_name", "?"),
                "content": dp.get("content", ""),
                "embedding": embedding
            })
        except Exception as e:
            print(f"Error decoding {dp.get('entity_name', '?')}: {e}")
    
    print(f"Decoded {len(entities)} entity embeddings")
    
    # Test queries (these simulate what LightRAG would search for as ll_keywords)
    test_queries = [
        # Simulated ll_keywords that would be extracted
        "workload, ADAB, Al Dhafra, aircraft, monthly",
        "aircraft quantities, C-17, C-130, visits",
        "Appendix H, workload data, estimated monthly",
        "table, H.2.0, aircraft schedule, ADAB",
        # More specific
        "760 aircraft, annual total, ADAB workload",
        "estimated monthly aircraft visits Al Dhafra",
        # Direct entity content matches
        "H.2.0 Estimated Monthly Workload Data ADAB",
        "table_p53",
    ]
    
    top_k = 10
    cosine_threshold = 0.2  # LightRAG default
    
    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"Search Query: '{query}'")
        print(f"{'─'*80}")
        
        # Embed query
        query_embedding = np.array(await embed_query(query))
        
        # Calculate similarities
        results = []
        for entity in entities:
            sim = cosine_similarity(query_embedding, entity["embedding"])
            if sim >= cosine_threshold:
                results.append({
                    "entity_name": entity["entity_name"],
                    "content_preview": entity["content"][:150],
                    "similarity": sim
                })
        
        # Sort by similarity
        results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # Show top results
        print(f"\nResults above threshold ({cosine_threshold}): {len(results)}")
        print(f"\nTop {top_k} matches:")
        for i, r in enumerate(results[:top_k], 1):
            print(f"\n  {i}. {r['entity_name']} (sim: {r['similarity']:.4f})")
            print(f"     Content: {r['content_preview']}...")
        
        # Check if key table entities are in results
        table_entities = [r for r in results if 'table_p53' in r['entity_name'] or 
                                               'table_p54' in r['entity_name'] or
                                               'H.2.0' in r['entity_name'] or
                                               'workload' in r['entity_name'].lower()]
        
        if table_entities:
            print(f"\n  ✅ Found {len(table_entities)} workload/table entities in results")
            for te in table_entities[:3]:
                print(f"     - {te['entity_name']} @ rank {results.index(te)+1} (sim: {te['similarity']:.4f})")
        else:
            print(f"\n  ❌ NO workload/table entities found above threshold!")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_semantic_search())
