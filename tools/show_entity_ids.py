#!/usr/bin/env python3
"""Show entity IDs and types."""

import json

with open("./rag_storage/swa_tas/vdb_entities.json", "r", encoding="utf-8") as f:
    vdb_data = json.load(f)

data = vdb_data.get("data", [])

print("Sample entity IDs and types:")
for entry in data[:30]:
    eid = entry.get("__id__", "")
    etype = entry.get("entity_type", "")
    print(f"  {etype:20} | {eid[:50]}")

# Check for any entity with workload or table-like content
print("\n\nEntity types distribution:")
types = {}
for entry in data:
    t = entry.get("entity_type", "unknown")
    types[t] = types.get(t, 0) + 1

for t, c in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

# Search for entities whose content mentions "table"
print("\n\nEntities with 'table' in content or id:")
count = 0
for entry in data:
    eid = entry.get("__id__", "").lower()
    content = entry.get("content", "").lower()
    if "table" in eid or "table" in content:
        count += 1
        if count <= 10:
            print(f"  {entry.get('entity_type', '')} | {entry.get('__id__', '')[:60]}")

print(f"\nTotal entities with 'table' reference: {count}")
