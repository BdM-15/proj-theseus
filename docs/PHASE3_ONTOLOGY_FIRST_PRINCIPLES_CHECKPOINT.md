# Phase 3 Ontology First-Principles Checkpoint

Date: 2026-05-02
Branch: 163-phase3-first-principles-prompt-audit
Status: Research checkpoint (no ontology or prompt rewrite applied yet)

## Objective

Establish a first-principles decision baseline for entity/relationship structure before any major extraction prompt rewrite.

Priority order used for decisions:

1. Extraction fidelity on real federal solicitations (not token count)
2. End-to-end traceability (Section L to M to execution to evidence)
3. Schema enforceability (typed constraints, low ambiguity)
4. Interoperability with external procurement vocabularies and APIs

## Evidence Base

Internal sources reviewed:

- prompts/extraction/govcon_entity_types.yaml (catalog-driven entity types)
- src/ontology/schema.py (current canonical relationships)
- prompts/extraction/govcon_lightrag_json.txt (mandatory extraction relationship list)
- docs/.shipley_extracted.json term-mining summary (capture/proposal concept frequency)

External references reviewed:

- OCDS (Open Contracting Data Standard)
- ePO (EU eProcurement Ontology)
- PPROC (Public Procurement Ontology)
- SAM.gov Opportunities Public API field model
- CCCEV (Core Criterion and Core Evidence Vocabulary)

## High-Confidence Findings

1. The current catalog-driven entity types are structurally sound for federal proposal intelligence extraction.
2. The highest value improvements are not type-count changes, but stronger constraints and role semantics.
3. A terminology drift exists: multiple files still claim 43 canonical relationship types, but active extraction/schema lists are 35.
4. The ontology already aligns with external best practice patterns:
   - Lifecycle segmentation (OCDS/ePO)
   - Typed constraints and disjointness (PPROC)
   - Requirement-to-evidence framing (CCCEV)
   - Operational market fields (SAM: NAICS, set-aside, POP, deadlines, awardee)

## Keep/Merge/Split Matrix (Entity Types)

Legend:

- Keep: retain as-is
- Keep+: retain, add constraints/metadata clarity
- Merge?: candidate for future consolidation (not approved)
- Split?: candidate for future subdivision (not approved)

| #   | Entity Type                | Decision | Rationale                                                                                                   |
| --- | -------------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| 1   | requirement                | Keep+    | Core obligation primitive; highest downstream utility. Tighten modal/criticality checks.                    |
| 2   | contract_line_item         | Keep     | Distinct financial container; maps to CLIN/SLIN economics.                                                  |
| 3   | pricing_element            | Keep     | Needed to represent rate/fee/escalation logic separate from line items.                                     |
| 4   | government_furnished_item  | Keep     | Distinct Gov-provided resource class; not equivalent to generic equipment.                                  |
| 5   | deliverable                | Keep+    | Essential for compliance and CDRL traceability; enforce stronger link to requirement and submission target. |
| 6   | workload_metric            | Keep+    | High signal for BOE/staffing; tighten quantitative metadata completeness.                                   |
| 7   | labor_category             | Keep+    | Critical for staffing realism and key-personnel extraction; tighten key-person metadata semantics.          |
| 8   | performance_standard       | Keep     | Required for measurable requirement evaluation (SLA/KPI/QASP).                                              |
| 9   | transition_activity        | Keep     | Transitional work is behaviorally distinct from steady-state scope.                                         |
| 10  | document_section           | Keep     | Structural anchor needed for hierarchy and context reconstruction.                                          |
| 11  | document                   | Keep+    | Preserve separation from section; add stronger subtype tags (attachment/exhibit/annex/manual).              |
| 12  | amendment                  | Keep     | Temporal/version control primitive for supersession logic.                                                  |
| 13  | clause                     | Keep     | Federal acquisition authority class is independently actionable.                                            |
| 14  | regulatory_reference       | Keep     | Distinct from clauses and technical specs; policy authority role.                                           |
| 15  | technical_specification    | Keep     | Engineering authority needs separation from policy authority.                                               |
| 16  | work_scope_item            | Keep+    | Execution unit with very high extraction volume; tighten relation expectations to requirement/deliverable.  |
| 17  | evaluation_factor          | Keep     | Core M-side scoring structure.                                                                              |
| 18  | subfactor                  | Keep     | Required for granular M decomposition and weighting.                                                        |
| 19  | proposal_instruction       | Keep     | Core L-side authoring and compliance behavior driver.                                                       |
| 20  | proposal_volume            | Keep     | Distinct packaging object useful for GUIDES/page-limit controls.                                            |
| 21  | past_performance_reference | Keep+    | Important evidence object; tighten evidence linkage requirements.                                           |
| 22  | strategic_theme            | Keep     | Essential capture/proposal reasoning primitive.                                                             |
| 23  | customer_priority          | Keep     | Independent strategic demand signal.                                                                        |
| 24  | pain_point                 | Keep     | Distinct from priority; needed for RESOLVES/ADDRESSES logic.                                                |
| 25  | organization               | Keep+    | Keep broad class; introduce role metadata (customer/incumbent/offeror/sub).                                 |
| 26  | program                    | Keep     | Distinct acquisition context node for cross-document alignment.                                             |
| 27  | equipment                  | Keep     | Needed for physical asset references outside GFI semantics.                                                 |
| 28  | technology                 | Keep     | Needed for stack/capability references separate from equipment.                                             |
| 29  | location                   | Keep     | Independent POP and geospatial anchor class.                                                                |
| 30  | event                      | Keep     | Supports milestone and meeting semantics distinct from document structure.                                  |
| 31  | person                     | Keep     | Required for key personnel, POCs, named authorities.                                                        |
| 32  | compliance_artifact        | Keep+    | Critical for evidence chain; consider future split by lifecycle phase only if precision demands it.         |
| 33  | concept                    | Keep     | Safety-valve abstraction class needed for non-canonical but valid domain concepts.                          |

Decision summary:

- Approved merges: 0
- Approved splits: 0
- Approved keep/constraint hardening: 10 entity types

## Relationship Model Checkpoint

Current active canonical set size: 35

- This count is consistent between:
  - src/ontology/schema.py
  - prompts/extraction/govcon_lightrag_json.txt (F.1 list)

Drift to correct:

- Several comments/docs/UI strings still claim 43 relationship types.
- This should be corrected to avoid governance confusion and test/spec mismatch.

First-principles decision:

- Do not expand relationship vocabulary during this phase.
- Improve relation quality by better extraction constraints and validation tests before adding new types.

## Cross-Standard Mapping (Practical Implications)

1. PPROC pattern adopted: stronger typing over vocabulary growth
   - Favor domain/range and disjoint checks over adding synonyms.
2. OCDS/ePO pattern adopted: lifecycle continuity
   - Maintain explicit edges across instruction -> evaluation -> work -> deliverable -> evidence.
3. CCCEV pattern adopted: requirement-to-evidence rigor
   - Enforce that evidentiary entities are not orphaned from governing requirement/evaluation context.
4. SAM field reality adopted: operational metadata matters
   - Preserve explicit support for NAICS, set-aside, POP, response deadlines, awardee context where present.

## TDD Quality Gate Recommendations (Pre-Rewrite)

Before any major prompt rewrite commit, gate on:

1. Structural coverage floor
   - No regression in extraction of: proposal_instruction, evaluation_factor, requirement, work_scope_item, deliverable.
2. Golden-thread connectivity floor
   - L->M->execution->evidence path rate does not regress.
3. Authority traceability floor
   - clause/regulatory_reference links to governed/mandated entities do not regress.
4. Workload realism floor
   - workload_metric and labor_category extraction/link rates do not regress.
5. Hallucination/rogue type floor
   - Invalid entity_type and relationship_type incidence does not increase.

## Recommended Next Step

Proceed with Phase 3 prompt rewrite only under this guardrail:

- Rewrite for clarity and extraction precision
- No ontology cardinality changes (33/35) in the first rewrite wave
- Apply drift cleanup for "43" references as a separate, explicit consistency change
