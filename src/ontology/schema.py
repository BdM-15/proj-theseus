from typing import List, Optional, Literal, Dict
from enum import Enum
from pydantic import BaseModel, Field, model_validator, field_validator
import logging

logger = logging.getLogger(__name__)

# ==========================================
# Core Enums (The "Rules" of the Ontology)
# ==========================================

CriticalityLevel = Literal["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"]
RequirementType = Literal["FUNCTIONAL", "PERFORMANCE", "SECURITY", "TECHNICAL", "INTERFACE", "MANAGEMENT", "DESIGN", "QUALITY", "OTHER"]
ThemeType = Literal["DISCRIMINATOR", "PROOF_POINT", "WIN_THEME"]
EntityType = Literal[
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "document_section", "document", "deliverable",
    "evaluation_factor", "proposal_instruction", "proposal_volume", "program", "equipment",
    "strategic_theme", "work_scope_item", "contract_line_item", "workload_metric",
    "labor_category", "subfactor", "regulatory_reference", "performance_standard",
    "pricing_element", "government_furnished_item", "compliance_artifact",
    "transition_activity", "technical_specification", "past_performance_reference",
    "customer_priority", "pain_point", "amendment"
]

# Set for fast validation lookups (Branch 040 pattern)
VALID_ENTITY_TYPES = {
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "document_section", "document", "deliverable",
    "evaluation_factor", "proposal_instruction", "proposal_volume", "program", "equipment",
    "strategic_theme", "work_scope_item", "contract_line_item", "workload_metric",
    "labor_category", "subfactor", "regulatory_reference", "performance_standard",
    "pricing_element", "government_furnished_item", "compliance_artifact",
    "transition_activity", "technical_specification", "past_performance_reference",
    "customer_priority", "pain_point", "amendment"
}

# Valid relationship types - canonical set matching extraction prompt Part F.1/J
# These are the ONLY valid values for the relationship_type / keywords field.
# Organized by functional group for clarity.
VALID_RELATIONSHIP_TYPES = {
    # Structural (Document Hierarchy & Cross-References)
    "CHILD_OF", "ATTACHMENT_OF", "CONTAINS", "AMENDS", "SUPERSEDED_BY", "REFERENCES",
    # Evaluation & Proposal (Section L↔M Golden Thread)
    "GUIDES", "EVALUATED_BY", "HAS_SUBFACTOR", "MEASURED_BY", "EVIDENCES",
    # Work & Deliverables (Traceability Chain)
    "PRODUCES", "SATISFIED_BY", "TRACKED_BY", "SUBMITTED_TO", "STAFFED_BY",
    "PRICED_UNDER", "FUNDS", "QUANTIFIES",
    # Authority & Governance
    "GOVERNED_BY", "MANDATES", "CONSTRAINED_BY", "DEFINES", "APPLIES_TO",
    # Resource & Operational
    "HAS_EQUIPMENT", "PROVIDED_BY", "COORDINATED_WITH", "REPORTED_TO",
    # Strategic & Capture Intelligence
    "ADDRESSES", "RESOLVES", "SUPPORTS", "RELATED_TO",
    # Inference-only types (produced by post-processing algo 8: orphan resolution)
    "REQUIRES", "ENABLED_BY", "RESPONSIBLE_FOR",
}


def normalize_relationship_type(rel_type: str, fallback: str = "RELATED_TO") -> str:
    """
    Normalize a relationship type string to a valid canonical type.

    GRACEFUL HANDLING: Never returns None - always maps to a valid type.
    Unknown types are mapped to fallback (default: RELATED_TO) and logged as WARNING.
    """
    normalized = rel_type.strip().upper().replace(" ", "_")
    if normalized in VALID_RELATIONSHIP_TYPES:
        return normalized

    # Common rogue type mappings (from old prompts / LLM drift)
    _ROGUE_MAPPINGS = {
        # Legacy / renamed
        "MEASURES": "MEASURED_BY",
        "PART_OF": "CHILD_OF",
        "BELONGS_TO": "RELATED_TO",
        "CONTAINED_IN": "RELATED_TO",
        "HAS": "CONTAINS",
        "IS_A": "RELATED_TO",
        "TYPE_OF": "RELATED_TO",
        "MEMBER_OF": "CHILD_OF",
        "ASSOCIATED_WITH": "RELATED_TO",
        "LOCATED_AT": "RELATED_TO",
        "SPECIFIES": "DEFINES",
        "FIELD_IN": "CHILD_OF",
        "INFERRED": "RELATED_TO",
        # LLM-generated types not yet in canonical set
        "IMPLEMENTED_BY": "SATISFIED_BY",    # requirement IMPLEMENTED_BY approach
        "SUBJECT_TO": "GOVERNED_BY",          # entity SUBJECT_TO regulation
        "REFERENCED_BY": "REFERENCES",        # inverse reference (direction approximated)
        "REQUIRES_DELIVERABLE": "REQUIRES",   # more specific form of REQUIRES
        "USED_FOR": "SUPPORTS",               # resource/tech USED_FOR purpose
    }
    if normalized in _ROGUE_MAPPINGS:
        mapped = _ROGUE_MAPPINGS[normalized]
        logger.info(f"Mapped rogue relationship type '{rel_type}' → '{mapped}'")
        return mapped

    logger.warning(
        f"⚠️ Unknown relationship type '{rel_type}' → defaulting to '{fallback}'"
    )
    return fallback


# ==========================================
# BOE Category Enum (Workload Enrichment)
# ==========================================

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
BOE_CATEGORY_MAPPING: Dict[str, BOECategory] = {
    "security": BOECategory.COMPLIANCE,
    "base access": BOECategory.COMPLIANCE,
}


def normalize_boe_category(category: str, fallback: BOECategory = BOECategory.LABOR) -> BOECategory:
    """
    Normalize a category string to a valid BOECategory.
    
    GRACEFUL HANDLING: Never returns None - always maps to a valid category.
    Unknown categories are mapped to fallback (default: Labor) and logged as WARNING.
    """
    category_lower = category.lower().strip()
    
    # Check if it's already a valid category
    for boe_cat in BOECategory:
        if boe_cat.value.lower() == category_lower:
            return boe_cat
    
    # Try mapping from common invalid values
    if category_lower in BOE_CATEGORY_MAPPING:
        return BOE_CATEGORY_MAPPING[category_lower]
    
    # GRACEFUL FALLBACK: Log warning and use fallback category
    logger.warning(f"Unmapped BOE category '{category}' -> defaulting to '{fallback.value}'")
    return fallback

# ==========================================
# Base Entity Model
# ==========================================

class BaseEntity(BaseModel):
    entity_name: str = Field(..., description="The canonical name of the entity (Title Case).")
    entity_type: EntityType = Field(..., description="The strict entity type from the government contracting ontology.")
    description: str = Field(..., description="Comprehensive description including context, values, and relationships.")

    @model_validator(mode='before')
    @classmethod
    def validate_entity_type(cls, values):
        """
        Validate entity_type BEFORE Pydantic parsing.
        
        NOTE (Issue #54 - Back to Basics):
        This validator is now primarily used for post-processing operations,
        not extraction. Native LightRAG handles extraction with our ontology.
        
        For invalid types:
        - Logs a clear warning (helps identify prompt issues)
        - Normalizes case (Organization → organization)
        - Uses 'concept' as fallback for unknown types
        """
        if isinstance(values, dict):
            entity_type = values.get('entity_type', '')
            if entity_type:
                entity_type_lower = entity_type.lower()
                
                if entity_type_lower not in VALID_ENTITY_TYPES:
                    entity_name = values.get('entity_name', 'unknown')
                    # Log clearly - this helps identify prompt issues
                    logger.warning(
                        f"⚠️ Invalid entity_type '{entity_type}' for '{entity_name}' "
                        f"(valid types: {', '.join(sorted(VALID_ENTITY_TYPES)[:5])}...)"
                    )
                    # Use 'concept' as intelligent fallback
                    values['entity_type'] = 'concept'
                elif entity_type != entity_type_lower:
                    # Just normalize case
                    values['entity_type'] = entity_type_lower
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

class ProposalInstruction(BaseEntity):
    entity_type: Literal["proposal_instruction"] = "proposal_instruction"
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

class PerformanceStandard(BaseEntity):
    entity_type: Literal["performance_standard"] = "performance_standard"
    threshold: str = Field(..., description="The specific value/limit (e.g., '99.9%', '< 2 errors').")
    measurement_method: Optional[str] = Field(None, description="How the metric is calculated or inspected.")

# ==========================================
# Relationship Model
# ==========================================

class RelationshipEntity(BaseModel):
    """
    Entity reference for relationships.
    Requires entity_name, entity_type, and description for full context.
    """
    entity_name: str = Field(..., description="Name of the entity being referenced")
    entity_type: str = Field(..., description="Type of the entity being referenced")
    description: str = Field(..., description="Brief description of the entity (20-50 words)")


class Relationship(BaseModel):
    """
    Relationship between two entities with full context.
    
    All fields are REQUIRED for complete intelligence capture.
    """
    source_entity: RelationshipEntity = Field(..., description="Source entity with name, type, and description")
    target_entity: RelationshipEntity = Field(..., description="Target entity with name, type, and description")
    relationship_type: str = Field(..., description="Type of relationship - MUST be one of the valid relationship types (e.g., EVALUATED_BY, GUIDES, CHILD_OF).")
    description: str = Field(..., description="Explanation of the relationship (20-50 words)")

    @field_validator('relationship_type')
    @classmethod
    def validate_relationship_type(cls, v: str) -> str:
        """Normalize and validate relationship type against canonical set."""
        return normalize_relationship_type(v)

# ==========================================
# Container for LLM Output
# ==========================================

# ==========================================
# Pydantic Models for Post-Processing (Branch 040)
# ==========================================

class InferredRelationship(BaseModel):
    """
    Pydantic model for LLM-inferred relationships in semantic post-processing.
    
    Validates relationship structure and prevents common LLM errors:
    - Self-loops (source_id == target_id)
    - Missing required fields
    - Invalid confidence scores
    
    Pattern: Graceful degradation - validate one-by-one, drop bad ones, keep batch.
    """
    source_id: str = Field(..., min_length=1, description="Entity ID of source node")
    target_id: str = Field(..., min_length=1, description="Entity ID of target node")
    relationship_type: str = Field(..., min_length=1, description="Relationship type (e.g., EVALUATED_BY, GUIDES)")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    reasoning: str = Field(default="", description="LLM explanation for this relationship")
    
    @field_validator('relationship_type')
    @classmethod
    def validate_inferred_relationship_type(cls, v: str) -> str:
        """Normalize and validate relationship type against canonical set."""
        return normalize_relationship_type(v)
    
    @field_validator('reasoning')
    @classmethod
    def clean_reasoning(cls, v: str) -> str:
        """Remove markdown formatting from reasoning."""
        cleaned = v.strip()
        cleaned = cleaned.replace('**', '').replace('__', '').replace('*', '')
        return cleaned[:500] if len(cleaned) > 500 else cleaned  # Truncate long reasoning
    
    @model_validator(mode='after')
    def check_no_self_loop(self):
        """Prevent self-referential relationships."""
        if self.source_id == self.target_id:
            raise ValueError(f"Self-loop detected: {self.source_id} -> {self.target_id}")
        return self
    
    def to_dict(self) -> dict:
        """Convert to dict for Neo4j insertion."""
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
            for key in ['results', 'data', 'items']:
                if key in values and 'relationships' not in values:
                    values['relationships'] = values.pop(key)
        
        return values


# ==========================================
# Workload Enrichment Models (Branch 040)
# ==========================================

class WorkloadEnrichmentItem(BaseModel):
    """
    Pydantic model for validating workload enrichment LLM responses.
    Enforces BOE category constraints at parse time with graceful fallback.
    """
    entity_index: int = Field(..., description="Index of the entity in the batch.")
    has_workload_metric: bool = Field(True, description="Whether this requirement has workload implications.")
    workload_categories: List[str] = Field(default_factory=list, description="Raw categories from LLM.")
    validated_categories: List[BOECategory] = Field(default_factory=list, description="Validated BOE categories.")
    boe_relevance: Dict[str, float] = Field(default_factory=dict, description="Confidence scores per BOE category.")
    labor_drivers: List[str] = Field(default_factory=list, description="Labor-specific details.")
    material_needs: List[str] = Field(default_factory=list, description="Material-specific details.")
    complexity_score: int = Field(default=5, ge=0, le=10, description="Complexity 0-10 (0=unknown, 1-10=assessed).")
    complexity_rationale: str = Field(default="", description="Complexity explanation.")
    effort_estimate: str = Field(default="", description="Effort description.")
    
    @field_validator('workload_categories', mode='before')
    @classmethod
    def normalize_categories_input(cls, v):
        """Accept any input format for workload_categories."""
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        return list(v)
    
    @model_validator(mode='after')
    def validate_and_map_categories(self):
        """Normalize raw workload_categories to validated BOE categories."""
        validated = []
        for cat in self.workload_categories:
            normalized = normalize_boe_category(cat)
            if normalized not in validated:
                validated.append(normalized)
        self.validated_categories = validated
        return self
    
    def get_category_values(self) -> List[str]:
        """Return validated category values as strings."""
        return [cat.value for cat in self.validated_categories]


class WorkloadEnrichmentResponse(BaseModel):
    """Container for batch workload enrichment LLM responses."""
    requirements: List[WorkloadEnrichmentItem] = Field(default_factory=list)
    
    @model_validator(mode='before')
    @classmethod
    def handle_response_formats(cls, values):
        """Handle various LLM response formats."""
        if isinstance(values, list):
            return {'requirements': values}
        if isinstance(values, dict):
            if 'requirements' not in values and 'entities' in values:
                values['requirements'] = values.pop('entities')
        return values


# ==========================================
# Container for LLM Extraction Output
# ==========================================

class ExtractionResult(BaseModel):
    """The root object expected from the LLM."""
    entities: List[
        Requirement | EvaluationFactor | ProposalInstruction |
        StrategicTheme | Clause | PerformanceStandard | BaseEntity
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
