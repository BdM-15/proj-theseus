"""
Diagnose why Phase 6 produced 0 EVALUATED_BY relationships.

Checks:
1. Do we have both requirement and evaluation_factor entities?
2. What do the entity descriptions look like?
3. Did Phase 6 actually run?
4. Are there any Phase 6 relationships at all?
"""

import networkx as nx
from pathlib import Path

graphml_path = Path("./rag_storage/default/graph_chunk_entity_relation.graphml")

print("=" * 70)
print("Phase 6 Diagnostic - Why No EVALUATED_BY Relationships?")
print("=" * 70)

G = nx.read_graphml(graphml_path)

# Check 1: Entity counts
requirements = [n for n, d in G.nodes(data=True) if d.get('entity_type') == 'requirement']
eval_factors = [n for n, d in G.nodes(data=True) if d.get('entity_type') == 'evaluation_factor']

print(f"\n✅ Entity Availability:")
print(f"   Requirements: {len(requirements)}")
print(f"   Evaluation Factors: {len(eval_factors)}")

if requirements and eval_factors:
    print(f"   ✅ Both entity types exist - Phase 6 should have run")
else:
    print(f"   ❌ Missing entity types - Phase 6 cannot create EVALUATED_BY")

# Check 2: Sample entity descriptions
print(f"\n📋 Sample Requirements:")
for req_name in requirements[:3]:
    req_data = G.nodes[req_name]
    desc = req_data.get('description', '')[:150]
    print(f"   • {req_name[:50]}")
    print(f"     {desc}...")

print(f"\n📋 Sample Evaluation Factors:")
for ef_name in eval_factors[:3]:
    ef_data = G.nodes[ef_name]
    desc = ef_data.get('description', '')[:150]
    print(f"   • {ef_name[:50]}")
    print(f"     {desc}...")

# Check 3: Relationship types
relationship_types = {}
for source, target, data in G.edges(data=True):
    rel_desc = data.get('description', 'unknown')
    # Extract relationship type from description
    if 'EVALUATED_BY' in rel_desc.upper():
        relationship_types['EVALUATED_BY'] = relationship_types.get('EVALUATED_BY', 0) + 1
    elif 'GUIDES' in rel_desc.upper():
        relationship_types['GUIDES'] = relationship_types.get('GUIDES', 0) + 1
    elif 'CHILD_OF' in rel_desc.upper():
        relationship_types['CHILD_OF'] = relationship_types.get('CHILD_OF', 0) + 1
    elif 'ATTACHMENT_OF' in rel_desc.upper():
        relationship_types['ATTACHMENT_OF'] = relationship_types.get('ATTACHMENT_OF', 0) + 1
    elif 'PRODUCES' in rel_desc.upper():
        relationship_types['PRODUCES'] = relationship_types.get('PRODUCES', 0) + 1
    else:
        relationship_types['OTHER'] = relationship_types.get('OTHER', 0) + 1

print(f"\n🔗 Relationship Type Distribution:")
for rel_type, count in sorted(relationship_types.items(), key=lambda x: x[1], reverse=True):
    print(f"   {rel_type}: {count}")

# Check 4: Any relationships involving requirements or eval_factors?
req_relationships = []
ef_relationships = []

for source, target, data in G.edges(data=True):
    if source in requirements or target in requirements:
        req_relationships.append((source, target, data.get('description', '')[:100]))
    if source in eval_factors or target in eval_factors:
        ef_relationships.append((source, target, data.get('description', '')[:100]))

print(f"\n🔍 Requirement-Involved Relationships:")
print(f"   Total: {len(req_relationships)}")
if req_relationships:
    print(f"   Samples:")
    for source, target, desc in req_relationships[:5]:
        print(f"     {source[:30]} → {target[:30]}: {desc}")

print(f"\n🔍 Evaluation Factor-Involved Relationships:")
print(f"   Total: {len(ef_relationships)}")
if ef_relationships:
    print(f"   Samples:")
    for source, target, desc in ef_relationships[:5]:
        print(f"     {source[:30]} → {target[:30]}: {desc}")

# Check 5: Phase 6 execution evidence
print(f"\n🔎 Phase 6 Execution Evidence:")
phase6_keywords = ['GUIDES', 'EVALUATED_BY', 'CHILD_OF', 'ATTACHMENT_OF', 'PRODUCES']
phase6_rels = []

for source, target, data in G.edges(data=True):
    desc = data.get('description', '')
    if any(kw in desc.upper() for kw in phase6_keywords):
        phase6_rels.append(desc)

if phase6_rels:
    print(f"   ✅ Found {len(phase6_rels)} Phase 6-style relationships")
    print(f"   Phase 6 DID execute")
else:
    print(f"   ❌ No Phase 6-style relationships found")
    print(f"   Phase 6 may NOT have executed")

print(f"\n" + "=" * 70)
print("DIAGNOSIS SUMMARY")
print("=" * 70)

issues = []
if not requirements:
    issues.append("❌ No REQUIREMENT entities found")
if not eval_factors:
    issues.append("❌ No EVALUATION_FACTOR entities found")
if not phase6_rels:
    issues.append("❌ No Phase 6-style relationships found (Phase 6 may have failed silently)")
if len(req_relationships) == 0:
    issues.append("⚠️  Requirements have NO relationships at all")
if len(ef_relationships) == 0:
    issues.append("⚠️  Evaluation factors have NO relationships at all")

if issues:
    for issue in issues:
        print(issue)
else:
    print("✅ All Phase 6 prerequisites met")
    print("⚠️  Phase 6 ran but produced 0 EVALUATED_BY - check LLM inference quality")

print()
