from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator
import logging

logger = logging.getLogger(__name__)

# ==========================================
# Core Enums (The "Rules" of the Ontology)
# ==========================================

CriticalityLevel = Literal["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"]
RequirementType = Literal["FUNCTIONAL", "PERFORMANCE", "SECURITY", "TECHNICAL", "INTERFACE", "MANAGEMENT", "DESIGN", "QUALITY", "OTHER"]
ThemeType = Literal["CUSTOMER_HOT_BUTTON", "DISCRIMINATOR", "PROOF_POINT", "WIN_THEME"]
EntityType = Literal[
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
]

# ==========================================
# Base Entity Model
# ==========================================

class BaseEntity(BaseModel):
    entity_name: str = Field(..., description="The canonical name of the entity (Title Case).")
    entity_type: EntityType = Field(..., description="The strict entity type from the government contracting ontology.")

    @model_validator(mode='after')
    def clean_entity_name(self):
        """
        Clean entity name by removing leading '#' characters often added by Grok.
        """
        if self.entity_name:
            # Strip leading '#' and whitespace
            cleaned_name = self.entity_name.lstrip('#').strip()
            if cleaned_name != self.entity_name:
                self.entity_name = cleaned_name
        return self

# ==========================================
# Specialized Entity Models
# ==========================================

class Requirement(BaseEntity):
    entity_type: Literal["requirement"] = "requirement"
    criticality: CriticalityLevel = Field(..., description="MANDATORY (shall), IMPORTANT (should), OPTIONAL (may).")
    modal_verb: str = Field(..., description="The exact verb used (shall, must, will, should, may).")
    req_type: RequirementType = Field("OTHER", description="Functional classification of the requirement.")
    # Workload specific fields (captured upfront!)
    labor_drivers: List[str] = Field(default_factory=list, description="Raw workload data (volumes, frequencies, shifts, quantities, customer counts) that drive staffing requirements. NOT staffing roles.")
    material_needs: List[str] = Field(default_factory=list, description="List of equipment, supplies, or facilities mentioned.")

class EvaluationFactor(BaseEntity):
    entity_type: Literal["evaluation_factor"] = "evaluation_factor"
    weight: Optional[str] = Field(None, description="Numerical weight (e.g., '40%', '25 points').")
    importance: Optional[str] = Field(None, description="Relative importance (e.g., 'Most Important').")
    subfactors: List[str] = Field(default_factory=list, description="List of sub-criteria or subfactors.")

class SubmissionInstruction(BaseEntity):
    entity_type: Literal["submission_instruction"] = "submission_instruction"
    page_limit: Optional[str] = Field(None, description="Page count constraints.")
    format_reqs: Optional[str] = Field(None, description="Font, margin, or file format requirements.")
    volume: Optional[str] = Field(None, description="The proposal volume this applies to (e.g., 'Volume I').")

class StrategicTheme(BaseEntity):
    entity_type: Literal["strategic_theme"] = "strategic_theme"
    theme_type: ThemeType = Field(..., description="Classification of the strategic element.")

class Clause(BaseEntity):
    entity_type: Literal["clause"] = "clause"
    clause_number: str = Field(..., description="The FAR/DFARS citation (e.g., 'FAR 52.212-1').")
    regulation: str = Field(..., description="FAR, DFARS, AFFARS, etc.")

class PerformanceMetric(BaseEntity):
    entity_type: Literal["performance_metric"] = "performance_metric"
    threshold: str = Field(..., description="The specific value/limit (e.g., '99.9%', '< 2 errors').")
    measurement_method: Optional[str] = Field(None, description="How the metric is calculated or inspected.")

# ==========================================
# Relationship Model
# ==========================================

class Relationship(BaseModel):
    source_entity: BaseEntity = Field(..., description="Full source entity object with entity_name and entity_type.")
    target_entity: BaseEntity = Field(..., description="Full target entity object with entity_name and entity_type.")
    relationship_type: str = Field(..., description="Type of relationship (e.g., EVALUATED_BY, GUIDES, CHILD_OF, ATTACHMENT_OF, PRODUCES).")

# ==========================================
# Container for LLM Output
# ==========================================

class ExtractionResult(BaseModel):
    """The root object expected from the LLM."""
    entities: List[
        Requirement | EvaluationFactor | SubmissionInstruction | 
        StrategicTheme | Clause | PerformanceMetric | BaseEntity
    ] = Field(..., description="List of all extracted entities.")
    relationships: List[Relationship] = Field(default_factory=list, description="List of relationships between entities.")

    @model_validator(mode='after')
    def validate_relationships(self):
        """
        Ensure that every relationship points to a valid entity name.
        Drops relationships that point to non-existent entities (Ghost Nodes).
        """
        # Create a set of all valid entity names (normalized)
        valid_names = {e.entity_name.strip().lower() for e in self.entities if e.entity_name}
        
        valid_relationships = []
        dropped_count = 0
        
        for rel in self.relationships:
            # Now using entity objects instead of strings
            source = rel.source_entity.entity_name.strip().lower()
            target = rel.target_entity.entity_name.strip().lower()
            
            if source in valid_names and target in valid_names:
                valid_relationships.append(rel)
            else:
                dropped_count += 1
                # Optional: Log detailed warning if needed, but keep schema clean
                # logger.warning(f"Dropping ghost relationship: {rel.source_entity.entity_name} -> {rel.target_entity.entity_name}")
        
        if dropped_count > 0:
            # We can't easily log from inside a model validator without a logger instance, 
            # but the dropped count will be reflected in the final list length.
            pass
            
        self.relationships = valid_relationships
        return self
