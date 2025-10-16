# Document Reference Naming Issue - Future Branch

**Status**: Not Started (Documented for Future Implementation)  
**Priority**: Medium (User Experience Enhancement)  
**Estimated Effort**: 2-4 hours  
**Branch Name Suggestion**: `006-human-readable-document-references`

---

## Problem Statement

### Current Behavior

When uploading documents via API/WebUI endpoints (`/insert` or `/documents/upload`), query results show temporary filenames instead of human-readable RFP identifiers:

```
Query: "What are the deliverables?"
Response: "According to the RFP, deliverables include..."
References:
  [1] tmpgo9yz6nu.pdf  ← PROBLEM: Unprofessional, meaningless reference
```

**Expected Behavior**:

```
References:
  [1] N6945025R0003 Navy MBOS RFP.pdf  ← SOLUTION: Human-readable RFP number/title
```

### Impact

- **Capture Management**: Unprofessional references in client-facing deliverables
- **Traceability**: Impossible to identify which RFP a query result references
- **User Experience**: Confusing for proposal teams tracking multiple RFPs

---

## Root Cause Analysis

### Technical Architecture Discovery

Your system has **two distinct upload workflows**:

#### 1. Manual Processing Path (`inputs/__enqueued__/`)

- **Status**: ✅ Working correctly with human-readable names
- **Usage**: Manual MinerU preprocessing
- **Example**: `inputs/__enqueued__/M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf`
- **Processing**: `mineru -p "inputs/__enqueued__/file.pdf" -o output/`
- **Result**: Original filename preserved through entire pipeline

#### 2. API Upload Path (`inputs/uploaded/`)

- **Status**: ❌ Broken - folder doesn't exist, temp files used instead
- **Config Reference**: `config.py` line 38 sets `INPUT_DIR = "./inputs/uploaded"`
- **Actual Behavior**: Folder never created, upload endpoints use Python `tempfile` module
- **Result**: Random temp names (`tmpgo9yz6nu.pdf`) stored in LightRAG knowledge graph

### Code Location: The Problem

**File**: `src/server/routes.py`  
**Functions**: `create_insert_endpoint()` (lines 286-320) and `create_documents_upload_endpoint()` (lines 339-380)

```python
# PROBLEM CODE: Lines 286-320 in create_insert_endpoint()
with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
    shutil.copyfileobj(file.file, tmp)
    tmp_path = tmp.name  # Creates: /tmp/tmpgo9yz6nu.pdf

# This temp path is what gets stored in LightRAG:
await rag.apipeline_enqueue_documents(content, file_paths=[tmp_path])
#                                                              ^^^^^^^^
#                                                              Random temp filename!

# Later cleanup destroys the file but LightRAG already stored the temp name
os.unlink(tmp_path)
```

**LightRAG's Behavior** (from GitHub repo analysis):

- Stores whatever `file_path` you pass during `apipeline_enqueue_documents()`
- Query results include: `{"reference_id": "1", "file_path": "<stored_filename>"}`
- The library **preserves what you give it** - it doesn't manage document naming conventions

### Data Flow Diagram

```
User uploads "Navy_MBOS_RFP.pdf"
    ↓
FastAPI receives UploadFile(filename="Navy_MBOS_RFP.pdf")
    ↓
routes.py: tempfile.NamedTemporaryFile(suffix=".pdf")
    ↓
Creates random name: /tmp/tmpgo9yz6nu.pdf
    ↓
RAG-Anything processes with temp path
    ↓
LightRAG stores: file_path="tmpgo9yz6nu.pdf"
    ↓
GraphML: <data key="file_path">tmpgo9yz6nu.pdf</data>
    ↓
Query returns: [1] tmpgo9yz6nu.pdf ← Displayed to user
```

---

## Solution Options

### Option 1: Preserve Original Filename (Recommended - Simplest)

**Approach**: Pass original filename to LightRAG instead of temp path

**Changes Required**:

1. Modify `create_insert_endpoint()` in `src/server/routes.py` (lines 286-320)
2. Modify `create_documents_upload_endpoint()` in `src/server/routes.py` (lines 339-380)

**Implementation**:

```python
# BEFORE (Current broken code):
with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
    shutil.copyfileobj(file.file, tmp)
    tmp_path = tmp.name

# Process document...
await rag.apipeline_enqueue_documents(content, file_paths=[tmp_path])
os.unlink(tmp_path)

# AFTER (Fixed code):
with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
    shutil.copyfileobj(file.file, tmp)
    tmp_path = tmp.name

# Process document but use ORIGINAL filename for LightRAG storage
original_filename = file.filename  # "Navy_MBOS_RFP.pdf"
await rag.apipeline_enqueue_documents(content, file_paths=[original_filename])
os.unlink(tmp_path)
```

**Pros**:

- Minimal code changes (2 lines in each endpoint)
- No database migration required
- Preserves user's original naming convention
- Zero performance impact

**Cons**:

- Filename collisions possible if users upload multiple files with same name
- Doesn't enforce RFP numbering conventions

**Testing**:

1. Upload test RFP: `curl -X POST http://localhost:9621/insert -F "file=@Navy_MBOS.pdf"`
2. Query: `curl -X POST http://localhost:9621/query -d '{"query": "deliverables"}'`
3. Verify reference shows: `[1] Navy_MBOS.pdf` instead of `[1] tmpgo9yz6nu.pdf`

---

### Option 2: Extract RFP Number from Content (Advanced)

**Approach**: Use LLM to detect RFP number from document content, set as document ID

**Changes Required**:

1. Create new function: `extract_rfp_metadata()` in `src/inference/llm_relationship_inference.py`
2. Modify upload endpoints to call extraction before LightRAG insertion
3. Update Phase 6 pipeline to standardize document naming

**Implementation Sketch**:

```python
async def extract_rfp_metadata(content: str, llm_func) -> dict:
    """Extract RFP number and title using LLM"""
    prompt = """
    Extract the following from this RFP:
    1. RFP Number (e.g., "N6945025R0003", "FA8732-25-R-0042")
    2. Program Title (e.g., "Navy MBOS", "MCPP II")

    RFP Content:
    {content[:5000]}

    Return JSON: {{"rfp_number": "...", "program_title": "..."}}
    """

    response = await llm_func(prompt)
    # Parse JSON, construct filename: "{rfp_number} {program_title}.pdf"
    return metadata

# In upload endpoint:
metadata = await extract_rfp_metadata(content, llm_func)
standardized_filename = f"{metadata['rfp_number']} {metadata['program_title']}.pdf"
await rag.apipeline_enqueue_documents(content, file_paths=[standardized_filename])
```

**Pros**:

- Enforces consistent naming: "N6945025R0003 Navy MBOS.pdf"
- Automatically extracts professional identifiers
- Handles cases where user uploads poorly named files

**Cons**:

- Requires LLM call per upload (adds latency and cost ~$0.001)
- More complex error handling (what if RFP number not found?)
- Risk of incorrect extraction

**Cost Estimate**: $0.001 per RFP upload (1,000-token extraction prompt to Grok-beta)

---

### Option 3: Unified `__enqueued__/` Workflow (Architectural Simplification)

**Approach**: Eliminate `uploaded/` folder concept, use `__enqueued__/` pattern for all uploads

**Changes Required**:

1. Modify upload endpoints to save files to `inputs/__enqueued__/` with original names
2. Remove `INPUT_DIR="./inputs/uploaded"` config (unused anyway)
3. Update `.gitignore` to only reference `__enqueued__/` pattern

**Implementation**:

```python
# In upload endpoint:
safe_filename = sanitize_filename(file.filename)  # Already exists in code
enqueued_path = Path("./inputs/__enqueued__") / safe_filename

# Handle filename collisions
if enqueued_path.exists():
    enqueued_path = get_unique_filename_in_enqueued(enqueued_path.parent, safe_filename)

# Save uploaded file directly to __enqueued__/
with open(enqueued_path, "wb") as f:
    shutil.copyfileobj(file.file, f)

# Process with original path (no temp files!)
content = await process_document_with_ucf_detection(str(enqueued_path))
await rag.apipeline_enqueue_documents(content, file_paths=[safe_filename])

# Optionally: Delete from __enqueued__/ after processing if desired
```

**Pros**:

- Architectural consistency (one upload path for all documents)
- Original filenames preserved
- Files visible on disk during processing (easier debugging)
- Cleanup: Remove unused `uploaded/` folder concept

**Cons**:

- Larger change scope (more code modifications)
- Need to handle disk space management (when to delete from `__enqueued__/`?)
- Risk of filename collisions (need `get_unique_filename_in_enqueued()` function)

---

## Recommended Implementation Plan

**Choose Option 1** (Preserve Original Filename) for MVP:

### Phase 1: Quick Fix (1-2 hours)

1. Modify `create_insert_endpoint()` to use `file.filename` instead of `tmp_path.name`
2. Modify `create_documents_upload_endpoint()` same way
3. Test with one RFP upload
4. Commit as working fix

### Phase 2: Collision Handling (1 hour)

1. Add duplicate filename detection in upload endpoints
2. Append `_001`, `_002` suffixes if collision detected
3. Log warning when collision occurs

### Phase 3: Enhancement (Optional - Future)

1. Consider Option 2 (LLM extraction) if standardization becomes critical
2. Consider Option 3 (unified workflow) as part of larger refactoring

---

## Files to Modify

### Primary Changes

- **`src/server/routes.py`** (lines 286-320, 339-380)
  - `create_insert_endpoint()`: Change `file_paths=[tmp_path]` to `file_paths=[file.filename]`
  - `create_documents_upload_endpoint()`: Same change

### Configuration Cleanup (Optional)

- **`src/server/config.py`** (line 38)
  - Document why `INPUT_DIR` is unused (or remove if Option 3 chosen)

### Testing

- **Manual Test Script** (create new file):

  ```bash
  # Upload test RFP with known filename
  curl -X POST http://localhost:9621/insert \
    -F "file=@Navy_MBOS_Test.pdf" \
    -F "mode=auto"

  # Query and verify reference
  curl -X POST http://localhost:9621/query \
    -H "Content-Type: application/json" \
    -d '{"query": "What are the deliverables?", "mode": "hybrid"}'

  # Expected output should contain:
  # "references": [{"reference_id": "1", "file_path": "Navy_MBOS_Test.pdf"}]
  ```

---

## Testing Checklist

### Unit Tests (Create in `tests/test_document_references.py`)

```python
async def test_upload_preserves_original_filename():
    """Verify uploaded filename appears in query references"""
    # Upload file with specific name
    # Query knowledge graph
    # Assert reference matches original filename

async def test_filename_collision_handling():
    """Verify duplicate filenames get unique suffixes"""
    # Upload "test.pdf" twice
    # Assert second becomes "test_001.pdf"

async def test_special_characters_in_filename():
    """Verify filename sanitization doesn't break references"""
    # Upload "RFP (Draft) #123.pdf"
    # Assert sanitized name appears in references
```

### Integration Tests

1. Upload 3 different RFPs with descriptive names
2. Run queries that reference each RFP
3. Verify all references show original filenames
4. Check GraphML file contains correct `file_path` attributes

### Regression Tests

1. Verify existing `__enqueued__/` manual workflow still works
2. Confirm Phase 6 post-processing doesn't break with filename changes
3. Test MinerU output directories use correct naming

---

## Known Risks & Mitigations

### Risk 1: Filename Collisions

**Scenario**: User uploads two files with same name (e.g., "RFP.pdf")  
**Current Behavior**: Second upload overwrites first in knowledge graph  
**Mitigation**:

- Option A: Add collision detection, reject duplicate with error message
- Option B: Auto-append suffix (`RFP_001.pdf`, `RFP_002.pdf`)
- **Recommended**: Option B (better UX)

### Risk 2: Special Characters in Filenames

**Scenario**: Filename contains `/`, `\`, `..`, or other path traversal characters  
**Current State**: Already handled by `sanitize_filename()` in `routes.py`  
**Mitigation**: Verify sanitization doesn't break reference display

### Risk 3: LightRAG Storage Compatibility

**Scenario**: LightRAG expects actual file paths, breaks if file doesn't exist  
**Investigation Result**: ✅ LightRAG stores `file_path` as **metadata string only** - file doesn't need to exist on disk after processing (confirmed from GitHub repo analysis)  
**Mitigation**: None needed - library design supports this pattern

### Risk 4: Existing Documents in Production

**Scenario**: Already-processed RFPs have `tmpgo9yz6nu.pdf` references  
**Impact**: Historical queries will still show temp filenames  
**Mitigation**:

- Option A: Accept as technical debt (new uploads fixed going forward)
- Option B: Write migration script to update GraphML `file_path` attributes
- **Recommended**: Option A unless production deployment imminent

---

## Migration Strategy (If Needed)

If you have production RFPs already processed with temp filenames:

### GraphML Repair Script

```python
# scripts/fix_document_references.py
import networkx as nx
from pathlib import Path

def repair_graphml_references(graphml_path: Path, filename_map: dict):
    """
    Replace temp filenames with human-readable names in existing GraphML

    Args:
        graphml_path: Path to graph_chunk_entity_relation.graphml
        filename_map: {"tmpgo9yz6nu": "Navy_MBOS_RFP.pdf", ...}
    """
    G = nx.read_graphml(str(graphml_path))

    # Update node file_path attributes
    for node_id, node_data in G.nodes(data=True):
        if 'file_path' in node_data:
            old_path = node_data['file_path']
            if old_path in filename_map:
                G.nodes[node_id]['file_path'] = filename_map[old_path]

    # Update edge file_path attributes
    for u, v, edge_data in G.edges(data=True):
        if 'file_path' in edge_data:
            old_path = edge_data['file_path']
            if old_path in edge_data:
                G.edges[u, v]['file_path'] = filename_map[old_path]

    # Save repaired graph
    nx.write_graphml(G, str(graphml_path))
    print(f"✅ Repaired {len(filename_map)} document references")

# Usage:
# python scripts/fix_document_references.py --map "tmpgo9yz6nu:Navy_MBOS.pdf"
```

---

## Success Metrics

### Definition of Done

- [ ] Upload RFP with filename "N6945025R0003_Navy_MBOS.pdf"
- [ ] Query knowledge base about that RFP
- [ ] Response references show: `[1] N6945025R0003_Navy_MBOS.pdf`
- [ ] No `tmpgo9yz6nu` or other temp filenames visible in any query
- [ ] Existing manual `__enqueued__/` workflow still functions correctly
- [ ] Unit tests pass for filename preservation
- [ ] Integration test covers 3+ different RFPs with unique names

### Performance Benchmarks

- No impact on 69-second processing time (Navy MBOS baseline)
- No increase in $0.042 cost per RFP (no new LLM calls in Option 1)
- Upload endpoint latency unchanged (< 500ms for file save)

---

## Related Documentation

### Existing Files

- **`docs/MINERU_SETUP_GUIDE.md`** (line 132): Shows `__enqueued__/` pattern with human-readable names
- **`docs/ARCHITECTURE.md`**: Documents two-stage processing (ingestion vs post-processing)
- **`.gitignore`** (lines 131-150): Both `uploaded/` and `__enqueued__/` patterns

### External Resources

- **RAG-Anything GitHub**: `raganything/parser.py` shows temp file usage for MinerU processing
- **LightRAG GitHub**: `lightrag/utils.py` line 2493 shows `build_file_path()` metadata handling
- **LightRAG GitHub**: `lightrag/api/routers/document_routes.py` shows document upload patterns

---

## Branch Strategy

### Suggested Branch Name

`006-human-readable-document-references`

### Branch From

`005-mineru-optimization` (current working branch)

### Merge Strategy

1. Implement Option 1 (quick fix) in branch
2. Test with 3+ RFPs
3. Create PR to `005-mineru-optimization`
4. After merge, consider Option 2/3 as separate enhancement branches

### Commit Message Pattern

```
fix(upload): preserve original filenames in document references

- Modified create_insert_endpoint() to use file.filename instead of temp path
- Modified create_documents_upload_endpoint() same way
- Query references now show human-readable RFP names instead of tmpgo9yz6nu
- Resolves unprofessional reference naming in capture management workflow

Closes #[issue number if tracking]
```

---

## Questions for Future Developer

Before implementing, clarify:

1. **Collision Policy**: Should duplicate filenames be rejected or auto-suffixed?
2. **Historical Data**: Do existing RFPs with temp names need migration?
3. **Naming Convention**: Should we enforce RFP number format (e.g., "N6945025R0003")?
4. **Production Timeline**: Is this blocking any client deliverables?

---

## Estimated Timeline

### Option 1 (Recommended)

- **Implementation**: 1 hour
- **Testing**: 1 hour
- **Documentation**: 30 minutes
- **Total**: 2.5 hours

### Option 2 (LLM Extraction)

- **Implementation**: 2 hours
- **Testing**: 1.5 hours
- **Prompt Engineering**: 1 hour
- **Total**: 4.5 hours

### Option 3 (Unified Workflow)

- **Implementation**: 2 hours
- **Testing**: 1 hour
- **Cleanup**: 1 hour
- **Total**: 4 hours

---

## Contact Context

**Discovered By**: User query on October 16, 2025  
**Original Question**: "Why does query show `[1] tmpgo9yz6nu.pdf` instead of RFP number?"  
**Root Cause Identified**: Python `tempfile.NamedTemporaryFile` in upload endpoints destroys original filenames before LightRAG storage  
**Documented By**: GitHub Copilot analysis of RAG-Anything and LightRAG source code

---

## Appendix: Code Archaeology

### Why `uploaded/` Folder Was Never Used

**Evidence from Codebase**:

1. **`config.py` line 38**: Sets `INPUT_DIR = "./inputs/uploaded"` (default)
2. **Upload Endpoints**: Never reference `INPUT_DIR` or write to it
3. **Physical Filesystem**: `list_dir("inputs/")` returns only `__enqueued__/` subfolder
4. **.gitignore**: Patterns for both folders suggest planned infrastructure

**Hypothesis**: Original design intended document scanning workflow (like LightRAG's `DocumentManager.scan_directory_for_new_files()`), but implementation evolved to use `tempfile` approach instead. Config reference became orphaned.

**Decision**: Don't create `uploaded/` folder - it's unnecessary with direct processing pattern. Either remove config reference or document as unused.

---

**Status**: Ready for implementation when prioritized.  
**Last Updated**: October 16, 2025  
**Next Step**: Create branch `006-human-readable-document-references` and implement Option 1.
