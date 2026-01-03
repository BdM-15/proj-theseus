"""Quick script to check SWA TAS entities - analyze description quality."""
import json

# Load VDB entities (has descriptions and vectors)
print("=== Loading vdb_entities.json ===")
with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    vdb_data = json.load(f)

entities = vdb_data.get('data', [])
print(f'Total entity vectors: {len(entities)}')

# Count empty vs non-empty descriptions
empty_desc = 0
short_desc = 0  # < 20 chars
good_desc = 0   # >= 20 chars

for entity in entities:
    desc = entity.get('description', '')
    if not desc or desc.strip() == '':
        empty_desc += 1
    elif len(desc) < 20:
        short_desc += 1
    else:
        good_desc += 1

print(f'\n=== Description Quality ===')
print(f'Empty descriptions:  {empty_desc} ({100*empty_desc/len(entities):.1f}%)')
print(f'Short descriptions:  {short_desc} ({100*short_desc/len(entities):.1f}%)')
print(f'Good descriptions:   {good_desc} ({100*good_desc/len(entities):.1f}%)')

# Show some with good descriptions
print('\n=== Sample entities WITH descriptions ===')
count = 0
for entity in entities:
    desc = entity.get('description', '')
    if len(desc) >= 20:
        print(f'NAME: {entity.get("entity_name")}')
        print(f'DESC: {desc[:200]}')
        print('-' * 60)
        count += 1
        if count >= 5:
            break

if count == 0:
    print('NO ENTITIES HAVE DESCRIPTIONS!')
