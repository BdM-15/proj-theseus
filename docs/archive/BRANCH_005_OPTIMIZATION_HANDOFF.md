# Branch 005: MinerU Optimization - Implementation Handoff

**Date**: October 10, 2025  
**Current Branch**: `005-mineru-optimization`  
**Status**: ✅ Ready for Implementation  
**Parent**: `main` (includes Branch 005 Entity Type Fix - 313 lines removed)

---

## 🎯 Mission

**Implement Grok-4-fast-reasoning's self-diagnosed solutions to reduce entity type corruption from 22 warnings to <5 warnings per RFP.**

---

## ✅ What's Been Completed

### Branch 005 Entity Type Fix (Merged to Main)

- ✅ Deleted `src/utils/entity_cleanup.py` (257 lines) - defensive code that ran too late
- ✅ Removed entity_cleanup integration from `routes.py` (29 lines)
- ✅ Simplified extraction prompt in `initialization.py` (15 lines) - removed "WRONG EXAMPLES"
- ✅ Cleaned up `utils/__init__.py` (12 lines)
- ✅ **Total**: 313 lines removed
- ✅ **Result**: 76% reduction in warnings (90+ → 22)
- ✅ **Test**: MCPP RFP (425 pages) processed successfully - 2,962 entities extracted

### Key Findings

1. **Hotel WiFi Impact**: Sporadic 403 embedding errors (2 out of 2,962 entities) due to unstable connection - NOT a bug
2. **Root Cause Identified**: Grok-4-fast self-diagnostic revealed prompt echoing + field count confusion
3. **VDB Retries Work**: System successfully retried failed embeddings - no data loss

---

## 📋 Implementation Plan - Priority Order

### **TASK 1: Ultra-Simplify Entity Type List** (HIGH PRIORITY - 30 min)

**Problem**: Current prompt has delimiter instructions that Grok "echoes" into output

- References to `#`, `|`, `>` characters trigger corruption patterns
- Grok interprets these as structural markers to include in output

**Solution**: Grok's Recommendation #1

```python
# CURRENT (initialization.py, ~line 145):
entity_types = ["ORGANIZATION", "CONCEPT", "EVENT", ...]
# + 50 lines of delimiter usage instructions with special characters

# TARGET:
entity_types = [
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY",
    "PERSON", "LOCATION", "REQUIREMENT", "CLAUSE",
    "SECTION", "DOCUMENT", "DELIVERABLE", "EVALUATION_FACTOR",
    "SUBMISSION_INSTRUCTION", "STATEMENT_OF_WORK", "ANNEX",
    "PROGRAM", "STRATEGIC_THEME", "EQUIPMENT", "REGULATION"
]

# Present as SIMPLE BULLETED LIST:
"Valid entity types (choose ONE per entity):
• ORGANIZATION
• CONCEPT
• EVENT
... (no special characters anywhere)"
```

**Files to Edit**:

- `src/server/initialization.py` (lines ~140-200)

**Expected Impact**: 50% reduction in corruption (22 → 11 warnings)

---

### **TASK 2: Pre-Validation Sanitizer** (HIGH PRIORITY - 45 min)

**Problem**: Old cleanup code ran AFTER validation rejected entities (too late)

**Solution**: Grok's Recommendation #3 - Strip corruption BEFORE validation

```python
# NEW FILE: src/utils/entity_sanitizer.py

import re
from typing import Tuple

def sanitize_entity_type(entity_type: str) -> Tuple[str, bool]:
    """
    Clean entity type BEFORE validation (runs early, not late like old cleanup).

    Returns:
        (cleaned_type, was_corrupted)
    """
    original = entity_type

    # Strip corruption patterns
    cleaned = re.sub(r'#[/>|]+', '', entity_type)  # Remove #/>, #>|, #|
    cleaned = cleaned.strip().upper()               # Normalize case

    was_corrupted = (original != cleaned)
    return cleaned, was_corrupted

def sanitize_entities_batch(entities: List[Dict]) -> Tuple[List[Dict], int]:
    """
    Sanitize all entities BEFORE validation.
    Logs corruption patterns for monitoring.
    """
    cleaned_entities = []
    corruption_count = 0

    for entity in entities:
        entity_type = entity.get('entity_type', '')
        cleaned_type, was_corrupted = sanitize_entity_type(entity_type)

        if was_corrupted:
            corruption_count += 1
            logger.debug(f"Sanitized: '{entity_type}' → '{cleaned_type}'")

        entity['entity_type'] = cleaned_type
        cleaned_entities.append(entity)

    if corruption_count > 0:
        logger.info(f"Pre-validation sanitizer cleaned {corruption_count} corrupted types")

    return cleaned_entities, corruption_count
```

**Integration Point**: `src/server/routes.py` - BEFORE entity validation

```python
# In /insert endpoint, around line 180 (after entity extraction, before validation)

# NEW: Pre-validation sanitization (runs EARLY, not late)
entities, corruption_count = sanitize_entities_batch(extracted_entities)

# THEN: Existing validation (now works on clean data)
valid_entities = [e for e in entities if e['entity_type'] in VALID_ENTITY_TYPES]
```

**Key Difference from Old Code**:

- ❌ OLD: Cleanup ran in Phase 6 (after validation rejected entities)
- ✅ NEW: Sanitizer runs in Phase 1 (before validation, entities recovered)

**Expected Impact**: 50% reduction in remaining warnings (11 → <5 warnings)

---

### **TASK 3: Prompt Modularization** (MEDIUM PRIORITY - 1 hour)

**Problem**: ~100-line entity extraction prompt hardcoded in `initialization.py`

**Solution**: Extract to `/prompts/entity_extraction/entity_extraction_prompt.md`

**Steps**:

1. Create `/prompts/entity_extraction/entity_extraction_prompt.md`

   - Extract lines 140-240 from `initialization.py`
   - Add metadata header
   - Document template variables: `{entity_types}`, `{tuple_delimiter}`

2. Create `src/utils/prompt_loader.py`

   ```python
   def load_prompt(prompt_path: str, variables: Dict[str, str]) -> str:
       """Load prompt from /prompts with template substitution."""
       with open(prompt_path, 'r', encoding='utf-8') as f:
           prompt = f.read()

       for key, value in variables.items():
           prompt = prompt.replace(f"{{{key}}}", value)

       return prompt
   ```

3. Update `src/server/initialization.py`

   ```python
   from src.utils.prompt_loader import load_prompt

   # Replace hardcoded prompt with:
   entity_extraction_prompt = load_prompt(
       'prompts/entity_extraction/entity_extraction_prompt.md',
       variables={
           'entity_types': '\n'.join(f'• {t}' for t in entity_types),
           'tuple_delimiter': '<|>',
           'record_delimiter': '##',
           'completion_delimiter': '<|COMPLETE|>'
       }
   )
   ```

4. Update `src/utils/__init__.py` - add `load_prompt` export

**Benefits**:

- Cleaner code: -100 lines from `initialization.py`
- Easier prompt iteration: Edit markdown, not Python
- Aligns with existing `/prompts/relationship_inference/` architecture

---

### **TASK 4: Test grok-2-1212 Model** (LOW PRIORITY - 15 min)

**Problem**: `grok-4-fast-reasoning` trades accuracy for speed

**Solution**: Grok's Recommendation #4 - Test slower, more accurate model

**Change**: `.env` file

```bash
# CURRENT:
LLM_MODEL=grok-4-fast-reasoning

# TEST:
LLM_MODEL=grok-2-1212  # Better schema adherence, ~2x slower
```

**Test Process**:

1. Update `.env`
2. Restart server: `python app.py`
3. Re-upload Navy MBOS (71 pages - quick baseline)
4. Count warnings in logs
5. Compare: grok-4-fast vs grok-2-1212

**Decision Criteria**:

- If grok-2-1212: <3 warnings → Keep it (acceptable 2x slowdown)
- If grok-2-1212: >10 warnings → Revert to grok-4-fast (speed matters)

---

### **TASK 5: UCF Redundancy Experiment** (DEFERRED)

**Status**: Postponed until Tasks 1-3 complete

**Hypothesis**: MinerU table extraction might make 971-line UCF detection system redundant

**Experiment**: 30-minute test

1. Disable UCF detection in `routes.py`
2. Re-upload Navy MBOS
3. Compare entity counts (target: ±5% of 4,302 baseline)
4. If successful → Delete 971 lines (40% LOC reduction)

**Risk**: Low (separate branch, quick rollback)

---

## 📊 Success Metrics

### Current Baseline (After Branch 005 Entity Type Fix)

- Entity Type Warnings: **22** (MCPP RFP, 425 pages)
- Entity Extraction: **2,962 entities** (successful)
- Processing Time: **~5 minutes** (cloud-optimized)
- Cost: **~$0.05** (Grok-4-fast + OpenAI embeddings)

### Target Metrics (After Tasks 1-3)

- Entity Type Warnings: **<5** (95% improvement from baseline 90+)
- Entity Extraction: **≥2,900 entities** (≤5% loss acceptable)
- Processing Time: **≤6 minutes** (≤20% slowdown acceptable)
- Code Quality: **-100 lines** (prompt modularization)

---

## 🔧 Technical Context

### Entity Types (19 total)

```python
ORGANIZATION, CONCEPT, EVENT, TECHNOLOGY, PERSON, LOCATION,
REQUIREMENT, CLAUSE, SECTION, DOCUMENT, DELIVERABLE,
EVALUATION_FACTOR, SUBMISSION_INSTRUCTION, STATEMENT_OF_WORK,
ANNEX, PROGRAM, STRATEGIC_THEME, EQUIPMENT, REGULATION
```

### Current Corruption Patterns (from logs)

```
WARNING: invalid entity type in: ['entity', 'Past Performance Questionnaire', '#>|DOCUMENT', ...]
WARNING: invalid entity type in: ['entity', 'FAR 19.705-4', '#>|CLAUSE', ...]
WARNING: LLM output format error; found 5/4 fields on ENTITY `Security Assistance Program` @ `PROGRAM`
```

### Key Files to Edit

1. `src/server/initialization.py` - Lines 140-240 (entity extraction prompt)
2. `src/server/routes.py` - Lines 180-200 (add pre-validation sanitizer)
3. `src/utils/entity_sanitizer.py` - NEW FILE (sanitization logic)
4. `src/utils/prompt_loader.py` - NEW FILE (prompt loading utility)
5. `src/utils/__init__.py` - Add new exports
6. `prompts/entity_extraction/entity_extraction_prompt.md` - NEW FILE (extracted prompt)

---

## 🚀 Quick Start for Next Session

```powershell
# 1. Verify you're on the right branch
git branch --show-current
# Expected: 005-mineru-optimization

# 2. Verify baseline (entity cleanup deleted)
Test-Path "src\utils\entity_cleanup.py"
# Expected: False

# 3. Read Grok's self-diagnostic
Get-Content "docs\GROK_DIAGNOSTIC_FEEDBACK.md" | Select-Object -First 50

# 4. Start with Task 1: Ultra-Simplify Entity Type List
# Edit: src/server/initialization.py (lines ~140-200)
```

---

## 📚 Key Resources

### Documentation in This Branch

- `docs/GROK_DIAGNOSTIC_FEEDBACK.md` - Grok's 5 solution recommendations (355 lines)
- `docs/BRANCH_005_ENTITY_TYPE_FIX.md` - Entity fix investigation results
- `BRANCH_005_HANDOFF.md` - UCF experiment + prompt modularization plan

### Test Cases

- **Quick**: Navy MBOS (71 pages) - Baseline: 4,302 entities, 69 seconds
- **Comprehensive**: MCPP RFP (425 pages) - Baseline: 2,962 entities, 22 warnings

### Git History

- `main` @ `314cc72` - Branch 005 Entity Type Fix merged (313 lines removed)
- `005-mineru-optimization` @ `ae981b9` - Current branch with Grok diagnostic

---

## ⚠️ Critical Reminders

1. **Pre-Validation vs Post-Processing**: NEW sanitizer runs BEFORE validation (recovers entities), OLD cleanup ran AFTER (too late)

2. **Hotel WiFi**: Sporadic 403/timeout errors are network issues, NOT bugs - retry logic handles them

3. **Prompt Simplification**: Remove ALL special character references (`#`, `|`, `>`) from instructions - these trigger Grok's echoing behavior

4. **Test After Each Task**: Run quick Navy MBOS test after Tasks 1, 2, 3 to validate improvements

5. **Commit Atomically**: Commit each task separately with clear messages for easy rollback

---

## 🎯 Recommended First Action

**Start with Task 1 + Task 2 together** (75 minutes total):

- Task 1 fixes the prompt (prevents future corruption)
- Task 2 fixes the pipeline (recovers existing corruption)
- Combined impact: 22 warnings → <5 warnings (95% improvement)

Once those work, Task 3 (prompt modularization) is cleanup/refactoring for maintainability.

---

**Branch Status**: ✅ Ready for implementation  
**Time to Complete Tasks 1-3**: ~2.5 hours  
**Expected Outcome**: <5 warnings per RFP, cleaner architecture, -100 LOC

**Next Command**: `code src/server/initialization.py` (start Task 1)
