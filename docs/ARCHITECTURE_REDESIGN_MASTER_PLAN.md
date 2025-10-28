# Architecture Redesign Master Plan: Blank Slate + Proven Content

**Objective**: Keep NEW architecture structure, replace ALL content with OLD proven patterns

**Philosophy**: Don't retrofit old prompts into new structure. Keep skeleton, gut the interior, rebuild with premium materials that worked.

**Status**: STEP 1 of 6 COMPLETE ✅

---

## Vision: The "Whittle the Wood" Approach

**What we're keeping** (NEW architecture structure):
- Directory organization: `prompts/extraction/` (4 files) + `prompts/relationship_inference/` (9 files)
- Execution flow: Phase 1 (entity extraction) → Phase 2 (relationship inference)
- Ontology framework: 17 entity types, 13 relationship types
- Two-phase separation: Foundation building (extraction) → Decision making (query)

**What we're replacing** (content with OLD proven patterns):
- Every prompt content, rule, example, algorithm
- Detection logic, inference patterns, domain knowledge
- Examples, decision trees, confidence thresholds
- Quality standards, enrichment patterns, relationship inference

**Why this works**:
- Test 4: New content failed catastrophically (873 relationship types, 9 strategic themes)
- Test 5: Enhanced content partially improved (strategic themes 21 ✅, but UNKNOWN 24 ✗)
- Root cause: New architecture is good, but content never matched proven patterns
- Solution: Replace content entirely with what we know works (old prompts) while keeping organizational structure that works (new architecture)

---

## The Six-Step Implementation Plan

### ✅ STEP 1: Entity Detection Rules (COMPLETE)
**File**: `prompts/extraction/3_entity_specifications.md`  
**Content swapped from**: `entity_detection_rules.md` (attached)  
**What changed**:
- Old approach: Abstract entity type definitions
- New approach: Semantic-first detection, UCF patterns, agency variations, 17-type decision tree
- Size: ~2,700 lines of detection algorithms, examples, disambiguation rules
- Backup: `3_entity_specifications.md.bak` (recovery if needed)
- **Commit**: `1203a1a` - "Architecture Redesign Step 1"

---

### STEP 2: Entity Extraction Patterns (NEXT)
**File**: `prompts/extraction/2_execution_framework.md`  
**Content to swap from**: `entity_extraction_prompt.md` (attached)  
**What will change**:
- Current: Generic extraction framework with 5-step process
- New: 5 annotated RFP examples (Section L↔M, requirements, clauses, annexes, deliverables)
- New: 8-decision disambiguation tree for edge cases
- New: Topic taxonomy (6 categories) for semantic cross-referencing
- New: 6 inference algorithms with confidence thresholds
- Size: ~2,800 lines of working extraction patterns with real examples

**Why it matters**: Test 5 showed strategic themes improved 133% (21 vs 9) when we added examples. This step encodes all successful extraction patterns into the framework.

**Files affected**:
- Main file: `prompts/extraction/2_execution_framework.md`
- May need to review: `prompts/extraction/domain_knowledge/` directory for related patterns

---

### STEP 3: Relationship System Prompt (PLANNED)
**File**: `prompts/relationship_inference/system_prompt.md`  
**Content to swap from**: Combination of old `system_prompt.md` + `semantic_concept_linking.md`  
**What will change**:
- Current: Generic relationship classification prompt
- New: Hard constraints (EXACTLY 13 types, no custom types)
- New: Confidence thresholds (≥0.70 minimum, ≥0.80 for complex)
- New: Topic taxonomy matching (technical, management, logistics, security, financial, documentation)
- New: 6 core inference algorithms (pain point mapping, factor decomposition, adjacency discovery, etc.)
- Size: ~1,200 lines of working relationship patterns

**Why it matters**: Test 5 showed 5,270 relationships with comma-separated custom types (FAILED inference). This replaces that with strict 13-type enforcement + confidence filtering.

---

### STEP 4: Individual Relationship Linking Guides (PLANNED)
**Files** (8 files total):
1. `prompts/relationship_inference/attachment_section_linking.md` → `attachment_section_linking.md` content
2. `prompts/relationship_inference/clause_clustering.md` → `clause_clustering.md` content
3. `prompts/relationship_inference/document_hierarchy.md` → `document_hierarchy.md` content
4. `prompts/relationship_inference/document_section_linking.md` → `document_section_linking.md` content
5. `prompts/relationship_inference/instruction_evaluation_linking.md` → `instruction_evaluation_linking.md` content
6. `prompts/relationship_inference/requirement_evaluation.md` → `requirement_evaluation.md` content
7. `prompts/relationship_inference/semantic_concept_linking.md` → `semantic_concept_linking.md` content
8. `prompts/relationship_inference/sow_deliverable_linking.md` → `sow_deliverable_linking.md` content

**What will change**:
- Current: Generic linking patterns
- New: 3-4 specific inference patterns per type (confidence 0.70-1.0)
- New: Agency-specific naming conventions (DoD J-####, GSA Exhibit, NASA Annex, etc.)
- New: LLM prompt templates for each relationship type
- New: Special cases (multi-deliverable tasks, orphaned attachments, scattered clauses)
- Size: 50-200 lines per file = ~900 lines total

**Why it matters**: Test 5 showed attachment coverage is still incomplete (UNKNOWN=24). These guides encode proven patterns for 100% coverage.

---

### STEP 5: Content Gaps Analysis (PLANNED)
**Files to check**:
- `prompts/extraction/1_system_role.md` - Mission/role definition (keep or update with old patterns?)
- `prompts/extraction/domain_knowledge/` directory - Should this be updated?
- Any NEW features not in old prompts?

**What we need to decide**:
- Keep current 1_system_role.md or replace with old patterns?
- Domain knowledge library is new feature - keep minimal or integrate old content?
- Any missing pieces we need to add?

**Size**: Probably small changes, mostly verification

---

### STEP 6: Full Test & Validation (PLANNED)
**Process**:
1. Back up entire `prompts/` directory state
2. Complete content replacements for STEPS 2-5
3. Run Test 6: Navy MBOS RFP with full new/old hybrid architecture
4. Measure metrics:
   - Entity types: Target ≤17 (was 18 in Test 5, 18 in Test 4)
   - Relationship types: Target ≤13 (was 5,270 in Test 5, 873 in Test 4) 🚨
   - Strategic themes: Target ≥20 (was 21 in Test 5, 9 in Test 4) ✅
   - EVALUATED_BY relationships: Target ≥100 (was 10 in Test 5, 56 in Test 4)
   - UNKNOWN entities: Target ≤5 (was 24 in Test 5, 5 in Test 4)

**Success criteria**:
- ✅ Entity types ≤17: Indicates ontology control working
- ✅ Relationship types ≤13: CRITICAL - indicates hard constraints enforced
- ✅ Strategic themes ≥20: Indicates extraction patterns working (learned from Test 5)
- ✅ EVALUATED_BY ≥100: Indicates relationship inference working
- ✅ UNKNOWN ≤5: Indicates disambiguation working

---

## Risk & Mitigation

### Risk 1: Format Incompatibility
**Issue**: Old prompt content may have different format/structure than new architecture expects  
**Mitigation**:
- Keep NEW file names, directory structure unchanged
- Convert old content format to new architecture (add/remove headers as needed)
- Test with small sample before full Test 6

### Risk 2: LLM Prompt Sensitivity
**Issue**: LLM may behave differently with old vs new prompt phrasing  
**Mitigation**:
- Test with same RFP (Navy MBOS) for apples-to-apples comparison
- Monitor for unexpected behavior changes
- Can revert to backup if needed (backed up entire old version)

### Risk 3: Incomplete Content Transfer
**Issue**: Old prompts may reference content not fully transferred  
**Mitigation**:
- Cross-reference old files with new locations
- Identify any gaps before Test 6
- Manually fill gaps if needed

### Risk 4: Relationship Type Control Not Enforced
**Issue**: LLM might ignore hard constraints and create custom types again  
**Mitigation**:
- STEP 3 adds explicit "HARD CONSTRAINT" sections
- Add post-processing validation (check count of unique types)
- Include "invalid types will cause system failure" language
- Consider: Do we need post-processing cleanup script to catch violations?

---

## File Mapping Reference

### OLD PROMPT FILES → NEW ARCHITECTURE FILES

| Old File | New Location | STEP | Key Content |
|----------|--------------|------|------------|
| entity_detection_rules.md | `3_entity_specifications.md` | 1 ✅ | Semantic-first detection, 17 types |
| entity_extraction_prompt.md | `2_execution_framework.md` | 2 ⏳ | 5 examples, 8-decision tree |
| system_prompt.md (old) | `relationship_inference/system_prompt.md` | 3 ⏳ | Hard constraints, 13 types, confidence |
| attachment_section_linking.md | Same | 4 ⏳ | Agency-specific patterns |
| clause_clustering.md | Same | 4 ⏳ | FAR/DFARS grouping |
| document_hierarchy.md | Same | 4 ⏳ | Hierarchical relationships |
| document_section_linking.md | Same | 4 ⏳ | Document→Section mapping |
| instruction_evaluation_linking.md | Same | 4 ⏳ | L↔M relationship patterns |
| requirement_evaluation.md | Same | 4 ⏳ | Topic alignment mapping |
| semantic_concept_linking.md | Same | 4 ⏳ | Implicit concept relationships |
| sow_deliverable_linking.md | Same | 4 ⏳ | Work→Deliverable mapping |

---

## Test 5 vs Test 6: What We Expect to Change

### Test 5 Results (Pattern-Enhanced):
- Entity types: 18 (violating 17 limit)
- Unique types: UNKNOWN=24, clause=243, deliverable=428, etc.
- Relationship types: 5,270 (comma-separated custom types) 🚨
- Strategic themes: 21 ✅ (improvement from 9)
- EVALUATED_BY: 10 (way below target 100+)
- Total entities: 2,987 (good coverage)

### Test 6 Expected (Full Architecture Redesign):
- Entity types: ≤17 ✅ (entity detection rules should fix UNKNOWN)
- Relationship types: ≤13 ✅ (hard constraints + confidence threshold should enforce)
- Strategic themes: 20+ ✅ (extraction patterns should maintain Test 5 improvement)
- EVALUATED_BY: 100+ ✅ (requirement_evaluation linking patterns should activate)
- UNKNOWN: ≤5 ✅ (disambiguation tree should prevent generic assignment)

**Biggest unknown**: Will relationship types actually drop from 5,270 to ≤13? This is THE critical metric because it was worst violation in Test 4 (873) AND Test 5 (5,270).

---

## Next Actions (Immediate)

1. **STEP 2: Complete 2_execution_framework.md swap**
   - Read: `entity_extraction_prompt.md` content
   - Swap: Replace current framework with 5 examples + 8-decision tree + topic taxonomy
   - Commit: "Step 2: Entity extraction patterns with annotated examples"
   - Estimated time: 30 minutes

2. **STEP 3: Complete relationship_inference/system_prompt.md swap**
   - Combine: Old `system_prompt.md` + `semantic_concept_linking.md`
   - Focus on: Hard constraints (exactly 13 types), confidence thresholds
   - Commit: "Step 3: Relationship inference system prompt with hard constraints"
   - Estimated time: 20 minutes

3. **STEP 4: Complete 8 individual relationship linking files**
   - Copy: Old relationship pattern files into corresponding new files
   - Convert: Format to match new architecture expectations
   - Commit: "Step 4: Individual relationship linking patterns for all 8 types"
   - Estimated time: 45 minutes

4. **STEP 5: Content gaps analysis**
   - Review: What pieces might be missing?
   - Decide: Updates needed or complete with what we have?
   - Estimated time: 15 minutes

5. **STEP 6: Test 6 execution**
   - Run: Navy MBOS RFP with full hybrid architecture
   - Measure: All 6 metrics (entity types, relationship types, themes, EVALUATED_BY, UNKNOWN, coverage)
   - Analyze: Success vs failure diagnosis
   - Estimated time: Processing 30 min + Analysis 30 min

---

## Why This Approach Will Work

**Root cause analysis from Tests 4-5**:

Test 4 Failure:
- 873 relationship types (LLM created custom comma-separated types)
- 9 strategic themes (detection not working)
- Root cause: New architecture didn't have strong enough pattern guidance

Test 5 Partial Success:
- Strategic themes 21 ✅ (pattern examples WORKED)
- Entity coverage 2,987 ✅ (comprehensive extraction working)
- But UNKNOWN 24 ✗, relationship types 5,270 ✗ (pattern enforcement still weak)
- Root cause: Examples helped, but not enough pattern strength for hard constraint enforcement

Test 6 Strategy:
- **For entity types**: entity_detection_rules (disambiguation tree) should prevent UNKNOWN
- **For relationship types**: Hard constraints + confidence thresholds should enforce 13-type limit
- **For strategic themes**: Keep extraction patterns that improved them 133%
- **For EVALUATED_BY**: New relationship patterns should create 100+ instances
- Root cause addressed: Old proven patterns + new organization structure

---

## Contingency: Revert Plan

If Test 6 fails unexpectedly:
1. Full backup exists: `prompts/` directory backed up before changes
2. Individual backups: Each file has `.bak` version
3. Git history: Each step committed separately (can revert individual commits)
4. Fallback: Return to Test 5 enhanced prompts and debug specific failures

---

**Document Version**: 1.0  
**Date**: October 28, 2025  
**Author**: Architectural Redesign Initiative  
**Status**: STEP 1 COMPLETE, STEPS 2-6 IN PROGRESS
