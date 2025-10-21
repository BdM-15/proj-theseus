# Branch 008: Knowledge Graph Accumulation Fix

**Created**: January 19, 2025  
**Issue**: Documents processed via WebUI are NOT being added to the unified knowledge graph  
**Impact**: CRITICAL - Complete loss of cross-document reasoning capability

---

## Problem Statement

### What Was Discovered

When uploading Excel file `AFCAP V FA8051-25-R-1009 R00 Submittal.xlsx` via WebUI:

1. ✅ **Document processes successfully** (LibreOffice converts Excel → PDF)
2. ✅ **Entities extracted** (49 entities, 82 relationships from MinerU tables)
3. ✅ **Graph written** to `rag_storage/default/graph_chunk_entity_relation.graphml`
4. ❌ **Semantic inference NEVER runs** - code looks in wrong location

### Root Cause

**Path Mismatch in `src/server/routes.py`**:

```python
# Line 75: RAG-Anything writes to this directory
await rag_instance.process_document_complete(
    file_path=file_path,
    output_dir=global_args.working_dir,  # "./rag_storage"
    parse_method="auto"
)

# Line 83: But semantic inference looks HERE (wrong!)
graphml_path = Path(global_args.working_dir) / "graph_chunk_entity_relation.graphml"
# Resolves to: rag_storage/graph_chunk_entity_relation.graphml (does not exist!)
```

**Actual Location** where LightRAG writes the graph:

```
rag_storage/default/graph_chunk_entity_relation.graphml
```

### Why This Matters

**Without semantic inference**, the knowledge graph is missing:

- ❌ Section L ↔ M relationship mapping (evaluation instructions)
- ❌ Document attachment linkage (J-#### → parent sections)
- ❌ Requirement → Evaluation factor mapping
- ❌ Clause clustering (FAR/DFARS hierarchy)
- ❌ SOW deliverable relationships

**Result**: Queries return basic entity extraction only, no intelligent cross-referencing.

---

## The Bigger Issue: Knowledge Graph Architecture

### Expected Behavior (Unified Graph)

**ONE monolithic knowledge graph** accumulating ALL processed documents:

```
rag_storage/default/
├── graph_chunk_entity_relation.graphml  ← 1545 nodes (growing with each doc)
├── kv_store_full_entities.json
├── kv_store_full_relations.json
└── [other storage files]
```

**Every document upload should**:

1. Extract entities/relationships from new document
2. **MERGE** into existing graph (deduplicate, link cross-document entities)
3. Run semantic inference on **complete graph**
4. Enable cross-document queries: "Which documents reference Section M Factor 1?"

### Current Behavior (Isolated Graphs)

Investigation of `rag_storage/` reveals potential isolation:

```
rag_storage/
├── AFCAP V FA8051-25-R-1009 R00 Submittal/  ← Per-doc MinerU output (expected)
│   └── auto/  ← Parsing artifacts
├── default/  ← Main graph (SHOULD accumulate all docs)
│   └── graph_chunk_entity_relation.graphml
├── Document2/
└── Document3/
```

**Question to investigate**: Are all documents being merged into `default/` graph, or are some being isolated?

---

## Proposed Fix (Branch 008)

### Phase 1: Path Correction (IMMEDIATE)

**File**: `src/server/routes.py`

Change line 83 from:

```python
graphml_path = Path(global_args.working_dir) / "graph_chunk_entity_relation.graphml"
```

To:

```python
graphml_path = Path(global_args.working_dir) / "default" / "graph_chunk_entity_relation.graphml"
```

**Impact**: Semantic inference will now find the graph and run successfully.

### Phase 2: Validation (TESTING)

1. **Upload test document** via WebUI
2. **Verify logs show**:
   - `✅ GraphML ready after Xs total wait`
   - `🤖 Running LLM-powered relationship inference (5 algorithms)...`
   - `✅ VALIDATED: N new relationships persisted to GraphML`
3. **Check graph size grows**: `rag_storage/default/graph_chunk_entity_relation.graphml` node count increases
4. **Run cross-document query**: Verify entities from multiple docs appear together

### Phase 3: Architecture Audit (DOCUMENTATION)

**Investigate**:

- Why does LightRAG use `default/` subdirectory? (RAG-Anything behavior)
- Are per-document directories (`AFCAP V FA8051.../`) just parsing artifacts?
- Does `process_document_complete()` always merge into `default/` graph?

**Document findings** in `docs/ARCHITECTURE.md` for future reference.

---

## Success Criteria

✅ **Semantic inference runs** after every document upload  
✅ **Knowledge graph accumulates** all documents in `default/` directory  
✅ **Cross-document queries work**: "Show all EVALUATION_FACTOR entities across documents"  
✅ **Graph metrics increase**: Node/edge count grows with each upload  
✅ **No regressions**: Existing RFP processing still works (69s Navy MBOS baseline)

---

## Risk Assessment

**Risk**: LOW

- Single-line path fix in one file
- No changes to RAG-Anything/LightRAG core logic
- Semantic inference code already tested and working

**Rollback**: Simple - revert branch if issues arise

---

## Timeline

- **January 19, 2025**: Issue discovered during Excel file upload testing
- **January 19, 2025**: Branch 008 created, fix implemented
- **Target**: Merge to main after validation (same day if tests pass)

---

## Related Issues

- **Excel filename bug**: Discovered LibreOffice headless mode fails with complex filenames (multiple hyphens)
- **openpyxl dependency**: Installed but not needed after path fix resolves issue

---

## Fix Implementation Results

### ✅ Successfully Fixed (January 19, 2025)

**Changes Made**:

1. Updated `src/server/routes.py` line 83: Added `/ "default"` to GraphML path
2. Updated `post_process_knowledge_graph()`: Changed to `rag_storage / "default" / "graph_chunk_entity_relation.graphml"`
3. Updated `save_relationships_to_kv_store()`: Changed to `rag_storage / "default"`

**Validation Results**:

- ✅ Processed 5-6 documents successfully
- ✅ Semantic inference ran on every upload (207+ relationships added)
- ✅ Knowledge graph accumulated to 1518 nodes, 3785 edges
- ✅ Cross-document queries working perfectly (tested with GAO protest prep query)
- ✅ Entity merging across documents: `AFCAP V` merged 4+11 times, `KBR` merged 2+27 times
- ✅ GraphML file size grew from 170KB → 3.3MB across uploads

**Example Query Success**:
Query about "price evaluation methods for debrief" returned:

- Labor categories from Excel spreadsheet ✅
- AFCAP V FOPR details from PDFs ✅
- FAR/DFARS clauses from provisions document ✅
- GAO case citations (Apprio, Valor Healthcare) ✅
- Pricing analysis across multiple RFPs ✅

### ⚠️ Remaining Minor Issues (Non-Blocking)

**1. WebUI Display Bug**

- **Issue**: Excel file `AFCAP V FA8051-25-R-1009 R00 Submittal.xlsx` processed successfully but doesn't appear in WebUI document list
- **Root Cause**: `doc_status` not updated for multimodal-only documents (zero text content, only tables)
- **Impact**: Cosmetic only - entities ARE in knowledge graph and queryable
- **Evidence**: Graph shows merged entities (Force Protection specialists, pricing tables)
- **Fix Required**: Separate issue - update doc_status tracking for multimodal-only uploads

**2. Semantic Inference LLM Output Errors**

- **Issue**: 3 relationships rejected due to missing `relationship_type` field
- **Errors**:
  ```
  ERROR: Relationship 31 missing required keys: {'relationship_type'}
  Source: '52.204-26 Covered Telecommunications Equipment' → 'Section I'
  ```
- **Impact**: Minimal - 3 out of 200+ relationships lost (98.5% success rate)
- **Root Cause**: LLM occasionally omits required field in JSON response
- **Fix Required**: Prompt refinement in `src/inference/prompts.py` - add more explicit field requirements

**3. LibreOffice Command Warning**

- **Issue**: `WARNING: LibreOffice command 'libreoffice' not found`
- **Status**: Cosmetic warning only - conversion succeeds via fallback mechanism
- **Solution**: Created symlink `libreoffice.exe` → `soffice.exe` (resolved post-testing)
- **Impact**: None - Excel/Word files process successfully

### LightRAG Architecture Discovery

**Why `default/` Subdirectory Exists**:

- LightRAG uses `workspace` parameter for data isolation (multi-tenant support)
- When `workspace=""` (empty string), LightRAG internally converts to `"_"` and creates `default/` subdirectory
- This is **core LightRAG architecture**, not a bug
- Per-document folders (e.g., `AFCAP V FA8051.../`) are MinerU parsing artifacts, not knowledge graphs
- **Only** `default/graph_chunk_entity_relation.graphml` contains the unified knowledge graph

**Verified Behavior**:

- All documents merge into single `default/` graph ✅
- Entity deduplication works across documents ✅
- Relationships span multiple documents ✅
- Cross-document queries retrieve from unified graph ✅

---

## Notes for Future Branches

**Always verify**:

- Path resolution when using `global_args.working_dir`
- LightRAG's actual file output locations (check `rag_storage/` structure)
- Semantic inference logs confirm GraphML was found and processed
- **New**: Check LightRAG workspace subdirectory pattern when working with storage paths
- **New**: Test multimodal-only documents for doc_status tracking
- **New**: Monitor LLM output validation errors in semantic inference
