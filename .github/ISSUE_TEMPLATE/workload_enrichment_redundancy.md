# Workload Enrichment Redundancy in Multi-Document Processing

## Problem Statement

When processing multiple RFP documents sequentially (e.g., Amendment → PWS → Attachments), the workload enrichment step re-processes ALL requirements from ALL previously processed documents in the workspace, not just the new requirements from the current document.

### Example from Processing Logs

**Document 1 (Amendment 1 FOPR):**
```
Found 7 requirement entities to enrich
✓ Workload enrichment complete: 7/7 requirements
Processing time: ~18 seconds
```

**Document 2 (PWS):**
```
Found 292 requirement entities to enrich  ← Includes 7 from Document 1!
Processing batch 1/6 (50 requirements)...
Processing batch 2/6 (50 requirements)...
Processing batch 3/6 (50 requirements)...
Processing batch 4/6 (50 requirements)...
Processing batch 5/6 (50 requirements)...
Processing batch 6/6 (42 requirements)...
✓ Workload enrichment complete: 292/292 requirements
Processing time: ~3 minutes
```

**Inefficiency:**
- Document 1's 7 requirements get enriched AGAIN in Document 2
- Document 2's actual new requirements: ~285 (not 292)
- Wasted LLM calls: ~7 requirements × redundant processing
- This compounds with each additional document!

**Cost Impact:**
- Full RFP with 5 documents: ~200 requirements
- Without fix: Requirement #1 processed 5 times (once per document)
- With fix: Requirement #1 processed 1 time (only in its source document)
- Estimated savings: **60-80% reduction** in enrichment time and costs

---

## Root Cause

**File:** `src/inference/workload_enrichment.py`  
**Line:** 103-104

```python
# Current behavior: Fetches ALL requirements from entire workspace
all_entities = neo4j_io.get_all_entities()
requirements = [e for e in all_entities if e.get('entity_type') == 'requirement']
```

This fetches requirements from:
- Current document being processed ✅
- **Previous documents in the same workspace** ❌ (redundant)

---

## Proposed Solution

### Option 1: Skip Already-Enriched Requirements (Recommended)

Filter out requirements that already have `has_workload_metric: true`:

```python
# Filter for requirements WITHOUT enrichment metadata
requirements = [
    e for e in all_entities 
    if e.get('entity_type') == 'requirement' 
    and not e.get('has_workload_metric', False)  # Skip already enriched
]
```

**Benefits:**
- Simple 1-line fix
- Idempotent (safe to re-run)
- Works with re-processing scenarios
- Compatible with existing data

**Tradeoffs:**
- Requires Neo4j property check (minimal overhead)
- Assumes enrichment is immutable (reasonable for most use cases)

---

### Option 2: Track Document-Specific Entities (Advanced)

Pass document context to enrichment:

```python
async def enrich_workload_metadata(
    neo4j_io: Neo4jGraphIO,
    llm_func: Callable,
    batch_size: int = 50,
    doc_id: str = None  # NEW: Filter to specific document
) -> Dict[str, any]:
    """
    Enrich requirements from a specific document only.
    """
    all_entities = neo4j_io.get_all_entities()
    requirements = [
        e for e in all_entities 
        if e.get('entity_type') == 'requirement'
        and (doc_id is None or doc_id in e.get('source_id', ''))  # Filter by doc
    ]
```

**Benefits:**
- More precise control over what gets enriched
- Supports incremental processing
- Could enable per-document enrichment strategies

**Tradeoffs:**
- Requires passing `doc_id` through call chain
- More invasive code changes
- Assumes `source_id` contains document identifier

---

## Recommended Implementation

**Use Option 1** (skip already-enriched) because:

1. **Minimal code change** - One line addition
2. **Immediate impact** - 60-80% reduction in redundant processing
3. **Safe** - Doesn't break existing functionality
4. **Idempotent** - Can safely re-run enrichment without duplication

### Code Change

**File:** `src/inference/workload_enrichment.py`

```python
# Line 103-104 (current)
requirements = [e for e in all_entities if e.get('entity_type') == 'requirement']

# Proposed fix
requirements = [
    e for e in all_entities 
    if e.get('entity_type') == 'requirement'
    and not e.get('has_workload_metric', False)  # NEW: Skip already enriched
]
```

**Logging addition:**
```python
logger.info(f"Found {len(requirements)} NEW requirement entities to enrich (skipped {skipped_count} already enriched)")
```

---

## Testing Plan

1. **Process Document 1** (Amendment):
   - Verify 7 requirements enriched
   - Check all have `has_workload_metric: true`

2. **Process Document 2** (PWS):
   - Verify ONLY NEW ~285 requirements enriched
   - Verify Document 1's 7 requirements NOT re-enriched
   - Check total: 292 requirements in graph, all enriched

3. **Process Document 3** (Attachment):
   - Verify ONLY NEW requirements enriched
   - Verify cumulative totals correct
   - Measure time savings vs. baseline

**Success Criteria:**
- ✅ Each requirement enriched exactly once
- ✅ Processing time scales linearly with NEW requirements (not total)
- ✅ No duplicate enrichment in logs
- ✅ Backward compatible with existing graphs

---

## Impact Assessment

### Current Behavior (Without Fix)
| Document | New Reqs | Total in Graph | Actually Enriched | Wasted Calls |
|----------|----------|----------------|-------------------|--------------|
| Doc 1    | 7        | 7              | 7                 | 0            |
| Doc 2    | 285      | 292            | **292**           | **7**        |
| Doc 3    | 50       | 342            | **342**           | **292**      |
| Doc 4    | 30       | 372            | **372**           | **342**      |
| Doc 5    | 20       | 392            | **392**           | **372**      |
| **TOTAL**| **392**  | **392**        | **1,405**         | **1,013**    |

**Redundant enrichment calls: 1,013 / 1,405 = 72% waste!**

### With Fix (Skip Already-Enriched)
| Document | New Reqs | Total in Graph | Actually Enriched | Wasted Calls |
|----------|----------|----------------|-------------------|--------------|
| Doc 1    | 7        | 7              | 7                 | 0            |
| Doc 2    | 285      | 292            | **285**           | **0**        |
| Doc 3    | 50       | 342            | **50**            | **0**        |
| Doc 4    | 30       | 372            | **30**            | **0**        |
| Doc 5    | 20       | 392            | **20**            | **0**        |
| **TOTAL**| **392**  | **392**        | **392**           | **0**        |

**Redundant enrichment calls: 0 / 392 = 0% waste ✅**

---

## Cost Savings Estimate

**Assumptions:**
- Average 50 requirements per document
- 5 documents in full RFP
- Grok-4 cost: ~$0.006 per enrichment batch (50 requirements)

**Current Cost (Without Fix):**
```
Doc 1: 7 reqs   = 1 batch × $0.006 = $0.006
Doc 2: 57 total = 2 batches × $0.006 = $0.012 (includes Doc 1's 7 again)
Doc 3: 107 total = 3 batches × $0.006 = $0.018
Doc 4: 157 total = 4 batches × $0.006 = $0.024
Doc 5: 207 total = 5 batches × $0.006 = $0.030
Total: $0.090
```

**With Fix:**
```
Doc 1: 7 new   = 1 batch × $0.006 = $0.006
Doc 2: 50 new  = 1 batch × $0.006 = $0.006
Doc 3: 50 new  = 1 batch × $0.006 = $0.006
Doc 4: 50 new  = 1 batch × $0.006 = $0.006
Doc 5: 50 new  = 1 batch × $0.006 = $0.006
Total: $0.030
```

**Savings: $0.060 per full RFP (67% reduction)**

For 100 RFPs/year: **$6 saved** (modest but compounds with time savings)

---

## Priority

**MEDIUM-HIGH**

**Rationale:**
- Not blocking (system works, just inefficient)
- Significant time savings (3-5 minutes per multi-document RFP)
- Simple fix with high ROI
- Improves user experience (faster processing)
- Reduces cloud costs

**Assign to:** Agent / Developer  
**Milestone:** Branch 023 (Multi-document optimization)  
**Effort Estimate:** 30 minutes (1-line code change + testing)
