"""Inspect raw requirement entity structure."""
from neo4j import GraphDatabase
import os
import json
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

with driver.session(database='neo4j') as session:
    result = session.run("MATCH (r:`37b_test_mcpp`) WHERE r.entity_type = 'requirement' RETURN r LIMIT 3")
    records = list(result)
    
    print(f"Found {len(records)} requirement samples:\n")
    
    for i, record in enumerate(records, 1):
        entity = dict(record['r'])
        print(f"\n{'=' * 80}")
        print(f"REQUIREMENT #{i}")
        print('=' * 80)
        
        # Print fields individually to handle Neo4j types
        for key, value in entity.items():
            print(f"{key}: {value}")

driver.close()
