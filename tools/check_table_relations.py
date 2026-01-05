#!/usr/bin/env python3
"""Check table relationships in KV store."""

import json

with open("./rag_storage/swa_tas/kv_store_full_relations.json", "r", encoding="utf-8") as f:
    relations = json.load(f)

print(f"Total relationships: {len(relations)}")

# Find relationships involving tables
table_rels = []
child_of_rels = []

for rel_id, rel_data in relations.items():
    src = rel_data.get("src_id", "").lower()
    tgt = rel_data.get("tgt_id", "").lower()
    rel_type = rel_data.get("description", "").lower()
    
    if "table" in src or "table" in tgt:
        table_rels.append((src, tgt, rel_data.get("description", "")))
    
    if "child_of" in rel_type or "child" in rel_type:
        child_of_rels.append((src, tgt, rel_data.get("description", "")))

print(f"Relationships involving tables: {len(table_rels)}")
print(f"CHILD_OF relationships: {len(child_of_rels)}")

print("\nSample table relationships:")
for src, tgt, desc in table_rels[:10]:
    print(f"  {src[:30]} -> {tgt[:30]}")
    print(f"    Desc: {desc[:80]}...")
