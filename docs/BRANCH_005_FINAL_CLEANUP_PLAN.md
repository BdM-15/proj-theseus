# Branch 005 Final Cleanup Plan

**Date**: October 16, 2025  
**Branch**: 005-final-cleanup (sub-branch of 005-mineru-optimization)  
**Goal**: Clean up accumulated artifacts and prepare for branch closure

---

## 🎯 Cleanup Objectives

1. **Archive Root-Level Handoff Documents** → Move to `docs/archive/`
2. **Remove Redundant Files** → Delete duplicates and obsolete scripts
3. **Consolidate Documentation** → Merge overlapping documents
4. **Clean Up Temporary Files** → Remove test outputs and caches
5. **Update README** → Remove outdated references
6. **Final Commit** → Clean branch ready for merge/archival

---

## 📋 Cleanup Checklist

### Phase 1: Archive Root-Level Handoff Documents

**Files to Archive** (move to `docs/archive/`):
- [ ] `BRANCH_004_COMPLETION.md` → Already documented in archive
- [ ] `BRANCH_005_HANDOFF.md` → Initial Branch 005 hypothesis document
- [ ] `BRANCH_005_OPTIMIZATION_HANDOFF.md` → Redundant with HANDOFF
- [ ] `HANDOFF_SUMMARY.md` → Consolidated summary (check if still needed)
- [ ] `MINERU_HANDOFF.md` → MinerU-specific handoff
- [ ] `PROMPT_CENTRALIZATION_SUMMARY.md` → Phase 1 work summary

**Reasoning**: These are historical records useful for archaeology but clutter the root directory.

**Action**:
```bash
git mv BRANCH_004_COMPLETION.md docs/archive/
git mv BRANCH_005_HANDOFF.md docs/archive/
git mv BRANCH_005_OPTIMIZATION_HANDOFF.md docs/archive/
git mv HANDOFF_SUMMARY.md docs/archive/
git mv MINERU_HANDOFF.md docs/archive/
git mv PROMPT_CENTRALIZATION_SUMMARY.md docs/archive/
```

---

### Phase 2: Review Examples Directory

**Current State**:
- `examples/edit_graph_example.py` (43 lines)
- `examples/sample_*.json` (4 files - Shipley output examples)

**Decision Points**:
- [ ] Keep `examples/` for user reference? YES - demonstrates Shipley functionality
- [ ] Move `edit_graph_example.py` to `graph_node_edits/manual/`? (duplicate exists there)

**Recommended Action**:
- DELETE `examples/edit_graph_example.py` (duplicate of `graph_node_edits/manual/edit_graph_example.py`)
- KEEP sample JSON files as Shipley output format reference

```bash
git rm examples/edit_graph_example.py
```

---

### Phase 3: Clean Up __pycache__ and Test Artifacts

**Check for**:
- [ ] `__pycache__/` directories (should be in .gitignore)
- [ ] `rag_storage/tmpXXXXX/` temporary processing directories
- [ ] Test output files in `inputs/__enqueued__/`

**Action**:
```bash
# Remove pycache if accidentally committed
find . -type d -name __pycache__ -exec rm -rf {} +

# Clean up temp rag_storage directories (manual check first)
# ls -la rag_storage/
# rm -rf rag_storage/tmp*

# Verify .gitignore covers these patterns
```

---

### Phase 4: Consolidate Branch Documentation

**Current Branch 005 Documents**:
1. `docs/BRANCH_005_ENTITY_TYPE_FIX.md` (151 lines) - Entity type consolidation work
2. `docs/archive/BRANCH_005_HANDOFF.md` (after move)
3. `docs/archive/BRANCH_005_OPTIMIZATION_HANDOFF.md` (after move)

**Recommendation**: 
- KEEP `BRANCH_005_ENTITY_TYPE_FIX.md` in main `docs/` (technical reference for entity type decisions)
- Archive the others as they're historical handoffs

**No Action Needed** - already addressed in Phase 1

---

### Phase 5: Review prompts/ Directory Structure

**Current Structure**:
```
prompts/
├── entity_extraction/
│   ├── entity_detection_rules.md (1,075 lines) ✅
│   ├── entity_extraction_prompt.md (134 lines) ✅
│   ├── metadata_extraction.md (82 lines) ✅
│   └── section_normalization.md (67 lines) ✅
├── relationship_inference/
│   ├── attachment_section_linking.md (201 lines) ✅
│   ├── clause_clustering.md (186 lines) ✅
│   ├── document_hierarchy.md (199 lines) ✅
│   ├── document_section_linking.md (224 lines) ✅
│   ├── requirement_evaluation.md (216 lines) ✅
│   ├── section_l_m_linking.md (234 lines) ✅
│   ├── section_l_m_mapping.md (157 lines) ✅
│   ├── semantic_concept_linking.md (166 lines) ✅
│   ├── sow_deliverable_linking.md (165 lines) ✅
│   └── system_prompt.md (56 lines) ✅
└── user_queries/
    └── capture_manager_prompts.md (728 lines) ✅
```

**Status**: ✅ Clean, well-organized, no action needed

---

### Phase 6: Update README.md References

**Check for Obsolete References**:
- [ ] References to `BRANCH_003_IMPLEMENTATION.md` (archived)
- [ ] References to `BRANCH_004_*` documents (archived)
- [ ] Outdated file paths or moved documents

**Action**: Update README to reflect current documentation structure

---

### Phase 7: Review graph_node_edits/ Directory

**Current Structure**:
```
graph_node_edits/
├── README.md (entry point)
├── MANUAL_EDITING_TOOLS.md (guide)
├── auto_bulk/
│   ├── README.md
│   └── bulk_graph_fixes.py
└── manual/
    ├── README.md
    ├── WEBUI_NODE_EDITING_GUIDE.md
    ├── edit_graph_example.py
    └── interactive_graph_edit.ps1
```

**Decision**: KEEP - useful utilities for graph editing

**Verification**:
- [ ] Check if scripts still work with current codebase
- [ ] Update any outdated imports or paths

---

### Phase 8: Create Branch 005 Completion Summary

**Create**: `docs/BRANCH_005_COMPLETION.md`

**Content**:
- What was accomplished in Branch 005
- Key decisions (document reference naming issue documented)
- Prompt centralization completed
- Post-processing validation completed
- Next steps (Branch 006 documented for future)
- Final metrics (if any)

---

### Phase 9: Final Verification

**Pre-Merge Checks**:
- [ ] Run `python app.py` to verify server starts
- [ ] No broken imports
- [ ] Documentation references are valid
- [ ] .gitignore patterns appropriate
- [ ] No sensitive data committed

**Code Quality**:
- [ ] No unused imports (run pylint if available)
- [ ] No dead code paths
- [ ] Prompt files load correctly via `PromptLoader`

---

## 🗑️ Files to Delete

### Confirmed Deletions:
1. `examples/edit_graph_example.py` - Duplicate of `graph_node_edits/manual/edit_graph_example.py`

### Potential Deletions (Verify First):
- Root `__pycache__/` if present (should be gitignored)
- Any `.pyc` files accidentally committed
- Test RFPs in `inputs/__enqueued__/` (if not needed for testing)

---

## 📁 Files to Move (Git Mv)

### Root → docs/archive/:
1. `BRANCH_004_COMPLETION.md`
2. `BRANCH_005_HANDOFF.md`
3. `BRANCH_005_OPTIMIZATION_HANDOFF.md`
4. `HANDOFF_SUMMARY.md`
5. `MINERU_HANDOFF.md`
6. `PROMPT_CENTRALIZATION_SUMMARY.md`

---

## 📝 Files to Create

### docs/BRANCH_005_COMPLETION.md:
```markdown
# Branch 005 Completion Summary

**Date**: October 9-16, 2025
**Branch**: 005-mineru-optimization
**Status**: ✅ COMPLETE

## What Was Accomplished

1. **Prompt Centralization** (October 9-10)
   - Moved 14 inline prompts to external .md files
   - Created prompts/ directory structure
   - Implemented PromptLoader utility

2. **Post-Processing Validation** (October 15)
   - Verified 299 LLM-inferred relationships working
   - All 5 inference algorithms confirmed functional
   - GraphML integrity validated

3. **Document Reference Naming Issue** (October 16)
   - Discovered tmpXXXXX.pdf reference problem
   - Root cause: tempfile.NamedTemporaryFile in upload endpoints
   - Comprehensive solution documented for Branch 006
   - Decision: Defer to future branch (2.5 hour fix)

## Key Deliverables

- ✅ Prompts externalized and centralized
- ✅ Post-processing working correctly
- ✅ Branch 006 handoff document created
- ✅ Codebase cleaned and organized

## Metrics

- LOC: Minimal change (prompt externalization)
- Processing time: 69s (unchanged)
- Cost: $0.042 (unchanged)
- Code quality: Improved maintainability

## Next Steps

- Branch 006: Human-readable document references
- Consider prompt versioning/testing framework
- Evaluate prompt performance metrics
```

---

## 🔄 Git Workflow

### Step-by-Step Execution:

```bash
# 1. Archive root-level handoff docs
git mv BRANCH_004_COMPLETION.md docs/archive/
git mv BRANCH_005_HANDOFF.md docs/archive/
git mv BRANCH_005_OPTIMIZATION_HANDOFF.md docs/archive/
git mv HANDOFF_SUMMARY.md docs/archive/
git mv MINERU_HANDOFF.md docs/archive/
git mv PROMPT_CENTRALIZATION_SUMMARY.md docs/archive/

# 2. Remove duplicate example file
git rm examples/edit_graph_example.py

# 3. Stage changes
git add -A

# 4. Commit cleanup
git commit -m "chore: final Branch 005 cleanup - archive handoff docs

- Moved 6 root-level handoff documents to docs/archive/
- Removed duplicate edit_graph_example.py from examples/
- Created BRANCH_005_COMPLETION.md summary
- Cleaned up repository structure for branch closure

Branch 005 complete: prompt centralization, post-processing validation,
and Branch 006 document reference fix documented for future work."

# 5. Merge back to parent branch
git checkout 005-mineru-optimization
git merge 005-final-cleanup --no-ff

# 6. Optional: Delete cleanup sub-branch
git branch -d 005-final-cleanup
```

---

## ✅ Success Criteria

Branch cleanup is complete when:

1. ✅ Root directory has only essential files (app.py, pyproject.toml, README.md, .env, .gitignore)
2. ✅ All handoff docs archived in `docs/archive/`
3. ✅ No duplicate files exist
4. ✅ `python app.py` starts successfully
5. ✅ All documentation references are valid
6. ✅ Branch 005 completion summary created
7. ✅ Git history is clean with meaningful commit messages

---

## 📊 Before/After Comparison

### Root Directory Before:
```
app.py
BRANCH_004_COMPLETION.md          ← Archive
BRANCH_005_HANDOFF.md             ← Archive
BRANCH_005_OPTIMIZATION_HANDOFF.md ← Archive
HANDOFF_SUMMARY.md                ← Archive
MINERU_HANDOFF.md                 ← Archive
PROMPT_CENTRALIZATION_SUMMARY.md  ← Archive
pyproject.toml
README.md
.env
.gitignore
docs/
examples/
src/
```

### Root Directory After:
```
app.py
pyproject.toml
README.md
.env
.gitignore
docs/
examples/
src/
```

**Result**: Clean, professional root directory with historical docs preserved in archive.

---

## 🎯 Estimated Time

- Phase 1-2: 15 minutes (git mv commands)
- Phase 3-4: 10 minutes (verification)
- Phase 5-7: 10 minutes (review)
- Phase 8: 20 minutes (create completion doc)
- Phase 9: 15 minutes (testing)

**Total**: ~70 minutes

---

**Status**: Ready to Execute  
**Next Action**: Begin Phase 1 - Archive handoff documents
