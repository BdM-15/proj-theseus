"""
Duplicate Workspace Tool

Duplicates an existing Neo4j workspace and its rag_storage folder to create
a baseline snapshot that can be extended with additional documents without
reprocessing the original RFP.

Usage:
    python tools/duplicate_workspace.py

Features:
- Interactive prompts with validation
- Copies Neo4j nodes/relationships with new workspace label
- Duplicates rag_storage vector databases and metadata
- Option to update .env file
- Dry-run mode
- Progress indicators and summary report
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Tuple
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()


class WorkspaceDuplicator:
    """Handles duplication of Neo4j workspace and rag_storage"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.neo4j_username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.rag_storage_dir = Path("rag_storage")
        
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD not set in .env file")
        
        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password)
        )
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def get_available_workspaces(self) -> list:
        """Get list of existing workspace labels in Neo4j"""
        query = """
        CALL db.labels()
        YIELD label
        WHERE label <> 'entity' AND label <> 'relationship'
        RETURN label
        ORDER BY label
        """
        
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query)
            return [record['label'] for record in result]
    
    def workspace_exists(self, workspace: str) -> bool:
        """Check if workspace exists in Neo4j"""
        query = f"""
        MATCH (n:`{workspace}`)
        RETURN count(n) as count
        LIMIT 1
        """
        
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query)
            record = result.single()
            return record['count'] > 0 if record else False
    
    def get_workspace_stats(self, workspace: str) -> Tuple[int, int]:
        """Get entity and relationship counts for workspace"""
        entity_query = f"""
        MATCH (n:`{workspace}`)
        RETURN count(n) as count
        """
        
        rel_query = f"""
        MATCH (a:`{workspace}`)-[r]->(b:`{workspace}`)
        RETURN count(r) as count
        """
        
        with self.driver.session(database=self.neo4j_database) as session:
            entities = session.run(entity_query).single()['count']
            relationships = session.run(rel_query).single()['count']
            return entities, relationships
    
    def duplicate_neo4j_workspace(self, source: str, target: str, dry_run: bool = False) -> Tuple[int, int]:
        """
        Duplicate Neo4j workspace by copying all nodes and relationships.
        
        Returns:
            Tuple of (entities_copied, relationships_copied)
        """
        if dry_run:
            entities, rels = self.get_workspace_stats(source)
            print(f"  [DRY RUN] Would copy {entities} entities and {rels} relationships")
            return entities, rels
        
        # Copy nodes
        copy_nodes_query = f"""
        MATCH (n:`{source}`)
        CREATE (n2:`{target}`)
        SET n2 = properties(n)
        RETURN count(n2) as count
        """
        
        # Copy relationships
        copy_rels_query = f"""
        MATCH (a:`{source}`)-[r]->(b:`{source}`)
        MATCH (a2:`{target}` {{entity_id: a.entity_id}})
        MATCH (b2:`{target}` {{entity_id: b.entity_id}})
        WITH a2, b2, r, type(r) as rel_type, properties(r) as props
        CALL apoc.create.relationship(a2, rel_type, props, b2) YIELD rel
        RETURN count(rel) as count
        """
        
        # Fallback if APOC not available
        copy_rels_fallback = f"""
        MATCH (a:`{source}`)-[r]->(b:`{source}`)
        MATCH (a2:`{target}` {{entity_id: a.entity_id}})
        MATCH (b2:`{target}` {{entity_id: b.entity_id}})
        CREATE (a2)-[r2:INFERRED_RELATIONSHIP]->(b2)
        SET r2 = properties(r)
        RETURN count(r2) as count
        """
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Copy nodes
            print(f"  Copying entities from '{source}' to '{target}'...")
            result = session.run(copy_nodes_query)
            entities_copied = result.single()['count']
            print(f"    ✓ Copied {entities_copied} entities")
            
            # Copy relationships (try APOC first, fallback if not available)
            print(f"  Copying relationships...")
            try:
                result = session.run(copy_rels_query)
                rels_copied = result.single()['count']
            except Exception as e:
                if 'apoc' in str(e).lower():
                    print(f"    ⚠️  APOC not available, using fallback method")
                    result = session.run(copy_rels_fallback)
                    rels_copied = result.single()['count']
                else:
                    raise
            
            print(f"    ✓ Copied {rels_copied} relationships")
            
            return entities_copied, rels_copied
    
    def duplicate_rag_storage(self, source: str, target: str, dry_run: bool = False) -> int:
        """
        Duplicate rag_storage folder.
        
        Returns:
            Size in MB of copied data
        """
        source_path = self.rag_storage_dir / source
        target_path = self.rag_storage_dir / target
        
        if not source_path.exists():
            raise FileNotFoundError(f"Source rag_storage folder not found: {source_path}")
        
        if target_path.exists():
            raise FileExistsError(f"Target rag_storage folder already exists: {target_path}")
        
        # Calculate size
        total_size = sum(f.stat().st_size for f in source_path.rglob('*') if f.is_file())
        size_mb = total_size / (1024 * 1024)
        
        if dry_run:
            print(f"  [DRY RUN] Would copy {size_mb:.2f} MB from {source_path} to {target_path}")
            return int(size_mb)
        
        print(f"  Copying rag_storage folder ({size_mb:.2f} MB)...")
        shutil.copytree(source_path, target_path)
        print(f"    ✓ Copied {source_path} → {target_path}")
        
        return int(size_mb)
    
    def update_env_file(self, new_workspace: str, dry_run: bool = False):
        """Update .env file to point to new workspace"""
        env_path = Path(".env")
        
        if not env_path.exists():
            print(f"  ⚠️  .env file not found, skipping update")
            return
        
        if dry_run:
            print(f"  [DRY RUN] Would update .env: NEO4J_WORKSPACE={new_workspace}")
            return
        
        # Read current .env
        with open(env_path, 'r') as f:
            lines = f.readlines()
        
        # Update or add NEO4J_WORKSPACE
        workspace_found = False
        for i, line in enumerate(lines):
            if line.startswith('NEO4J_WORKSPACE='):
                lines[i] = f'NEO4J_WORKSPACE={new_workspace}\n'
                workspace_found = True
                break
        
        if not workspace_found:
            lines.append(f'\nNEO4J_WORKSPACE={new_workspace}\n')
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)
        
        print(f"  ✓ Updated .env: NEO4J_WORKSPACE={new_workspace}")


def main():
    """Interactive workspace duplication"""
    print("=" * 80)
    print("WORKSPACE DUPLICATION TOOL")
    print("=" * 80)
    print()
    print("Duplicates an existing Neo4j workspace + rag_storage to create a baseline")
    print("that can be extended with additional documents without reprocessing.")
    print()
    
    duplicator = WorkspaceDuplicator()
    
    try:
        # Step 1: Show available workspaces
        print("📊 Available workspaces in Neo4j:")
        workspaces = duplicator.get_available_workspaces()
        
        if not workspaces:
            print("  ⚠️  No workspaces found in Neo4j")
            return
        
        for ws in workspaces:
            entities, rels = duplicator.get_workspace_stats(ws)
            rag_path = Path(f"rag_storage/{ws}")
            rag_status = "✓" if rag_path.exists() else "✗"
            print(f"  [{rag_status}] {ws}: {entities} entities, {rels} relationships")
        
        print()
        
        # Step 2: Get source workspace
        while True:
            source_workspace = input("Enter source workspace name: ").strip()
            
            if not source_workspace:
                print("  ❌ Workspace name cannot be empty")
                continue
            
            if not duplicator.workspace_exists(source_workspace):
                print(f"  ❌ Workspace '{source_workspace}' not found in Neo4j")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return
                continue
            
            source_rag_path = Path(f"rag_storage/{source_workspace}")
            if not source_rag_path.exists():
                print(f"  ⚠️  Warning: rag_storage folder not found at {source_rag_path}")
                proceed = input("Continue anyway? (y/n): ").strip().lower()
                if proceed != 'y':
                    continue
            
            break
        
        print()
        
        # Step 3: Get target workspace
        while True:
            target_workspace = input("Enter new workspace name: ").strip()
            
            if not target_workspace:
                print("  ❌ Workspace name cannot be empty")
                continue
            
            if target_workspace == source_workspace:
                print("  ❌ Target workspace must be different from source")
                continue
            
            if duplicator.workspace_exists(target_workspace):
                print(f"  ❌ Workspace '{target_workspace}' already exists in Neo4j")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return
                continue
            
            target_rag_path = Path(f"rag_storage/{target_workspace}")
            if target_rag_path.exists():
                print(f"  ❌ rag_storage folder already exists at {target_rag_path}")
                retry = input("Try again? (y/n): ").strip().lower()
                if retry != 'y':
                    return
                continue
            
            break
        
        print()
        
        # Step 4: Dry run option
        dry_run_input = input("Run in dry-run mode (preview only)? (y/n): ").strip().lower()
        dry_run = dry_run_input == 'y'
        
        print()
        
        # Step 5: Confirmation
        entities, rels = duplicator.get_workspace_stats(source_workspace)
        print("📋 Duplication Summary:")
        print(f"  Source:      {source_workspace} ({entities} entities, {rels} relationships)")
        print(f"  Target:      {target_workspace}")
        print(f"  Mode:        {'DRY RUN (preview only)' if dry_run else 'LIVE (will copy data)'}")
        print()
        
        if not dry_run:
            confirm = input("Proceed with duplication? (yes/no): ").strip().lower()
            if confirm != 'yes':
                print("❌ Duplication cancelled")
                return
        
        print()
        print("=" * 80)
        print("STARTING DUPLICATION...")
        print("=" * 80)
        print()
        
        # Step 6: Duplicate Neo4j workspace
        print("🔄 Step 1/2: Duplicating Neo4j workspace...")
        entities_copied, rels_copied = duplicator.duplicate_neo4j_workspace(
            source_workspace, 
            target_workspace,
            dry_run
        )
        print()
        
        # Step 7: Duplicate rag_storage
        print("🔄 Step 2/2: Duplicating rag_storage folder...")
        try:
            size_mb = duplicator.duplicate_rag_storage(
                source_workspace,
                target_workspace,
                dry_run
            )
        except FileNotFoundError as e:
            print(f"  ⚠️  {e}")
            print(f"  ⚠️  Skipping rag_storage duplication (Neo4j workspace still copied)")
            size_mb = 0
        print()
        
        # Step 8: Update .env option
        if not dry_run:
            update_env = input("Update .env to point to new workspace? (y/n): ").strip().lower()
            if update_env == 'y':
                duplicator.update_env_file(target_workspace, dry_run)
                print()
        
        # Step 9: Summary
        print("=" * 80)
        if dry_run:
            print("DRY RUN COMPLETE")
        else:
            print("✅ DUPLICATION COMPLETE")
        print("=" * 80)
        print()
        print(f"Source workspace:  {source_workspace}")
        print(f"Target workspace:  {target_workspace}")
        print(f"Entities copied:   {entities_copied}")
        print(f"Relationships:     {rels_copied}")
        print(f"Storage copied:    {size_mb} MB")
        print()
        
        if not dry_run:
            print("Next steps:")
            print(f"1. Ensure .env has: NEO4J_WORKSPACE={target_workspace}")
            print(f"2. Restart application server")
            print(f"3. Upload additional documents via WebUI")
            print(f"4. New entities/relationships will be added to the duplicated baseline")
        
    except KeyboardInterrupt:
        print("\n\n❌ Duplication cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        duplicator.close()


if __name__ == "__main__":
    main()
