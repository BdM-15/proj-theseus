"""
Coherence tests for the production govcon entity catalog YAML.

These guard against drift between:

  * `prompts/extraction/govcon_entity_types.yaml` (single source of truth)
  * `src/ontology/schema.py::VALID_ENTITY_TYPES`
  * The 33-type contract documented in `.github/copilot-instructions.md`.

If you add or remove an entity type, you MUST update the YAML *and*
re-run this test. After Phase 1.1c lands, `VALID_ENTITY_TYPES` will be
derived from the YAML directly and these tests become tautological for
the count assertion — they remain valuable as a guard against the YAML
silently losing entries.
"""
from __future__ import annotations

from src.ontology.entity_catalog import get_default_catalog
from src.ontology.schema import VALID_ENTITY_TYPES


def test_yaml_loads_and_has_33_entity_types():
    cat = get_default_catalog()
    assert len(cat.all_entries) == 33, (
        f"Expected exactly 33 entity types, got {len(cat.all_entries)}. "
        "If you intentionally added or removed a type, update the cross-cutting "
        "checklist in .github/copilot-instructions.md."
    )


def test_yaml_entity_names_match_valid_entity_types():
    cat = get_default_catalog()
    yaml_names = cat.entity_type_names
    schema_names = frozenset(VALID_ENTITY_TYPES)

    only_in_yaml = sorted(yaml_names - schema_names)
    only_in_schema = sorted(schema_names - yaml_names)
    assert not only_in_yaml and not only_in_schema, (
        f"Drift between YAML and schema.\n"
        f"  YAML only:   {only_in_yaml}\n"
        f"  Schema only: {only_in_schema}"
    )


def test_yaml_entity_numbering_is_contiguous_1_to_33():
    cat = get_default_catalog()
    numbers = sorted(e.number for e in cat.all_entries)
    assert numbers == list(range(1, 34)), f"Entity numbering must be 1..33, got {numbers}"


def test_yaml_categories_match_documented_five():
    cat = get_default_catalog()
    titles = [c.title for c in cat.categories]
    assert titles == [
        "CONTRACT, EXECUTION, AND COMMERCIAL STRUCTURE",
        "DOCUMENT STRUCTURE, AUTHORITIES, AND WORK PATTERNS",
        "PROPOSAL AND EVALUATION STRUCTURE",
        "STRATEGIC AND ANALYTICAL SIGNAL",
        "STANDARD ENTITIES",
    ], f"Category titles drifted: {titles}"


def test_render_part_d_round_trip_contains_every_entity_name():
    cat = get_default_catalog()
    rendered = cat.render_part_d()
    for name in cat.entity_type_names:
        assert name.upper() in rendered, f"Rendered Part D missing {name!r}"


def test_render_part_d_contains_disambiguation_and_forbidden_blocks():
    cat = get_default_catalog()
    rendered = cat.render_part_d()
    assert "─── DISAMBIGUATION RULES ───" in rendered
    assert "STRICTLY FORBIDDEN entity types (NEVER USE):" in rendered
    assert "FALLBACK MAPPING" in rendered
    assert "Example Classifications (follow these patterns):" in rendered


def test_no_forbidden_type_is_a_valid_entity_type():
    cat = get_default_catalog()
    overlap = cat.entity_type_names & {f.lower() for f in cat.forbidden_types}
    assert not overlap, f"Forbidden types overlap valid entity names: {overlap}"
