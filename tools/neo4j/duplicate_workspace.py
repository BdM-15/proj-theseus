"""
Duplicate Workspace Tool

Duplicates an existing Neo4j workspace and its rag_storage folder to create
a baseline snapshot that can be extended with additional documents without
reprocessing the original RFP.

CRITICAL SCENARIOS:
1. Pure Baseline Backup (single-label, baseline-only filter):
   - Source: afcapv_adab_iss_2025 (PURE baseline, no dual-labels)
   - Target: afcapv_adab_iss_2025_backup
   - Filter: baseline-only (excludes dual-labeled nodes)
   - Result: 1,321 entities (pure baseline snapshot)
   
2. Contaminated Baseline (single-label, no filter):
   - Source: afcapv_adab_iss_2025 (has dual-labels with pwsdocs)
   - Target: afcapv_adab_iss_2025_backup
   - Filter: none (copies ALL nodes with source label)
   - Result: 2,642 entities (baseline + extended workspace entities)
   
3. Baseline Extension (dual-label):
   - Source: afcapv_adab_iss_2025 (baseline)
   - Target: afcapv_adab_iss_2025_pwsdocs (extended workspace)
   - Mode: dual-label (adds target label to baseline nodes)
   - Result: Baseline entities visible in BOTH workspaces

Usage:
    python tools/duplicate_workspace.py

Features:
- Interactive prompts with validation
- Baseline purity detection (warns if source has dual-labels)
- Optional baseline-only filter (excludes dual-labeled nodes)
- Copies Neo4j nodes/relationships with new workspace label
- Duplicates rag_storage vector databases and metadata
- Dry-run mode with accurate preview counts
- Progress indicators and summary report
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Optional, Tuple
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Add src to path for imports (tools/neo4j/ -> project root)
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

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
    
    def analyze_workspace_purity(self, workspace: str) -> dict:
        """Analyze if workspace has dual-labeled nodes (contaminated baseline)
        
        Returns:
            dict with keys:
            - total_nodes: Total nodes with workspace label
            - pure_nodes: Nodes with ONLY workspace label + entity types
            - contaminated_nodes: Nodes with other workspace labels
            - other_workspaces: List of other workspace labels found
            - is_pure: Boolean if workspace is a pure baseline
        """
        query = f"""
        MATCH (n:`{workspace}`)
        WITH n, 
             [label IN labels(n) WHERE label <> '{workspace}' 
              AND label NOT IN ['concept', 'section', 'document', 'deliverable', 
                                'requirement', 'organization', 'location', 'equipment', 
                                'program', 'person', 'clause', 'evaluation_factor', 
                                'event', 'technology', 'table', 'other', 'UNKNOWN',
                                'statement_of_work', 'workload', 'strategic_theme',
                                'submission_instruction', 'entity', 'relationship']
             ] as workspace_labels
        RETURN 
            count(n) as total_nodes,
            sum(CASE WHEN size(workspace_labels) = 0 THEN 1 ELSE 0 END) as pure_nodes,
            sum(CASE WHEN size(workspace_labels) > 0 THEN 1 ELSE 0 END) as contaminated_nodes,
            collect(DISTINCT workspace_labels) as all_workspace_labels
        """
        
        with self.driver.session(database=self.neo4j_database) as session:
            result = session.run(query).single()
            
            # Flatten nested list of workspace labels
            other_workspaces = []
            for labels_list in result['all_workspace_labels']:
                other_workspaces.extend(labels_list)
            other_workspaces = list(set(other_workspaces))  # Deduplicate
            
            return {
                'total_nodes': result['total_nodes'],
                'pure_nodes': result['pure_nodes'],
                'contaminated_nodes': result['contaminated_nodes'],
                'other_workspaces': other_workspaces,
                'is_pure': result['contaminated_nodes'] == 0
            }
    
    def duplicate_neo4j_workspace(self, source: str, target: str, dry_run: bool = False, dual_label: bool = True, baseline_only: bool = False) -> Tuple[int, int]:
        """
        Duplicate Neo4j workspace by adding target label to source nodes.
        
        Args:
            source: Source workspace label
            target: Target workspace label to add
            dry_run: If True, only preview without making changes
            dual_label: If True, add target label to existing nodes (baseline inheritance)
                       If False, create separate nodes with only target label (full copy)
            baseline_only: If True, only copy nodes with ONLY source label (pure baseline)
                          If False, copy ALL nodes with source label (including dual-labeled)
        
        Returns:
            Tuple of (entities_copied, relationships_copied)
        """
        if dry_run:
            entities, rels = self.get_workspace_stats(source)
            mode_desc = "dual-label (add to baseline)" if dual_label else "single-label (full copy)"
            print(f"  [DRY RUN] Would copy {entities} entities and {rels} relationships ({mode_desc})")
            return entities, rels
        
        # Build WHERE clause for baseline-only filtering
        entity_types = ['concept', 'section', 'document', 'deliverable', 'requirement', 
                       'organization', 'location', 'equipment', 'program', 'person', 
                       'clause', 'evaluation_factor', 'event', 'technology', 'table', 
                       'other', 'UNKNOWN', 'statement_of_work', 'workload', 
                       'strategic_theme', 'submission_instruction', 'entity', 'relationship']
        entity_types_str = "', '".join(entity_types)
        
        if baseline_only:
            # Filter: Only nodes with source label + entity types (no other workspace labels)
            where_clause = f"""
            WHERE all(label IN labels(n) WHERE label = '{source}' OR label IN ['{entity_types_str}'])
            """
        else:
            where_clause = ""  # No filter, copy all nodes with source label
        
        if dual_label:
            # Dual-label mode: Add target label to source nodes (baseline inheritance)
            # This allows new documents in target workspace to reference baseline entities
            copy_nodes_query = f"""
            MATCH (n:`{source}`)
            {where_clause}
            SET n:`{target}`
            RETURN count(n) as count
            """
        else:
            # Single-label mode: Create separate copy with ALL labels preserved
            # CRITICAL: Must copy entity type labels (requirement, deliverable, etc.)
            copy_nodes_query = f"""
            MATCH (n:`{source}`)
            WITH n, properties(n) as props,
                 [label IN labels(n) WHERE label <> '{source}'] as entity_labels
            CREATE (n2:`{target}`)
            SET n2 = props
            WITH n2, entity_labels
            CALL apoc.create.addLabels(n2, entity_labels) YIELD node
            RETURN count(node) as count
            """
            
            # Fallback if APOC not available - WARNING: loses entity type labels!
            copy_nodes_fallback = f"""
            MATCH (n:`{source}`)
            CREATE (n2:`{target}`)
            SET n2 = properties(n)
            RETURN count(n2) as count
            """
        
        # Add baseline-only filter to relationship queries if needed
        if baseline_only:
            rel_where_clause = f"""
            WHERE all(label IN labels(a) WHERE label = '{source}' OR label IN ['{entity_types_str}'])
              AND all(label IN labels(b) WHERE label = '{source}' OR label IN ['{entity_types_str}'])
            """
        else:
            rel_where_clause = ""
        
        if dual_label:
            # Dual-label mode: Relationships already exist on the same nodes
            # Just need to count them for the target workspace view
            copy_rels_query = f"""
            MATCH (a:`{target}`)-[r]->(b:`{target}`)
            RETURN count(r) as count
            """
            copy_rels_fallback = copy_rels_query  # Same query, no APOC needed
        else:
            # Single-label mode: Need to duplicate relationships to new nodes
            copy_rels_query = f"""
            MATCH (a:`{source}`)-[r]->(b:`{source}`)
            {rel_where_clause}
            MATCH (a2:`{target}` {{entity_id: a.entity_id}})
            MATCH (b2:`{target}` {{entity_id: b.entity_id}})
            WITH a2, b2, r, type(r) as rel_type, properties(r) as props
            CALL apoc.create.relationship(a2, rel_type, props, b2) YIELD rel
            RETURN count(rel) as count
            """
            
            # Fallback if APOC not available
            copy_rels_fallback = f"""
            MATCH (a:`{source}`)-[r]->(b:`{source}`)
            {rel_where_clause}
            MATCH (a2:`{target}` {{entity_id: a.entity_id}})
            MATCH (b2:`{target}` {{entity_id: b.entity_id}})
            CREATE (a2)-[r2:INFERRED_RELATIONSHIP]->(b2)
            SET r2 = properties(r)
            RETURN count(r2) as count
            """
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Copy/label nodes
            action = "Adding target label to" if dual_label else "Copying entities from"
            print(f"  {action} '{source}' baseline...")
            
            if dual_label:
                result = session.run(copy_nodes_query)
                entities_copied = result.single()['count']
                print(f"    ✓ Added '{target}' label to {entities_copied} baseline entities")
            else:
                # Single-label mode: Try APOC-enhanced copy first
                try:
                    result = session.run(copy_nodes_query)
                    entities_copied = result.single()['count']
                    print(f"    ✓ Copied {entities_copied} entities (with entity type labels)")
                except Exception as e:
                    if 'apoc' in str(e).lower():
                        print(f"    ⚠️  APOC not available, using fallback (entity type labels will be lost!)")
                        result = session.run(copy_nodes_fallback)
                        entities_copied = result.single()['count']
                        print(f"    ✓ Copied {entities_copied} entities (workspace label only)")
                    else:
                        raise
            
            # Handle relationships
            if dual_label:
                print(f"  Counting existing relationships in target workspace view...")
                result = session.run(copy_rels_query)
                rels_copied = result.single()['count']
                print(f"    ✓ {rels_copied} relationships available in '{target}' workspace")
            else:
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
        
        # Step 4: Backup creation option (for dual-label safety)
        create_backup = False
        backup_workspace = f"{source_workspace}_backup"
        
        # Skip backup prompt if target IS the backup (single-label backup scenario)
        if target_workspace == backup_workspace:
            print(f"ℹ️  Target is the backup workspace, skipping redundant backup creation")
            print()
        elif not duplicator.workspace_exists(backup_workspace):
            print("💾 Backup Protection:")
            print(f"  Create safety backup '{backup_workspace}' before extending baseline?")
            print()
            print("  ⚠️  Answer 'n' if you ARE creating the backup (single-label copy)")
            print("  ⚠️  Answer 'y' only if extending baseline (dual-label mode)")
            print()
            print("  → Protects baseline from accidental deletion")
            print("  → Single-label copy (isolated, never modified)")
            print("  → Can restore baseline if working copy gets corrupted")
            print()
            backup_input = input("Create backup? (y/n): ").strip().lower()
            create_backup = backup_input == 'y'
            print()
        else:
            print(f"ℹ️  Backup '{backup_workspace}' already exists, skipping backup creation")
            print()
        
        # Step 5: Choose duplication mode (skip if creating backup - always single-label)
        if target_workspace.endswith('_backup'):
            dual_label = False
            print("ℹ️  Backup mode detected: Using single-label copy (isolated workspace)")
            print()
        else:
            print("🔀 Duplication Mode:")
            print("  [1] Dual-label (recommended): Add new workspace label to baseline entities")
            print("      → Baseline entities visible in BOTH workspaces")
            print("      → New documents can reference baseline entities")
            print("      → Use this to extend baseline with additional documents")
            print()
            print("  [2] Single-label (full copy): Create separate copy with new label only")
            print("      → Baseline and new workspace are completely independent")
            print("      → No cross-workspace connections possible")
            print("      → Use this for testing or complete isolation")
            print("      ⚠️  WARNING: Copies ALL nodes with source label (including dual-labeled)")
            print()
            
            while True:
                mode_input = input("Select mode (1 or 2): ").strip()
                if mode_input == '1':
                    dual_label = True
                    break
                elif mode_input == '2':
                    dual_label = False
                    break
                else:
                    print("  ❌ Invalid selection. Enter 1 or 2.")
            
            print()
        
        # Step 5b: Baseline purity check and filtering (single-label mode only)
        baseline_only = False
        if not dual_label:
            print("🔍 Analyzing source workspace purity...")
            purity = duplicator.analyze_workspace_purity(source_workspace)
            
            if not purity['is_pure']:
                print(f"  ⚠️  WARNING: Source workspace has DUAL-LABELED nodes!")
                print(f"     Total nodes:        {purity['total_nodes']}")
                print(f"     Pure baseline:      {purity['pure_nodes']} (only '{source_workspace}' label)")
                print(f"     Contaminated:       {purity['contaminated_nodes']} (has other workspace labels)")
                if purity['other_workspaces']:
                    print(f"     Other workspaces:   {', '.join(purity['other_workspaces'])}")
                print()
                print("  📋 SCENARIOS:")
                print("     [1] Copy ALL nodes (baseline + extended)")
                print(f"         → Will copy {purity['total_nodes']} entities (CONTAMINATED backup)")
                print("         → Includes nodes from other workspaces")
                print()
                print("     [2] Copy PURE BASELINE only (recommended)")
                print(f"         → Will copy {purity['pure_nodes']} entities (CLEAN backup)")
                print(f"         → Excludes dual-labeled nodes")
                print()
                
                while True:
                    filter_input = input("Select copy mode (1 or 2): ").strip()
                    if filter_input == '1':
                        baseline_only = False
                        break
                    elif filter_input == '2':
                        baseline_only = True
                        break
                    else:
                        print("  ❌ Invalid selection. Enter 1 or 2.")
                print()
            else:
                print(f"  ✅ Source workspace is PURE baseline ({purity['pure_nodes']} entities)")
                print(f"     No dual-labeled nodes detected")
                print()
        
        # Step 6: Dry run option
        dry_run_input = input("Run in dry-run mode (preview only)? (y/n): ").strip().lower()
        dry_run = dry_run_input == 'y'
        
        print()
        
        # Step 7: Confirmation
        entities, rels = duplicator.get_workspace_stats(source_workspace)
        mode_desc = "Dual-label (baseline inheritance)" if dual_label else "Single-label (full copy)"
        if baseline_only:
            mode_desc += " - BASELINE ONLY (excludes dual-labeled nodes)"
        print("📋 Duplication Summary:")
        print(f"  Source:      {source_workspace} ({entities} entities, {rels} relationships)")
        if create_backup:
            print(f"  Backup:      {backup_workspace} (safety copy, single-label)")
        print(f"  Target:      {target_workspace}")
        print(f"  Mode:        {mode_desc}")
        if baseline_only:
            purity = duplicator.analyze_workspace_purity(source_workspace)
            print(f"  Filter:      Pure baseline only ({purity['pure_nodes']} of {purity['total_nodes']} entities)")
        print(f"  Execution:   {'DRY RUN (preview only)' if dry_run else 'LIVE (will modify data)'}")
        print()
        
        if not dry_run:
            confirm = input("Proceed with duplication? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Duplication cancelled")
                return
        
        print()
        print("=" * 80)
        print("STARTING DUPLICATION...")
        print("=" * 80)
        print()
        
        # Step 8: Create backup first (if requested)
        backup_size_mb = 0
        if create_backup:
            print("🔄 Step 1: Creating safety backup...")
            print(f"  Source: {source_workspace}")
            print(f"  Backup: {backup_workspace}")
            print()
            
            # Create backup with single-label mode
            backup_entities, backup_rels = duplicator.duplicate_neo4j_workspace(
                source_workspace,
                backup_workspace,
                dry_run,
                dual_label=False,  # Always single-label for backups
                baseline_only=baseline_only  # Use same filter as target
            )
            print()
            
            # Copy backup rag_storage
            try:
                backup_size_mb = duplicator.duplicate_rag_storage(
                    source_workspace,
                    backup_workspace,
                    dry_run
                )
            except FileNotFoundError as e:
                print(f"  ⚠️  {e}")
                print(f"  ⚠️  Skipping backup rag_storage duplication")
                backup_size_mb = 0
            print()
            print(f"  ✅ Backup created: {backup_entities} entities, {backup_rels} relationships, {backup_size_mb} MB")
            print()
        
        # Step 9: Duplicate Neo4j workspace (working copy)
        step_num = "2" if create_backup else "1"
        print(f"🔄 Step {step_num}/2: Duplicating Neo4j workspace...")
        entities_copied, rels_copied = duplicator.duplicate_neo4j_workspace(
            source_workspace, 
            target_workspace,
            dry_run,
            dual_label,
            baseline_only
        )
        print()
        
        # Step 10: Duplicate rag_storage
        print(f"🔄 Step {step_num}/2: Duplicating rag_storage folder...")
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
        
        # Step 11: Update .env option
        if not dry_run:
            update_env = input("Update .env to point to new workspace? (y/n): ").strip().lower()
            if update_env == 'y':
                duplicator.update_env_file(target_workspace, dry_run)
                print()
        
        # Step 12: Summary
        print("=" * 80)
        if dry_run:
            print("DRY RUN COMPLETE")
        else:
            print("✅ DUPLICATION COMPLETE")
        print("=" * 80)
        print()
        print(f"Source workspace:  {source_workspace}")
        if create_backup:
            print(f"Backup workspace:  {backup_workspace} (isolated, never modified)")
        print(f"Target workspace:  {target_workspace}")
        print(f"Mode:              {mode_desc}")
        print(f"Entities:          {entities_copied}")
        print(f"Relationships:     {rels_copied}")
        print(f"Storage copied:    {size_mb} MB")
        print()
        
        if not dry_run:
            print("Next steps:")
            print(f"1. Ensure .env has: NEO4J_WORKSPACE={target_workspace}")
            print(f"2. Restart application server")
            print(f"3. Upload additional documents via WebUI")
            if dual_label:
                print(f"4. New documents will be able to reference baseline entities")
                print(f"5. Baseline entities are visible in both '{source_workspace}' and '{target_workspace}' workspaces")
                if create_backup:
                    print()
                    print(f"💾 Safety Net:")
                    print(f"   - If baseline gets corrupted, restore from '{backup_workspace}'")
                    print(f"   - Backup is isolated (single-label only, never modified)")
            else:
                print(f"4. New documents will only link to entities within '{target_workspace}'")
                print(f"5. '{source_workspace}' and '{target_workspace}' are completely independent")
        
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
