"""
Quick check of Neo4j source_id values for table entity validation.
Uses Neo4j Python driver directly with correct connection settings.
"""
import os
from neo4j import GraphDatabase

# Load from .env
uri = "neo4j://localhost:7687"
username = "neo4j"
password = "govcon-capture-2025"
database = "neo4j"
workspace = "afcapv_adab_iss_2025_pwstst_4mod"

print(f"Connecting to Neo4j at {uri}...")
print(f"Workspace: {workspace}\n")

driver = GraphDatabase.driver(uri, auth=(username, password))

try:
    with driver.session(database=database) as session:
        # First, list all labels (workspaces) in the database
        labels_query = "CALL db.labels()"
        result = session.run(labels_query)
        labels = [record["label"] for record in result]
        
        print(f"Available labels/workspaces in Neo4j:")
        for label in labels:
            count_q = f"MATCH (n:`{label}`) RETURN count(n) AS count"
            count_r = session.run(count_q)
            count = count_r.single()['count']
            print(f"  - {label}: {count} nodes")
        
        print(f"\n{'=' * 100}")
        print(f"Looking for workspace: {workspace}")
        
        # Get sample entities from target workspace
        query = f"""
        MATCH (n:`{workspace}`)
        RETURN n.entity_id AS name, n.source_id AS sid, n.entity_type AS type
        LIMIT 20
        """
        
        result = session.run(query)
        records = list(result)
        
        if not records:
            print(f"\n⚠️  Workspace '{workspace}' is EMPTY (0 entities)")
            print("This may indicate:")
            print("  1. Processing failed to write to Neo4j")
            print("  2. Workspace name mismatch")
            print("  3. Data was written to different workspace")
        else:
            print(f"\n{'#':>3} | {'Entity Name':50} | {'Type':20} | {'Source ID':30}")
            print("-" * 110)
            
            for i, record in enumerate(records, 1):
                name = (record.get('name', 'N/A') or 'N/A')[:48]
                etype = (record.get('type', 'N/A') or 'N/A')[:18]
                sid = (record.get('sid', 'UNKNOWN') or 'UNKNOWN')[:28]
                print(f"{i:3} | {name:50} | {etype:20} | {sid:30}")
        
        # Count by source_id pattern
        count_query = f"""
        MATCH (n:`{workspace}`)
        RETURN
            count(CASE WHEN n.source_id STARTS WITH 'chunk-' THEN 1 END) AS chunk_based,
            count(CASE WHEN n.source_id = 'UNKNOWN' OR n.source_id IS NULL THEN 1 END) AS unknown,
            count(n) AS total
        """
        
        result = session.run(count_query)
        record = result.single()
        
        chunk_based = record['chunk_based']
        unknown = record['unknown']
        total = record['total']
        other = total - chunk_based - unknown
        
        if total > 0:
            print(f"\n{'=' * 100}")
            print(f"Source ID Analysis:")
            print(f"  Chunk-based (chunk-...): {chunk_based:4} ({chunk_based/total*100:.1f}%)")
            print(f"  UNKNOWN/missing:         {unknown:4} ({unknown/total*100:.1f}%)")
            print(f"  Other formats:           {other:4} ({other/total*100:.1f}%)")
            print(f"  Total entities:          {total:4}")
            
            if chunk_based == total:
                print(f"\n✅ SUCCESS: 100% of entities have chunk-based source_id!")
            elif chunk_based > 0:
                print(f"\n⚠️  PARTIAL: {chunk_based/total*100:.1f}% have chunk-based source_id")
            else:
                print(f"\n❌ FAILURE: No entities have chunk-based source_id (all UNKNOWN)")
            
finally:
    driver.close()
