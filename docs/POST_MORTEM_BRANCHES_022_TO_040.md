# Post-Mortem Analysis: Branches 022-040 RAG Pipeline Evolution

**Date**: December 13, 2025  
**Analysis Type**: Non-destructive historical review  
**Baseline Reference**: Branch 022 ("Perfect Run" - November 21, 2025)  
**Purpose**: Preserve lessons learned before potential reset to clean baseline

---

## Executive Summary

This analysis documents the evolution of the GovCon Capture Vibe RAG pipeline from the "Perfect Run" baseline (Branch 022, November 21, 2025) through approximately 20 subsequent experimental branches ending at Branch 040. The system experienced **progressive quality degradation** despite numerous "improvements."

### The Core Paradox

> The system paradoxically got worse as "advanced features" were added. Adding granular entity types, strict validation, complex post-processing algorithms, and parallel optimization fragmented knowledge and reduced retrieval precision.

### Key Metrics Journey

| Metric | Branch 022 (Perfect) | Branch 030+ (Degraded) | Issue |
|--------|---------------------|----------------------|-------|
| Workload Query Quality | 98%+ | ~70-80% (generic) | Lost granular details |
| Entity Extraction | 368 entities | 1,100+ entities | Over-extraction noise |
| Inferred Relationships | 154 | 3,000+ | Ghost relationships |
| Response Style | Comprehensive narrative | Structured but shallow | Lost analytical depth |

### Root Cause Summary

1. **Over-engineering**: 18 entity types + 8 post-processing algorithms + strict Pydantic validation
2. **Architectural duplication**: Custom code duplicating RAG-Anything/LightRAG internals
3. **Token starvation**: Query overrides capped KG context tokens, dropping granular details
4. **Prompt compression regression**: 23% token reduction traded quality for cost savings

---

## Timeline of Branches

### Branch 022: "Perfect Run" Baseline ✅ GOLDEN STANDARD

**Date**: November 21, 2025  
**Commit**: `cb204fd`  
**Status**: Production baseline - DO NOT MODIFY

**Key Configuration (Locked)**:
```bash
LLM_MODEL=grok-4-fast-reasoning
CHUNK_SIZE=8192
CHUNK_OVERLAP_SIZE=1200
ENTITY_EXTRACT_MAX_GLEANING=0
GRAPH_STORAGE=Neo4JStorage
```

**Critical Code** (`routes.py`):
```python
# TEXT-ONLY filter - THE critical fix
if item.get('type') == 'text':  # Only 421 text blocks, not 474
```

**Results**:
- 368 entities (8.6% above baseline 339)
- 154 inferred relationships (EXACT MATCH)
- 1.0% error rate (better than previous 1.3%)
- 98%+ workload query quality

**What Made It Work**:
1. Text-only content filtering (prevented over-extraction)
2. 8K token chunks with 15% overlap
3. Original prompts (~284K chars) with comprehensive GovCon guidance
4. Graceful degradation (simple skip-and-continue, no complex retries)
5. Neo4j storage with workspace isolation

---

### Branch 022a-c: Sub-branches (Mixed Results)

#### 022a-prompt-compression ⚠️ REGRESSION DOCUMENTED

**Goal**: Reduce prompts from 284K → 30K chars (89% reduction)  
**Outcome**: Tokens reduced but NOT ACTIVATED - quality concerns

**Learning**: Compressed prompts created but kept inactive. The 284K original prompts contain domain expertise that compression removes.

#### 022a-table-ontology-processing ✅ GOOD FOUNDATION

**Goal**: 2-stage pipeline for table entities  
**Outcome**: Proper multimodal ontology integration

**Key Commits**:
- `02f5630`: Implement table ontology processing
- `985fad3`: Multimodal processing with synthetic chunks

#### 022b-multimodal-ontology-integration ✅ GOOD

**Goal**: Integrate multimodal content with govcon ontology  
**Outcome**: Fixed premature semantic post-processing during sequential uploads

**Key Fix** (`2327752`): Prevent premature semantic post-processing

#### 022c-new-app-cleanup ✅ GOOD

**Goal**: Remove obsolete code, reorganize tools  
**Outcome**: Cleaner codebase, diagnostic scripts moved to `tools/diagnostics/`

---

### Branch 023: Verbatim Extraction Refactor ✅ GOOD

**Date**: November 2025  
**Goal**: Fix xAI API truncation (Issue #6)  
**Key Changes**:
- `b182603`: Add `stream=False` to prevent truncation
- `b56a924`: Switch to native xAI SDK (gRPC)
- `97e992b`: Remove `source_text` field (KG is index to chunks)

**Outcome**: Fixed critical API truncation bug ✅

**Learning**: xAI SDK native gRPC is more reliable than REST with streaming.

---

### Branch 025: Entity Type Schema Enforcement ✅ GOOD

**Date**: November 2025  
**Goal**: Enforce entity types via Pydantic validation  
**Key Commit**: `bca30a8`

**What Worked**:
- Invalid entity types coerced to `concept` with warning
- No crashes from validation failures
- Graceful fallback pattern

**What to Preserve**:
```python
# Pattern: Validate but don't crash
try:
    validated = EntityModel.model_validate(data)
except ValidationError:
    logger.warning(f"Invalid entity type: {data.get('entity_type')}")
    data['entity_type'] = 'concept'  # Graceful fallback
```

---

### Branch 027: Query Config + BOE Category ✅ MOSTLY GOOD

**Date**: November 2025  
**Sub-branches**:

#### 027-query-config-grok4-2M ✅ GOOD

**Goal**: Query optimization for Grok-4's 2M context  
**Key Commits**:
- `922db5d`: File path citations use clean filenames
- Algorithm 6 logging corrections

#### 027-workload-driver-entity ⚠️ MIXED

**Goal**: Add BOECategory Pydantic enforcement  
**Key Commit**: `fda1e95`

**Good**: BOECategory enum with graceful fallback  
**Warning**: Began pattern of adding specialized fields that later caused fragmentation

---

### Branch 028: Parallel Chunk Extraction ✅ GOOD (Performance)

**Date**: December 2025  
**Goal**: Parallelize chunk and multimodal extraction  
**Key Commit**: `6035921`

**Outcome**:
- Significant processing time reduction
- No quality regression

**Learning**: Parallelization at extraction level is safe and beneficial.

---

### Branch 029: Semantic Post-Processing Optimization ✅ GOOD (Performance)

**Date**: December 2025  
**Goal**: Parallelize 8 semantic algorithms (Issue #30)  
**Key Commit**: `8706daf`

**Results**:
- Post-processing: 20.3 min → 4.75 min (76.6% reduction)
- Total pipeline: 30+ min → 15 min (50% reduction)
- 3,111 relationships inferred
- 100% requirement enrichment

**Phases Implemented**:
1. Phase 1: Parallel execution (43% reduction)
2. Phase 2: Algorithm-specific batching (+867 relationships)
3. Phase 3A: Parallel enrichment (85% reduction)
4. Phase 3B: Full algorithm parallelization (39% reduction)

**Learning**: Parallelization of post-processing is safe when algorithms are independent.

---

### Branch 030: Pydantic LLM Utilities ❌ PROBLEMATIC

**Date**: December 2025  
**Goal**: Three-phase KG processor with Neo4j deduplication  
**Key Commit**: `326aff9`

**What Was Built**:
- `GovconKGProcessor` - 3-phase pipeline (Accumulate → Merge → Finalize)
- Custom entity deduplication logic
- Manual chunk formatting

**THE PROBLEM**: Duplicated RAG-Anything's internal functionality

| What We Built | What RAG-Anything Already Does |
|--------------|-------------------------------|
| `GovconKGProcessor` (3-phase dedup) | `merge_nodes_and_edges()` in Stage 6 |
| `extract_multimodal_with_semaphore()` | `_process_multimodal_content_batch_type_aware()` |
| Manual chunk formatting in `routes.py` | `GovconMultimodalProcessor.generate_description_only()` |

**Evidence of Regression**:
- Commit `ffa2d75` (Branch 031): "remove finalize_storages() call that broke multi-document batch processing"
- Issue #42 documented: "Root cause analysis and regression documentation"

**Learning**: 
> Never duplicate library internals. RAG-Anything has a 7-stage pipeline we should use, not rebuild.

---

### Branch 032: Algorithm 7 CDRL Pattern Enhancement ✅ GOOD

**Date**: December 2025  
**Goal**: Expand CDRL/DID pattern matching  
**Key Commits**:
- `6483c7c`: Comprehensive regex coverage
- `abaca69`: Fix Algorithm 5 ID hallucination
- `8a52040`: Add Appendix pattern support

**What Worked**:
- CDRL patterns: `\bCDRL\s*[A-Z]?\d{3,4}\b`
- DID patterns: `\bDI-[A-Z]+-\d{5}[A-Z]?\b`

**Learning**: Heuristic patterns ARE appropriate for standardized government formats (CDRL/DID). The issue was using brittle patterns for semantic discovery.

---

### Branch 037: Prompt Compression ❌ SIGNIFICANT REGRESSION

**Date**: December 10, 2025  
**Goal**: 23% token reduction in prompts  
**Key Commit**: `7dc1c3a` - Documented regression

**What Was Attempted**:
- V2 prompt architecture with 33% token reduction
- Inline relationship extraction examples
- Compressed inference rule sets

**THE REGRESSION**:

| Aspect | Branch 027/022 | Branch 037 |
|--------|---------------|------------|
| Evaluation factor analysis | 2-3 paragraph comprehensive with regulatory context | Structured but lacking depth |
| Workload detail | Granular quantitative with operational organization | Metadata present but missing narrative |
| Response style | Analytical depth + narrative flow | Structured responses, shallow analysis |

**Root Cause Analysis**:
1. Optional Pydantic fields discouraged LLM extraction
2. LightRAG uses single `PROMPTS[rag_response]` for ALL query modes
3. Token reduction removed domain expertise

**Documented Learning** (from commit message):
> "Optional fields discourage LLM extraction (If it's optional the LLM may be reasoning not to fill it)"

---

### Branch 038: Table Analysis Chunk Format ⚠️ MIXED

**Date**: December 2025  
**Goal**: Fix table analysis in vdb_chunks  
**Key Commits**:
- `528477f`: Restore RAG-Anything pipeline with Pydantic LLM adapter
- `898b373`: Remove duplicate multimodal extraction (47 LLM calls saved)
- `50bc27c`: Revert original Algorithm 2 batching logic

**Good Parts**:
- Removed duplicate multimodal extraction
- Restored original batching logic after regression

**Learning**: The back-and-forth commits show experimentation instability.

---

### Branch 039: Schema-Driven LLM Prompts ✅ GOOD (Algorithm Fix)

**Date**: December 2025  
**Sub-branches**:

#### 039-algorithm-2-llm-discovery ✅ IMPORTANT FIX

**Goal**: Replace brittle keyword matching with LLM-based discovery  
**Key Commit**: `d82bb28`

**Problem Fixed**: Algorithm 2 (Evaluation Hierarchy) missed Factor F due to hardcoded keywords:
```python
# BROKEN: Hardcoded keyword matching
if any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
    # Missing 'small business' → Factor F not discovered
```

#### 039-pydantic-schema-llm-guidance ✅ IMPORTANT FIX

**Goal**: Use Pydantic schema metadata for algorithm robustness  
**Key Commit**: `2efb4ef` (Issue #43)

**Solution Pattern**:
```python
# NEW: Schema-driven LLM discovery
schema_guidance = get_evaluation_hierarchy_guidance()
prompt = f"""{schema_guidance}
Include ALL factors regardless of naming convention.
"""
```

**Algorithms Fixed**:
- Algorithm 1: Instruction-Evaluation Linking
- Algorithm 2: Evaluation Hierarchy
- Algorithm 5: Document Hierarchy

**Learning**: Use hardcoded patterns ONLY for standardized formats (CDRL/DID). Use LLM reasoning for semantic discovery.

---

### Branch 040: Issue #46 Query-Time Ontology ⚠️ IN PROGRESS

**Date**: December 13, 2025  
**Goal**: Fix generic responses missing granular details  
**Key Commits**:
- `09e1497`/`e643a1b`: Query-time ontology + description enrichment + MinerU tables
- `f27f8c3`: **CRITICAL FIX** - Remove artificial KG token caps

**The Token Cap Problem**:
```python
# BROKEN: Query overrides capped tokens
max_entity_tokens = min(max_entity_tokens, 2500)  # Dropped granular details
max_relation_tokens = min(max_relation_tokens, 3500)

# FIXED: Generous token budgets for Grok-4's 2M context
max_entity_tokens = max(max_entity_tokens, 15000)
max_relation_tokens = max(max_relation_tokens, 20000)
```

**Learning**: With Grok-4's 2M context window, don't artificially constrain KG context.

---

## Good Things Worth Keeping/Revisiting

### 1. Pydantic Schema Validation (Branch 025)

**Pattern to preserve**:
```python
class EntityModel(BaseModel):
    entity_type: Literal[*VALID_ENTITY_TYPES]
    
    @model_validator(mode='after')
    def validate_gracefully(self):
        # Validate but don't crash
        return self
```

**Why it works**: Enforces schema without dropping valid data.

### 2. Parallel Processing (Branches 028, 029)

**Safe parallelization**:
- Chunk extraction (independent operations)
- Semantic algorithm execution (8 algorithms run in parallel)
- Workload enrichment batches

**Impact**: 76% reduction in post-processing time.

### 3. Schema-Driven LLM Prompts (Branch 039)

**Pattern** (`src/inference/schema_prompts.py`):
```python
from src.inference.schema_prompts import get_schema_guidance
guidance = get_schema_guidance(EvaluationFactor)
# Returns field descriptions, identification hints, relationship patterns
```

**Fixed algorithms**: 1, 2, 5 now use LLM reasoning instead of brittle keywords.

### 4. BOECategory Enrichment (Branch 027)

**Workload categorization**:
```python
class BOECategory(str, Enum):
    LABOR = "Labor"
    MATERIALS = "Materials"
    ODCS = "ODCs"
    QA = "QA"
    LOGISTICS = "Logistics"
    LIFECYCLE = "Lifecycle"
    COMPLIANCE = "Compliance"
```

### 5. Algorithm 7 CDRL Patterns (Branch 032)

**Appropriate heuristics** for standardized government formats:
```python
cdrl_pattern = r'\bCDRL\s*[A-Z]?\d{3,4}\b'
did_pattern = r'\bDI-[A-Z]+-\d{5}[A-Z]?\b'
```

### 6. Text-Only Content Filter (Branch 022)

**THE critical success factor**:
```python
for item in filtered_content:
    if item.get('type') == 'text':  # ONLY text blocks
        text_chunks.append(item.get('text', ''))
```

**Impact**: 474 blocks → 421 text blocks → 368 optimal entities (vs 1,100+ over-extraction)

### 7. Graceful Error Handling (Branch 022)

**Simple skip-and-continue**:
```python
try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    logger.warning(f"⚠️ Malformed JSON - skipping and continuing")
    return ExtractionResult(entities=[], relationships=[])
```

**What NOT to do**: Complex retries, exponential backoff, temperature adjustments.

---

## Pitfalls & Failed Experiments

### 1. ❌ Duplicating RAG-Anything Internals (Branch 030)

**What went wrong**: Built `GovconKGProcessor` that duplicated RAG-Anything's 7-stage pipeline.

**Correct approach**:
```python
# Register our processor with RAG-Anything
rag_instance.modal_processors["table"] = govcon_processor
# Let RAG-Anything handle the pipeline
await rag_instance.insert_content_list(content_list=filtered_content, ...)
```

### 2. ❌ Artificial Token Caps in Query Overrides (Branch 040 discovery)

**What went wrong**:
```python
# BAD: Caps dropped granular details
max_entity_tokens = min(max_entity_tokens, 2500)
max_relation_tokens = min(max_relation_tokens, 3500)
```

**These were from an era of smaller context windows. Grok-4's 2M context can handle generous KG context.**

### 3. ❌ Prompt Compression at Cost of Quality (Branch 037)

**What went wrong**: 23% token reduction removed domain expertise.

**Evidence**: "Branch 037: Structured responses with metadata but lacking analytical depth and narrative flow"

**Lesson**: Prompts contain encoded domain knowledge. Token reduction should be validated against quality benchmarks.

### 4. ❌ Making Pydantic Fields Optional (Branch 037)

**What went wrong**:
```python
# BAD: Optional fields discourage extraction
modal_verb: Optional[str] = None  # LLM reasons "it's optional, skip it"

# BETTER: Required with defaults
modal_verb: str = Field(default="none")  # Forces LLM to provide value
```

### 5. ❌ Over-Specifying Entity Types (18 types)

**What went wrong**: 
- Fragmented extraction across too many types
- Increased misclassification
- Sparse graph with reduced relationship density
- Validation overhead per type

**Current 18 types**:
```python
VALID_ENTITY_TYPES = {
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
}
```

**Recommendation**: Consider simplification to 12-13 core types per analysis in Branch cursor/* experiments.

### 6. ❌ Hardcoded Keyword Matching in Algorithms (Pre-Branch 039)

**What went wrong** (Algorithm 2):
```python
# BRITTLE: Hardcoded factor keywords
if any(keyword in name.lower() for keyword in ['technical', 'management', 'price', 'cost', 'past performance']):
    # Missed Factor F "Small Business Participation"
```

**Fixed in Branch 039**: Use schema-driven LLM discovery.

### 7. ❌ Complex 8-Algorithm Post-Processing

**Issues**:
- 8 algorithms create overlapping/conflicting edges
- 5+ minutes processing per document batch
- Ghost relationships to non-existent entities
- Each algorithm has its own prompt, validation, batch logic

**Evidence**: 154 relationships (Branch 022) vs 3,000+ relationships (later branches) - quality vs quantity.

---

## Recommendations for Reset

### Starting Point

**Reset to Branch 022** (`cb204fd`) as the clean baseline. This is the "Perfect Run" with documented success metrics.

### Selective Reintroduction Strategy

#### Phase 1: Core Stability (Week 1)

1. **Preserve Branch 022 configuration exactly**:
   - Text-only filter
   - 8192 token chunks, 1200 overlap
   - grok-4-fast-reasoning model
   - Original prompts (~284K chars)

2. **Add back Branch 025 schema validation**:
   - Pydantic EntityModel with graceful fallback
   - Don't make it too strict

3. **Add back Branch 023 xAI SDK fix**:
   - `stream=False` for truncation prevention
   - Native xAI SDK (gRPC)

#### Phase 2: Performance (Week 2)

4. **Add back Branch 028 parallel extraction**:
   - Parallelized chunk processing
   - Safe performance improvement

5. **Add back Branch 029 parallel post-processing**:
   - 8 algorithms in parallel
   - 76% time reduction

#### Phase 3: Algorithm Robustness (Week 3)

6. **Add back Branch 039 schema-driven algorithms**:
   - `schema_prompts.py` utility
   - LLM-based discovery for algorithms 1, 2, 5

7. **Add back Branch 032 CDRL patterns**:
   - Algorithm 7 heuristics for standardized formats

#### Phase 4: Query Optimization (Week 4)

8. **Apply Branch 040 token cap fix**:
   - Remove artificial KG token limits
   - Let Grok-4's 2M context work

### What NOT to Reintroduce

1. ❌ `GovconKGProcessor` - Use RAG-Anything's pipeline
2. ❌ Prompt compression - Keep original 284K prompts
3. ❌ Optional Pydantic fields - Use required with defaults
4. ❌ Complex retry logic - Simple skip-and-continue
5. ❌ Redundant multimodal extraction - RAG-Anything handles it

### Configuration Anchors (Never Change)

```bash
# These values are LOCKED from Branch 022
LLM_MODEL=grok-4-fast-reasoning
CHUNK_SIZE=8192
CHUNK_OVERLAP_SIZE=1200
ENTITY_EXTRACT_MAX_GLEANING=0

# Code anchor
if item.get('type') == 'text':  # Text-only filter - DO NOT REMOVE
```

---

## The 18-Entity Ontology

### Preserve These Types

The 18 entity types represent domain expertise worth keeping:

**Generic types (6)**:
- `organization`, `concept`, `event`, `technology`, `person`, `location`

**GovCon specialized types (12)**:
- `requirement` - Contractor obligations (shall/should/may)
- `clause` - FAR/DFARS references
- `section` - RFP structure (A-M)
- `document` - Referenced documents
- `deliverable` - CDRLs
- `evaluation_factor` - Section M criteria
- `submission_instruction` - Section L requirements
- `statement_of_work` - SOW/PWS tasks
- `performance_metric` - KPIs/QASP
- `program` - Government programs
- `equipment` - GFE/CFE items
- `strategic_theme` - Win themes

### Validation Pattern to Preserve

```python
# From Branch 025 - graceful validation
if entity_type not in VALID_ENTITY_TYPES:
    logger.warning(f"Invalid type '{entity_type}' → coercing to 'concept'")
    entity_type = 'concept'
```

---

## LightRAG/RAGAnything Alignment

### Official LightRAG Best Practices

From LightRAG repository:
- Query modes: `hybrid` recommended (combines local + global)
- `top_k=60` - entities/relationships to retrieve
- `chunk_top_k=20` - text chunks for context
- `enable_rerank=True` - better precision

### Official RAG-Anything 7-Stage Pipeline

```
Stage 1: processor.generate_description_only()  ← OUR PROCESSOR
Stage 2: Convert to LightRAG chunks format      ← RAG-Anything
Stage 3: Store chunks to LightRAG storage       ← LightRAG
Stage 3.5: Store multimodal main entities       ← LightRAG
Stage 4: extract_entities()                     ← LightRAG
Stage 5: Add belongs_to relations               ← LightRAG
Stage 6: merge_nodes_and_edges()               ← LightRAG deduplication
Stage 7: Update doc_status                      ← LightRAG
```

**Our role**: Provide Stage 1 processor with GovCon ontology. Don't rebuild Stages 2-7.

---

## Appendix: Branch Reference Table

| Branch | Key Changes | Goal | Impact | Quality Effect |
|--------|------------|------|--------|---------------|
| **022** | Perfect Run baseline | Lock working config | ✅ Positive | 98%+ quality |
| 022a | Prompt compression | Token reduction | ⚠️ Not activated | N/A (preserved) |
| 022b | Multimodal integration | Table/image entities | ✅ Positive | Maintained |
| 022c | Code cleanup | Remove obsolete code | ✅ Positive | Maintained |
| **023** | xAI SDK fix | Fix truncation | ✅ Positive | Fixed bug |
| **025** | Pydantic validation | Schema enforcement | ✅ Positive | Improved |
| **027** | Query config, BOE | Optimization | ✅ Mostly positive | Improved |
| **028** | Parallel extraction | Performance | ✅ Positive | Maintained |
| **029** | Parallel post-proc | Performance | ✅ Positive | 76% faster |
| **030** | KG processor | Deduplication | ❌ **Problematic** | Duplication issues |
| 031 | Neo4j driver fix | Bug fix | ✅ Positive | Fixed crash |
| **032** | CDRL patterns | Algorithm 7 | ✅ Positive | Better matching |
| 034 | Multimodal fix | Bug fix | ⚠️ Mixed | Instability |
| **037** | Prompt compression | Token reduction | ❌ **Regression** | Quality dropped |
| 038 | Table analysis | Chunk format | ⚠️ Mixed | Back-and-forth |
| **039** | Schema-driven prompts | Algorithm robustness | ✅ Positive | Fixed brittleness |
| **040** | Query-time ontology | Fix generic responses | ⚠️ In progress | Fixing token caps |

---

## Conclusion

The journey from Branch 022 to Branch 040 demonstrates a classic pattern of **feature creep degrading system quality**. Each change made sense in isolation but collectively:

1. **Fragmented the knowledge graph** through over-specification
2. **Duplicated framework functionality** unnecessarily
3. **Constrained retrieval** through artificial limits
4. **Traded quality for metrics** (token reduction, relationship counts)

The path forward is clear: **reset to Branch 022** and selectively reintroduce only the proven improvements (parallelization, schema-driven algorithms, token cap fixes) while avoiding the architectural mistakes (KG processor duplication, prompt compression, optional fields).

The 18-entity ontology and refined prompts represent valuable domain expertise. The goal is to restore the simple, working configuration that achieved 98%+ quality, then carefully add back performance optimizations without repeating the quality regression.

---

**Document Status**: Complete  
**Next Steps**: Create implementation plan for selective reintroduction  
**Related Issues**: #42, #43, #46  
**Preserved For**: Historical learning and reset guidance

---

*"This is the foundation. Lock it in. Document it. Never let it go."* - Branch 022 commit message
