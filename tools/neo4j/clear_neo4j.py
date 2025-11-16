"""
Clear Neo4j Database for Testing
=================================

Quick script to delete all data from Neo4j workspace for fresh testing.

Usage:
    python clear_neo4j.py                    # Clear current workspace only
    python clear_neo4j.py --all              # Clear ALL data from Neo4j
    python clear_neo4j.py --workspace NAME   # Clear specific workspace
"""

import os
import sys

# Add project root to path so we can import src module (tools/neo4j/ -> project root)
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv()

from src.inference.neo4j_graph_io import Neo4jGraphIO


def clear_workspace(workspace_name: str = None):
    """Clear a specific workspace"""
    neo4j_io = Neo4jGraphIO()
    
    if workspace_name is None:
        workspace_name = neo4j_io.workspace
    
    print(f"\n🗑️  Clearing Neo4j workspace: {workspace_name}")
    
    # Count before deletion
    count_query = f"""
    MATCH (n:`{workspace_name}`)
    RETURN count(n) as node_count
    """
    
    with neo4j_io.driver.session(database=neo4j_io.database) as session:
        result = session.run(count_query)
        record = result.single()
        node_count = record['node_count'] if record else 0
        
        if node_count == 0:
            print(f"   ℹ️  Workspace '{workspace_name}' is already empty")
            neo4j_io.close()
            return
        
        print(f"   Found {node_count} nodes to delete...")
        
        # Confirm deletion
        confirm = input(f"   Delete {node_count} nodes from '{workspace_name}'? (yes/no): ")
        if confirm.lower() not in ['yes', 'y']:
            print("   ❌ Cancelled")
            neo4j_io.close()
            return
        
        # Delete all nodes with this label
        delete_query = f"""
        MATCH (n:`{workspace_name}`)
        DETACH DELETE n
        """
        
        session.run(delete_query)
        print(f"   ✅ Deleted {node_count} nodes from workspace '{workspace_name}'")
    
    neo4j_io.close()


def clear_all():
    """Clear ALL data from Neo4j (dangerous!)"""
    neo4j_io = Neo4jGraphIO()
    
    print(f"\n⚠️  WARNING: This will delete ALL data from Neo4j!")
    
    # Count all nodes
    count_query = "MATCH (n) RETURN count(n) as node_count"
    
    with neo4j_io.driver.session(database=neo4j_io.database) as session:
        result = session.run(count_query)
        record = result.single()
        node_count = record['node_count'] if record else 0
        
        if node_count == 0:
            print("   ℹ️  Database is already empty")
            neo4j_io.close()
            return
        
        print(f"   Found {node_count} total nodes...")
        
        # Double confirm for safety
        confirm = input(f"   Delete ALL {node_count} nodes? Type 'DELETE ALL' to confirm: ")
        if confirm != 'DELETE ALL':
            print("   ❌ Cancelled")
            neo4j_io.close()
            return
        
        # Delete everything
        delete_query = "MATCH (n) DETACH DELETE n"
        session.run(delete_query)
        print(f"   ✅ Deleted all {node_count} nodes from database")
    
    neo4j_io.close()


def list_workspaces():
    """List all workspace labels in Neo4j"""
    neo4j_io = Neo4jGraphIO()
    
    print("\n📊 Workspaces in Neo4j:")
    
    # Get all labels that look like workspace labels (not system labels)
    query = """
    CALL db.labels() YIELD label
    WHERE NOT label IN ['__Entity__', '__Relation__', '__Community__']
    RETURN label, size([(n:`label`) | n]) as count
    """
    
    with neo4j_io.driver.session(database=neo4j_io.database) as session:
        # We need to build query dynamically for each label
        result = session.run("CALL db.labels() YIELD label RETURN collect(label) as labels")
        record = result.single()
        labels = record['labels'] if record else []
        
        workspaces = []
        for label in labels:
            if label not in ['__Entity__', '__Relation__', '__Community__']:
                count_query = f"MATCH (n:`{label}`) RETURN count(n) as count"
                count_result = session.run(count_query)
                count_record = count_result.single()
                count = count_record['count'] if count_record else 0
                if count > 0:
                    workspaces.append((label, count))
        
        if not workspaces:
            print("   (no workspaces found)")
        else:
            for label, count in sorted(workspaces, key=lambda x: x[1], reverse=True):
                current = " (current)" if label == neo4j_io.workspace else ""
                print(f"   - {label}: {count} nodes{current}")
    
    neo4j_io.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Clear Neo4j data for testing')
    parser.add_argument('--all', action='store_true', help='Delete ALL data (dangerous!)')
    parser.add_argument('--workspace', type=str, help='Workspace name to clear')
    parser.add_argument('--list', action='store_true', help='List all workspaces')
    
    args = parser.parse_args()
    
    try:
        if args.list:
            list_workspaces()
        elif args.all:
            clear_all()
        elif args.workspace:
            clear_workspace(args.workspace)
        else:
            # Default: clear current workspace
            clear_workspace()
        
        print("\n✅ Done!\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
