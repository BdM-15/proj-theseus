# Codebase Cleanup Plan - Branch 013

## Files to DELETE (Obsolete/Duplicate/Testing)

### Root Directory - Test Scripts (Move to tests/ or delete)

- [ ] `test_neo4j_connection.py` - DELETE (obsolete, replaced by test_neo4j_quick.py)
- [ ] `test_neo4j_detailed.py` - DELETE (obsolete, replaced by tests/test_neo4j_postprocessing.py)
- [ ] `check_neo4j_props.py` - DELETE (was debugging tool, no longer needed)

### Root Directory - Keep but move to tools/

- [ ] `assess_quality.py` - MOVE to `tools/assess_quality.py`
- [ ] `clear_neo4j.py` - MOVE to `tools/clear_neo4j.py`
- [ ] `test_neo4j_quick.py` - KEEP in root (frequently used for quick testing)

### Docs - Archive old documentation

- [ ] `docs/archive/BRANCH_002_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_003_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_004_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_005_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_006_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_008_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_009_*` - KEEP (historical record)
- [ ] `docs/archive/BRANCH_010_*` - KEEP (historical record)

### Docs - Consolidate active docs

- [ ] Review `docs/neo4j/` - Keep essential, archive experimental
- [ ] Review `docs/ontology/` - Consolidate into single reference
- [ ] Review `docs/capture-intelligence/` - Archive if not in use

### Examples Directory

- [ ] `examples/sample_*.json` - KEEP (useful examples)

### Graph Node Edits

- [ ] `graph_node_edits/manual/` - ARCHIVE (manual editing deprecated with automation)
- [ ] `graph_node_edits/auto_bulk/` - ARCHIVE (automation handles this now)
- [ ] `graph_node_edits/neo4j_corrections/` - KEEP (still useful for advanced users)

### Prompts Directory

- [ ] Review `prompts/extraction/` - Consolidate if duplicates exist
- [ ] Review `prompts/relationship_inference/` - Archive historical versions
- [ ] Review `prompts/user_queries/` - Keep only active versions

### Source Code

- [ ] `src/inference/graph_io.py` - KEEP (still used for NetworkX/GraphML path)
- [ ] Review for unused imports across all files
- [ ] Review for commented-out code blocks

---

## Actions to Take

### 1. Create tools/ directory for utilities

```
tools/
  ├── assess_quality.py
  ├── clear_neo4j.py
  └── README.md
```

### 2. Delete obsolete test scripts

```powershell
Remove-Item test_neo4j_connection.py
Remove-Item test_neo4j_detailed.py
Remove-Item check_neo4j_props.py
```

### 3. Archive unused graph editing tools

```powershell
Move-Item graph_node_edits/manual docs/archive/manual_editing_deprecated/
Move-Item graph_node_edits/auto_bulk docs/archive/auto_bulk_deprecated/
```

### 4. Clean up **pycache** directories

```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

### 5. Review and consolidate docs

- Merge similar documents
- Archive experimental approaches
- Keep only production-ready documentation

---

## Files to KEEP (Essential for Production)

### Root

- ✅ `app.py` - Main entry point
- ✅ `test_neo4j_quick.py` - Quick validation tool
- ✅ `.env` / `.env.example` - Configuration
- ✅ `docker-compose.neo4j.yml` - Infrastructure
- ✅ `pyproject.toml` / `uv.lock` - Dependencies
- ✅ `README.md` - Project documentation

### Source Code

- ✅ `src/inference/` - All inference modules
- ✅ `src/server/` - Server components
- ✅ `src/utils/` - Utilities
- ✅ `src/models/` - Data models (if exists)

### Tests

- ✅ `tests/test_neo4j_postprocessing.py` - Comprehensive tests
- ✅ `tests/TEST_SCRIPTS_README.md` - Test documentation
- ✅ `tests/test_user_prompts.py` - Prompt tests

### Documentation (Essential)

- ✅ `docs/neo4j/NEO4J_USER_GUIDE.md`
- ✅ `docs/neo4j/NEO4J_SEMANTIC_POSTPROCESSING.md`
- ✅ `docs/ARCHITECTURE.md`
- ✅ `docs/README.md`

### Prompts (Active)

- ✅ `prompts/extraction/` - Current extraction prompts
- ✅ `prompts/user_queries/` - Query templates
- ✅ `prompts/relationship_inference/` - Current inference prompts

---

## Estimated Impact

**Files to Delete**: ~10-15 files  
**Directories to Archive**: 2-3 directories  
**Space Saved**: ~5-10MB (minimal, mostly cleanup for clarity)  
**Maintenance Benefit**: HIGH (clearer structure, easier navigation)

---

## Priority Order

1. **HIGH**: Delete obsolete test scripts (immediate cleanup)
2. **HIGH**: Create tools/ directory and move utilities
3. **MEDIUM**: Clean **pycache** directories
4. **MEDIUM**: Archive deprecated manual editing tools
5. **LOW**: Consolidate documentation (can be done incrementally)

---

## Next Steps

1. Review this plan
2. Execute deletions (with git safety)
3. Create tools/ directory structure
4. Update README.md to reflect new structure
5. Commit cleanup changes
