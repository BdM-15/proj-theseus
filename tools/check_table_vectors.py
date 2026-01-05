#!/usr/bin/env python3
"""Check table_p53 embedding vector validity."""
import json
import base64
import numpy as np

with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find table_p53
for e in data.get('data', []):
    if 'table_p53' in e.get('entity_name', '').lower():
        vector_data = e.get('vector', '')
        print(f"Entity: {e.get('entity_name')}")
        print(f"Vector type: {type(vector_data)}")
        print(f"Vector raw length: {len(vector_data)}")
        
        # Check if it's base64 encoded
        if isinstance(vector_data, str):
            try:
                decoded = base64.b64decode(vector_data)
                arr = np.frombuffer(decoded, dtype=np.float32)
                print(f"Decoded vector dim: {len(arr)}")
                print(f"Sample values: {arr[:5]}")
                print(f"Vector norm: {np.linalg.norm(arr):.4f}")
            except Exception as ex:
                print(f"Decode error: {ex}")
        elif isinstance(vector_data, list):
            print(f"List vector dim: {len(vector_data)}")
            print(f"Sample: {vector_data[:5]}")
        
        # Check content embedding alignment
        content = e.get('content', '')
        print(f"\nContent length: {len(content)} chars")
        print(f"Content preview: {content[:300]}...")
        break

# Also check a few other entities for comparison
print("\n" + "="*60)
print("COMPARISON WITH OTHER ENTITIES")
print("="*60)

table_entities = []
for e in data.get('data', []):
    if e.get('entity_type') == 'table':
        table_entities.append(e)

print(f"\nTotal 'table' type entities: {len(table_entities)}")
for te in table_entities[:5]:
    vec = te.get('vector', '')
    print(f"  {te.get('entity_name')}: vector len={len(vec)}")
