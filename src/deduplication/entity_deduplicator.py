"""
Entity deduplication module for custom knowledge graph insertion.

LightRAG's ainsert_custom_kg() doesn't properly deduplicate entities when using
Neo4j storage. This module implements manual deduplication by entity_name,
merging duplicate entities while preserving metadata and descriptions.
"""

import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def deduplicate_entities(entities: List[Dict]) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Deduplicate entities by entity_name, merging metadata from duplicates.
    
    Args:
        entities: List of entity dictionaries with 'entity_name' keys
        
    Returns:
        Tuple of (deduplicated_entities, duplicate_counts)
        - deduplicated_entities: List with duplicates merged
        - duplicate_counts: Dict mapping entity_name to occurrence count (only duplicates)
    
    Merge Strategy:
        - Keep first occurrence of each entity_name
        - Merge descriptions from duplicates (append unique text)
        - Preserve all metadata from first occurrence
        - Track how many duplicates were consolidated
    """
    if not entities:
        return [], {}
    
    # Count occurrences of each entity_name
    entity_count = {}
    for entity_dict in entities:
        name = entity_dict.get("entity_name")
        if name:
            entity_count[name] = entity_count.get(name, 0) + 1
    
    # Identify duplicates (appearing more than once)
    duplicates = {name: count for name, count in entity_count.items() if count > 1}
    
    if not duplicates:
        logger.debug(f"No duplicate entity names found (all {len(entities)} are unique)")
        return entities, {}
    
    # Deduplicate: keep first occurrence, merge metadata from duplicates
    seen_names = {}
    deduplicated_entities = []
    
    for entity_dict in entities:
        name = entity_dict.get("entity_name")
        if not name:
            # Entity without name - keep as-is
            deduplicated_entities.append(entity_dict)
            continue
        
        if name not in seen_names:
            # First occurrence - keep it
            seen_names[name] = entity_dict
            deduplicated_entities.append(entity_dict)
        else:
            # Duplicate - merge description into first occurrence
            first_occurrence = seen_names[name]
            duplicate_desc = entity_dict.get("description", "").strip()
            
            if duplicate_desc:
                existing_desc = first_occurrence.get("description", "").strip()
                # Only append if description text is different
                if duplicate_desc not in existing_desc:
                    merged_desc = f"{existing_desc} {duplicate_desc}".strip()
                    first_occurrence["description"] = merged_desc
    
    entities_merged = len(entities) - len(deduplicated_entities)
    logger.debug(f"Deduplicated {len(entities)} → {len(deduplicated_entities)} entities ({entities_merged} duplicates merged)")
    
    return deduplicated_entities, duplicates


def log_deduplication_stats(
    total_before: int,
    total_after: int,
    duplicates: Dict[str, int],
    max_examples: int = 10
) -> None:
    """
    Log deduplication statistics in LightRAG-compatible format.
    
    Args:
        total_before: Entity count before deduplication
        total_after: Entity count after deduplication
        duplicates: Dict mapping entity_name to occurrence count
        max_examples: Maximum number of example merges to show
    """
    if not duplicates:
        logger.info(f"💾 No duplicate entity names found (all {total_before} are unique)")
        return
    
    entities_merged = total_before - total_after
    
    logger.info(f"🔀 Pre-processing: Merging {len(duplicates)} duplicate entity names before insertion...")
    
    # Show itemized merges (sorted by occurrence count, descending)
    sample_size = min(max_examples, len(duplicates))
    for name, count in sorted(duplicates.items(), key=lambda x: -x[1])[:sample_size]:
        # LightRAG format: "Merged: 'Entity Name' | X+1" where X = duplicates merged
        logger.info(f"   Merged: `{name}` | {count-1}+1")
    
    if len(duplicates) > sample_size:
        logger.info(f"   ... and {len(duplicates) - sample_size} more entities merged")
    
    logger.info(f"   ✅ Deduplicated: {total_before} → {total_after} entities ({entities_merged} duplicates merged)")
