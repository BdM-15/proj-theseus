#!/usr/bin/env python3
"""Check full entity data in KV store vs VDB."""

import json

# Check KV store for full entity data
with open("./rag_storage/swa_tas/kv_store_full_entities.json", "r", encoding="utf-8") as f:
    kv_data = json.load(f)

print("KV Store entity keys (first 20):")
for i, key in enumerate(list(kv_data.keys())[:20]):
    print(f"  {key}")

# Find tables by searching values
print("\n\nSearching for table entities in KV store...")
table_count = 0
for key, value in kv_data.items():
    if isinstance(value, dict):
        etype = value.get("entity_type", "")
        if etype == "table":
            table_count += 1
            if table_count <= 5:
                print(f"\n  Key: {key}")
                desc = value.get("description", "")
                print(f"  Description length: {len(desc)}")
                print(f"  Description preview: {desc[:300]}...")

print(f"\nTotal tables in KV store: {table_count}")

# Check if table_p1 exists with different naming
print("\n\nSearching for 'table_p1' or similar...")
for key in kv_data.keys():
    if "table" in key.lower() and "p1" in key.lower():
        print(f"  Found: {key}")
