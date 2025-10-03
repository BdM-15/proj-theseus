"""
Ontology Validation for LightRAG Knowledge Graph Extraction

Post-processes LightRAG extraction results to ensure compliance with government
contracting ontology constraints. Filters invalid entities and relationships that
don't match our VALID_RELATIONSHIPS schema.

Purpose:
- Validate entity types against EntityType enum
- Validate relationships against VALID_RELATIONSHIPS schema
- Filter fictitious or malformed entities (Path A regression prevention)
- Provide detailed validation reporting for debugging

Architecture Note:
This is POST-PROCESSING validation, applied AFTER LightRAG extraction.
Does not bypass LightRAG - validates and cleans its output to ensure ontology compliance.

References:
- src/core/ontology.py: Entity types and relationship constraints
- src/core/lightrag_prompts.py: Prompt guidance that precedes this validation
- .venv/Lib/site-packages/lightrag/operate.py: LightRAG extraction output format
"""

from typing import Dict, List, Tuple, Set, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

from src.core.ontology import (
    EntityType,
    RelationshipType,
    VALID_RELATIONSHIPS,
    is_valid_relationship,
    validate_knowledge_graph_relationship,
    MAX_RELATIONSHIPS_PER_ENTITY,
    MIN_RELATIONSHIP_CONFIDENCE,
)

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION RESULT STRUCTURES
# ============================================================================

class ValidationStatus(str, Enum):
    """Validation status for entities and relationships"""
    VALID = "valid"
    INVALID_TYPE = "invalid_type"
    INVALID_RELATIONSHIP = "invalid_relationship"
    MALFORMED = "malformed"
    DUPLICATE = "duplicate"
    BELOW_CONFIDENCE = "below_confidence"


@dataclass
class EntityValidationResult:
    """Result of entity validation"""
    entity_name: str
    entity_type: str
    status: ValidationStatus
    error_message: Optional[str] = None
    original_data: Optional[Dict[str, Any]] = None


@dataclass
class RelationshipValidationResult:
    """Result of relationship validation"""
    source_entity: str
    target_entity: str
    relationship_type: str
    status: ValidationStatus
    error_message: Optional[str] = None
    original_data: Optional[Dict[str, Any]] = None


@dataclass
class KnowledgeGraphValidationReport:
    """Complete validation report for knowledge graph"""
    total_entities: int
    valid_entities: int
    invalid_entities: int
    total_relationships: int
    valid_relationships: int
    invalid_relationships: int
    entity_results: List[EntityValidationResult]
    relationship_results: List[RelationshipValidationResult]
    
    def get_validation_summary(self) -> str:
        """Get human-readable validation summary"""
        return (
            f"Validation Summary:\n"
            f"  Entities: {self.valid_entities}/{self.total_entities} valid "
            f"({self.invalid_entities} invalid)\n"
            f"  Relationships: {self.valid_relationships}/{self.total_relationships} valid "
            f"({self.invalid_relationships} invalid)"
        )
    
    def get_error_report(self) -> str:
        """Get detailed error report for invalid items"""
        lines = ["Validation Errors:"]
        
        # Entity errors
        entity_errors = [e for e in self.entity_results if e.status != ValidationStatus.VALID]
        if entity_errors:
            lines.append(f"\n  Invalid Entities ({len(entity_errors)}):")
            for error in entity_errors[:10]:  # Limit to first 10
                lines.append(f"    - {error.entity_name} ({error.entity_type}): {error.error_message}")
        
        # Relationship errors
        rel_errors = [r for r in self.relationship_results if r.status != ValidationStatus.VALID]
        if rel_errors:
            lines.append(f"\n  Invalid Relationships ({len(rel_errors)}):")
            for error in rel_errors[:10]:  # Limit to first 10
                lines.append(
                    f"    - {error.source_entity} -{error.relationship_type}-> "
                    f"{error.target_entity}: {error.error_message}"
                )
        
        return "\n".join(lines)


# ============================================================================
# ENTITY VALIDATION
# ============================================================================

def validate_entity_type(entity_name: str, entity_type: str) -> EntityValidationResult:
    """
    Validate that an entity type matches our government contracting ontology.
    
    Checks if entity_type is a valid member of EntityType enum. Prevents LightRAG
    from creating arbitrary entity types not in our domain model.
    
    Args:
        entity_name: Name of the entity (e.g., "Section L.3.2", "CLIN 0001")
        entity_type: Type claimed by extraction (e.g., "SECTION", "CONCEPT")
    
    Returns:
        EntityValidationResult with validation status and error details
    
    Example:
        >>> validate_entity_type("Section L.3.2", "SECTION")
        EntityValidationResult(entity_name="Section L.3.2", entity_type="SECTION", 
                              status=ValidationStatus.VALID)
        
        >>> validate_entity_type("Section L.3.2", "INVALID_TYPE")
        EntityValidationResult(entity_name="Section L.3.2", entity_type="INVALID_TYPE",
                              status=ValidationStatus.INVALID_TYPE, 
                              error_message="Entity type 'INVALID_TYPE' not in ontology...")
    """
    # Normalize entity type to uppercase for comparison
    normalized_type = entity_type.upper()
    
    # Check if entity type exists in our ontology
    valid_types = [et.value for et in EntityType]
    
    if normalized_type not in valid_types:
        return EntityValidationResult(
            entity_name=entity_name,
            entity_type=entity_type,
            status=ValidationStatus.INVALID_TYPE,
            error_message=(
                f"Entity type '{entity_type}' not in ontology. "
                f"Valid types: {', '.join(valid_types)}"
            )
        )
    
    return EntityValidationResult(
        entity_name=entity_name,
        entity_type=normalized_type,
        status=ValidationStatus.VALID
    )


def validate_entity_name_format(entity_name: str, entity_type: str) -> EntityValidationResult:
    """
    Validate entity name format against government contracting conventions.
    
    Checks for:
    - Section format: "Section X.Y.Z" (not "RFP Section J-L" - Path A regression check)
    - CLIN format: "CLIN XXXX"
    - Clause format: "FAR X.XXX-X" or "DFARS XXX.XXX-XX"
    - Non-empty names
    
    Args:
        entity_name: Name to validate
        entity_type: Entity type context
    
    Returns:
        EntityValidationResult with validation status
    """
    # Check for empty or whitespace-only names
    if not entity_name or not entity_name.strip():
        return EntityValidationResult(
            entity_name=entity_name,
            entity_type=entity_type,
            status=ValidationStatus.MALFORMED,
            error_message="Entity name is empty or whitespace-only"
        )
    
    # Check for Path A regression: fictitious combined sections like "RFP Section J-L"
    if entity_type == "SECTION":
        if "-" in entity_name and "Section" in entity_name:
            # Check if it looks like "Section A-B" or "Section J-L" (invalid combined sections)
            import re
            if re.search(r'Section\s+[A-Z]-[A-Z]', entity_name, re.IGNORECASE):
                return EntityValidationResult(
                    entity_name=entity_name,
                    entity_type=entity_type,
                    status=ValidationStatus.MALFORMED,
                    error_message=(
                        "Invalid combined section format (Path A regression). "
                        "Use specific sections like 'Section L.3.2', not 'Section J-L'"
                    )
                )
    
    # Check CLIN format
    if entity_type == "CONCEPT" and "CLIN" in entity_name.upper():
        import re
        if not re.match(r'CLIN\s+\d{4}', entity_name, re.IGNORECASE):
            logger.warning(f"CLIN format may be non-standard: {entity_name}")
    
    return EntityValidationResult(
        entity_name=entity_name,
        entity_type=entity_type,
        status=ValidationStatus.VALID
    )


def validate_entities(entities: List[Dict[str, Any]]) -> List[EntityValidationResult]:
    """
    Validate a list of entities extracted by LightRAG.
    
    Performs both type validation and format validation for each entity.
    
    Args:
        entities: List of entity dictionaries with 'entity_name' and 'entity_type' keys
    
    Returns:
        List of EntityValidationResult objects
    
    Example:
        >>> entities = [
        ...     {"entity_name": "Section L.3.2", "entity_type": "SECTION"},
        ...     {"entity_name": "Invalid Entity", "entity_type": "FAKE_TYPE"}
        ... ]
        >>> results = validate_entities(entities)
        >>> valid_results = [r for r in results if r.status == ValidationStatus.VALID]
    """
    results = []
    seen_entities = set()
    
    for entity in entities:
        entity_name = entity.get("entity_name", "")
        entity_type = entity.get("entity_type", "")
        
        # Check for duplicates
        entity_key = (entity_name.lower(), entity_type.upper())
        if entity_key in seen_entities:
            results.append(EntityValidationResult(
                entity_name=entity_name,
                entity_type=entity_type,
                status=ValidationStatus.DUPLICATE,
                error_message="Duplicate entity",
                original_data=entity
            ))
            continue
        seen_entities.add(entity_key)
        
        # Validate type
        type_result = validate_entity_type(entity_name, entity_type)
        if type_result.status != ValidationStatus.VALID:
            type_result.original_data = entity
            results.append(type_result)
            continue
        
        # Validate format
        format_result = validate_entity_name_format(entity_name, entity_type)
        format_result.original_data = entity
        results.append(format_result)
    
    return results


# ============================================================================
# RELATIONSHIP VALIDATION
# ============================================================================

def validate_relationship(
    source_entity: str,
    source_type: str,
    relationship_type: str,
    target_entity: str,
    target_type: str,
    confidence: Optional[float] = None
) -> RelationshipValidationResult:
    """
    Validate a relationship against VALID_RELATIONSHIPS schema.
    
    Uses ontology.is_valid_relationship() to check if the relationship pattern
    is allowed in government contracting domain.
    
    Args:
        source_entity: Source entity name
        source_type: Source entity type
        relationship_type: Relationship type
        target_entity: Target entity name
        target_type: Target entity type
        confidence: Optional confidence score (0.0-1.0)
    
    Returns:
        RelationshipValidationResult with validation status
    
    Example:
        >>> validate_relationship(
        ...     "Section L.3.2", "SECTION", "REFERENCES", "REQ-001", "REQUIREMENT"
        ... )
        RelationshipValidationResult(status=ValidationStatus.VALID, ...)
    """
    # Check confidence threshold if provided
    if confidence is not None and confidence < MIN_RELATIONSHIP_CONFIDENCE:
        return RelationshipValidationResult(
            source_entity=source_entity,
            target_entity=target_entity,
            relationship_type=relationship_type,
            status=ValidationStatus.BELOW_CONFIDENCE,
            error_message=f"Confidence {confidence:.2f} below threshold {MIN_RELATIONSHIP_CONFIDENCE}"
        )
    
    # Validate using ontology schema
    is_valid, error_msg = validate_knowledge_graph_relationship(
        source_entity, source_type, relationship_type, target_entity, target_type
    )
    
    if not is_valid:
        return RelationshipValidationResult(
            source_entity=source_entity,
            target_entity=target_entity,
            relationship_type=relationship_type,
            status=ValidationStatus.INVALID_RELATIONSHIP,
            error_message=error_msg
        )
    
    return RelationshipValidationResult(
        source_entity=source_entity,
        target_entity=target_entity,
        relationship_type=relationship_type,
        status=ValidationStatus.VALID
    )


def validate_relationships(
    relationships: List[Dict[str, Any]],
    entity_types: Dict[str, str]
) -> List[RelationshipValidationResult]:
    """
    Validate a list of relationships extracted by LightRAG.
    
    Args:
        relationships: List of relationship dictionaries with 'source_entity', 
                      'target_entity', and 'relationship_type' keys
        entity_types: Dictionary mapping entity names to their types
    
    Returns:
        List of RelationshipValidationResult objects
    
    Example:
        >>> relationships = [
        ...     {
        ...         "source_entity": "Section L",
        ...         "target_entity": "Section M",
        ...         "relationship_type": "REFERENCES"
        ...     }
        ... ]
        >>> entity_types = {"Section L": "SECTION", "Section M": "SECTION"}
        >>> results = validate_relationships(relationships, entity_types)
    """
    results = []
    seen_relationships = set()
    
    for rel in relationships:
        source_entity = rel.get("source_entity", "")
        target_entity = rel.get("target_entity", "")
        relationship_type = rel.get("relationship_type", "")
        confidence = rel.get("confidence")
        
        # Look up entity types
        source_type = entity_types.get(source_entity, "UNKNOWN")
        target_type = entity_types.get(target_entity, "UNKNOWN")
        
        # Check for duplicates (treat relationships as undirected)
        rel_key = tuple(sorted([source_entity.lower(), target_entity.lower()]) + 
                       [relationship_type.upper()])
        if rel_key in seen_relationships:
            results.append(RelationshipValidationResult(
                source_entity=source_entity,
                target_entity=target_entity,
                relationship_type=relationship_type,
                status=ValidationStatus.DUPLICATE,
                error_message="Duplicate relationship",
                original_data=rel
            ))
            continue
        seen_relationships.add(rel_key)
        
        # Validate relationship
        result = validate_relationship(
            source_entity, source_type, relationship_type, target_entity, target_type, confidence
        )
        result.original_data = rel
        results.append(result)
    
    return results


# ============================================================================
# KNOWLEDGE GRAPH FILTERING
# ============================================================================

def filter_knowledge_graph(
    entities: List[Dict[str, Any]],
    relationships: List[Dict[str, Any]],
    remove_invalid: bool = True,
    log_errors: bool = True
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], KnowledgeGraphValidationReport]:
    """
    Filter LightRAG knowledge graph to remove invalid entities and relationships.
    
    Primary entry point for post-processing LightRAG extraction results.
    Validates both entities and relationships, removes invalid items if requested,
    and generates comprehensive validation report.
    
    Args:
        entities: List of entity dictionaries from LightRAG
        relationships: List of relationship dictionaries from LightRAG
        remove_invalid: If True, filter out invalid items; if False, keep all but report
        log_errors: If True, log validation errors to logger
    
    Returns:
        Tuple of (filtered_entities, filtered_relationships, validation_report)
    
    Example:
        >>> # After LightRAG extraction
        >>> entities = lightrag_extract_entities(text)
        >>> relationships = lightrag_extract_relationships(text)
        >>> 
        >>> # Validate and filter with ontology
        >>> clean_entities, clean_rels, report = filter_knowledge_graph(
        ...     entities, relationships
        ... )
        >>> print(report.get_validation_summary())
    """
    # Validate entities
    entity_results = validate_entities(entities)
    
    # Build entity type lookup for relationship validation
    entity_types = {}
    for entity in entities:
        entity_name = entity.get("entity_name", "")
        entity_type = entity.get("entity_type", "").upper()
        entity_types[entity_name] = entity_type
    
    # Validate relationships
    relationship_results = validate_relationships(relationships, entity_types)
    
    # Filter results if requested
    if remove_invalid:
        # Keep only valid entities
        valid_entity_names = {
            r.entity_name for r in entity_results 
            if r.status == ValidationStatus.VALID
        }
        filtered_entities = [
            e for e in entities 
            if e.get("entity_name") in valid_entity_names
        ]
        
        # Keep only valid relationships where both entities are valid
        valid_relationship_indices = {
            i for i, r in enumerate(relationship_results)
            if (r.status == ValidationStatus.VALID and
                r.source_entity in valid_entity_names and
                r.target_entity in valid_entity_names)
        }
        filtered_relationships = [
            r for i, r in enumerate(relationships)
            if i in valid_relationship_indices
        ]
    else:
        filtered_entities = entities
        filtered_relationships = relationships
    
    # Generate report
    report = KnowledgeGraphValidationReport(
        total_entities=len(entities),
        valid_entities=sum(1 for r in entity_results if r.status == ValidationStatus.VALID),
        invalid_entities=sum(1 for r in entity_results if r.status != ValidationStatus.VALID),
        total_relationships=len(relationships),
        valid_relationships=sum(1 for r in relationship_results if r.status == ValidationStatus.VALID),
        invalid_relationships=sum(1 for r in relationship_results if r.status != ValidationStatus.VALID),
        entity_results=entity_results,
        relationship_results=relationship_results
    )
    
    # Log errors if requested
    if log_errors and (report.invalid_entities > 0 or report.invalid_relationships > 0):
        logger.warning(report.get_validation_summary())
        logger.debug(report.get_error_report())
    
    return filtered_entities, filtered_relationships, report


# ============================================================================
# ENTITY CLEANUP UTILITIES
# ============================================================================

def deduplicate_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Remove duplicate entities based on name and type.
    
    Keeps first occurrence of each unique (name, type) pair.
    """
    seen = set()
    deduplicated = []
    
    for entity in entities:
        name = entity.get("entity_name", "").lower()
        etype = entity.get("entity_type", "").upper()
        key = (name, etype)
        
        if key not in seen:
            seen.add(key)
            deduplicated.append(entity)
    
    return deduplicated


def limit_entity_relationships(
    relationships: List[Dict[str, Any]],
    max_per_entity: int = MAX_RELATIONSHIPS_PER_ENTITY
) -> List[Dict[str, Any]]:
    """
    Limit number of relationships per entity to prevent explosion.
    
    Keeps relationships with highest confidence scores (if available).
    """
    # Count relationships per entity
    entity_rel_count: Dict[str, int] = {}
    limited_relationships = []
    
    # Sort by confidence if available (highest first)
    sorted_rels = sorted(
        relationships,
        key=lambda r: r.get("confidence", 0.5),
        reverse=True
    )
    
    for rel in sorted_rels:
        source = rel.get("source_entity", "")
        target = rel.get("target_entity", "")
        
        # Check limits for both source and target
        source_count = entity_rel_count.get(source, 0)
        target_count = entity_rel_count.get(target, 0)
        
        if source_count < max_per_entity and target_count < max_per_entity:
            limited_relationships.append(rel)
            entity_rel_count[source] = source_count + 1
            entity_rel_count[target] = target_count + 1
        else:
            logger.debug(
                f"Relationship limit reached for {source} or {target}, "
                f"skipping: {source} -> {target}"
            )
    
    return limited_relationships


# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

__all__ = [
    # Validation status
    'ValidationStatus',
    
    # Result structures
    'EntityValidationResult',
    'RelationshipValidationResult',
    'KnowledgeGraphValidationReport',
    
    # Entity validation
    'validate_entity_type',
    'validate_entity_name_format',
    'validate_entities',
    
    # Relationship validation
    'validate_relationship',
    'validate_relationships',
    
    # Knowledge graph filtering (primary entry point)
    'filter_knowledge_graph',
    
    # Utilities
    'deduplicate_entities',
    'limit_entity_relationships',
]
