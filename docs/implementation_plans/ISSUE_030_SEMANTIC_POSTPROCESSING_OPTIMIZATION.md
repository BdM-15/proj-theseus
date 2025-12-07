# Implementation Plan: Issue #30 - Optimize Semantic Post-Processing

**Issue**: [#30 - Optimize Semantic Post-Processing: Holistic Pipeline Redesign (34min → 2min)](https://github.com/BdM-15/govcon-capture-vibe/issues/30)

**Priority**: P0 - Production Blocker

**Branch**: `029-semantic-postprocessing-optimization`

**Estimated Duration**: 2-4 weeks (3 milestones)

**Expected Impact**: 94% time reduction (34+ min → 2 min), 100% reliability, complete pipeline optimization

---

## Executive Summary

This plan addresses **SYSTEMIC** sequential execution bottlenecks affecting all 8 relationship inference algorithms, with 2 critical failures (Algorithms 3 & 4) blocking production entirely. The solution implements parallel execution architecture + smart batching strategies proven in Issue #17 (87% reduction).

### Current State

- **Runtime**: 34+ minutes for 425-page MCPP RFP
- **Failures**: Algorithm 3 (JSON truncation at 2m32s), Algorithm 4 (30+ min timeout)
- **Architecture**: Sequential execution (no parallelization)
- **Quality**: Unreliable, manual termination required

### Target State

- **Runtime**: 2 minutes (94% reduction)
- **Failures**: Zero (production-ready reliability)
- **Architecture**: 3-wave parallel execution with semaphore-based rate limiting
- **Quality**: Maintained/improved via batching with overlap

---

## Problem Analysis

### Root Causes

1. **SYSTEMIC BOTTLENECK: Sequential Execution** (lines 414-930)

   - All 8 algorithms wait for previous completion
   - No `asyncio.gather` usage (proven pattern from Issue #17)
   - Total time = SUM(all algorithms) instead of MAX(parallel groups)

2. **CRITICAL FAILURE: Algorithm 3 (Requirement→Evaluation Mapping)**

   - **Runtime**: 2m32s for 1,201 requirements
   - **Error**: JSON truncation at 105,278 characters
   - **Cause**: Processing requirements ONE-BY-ONE (1,201 sequential LLM calls)

3. **CRITICAL FAILURE: Algorithm 4 (Deliverable Traceability)**
   - **Runtime**: 30+ minutes without completion
   - **Error**: Timeout (user-terminated)
   - **Cause**: Single massive prompt (1,201 reqs × 150 deliverables = 180K combinations)

### Current Performance (425-page MCPP RFP)

| Algorithm                          | Runtime        | Status               | Root Cause                  |
| ---------------------------------- | -------------- | -------------------- | --------------------------- |
| **EXECUTION**                      | **SEQUENTIAL** | 🔴 **#1 BOTTLENECK** | No `asyncio.gather`         |
| Algorithm 1: Instruction→Eval      | ~15-30s        | ✅ Working           | Could benefit from batching |
| Algorithm 2: Eval Hierarchy        | ~10-20s        | ✅ Working           | Could benefit from batching |
| **Algorithm 3: Req→Eval**          | **2m32s**      | 🔴 **FAILING**       | 1,201 sequential calls      |
| **Algorithm 4: Deliverable Trace** | **30+ min**    | 🔴 **TIMEOUT**       | Massive single prompt       |
| Algorithm 5: Doc Hierarchy         | ~10-15s        | ✅ Working           | Could benefit from batching |
| Algorithm 6: Concept Linking       | ~15-25s        | ✅ Working           | 50-concept limit hardcoded  |
| Algorithm 7: CDRL Heuristic        | <1s            | ✅ Optimal           | Regex-based (no LLM)        |
| Algorithm 8: Orphan Resolution     | ~20-30s        | ✅ Working           | Could benefit from batching |
| **TOTAL**                          | **34+ min**    | 🔴 **UNRELIABLE**    | Sequential + failures       |

---

## Solution Strategy

### Guiding Principles

1. **PARALLELIZE FIRST** - Execution architecture trumps algorithm optimizations (proven 87% reduction)
2. **BATCH EVERYTHING** - No single-entity processing, no massive all-in-one calls
3. **DYNAMIC SIZING** - Adapt batch size to entity count and complexity
4. **PRESERVE QUALITY** - Use overlap, validation, and proven patterns from Issue #17

### Three-Phase Approach

- **Phase 1** (Week 1): Parallel foundation + critical fixes (Algorithms 3 & 4)
- **Phase 2** (Week 2): Optimize remaining algorithms (1, 2, 5, 6, 8)
- **Phase 3** (Week 3-4): Advanced optimizations (streaming, compression, caching)

---

## Phase 1: Parallel Foundation + Critical Fixes (Week 1) 🔥

**Objective**: Fix production blockers AND establish parallel execution for ALL algorithms

**Expected Impact**: 34+ min → ~3min (91% reduction)

### Task 1.1: Refactor Execution Architecture (Sequential → Parallel)

**File**: `src/inference/semantic_post_processor.py`

**Location**: `_infer_relationships_multi_algorithm()` function (lines 414-930)

**Changes**:

1. **Replace sequential execution with 3-wave parallel architecture**:

```python
async def _infer_relationships_multi_algorithm(
    entities: List[Dict],
    existing_rels: List[Dict],
    neo4j_io,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Multi-algorithm relationship inference with PARALLEL execution.

    Algorithms grouped into 3 independent waves:
    - Wave 1: Document structure (Algorithms 1, 2, 5) - no dependencies
    - Wave 2: Relationship inference (Algorithms 3, 4) - batched processing
    - Wave 3: Semantic linking (Algorithms 6, 8) - independent
    - Algorithm 7: Heuristic (instant, regex-based) - runs separately

    Proven pattern from Issue #17: asyncio.gather + semaphore = 87% reduction
    """
    import asyncio

    all_relationships = []

    # Build entity lookups
    id_to_entity = {e['id']: e for e in entities}
    entities_by_type = {}
    for e in entities:
        entity_type = e.get('entity_type', 'unknown')
        entities_by_type.setdefault(entity_type, []).append(e)

    # Load system prompt
    system_prompt = await _load_prompt_template("system_prompt.md")

    # Create semaphore for rate limiting (4 concurrent LLM calls max)
    semaphore = asyncio.Semaphore(int(os.getenv("MAX_ASYNC", 4)))

    # WAVE 1: Document structure algorithms (independent)
    logger.info("\n🌊 Wave 1: Document Structure Analysis")
    wave_1_tasks = [
        _algorithm_1_instruction_eval(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
        _algorithm_2_eval_hierarchy(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
        _algorithm_5_doc_hierarchy(entities, id_to_entity, system_prompt, model, temperature, semaphore),
    ]

    wave_1_results = await asyncio.gather(*wave_1_tasks, return_exceptions=True)
    for i, result in enumerate(wave_1_results, 1):
        if isinstance(result, Exception):
            logger.error(f"  ❌ Wave 1 Algorithm {i} failed: {result}")
        else:
            all_relationships.extend(result)
            logger.info(f"  ✅ Wave 1 Algorithm {i}: {len(result)} relationships")

    # WAVE 2: Batched relationship inference (critical fixes)
    logger.info("\n🌊 Wave 2: Batched Relationship Inference")
    wave_2_tasks = [
        _algorithm_3_req_eval_batched(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
        _algorithm_4_deliverable_trace_batched(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
    ]

    wave_2_results = await asyncio.gather(*wave_2_tasks, return_exceptions=True)
    for i, result in enumerate(wave_2_results, 1):
        if isinstance(result, Exception):
            logger.error(f"  ❌ Wave 2 Algorithm {i} failed: {result}")
        else:
            all_relationships.extend(result)
            logger.info(f"  ✅ Wave 2 Algorithm {i}: {len(result)} relationships")

    # WAVE 3: Semantic linking algorithms (independent)
    logger.info("\n🌊 Wave 3: Semantic Linking")
    wave_3_tasks = [
        _algorithm_6_concept_linking(entities_by_type, id_to_entity, system_prompt, model, temperature, semaphore),
        _algorithm_8_orphan_resolution(entities, id_to_entity, neo4j_io, model, temperature, semaphore),
    ]

    wave_3_results = await asyncio.gather(*wave_3_tasks, return_exceptions=True)
    for i, result in enumerate(wave_3_results, 1):
        if isinstance(result, Exception):
            logger.error(f"  ❌ Wave 3 Algorithm {i} failed: {result}")
        else:
            all_relationships.extend(result)
            logger.info(f"  ✅ Wave 3 Algorithm {i}: {len(result)} relationships")

    # ALGORITHM 7: Heuristic pattern matching (instant, no LLM)
    logger.info("\n⚡ Algorithm 7: Heuristic Pattern Matching")
    heuristic_rels = _algorithm_7_heuristic(entities, entities_by_type)
    all_relationships.extend(heuristic_rels)
    logger.info(f"  ✅ Algorithm 7: {len(heuristic_rels)} relationships")

    # Summary
    logger.info(f"\n✅ Total relationships from all algorithms: {len(all_relationships)}")
    return all_relationships
```

2. **Add semaphore-wrapped LLM call helper**:

```python
async def _call_llm_with_semaphore(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> str:
    """
    Async LLM call with semaphore-based rate limiting.

    Prevents overwhelming xAI API with concurrent requests.
    Default: 4 concurrent calls (configurable via MAX_ASYNC env var)
    """
    async with semaphore:
        return await _call_llm_async(prompt, system_prompt, model, temperature)
```

**Acceptance Criteria**:

- ✅ All algorithms run in parallel within appropriate waves
- ✅ Semaphore limits concurrent LLM calls to 4 (or MAX_ASYNC env var)
- ✅ Wave-based execution with progress logging
- ✅ Exception handling preserves partial results

---

### Task 1.2: Fix Algorithm 3 - Batching with Overlap (CRITICAL)

**File**: `src/inference/semantic_post_processor.py`

**New Function**: `_algorithm_3_req_eval_batched()`

**Strategy**: Process 100 requirements per LLM call with 20-requirement overlap

**Implementation**:

```python
async def _algorithm_3_req_eval_batched(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Algorithm 3: Requirement→Evaluation Mapping (BATCHED)

    CRITICAL FIX:
    - OLD: 1,201 sequential LLM calls (2m32s, JSON truncation)
    - NEW: ~15 batched calls with overlap (10-15s, no truncation)

    Batching Strategy:
    - Batch size: 100 requirements per call
    - Overlap: 20 requirements between batches
    - Cross-batch relationships preserved via overlap
    - JSON response < 10K chars per batch (vs 105K accumulated)

    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID lookup
        system_prompt: System prompt
        model: LLM model name
        temperature: LLM temperature
        semaphore: Asyncio semaphore for rate limiting

    Returns:
        List of inferred relationships
    """
    requirements = entities_by_type.get('requirement', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])

    # Filter to main evaluation factors (same logic as current)
    main_eval_factors = [f for f in eval_factors if _is_main_evaluation_factor(f)]

    if not requirements or not main_eval_factors:
        logger.info(f"  [Algorithm 3/8] Requirement-Evaluation Mapping: SKIPPED (no requirements or factors)")
        return []

    logger.info(f"  [Algorithm 3/8] Requirement-Evaluation Mapping: {len(requirements)} requirements × {len(main_eval_factors)} main factors (batched)")

    # Load prompt template
    prompt_instructions = await _load_prompt_template("requirement_evaluation.md")

    # Prepare evaluation factors JSON (reused across all batches)
    factors_json = json.dumps([{
        'id': f['id'],
        'name': f['entity_name'],
        'type': f.get('entity_type'),
        'description': f.get('description', '')[:5000]
    } for f in main_eval_factors], indent=2)

    # Batching parameters
    BATCH_SIZE = 100
    OVERLAP = 20

    all_relationships = []
    batch_tasks = []

    # Create batches with overlap
    num_batches = max(1, (len(requirements) + BATCH_SIZE - OVERLAP - 1) // (BATCH_SIZE - OVERLAP))

    for batch_num in range(num_batches):
        batch_start = batch_num * (BATCH_SIZE - OVERLAP)
        batch_end = min(batch_start + BATCH_SIZE, len(requirements))
        batch = requirements[batch_start:batch_end]

        # Build batch JSON
        reqs_json = json.dumps([{
            'id': r['id'],
            'name': r['entity_name'],
            'type': r.get('entity_type'),
            'description': r.get('description', '')[:5000]
        } for r in batch], indent=2)

        prompt = f"""{prompt_instructions}

REQUIREMENTS (batch {batch_num + 1}/{num_batches}):
{reqs_json}

EVALUATION_FACTORS:
{factors_json}

CRITICAL INSTRUCTION - Use factor descriptions for semantic matching:
- Factor names may be generic (Factor A, Factor B, Factor 1, etc.)
- Factor descriptions contain evaluation criteria and topics
- Match requirement CONTENT to factor DESCRIPTION topics, not just factor names

Apply the inference patterns from the instructions above. Use entity IDs from 'id' field (NOT names).
Focus ONLY on main evaluation factors. Exclude rating scales, metrics, and thresholds.
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "factor_id", "relationship_type": "EVALUATED_BY", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""

        # Create async task for this batch
        batch_tasks.append(_process_req_eval_batch(
            prompt, system_prompt, model, temperature, semaphore, id_to_entity, batch_num + 1, num_batches
        ))

    # Process all batches in parallel (within semaphore limits)
    batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

    # Combine results
    for result in batch_results:
        if isinstance(result, Exception):
            logger.error(f"    ❌ Batch failed: {result}")
        else:
            all_relationships.extend(result)

    logger.info(f"    → Found {len(all_relationships)} requirement→main-factor relationships ({num_batches} batches)")
    return all_relationships


async def _process_req_eval_batch(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore,
    id_to_entity: Dict,
    batch_num: int,
    total_batches: int
) -> List[Dict]:
    """Process single batch for Algorithm 3"""
    try:
        async with semaphore:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)

        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 3 Batch {batch_num}/{total_batches}")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Batch {batch_num}/{total_batches} failed: {e}")
        return []


def _is_main_evaluation_factor(entity: Dict) -> bool:
    """
    Identify main evaluation factors vs supporting entities.

    MOVED from inline logic to reusable function.
    """
    # CRITICAL: Neo4j can return None for null values, so use 'or' to ensure string
    name_lower = (entity.get('entity_name') or '').lower()

    # STRICT KEEP: Explicit main factor patterns only
    main_factor_patterns = [
        'factor a', 'factor b', 'factor c', 'factor d', 'factor e', 'factor f',
        'factor 1', 'factor 2', 'factor 3', 'factor 4', 'factor 5', 'factor 6',
        'subfactor',
        'technical factor', 'price factor', 'cost factor', 'management factor',
        'tomp', 'past performance', 'small business',
        'mission essential', 'quality control plan'
    ]

    # Check for methodology subfactors (conditional)
    if 'methodology' in name_lower and any(x in name_lower for x in ['management', 'technical', 'navy', 'usmc', 'army']):
        main_factor_patterns.append('methodology')

    # CRITICAL: Must match at least ONE main factor pattern (default EXCLUDE)
    has_main_pattern = any(pattern in name_lower for pattern in main_factor_patterns)
    if not has_main_pattern:
        return False

    # EXCLUDE: Even if main pattern matched, exclude supporting entities

    # Rating scale values
    rating_values = ['outstanding', 'good', 'acceptable', 'marginal', 'unacceptable',
                    'satisfactory', 'unsatisfactory', 'pass', 'fail',
                    'substantial confidence', 'limited confidence', 'neutral confidence',
                    'very relevant', 'relevant', 'somewhat relevant', 'not relevant']
    if any(rating in name_lower for rating in rating_values):
        return False

    # Generic processes/analyses
    generic_processes = ['analysis', 'assessment', 'government evaluation', 'interviews',
                       'realism', 'reasonableness', 'completeness', 'adjectival']
    if any(term in name_lower for term in generic_processes):
        return False

    # Metrics/indices
    if any(indicator in name_lower for indicator in ['%', 'cei', 'sei', 'kpi', 'index', 'cost effectiveness']):
        return False

    # Tables/outlines
    if '(table)' in name_lower or 'table' in name_lower or 'outline' in name_lower:
        return False

    # Volume references
    if 'volume' in name_lower and any(x in name_lower for x in ['i', 'ii', 'iii', 'iv', 'v']):
        return False

    # PASSED: Has main pattern AND not excluded = TRUE MAIN FACTOR
    return True
```

**Acceptance Criteria**:

- ✅ Runtime: < 20s (vs 2m32s baseline)
- ✅ Zero JSON truncation errors
- ✅ LLM calls reduced: 1,201 → ~15 batches
- ✅ Relationship counts match baseline ±5%
- ✅ 20-requirement overlap preserves cross-batch relationships

---

### Task 1.3: Fix Algorithm 4 - Sub-Batching Strategy (CRITICAL)

**File**: `src/inference/semantic_post_processor.py`

**New Function**: `_algorithm_4_deliverable_trace_batched()`

**Strategy**: Process 50 requirements per LLM call (all deliverables each time)

**Implementation**:

```python
async def _algorithm_4_deliverable_trace_batched(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Algorithm 4: Deliverable Traceability (SUB-BATCHED)

    CRITICAL FIX:
    - OLD: Single massive prompt (1,201 reqs × 150 delivs = 180K combinations, 30+ min timeout)
    - NEW: ~24 batched calls (50 reqs × 150 delivs = 7,500 combinations each, 1-2 min total)

    Batching Strategy:
    - Batch size: 50 requirements per call
    - Deliverables: ALL deliverables included in each batch (reused context)
    - Cross-product complexity: 7,500 vs 180K combinations per batch
    - Each batch completes in <5s

    Dual-Pattern Approach:
    - Pattern 1: Requirement → Deliverable (evidence relationships)
    - Pattern 2: Work Statement → Deliverable (explicit references)

    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID lookup
        system_prompt: System prompt
        model: LLM model name
        temperature: LLM temperature
        semaphore: Asyncio semaphore for rate limiting

    Returns:
        List of inferred relationships
    """
    requirements = entities_by_type.get('requirement', [])
    work_statements = (entities_by_type.get('statement_of_work', []) +
                       entities_by_type.get('pws', []) +
                       entities_by_type.get('soo', []))
    deliverables = entities_by_type.get('deliverable', [])

    if not deliverables or (not requirements and not work_statements):
        logger.info(f"  [Algorithm 4/8] Deliverable Traceability: SKIPPED (no deliverables or requirements/work)")
        return []

    logger.info(f"  [Algorithm 4/8] Deliverable Traceability: {len(requirements)} requirements + {len(work_statements)} work statements × {len(deliverables)} deliverables (batched)")

    # Load prompt template
    prompt_instructions = await _load_prompt_template("deliverable_traceability.md")

    # Prepare deliverables JSON (reused across all batches)
    deliv_json = json.dumps([{
        'id': d['id'],
        'name': d['entity_name'],
        'type': d.get('entity_type'),
        'description': d.get('description', '')[:5000]
    } for d in deliverables], indent=2)

    # Batching parameters
    BATCH_SIZE = 50

    all_relationships = []

    # PATTERN 1: Requirement → Deliverable (batched)
    if requirements:
        logger.info(f"    → Pattern 1 (Requirement→Deliverable): {len(requirements)} requirements")

        pattern1_tasks = []
        num_batches = (len(requirements) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(num_batches):
            batch_start = batch_num * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, len(requirements))
            batch = requirements[batch_start:batch_end]

            # Build batch JSON
            reqs_json = json.dumps([{
                'id': r['id'],
                'name': r['entity_name'],
                'type': r.get('entity_type'),
                'description': r.get('description', '')[:5000]
            } for r in batch], indent=2)

            prompt = f"""{prompt_instructions}

Apply PATTERN 1 (Requirement → Deliverable) detection rules.

REQUIREMENTS (batch {batch_num + 1}/{num_batches}):
{reqs_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on evidence relationships (deliverables that prove/document requirement compliance).
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "deliverable_id", "relationship_type": "SATISFIED_BY", "confidence": 0.50-0.95, "reasoning": "evidence relationship explanation"}}
]
"""

            pattern1_tasks.append(_process_deliverable_batch(
                prompt, system_prompt, model, temperature, semaphore, id_to_entity,
                f"Pattern 1 Batch {batch_num + 1}/{num_batches}"
            ))

        # Process Pattern 1 batches in parallel
        pattern1_results = await asyncio.gather(*pattern1_tasks, return_exceptions=True)

        pattern1_count = 0
        for result in pattern1_results:
            if isinstance(result, Exception):
                logger.error(f"    ❌ Pattern 1 batch failed: {result}")
            else:
                all_relationships.extend(result)
                pattern1_count += len(result)

        logger.info(f"    → Pattern 1: {pattern1_count} relationships")

    # PATTERN 2: Work Statement → Deliverable (batched)
    if work_statements:
        logger.info(f"    → Pattern 2 (WorkStatement→Deliverable): {len(work_statements)} work statements")

        pattern2_tasks = []
        num_batches = (len(work_statements) + BATCH_SIZE - 1) // BATCH_SIZE

        for batch_num in range(num_batches):
            batch_start = batch_num * BATCH_SIZE
            batch_end = min(batch_start + BATCH_SIZE, len(work_statements))
            batch = work_statements[batch_start:batch_end]

            # Build batch JSON
            work_json = json.dumps([{
                'id': w['id'],
                'name': w['entity_name'],
                'type': w.get('entity_type'),
                'description': w.get('description', '')[:5000]
            } for w in batch], indent=2)

            prompt = f"""{prompt_instructions}

Apply PATTERN 2 (Work Statement → Deliverable) detection rules.

WORK_STATEMENTS (batch {batch_num + 1}/{num_batches}):
{work_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on explicit CDRL references and work-product relationships.
Return ONLY valid JSON array:
[
  {{"source_id": "work_statement_id", "target_id": "deliverable_id", "relationship_type": "PRODUCES", "confidence": 0.50-0.96, "reasoning": "explicit reference or work-product explanation"}}
]
"""

            pattern2_tasks.append(_process_deliverable_batch(
                prompt, system_prompt, model, temperature, semaphore, id_to_entity,
                f"Pattern 2 Batch {batch_num + 1}/{num_batches}"
            ))

        # Process Pattern 2 batches in parallel
        pattern2_results = await asyncio.gather(*pattern2_tasks, return_exceptions=True)

        pattern2_count = 0
        for result in pattern2_results:
            if isinstance(result, Exception):
                logger.error(f"    ❌ Pattern 2 batch failed: {result}")
            else:
                all_relationships.extend(result)
                pattern2_count += len(result)

        logger.info(f"    → Pattern 2: {pattern2_count} relationships")

    logger.info(f"    → Total Deliverable Traceability: {len(all_relationships)} relationships")
    return all_relationships


async def _process_deliverable_batch(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore,
    id_to_entity: Dict,
    batch_label: str
) -> List[Dict]:
    """Process single batch for Algorithm 4"""
    try:
        async with semaphore:
            response = await _call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)

        rels = json.loads(response.strip())
        valid_rels = _validate_relationships(rels, id_to_entity, f"Algorithm 4 {batch_label}")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ {batch_label} failed: {e}")
        return []
```

**Acceptance Criteria**:

- ✅ Runtime: < 2 min (vs 30+ min baseline)
- ✅ Zero timeout errors
- ✅ LLM calls: 1 massive → ~24 batches (Pattern 1) + work statement batches (Pattern 2)
- ✅ Each batch: 7,500 combinations vs 180K (24x reduction)
- ✅ Relationship quality improved (LLM focuses on manageable subset)

---

### Task 1.4: Refactor Remaining Algorithms for Parallel Execution

Extract inline algorithm logic into separate async functions compatible with `asyncio.gather`:

**Functions to Create**:

1. `_algorithm_1_instruction_eval()` - Extract Algorithm 1 logic
2. `_algorithm_2_eval_hierarchy()` - Extract Algorithm 2 logic
3. `_algorithm_5_doc_hierarchy()` - Extract Algorithm 5 logic
4. `_algorithm_6_concept_linking()` - Extract Algorithm 6 logic
5. `_algorithm_7_heuristic()` - Extract Algorithm 7 logic (sync function)
6. `_algorithm_8_orphan_resolution()` - Refactor existing `_resolve_orphan_patterns()`

**Pattern for Each Function**:

```python
async def _algorithm_X_name(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Algorithm X: Description

    Args:
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID lookup
        system_prompt: System prompt
        model: LLM model name
        temperature: LLM temperature
        semaphore: Asyncio semaphore for rate limiting

    Returns:
        List of inferred relationships
    """
    # Extract current inline logic
    # Wrap LLM calls with: async with semaphore:
    # Return list of relationships
```

**Acceptance Criteria**:

- ✅ All 8 algorithms extracted to separate functions
- ✅ Each function uses semaphore for rate limiting
- ✅ Consistent function signature across all algorithms
- ✅ Proper error handling with try/except
- ✅ Logging matches current format

---

### Task 1.5: Add Configuration and Environment Variables

**File**: `.env` (document in README if not already present)

**New Variables**:

```bash
# Semantic Post-Processing Configuration
MAX_ASYNC=4                          # Max concurrent LLM calls (semaphore limit)
BATCH_SIZE_ALGORITHM_3=100          # Requirements per batch for Algorithm 3
BATCH_OVERLAP_ALGORITHM_3=20        # Overlap between batches for Algorithm 3
BATCH_SIZE_ALGORITHM_4=50           # Requirements/work statements per batch for Algorithm 4
```

**File**: `src/inference/semantic_post_processor.py`

**Implementation**:

```python
# Configuration (top of file, after imports)
MAX_CONCURRENT_LLM_CALLS = int(os.getenv("MAX_ASYNC", 4))
BATCH_SIZE_ALGO3 = int(os.getenv("BATCH_SIZE_ALGORITHM_3", 100))
BATCH_OVERLAP_ALGO3 = int(os.getenv("BATCH_OVERLAP_ALGORITHM_3", 20))
BATCH_SIZE_ALGO4 = int(os.getenv("BATCH_SIZE_ALGORITHM_4", 50))
```

**Acceptance Criteria**:

- ✅ Configuration values read from environment variables
- ✅ Sensible defaults if env vars not set
- ✅ Documentation in `.env.example` or README

---

### Task 1.6: Testing and Validation

**Test File**: `tests/test_semantic_postprocessing_parallel.py` (new)

**Test Cases**:

```python
"""
Validation tests for parallel semantic post-processing (Issue #30 Phase 1)
"""
import pytest
import asyncio
import time
from src.inference.semantic_post_processor import _semantic_post_processor_neo4j
from src.inference.neo4j_graph_io import Neo4jGraphIO


@pytest.mark.asyncio
async def test_algorithm_3_batching():
    """Verify Algorithm 3 uses batching (no JSON truncation)"""
    # Run semantic post-processing on MCPP workspace
    stats = await _semantic_post_processor_neo4j(llm_model_name="grok-4-fast-reasoning")

    # Check for errors in stats
    assert stats.get('errors') == 0 or stats.get('errors') is None
    assert 'JSON truncation' not in str(stats)


@pytest.mark.asyncio
async def test_algorithm_4_no_timeout():
    """Verify Algorithm 4 completes without timeout"""
    start_time = time.time()

    stats = await _semantic_post_processor_neo4j(llm_model_name="grok-4-fast-reasoning")

    elapsed = time.time() - start_time

    # Should complete in < 5 minutes (was 30+ min before)
    assert elapsed < 300, f"Algorithm 4 took {elapsed}s (expected < 300s)"


@pytest.mark.asyncio
async def test_parallel_execution_performance():
    """Verify parallel execution reduces total time"""
    start_time = time.time()

    stats = await _semantic_post_processor_neo4j(llm_model_name="grok-4-fast-reasoning")

    elapsed = time.time() - start_time

    # Target: < 5 minutes (conservative for Phase 1)
    # Ultimate goal: < 3 minutes
    assert elapsed < 300, f"Total pipeline took {elapsed}s (expected < 300s for Phase 1)"


@pytest.mark.asyncio
async def test_relationship_quality_maintained():
    """Verify relationship counts match baseline ±5%"""
    neo4j_io = Neo4jGraphIO()

    # Get relationship counts before and after
    entities_before, rels_before = neo4j_io.read_graph()

    stats = await _semantic_post_processor_neo4j(llm_model_name="grok-4-fast-reasoning")

    entities_after, rels_after = neo4j_io.read_graph()

    # Check relationship count increase
    new_rels = len(rels_after) - len(rels_before)

    # Should add relationships (not lose them)
    assert new_rels > 0, f"No new relationships added (before: {len(rels_before)}, after: {len(rels_after)})"

    # Compare to baseline (if available)
    # TODO: Load baseline counts from test fixture


@pytest.mark.asyncio
async def test_semaphore_rate_limiting():
    """Verify semaphore limits concurrent LLM calls"""
    # This test would require instrumentation in _call_llm_async
    # to track concurrent calls. Placeholder for future enhancement.
    pass
```

**Manual Validation**:

1. **Baseline Capture** (if Algorithm 3/4 failures allow):

   - Process MCPP RFP with current code (if completes)
   - Export Neo4j graph: `python tools/neo4j/export_workspace.py --workspace 2_mcpp_drfp_2025 --output baseline_graph.graphml`
   - Save entity/relationship counts

2. **Phase 1 Testing**:

   - Create new workspace: `python tools/neo4j/duplicate_workspace.py`
   - Process MCPP RFP with Phase 1 code
   - Export graph: `python tools/neo4j/export_workspace.py --workspace test_phase1 --output phase1_graph.graphml`
   - Compare metrics

3. **Quality Validation**:
   - Entity counts: ±2% variance
   - Relationship counts: ±5% variance
   - Sample 50 random relationships for accuracy
   - Manual review: 90%+ accuracy maintained

**Acceptance Criteria**:

- ✅ All automated tests pass
- ✅ Total pipeline time < 5 min (target: 3 min)
- ✅ Zero JSON truncation or timeout errors
- ✅ Relationship counts match baseline ±5%
- ✅ Manual quality review: 90%+ accuracy

---

### Phase 1 Milestone Checklist

- [ ] Task 1.1: Parallel execution architecture implemented
- [ ] Task 1.2: Algorithm 3 batching implemented
- [ ] Task 1.3: Algorithm 4 sub-batching implemented
- [ ] Task 1.4: All 8 algorithms refactored for parallelism
- [ ] Task 1.5: Configuration and env vars added
- [ ] Task 1.6: Tests pass, validation complete
- [ ] **Success Criteria Met**:
  - [ ] Algorithm 3: < 20s (vs 2m32s)
  - [ ] Algorithm 4: < 2min (vs 30+ min)
  - [ ] Total pipeline: < 5min (target: 3min)
  - [ ] Zero JSON truncation or timeout errors
  - [ ] Relationship counts match baseline ±5%

**Expected Delivery**: End of Week 1

---

## Phase 2: Optimize Remaining Algorithms (Week 2) ⚡

**Objective**: Apply batching strategies to Algorithms 1, 2, 5, 6, 8 for improved scalability

**Expected Impact**: 3min → 2.5min (additional 17% reduction)

### Task 2.1: Algorithm 1 - Batch by Instruction Type

**Strategy**: Group instructions by type, process groups in parallel

**Implementation**:

```python
async def _algorithm_1_instruction_eval_batched(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Algorithm 1: Instruction-Evaluation Linking (TYPE-BATCHED)

    Optimization:
    - Group instructions by type (submission, deliverable, requirement)
    - Process groups in parallel
    - Reduces context size and improves LLM focus

    Expected: 15-30s → 10s
    """
    # Group instructions by source type
    # Process each group as separate LLM call
    # Use asyncio.gather for parallel execution
```

### Task 2.2: Algorithm 2 - Batch by Parent Factor

**Strategy**: Group evaluation hierarchy by root factor, process hierarchies independently

### Task 2.3: Algorithm 5 - Batch by Document Type

**Strategy**: Group documents by type (attachments, sections, clauses), process types in parallel

### Task 2.4: Algorithm 6 - Dynamic Batching

**Strategy**: Remove 50-concept hardcoded limit, implement dynamic batch sizing

### Task 2.5: Algorithm 8 - Conditional Batching

**Strategy**: Batch orphan resolution if > 100 orphans, otherwise single call

### Task 2.6: Scalability Testing

**Test**: Process 2x larger RFPs (1,000+ pages) to validate batching handles scale

**Acceptance Criteria**:

- ✅ Algorithms 1, 2, 5, 6, 8: All < 20s each
- ✅ Total pipeline: < 3min
- ✅ Handles 2x larger RFPs without degradation
- ✅ No arbitrary limits (50-concept cap removed)

**Expected Delivery**: End of Week 2

---

## Phase 3: Advanced Optimizations (Week 3-4) 🔬

**Objective**: Implement streaming, compression, and caching for ultimate performance

**Expected Impact**: 2.5min → 2min (additional 20% reduction)

### Task 3.1: Streaming JSON Responses

**Strategy**: Implement Server-Sent Events (SSE) streaming for Algorithm 3 to eliminate truncation risk

**Implementation**:

```python
async def _stream_json_relationships(
    prompt: str,
    system_prompt: str,
    model: str,
    temperature: float,
    semaphore: asyncio.Semaphore
) -> List[Dict]:
    """
    Stream JSON relationships from LLM using SSE.

    Benefits:
    - No max_output_tokens limit (eliminates truncation)
    - Progressive parsing (detect errors early)
    - Lower memory footprint
    """
    import ijson

    async with semaphore:
        client = AsyncOpenAI(
            api_key=os.getenv("LLM_BINDING_API_KEY"),
            base_url=os.getenv("LLM_BINDING_HOST")
        )

        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            stream=True,
            temperature=temperature
        )

        buffer = ""
        relationships = []

        async for chunk in stream:
            content = chunk.choices[0].delta.content or ""
            buffer += content

            # Parse incrementally using ijson
            try:
                parsed = ijson.items(buffer, 'item')
                for item in parsed:
                    relationships.append(item)
            except ijson.IncompleteJSONError:
                continue  # Wait for more data

        return relationships
```

### Task 3.2: Prompt Compression

**Strategy**: Reduce system prompt verbosity by 30-50% (token reduction → faster inference, lower costs)

### Task 3.3: KV Cache Optimization

**Strategy**: Reuse evaluation factor context across Algorithm 3 batches (if xAI API supports)

### Task 3.4: Dynamic Batch Sizing

**Strategy**: Adjust batch size based on entity complexity (average description length, entity type)

**Acceptance Criteria**:

- ✅ Total pipeline: < 2min
- ✅ Zero API errors across all algorithms
- ✅ 50% reduction in token usage (compression)
- ✅ Streaming implemented (progressive UI updates possible)

**Expected Delivery**: End of Week 3-4

---

## Implementation Workflow

### Branch Management

**Branch Name**: `029-semantic-postprocessing-optimization`

**Workflow**:

```powershell
# 1. Create feature branch from main
git checkout main
git pull origin main
git checkout -b 029-semantic-postprocessing-optimization

# 2. Develop Phase 1 (Week 1)
# ... implement tasks 1.1 - 1.6 ...

# 3. Commit incrementally (Conventional Commits)
git add src/inference/semantic_post_processor.py
git commit -m "feat(inference): implement parallel execution architecture for semantic post-processing"

git add tests/test_semantic_postprocessing_parallel.py
git commit -m "test(inference): add validation tests for parallel semantic post-processing"

# 4. Push to remote
git push -u origin 029-semantic-postprocessing-optimization

# 5. Create PR after Phase 1 complete
# Link to Issue #30, include validation results
```

### Commit Message Examples

```
feat(inference): implement parallel execution architecture

- Refactor _infer_relationships_multi_algorithm to use 3-wave parallel execution
- Add asyncio.gather for independent algorithm groups
- Implement semaphore-based rate limiting (4 concurrent LLM calls)
- Expected 91% time reduction for semantic post-processing pipeline

Related to #30 (Phase 1)
```

```
feat(inference): implement batching for Algorithm 3 (Requirement→Evaluation)

- Replace 1,201 sequential LLM calls with ~15 batched calls
- Batch size: 100 requirements with 20-requirement overlap
- Eliminates JSON truncation (105K chars → <10K per batch)
- Runtime: 2m32s → 10-15s (90% reduction)

Fixes #30 (Algorithm 3 critical failure)
```

```
feat(inference): implement sub-batching for Algorithm 4 (Deliverable Traceability)

- Replace single massive prompt with ~24 batched calls
- Batch size: 50 requirements per call (all deliverables reused)
- Cross-product complexity: 180K → 7,500 combinations per batch
- Eliminates timeout (30+ min → 1-2min)

Fixes #30 (Algorithm 4 critical failure)
```

---

## Risk Management

| Risk                                         | Likelihood | Impact | Mitigation                                                                                                                                  |
| -------------------------------------------- | ---------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Batching reduces relationship quality**    | Medium     | High   | • 20-30% overlap between batches<br>• Validate on test RFP<br>• Compare to baseline metrics<br>• Adjust overlap if needed                   |
| **Parallel execution hits xAI rate limits**  | Low        | Medium | • Start with semaphore=4<br>• Monitor xAI API dashboard<br>• Adjust MAX_ASYNC env var<br>• Implement exponential backoff                    |
| **Streaming adds implementation complexity** | Medium     | Low    | • Use `ijson` for partial parsing<br>• Extensive testing<br>• Fallback to non-streaming if issues<br>• Phase 3 (not critical path)          |
| **Regression in working algorithms**         | Low        | High   | • Run validation suite<br>• Compare graph structure to baseline<br>• Manual review of sample relationships<br>• Rollback capability via git |
| **Dynamic batching introduces edge cases**   | Medium     | Medium | • Conservative defaults<br>• Boundary testing (0, 1, 1000+ entities)<br>• Logging for debugging<br>• Graceful fallbacks                     |

---

## Success Metrics

### Quantitative (Phase 1 Targets)

- ⏱️ **Total time**: 34+ min → 3 min (91% reduction)
- ✅ **Success rate**: 0% → 100% (eliminate 2 critical failures)
- 🚀 **Throughput**: 4x improvement via parallelization
- 💰 **API cost**: Reduce by ~60% (fewer redundant LLM calls)

### Quantitative (Ultimate Targets - Phase 3)

- ⏱️ **Total time**: 34+ min → 2 min (94% reduction)
- 💰 **API cost**: Reduce by ~80% (batching + compression)
- 📊 **Token usage**: 50% reduction via prompt compression

### Qualitative

- ✅ Production-ready semantic post-processing
- ✅ Predictable, reliable runtime (< 3min guaranteed)
- ✅ Scalable to larger RFPs (500+ page documents)
- ✅ Maintainable codebase (proven patterns from Issue #17)
- ✅ ALL 8 algorithms optimized (not just critical failures)

---

## Documentation Updates

### Files to Update

1. **`docs/inference/SEMANTIC_POST_PROCESSING.md`**:

   - Add "Performance Optimization" section
   - Document parallel execution architecture
   - Explain batching strategies for each algorithm
   - Include configuration options (env vars)

2. **`README.md`** (if semantic post-processing mentioned):

   - Update performance claims (2 min vs 34+ min)
   - Add configuration section for batch sizes

3. **`docs/ARCHITECTURE.md`**:

   - Update semantic post-processing performance metrics
   - Document parallel execution design pattern

4. **`.env.example`** (create if doesn't exist):
   ```bash
   # Semantic Post-Processing Configuration
   MAX_ASYNC=4                          # Max concurrent LLM calls
   BATCH_SIZE_ALGORITHM_3=100          # Requirements per batch for Algorithm 3
   BATCH_OVERLAP_ALGORITHM_3=20        # Overlap for Algorithm 3
   BATCH_SIZE_ALGORITHM_4=50           # Requirements per batch for Algorithm 4
   ```

---

## Related Issues and References

### Related Issues

- **Issue #17**: Parallel chunk extraction (closed) - Proven 87% reduction with `asyncio.gather`

  - Pattern: asyncio.gather + semaphore for rate limiting
  - Validation: Preserved quality with parallel execution
  - Lessons learned: Semaphore prevents rate limit issues

- **Issue #14**: Prompt compression (future enhancement)
  - Relevant for Phase 3 (prompt compression task)
  - 30-50% token reduction potential

### Industry Best Practices (from Issue #30)

1. **Neo4j Advanced RAG** (2025): Batching with overlap for knowledge graph inference
2. **Clarifai LLM Optimization** (2024): Dynamic batching strategies
3. **Chrome Developer Docs** (2025): Streaming LLM responses
4. **Soumendrak Async Guide** (2024): `asyncio.gather` + semaphore patterns
5. **arXiv KG-R1** (2025): Efficient knowledge graph RAG

---

## Appendix: Code Structure

### New/Modified Files

**Modified**:

- `src/inference/semantic_post_processor.py` - Main refactoring (1,086 → ~1,500 lines estimated)

**New**:

- `tests/test_semantic_postprocessing_parallel.py` - Validation tests
- `docs/implementation_plans/ISSUE_030_SEMANTIC_POSTPROCESSING_OPTIMIZATION.md` - This document

**Configuration**:

- `.env` - Add new environment variables
- `.env.example` - Document configuration options

### Function Inventory (Post-Refactoring)

**Main Entry Point**:

- `_semantic_post_processor_neo4j()` - Orchestrator (unchanged signature)

**Core Execution**:

- `_infer_relationships_multi_algorithm()` - **REFACTORED** for parallel execution

**Algorithm Functions** (new/refactored):

- `_algorithm_1_instruction_eval()` - Extracted from inline
- `_algorithm_2_eval_hierarchy()` - Extracted from inline
- `_algorithm_3_req_eval_batched()` - **NEW** batched implementation
- `_algorithm_4_deliverable_trace_batched()` - **NEW** sub-batched implementation
- `_algorithm_5_doc_hierarchy()` - Extracted from inline
- `_algorithm_6_concept_linking()` - Extracted from inline
- `_algorithm_7_heuristic()` - Extracted from inline (sync)
- `_algorithm_8_orphan_resolution()` - Refactor existing `_resolve_orphan_patterns()`

**Helper Functions** (new):

- `_call_llm_with_semaphore()` - Semaphore-wrapped LLM call
- `_process_req_eval_batch()` - Batch processor for Algorithm 3
- `_process_deliverable_batch()` - Batch processor for Algorithm 4
- `_is_main_evaluation_factor()` - Extracted filter logic (reusable)

**Utilities** (existing, unchanged):

- `_call_llm_async()` - Base LLM call
- `_validate_relationships()` - Relationship validation
- `_load_prompt_template()` - Prompt loading

---

## Approval and Sign-Off

**Implementation Plan Reviewed By**: [Agent - GitHub Copilot]

**Date Created**: December 6, 2025

**Status**: Ready for Implementation

**Next Steps**:

1. Create branch `030-semantic-postprocessing-optimization`
2. Begin Phase 1 implementation (Week 1)
3. Daily progress updates in Issue #30 comments
4. PR creation after Phase 1 validation complete

---

**End of Implementation Plan**
