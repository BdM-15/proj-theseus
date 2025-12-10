"""Check entity_name casing in Neo4j."""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session(database='neo4j') as session:
    # Check what fields LightRAG actually stores
    result = session.run("""
        MATCH (n:`37c_test_mcpp`)
        RETURN n.entity_id as entity_id, 
               n.entity_name as entity_name, 
               n.description as description
        LIMIT 5
    """)
    
    records = list(result)
    print(f"LightRAG Neo4j Storage Format:\n")
    print(f"{'='*80}\n")
    
    for i, r in enumerate(records, 1):
        entity_id = r['entity_id'] or 'N/A'
        entity_name = r['entity_name'] or 'N/A'
        desc = r['description'][:100] if r['description'] else 'N/A'
        
        print(f"Entity {i}:")
        print(f"  entity_id:   {entity_id}")
        print(f"  entity_name: {entity_name}")
        print(f"  description: {desc}")
        print("=" * 80 + "\n")

driver.close()
