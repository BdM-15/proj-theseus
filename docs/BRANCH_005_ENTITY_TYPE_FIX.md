# Branch 005: Entity Type Quality Fix

**Created**: October 10, 2025  
**Branch**: `005-entity-type-quality-fix`  
**Parent**: `main` (commit 02153bb - logging cleanup)  
**Status**: Investigation & Planning Phase

---

## Problem Statement

### Observed Symptoms (MCPP RFP Processing)

Processing the MCPP RFP generates **hundreds of warnings** during entity extraction:

```
WARNING: Entity extraction error: invalid entity type in: ['entity', 'CDRL 6023', '#|DELIVERABLE', ...]
WARNING: Entity extraction error: invalid entity type in: ['entity', 'Risk Control Plan (RCP)', '#/>SECTION', ...]
WARNING: Entity extraction error: invalid entity type in: ['entity', 'NAVSEA Publication S6430-AE-TED-010', '#/>DOCUMENT', ...]
WARNING:src.utils.entity_cleanup:Skipping invalid entity 'Fire Wardens' with type 'OTHER' (not in valid_types)
WARNING:src.utils.entity_cleanup:Skipping invalid entity '10.C.5' with type '#SECTION' (not in valid_types)
WARNING:src.utils.entity_cleanup:Skipping invalid entity 'Navy Technical Methodology', '#>|SECTION', ...]
```

**Impact**: Valid entities are being **rejected and lost** from the knowledge graph due to malformed type names.

### Root Causes Identified

1. **Negative Example Confusion**: The extraction prompt includes "❌ WRONG EXAMPLES" showing malformed patterns like `#/>CONCEPT` that LLMs sometimes copy instead of avoiding

2. **Type Format Corruption**: LLM (Grok-4-fast-reasoning) adds special characters:
   - `#/>CONCEPT` instead of `CONCEPT`
   - `#>|DOCUMENT` instead of `DOCUMENT`
   - `#|SECTION` instead of `SECTION`
   - `#technology` instead of `TECHNOLOGY`

3. **Invalid Fallback Types**: LLM uses non-existent types:
   - `other` / `OTHER` (not in valid entity list)
   - `UNKNOWN` (not in valid entity list)
   - Lowercase variants (`#section` vs `SECTION`)

4. **Cleanup Timing Issue**: Entity cleanup (`src/utils/entity_cleanup.py`) runs AFTER extraction in Phase 6 post-processing, but invalid entities are already rejected during initial extraction, so they never reach the cleanup step.

### Current Architecture

```
[Text Extraction] → [Entity Extraction with Prompt] → [Validation] → [Graph Storage]
                                                           ↓
                                                    [REJECT Invalid] ← Lost forever!
                                                           
[Phase 6 Post-Processing] → [Entity Cleanup] ← Too late! Invalid entities already gone
```

**The Problem**: Cleanup happens AFTER rejection, not BEFORE validation.

---

## Quality Impact Assessment

### Baseline (Navy MBOS - Working)
- **Entities**: 4,302 total
- **Relationships**: 5,715 total
- **Warnings**: Minimal (~10 format warnings)
- **Success Rate**: 99%+

### Regression (MCPP RFP - Current)
- **Entities**: 2,794 total (likely undercounted due to rejections)
- **Warnings**: **90+ invalid entity warnings** during extraction
- **Lost Entities**: Unknown count (rejected before reaching graph)
- **Success Rate**: Estimated 85-90% (10-15% loss)

**Estimated Impact**: 10-15% of valid government contracting entities (requirements, clauses, deliverables) are being lost due to type format corruption.

---

## Solution Strategy

### Option A: Simplify Prompt (RECOMMENDED)

**Philosophy**: Remove complexity that confuses the LLM. Show ONLY correct patterns.

**Changes**:
1. **Remove "❌ WRONG EXAMPLES" section** - Stop showing malformed patterns
2. **Strengthen positive examples** - Add 3-5 more correct entity examples
3. **Add explicit type list** - Show all 19 valid types in prompt header
4. **Simplify instructions** - Remove delimiter explanation complexity

**Implementation** (`src/server/initialization.py`):
- Lines 177-213: Delete "❌ WRONG EXAMPLES (LEARN FROM THESE MISTAKES)" section
- Lines 195-209: Expand "✅ CORRECT EXAMPLES" from 9 to 15+ examples
- Lines 145-170: Add explicit valid entity type list at prompt start

**Expected Outcome**: 95%+ correct entity types on first extraction (no cleanup needed)

**Risk**: Low - Reduces prompt complexity, aligns with best practices

### Option B: Pre-Extraction Cleanup (FALLBACK)

**Philosophy**: Accept LLM will make mistakes, intercept and fix before validation.

**Changes**:
1. Hook into LightRAG extraction pipeline before validation
2. Apply `clean_entity_type()` to all extracted entities
3. Log corrections for monitoring

**Implementation**:
- Modify RAG-Anything/LightRAG callback (requires library customization)
- OR: Post-process extraction results before graph insert

**Expected Outcome**: 100% entity retention (all entities cleaned and saved)

**Risk**: Medium - Adds complexity, masks underlying prompt issues

### Option C: Hybrid Approach

**Philosophy**: Fix prompt first, add cleanup safety net second.

**Implementation**:
1. Apply Option A changes to prompt
2. Add lightweight pre-validation cleanup hook
3. Monitor which approach catches more errors

**Expected Outcome**: Best of both worlds (prompt quality + safety net)

**Risk**: Low-Medium - More code to maintain

---

## Decision Criteria

**Choose Option A** if:
- Prompt simplification reduces warnings to <5% of entities
- Navy MBOS and MCPP RFP both achieve 95%+ correct types
- Processing time and cost remain stable

**Choose Option B** if:
- Option A fails to reduce warnings below 10%
- LLM continues generating malformed types despite prompt fixes
- Need 100% entity retention guarantee

**Choose Option C** if:
- Option A achieves 90-95% (good but not great)
- Want production safety net for edge cases
- Acceptable to add modest complexity

---

## Validation Plan (30 Minutes)

### Phase 1: Prompt Simplification (15 minutes)

1. **Backup current prompt** (copy lines 137-270 to temp file)
2. **Apply Option A changes** to `src/server/initialization.py`
3. **Restart server** with simplified prompt
4. **Re-process MCPP RFP** (clear `rag_storage/` first)
5. **Count warnings**: `cat app.log | grep "WARNING:" | wc -l`

**Success Criteria**: <20 warnings (down from 90+)

### Phase 2: Comparative Analysis (10 minutes)

1. **Check entity count**: Should match or exceed 2,794 baseline
2. **Check relationship count**: Should match or exceed 2,377 baseline  
3. **Spot-check entities**: Verify DELIVERABLE, REQUIREMENT, CLAUSE entities present
4. **Query quality test**: Run 3 test queries in WebUI (e.g., "What are the key deliverables?")

**Success Criteria**: 
- Entity count ≥ 2,794 (no loss)
- Query answers include section references and specific requirements
- No "entity not found" errors

### Phase 3: Regression Testing (5 minutes)

1. **Process Navy MBOS** (known good baseline)
2. **Verify 4,302 entities** (no regression)
3. **Compare warning count** (should remain low)

**Success Criteria**: Navy MBOS unaffected by prompt changes

---

## Implementation Checklist

### Pre-Work
- [ ] Create branch `005-entity-type-quality-fix` ✅ (DONE)
- [ ] Document problem and strategy (this file) ✅ (DONE)
- [ ] Clear `rag_storage/` to start fresh
- [ ] Save backup of current extraction prompt

### Option A Changes
- [ ] Remove "❌ WRONG EXAMPLES" section (lines 211-213)
- [ ] Expand "✅ CORRECT EXAMPLES" to 15+ entity examples
- [ ] Add explicit valid entity type list in prompt header
- [ ] Simplify delimiter rules section (remove redundancy)
- [ ] Remove references to malformed patterns in comments

### Testing
- [ ] Restart server with new prompt
- [ ] Process MCPP RFP, count warnings
- [ ] Compare entity/relationship counts to baseline
- [ ] Test 3-5 queries in WebUI for quality
- [ ] Process Navy MBOS for regression check

### Decision
- [ ] IF warnings <5%: Commit Option A, merge to main
- [ ] IF warnings 5-10%: Implement Option B safety net
- [ ] IF warnings >10%: Escalate for deeper LLM investigation

### Completion
- [ ] Document final metrics in `BRANCH_005_COMPLETION.md`
- [ ] Update `HANDOFF_SUMMARY.md` with fix details
- [ ] Commit changes with detailed message
- [ ] Merge to main after validation

---

## Key Insights

1. **Prompt Engineering Anti-Pattern**: Showing "wrong examples" to teach avoidance can backfire with LLMs that pattern-match rather than reason

2. **Validation Timing Matters**: Cleanup must happen BEFORE validation rejects entities, not after

3. **Complexity ≠ Quality**: The current 133-line extraction prompt with nested rules may be overwhelming the LLM. Simpler prompts often perform better.

4. **Safety Nets Have Costs**: Entity cleanup adds defensive code complexity but masks root cause (prompt issues)

---

## Success Metrics

**Before Fix** (MCPP RFP):
- Warnings: 90+ invalid entity types
- Entity Loss: 10-15% estimated
- Types Affected: DELIVERABLE, SECTION, DOCUMENT, REQUIREMENT

**Target** (Option A):
- Warnings: <10 invalid entity types (<1% of total)
- Entity Loss: 0%
- Extraction Success Rate: 95%+

**Ideal** (Option C with safety net):
- Warnings: 0 (all caught and corrected)
- Entity Loss: 0%
- Extraction Success Rate: 100%

---

## Next Steps

1. **User Decision**: Which option to pursue?
   - Option A: Simplify prompt (fast, low risk)
   - Option B: Add cleanup hook (safety net, more complex)
   - Option C: Hybrid (both)

2. **Implementation**: Apply selected option changes

3. **Validation**: Run 30-minute test plan

4. **Iterate or Merge**: Based on results

---

**Charter**: Fix entity type extraction quality regression without adding unnecessary complexity. Prioritize prompt simplification over defensive cleanup code. Validate against both MCPP RFP (problem case) and Navy MBOS (known good baseline).
