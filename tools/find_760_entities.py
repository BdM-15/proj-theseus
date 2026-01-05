#!/usr/bin/env python
"""
Deep dive into which entities contain "760" and why they're not consistently retrieved.
"""

import json
import base64
import zlib
import numpy as np
from pathlib import Path


def load_vdb(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def decode_vector(vector_str: str) -> np.ndarray:
    """Decode Float16+zlib+Base64 compressed vector."""
    decoded = base64.b64decode(vector_str)
    decompressed = zlib.decompress(decoded)
    vector_f16 = np.frombuffer(decompressed, dtype=np.float16)
    return vector_f16.astype(np.float32)


def find_760_entities(vdb_path: str):
    """Find all entities containing '760' in their content."""
    vdb = load_vdb(vdb_path)
    entities = vdb.get("data", [])
    
    print(f"Searching {len(entities)} entities for '760'...\n")
    
    found = []
    for entity in entities:
        content = entity.get("content", "")
        entity_name = entity.get("entity_name", "")
        
        if "760" in content:
            found.append({
                "name": entity_name,
                "content_preview": content[:500],
                "content_length": len(content),
            })
    
    print(f"Found {len(found)} entities containing '760':\n")
    for i, e in enumerate(found):
        print(f"\n{'='*60}")
        print(f"[{i+1}] Entity: {e['name']}")
        print(f"Content length: {e['content_length']} chars")
        print(f"Content preview:\n{e['content_preview']}")
    
    return found


def find_total_entities(vdb_path: str):
    """Find entities containing 'total' and aircraft-related terms."""
    vdb = load_vdb(vdb_path)
    entities = vdb.get("data", [])
    
    print(f"\n\n{'='*60}")
    print("Searching for entities with 'annual total' or 'grand total'...")
    print("="*60)
    
    found = []
    for entity in entities:
        content = entity.get("content", "").lower()
        entity_name = entity.get("entity_name", "")
        
        if ("annual total" in content or "grand total" in content) and "aircraft" in content:
            full_content = entity.get("content", "")
            found.append({
                "name": entity_name,
                "content": full_content,
                "content_length": len(full_content),
            })
    
    print(f"\nFound {len(found)} entities with aircraft totals:\n")
    for i, e in enumerate(found):
        print(f"\n{'='*60}")
        print(f"[{i+1}] Entity: {e['name']}")
        print(f"Content length: {e['content_length']} chars")
        print(f"Content:\n{e['content'][:800]}")
    
    return found


def analyze_table_p53(vdb_path: str):
    """Detailed analysis of table_p53 entity."""
    vdb = load_vdb(vdb_path)
    entities = vdb.get("data", [])
    
    print(f"\n\n{'='*60}")
    print("DETAILED ANALYSIS OF table_p53")
    print("="*60)
    
    for entity in entities:
        if entity.get("entity_name", "") == "table_p53":
            content = entity.get("content", "")
            print(f"\nEntity name: {entity.get('entity_name')}")
            print(f"Content length: {len(content)} chars")
            print(f"\nFULL CONTENT:\n{content}")
            
            # Check for specific numbers
            print(f"\n--- KEY DATA PRESENCE ---")
            print(f"Contains '760': {'760' in content}")
            print(f"Contains '271': {'271' in content}")
            print(f"Contains '224': {'224' in content}")
            print(f"Contains 'C-17': {'C-17' in content}")
            print(f"Contains 'C-130': {'C-130' in content}")
            print(f"Contains 'grand total': {'grand total' in content.lower()}")
            print(f"Contains 'annual total': {'annual total' in content.lower()}")
            return entity
    
    print("table_p53 NOT FOUND!")
    return None


def check_h20_entities(vdb_path: str):
    """Check H.2.0 related entities."""
    vdb = load_vdb(vdb_path)
    entities = vdb.get("data", [])
    
    print(f"\n\n{'='*60}")
    print("H.2.0 RELATED ENTITIES")
    print("="*60)
    
    h20_entities = []
    for entity in entities:
        entity_name = entity.get("entity_name", "")
        if "h.2.0" in entity_name.lower() or "h2.0" in entity_name.lower():
            h20_entities.append(entity)
    
    print(f"\nFound {len(h20_entities)} H.2.0 entities:\n")
    for e in h20_entities:
        name = e.get("entity_name", "")
        content = e.get("content", "")
        print(f"\n--- {name} ---")
        print(f"Length: {len(content)} chars")
        print(f"Contains '760': {'760' in content}")
        print(f"Preview: {content[:300]}...")
    
    return h20_entities


if __name__ == "__main__":
    vdb_path = "rag_storage/swa_tas/vdb_entities.json"
    
    # Find entities with 760
    entities_760 = find_760_entities(vdb_path)
    
    # Find entities with totals
    total_entities = find_total_entities(vdb_path)
    
    # Analyze table_p53 specifically
    table_p53 = analyze_table_p53(vdb_path)
    
    # Check H.2.0 entities
    h20_entities = check_h20_entities(vdb_path)
