# Issue #31: DRY Refactoring - Consolidate Batch Processing Utilities

## Summary

Refactor repeated batch processing, semaphore control, and JSON parsing patterns into reusable utility modules to reduce code duplication by ~19% (~485 lines) and improve maintainability.

**Priority**: Low (polish/code quality)  
**Effort**: Medium (2-3 days)  
**Type**: Technical Debt / Code Quality  
**Blocked by**: Issue #30 (complete after Phase 3B)

---

## Problem Statement

During implementation of Issue #30 (Phases 1-3A), parallel batch processing patterns were duplicated across multiple files to achieve performance goals quickly. Now that functionality is validated, these patterns should be consolidated into reusable utilities.

### Current State

**Repeated code patterns** (10+ instances each):

1. **Batch processing with asyncio.gather** (~150 lines duplicated)
2. **Semaphore-controlled async functions** (~50 lines duplicated)
3. **JSON response parsing + validation** (~80 lines duplicated)
4. **Batch preparation logic** (~40 lines duplicated)

**Files affected**:

- `src/inference/semantic_post_processor.py` (~1,759 lines, 20% duplication)
- `src/inference/workload_enrichment.py` (~356 lines, 21% duplication)
- `src/server/routes.py` (~450 lines, 11% duplication)

---

## Code Duplication Analysis

### 🔴 HIGH PRIORITY: Parallel Batch Processing Pattern

**Current** (repeated 10+ times across files):

```python
# DUPLICATED BLOCK (~15 lines each):
batch_tasks = []
for batch in batches:
    batch_tasks.append(process_function(...))

batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

all_results = []
for i, result in enumerate(batch_results):
    if isinstance(result, Exception):
        logger.error(f"Batch {i} failed: {result}")
    else:
        all_results.extend(result)
```

**Locations**:

- `semantic_post_processor.py`: Lines 485, 728, 849, 950, 1074, 1282, 1402, 1457, 1540, 1555, 1570
- `workload_enrichment.py`: Lines 337
- `routes.py`: Multiple extraction functions

**Proposed utility**:

```python
# src/utils/async_batch_processor.py
async def process_batches_parallel(
    batches: List,
    process_fn: Callable,
    semaphore: asyncio.Semaphore = None,
    batch_label: str = "Batch",
    aggregate_fn: Callable = lambda results: [item for r in results for item in r]
) -> List:
    """
    Process batches in parallel with error handling.

    Args:
        batches: List of batch data to process
        process_fn: Async function to process each batch
        semaphore: Optional semaphore for concurrency control
        batch_label: Label for error logging
        aggregate_fn: Function to combine results (default: flatten lists)

    Returns:
        Aggregated results from all batches
    """
    batch_tasks = [process_fn(batch) for batch in batches]
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

    all_results = []
    for i, result in enumerate(batch_results, 1):
        if isinstance(result, Exception):
            logger.error(f"    ❌ {batch_label} {i} failed: {result}")
        else:
            all_results = aggregate_fn([all_results, result])

    return all_results
```

**Impact**: 150 lines → 30 lines (80% reduction)

---

### 🟡 MEDIUM PRIORITY: Semaphore Control Pattern

**Current** (repeated 8+ times):

```python
# DUPLICATED PATTERN:
async def process_batch_with_semaphore(batch_info: Dict) -> int:
    async with semaphore:
        response = await _call_llm_async(...)
    return parse_and_validate(response)
```

**Locations**:

- `semantic_post_processor.py`: `_process_req_eval_batch`, `_process_deliverable_batch`
- `workload_enrichment.py`: `process_batch_with_semaphore`
- `routes.py`: `extract_with_semaphore`, `extract_multimodal_with_semaphore`

**Proposed decorator**:

```python
# src/utils/async_batch_processor.py
def with_semaphore(semaphore_arg: str = 'semaphore'):
    """Decorator to wrap async function with semaphore control."""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            sem = kwargs.get(semaphore_arg) or args[func_signature_index]
            async with sem:
                return await func(*args, **kwargs)
        return wrapper
    return decorator

# USAGE:
@with_semaphore()
async def process_batch(batch, semaphore):
    return await _call_llm_async(...)
```

**Impact**: 50 lines → 10 lines (80% reduction)

---

### 🟡 MEDIUM PRIORITY: JSON Response Parsing

**Current** (repeated 10+ times):

````python
# DUPLICATED BLOCK (~8 lines each):
response_clean = response.strip()
if response_clean.startswith("```json"):
    response_clean = response_clean[7:]
if response_clean.startswith("```"):
    response_clean = response_clean[3:]
if response_clean.endswith("```"):
    response_clean = response_clean[:-3]
response_clean = response_clean.strip()

rels = json.loads(response_clean)
valid_rels = _validate_relationships(rels, id_to_entity, label)
````

**Locations**:

- `semantic_post_processor.py`: Algorithms 1-8 (8 instances)
- `workload_enrichment.py`: Enrichment processing (1 instance)

**Proposed utility**:

````python
# src/utils/llm_response_parser.py
def clean_markdown_wrapper(response: str) -> str:
    """Remove markdown code block wrappers from LLM response."""
    response = response.strip()
    if response.startswith("```json"):
        response = response[7:]
    if response.startswith("```"):
        response = response[3:]
    if response.endswith("```"):
        response = response[:-3]
    return response.strip()

def parse_llm_json_response(
    response: str,
    id_to_entity: Dict,
    label: str,
    validator_fn: Callable = None
) -> List[Dict]:
    """
    Parse LLM JSON response with markdown cleanup and validation.

    Args:
        response: Raw LLM response string
        id_to_entity: Entity ID lookup for validation
        label: Label for error logging
        validator_fn: Optional custom validator (default: _validate_relationships)

    Returns:
        List of validated relationship dicts
    """
    cleaned = clean_markdown_wrapper(response)
    data = json.loads(cleaned)

    if validator_fn:
        return validator_fn(data, id_to_entity, label)
    else:
        # Default validation logic
        return _validate_relationships(data, id_to_entity, label)
````

**Impact**: 80 lines → 15 lines (81% reduction)

---

### 🟢 LOW PRIORITY: Batch Preparation Logic

**Current** (repeated 5+ times):

```python
# DUPLICATED BLOCK (~5 lines each):
num_batches = (total_items + batch_size - 1) // batch_size
for batch_num in range(num_batches):
    batch_start = batch_num * batch_size
    batch_end = min(batch_start + batch_size, total_items)
    batch = items[batch_start:batch_end]
```

**Locations**:

- `semantic_post_processor.py`: Algorithms 3, 4, 8
- `workload_enrichment.py`: Enrichment batching

**Proposed utility**:

```python
# src/utils/batch_helpers.py
def create_batches(items: List, batch_size: int) -> List[List]:
    """Split items into batches of specified size."""
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

def create_batches_with_overlap(
    items: List,
    batch_size: int,
    overlap: int
) -> List[List]:
    """
    Create batches with overlap for cross-batch relationship preservation.

    Used by Algorithm 3 (Requirement→Evaluation Mapping).
    """
    batches = []
    start = 0
    while start < len(items):
        end = min(start + batch_size, len(items))
        batches.append(items[start:end])
        start += (batch_size - overlap)
    return batches
```

**Impact**: 40 lines → 10 lines (75% reduction)

---

## Proposed Solution

### New Utility Module Structure

```
src/utils/
  __init__.py                    # Export public APIs
  async_batch_processor.py       # 🔴 HIGH PRIORITY
    - process_batches_parallel()
    - with_semaphore() decorator
  llm_response_parser.py         # 🟡 MEDIUM PRIORITY
    - clean_markdown_wrapper()
    - parse_llm_json_response()
  batch_helpers.py               # 🟢 LOW PRIORITY
    - create_batches()
    - create_batches_with_overlap()
```

### Migration Strategy

**Phase 1**: Create utilities (1 day)

- Implement `async_batch_processor.py`
- Implement `llm_response_parser.py`
- Implement `batch_helpers.py`
- Add comprehensive unit tests (>90% coverage)

**Phase 2**: Migrate semantic_post_processor.py (1 day)

- Replace 11 batch processing instances
- Replace 8 JSON parsing instances
- Replace 3 batch preparation instances
- Validate with existing tests

**Phase 3**: Migrate workload_enrichment.py + routes.py (0.5 day)

- Replace remaining instances
- Validate end-to-end processing

**Phase 4**: Cleanup (0.5 day)

- Remove old duplicated code
- Update documentation
- Final validation

---

## Acceptance Criteria

- ✅ All batch processing uses `process_batches_parallel()`
- ✅ All semaphore patterns use `@with_semaphore()` decorator
- ✅ All JSON parsing uses `parse_llm_json_response()`
- ✅ All batch preparation uses `create_batches()`
- ✅ Unit tests for all new utilities (>90% coverage)
- ✅ All existing tests pass (no regression)
- ✅ Code duplication reduced by ~19% (485 lines)
- ✅ No performance degradation (same runtime ±5%)

---

## Testing Strategy

### Unit Tests (New)

```python
# tests/test_async_batch_processor.py
async def test_process_batches_parallel():
    """Test parallel batch processing with error handling"""

async def test_with_semaphore_decorator():
    """Test semaphore decorator limits concurrency"""

# tests/test_llm_response_parser.py
def test_clean_markdown_wrapper():
    """Test markdown cleanup variations"""

def test_parse_llm_json_response():
    """Test JSON parsing + validation"""

# tests/test_batch_helpers.py
def test_create_batches():
    """Test batch splitting"""

def test_create_batches_with_overlap():
    """Test overlapping batches"""
```

### Integration Tests (Existing)

- `test_semantic_postprocessing_phase1.py` (must pass)
- `test_semantic_postprocessing_phase2.py` (must pass)
- `test_workload_enrichment_phase3a.py` (must pass)
- Production RFP test (MCPP II) - validate same results

---

## Impact Analysis

| Metric                       | Before   | After    | Change            |
| ---------------------------- | -------- | -------- | ----------------- |
| **Total Lines**              | 2,565    | 2,080    | -485 lines (-19%) |
| `semantic_post_processor.py` | 1,759    | 1,400    | -359 lines (-20%) |
| `workload_enrichment.py`     | 356      | 280      | -76 lines (-21%)  |
| `routes.py`                  | 450      | 400      | -50 lines (-11%)  |
| **Utilities (new)**          | 0        | 150      | +150 lines        |
| **Duplication**              | High     | Minimal  | DRY compliant     |
| **Maintainability**          | Medium   | High     | ✅ Improved       |
| **Performance**              | Baseline | Same ±5% | No regression     |

---

## Dependencies

- **Blocked by**: Issue #30 Phase 3B completion
- **Blocks**: None (polish task)
- **Related**: Issue #14 (Prompt Compression) - could benefit from shared utilities

---

## Non-Goals

- ❌ Performance optimization (already achieved in Issue #30)
- ❌ Algorithm logic changes (only structure refactoring)
- ❌ Prompt modifications (defer to Issue #14)
- ❌ New features (code quality only)

---

## Notes

- Defer until after Phase 3B to avoid regression risk during active development
- Maintain 100% backward compatibility during migration
- Use gradual migration strategy (file-by-file, not wholesale replacement)
- Keep old code commented for 1 sprint before deletion
- Monitor performance metrics during migration (should be identical)

---

**Created**: December 7, 2025  
**Status**: Backlog (pending Issue #30 completion)  
**Assignee**: TBD  
**Labels**: `technical-debt`, `code-quality`, `refactoring`, `low-priority`
