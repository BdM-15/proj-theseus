"""Check what properties are actually stored in Neo4j nodes"""
import os
from dotenv import load_dotenv
load_dotenv()

from src.inference.neo4j_graph_io import Neo4jGraphIO

neo = Neo4jGraphIO()

# Get a few sample nodes with ALL their properties
query = """
MATCH (n:afcapv_adab_iss_2025_pwstst_4mod)
RETURN n
LIMIT 5
"""

result = neo.driver.session(database='neo4j').run(query)
nodes = list(result)

print("\n" + "=" * 100)
print("SAMPLE NEO4J NODE PROPERTIES")
print("=" * 100)

for i, record in enumerate(nodes, 1):
    node = record['n']
    print(f"\nNode {i}:")
    print(f"  Internal ID: {node.id}")
    print(f"  Labels: {list(node.labels)}")
    print(f"  Properties:")
    for key, value in dict(node).items():
        # Truncate long values
        value_str = str(value)[:100] if value else "None"
        print(f"    {key}: {value_str}")

# Check for table entities
print("\n" + "=" * 100)
table_query = """
MATCH (n:afcapv_adab_iss_2025_pwstst_4mod)
WHERE n.source_id CONTAINS '[TABLE-P'
RETURN count(n) AS count
"""
table_result = neo.driver.session(database='neo4j').run(table_query)
table_count = list(table_result)[0]['count']
print(f"Entities with [TABLE-P] in source_id: {table_count}")

# Total count
total_query = "MATCH (n:afcapv_adab_iss_2025_pwstst_4mod) RETURN count(n) AS count"
total_result = neo.driver.session(database='neo4j').run(total_query)
total_count = list(total_result)[0]['count']
print(f"Total entities in workspace: {total_count}")

neo.close()
