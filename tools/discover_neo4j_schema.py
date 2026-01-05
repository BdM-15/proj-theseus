#!/usr/bin/env python3
"""Discover Neo4j schema and data."""

import os
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_query(query, params=None):
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(r) for r in result]

print("=" * 70)
print("NEO4J SCHEMA DISCOVERY")
print("=" * 70)

# 1. Get all node labels
print("\n📋 NODE LABELS IN DATABASE:")
labels = run_query("CALL db.labels() YIELD label RETURN label ORDER BY label")
for l in labels:
    print(f"  - {l['label']}")

# 2. Get all relationship types
print("\n🔗 RELATIONSHIP TYPES:")
rel_types = run_query("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType ORDER BY relationshipType")
for r in rel_types:
    print(f"  - {r['relationshipType']}")

# 3. Count nodes by label
print("\n📊 NODE COUNTS BY LABEL:")
for l in labels:
    label = l['label']
    count = run_query(f"MATCH (n:`{label}`) RETURN count(n) as count")[0]['count']
    print(f"  {label}: {count}")

# 4. Count relationships by type
print("\n📊 RELATIONSHIP COUNTS BY TYPE:")
for r in rel_types:
    rel_type = r['relationshipType']
    count = run_query(f"MATCH ()-[r:`{rel_type}`]->() RETURN count(r) as count")[0]['count']
    print(f"  {rel_type}: {count}")

# 5. Sample nodes from each label
print("\n📝 SAMPLE NODES (first from each label):")
for l in labels[:5]:  # First 5 labels
    label = l['label']
    sample = run_query(f"MATCH (n:`{label}`) RETURN properties(n) as props LIMIT 1")
    if sample:
        print(f"\n  {label}:")
        props = sample[0]['props']
        for k, v in list(props.items())[:5]:
            val_str = str(v)[:60] if v else 'null'
            print(f"    {k}: {val_str}")

# 6. Check for entity_type property
print("\n🔍 ENTITY TYPE DISTRIBUTION (if exists):")
try:
    types = run_query("""
        MATCH (n)
        WHERE n.entity_type IS NOT NULL
        RETURN n.entity_type as type, count(n) as count
        ORDER BY count DESC
        LIMIT 20
    """)
    for t in types:
        print(f"  {t['type']}: {t['count']}")
except Exception as e:
    print(f"  Error: {e}")

# 7. Sample relationships
print("\n🔗 SAMPLE RELATIONSHIPS:")
sample_rels = run_query("""
    MATCH (a)-[r]->(b)
    RETURN labels(a)[0] as from_label, type(r) as rel, labels(b)[0] as to_label,
           a.entity_name as from_name, b.entity_name as to_name
    LIMIT 10
""")
for sr in sample_rels:
    print(f"  ({sr['from_name'][:30] if sr['from_name'] else sr['from_label']}) "
          f"-[{sr['rel']}]-> "
          f"({sr['to_name'][:30] if sr['to_name'] else sr['to_label']})")

driver.close()
