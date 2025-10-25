"""
Assess MCPP II RFP processing with Phase 7 metadata enrichment.

Validates:
1. Entity extraction quality (counts, distribution)
2. Phase 6 semantic inference (relationship types)
3. Phase 7 metadata enrichment (attribute coverage)
4. Strategic reasoning preservation (description analysis)
"""

import networkx as nx
from pathlib import Path
from collections import defaultdict

graphml_path = Path("./rag_storage/default/graph_chunk_entity_relation.graphml")

print("=" * 70)
print("MCPP II RFP - Phase 7 Metadata Enrichment Assessment")
print("=" * 70)

# Load graph
G = nx.read_graphml(graphml_path)

print(f"\n📊 EXTRACTION SUMMARY")
print(f"{'─' * 70}")
print(f"Total Entities: {len(G.nodes()):,}")
print(f"Total Relationships: {len(G.edges()):,}")

# Entity type distribution
print(f"\n📋 ENTITY TYPE DISTRIBUTION")
print(f"{'─' * 70}")
entity_types = defaultdict(int)
for _, data in G.nodes(data=True):
    entity_type = data.get('entity_type', 'unknown')
    entity_types[entity_type] += 1

for et, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
    print(f"  {et:30} {count:6,}")

# Phase 6 relationship analysis
print(f"\n🔗 PHASE 6 SEMANTIC INFERENCE")
print(f"{'─' * 70}")

phase6_relationships = defaultdict(int)
for source, target, data in G.edges(data=True):
    desc = data.get('description', '')
    # Phase 6 adds specific relationship types
    phase6_relationships[desc] += 1

# Key Phase 6 relationship types
key_rels = {
    'EVALUATED_BY': 0,
    'GUIDES': 0,
    'CHILD_OF': 0,
    'ATTACHMENT_OF': 0,
    'APPLIES_TO': 0,
}

for rel_type in phase6_relationships.keys():
    for key in key_rels.keys():
        if key in rel_type.upper():
            key_rels[key] += phase6_relationships[rel_type]

print("Key Phase 6 Relationships:")
for rel_type, count in sorted(key_rels.items(), key=lambda x: x[1], reverse=True):
    status = "✅" if count > 0 else "⚠️"
    print(f"  {status} {rel_type:20} {count:6}")

# Phase 7 metadata enrichment analysis
print(f"\n📊 PHASE 7 METADATA ENRICHMENT")
print(f"{'─' * 70}")

metadata_attrs = {
    'metadata_weight': 'Evaluation Factor Weight',
    'metadata_importance': 'Importance Hierarchy',
    'metadata_subfactors': 'Subfactor Details',
    'metadata_page_limit': 'Page Limits',
    'metadata_format': 'Format Requirements',
    'metadata_addressed_factors': 'Addressed Factors',
    'metadata_criticality': 'Requirement Criticality',
    'metadata_modal_verb': 'Modal Verb (shall/should/may)',
    'metadata_subject': 'Subject (Contractor/Government)',
}

metadata_counts = defaultdict(int)
nodes_with_any_metadata = set()

for node_id, data in G.nodes(data=True):
    for attr in metadata_attrs.keys():
        if attr in data and data[attr]:
            metadata_counts[attr] += 1
            nodes_with_any_metadata.add(node_id)

print(f"Total nodes with metadata: {len(nodes_with_any_metadata)}")
print(f"\nMetadata Attribute Coverage:")
for attr, description in metadata_attrs.items():
    count = metadata_counts[attr]
    status = "✅" if count > 0 else "⚠️"
    print(f"  {status} {description:35} {count:4}")

# Sample metadata-enriched entities
print(f"\n🔍 SAMPLE METADATA-ENRICHED ENTITIES")
print(f"{'─' * 70}")

# Find evaluation factors with metadata
eval_factors_with_meta = [
    (n, d) for n, d in G.nodes(data=True)
    if d.get('entity_type') == 'evaluation_factor' and 'metadata_importance' in d
]

if eval_factors_with_meta:
    print(f"\nEvaluation Factors ({len(eval_factors_with_meta)} with metadata):")
    for name, data in eval_factors_with_meta[:3]:
        print(f"\n  Entity: {name[:60]}")
        print(f"    Importance: {data.get('metadata_importance', 'N/A')}")
        if 'metadata_weight' in data:
            print(f"    Weight: {data.get('metadata_weight')}")
        if 'metadata_subfactors' in data:
            print(f"    Subfactors: {data.get('metadata_subfactors')[:80]}...")
        # Check description is still natural language
        desc = data.get('description', '')[:150]
        print(f"    Description: {desc}...")
        if desc and not desc.startswith('Factor'):
            print(f"    ✅ Natural language preserved")

# Find requirements with metadata
reqs_with_meta = [
    (n, d) for n, d in G.nodes(data=True)
    if d.get('entity_type') == 'requirement' and 'metadata_criticality' in d
]

if reqs_with_meta:
    print(f"\nRequirements ({len(reqs_with_meta)} with metadata):")
    for name, data in reqs_with_meta[:3]:
        print(f"\n  Entity: {name[:60]}")
        print(f"    Criticality: {data.get('metadata_criticality', 'N/A')}")
        if 'metadata_modal_verb' in data:
            print(f"    Modal Verb: {data.get('metadata_modal_verb')}")
        if 'metadata_subject' in data:
            print(f"    Subject: {data.get('metadata_subject')}")

# Strategic language check
print(f"\n🎯 STRATEGIC REASONING VALIDATION")
print(f"{'─' * 70}")

strategic_phrases = [
    'competitive advantage',
    'gain favor',
    'innovative',
    'demonstrate',
    'position',
    'risk mitigation',
    'outstanding',
    'low-risk',
]

strategic_count = 0
sample_strategic = []

for node_id, data in G.nodes(data=True):
    desc = data.get('description', '').lower()
    for phrase in strategic_phrases:
        if phrase in desc:
            strategic_count += 1
            if len(sample_strategic) < 3:
                sample_strategic.append((node_id, phrase, desc[:100]))
            break

print(f"Entities with strategic language: {strategic_count}")
if sample_strategic:
    print(f"\nSample strategic descriptions:")
    for entity, phrase, desc in sample_strategic:
        print(f"  • '{phrase}' in: {desc}...")

# Comparison to main branch baseline
print(f"\n📈 COMPARISON TO MAIN BRANCH BASELINE")
print(f"{'─' * 70}")

baseline = {
    'entities': 4462,
    'relationships': 6190,
    'evaluated_by': 22,
    'guides': 23,
}

print(f"{'Metric':30} {'MCPP II':>10} {'Main Baseline':>15} {'Delta':>10}")
print(f"{'─' * 70}")
print(f"{'Total Entities':30} {len(G.nodes()):>10,} {baseline['entities']:>15,} {len(G.nodes()) - baseline['entities']:>+10,}")
print(f"{'Total Relationships':30} {len(G.edges()):>10,} {baseline['relationships']:>15,} {len(G.edges()) - baseline['relationships']:>+10,}")
print(f"{'EVALUATED_BY':30} {key_rels['EVALUATED_BY']:>10} {baseline['evaluated_by']:>15} {key_rels['EVALUATED_BY'] - baseline['evaluated_by']:>+10}")
print(f"{'GUIDES':30} {key_rels['GUIDES']:>10} {baseline['guides']:>15} {key_rels['GUIDES'] - baseline['guides']:>+10}")

# Final verdict
print(f"\n{'=' * 70}")
print(f"PHASE 7 ASSESSMENT VERDICT")
print(f"{'=' * 70}")

issues = []
successes = []

if len(G.nodes()) < baseline['entities'] * 0.7:
    issues.append("❌ Entity count significantly below baseline (extraction degraded)")
else:
    successes.append(f"✅ Entity extraction: {len(G.nodes()):,} entities ({(len(G.nodes())/baseline['entities']*100):.1f}% of baseline)")

if key_rels['EVALUATED_BY'] == 0:
    issues.append("❌ No EVALUATED_BY relationships (Phase 6 broken)")
else:
    successes.append(f"✅ Phase 6 inference: {key_rels['EVALUATED_BY']} EVALUATED_BY relationships")

if len(nodes_with_any_metadata) == 0:
    issues.append("❌ No metadata enrichment (Phase 7 not executed)")
else:
    successes.append(f"✅ Phase 7 enrichment: {len(nodes_with_any_metadata)} entities with metadata")

if strategic_count < 5:
    issues.append("⚠️ Limited strategic language (may indicate description degradation)")
else:
    successes.append(f"✅ Strategic reasoning: {strategic_count} entities with competitive intelligence")

print()
for success in successes:
    print(success)

if issues:
    print()
    for issue in issues:
        print(issue)
else:
    print("\n🎉 All quality checks passed!")

print()
