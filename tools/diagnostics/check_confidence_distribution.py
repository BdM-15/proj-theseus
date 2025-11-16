#!/usr/bin/env python3
"""
Check confidence distribution across all relationships in Neo4j.

This helps determine if the LLM is actually providing confidence values
or if we're always falling back to the default 0.7.
"""

import os
import sys
from pathlib import Path

# Add project root to path (tools/diagnostics/ -> project root)
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase


def check_confidence_distribution(workspace: str = "afcapv_adab_iss_2025"):
    """Check confidence distribution across all relationships."""
    
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    # Get confidence distribution
    query = f"""
    MATCH (n:`{workspace}`)-[r]->(m:`{workspace}`)
    RETURN r.confidence as conf, count(*) as count
    ORDER BY conf
    """
    
    with driver.session(database='neo4j') as session:
        results = list(session.run(query))
        
        print("\n" + "="*80)
        print("CONFIDENCE DISTRIBUTION ACROSS ALL RELATIONSHIPS")
        print("="*80)
        
        total = sum(record['count'] for record in results)
        
        for record in results:
            conf = record['conf']
            count = record['count']
            pct = (count / total) * 100
            bar = '#' * int(count / 50)
            # Handle both float and string confidence values
            conf_str = f'{float(conf):4.2f}' if conf is not None else 'None'
            print(f'{conf_str}: {count:5d} ({pct:5.1f}%) {bar}')
        
        print(f'\nTotal relationships: {total}')
        
        # Find 0.7 count
        default_count = next((r['count'] for r in results if r['conf'] == 0.7), 0)
        if default_count > 0:
            default_pct = (default_count / total) * 100
            print(f'\n⚠️  Relationships with 0.7 confidence: {default_count} ({default_pct:.1f}%)')
            print(f'    This is the DEFAULT fallback value - LLM likely not providing confidence!')
        
        # Check if we have variety in confidence values
        unique_values = len(results)
        print(f'\nUnique confidence values: {unique_values}')
        
        if unique_values == 1 and results[0]['conf'] == 0.7:
            print('\n❌ PROBLEM: ALL relationships have confidence=0.7!')
            print('   The LLM is NOT providing confidence values.')
            print('   We are ALWAYS using the fallback default.')
        elif default_pct > 80:
            print(f'\n⚠️  WARNING: {default_pct:.1f}% of relationships use default confidence!')
            print('   LLM is rarely providing confidence values.')
        else:
            print('\n✅ Good: LLM is providing varied confidence values.')
    
    driver.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check confidence distribution")
    parser.add_argument(
        "workspace",
        nargs="?",
        default="afcapv_adab_iss_2025",
        help="Neo4j workspace label (default: afcapv_adab_iss_2025)"
    )
    
    args = parser.parse_args()
    check_confidence_distribution(args.workspace)
