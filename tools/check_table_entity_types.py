"""Check entity types for table entities"""
import json

with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

tables = [e for e in d['data'] if 'table_p' in e.get('entity_name', '')]
print(f"Found {len(tables)} table entities\n")
print("Table entity types:")
for e in tables[:15]:
    print(f"  {e['entity_name']}: entity_type = '{e.get('entity_type', 'MISSING')}'")

# Count entity types for tables
type_counts = {}
for e in tables:
    et = e.get('entity_type', 'MISSING')
    type_counts[et] = type_counts.get(et, 0) + 1

print(f"\nEntity type distribution for tables:")
for et, count in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f"  {et}: {count}")

# Also check H.2.0 entities
print("\n\nH.2.0 workload entities:")
h2_entities = [e for e in d['data'] if 'H.2.0' in e.get('entity_name', '') or 'workload' in e.get('entity_name', '').lower()]
for e in h2_entities[:10]:
    print(f"  {e['entity_name']}: entity_type = '{e.get('entity_type', 'MISSING')}'")
