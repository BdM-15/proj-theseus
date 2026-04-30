"""Unit tests for the EntityCatalog Pydantic schema, loader, and renderer."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.ontology.entity_catalog import (
    Category,
    EntityCatalog,
    EntityTypeDef,
    FallbackMapping,
    SubPattern,
)


# ---------- fixtures ---------- #


def _entry(number: int, name: str, **overrides) -> dict:
    base = {
        "number": number,
        "name": name,
        "title": f"{name} title",
        "example": f"{name} example",
    }
    base.update(overrides)
    return base


def _minimal_catalog_dict() -> dict:
    return {
        "version": "1.0",
        "categories": [
            {
                "title": "CONTRACT, EXECUTION, AND COMMERCIAL STRUCTURE",
                "entries": [_entry(1, "requirement"), _entry(2, "contract_line_item")],
            }
        ],
    }


# ---------- name validation ---------- #


def test_entity_name_must_be_snake_case():
    with pytest.raises(ValidationError, match="snake_case"):
        EntityTypeDef(number=1, name="Requirement", title="t", example="e")
    with pytest.raises(ValidationError, match="snake_case"):
        EntityTypeDef(number=1, name="contract-line-item", title="t", example="e")
    # snake_case underscores allowed
    EntityTypeDef(number=1, name="contract_line_item", title="t", example="e")


def test_extra_fields_forbidden_on_entry():
    with pytest.raises(ValidationError):
        EntityTypeDef(
            number=1, name="requirement", title="t", example="e", made_up_field="x"
        )


# ---------- catalog loading ---------- #


def test_minimal_catalog_validates():
    cat = EntityCatalog.model_validate(_minimal_catalog_dict())
    assert cat.version == "1.0"
    assert len(cat.all_entries) == 2
    assert cat.entity_type_names == frozenset({"requirement", "contract_line_item"})


def test_fallback_mapping_uses_from_alias():
    # 'from' is a Python keyword — must come in via the alias.
    fm = FallbackMapping.model_validate({"from": "Plans/Policies/Manuals", "to": "document"})
    assert fm.from_pattern == "Plans/Policies/Manuals"
    assert fm.to == "document"


# ---------- rendering ---------- #


def test_render_part_d_includes_header_and_entries():
    cat = EntityCatalog.model_validate(_minimal_catalog_dict())
    rendered = cat.render_part_d()
    assert "PART D: THE 2 ENTITY TYPES" in rendered
    assert "1. REQUIREMENT - requirement title" in rendered
    assert "2. CONTRACT_LINE_ITEM - contract_line_item title" in rendered
    assert "─── CONTRACT, EXECUTION, AND COMMERCIAL STRUCTURE ───" in rendered


def test_render_omits_optional_fields_when_absent():
    cat = EntityCatalog.model_validate(_minimal_catalog_dict())
    rendered = cat.render_part_d()
    # Minimal entry has no metadata / signals — those labels should NOT appear.
    assert "Required metadata:" not in rendered
    assert "Content signals:" not in rendered
    assert "Distinction:" not in rendered


def test_render_quotes_multi_word_signals():
    data = _minimal_catalog_dict()
    data["categories"][0]["entries"][0]["content_signals"] = [
        "Contractor shall",
        "CLIN",
        '"already quoted phrase"',
        'has "internal" quotes here',
    ]
    cat = EntityCatalog.model_validate(data)
    rendered = cat.render_part_d()
    # Multi-word bare phrases get wrapped.
    assert '"Contractor shall"' in rendered
    # Single-token signals stay bare.
    assert ", CLIN," in rendered or rendered.endswith(" CLIN") or " CLIN," in rendered
    # Already-quoted strings are not double-wrapped.
    assert '""already quoted phrase""' not in rendered
    assert '"already quoted phrase"' in rendered
    # Strings with internal quotes are not double-wrapped.
    assert '"has "internal" quotes here"' not in rendered
    assert 'has "internal" quotes here' in rendered


def test_render_includes_forbidden_and_fallback_blocks():
    data = _minimal_catalog_dict()
    data["forbidden_types"] = ["other", "UNKNOWN"]
    data["fallback_mapping"] = [{"from": "Plans/Policies", "to": "document"}]
    data["example_classifications"] = [
        {"input": "CLIN 0001", "type": "contract_line_item", "note": "NOT 'concept'"}
    ]
    cat = EntityCatalog.model_validate(data)
    rendered = cat.render_part_d()
    assert "STRICTLY FORBIDDEN entity types (NEVER USE):" in rendered
    assert "❌ other, UNKNOWN" in rendered
    assert "FALLBACK MAPPING" in rendered
    assert "- Plans/Policies → document" in rendered
    assert '- "CLIN 0001" → contract_line_item (NOT \'concept\')' in rendered


def test_render_sub_patterns_for_customer_priority_shape():
    data = _minimal_catalog_dict()
    data["categories"][0]["entries"][0]["sub_patterns"] = [
        {"label": "STATED PRIORITY", "description": "Direct importance language"},
        {"label": "WEIGHTED PRIORITY", "description": "Evaluation factor emphasis"},
    ]
    cat = EntityCatalog.model_validate(data)
    rendered = cat.render_part_d()
    assert "Two sub-patterns:" in rendered
    assert "- STATED PRIORITY: Direct importance language" in rendered


def test_render_extraction_rule_wrapped_in_asterisks():
    data = _minimal_catalog_dict()
    data["categories"][0]["entries"][0]["extraction_rule"] = "Use sparingly."
    cat = EntityCatalog.model_validate(data)
    rendered = cat.render_part_d()
    assert "*** EXTRACTION RULE: Use sparingly. ***" in rendered


def test_disambiguation_rule_block_emitted():
    data = _minimal_catalog_dict()
    data["disambiguation_rules"] = [
        {
            "title": "REQUIREMENT vs WORKLOAD_METRIC",
            "body": '  "shall process repairs" → requirement\n  "500 repairs/month" → workload_metric',
        }
    ]
    cat = EntityCatalog.model_validate(data)
    rendered = cat.render_part_d()
    assert "─── DISAMBIGUATION RULES ───" in rendered
    assert "REQUIREMENT vs WORKLOAD_METRIC:" in rendered
    assert '"shall process repairs" → requirement' in rendered
