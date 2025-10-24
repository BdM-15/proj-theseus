"""
Phase 7: Metadata Enrichment for Knowledge Graph Entities

GOAL: Extract structured metadata from entity descriptions WITHOUT modifying descriptions.
APPROACH: Parse natural language descriptions → populate separate GraphML node attributes.
USE CASE: Future agents need structured data (weights, page limits, criticality) for deliverables.

This is a NON-DESTRUCTIVE enhancement that preserves strategic reasoning in descriptions.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


async def enrich_entities_with_metadata(
    nodes: List[Dict],
    llm_func,
    entity_types_to_enrich: List[str] = None
) -> Dict[str, int]:
    """
    Extract structured metadata from entity descriptions and add as node attributes.
    
    Args:
        nodes: List of entity dicts with 'entity_type', 'description', 'id'
        llm_func: Async LLM function for metadata extraction
        entity_types_to_enrich: List of entity types to process (default: evaluation_factor, 
                                submission_instruction, requirement)
    
    Returns:
        Dict with counts of enriched entities by type
    """
    if entity_types_to_enrich is None:
        entity_types_to_enrich = ['evaluation_factor', 'submission_instruction', 'requirement']
    
    logger.info(f"📊 Phase 7: Metadata enrichment starting...")
    
    # Filter entities to enrich
    entities_to_process = [
        node for node in nodes 
        if node.get('entity_type', '').lower() in entity_types_to_enrich
    ]
    
    if not entities_to_process:
        logger.info(f"  ⏭️  No entities matching types {entity_types_to_enrich} - skipping enrichment")
        return {}
    
    logger.info(f"  🎯 Enriching {len(entities_to_process)} entities across {len(entity_types_to_enrich)} types")
    
    # Process by type for efficient batching
    enrichment_counts = {}
    
    for entity_type in entity_types_to_enrich:
        type_entities = [e for e in entities_to_process if e.get('entity_type', '').lower() == entity_type]
        
        if not type_entities:
            continue
        
        logger.info(f"  📝 Processing {len(type_entities)} {entity_type} entities...")
        
        if entity_type == 'evaluation_factor':
            enriched = await _enrich_evaluation_factors(type_entities, llm_func)
        elif entity_type == 'submission_instruction':
            enriched = await _enrich_submission_instructions(type_entities, llm_func)
        elif entity_type == 'requirement':
            enriched = await _enrich_requirements(type_entities, llm_func)
        else:
            enriched = 0
        
        enrichment_counts[entity_type] = enriched
    
    total_enriched = sum(enrichment_counts.values())
    logger.info(f"  ✅ Enriched {total_enriched} entities with metadata")
    
    return enrichment_counts


async def _enrich_evaluation_factors(entities: List[Dict], llm_func) -> int:
    """Extract metadata for EVALUATION_FACTOR entities."""
    
    prompt_template = """Extract structured metadata from this evaluation factor description.

Entity: {entity_name}
Description: {description}

Extract ONLY if explicitly stated in the description:
1. weight: Numerical weight with unit (e.g., "40%", "25 points", "300/1000")
2. importance: Relative hierarchy (e.g., "Most Important", "Significantly More Important")
3. subfactors: List of sub-evaluation areas with weights if hierarchical

Return JSON format:
{{
  "weight": "40%" or "unknown",
  "importance": "Most Important" or "unknown",
  "subfactors": ["subfactor1", "subfactor2"] or []
}}

If information is NOT in the description, use "unknown" or empty list. DO NOT infer."""

    enriched_count = 0
    
    for entity in entities:
        entity_name = entity.get('entity_name', entity.get('id', 'Unknown'))
        description = entity.get('description', '')
        
        if not description:
            continue
        
        prompt = prompt_template.format(
            entity_name=entity_name,
            description=description
        )
        
        try:
            response = await llm_func(prompt, max_tokens=200)
            
            # Parse JSON response
            metadata = json.loads(response)
            
            # Add metadata as node attributes (only if not "unknown")
            if metadata.get('weight') and metadata['weight'] != 'unknown':
                entity['metadata_weight'] = metadata['weight']
                enriched_count += 1
            
            if metadata.get('importance') and metadata['importance'] != 'unknown':
                entity['metadata_importance'] = metadata['importance']
            
            if metadata.get('subfactors'):
                entity['metadata_subfactors'] = json.dumps(metadata['subfactors'])
            
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not extract metadata for {entity_name}: {e}")
            continue
    
    return enriched_count


async def _enrich_submission_instructions(entities: List[Dict], llm_func) -> int:
    """Extract metadata for SUBMISSION_INSTRUCTION entities."""
    
    prompt_template = """Extract structured metadata from this submission instruction description.

Entity: {entity_name}
Description: {description}

Extract ONLY if explicitly stated:
1. page_limit: Exact number (e.g., "25 pages", "30 slides", "unlimited")
2. format: Font, margins, spacing (e.g., "12pt Times New Roman, 1-inch margins")
3. addressed_factors: Which evaluation factors this guides (e.g., ["Factor 1", "Factor 2"])

Return JSON format:
{{
  "page_limit": "25 pages" or "unknown",
  "format": "12pt Times New Roman, 1-inch margins" or "unknown",
  "addressed_factors": ["Factor 1"] or []
}}

If information is NOT in the description, use "unknown" or empty list. DO NOT infer."""

    enriched_count = 0
    
    for entity in entities:
        entity_name = entity.get('entity_name', entity.get('id', 'Unknown'))
        description = entity.get('description', '')
        
        if not description:
            continue
        
        prompt = prompt_template.format(
            entity_name=entity_name,
            description=description
        )
        
        try:
            response = await llm_func(prompt, max_tokens=200)
            metadata = json.loads(response)
            
            if metadata.get('page_limit') and metadata['page_limit'] != 'unknown':
                entity['metadata_page_limit'] = metadata['page_limit']
                enriched_count += 1
            
            if metadata.get('format') and metadata['format'] != 'unknown':
                entity['metadata_format'] = metadata['format']
            
            if metadata.get('addressed_factors'):
                entity['metadata_addressed_factors'] = json.dumps(metadata['addressed_factors'])
            
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not extract metadata for {entity_name}: {e}")
            continue
    
    return enriched_count


async def _enrich_requirements(entities: List[Dict], llm_func) -> int:
    """Extract metadata for REQUIREMENT entities."""
    
    prompt_template = """Extract structured metadata from this requirement description.

Entity: {entity_name}
Description: {description}

Extract ONLY if explicitly stated:
1. criticality: MANDATORY, IMPORTANT, or OPTIONAL (based on shall/should/may)
2. modal_verb: Exact verb used (shall, should, may, must, will)
3. subject: Who has the obligation (Contractor, Offeror, Personnel, Government)

Return JSON format:
{{
  "criticality": "MANDATORY" or "IMPORTANT" or "OPTIONAL" or "unknown",
  "modal_verb": "shall" or "unknown",
  "subject": "Contractor" or "unknown"
}}

If information is NOT in the description, use "unknown". DO NOT infer."""

    enriched_count = 0
    
    for entity in entities:
        entity_name = entity.get('entity_name', entity.get('id', 'Unknown'))
        description = entity.get('description', '')
        
        if not description:
            continue
        
        prompt = prompt_template.format(
            entity_name=entity_name,
            description=description
        )
        
        try:
            response = await llm_func(prompt, max_tokens=150)
            metadata = json.loads(response)
            
            if metadata.get('criticality') and metadata['criticality'] != 'unknown':
                entity['metadata_criticality'] = metadata['criticality']
                enriched_count += 1
            
            if metadata.get('modal_verb') and metadata['modal_verb'] != 'unknown':
                entity['metadata_modal_verb'] = metadata['modal_verb']
            
            if metadata.get('subject') and metadata['subject'] != 'unknown':
                entity['metadata_subject'] = metadata['subject']
            
        except (json.JSONDecodeError, Exception) as e:
            logger.debug(f"Could not extract metadata for {entity_name}: {e}")
            continue
    
    return enriched_count


def save_metadata_to_graphml(graphml_path: Path, nodes: List[Dict]) -> int:
    """
    Save metadata attributes to GraphML file.
    
    Adds metadata_* attributes to nodes without modifying description field.
    
    Args:
        graphml_path: Path to graph_chunk_entity_relation.graphml
        nodes: List of entities with metadata_* attributes populated
    
    Returns:
        Count of nodes with metadata saved
    """
    tree = ET.parse(graphml_path)
    root = tree.getroot()
    
    ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
    graphml_ns = 'http://graphml.graphdrawing.org/xmlns'
    
    # Register namespace
    try:
        ET.register_namespace('ns0', graphml_ns)
    except ValueError:
        pass
    
    # Find graph element to potentially add new key definitions
    graph_elem = root.find('.//graphml:graph', ns)
    if graph_elem is None:
        logger.error("❌ Could not find graph element")
        return 0
    
    # Get existing key definitions
    existing_keys = set()
    for key_elem in root.findall('.//graphml:key', ns):
        existing_keys.add(key_elem.get('id'))
    
    # Metadata attribute definitions we might need
    metadata_keys = {
        # Evaluation factor metadata
        'd10': ('metadata_weight', 'node', 'Evaluation factor weight (percentage or points)'),
        'd11': ('metadata_importance', 'node', 'Relative importance hierarchy'),
        'd12': ('metadata_subfactors', 'node', 'List of subfactors with weights'),
        # Submission instruction metadata
        'd13': ('metadata_page_limit', 'node', 'Page limit for submission'),
        'd14': ('metadata_format', 'node', 'Format requirements (font, margins, spacing)'),
        'd15': ('metadata_addressed_factors', 'node', 'Evaluation factors addressed by instruction'),
        # Requirement metadata
        'd16': ('metadata_criticality', 'node', 'Requirement criticality (MANDATORY/IMPORTANT/OPTIONAL)'),
        'd17': ('metadata_modal_verb', 'node', 'Modal verb used (shall/should/may)'),
        'd18': ('metadata_subject', 'node', 'Subject with obligation (Contractor/Offeror/Government)'),
    }
    
    # Add missing key definitions
    keys_added = []
    for key_id, (attr_name, for_type, description) in metadata_keys.items():
        if key_id not in existing_keys:
            key_elem = ET.Element(f'{{{graphml_ns}}}key')
            key_elem.set('id', key_id)
            key_elem.set('for', for_type)
            key_elem.set('attr.name', attr_name)
            key_elem.set('attr.type', 'string')
            
            # Add description
            desc_elem = ET.SubElement(key_elem, f'{{{graphml_ns}}}desc')
            desc_elem.text = description
            
            # Insert before graph element
            root.insert(list(root).index(graph_elem), key_elem)
            keys_added.append(attr_name)
            existing_keys.add(key_id)
    
    if keys_added:
        logger.info(f"  📋 Added {len(keys_added)} new metadata key definitions to GraphML")
    
    # Create entity lookup by ID
    node_lookup = {node.get('id', node.get('entity_name', '')): node for node in nodes}
    
    # Update nodes with metadata
    nodes_updated = 0
    
    for node_elem in root.findall('.//graphml:node', ns):
        node_id = node_elem.get('id')
        
        if node_id not in node_lookup:
            continue
        
        node_data = node_lookup[node_id]
        
        # Check if node has any metadata attributes
        metadata_attrs = {k: v for k, v in node_data.items() if k.startswith('metadata_')}
        
        if not metadata_attrs:
            continue
        
        # Map metadata attributes to key IDs
        attr_to_key = {v[0]: k for k, v in metadata_keys.items()}
        
        # Add metadata data elements
        for attr_name, value in metadata_attrs.items():
            key_id = attr_to_key.get(attr_name)
            if not key_id:
                continue
            
            # Check if data element already exists
            existing_data = node_elem.find(f'graphml:data[@key="{key_id}"]', ns)
            if existing_data is not None:
                existing_data.text = str(value)
            else:
                data_elem = ET.SubElement(node_elem, f'{{{graphml_ns}}}data')
                data_elem.set('key', key_id)
                data_elem.text = str(value)
        
        nodes_updated += 1
    
    # Write back to file
    tree.write(graphml_path, encoding='utf-8', xml_declaration=True)
    
    logger.info(f"  💾 Saved metadata for {nodes_updated} nodes to GraphML")
    
    return nodes_updated
