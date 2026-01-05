#!/usr/bin/env python3
"""
Deep diagnosis: Why isn't table_p53 being retrieved even with high token budgets?

Check if the issue is:
1. VDB embedding search not ranking table_p53 high enough
2. Entity not properly indexed in VDB
3. Graph traversal not reaching it
"""

import json
from pathlib import Path

def check_vdb_entity_structure(workspace: str = "swa_tas"):
    """Check if table_p53 is properly indexed in VDB."""
    
    print("=" * 70)
    print("VDB ENTITY INDEX CHECK")
    print("=" * 70)
    
    vdb_path = Path(f"rag_storage/{workspace}/vdb_entities.json")
    
    with open(vdb_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    print(f"\nVDB structure keys: {list(vdb_data.keys())}")
    print(f"Embedding dimension: {vdb_data.get('embedding_dim', 'N/A')}")
    
    data = vdb_data.get('data', [])
    print(f"Total indexed entities: {len(data)}")
    
    # Check structure of first entry
    if data:
        first = data[0]
        print(f"\nEntry format: {type(first)}")
        if isinstance(first, dict):
            print(f"Keys: {list(first.keys())}")
        elif isinstance(first, list):
            print(f"List length: {len(first)}")
            for i, elem in enumerate(first):
                if isinstance(elem, list) and len(elem) > 100:
                    print(f"  [{i}] Embedding vector: {len(elem)} dims")
                elif isinstance(elem, str):
                    print(f"  [{i}] String: {elem[:60]}...")
                else:
                    print(f"  [{i}] {type(elem).__name__}")
    
    # Find table_p53 specifically
    print("\n" + "-" * 70)
    print("SEARCHING FOR table_p53 IN VDB")
    print("-" * 70)
    
    table_p53_entry = None
    table_p53_has_embedding = False
    
    for entry in data:
        # Handle both dict and list formats
        if isinstance(entry, dict):
            entity_name = entry.get('entity_name', '')
            has_embedding = 'embedding' in entry or '__vector__' in entry
        elif isinstance(entry, list):
            entity_name = entry[0] if entry else ''
            # Check if there's a vector (list of floats)
            has_embedding = any(isinstance(e, list) and len(e) > 100 for e in entry)
        else:
            continue
        
        if 'table_p53' in str(entity_name).lower():
            table_p53_entry = entry
            table_p53_has_embedding = has_embedding
            break
    
    if table_p53_entry:
        print(f"✅ table_p53 FOUND in VDB index")
        print(f"   Has embedding: {table_p53_has_embedding}")
        
        if isinstance(table_p53_entry, dict):
            print(f"   Entity name: {table_p53_entry.get('entity_name', 'N/A')}")
            print(f"   Content length: {len(table_p53_entry.get('content', ''))}")
        elif isinstance(table_p53_entry, list):
            print(f"   Entry ID: {table_p53_entry[0]}")
            # Find content string
            for elem in table_p53_entry:
                if isinstance(elem, str) and len(elem) > 100:
                    print(f"   Content preview: {elem[:200]}...")
                    break
    else:
        print("❌ table_p53 NOT FOUND in VDB index!")
        print("   This explains why retrieval fails - entity isn't searchable!")

def check_graph_storage(workspace: str = "swa_tas"):
    """Check if table_p53 is in graph storage (separate from VDB)."""
    
    print("\n" + "=" * 70)
    print("GRAPH STORAGE CHECK")
    print("=" * 70)
    
    # Check graph JSON files
    graph_files = [
        "graph_chunk_entity_relation.json",
        "kv_store_llm_response_cache.json",
        "kv_store_full_docs.json",
        "kv_store_text_chunks.json"
    ]
    
    base = Path(f"rag_storage/{workspace}")
    
    for gf in graph_files:
        gf_path = base / gf
        if gf_path.exists():
            with open(gf_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # Search for table_p53
                    data_str = json.dumps(data)
                    if 'table_p53' in data_str.lower():
                        print(f"✅ {gf}: Contains table_p53 reference")
                    else:
                        print(f"⚪ {gf}: No table_p53 reference")
                except:
                    print(f"⚠️ {gf}: Could not parse")
        else:
            print(f"❌ {gf}: File not found")

def check_chunk_entity_mapping(workspace: str = "swa_tas"):
    """Check if chunks are properly associated with table_p53 entity."""
    
    print("\n" + "=" * 70)
    print("CHUNK-ENTITY MAPPING CHECK")
    print("=" * 70)
    
    base = Path(f"rag_storage/{workspace}")
    
    # Load chunk-entity relation
    rel_path = base / "graph_chunk_entity_relation.json"
    if rel_path.exists():
        with open(rel_path, 'r', encoding='utf-8') as f:
            relations = json.load(f)
        
        print(f"Total chunk-entity relations: {len(relations)}")
        
        # Find relations involving table_p53
        table_relations = []
        for key, value in relations.items():
            if 'table_p53' in str(key).lower() or 'table_p53' in str(value).lower():
                table_relations.append((key, value))
        
        print(f"Relations involving table_p53: {len(table_relations)}")
        for k, v in table_relations[:5]:
            print(f"   {str(k)[:40]} -> {str(v)[:40]}")
    else:
        print("❌ graph_chunk_entity_relation.json not found")
    
    # Check text chunks for workload data
    chunks_path = base / "kv_store_text_chunks.json"
    if chunks_path.exists():
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"\nTotal text chunks: {len(chunks)}")
        
        # Find chunks with H.2.0 or workload table data
        workload_chunks = []
        for chunk_id, chunk_data in chunks.items():
            content = str(chunk_data).lower()
            if any(term in content for term in ['h.2.0', '760 aircraft', 'c-17', 'c-130', 'estimated monthly']):
                workload_chunks.append({
                    'id': chunk_id,
                    'preview': str(chunk_data)[:200]
                })
        
        print(f"Chunks with workload table data: {len(workload_chunks)}")
        for c in workload_chunks[:3]:
            print(f"\n   Chunk: {c['id'][:50]}")
            print(f"   Preview: {c['preview'][:150]}...")

def check_vdb_chunks(workspace: str = "swa_tas"):
    """Check if workload chunks are in the VDB."""
    
    print("\n" + "=" * 70)
    print("VDB CHUNKS CHECK")
    print("=" * 70)
    
    vdb_chunks_path = Path(f"rag_storage/{workspace}/vdb_chunks.json")
    
    if not vdb_chunks_path.exists():
        print("❌ vdb_chunks.json not found")
        return
    
    with open(vdb_chunks_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    data = vdb_data.get('data', [])
    print(f"Total chunks in VDB: {len(data)}")
    
    # Find chunks with workload data
    workload_chunks = []
    for entry in data:
        # Get content from entry
        content = ""
        if isinstance(entry, dict):
            content = entry.get('content', '')
        elif isinstance(entry, list):
            for elem in entry:
                if isinstance(elem, str) and len(elem) > 50:
                    content = elem
                    break
        
        if any(term in content.lower() for term in ['760', 'c-17', 'c-130', 'estimated monthly workload']):
            chunk_id = entry[0] if isinstance(entry, list) else entry.get('id', 'N/A')
            workload_chunks.append({
                'id': str(chunk_id)[:60],
                'content': content[:300]
            })
    
    print(f"Chunks with actual workload numbers: {len(workload_chunks)}")
    for c in workload_chunks[:5]:
        print(f"\n   ID: {c['id']}")
        print(f"   Content: {c['content'][:200]}...")

def main():
    print("=" * 70)
    print("DEEP RETRIEVAL DIAGNOSIS")
    print("Why isn't table_p53 being retrieved with 40K token budget?")
    print("=" * 70)
    
    check_vdb_entity_structure()
    check_graph_storage()
    check_chunk_entity_mapping()
    check_vdb_chunks()
    
    print("\n" + "=" * 70)
    print("DIAGNOSIS COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
