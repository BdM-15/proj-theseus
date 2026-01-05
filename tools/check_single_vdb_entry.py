"""Check full VDB entry for a workload table."""
import json
from pathlib import Path

vdb_path = Path('./rag_storage/swa_tas/vdb_entities.json')
with open(vdb_path, 'r', encoding='utf-8') as f:
    vdb = json.load(f)

data = vdb.get('data', [])

# Find a workload table and check its full content
for entry in data:
    if isinstance(entry, dict):
        name = str(entry.get('entity_name', ''))
        if name == 'table_p53':
            print('FULL VDB ENTRY FOR table_p53 (Workload table)')
            print('=' * 60)
            print(f"entity_name: {entry.get('entity_name')}")
            print(f"entity_type: {entry.get('entity_type')}")
            print(f"description length: {len(entry.get('description', ''))}")
            print(f"content length: {len(entry.get('content', ''))}")
            print()
            print('DESCRIPTION:')
            print(entry.get('description', 'N/A')[:1000])
            print()
            print('CONTENT (for embedding):')
            print(entry.get('content', 'N/A')[:1000])
            print()
            print('ALL KEYS IN ENTRY:')
            print(list(entry.keys()))
            break
