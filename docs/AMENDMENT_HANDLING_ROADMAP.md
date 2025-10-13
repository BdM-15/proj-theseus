# Amendment Handling Roadmap

**Status**: DEFERRED - Future Branch (Branch 006 or later)  
**Estimated Effort**: 8-12 hours (full implementation + testing)  
**Priority**: HIGH (core capture management workflow)  
**Last Updated**: October 12, 2025

---

## Executive Summary

Federal RFPs are frequently amended during the open solicitation period. Capture managers need to:

1. Upload amendments **incrementally** as they arrive (not batch processing)
2. Immediately identify **what changed** (added/modified/removed entities)
3. Query **cumulative changes** across multiple amendments
4. Track **historical state** (what was the RFP before Amendment 0002?)
5. Generate **impact assessments** for proposal teams (page limits, requirements, evaluation factors)

**Current State**: System processes single RFP documents. No amendment detection or delta tracking.

**Future State**: Incremental knowledge graph updates with change metadata, historical versioning, and amendment-specific queries.

---

## Real-World Workflow (User Requirements)

### Iterative Upload Process

```
Day 1:   RFP baseline released
         → Upload baseline.pdf
         → Knowledge graph v1.0 created (594 entities)

Day 15:  Amendment 0001 arrives (10 pages, changes to Section L/M)
         → Upload amendment_0001.pdf
         → Knowledge graph v1.1 (597 entities: 3 added, 5 modified, 2 removed)
         → Query: "What changed in Amendment 0001?"

Day 30:  Amendment 0002 arrives (5 pages, new attachment J-06)
         → Upload amendment_0002.pdf
         → Knowledge graph v1.2 (605 entities: 8 added, 3 modified, 0 removed)
         → Query: "Compare baseline to Amendment 0002"

Day 45:  Proposal submission (using latest knowledge graph state)
```

**Critical Requirements**:

- ✅ **Never reprocess baseline** - Only process amendment documents
- ✅ **Preserve history** - Don't delete superseded entities (mark as removed/superseded)
- ✅ **Immediate results** - Amendment analysis within 5-10 minutes of upload
- ✅ **Cumulative queries** - Show all changes from baseline through latest amendment

---

## Design Decisions (Captured During Research)

### Amendment Document Structures (Need Clarification)

**Question**: What format do amendments typically arrive in?

Options:

1. **Delta document** - Only changed pages (e.g., "Replace page 42 with attached page 42")
2. **Redline document** - Full RFP with strikethrough/underline markup
3. **Amendment text + attachments** - Separate "what changed" text + replacement documents

**Impact**: Affects entity extraction strategy (extract from delta vs compare full documents)

---

### Storage Strategy (Need Decision)

**Question**: How should we store knowledge graph versions?

Options:

**Option A: Single Graph (Continuously Updated)**

```
./rag_storage/
  ├── graph_chunk_entity_relation.graphml  (always latest state)
  └── metadata.json (amendment timeline)
```

- ✅ Simpler file management
- ✅ LightRAG WebUI always shows current state
- ❌ No historical snapshots (unless we add versioning layer)

**Option B: Snapshot Per Amendment**

```
./rag_storage/
  ├── baseline/
  │   └── graph_chunk_entity_relation.graphml (v1.0)
  ├── amendment_0001/
  │   └── graph_chunk_entity_relation.graphml (v1.1)
  ├── amendment_0002/
  │   └── graph_chunk_entity_relation.graphml (v1.2)
  └── current -> amendment_0002/  (symlink to latest)
```

- ✅ Full historical snapshots (easy rollback)
- ✅ Can diff any two versions
- ❌ More complex file management
- ❌ Storage overhead (though graphs are small ~10MB)

**Option C: Hybrid (Recommended)**

```
./rag_storage/
  ├── graph_chunk_entity_relation.graphml  (current state with metadata)
  └── snapshots/
      ├── v1.0_baseline_2025-01-01.graphml
      ├── v1.1_amd001_2025-01-15.graphml
      └── v1.2_amd002_2025-01-30.graphml
```

- ✅ Current graph for queries (fast)
- ✅ Historical snapshots for rollback (safety)
- ✅ Metadata tags enable historical queries without loading snapshots

**Recommendation**: Start with Option A (single graph), add snapshots if needed later.

---

### Query Default Behavior (Need Decision)

**Question**: When user queries without specifying amendment version, what should we return?

**Scenario**: User asks "What are the requirements for technical approach?"

**Option A: Latest Version Only (Recommended)**

- Returns: Entities where `metadata["status"] != "REMOVED"` AND NOT `metadata["superseded_by"]`
- Use Case: Active proposal development (team needs current requirements only)

**Option B: All Versions**

- Returns: All entities including superseded/removed (with version tags)
- Use Case: Historical analysis, compliance auditing

**Option C: User Preference (Setting)**

- Allow user to toggle default behavior in UI/config
- Use Case: Flexibility for different use cases

**Recommendation**: Default to Option A (latest only), add explicit query syntax for historical versions:

- `"What are the requirements?"` → Latest only
- `"What are the requirements in baseline?"` → Pre-amendment state
- `"Show requirement REQ-089 history"` → All versions with SUPERSEDES chain

---

### Amendment Detection Patterns

**Filename Patterns** (Regex):

```python
patterns = [
    r"amendment[_\s-]*(\d+)",       # "Amendment 0001", "Amendment_01"
    r"amd[_\s-]*(\d+)",              # "AMD1", "AMD-001"
    r"modification[_\s-]*(\d+)",     # "Modification 0002"
    r"mod[_\s-]*(\d+)",              # "MOD1", "MOD-02"
    r"change[_\s-]*(\d+)",           # "Change 01"
    r"revision[_\s-]*(\d+)",         # "Revision 3"
    r"amend[_\s-]*(\d+)",            # "Amend1"
]
```

**Content Patterns** (First 5 pages):

```python
content_patterns = [
    "AMENDMENT TO SOLICITATION",
    "This amendment is issued to",
    "The following changes are made",
    "All other terms and conditions remain unchanged",
]
```

**Confidence Scoring**:

- Filename + content match: 95% confidence
- Filename only: 75% confidence
- Content only: 60% confidence
- Manual override: Allow user to force amendment mode

---

## Implementation Plan (8-12 Hours)

### Phase 1: Amendment Detection (2 hours)

**File**: `src/ingestion/amendment_detector.py`

```python
def detect_amendment_info(file_path: str) -> dict:
    """Detect if uploaded document is an amendment"""
    return {
        "is_amendment": bool,
        "amendment_number": str,  # "0001", "0002", etc.
        "confidence": float,      # 0.0-1.0
        "detection_method": str   # "filename", "content", "both"
    }
```

**Tests**: Create sample files with various naming conventions, verify detection accuracy.

---

### Phase 2: LLM-Powered Change Detection (3 hours)

**File**: `prompts/relationship_inference/amendment_comparison.md`

**Prompt Template**:

```markdown
# Amendment Change Detection Prompt

Compare baseline entities to amendment entities. Identify:

1. ADDED: New entities in amendment not in baseline
2. MODIFIED: Entities with same name but different content
3. REMOVED: Baseline entities not in amendment (implied removal)

Output Format:
change|ADDED|entity_id|entity_name|entity_type|reasoning
change|MODIFIED|old_entity_id|new_entity_id|change_description|reasoning
change|REMOVED|entity_id|entity_name|reasoning
```

**File**: `src/inference/amendment_integration.py`

```python
async def detect_entity_changes(
    baseline_entities: list,
    amendment_entities: list,
    llm_func
) -> list[Change]:
    """Use LLM to semantically compare entities"""
    # Build context with both entity sets
    # Call LLM with comparison prompt
    # Parse structured output
    # Return Change objects
```

---

### Phase 3: Knowledge Graph Merge (3 hours)

**File**: `src/inference/amendment_integration.py`

```python
async def integrate_amendment_into_graph(
    baseline_graph: GraphML,
    amendment_entities: list,
    amendment_metadata: dict,
    llm_func
) -> GraphML:
    """Merge amendment entities with change tracking"""

    # 1. Detect changes (Phase 2)
    changes = await detect_entity_changes(...)

    # 2. Apply changes with metadata tagging
    for change in changes:
        if change.type == "ADDED":
            entity.metadata["added_by"] = amendment_metadata["amendment_number"]
            baseline_graph.add_entity(entity)

        elif change.type == "MODIFIED":
            old_entity.metadata["superseded_by"] = amendment_metadata["amendment_number"]
            new_entity.metadata["supersedes"] = old_entity.id
            baseline_graph.add_entity(new_entity)
            baseline_graph.add_relationship(new_entity, old_entity, "SUPERSEDES")

        elif change.type == "REMOVED":
            entity.metadata["removed_by"] = amendment_metadata["amendment_number"]
            entity.metadata["status"] = "REMOVED"

    # 3. Save updated graph
    baseline_graph.save()
    return baseline_graph
```

---

### Phase 4: Enhanced Queries (2 hours)

**File**: `src/server/query_handler.py`

**Add Metadata Filtering**:

```python
def filter_by_version(entities: list, version_filter: str = "latest") -> list:
    """Filter entities by amendment version"""

    if version_filter == "latest":
        # Exclude superseded and removed entities
        return [e for e in entities
                if e.metadata.get("status") != "REMOVED"
                and "superseded_by" not in e.metadata]

    elif version_filter == "baseline":
        # Only entities from baseline (no added_by metadata)
        return [e for e in entities
                if "added_by" not in e.metadata]

    elif version_filter.startswith("amd"):
        # Entities up to specific amendment
        amd_num = extract_amendment_number(version_filter)
        return filter_by_amendment_number(entities, amd_num)

    else:
        # Return all (including superseded)
        return entities
```

**Query Enhancements**:

```python
# "What changed in Amendment 0001?"
# Returns: Entities where metadata["added_by"] == "0001" OR metadata["modified_by"] == "0001"

# "Show requirement REQ-089 history"
# Returns: Chain of entities linked by SUPERSEDES relationships

# "What was the state before Amendment 0002?"
# Returns: Entities filtered by filter_by_version("amd0001")
```

---

### Phase 5: Testing & Validation (2 hours)

**Test Cases**:

1. **Baseline Processing**

   - Upload Navy MBOS RFP baseline
   - Verify 594 entities extracted
   - No amendment metadata present

2. **Amendment 0001 Upload**

   - Create synthetic amendment (modify Section L page limits)
   - Upload amendment
   - Verify: Detection (is_amendment=True), change detection (3 MODIFIED entities), merge (597 total entities)

3. **Amendment 0002 Upload**

   - Create synthetic amendment (add new attachment J-06)
   - Upload amendment
   - Verify: Cumulative changes (baseline → AMD 0001 → AMD 0002)

4. **Query Testing**

   - "What changed in Amendment 0001?" → Returns 3 modified entities
   - "Show all requirements" → Returns latest version only (excludes superseded)
   - "Show requirement REQ-042 history" → Returns SUPERSEDES chain

5. **Edge Cases**
   - Upload non-amendment after baseline → No changes applied
   - Upload amendment without baseline → Error (no baseline to merge into)
   - Upload out-of-order amendments → Warning (AMD 0002 before AMD 0001)

---

## Integration Points

### Existing Code to Modify

1. **`src/server/endpoints.py`** - `/insert` endpoint

   - Add amendment detection before processing
   - Load existing graph if amendment detected
   - Call amendment_integration.py after entity extraction

2. **`src/raganything_server.py`** - Custom `/insert` endpoint

   - Hook amendment detector into Phase 6 pipeline
   - Pass amendment metadata to post-processing

3. **`prompts/user_queries/capture_manager_prompts.md`**
   - ✅ Already added Category 10: Amendment & Change Analysis (5 query examples)
   - No further changes needed

---

## Category 10 Queries (Already Implemented)

The following amendment queries were added to `capture_manager_prompts.md` on October 12, 2025:

1. **Amendment Summary** - "What changed in Amendment [NUMBER]?"
2. **Baseline vs Latest Comparison** - "Compare baseline to Amendment [NUMBER]"
3. **Proposal Impact Analysis** - "How does Amendment [NUMBER] affect our proposal?"
4. **Attachment Change Detection** - "Compare Attachment [ID] between baseline and Amendment [NUMBER]"
5. **Q&A Generation** - "What questions should we ask based on Amendment [NUMBER]?"

These queries provide output templates for the amendment feature to target when generating responses.

---

## Cost Estimates

| Operation                       | LLM Calls   | Estimated Cost | Duration       |
| ------------------------------- | ----------- | -------------- | -------------- |
| Baseline processing             | 32 parallel | $0.042         | 69 seconds     |
| Amendment processing (10 pages) | 5 parallel  | $0.008         | 15 seconds     |
| LLM change detection            | 1 call      | $0.015         | 10 seconds     |
| **Total per amendment**         | **6 calls** | **$0.023**     | **25 seconds** |

**Cumulative Cost for 3 Amendments**:

- Baseline: $0.042
- AMD 0001: $0.023
- AMD 0002: $0.023
- AMD 0003: $0.023
- **Total: $0.111** (vs $0.168 if reprocessing baseline each time - **34% savings**)

---

## Open Questions (Need User Input)

### Critical Questions

1. **Amendment Document Format**

   - Do amendments include only changed pages (delta) or full document with redlines?
   - Are attachments included in amendment PDF or uploaded separately?

2. **Storage Strategy**

   - Single graph (continuously updated) or snapshots per amendment?
   - How long to retain historical snapshots?

3. **Query Defaults**
   - Default to "latest version only" or "all versions including superseded"?
   - Should queries show amendment provenance by default? (e.g., "REQ-089 (added by AMD 0001)")

### Nice-to-Have Questions

4. **Amendment Urgency**

   - How fast do you need amendment analysis? (Immediate vs can wait 10 minutes)
   - Should we send notifications when amendment processing completes?

5. **Rollback Capability**

   - Do you ever need to "undo" an amendment and revert to previous state?
   - Should WebUI show "time travel" slider to view graph at any amendment version?

6. **Multi-File Amendments**
   - Do amendments ever come as multiple files (amendment text + replacement attachments)?
   - Should we support bulk upload for amendment packages?

---

## Success Metrics

### Must-Have (MVP)

- ✅ Detect amendments with 90%+ accuracy (filename + content patterns)
- ✅ Process amendment in <60 seconds (vs 69 seconds for full baseline)
- ✅ Identify ADDED/MODIFIED/REMOVED entities with 85%+ accuracy (LLM comparison)
- ✅ Query "What changed in Amendment X?" returns structured diff
- ✅ Cost per amendment <$0.03 (40% cheaper than reprocessing baseline)

### Nice-to-Have (Future Enhancements)

- 🎯 Historical queries ("Show state before Amendment 0002")
- 🎯 Amendment impact scoring (High/Medium/Low priority changes)
- 🎯 Automated Q&A generation (ambiguous changes trigger questions)
- 🎯 Attachment-level change detection (compare J-02 PWS v1 vs v2)
- 🎯 Visual diff in WebUI (side-by-side baseline vs amendment)

---

## Branch Strategy

**Recommended Branch**: `006-amendment-handling` (or later)

**Prerequisites**:

- ✅ Branch 005 complete (MinerU optimization, prompt modularization)
- ✅ Task 5 complete (UCF redundancy test, code optimization)
- ⏱️ Dedicated 8-12 hour development window (focused work, no interruptions)

**Development Phases**:

1. Create `006-amendment-handling` branch from latest `main`
2. Implement Phase 1-3 (detection + comparison + merge) - 6 hours
3. Test with synthetic amendments - 2 hours
4. Implement Phase 4 (enhanced queries) - 2 hours
5. Integration testing with real RFP + amendments - 2 hours
6. PR to `main` with comprehensive testing results

**Merge Criteria**:

- All 5 test cases pass
- Cost per amendment <$0.03
- Processing time <60 seconds
- No regression in baseline processing (still 69 seconds)

---

## Related Documents

- **Amendment Queries**: `prompts/user_queries/capture_manager_prompts.md` (Category 10)
- **Architecture**: `docs/ARCHITECTURE.md` (will need amendment section)
- **Copilot Instructions**: `.github/copilot-instructions.md` (will need workflow update)

---

## Notes

- **Date Created**: October 12, 2025
- **Research Source**: Conversation about iterative amendment workflow
- **User Requirement**: "We will get an RFP and process it, then get amendments one at a time and upload them to update the knowledge graph"
- **Deferred Reason**: Amendment handling is major feature requiring dedicated focus (not part of Task 5)

---

**Status**: READY FOR IMPLEMENTATION (all research complete, detailed plan available)  
**Next Step**: Create Branch 006 when ready for focused development session
