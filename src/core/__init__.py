"""
Core LightRAG Integration Module (Phase 2+3)

Contains the core components for ontology-modified LightRAG integration:
- Ontology configuration (entity types, relationships)
- Ontology-guided prompts for LightRAG extraction
- Post-processing validation for knowledge graphs
- LightRAG integration with ontology injection

Phase 1 (archived): ShipleyRFPChunker removed - Path A archived
Phase 2: Ontology injection via addon_params, prompt override, validation
Phase 3: DELIVERABLE entity type added
"""

# Import ontology components
from .ontology import (
    EntityType,
    RelationshipType,
    VALID_RELATIONSHIPS,
    is_valid_relationship,
)

# Import prompts
from .lightrag_prompts import (
    get_government_contracting_entity_types,
    get_rfp_entity_extraction_examples,
    get_ontology_addon_params,
)

# Import validation
from .ontology_validation import (
    filter_knowledge_graph,
    validate_entities,
    validate_relationships,
)

# Import integration
from .lightrag_integration import (
    create_ontology_modified_lightrag,
    validate_lightrag_extraction,
)

__all__ = [
    # Ontology
    'EntityType',
    'RelationshipType',
    'VALID_RELATIONSHIPS',
    'is_valid_relationship',
    
    # Prompts
    'get_government_contracting_entity_types',
    'get_rfp_entity_extraction_examples',
    'get_ontology_addon_params',
    
    # Validation
    'filter_knowledge_graph',
    'validate_entities',
    'validate_relationships',
    
    # Integration
    'create_ontology_modified_lightrag',
    'validate_lightrag_extraction',
]