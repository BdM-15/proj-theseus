"""
Knowledge Graph I/O Operations

Handles reading and writing to GraphML and kv_store files for the knowledge graph.
Provides clean interfaces for semantic relationship inference and post-processing.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


def parse_graphml(graphml_path: Path) -> Tuple[List[Dict], List[Dict]]:
    """
    Parse GraphML file to extract nodes (entities) and edges (relationships).
    
    Args:
        graphml_path: Path to graph_chunk_entity_relation.graphml file
        
    Returns:
        Tuple of (nodes, edges) where:
        - nodes: List of dicts with keys: id, entity_name, entity_type, description
        - edges: List of dicts with keys: id, source, target, keywords, weight, description, source_id
        
    Example:
        nodes, edges = parse_graphml(Path("./rag_storage/graph_chunk_entity_relation.graphml"))
    """
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    
    # GraphML namespace
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    
    nodes = []
    edges = []
    
    # Extract nodes (entities)
    for node in root.findall('.//graphml:node', ns):
        node_id = node.get('id')
        node_data = {'id': node_id}
        
        # Extract data attributes (d0=entity_name, d1=entity_type, d2=description)
        for data in node.findall('graphml:data', ns):
            key = data.get('key')
            value = data.text
            
            if key == 'd0':
                node_data['entity_name'] = value
            elif key == 'd1':
                node_data['entity_type'] = value
            elif key == 'd2':
                node_data['description'] = value
        
        nodes.append(node_data)
    
    # Extract edges (relationships)
    for edge in root.findall('.//graphml:edge', ns):
        edge_id = edge.get('id')
        source = edge.get('source')
        target = edge.get('target')
        
        edge_data = {
            'id': edge_id,
            'source': source,
            'target': target
        }
        
        # Extract edge attributes (d3=keywords, d4=weight, d5=description, d6=source_id)
        for data in edge.findall('graphml:data', ns):
            key = data.get('key')
            value = data.text
            
            if key == 'd3':
                edge_data['keywords'] = value
            elif key == 'd4':
                edge_data['weight'] = float(value) if value else 0.0
            elif key == 'd5':
                edge_data['description'] = value
            elif key == 'd6':
                edge_data['source_id'] = value
        
        edges.append(edge_data)
    
    logger.info(f"  📊 Parsed GraphML: {len(nodes)} nodes, {len(edges)} edges")
    return nodes, edges


def save_cleaned_entities_to_graphml(
    graphml_path: Path,
    nodes: List[Dict]
) -> None:
    """
    Update entity types in GraphML after cleanup (removes UNKNOWN, other, #prefixes).
    
    Args:
        graphml_path: Path to graph_chunk_entity_relation.graphml file
        nodes: List of cleaned entity dicts with updated entity_type fields
    """
    # Parse existing GraphML
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    
    # Create entity_type lookup from cleaned nodes
    entity_type_map = {node['id']: node.get('entity_type', 'concept') for node in nodes}
    
    # Update entity_type (d1) for all nodes
    updated_count = 0
    for node in root.findall('.//graphml:node', ns):
        node_id = node.get('id')
        if node_id in entity_type_map:
            new_type = entity_type_map[node_id]
            
            # Find d1 (entity_type) data element
            for data in node.findall('graphml:data', ns):
                if data.get('key') == 'd1':
                    old_type = data.text
                    if old_type != new_type:
                        data.text = new_type
                        updated_count += 1
                        logger.debug(f"Updated {node_id}: {old_type} → {new_type}")
                    break
    
    # Write updated GraphML back to file
    tree.write(graphml_path, encoding='utf-8', xml_declaration=True)
    logger.info(f"  ✅ Updated {updated_count} entity types in GraphML")


def save_relationships_to_graphml(
    graphml_path: Path,
    new_relationships: List[Dict],
    nodes: List[Dict]
) -> None:
    """
    Save new relationships back to GraphML file.
    
    Appends new edge elements to existing GraphML structure without
    overwriting existing data.
    
    Args:
        graphml_path: Path to graph_chunk_entity_relation.graphml file
        new_relationships: List of relationship dicts with keys:
            - source_id: Entity ID for source node
            - target_id: Entity ID for target node
            - relationship_type: Type of relationship (e.g., "CHILD_OF")
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Human-readable explanation
        nodes: List of entity nodes for reference
        
    Example:
        save_relationships_to_graphml(
            Path("./rag_storage/graph_chunk_entity_relation.graphml"),
            [{"source_id": "n1", "target_id": "n2", "relationship_type": "CHILD_OF", 
              "confidence": 0.95, "reasoning": "J-12345 belongs to Section J"}],
            nodes
        )
    """
    # Parse existing GraphML
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    
    # Find graph element
    graph = root.find('.//graphml:graph', ns)
    if graph is None:
        logger.error("❌ Could not find graph element in GraphML")
        return
    
    # Get next edge ID and build set of existing edges to avoid duplicates
    existing_edges = graph.findall('.//graphml:edge', ns)
    max_edge_id = 0
    existing_edge_pairs = set()
    
    for edge in existing_edges:
        edge_id = edge.get('id', 'e0')
        if edge_id.startswith('e'):
            try:
                edge_num = int(edge_id[1:])
                max_edge_id = max(max_edge_id, edge_num)
            except ValueError:
                pass
        
        # Track existing edges (normalized for undirected graph)
        src = edge.get('source')
        tgt = edge.get('target')
        if src and tgt:
            edge_pair = tuple(sorted([src, tgt]))
            existing_edge_pairs.add(edge_pair)
    
    next_edge_id = max_edge_id + 1
    
    # Add new edges (using proper GraphML namespace - match LightRAG's ns0: prefix)
    graphml_ns = 'http://graphml.graphdrawing.org/xmlns'
    try:
        ET.register_namespace('ns0', graphml_ns)  # Register as ns0: to match LightRAG
    except ValueError:
        # Namespace already registered (happens if file was parsed earlier in same process)
        pass
    
    added_count = 0
    skipped_count = 0
    
    for rel in new_relationships:
        source_id = rel['source_id']
        target_id = rel['target_id']
        
        # Check if edge already exists (normalized for undirected graph)
        edge_pair = tuple(sorted([source_id, target_id]))
        if edge_pair in existing_edge_pairs:
            skipped_count += 1
            logger.debug(f"  ⏭️  Skipping duplicate edge: {source_id} <-> {target_id}")
            continue
        
        rel_type = rel['relationship_type']
        confidence = rel['confidence']
        reasoning = rel['reasoning']
        
        # Create edge element with namespace
        edge = ET.SubElement(graph, f'{{{graphml_ns}}}edge')
        edge.set('id', f'e{next_edge_id}')
        edge.set('source', source_id)
        edge.set('target', target_id)
        
        # Add edge data (MATCH LightRAG schema: d6=weight, d7=description, d8=keywords, d9=source_id)
        weight_data = ET.SubElement(edge, f'{{{graphml_ns}}}data')
        weight_data.set('key', 'd6')
        weight_data.text = str(confidence)
        
        description_data = ET.SubElement(edge, f'{{{graphml_ns}}}data')
        description_data.set('key', 'd7')
        description_data.text = f"{reasoning} (LLM-inferred)"
        
        keywords_data = ET.SubElement(edge, f'{{{graphml_ns}}}data')
        keywords_data.set('key', 'd8')
        keywords_data.text = rel_type
        
        source_data = ET.SubElement(edge, f'{{{graphml_ns}}}data')
        source_data.set('key', 'd9')
        source_data.text = 'semantic_post_processing'
        
        # Add to tracking set
        existing_edge_pairs.add(edge_pair)
        added_count += 1
        next_edge_id += 1
    
    # Write back to file
    tree.write(graphml_path, encoding='utf-8', xml_declaration=True)
    
    if skipped_count > 0:
        logger.info(f"  💾 Added {added_count} new relationships, skipped {skipped_count} duplicates")
    else:
        logger.info(f"  💾 Saved {added_count} new relationships to GraphML")


def save_relationships_to_kv_store(
    rag_storage_path: Path,
    new_relationships: List[Dict],
    nodes: List[Dict]
) -> None:
    """
    Save new relationships to kv_store_full_relations.json.
    
    Appends to both individual relationship records AND document's relation_pairs array.
    This ensures LightRAG WebUI displays the new relationships correctly.
    
    Args:
        rag_storage_path: Path to rag_storage directory
        new_relationships: List of relationship dicts (same format as save_relationships_to_graphml)
        nodes: List of entity nodes for looking up entity names
        
    Example:
        save_relationships_to_kv_store(
            Path("./rag_storage"),
            [{"source_id": "n1", "target_id": "n2", "relationship_type": "CHILD_OF", 
              "confidence": 0.95, "reasoning": "J-12345 belongs to Section J"}],
            nodes
        )
    """
    relations_path = rag_storage_path / "kv_store_full_relations.json"
    
    # Load existing relationships
    with open(relations_path, 'r', encoding='utf-8') as f:
        relations_data = json.load(f)
    
    # Find document key
    doc_keys = [k for k in relations_data.keys() if k.startswith('doc-')]
    if not doc_keys:
        logger.error("❌ No document key found in kv_store_full_relations.json")
        return
    
    doc_id = doc_keys[0]
    
    # Get next relationship ID
    max_id = 0
    for rel_id in relations_data.keys():
        if rel_id.startswith('rel_'):
            try:
                id_num = int(rel_id.split('_')[1])
                max_id = max(max_id, id_num)
            except (ValueError, IndexError):
                pass
    
    next_id = max_id + 1
    
    # Create node name lookup for relation_pairs
    node_lookup = {node['id']: node.get('entity_name', 'Unknown') for node in nodes}
    
    # Add new relationships
    for rel in new_relationships:
        rel_id = f"rel_llm_{next_id}"
        relations_data[rel_id] = {
            'src_id': rel['source_id'],
            'tgt_id': rel['target_id'],
            'relationship_type': rel['relationship_type'],
            'description': f"{rel['reasoning']} (LLM-inferred, confidence={rel['confidence']:.2f})",
            'weight': rel['confidence'],
            'keywords': rel['relationship_type'],
            'source_id': 'semantic_post_processing'
        }
        
        # CRITICAL: Also add to document's relation_pairs array for WebUI display
        src_name = node_lookup.get(rel['source_id'], 'Unknown')
        tgt_name = node_lookup.get(rel['target_id'], 'Unknown')
        relations_data[doc_id]['relation_pairs'].append([src_name, tgt_name])
        
        next_id += 1
    
    # Write back to file
    with open(relations_path, 'w', encoding='utf-8') as f:
        json.dump(relations_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"  💾 Saved {len(new_relationships)} relationships to kv_store (individual records + relation_pairs)")


def group_entities_by_type(nodes: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group entities by type for efficient batching.
    
    Args:
        nodes: List of entity dicts with 'entity_type' key
        
    Returns:
        Dict mapping entity_type (lowercase) to list of entities
        
    Example:
        grouped = group_entities_by_type(nodes)
        # {"document": [...], "section": [...], "requirement": [...]}
    """
    grouped = {}
    for node in nodes:
        entity_type = node.get('entity_type', '').lower()
        if entity_type not in grouped:
            grouped[entity_type] = []
        grouped[entity_type].append(node)
    
    return grouped
