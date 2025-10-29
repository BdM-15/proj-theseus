from enum import Enum
from typing import List, Optional, Any
from pydantic import BaseModel, Field, ValidationError, field_validator


class EntityType(str, Enum):
    organization = "organization"
    concept = "concept"
    event = "event"
    technology = "technology"
    person = "person"
    location = "location"
    requirement = "requirement"
    clause = "clause"
    section = "section"
    document = "document"
    deliverable = "deliverable"
    evaluation_factor = "evaluation_factor"
    submission_instruction = "submission_instruction"
    strategic_theme = "strategic_theme"
    statement_of_work = "statement_of_work"
    program = "program"
    equipment = "equipment"


class EvidenceRef(BaseModel):
    source: str
    page: Optional[int] = None
    excerpt: Optional[str] = None


class Relationship(BaseModel):
    subject_id: str
    object_id: str
    relation_type: str
    description: Optional[str] = None


class Requirement(BaseModel):
    id: str = Field(..., description="Stable requirement id (e.g., R-001)")
    text: str = Field(..., description="Human-readable requirement text")
    criticality: Optional[str] = None
    requirement_type: Optional[str] = None
    evidence: Optional[List[EvidenceRef]] = None

    # Pydantic v2 field validator
    @field_validator("id")
    def id_not_empty(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("id must not be empty")
        return v


def validate_extraction_payload(payload: dict) -> tuple[bool, Optional[List[str]]]:
    """Lightweight validator for extraction outputs.

    Expects a dict with top-level keys like 'entities', 'requirements', 'relationships'.
    Returns a tuple (valid, errors) where errors is None on success or a list of error messages.
    """
    errors: List[str] = []
    try:
        entities = payload.get("entities", []) if isinstance(payload, dict) else []
        # Validate entity types if present
        for e in entities:
            try:
                et = e.get("type")
            except Exception:
                et = None
            if et and et not in [t.value for t in EntityType]:
                errors.append(f"Unknown entity type: {et}")

        # Validate requirements
        requirements = payload.get("requirements", []) if isinstance(payload, dict) else []
        for r in requirements:
            try:
                Requirement.model_validate(r)
            except ValidationError as ve:
                errors.append(f"Requirement validation error: {ve}")

        # Validate relationships shape
        relationships = payload.get("relationships", []) if isinstance(payload, dict) else []
        for rel in relationships:
            try:
                Relationship.model_validate(rel)
            except ValidationError as ve:
                errors.append(f"Relationship validation error: {ve}")

    except Exception as exc:
        errors.append(str(exc))

    return (len(errors) == 0, errors if errors else None)
