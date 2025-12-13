# Lessons Learned: Branches 021–040 (LightRAG/RAG-Anything GovCon Pipeline)

> **Scope note (important):** This repository does **not** contain a `021` branch ref (`origin/021` is missing). The closest “early stable” baseline ref available is `origin/020-user-prompt-integration`, which is the **merge-base** of `origin/022`. Branch `origin/022` includes a “Perfect Run Achieved” commit and serves as the best available proxy for the quality state you described as “021/early stable”.
>
> This report is **non-destructive**: no checkouts, no commits, no pushes. It is based on ref-based `git log`/`git diff` inspection of the available branch heads in the `022`–`040` lineage.

## Executive Summary

The pipeline’s quality degradation followed a familiar pattern:

- **Baseline quality (≈021/022)** was achieved primarily by strong, domain-specific extraction prompts + a stable ingestion flow. The “intelligence” largely lived in **high-precision ontology definitions** (18 GovCon entity types) and extraction rules.
- Subsequent branches attempted to add “smartness” via **multimodal/table ingestion**, **Neo4j-centric post-processing**, **parallel extraction/post-processing**, **prompt compression/rewrites**, and **query-time overrides**.
- Many of those attempts unintentionally **shifted the system’s center of gravity** from “precise extraction with simple retrieval” to “complex, fragile orchestration”. This introduced:
  - **Noise amplification** (tables/synthetic chunks; aggressive relationship inference)
  - **Non-determinism** (parallelism + racey storage/finalization)
  - **Schema rigidity in hot paths** (dropped/failed extractions instead of graceful degradation)
  - **Prompt regressions** (compressed/rewritten prompts losing guardrails)
  - **Retrieval dilution** (entity descriptions becoming near-duplicate compliance text; overly wide retrieval settings)

In other words: the system increasingly optimized for *pipeline sophistication* rather than *answer relevance*. The best ideas (schema validation, dedup, query-time ontology hints, post-processing descriptions) often appeared, but were sometimes placed in the **critical path** (where failures are catastrophic) instead of behind flags or post-processing steps.

**Primary lesson:** Reset to the early stable baseline and reintroduce improvements **one at a time**, with flags, metrics, and strict guardrails to preserve extraction precision and retrieval diversity.

## Reference Defaults (Upstream Alignment)

When deciding what to keep vs. avoid, treat upstream defaults as a “stability anchor”:

- **LightRAG** defaults: `https://github.com/HKUDS/LightRAG`
  - Uses its own storage conventions (e.g., `rag_storage/<workspace>/kv_store_*.json`, GraphML outputs).
  - Query behavior is tuned for generic use; heavy override logic should be minimal and measurable.
- **RAG-Anything / MinerU** defaults: (project integration varies by version; keep multimodal parsing close to upstream patterns).

## Timeline of Branches (022–040)

> Table uses **retrieval quality effect** as a qualitative proxy (↑/↓/≈) based on the nature of diffs and regression notes embedded in branch docs/commits.

| Branch ref (found) | Key changes (diff-based) | Intended goal | Observed impact / likely outcome | Retrieval quality effect |
|---|---|---|---|---|
| **Baseline candidate:** `origin/020-user-prompt-integration` | Prompt/query docs cleanup, workload query simplification | Stabilize prompt system & user queries | Reasonably stable baseline; fewer confusing examples | ≈ (baseline) |
| `origin/022-ontology-split-performance-metric` | Added Pydantic JSON extractor; ontology split (`requirement` vs `performance_metric`); metric decomposition; changes to routes + inference flow | Improve workload prompting + extraction precision | **Good direction**: separating metrics from requirements reduces “workload_driver contamination” and improves downstream query clarity | ↑ |
| `origin/022` (“Perfect Run Achieved”) | Added compressed prompt artifacts + extensive “perfect run” documentation; minor code tweaks | Reduce prompt tokens while preserving behavior | Likely still high quality because compression artifacts were additive and baseline prompts remained available | ↑ (documented “perfect run”) |
| `origin/022a-prompt-compression` | Introduced `USE_COMPRESSED_PROMPTS` support; heavily edited/shortened relationship inference prompts; removed many docs/examples | Cut token costs + speed up | **High regression risk**: compressing relationship rules often removes edge-case guardrails; “shorter prompts” can increase hallucinated links or generic answers | ↓/≈ (depends on flag) |
| `origin/022a-table-ontology-processing` | Added **table ontology processing** + “synthetic chunks” for table entities; new table prompt; tests for table retrieval | Improve table extraction and retrieval | **Likely major regression source**: tables can explode entity counts, introduce duplicates, and dominate retrieval, causing generic/flattened answers | ↓↓ |
| `origin/022b-multimodal-ontology-integration` | Removed earlier table processor; added multimodal processor; fixed “premature semantic post-processing during sequential uploads” | Make multimodal ingestion safe and cumulative | **Good fix**: moving post-processing out of per-upload critical path prevents partial KG pollution | ↑/≈ |
| `origin/022c-new-app-cleanup` | Merge/consolidation | Cleanup | Neutral | ≈ |
| `origin/023-verbatim-extraction-refactor` (+ `origin/023a-stream-false-fix`) | xAI SDK migration; `stream=False` to prevent truncation; schema cleanup (remove `source_text`); major code/doc moves | Fix truncation and simplify schema | **Good operational fix** (`stream=False`). But large refactors + removals can easily drop useful enrichment or reduce granularity if extraction outputs become thinner | ↑ for stability, risk ↓ for granularity |
| `origin/025-entity-type-schema-enforcement` | Enforced entity types via Pydantic; removed large chunks of inference/graph IO modules; added audits/fix tools | Eliminate invalid types and stabilize ontology | **Mixed**: type enforcement is good, but removing cleanup/graph ops risks losing relationships or silently dropping entities. Needs graceful fallback | ↑/↓ (implementation-sensitive) |
| `origin/026-extraction-enhancements` | BOECategory enforcement with fallback; prompt enhancements for `performance_metric` & `strategic_theme` | Improve metadata structure | **Good idea**, but can increase extraction complexity; if validation is strict in hot path, it can reduce recall | ↑/≈ |
| `origin/027-query-config-grok4-2M` | File citation formatting, logging fixes | Improve answer readability | Mostly positive; unlikely to change retrieval itself | ↑ |
| `origin/028-parallel-chunk-extraction` | Parallel chunk + multimodal extraction; large docs/agent framework updates | Speed up ingestion | **Risk**: parallel ingestion can create nondeterministic ordering/partial writes; this often manifests as “lost granularity” or inconsistent graph shape | ↓/≈ |
| `origin/029-semantic-postprocessing-optimization` | Full parallel semantic post-processing; algorithm-specific batching; many new tests | Scale relationship inference | **Common regression vector**: relationship inference at scale tends to add noisy edges and blur retrieval signals unless extremely constrained | ↓↓ |
| `origin/030-pydantic-llm-utilities` | Added LLM client + Pydantic parsing utilities; pipeline enhancements; more schema fields | Increase robustness + schema enforcement | Good components, but if used to *reject* rather than *repair* extraction, can reduce recall and lead to generic answers | ↑/↓ |
| `origin/032-algo-7-cdrl-pattern-enhancement` | Three-phase KG processor + Neo4j dedup; expanded Algorithm 7 patterns; more orchestration | Fix CDRL/attachment linking; deduplicate graph | **Mixed**: targeted Algorithm 7 improvements can help, but broad orchestration increases fragility and can over-normalize entities | ↑ for CDRL, ↓ for overall retrieval diversity |
| `origin/034-multimodal-ontology-fix` | “Use full ontology extract() for multimodal items” | Fix multimodal parity | Positive bug fix | ↑ |
| `origin/037-prompt-compression-intelligence-first` | Huge “extraction_v2” prompt architecture, schema mirrors, relationship extraction rules; modifies extractor & post-processor; explicitly documents regression | Lower tokens + “intelligence-first” prompts | **Documented regression**: large prompt rewrites tend to change what’s extracted (and how), harming retrieval unless validated against baseline metrics | ↓↓ |
| `origin/039-pydantic-schema-llm-guidance` | Restore RAG-Anything pipeline with Pydantic adapter; remove duplicate multimodal extraction; algorithm brittleness audit; changes to semantic post-processing | Improve robustness, reduce duplicate work | Good direction: treat brittleness explicitly and reduce duplicate calls; still significant churn in inference logic | ↑/≈ |
| `origin/039-algorithm-2-llm-discovery` | Replace Algorithm 2 keyword matching with LLM discovery | Reduce brittleness | **Tradeoff**: better recall, but increased variability/hallucination risk and cost; needs strict grounding | ↑/↓ |
| `origin/feature/040-issue46-ontology-query-bounded-entity-description` (≈040) | Added query-time ontology context builder; query overrides; **description enrichment** to prevent “description = raw snippet” retrieval collapse; MinerU table handling utilities | Restore query quality via query-time framing + better entity descriptions | Promising: explicitly addresses a known LightRAG failure mode (duplicate descriptions). However, very high retrieval budgets can still dilute relevance if not carefully tuned | ↑ (if bounded), ↓ (if too wide) |

### Missing numeric branches

The following numeric branch labels from the prompt do not appear as branch refs in this repo snapshot: **021, 024, 031, 033, 035, 036, 038, 040**.

- `031` and `038` **did exist as merge history** (e.g., commits merging `031-neo4j-driver-fix` and `038-table-analysis-chunk-format`), but the branch refs are no longer present.
- `040` exists as `origin/feature/040-issue46-ontology-query-bounded-entity-description`.

## What Worked (Worth Keeping / Reapplying Cleanly)

### Extraction & schema ideas (keep, but place carefully)

- **Ontology split for workload clarity** (`requirement` vs `performance_metric`) from the 022 line.
  - Rationale: reduces the “everything becomes a requirement” failure mode.
- **Pydantic validation as a *repair layer*, not a gate**.
  - Keep “graceful fallback” patterns (e.g., BOECategory fallback) and avoid dropping whole chunks.
- **xAI SDK + `stream=False` to prevent truncation** (Issue #6 fixes in the 023 line).
  - This is pure reliability gain.

### Post-processing ideas (best ROI when moved off the critical path)

- **Description enrichment that preserves retrieval diversity** (040):
  - Avoid putting raw compliance snippets into `description` for every node.
  - Prefer: `evidence_snippet` (grounding) + compact semantic `description` for query-critical types.
- **Pick the *best* evidence chunk per entity** (040’s `best_chunk_id` / `context_snippet` enrichment).
  - This is a strong “cheap heuristic” that improves grounding without LLM calls.

### Query-time improvements (good if small and bounded)

- **Compact query-time ontology hints** (040 `src/query/ontology_context.py`):
  - Target entity-type hints and UCF L/M framing can reduce generic answers without mega-prompts.
- **Override prompts stored as modular files** (`prompts/query/*`) is good hygiene, *if overrides stay minimal*.

## Pitfalls & Failed Experiments (What to Avoid)

### 1) Table → synthetic chunk explosion

Branch `022a-table-ontology-processing` is a classic regression pattern:

- Tables produce **many shallow entities** (line items, headers, fragments).
- “Synthetic chunks” can become retrieval magnets, outcompeting narrative sections.
- Net effect: answers become **generic, flattened, and less grounded** in the right evidence.

Recommendation: keep tables **separate** (tagged chunk type, lower retrieval weight, or only used for specific queries like CLIN/price/CDRL tables).

### 2) Over-parallelization in ingestion and post-processing

Parallel extraction (`028`) and parallel relationship inference (`029`) can:

- Create **nondeterministic** graph shape across runs.
- Produce partial writes and “premature post-processing” bugs.
- Increase relationship noise faster than any cleanup can remove.

Recommendation: parallelize only where idempotent and order-independent; batch writes; run post-processing only after ingestion completes.

### 3) Relationship inference as a default “always-on” layer

Aggressive relationship inference (multiple algorithms, expanded patterns, LLM discovery) tends to:

- Add edges that *feel plausible* but are **low-value for retrieval**.
- Create a “noisy KG” where entity similarity collapses and retrieval becomes less selective.

Recommendation: gate relationship inference behind explicit switches, and keep only a **small number** of high-precision relationships that directly improve query answering (e.g., Section L ↔ M mappings, evaluation hierarchy, CDRL references).

### 4) Prompt compression/rewrites without baseline parity tests

Compression is not inherently bad, but two consistent failure modes appeared:

- Compressed prompts omit “negative instructions” and edge-case rules.
- Large rewrites (“extraction_v2”) change the extraction distribution.

Recommendation: treat prompt changes like code changes: diff them, run baseline queries, compare entity counts/coverage, and only enable by default after passing parity thresholds.

### 5) Neo4j-centric orchestration as the “spine” of the pipeline

Neo4j can be valuable for persistence and analytics, but using it as the “spine” while rapidly changing schemas and post-processing logic tends to:

- Lock in noisy early design decisions.
- Increase coupling and break multi-doc batching/processing flows.

Recommendation: keep Neo4j as a **storage backend**, not the primary driver of pipeline control flow.

## Recommendations for a Reset (Selective Reintroduction Plan)

### Reset principles

- **Start from `021`** (or, in this repo snapshot, the closest proxy: `origin/022` “Perfect Run” baseline).
- Preserve:
  - **18-entity ontology** and the refined extraction prompts that produced the “perfect run”.
  - The stable ingestion flow (no premature post-processing).
- Reintroduce changes **one at a time** under flags, with a repeatable evaluation harness.

### Stepwise reintroduction (high-signal, low-risk first)

1. **Reliability fixes**
   - Keep xAI SDK truncation fixes (`stream=False`).
   - Keep clean file-path citations.

2. **Schema enforcement (soft)**
   - Use Pydantic to normalize/repair outputs.
   - Never reject an entire chunk because one entity is invalid.

3. **Query-time minimal ontology context**
   - Use a compact hint block (entity types + UCF L/M hint) only.
   - Avoid huge token budgets; start close to LightRAG defaults and widen only if necessary.

4. **Description enrichment (post-processing)**
   - Implement the “description diversity” approach: `evidence_snippet` + short semantic `description`.
   - Keep LLM description generation batched and only for a small subset of types.

5. **Tables (carefully sandboxed)**
   - Ingest tables, but mark them explicitly and down-weight retrieval.
   - Avoid synthetic chunks unless you can prove they improve *specific* queries.

6. **Relationship inference (surgical)**
   - Start with only the few relationship algorithms that show consistent quality gains.
   - Add hard constraints and evaluation metrics before enabling any LLM-driven discovery.

### How to prevent repeating the same regressions

- **Baseline parity tests**:
  - Entity counts per type (within a tolerance band)
  - “Known good” query suite (workload, eval factors, compliance items)
  - Retrieval diversity checks (avoid all entities sharing near-identical descriptions)
- **Feature flags everywhere**:
  - Prompt compression
  - Table extraction
  - Each inference algorithm
  - Any query override profile

## Appendix: Evidence from Git Diffs (High-Signal Highlights)

- `022a-table-ontology-processing` introduced new table processing + tests and large-scale prompt shifts.
- `028` introduced parallel extraction.
- `029` massively expanded parallel semantic post-processing.
- `037` introduced a large new prompt architecture (`prompts/extraction_v2/*`) and explicitly documents regression.
- `040` introduced query-time context + description enrichment that explicitly calls out a key LightRAG retrieval failure mode: **putting raw snippets in `description` collapses retrieval diversity**.

---

*If you want, I can also generate a concise “diff index” appendix (per-branch: key files changed + 3–5 bullet findings) without adding any new code—just a deeper textual analysis of the same diff evidence.*
