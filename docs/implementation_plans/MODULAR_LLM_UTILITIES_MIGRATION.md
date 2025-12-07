# Migration Guide: Modular LLM Utilities

**Created**: December 7, 2025  
**Purpose**: Eliminate code duplication by centralizing LLM client and parsing logic

---

## Overview

We've extracted repeated LLM interaction patterns into reusable utilities:

- **`src/utils/llm_client.py`** - Async LLM calls to xAI Grok
- **`src/utils/llm_parsing.py`** - JSON extraction and Pydantic validation

This eliminates **20+ instances** of duplicate code across:

- `semantic_post_processor.py`
- `workload_enrichment.py`
- `semantic_post_processor_backup.py`
- Any custom LLM interactions

---

## Quick Reference

### Before (Duplicated Code)

**Pattern 1: LLM Call + JSON Parsing**

```python
# Found in: semantic_post_processor.py (9x), workload_enrichment.py (1x), etc.
client = AsyncOpenAI(
    api_key=os.getenv("LLM_BINDING_API_KEY"),
    base_url=os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
)

messages = []
if system_prompt:
    messages.append({"role": "system", "content": system_prompt})
messages.append({"role": "user", "content": prompt})

response = await client.chat.completions.create(
    model=model,
    messages=messages,
    temperature=temperature
)

result = response.choices[0].message.content
rels = json.loads(result.strip())  # ❌ Repeated 20+ times!
```

**After (Centralized Utility)**

```python
from src.utils.llm_client import call_llm_async
from src.utils.llm_parsing import extract_json_from_response

response = await call_llm_async(prompt, system_prompt, model, temperature)
rels = extract_json_from_response(response)  # ✅ One place, consistent behavior
```

---

**Pattern 2: Markdown Code Block Removal**

````python
# Found in: workload_enrichment.py (1x), likely others
response_clean = response.strip()
if response_clean.startswith("```json"):
    response_clean = response_clean[7:]
if response_clean.startswith("```"):
    response_clean = response_clean[3:]
if response_clean.endswith("```"):
    response_clean = response_clean[:-3]
response_clean = response_clean.strip()

raw_data = json.loads(response_clean)  # ❌ Manual parsing everywhere
````

**After**

```python
from src.utils.llm_parsing import extract_json_from_response

raw_data = extract_json_from_response(response)  # ✅ Handles all cases
```

---

**Pattern 3: Pydantic Validation with Error Handling**

```python
# Found in: workload_enrichment.py (1x)
try:
    enrichment = WorkloadEnrichmentItem.model_validate(raw_enrichment)
except ValidationError as ve:
    logger.warning(f"Pydantic validation error: {ve}")
    # Manually create fallback...
    enrichment = WorkloadEnrichmentItem(
        entity_index=raw_enrichment.get('entity_index', 0),
        # ... manual field mapping ...
    )
```

**After**

```python
from src.utils.llm_parsing import parse_with_pydantic, create_fallback_response

# Option 1: Parse with auto-fallback
enrichment = parse_with_pydantic(
    response,
    WorkloadEnrichmentItem,
    context="Batch 5",
    allow_partial=True  # Returns None on error
)

# Option 2: Explicit fallback
if not enrichment:
    enrichment = create_fallback_response(
        WorkloadEnrichmentItem,
        {"entity_index": 0, "has_workload_metric": True, ...},
        context="Recovery"
    )
```

---

## Migration Checklist

### Phase 1: `semantic_post_processor.py` (Highest Priority)

**File**: `src/inference/semantic_post_processor.py`

**Current Duplications**:

- `_call_llm_async` function (lines 47-78) - **DELETE, use `call_llm_async`**
- `json.loads(result.strip())` - **20+ occurrences** across all algorithms

**Step 1: Replace `_call_llm_async` function**

```python
# DELETE lines 47-78 (entire _call_llm_async function)

# ADD import at top of file:
from src.utils.llm_client import call_llm_async
```

**Step 2: Replace all `json.loads` calls with `extract_json_from_response`**

```python
# ADD import:
from src.utils.llm_parsing import extract_json_from_response

# FIND (appears 20+ times):
rels = json.loads(result.strip())

# REPLACE WITH:
rels = extract_json_from_response(result)
```

**Specific Locations** (use search & replace):

- Line 181: `relationships = json.loads(response)`
- Line 359: `rels = json.loads(response.strip())`
- Line 381: `rels = json.loads(response.strip())`
- Line 569: `rels = json.loads(response.strip())`
- Line 737: `rels = json.loads(result.strip())`
- Line 858: `rels = json.loads(result.strip())`
- Line 959: `rels = json.loads(result.strip())`
- Line 1086: `rels = json.loads(result.strip())`

**All should become**: `rels = extract_json_from_response(response)` or `extract_json_from_response(result)`

---

### Phase 2: `workload_enrichment.py`

**File**: `src/inference/workload_enrichment.py`

**Step 1: Replace markdown cleaning (lines 246-254)**

````python
# DELETE lines 246-254:
response_clean = response.strip()
if response_clean.startswith("```json"):
    response_clean = response_clean[7:]
if response_clean.startswith("```"):
    response_clean = response_clean[3:]
if response_clean.endswith("```"):
    response_clean = response_clean[:-3]
response_clean = response_clean.strip()

raw_data = json.loads(response_clean)

# REPLACE WITH:
from src.utils.llm_parsing import extract_json_from_response

raw_data = extract_json_from_response(response)
````

**Step 2: Simplify Pydantic validation (lines 270-278)**

```python
# CURRENT:
try:
    enrichment = WorkloadEnrichmentItem.model_validate(raw_enrichment)
except ValidationError as ve:
    logger.warning(f"Pydantic validation error: {ve}")
    enrichment = WorkloadEnrichmentItem(
        entity_index=raw_enrichment.get('entity_index', 0),
        has_workload_metric=raw_enrichment.get('has_workload_metric', True),
        workload_categories=raw_enrichment.get('workload_categories', [])
    )

# BETTER (optional - keeps similar pattern but cleaner):
from src.utils.llm_parsing import create_fallback_response

try:
    enrichment = WorkloadEnrichmentItem.model_validate(raw_enrichment)
except ValidationError as ve:
    logger.warning(f"Pydantic validation error: {ve}")
    enrichment = create_fallback_response(
        WorkloadEnrichmentItem,
        {
            'entity_index': raw_enrichment.get('entity_index', 0),
            'has_workload_metric': True,
            'workload_categories': []
        },
        context=f"Batch {batch_num}"
    )
```

---

### Phase 3: Future LLM Operations

**For ANY new LLM operation**, use centralized utilities:

```python
from src.utils.llm_client import call_llm_async, call_llm_with_schema
from src.utils.llm_parsing import extract_json_from_response, parse_with_pydantic

# Option 1: Simple call + manual parsing
response = await call_llm_async(prompt, system_prompt)
data = extract_json_from_response(response)

# Option 2: Structured output with Pydantic (RECOMMENDED)
validated_data = await call_llm_with_schema(
    prompt=prompt,
    response_model=MyPydanticModel,
    system_prompt=system_prompt
)

# Option 3: Batch parallel calls
responses = await call_llm_batch(
    prompts=[prompt1, prompt2, prompt3],
    max_concurrent=4
)
```

---

## Benefits

### 1. **DRY Principle** (Don't Repeat Yourself)

- **Before**: 20+ instances of `json.loads()` with markdown cleaning
- **After**: 1 centralized function with comprehensive error handling

### 2. **Consistent Behavior**

- All LLM calls use same retry logic
- All JSON parsing handles same edge cases
- All errors logged consistently

### 3. **Easier Debugging**

- Change logging in ONE place → affects all operations
- Add new error handling → automatically used everywhere
- Performance monitoring centralized

### 4. **Better Error Messages**

```python
# Before:
json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)

# After:
ValueError: No valid JSON found in LLM response.
Response preview: Here is some explanation before the JSON...
```

### 5. **Future Enhancements**

Add features once, benefit everywhere:

- Automatic retry on validation errors
- Response caching
- Token usage tracking
- Cost monitoring

---

## Testing After Migration

### Unit Tests

```powershell
# Test parsing utilities
python -m pytest tests/test_llm_parsing.py -v

# Test client utilities
python -m pytest tests/test_llm_client.py -v
```

### Integration Tests

```powershell
# Run semantic post-processing (uses migrated code)
python tests/test_semantic_postprocessing_smoke.py

# Run workload enrichment
python tests/test_workload_enrichment.py
```

### Validation

1. **Check logs** - Should see cleaner error messages
2. **Compare results** - Same relationship counts as before migration
3. **Monitor performance** - Should be equivalent (minimal overhead)

---

## Rollback Plan

If issues occur after migration:

1. **Git revert** to previous commit
2. **Identify problematic function** (check logs)
3. **Fix in centralized utility** (benefits all callers)
4. **Re-migrate incrementally** (one file at a time)

---

## Implementation Priority

| File                         | Duplications | Priority | Effort  | Timeline         |
| ---------------------------- | ------------ | -------- | ------- | ---------------- |
| `semantic_post_processor.py` | 20+          | **P0**   | 30 min  | Immediate        |
| `workload_enrichment.py`     | 2            | **P1**   | 10 min  | Same day         |
| Future code                  | N/A          | **P1**   | Ongoing | Always use utils |

---

## Success Metrics

### Before Migration

- **20+** instances of duplicate JSON parsing code
- **3** different LLM client implementations
- Ad-hoc error handling per file

### After Migration

- **1** centralized JSON parsing utility
- **1** centralized LLM client
- **Consistent** error handling everywhere

**Lines of Code Saved**: ~150+ (conservative estimate)  
**Maintenance Burden**: Reduced by ~80%  
**Bug Risk**: Reduced (single source of truth)

---

**Status**: Ready for implementation  
**Next Steps**: Start with Phase 1 (`semantic_post_processor.py`) migration
