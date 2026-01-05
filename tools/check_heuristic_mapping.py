"""Check heuristic mapping for workload tables"""
import json

with open('rag_storage/swa_tas/vdb_entities.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

# UPDATED Heuristic from semantic_post_processor.py (BUG FIX)
def _heuristic_table_type_mapping_FIXED(entity):
    name = (entity.get('entity_name') or '').lower()
    # BUG FIX: Check 'content' field, not just 'description'
    desc = (entity.get('description') or entity.get('content') or '').lower()
    text = f"{name} {desc}"
    
    # Check order matters - first match wins
    if any(kw in text for kw in ['cdrl', 'contract data', 'deliverable', 'dd form 1423', 'data item']):
        return 'deliverable'
    if any(kw in text for kw in ['evaluation', 'rating', 'scoring', 'assessment', 'criteria', 'factor']):
        return 'evaluation_factor'
    if any(kw in text for kw in ['performance', 'metric', 'sla', 'kpi', 'threshold', 'standard']):
        return 'performance_metric'
    # NEW: Explicit workload data tables check (before general 'work')
    if any(kw in text for kw in ['workload', 'aircraft visit', 'estimated monthly', 'h.2.0', 'j.2.0', 'k.2.0', 'l.2.0']):
        return 'requirement'
    if any(kw in text for kw in ['requirement', 'shall', 'must', 'sow', 'pws', 'task', 'work']):
        return 'requirement'
    if any(kw in text for kw in ['submission', 'proposal', 'volume', 'page limit', 'format']):
        return 'submission_instruction'
    if any(kw in text for kw in ['far ', 'dfars', 'clause', 'provision', '52.2']):
        return 'clause'
    if any(kw in text for kw in ['section', 'attachment', 'annex', 'exhibit', 'appendix']):
        return 'section'
    if any(kw in text for kw in ['organization', 'contractor', 'government', 'agency']):
        return 'organization'
    if any(kw in text for kw in ['personnel', 'staff', 'position', 'role', 'labor category']):
        return 'person'
    if any(kw in text for kw in ['equipment', 'material', 'supply', 'asset', 'gfe', 'gfp']):
        return 'equipment'
    if any(kw in text for kw in ['schedule', 'timeline', 'milestone', 'calendar', 'date']):
        return 'concept'
    if any(kw in text for kw in ['price', 'cost', 'clin', 'labor rate', 'fee']):
        return 'concept'
    return 'concept'

# Check workload table entities
tables = [e for e in d['data'] if 'table_p' in e.get('entity_name', '')]
print("=" * 70)
print("FIXED HEURISTIC MAPPING FOR WORKLOAD TABLES")
print("=" * 70)

workload_tables = []
for e in tables:
    content = e.get('content', '').lower()
    if 'workload' in content or 'aircraft' in content or 'h.2.0' in content.lower():
        workload_tables.append(e)

print(f"\nFound {len(workload_tables)} workload-related tables\n")

for e in workload_tables:
    name = e.get('entity_name')
    current_type = e.get('entity_type')
    would_map_to = _heuristic_table_type_mapping_FIXED(e)
    
    # Check what triggers
    text = (e.get('entity_name', '') + ' ' + e.get('content', '')).lower()
    triggers = []
    if 'workload' in text: triggers.append('workload')
    if 'aircraft visit' in text: triggers.append('aircraft visit')
    if 'estimated monthly' in text: triggers.append('estimated monthly')
    if 'h.2.0' in text: triggers.append('h.2.0')
    
    print(f"{name}:")
    print(f"  Current type: {current_type}")
    print(f"  FIXED would map to: {would_map_to}")
    print(f"  Triggers: {triggers}")
    
    # Check if it contains key workload data
    content = e.get('content', '')
    has_760 = '760' in content
    has_c17 = 'c-17' in content.lower() or 'c17' in content.lower()
    has_c130 = 'c-130' in content.lower() or 'c130' in content.lower()
    if has_760 or has_c17 or has_c130:
        print(f"  ⭐ KEY DATA: 760={has_760}, C-17={has_c17}, C-130={has_c130}")
    print()
