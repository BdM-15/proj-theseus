from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, model_validator
import logging

logger = logging.getLogger(__name__)

# ==========================================
# Core Ontology (Simplified for LightRAG)
# ==========================================

# 13 Core Entity Types
VALID_ENTITY_TYPES = {
    # General
    "organization", "person", "location", "document", "section",
    
    # GovCon / Shipley Specific
    "opportunity", 
    "rfp_requirement",  # Consolidates requirement, SOW, tech specs
    "compliance_item",  # Clauses, specific constraints
    "win_theme",        # Strategic themes, discriminators
    "risk",
    "competitor",
    "deliverable",      # CDRLs, outputs
    "shipley_phase"     # Pursuit, Capture, Proposal, Review
}

EntityType = Literal[
    "organization", "person", "location", "document", "section",
    "opportunity", "rfp_requirement", "compliance_item", "win_theme",
    "risk", "competitor", "deliverable", "shipley_phase"
]

# ==========================================
# Base Entity Model
# ==========================================

class BaseEntity(BaseModel):
    entity_name: str = Field(..., description="The canonical name of the entity (Title Case).")
    entity_type: EntityType = Field(..., description="The entity type from the simplified ontology.")
    description: str = Field(default="", description="Comprehensive description of the entity and its context.")
    
    # Flexible metadata dict to capture granular details (workload, volumes, etc.) without strict schema
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Flexible key-value pairs for specific details (e.g., volume, frequency, weight).")

    @model_validator(mode='before')
    @classmethod
    def validate_entity_type(cls, values):
        """
        Validate entity_type. Coerces invalid types to 'document' or 'section' 
        if possible, otherwise 'organization' or generic fallback.
        """
        if isinstance(values, dict):
            entity_type = values.get('entity_type', '').lower()
            if entity_type and entity_type not in VALID_ENTITY_TYPES:
                # Simple mapping for legacy/other types
                mapping = {
                    "submission_instruction": "rfp_requirement",
                    "statement_of_work": "rfp_requirement",
                    "evaluation_factor": "compliance_item",
                    "clause": "compliance_item",
                    "program": "opportunity",
                    "concept": "win_theme", # or generic
                    "technology": "win_theme", # or generic
                    "equipment": "rfp_requirement",
                    "performance_metric": "rfp_requirement"
                }
                
                new_type = mapping.get(entity_type, "document") # Fallback
                logger.warning(f"Coercing entity type '{entity_type}' to '{new_type}'")
                values['entity_type'] = new_type
            elif entity_type:
                values['entity_type'] = entity_type
                
        return values

    @model_validator(mode='after')
    def clean_entity_name(self):
        if self.entity_name:
            self.entity_name = self.entity_name.lstrip('#').strip()
        return self

# ==========================================
# Relationship Model
# ==========================================

class Relationship(BaseModel):
    source_entity: BaseEntity = Field(..., description="Source entity.")
    target_entity: BaseEntity = Field(..., description="Target entity.")
    relationship_type: str = Field(..., description="Type of relationship (e.g., HAS_REQUIREMENT, ADDRESSES_RISK).")
    description: Optional[str] = Field(None, description="Contextual description of the relationship.")

# ==========================================
# Container for LLM Output
# ==========================================

class ExtractionResult(BaseModel):
    """The root object expected from the LLM."""
    entities: List[BaseEntity] = Field(..., description="List of extracted entities.")
    relationships: List[Relationship] = Field(default_factory=list, description="List of relationships.")

    @model_validator(mode='after')
    def validate_relationships(self):
        # Basic consistency check - ensured by flexible schema
        return self
