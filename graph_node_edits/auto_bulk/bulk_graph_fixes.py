"""
Pattern-Based Bulk Graph Editing Tool

This is the PRIMARY method for fixing common graph issues:
- Isolated nodes (low edge count)
- Missing hierarchical relationships
- Untyped or generic relationships
- Scattered clauses/annexes
- Entity type corruption (Branch 005 - #>|TYPE, #|TYPE, lowercase)

For one-off or controversial edits, use interactive_graph_edit.ps1 instead.

Usage:
    python bulk_graph_fixes.py --pattern isolated_nodes --dry-run
    python bulk_graph_fixes.py --pattern missing_hierarchy --apply
    python bulk_graph_fixes.py --pattern corruption --dry-run
    python bulk_graph_fixes.py --pattern all --dry-run

WARNING: 'corruption' pattern modifies entity_type directly. Test on dedicated branch first!
"""

import asyncio
import argparse
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Tuple
from pathlib import Path
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from lightrag import LightRAG


class BulkGraphFixer:
    """
    Pattern-based bulk editing for common graph issues.
    """
    
    def __init__(self, working_dir: str = "./rag_storage"):
        self.working_dir = Path(working_dir)
        self.rag = None
        self.graphml_path = self.working_dir / "graph_chunk_entity_relation.graphml"
        self.dry_run = True
        
    async def initialize(self):
        """Initialize LightRAG connection."""
        self.rag = LightRAG(working_dir=str(self.working_dir))
        print(f"✅ Connected to graph: {self.working_dir}")
        print()
    
    def load_graph_structure(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Load graph structure from GraphML.
        
        Returns:
            (nodes, edges) - Lists of node and edge dictionaries
        """
        if not self.graphml_path.exists():
            raise FileNotFoundError(f"GraphML not found: {self.graphml_path}")
        
        tree = ET.parse(str(self.graphml_path))
        root = tree.getroot()
        ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}
        
        # Parse nodes
        nodes = []
        for node_elem in root.findall('.//g:node', ns):
            node_id = node_elem.get('id')
            node_data = {'id': node_id}
            
            for data_elem in node_elem.findall('g:data', ns):
                key = data_elem.get('key')
                value = data_elem.text
                
                # Map keys (d0=name, d1=type, d2=description, etc.)
                if key == 'd0':
                    node_data['entity_name'] = value
                elif key == 'd1':
                    node_data['entity_type'] = value
                elif key == 'd2':
                    node_data['description'] = value
            
            nodes.append(node_data)
        
        # Parse edges
        edges = []
        for edge_elem in root.findall('.//g:edge', ns):
            edge_data = {
                'id': edge_elem.get('id'),
                'source': edge_elem.get('source'),
                'target': edge_elem.get('target')
            }
            
            for data_elem in edge_elem.findall('g:data', ns):
                key = data_elem.get('key')
                value = data_elem.text
                
                if key == 'd5':  # relationship_type
                    edge_data['relationship_type'] = value
            
            edges.append(edge_data)
        
        print(f"📊 Loaded graph: {len(nodes)} nodes, {len(edges)} edges")
        print()
        
        return nodes, edges
    
    def find_isolated_nodes(self, nodes: List[Dict], edges: List[Dict], 
                           threshold: int = 3) -> List[Dict]:
        """
        Find nodes with fewer than threshold edges.
        
        Args:
            nodes: List of node dicts
            edges: List of edge dicts
            threshold: Minimum edge count (default: 3)
        
        Returns:
            List of isolated nodes
        """
        # Count edges per node
        edge_count = {}
        for edge in edges:
            src = edge['source']
            tgt = edge['target']
            edge_count[src] = edge_count.get(src, 0) + 1
            edge_count[tgt] = edge_count.get(tgt, 0) + 1
        
        # Find isolated nodes
        isolated = []
        for node in nodes:
            node_id = node['id']
            count = edge_count.get(node_id, 0)
            
            if count < threshold:
                node['edge_count'] = count
                isolated.append(node)
        
        return isolated
    
    def find_missing_hierarchical_relationships(self, nodes: List[Dict], 
                                               edges: List[Dict]) -> List[Dict]:
        """
        Find entities that should have hierarchical relationships but don't.
        
        Patterns:
        - ANNEX with prefix (J-######) missing link to Section J
        - CLAUSE missing link to parent section
        - REQUIREMENT missing link to STATEMENT_OF_WORK
        """
        missing = []
        
        # Build edge lookup
        edge_lookup = {}
        for edge in edges:
            src = edge['source']
            tgt = edge['target']
            if src not in edge_lookup:
                edge_lookup[src] = []
            if tgt not in edge_lookup:
                edge_lookup[tgt] = []
            edge_lookup[src].append({'target': tgt, 'type': edge.get('relationship_type')})
            edge_lookup[tgt].append({'target': src, 'type': edge.get('relationship_type')})
        
        # Build node name to type mapping
        node_map = {n['entity_name']: n for n in nodes}
        
        # Pattern 1: ANNEX with prefix missing parent section
        for node in nodes:
            if node.get('entity_type') == 'annex':
                name = node.get('entity_name', '')
                
                # Extract prefix (e.g., "J-" from "J-1234567")
                if '-' in name:
                    prefix = name.split('-')[0]
                    parent_name = f"Section {prefix}"
                    
                    # Check if parent exists and is connected
                    if parent_name in node_map:
                        connected = edge_lookup.get(node['id'], [])
                        parent_connected = any(
                            edge_lookup.get(c['target'], [])
                            for c in connected
                            if node_map.get(c['target'], {}).get('entity_name') == parent_name
                        )
                        
                        if not parent_connected:
                            missing.append({
                                'source': node['entity_name'],
                                'target': parent_name,
                                'relationship_type': 'CHILD_OF',
                                'reason': f'Annex {name} has prefix "{prefix}-" matching Section {prefix}',
                                'confidence': 0.95
                            })
        
        # Pattern 2: CLAUSE missing parent section link
        for node in nodes:
            if node.get('entity_type') == 'clause':
                name = node.get('entity_name', '')
                
                # Most clauses belong to Section I or Section K
                # Check description for hints
                desc = node.get('description', '').lower()
                
                parent_candidates = []
                if 'section i' in desc or 'contract clause' in desc:
                    parent_candidates.append('Section I')
                elif 'section k' in desc or 'representation' in desc:
                    parent_candidates.append('Section K')
                
                for parent_name in parent_candidates:
                    if parent_name in node_map:
                        connected = edge_lookup.get(node['id'], [])
                        parent_connected = any(
                            node_map.get(c['target'], {}).get('entity_name') == parent_name
                            for c in connected
                        )
                        
                        if not parent_connected:
                            missing.append({
                                'source': node['entity_name'],
                                'target': parent_name,
                                'relationship_type': 'CHILD_OF',
                                'reason': f'Clause references {parent_name} in description',
                                'confidence': 0.75
                            })
        
        return missing
    
    def find_untyped_relationships(self, edges: List[Dict]) -> List[Dict]:
        """
        Find edges with no relationship_type or generic types.
        """
        untyped = []
        
        for edge in edges:
            rel_type = edge.get('relationship_type')
            
            if not rel_type or rel_type in ['None', 'RELATED_TO', '']:
                untyped.append(edge)
        
        return untyped
    
    async def fix_isolated_nodes(self, isolated: List[Dict], apply: bool = False):
        """
        Fix isolated nodes by adding contextual relationships.
        
        Strategy:
        - Connect to likely parent sections based on description
        - Connect to program-level entities (MCPP II, Navy MBOS)
        - Connect similar entities together
        """
        print("=" * 80)
        print("FIX PATTERN: Isolated Nodes")
        print("=" * 80)
        print()
        
        if not isolated:
            print("✅ No isolated nodes found!")
            return
        
        print(f"Found {len(isolated)} isolated nodes (edge count < 3):")
        print()
        
        fixes = []
        
        for node in isolated:
            name = node['entity_name']
            node_type = node.get('entity_type', 'unknown')
            count = node.get('edge_count', 0)
            desc = node.get('description', '')[:100]
            
            print(f"  • {name} ({node_type})")
            print(f"    Edges: {count}")
            print(f"    Description: {desc}...")
            print()
            
            # Determine target based on type and description
            target = None
            rel_type = None
            reason = ""
            
            if node_type == 'technology':
                # Technology nodes should link to program or SOW
                if 'MCPP' in desc.upper() or 'MARINE CORPS' in desc.upper():
                    target = "MCPP II Program"
                    rel_type = "CHILD_OF"
                    reason = "Technology mentioned in MCPP II context"
                elif 'NAVY' in desc.upper():
                    target = "Navy Organic Ground Support Equipment Maintenance"
                    rel_type = "MAINTAINED_BY"
                    reason = "Technology maintained under Navy GSE program"
            
            elif node_type == 'requirement':
                # Requirements should link to SOW
                target = "MCPP II SOW"
                rel_type = "COMPONENT_OF"
                reason = "Requirement specified in Statement of Work"
            
            elif node_type == 'deliverable':
                # Deliverables should link to SOW
                target = "MCPP II SOW"
                rel_type = "COMPONENT_OF"
                reason = "Deliverable specified in Statement of Work"
            
            if target:
                fixes.append({
                    'source': name,
                    'target': target,
                    'relationship_type': rel_type,
                    'reason': reason,
                    'weight': 0.85
                })
                print(f"    → FIX: Add {rel_type} relationship to {target}")
                print(f"       Reason: {reason}")
                print()
        
        if not fixes:
            print("⚠️  No automatic fixes available for these isolated nodes.")
            print("   Consider using interactive_graph_edit.ps1 for manual review.")
            return
        
        print("=" * 80)
        print(f"SUMMARY: {len(fixes)} fixes identified")
        print("=" * 80)
        print()
        
        if apply and not self.dry_run:
            print("Applying fixes...")
            for fix in fixes:
                await self.rag.acreate_relation(
                    source_entity=fix['source'],
                    target_entity=fix['target'],
                    relation_data={
                        'description': fix['reason'],
                        'relationship_type': fix['relationship_type'],
                        'weight': fix['weight']
                    }
                )
                print(f"  ✅ {fix['source']} → {fix['target']} ({fix['relationship_type']})")
            print()
            print("✅ All fixes applied!")
        else:
            print("DRY RUN - No changes applied")
            print("Run with --apply to execute fixes")
        
        print()
    
    async def fix_missing_hierarchical_relationships(self, missing: List[Dict], 
                                                    apply: bool = False):
        """
        Fix missing hierarchical relationships.
        """
        print("=" * 80)
        print("FIX PATTERN: Missing Hierarchical Relationships")
        print("=" * 80)
        print()
        
        if not missing:
            print("✅ No missing hierarchical relationships found!")
            return
        
        print(f"Found {len(missing)} missing hierarchical relationships:")
        print()
        
        for rel in missing:
            print(f"  • {rel['source']} → {rel['target']}")
            print(f"    Type: {rel['relationship_type']}")
            print(f"    Reason: {rel['reason']}")
            print(f"    Confidence: {rel['confidence']:.2f}")
            print()
        
        print("=" * 80)
        print(f"SUMMARY: {len(missing)} fixes identified")
        print("=" * 80)
        print()
        
        if apply and not self.dry_run:
            print("Applying fixes...")
            for rel in missing:
                await self.rag.acreate_relation(
                    source_entity=rel['source'],
                    target_entity=rel['target'],
                    relation_data={
                        'description': rel['reason'],
                        'relationship_type': rel['relationship_type'],
                        'weight': rel['confidence']
                    }
                )
                print(f"  ✅ {rel['source']} → {rel['target']} ({rel['relationship_type']})")
            print()
            print("✅ All fixes applied!")
        else:
            print("DRY RUN - No changes applied")
            print("Run with --apply to execute fixes")
        
        print()
    
    def find_corrupted_entity_types(self, nodes: List[Dict]) -> List[Dict]:
        """
        Find entities with corrupted entity_type values (Branch 005).
        
        Corruption patterns from Grok-4-fast-reasoning chain-of-thought artifacts:
        - Prefix "#>|" or "#|" (e.g., "#>|LOCATION", "#|PROGRAM")
        - Lowercase when should be uppercase (e.g., "evaluation_factor")
        - Invalid types not in entity_types list
        
        Baseline: 2.2% corruption rate (13/594 entities in Navy MBOS)
        
        WARNING: This modifies entity_type directly. Test on dedicated branch first!
        """
        # 17 valid entity types from src/raganything_server.py
        VALID_TYPES = {
            'ORGANIZATION', 'CONCEPT', 'EVENT', 'TECHNOLOGY', 'PERSON', 'LOCATION',
            'REQUIREMENT', 'CLAUSE', 'SECTION', 'DOCUMENT', 'DELIVERABLE', 
            'PROGRAM', 'EQUIPMENT', 'EVALUATION_FACTOR', 'SUBMISSION_INSTRUCTION',
            'STRATEGIC_THEME', 'STATEMENT_OF_WORK'
        }
        
        corrupted = []
        
        for node in nodes:
            entity_type = node.get('entity_type', '')
            entity_name = node.get('entity_name', '')
            
            # Skip if no type
            if not entity_type or entity_type in ['', 'None']:
                continue
            
            # Pattern 1: Prefix corruption (#>|TYPE, #|TYPE)
            if entity_type.startswith('#>|') or entity_type.startswith('#|'):
                clean_type = entity_type.replace('#>|', '').replace('#|', '').strip()
                expected_type = clean_type.upper() if clean_type.upper() in VALID_TYPES else 'UNKNOWN'
                
                corrupted.append({
                    'node_id': node['id'],
                    'entity_name': entity_name,
                    'corrupted_type': entity_type,
                    'expected_type': expected_type,
                    'pattern': 'prefix_corruption',
                    'confidence': 0.95 if expected_type != 'UNKNOWN' else 0.50
                })
            
            # Pattern 2: Lowercase corruption (evaluation_factor -> EVALUATION_FACTOR)
            elif entity_type.lower() in [t.lower() for t in VALID_TYPES] and entity_type not in VALID_TYPES:
                expected_type = entity_type.upper()
                
                corrupted.append({
                    'node_id': node['id'],
                    'entity_name': entity_name,
                    'corrupted_type': entity_type,
                    'expected_type': expected_type,
                    'pattern': 'lowercase_corruption',
                    'confidence': 0.90
                })
            
            # Pattern 3: Invalid type not in list (excluding common variations)
            elif entity_type not in VALID_TYPES:
                # Try to guess expected type
                expected_type = 'UNKNOWN'
                
                # Common mappings
                type_lower = entity_type.lower()
                if 'location' in type_lower or 'place' in type_lower:
                    expected_type = 'LOCATION'
                elif 'program' in type_lower or 'project' in type_lower:
                    expected_type = 'PROGRAM'
                elif 'document' in type_lower or 'file' in type_lower:
                    expected_type = 'DOCUMENT'
                elif 'requirement' in type_lower or 'req' in type_lower:
                    expected_type = 'REQUIREMENT'
                
                corrupted.append({
                    'node_id': node['id'],
                    'entity_name': entity_name,
                    'corrupted_type': entity_type,
                    'expected_type': expected_type,
                    'pattern': 'invalid_type',
                    'confidence': 0.50 if expected_type != 'UNKNOWN' else 0.20
                })
        
        return corrupted
    
    async def fix_corrupted_entity_types(self, corrupted: List[Dict], apply: bool = False):
        """
        Fix corrupted entity types by updating entity metadata.
        
        WARNING: This directly modifies entity_type. Only auto-fixes high-confidence patterns.
        Low-confidence items require manual review.
        """
        print("=" * 80)
        print("FIX PATTERN: Entity Type Corruption (Branch 005)")
        print("=" * 80)
        print()
        print("⚠️  WARNING: This pattern modifies entity_type directly!")
        print("   Only run on dedicated branch after backup.")
        print("   Baseline corruption rate: 2.2% (13/594 entities)")
        print()
        
        if not corrupted:
            print("✅ No corrupted entity types found!")
            return
        
        # Separate by confidence
        high_confidence = [c for c in corrupted if c['confidence'] >= 0.80]
        low_confidence = [c for c in corrupted if c['confidence'] < 0.80]
        
        print(f"Found {len(corrupted)} corrupted entity types:")
        print(f"  - High confidence (auto-fixable): {len(high_confidence)}")
        print(f"  - Low confidence (manual review):  {len(low_confidence)}")
        print()
        
        # Show high-confidence fixes
        if high_confidence:
            print("HIGH CONFIDENCE FIXES (auto-fixable):")
            print()
            for item in high_confidence:
                print(f"  • {item['entity_name']}")
                print(f"    Corrupted: {item['corrupted_type']}")
                print(f"    Expected:  {item['expected_type']}")
                print(f"    Pattern:   {item['pattern']}")
                print(f"    Confidence: {item['confidence']:.2f}")
                print()
        
        # Show low-confidence items (require manual review)
        if low_confidence:
            print("LOW CONFIDENCE ITEMS (require manual review):")
            print()
            for item in low_confidence:
                print(f"  • {item['entity_name']}")
                print(f"    Corrupted: {item['corrupted_type']}")
                print(f"    Suggested: {item['expected_type']}")
                print(f"    Pattern:   {item['pattern']}")
                print(f"    Confidence: {item['confidence']:.2f}")
                print()
        
        print("=" * 80)
        print(f"SUMMARY: {len(high_confidence)} auto-fixable, {len(low_confidence)} manual review")
        print("=" * 80)
        print()
        
        if apply and not self.dry_run:
            print("Applying fixes to high-confidence items...")
            fixed_count = 0
            for item in high_confidence:
                if item['expected_type'] != 'UNKNOWN':
                    try:
                        await self.rag.aedit_entity(
                            entity_name=item['entity_name'],
                            updated_data={'entity_type': item['expected_type']}
                        )
                        print(f"  ✅ {item['entity_name']}: {item['corrupted_type']} → {item['expected_type']}")
                        fixed_count += 1
                    except Exception as e:
                        print(f"  ❌ {item['entity_name']}: Failed - {str(e)}")
            
            print()
            print(f"✅ Fixed {fixed_count}/{len(high_confidence)} high-confidence items")
            
            if low_confidence:
                print()
                print(f"⚠️  {len(low_confidence)} items require manual review via Web UI or interactive CLI")
        else:
            print("DRY RUN - No changes applied")
            print("Run with --apply to execute fixes")
            if low_confidence:
                print()
                print(f"Note: Only {len(high_confidence)} high-confidence items would be auto-fixed")
                print(f"      {len(low_confidence)} low-confidence items require manual review regardless")
        
        print()
    
    async def run_pattern(self, pattern: str, apply: bool = False):
        """
        Run a specific fix pattern.
        
        Args:
            pattern: One of ['isolated_nodes', 'missing_hierarchy', 'corruption', 'all']
            apply: If True, apply fixes. If False, dry run only.
        """
        self.dry_run = not apply
        
        # Load graph
        nodes, edges = self.load_graph_structure()
        
        if pattern in ['isolated_nodes', 'all']:
            isolated = self.find_isolated_nodes(nodes, edges, threshold=3)
            await self.fix_isolated_nodes(isolated, apply=apply)
        
        if pattern in ['missing_hierarchy', 'all']:
            missing = self.find_missing_hierarchical_relationships(nodes, edges)
            await self.fix_missing_hierarchical_relationships(missing, apply=apply)
        
        if pattern in ['corruption']:
            # NOTE: 'corruption' pattern NOT included in 'all' for safety
            # Must be explicitly requested
            corrupted = self.find_corrupted_entity_types(nodes)
            await self.fix_corrupted_entity_types(corrupted, apply=apply)


async def main():
    parser = argparse.ArgumentParser(
        description="Pattern-based bulk graph editing tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview only)
  python bulk_graph_fixes.py --pattern isolated_nodes --dry-run
  
  # Apply isolated nodes fixes
  python bulk_graph_fixes.py --pattern isolated_nodes --apply
  
  # Run all patterns (dry run)
  python bulk_graph_fixes.py --pattern all --dry-run
  
  # Apply all fixes
  python bulk_graph_fixes.py --pattern all --apply
  
  # Check for entity type corruption (Branch 005)
  python bulk_graph_fixes.py --pattern corruption --dry-run
  
  # Fix corruption (WARNING: Test on dedicated branch first!)
  python bulk_graph_fixes.py --pattern corruption --apply

Patterns:
  isolated_nodes     - Fix nodes with < 3 edges
  missing_hierarchy  - Add missing CHILD_OF relationships
  corruption         - Fix entity_type corruption (#>|TYPE, #|TYPE, lowercase)
                       WARNING: NOT included in 'all', must explicitly specify
                       Test on dedicated branch first!
  all                - Run all patterns EXCEPT corruption (for safety)
        """
    )
    
    parser.add_argument(
        '--pattern',
        choices=['isolated_nodes', 'missing_hierarchy', 'corruption', 'all'],
        required=True,
        help='Fix pattern to run (NOTE: corruption must be explicitly specified, not included in all)'
    )
    
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Apply fixes (default is dry-run only)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview fixes without applying (default)'
    )
    
    parser.add_argument(
        '--working-dir',
        default='./rag_storage',
        help='Path to RAG storage directory (default: ./rag_storage)'
    )
    
    args = parser.parse_args()
    
    # Initialize fixer
    fixer = BulkGraphFixer(working_dir=args.working_dir)
    await fixer.initialize()
    
    # Run pattern
    apply = args.apply and not args.dry_run
    await fixer.run_pattern(args.pattern, apply=apply)


if __name__ == "__main__":
    asyncio.run(main())
