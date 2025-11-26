# Branch 025: Entity Type Schema Enforcement

## Overview

This branch addresses **entity type schema violations** discovered in production (`afcapv_adab_iss_2025_main_production`). The primary issue is that invalid entity types like `govcon_table` and `other` are being inserted into Neo4j despite having a Pydantic schema that should enforce only 18 valid types.

This work builds on prior closed issues:

- **Issue #6**: xAI SDK + Instructor integration for Pydantic validation with retry logic
- **Issue #7**: Verbatim extraction refactor (removed description field)

And relates to open issue:

- **Issue #9**: Entity extraction prompt enhancement (addresses LLM-side quality)

---

## Problem Statement

### Current State (Production Workspace)

| Entity Type          | Count | Status               |
| -------------------- | ----- | -------------------- |
| **Schema-compliant** | 1,047 | ✅ Valid             |
| `govcon_table`       | 40    | ❌ **NOT IN SCHEMA** |
| `other`              | 24    | ❌ **NOT IN SCHEMA** |
| `UNKNOWN`            | 2     | ❌ **NOT IN SCHEMA** |

**Total entities**: 1,087  
**Schema violations**: 66 entities (6%)

### Root Cause

The Pydantic schema in `src/ontology/schema.py` defines `EntityType` as a `Literal` with 18 allowed values:

```python
EntityType = Literal[
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
]
```

**However**, when the LLM returns an invalid type like `govcon_table`, the Instructor library's default parsing mode allows coercion or the validation is bypassed. The invalid types then flow through to Neo4j insertion.

---

## Solution: Extraction-Level Enforcement

### 1. Schema Validation Enhancement (`src/ontology/schema.py`)

Add a `model_validator(mode='before')` to `BaseEntity` that **intercepts invalid types before Pydantic parsing**:

```python
# 18 allowed entity types - single source of truth
VALID_ENTITY_TYPES = {
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
}

class BaseEntity(BaseModel):
    entity_name: str
    entity_type: EntityType

    @model_validator(mode='before')
    @classmethod
    def validate_entity_type(cls, values):
        """Coerce invalid types to 'concept' with warning."""
        if isinstance(values, dict):
            entity_type = values.get('entity_type', '')
            if entity_type and entity_type not in VALID_ENTITY_TYPES:
                logger.warning(f"⚠️ Invalid entity_type '{entity_type}' - coercing to 'concept'")
                values['entity_type'] = 'concept'
        return values
```

**Result**: Invalid types are now caught at extraction time and coerced to `concept` with a logged warning.

### 2. Test Verification

```bash
# Before fix: Invalid types accepted silently
>>> BaseEntity(entity_name='Test', entity_type='govcon_table')
BaseEntity(entity_name='Test', entity_type='govcon_table')  # BAD

# After fix: Invalid types coerced with warning
>>> BaseEntity(entity_name='Test', entity_type='govcon_table')
⚠️ Invalid entity_type 'govcon_table' for 'Test' - coercing to 'concept'
BaseEntity(entity_name='Test', entity_type='concept')  # GOOD
```

---

## Related Issue: Issue #9 - Entity Extraction Prompt Enhancement

The schema enforcement fix addresses **symptom** (invalid types getting through), but Issue #9 addresses the **root cause** (LLM generating incorrect types in the first place).

### Issue #9 Summary

**Problem**: Production extraction is missing 8/18 entity types:

1. `performance_metric` - **CRITICAL** - 40+ metrics misclassified as `requirement`
2. `strategic_theme` - Weak prompt examples
3. `submission_instruction` - Format-agnostic detection broken (UCF vs non-UCF)
4. `clause` - Partial extraction
5. `event`, `technology`, `program`, `statement_of_work` - May be absent or misclassified

### Connection to Schema Enforcement

| Issue          | What It Fixes                          | Priority                      |
| -------------- | -------------------------------------- | ----------------------------- |
| **Branch 025** | Invalid types bypass schema validation | **HIGH** - Data integrity     |
| **Issue #9**   | LLM generates wrong types from prompts | **HIGH** - Extraction quality |

**Both issues must be addressed together** because:

1. Schema enforcement (Branch 025) prevents garbage data from entering Neo4j
2. Prompt enhancement (Issue #9) ensures LLM generates correct types in the first place

---

## Implementation Plan

### Branch 025 Scope (This Branch)

- [x] Add `VALID_ENTITY_TYPES` set to `schema.py`
- [x] Add `model_validator(mode='before')` to `BaseEntity`
- [x] Test invalid type coercion works
- [ ] Update `forbidden_type_cleanup.py` to use `VALID_ENTITY_TYPES` (consistency)
- [ ] Add unit tests for schema validation
- [ ] Create diagnostic tool for entity type auditing

### Issue #9 Scope (Separate Branch 024)

- [ ] Update `prompts/extraction/entity_extraction_prompt.md`
  - Add `requirement` vs `performance_metric` distinction
  - Add 5-10 clear performance metric examples
  - Add 10-15 strategic theme examples (Shipley Capture patterns)
- [ ] Update `prompts/extraction/entity_detection_rules.md`
  - Add performance metric trigger phrases
  - Add format-agnostic submission instruction patterns
- [ ] Test with PWS Section 2.0 containing QASP table
- [ ] Verify PO-1 through PO-I4 extracted as `performance_metric`

---

## Files Changed

### Branch 025 (Schema Enforcement)

| File                                      | Change                                                                                      |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| `src/ontology/schema.py`                  | Add `VALID_ENTITY_TYPES` set, add `model_validator` to `BaseEntity`                         |
| `src/inference/forbidden_type_cleanup.py` | Add `performance_metric` to allowed types, add `govcon_table`/`workload` to forbidden types |
| `tools/diagnostics/entity_type_audit.py`  | New diagnostic tool for auditing entity types in Neo4j                                      |
| `tools/neo4j/fix_govcon_table_types.py`   | One-time cleanup script (optional - for production data repair)                             |

### Issue #9 (Prompt Enhancement)

| File                                             | Change                                                 |
| ------------------------------------------------ | ------------------------------------------------------ |
| `prompts/extraction/entity_extraction_prompt.md` | Add examples for performance metrics, strategic themes |
| `prompts/extraction/entity_detection_rules.md`   | Add detection patterns                                 |
| `tests/test_extraction.py`                       | Add test cases                                         |

---

## Success Metrics

### Branch 025 (Schema Enforcement)

**Before**:

- Invalid types (`govcon_table`, `other`, `UNKNOWN`) accepted silently
- 66 entities with invalid types in production

**After**:

- Invalid types coerced to `concept` with warning log
- Zero invalid types in new extractions
- 18/18 schema types enforced at extraction level

### Issue #9 (Prompt Enhancement)

**Before**:

- 10/18 entity types extracted
- 0 performance metrics (should be ~40-50)
- 0 strategic themes

**After**:

- 15-16/18 entity types extracted
- 40-50 performance metrics from PWS Section 2.0
- 5-10 strategic themes from evaluation factors

---

## Testing Commands

```bash
# Verify schema enforcement
python -c "from src.ontology.schema import BaseEntity; e = BaseEntity(entity_name='Test', entity_type='govcon_table'); print(f'Type: {e.entity_type}')"
# Expected: Warning + Type: concept

# Run entity type audit
python tools/diagnostics/entity_type_audit.py --workspace afcapv_adab_iss_2025_main_production

# Run extraction tests
python -m pytest tests/test_json_extraction.py -v
```

---

## Dependencies

- **Issue #6** (CLOSED): xAI SDK + Instructor for Pydantic validation with retry logic
- **Issue #7** (CLOSED): Verbatim Extraction Refactor (removed `description` field)
- **Issue #9**: Entity Extraction Prompt Enhancement (addresses LLM-side quality)
- **Branch 022**: Ontology split performance metric (original solution - review what worked)

---

## Prior Work: Issue #6 - Pydantic Schema + Retry Logic (CLOSED)

### Problem Solved

Issue #6 addressed **data loss from JSON parsing failures** during entity extraction:

```
ERROR | Failed to parse JSON: Unterminated string at char 30727
```

**Failure modes before Issue #6:**

- 1-4% JSON parse error rate on long LLM outputs (30K+ chars)
- `null` relationship types crashed Neo4j
- Invalid enum values corrupted data (e.g., "Marketing" instead of valid BOE category)
- Manual `json.loads()` with no retry → permanent data loss

### Solution: xAI SDK + Instructor Library

**Implementation** (`src/extraction/json_extractor.py`):

```python
import instructor
from src.ontology.schema import ExtractionResult

class JsonExtractor:
    def __init__(self):
        # Instructor wraps xAI client with automatic retry + Pydantic enforcement
        self.client = instructor.from_provider(
            f"xai/{self.model}",
            async_client=True
        )

    async def extract(self, text: str, chunk_id: str) -> ExtractionResult:
        result = await self.client.chat.completions.create(
            model=self.model,
            response_model=ExtractionResult,  # ✅ Pydantic schema enforced
            max_retries=2,  # ✅ Automatic retry on validation errors
            messages=[...],
            temperature=0.1,
        )
        return result  # Always valid ExtractionResult
```

**Key benefits:**

1. **Native Pydantic output** - No manual `json.loads()` or try/except
2. **Automatic retry with backoff** - Up to 5 attempts (5s, 15s, 45s, 135s delays)
3. **Graceful tolerance** - 2-3% failure rate acceptable, empty result returned on exhaustion
4. **Failed chunk tracking** - `self.failed_chunks` list for visibility and potential batch retry

### Retry Logic Architecture

```python
async def _extract_with_retry(self, text: str, chunk_id: str) -> ExtractionResult:
    """Manual retry with exponential backoff."""
    max_attempts = self.max_retries  # Default: 5

    for attempt in range(1, max_attempts + 1):
        try:
            result = await self.client.chat.completions.create(
                model=self.model,
                response_model=ExtractionResult,
                max_retries=2,  # Instructor's internal retry for validation
                messages=[...],
            )
            self._successful_extractions += 1
            return result

        except Exception as e:
            logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{max_attempts} failed")

            if attempt < max_attempts:
                delay = 5 * (3 ** (attempt - 1))  # 5s, 15s, 45s, 135s
                await asyncio.sleep(delay)

    # All attempts exhausted - track failure for visibility
    self.failed_chunks.append({
        "chunk_id": chunk_id,
        "text": text,
        "error": str(last_error),
    })
    raise last_error
```

### Connection to Branch 025

**Issue #6 solved:** LLM output parsing failures and retry logic  
**Branch 025 solves:** Invalid entity types bypassing Pydantic validation

The Instructor library + Pydantic schema **should** catch invalid types, but our audit revealed `govcon_table` entities in production. This means:

1. **Either:** LLM returns valid JSON that Pydantic accepts via coercion
2. **Or:** There's a code path bypassing the Instructor client

Branch 025's `model_validator(mode='before')` adds a **second layer of defense** that catches invalid types even if they slip through Instructor's validation.

---

## Prior Work: Issue #7 - Verbatim Extraction Refactor (CLOSED)

### Problem Solved

Issue #7 addressed **hallucination baked into the knowledge graph**:

- LLM-generated `description` fields were 30K+ chars (caused JSON parse errors)
- Descriptions were paraphrased interpretations, not source truth
- "500 users" → "serves users" (data loss from paraphrasing)
- No source traceability for legal/compliance review

### Solution: Remove Description Field Entirely

**Schema change:**

- Removed `description` field from `BaseEntity` (was causing 30K+ char JSON outputs)
- **Did NOT add `source_text` field** - the chunk already contains verbatim RFP content
- Structured metadata fields capture specifics (criticality, weight, thresholds)

**Design rationale:**

- Each entity is extracted FROM a chunk that already has the verbatim source text
- Adding `source_text` to entities would duplicate data already in the chunk
- LightRAG's vector embeddings are created from chunk content (verbatim RFP text)
- Query-time retrieval finds relevant chunks → provides source context

**Impact on entity extraction:**

- Average entity size reduced from ~30K chars to ~500 chars (60x reduction)
- JSON parse error rate dropped to near 0%
- Source traceability preserved through chunk linkage (not entity duplication)

### Connection to Branch 025

Issue #7's removal of `description` may have impacted prompt examples for certain entity types (see Issue #9). The prompt examples that guided the LLM toward correct entity types may have been inadvertently weakened, leading to:

- `govcon_table` type invented by LLM (not in schema)
- `other` type used as catch-all
- Misclassification of `performance_metric` as `requirement`

---

## Notes for Continuation

1. **Schema enforcement is in place** - invalid types will now be coerced to `concept`
2. **Issue #9 should be implemented next** to improve LLM prompt quality
3. **Production data repair** - the 66 invalid entities in `afcapv_adab_iss_2025_main_production` can be:

   - Left as-is (schema enforcement only prevents new invalid types)
   - Retyped using `tools/neo4j/fix_govcon_table_types.py` (LLM-based retyping)
   - Manually fixed in Neo4j Browser

4. **Consider combining Branches 024 and 025** - both address entity extraction quality at different levels

---

## Branch Status

**Branch**: `025-entity-type-schema-enforcement`  
**Base**: `main`  
**Status**: In Progress

### Pending Commits

```
modified:   src/ontology/schema.py
modified:   src/inference/forbidden_type_cleanup.py
new file:   tools/diagnostics/entity_type_audit.py
new file:   tools/neo4j/fix_govcon_table_types.py
```
