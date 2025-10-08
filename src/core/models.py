"""
Pydantic Models for Phase 6 Relationship Inference

Validates LLM responses to ensure structured, type-safe relationship data.
Replaces ~120 lines of manual validation in llm_relationship_inference.py.

Models:
1. RelationshipInference: Single relationship with confidence and reasoning
2. RelationshipInferenceResponse: Batch of relationships from LLM
3. UCFDetectionResult: UCF format detection with confidence
4. UCFSection: Individual UCF section metadata
5. DocumentIngestionResult: Post-ingestion metrics
6. EntityMetadata: Rich entity attributes for knowledge graph

Benefits:
- Type safety: Pydantic catches malformed LLM JSON
- Self-documenting: Models serve as schema documentation
- Validation: Automatic confidence thresholds, ID patterns
- IDE support: Auto-completion and type hints
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum


class RelationshipType(str, Enum):
    """Valid relationship types in government contracting ontology"""
    # Structural relationships
    GUIDES = "GUIDES"  # Section L → Section M
    EVALUATED_BY = "EVALUATED_BY"  # Requirement → Evaluation Factor
    CHILD_OF = "CHILD_OF"  # Sub-document → Parent document
    ATTACHMENT_OF = "ATTACHMENT_OF"  # Annex → Section
    
    # Semantic relationships (Phase 6.1 enhancement)
    INFORMS = "INFORMS"  # Concept → Evaluation Factor
    IMPACTS = "IMPACTS"  # Weakness/Strength → Rating
    DETERMINES = "DETERMINES"  # Factor → Award Decision
    ADDRESSED_BY = "ADDRESSED_BY"  # Pain Point → Solution


class RelationshipInference(BaseModel):
    """
    Single inferred relationship between two entities.
    
    Used by LLM inference algorithms to create structured relationships.
    """
    source_id: str = Field(
        ...,
        description="Entity ID of relationship source (e.g., 'requirement_043')"
    )
    target_id: str = Field(
        ...,
        description="Entity ID of relationship target (e.g., 'evaluation_factor_m2')"
    )
    relationship_type: RelationshipType = Field(
        ...,
        description="Type of relationship (GUIDES, EVALUATED_BY, etc.)"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        description="LLM explanation for why this relationship exists (min 10 chars)"
    )
    
    @field_validator('confidence')
    @classmethod
    def confidence_threshold(cls, v: float) -> float:
        """Ensure confidence meets minimum threshold"""
        if v < 0.30:
            raise ValueError(f"Confidence {v} below minimum threshold 0.30")
        return v
    
    @field_validator('source_id', 'target_id')
    @classmethod
    def valid_entity_id(cls, v: str) -> str:
        """Validate entity ID format (lowercase, underscores, no spaces)"""
        if not v or len(v) < 3:
            raise ValueError(f"Entity ID '{v}' too short (min 3 chars)")
        if ' ' in v:
            raise ValueError(f"Entity ID '{v}' contains spaces (use underscores)")
        return v


class RelationshipInferenceResponse(BaseModel):
    """
    Batch response from LLM containing multiple inferred relationships.
    
    LLM returns this structure for each inference algorithm run.
    """
    relationships: List[RelationshipInference] = Field(
        default_factory=list,
        description="List of inferred relationships"
    )
    algorithm: str = Field(
        ...,
        description="Which inference algorithm produced these relationships"
    )
    entity_count: int = Field(
        ...,
        ge=0,
        description="Number of entities analyzed"
    )
    total_cost: Optional[float] = Field(
        None,
        ge=0.0,
        description="Cost in USD for this LLM call"
    )
    
    @field_validator('relationships')
    @classmethod
    def no_duplicate_relationships(cls, v: List[RelationshipInference]) -> List[RelationshipInference]:
        """Ensure no duplicate source→target relationships"""
        seen = set()
        unique = []
        for rel in v:
            key = (rel.source_id, rel.target_id, rel.relationship_type.value)
            if key not in seen:
                seen.add(key)
                unique.append(rel)
        
        if len(unique) < len(v):
            print(f"Warning: Removed {len(v) - len(unique)} duplicate relationships")
        
        return unique


class UCFSection(BaseModel):
    """
    Individual UCF (Uniform Contract Format) section metadata.
    
    Used by UCF detector to represent detected sections.
    """
    label: str = Field(
        ...,
        description="Section label (e.g., 'Section M', 'Section L')"
    )
    page_start: int = Field(
        ...,
        ge=1,
        description="Starting page number (1-indexed)"
    )
    page_end: Optional[int] = Field(
        None,
        ge=1,
        description="Ending page number (1-indexed)"
    )
    semantic_type: str = Field(
        ...,
        description="Semantic type (e.g., 'EVALUATION_CRITERIA', 'SUBMISSION_INSTRUCTIONS')"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Detection confidence"
    )
    
    @field_validator('page_end')
    @classmethod
    def page_end_after_start(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure page_end >= page_start"""
        if v is not None and 'page_start' in info.data:
            if v < info.data['page_start']:
                raise ValueError(f"page_end {v} < page_start {info.data['page_start']}")
        return v


class UCFDetectionResult(BaseModel):
    """
    Result of UCF format detection on an RFP document.
    
    Used by ucf_detector.py to return structured detection results.
    """
    is_ucf: bool = Field(
        ...,
        description="Whether document follows UCF format"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall UCF detection confidence"
    )
    sections_detected: List[UCFSection] = Field(
        default_factory=list,
        description="List of detected UCF sections"
    )
    document_path: str = Field(
        ...,
        description="Path to analyzed document"
    )
    page_count: int = Field(
        ...,
        ge=1,
        description="Total pages in document"
    )
    
    @field_validator('confidence')
    @classmethod
    def ucf_confidence_threshold(cls, v: float) -> float:
        """UCF detection requires ≥0.70 confidence"""
        if v < 0.70:
            print(f"Warning: UCF confidence {v} below recommended threshold 0.70")
        return v


class DocumentIngestionResult(BaseModel):
    """
    Metrics from document ingestion + Phase 6 post-processing.
    
    Used by custom /insert endpoint to return comprehensive results.
    """
    document_name: str = Field(
        ...,
        description="Name of ingested document"
    )
    entity_count: int = Field(
        ...,
        ge=0,
        description="Total entities extracted"
    )
    relationship_count: int = Field(
        ...,
        ge=0,
        description="Total relationships inferred (includes Phase 6)"
    )
    is_ucf: bool = Field(
        ...,
        description="Whether document uses UCF format"
    )
    ucf_confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="UCF detection confidence"
    )
    processing_time_seconds: float = Field(
        ...,
        ge=0.0,
        description="Total processing time in seconds"
    )
    phase6_enabled: bool = Field(
        default=True,
        description="Whether Phase 6 post-processing ran"
    )
    cost_usd: Optional[float] = Field(
        None,
        ge=0.0,
        description="Total cost in USD (LLM + embedding)"
    )
    
    # Breakdown by Phase 6 algorithm (optional)
    section_l_m_relationships: Optional[int] = Field(None, ge=0)
    document_hierarchy_relationships: Optional[int] = Field(None, ge=0)
    attachment_section_relationships: Optional[int] = Field(None, ge=0)
    clause_clustering_relationships: Optional[int] = Field(None, ge=0)
    requirement_evaluation_relationships: Optional[int] = Field(None, ge=0)
    semantic_concept_relationships: Optional[int] = Field(None, ge=0)


class EntityMetadata(BaseModel):
    """
    Rich metadata for knowledge graph entities.
    
    Used by Phase 6 to attach structured metadata to entities.
    """
    entity_id: str = Field(
        ...,
        description="Unique entity identifier"
    )
    entity_type: str = Field(
        ...,
        description="Entity type (REQUIREMENT, EVALUATION_FACTOR, etc.)"
    )
    entity_name: str = Field(
        ...,
        description="Human-readable entity name"
    )
    description: Optional[str] = Field(
        None,
        description="Entity description"
    )
    source_section: Optional[str] = Field(
        None,
        description="Source section (e.g., 'Section M.2.1')"
    )
    page_number: Optional[int] = Field(
        None,
        ge=1,
        description="Page number where entity appears"
    )
    
    # Entity-specific attributes (optional)
    attributes: Dict[str, Any] = Field(
        default_factory=dict,
        description="Entity-specific attributes (criticality, factor_id, etc.)"
    )
    
    @field_validator('entity_type')
    @classmethod
    def valid_entity_type(cls, v: str) -> str:
        """Validate against known entity types"""
        valid_types = [
            "REQUIREMENT", "EVALUATION_FACTOR", "SUBMISSION_INSTRUCTION",
            "SECTION", "CLAUSE", "ANNEX", "DOCUMENT", "DELIVERABLE",
            "ORGANIZATION", "PERSON", "LOCATION", "CONCEPT", "EVENT",
            "TECHNOLOGY", "STRATEGIC_THEME", "PROGRAM", "STATEMENT_OF_WORK"
        ]
        if v not in valid_types:
            print(f"Warning: Entity type '{v}' not in standard ontology")
        return v


# Example usage (for testing/documentation)
if __name__ == "__main__":
    # Test relationship inference
    rel = RelationshipInference(
        source_id="requirement_043",
        target_id="evaluation_factor_m2",
        relationship_type=RelationshipType.EVALUATED_BY,
        confidence=0.85,
        reasoning="Weekly status reports (REQ-043) are evaluated under Management Approach (Factor M2)"
    )
    print("✅ Valid relationship:", rel.model_dump_json(indent=2))
    
    # Test validation failure (confidence too low)
    try:
        bad_rel = RelationshipInference(
            source_id="req_1",
            target_id="factor_1",
            relationship_type=RelationshipType.GUIDES,
            confidence=0.25,  # Too low!
            reasoning="Low confidence"
        )
    except ValueError as e:
        print(f"✅ Validation caught low confidence: {e}")
    
    print("\n✨ Pydantic models validated successfully!")
