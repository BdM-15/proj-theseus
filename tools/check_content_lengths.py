#!/usr/bin/env python3
"""Check content lengths across all tables."""

import json

with open("./rag_storage/swa_tas/vdb_entities.json", "r", encoding="utf-8") as f:
    vdb_data = json.load(f)

data = vdb_data.get("data", [])
tables = [e for e in data if e.get("entity_type", "").lower() == "table"]

print("TABLE CONTENT LENGTHS")
print("=" * 60)

lengths = []
for t in tables:
    name = t.get("entity_name", "")
    content = t.get("content", "")
    lengths.append((name, len(content)))

# Sort by length
lengths.sort(key=lambda x: x[1])

print(f"\nShortest tables:")
for name, length in lengths[:10]:
    print(f"  {name}: {length} chars")

print(f"\nLongest tables:")
for name, length in lengths[-5:]:
    print(f"  {name}: {length} chars")

print(f"\nStatistics:")
all_lengths = [l for _, l in lengths]
print(f"  Min: {min(all_lengths)}")
print(f"  Max: {max(all_lengths)}")
print(f"  Avg: {sum(all_lengths)/len(all_lengths):.0f}")

# Check if truncation is at exact boundary
print(f"\nTables at ~200 chars (possible truncation):")
for name, length in lengths:
    if 195 <= length <= 215:
        print(f"  {name}: {length} chars")
