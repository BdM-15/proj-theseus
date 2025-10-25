"""
Analyze relationship sources: LightRAG extraction vs Phase 6 inference.

Question: Are the 41 requirement→evaluation_factor relationships from:
1. Initial LightRAG extraction (extraction prompts working well)?
2. Phase 6 LLM inference (post-processing adding value)?
3. Mix of both?
"""

import networkx as nx
from pathlib import Path
from collections import defaultdict

graphml_path = Path("./rag_storage/default/graph_chunk_entity_relation.graphml")
G = nx.read_graphml(graphml_path)

requirements = set(n for n, d in G.nodes(data=True) if d.get('entity_type') == 'requirement')
eval_factors = set(n for n, d in G.nodes(data=True) if d.get('entity_type') == 'evaluation_factor')

print("=" * 80)
print("Relationship Source Analysis")
print("=" * 80)

# Categorize all requirement↔evaluation_factor relationships by description pattern
req_ef_relationships = []

for source, target, data in G.edges(data=True):
    desc = data.get('description', '')
    
    if (source in requirements and target in eval_factors) or \
       (source in eval_factors and target in requirements):
        req_ef_relationships.append({
            'source': source,
            'target': target,
            'description': desc,
            'direction': 'req→ef' if source in requirements else 'ef→req'
        })

print(f"\n📊 Total requirement↔evaluation_factor relationships: {len(req_ef_relationships)}\n")

# Categorize by description pattern
patterns = defaultdict(list)

for rel in req_ef_relationships:
    desc = rel['description']
    
    # Phase 6 LLM inference patterns (from prompts)
    if 'Topic alignment:' in desc:
        patterns['Phase 6: Topic Alignment'].append(rel)
    elif 'Criticality mapping:' in desc:
        patterns['Phase 6: Criticality Mapping'].append(rel)
    elif 'Content proximity:' in desc:
        patterns['Phase 6: Content Proximity'].append(rel)
    elif 'Explicit cross-reference:' in desc:
        patterns['Phase 6: Explicit Cross-Reference'].append(rel)
    elif 'LLM-inferred' in desc or '(LLM-inferred)' in desc:
        patterns['Phase 6: LLM Generic'].append(rel)
    # LightRAG extraction patterns (initial graph building)
    elif 'belongs to' in desc.lower():
        patterns['Extraction: Belongs To (table structure)'].append(rel)
    elif '<SEP>' in desc:
        patterns['Extraction: Multi-relationship'].append(rel)
    elif len(desc) < 50 and not any(kw in desc for kw in ['Topic', 'Criticality', 'LLM']):
        patterns['Extraction: Short/Direct'].append(rel)
    else:
        patterns['Other/Unclear'].append(rel)

# Report by category
print("Breakdown by Source:\n")
for category, rels in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"  {category}: {len(rels)}")

print("\n" + "=" * 80)
print("Sample Relationships by Category")
print("=" * 80)

for category, rels in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n### {category} ({len(rels)} relationships)")
    print(f"{'─' * 80}")
    
    for rel in rels[:3]:  # Show first 3 samples
        source = rel['source'][:40]
        target = rel['target'][:40]
        desc = rel['description'][:120]
        print(f"  {rel['direction']}: {source} → {target}")
        print(f"  Description: {desc}")
        print()

# Key question: Are Phase 6 relationships semantically valuable?
print("\n" + "=" * 80)
print("ANALYSIS: Value of Phase 6 vs Extraction")
print("=" * 80)

phase6_count = sum(len(rels) for cat, rels in patterns.items() if 'Phase 6' in cat)
extraction_count = sum(len(rels) for cat, rels in patterns.items() if 'Extraction' in cat)
other_count = sum(len(rels) for cat, rels in patterns.items() if 'Other' in cat)

print(f"\nPhase 6 LLM Inference: {phase6_count} relationships ({phase6_count/len(req_ef_relationships)*100:.1f}%)")
print(f"LightRAG Extraction: {extraction_count} relationships ({extraction_count/len(req_ef_relationships)*100:.1f}%)")
print(f"Other/Unclear: {other_count} relationships ({other_count/len(req_ef_relationships)*100:.1f}%)")

print("\n📊 VERDICT:")

if phase6_count > extraction_count * 2:
    print("✅ Phase 6 is PRIMARY source - inference adds significant value")
    print("   Recommendation: Keep Phase 6, consider fixing relationship_type labels")
elif extraction_count > phase6_count * 2:
    print("✅ Extraction is PRIMARY source - initial prompts work well")
    print("   Recommendation: Phase 6 adds little value, could simplify by removing it")
    print("   Alternative: Enhance extraction prompts to create more requirement→factor links")
else:
    print("🔄 BOTH contribute significantly - complementary value")
    print("   Recommendation: Keep both systems, they serve different purposes")

# Check if extraction-created relationships are semantically meaningful
print("\n" + "=" * 80)
print("Quality Assessment: Are Extraction Relationships Semantic?")
print("=" * 80)

if extraction_count > 0:
    print("\nSample extraction-created requirement↔evaluation_factor relationships:")
    extraction_rels = [rel for cat, rels in patterns.items() if 'Extraction' in cat for rel in rels]
    
    for rel in extraction_rels[:5]:
        print(f"\n  • {rel['source'][:50]}")
        print(f"    → {rel['target'][:50]}")
        print(f"    Description: {rel['description'][:150]}")
        
        # Check if it's meaningful
        if 'belongs to' in rel['description'].lower():
            print(f"    ⚠️  Table structure relationship (not semantic)")
        elif len(rel['description']) > 100:
            print(f"    ✅ Rich semantic description")
        else:
            print(f"    ⚠️  Short description - may lack semantic depth")

print("\n")
