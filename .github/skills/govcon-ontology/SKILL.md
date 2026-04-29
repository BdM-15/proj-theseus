---
name: govcon-ontology
description: Authoritative, agent-readable specification of Project Theseus's 33-entity / 35-relationship federal-contracting ontology. USE WHEN extracting entities or relationships from any federal solicitation text — RFP, SOW, PWS, proposal instructions (UCF Section L or equivalent), evaluation criteria (UCF Section M or equivalent), attachments (UCF Section J or equivalent), FAR 16 task orders, FOPRs, BPA calls, OTAs, agency-specific formats; validating extraction output; extending the ontology with a new entity type or relationship; debugging "why didn't it tag this as a CLIN?"; or when any agent (Copilot, sub-agent, Theseus runtime) needs to produce or consume Theseus-graph-compatible structured output. The ontology is intentionally format-agnostic — entity types map to purpose, not UCF position. DO NOT USE FOR generic NER, non-federal contracting (state/local/commercial), or open-domain knowledge graphs. Acts as living documentation and a guardrail so agents extend the ontology consistently without spelunking source code.
license: MIT
metadata:
  # Phase 4j taxonomy — see docs/SKILL_TAXONOMY.md
  personas_primary: none
  personas_secondary: []
  shipley_phases: []
  capability: meta
  category: ontology
  version: 1.3.0
  status: active
  runtime: legacy
  authoritative_source: src/ontology/schema.py
---

# Theseus GovCon Ontology — Agent Spec

This skill is the **portable, machine-and-human-readable** version of the ontology defined in [`src/ontology/schema.py`](../../../src/ontology/schema.py). Use it whenever you need to think in Theseus vocabulary without reading Python source.

> **Authoritative source rule.** If this file disagrees with `src/ontology/schema.py`, the schema wins and this file must be updated. See [Cross-Cutting Change Checklist](../../../.github/copilot-instructions.md#cross-cutting-change-checklist).

## When to Use

- Extracting entities/relationships from federal RFP text
- Building or reviewing extraction prompts
- Validating that an LLM's structured output conforms to Theseus types
- Adding a new entity type or relationship type (extension workflow below)
- Explaining ontology choices to a teammate or evaluator

## The 33 Entity Types

Always emit `type` as **lowercase snake_case**. Entity `name` should be a canonical, deduplicable surface form (CLIN numbers, clause IDs, factor titles).

### Group A — Contract, Execution & Commercial Structure (9)

| Type                        | Detect on                                        | Example name                     |
| --------------------------- | ------------------------------------------------ | -------------------------------- |
| `requirement`               | "shall", "must", "will provide"                  | `R-014: 24/7 Help Desk Coverage` |
| `contract_line_item`        | CLIN/SLIN headings, priced line tables           | `CLIN 0001`                      |
| `pricing_element`           | Rates, fees, ceilings, escalation factors        | `Award Fee Pool 7%`              |
| `government_furnished_item` | GFE / GFP / GFI / GOTS lists                     | `GFP Vehicle Fleet`              |
| `deliverable`               | CDRL tables, "deliver…by…"                       | `CDRL A001`                      |
| `workload_metric`           | Numeric volume drivers (sorties, tickets, sq ft) | `12,500 sorties/year`            |
| `labor_category`            | Named LCATs in staffing tables                   | `Systems Engineer III`           |
| `performance_standard`      | KPIs, SLAs, AQLs, QASP rows                      | `99.9% Uptime`                   |
| `transition_activity`       | Phase-in/out, mobilization tasks                 | `30-Day Phase-In Plan`           |

### Group B — Document Structure, Authorities & Work Patterns (7)

| Type                      | Detect on                                       | Example name           |
| ------------------------- | ----------------------------------------------- | ---------------------- |
| `document_section`        | Numbered/lettered headings (L.3.4, M.2, C.5)    | `Section L.3.4`        |
| `document`                | Attachments, exhibits, annexes, standalone PDFs | `Attachment J-3 QASP`  |
| `amendment`               | "Amendment 0001", Q&A rounds                    | `Amendment 0003`       |
| `clause`                  | FAR/DFARS/agency clause IDs                     | `FAR 52.212-4`         |
| `regulatory_reference`    | DAFI / AR / MIL-STD / NIST SP IAW citations     | `NIST SP 800-171`      |
| `technical_specification` | ICDs, TDPs, MIL-DTL/MIL-PRF                     | `MIL-DTL-38999`        |
| `work_scope_item`         | PWS/SOW/SOO numbered tasks/objectives           | `Task 3.2 Network Ops` |

### Group C — Proposal & Evaluation Structure (5)

| Type                         | Detect on                                                                                                                 | Example name                           |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| `evaluation_factor`          | Factor headings + weights (UCF Section M or equivalent — incl. adjectival / LPTA)                                         | `Technical Approach (40%)`             |
| `subfactor`                  | Factor children (UCF Section M or equivalent)                                                                             | `Subfactor 1.2 Staffing (15%)`         |
| `proposal_instruction`       | "shall submit", page limits, format rules (UCF Section L or equivalent — may live inline in PWS or in a named attachment) | `L.3.4 Submit Past Performance Volume` |
| `proposal_volume`            | Volume I/II/III containers                                                                                                | `Volume I — Technical`                 |
| `past_performance_reference` | Reference contract tables, CPARS rows                                                                                     | `Contract W912-1234`                   |

### Group D — Strategic & Analytical Signals (3)

| Type                | Detect on                                                  | Example name                 |
| ------------------- | ---------------------------------------------------------- | ---------------------------- |
| `strategic_theme`   | Win themes / discriminators / proof points                 | `Mission Readiness Priority` |
| `customer_priority` | Explicit weighting language ("paramount", "most critical") | `Cybersecurity Is Paramount` |
| `pain_point`        | Government problem statements, deficiencies                | `Current Turnaround Delays`  |

### Group E — Standard Entities (9)

`organization`, `program`, `equipment`, `technology`, `location`, `event`, `person`, `compliance_artifact`, `concept`. Use these only when no Group A–D type fits.

## The 35 Relationship Types

Always emit `relationship_type` as **UPPERCASE_SNAKE**. Subject is the **source** entity, object is the **target**.

### Structural (6)

`CHILD_OF`, `ATTACHMENT_OF`, `CONTAINS`, `AMENDS`, `SUPERSEDED_BY`, `REFERENCES`

### Evaluation & Proposal — the proposal_instruction ↔ evaluation_factor Golden Thread (5)

`GUIDES` (instruction → factor), `EVALUATED_BY` (factor → instruction or evidence), `HAS_SUBFACTOR`, `MEASURED_BY`, `EVIDENCES`

### Work & Deliverables — Traceability Chain (8)

`PRODUCES`, `SATISFIED_BY`, `TRACKED_BY`, `SUBMITTED_TO`, `STAFFED_BY`, `PRICED_UNDER`, `FUNDS`, `QUANTIFIES`

### Authority & Governance (5)

`GOVERNED_BY`, `MANDATES`, `CONSTRAINED_BY`, `DEFINES`, `APPLIES_TO`

### Resource & Operational (4)

`HAS_EQUIPMENT`, `PROVIDED_BY`, `COORDINATED_WITH`, `REPORTED_TO`

### Strategic & Capture Intelligence (4)

`ADDRESSES`, `RESOLVES`, `SUPPORTS`, `RELATED_TO`

### Inference-Only — added by post-processing, do not emit during extraction (3)

`REQUIRES`, `ENABLED_BY`, `RESPONSIBLE_FOR`

## Output Contract

Structured extraction output **must** validate against the Pydantic models in `src/ontology/schema.py`:

```json
{
  "entities": [
    {
      "name": "CLIN 0001",
      "type": "contract_line_item",
      "description": "Base year operations FFP",
      "source_id": "chunk_abc"
    }
  ],
  "relationships": [
    {
      "source": "CLIN 0001",
      "target": "Task 3.2 Network Ops",
      "relationship_type": "PRICED_UNDER",
      "description": "...",
      "source_id": "chunk_abc"
    }
  ]
}
```

Names not in `VALID_ENTITY_TYPES` / `VALID_RELATIONSHIP_TYPES` will be **silently coerced** by `normalize_relationship_type()` to `RELATED_TO` with a WARN log. Don't rely on coercion — emit canonical types.

## Common Pitfalls (Battle-Tested)

See [`references/pitfalls.md`](./references/pitfalls.md) for the full list. The top 5:

1. **Tagging "shall" sentences as `clause`** — they are `requirement`. `clause` is reserved for FAR/DFARS/agency citations.
2. **Confusing `evaluation_factor` and `proposal_instruction`** — evaluation criteria (UCF Section M or equivalent) are `evaluation_factor`; submission instructions (UCF Section L or equivalent — may live inline in PWS or in a named attachment for non-UCF) are `proposal_instruction`. They are linked by `GUIDES` / `EVALUATED_BY`.
3. **Emitting `MEASURES` instead of `MEASURED_BY`** — it gets coerced but pollutes the graph. Always pick the canonical direction.
4. **Creating `document` entities for individual chapters** — chapters are `document_section`. `document` is for the whole RFP, attachments, amendments.
5. **Missing the proposal_instruction ↔ evaluation_factor golden thread** — every `evaluation_factor` should ideally have at least one `proposal_instruction` linked via `GUIDES`. If not, leave it for post-processing inference rather than guessing. Works on UCF (Section L↔M) and non-UCF solicitations alike.

## Extending the Ontology

To add a new entity or relationship type, follow the **Cross-Cutting Change Checklist** ([copilot-instructions.md](../../../.github/copilot-instructions.md)):

1. Add to `VALID_ENTITY_TYPES` / `VALID_RELATIONSHIP_TYPES` in [`src/ontology/schema.py`](../../../src/ontology/schema.py).
2. Update Pydantic model docstrings.
3. Update the extraction prompt at [`prompts/extraction/govcon_lightrag_native.txt`](../../../prompts/extraction/govcon_lightrag_native.txt) — Parts D (catalog), F (rules), J (output format).
4. Update multimodal prompts at [`prompts/multimodal/govcon_multimodal_prompts.py`](../../../prompts/multimodal/govcon_multimodal_prompts.py).
5. Update query/response prompts at [`prompts/govcon_prompt.py`](../../../prompts/govcon_prompt.py) (`rag_response`, `naive_rag_response`).
6. Update inference prompts under `prompts/relationship_inference/` if applicable.
7. Update `vdb_sync.py` normalization if a new relationship type.
8. Update **this file**.
9. Bump the extraction prompt version header.
10. Add fixtures to `tests/` and `tools/test_query_prompt.py`.

## References (load on demand)

- [`references/pitfalls.md`](./references/pitfalls.md) — full list of common extraction errors
- [`references/extraction_examples.md`](./references/extraction_examples.md) — worked examples per entity group
- [`references/lm_golden_thread.md`](./references/lm_golden_thread.md) — proposal_instruction ↔ evaluation_factor golden thread deep dive (UCF Section L↔M or non-UCF equivalent)
- [`references/relationship_directionality.md`](./references/relationship_directionality.md) — which side is source vs target for each rel type
