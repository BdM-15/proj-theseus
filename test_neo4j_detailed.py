"""
Detailed Neo4j Data Inspection
Checks what data actually exists in the Neo4j database
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

def inspect_neo4j():
    """Inspect Neo4j database for any data."""
    
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    workspace = os.getenv('NEO4J_WORKSPACE', 'mcpp_drfp_2025')
    
    print("🔍 Detailed Neo4j Data Inspection")
    print("=" * 60)
    
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    with driver.session() as session:
        # 1. Count ALL nodes (regardless of label)
        result = session.run("MATCH (n) RETURN count(n) AS total")
        total = result.single()["total"]
        print(f"\n📊 Total nodes in database: {total}")
        
        # 2. List all node labels
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
        print(f"\n🏷️  All node labels in database ({len(labels)}):")
        for label in labels:
            print(f"   • {label}")
        
        # 3. Count nodes by label
        if labels:
            print(f"\n📊 Node count by label:")
            for label in labels:
                result = session.run(f"MATCH (n:`{label}`) RETURN count(n) AS count")
                count = result.single()["count"]
                print(f"   • {label}: {count} nodes")
        
        # 4. Sample nodes from each label
        if labels:
            print(f"\n🔍 Sample nodes:")
            for label in labels[:3]:  # Only show first 3 labels
                print(f"\n   Label: {label}")
                result = session.run(f"""
                    MATCH (n:`{label}`)
                    RETURN n
                    LIMIT 3
                """)
                for i, record in enumerate(result, 1):
                    node = record["n"]
                    props = dict(node.items())
                    print(f"      Node {i}:")
                    for key, value in list(props.items())[:5]:  # First 5 properties
                        if isinstance(value, str) and len(value) > 80:
                            value = value[:80] + "..."
                        print(f"         {key}: {value}")
        
        # 5. Count relationships
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS total")
        rel_total = result.single()["total"]
        print(f"\n🔗 Total relationships: {rel_total}")
        
        # 6. List relationship types
        result = session.run("CALL db.relationshipTypes()")
        rel_types = [record["relationshipType"] for record in result]
        if rel_types:
            print(f"\n🔗 Relationship types ({len(rel_types)}):")
            for rel_type in rel_types:
                print(f"   • {rel_type}")
        
        # 7. Check specific workspace
        print(f"\n🎯 Checking workspace label: '{workspace}'")
        result = session.run(f"MATCH (n:`{workspace}`) RETURN count(n) AS count")
        ws_count = result.single()["count"]
        print(f"   Nodes with label '{workspace}': {ws_count}")
        
        # 8. Check for common LightRAG property names
        if total > 0:
            print(f"\n🔍 Checking for common LightRAG properties:")
            for prop in ['entity_type', 'entity_name', 'description', 'source_id']:
                result = session.run(f"MATCH (n) WHERE n.{prop} IS NOT NULL RETURN count(n) AS count")
                count = result.single()["count"]
                if count > 0:
                    print(f"   • Nodes with '{prop}': {count}")
    
    driver.close()
    print("\n" + "=" * 60)

if __name__ == "__main__":
    inspect_neo4j()
