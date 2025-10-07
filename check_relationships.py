import json
from pathlib import Path

# Load kv_store relationships
kv_path = Path('rag_storage/kv_store_full_relations.json')
with open(kv_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("RELATIONSHIP ANALYSIS")
print("=" * 80)

# Count LLM relationships
llm_rels = [k for k in data.keys() if 'llm' in k.lower()]
print(f"\n✅ Phase 6.1 LLM-inferred relationships: {len(llm_rels)}")

# Get document relationship pairs
doc_keys = [k for k in data.keys() if k.startswith('doc-')]
if doc_keys:
    doc_id = doc_keys[0]
    pairs = data[doc_id]['relation_pairs']
    print(f"✅ Document relation_pairs array: {len(pairs)}")
    print(f"\n📊 TOTAL RELATIONSHIPS: {len(pairs)}")
    print(f"   Breakdown:")
    print(f"     - Baseline (LightRAG): 554")
    print(f"     - Phase 6.1 added: {len(pairs) - 554}")
else:
    print(f"\n⚠️  No document key found, counting individual relationships:")
    total = len(data)
    print(f"   Total relationship records: {total}")
    print(f"   LLM relationships: {len(llm_rels)}")
    print(f"   Baseline relationships: {total - len(llm_rels)}")

# Sample LLM relationships
print(f"\n📋 Sample LLM relationships (first 3):")
for rel_id in llm_rels[:3]:
    rel = data[rel_id]
    print(f"\n  {rel_id}:")
    print(f"    {rel.get('src_id')} → {rel.get('tgt_id')}")
    print(f"    Type: {rel.get('relationship_type')}")
    print(f"    Description: {rel.get('description', '')[:80]}...")
    print(f"    Confidence: {rel.get('weight', 'N/A')}")

print("\n" + "=" * 80)
