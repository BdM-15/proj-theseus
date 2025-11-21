# Grok 4-1 Migration Plan: Reproducing the Perfect Run with Native Pydantic

**Date**: November 21, 2025  
**Branch**: 022-ontology-split-performance-metric  
**Goal**: Lock in the "holy grail" extraction quality (339 entities, 154 relationships) while upgrading to Grok 4-1's native Pydantic support

---

## 🎯 Evidence of Success (The Holy Grail)

### Perfect Run Performance (November 20, 2025 - 12:15-12:40)

**Extraction Quality**:

- **339 entities** extracted from 4 chunks
- **154 relationships** with pristine workload driver capture
- Near-perfect retrieval of frequencies, quantities, hours, coverage metrics for BOE/FTE estimation

**Schema Adherence**:

- Strict Pydantic validation blocking malformed relationships (3 total rejected across all chunks)
- Zero data loss from valid extractions
- Clean execution end-to-end

**Technical Details**:

- **Model**: `grok-4-fast-reasoning` (hardcoded in multiple locations)
- **Chunking**: 8192 tokens, 1024 overlap → 4 chunks from 421 content blocks (125,954 chars)
- **Extraction Prompts**: 284,942 char system prompt + entity detection rules
- **Validation**: Pydantic schema catching malformed relationships without data loss:
  - Chunk 3: Rejected 2/40 relationships (missing source_entity, malformed dict)
  - Chunk 4: Rejected 1/49 relationships (missing source_entity)
- **Post-Processing**: Workload enrichment detecting invalid BOE categories proving semantic validation works

---

## 🔬 Grok 4-1 Fast Reasoning Capabilities

### Research Findings (xAI Documentation + Web Search)

**Native Pydantic Structured Outputs**:

- ✅ Supported on ALL models after `grok-2-1212` and `grok-2-vision-1212`
- ✅ `grok-4-1-fast-reasoning` fully supports native Pydantic via `response_format` parameter
- ✅ **GUARANTEED schema compliance** - xAI enforces the Pydantic model natively
- ✅ No JSON parsing needed - model returns typed Python objects directly

**SDK Integration** (xai_sdk):

```python
from xai_sdk import Client
from xai_sdk.chat import system, user

client = Client(api_key=os.getenv("XAI_API_KEY"))
chat = client.chat.create(model="grok-4-1-fast-reasoning")
chat.append(system("Your instructions..."))
chat.append(user("Extract entities from this text..."))

# Native Pydantic parsing
response, result = chat.parse(ExtractionResult)
assert isinstance(result, ExtractionResult)  # Type-safe!
```

**Key Advantages**:

1. **Zero JSON EOF Errors**: No manual parsing means no truncation issues
2. **Type Safety**: Direct Python objects with full Pydantic validation
3. **Cleaner Code**: Eliminate JSON parsing overhead and error handling
4. **Better Instruction Following**: Model optimized for structured output
5. **Cost Efficiency**: Same pricing as grok-4-fast ($0.20/1M input tokens)

**Supported Schema Features**:

- ✅ `string`, `number`, `integer`, `float`
- ✅ `object`, `array`, `boolean`, `enum`
- ✅ `anyOf` (union types - critical for our `BaseEntity | Requirement | EvaluationFactor` unions)
- ❌ `allOf` not supported (we don't use this)
- ⚠️ `minLength`/`maxLength` not supported (we don't use these)
- ⚠️ `minItems`/`maxItems` not supported (we don't use these)

---

## 📊 Current Architecture Analysis

### Model Configuration Status

**✅ .env File (Correct)**:

```bash
LLM_MODEL=grok-4-1-fast-reasoning
EXTRACTION_LLM_NAME=grok-4-1-fast-reasoning
REASONING_LLM_NAME=grok-4-1-fast-reasoning
```

**❌ Hardcoded Locations (Bypassing .env)**:

1. **src/server/initialization.py** (Line 120):

   ```python
   async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
       return await openai_complete_if_cache(
           "grok-4-fast-reasoning",  # ❌ HARDCODED
   ```

2. **src/server/initialization.py** (Lines 133, 149):

   ```python
   "grok-4-fast-reasoning", ""  # ❌ HARDCODED (vision function)
   ```

3. **src/server/config.py** (Line 64):

   ```python
   global_args.llm_model_name = "grok-4-fast-reasoning"  # ❌ HARDCODED
   ```

4. **src/inference/workload_enrichment.py** (Line 52):

   ```python
   model: str = "grok-4-fast-reasoning",  # ❌ HARDCODED
   ```

5. **src/inference/semantic_post_processor.py** (Lines 36, 918):
   ```python
   model: str = "grok-4-fast-reasoning"  # ❌ HARDCODED
   ```

### Current Extraction Flow

**src/extraction/json_extractor.py**:

```python
# Current approach (manual JSON parsing)
response = await self.client.chat.completions.create(
    model=self.model,
    messages=[...],
    response_format={"type": "json_object"},  # ❌ Old way
    temperature=0.1,
    max_tokens=32000
)

content = response.choices[0].message.content
data = json.loads(content)  # ❌ Manual parsing with error handling
result = ExtractionResult(**data)  # ❌ Manual validation
```

**Pydantic Schema (src/ontology/schema.py)**:

```python
class ExtractionResult(BaseModel):
    """The root object expected from the LLM."""
    entities: List[
        Requirement | EvaluationFactor | SubmissionInstruction |
        StrategicTheme | Clause | PerformanceMetric | BaseEntity
    ] = Field(..., description="List of all extracted entities.")
    relationships: List[Relationship] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_relationships(self):
        """Ghost node prevention - drops invalid relationships"""
        # Already perfect! Just needs native parsing instead of JSON
```

---

## 🎯 Migration Strategy

### Phase 1: Lock Down Perfect Run Configuration (IMMEDIATE)

**Goal**: Document and preserve the exact configuration that produced 339/154 results

1. **Capture Perfect Run State**:

   - ✅ Chunking: 8192 tokens, 1024 overlap (already in .env)
   - ✅ Prompts: 284,942 char system prompt (already loaded)
   - ✅ Pydantic Schema: `ExtractionResult` with relationship validation (already working)
   - ⚠️ Model: `grok-4-fast-reasoning` (need to make .env authoritative)

2. **Centralize Model Configuration** (HIGH PRIORITY):

   ```python
   # Replace ALL hardcoded "grok-4-fast-reasoning" with:
   model = os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning")
   extraction_model = os.getenv("EXTRACTION_LLM_NAME", model)
   reasoning_model = os.getenv("REASONING_LLM_NAME", model)
   ```

3. **Create Baseline Test**:
   ```python
   # tests/test_perfect_run_baseline.py
   # Reproduce 339/154 results with current configuration
   # Assert chunk count = 4, entity count >= 330, relationship count >= 150
   ```

### Phase 2: Migrate to Native Pydantic (EXPERIMENTAL)

**Goal**: Upgrade to `grok-4-1-fast-reasoning` with xai_sdk for native Pydantic parsing

**Prerequisites**:

- Install xai_sdk: `uv pip install xai-sdk`
- Test in isolated branch (do NOT merge to main until validated)

**Code Changes**:

1. **Update json_extractor.py**:

   ```python
   # OLD: Manual JSON parsing
   response = await self.client.chat.completions.create(
       model=self.model,
       messages=[...],
       response_format={"type": "json_object"}
   )
   content = response.choices[0].message.content
   data = json.loads(content)
   result = ExtractionResult(**data)

   # NEW: Native Pydantic with xai_sdk
   from xai_sdk import Client
   from xai_sdk.chat import system, user

   client = Client(api_key=self.api_key)
   chat = client.chat.create(model=self.model)
   chat.append(system(self.system_prompt))
   chat.append(user(text))

   # Type-safe parsing - no JSON involved!
   response, result = chat.parse(ExtractionResult)
   assert isinstance(result, ExtractionResult)
   ```

2. **Update initialization.py**:

   ```python
   # Replace hardcoded model names with environment variables
   async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
       model = os.getenv("EXTRACTION_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"))
       return await openai_complete_if_cache(
           model,  # ✅ Dynamic model selection
           prompt,
           system_prompt=system_prompt,
           history_messages=history_messages,
           api_key=xai_api_key,
           base_url=xai_base_url,
           **kwargs,
       )
   ```

3. **Validation Testing**:
   ```python
   # Compare old vs new extraction on same chunks
   # Assert entity count within 5% (330-345 range)
   # Assert relationship count within 5% (147-162 range)
   # Assert workload driver completeness (all labor_drivers captured)
   ```

### Phase 3: Prompt Compression (IMMEDIATE PRIORITY)

**Goal**: Remove markdown formatting waste without losing ANY domain intelligence

**Current State - The Token Economics Problem**:

```
System Prompt:  284,942 chars (~71,236 tokens)
Chunk Size:       8,192 tokens
Ratio:           System prompt is 8.7x LARGER than each chunk!

Perfect Run (4 chunks):
- System tokens per extraction: 71,236 tokens
- Total tokens (4 chunks):     355,180 tokens
- Cost per document:           $0.057 input only
```

**The Critical Discovery**:

- ✅ **Markdown formatting costs ~103,000 chars (36% of prompt) with ZERO intelligence value**
- ✅ **LLMs don't need headers, bold, tables, code fences, bullets, checkmarks**
- ✅ **Same semantic content can be delivered in ultra-dense plain text**

**Conservative Compression (Phase 3A) - 36% Reduction**:

````
Target: 182K chars (~45,500 tokens)
Savings: 25,751 tokens per chunk
Cost reduction: $0.021 per document
Method: Remove ONLY formatting, preserve 100% intelligence

Changes:
- Strip markdown headers (### → plain text with :)
- Remove bold/italic (**text** → text)
- Eliminate code fences (```json → direct JSON)
- Convert tables to pipe-separated inline format
- Remove horizontal rules, checkmarks, excess whitespace
- Convert bullet/numbered lists to comma-separated inline
````

**Aggressive Compression (Phase 3B) - 48% Reduction**:

```
Target: 147K chars (~36,750 tokens)
Savings: 34,501 tokens per chunk
Cost reduction: $0.028 per document
Method: Ultra-dense format (only if Phase 3A validates)

Additional changes:
- Inline examples (remove multi-line formatting)
- Compact Pydantic schemas to inline notation
- Ultra-dense signal lists
```

**What Gets PRESERVED (100% Intelligence)**:

1. ✅ Entity types: All 18 specialized government contracting types (requirement, evaluation_factor, submission_instruction, deliverable, clause, section, document, statement_of_work, performance_metric, strategic_theme, organization, concept, event, technology, person, location, program, equipment)
2. ✅ Normalization rules: Section formatting, clause citations, CDRL format
3. ✅ UCF section mapping: A-M sections with entity types and signals
4. ✅ Detection signals: Phrase patterns for semantic-first extraction
5. ✅ Specialized metadata: labor_drivers, subfactors, threshold, modal_verb
6. ✅ Examples: All 5+ real RFP examples (minimal formatting only)
7. ✅ Decision trees: Edge case handling rules
8. ✅ Relationship types: EVALUATED_BY, GUIDES, CHILD_OF, etc.

**Validation Protocol** (Must Pass Before Deployment):

```python
# A/B test compressed vs original against perfect run
assert entity_count in range(322, 356)      # 339 ±5%
assert relationship_count in range(147, 162) # 154 ±5%
assert len(labor_drivers) >= baseline * 0.95 # Workload completeness
assert rejection_rate <= 5/543              # Schema compliance (3 ±2)
```

**Safety Net**:

- ✅ Feature flag toggle between compressed/original
- ✅ Rollback immediately if quality degrades
- ✅ Full A/B validation before merging to main

**Why This is Safe**:

- Perfect run proves the INTELLIGENCE works (339/154 with validation)
- Markdown is cosmetic packaging for humans, not LLMs
- Zero semantic changes to rules, examples, or entity types
- Validation gates prevent deployment if extraction quality drops

**See**: `docs/PROMPT_COMPRESSION_ANALYSIS.md` for detailed breakdown

---

## 🚨 Critical Success Factors

### DO NOT Change These (Proven Components)

1. **✅ Chunking Strategy**: 8192 tokens, 1024 overlap

   - Ensures comprehensive entity coverage (5-6 passes over 71-page doc)
   - Prevents attention decay from 50K chunk catastrophe

2. **✅ Pydantic Schema**: `ExtractionResult` with relationship validation

   - Ghost node prevention working perfectly (3 invalid relationships dropped)
   - No data loss from valid extractions

3. **✅ Workload Driver Fields**: `labor_drivers` and `material_needs` in Requirement model

   - Critical for BOE/FTE estimation
   - Proven to capture frequencies, quantities, hours, coverage metrics

4. **✅ Post-Processing Pipeline**: Workload enrichment + semantic validation
   - Catches invalid BOE categories (Training, Security, etc.)
   - Preserves extraction quality through validation layers

### Change Carefully (Configuration Hygiene)

1. **⚠️ Model Name Centralization**: Replace hardcoded values with .env references

   - Test each change individually
   - Validate against perfect run baseline

2. **⚠️ xai_sdk Migration**: Native Pydantic parsing

   - A/B test against current JSON parsing approach
   - Measure token usage, latency, and quality

3. **⚠️ Prompt Streamlining**: Only after validating Grok 4-1 performance
   - Incremental reductions with quality gates
   - Rollback immediately if metrics degrade

---

## 📈 Success Metrics

### Baseline (Perfect Run - Must Maintain or Improve)

- **Entity Count**: 330-345 (target: 339)
- **Relationship Count**: 147-162 (target: 154)
- **Chunk Count**: 4 (from 421 content blocks)
- **Workload Driver Completeness**: 100% of frequencies, quantities, hours, coverage captured
- **Schema Compliance**: <1% rejection rate (3/543 total entities+relationships)
- **Zero Failures**: No JSON EOF errors, no token limit issues

### Migration Validation Gates

**Phase 1 (Model Centralization)**:

- ✅ All hardcoded model names replaced with .env references
- ✅ Perfect run reproducible with .env configuration
- ✅ No performance regression (339/154 results maintained)

**Phase 2 (Native Pydantic)**:

- ✅ xai_sdk integration working with ExtractionResult schema
- ✅ Entity count within 5% of baseline (330-345)
- ✅ Relationship count within 5% of baseline (147-162)
- ✅ Zero JSON parsing errors
- ✅ Workload driver completeness maintained

**Phase 3 (Prompt Optimization)**:

- ✅ System prompt reduced by 10-30% without quality loss
- ✅ All baseline metrics maintained or improved
- ✅ Faster extraction (fewer tokens = lower latency)

---

## 🛠️ Implementation Checklist

### Immediate Actions (Phase 1 - Model Centralization)

- [ ] Create `tests/test_perfect_run_baseline.py` with 339/154 assertions
- [ ] Run baseline test against current configuration (validate reproducibility)
- [ ] Centralize model configuration in `initialization.py` (use .env)
- [ ] Centralize model configuration in `config.py` (use .env)
- [ ] Centralize model configuration in `workload_enrichment.py` (use .env)
- [ ] Centralize model configuration in `semantic_post_processor.py` (use .env)
- [ ] Validate no regression after centralization (re-run baseline test)
- [ ] Document exact configuration that produces perfect run (commit to repo)

### Experimental Actions (Phase 2 - Native Pydantic)

- [ ] Install xai_sdk: `uv pip install xai-sdk`
- [ ] Create feature branch: `023-grok-4-1-native-pydantic`
- [ ] Update `json_extractor.py` to use xai_sdk parsing
- [ ] Run A/B test: current JSON parsing vs xai_sdk parsing
- [ ] Validate entity count within 5% (330-345)
- [ ] Validate relationship count within 5% (147-162)
- [ ] Validate workload driver completeness (qualitative review)
- [ ] Measure token usage and latency improvements
- [ ] Merge to main ONLY if all validation gates pass

### High-Priority Actions (Phase 3 - Prompt Compression)

**Phase 3A: Conservative Compression (36% reduction)**

- [ ] Create compressed versions of 3 prompt files (strip markdown only)
- [ ] Add feature flag: `USE_COMPRESSED_PROMPTS` in .env
- [ ] Update `json_extractor.py` to support both prompts
- [ ] Run A/B test: compressed vs original on perfect run document
- [ ] Validate entity count 339 ±5% (322-356 range)
- [ ] Validate relationship count 154 ±5% (147-162 range)
- [ ] Validate workload driver completeness (≥95% of baseline)
- [ ] Validate schema compliance (3 ±2 rejections)
- [ ] If successful: Set compressed as default, document savings
- [ ] If failed: Rollback, analyze what intelligence was lost

**Phase 3B: Aggressive Compression (48% reduction)**

- [ ] ONLY proceed if Phase 3A passes all validation
- [ ] Create ultra-dense prompt format (inline examples, compact schemas)
- [ ] Run same A/B validation tests
- [ ] Measure incremental quality/cost tradeoff vs Phase 3A
- [ ] Deploy only if no degradation from Phase 3A

### Future Actions (Phase 4 - Example Optimization)

- [ ] Analyze which examples provide most value (ONLY after Phase 3 validated)
- [ ] Test removing lowest-value examples one-by-one
- [ ] Identify minimum viable example set for holy grail quality
- [ ] Update documentation with optimized prompt guidelines

---

## 🎓 Key Insights

### Why the Perfect Run Worked

1. **Multiple Focused Passes**: 8K chunking = 4 passes over doc = comprehensive entity coverage
2. **Strict Schema Validation**: Pydantic catching malformed relationships without data loss
3. **Government Contracting Ontology**: Specialized entity types (requirement, evaluation_factor, etc.) align with RFP structure
4. **Workload-First Design**: `labor_drivers` field captured at extraction time (not post-processing)
5. **LLM-Powered Inference**: Relationship validation detecting missing source_entity fields

### The System Prompt Paradox

**Shocking Discovery**: The system prompt (71,236 tokens) is **8.7x LARGER than each chunk** (8,192 tokens)!

```
Perfect Run Token Economics:
- System prompt sent 4 times (once per chunk): 284,944 tokens
- Actual content chunks (4 × 8,192):          32,768 tokens
- Ratio: 87% of tokens are THE SAME PROMPT repeated 4 times!
```

**Why This Matters**:

- Every chunk extraction re-sends the ENTIRE 285K system prompt
- With 4 chunks, we send 1.14 MILLION characters (285K × 4)
- **36% of those characters are markdown formatting** (headers, bold, tables, code fences)
- Compression = immediate 36-48% cost reduction with ZERO intelligence loss

**Why Compression is Safe**:

- LLMs parse plain text semantics, not markdown formatting
- The perfect run proves the INTELLIGENCE works (339/154 validated)
- Markdown is cosmetic packaging for humans, not for models
- Conservative approach: Remove ONLY formatting, preserve 100% domain expertise

### What Could Break Reproducibility

1. **Model Drift**: Hardcoded `grok-4-fast-reasoning` bypassing .env updates
2. **Chunk Size Changes**: Switching from 8K to 50K would cause attention decay catastrophe
3. **Prompt Modifications**: Removing entity detection rules without validation
4. **Schema Changes**: Altering `ExtractionResult` structure without testing
5. **MinerU Version Drift**: Different parsing quality from version changes

### Grok 4-1 Advantages for This Use Case

1. **Native Pydantic**: Eliminates JSON parsing overhead and error handling
2. **Better Instruction Following**: May allow prompt streamlining (test carefully!)
3. **Type Safety**: Direct Python objects reduce validation complexity
4. **Cost Parity**: Same pricing as grok-4-fast ($0.20/1M input tokens)
5. **Agentic Optimization**: Model designed for structured output tasks like entity extraction

### Prompt Compression Economics

**Conservative Compression (36% reduction)**:

```
Before:  284,942 chars × 4 chunks = 1,139,768 chars per doc
After:   181,942 chars × 4 chunks =   727,768 chars per doc
Savings:                             412,000 chars (103,000 tokens)
Cost impact: $0.057 → $0.036 per document (36% reduction)
```

**Aggressive Compression (48% reduction)**:

```
Before:  284,942 chars × 4 chunks = 1,139,768 chars per doc
After:   146,942 chars × 4 chunks =   587,768 chars per doc
Savings:                             552,000 chars (138,000 tokens)
Cost impact: $0.057 → $0.029 per document (49% reduction)
```

**At Scale** (100 RFPs/month):

- Conservative: Save $2.10/month per workspace
- Aggressive: Save $2.80/month per workspace
- With 10 concurrent workspaces: $21-28/month savings

**The Real Win**: More available context window for larger chunks or longer documents without hitting limits.

---

## 🔗 References

- **xAI Structured Outputs**: https://docs.x.ai/docs/guides/structured-outputs
- **Grok 4-1 Fast Reasoning**: https://console.x.ai/models/grok-4-1-fast-reasoning
- **Perfect Run Evidence**: `logs/perfectrun_workload_prompt_response.md`
- **Perfect Run Log**: `logs/server.log.perfect_339_run_backup_20251120_181302`
- **Pydantic Schema**: `src/ontology/schema.py`
- **Current Extraction Code**: `src/extraction/json_extractor.py`

---

**Next Steps**: Execute Phase 1 checklist to lock down perfect run configuration, then proceed to Phase 2 experimental validation in isolated branch.
