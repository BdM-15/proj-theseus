"""Phase 3 quality-floor policy tests for ontology and extraction prompt alignment.

These tests intentionally validate static quality gates before major prompt rewrites:
- Canonical relationship vocabulary count is stable.
- Extraction prompt F.1 relationship list exactly matches schema canonical set.
- Golden-thread and authority-traceability relationship primitives remain present.
- Core entity types required for Section L↔M traceability remain present.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES

_ROOT = Path(__file__).parent.parent
_PROMPT_PATH = _ROOT / "prompts" / "extraction" / "govcon_lightrag_json.txt"
_INFERENCE_ONLY_RELATIONSHIP_TYPES = {"REQUIRES", "ENABLED_BY", "RESPONSIBLE_FOR"}


def _read_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _extract_f1_relationship_types(prompt_text: str) -> set[str]:
    """Extract canonical relationship types listed under prompt Part F.1.

    We parse only the F.1 block and collect tokens like `CHILD_OF - ...`.
    """
    start = prompt_text.find("F.1 Mandatory Relationship Types")
    end = prompt_text.find("F.2 Proposal Instruction")
    assert start != -1 and end != -1 and end > start, (
        "Could not locate Part F.1/F.2 boundaries in govcon_lightrag_json.txt"
    )
    block = prompt_text[start:end]
    return set(re.findall(r"^([A-Z_]+)\s+-\s+", block, flags=re.MULTILINE))


# ---------------------------------------------------------------------------
# Relationship vocabulary stability and prompt/schema parity
# ---------------------------------------------------------------------------


def test_canonical_relationship_count_is_35():
    assert len(VALID_RELATIONSHIP_TYPES) == 35, (
        f"Expected 35 canonical relationship types, found {len(VALID_RELATIONSHIP_TYPES)}"
    )


def test_prompt_contract_note_uses_35_relationship_count():
    prompt_text = _read_prompt()
    expected = "The 33 govcon entity types and 35 canonical relationship types are unchanged."
    assert expected in prompt_text, (
        "Prompt contract note must state the active 33/35 ontology cardinality."
    )


def test_prompt_f1_relationship_types_match_schema_exactly():
    prompt_types = _extract_f1_relationship_types(_read_prompt())
    extraction_schema_types = set(VALID_RELATIONSHIP_TYPES) - _INFERENCE_ONLY_RELATIONSHIP_TYPES
    assert prompt_types == extraction_schema_types, (
        "Part F.1 relationship list drifted from extraction relationship types. "
        f"Missing in prompt: {sorted(extraction_schema_types - prompt_types)}; "
        f"Extra in prompt: {sorted(prompt_types - extraction_schema_types)}"
    )


def test_inference_only_relationship_types_present_in_schema():
    missing = _INFERENCE_ONLY_RELATIONSHIP_TYPES - set(VALID_RELATIONSHIP_TYPES)
    assert not missing, f"Missing inference-only relationship types in schema: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Phase 3 quality-floor relationship primitives (connectivity/traceability)
# ---------------------------------------------------------------------------


def test_golden_thread_relationship_primitives_present():
    required = {
        "GUIDES",
        "EVALUATED_BY",
        "HAS_SUBFACTOR",
        "PRODUCES",
        "SATISFIED_BY",
        "TRACKED_BY",
        "SUBMITTED_TO",
        "EVIDENCES",
    }
    missing = required - set(VALID_RELATIONSHIP_TYPES)
    assert not missing, f"Missing golden-thread relationship primitives: {sorted(missing)}"


def test_authority_and_constraint_relationship_primitives_present():
    required = {
        "GOVERNED_BY",
        "MANDATES",
        "CONSTRAINED_BY",
        "DEFINES",
        "APPLIES_TO",
    }
    missing = required - set(VALID_RELATIONSHIP_TYPES)
    assert not missing, f"Missing authority/constraint relationship primitives: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Core entity primitives required for L↔M↔execution traceability
# ---------------------------------------------------------------------------


def test_core_entity_primitives_present():
    required = {
        "requirement",
        "proposal_instruction",
        "evaluation_factor",
        "work_scope_item",
        "deliverable",
        "performance_standard",
        "labor_category",
        "workload_metric",
        "compliance_artifact",
        "past_performance_reference",
    }
    missing = required - set(VALID_ENTITY_TYPES)
    assert not missing, f"Missing core traceability entity types: {sorted(missing)}"
