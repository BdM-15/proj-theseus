"""Check VDB content for key workload entities to understand semantic gaps."""
import json

# Check what the VDB embeddings look like for key entities
f = open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8')
vdb = json.load(f)
f.close()

entities = vdb.get('data', [])

# Find key entities
print('=== VDB ENTITY CONTENT FOR KEY WORKLOAD ENTITIES ===')
print()

targets = ['table_p53', 'appendix h al dhafra', 'h.2.0 estimated monthly workload', 'al dhafra air base']

for ent in entities:
    name = ent.get('entity_name', '').lower()
    if any(t in name for t in targets):
        entity_name = ent.get('entity_name', '')
        print(f'ENTITY: {entity_name}')
        content = ent.get('content', '')
        print(f'Content length: {len(content)} chars')
        print(f'First 500 chars:')
        print(content[:500])
        print('...')
        print()
        
        # Check for key retrieval terms in content
        key_terms = ['scope of work', 'workload driver', 'monthly volumes', 'aircraft counts', 'transient aircraft']
        found = [t for t in key_terms if t in content.lower()]
        missing = [t for t in key_terms if t not in content.lower()]
        print(f'Found terms: {found}')
        print(f'Missing terms: {missing}')
        print('-' * 60)
        print()
