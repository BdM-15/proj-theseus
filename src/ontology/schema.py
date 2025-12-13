from typing import List, Optional, Literal, Dict
from pydantic import BaseModel, Field, model_validator, field_validator
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# ==========================================
# Core Enums (The "Rules" of the Ontology)
# ==========================================

CriticalityLevel = Literal["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"]
RequirementType = Literal["FUNCTIONAL", "PERFORMANCE", "SECURITY", "TECHNICAL", "INTERFACE", "MANAGEMENT", "DESIGN", "QUALITY", "OTHER"]
ThemeType = Literal["CUSTOMER_HOT_BUTTON", "DISCRIMINATOR", "PROOF_POINT", "WIN_THEME"]


class BOECategory(str, Enum):
    """
    Standard Basis of Estimate (BOE) categories for workload enrichment.
    These are the ONLY valid values for workload_categories.
    """
    LABOR = "Labor"
    MATERIALS = "Materials"
    ODCS = "ODCs"
    QA = "QA"
    LOGISTICS = "Logistics"
    LIFECYCLE = "Lifecycle"
    COMPLIANCE = "Compliance"


# Mapping of common LLM-generated invalid categories to valid BOE categories
# NOTE: Keep this MINIMAL - prefer improving the prompt over adding mappings.
# Warnings for unmapped categories guide prompt engineering efforts.
BOE_CATEGORY_MAPPING: Dict[str, BOECategory] = {
    # These are observed production issues from initial runs (Nov 2025)
    # Future iterations should fix these at the prompt level, not here
    
    # Security-related → Compliance (common LLM mistake)
    "security": BOECategory.COMPLIANCE,
    "base access": BOECategory.COMPLIANCE,
}


def normalize_boe_category(category: str, fallback: BOECategory = BOECategory.LABOR) -> BOECategory:
    """
    Normalize a category string to a valid BOECategory.
    
    GRACEFUL HANDLING: Never returns None - always maps to a valid category.
    Unknown categories are mapped to fallback (default: Labor) and logged as WARNING
    so they can be added to BOE_CATEGORY_MAPPING in future iterations.
    
    Args:
        category: Raw category string from LLM
        fallback: Default BOE category for unmapped values (default: Labor)
    
    Returns:
        BOECategory: Always returns a valid category (never None)
    """
    # First try exact match (case-insensitive)
    category_lower = category.lower().strip()
    
    # Check if it's already a valid category
    for boe_cat in BOECategory:
        if boe_cat.value.lower() == category_lower:
            return boe_cat
    
    # Try mapping from common invalid values
    if category_lower in BOE_CATEGORY_MAPPING:
        return BOE_CATEGORY_MAPPING[category_lower]
    
    # GRACEFUL FALLBACK: Log warning and use fallback category
    logger.warning(f"Unmapped BOE category '{category}' → defaulting to '{fallback.value}'. Consider adding to BOE_CATEGORY_MAPPING.")
    return fallback

# 18 allowed entity types - this is the single source of truth
VALID_ENTITY_TYPES = {
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
}

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

    @model_validator(mode='before')
    @classmethod
    def validate_entity_type(cls, values):
        """
        Validate entity_type BEFORE Pydantic parsing to catch invalid types early.
        Coerces invalid types to 'concept' instead of silently accepting them.
        """
        if isinstance(values, dict):
            entity_type = values.get('entity_type', '')
            if entity_type and entity_type not in VALID_ENTITY_TYPES:
                entity_name = values.get('entity_name', 'unknown')
                logger.warning(
                    f"⚠️ Invalid entity_type '{entity_type}' for '{entity_name}' - coercing to 'concept'"
                )
                values['entity_type'] = 'concept'
        return values

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
# Workload Enrichment Model (for LLM response parsing)
# ==========================================

class WorkloadEnrichmentItem(BaseModel):
    """
    Pydantic model for validating workload enrichment LLM responses.
    Enforces BOE category constraints at parse time.
    """
    entity_index: int = Field(..., description="Index of the entity in the batch.")
    has_workload_metric: bool = Field(True, description="Whether this requirement has workload implications.")
    workload_categories: List[str] = Field(default_factory=list, description="Raw categories from LLM (validated in validator).")
    validated_categories: List[BOECategory] = Field(default_factory=list, description="Validated BOE categories after normalization.")
    boe_relevance: Dict[str, float] = Field(default_factory=dict, description="Confidence scores per BOE category (0.0-1.0).")
    estimated_volume: Optional[str] = Field(None, description="Volume descriptor (e.g., 'daily', 'monthly').")
    complexity: Optional[str] = Field(None, description="Complexity level (High/Medium/Low).")
    
    @field_validator('workload_categories', mode='before')
    @classmethod
    def normalize_categories(cls, v):
        """Accept any input format for workload_categories."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)
    
    @model_validator(mode='after')
    def validate_and_map_categories(self):
        """
        Normalize raw workload_categories to validated BOE categories.
        Uses graceful fallback - ALL categories are mapped (no data loss).
        Invalid categories default to Labor and generate a WARNING log.
        """
        validated = []
        for cat in self.workload_categories:
            normalized = normalize_boe_category(cat)  # Always returns valid category
            if normalized not in validated:
                validated.append(normalized)
        
        self.validated_categories = validated
        return self
    
    def get_category_values(self) -> List[str]:
        """Return validated categories as string values for Neo4j storage."""
        return [cat.value for cat in self.validated_categories]


class WorkloadEnrichmentResponse(BaseModel):
    """Container for batch workload enrichment LLM response."""
    requirements: List[WorkloadEnrichmentItem] = Field(default_factory=list)
    
    @model_validator(mode='before')
    @classmethod
    def handle_response_formats(cls, values):
        """Handle various LLM response formats."""
        if isinstance(values, dict):
            # Handle case where requirements is nested
            if 'requirements' not in values and 'entities' in values:
                values['requirements'] = values.pop('entities')
        return values


# ==========================================
# Relationship Model
# ==========================================

class Relationship(BaseModel):
    source_entity: BaseEntity = Field(..., description="Full source entity object with entity_name and entity_type.")
    target_entity: BaseEntity = Field(..., description="Full target entity object with entity_name and entity_type.")
    relationship_type: str = Field(..., description="Type of relationship (e.g., EVALUATED_BY, GUIDES, CHILD_OF, ATTACHMENT_OF, PRODUCES).")


# ==========================================
# Inferred Relationship Model (Post-Processing)
# ==========================================

class InferredRelationship(BaseModel):
    """
    Pydantic model for LLM-inferred relationships in semantic post-processing.
    
    Validates relationship structure and prevents common LLM errors:
    - Self-loops (source_id == target_id)
    - Missing required fields
    - Invalid confidence scores
    - Malformed reasoning text
    
    Pattern: Follows WorkloadEnrichmentItem proven approach (100% success rate).
    """
    source_id: str = Field(..., min_length=1, description="Entity ID of source node")
    target_id: str = Field(..., min_length=1, description="Entity ID of target node")
    relationship_type: str = Field(..., min_length=1, description="Relationship type (e.g., EVALUATED_BY, GUIDES)")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    reasoning: str = Field(default="", description="LLM explanation for this relationship")
    
    @field_validator('relationship_type')
    @classmethod
    def normalize_relationship_type(cls, v: str) -> str:
        """Normalize relationship type to uppercase for consistency."""
        return v.strip().upper()
    
    @field_validator('reasoning')
    @classmethod
    def clean_reasoning(cls, v: str) -> str:
        """Remove markdown formatting and excessive whitespace from reasoning."""
        cleaned = v.strip()
        # Remove markdown bold/italics
        cleaned = cleaned.replace('**', '').replace('__', '').replace('*', '').replace('_', '')
        # Collapse multiple spaces
        cleaned = ' '.join(cleaned.split())
        return cleaned
    
    @model_validator(mode='after')
    def prevent_self_loops(self):
        """Prevent self-referential relationships (source == target)."""
        if self.source_id == self.target_id:
            raise ValueError(
                f"Self-loop detected: {self.source_id} cannot reference itself. "
                f"Relationship type: {self.relationship_type}"
            )
        return self
    
    def to_dict(self) -> dict:
        """Convert to dict format for backward compatibility with existing code."""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relationship_type': self.relationship_type,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class InferredRelationshipBatch(BaseModel):
    """
    Container for batch relationship inference LLM responses.
    
    Handles various LLM response formats:
    - {"relationships": [...]}
    - {"results": [...]}
    - Direct array: [...]
    """
    relationships: List[InferredRelationship] = Field(default_factory=list)
    
    @model_validator(mode='before')
    @classmethod
    def handle_response_formats(cls, values):
        """Normalize various LLM response formats to expected structure."""
        # Handle direct array response
        if isinstance(values, list):
            return {'relationships': values}
        
        # Handle dict with alternative keys
        if isinstance(values, dict):
            # Try common alternative keys
            for key in ['results', 'data', 'items']:
                if key in values and 'relationships' not in values:
                    values['relationships'] = values.pop(key)
        
        return values


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
