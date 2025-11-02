# Hybrid Extraction with Reasoning Adjudication – Implementation Plan

Last updated: 2025-11-01

## Executive summary

Objective: Reduce misclassification between requirement and submission_instruction by adding a lightweight adjudication phase that retypes only the ambiguous cases using a reasoning LLM, while keeping fast non-reasoning extraction for throughput.

Expected impact: Significant precision gains on proposal-related instructions (e.g., "shall submit/provide/include" + CDRL/Section L contexts) with minimal latency/cost overhead.

Scope: Minimal, self-contained additions on top of main; no library forks; fully gated by an environment toggle.

---

## Goals and non-goals

- Goals
  - Improve precision/recall for submission_instruction without regressing requirement extraction
  - Keep extraction fast (non-reasoning) and add a targeted reasoning pass only where needed
  - Persist retyped entity types back to GraphML before relationship inference
  - Provide auditability of retyping decisions
- Non-goals
  - Replacing the base extraction model or restructuring LightRAG/RAG-Anything internals
  - Changing relationship inference algorithms (Phase 6) beyond better inputs

---

## High-level design

Two-pass hybrid pipeline:

1. Pass 1 – Bulk extraction (status quo)

- Keep current ingestion (RAG-Anything + LightRAG) and Option C structured output.
- Validate entities (corrective validation) as implemented.

2. Pass 1.5 – Reasoning adjudication (new Phase 5a)

- Identify ambiguous entities likely misclassified between requirement and submission_instruction via fast heuristics.
- Batch those entities and call a reasoning LLM to choose strictly between the two labels.
- Update in-memory nodes and persist corrected entity_type back to GraphML.
- Save an adjudication audit for transparency.

3. Pass 2 – Relationship inference (status quo)

- Run existing Phase 6/7 pipelines on the corrected graph for improved linkage and metadata enrichment.

Key properties:

- Small, focused change. No changes to upstream library code; instance-level wiring only.
- Backward compatible; guarded by `ENABLE_SUBMISSION_ADJUDICATION` (default ON or OFF per your policy).

---

## Integration points (on top of main)

- New module

  - `src/inference/submission_adjudication.py`
    - Functions:
      - `identify_ambiguous_candidates(nodes) -> List[Dict]`
      - `run_adjudication(nodes, llm_func, batch_size=40) -> (updated_nodes, changes, audit)`
    - Responsibilities:
      - Heuristic detection
      - Batch LLM adjudication (strict binary choice)
      - In-memory updates and audit entries

- Pipeline hook (before relationships)

  - `src/server/routes.py`
    - In the document processing pipeline, after GraphML is present and after any entity validation but before Phase 6 relationship inference:
      - Load nodes from GraphML
      - Call `run_adjudication(..., reasoning_llm)` if `ENABLE_SUBMISSION_ADJUDICATION=true`
      - If changes > 0, persist updated entity types back to GraphML
      - Optionally write `rag_storage/default/adjudication_audit.json`

- Reasoning LLM access

  - `src/server/initialization.py`
    - Expose both callables on the RAG-Anything instance:
      - `rag_instance.extraction_llm_func`
      - `rag_instance.reasoning_llm_func`
    - This keeps the reasoning LLM clearly separable for adjudication/query phases.

- Graph I/O helpers (already present)
  - Use `parse_graphml(...)` and `save_cleaned_entities_to_graphml(...)` from `src/inference/graph_io.py` to read/write GraphML node types.

---

## Heuristics for ambiguity detection

Flag only when likely misclassification:

1. requirement → submission_instruction candidates

- requirement nodes whose text contains submission cues and proposal/document context:
  - Submission verbs: submit/provide/include/deliver/transmit/upload/furnish/supply
  - Proposal/Section L/CDRL/DID cues: proposal, offer, bid, volume, tab, Section L/M, CDRL, DID, DI-XXX
  - Time-bound submission phrasing: within X days, NLT, no later than, by <date>

2. submission_instruction → requirement candidates

- submission_instruction nodes whose text looks like performance obligations without proposal context:
  - Performance verbs: perform/maintain/operate/install/develop/implement/configure/repair/monitor/manage
  - Performance context: system/equipment/service/facility/training/maintenance/operations
  - And notably lacks proposal/CDRL/Section L cues

Notes:

- Heuristics are deliberately conservative to minimize false positives.
- All final decisions made by the reasoning LLM; heuristics only select candidates.

---

## Adjudication prompt (compact)

- Binary choice: requirement vs submission_instruction only
- Semantic definitions (not keyword-only):
  - submission_instruction: What must be included/submitted in the proposal or delivered as a data deliverable (CDRL/DID), including page limits/format/volumes/tabs
  - requirement: A performance/delivery obligation during contract performance
- Priority override rule: Phrases like “shall submit/provide/include” about proposal content or CDRLs/DIDs are submission_instruction
- Output format: one label per item line, no extra text
- Low temperature (e.g., 0.1) for consistency

---

## Configuration and defaults

- .env additions

  - `ENABLE_SUBMISSION_ADJUDICATION=true|false` (default per rollout policy)
  - Reuse existing LLM settings:
    - Extraction (non-reasoning) model: `EXTRACTION_LLM_NAME`
    - Reasoning model: `REASONING_LLM_NAME` (e.g., `grok-4-fast-reasoning`)

- Logging and audit
  - Log counts of candidates, changed nodes
  - Write `rag_storage/default/adjudication_audit.json` containing `{ id, entity_name, old_type, new_type }`

---

## Pseudocode: pipeline hook

```
# After GraphML is created and basic validation is done
if ENABLE_SUBMISSION_ADJUDICATION:
    nodes, _ = parse_graphml(graphml_path)
    updated_nodes, changes, audit = await run_adjudication(nodes, reasoning_llm)
    if changes > 0:
        save_cleaned_entities_to_graphml(graphml_path, updated_nodes)
        write adjudication_audit.json
# Continue with relationship inference and metadata enrichment
```

---

## Edge cases and safeguards

- Mixed content sentences (“shall submit monthly reports and maintain system”):
  - If proposal/CDRL context is explicit, prefer submission_instruction; otherwise keep requirement
- Non-proposal sections mentioning “submit” (e.g., during performance for a deliverable):
  - Still submission_instruction if it produces a document/data deliverable
- If LLM returns unexpected labels:
  - Ignore and keep original type for that item (fail-safe)
- If reasoning LLM unavailable or errors out:
  - Skip adjudication; proceed with existing pipeline

---

## Evaluation plan

- Datasets
  - MCPP, MBOS RFPs (or your standard test corpora)
- Variants
  - A: Baseline (no adjudication)
  - B: Full reasoning extraction (optional reference)
  - C: Hybrid (adjudication only)
- Metrics
  - submission_instruction precision/recall, misclassification count
  - requirement precision/recall (ensure no regressions)
  - Runtime and token cost deltas
- Success criteria
  - ≥ 30–50% reduction in submission_instruction misclassifications on “shall submit …”/CDRL/Section L contexts
  - No material degradation in requirement classification
  - < 10–15% runtime overhead relative to baseline

---

## Rollout strategy

- Phase 1 (shadow)
  - Enable adjudication behind toggle; log changes, do not persist (dry run)
- Phase 2 (limited)
  - Persist retyping on a subset of documents; monitor metrics
- Phase 3 (default)
  - Enable by default once metrics are consistently improved

---

## Risks and mitigations

- Overcorrection risk (retyping true requirements as submission_instruction)
  - Conservative heuristics + binary LLM confirmation + audit
- Cost/time increase
  - Small batches; candidates only; cap batch size and total items
- Prompt drift / model variance
  - Low temperature; strict output format; unit tests

---

## Testing

- Unit tests
  - Heuristic selection: feed crafted examples and assert candidate selection
  - Prompt parser: ensure binary labels are parsed safely, extras ignored
  - No-op behavior: when no candidates, pipeline passes through unchanged
- Integration tests
  - End-to-end document ingest with toggle ON/OFF; verify GraphML entity_type changes and audit file

---

## Minimal change list (on top of main)

- Add: `src/inference/submission_adjudication.py` (new)
- Edit: `src/server/initialization.py`
  - Attach `extraction_llm_func` and `reasoning_llm_func` to the instance for downstream use
- Edit: `src/server/routes.py`
  - Insert adjudication step before relationship inference (guarded by `ENABLE_SUBMISSION_ADJUDICATION`)
- No changes to: LightRAG/RAG-Anything libraries or public APIs

---

## Operational notes

- Keep Option C structured output and corrective validation as-is
- Continue to prefer non-reasoning for bulk extraction; reserve reasoning for adjudication and querying
- Use existing `.env` management and never combine activation with execution in PowerShell (see project’s copilot instructions)

---

## Appendix: example adjudication prompt (sketch)

```
You are adjudicating entity types for a federal RFP knowledge graph.
Choose ONLY between: requirement, submission_instruction.

Definitions:
- submission_instruction: What the offeror must include/submit in the proposal or deliver as a data deliverable (CDRL/DID), including page limits, format, volumes, tabs. PRIORITY OVERRIDE: “shall submit/provide/include” about proposal content or CDRLs is submission_instruction.
- requirement: Performance/delivery obligation during contract performance.

Output: strictly one label per item, lines 1..N.

ITEMS:
1. Name: ...
   Description: ...
2. Name: ...
   Description: ...
```

---

## Acceptance criteria

- Toggle controls feature end-to-end (on/off works as expected)
- Adjudication audit is written and contains only changed items
- Misclassification rate for submission_instruction decreases materially on benchmark RFPs
- No new error classes introduced in logs; pipeline remains stable
