"""
Entity Type Cleanup Utilities

Post-processing functions to fix LLM entity type format corruption.
Addresses issue where Grok-4-fast-reasoning occasionally adds special 
characters (#/>, #>|, #|) despite extensive prompt engineering.
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Known corruption patterns from terminal logs
CORRUPTION_PATTERNS = [
    "#/>",  # Most common: #/>CONCEPT
    "#>|",  # Second most common: #>|DOCUMENT, #>|SECTION
    "#|",   # Third: #|SECTION
    "<|",   # Edge case
    "|>",   # Edge case
]


def clean_entity_type(entity_type: str) -> str:
    """
    Remove LLM format corruption from entity types.
    
    Handles corruption patterns from Grok-4-fast-reasoning:
    - #/>CONCEPT → CONCEPT
    - #>|DOCUMENT → DOCUMENT
    - #|SECTION → SECTION
    - <|TECHNOLOGY → TECHNOLOGY
    - |>REQUIREMENT → REQUIREMENT
    
    Args:
        entity_type: Raw entity type string from LLM extraction
    
    Returns:
        Cleaned uppercase entity type without corruption prefixes/suffixes
    
    Examples:
        >>> clean_entity_type("#/>CONCEPT")
        'CONCEPT'
        >>> clean_entity_type("#>|DOCUMENT")
        'DOCUMENT'
        >>> clean_entity_type("ORGANIZATION")
        'ORGANIZATION'
    """
    if not entity_type:
        return entity_type
    
    cleaned = entity_type.strip()
    
    # Strip corruption prefixes (check all patterns)
    for prefix in CORRUPTION_PATTERNS:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            logger.debug(f"Cleaned entity type prefix: {entity_type} → {cleaned}")
        if cleaned.endswith(prefix):
            cleaned = cleaned[:-len(prefix)]
            logger.debug(f"Cleaned entity type suffix: {entity_type} → {cleaned}")
    
    # Ensure uppercase (standard format)
    cleaned = cleaned.upper().strip()
    
    return cleaned


def validate_entity_type(entity_type: str, valid_types: List[str]) -> Tuple[bool, str]:
    """
    Validate entity type against known valid types with automatic cleanup.
    
    Args:
        entity_type: Raw entity type from extraction
        valid_types: List of valid entity type names (e.g., from config.py)
    
    Returns:
        Tuple of (is_valid, cleaned_type)
        - is_valid: True if cleaned type matches valid_types
        - cleaned_type: Cleaned entity type (uppercase, no corruption)
    
    Examples:
        >>> validate_entity_type("#/>CONCEPT", ["CONCEPT", "ORGANIZATION"])
        (True, 'CONCEPT')
        >>> validate_entity_type("INVALID_TYPE", ["CONCEPT", "ORGANIZATION"])
        (False, 'INVALID_TYPE')
    """
    cleaned = clean_entity_type(entity_type)
    
    # Check if cleaned type is valid
    is_valid = cleaned in valid_types
    
    if not is_valid and entity_type != cleaned:
        # Log when cleanup was attempted but still invalid
        logger.warning(
            f"Entity type cleanup attempted but still invalid: "
            f"{entity_type} → {cleaned} (valid types: {valid_types})"
        )
    
    return is_valid, cleaned


def clean_entities_batch(entities: List[Dict], valid_types: List[str]) -> Tuple[List[Dict], int]:
    """
    Clean entity types in a batch of entities.
    
    Args:
        entities: List of entity dicts with 'entity_type' field
        valid_types: List of valid entity type names
    
    Returns:
        Tuple of (cleaned_entities, correction_count)
        - cleaned_entities: List with corrected entity_type fields
        - correction_count: Number of entities that required cleanup
    
    Example:
        >>> entities = [
        ...     {"entity_name": "MCPP II", "entity_type": "#/>CONCEPT"},
        ...     {"entity_name": "Navy", "entity_type": "ORGANIZATION"}
        ... ]
        >>> cleaned, count = clean_entities_batch(entities, ["CONCEPT", "ORGANIZATION"])
        >>> count
        1
        >>> cleaned[0]["entity_type"]
        'CONCEPT'
    """
    cleaned_entities = []
    correction_count = 0
    
    for entity in entities:
        if "entity_type" not in entity:
            # Skip entities without type field
            cleaned_entities.append(entity)
            continue
        
        original_type = entity["entity_type"]
        is_valid, cleaned_type = validate_entity_type(original_type, valid_types)
        
        # Update entity with cleaned type
        entity_copy = entity.copy()
        entity_copy["entity_type"] = cleaned_type
        
        if original_type != cleaned_type:
            correction_count += 1
            logger.info(
                f"Corrected entity '{entity.get('entity_name', 'unknown')}': "
                f"{original_type} → {cleaned_type}"
            )
        
        # Only include valid entities
        if is_valid:
            cleaned_entities.append(entity_copy)
        else:
            logger.warning(
                f"Skipping invalid entity '{entity.get('entity_name', 'unknown')}' "
                f"with type '{cleaned_type}' (not in valid_types)"
            )
    
    if correction_count > 0:
        logger.info(
            f"Entity type cleanup complete: {correction_count}/{len(entities)} entities corrected"
        )
    
    return cleaned_entities, correction_count


def analyze_corruption_patterns(entities: List[Dict]) -> Dict[str, int]:
    """
    Analyze entity type corruption patterns in a dataset.
    
    Useful for debugging and monitoring LLM extraction quality.
    
    Args:
        entities: List of entity dicts with 'entity_type' field
    
    Returns:
        Dict mapping corruption pattern to occurrence count
    
    Example:
        >>> entities = [
        ...     {"entity_type": "#/>CONCEPT"},
        ...     {"entity_type": "#>|DOCUMENT"},
        ...     {"entity_type": "#/>TECHNOLOGY"}
        ... ]
        >>> analyze_corruption_patterns(entities)
        {'#/>': 2, '#>|': 1}
    """
    pattern_counts = {pattern: 0 for pattern in CORRUPTION_PATTERNS}
    
    for entity in entities:
        entity_type = entity.get("entity_type", "")
        for pattern in CORRUPTION_PATTERNS:
            if pattern in entity_type:
                pattern_counts[pattern] += 1
    
    # Filter to only patterns found
    return {k: v for k, v in pattern_counts.items() if v > 0}
