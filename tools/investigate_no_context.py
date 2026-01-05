#!/usr/bin/env python3
"""Investigate tables without context."""

import json

with open("./rag_storage/swa_tas/vdb_entities.json", "r", encoding="utf-8") as f:
    vdb_data = json.load(f)

data = vdb_data.get("data", [])
tables = [e for e in data if e.get("entity_type", "").lower() == "table"]

no_context_tables = ["table_p1", "table_p6", "table_p35", "table_p36"]
context_keywords = ["appendix", "section", "attachment", "h.2", "workload", "pws"]

print("=" * 70)
print("TABLES WITHOUT CONTEXT - INVESTIGATION")
print("=" * 70)

for table in tables:
    name = table.get("entity_name", "")
    if name in no_context_tables:
        content = table.get("content", "")
        
        print(f"\n{'='*60}")
        print(f"TABLE: {name}")
        print(f"{'='*60}")
        print(f"\nFULL CONTENT:\n{content}")
        print(f"\n--- Content length: {len(content)} chars ---")
