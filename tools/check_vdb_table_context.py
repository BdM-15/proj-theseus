"""Check table entries in VDB for section context."""
import json
from pathlib import Path

vdb_path = Path('./rag_storage/swa_tas/vdb_entities.json')
with open(vdb_path, 'r', encoding='utf-8') as f:
    vdb = json.load(f)

data = vdb.get('data', [])
context_markers = ['appendix', 'section', 'attachment', 'h.2.0', 'workload data', 'pws']

print('TABLE ENTRIES IN VDB WITH CONTEXT CHECK')
print('=' * 60)

tables_with_context = 0
tables_total = 0

for entry in data:
    if isinstance(entry, dict):
        name = str(entry.get('entity_name', '')).lower()
        if 'table_p' in name:
            tables_total += 1
            desc = str(entry.get('description', '')).lower()
            content = str(entry.get('content', '')).lower()
            combined = desc + ' ' + content
            
            has_context = any(m in combined for m in context_markers)
            if has_context:
                tables_with_context += 1
                status = '✅'
            else:
                status = '❌'
            
            ent_name = entry.get('entity_name')
            ent_type = entry.get('entity_type')
            print(f"{status} | {ent_name} | {ent_type}")
            if tables_total <= 8:
                print(f"    DESC: {desc[:200]}...")
                print()

print()
print(f'Tables with context: {tables_with_context}/{tables_total}')
print(f'Context coverage: {tables_with_context/tables_total*100:.1f}%' if tables_total else 'N/A')
