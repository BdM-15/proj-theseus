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

---

## Extraction Prompt Audit (Completed Dec 19, 2025)

### Relationship Rules in `govcon_lightrag_native.txt`

**Part F: Relationship Patterns and Inference Rules** contains comprehensive rules:

| Relationship Type | Purpose | Status |
|-------------------|---------|--------|
| CHILD_OF | Hierarchical structure | ✅ In prompt |
| GUIDES | Section L → M mapping | ✅ In prompt (F.2) |
| EVALUATED_BY | Requirement → Eval Factor | ✅ In prompt (F.3) |
| MEASURED_BY | Requirement → Performance Metric | ✅ In prompt |
| PRODUCES | SOW → Deliverable | ✅ In prompt |
| TRACKED_BY | Deliverable → CDRL | ✅ In prompt |
| APPLIES_TO | Requirement → Equipment | ✅ In prompt |
| REFERENCES | Cross-document references | ✅ In prompt |
| ATTACHMENT_OF | Document → Section | ✅ In prompt |

**Missing from Extraction (Handled by Post-Processing)**:
- FULFILLED_BY (Deliverable → Requirement) - Algorithm 4 handles this
- Cross-document semantic linking - Algorithm 6 handles this

### Entity Metadata in Extraction Prompt

| Entity Type | Required Metadata | Status |
|-------------|-------------------|--------|
| requirement | criticality, modal_verb, req_type, labor_drivers | ✅ In Part D |
| evaluation_factor | weight, importance, subfactors | ✅ In Part D |
| submission_instruction | page_limit, format_reqs, volume | ✅ In Part D |
| performance_metric | threshold, measurement_method | ✅ In Part D |

**Note**: `material_needs` is NOT in extraction prompt but IS in Pydantic schema.

### Format Agnosticism Assessment

**Algorithm Code**: Only 1 Section reference (comment in algo_1) ✅

**Relationship Prompts**: Use UCF sections as EDUCATIONAL context but emphasize pattern-based detection:
- `instruction_evaluation_linking.md` line 25: "format-agnostic, works across all RFP structures"
- Pattern 4: "Agnostic Content-Based Detection"

**Extraction Prompt**: Uses Section references in:
- Part E: UCF Reference (Educational)
- Part K: Examples (Educational)

**Conclusion**: System is already reasonably format-agnostic. UCF references are for LLM education, not hardcoded logic.

