"""
Analyze Orphaned Node Properties: Why no entity_name?
======================================================

Finding: Orphaned nodes missing entity_name property
This suggests they're created differently than connected entities
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = 'afcapv_adab_iss_2025'
db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("="*80)
print("ORPHANED NODE PROPERTY ANALYSIS")
print("="*80)

with driver.session(database=db) as session:
    # Get orphaned nodes with ALL properties
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE NOT (n)-[]-()
        RETURN properties(n) as props, labels(n) as labels
        LIMIT 5
    """)
    
    print(f"\n1. SAMPLE ORPHANED NODES (All Properties)")
    for i, record in enumerate(result, 1):
        print(f"\n   Orphan #{i}:")
        print(f"   Labels: {record['labels']}")
        props = record['props']
        for key, value in sorted(props.items()):
            # Truncate long values
            val_str = str(value)[:100]
            print(f"     {key}: {val_str}")
    
    # Compare with connected nodes
    result = session.run(f"""
        MATCH (n:{workspace})-[r]-()
        RETURN properties(n) as props, labels(n) as labels
        LIMIT 5
    """)
    
    print(f"\n2. SAMPLE CONNECTED NODES (All Properties)")
    for i, record in enumerate(result, 1):
        print(f"\n   Connected #{i}:")
        print(f"   Labels: {record['labels']}")
        props = record['props']
        for key, value in sorted(props.items()):
            val_str = str(value)[:100]
            print(f"     {key}: {val_str}")
    
    # Check property key distribution
    result = session.run(f"""
        MATCH (n:{workspace})
        WHERE NOT (n)-[]-()
        UNWIND keys(n) as key
        RETURN key, count(*) as freq
        ORDER BY freq DESC
    """)
    
    print(f"\n3. PROPERTY KEYS IN ORPHANED NODES")
    orphan_keys = {}
    for record in result:
        orphan_keys[record['key']] = record['freq']
        print(f"   {record['key']}: {record['freq']} nodes")
    
    result = session.run(f"""
        MATCH (n:{workspace})-[]-()
        WITH DISTINCT n
        UNWIND keys(n) as key
        RETURN key, count(*) as freq
        ORDER BY freq DESC
    """)
    
    print(f"\n4. PROPERTY KEYS IN CONNECTED NODES")
    connected_keys = {}
    for record in result:
        connected_keys[record['key']] = record['freq']
        print(f"   {record['key']}: {record['freq']} nodes")
    
    # Find differences
    missing_in_orphans = set(connected_keys.keys()) - set(orphan_keys.keys())
    extra_in_orphans = set(orphan_keys.keys()) - set(connected_keys.keys())
    
    print(f"\n5. SCHEMA DIFFERENCES")
    if missing_in_orphans:
        print(f"   Properties MISSING in orphaned nodes:")
        for key in sorted(missing_in_orphans):
            print(f"     - {key} (in {connected_keys[key]} connected nodes)")
    
    if extra_in_orphans:
        print(f"   Properties ONLY in orphaned nodes:")
        for key in sorted(extra_in_orphans):
            print(f"     - {key} (in {orphan_keys[key]} orphaned nodes)")

driver.close()

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
print("""
If orphaned nodes have DIFFERENT properties than connected nodes:
  → Created by different code path (LightRAG vs Phase 6/7)
  → Likely created during insert_content_list(), not by Phase 6
  → These are the chunk-level entities that never get enhanced

If orphaned nodes have SAME schema but no relationships:
  → Created by Phase 6 but relationship inference failed
  → Issue is in semantic_post_processor.py logic
""")
