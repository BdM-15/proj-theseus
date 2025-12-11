# Workload Enrichment Optimization: Use Descriptions Instead of Full Chunks

## Problem Statement

Currently, workload enrichment sends **3 full text chunks** per requirement (averaging 54K characters) when only **entity descriptions** (~500-2,000 chars) are needed for BOE (Basis of Estimate) category analysis.

**Performance Impact:**
- Current: 18 minutes for 21 batches × 50 requirements
- Batch payload: 50 reqs × 54K chars = ~2.7MB per batch
- LLM response time: Variable 15s-4min per batch

## Root Cause Analysis

### Current Implementation (`src/inference/workload_enrichment.py` lines 168-200)

```python
# Takes first 3 chunks per requirement
selected_chunks = chunk_ids[:3]  # line 177

# Joins chunks with separator
text_content = "\n---\n".join([chunks[cid] for cid in selected_chunks])

# Truncates to 100K chars (rarely hit)
display_text = raw_text[:100000]  # line 192
```

**Result:** 3 chunks × 18K avg = 54K chars per requirement

### What Workload Enrichment Actually Needs

BOE category analysis requires simple patterns like:
- **Frequency**: "24/7", "daily", "monthly checks"
- **Quantities**: "799 washers", "1 bar at one location"
- **Temporal**: "annual", "quarterly", "ad-hoc"

**These patterns already exist in entity descriptions** (extracted during initial processing).

## Proposed Solution

### Change 1: Use Description Field Instead of Chunks

Modify `workload_enrichment.py` to use entity `description` field:

```python
# BEFORE: 3 chunks × 18K = 54K chars
selected_chunks = chunk_ids[:3]
text_content = "\n---\n".join([chunks[cid] for cid in selected_chunks])

# AFTER: Entity description only (~500-2,000 chars)
description_text = requirement_entity.description or requirement_entity.name
```

**Impact:** 2.7MB → 50KB per batch (98% reduction)

### Change 2: Preserve Fallback Logic

If description is missing or too short, fall back to first chunk only:

```python
if not description_text or len(description_text) < 100:
    # Fallback: Use first chunk only (not all 3)
    description_text = chunks[chunk_ids[0]] if chunk_ids else requirement_entity.name
```

## Expected Performance Improvement

| Metric | Current | Optimized | Improvement |
|--------|---------|-----------|-------------|
| **Chars per requirement** | 54,000 | 1,000 avg | 98% reduction |
| **Batch payload** | 2.7MB | 50KB | 98% reduction |
| **LLM time per batch** | 15s-4min | 5-15s est | 75% reduction |
| **Total duration** | 18 min | 3-5 min est | 72-83% reduction |
| **Cost savings** | Baseline | ~75% | Significant |

## Testing Strategy

### 1. Accuracy Validation

Compare BOE category assignments before/after optimization:

```python
# Run enrichment with current implementation
python -m tests.test_workload_enrichment --mode baseline

# Run enrichment with description-only
python -m tests.test_workload_enrichment --mode optimized

# Compare results
python -m tests.compare_workload_results
```

**Success Criteria:**
- 95%+ category agreement between methods
- No reduction in pattern detection quality

### 2. Performance Validation

```bash
# Monitor processing.log for timing
grep "Workload enrichment completed" logs/processing.log

# Expected: 18 min → 3-5 min
```

### 3. Edge Case Testing

- **Missing descriptions**: Verify fallback to first chunk
- **Short descriptions**: Verify minimum length threshold
- **Complex requirements**: Verify patterns still detected

## Implementation Checklist

- [ ] Modify `src/inference/workload_enrichment.py` lines 168-200
- [ ] Add description-only logic with fallback
- [ ] Create test script for accuracy comparison
- [ ] Run baseline measurement on known dataset
- [ ] Run optimized measurement on same dataset
- [ ] Compare BOE category assignments (95%+ agreement target)
- [ ] Verify 72-83% time reduction
- [ ] Update documentation with new performance metrics
- [ ] Update `.github/copilot-instructions.md` with learnings

## Dependencies

**Prerequisite:** Branch 038 merged successfully (table analysis + chunk format fixes)

**Related Components:**
- `src/inference/workload_enrichment.py` - Core enrichment logic
- `src/ontology/schema.py` - Requirement entity definition
- Entity extraction prompts - Ensure descriptions are comprehensive

## References

- **Processing Log Analysis:** `logs/processing.log` (branch 038 run)
- **Chunk Size Analysis:** Average 18,468 chars, Max 42,222, Min 1,196
- **Grok-4 Context Window:** 2M tokens input, 524K output configured
- **Current Hardcoded Limit:** 100K chars per requirement (rarely hit)

## Evidence from Branch 038 Run

**Workload Enrichment Stats:**
- Duration: 18 min 23 sec
- Batches: 21 batches × 50 requirements
- Parallel workers: 16 (MAX_ASYNC=16)
- Average batch time: ~52 seconds
- Slowest batch: 3 min 57 sec

**Entity Description Examples:**
```
"Perform 24/7 security monitoring at facility entrance"
"Replace 799 washers across 12 maintenance locations"
"Conduct monthly safety checks at 1 bar location"
"Annual HVAC inspection for Building 7"
```

**Conclusion:** Descriptions already contain all patterns needed for BOE analysis.

---

**Created:** 2025-12-11  
**Branch Context:** 038-table-analysis-chunk-format  
**Priority:** High (72-83% performance improvement potential)  
**Complexity:** Medium (isolated change, clear success criteria)
