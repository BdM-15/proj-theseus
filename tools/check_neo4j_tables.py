#!/usr/bin/env python3
"""Check table relationships in Neo4j."""

import os
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
user = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "")

print(f"Connecting to Neo4j at {uri}...")

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session(database="swa_tas") as session:
    # Count all nodes
    result = session.run("MATCH (n) RETURN count(n) as count")
    total_nodes = result.single()["count"]
    print(f"Total nodes: {total_nodes}")
    
    # Count table nodes
    result = session.run("MATCH (n) WHERE n.entity_type = 'table' RETURN count(n) as count")
    table_nodes = result.single()["count"]
    print(f"Table nodes: {table_nodes}")
    
    # Count relationships involving tables
    result = session.run("""
        MATCH (t)-[r]-(other)
        WHERE t.entity_type = 'table'
        RETURN count(r) as count
    """)
    table_rels = result.single()["count"]
    print(f"Relationships involving tables: {table_rels}")
    
    # Count CHILD_OF relationships
    result = session.run("""
        MATCH ()-[r:CHILD_OF]->()
        RETURN count(r) as count
    """)
    child_of = result.single()["count"]
    print(f"CHILD_OF relationships: {child_of}")
    
    # Sample table relationships
    print("\nSample table relationships:")
    result = session.run("""
        MATCH (t)-[r]-(other)
        WHERE t.entity_type = 'table'
        RETURN t.entity_name as table_name, type(r) as rel_type, other.entity_name as other_name
        LIMIT 10
    """)
    for record in result:
        print(f"  {record['table_name'][:30]} --[{record['rel_type']}]--> {record['other_name'][:30]}")

driver.close()
