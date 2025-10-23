# Prompt Audit Analysis - Branch 009 Iteration 5

**Date**: January 23, 2025  
**Issue**: UNKNOWN entities increased 206% (35 → 107) after multi-prompt loading  
**Root Cause Hypothesis**: Redundancy, conflicts, and blurred separation of concerns

---

## 📊 Current Prompt Structure

### **Loaded Prompts** (Iteration 5)

1. **entity_extraction_prompt.md** (1,460 lines)
2. **entity_detection_rules.md** (1,103 lines)
3. **section_normalization.md** (321 lines)
4. **metadata_extraction.md** (554 lines)

**Total**: 3,438 lines (~20K tokens, 1% of 2M context)

---

## 🔍 Redundancy & Conflict Analysis

### **1. Entity Naming Normalization** ❌ REDUNDANT

**Location 1**: `entity_extraction_prompt.md` (Lines 30-90)

```markdown
**CRITICAL ENTITY NAMING NORMALIZATION RULES:**

1. Section Names: Always use Title Case with periods
2. FAR/DFARS Clauses: Always use exact citation format
3. CDRL/Deliverables: Always use uppercase identifier + name
4. Organizations/Programs: Use official capitalization
5. When you see multiple formatting variations...
```

**Location 2**: `section_normalization.md` (Lines 1-80)

```markdown
# Section Normalization Mapping

**Purpose**: Map non-standard section labels to semantic types
```

**CONFLICT**:

- `entity_extraction_prompt.md` focuses on **entity naming** (format consistency)
- `section_normalization.md` focuses on **semantic type mapping** (UCF structure)
- **BUT** both discuss section naming, creating confusion

**RESOLUTION**: Keep naming rules in extraction prompt, remove from normalization prompt

---

### **2. Entity Type Classification** ❌ REDUNDANT

**Location 1**: `entity_extraction_prompt.md` (Lines 100-160)

```markdown
2. You MUST use EXACTLY ONE of these 17 types for EVERY entity
3. DO NOT invent new entity types. Fallback mappings:
   - Plans, policies, standards → document
   - Systems, tools, software → technology
   - Tables, lists, schedules → concept
```

**Location 2**: `entity_detection_rules.md` (Lines 20-1100)

```markdown
## Entity Type 1: EVALUATION_FACTOR

### Content Signals

- "will be evaluated"
- "evaluation factor"

## Entity Type 2: REQUIREMENT

### Content Signals

- modal verbs (shall, should, may)
```

**CONFLICT**:

- Extraction prompt: Type LIST + Fallback mappings (prescriptive)
- Detection rules: Type DESCRIPTIONS + Content signals (semantic)
- LLM gets conflicting guidance: "Use these 17 types" vs "Detect by content signals"

**RESOLUTION**:

- Extraction prompt: TYPE LIST + Forbidden types + Fallback mappings
- Detection rules: CONTENT SIGNALS + Metadata extraction patterns (HOW to detect, not WHAT)

---

### **3. UCF Section Structure** ⚠️ CONFLICTING

**Location 1**: `entity_extraction_prompt.md` (Lines 170-190)

```markdown
**Uniform Contract Format (UCF) Sections:**

- Section A: Solicitation/Contract Form
- Section C: Statement of Work
- Section L: Instructions to Offerors (SUBMISSION_INSTRUCTION)
- Section M: Evaluation Factors (EVALUATION_FACTOR)
```

**Location 2**: `section_normalization.md` (ENTIRE FILE - 321 lines)

```markdown
## Standard Uniform Contract Format (UCF)

| Section A | SOLICITATION_FORM | SF 1449, Cover Page |
| Section C | DESCRIPTION_SPECS | SOW, PWS, SOO |
| Section L | SUBMISSION_INSTRUCTIONS | Proposal Format |
| Section M | EVALUATION_CRITERIA | Source Selection |

## Non-Standard Label Mapping

| Request for Quote | Section A | SOLICITATION_FORM |
| Selection Criteria | Section M | EVALUATION_CRITERIA |
```

**CONFLICT**:

- Extraction prompt: Brief UCF summary (entity type → section mapping)
- Normalization prompt: Extensive UCF mapping tables (section → semantic type)
- **Different naming conventions**:
  - Extraction: "SUBMISSION_INSTRUCTION" (entity type)
  - Normalization: "SUBMISSION_INSTRUCTIONS" (semantic type plural)

**RESOLUTION**: Remove UCF from extraction prompt, consolidate in detection rules

---

### **4. Metadata Extraction** ✅ UNIQUE (No Conflict)

**Location**: `metadata_extraction.md` (554 lines)

**Purpose**: Field-level extraction for structured metadata

- REQUIREMENT: requirement_type, criticality_level, modal_verb
- EVALUATION_FACTOR: factor_id, relative_importance, subfactors
- DELIVERABLE: deliverable_type, due_date, submission_format

**Status**: NO REDUNDANCY - This is unique functionality

**BUT**: May be causing over-extraction (more fields → more entities → more UNKNOWN)

---

## 🎯 Separation of Concerns Analysis

### **Current Problem**: Blurred Responsibilities

| Prompt                        | Current Responsibility                                                 | Should Be                                                      |
| ----------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------- |
| `entity_extraction_prompt.md` | Entity types + Naming rules + UCF structure + Examples + Relationships | **Core extraction rules + Examples + Relationships ONLY**      |
| `entity_detection_rules.md`   | Content signals + Metadata schemas + Location patterns                 | **Content signals for 17 entity types ONLY**                   |
| `section_normalization.md`    | UCF mapping + Non-standard labels + Content detection                  | **DELETE - Merge content detection into detection_rules**      |
| `metadata_extraction.md`      | Field-level schemas + Extraction rules + Priority scoring              | **DEFER to Phase 2 (query-time) - Too complex for extraction** |

---

## 💡 Recommended Refactoring

### **Option A: Aggressive Cleanup** (RECOMMENDED)

**Goal**: Clean separation of concerns, remove all redundancy

#### **1. Slim Down `entity_extraction_prompt.md`** (1,460 → ~800 lines)

**KEEP**:

- ✅ Entity naming normalization rules (30-90 lines)
- ✅ 17 entity type list with forbidden types (100-160 lines)
- ✅ Fallback mappings (plans→document, systems→technology)
- ✅ Relationship extraction philosophy
- ✅ 10 ontology-grounded examples (L↔M, requirements, attachments)

**REMOVE**:

- ❌ UCF section descriptions (Lines 170-190) → Move to detection_rules
- ❌ FAR/DFARS pattern details (Lines 160-170) → Move to detection_rules
- ❌ Redundant type classification examples → Keep only unique edge cases

**Result**: ~800 lines of PURE extraction rules + examples

---

#### **2. Refocus `entity_detection_rules.md`** (1,103 → ~600 lines)

**KEEP**:

- ✅ Content signals for 17 entity types ("will be evaluated", modal verbs)
- ✅ Structural patterns (hierarchy, numbering, ratings)
- ✅ Context clues (relative importance, point scores)
- ✅ UCF section structure (merge from extraction prompt + normalization)

**REMOVE**:

- ❌ Extensive metadata schemas (Lines 40-100 per type) → Too detailed, causing confusion
- ❌ JSON schema examples → Defer to Phase 2 (query-time metadata)
- ❌ Priority scoring algorithms → Not needed at extraction time

**MERGE IN**:

- ➕ UCF structure from `entity_extraction_prompt.md` (Lines 170-190)
- ➕ Non-standard label mapping from `section_normalization.md` (80 lines)
- ➕ Content-based detection rules from `section_normalization.md` (40 lines)

**Result**: ~600 lines of PURE content signals + UCF context

---

#### **3. DELETE `section_normalization.md`** (321 lines → 0)

**Rationale**:

- 80% redundant with extraction prompt UCF section
- 20% unique content (non-standard mapping) merges into detection_rules
- Creating confusion by duplicating structure information

**Result**: DELETED

---

#### **4. DEFER `metadata_extraction.md`** (554 lines → Move to Branch 010)

**Rationale**:

- Metadata extraction is a **query-time operation**, not extraction-time
- Field-level schemas (requirement_type, criticality_level) are causing over-extraction
- LLM is extracting too many granular entities trying to populate all fields
- Better approach: Extract entities simply, enrich metadata at query time

**Action**:

- Move to `prompts/user_queries/metadata_enrichment.md`
- Use as `user_prompt` parameter during queries
- Example: "Analyze requirements and extract criticality levels"

**Result**: Moved to Branch 010 (query-time intelligence)

---

### **Final Prompt Structure (Option A)**

```
prompts/entity_extraction/
├── entity_extraction_prompt.md (~800 lines)
│   ├── Entity naming normalization (consistent formatting)
│   ├── 17 entity types + forbidden types
│   ├── Fallback mappings (plans→document, systems→technology)
│   ├── Relationship extraction philosophy
│   └── 10 ontology-grounded examples
│
├── entity_detection_rules.md (~600 lines)
│   ├── Content signals for 17 entity types
│   ├── Structural patterns (hierarchy, numbering)
│   ├── UCF section structure (merged from other prompts)
│   ├── Non-standard label mapping (Task Orders, FOPRs)
│   └── Context-based detection rules
│
└── [DELETED] section_normalization.md
└── [MOVED TO BRANCH 010] metadata_extraction.md
```

**Total**: ~1,400 lines (~10K tokens, 0.5% of 2M context)  
**Reduction**: 59% fewer lines (3,438 → 1,400)

---

### **Option B: Conservative Cleanup** (Safer, Less Aggressive)

**Goal**: Remove obvious redundancy, keep functional prompts

#### **Changes**:

1. ✅ Keep `entity_extraction_prompt.md` as-is
2. ✅ Keep `entity_detection_rules.md` (remove metadata schemas only)
3. ❌ DELETE `section_normalization.md` (merge 120 lines into detection_rules)
4. ❌ DELETE `metadata_extraction.md` (defer to Branch 010)

**Total**: ~2,200 lines (~13K tokens, 0.65% of 2M context)  
**Reduction**: 36% fewer lines (3,438 → 2,200)

---

## 📊 Expected Impact

### **Option A: Aggressive Cleanup**

| Metric          | Current (Iteration 5) | Expected (Iteration 6) | Improvement                |
| --------------- | --------------------- | ---------------------- | -------------------------- |
| Prompt Lines    | 3,438                 | 1,400                  | -59%                       |
| Prompt Tokens   | ~20K                  | ~10K                   | -50%                       |
| UNKNOWN         | 107 (2.8%)            | ~40-50 (1.2-1.5%)      | ✅ Major improvement       |
| Entity Count    | 3,776                 | ~2,800-3,000           | ✅ Reduced over-extraction |
| Edge/Node Ratio | 1.44                  | ~1.6-1.7               | ✅ Restore quality         |
| Custom Coverage | 97.2%                 | ~98-99%                | ✅ Slight improvement      |

**Risks**:

- May lose some semantic detection nuance
- Need to validate examples still work

---

### **Option B: Conservative Cleanup**

| Metric          | Current (Iteration 5) | Expected (Iteration 6) | Improvement             |
| --------------- | --------------------- | ---------------------- | ----------------------- |
| Prompt Lines    | 3,438                 | 2,200                  | -36%                    |
| Prompt Tokens   | ~20K                  | ~13K                   | -35%                    |
| UNKNOWN         | 107 (2.8%)            | ~60-70 (1.8-2.0%)      | ✅ Moderate improvement |
| Entity Count    | 3,776                 | ~3,200-3,400           | ✅ Moderate reduction   |
| Edge/Node Ratio | 1.44                  | ~1.5-1.6               | ✅ Some improvement     |
| Custom Coverage | 97.2%                 | ~97.5-98%              | ✅ Slight improvement   |

**Risks**:

- Lower (safer)

---

## 🚀 Recommendation

**I recommend Option A (Aggressive Cleanup)** for these reasons:

1. **Clear Separation of Concerns**:

   - Extraction prompt: WHAT to extract (types, naming rules, examples)
   - Detection rules: HOW to detect (content signals, patterns)
   - Query-time: Metadata enrichment (defer to Branch 010)

2. **Eliminates Redundancy**:

   - No duplicate UCF structure
   - No conflicting entity type guidance
   - No metadata over-extraction

3. **Manageable Token Budget**:

   - 10K tokens (0.5% of context) vs 20K tokens (1%)
   - More room for future enhancements

4. **Aligns with Branch 010 Vision**:

   - Simple extraction foundation
   - Rich query-time intelligence layer
   - Two-stage intelligence system

5. **Proven Pattern**:
   - Iteration 4: Single 1,460-line prompt = 1.72 ratio, 1.2% UNKNOWN
   - Option A: Two 800-line prompts = Similar target with semantic signals

---

## ✅ Implementation Plan

### **Step 1: Create Refactored Prompts**

1. **Slim down entity_extraction_prompt.md**:

   - Remove UCF section descriptions (Lines 170-190)
   - Keep naming normalization rules (Lines 30-90)
   - Keep 17 entity types + forbidden types (Lines 100-160)
   - Keep examples (Lines 500-1400)

2. **Refocus entity_detection_rules.md**:

   - Keep content signals (Lines 1-600)
   - Remove metadata schemas (Lines 600-1100)
   - Merge UCF from extraction prompt + normalization prompt

3. **Delete prompts**:
   - Delete `section_normalization.md`
   - Move `metadata_extraction.md` to Branch 010 planning

### **Step 2: Test Iteration 6**

1. Restart server with refactored prompts
2. Clear rag_storage/default/
3. Process MCPP II RFP
4. Measure metrics vs Iteration 5

### **Step 3: Compare Results**

| Success Criteria | Target              |
| ---------------- | ------------------- |
| UNKNOWN          | ≤50 entities (1.5%) |
| Edge/Node Ratio  | ≥1.6                |
| Entity Count     | 2,800-3,200         |
| Custom Coverage  | ≥98%                |

### **Step 4: Decision Point**

- ✅ **If successful**: Commit, merge to main, proceed to Branch 010
- ⚠️ **If marginal**: Try Option B (conservative cleanup)
- ❌ **If worse**: Rollback to single prompt (Iteration 4 baseline)

---

**What do you think?** Should I proceed with **Option A** (aggressive refactoring)?
