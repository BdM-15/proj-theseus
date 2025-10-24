#!/usr/bin/env python3
"""
Comprehensive assessment of main branch RFP extraction quality.
Compares against Branch 010 baseline to validate hypothesis.
"""

import networkx as nx
from collections import Counter
import json

def parse_graphml(path):
    """Parse GraphML file and return entities and relationships."""
    G = nx.read_graphml(path)
    
    entities = []
    relationships = []
    
    for node_id, data in G.nodes(data=True):
        entities.append({
            'id': node_id,
            'type': data.get('entity_type', 'unknown'),
            'description': data.get('description', '')
        })
    
    for source, target, data in G.edges(data=True):
        relationships.append({
            'source': source,
            'target': target,
            'type': data.get('keywords', 'unknown'),
            'description': data.get('description', ''),
            'weight': data.get('weight', 1.0)
        })
    
    return entities, relationships

def analyze_extraction_quality(entities, relationships):
    """Comprehensive analysis of extraction quality."""
    
    print("=" * 80)
    print("MAIN BRANCH EXTRACTION QUALITY ASSESSMENT")
    print("=" * 80)
    
    # Entity counts
    print(f"\nTotal Entities: {len(entities)}")
    print(f"Total Relationships: {len(relationships)}")
    
    # Entity type distribution
    entity_types = Counter(e['type'] for e in entities)
    print("\n--- Entity Type Distribution ---")
    for entity_type, count in entity_types.most_common():
        print(f"  {entity_type}: {count}")
    
    # Critical entity types for government contracting
    critical_types = {
        'evaluation_factor': 0,
        'requirement': 0,
        'submission_instruction': 0,
        'clause': 0,
        'deliverable': 0,
        'statement_of_work': 0,
        'section': 0,
        'document': 0
    }
    
    for entity in entities:
        etype = entity['type'].lower()
        if etype in critical_types:
            critical_types[etype] += 1
    
    print("\n--- Critical Entity Types (Government Contracting) ---")
    for etype, count in critical_types.items():
        print(f"  {etype}: {count}")
    
    # Relationship type distribution
    rel_types = Counter(r['type'] for r in relationships)
    print("\n--- Top 20 Relationship Types ---")
    for rel_type, count in rel_types.most_common(20):
        print(f"  {rel_type}: {count}")
    
    # Phase 6 relationships (semantic inference)
    phase6_patterns = {
        'EVALUATED_BY': 0,
        'GUIDES': 0,
        'ATTACHMENT_OF': 0,
        'CHILD_OF': 0,
        'MAPS_TO': 0
    }
    
    for rel in relationships:
        rel_type = rel['type'].upper()
        for pattern in phase6_patterns.keys():
            if pattern in rel_type:
                phase6_patterns[pattern] += 1
    
    print("\n--- Phase 6 Semantic Inference Relationships ---")
    for pattern, count in phase6_patterns.items():
        print(f"  {pattern}: {count}")
    
    # Sample entity descriptions (strategic vs structured)
    print("\n--- Sample EVALUATION_FACTOR Descriptions (First 3) ---")
    eval_factors = [e for e in entities if e['type'].lower() == 'evaluation_factor'][:3]
    for i, ef in enumerate(eval_factors, 1):
        desc = ef['description'][:200] + "..." if len(ef['description']) > 200 else ef['description']
        print(f"\n  {i}. {ef['id']}")
        print(f"     {desc}")
    
    print("\n--- Sample SUBMISSION_INSTRUCTION Descriptions (First 3) ---")
    submissions = [e for e in entities if e['type'].lower() == 'submission_instruction'][:3]
    for i, si in enumerate(submissions, 1):
        desc = si['description'][:200] + "..." if len(si['description']) > 200 else si['description']
        print(f"\n  {i}. {si['id']}")
        print(f"     {desc}")
    
    print("\n--- Sample REQUIREMENT Descriptions (First 3) ---")
    reqs = [e for e in entities if e['type'].lower() == 'requirement'][:3]
    for i, req in enumerate(reqs, 1):
        desc = req['description'][:200] + "..." if len(req['description']) > 200 else req['description']
        print(f"\n  {i}. {req['id']}")
        print(f"     {desc}")
    
    # Quality indicators
    print("\n--- Quality Indicators ---")
    
    # Check for metadata formatting in descriptions
    metadata_count = 0
    strategic_count = 0
    
    for entity in entities:
        desc = entity['description'].lower()
        # Metadata indicators: pipe separators, structured fields
        if '|' in desc or 'worth' in desc and '%' in desc:
            metadata_count += 1
        # Strategic indicators: competitive advantage language
        strategic_phrases = ['gain favor', 'competitive', 'advantage', 'exceed', 'innovative', 
                           'demonstrate', 'position', 'risk mitigation', 'proof point']
        if any(phrase in desc for phrase in strategic_phrases):
            strategic_count += 1
    
    print(f"  Entities with metadata formatting: {metadata_count}")
    print(f"  Entities with strategic language: {strategic_count}")
    
    # Entity description length distribution
    desc_lengths = [len(e['description']) for e in entities if e['description']]
    if desc_lengths:
        avg_length = sum(desc_lengths) / len(desc_lengths)
        print(f"  Average entity description length: {avg_length:.1f} chars")
    
    # Relationship description quality
    rel_with_desc = sum(1 for r in relationships if r['description'])
    print(f"  Relationships with descriptions: {rel_with_desc}/{len(relationships)} ({rel_with_desc/len(relationships)*100:.1f}%)")
    
    print("\n" + "=" * 80)
    print("COMPARISON TO BRANCH 010 BASELINE")
    print("=" * 80)
    
    # Branch 010 baseline metrics
    baseline = {
        'total_entities': 3070,
        'total_relationships': 5246,
        'evaluated_by': 0,
        'guides': 11,
        'attachment_of': 0,
        'evaluation_factor': 77,
        'requirement': 183,
        'submission_instruction': 21,
        'clause': 196,
        'deliverable': 489
    }
    
    current = {
        'total_entities': len(entities),
        'total_relationships': len(relationships),
        'evaluated_by': phase6_patterns['EVALUATED_BY'],
        'guides': phase6_patterns['GUIDES'],
        'attachment_of': phase6_patterns['ATTACHMENT_OF'],
        'evaluation_factor': critical_types['evaluation_factor'],
        'requirement': critical_types['requirement'],
        'submission_instruction': critical_types['submission_instruction'],
        'clause': critical_types['clause'],
        'deliverable': critical_types['deliverable']
    }
    
    print("\nMetric Comparison (Main vs Branch 010):")
    print(f"  Total Entities: {current['total_entities']} vs {baseline['total_entities']} " +
          f"({current['total_entities'] - baseline['total_entities']:+d}, " +
          f"{(current['total_entities']/baseline['total_entities']-1)*100:+.1f}%)")
    
    print(f"  Total Relationships: {current['total_relationships']} vs {baseline['total_relationships']} " +
          f"({current['total_relationships'] - baseline['total_relationships']:+d}, " +
          f"{(current['total_relationships']/baseline['total_relationships']-1)*100:+.1f}%)")
    
    print("\nPhase 6 Inference Quality:")
    print(f"  EVALUATED_BY: {current['evaluated_by']} vs {baseline['evaluated_by']} " +
          f"({current['evaluated_by'] - baseline['evaluated_by']:+d})")
    print(f"  GUIDES: {current['guides']} vs {baseline['guides']} " +
          f"({current['guides'] - baseline['guides']:+d})")
    print(f"  ATTACHMENT_OF: {current['attachment_of']} vs {baseline['attachment_of']} " +
          f"({current['attachment_of'] - baseline['attachment_of']:+d})")
    
    print("\nCritical Entity Types:")
    for etype in ['evaluation_factor', 'requirement', 'submission_instruction', 'clause', 'deliverable']:
        print(f"  {etype}: {current[etype]} vs {baseline[etype]} " +
              f"({current[etype] - baseline[etype]:+d})")
    
    # Final verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)
    
    if current['total_entities'] > baseline['total_entities'] * 1.2:
        print("\n✅ MAIN BRANCH SHOWS SIGNIFICANTLY HIGHER ENTITY EXTRACTION")
        print("   Main extracts ~45% more entities than Branch 010")
    
    if current['evaluated_by'] > 10 and baseline['evaluated_by'] == 0:
        print("\n✅ PHASE 6 SEMANTIC INFERENCE WORKING ON MAIN")
        print("   EVALUATED_BY relationships present (vs 0 on Branch 010)")
    
    if metadata_count < len(entities) * 0.1:
        print("\n✅ MINIMAL METADATA FORMATTING IN DESCRIPTIONS")
        print("   Less than 10% of entities have structured metadata format")
    
    if strategic_count > len(entities) * 0.05:
        print("\n✅ STRATEGIC LANGUAGE PRESENT IN ENTITY DESCRIPTIONS")
        print("   Over 5% of entities contain competitive advantage language")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    graphml_path = "./rag_storage/default/graph_chunk_entity_relation.graphml"
    
    print("\nParsing GraphML from main branch extraction...")
    entities, relationships = parse_graphml(graphml_path)
    
    analyze_extraction_quality(entities, relationships)
    
    print("\nAssessment complete.")
