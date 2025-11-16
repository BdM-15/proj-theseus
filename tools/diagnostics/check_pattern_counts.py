"""Quick check of Pattern 1 vs Pattern 2 relationship counts."""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")

with driver.session(database='neo4j') as session:
    # Pattern 1: SATISFIED_BY
    result1 = session.run(f"""
        MATCH (r:`{workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d:`{workspace}`)
        WHERE rel.type = 'SATISFIED_BY'
          AND r.entity_type = 'requirement'
          AND d.entity_type = 'deliverable'
        RETURN count(rel) as count
    """)
    pattern1_count = result1.single()['count']
    
    # Pattern 2: PRODUCES
    result2 = session.run(f"""
        MATCH (w:`{workspace}`)-[rel:INFERRED_RELATIONSHIP]->(d:`{workspace}`)
        WHERE rel.type = 'PRODUCES'
          AND w.entity_type IN ['statement_of_work', 'pws', 'soo']
          AND d.entity_type = 'deliverable'
        RETURN count(rel) as count
    """)
    pattern2_count = result2.single()['count']
    
    # Total deliverables
    result3 = session.run(f"""
        MATCH (d:`{workspace}`)
        WHERE d.entity_type = 'deliverable'
        RETURN count(d) as count
    """)
    total_delivs = result3.single()['count']
    
    print(f"\n{'='*60}")
    print(f"Pattern Relationship Counts")
    print(f"{'='*60}")
    print(f"Pattern 1 (SATISFIED_BY):  {pattern1_count} relationships")
    print(f"Pattern 2 (PRODUCES):      {pattern2_count} relationships")
    print(f"Total:                     {pattern1_count + pattern2_count} relationships")
    print(f"\nTotal deliverables:        {total_delivs}")
    print(f"{'='*60}\n")

driver.close()
