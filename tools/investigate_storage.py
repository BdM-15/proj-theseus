"""Investigate where entity_type is actually stored."""
import os
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# List all files to find graph storage
print('Files in workspace:')
for f in sorted(os.listdir(workspace)):
    fpath = os.path.join(workspace, f)
    size = os.path.getsize(fpath)
    print(f'  {f}: {size:,} bytes')

# Check for graph files
graph_files = [f for f in os.listdir(workspace) if 'graph' in f.lower()]
print(f'\nGraph files: {graph_files}')

# If there's a graph file, check its structure
for gf in graph_files:
    print(f'\n=== Checking {gf} ===')
    try:
        with open(os.path.join(workspace, gf), 'r', encoding='utf-8') as f:
            first_1000 = f.read(1000)
            print(first_1000)
    except:
        print('Could not read as text')

# Check relation_chunks for relationship structure
print('\n=== relation_chunks sample ===')
with open(f'{workspace}/kv_store_relation_chunks.json', 'r', encoding='utf-8') as f:
    relation_chunks = json.load(f)

print(f'Total relation mappings: {len(relation_chunks)}')
for name, data in list(relation_chunks.items())[:3]:
    print(f'\nRelation: {name}')
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, list):
                print(f'  {k}: {v[:3]}...' if len(v) > 3 else f'  {k}: {v}')
            else:
                print(f'  {k}: {v}')
