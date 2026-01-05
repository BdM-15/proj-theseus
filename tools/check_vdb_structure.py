"""Check VDB structure and table entity embeddings."""
import json
from pathlib import Path

vdb_path = Path('./rag_storage/swa_tas/vdb_entities.json')
with open(vdb_path, 'r', encoding='utf-8') as f:
    vdb = json.load(f)

print(f"Keys: {list(vdb.keys())}")
print(f"Embedding dim: {vdb.get('embedding_dim')}")

# Check data structure
data = vdb.get('data', {})
print(f"Data type: {type(data)}")
print(f"Data entries: {len(data) if isinstance(data, (dict, list)) else 'N/A'}")

# Check matrix (embeddings)
matrix = vdb.get('matrix', [])
print(f"Matrix type: {type(matrix)}")
print(f"Matrix entries: {len(matrix) if isinstance(matrix, list) else 'N/A'}")

# Sample data entries
if isinstance(data, dict):
    print("\n--- Sample VDB entries ---")
    for i, (k, v) in enumerate(data.items()):
        if i >= 5:
            break
        if isinstance(v, dict):
            entity_name = v.get('entity_name', 'unknown')
            entity_type = v.get('entity_type', 'unknown')
            print(f"  [{entity_type}] {entity_name}")
elif isinstance(data, list):
    print("\n--- Sample VDB entries (list format) ---")
    for i, entry in enumerate(data[:5]):
        if isinstance(entry, dict):
            entity_name = entry.get('entity_name', 'unknown')
            entity_type = entry.get('entity_type', 'unknown')
            print(f"  [{entity_type}] {entity_name}")

# Search for table entries
print("\n--- Searching for 'table' in VDB ---")
table_count = 0
if isinstance(data, dict):
    for k, v in data.items():
        if isinstance(v, dict):
            name = str(v.get('entity_name', '')).lower()
            if 'table_p' in name or 'table ' in name:
                table_count += 1
                if table_count <= 5:
                    print(f"  Found: {v.get('entity_name')}")
elif isinstance(data, list):
    for entry in data:
        if isinstance(entry, dict):
            name = str(entry.get('entity_name', '')).lower()
            if 'table_p' in name or 'table ' in name:
                table_count += 1
                if table_count <= 5:
                    print(f"  Found: {entry.get('entity_name')}")

print(f"\nTotal table entries found: {table_count}")

# Check total entity count
total = len(data) if isinstance(data, (dict, list)) else 0
print(f"Total VDB entities: {total}")
