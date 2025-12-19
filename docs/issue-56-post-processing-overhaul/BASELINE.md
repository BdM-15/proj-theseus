# Issue #56 Post-Processing Overhaul - Baseline Metrics

**Branch**: `feature/56-post-processing-overhaul`  
**Created**: December 19, 2025  
**Base**: `main` (post Issue #54 "Back to Basics")

---

## Pre-Overhaul Baseline Metrics

### Entity Extraction (Branch 022 Perfect Run)

| Metric | Value | Source |
|--------|-------|--------|
| Entities | 339-368 | ISS PWS |
| Initial Relationships | 154-274 | Native extraction |
| Inferred Relationships | 154 | Post-processing |
| Total Relationships | 154-428 | Combined |
| Error Rate | 1.0-1.3% | Entity type corrections |

### Post-Processing Algorithms (8 Total)

| # | Algorithm | Purpose | Status |
|---|-----------|---------|--------|
| 1 | Instruction-Eval | Links submission instructions to eval factors | Active |
| 2 | Eval Hierarchy | Links subfactors to parent factors | Active |
| 3 | Req-Eval | Maps requirements to eval factors | Review for overlap |
| 4 | Deliverable Trace | Links deliverables to requirements | Review for overlap |
| 5 | Doc Hierarchy | Builds section/attachment hierarchy | Active |
| 6 | Concept Linking | Connects concepts to parent entities | Review for overlap |
| 7 | Heuristic | Regex-based CDRL patterns (no LLM) | Active |
| 8 | Orphan Resolution | Resolves unlinked entities | Active |

### Workload Enrichment

| Metric | Pre-Fix | Target |
|--------|---------|--------|
| Success Rate | 82.9% (194/234) | 100% |
| BOE Categories | 7 (Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance) | 7 |
| Model | Mixed routing | REASONING_LLM_NAME |

### Cost Baseline

| Document Type | Old Cost | Target |
|---------------|----------|--------|
| 425-page MCPP II | ~$4.00 | $2-3 |
| Standard PWS | ~$2.00 | $1-2 |

#### xAI Grok Pricing (Both Models)
- Input: $0.20 per million tokens
- Output: $0.50 per million tokens

### LLM Configuration

| Task | Model | Purpose |
|------|-------|---------|
| Extraction | grok-4-1-fast-non-reasoning | Literal format compliance |
| Post-Processing | grok-4-fast-reasoning | Inference and reasoning |
| Query | grok-4-fast-reasoning | Synthesis and answers |
| Embeddings | text-embedding-3-large | 3072-dim vectors |

---

## Success Criteria for Overhaul

- [ ] Workload enrichment: 100% success rate
- [ ] All post-processing algorithms use reasoning model
- [ ] No duplicate relationship extraction between phases
- [ ] Processing time within 5-10 min for standard PWS
- [ ] Cost per RFP: $1-3 target, $4-6 upper bound
- [ ] Format agnostic: No hardcoded section references in extraction logic
- [ ] At least one algorithm removed or made conditional

---

## Files to Review

### Extraction Prompt
- `prompts/extraction/govcon_lightrag_native.txt` (~35K tokens)
- `prompts/govcon_prompt.py`

### Post-Processing
- `src/inference/semantic_post_processor.py`
- `src/inference/workload_enrichment.py`
- `src/inference/algorithms/orchestrator.py`
- `src/inference/algorithms/algo_*.py`

### Relationship Inference Prompts
- `prompts/relationship_inference/instruction_evaluation_linking.md`
- `prompts/relationship_inference/requirement_evaluation.md`
- `prompts/relationship_inference/document_hierarchy.md`
- `prompts/relationship_inference/deliverable_traceability.md`

