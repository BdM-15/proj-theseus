"""Analyze annex entities and their relationships"""
import json
from pathlib import Path

# Load entities
with open('rag_storage/kv_store_full_entities.json', 'r', encoding='utf-8') as f:
    entities = json.load(f)

print(f"Total entities loaded: {len(entities)}")
print(f"Entity structure sample (first 3 keys):")
for i, (k, v) in enumerate(list(entities.items())[:3]):
    print(f"\nKey: {k}")
    print(f"Value type: {type(v)}")
    if isinstance(v, dict):
        print(f"  Keys: {list(v.keys())}")
        print(f"  Sample: {str(v)[:200]}...")
print("\n")

# Load relationships
with open('rag_storage/kv_store_full_relations.json', 'r', encoding='utf-8') as f:
    relations = json.load(f)

print("=" * 80)
print("ANNEX ENTITY ANALYSIS")
print("=" * 80)

# Extract entity_names array
all_entity_names = []
for eid, entity in entities.items():
    if isinstance(entity, dict) and 'entity_names' in entity:
        all_entity_names.extend(entity['entity_names'])

print(f"Total unique entity names: {len(all_entity_names)}\n")

# Find all annex-like entities (broader search)
j_entities = []
for name in all_entity_names:
    # Search for: J-XXXXX, Annex, Attachment, JM-, JL-, etc.
    if any(pattern in name for pattern in ['J-', 'Annex', 'Attachment', 'JM-', 'JL-']):
        j_entities.append(name)

print(f"\nFound {len(j_entities)} annex-like entities:\n")
for name in sorted(j_entities)[:30]:
    print(f"  {name}")

# Check relationships for these entities
print("\n" + "=" * 80)
print("RELATIONSHIP ANALYSIS FOR J- ENTITIES")
print("=" * 80)

for entity_name in j_entities[:15]:
    # Find relationships where this entity is source or target
    connected_rels = []
    for rid, rel in relations.items():
        if isinstance(rel, dict):
            src = rel.get('src_id', '')
            tgt = rel.get('tgt_id', '')
            
            if src == entity_name or tgt == entity_name:
                connected_rels.append(rel)
    
    print(f"\n{entity_name}:")
    if connected_rels:
        print(f"  ✅ Has {len(connected_rels)} relationships")
        for rel in connected_rels[:2]:
            print(f"    - {rel.get('src_id')} → {rel.get('relationship_type')} → {rel.get('tgt_id')}")
    else:
        print(f"  ❌ ISOLATED - No relationships found")

# Find Section J
print("\n" + "=" * 80)
print("SECTION J SEARCH")
print("=" * 80)

section_j_entities = []
for name in all_entity_names:
    if 'SECTION' in name.upper() and 'J' in name.upper():
        section_j_entities.append(name)

if section_j_entities:
    print(f"\nFound {len(section_j_entities)} Section J candidates:")
    for s in section_j_entities:
        print(f"  {s}")
else:
    print("\n❌ No 'Section J' entity found in knowledge graph!")

# Analyze annex prefix patterns
print("\n" + "=" * 80)
print("ANNEX PREFIX PATTERN ANALYSIS")
print("=" * 80)

annex_prefixes = {}
for name in j_entities:
    # Extract pattern: J-XXXXXXX-YY
    if '-' in name:
        parts = name.split('-')
        if len(parts) >= 2:
            prefix = f"{parts[0]}-{parts[1][:4] if len(parts[1]) >= 4 else parts[1]}"
            if prefix not in annex_prefixes:
                annex_prefixes[prefix] = []
            annex_prefixes[prefix].append(name)

print(f"\nFound {len(annex_prefixes)} unique prefix patterns:")
for prefix, names in sorted(annex_prefixes.items()):
    print(f"\n  {prefix}* ({len(names)} annexes):")
    for name in names[:5]:
        print(f"    - {name}")
    if len(names) > 5:
        print(f"    ... and {len(names) - 5} more")
