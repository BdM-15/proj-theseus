"""
Strict JSON Schema for entity/relationship extraction (Phase 1.3, issue #124).

This module builds the JSON Schema passed to xAI's strict structured-output mode
via OpenAI-compatible `response_format={"type": "json_schema", ...}`.

The schema MIRRORS the field names LightRAG 1.5.0's `_process_json_extraction_result`
parser (in `lightrag.operate`) reads from each object:

    entities[]:      {name, type, description}
    relationships[]: {source, target, keywords, description}

By passing this schema to xAI with `strict: true`, the model is forced to:
  - Produce the exact field names the parser expects (no `entity` / `subject` drift).
    - Pick `type` from the catalog-backed entity-type enum (no invented types).
  - Always include all required fields (no missing `description`, no missing `keywords`).

NOTE on `keywords`: xAI strict-mode validation rejects JSON-Schema `pattern`
(empirically confirmed 2025-11 — schemas with `pattern` return HTTP 400
"Invalid arguments"). The first-token-must-be-canonical-relationship-type rule
from Part J is therefore enforced via (a) the extraction prompt, and (b)
downstream `normalize_relationship_type()` in `src/ontology/schema.py` which
applies rogue-type mappings and falls back to RELATED_TO. xAI's enum support
on the entity `type` field still works, which is the bigger recall lever.

Why this beats relying on the prompt alone (Phase 1.2 baseline):
  - mcpp_drfp baseline (TUPLE)        : 4994 entities / 8603 relationships
  - mcpp_drfp_t1 (JSON, no schema)    : 2614 entities / 4245 relationships  (-48% / -51%)
  Live API smoke test confirmed strict mode returns the exact shape; json_object
  alone returns improvised shapes (`{entity, type}`, `{subject, relation, object}`)
  that LightRAG's parser drops.
"""

from __future__ import annotations

from typing import Any

from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES


# ─────────────────────────────────────────────────────────────────────────────
# Excluded inference-only relationship types (produced by post-processing
# algorithm 8 — NOT extracted from chunks). Listing them in the extraction
# pattern would invite the model to emit them inappropriately during chunk
# extraction. See `src/inference/` for the inference-time set.
# ─────────────────────────────────────────────────────────────────────────────
_INFERENCE_ONLY_REL_TYPES: frozenset[str] = frozenset({
    "REQUIRES", "ENABLED_BY", "RESPONSIBLE_FOR",
})


def _extraction_relationship_types() -> list[str]:
    """Canonical extraction-time relationship types (sorted for deterministic output).

    Currently used only for documentation / future schema variants — the live
    schema does NOT include a `pattern` constraint on `keywords` because xAI
    strict mode rejects regex patterns. Normalization happens downstream.
    """
    return sorted(VALID_RELATIONSHIP_TYPES - _INFERENCE_ONLY_REL_TYPES)


def build_extraction_json_schema() -> dict[str, Any]:
    """
    Build the strict JSON Schema for `response_format={"type": "json_schema", ...}`.

    Returns a dict in OpenAI's `json_schema` envelope:
        {"name": "...", "strict": True, "schema": {...}}

    Strict mode requirements honored:
      - Every object has `additionalProperties: false`.
      - Every property is listed in `required` (strict mode does not allow
        optional properties; downstream parsing tolerates empty strings).
    """
    entity_type_enum = sorted(VALID_ENTITY_TYPES)

    schema: dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "required": ["entities", "relationships"],
        "properties": {
            "entities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["name", "type", "description"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Canonical entity name (Title Case for sections, exact citation for clauses).",
                        },
                        "type": {
                            "type": "string",
                            "enum": entity_type_enum,
                            "description": "Entity type from the catalog-backed govcon ontology.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Comprehensive description with embedded metadata (criticality, modal_verb, threshold, etc.).",
                        },
                    },
                },
            },
            "relationships": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["source", "target", "keywords", "description"],
                    "properties": {
                        "source": {
                            "type": "string",
                            "description": "Source entity name (must match an entity in entities[]).",
                        },
                        "target": {
                            "type": "string",
                            "description": "Target entity name (must match an entity in entities[]).",
                        },
                        "keywords": {
                            "type": "string",
                            "description": "First comma-separated token MUST be one of the canonical UPPERCASE relationship types (enforced by prompt + downstream normalize_relationship_type); remainder is free-form descriptive cues.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Explanation of the semantic relationship between source and target.",
                        },
                    },
                },
            },
        },
    }

    return {
        "name": "GovConExtractionResult",
        "strict": True,
        "schema": schema,
    }


def build_response_format() -> dict[str, Any]:
    """Convenience wrapper: returns the full `response_format` value for OpenAI/xAI clients."""
    return {
        "type": "json_schema",
        "json_schema": build_extraction_json_schema(),
    }
