"""Check VDB relationships structure for entity_type info."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# Check VDB relationships
print('=== VDB Relationships Structure ===')
with open(f'{workspace}/vdb_relationships.json', 'r', encoding='utf-8') as f:
    vdb_rel = json.load(f)

print(f'Keys in VDB relationships: {list(vdb_rel.keys())}')
print(f'Embedding dim: {vdb_rel.get("embedding_dim")}')

data = vdb_rel.get('data', [])
print(f'Total relationships: {len(data)}')

# Check structure of first few relationships
print('\n=== Sample Relationships ===')
for i, rel in enumerate(data[:3]):
    print(f'\n--- Relationship {i+1} ---')
    for k, v in rel.items():
        if k == 'vector':
            print(f'  vector: [embedding...]')
        elif isinstance(v, str) and len(v) > 200:
            print(f'  {k}: {v[:200]}...')
        else:
            print(f'  {k}: {v}')

# Look for relationships that mention Appendix H
print('\n=== Relationships mentioning Appendix H ===')
found = 0
for rel in data:
    content = rel.get('content', '')
    if 'appendix h' in content.lower() or 'h.2' in content.lower():
        print(f'\nSrc: {rel.get("src_id")}')
        print(f'Tgt: {rel.get("tgt_id")}')
        print(f'Keywords: {rel.get("keywords")}')
        print(f'Content preview: {content[:200]}')
        found += 1
        if found >= 3:
            break
