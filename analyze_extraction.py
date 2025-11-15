#!/usr/bin/env python3
"""
Analyze ISS RFP extraction results to identify over-extraction issues.
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
    auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
)

def analyze_extraction():
    with driver.session(database=os.getenv("NEO4J_DATABASE", "neo4j")) as session:
        workspace = "afcapv_adab_iss_2025"
        
        print("="*80)
        print("ENTITY TYPE DISTRIBUTION")
        print("="*80)
        
        # Get entity type counts (workspace is a LABEL, not property)
        result = session.run(f"""
            MATCH (n:{workspace})
            RETURN n.entity_type as type, count(*) as count
            ORDER BY count DESC
        """)
        
        total = 0
        for record in result:
            count = record['count']
            total += count
            print(f"{record['type']:30} {count:6}")
        
        print(f"{'TOTAL':30} {total:6}")
        print()
        
        # Check for parsing artifacts (entity_id contains the name)
        print("="*80)
        print("PARSING ARTIFACTS (entities with | and numbers)")
        print("="*80)
        
        result = session.run(f"""
            MATCH (n:{workspace})
            WHERE n.entity_id =~ '.*\\|.*\\d+.*' OR n.entity_id =~ '.*Page.*\\|.*'
            RETURN n.entity_type as type, n.entity_id as name
            LIMIT 50
        """)
        
        artifacts = list(result)
        print(f"Found {len(artifacts)} potential artifacts")
        for record in artifacts[:20]:
            print(f"  {record['type']:20} | {record['name']}")
        
        print()
        
        # Check for duplicate entities (similar names)
        print("="*80)
        print("POTENTIAL DUPLICATES (similar entity names)")
        print("="*80)
        
        result = session.run(f"""
            MATCH (n:{workspace})
            WITH n.entity_type as type, 
                 toLower(replace(replace(n.entity_id, ' ', ''), '-', '')) as normalized,
                 collect(n.entity_id) as variants
            WHERE size(variants) > 1
            RETURN type, variants, size(variants) as count
            ORDER BY count DESC
            LIMIT 20
        """)
        
        for record in result:
            print(f"{record['type']:20} ({record['count']} variants): {', '.join(record['variants'][:3])}")
        
        print()
        
        # Get relationship stats
        print("="*80)
        print("RELATIONSHIP STATISTICS")
        print("="*80)
        
        result = session.run(f"""
            MATCH (n:{workspace})-[r]->()
            RETURN type(r) as rel_type, count(*) as count
            ORDER BY count DESC
        """)
        
        total_rels = 0
        for record in result:
            count = record['count']
            total_rels += count
            print(f"{record['rel_type']:30} {count:6}")
        
        print(f"{'TOTAL':30} {total_rels:6}")
        print()
        
        # Avg relationships per entity
        print(f"Average relationships per entity: {total_rels/total:.2f}")
        print()
        
        # Check for contamination from LightRAG examples
        print("="*80)
        print("CONTAMINATION CHECK (non-RFP terms)")
        print("="*80)
        
        result = session.run(f"""
            MATCH (n:{workspace})
            WHERE toLower(n.entity_id) CONTAINS 'knowledge'
               OR toLower(n.entity_id) CONTAINS 'graph'
               OR toLower(n.entity_id) CONTAINS 'extraction'
               OR toLower(n.entity_id) CONTAINS 'llm'
               OR toLower(n.entity_id) CONTAINS 'taylor'
               OR toLower(n.entity_id) CONTAINS 'alex'
               OR toLower(n.entity_id) CONTAINS 'jordan'
               OR toLower(n.entity_id) CONTAINS 'beekeeper'
            RETURN n.entity_type as type, n.entity_id as name, 
                   substring(n.description, 0, 100) as desc
            LIMIT 50
        """)
        
        contaminated = list(result)
        print(f"Found {len(contaminated)} potentially contaminated entities")
        for record in contaminated:
            print(f"  {record['type']:20} | {record['name']:40}")
            if record['desc']:
                print(f"    → {record['desc']}")

if __name__ == "__main__":
    try:
        analyze_extraction()
    finally:
        driver.close()
