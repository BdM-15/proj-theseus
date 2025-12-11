# Implementation Plan: Restore RAG-Anything Pipeline

**Issue**: #42 - Table Analysis Missing from vdb_chunks  
**Branch**: 038-table-analysis-chunk-format → will be updated  
**Author**: AI Agent  
**Date**: December 10, 2025

---

## Executive Summary

The current codebase has accumulated unnecessary custom code that duplicates RAG-Anything/LightRAG's internal functionality. This plan restores the original design: **our ontology integrated into RAG-Anything's pipeline**, not a parallel implementation.

### Problem: Accidental Duplication

| What We Built (Branch 030+)            | What RAG-Anything Already Does                              |
| -------------------------------------- | ----------------------------------------------------------- |
| `GovconKGProcessor` (3-phase dedup)    | `merge_nodes_and_edges()` in Stage 6                        |
| `extract_multimodal_with_semaphore()`  | `_process_multimodal_content_batch_type_aware()`            |
| Manual chunk formatting in `routes.py` | Our `GovconMultimodalProcessor.generate_description_only()` |
| Custom entity dict conversion          | RAG-Anything's chunk conversion (Stage 2)                   |

### Solution: Remove Duplication, Restore Original Design

Branch 027 (last working) had the correct pattern:

```python
# Register our processor
rag_instance.modal_processors["table"] = govcon_processor
rag_instance.modal_processors["image"] = govcon_processor
rag_instance.modal_processors["equation"] = govcon_processor

# Use RAG-Anything's pipeline (which calls our processor)
await rag_instance.insert_content_list(content_list=multimodal_items, ...)
```

---

## Architecture Comparison

### RAG-Anything's 7-Stage Pipeline (We Should Use This)

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

### What We Provide

1. **`GovconMultimodalProcessor.generate_description_only()`** - Returns our ontology entities as the "description" that becomes the chunk content
2. **Entity extraction prompts** (`prompts/extraction/`) - Define our 18 entity types
3. **Semantic post-processing** (`src/inference/`) - LLM algorithms AFTER insertion

### What We Should NOT Provide (Delete)

1. **`GovconKGProcessor`** - Duplicates Stage 6
2. **`extract_multimodal_with_semaphore()`** - Duplicates Stage 1
3. **Manual chunk formatting in `routes.py`** - Our processor already handles this
4. **Entity/relationship dict conversion** - Stage 2 handles this

---

## Implementation Steps

### Phase 1: Restore `routes.py` to Branch 027 Pattern

**File**: `src/server/routes.py`

**Remove** (lines ~296-560 - the entire "Neo4J custom extraction" block):

- `GovconKGProcessor` import and usage
- `extract_with_semaphore()` for text chunks (keep for different purpose or remove entirely)
- `extract_multimodal_with_semaphore()` for multimodal items
- Manual entity/relationship dict conversion
- Manual chunk formatting with "Table Analysis:" template
- `processed_kg` building logic

**Restore** (from Branch 027 - `git show b1c6c5b:src/server/routes.py`):

```python
# Register our govcon processors with RAG-Anything
from src.processors import GovconMultimodalProcessor

govcon_processor = GovconMultimodalProcessor(
    lightrag=rag_instance.lightrag,
    modal_caption_func=llm_func,
    context_extractor=rag_instance.context_extractor
)

# Override RAG-Anything's default processors
rag_instance.modal_processors["table"] = govcon_processor
rag_instance.modal_processors["image"] = govcon_processor
rag_instance.modal_processors["equation"] = govcon_processor

# Process multimodal content through RAG-Anything's pipeline
multimodal_items = [item for item in filtered_content if item.get('type') in ['table', 'image', 'equation']]
if multimodal_items:
    logger.info(f"📊 Processing {len(multimodal_items)} multimodal items with govcon ontology...")
    await rag_instance.insert_content_list(
        content_list=multimodal_items,
        file_path=file_name,
        doc_id=doc_id
    )
```

### Phase 2: Verify/Update `GovconMultimodalProcessor`

**File**: `src/processors/govcon_multimodal_processor.py`

This processor should already be correct since it was designed for RAG-Anything's pipeline. Verify:

1. **`generate_description_only()`** returns `(description, entity_info)` tuple
2. The `description` string is formatted with "Table Analysis:" template + our entities
3. The `entity_info` dict contains entity metadata for RAG-Anything's Stage 3.5

**Expected Output Format** (from `generate_description_only()`):

```python
description = """Table Analysis:
Image Path: /path/to/table.png
Caption: Contract Requirements Matrix
Structure: <table HTML>
Footnotes: None

Analysis:
requirement: Monthly Status Report
deliverable: CDRL A001
metric: 30 calendar days
compliance_term: SHALL provide
"""

entity_info = {
    "entity_name": "Contract Requirements Matrix",
    "entity_type": "table",
    "source_id": doc_id
}

return (description, entity_info)
```

### Phase 3: Text Chunk Handling - RAG-Anything All The Way

**Decision**: RAG-Anything handles ALL content. LightRAG's `ainsert()` bypasses our ontology.

```python
# Register our ontology processor for multimodal content
rag_instance.modal_processors["table"] = govcon_processor
rag_instance.modal_processors["image"] = govcon_processor
rag_instance.modal_processors["equation"] = govcon_processor

# RAG-Anything handles ALL content
# - Text → LightRAG's text pipeline (chunking, entity extraction)
# - Multimodal → Our GovconMultimodalProcessor (ontology-aware extraction)
await rag_instance.insert_content_list(
    content_list=filtered_content,  # ALL types: text, table, image, equation
    file_path=file_name,
    doc_id=doc_id
)
```

RAG-Anything's `insert_content_list()` separates text vs multimodal internally:

- Text items → LightRAG's native text processing
- Multimodal items → Our registered processors with Pydantic-validated ontology

````

**Recommendation**: Start with Option B (matches Branch 027), test, then consider Option A.

### Phase 4: Delete Redundant Code

**Files to DELETE entirely**:

- `src/processors/govcon_kg_processor.py` - Duplicates LightRAG's merge
- `src/extraction/table_extractor.py` - Dead code, never integrated
- `tests/test_kg_processor.py` - Tests for deleted file

**Code to DELETE from `routes.py`**:

- `extract_with_semaphore()` function (unless reused for different purpose)
- `extract_multimodal_with_semaphore()` function
- All Phase 2A/2B/3-5 code blocks in `process_document_with_semantic_inference()`

### Phase 5: Update Tests

**Keep**:

- `tests/test_json_extraction.py` - Tests our entity extraction (still used by processor)
- `tests/test_semantic_postprocessing_smoke.py` - Tests inference algorithms

**Delete**:

- `tests/test_kg_processor.py` - Tests deleted processor

**Update**:

- Integration tests to verify RAG-Anything pipeline produces correct chunks

---

## Validation Plan

### Test 1: Table Count Match

Process MCPP RFP through restored pipeline:

```bash
# Should produce 42 tables (matching workspace 2_mcpp_drfp_2025)
python tools/diagnostics/compare_vdb_chunks.py 2_mcpp_drfp_2025 <new_workspace>
````

Expected: Same table count, same "Table Analysis:" format in chunks

### Test 2: Chunk Format Verification

Check vdb_chunks for proper format:

```python
# All table chunks should have:
# - "Table Analysis:" prefix
# - "Image Path:" field
# - "Analysis:" section with our entities
```

### Test 3: User Query Quality

Test representative queries:

1. "What are the CDRLs in this RFP?" - Should find deliverables
2. "Show me performance metrics" - Should find tables with metrics
3. "What are the key person requirements?" - Should work as before

---

## Risk Assessment

| Risk                                         | Mitigation                                           |
| -------------------------------------------- | ---------------------------------------------------- |
| RAG-Anything API changed                     | Library is pip-installed, version pinned             |
| `generate_description_only()` format differs | Verify return tuple format matches expected          |
| Text chunk extraction quality differs        | Can always fall back to Option B (separate handling) |
| Semantic post-processing still needed        | Unchanged - runs AFTER insertion                     |

---

## Files Changed Summary

| File                                            | Action | Reason                                                                  |
| ----------------------------------------------- | ------ | ----------------------------------------------------------------------- |
| `src/server/routes.py`                          | MODIFY | Remove ~300 lines of custom extraction, restore `insert_content_list()` |
| `src/processors/govcon_multimodal_processor.py` | VERIFY | Ensure `generate_description_only()` returns correct format             |
| `src/processors/govcon_kg_processor.py`         | DELETE | Duplicates LightRAG's merge                                             |
| `src/extraction/table_extractor.py`             | DELETE | Dead code                                                               |
| `tests/test_kg_processor.py`                    | DELETE | Tests deleted code                                                      |
| `src/processors/__init__.py`                    | MODIFY | Remove `GovconKGProcessor` export                                       |

---

## Rollback Plan

If issues arise:

1. Branch 038 current state is preserved
2. Branch 027 (`b1c6c5b`) contains known-working code
3. Can cherry-pick specific fixes back

---

## Estimated Effort

| Phase                           | Effort    | Complexity                |
| ------------------------------- | --------- | ------------------------- |
| Phase 1: Restore routes.py      | 1-2 hours | Medium (careful deletion) |
| Phase 2: Verify processor       | 30 min    | Low                       |
| Phase 3: Text handling decision | 30 min    | Low                       |
| Phase 4: Delete redundant code  | 30 min    | Low                       |
| Phase 5: Update tests           | 30 min    | Low                       |
| Validation                      | 1-2 hours | Medium (full RFP test)    |

**Total**: 4-6 hours

---

## Approval Required

Before implementation:

1. ☐ Confirm Option A vs Option B for text handling
2. ☐ Confirm deletion of `govcon_kg_processor.py`
3. ☐ Confirm deletion of `table_extractor.py`

---

## References

- **RAG-Anything Pipeline**: `_process_multimodal_content_batch_type_aware()` source code
- **Branch 027 (working)**: `git show b1c6c5b:src/server/routes.py`
- **Commit that broke it**: `326aff9` - "feat(extraction): implement three-phase KG processor"
- **Issue #42**: Root cause analysis and regression documentation
