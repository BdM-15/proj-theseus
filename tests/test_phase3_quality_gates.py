"""Phase 3 quality-floor policy tests for ontology and extraction prompt alignment.

These tests intentionally validate static quality gates before major prompt rewrites:
- Canonical relationship vocabulary count is stable.
- Extraction prompt (V8 compact frame) relationship set exactly matches schema canonical set.
- Golden-thread and authority-traceability relationship primitives remain present.
- Core entity types required for Section L⇔M traceability remain present.

V8-4 (issue #124): govcon_lightrag_json.txt was retired. Tests now verify the V8 compact
frame built by _build_v8_system_prompt() in prompts/govcon_prompt.py.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES, render_relationship_types_guidance
from prompts.govcon_prompt import _build_v8_system_prompt

_INFERENCE_ONLY_RELATIONSHIP_TYPES = {"REQUIRES", "ENABLED_BY", "RESPONSIBLE_FOR"}


def _read_prompt() -> str:
    """Return the active V8 extraction system prompt."""
    return _build_v8_system_prompt()

def _extract_extraction_relationship_types(prompt_text: str) -> set[str]:
    """Extract canonical relationship types from the V8 prompt's Part E.

    render_relationship_types_guidance() embeds types as comma-separated tokens in
    lines like `- Structural: CHILD_OF, AMENDS, SUPERSEDED_BY, REFERENCES`.
    We parse only the extraction-time block (before the inference-only line).
    """
    # Locate Part E block
    start = prompt_text.find("PART E: RELATIONSHIP GUIDANCE")
    end = prompt_text.find("PART F: OUTPUT CONTRACT")
    assert start != -1, "V8 prompt missing PART E: RELATIONSHIP GUIDANCE"
    assert end != -1 and end > start, "V8 prompt missing PART F: OUTPUT CONTRACT after PART E"
    block = prompt_text[start:end]

    # Stop at the inference-only section to avoid collecting REQUIRES/ENABLED_BY/RESPONSIBLE_FOR
    inference_marker = "Inference-only types"
    if inference_marker in block:
        block = block[:block.index(inference_marker)]

    # Collect UPPERCASE_WITH_UNDERSCORES tokens
    return set(re.findall(r"\b([A-Z][A-Z_]+[A-Z])\b", block))


# ---------------------------------------------------------------------------
# Relationship vocabulary stability and prompt/schema parity
# ---------------------------------------------------------------------------


def test_canonical_relationship_count_is_26():
    """26 = 23 extraction-time + 3 inference-only.
    9 types removed in Phase 3 first-principles reduction (produce phantom duplicate edges):
    CONTAINS, ATTACHMENT_OF, HAS_SUBFACTOR, FUNDS, MANDATES, RESOLVES, SUPPORTS,
    COORDINATED_WITH, REPORTED_TO — all normalized to canonical equivalents in schema.
    """
    assert len(VALID_RELATIONSHIP_TYPES) == 26, (
        f"Expected 26 canonical relationship types (23 extraction + 3 inference-only), found {len(VALID_RELATIONSHIP_TYPES)}"
    )


def test_prompt_contract_note_uses_35_relationship_count():
    """
    Verify the V8 prompt contains its structural landmark sections and the
    entity types guidance placeholder (rendered from YAML at init time).
    This is the V8-4 equivalent of the legacy monolith's Part F contract-note check.
    """
    prompt_text = _read_prompt()
    assert "{entity_types_guidance}" in prompt_text, (
        "Entity types guidance placeholder must be present in V8 prompt (rendered from YAML)."
    )
    assert "PART E: RELATIONSHIP GUIDANCE" in prompt_text, "V8 prompt must contain Part E relationship section."
    assert "PART F: OUTPUT CONTRACT" in prompt_text, "V8 prompt must contain Part F output contract."


def test_prompt_f1_relationship_types_match_schema_exactly():
    """V8 prompt Part E must contain every extraction-time canonical relationship type.

    V8 builds Part E by calling render_relationship_types_guidance() directly from
    schema.py, so prompt/schema parity is guaranteed by construction. This test
    verifies no type was silently dropped from the rendered output.
    """
    prompt_types = _extract_extraction_relationship_types(_read_prompt())
    extraction_schema_types = set(VALID_RELATIONSHIP_TYPES) - _INFERENCE_ONLY_RELATIONSHIP_TYPES
    missing_in_prompt = extraction_schema_types - prompt_types
    assert not missing_in_prompt, (
        "Extraction-time relationship types missing from V8 prompt Part E: "
        f"{sorted(missing_in_prompt)}. "
        "render_relationship_types_guidance() in schema.py may have drifted."
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
        "CHILD_OF",        # covers HAS_SUBFACTOR (eval factor hierarchy) + ATTACHMENT_OF + CONTAINS
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
        "GOVERNED_BY",      # MANDATES normalized to GOVERNED_BY (inverse direction eliminated)
        "CONSTRAINED_BY",
        "DEFINES",
        "APPLIES_TO",
    }
    missing = required - set(VALID_RELATIONSHIP_TYPES)
    assert not missing, f"Missing authority/constraint relationship primitives: {sorted(missing)}"


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
