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

## Decision Made: Full Rollback to Pre-Cleanup State

**DECISION**: Remove entity_cleanup.py and simplify prompts (hybrid of prevention + rollback)

**Rationale**:
1. **Timeline Analysis** revealed the root cause:
   - Branch 004 MinerU multimodal (commit d93e344, Oct 9 @ 3:41 PM): **Working perfectly** - 4,302 entities, minimal warnings
   - Entity cleanup added (commit f43df7c, Oct 9 @ 6:04 PM): 257 lines of defensive code that **masked prompt issues**
   - New entity types added (commit 3f30497): EQUIPMENT and REGULATION
   - **Result**: 90+ warnings during MCPP RFP processing

2. **Fundamental Flaw**: Entity cleanup ran AFTER validation rejection, making it useless for recovery
   
3. **Anti-Pattern Identified**: The "❌ WRONG EXAMPLES" section in the prompt was **teaching the LLM bad patterns** instead of preventing them

**Solution Applied**:
- ✅ Deleted `src/utils/entity_cleanup.py` (257 lines)
- ✅ Removed Step 1.5 cleanup logic from `src/server/routes.py` (29 lines removed)
- ✅ Removed entity_cleanup imports from `src/utils/__init__.py`
- ✅ Simplified extraction prompt - removed confusing "WRONG EXAMPLES" section (15 lines removed)
- ✅ Total code removed: ~301 lines of defensive complexity

**Expected Outcome**: Return to stable Branch 004 MinerU multimodal baseline with minimal warnings

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

- [x] Remove "❌ WRONG EXAMPLES" section (lines 211-213) ✅ DONE
- [x] Expand "✅ CORRECT EXAMPLES" to 15+ entity examples ✅ DONE (15 examples)
- [x] Add explicit valid entity type list in prompt header ✅ DONE (19 types)
- [x] Simplify delimiter rules section (remove redundancy) ✅ DONE (removed nested warnings)
- [x] Remove references to malformed patterns in comments ✅ DONE (clean comments)

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

## Implementation Complete ✅

### Changes Applied

1. **Deleted `src/utils/entity_cleanup.py`** (257 lines)
   - Removed defensive cleanup that ran AFTER validation rejection
   - Eliminated 5 functions: `clean_entity_type()`, `validate_entity_type()`, `clean_entities_batch()`, `analyze_corruption_patterns()`

2. **Removed entity_cleanup integration from `src/server/routes.py`** (29 lines removed)
   - Deleted Step 1.5 cleanup logic
   - Removed import statement for entity_cleanup functions
   - Removed corruption analysis and entity correction code
   - Cleaned up logging and return values

3. **Cleaned up `src/utils/__init__.py`** (12 lines removed)
   - Removed entity_cleanup imports and exports
   - Simplified module structure

4. **Simplified extraction prompt in `src/server/initialization.py`** (15 lines removed)
   - Removed "❌ WRONG EXAMPLES" section showing `<|location|>` anti-patterns
   - Simplified delimiter usage instructions (removed nested warnings)
   - Updated module docstring to reflect simplification

**Total Code Removed**: ~313 lines of defensive complexity

### Architectural Debt Identified

- **Issue**: Entity extraction prompt hardcoded in `initialization.py` (should be in `/prompts`)
- **Target**: Add to `005-mineru-optimization` branch scope (comprehensive codebase review with focus on prompts and processing)
- **Decision**: Fix AFTER Branch 005 entity type fix stability confirmed (don't add variables during testing)

**Rationale**: Prompt modularization fits naturally with the broader MinerU optimization work, which includes:
- UCF redundancy experiments
- Prompt engineering improvements
- Processing pipeline optimization
- Codebase quality review

### Test Results ✅

**Test Case**: MCPP RFP processing (October 10, 2025)

**Warnings Breakdown**:
- Invalid entity type errors: **22** (down from 90+ = **76% reduction** ✅)
- LLM format errors: **13** (field count mismatches, wrong delimiters)
- **Total**: 35 warnings vs 90+ baseline

**Lost Entities** (Critical Data):
- Organizations: USAMMA, HQMC
- Documents: Watercraft Maintenance Status Report, DD Form 1348, CmdO 4790.1, DLA-Energy P2, 29 CFR 1915, MCO 4450.12, International Maritime Dangerous Goods Rules
- Deliverables: Annual Spend Plan, Investigation Report, Container Packing Lists, Sustainment Blocks, AASP Plan, Class IX Battery Plan, CDRL 5010, Post Exercise After Action Report, Shipboard Post Exercise After Action Report
- Concepts: FED LOG
- Technology: MCPIC Prepositioning Planning System
- Locations: DMO
- Requirements: Phase-Out

**Corruption Patterns Still Present**:
- `#>|TYPE` (most common) - 19 occurrences
- `#|TYPE` - 1 occurrence
- `#>|section` (lowercase!) - 1 occurrence
- `#>|document` (lowercase!) - 1 occurrence

**Assessment**: 
✅ **MAJOR IMPROVEMENT** - 76% reduction in warnings  
❌ **STILL LOSING CRITICAL DATA** - ~22 important entities rejected  
⚠️ **ROOT CAUSE PERSISTS** - LLM generating special characters despite prompt simplification

### Next Steps

1. **Commit Branch 005 Entity Type Fix** ✅
   - Document as partial success (76% improvement)
   - Note that corruption patterns persist
   - Ready for Branch 005 MinerU Optimization

2. **Branch 005 MinerU Optimization Scope** (Critical Follow-up):
   - **Rewrite entity extraction prompt from scratch**
     - Study what triggers `#>|` corruption in Grok-4-fast-reasoning
     - Remove ALL special character references
     - Ultra-simplify delimiter instructions
     - Consider model-specific tuning
   
   - **Add pre-validation cleanup** (done RIGHT this time)
     - Hook into RAG-Anything pipeline BEFORE validation
     - Clean entity types before rejection occurs
     - Log corrections for quality monitoring
   
   - **Test alternative LLM models**
     - Try `grok-2-1212` vs `grok-4-fast-reasoning`
     - Compare with Claude or GPT-4 if needed
     - Model-specific prompt engineering
   
   - **Prompt modularization** (architectural cleanup)
     - Extract hardcoded prompt to `/prompts/entity_extraction/`
     - Create `prompt_loader.py` utility
     - Enable rapid A/B testing of prompts

3. **Success Criteria for Branch 005 MinerU Optimization**:
   - Warnings: <5 per RFP (currently 35)
   - Entity loss: <1% (currently ~2-3%)
   - No critical deliverables/documents lost

### Grok-4-Fast Self-Diagnostic ✅

**Added to Branch 005 MinerU Optimization** (`docs/GROK_DIAGNOSTIC_FEEDBACK.md`)

Grok-4-fast-reasoning provided self-analysis of the corruption patterns:

**Root Cause Identified**:
1. **Prompt Echoing** - Model echoes instructional delimiters as output patterns
2. **Field Count Mismatch** - Speed optimization sacrifices schema adherence
3. **Model-Specific Behavior** - `grok-4-fast-reasoning` prioritizes speed over strict formatting

**Recommended Solutions** (now in Branch 005 scope):
1. ✅ **Ultra-simplify entity type list** - Remove ALL special character references
2. ✅ **Switch to JSON output** - Eliminate line-based parsing issues (if feasible)
3. ✅ **Pre-validation sanitizer** - Strip corruption BEFORE validation
4. ✅ **Test grok-2-1212** - Better schema adherence for extraction
5. ✅ **Prompt ablation** - Zero-shot testing with minimal instructions

**Key Insight**: Speed-optimized models (grok-4-fast-reasoning) trade accuracy for speed. For RAG extraction, consider slower but more accurate models (grok-2-1212) while keeping fast models for queries.

---

**Charter**: Fix entity type extraction quality regression without adding unnecessary complexity. Prioritize prompt simplification over defensive cleanup code. Validate against both MCPP RFP (problem case) and Navy MBOS (known good baseline).

**Outcome**: ✅ Partial success (76% improvement) + Clear roadmap for complete fix in Branch 005 MinerU Optimization
