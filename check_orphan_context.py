"""Check extraction context for orphaned entities."""

import json

# Load entities
with open(r'rag_storage\afcapv_adab_iss_2025\kv_store_full_entities.json', 'r', encoding='utf-8') as f:
    entities = json.load(f)

# Load relationships
with open(r'rag_storage\afcapv_adab_iss_2025\kv_store_full_relations.json', 'r', encoding='utf-8') as f:
    relations = json.load(f)

orphaned_names = [
    'AFCAP V Contractors',
    'DOD SAFE File Exchange', 
    'Camber Corporation',
    'Admin Dodaac',
    'Alternate Program Manager',
    'AFCAP Main Contract'
]

print('='*80)
print('ORPHANED ENTITY EXTRACTION CONTEXT')
print('='*80)

for name in orphaned_names:
    if name in entities:
        entity = entities[name]
        print(f'\n{"="*80}')
        print(f'Entity: {name}')
        print(f'Type: {entity.get("entity_type", "unknown")}')
        desc = entity.get("description", "N/A")
        print(f'Description: {desc[:300]}')
        print(f'Source IDs: {entity.get("source_id", "N/A")}')
        
        # Check if any relationships mention this entity
        related_rels = []
        for rel_key, rel in relations.items():
            if name in rel.get('src_id', '') or name in rel.get('tgt_id', ''):
                related_rels.append(rel)
        
        if related_rels:
            print(f'⚠️  FOUND {len(related_rels)} relationships in storage but NOT in Neo4j!')
            for rel in related_rels[:3]:
                print(f'  → {rel.get("src_id")} --[{rel.get("description", "?")}]--> {rel.get("tgt_id")}')
        else:
            print('❌ No relationships in storage either - truly orphaned')
    else:
        print(f'\n⚠️  {name} not found in entities storage')

print('\n' + '='*80)
print('ENTITY TYPE SOURCE ANALYSIS')
print('='*80)

# Check where entity types are coming from - are they in LightRAG prompts?
print('\nChecking src/server/initialization.py for entity type definition...')
