"""Check what entities are actually in LightRAG's vector database."""
import json

# Check entities in the vector DB
with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    db = json.load(f)

print(f'Total entities with embeddings: {len(db["data"])}')
print()
print('WORKLOAD-RELATED ENTITIES IN VDB:')
print('='*60)
found = False
for entity in db['data']:
    name = entity.get('entity_name', '')
    content = entity.get('content', '')
    if 'workload' in name.lower() or 'workload' in content.lower() or 'aircraft operations' in name.lower():
        found = True
        print(f'Entity: {name}')
        print(f'Content preview: {content[:400]}...')
        print()

if not found:
    print('(NONE FOUND!)')

print()
print('='*60)
print(f'First 15 entities in VDB (of {len(db["data"])} total):')
for i, entity in enumerate(db['data'][:15]):
    name = entity.get('entity_name', '?')
    print(f'  {i+1}. {name}')

print()
print('='*60)
print('AL DHAFRA SPECIFIC ENTITIES:')
for entity in db['data']:
    name = entity.get('entity_name', '')
    content = entity.get('content', '')
    if 'dhafra' in name.lower() or 'adab' in name.lower():
        content_safe = content[:300].encode('ascii', 'replace').decode()
        print(f'  - {name}')
        print(f'    Content: {content_safe}...')
        print()

print()
print('='*60)
print('APPENDIX H ENTITIES:')
for entity in db['data']:
    name = entity.get('entity_name', '')
    content = entity.get('content', '')
    if 'appendix h' in name.lower() or 'appendix h' in content.lower():
        content_safe = content[:200].encode('ascii', 'replace').decode()
        print(f'  - {name}')
        print(f'    Content: {content_safe}...')
