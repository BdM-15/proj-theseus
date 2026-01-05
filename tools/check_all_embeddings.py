#!/usr/bin/env python3
"""Check ALL entity embeddings for corruption."""
import json
import base64
import numpy as np

with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

expected_dim = data.get('embedding_dim', 3072)
print(f"Expected embedding dimension: {expected_dim}")
print("="*60)

valid_count = 0
invalid_count = 0
invalid_entities = []

for e in data.get('data', []):
    entity_name = e.get('entity_name', 'unknown')
    entity_type = e.get('entity_type', 'unknown')
    vector_data = e.get('vector', '')
    
    if isinstance(vector_data, str) and len(vector_data) > 0:
        try:
            decoded = base64.b64decode(vector_data)
            arr = np.frombuffer(decoded, dtype=np.float32)
            
            # Check validity
            is_valid = (
                len(arr) == expected_dim and 
                np.isfinite(arr).all() and
                np.linalg.norm(arr) > 0.1 and
                np.linalg.norm(arr) < 100
            )
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                reason = []
                if len(arr) != expected_dim:
                    reason.append(f"dim={len(arr)}")
                if not np.isfinite(arr).all():
                    reason.append("has inf/nan")
                norm = np.linalg.norm(arr)
                if norm < 0.1 or norm > 100:
                    reason.append(f"norm={norm:.4f}")
                invalid_entities.append({
                    'name': entity_name,
                    'type': entity_type,
                    'reason': ', '.join(reason)
                })
        except Exception as ex:
            invalid_count += 1
            invalid_entities.append({
                'name': entity_name,
                'type': entity_type,
                'reason': f"decode error: {ex}"
            })
    elif isinstance(vector_data, list):
        if len(vector_data) == expected_dim:
            valid_count += 1
        else:
            invalid_count += 1
            invalid_entities.append({
                'name': entity_name,
                'type': entity_type,
                'reason': f"list dim={len(vector_data)}"
            })
    else:
        invalid_count += 1
        invalid_entities.append({
            'name': entity_name,
            'type': entity_type,
            'reason': "no vector"
        })

print(f"\nValid embeddings: {valid_count}")
print(f"Invalid embeddings: {invalid_count}")
print(f"\nInvalid entities ({len(invalid_entities)}):")
print("-"*60)

# Group by entity type
by_type = {}
for ie in invalid_entities:
    et = ie['type']
    if et not in by_type:
        by_type[et] = []
    by_type[et].append(ie)

for etype, entities in sorted(by_type.items()):
    print(f"\n[{etype}] - {len(entities)} invalid:")
    for ie in entities[:10]:
        print(f"  {ie['name'][:45]}: {ie['reason']}")
    if len(entities) > 10:
        print(f"  ... and {len(entities)-10} more")
