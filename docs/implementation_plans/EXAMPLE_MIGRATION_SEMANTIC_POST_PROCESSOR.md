# Example Migration: semantic_post_processor.py

**File**: `src/inference/semantic_post_processor.py`  
**Current State**: 1,100+ lines with 20+ instances of duplicate code  
**Target State**: Clean, modular code using centralized utilities

---

## Step 1: Update Imports (Top of File)

### Before

```python
import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from openai import AsyncOpenAI
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from src.utils.logging_config import setup_logging

logger = logging.getLogger(__name__)
```

### After

```python
import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

# ✅ NEW: Import centralized utilities
from src.utils.logging_config import setup_logging
from src.utils.llm_client import call_llm_async
from src.utils.llm_parsing import extract_json_from_response

logger = logging.getLogger(__name__)
```

**Changes**:

- Removed `import json` (no longer needed - handled by `extract_json_from_response`)
- Removed `from openai import AsyncOpenAI` (replaced by `call_llm_async` utility)
- Added centralized utility imports

---

## Step 2: DELETE `_call_llm_async` Function

### Before (Lines 47-78 - DELETE ENTIRELY)

```python
async def _call_llm_async(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.3
) -> str:
    """
    Call the LLM asynchronously with the specified prompt

    Args:
        prompt: The user prompt to send to the LLM
        system_prompt: Optional system prompt to set context
        model: The LLM model to use (defaults to grok-4-fast-reasoning)
        temperature: The temperature for generation

    Returns:
        The LLM response as a string
    """
    if model is None:
        model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")

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

    return response.choices[0].message.content
```

### After

```python
# ❌ DELETE ENTIRE FUNCTION (lines 47-78)
# Now using: from src.utils.llm_client import call_llm_async
```

---

## Step 3: Replace All `_call_llm_async` Calls

### Example 1: `infer_section_l_section_m_relationships()`

**Before (Line 173)**

```python
async def infer_section_l_section_m_relationships(
    driver,
    batch_size: int = 20,
    max_concurrent: int = 5
) -> Tuple[int, int]:
    """Infer relationships between Section L and Section M using the LLM."""
    logger = logging.getLogger(__name__)
    logger.info("Starting Section L ↔ Section M inference algorithm")

    semaphore = asyncio.Semaphore(max_concurrent)

    # ... code to fetch entities ...

    # LLM call
    response = await _call_llm_async(prompt, system_prompt)  # ❌ OLD
    relationships = json.loads(response)  # ❌ DUPLICATE PARSING
```

**After**

```python
async def infer_section_l_section_m_relationships(
    driver,
    batch_size: int = 20,
    max_concurrent: int = 5
) -> Tuple[int, int]:
    """Infer relationships between Section L and Section M using the LLM."""
    logger = logging.getLogger(__name__)
    logger.info("Starting Section L ↔ Section M inference algorithm")

    semaphore = asyncio.Semaphore(max_concurrent)

    # ... code to fetch entities ...

    # ✅ NEW: Centralized LLM call + parsing
    response = await call_llm_async(prompt, system_prompt)
    relationships = extract_json_from_response(response)
```

---

### Example 2: `infer_section_l_requirements()` (Lines 350-360)

**Before**

```python
async def _process_section_batch(section_batch: List[Dict], requirements: List[Dict]) -> List[Dict]:
    """Process a batch of Section L entities."""
    # ... code ...

    response = await _call_llm_async(prompt, system_prompt)  # ❌ OLD

    try:
        rels = json.loads(response.strip())  # ❌ DUPLICATE PARSING
        if isinstance(rels, dict):
            rels = rels.get('relationships', [])
        return rels
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        return []
```

**After**

```python
async def _process_section_batch(section_batch: List[Dict], requirements: List[Dict]) -> List[Dict]:
    """Process a batch of Section L entities."""
    # ... code ...

    response = await call_llm_async(prompt, system_prompt)  # ✅ NEW

    try:
        rels = extract_json_from_response(response)  # ✅ NEW: Handles .strip() + code blocks
        if isinstance(rels, dict):
            rels = rels.get('relationships', [])
        return rels
    except (ValueError, TypeError) as e:  # ✅ NEW: Broader error handling
        logger.error(f"Response parsing error: {e}")
        return []
```

---

### Example 3: All Other Algorithms (8 total)

**Search & Replace Pattern**:

1. **Find**: `await _call_llm_async(`
   **Replace**: `await call_llm_async(`

2. **Find**: `json.loads(response.strip())`
   **Replace**: `extract_json_from_response(response)`

3. **Find**: `json.loads(result.strip())`
   **Replace**: `extract_json_from_response(result)`

4. **Find**: `except json.JSONDecodeError`
   **Replace**: `except (ValueError, TypeError)` # ValueError is what extract_json_from_response raises

---

## Step 4: Verify All Changes (8 Algorithms)

### Complete List of Functions to Update

| Line    | Function                                    | Change Required                                                     |
| ------- | ------------------------------------------- | ------------------------------------------------------------------- |
| 47-78   | `_call_llm_async()`                         | ❌ DELETE ENTIRELY                                                  |
| 173     | `infer_section_l_section_m_relationships()` | ✅ Replace call + parsing                                           |
| 350     | `infer_section_l_requirements()`            | ✅ Replace call + parsing                                           |
| 560     | `infer_evaluation_factor_requirement()`     | ✅ Replace call + parsing                                           |
| 728     | `infer_clause_requirement()`                | ✅ Replace call + parsing                                           |
| 849     | `infer_specification_requirement()`         | ✅ Replace call + parsing                                           |
| 950     | `infer_deliverable_phase()`                 | ✅ Replace call + parsing                                           |
| 1077    | `infer_representation_requirement()`        | ✅ Replace call + parsing                                           |
| 234-270 | `_validate_relationships()`                 | ⏸️ NO CHANGE (manual dict validation - Issue #11 will replace this) |

---

## Step 5: Test Migration

### Unit Test (Create New File)

**File**: `tests/test_migrated_semantic_post_processor.py`

````python
"""
Test migrated semantic_post_processor.py uses centralized utilities
"""
import asyncio
import pytest
from unittest.mock import patch, AsyncMock
from src.inference.semantic_post_processor import (
    infer_section_l_section_m_relationships
)
from src.utils.llm_client import call_llm_async
from src.utils.llm_parsing import extract_json_from_response


@pytest.mark.asyncio
async def test_uses_centralized_llm_client():
    """Verify algorithm uses call_llm_async from utils"""
    with patch('src.utils.llm_client.call_llm_async', new_callable=AsyncMock) as mock_llm:
        mock_llm.return_value = '{"relationships": []}'

        # Mock Neo4j driver
        with patch('src.inference.semantic_post_processor.AsyncGraphDatabase') as mock_db:
            mock_driver = AsyncMock()
            mock_session = AsyncMock()
            mock_session.run.return_value.data.return_value = []
            mock_driver.session.return_value.__aenter__.return_value = mock_session

            # Run algorithm
            created, skipped = await infer_section_l_section_m_relationships(
                mock_driver,
                batch_size=5
            )

            # Verify centralized utility was called
            assert mock_llm.called, "Should use call_llm_async from utils"


@pytest.mark.asyncio
async def test_uses_centralized_json_parser():
    """Verify algorithm uses extract_json_from_response"""
    test_response = """
    Here are the relationships:
    ```json
    {
        "relationships": [
            {"source": "REQ-001", "target": "SEC-M-01", "type": "ADDRESSES"}
        ]
    }
    ```
    """

    result = extract_json_from_response(test_response)

    assert isinstance(result, dict)
    assert "relationships" in result
    assert len(result["relationships"]) == 1
````

### Integration Test (Existing)

```powershell
# Run existing smoke test - should still pass
python tests/test_semantic_postprocessing_smoke.py
```

**Expected Output**:

```
✅ All algorithms complete successfully
✅ Same relationship counts as before migration
✅ Cleaner logs (centralized error messages)
```

---

## Step 6: Validate in Production

### Before Migration (Baseline)

```powershell
# Run on MCPP workspace
python tests/test_neo4j_postprocessing.py

# Expected results (from Issue #30):
# - 39 malformed relationships filtered (98.8% success)
# - ~1,145 valid relationships created
```

### After Migration (Should Match)

```powershell
# Re-run same test
python tests/test_neo4j_postprocessing.py

# Expected results:
# - Same or FEWER malformed relationships (better parsing)
# - Same ~1,145 valid relationships created
# - Cleaner error messages in logs
```

---

## Benefits of This Migration

### Code Quality

- **Lines Removed**: ~100+ (deleted `_call_llm_async`, consolidated JSON parsing)
- **Maintainability**: 1 place to fix LLM bugs vs 8 functions
- **Consistency**: All algorithms use same error handling

### Error Handling

**Before**: `json.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`  
**After**: `ValueError: No valid JSON found in LLM response. Response preview: Here is some...`

### Future Enhancements

Add once → benefit everywhere:

- Automatic retry on parsing errors
- Response caching for same prompts
- Token usage tracking
- Cost monitoring

---

## Rollback Plan

If issues occur:

1. **Check Git history**: `git log --oneline src/inference/semantic_post_processor.py`
2. **Revert if needed**: `git checkout HEAD~1 src/inference/semantic_post_processor.py`
3. **Compare results**: Run smoke test on both versions
4. **Fix centralized utility** instead of rolling back (benefits all callers)

---

## Next Steps After This Migration

1. ✅ **semantic_post_processor.py** (this file) - Immediate priority
2. ⏭️ **workload_enrichment.py** - Similar pattern (10 minutes)
3. ⏭️ **Issue #11 Implementation** - Add Pydantic validation using modular utilities
4. ⏭️ **Phase 3 (JSON Schema Mode)** - 4 hours, 80% error reduction

---

**Status**: Ready for implementation  
**Effort**: 30 minutes  
**Risk**: Low (centralized utilities tested, easy rollback)  
**Impact**: Eliminates 20+ instances of duplicate code
