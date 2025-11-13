# Branch 013b: Workload Enrichment + Semantic Relationship Fixes

**Branch**: `013b-workload-enrichment-semantic-fixes`  
**Parent**: `main` (includes branch 013 batching fix)  
**Date**: November 10, 2025  
**Status**: ACTIVE

## Objectives

Fix the core issues identified in validation to achieve **85%+ production readiness**:

1. **Workload Enrichment** (0% → 100% target)

   - Add 7 BOE category metadata to REQUIREMENT entities
   - Enable capture manager queries for labor/materials/compliance analysis

2. **Section L↔M Coverage** (31% → 75%+ target)

   - Improve relationship inference between requirements and evaluation factors
   - Better prompt engineering for EVALUATES relationships
   - Context-aware relationship detection

3. **Deliverable Traceability** (28% → 70%+ target)
   - Enhance FULFILLS relationships (deliverable → requirement)
   - Better extraction of CDRLs and submission requirements

## Current State (From 013a Test)

**Small Document Validation Results:**

```
Overall Score: 43.3%
├─ Query Quality:        100.0% ✅
├─ Section L↔M:           31.0% ❌ (6/14 reqs, 5/26 eval factors linked)
├─ Workload Enrichment:    0.0% ❌ (removed in branch 013 baseline)
└─ Deliverable Trace:     27.9% ❌ (3/15 deliverables, 5/14 reqs linked)
```

**Target After 013b:**

```
Overall Score: 85%+
├─ Query Quality:        100.0% ✅ (maintain)
├─ Section L↔M:           75%+ 🎯 (improve inference)
├─ Workload Enrichment:  100.0% 🎯 (implement)
└─ Deliverable Trace:     70%+ 🎯 (improve inference)
```

## Implementation Plan

### Task 1: Integrate Workload Enrichment Module

**What:** Re-enable workload metadata enrichment on REQUIREMENT entities

**Files to modify:**

- `src/inference/semantic_post_processor.py`:
  - Add Step 4: Workload metadata enrichment
  - Call `enrich_workload_metadata()` after relationship inference
  - Add enrichment stats to return dict

**Code already exists** in `src/inference/workload_enrichment.py` (created in earlier work):

- 7 BOE categories: Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance
- Properties added: `has_workload_metric`, `workload_categories`, `labor_drivers`, etc.
- LLM-powered analysis using Shipley Capture principles

**Expected Impact:**

- Workload Enrichment: 0% → 95-100%
- Overall Score: +25 points (from 43% to ~68%)

**Implementation:**

```python
# In semantic_post_processor.py, after Step 3 (relationship inference):

logger.info("\n🏗️ Step 4: Enriching requirements with workload metadata...")
from src.inference.workload_enrichment import enrich_workload_metadata

workload_stats = await enrich_workload_metadata(
    neo4j_io=neo4j_io,
    llm_func=_call_llm_async
)

# Add to return stats
stats["requirements_enriched"] = workload_stats.get("requirements_enriched", 0)
stats["workload_categories"] = workload_stats.get("category_distribution", {})
```

**Testing:**

```powershell
# Reprocess small document
python tools/clear_neo4j.py
# Upload Amendment 1 via WebUI
python tools/validate_rfp_processing.py
# Expected: Workload Enrichment: 100%, Overall: ~68%
```

---

### Task 2: Improve Section L↔M Relationship Inference

**What:** Enhance relationship inference to better detect EVALUATES relationships

**Root Cause Analysis:**

- Current: Only 31% Section L↔M coverage (6/14 reqs, 5/26 eval factors)
- Issue: Generic prompt doesn't emphasize Section L↔M mapping
- Solution: Domain-specific relationship detection

**Files to modify:**

- `src/inference/semantic_post_processor.py`:
  - `_infer_relationships_batch()` prompt enhancement
  - Add Section L↔M detection guidance
  - Prioritize EVALUATES relationship type

**Prompt Enhancement Strategy:**

**CURRENT PROMPT:**

```
Relationship types to use:
- EVALUATES: Section M evaluation criteria → Section L requirements
- FULFILLS: Deliverable → Requirement it satisfies
...

Find logical relationships that are missing.
```

**ENHANCED PROMPT:**

```
Relationship types to use (in priority order):

**PRIMARY (Government Contracting Domain):**
- EVALUATES: Section M evaluation criteria/factors → Section L requirements
  * Look for: "Factor X evaluates...", "Subfactor assesses...", matching keywords
  * Example: "Technical Approach (factor)" EVALUATES "TOMP Submission (requirement)"

- FULFILLS: Deliverable/CDRL → Requirement it satisfies
  * Look for: CDRL numbers (A001, A002), deliverable names matching requirements
  * Example: "Monthly Report (deliverable)" FULFILLS "Submit monthly status (requirement)"

**SECONDARY (General):**
- REQUIRES: Requirement → Equipment/Resource needed
- REFERENCES: Document/Section → Another document/section
- APPLIES_TO: Clause/Regulation → Program/Contract
- PART_OF: Sub-component → Parent component

**ANALYSIS GUIDANCE:**
1. First pass: Find all EVALUATES relationships (Section M ↔ Section L mapping)
2. Second pass: Find all FULFILLS relationships (deliverables ↔ requirements)
3. Third pass: Find remaining relationship types

**Entity Type Hints:**
- evaluation_factor entities → likely source of EVALUATES relationships
- requirement entities → likely target of EVALUATES, source of REQUIRES
- deliverable entities → likely source of FULFILLS relationships

Focus on finding EVALUATES and FULFILLS relationships first - these are most critical for proposal compliance.
```

**Expected Impact:**

- Section L↔M: 31% → 70-80%
- Overall Score: +10-12 points (from ~68% to ~78-80%)

**Implementation:**

```python
# In _infer_relationships_batch(), replace prompt with enhanced version
# Emphasize EVALUATES and FULFILLS priority
# Add entity type hints
```

---

### Task 3: Improve Deliverable Traceability

**What:** Better detect FULFILLS relationships between deliverables and requirements

**Root Cause Analysis:**

- Current: Only 28% deliverable traceability (3/15 delivs, 5/14 reqs)
- Issue: CDRLs and deliverables often have different names than requirements
- Solution: CDRL number matching + semantic similarity

**Files to modify:**

- `src/inference/semantic_post_processor.py`:
  - Add deliverable-specific relationship detection
  - CDRL number pattern matching
  - Keyword similarity for deliverable↔requirement

**Enhancement Strategy:**

**Add CDRL Awareness:**

```python
# In entity reference table, highlight CDRL numbers for deliverables
entity_table += "\n".join([
    f"{e['id']} | {e['entity_type']} | {e['entity_name']} | "
    f"{'[CDRL: ' + extract_cdrl(e) + ']' if 'deliverable' in e['entity_type'] else ''} | "
    f"{e.get('description', '')[:80]}"
    for e in batch_entities
])

def extract_cdrl(entity):
    """Extract CDRL number from entity name/description"""
    import re
    text = f"{entity.get('entity_name', '')} {entity.get('description', '')}"
    match = re.search(r'(CDRL|A\d{3,4})', text, re.IGNORECASE)
    return match.group(0) if match else ''
```

**Prompt Guidance for FULFILLS:**

```
FULFILLS Relationship Detection:
- Look for CDRL numbers (A001, A002, etc.) in deliverable names
- Match deliverable names to requirement descriptions
- Keywords: "submit", "provide", "deliver", "report", "plan", "schedule"
- Example: "CDRL A007 Monthly Performance Report" FULFILLS "Submit monthly performance report by 5th of month"
```

**Expected Impact:**

- Deliverable Traceability: 28% → 70-75%
- Overall Score: +4-5 points (from ~78-80% to ~82-85%)

---

### Task 4: Confidence Threshold Tuning (Optional)

**What:** Filter low-confidence relationships to reduce noise

**Current:** Accept all relationships (no minimum confidence)

**Proposed:**

```python
# In _infer_relationships_batch(), filter results
for rel in relationships:
    confidence = rel.get('confidence', 0.7)

    # Higher threshold for critical relationship types
    min_confidence = 0.8 if rel_type in ['EVALUATES', 'FULFILLS'] else 0.6

    if confidence >= min_confidence:
        all_relationships.append({...})
    else:
        logger.debug(f"  Skipped low-confidence relationship: {rel_type} ({confidence:.2f})")
```

**Expected Impact:**

- Precision improvement (fewer false positives)
- Recall may decrease slightly (fewer total relationships)
- Overall: Higher quality relationships

---

## Testing & Validation

### Phase 1: Small Document Validation

```powershell
# Test each task incrementally
python tools/clear_neo4j.py

# Task 1: Workload enrichment
# (Upload Amendment 1 via WebUI)
python tools/validate_rfp_processing.py
# Expected: Workload 100%, Overall ~68%

# Task 2: Section L↔M improvements
# (Reprocess after prompt changes)
python tools/validate_rfp_processing.py
# Expected: Section L↔M 70-80%, Overall ~78-80%

# Task 3: Deliverable improvements
python tools/validate_rfp_processing.py
# Expected: Deliverable 70-75%, Overall 82-85%
```

### Phase 2: Full ISS RFP Validation

```powershell
# Clear Neo4j
python tools/clear_neo4j.py

# Process full ISS RFP
# Upload via WebUI: ADAB_ISS_RFP_Amendment_1.pdf (mode=auto)

# Wait for processing (~3-5 minutes)

# Run validation
python tools/validate_rfp_processing.py afcapv_adab_iss_2025

# Expected Results:
# - Overall Score: 85%+
# - Query Quality: 100%
# - Section L↔M: 75-85%
# - Workload Enrichment: 95-100%
# - Deliverable Traceability: 70-80%
```

### Success Criteria

**Minimum (PASS - 70%+):**

- ✅ Overall validation score ≥ 70%
- ✅ Workload enrichment ≥ 90%
- ✅ Section L↔M coverage ≥ 60%

**Target (PRODUCTION READY - 85%+):**

- 🎯 Overall validation score ≥ 85%
- 🎯 Workload enrichment ≥ 95%
- 🎯 Section L↔M coverage ≥ 75%
- 🎯 Deliverable traceability ≥ 70%

**Stretch (OPTIMAL - 90%+):**

- ⭐ Overall validation score ≥ 90%
- ⭐ All metrics ≥ 85%

---

## Implementation Order

1. **Task 1 first** - Workload enrichment (quick win, +25 points)
2. **Task 2 second** - Section L↔M improvements (+10-12 points)
3. **Task 3 third** - Deliverable traceability (+4-5 points)
4. **Task 4 optional** - Confidence tuning (quality vs quantity tradeoff)

**Incremental commits:**

- Commit after each task with validation results
- Test on small doc first, then full RFP
- Document what worked and what didn't

---

## Known Risks

### Risk 1: Workload Enrichment LLM Costs

- **Issue:** 173 requirements × 150 tokens/req = ~26K tokens per RFP
- **Cost:** ~$0.01-0.02 per RFP (negligible)
- **Mitigation:** Batch processing already implemented

### Risk 2: False Positive Relationships

- **Issue:** Enhanced prompts might infer incorrect relationships
- **Mitigation:** Confidence thresholds, validation framework catches issues
- **Fallback:** Manual Cypher corrections (templates in `graph_node_edits/neo4j_corrections/`)

### Risk 3: Small Document May Not Represent Full RFP

- **Issue:** Amendment 1 (8 pages) may have different characteristics than full RFP (400+ pages)
- **Mitigation:** Test on both small and full documents
- **Validation:** Use ISS RFP baseline (Run 5) as comparison

---

## Files to Modify

### Core Implementation:

- `src/inference/semantic_post_processor.py`:
  - Add Step 4: Workload enrichment call
  - Enhance relationship inference prompt
  - Add CDRL extraction helper
  - Confidence threshold filtering

### Supporting:

- `src/inference/workload_enrichment.py`: (already exists, may need tuning)
- `docs/BRANCH_013B_WORKLOAD_SEMANTIC_FIXES.md`: This document

### Testing:

- `tests/test_workload_enrichment.py`: Unit tests for enrichment
- `tests/test_relationship_quality.py`: Relationship precision/recall tests

---

## Completion Criteria

**Branch 013b is complete when:**

1. ✅ All 4 tasks implemented and tested
2. ✅ Small document validation ≥ 85%
3. ✅ Full ISS RFP validation ≥ 85%
4. ✅ All tests passing
5. ✅ Code committed with validation results
6. ✅ Ready to merge to main

**Estimated effort:** 2-3 hours (including testing)

**Next branch:** 013c or merge to main if 85%+ achieved
