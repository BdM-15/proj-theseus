#!/usr/bin/env python3
"""
Check the quality of Algorithm 8 relationship inferences.

Algorithm 8 uses confidence=0.7 as default when LLM doesn't provide confidence.
This script examines those relationships to verify semantic quality.
"""

import os
import sys
from pathlib import Path

# Add project root to path
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
    
    # Query 1: Get sample of Algorithm 8 relationships
    query_sample = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE r.confidence = 0.7
    RETURN 
        n.entity_name as source_name,
        n.entity_type as source_type,
        type(r) as relationship_type,
        r.reasoning as reasoning,
        m.entity_name as target_name,
        m.entity_type as target_type,
        n.description as source_desc,
        m.description as target_desc
    LIMIT 20
    """
    
    # Query 2: Count by relationship type
    query_counts = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE r.confidence = 0.7
    RETURN type(r) as rel_type, count(*) as count
    ORDER BY count DESC
    """
    
    # Query 3: Count by source entity type
    query_source_types = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    WHERE r.confidence = 0.7
    RETURN n.entity_type as entity_type, count(*) as count
    ORDER BY count DESC
    """
    
    with driver.session(database='neo4j') as session:
        # Get sample relationships
        sample_results = list(session.run(query_sample))
        
        # Get relationship type counts
        count_results = list(session.run(query_counts))
        
        # Get source entity type counts
        source_type_results = list(session.run(query_source_types))
        
        print("\n" + "="*100)
        print("ALGORITHM 8 RELATIONSHIP QUALITY ASSESSMENT")
        print("="*100)
        
        print(f"\nTotal relationships with confidence=0.7: {sum(r['count'] for r in count_results)}")
        
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
            if record['reasoning']:
                print(f"   → REASONING: {record['reasoning'][:250]}")
            else:
                print(f"   → REASONING: [No reasoning provided]")
            
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
