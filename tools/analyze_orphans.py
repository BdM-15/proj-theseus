#!/usr/bin/env python3
"""Analyze orphan entities to understand why they exist."""

import json
import os
from collections import Counter

# Load VDB data
with open("./rag_storage/swa_tas/vdb_entities.json", "r", encoding="utf-8") as f:
    vdb_data = json.load(f)

entities = vdb_data.get("data", [])

# Load relationships
with open("./rag_storage/swa_tas/vdb_relationships.json", "r", encoding="utf-8") as f:
    rel_data = json.load(f)

relationships = rel_data.get("data", [])

print("=" * 70)
print("ORPHAN ANALYSIS")
print("=" * 70)

print(f"\nTotal entities: {len(entities)}")
print(f"Total relationships: {len(relationships)}")

# Build connected entity set from relationships
connected_entities = set()
for rel in relationships:
    src = rel.get("src_id", "")
    tgt = rel.get("tgt_id", "")
    if src:
        connected_entities.add(src.lower())
    if tgt:
        connected_entities.add(tgt.lower())

print(f"Entities mentioned in relationships: {len(connected_entities)}")

# Find orphans
orphans = []
for e in entities:
    entity_name = e.get("entity_name", "").lower()
    if entity_name not in connected_entities:
        orphans.append(e)

print(f"Orphan entities: {len(orphans)}")

# Analyze orphan types
orphan_types = Counter(o.get("entity_type", "unknown") for o in orphans)
print("\nOrphan entity types:")
for etype, count in orphan_types.most_common():
    print(f"  {etype}: {count}")

# Show sample orphans
print("\n" + "-" * 70)
print("SAMPLE ORPHANS (first 20)")
print("-" * 70)

for i, orphan in enumerate(orphans[:20]):
    name = orphan.get("entity_name", "")
    etype = orphan.get("entity_type", "")
    content = orphan.get("content", "")[:200]
    print(f"\n[{i+1}] {name} ({etype})")
    print(f"    Content: {content}...")

# Check if these look like valid entities that should be connected
print("\n" + "-" * 70)
print("DIAGNOSTIC: Why are these orphaned?")
print("-" * 70)

print("""
Possible reasons entities become orphaned:

1. LightRAG extraction extracted the entity but no relationship
   - LLM didn't see a clear relationship in the chunk
   - Entity appeared standalone (e.g., a table header, a list item)

2. Entity name mismatch between entity and relationship
   - LLM used slightly different names (e.g., "PM" vs "Program Manager")
   - Case sensitivity issues

3. Chunk isolation
   - Entity appeared in a chunk without related entities
   - Context was lost during chunking

4. Post-processing limitations
   - Algo 8 only processes 50 orphans (hardcoded limit)
   - Only considers 50 candidate target entities
""")

# Check what the orphans look like - are they workload-related?
workload_orphans = [o for o in orphans if "workload" in o.get("content", "").lower()]
print(f"\nWorkload-related orphans: {len(workload_orphans)}")
for o in workload_orphans[:5]:
    print(f"  - {o.get('entity_name', '')} ({o.get('entity_type', '')})")
