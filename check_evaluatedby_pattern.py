"""
Check if EVALUATED_BY relationships exist but with different naming/pattern.
"""

import networkx as nx
from pathlib import Path

graphml_path = Path("./rag_storage/default/graph_chunk_entity_relation.graphml")
G = nx.read_graphml(graphml_path)

requirements = [n for n, d in G.nodes(data=True) if d.get('entity_type') == 'requirement']
eval_factors = [n for n, d in G.nodes(data=True) if d.get('entity_type') == 'evaluation_factor']

print("=" * 70)
print("EVALUATED_BY Pattern Analysis")
print("=" * 70)

# Find all edges between requirements and evaluation_factors
req_to_ef = []
ef_to_req = []

for source, target, data in G.edges(data=True):
    desc = data.get('description', '')
    
    if source in requirements and target in eval_factors:
        req_to_ef.append((source, target, desc))
    elif source in eval_factors and target in requirements:
        ef_to_req.append((source, target, desc))

print(f"\nRequirement → Evaluation Factor: {len(req_to_ef)}")
if req_to_ef:
    print(f"Sample relationships:")
    for source, target, desc in req_to_ef[:10]:
        print(f"  • {source[:40]} → {target[:40]}")
        print(f"    {desc[:120]}")
        print()

print(f"\nEvaluation Factor → Requirement: {len(ef_to_req)}")
if ef_to_req:
    print(f"Sample relationships:")
    for source, target, desc in ef_to_req[:10]:
        print(f"  • {source[:40]} → {target[:40]}")
        print(f"    {desc[:120]}")
        print()

# Check for EVALUATED_BY in relationship descriptions
all_relationship_descriptions = [data.get('description', '') for _, _, data in G.edges(data=True)]
evaluated_by_rels = [desc for desc in all_relationship_descriptions if 'EVALUATED_BY' in desc.upper()]

print(f"\nRelationships with 'EVALUATED_BY' in description: {len(evaluated_by_rels)}")
if evaluated_by_rels:
    print(f"Samples:")
    for desc in evaluated_by_rels[:5]:
        print(f"  • {desc[:150]}")

# Check what GUIDES relationships look like
guides_rels = [(s, t, d.get('description', '')) for s, t, d in G.edges(data=True) if 'GUIDES' in d.get('description', '').upper()]
print(f"\n✅ GUIDES relationships (working): {len(guides_rels)}")
if guides_rels:
    print(f"Samples:")
    for source, target, desc in guides_rels[:3]:
        print(f"  • {source[:40]} → {target[:40]}")
        print(f"    {desc}")
        print()

print("=" * 70)
print("CONCLUSION")
print("=" * 70)

if len(req_to_ef) == 0 and len(ef_to_req) == 0:
    print("❌ NO relationships exist between requirements and evaluation_factors")
    print("   Phase 6 Algorithm 4 (requirement_evaluation) did NOT create any links")
    print("   This is the problem - LLM did not infer semantic connections")
else:
    print(f"✅ {len(req_to_ef) + len(ef_to_req)} relationships exist between requirements and evaluation_factors")
    print("   But they may not be labeled as EVALUATED_BY")
    print("   Check if they use different relationship type names")
