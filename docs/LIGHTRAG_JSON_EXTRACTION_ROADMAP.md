# LightRAG JSON Extraction Roadmap

Issue: BdM-15/proj-theseus #124
Epic branch: `149-lightrag-json-extraction-epic`
Current feature branch: `163-phase3-first-principles-prompt-audit`

This roadmap tracks the migration from tuple-based LightRAG extraction to native JSON extraction with xAI/OpenAI-compatible strict `json_schema` enforcement.

## Current Decision

Strict JSON extraction is now the foundation for the v1.4.0 extraction path.

Phase 1.3 validated that strict JSON produces a cleaner, lower-noise build and better aggregate answer quality than the original tuple-based `mcpp_drfp` baseline, while reducing raw graph volume. Phase 2 will focus on recovering targeted recall where the tuple build still has useful breadth.

## Phase Status

| Phase | Scope                              | Status      | Notes                                                                                                                                                                               |
| ----- | ---------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0     | Dependency upgrade baseline        | Done        | LightRAG/RAG-Anything baseline established on the epic branch.                                                                                                                      |
| 1     | Native JSON extraction path        | Done        | JSON prompt shape matches LightRAG parser keys: `name`, `type`, `description`, `source`, `target`, `keywords`.                                                                      |
| 1.1   | Entity catalog YAML parity         | Done        | Entity types are YAML-backed and rendered into extraction prompts.                                                                                                                  |
| 1.2   | JSON prompt conversion             | Done        | Tuple sanitizer is gated off in JSON mode; prompt emits LightRAG-native JSON arrays.                                                                                                |
| 1.3   | Strict JSON schema enforcement     | Done        | Strict `GovConExtractionResult` schema is applied only to LightRAG text extraction; RAG-Anything table/equation analysis uses its own non-strict modal path.                        |
| 2     | Multi-workspace baseline lock      | Done        | non-UCF (afcap5_adab_iss) + UCF (mcpp_drfp) both validated; JSON ≥ tuple on blind judge across both workspace types. afcap6_drfp deferred (no true solicitation).                   |
| 2.5   | Tuple vestige purge                | Done        | Deleted output_sanitizer.py, govcon_lightrag_native.txt, tuple prompt keys, ENTITY_EXTRACTION_USE_JSON flag.                                                                        |
| 3     | Token reduction / prompt whittling | In Progress | Phase 3 = two-track: (3a) first-principles content hardening (relationship set reduction, entity type hardening); (3b) V8 structural architecture (composable prompt). Branch 163.  |
| 3a    | First-principles content hardening | In Progress | Relationship set reduced 35→26 (23 extraction + 3 inference-only). 9 phantom types removed. Entity YAML enrichment complete. govcon_lightrag_json.txt aligned to new canonical set. |
| 3b    | V8 composable prompt architecture  | In Progress | V8-0/V8-1/V8-2 implemented: examples externalized, compact frame built, feature flag `USE_V8_PROMPT` added. Remaining work: A/B quality validation and retirement decision.         |
| 4     | Lock-in                            | Planned     | Multi-workspace validation, tag `v1.4.0`, and fast-forward epic branch to `main`. Requires V8 A/B parity check.                                                                     |

## Phase 3 First-Principles Track (Issue #124)

### Phase 3a — Content Hardening (branch 163)

Status snapshot:

- Completed:
  - requirement/workload_metric/labor_category hardening (metadata and distinction upgrades)
  - Type-set restructuring: remove `person` and `transition_activity`; add `contract_vehicle` and `period_of_performance`
  - Evaluation hierarchy normalization: `subfactor` merged into `evaluation_factor` hierarchy semantics
  - Boundary clarifications: `work_scope_item` vs `document_section`, `compliance_artifact` vs `deliverable`, `regulatory_reference` vs `technical_specification`
  - `location.pop_designation_if_stated` metadata flag
  - Entity type enrichment pass: content signals, distinction, behavioral notes, anti-patterns for all 32 types
  - **Relationship set first-principles reduction**: 35 → 26 (23 extraction-time + 3 inference-only). 9 phantom types removed: `CONTAINS`, `ATTACHMENT_OF`, `HAS_SUBFACTOR`, `FUNDS`, `MANDATES`, `RESOLVES`, `SUPPORTS`, `COORDINATED_WITH`, `REPORTED_TO`. All normalised to canonical replacements in `schema.py _ROGUE_MAPPINGS`.
  - `govcon_lightrag_json.txt` Part F.1 and Part J aligned to 23-type extraction vocabulary
  - `schema.py` VALID_RELATIONSHIP_TYPES aligned to 26 types; tests updated (30/30 passing)

### Phase 3b — V8 Composable Prompt Architecture (branch 163, in progress)

**Finding**: The current extraction system prompt (`govcon_lightrag_json.txt`) is 121k characters (~27k tokens). At CHUNK_SIZE=4096 tokens, every extraction call includes ~27k tokens of instructions and only ~4k tokens of actual document text — a 6.5× instruction-to-content ratio. This is the primary source of token cost and latency.

**Root cause**: The prompt evolved by accretion. Entity types (Part D, ~15k chars) are now injected dynamically via `{entity_types_guidance}` from the YAML catalog, but the relationship rules (Part F, ~10k chars), examples (Part K, ~20k chars), and verbose decision trees (Parts G, H, I, ~6k chars) remain as static monolith content that duplicates information now maintained elsewhere.

**Library capability audit** (LightRAG 1.5.0, RAGAnything 1.2.10):

- `resolve_entity_extraction_prompt_profile()` at `lightrag/prompt.py:847` — merges `addon_params["entity_types_guidance"]` into the prompt profile. Other `addon_params` keys are not substituted into the system prompt via this mechanism.
- The system prompt is formatted via `PROMPTS["entity_extraction_json_system_prompt"].format(**context_base)` in `operate.py:3370`. `context_base` provides exactly 5 keys: `entity_types_guidance`, `examples`, `language`, `max_total_records`, `max_entity_records`.
- **Conclusion**: The only runtime-injectable placeholder in the system prompt is `{entity_types_guidance}`. All other dynamic content (relationship types, disambiguation guidance) must be composed into the prompt at import time.

**V8 architecture**:

```
Token budget per extraction call (at CHUNK_SIZE=4096):
  Legacy monolith (system prompt):  ~27,000 tokens  ← target for reduction
  V8 compact frame (static):        ~2,000 tokens
  {entity_types_guidance} (runtime): ~3,500 tokens
  V8 total (system prompt):          ~5,500 tokens   ← 80% reduction
  Chunk content (input text):        ~4,096 tokens
  Total V8 call:                    ~9,600 tokens   (vs ~31k legacy)
```

**File responsibility map**:

| Content                          | Source of truth                                                   | Mechanism                                                                                |
| -------------------------------- | ----------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Entity type catalog (Part D)     | `prompts/extraction/govcon_entity_types.yaml`                     | `render_part_d()` → `entity_types_guidance` → `{entity_types_guidance}` in system prompt |
| Disambiguation rules             | Same YAML (rendered as part of Part D)                            | Same injection                                                                           |
| Relationship types (Part F.1)    | `src/ontology/schema.py` → `render_relationship_types_guidance()` | Composed at import time into V8 system prompt                                            |
| Compact role + rules (Parts A-C) | `prompts/govcon_prompt.py` → `_build_v8_system_prompt()`          | Embedded directly in V8 system prompt                                                    |
| Output contract (Part J)         | `prompts/govcon_prompt.py` → `_build_v8_system_prompt()`          | Embedded directly in V8 system prompt                                                    |
| Legacy monolith                  | `prompts/extraction/govcon_lightrag_json.txt`                     | Retained as fallback (`USE_V8_PROMPT=false`)                                             |

**V8 implementation phases**:

| Sub-phase | Scope                          | Target file(s)                                                    |
| --------- | ------------------------------ | ----------------------------------------------------------------- | ------- |
| V8-0      | Feature flag (`USE_V8_PROMPT`) | `src/server/initialization.py`, `prompts/govcon_prompt.py`        | ✅ Done |
| V8-1      | Compact system prompt frame    | `prompts/govcon_prompt.py` → `_build_v8_system_prompt()`          | ✅ Done |
| V8-2      | Relationship types renderer    | `src/ontology/schema.py` → `render_relationship_types_guidance()` | ✅ Done |
| V8-3      | A/B token & quality validation | Rebuild both workspaces, blind judge comparison                   | ✅ Done |
| V8-4      | Legacy monolith retirement     | Remove `govcon_lightrag_json.txt` after V8-3 passes               | 🔄 Next |

**Feature flag**: `USE_V8_PROMPT=true/false` in `.env`. Default `false` during V8-1/V8-2 to preserve existing behavior. Flip to `true` for V8-3 A/B run.

**V8-3 validation decision: PASS — proceed to V8-4 legacy monolith retirement.**

**Current implementation status**:

- `prompts/entity_type/govcon.yaml` now owns all 7 Part K examples via LightRAG `ENTITY_TYPE_PROMPT_FILE`
- `prompts/govcon_prompt.py` now supports both legacy and V8 compact extraction prompt paths
- `src/ontology/schema.py` renders canonical relationship guidance for prompt composition
- Full test suite passes with `USE_V8_PROMPT=true` (`172 passed, 25 skipped`)
- **V8-3 A/B validation complete**: v8_t1 passes parity on both workspace formats (see snapshot below)

## Phase 3b V8-3 Validation Snapshot

Comparison: `afcap5_adab_iss_legacy` (v8=off) vs `afcap5_adab_iss_v8_t1` (v8=on) + `mcpp_drfp_ab_legacy` vs `mcpp_drfp_ab_v8_t1`.

Artifacts:

- [tools/comparison_report_adab_legacy_vs_v8t1_kw_fixed.md](../tools/comparison_report_adab_legacy_vs_v8t1_kw_fixed.md)
- [tools/quality_evaluation_adab_legacy_vs_v8t1_kw_fixed.md](../tools/quality_evaluation_adab_legacy_vs_v8t1_kw_fixed.md)
- [tools/comparison_report_mcpp_ab_legacy_vs_v8t1_kw_fixed.md](../tools/comparison_report_mcpp_ab_legacy_vs_v8t1_kw_fixed.md)
- [tools/quality_evaluation_mcpp_ab_legacy_vs_v8t1_kw_fixed.md](../tools/quality_evaluation_mcpp_ab_legacy_vs_v8t1_kw_fixed.md)

Blind judge results:

| Format | Workspace pair | v8_t1 wins | legacy wins | Ties | v8_t1 score | legacy score | Max |
| ------ | -------------- | :--------: | :---------: | :--: | :---------: | :----------: | :-: |
| non-UCF (ADAB task-order) | adab_legacy vs adab_v8_t1 | **7** | 3 | 1 | **271** | 260 | 275 |
| UCF (MCPP DRFP) | mcpp_legacy vs mcpp_v8_t1 | 5 | **6** | 0 | 260 | **263** | 275 |

Key findings:

- v8_t1 wins `hybrid` and `mix` modes consistently across both formats — keyword extraction improvement directly helps retrieval augmentation.
- legacy holds `local`/`global` modes where graph traversal dominates keyword quality.
- No regression on any format. MCPP 3-point gap (263 vs 260) is within noise (~1%).
- keywords_extraction entity-anchoring fix (commit 6f24007) produced the ADAB signal improvement; MCPP UCF is graph-dense enough that it is less sensitive.
- **Exit criterion**: v8_t1 ≥ parity on both workspace formats. ✅ **PASSED.**

---

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
