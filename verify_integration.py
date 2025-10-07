import json

# Load kv_store_full_relations.json
with open('rag_storage/kv_store_full_relations.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find document key
doc_key = [k for k in data.keys() if k.startswith('doc-')][0]

# Count LLM relationships (individual records)
llm_rels = len([k for k in data.keys() if k.startswith('rel_llm_')])

# Count document relation_pairs
doc_pairs = len(data[doc_key]['relation_pairs'])

print(f"✅ Integration Verification:")
print(f"  LLM relationships (individual records): {llm_rels}")
print(f"  Document relation_pairs array: {doc_pairs}")
print(f"  Baseline edges: 587")
print(f"  Expected total: 587 + 235 = 822")
print(f"  Status: {'✅ INTEGRATED CORRECTLY' if doc_pairs == 822 else '❌ INTEGRATION FAILED'}")
print()
print(f"📊 Sample Phase 6.1 relationships:")
for i in range(1, 6):
    rel_key = f"rel_llm_{i}"
    if rel_key in data:
        rel = data[rel_key]
        print(f"  {rel_key}: {rel.get('src_id', 'Unknown')} → {rel.get('tgt_id', 'Unknown')}")
        print(f"    Type: {rel.get('relationship_type')}, Weight: {rel.get('weight')}")
        print(f"    Description: {rel.get('description', '')[:80]}...")
