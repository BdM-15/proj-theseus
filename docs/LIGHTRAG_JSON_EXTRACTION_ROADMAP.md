# LightRAG JSON Extraction Roadmap

Issue: BdM-15/proj-theseus #124
Epic branch: `149-lightrag-json-extraction-epic`
Current feature branch: `163-phase3-first-principles-prompt-audit`

This roadmap tracks the migration from tuple-based LightRAG extraction to native JSON extraction with xAI/OpenAI-compatible strict `json_schema` enforcement.

## Current Decision

Strict JSON extraction is now the foundation for the v1.4.0 extraction path.

Phase 1.3 validated that strict JSON produces a cleaner, lower-noise build and better aggregate answer quality than the original tuple-based `mcpp_drfp` baseline, while reducing raw graph volume. Phase 2 will focus on recovering targeted recall where the tuple build still has useful breadth.

## Phase Status

| Phase | Scope                              | Status      | Notes                                                                                                                                                             |
| ----- | ---------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Dependency upgrade baseline        | Done        | LightRAG/RAG-Anything baseline established on the epic branch.                                                                                                    |
| 1     | Native JSON extraction path        | Done        | JSON prompt shape matches LightRAG parser keys: `name`, `type`, `description`, `source`, `target`, `keywords`.                                                    |
| 1.1   | Entity catalog YAML parity         | Done        | Entity types are YAML-backed and rendered into extraction prompts.                                                                                                |
| 1.2   | JSON prompt conversion             | Done        | Tuple sanitizer is gated off in JSON mode; prompt emits LightRAG-native JSON arrays.                                                                              |
| 1.3   | Strict JSON schema enforcement     | Done        | Strict `GovConExtractionResult` schema is applied only to LightRAG text extraction; RAG-Anything table/equation analysis uses its own non-strict modal path.      |
| 2     | Multi-workspace baseline lock      | Done        | non-UCF (afcap5_adab_iss) + UCF (mcpp_drfp) both validated; JSON ≥ tuple on blind judge across both workspace types. afcap6_drfp deferred (no true solicitation). |
| 2.5   | Tuple vestige purge                | Done        | Deleted output_sanitizer.py, govcon_lightrag_native.txt, tuple prompt keys, ENTITY_EXTRACTION_USE_JSON flag.                                                      |
| 3     | Token reduction / prompt whittling | In Progress | Phase 3 now includes first-principles ontology hardening before prompt collapse. Type-set restructuring landed on branch 163 (commit `8a96098`).                  |
| 4     | Lock-in                            | Planned     | Multi-workspace validation, tag `v1.4.0`, and fast-forward epic branch to `main`.                                                                                 |

## Phase 3 First-Principles Track (Issue #124)

Status snapshot:

- Completed:
  - requirement/workload_metric/labor_category hardening (metadata and distinction upgrades)
  - Type-set restructuring: remove `person` and `transition_activity`; add `contract_vehicle` and `period_of_performance`
  - Evaluation hierarchy normalization: `subfactor` merged into `evaluation_factor` hierarchy semantics
  - Boundary clarifications:
    - `work_scope_item` vs `document_section`
    - `compliance_artifact` vs `deliverable`
    - `regulatory_reference` vs `technical_specification`
  - `location.pop_designation_if_stated` metadata flag
- In progress:
  - Uniform enrichment pass for remaining entity types (content signals, distinction, behavioral notes, anti-patterns)
- Planned after enrichment:
  - Prompt first-principles structure pass (collapse Part C redundancy now represented in YAML)

## Phase 1.3 Validation Snapshot

Comparison: original tuple `mcpp_drfp` vs strict JSON `mcpp_drfp_t4`.

Artifacts:

- [tools/comparison_report_mcpp_original_t4_quality.md](../tools/comparison_report_mcpp_original_t4_quality.md)
- [tools/quality_evaluation_mcpp_original_t4.md](../tools/quality_evaluation_mcpp_original_t4.md)

Operational noise improved:

| Metric              | Original tuple | Strict JSON t4 |
| ------------------- | -------------: | -------------: |
| Processing warnings |             23 |              0 |
| Processing errors   |              0 |              0 |
| Table parse errors  |              0 |              0 |
| Orphaned entities   |            140 |             41 |
| Orphan rate         |          2.80% |          1.55% |

Answer quality improved in the blind judge run:

| Metric                | Original tuple | Strict JSON t4 |
| --------------------- | -------------: | -------------: |
| Query wins            |              2 |              7 |
| Ties                  |              1 |              1 |
| Grand total           |        207/250 |        234/250 |
| Accuracy average      |            4.5 |            4.8 |
| Completeness average  |            3.9 |            4.4 |
| Specificity average   |            4.3 |            4.7 |
| Structure average     |            4.0 |            4.8 |
| Actionability average |            4.0 |            4.7 |

Raw graph coverage dropped and must be handled in Phase 2:

| Metric                   | Original tuple | Strict JSON t4 |
| ------------------------ | -------------: | -------------: |
| Neo4j entities           |          4,994 |          2,649 |
| Neo4j relationships      |          9,679 |          4,536 |
| VDB entities             |          4,994 |          2,649 |
| VDB relationships        |          8,603 |          4,212 |
| Critical GovCon entities |          3,526 |          1,762 |
| Critical entity share    |         70.60% |         66.52% |

## Phase 2 Validation Snapshot

### non-UCF: afcap5_adab_iss (tuple) vs afcap5_adab_iss_j1 (strict JSON)

Artifacts:

- [tools/comparison_report_afcap5_adab_iss_vs_j1.md](../tools/comparison_report_afcap5_adab_iss_vs_j1.md)
- [tools/comparison_report_afcap5_adab_iss_vs_j1_rerun.md](../tools/comparison_report_afcap5_adab_iss_vs_j1_rerun.md)
- [tools/quality_evaluation_afcap5_adab_iss_vs_j1.md](../tools/quality_evaluation_afcap5_adab_iss_vs_j1.md)

Answer quality (blind judge):

| Metric      | tuple baseline | strict JSON j1 |
| ----------- | -------------: | -------------: |
| Query wins  |              4 |              5 |
| Ties        |              1 |              1 |
| Grand total |        220/250 |        229/250 |

Query timing (warm cache, 10 queries):

| Workspace                 | Avg (s) | Median (s) |
| ------------------------- | ------: | ---------: |
| afcap5_adab_iss (tuple)   |    0.74 |          — |
| afcap5_adab_iss_j1 (JSON) |    0.64 |          — |

**Decision: JSON holds/beats tuple on non-UCF format. Phase 2 exit criterion cleared.**

### UCF: mcpp_drfp (tuple) vs mcpp_drfp_t4 (strict JSON)

Already captured in Phase 1.3 snapshot above. JSON won 7-2 (234/250 vs 207/250).

**Decision: JSON holds/beats tuple on UCF format. Phase 2 exit criterion cleared on both axes.**

### afcap6_drfp

Deferred — no true solicitation yet. Not used as a reference baseline.

---

## Phase 2 Focus

Phase 2 should preserve strict JSON as the main extraction path while testing whether recall gaps are best solved in main extraction, post-processing, or both.

Priority quality gaps from the original-vs-t4 judge run:

1. Evaluation factor scoring criteria and rating detail.
2. Full document hierarchy and UCF section coverage.
3. Pain points, strategic themes, and customer priorities.
4. Workload metrics and operational thresholds.
5. Clause/regulatory breadth where the tuple build extracted useful extra coverage.

Recommended Phase 2 workflow:

1. Build a fixed multi-workspace baseline: `mcpp_drfp`, `afcap6_drfp`, and at least one smaller non-UCF workspace.
2. Track both deterministic graph metrics and blind query quality. Do not use raw entity count as a quality proxy by itself.
3. Add targeted extraction prompt/schema guidance only where the strict JSON build misses proposal-critical facts.
4. Prefer post-processing algorithms for relationships and hierarchy gaps that main extraction cannot reliably infer from chunk-local context.
5. Only proceed to Phase 2.5 tuple vestige deletion after the strict JSON path holds or beats tuple quality on the fixed baseline.

## Count Reporting Rule

All user-facing final counts must be based on the fully completed processing state, after semantic post-processing and VDB sync have finished.

The final count block must distinguish:

- final Neo4j entities and relationships
- final VDB entity and relationship entries
- post-processing deltas such as inferred and synced relationships

Do not mix pre-post-processing counts into the final count section.
