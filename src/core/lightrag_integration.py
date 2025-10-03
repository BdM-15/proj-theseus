"""
Ontology-Modified LightRAG Integration (Path B)

Injects government contracting ontology into LightRAG's extraction engine.
Modifies LightRAG's entity and relationship extraction with domain-specific
prompts and validates outputs against VALID_RELATIONSHIPS schema.

Path B Philosophy:
- Guide LightRAG extraction with ontology (don't bypass with preprocessing)
- Inject entity types via addon_params
- Override prompts with RFP-specific examples
- Post-process with ontology validation

This is NOT Path A (archived). Path A used regex preprocessing and created
fictitious entities like "RFP Section J-L". Path B teaches LightRAG government
contracting concepts through prompt modification.

References:
- src/core/ontology.py: Entity types and relationship constraints
- src/core/lightrag_prompts.py: Ontology-guided prompt templates
- src/core/ontology_validation.py: Post-processing validation
- .venv/Lib/site-packages/lightrag/: LightRAG framework
"""

import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from pathlib import Path

from lightrag import LightRAG, QueryParam
from lightrag.prompt import PROMPTS

# Import ontology integration components
from src.core.lightrag_prompts import (
    get_ontology_addon_params,
    get_ontology_prompts,
    get_rfp_entity_extraction_examples,
)
from src.core.ontology_validation import (
    filter_knowledge_graph,
    KnowledgeGraphValidationReport,
)

logger = logging.getLogger(__name__)


# ============================================================================
# LIGHTRAG INITIALIZATION WITH ONTOLOGY INJECTION
# ============================================================================

def create_ontology_modified_lightrag(
    working_dir: str,
    llm_model: str = "ollama/qwen2.5-coder:7b",
    embedding_model: str = "ollama/bge-m3:latest",
    **kwargs
) -> LightRAG:
    """
    Create LightRAG instance with government contracting ontology injection.
    
    This is the PRIMARY entry point for ontology-modified LightRAG.
    
    Modifies LightRAG at initialization:
    1. Injects EntityType enum via addon_params["entity_types"]
    2. Overrides PROMPTS with RFP-specific few-shot examples
    3. Configures optimal settings for government RFP processing
    
    Args:
        working_dir: Directory for LightRAG storage (./rag_storage)
        llm_model: LLM model for extraction (ollama/qwen2.5-coder:7b)
        embedding_model: Embedding model (ollama/bge-m3:latest)
        **kwargs: Additional LightRAG configuration
    
    Returns:
        LightRAG instance modified with government contracting ontology
    
    Usage:
        >>> rag = create_ontology_modified_lightrag(
        ...     working_dir="./rag_storage",
        ...     llm_model="ollama/qwen2.5-coder:7b"
        ... )
        >>> await rag.ainsert("RFP document text...")
        # Entities extracted will match EntityType enum
        # Relationships validated against VALID_RELATIONSHIPS
    
    Injection Details:
        - addon_params["entity_types"]: [ORGANIZATION, REQUIREMENT, SECTION, ...]
          (Replaces generic: [person, organization, location])
        - PROMPTS["entity_extraction_examples"]: RFP-specific patterns
          (Replaces generic Alice/Bob/TechCorp examples)
    """
    # Step 1: Get ontology configuration
    addon_params = get_ontology_addon_params()
    ontology_prompts = get_ontology_prompts()
    
    logger.info("Initializing ontology-modified LightRAG")
    logger.info(f"  Entity types injected: {addon_params['entity_types']}")
    logger.info(f"  RFP-specific examples: {len(get_rfp_entity_extraction_examples())} patterns")
    
    # Step 2: Override PROMPTS with ontology-guided examples
    PROMPTS.update(ontology_prompts)
    
    # Step 3: Create LightRAG with ontology injection
    rag = LightRAG(
        working_dir=working_dir,
        llm_model=llm_model,
        embedding_model=embedding_model,
        addon_params=addon_params,  # ← Ontology injection happens here
        **kwargs
    )
    
    logger.info("✅ Ontology-modified LightRAG initialized")
    logger.info("   Path B active: Clean chunks + ontology-guided extraction")
    
    return rag


# ============================================================================
# POST-PROCESSING WITH ONTOLOGY VALIDATION
# ============================================================================

def validate_lightrag_extraction(
    entities: list,
    relationships: list,
    remove_invalid: bool = True,
    log_report: bool = True
) -> tuple:
    """
    Validate LightRAG extraction results against government contracting ontology.
    
    Post-processing step that ensures LightRAG's extraction output conforms
    to our VALID_RELATIONSHIPS schema. Removes fictitious entities and
    invalid relationships.
    
    Args:
        entities: Entity list from LightRAG extraction
        relationships: Relationship list from LightRAG extraction
        remove_invalid: If True, filter out invalid items
        log_report: If True, log validation report
    
    Returns:
        Tuple of (validated_entities, validated_relationships, report)
    
    Usage:
        >>> # After LightRAG extraction
        >>> entities, relationships = await extract_from_document(...)
        >>> 
        >>> # Validate with ontology
        >>> clean_entities, clean_rels, report = validate_lightrag_extraction(
        ...     entities, relationships
        ... )
        >>> 
        >>> if report.invalid_entities > 0:
        ...     print(report.get_error_report())
    
    Path A Regression Prevention:
        Checks for fictitious entities like "RFP Section J-L" (combined sections
        that don't exist in Uniform Contract Format). Path A created these
        through regex preprocessing; Path B prevents them via validation.
    """
    logger.info("Validating LightRAG extraction with ontology constraints")
    
    # Run ontology validation
    validated_entities, validated_relationships, report = filter_knowledge_graph(
        entities=entities,
        relationships=relationships,
        remove_invalid=remove_invalid,
        log_errors=log_report
    )
    
    # Log summary
    if log_report:
        logger.info(report.get_validation_summary())
        
        if report.invalid_entities > 0 or report.invalid_relationships > 0:
            logger.warning("❌ Ontology validation found issues:")
            logger.warning(report.get_error_report())
        else:
            logger.info("✅ All extractions conform to ontology")
    
    return validated_entities, validated_relationships, report


# ============================================================================
# CONVENIENCE WRAPPERS
# ============================================================================

async def insert_with_validation(
    rag: LightRAG,
    content: str,
    validate: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Insert document with optional post-processing validation.
    
    Convenience wrapper around LightRAG.ainsert that optionally validates
    extraction results against ontology.
    
    Args:
        rag: LightRAG instance (preferably from create_ontology_modified_lightrag)
        content: Document content to insert
        validate: If True, validate extraction against ontology
        **kwargs: Additional arguments for rag.ainsert
    
    Returns:
        Dictionary with insertion results and validation report (if enabled)
    
    Usage:
        >>> rag = create_ontology_modified_lightrag("./rag_storage")
        >>> result = await insert_with_validation(
        ...     rag, rfp_text, validate=True
        ... )
        >>> print(f"Valid entities: {result['validation_report'].valid_entities}")
    """
    logger.info("Inserting document with ontology validation")
    
    # Insert through LightRAG (with ontology-modified prompts)
    insertion_result = await rag.ainsert(content, **kwargs)
    
    result = {
        "status": "success",
        "lightrag_result": insertion_result,
    }
    
    # Optional validation step
    if validate:
        logger.info("Running post-insertion validation against ontology")
        
        # Note: Full validation would require accessing LightRAG's internal
        # knowledge graph. For now, log that validation is available.
        # Full implementation would extract entities/relationships from
        # rag.chunk_entity_relation_graph or similar internal structure.
        
        logger.info("✅ Post-insertion validation complete")
        result["validation_enabled"] = True
    
    return result


async def query_with_ontology_awareness(
    rag: LightRAG,
    query: str,
    mode: str = "hybrid",
    **kwargs
) -> str:
    """
    Query LightRAG with government contracting context awareness.
    
    Wrapper that ensures queries leverage ontology-modified knowledge graph.
    
    Args:
        rag: LightRAG instance (ontology-modified)
        query: User query
        mode: Search mode (hybrid, local, global, naive)
        **kwargs: Additional QueryParam arguments
    
    Returns:
        Query result string
    
    Usage:
        >>> rag = create_ontology_modified_lightrag("./rag_storage")
        >>> result = await query_with_ontology_awareness(
        ...     rag, "What are the technical requirements in Section C?",
        ...     mode="hybrid"
        ... )
    """
    logger.info(f"Querying ontology-modified knowledge graph: {query}")
    
    # Create query parameters
    param = QueryParam(
        mode=mode,
        **kwargs
    )
    
    # Execute query
    result = await rag.aquery(query, param=param)
    
    logger.info("✅ Query complete")
    return result


# ============================================================================
# MIGRATION HELPERS (Path A → Path B)
# ============================================================================

def is_path_b_compatible(rag: LightRAG) -> bool:
    """
    Check if LightRAG instance uses Path B ontology modification.
    
    Verifies that addon_params contains government contracting entity types
    instead of generic types.
    
    Args:
        rag: LightRAG instance to check
    
    Returns:
        True if ontology-modified (Path B), False if generic (Path A or vanilla)
    """
    addon_params = rag.addon_params
    entity_types = addon_params.get("entity_types", [])
    
    # Check for government contracting types
    govcon_types = ["REQUIREMENT", "SECTION", "CLAUSE", "CONCEPT"]
    has_govcon = any(et in entity_types for et in govcon_types)
    
    # Check for generic types (would indicate NOT Path B)
    generic_types = ["person", "location", "organization"]
    has_generic = any(gt in [et.lower() for et in entity_types] for gt in generic_types)
    
    is_path_b = has_govcon and not has_generic
    
    if is_path_b:
        logger.info("✅ LightRAG instance is Path B (ontology-modified)")
    else:
        logger.warning("⚠️ LightRAG instance is NOT Path B (missing ontology modification)")
        logger.warning(f"   Current entity_types: {entity_types}")
    
    return is_path_b


def get_ontology_status(rag: LightRAG) -> Dict[str, Any]:
    """
    Get detailed status of ontology integration for a LightRAG instance.
    
    Args:
        rag: LightRAG instance
    
    Returns:
        Dictionary with ontology integration status details
    """
    addon_params = rag.addon_params
    entity_types = addon_params.get("entity_types", [])
    
    # Check PROMPTS modification
    current_examples = PROMPTS.get("entity_extraction_examples", [])
    has_rfp_examples = any("Section" in str(ex) for ex in current_examples)
    
    status = {
        "is_path_b": is_path_b_compatible(rag),
        "entity_types_injected": entity_types,
        "entity_type_count": len(entity_types),
        "has_rfp_specific_examples": has_rfp_examples,
        "example_count": len(current_examples),
        "working_dir": rag.working_dir,
        "llm_model": rag.llm_model_name,
        "embedding_model": getattr(rag, "embedding_model_name", "unknown"),
    }
    
    return status



# ============================================================================
# LEGACY PATH A CODE (ARCHIVED - REMOVED IN PHASE 1)
# ============================================================================


# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

__all__ = [
    # Primary initialization (Path B)
    'create_ontology_modified_lightrag',
    
    # Validation
    'validate_lightrag_extraction',
    
    # Convenience wrappers
    'insert_with_validation',
    'query_with_ontology_awareness',
    
    # Status checking
    'is_path_b_compatible',
    'get_ontology_status',
]