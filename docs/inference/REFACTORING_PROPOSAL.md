# Refactoring Plan: Unified Batch Processing Architecture

## Problem Statement

Current post-processing pipeline has become fragmented:

- Duplicate batching logic in Phase 6 and Phase 7
- Unclear separation between "forbidden type cleanup" and "relationship inference"
- Hardcoded batch sizes scattered across files
- Difficult to maintain and extend

## Proposed Architecture

### 1. Unified Batch Processor (NEW)

**File**: `src/inference/batch_processor.py`
**Purpose**: Single, reusable batching implementation
**Features**:

- Generic `process_batches()` method
- Progress logging (Batch 1/31: Processing 50 items...)
- Error handling (continue on batch failure)
- Result aggregation (merge dicts, flatten lists)
- Configurable batch size

### 2. Entity Operations (REFACTORED)

**File**: `src/inference/entity_operations.py` (rename from `forbidden_type_cleanup.py`)
**Purpose**: All entity-level transformations
**Operations**:

- Forbidden type cleanup (existing Phase 6 logic)
- Entity deduplication (currently in engine.py)
- Entity validation
  **Uses**: BatchProcessor for all LLM calls

### 3. Relationship Operations (REFACTORED)

**File**: `src/inference/relationship_operations.py` (rename from `engine.py`)
**Purpose**: All relationship inference algorithms
**Operations**:

- Document → Section (Algorithm 1)
- Clause → Section (Algorithm 2)
- Instruction ↔ Factor (Algorithm 3)
- Requirement → Factor (Algorithm 4) **with batching**
- SOW → Deliverable (Algorithm 5)
- Type-based heuristics (Algorithm 6)
  **Uses**: BatchProcessor for all LLM calls

### 4. Post-Processing Orchestrator (NEW)

**File**: `src/inference/post_processor.py`
**Purpose**: Single entry point for all post-processing
**Flow**:

```python
async def run_post_processing(graphml_path: str, llm_func) -> dict:
    \"\"\"
    Orchestrate all post-processing steps in correct order.

    Steps:
    1. Load entities/edges from GraphML
    2. Entity cleanup (forbidden types)
    3. Entity deduplication
    4. Relationship inference (7 algorithms)
    5. Save enhanced graph to GraphML + Neo4j

    Returns:
        Stats dict with counts and timings
    \"\"\"
```

## Benefits

### 1. **DRY (Don't Repeat Yourself)**

- One batching implementation vs. multiple scattered copies
- Easier to adjust batch size globally
- Consistent error handling and logging

### 2. **Clear Separation of Concerns**

- Entity operations = transforming individual nodes
- Relationship operations = creating/inferring edges
- Orchestrator = coordinating the pipeline

### 3. **Easier Testing**

- Test BatchProcessor once, reuse everywhere
- Mock LLM calls at orchestrator level
- Unit test individual operations in isolation

### 4. **Better Performance Tuning**

- Central config for batch sizes by operation type:
  ```python
  BATCH_SIZES = {
      "entity_retyping": 50,
      "requirement_inference": 50,
      "clause_clustering": 100  # Smaller entities = larger batch
  }
  ```

### 5. **Maintainability**

- New operation? Implement process function + use BatchProcessor
- Bug in batching? Fix once in BatchProcessor
- Add logging? Update BatchProcessor.process_batches()

## Implementation Steps

### Phase 1: Create Infrastructure (Today)

1. ✅ Create `batch_processor.py` with unified BatchProcessor
2. Create `post_processor.py` orchestrator skeleton
3. Update imports in `routes.py` to use new orchestrator

### Phase 2: Refactor Entity Operations (Next Session)

1. Rename `forbidden_type_cleanup.py` → `entity_operations.py`
2. Refactor `cleanup_forbidden_types()` to use BatchProcessor
3. Move `deduplicate_entities()` from engine.py to entity_operations.py
4. Test entity operations in isolation

### Phase 3: Refactor Relationship Operations (Next Session)

1. Rename `engine.py` → `relationship_operations.py`
2. Refactor all 7 algorithms to use BatchProcessor
3. Extract algorithm-specific logic into individual functions
4. Test relationship operations in isolation

### Phase 4: Integration & Testing (Next Session)

1. Update `routes.py` to use new `post_processor.run_post_processing()`
2. Run MCPP DRAFT RFP through refactored pipeline
3. Verify entity counts, relationship counts match baseline
4. Document new architecture in `/docs/inference/`

## Migration Strategy

### Option A: Big Bang (Risky)

- Refactor everything at once
- Test on MCPP RFP
- High risk if bugs introduced

### Option B: Gradual Migration (Recommended)

1. Keep old code in place
2. Create new `post_processor_v2.py` with refactored logic
3. Add feature flag: `USE_REFACTORED_PIPELINE=false` in .env
4. Test new pipeline in parallel with old
5. Compare results (entity counts, relationship counts)
6. When validated, switch flag to true and remove old code

## Decision Point

**Question for User**: Should we proceed with this refactoring?

**Pros**:

- Much cleaner architecture
- Easier to maintain long-term
- Reduces technical debt

**Cons**:

- Takes time (~2-3 hours to complete)
- Risk of introducing bugs during migration
- Need thorough testing with MCPP RFP

**Recommendation**:

- If MCPP processing is urgent → Skip refactoring, just add Phase 7 batching
- If we have time → Proceed with gradual migration (Option B)

---

**Status**: Proposal draft - awaiting user decision
