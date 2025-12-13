"""
Ontology mode selection (Simplified vs Legacy)
==============================================

This repo historically used a highly specialized GovCon ontology (see `src/ontology/schema.py`)
and (optionally) strict Pydantic validation during LightRAG text extraction.

Problem observed in production: retrieval quality degraded as the ontology and extraction
pipeline became more rigid/complex (sparse/noisy graphs, lossy entity descriptions, and
overly aggressive post-processing).

This module introduces a *lightweight*, hierarchical ontology mode intended to align with
LightRAG/RAG-Anything best practices: keep entity types few/broad, preserve evidence in
chunks, and infer fine-grained details at query-time or lightweight post-processing.
"""

from __future__ import annotations

import os
from typing import Final, Literal, Sequence

OntologyMode = Literal["simplified", "legacy"]


LEGACY_ENTITY_TYPES: Final[list[str]] = [
    # Core entities
    "organization",
    "concept",
    "event",
    "technology",
    "person",
    "location",
    # Requirements / scope / structure
    "requirement",
    "statement_of_work",
    "section",
    "document",
    "deliverable",
    "clause",
    # Evaluation / submission
    "evaluation_factor",
    "submission_instruction",
    # Program / assets
    "program",
    "equipment",
    # Strategy
    "strategic_theme",
    # Performance / QASP
    "performance_metric",
]


# 10–15 core entities, hierarchical and query-friendly (Shipley + Fed RFP centric)
SIMPLIFIED_ENTITY_TYPES: Final[list[str]] = [
    "opportunity",          # RFP/solicitation/opportunity metadata
    "customer",             # Government customer / requiring activity
    "competitor",           # Known incumbents / competitors
    "shipley_phase",        # PursuitDecision, CapturePlanning, ProposalDevelopment, ColorReview
    "section",              # UCF sections, attachments, appendices
    "document",             # referenced docs/standards/attachments
    "rfp_requirement",      # broad "shall/must/should" requirements (incl workload signals inside description)
    "compliance_item",      # submission/checklist items (page limits, formats, due dates)
    "evaluation_criterion", # Section M criteria / factors / subfactors
    "deliverable",          # CDRLs / reports / deliverables
    "risk",                 # capture/proposal/technical/programmatic risks
    "win_theme",            # win themes / hot buttons
    "discriminator",        # differentiators / discriminators / proof points
    "work_scope",           # SOW/PWS tasking scope (broad buckets)
]


def get_ontology_mode() -> OntologyMode:
    """
    Returns the active ontology mode.

    Env:
      ONTOLOGY_MODE: "simplified" (default) | "legacy"
    """
    v = (os.getenv("ONTOLOGY_MODE", "simplified") or "simplified").strip().lower()
    if v == "legacy":
        return "legacy"
    return "simplified"


def get_entity_types(mode: OntologyMode | None = None) -> list[str]:
    m = mode or get_ontology_mode()
    return list(LEGACY_ENTITY_TYPES if m == "legacy" else SIMPLIFIED_ENTITY_TYPES)


def get_valid_entity_types_set(mode: OntologyMode | None = None) -> set[str]:
    return set(get_entity_types(mode))


def get_extraction_prompt_names(mode: OntologyMode | None = None) -> Sequence[str]:
    """
    Prompt loader names under `prompts/extraction/` (without extension).
    """
    m = mode or get_ontology_mode()
    if m == "legacy":
        return (
            "extraction/entity_extraction_prompt",
            "extraction/entity_detection_rules",
        )
    return (
        "extraction/simplified_entity_extraction_prompt",
        "extraction/simplified_entity_detection_rules",
    )

