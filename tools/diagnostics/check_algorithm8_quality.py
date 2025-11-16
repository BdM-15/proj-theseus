#!/usr/bin/env python3
"""
Check the quality of Algorithm 8 relationship inferences.

Algorithm 8 uses confidence=0.7 as default when LLM doesn't provide confidence.
This script examines those relationships to verify semantic quality.
"""

import os
import sys
from pathlib import Path

# Add project root to path (tools/diagnostics/ -> project root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase


def check_algorithm8_relationships(workspace: str = "afcapv_adab_iss_2025"):
    """
    Query relationships with confidence=0.7 (Algorithm 8's default)
    and analyze their semantic quality.
    """
    
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    # Get Algorithm 8 relationships (those with reasoning from orphan resolution)
    # Since we removed confidence requirement, we'll look for INFERRED_RELATIONSHIP type
    query_sample = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE type(r) = 'INFERRED_RELATIONSHIP'
    RETURN 
        n.entity_name as source_name,
        n.entity_type as source_type,
        type(r) as relationship_type,
        r.reasoning as reasoning,
        r.confidence as confidence,
        m.entity_name as target_name,
        m.entity_type as target_type,
        n.description as source_desc,
        m.description as target_desc
    ORDER BY id(r) DESC
    LIMIT 20
    """
    
    # Count by relationship type (all semantic inference algorithms)
    query_counts = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE type(r) = 'INFERRED_RELATIONSHIP'
    RETURN type(r) as rel_type, count(*) as count
    ORDER BY count DESC
    """
    
    # Count by source entity type (for Algorithm 8 patterns)
    query_source_types = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE type(r) = 'INFERRED_RELATIONSHIP'
    RETURN n.entity_type as entity_type, count(*) as count
    ORDER BY count DESC
    """
    
    # Get relationships WITH reasoning (Algorithm 8)
    query_with_reasoning = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE type(r) = 'INFERRED_RELATIONSHIP' AND r.reasoning IS NOT NULL AND r.reasoning <> ''
    RETURN count(*) as count
    """
    
    # Get relationships WITHOUT reasoning (other algorithms or LightRAG)
    query_without_reasoning = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE type(r) = 'INFERRED_RELATIONSHIP' AND (r.reasoning IS NULL OR r.reasoning = '')
    RETURN count(*) as count
    """
    
    with driver.session(database='neo4j') as session:
        # Get sample relationships
        sample_results = list(session.run(query_sample))
        
        # Get relationship type counts
        count_results = list(session.run(query_counts))
        
        # Get source entity type counts
        source_type_results = list(session.run(query_source_types))
        
        # Get reasoning stats
        with_reasoning = session.run(query_with_reasoning).single()['count']
        without_reasoning = session.run(query_without_reasoning).single()['count']
        total_inferred = with_reasoning + without_reasoning
        
        print("\n" + "="*100)
        print("ALGORITHM 8 RELATIONSHIP QUALITY ASSESSMENT")
        print("="*100)
        
        print(f"\nTotal INFERRED_RELATIONSHIP relationships: {total_inferred}")
        print(f"  With reasoning (Algorithm 8): {with_reasoning} ({with_reasoning/total_inferred*100:.1f}%)")
        print(f"  Without reasoning (other algorithms): {without_reasoning} ({without_reasoning/total_inferred*100:.1f}%)")
        
        print("\n📊 RELATIONSHIP TYPE DISTRIBUTION:")
        print("-"*100)
        for record in count_results:
            print(f"  {record['rel_type']:40s} : {record['count']:3d}")
        
        print("\n📊 SOURCE ENTITY TYPE DISTRIBUTION:")
        print("-"*100)
        for record in source_type_results:
            print(f"  {record['entity_type']:40s} : {record['count']:3d}")
        
        print("\n🔍 SAMPLE RELATIONSHIPS (Quality Check):")
        print("="*100)
        
        for i, record in enumerate(sample_results, 1):
            print(f"\n{i}. SOURCE: {record['source_name']} ({record['source_type']})")
            if record['source_desc']:
                print(f"   Description: {record['source_desc'][:150]}...")
            
            print(f"\n   → RELATIONSHIP: {record['relationship_type']}")
            
            # Show confidence if present (some algorithms might still include it)
            if record.get('confidence'):
                print(f"   → CONFIDENCE: {record['confidence']}")
            
            if record['reasoning']:
                # Wrap reasoning text for readability
                reasoning = record['reasoning'][:300]
                print(f"   → REASONING: {reasoning}")
            else:
                print(f"   → REASONING: [No reasoning provided - not from Algorithm 8]")
            
            print(f"\n   TARGET: {record['target_name']} ({record['target_type']})")
            if record['target_desc']:
                print(f"   Description: {record['target_desc'][:150]}...")
            
            print("\n" + "-"*100)
        
        # Query 4: Check if any truly bad relationships exist
        query_check_orphans = f"""
        MATCH (n:`{workspace}`)
        WHERE NOT (n)-[]-()
        RETURN n.entity_name as name, n.entity_type as type
        LIMIT 10
        """
        
        orphan_results = list(session.run(query_check_orphans))
        
        print("\n🔍 REMAINING ORPHANS (should be truly unconnectable):")
        print("="*100)
        if orphan_results:
            for i, record in enumerate(orphan_results, 1):
                print(f"{i}. {record['name']} ({record['type']})")
        else:
            print("No orphans found!")
        
        # Summary stats
        if with_reasoning > 0:
            reasoning_pct = (with_reasoning / total_inferred) * 100
            print(f'\n📊 SUMMARY:')
            print(f'   Algorithm 8 relationships (with reasoning): {with_reasoning} ({reasoning_pct:.1f}%)')
            print(f'   Other algorithm relationships: {without_reasoning}')
            print(f'   Total INFERRED relationships: {total_inferred}')
        
        print('\n✅ No confidence requirement - trusting LLM semantic quality')
    
    driver.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check Algorithm 8 relationship quality")
    parser.add_argument(
        "workspace",
        nargs="?",
        default="afcapv_adab_iss_2025",
        help="Neo4j workspace label (default: afcapv_adab_iss_2025)"
    )
    
    args = parser.parse_args()
    check_algorithm8_relationships(args.workspace)
