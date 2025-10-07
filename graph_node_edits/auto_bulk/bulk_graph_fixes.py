"""
Pattern-Based Bulk Graph Editing Tool

This is the PRIMARY method for fixing common graph issues:
- Isolated nodes (low edge count)
- Missing hierarchical relationships
- Untyped or generic relationships
- Scattered clauses/annexes

For one-off or controversial edits, use interactive_graph_edit.ps1 instead.

Usage:
    python bulk_graph_fixes.py --pattern isolated_nodes --dry-run
    python bulk_graph_fixes.py --pattern missing_hierarchy --apply
    python bulk_graph_fixes.py --pattern all --dry-run
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
    
    async def run_pattern(self, pattern: str, apply: bool = False):
        """
        Run a specific fix pattern.
        
        Args:
            pattern: One of ['isolated_nodes', 'missing_hierarchy', 'all']
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

Patterns:
  isolated_nodes     - Fix nodes with < 3 edges
  missing_hierarchy  - Add missing CHILD_OF relationships
  all               - Run all patterns
        """
    )
    
    parser.add_argument(
        '--pattern',
        choices=['isolated_nodes', 'missing_hierarchy', 'all'],
        required=True,
        help='Fix pattern to run'
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
