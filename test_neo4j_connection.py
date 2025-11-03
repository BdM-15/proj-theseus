"""
Neo4j Connection Test for GovCon Capture Vibe
Tests Neo4j 5.25 connectivity and queries existing data

Prerequisites:
    1. Ensure Docker Desktop is running
    2. Neo4j container is started (either via 'python app.py' or manually)
    3. Server has already processed an RFP (data exists in ./rag_storage/default)

Usage:
    python test_neo4j_connection.py

Note: This test queries the Neo4j database directly using Cypher queries.
"""

import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()


def test_neo4j_connection():
    """Test Neo4j connection and query existing data."""
    
    neo4j_uri = os.getenv('NEO4J_URI', 'neo4j://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    workspace = os.getenv('NEO4J_WORKSPACE', 'navy_mbos_baseline')
    
    print("🔌 Testing Neo4j connection...")
    print(f"   URI: {neo4j_uri}")
    print(f"   Username: {neo4j_user}")
    print(f"   Workspace: {workspace}")
    
    if not neo4j_password:
        print("❌ Error: NEO4J_PASSWORD not set in .env")
        return False
    
    try:
        # Create Neo4j driver
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        with driver.session() as session:
            # Test 1: Verify connection
            result = session.run("RETURN 1 AS test")
            test_value = result.single()["test"]
            print(f"✅ Neo4j connection successful (test query returned: {test_value})")
            
            # Test 2: Check if APOC is available
            try:
                result = session.run("RETURN apoc.version() AS version")
                apoc_version = result.single()["version"]
                print(f"✅ APOC plugin available (version: {apoc_version})")
            except Exception:
                print("⚠️  APOC plugin not available (optional)")
            
            # Test 3: Count all nodes
            result = session.run("MATCH (n) RETURN count(n) AS total")
            total_nodes = result.single()["total"]
            print(f"📊 Total nodes in database: {total_nodes}")
            
            # Test 4: Count nodes in our workspace
            result = session.run(
                f"MATCH (n:`{workspace}`) RETURN count(n) AS total"
            )
            workspace_nodes = result.single()["total"]
            print(f"📊 Nodes in workspace '{workspace}': {workspace_nodes}")
            
            if workspace_nodes > 0:
                # Test 5: Sample some entities
                print(f"\n🔍 Sample entities from workspace '{workspace}':")
                result = session.run(
                    f"""
                    MATCH (n:`{workspace}`)
                    RETURN n.entity_type AS type, n.description AS description
                    LIMIT 5
                    """
                )
                for record in result:
                    entity_type = record.get("type", "unknown")
                    description = record.get("description", "no description")[:80]
                    print(f"   • {entity_type}: {description}...")
                
                # Test 6: Count by entity type
                print(f"\n📊 Entity breakdown by type:")
                result = session.run(
                    f"""
                    MATCH (n:`{workspace}`)
                    WHERE n.entity_type IS NOT NULL
                    RETURN n.entity_type AS type, count(n) AS count
                    ORDER BY count DESC
                    LIMIT 10
                    """
                )
                for record in result:
                    print(f"   • {record['type']}: {record['count']}")
            else:
                print(f"\n⚠️  No data found in workspace '{workspace}'")
                print("   This is expected if you haven't migrated data to Neo4j yet.")
                print("   The existing data is in ./rag_storage/default (NetworkX storage)")
        
        driver.close()
        
        print("\n" + "="*60)
        print("🎉 Neo4j is connected and accessible!")
        print("="*60)
        
        print("\n📋 Next steps:")
        print("1. Login to Neo4j Browser: http://localhost:7474")
        print(f"   Credentials: {neo4j_user} / {neo4j_password}")
        print("\n2. To query your workspace:")
        print(f"   MATCH (n:`{workspace}`) RETURN n LIMIT 25")
        print("\n3. To migrate existing data from ./rag_storage/default:")
        print("   You'll need to reprocess the RFP with GRAPH_STORAGE=Neo4JStorage")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Verify Neo4j is running:")
        print("   docker ps")
        print("\n2. Check Neo4j logs:")
        print("   docker logs govcon-neo4j")
        print("\n3. Verify .env configuration:")
        print(f"   NEO4J_URI={neo4j_uri}")
        print(f"   NEO4J_USERNAME={neo4j_user}")
        print(f"   NEO4J_PASSWORD={'***' if neo4j_password else 'NOT SET'}")
        print(f"   NEO4J_WORKSPACE={workspace}")
        print("\n4. Try manual connection in Neo4j Browser:")
        print("   http://localhost:7474")
        return False


if __name__ == "__main__":
    success = test_neo4j_connection()
    exit(0 if success else 1)
