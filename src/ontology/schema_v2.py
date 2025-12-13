"""
Simplified Government Contracting Ontology v2.0

This schema prioritizes:
- 12 core entity types (down from 18)
- Minimal required validation (maximum extraction success)
- Query-time inference for workload/staffing details
- Graceful type coercion for unknown entities

Philosophy: Broad entities with rich descriptions enable better multi-hop
retrieval than narrow entities with strict validation.

Shipley Associates Methodology Alignment:
- WinStrategy: Captures themes, discriminators, proof points
- Risk: Capture and proposal risks
- ComplianceItem: Section L/M compliance requirements
- EvaluationFactor: Scoring criteria for source selection
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, model_validator
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# SIMPLIFIED ONTOLOGY: 12 Core Entity Types
# =============================================================================

# Primary entity types for government contracting intelligence
VALID_ENTITY_TYPES_V2 = {
    # Document Structure (3)
    "section",           # RFP sections (A-M, J attachments)
    "document",          # Attachments, standards, references
    "regulation",        # FAR/DFARS/agency clauses (consolidated from clause)
    
    # Procurement Entities (3)
    "requirement",       # All obligations (functional, performance, security)
    "deliverable",       # CDRLs, reports, outputs
    "program",           # Contract/program name
    
    # Evaluation & Compliance (2)
    "evaluation_factor", # Section M criteria, scoring
    "compliance_item",   # Section L instructions, format requirements
    
    # Strategy & Risk (2)
    "win_strategy",      # Win themes, discriminators, proof points
    "risk",              # Capture and execution risks
    
    # Context (2)
    "organization",      # Agencies, contractors, commands
    "reference",         # Catch-all for misc references (replaces concept/event/etc)
}

EntityTypeV2 = Literal[
    "section", "document", "regulation",
    "requirement", "deliverable", "program",
    "evaluation_factor", "compliance_item",
    "win_strategy", "risk",
    "organization", "reference"
]

# Mapping from old 18-type ontology to new 12-type
OLD_TO_NEW_TYPE_MAPPING = {
    # Direct mappings
    "requirement": "requirement",
    "deliverable": "deliverable",
    "program": "program",
    "organization": "organization",
    "section": "section",
    "document": "document",
    "evaluation_factor": "evaluation_factor",
    
    # Consolidated mappings
    "performance_metric": "requirement",    # Metrics ARE requirements
    "clause": "regulation",                 # Clauses are regulations
    "submission_instruction": "compliance_item",  # Instructions are compliance
    "strategic_theme": "win_strategy",      # Themes are win strategies
    "statement_of_work": "section",         # SOW is a section type
    
    # Removed types → closest match
    "concept": "reference",                 # Generic concepts → reference
    "event": "reference",                   # Events → reference
    "technology": "reference",              # Tech → reference (or requirement)
    "person": "organization",               # People → org context
    "location": "organization",             # Locations → org context
    "equipment": "requirement",             # Equipment → requirement
}


def migrate_entity_type(old_type: str) -> str:
    """
    Convert old 18-type entity to new 12-type ontology.
    
    Args:
        old_type: Entity type from v1 ontology
        
    Returns:
        Mapped entity type in v2 ontology
    """
    old_type_lower = old_type.lower().strip()
    
    # Direct mapping
    if old_type_lower in OLD_TO_NEW_TYPE_MAPPING:
        return OLD_TO_NEW_TYPE_MAPPING[old_type_lower]
    
    # Already valid in new ontology
    if old_type_lower in VALID_ENTITY_TYPES_V2:
        return old_type_lower
    
    # Unknown → reference (graceful fallback)
    logger.warning(f"Unknown entity type '{old_type}' → mapping to 'reference'")
    return "reference"


# =============================================================================
# SIMPLIFIED PYDANTIC MODELS (Minimal Validation)
# =============================================================================

class BaseEntityV2(BaseModel):
    """
    Base entity with minimal required fields.
    
    Philosophy: Capture data permissively, validate/enrich at query time.
    """
    entity_name: str = Field(..., description="Canonical name of the entity")
    entity_type: EntityTypeV2 = Field(..., description="Entity type from 12-type ontology")
    description: str = Field("", description="Full description/context from source")
    source_id: str = Field("", description="Source chunk ID for traceability")
    
    @model_validator(mode='before')
    @classmethod
    def coerce_entity_type(cls, values):
        """
        Gracefully coerce invalid entity types to valid ones.
        Never drop entities - always map to closest valid type.
        """
        if isinstance(values, dict):
            entity_type = values.get('entity_type', '')
            if entity_type and entity_type.lower() not in VALID_ENTITY_TYPES_V2:
                migrated = migrate_entity_type(entity_type)
                logger.debug(f"Coerced entity_type '{entity_type}' → '{migrated}'")
                values['entity_type'] = migrated
        return values
    
    @model_validator(mode='after')
    def clean_entity_name(self):
        """Remove common LLM formatting artifacts from entity names."""
        if self.entity_name:
            # Strip leading # and whitespace
            cleaned = self.entity_name.lstrip('#').strip()
            # Remove markdown bold/italics
            cleaned = cleaned.replace('**', '').replace('__', '').replace('*', '')
            if cleaned != self.entity_name:
                self.entity_name = cleaned
        return self


class RequirementV2(BaseEntityV2):
    """
    Requirement entity - all contractual obligations.
    
    Includes: functional, performance, security, technical requirements
    Also includes: performance metrics (merged from performance_metric)
    
    SIMPLIFIED: No mandatory workload fields. Workload analysis happens
    at query time using the full description text.
    """
    entity_type: Literal["requirement"] = "requirement"
    
    # Optional classification (not required for extraction success)
    criticality: str = Field("", description="MANDATORY/IMPORTANT/OPTIONAL - optional")
    modal_verb: str = Field("", description="shall/must/should/may - optional")
    
    # NO labor_drivers, material_needs, req_type
    # These are INFERRED at query time from description


class DeliverableV2(BaseEntityV2):
    """
    Deliverable entity - CDRLs, reports, work products.
    
    SIMPLIFIED: Just capture the deliverable reference.
    Frequency, format, DID references are in description.
    """
    entity_type: Literal["deliverable"] = "deliverable"
    
    # Optional: CDRL identifier if present
    cdrl_id: str = Field("", description="CDRL number (A001, B002) - optional")


class EvaluationFactorV2(BaseEntityV2):
    """
    Evaluation factor - Section M scoring criteria.
    
    SIMPLIFIED: No subfactors list. Hierarchy is in graph relationships.
    """
    entity_type: Literal["evaluation_factor"] = "evaluation_factor"
    
    # Optional weighting
    weight: str = Field("", description="Weight or importance (40%, Most Important) - optional")


class ComplianceItemV2(BaseEntityV2):
    """
    Compliance item - Section L instructions, format requirements.
    
    Merged from: submission_instruction
    """
    entity_type: Literal["compliance_item"] = "compliance_item"
    
    # Optional: page limits, format requirements captured in description


class WinStrategyV2(BaseEntityV2):
    """
    Win strategy - themes, discriminators, proof points.
    
    Merged from: strategic_theme
    
    Shipley Methodology:
    - CUSTOMER_HOT_BUTTON: Government priorities
    - DISCRIMINATOR: Competitive differentiators
    - PROOF_POINT: Evidence of capability
    - WIN_THEME: Overarching positioning
    """
    entity_type: Literal["win_strategy"] = "win_strategy"
    
    # Optional: strategy type classification
    strategy_type: str = Field("", description="HOT_BUTTON/DISCRIMINATOR/PROOF_POINT/THEME - optional")


class RiskV2(BaseEntityV2):
    """
    Risk entity - capture and execution risks.
    
    NEW in v2: Explicit risk tracking for Shipley methodology.
    """
    entity_type: Literal["risk"] = "risk"
    
    # Optional: risk classification
    risk_type: str = Field("", description="CAPTURE/EXECUTION/TECHNICAL/PROGRAMMATIC - optional")


class RegulationV2(BaseEntityV2):
    """
    Regulation entity - FAR, DFARS, agency clauses.
    
    Merged from: clause
    """
    entity_type: Literal["regulation"] = "regulation"
    
    # Optional: clause number
    clause_number: str = Field("", description="FAR/DFARS citation (52.212-4) - optional")


class SectionV2(BaseEntityV2):
    """
    Section entity - RFP sections, SOW/PWS.
    
    Merged from: section, statement_of_work
    """
    entity_type: Literal["section"] = "section"
    
    # Optional: section label
    section_label: str = Field("", description="Section identifier (L, M, C) - optional")


class DocumentV2(BaseEntityV2):
    """
    Document entity - attachments, standards, references.
    """
    entity_type: Literal["document"] = "document"


class OrganizationV2(BaseEntityV2):
    """
    Organization entity - agencies, contractors, commands.
    
    Merged from: organization, person, location
    """
    entity_type: Literal["organization"] = "organization"


class ProgramV2(BaseEntityV2):
    """
    Program entity - contract/program names.
    """
    entity_type: Literal["program"] = "program"


class ReferenceV2(BaseEntityV2):
    """
    Reference entity - catch-all for miscellaneous entities.
    
    Replaces: concept, event, technology (when not better classified)
    """
    entity_type: Literal["reference"] = "reference"


# =============================================================================
# SIMPLIFIED RELATIONSHIP MODEL
# =============================================================================

class RelationshipV2(BaseModel):
    """
    Simplified relationship model.
    
    No entity object nesting - just names for flexibility.
    """
    source_entity: str = Field(..., description="Source entity name")
    target_entity: str = Field(..., description="Target entity name")
    relationship_type: str = Field(..., description="Relationship type")
    confidence: float = Field(0.7, ge=0.0, le=1.0, description="Confidence score")
    reasoning: str = Field("", description="Brief explanation")


# Focused relationship types (7 vs previous 20+)
RELATIONSHIP_TYPES_V2 = [
    "HAS_REQUIREMENT",   # Section → Requirement
    "EVALUATED_BY",      # Requirement → EvaluationFactor
    "PRODUCES",          # Requirement → Deliverable
    "PART_OF",           # Child → Parent (hierarchy)
    "REFERENCES",        # Entity → Document/Regulation
    "ADDRESSES",         # WinStrategy → Requirement/Risk
    "MITIGATES",         # WinStrategy → Risk
]


# =============================================================================
# EXTRACTION RESULT CONTAINER
# =============================================================================

class ExtractionResultV2(BaseModel):
    """
    Simplified extraction result container.
    
    GRACEFUL: Never drops valid entities. Coerces types as needed.
    """
    entities: List[BaseEntityV2] = Field(default_factory=list)
    relationships: List[RelationshipV2] = Field(default_factory=list)
    
    @model_validator(mode='before')
    @classmethod
    def handle_response_formats(cls, values):
        """Handle various LLM response formats gracefully."""
        if isinstance(values, dict):
            # Handle nested formats
            if 'results' in values and 'entities' not in values:
                values['entities'] = values.pop('results')
            if 'data' in values and 'entities' not in values:
                values['entities'] = values.pop('data')
        return values


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_entity_types_for_extraction() -> List[str]:
    """
    Return entity type list for LightRAG addon_params.
    
    Used in src/server/config.py and src/server/initialization.py
    """
    return list(VALID_ENTITY_TYPES_V2)


def create_entity(entity_type: str, entity_name: str, description: str = "", **kwargs) -> BaseEntityV2:
    """
    Factory function to create appropriate entity subclass.
    
    Args:
        entity_type: Entity type string
        entity_name: Name of the entity
        description: Entity description
        **kwargs: Additional fields
        
    Returns:
        Appropriate entity subclass instance
    """
    # Migrate to valid type
    valid_type = migrate_entity_type(entity_type)
    
    # Map to class
    type_to_class = {
        "requirement": RequirementV2,
        "deliverable": DeliverableV2,
        "evaluation_factor": EvaluationFactorV2,
        "compliance_item": ComplianceItemV2,
        "win_strategy": WinStrategyV2,
        "risk": RiskV2,
        "regulation": RegulationV2,
        "section": SectionV2,
        "document": DocumentV2,
        "organization": OrganizationV2,
        "program": ProgramV2,
        "reference": ReferenceV2,
    }
    
    entity_class = type_to_class.get(valid_type, ReferenceV2)
    
    return entity_class(
        entity_name=entity_name,
        entity_type=valid_type,
        description=description,
        **kwargs
    )
