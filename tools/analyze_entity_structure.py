"""Analyze entity structure in VDB to understand why descriptions might be empty."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    vdb = json.load(f)

entities = vdb.get('data', [])
print(f'Total entities: {len(entities)}')

# Check structure of first 3 entities
print('\n=== ENTITY STRUCTURE (first 3) ===')
for i, entity in enumerate(entities[:3]):
    print(f'\n--- Entity {i+1} ---')
    print(f'Keys: {list(entity.keys())}')
    for k, v in entity.items():
        if k == 'vector':
            print(f'  {k}: [embedding array]')
        elif v is None:
            print(f'  {k}: None')
        elif v == '':
            print(f'  {k}: EMPTY STRING')
        else:
            val_str = str(v)[:300]
            print(f'  {k}: {val_str}')

# Field analysis
print('\n=== FIELD PRESENCE ANALYSIS ===')
fields = {}
for entity in entities:
    for key in entity.keys():
        if key not in fields:
            fields[key] = {'present': 0, 'empty': 0, 'has_value': 0}
        fields[key]['present'] += 1
        val = entity.get(key)
        if val is None or val == '':
            fields[key]['empty'] += 1
        else:
            fields[key]['has_value'] += 1

for field, counts in fields.items():
    if field != 'vector':
        print(f'{field}: present={counts["present"]}, has_value={counts["has_value"]}, empty={counts["empty"]}')

# Check if description vs content
print('\n=== DESCRIPTION vs CONTENT ===')
sample_entities = ['Appendix H', 'Al Dhafra', 'workload', 'C-130']
for entity in entities:
    name = entity.get('entity_name', '')
    if any(term.lower() in name.lower() for term in sample_entities):
        print(f'\n{name}:')
        print(f'  entity_type: {entity.get("entity_type", "NOT SET")}')
        print(f'  description: {entity.get("description", "NOT SET")[:200] if entity.get("description") else "EMPTY/NONE"}')
        print(f'  content: {entity.get("content", "NOT SET")[:200] if entity.get("content") else "EMPTY/NONE"}')
