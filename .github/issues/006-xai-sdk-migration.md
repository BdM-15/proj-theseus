# xAI SDK Migration + Pydantic Schema Validation

## Problem

**Current State**: Using AsyncOpenAI with xAI endpoint + manual JSON parsing:

```python
# Current approach (OpenAI-compatible API)
from openai import AsyncOpenAI

client = AsyncOpenAI(
    api_key=os.getenv("LLM_BINDING_API_KEY"),
    base_url="https://api.x.ai/v1",
    timeout=120.0
)

response = await client.chat.completions.create(
    model="grok-4-fast-reasoning",
    messages=[...],
)

# Manual JSON parsing - no validation
result = json.loads(response.choices[0].message.content)
```

**Issues:**
1. **No schema validation** for LLM responses (discovered in Issue #6)
2. **Null relationship types** causing Neo4j crashes
3. **100% rejection rates** from malformed responses (Algorithm 5: 49/49 filtered)
4. **Missing required fields** (Algorithm 8: no source_id/target_id)
5. **Invalid enum values** (Workload enrichment: "Marketing" not in BOECategory)
6. **Using reasoning model for structured extraction** (overkill - slower, more expensive)

---

## Proposed Solution

**Migrate to xAI SDK + grok-4-1-fast-non-reasoning for all entity/relationship extraction:**

```python
# New approach (xAI native SDK)
from xai_sdk import Client
from xai_sdk.chat import system, user

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(model="grok-4-1-fast-non-reasoning")

chat.append(system("You are analyzing RFP entities..."))
chat.append(user(prompt))

# ✅ Returns validated Pydantic object OR raises ValidationError
response, result = chat.parse(ExtractionResult)
assert isinstance(result, ExtractionResult)

# Type-safe access, guaranteed schema compliance
for entity in result.entities:
    print(entity.entity_type)  # Never null/empty
```

---

## Why grok-4-1-fast-non-reasoning?

**Released:** November 17, 2025  
**Context:** 2 million tokens (vs 131K on grok-beta)  
**Optimized for:** Customer support, research, structured extraction

### Non-Reasoning is BETTER for Entity Extraction

| Feature | Reasoning Models | Non-Reasoning Models |
|---------|------------------|---------------------|
| **Use Case** | Open-ended problem solving | Structured output following detailed prompts |
| **Speed** | Slower (reasoning overhead) | **Faster (direct response)** |
| **Cost** | Higher (reasoning tokens) | **Lower** |
| **Schema Compliance** | Sometimes overthinks | **Better with detailed ontology prompts** |
| **Our Prompts** | 101K char extraction + 44K detection rules | **Perfect fit - strong instruction following** |

**Current results prove this:**
- grok-4-fast-reasoning extracted **126 entities** in 10m 51s from dense workload chunk
- Same chunk with grok-4-1-fast-non-reasoning: **~2-3 minutes** (estimated 4x faster)
- Quality maintained by detailed ontology prompts (17 entity types, 500+ line rules)

---

## Migration Benefits

### 1. Native Pydantic Validation
```python
class ExtractionResult(BaseModel):
    entities: List[Entity] = Field(..., min_items=0)
    relationships: List[Relationship] = Field(..., min_items=0)

class InferredRelationship(BaseModel):
    source_id: str = Field(..., min_length=1)  # Prevents null
    target_id: str = Field(..., min_length=1)
    relationship_type: str = Field(..., min_length=1)  # Algorithm 6 fix
    reasoning: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)

class BOECategory(str, Enum):
    LABOR = "Labor"
    MATERIALS = "Materials"
    ODCS = "ODCs"
    QA = "QA"
    LOGISTICS = "Logistics"
    # "Marketing" rejected at parse time ✅
```

### 2. Better Error Messages
```python
# Before (manual parsing)
# ❌ "Cannot merge relationship because of null property value for 'type'"

# After (xAI SDK)
# ✅ "ValidationError: Field required: relationship_type at relationships[23]"
# ✅ "ValidationError: Input should be 'Labor', 'Materials', ... (not 'Marketing')"
```

### 3. Performance Improvements
- **4x faster inference** (non-reasoning model)
- **2M token context** (future-proof for massive RFPs)
- **Native structured outputs** (LLM enforces schema during generation)
- **gRPC-based** (lower latency than REST)

### 4. Better Observability
- **OpenTelemetry tracing** built-in (integrates with Langfuse)
- **Token usage tracking** per request
- **Model metadata** (costs, limits) accessible via SDK

---

## Implementation Plan

### Phase 1: xAI SDK Installation
```bash
# In activated .venv
uv pip install xai-sdk
```

**Files to modify:**
- `pyproject.toml` - Add `xai-sdk` dependency
- `.env` - Change `EXTRACTION_LLM_NAME=grok-4-1-fast-non-reasoning`

### Phase 2: Entity Extraction Migration

**File:** `src/extraction/json_extractor.py`

**Before:**
```python
from openai import AsyncOpenAI

class JsonExtractor:
    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0
        )
    
    async def extract_from_text(self, text: str, ...):
        response = await self.client.chat.completions.create(...)
        result = json.loads(response.choices[0].message.content)
        return ExtractionResult(**result)  # Manual Pydantic conversion
```

**After:**
```python
from xai_sdk import Client
from xai_sdk.chat import system, user

class JsonExtractor:
    def __init__(self):
        self.client = Client(api_key=self.api_key)
        self.model = "grok-4-1-fast-non-reasoning"
    
    async def extract_from_text(self, text: str, ...):
        chat = self.client.chat.create(model=self.model)
        chat.append(system(self.system_prompt))
        chat.append(user(f"Extract entities from:\n\n{text}"))
        
        # ✅ Native Pydantic validation, schema enforcement
        response, result = chat.parse(ExtractionResult)
        return result  # Already validated Pydantic object
```

### Phase 3: Relationship Inference Migration

**File:** `src/inference/semantic_post_processor.py`

**Add Pydantic schemas:**
```python
class InferredRelationship(BaseModel):
    source_id: str = Field(..., min_length=1)
    target_id: str = Field(..., min_length=1)
    relationship_type: str = Field(..., min_length=1)
    reasoning: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)

class InferenceResult(BaseModel):
    relationships: List[InferredRelationship]
```

**Update 8 algorithms:**
```python
# Algorithm 6 (Concept Linking) - was returning null relationship_type
async def infer_concept_relationships(...):
    chat = client.chat.create(model="grok-4-1-fast-non-reasoning")
    chat.append(system("Infer semantic relationships..."))
    chat.append(user(entity_context))
    
    response, result = chat.parse(InferenceResult)
    # ✅ Guaranteed non-null relationship_type or ValidationError raised
    return [rel.model_dump() for rel in result.relationships]
```

### Phase 4: Workload Enrichment Migration

**File:** `src/inference/workload_enrichment.py`

```python
class BOECategory(str, Enum):
    LABOR = "Labor"
    MATERIALS = "Materials"
    ODCS = "ODCs"
    QA = "QA"
    LOGISTICS = "Logistics"
    LIFECYCLE = "Lifecycle"
    COMPLIANCE = "Compliance"

class WorkloadEnrichment(BaseModel):
    entity_id: str = Field(..., min_length=1)
    boe_categories: List[BOECategory] = Field(..., min_items=1)
    workload_estimate: Optional[str] = None
    reasoning: str

class WorkloadEnrichmentResult(BaseModel):
    enrichments: List[WorkloadEnrichment]

# Migration
chat.parse(WorkloadEnrichmentResult)
# ✅ "Marketing" rejected - must use valid BOECategory enum
```

### Phase 5: Testing

**Test cases:**
1. **Entity extraction** - Verify schema compliance on 70-page PWS
2. **Algorithm 6** - Confirm null relationship_type caught at parse time
3. **Algorithm 5** - Verify relationships not filtered (49/49 → 0/49 rejected)
4. **Algorithm 8** - Confirm missing IDs raise ValidationError
5. **Workload enrichment** - Verify invalid "Marketing" rejected
6. **Performance** - Measure 4x speedup on dense chunks
7. **Batch processing** - Run full 5-document RFP end-to-end

---

## Expected Outcomes

### Before (AsyncOpenAI + Manual Parsing)
```
⏱️  PWS chunk 3: 10m 51s (126 entities) - grok-4-fast-reasoning
❌ Algorithm 6: null relationship_type → Neo4j crash
❌ Algorithm 5: 49/49 relationships filtered (100% rejection)
❌ Workload enrichment: "Marketing" logged as warning, data corrupted
```

### After (xAI SDK + grok-4-1-fast-non-reasoning)
```
⏱️  PWS chunk 3: ~2-3 minutes (126 entities) - 4x faster
✅ Algorithm 6: ValidationError raised, logged, processing continues
✅ Algorithm 5: Malformed responses prevented by schema enforcement
✅ Workload enrichment: ValidationError forces LLM to use valid enums
```

**Time Savings:**
- Entity extraction: 10m 51s → ~2-3m per dense chunk (**~8 minutes saved**)
- Relationship inference: Faster + fewer retries (**~5 minutes saved**)
- **Total: ~13 minutes per 5-document RFP**

**Quality Improvements:**
- Zero null relationship types
- Zero invalid enum values
- Type-safe throughout codebase
- Better error diagnostics

---

## Files to Modify

1. **`pyproject.toml`** - Add `xai-sdk` dependency
2. **`.env`** - Update `EXTRACTION_LLM_NAME=grok-4-1-fast-non-reasoning`
3. **`src/extraction/json_extractor.py`** - Migrate to xAI SDK
4. **`src/inference/semantic_post_processor.py`** - Add Pydantic schemas, migrate 8 algorithms
5. **`src/inference/workload_enrichment.py`** - Add BOECategory enum, migrate
6. **`src/ontology/schema.py`** - Add InferredRelationship, WorkloadEnrichment models
7. **Prompts** - Update JSON examples if field names change

---

## xAI SDK Resources

- **Documentation:** https://docs.x.ai/docs/guides/structured-outputs
- **GitHub:** https://github.com/xai-org/xai-sdk-python
- **Model Console:** https://console.x.ai/team/4b9bd955-ddaa-434a-a8b7-19176f0a1399/models/grok-4-1-fast-non-reasoning
- **Pricing:** Grok 4.1 Fast - check xAI console for latest rates

---

## Priority

**HIGH** - Addresses multiple critical issues:
- Data quality (null values, invalid enums)
- Performance (4x faster extraction)
- Developer experience (type safety, better errors)
- Future scalability (2M token context)

---

## Labels

- `enhancement` - SDK migration + performance improvement
- `tech-debt` - Should use native SDK, not OpenAI compatibility layer
- `phase-6` - Semantic post-processing
- `extraction` - Entity extraction pipeline
- `xai-sdk` - Migration to xAI native SDK
