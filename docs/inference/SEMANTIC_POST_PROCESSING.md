# Semantic Post-Processing Architecture

**Branch**: 037-prompt-compression-intelligence-first  
**Date**: December 2025  
**Status**: ✅ Implemented (Role Updated)

---

## ⚠️ PARADIGM SHIFT: Post-Processing Role (December 2025)

### OLD MODEL (Before Branch 037):

- **Main extraction**: Basic entities + minimal relationships
- **Post-processing**: Heavy lifting (8 algorithms inferring relationships after the fact)

### NEW MODEL (After Branch 037):

- **Main extraction**: Rich entities + intelligent relationships (has full source context)
- **Post-processing**: Validation + cross-document gap-filling (trust but verify)

### Why This Matters:

During main extraction, the LLM has **full source text context**. Post-processing only sees extracted entity names and metadata - it's inferring relationships **without the original text**. That's backwards.

**Key Insight**: Extract relationships when you see them. Don't defer to post-processing.

---

## Post-Processing Roles (Updated)

### ✅ KEEP: Cross-Chunk Relationships

- Main extraction sees ONE chunk at a time (~8,192 tokens)
- A requirement in Chunk 5 may relate to a deliverable in Chunk 12
- Post-processing can see ALL entities across chunks

### ✅ KEEP: Orphan Resolution

- Entities extracted but with zero relationships
- Post-processing attempts to connect orphans to existing graph

### ✅ KEEP: Validation & Deduplication

- Confirm relationship targets exist
- Merge near-duplicate entities across chunks
- Remove circular/invalid relationships

### ✅ KEEP: Document Hierarchy (Algorithm 5)

- Structure detection needs document-wide view
- Section numbering patterns (X.Y is child of X)
- Cannot be detected in single-chunk extraction

### ⚠️ REDUCED ROLE: L↔M Mapping (Algorithm 1)

- **Primary**: Main extraction (has "addresses Factor X" text)
- **Secondary**: Post-processing (topic alignment fallback)

### ⚠️ REDUCED ROLE: Requirement→Evaluation (Algorithm 3)

- **Primary**: Main extraction (sees requirement + factor in context)
- **Secondary**: Post-processing (cross-chunk topic mapping)

### ⚠️ REDUCED ROLE: Deliverable Traceability (Algorithm 4)

- **Primary**: Main extraction (sees "per CDRL A001" in text)
- **Secondary**: Post-processing (work-product semantic inference)

---

## Overview

The semantic post-processing pipeline enhances RFP knowledge graphs through two core operations:

1. **Entity Type Correction**: Fixes improperly typed entities (UNKNOWN, forbidden types, etc.)
2. **Relationship Inference**: Discovers missing relationships between entities using LLM semantic understanding

This architecture **replaces** the legacy "Phase 6/7" terminology with clear, semantic operation names.

---

## Architecture

### Single Entry Point

```python
from src.inference.semantic_post_processor import enhance_knowledge_graph

result = await enhance_knowledge_graph(
    rag_storage_path="rag_storage/default",
    llm_func=llm_function,
    batch_size=50
)
```

### Unified Batching Infrastructure

All LLM operations use the centralized `BatchProcessor`:

```python
from src.inference.batch_processor import BatchProcessor

processor = BatchProcessor(batch_size=50)
results = await processor.process_batches(
    items=entities,
    process_fn=correct_types_batch,
    batch_name="Entity Type Correction",
    aggregate_fn=processor.merge_dict_results
)
```

**Benefits**:

- Single batching implementation (DRY principle)
- Consistent progress logging across all operations
- Configurable batch size (default: 50 items per LLM call)
- Unified error handling and result aggregation

---

## Processing Pipeline

### Step 1: Entity Type Correction

**File**: `src/inference/entity_operations.py`

Fixes entities with forbidden types (`UNKNOWN`, `OTHER`, etc.):

```python
from src.inference.entity_operations import correct_entity_types

entities_fixed, retyping_map = await correct_entity_types(
    entities=nodes,
    llm_func=llm_func,
    batch_size=50
)
```

**Input**: Entities with potentially incorrect types
**Output**: Clean entities + mapping of corrections
**Batching**: 50 entities per LLM call
**Cost**: ~$0.01 per 1000 entities

### Step 2: Relationship Inference

**File**: `src/inference/relationship_operations.py`

Discovers missing relationships using 7 algorithms:

```python
from src.inference.relationship_operations import infer_relationships

new_relationships = await infer_relationships(
    entities=nodes,
    existing_relationships=edges,
    llm_func=llm_func,
    batch_size=50
)
```

**Algorithms**:

1. **Document Hierarchy**: DOCUMENT → SECTION (CHILD_OF)
2. **Clause Clustering**: CLAUSE → SECTION (CHILD_OF)
3. **Instruction↔Factor Mapping**: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR (CORRESPONDS_TO)
4. **Requirement Evaluation**: REQUIREMENT → EVALUATION_FACTOR (EVALUATED_BY)
5. **SOW Deliverables**: STATEMENT_OF_WORK → DELIVERABLE (REQUIRES)
6. **Type-Based Heuristics**: Auto-linkage based on entity types
7. **Entity Deduplication**: Merge duplicate entities

**Batching**: 50 items per algorithm per LLM call
**Cost**: ~$0.03 per document (5 LLM batches)

---

## Code Organization

### Before Refactoring (Branch 010)

```
src/inference/
├── forbidden_type_cleanup.py  # Phase 6 - Entity retyping
│   └── Manual batching logic (batch_size=50)
├── engine.py                   # Phase 7 - Relationship inference
│   └── Manual batching logic (BATCH_SIZE=50)
└── [Duplicate code, confusing names]
```

**Problems**:

- Duplicate batching logic (2 implementations)
- Confusing "Phase 6/7" terminology
- Scattered batch size configuration
- Difficult to maintain and test

### After Refactoring (Branch 013)

```
src/inference/
├── batch_processor.py           # ✅ Unified batching infrastructure
├── semantic_post_processor.py   # ✅ Clean orchestrator
├── entity_operations.py         # ✅ Entity type correction
├── relationship_operations.py   # ✅ Relationship inference
└── [Single batching implementation, clear names]
```

**Benefits**:

- Single source of truth for batching
- Self-documenting operation names
- Centralized configuration (BATCH_SIZE)
- Easy to test and extend

---

## Legacy Code Preservation

The original `post_process_knowledge_graph()` function in `routes.py` is **deprecated but preserved** for backward compatibility. It will be removed in a future release.

**Migration**:

```python
# OLD (deprecated)
from src.server.routes import post_process_knowledge_graph
result = await post_process_knowledge_graph(rag_storage_path, llm_func)

# NEW (recommended)
from src.inference.semantic_post_processor import enhance_knowledge_graph
result = await enhance_knowledge_graph(rag_storage_path, llm_func, batch_size=50)
```

---

## Configuration

**Environment Variables**:

```bash
# Batch size for all LLM operations (default: 50)
INFERENCE_BATCH_SIZE=50

# LLM model for all semantic operations
REASONING_LLM_NAME=grok-4-fast-reasoning
```

**Performance Tuning**:

- **Small RFPs (<50 pages)**: batch_size=25 (faster turnaround)
- **Large RFPs (>400 pages)**: batch_size=100 (better throughput)
- **Default**: batch_size=50 (balanced cost/performance)

---

## Testing

```python
# Unit tests for batch processor
pytest tests/test_batch_processor.py

# Integration test with small RFP
python -m src.inference.semantic_post_processor \
  --graphml-path rag_storage/default/graph_chunk_entity_relation.graphml \
  --batch-size 50
```

---

## Cost Estimation

**Entity Type Correction**:

- Input: ~1000 entities with forbidden types
- Batches: 1000 / 50 = 20 batches
- Cost per batch: ~$0.0005 (Grok)
- Total: ~$0.01

**Relationship Inference**:

- Algorithms: 7 (5 LLM-powered + 2 heuristic)
- Batches per algorithm: ~10 (for 500 entities)
- Cost per batch: ~$0.006 (Grok)
- Total: ~$0.30 for all algorithms

**Total per RFP**: ~$0.31 (425-page MCPP DRAFT RFP)

---

## Monitoring

**Progress Logging**:

```
🤖 SEMANTIC POST-PROCESSING: Knowledge Graph Enhancement
  [1/3] Loading GraphML: graph_chunk_entity_relation.graphml
  [2/3] Entity Type Correction: Processing 20 batches...
    Batch 1/20: Processing 50 entities...
    Batch 2/20: Processing 50 entities...
    ...
  [3/3] Relationship Inference: Processing 7 algorithms...
    Algorithm 1: Document Hierarchy (10 batches)...
    Algorithm 2: Clause Clustering (5 batches)...
    ...
  ✅ Enhanced 1522 entities, added 487 relationships
```

---

## Future Enhancements

1. **Parallel Algorithm Execution**: Run 7 algorithms concurrently
2. **Incremental Updates**: Only reprocess changed entities
3. **Confidence Thresholds**: Filter low-confidence relationships
4. **Custom Algorithms**: Plugin architecture for domain-specific inference
5. **Performance Metrics**: Track algorithm effectiveness per RFP type

---

## Related Documentation

- `docs/inference/REFACTORING_PROPOSAL.md` - Original refactoring plan
- `docs/neo4j/IMPLEMENTATION_PLAN.md` - Neo4j integration context
- `docs/archive/PHASE_6_IMPLEMENTATION_HISTORY.md` - Legacy Phase 6 history
- `src/inference/batch_processor.py` - Batching infrastructure
- `src/inference/semantic_post_processor.py` - Orchestrator implementation

---

**Last Updated**: January 2025 (Branch 013 - Neo4j + Semantic Refactoring)
