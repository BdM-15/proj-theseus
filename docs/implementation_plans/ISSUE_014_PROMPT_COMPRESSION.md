# Implementation Plan: Issue #14 - Prompt Compression with Intelligence Preservation

**Issue**: [#14 - Compress Extraction Prompts](https://github.com/BdM-15/govcon-capture-vibe/issues/14)  
**Branch**: `037-prompt-compression-intelligence-first`  
**Status**: Planning  
**Priority**: IMMEDIATE (Highest ROI optimization)  
**Created**: December 9, 2025  

---

## BRANCH CREATION (MANDATORY FIRST STEP)

Before ANY implementation work begins:

```powershell
# 1. Ensure on main and up-to-date
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b 037-prompt-compression-intelligence-first

# 3. Push branch to remote
git push -u origin 037-prompt-compression-intelligence-first
```

**Branch Naming**: `037-prompt-compression-intelligence-first` follows the `{number}-{descriptive-kebab-case}` convention.

---

## Executive Summary

**Goal**: Reduce system prompt token count by **30-50%** (per Grok 4 guidance) while **preserving 100% of extraction intelligence**.

**Critical Constraint**: Intelligence preservation is the **utmost priority**. No compression technique should sacrifice extraction accuracy, entity coverage, or relationship inference quality.

**Methodology**: 
- **CAUTIOUS 100-200 LINES AT A TIME** - Incremental compression with validation after each batch
- **Grok 4 Optimized** - Following direct guidance from Grok 4 on optimal prompt structure

**Compression Approach** (Grok 4 Recommended):
1. Remove non-productive elements (decorative symbols, markdown formatting, verbose phrasing)
2. Convert tables to bullet lists (Grok handles plain lists well)
3. Consolidate examples to 3-5 diverse per category
4. Restructure to optimal flow: Role → Rules → Types → Examples → Relationships → Output

**Current State**:
| File | Characters | Est. Tokens |
|------|------------|-------------|
| `grok_json_prompt.md` | 15,354 | ~3,800 |
| `entity_detection_rules.md` | 53,586 | ~13,400 |
| `entity_extraction_prompt.md` | 122,812 | ~30,700 |
| Relationship inference (13 files) | 145,733 | ~36,400 |
| **Total System Prompt** | ~337,485 | **~84,300** |

**Target After Compression**: ~42,000-59,000 tokens (30-50% reduction)

**Cost Impact**: ~$0.017/chunk → ~$0.009-0.012/chunk = **$0.16-0.26 savings per RFP**

---

## CRITICAL: Intelligence That MUST Be Preserved

### 1. Entity Type Definitions (18 Types)
Every entity type's definition, disambiguation rules, and examples must remain intact:
- `requirement`, `evaluation_factor`, `submission_instruction`, `deliverable`
- `clause`, `statement_of_work`, `performance_metric`, `strategic_theme`
- `organization`, `document`, `section`, `program`, `equipment`
- `location`, `person`, `technology`, `concept`, `event`

### 2. Detection Rules & Trigger Phrases
These are the "secret sauce" that enables accurate extraction:
- **PERFORMANCE_METRIC triggers**: "PO-X", "Threshold:", "AQL", "QASP", numerical standards
- **REQUIREMENT triggers**: "Contractor shall...", "must", "will" with action verbs
- **STRATEGIC_THEME triggers**: "emphasizes", "critical to", "paramount", weighted >30%
- **SPLIT RULE**: One sentence → Two entities (action + metric)

### 3. Disambiguation Decision Trees
Complex logic for ambiguous cases:
- Document vs. Statement of Work (extract both)
- Requirement vs. Evaluation Factor (different concepts)
- Government obligations (skip) vs. Contractor obligations (extract)
- Performance Metric vs. Requirement distinction

### 4. Naming Normalization Rules
Prevent duplicate entities:
- Section names: Title Case with periods ("Section C.4 Supply")
- FAR/DFARS clauses: Exact citation format ("FAR 52.212-1")
- CDRLs: Uppercase + descriptive ("CDRL A001 Monthly Status Report")

### 5. JSON Schema Requirements
Output format specifications that Instructor validates:
- `entity_name` (not `name`)
- `entity_type` (not `type`)
- Relationship format with full entity objects (not string references)
- Type-specific metadata fields (criticality, weight, page_limit, etc.)

### 6. Domain Knowledge Patterns
Government contracting expertise:
- UCF section mapping (A-M)
- FAR/DFARS clause patterns
- CDRL/DD Form 1423 references
- Shipley methodology (MANDATORY/IMPORTANT/OPTIONAL)
- QASP separation rules

### 7. Relationship Inference Intelligence
All 13 relationship inference algorithm rules:
- Section L↔M mapping (GUIDES relationships)
- Clause clustering (CHILD_OF relationships)
- Deliverable traceability (SATISFIED_BY, PRODUCES relationships)
- SOW deliverable linking
- Workload enrichment patterns

---

## Grok 4 Prompt Structuring Guidelines

**Source**: Direct guidance from Grok 4 on optimal prompt compression for its architecture.

### Core Principles (From Grok 4)

1. **Token Efficiency Target**: 30-50% reduction
   - Remove repeats (multiple examples of same rule)
   - Remove verbose explanations
   - Remove unnecessary bold/italics
   - Keep concise, factual language

2. **Structure for LLM Comprehension** (Optimal Flow):
   ```
   1. Purpose/Role
   2. Key Rules/Decisions (critical distinctions)
   3. Entity Types/Schemas
   4. Examples (3-5 per category max)
   5. Relationships/Inferences
   6. Output Format
   ```

3. **Instruction-Following Enhancements**:
   - Prefix critical rules with "MUST" or "NEVER" for emphasis
   - Group related rules into numbered/bulleted lists
   - Retain annotated examples but trim to essentials (input → output JSON)
   - Keep fallback mappings and decision trees intact

4. **Education Optimization**:
   - Grok 4 learns best from clear patterns and contrasts
   - Keep PERFORMANCE_METRIC vs REQUIREMENT distinction prominent
   - Domain patterns (FAR/DFARS, CDRL) as bullet lists, not prose
   - Include brief "why" rationales for rules (leverages reasoning strength)

5. **Grok 4-Specific Tips**:
   - Handles plain lists well - avoid over-formatting
   - Focus on semantic inference rules for implicit relationship extraction
   - Plain text sections with minimal separators (`---` for major breaks only)

### What to REMOVE (Non-Productive Elements)

| Element | Action | Example |
|---------|--------|---------|
| Markdown headers (`#`, `##`) | Convert to `SECTION:` or remove | `## ⚠️ CRITICAL` → `CRITICAL:` |
| Decorative symbols | Remove entirely | `⚠️`, `⚡`, `✅`, `❌`, `📋` |
| Markdown tables (`\|`) | Convert to bullet lists | Table → `• Pattern → Type` |
| Bold/Italics (`**`, `_`) | Remove formatting | `**MUST**` → `MUST` |
| Code fences (` ``` `) | Remove, keep content | JSON stays, fences go |
| Redundant phrases | Delete | "Read carefully before extracting!" |
| Verbose explanations | Condense to bullets | Prose → bullet points |

### What to PRESERVE (Zero Loss Allowed)

- All 18 entity types
- All schemas/metadata fields
- All relationship types
- All inference rules
- All trigger phrases/patterns
- Decision trees for ambiguity
- Fallback mappings
- 3-5 diverse examples per category

### Grok 4 Optimal Prompt Structure

```
ROLE: You are a Knowledge Graph Specialist extracting entities from RFP texts.

CRITICAL DISTINCTIONS:
• PERFORMANCE_METRIC vs REQUIREMENT: [concise rule]
• SPLIT RULE: One sentence with action + metric → Two entities

ENTITY TYPES (18):
• requirement: Contractor obligation. Triggers: "shall", "must", "will"
• evaluation_factor: Scoring criterion. Triggers: "will be evaluated", "adjectival"
• [... remaining 16 types as bullets]

NORMALIZATION RULES:
• Sections: Title Case with periods ("Section C.4 Supply")
• Clauses: Exact citation ("FAR 52.212-1")
• CDRLs: Uppercase + name ("CDRL A001 Monthly Status Report")

FORBIDDEN TYPES (NEVER use):
• other, UNKNOWN, process, table, plan, policy, standard, system

DECISION TREE:
1. "J-02000 PWS" → Extract BOTH document AND statement_of_work
2. "Government shall..." → Skip (not contractor obligation)
3. Combined action + metric → Two entities with MEASURED_BY relationship

EXAMPLES (trimmed format):
Example 1 - QASP Table:
  Input: "PO-1: Escort Monitoring | Zero discrepancies | Monthly Inspection"
  Output: {"entity_name":"PO-1 Escort Monitoring","entity_type":"performance_metric","threshold":"Zero discrepancies","measurement_method":"Monthly Inspection"}
  Note: QASP rows → performance_metric, not requirement

[... 3-4 more diverse examples]

RELATIONSHIPS:
• MEASURED_BY: requirement → performance_metric
• GUIDES: submission_instruction → evaluation_factor
• CHILD_OF: clause → section
• [... remaining types]

OUTPUT FORMAT:
Return JSON object with "entities" array and "relationships" array.
MUST use entity_name (not name), entity_type (not type).
Relationships MUST use full entity objects, not string references.
```

---

## Compression Strategy: Intelligence-First Approach

### Strategy 1: Remove Non-Productive Elements (LOW RISK)

**What to Remove** (Grok 4 confirmed safe):
- Markdown headers (`#`, `##`, `###`) → Plain text labels
- Decorative symbols (`⚠️`, `⚡`, `✅`, `❌`, `📋`, `🔵`, `🟢`)
- Markdown horizontal rules (`---`) → Remove or use sparingly
- Bold/italics formatting (`**`, `_`, `*`)
- Code fence markers (` ``` `) → Keep JSON content, remove fences
- Excessive whitespace and blank lines
- Redundant phrasing ("Read carefully!", "This is critical!")

**What to KEEP**:
- All rule text content
- All examples (3-5 diverse per category)
- All entity definitions
- All trigger phrases and patterns
- Brief "why" rationales for rules

**Estimated Savings**: 15-25% token reduction

### Strategy 2: Table-to-List Conversion (LOW RISK per Grok 4)

**Transform** (Grok handles plain lists well):
```markdown
| Pattern | Example | Entity Type |
|---------|---------|-------------|
| Performance Objective (PO-X) | "PO-1: Escort Monitoring" | performance_metric |
| Performance Threshold: | "Threshold: Zero (0)" | performance_metric |
```

**Into**:
```text
performance_metric triggers:
• Performance Objective (PO-X) - e.g., "PO-1: Escort Monitoring"
• Performance Threshold: - e.g., "Threshold: Zero (0)"
• AQL, QASP, numerical standards (99.9%), per month/week
```

**Intelligence Preserved**: 100% - pattern, example, and type all retained
**Estimated Savings**: 10-15% additional reduction

### Strategy 3: Example Consolidation (MEDIUM RISK)

**Grok 4 Guidance**: Keep 3-5 diverse examples per category, trim to essentials.

**Transform verbose examples**:
```markdown
**Example Text:**
> "The Contractor shall clean equipment daily with no more than 2 defects per month."

**Extract as TWO entities:**
[30+ lines of explanation and JSON]
```

**Into**:
```text
Example 3 - Split Rule:
  Input: "Contractor shall clean equipment daily with no more than 2 defects per month."
  Entities: [{"entity_name":"Daily Equipment Cleaning","entity_type":"requirement"},{"entity_name":"Equipment Cleaning Defect Threshold","entity_type":"performance_metric","threshold":"No more than 2 defects per month"}]
  Relationship: requirement --MEASURED_BY--> performance_metric
  Note: Action + metric in one sentence → two entities
```

**Estimated Savings**: 20-30% on example sections

### Strategy 4: Header Condensation (LOW RISK per Grok 4)

**Transform**:
```markdown
## ⚠️ CRITICAL: PERFORMANCE_METRIC vs REQUIREMENT (Priority #1)

**This is the #1 extraction error. Read carefully before extracting!**

### PERFORMANCE_METRIC = Measurable Standard (How performance is judged)
```

**Into**:
```text
CRITICAL DISTINCTION - PERFORMANCE_METRIC vs REQUIREMENT:
PERFORMANCE_METRIC = Measurable standard (how performance is judged)
```

**Estimated Savings**: 5-10% additional reduction

### Strategy 5: Prose-to-Bullets Conversion (LOW RISK)

**Transform prose**:
```markdown
When you encounter HTML tables in the input, you should extract each building
or location as a location entity with equipment counts. You should also extract
equipment totals as equipment entities by maintenance schedule. Include quantities
in entity_name or metadata fields.
```

**Into**:
```text
HTML Table Extraction:
• Each building/location → location entity with equipment counts
• Equipment totals → equipment entity by maintenance schedule
• MUST include quantities in entity_name or metadata
```

**Estimated Savings**: 10-15% on prose sections

**Estimated Savings**: 15-20% on JSON examples alone

---

## Implementation Phases: CAUTIOUS 100-200 LINES APPROACH

### Why 100-200 Lines at a Time?

1. **Immediate Validation** - Test extraction quality after each batch
2. **Easy Rollback** - If quality drops, you know exactly which batch caused it
3. **Pattern Learning** - Discover which compression techniques work vs. damage intelligence
4. **Risk Isolation** - One bad optimization won't contaminate the entire prompt

### Batch Processing Order (Lowest to Highest Risk)

| Order | File | Total Lines | Batches | Risk Level |
|-------|------|-------------|---------|------------|
| 1 | `grok_json_prompt.md` | 377 | 2 batches | LOW |
| 2 | `entity_detection_rules.md` | 1,613 | 9 batches | MEDIUM |
| 3 | `entity_extraction_prompt.md` | 3,173 | 16 batches | MEDIUM |
| 4 | Relationship inference (13 files) | ~2,500 | 13+ batches | LOW (modular) |

---

### Phase 1: Setup & Baseline (Day 1)

**Step 1.1: Create Branch**
```powershell
git checkout main
git pull origin main
git checkout -b 037-prompt-compression-intelligence-first
git push -u origin 037-prompt-compression-intelligence-first
```

**Step 1.2: Create Directory Structure**
```powershell
mkdir prompts/extraction_optimized
mkdir prompts/relationship_inference_optimized
```

**Step 1.3: Create Baseline Measurement Script**
- Create `tests/test_prompt_compression_baseline.py`
- Run extraction on known test document
- Record: entity counts by type, relationship counts, processing time

**Step 1.4: Select Test Document**
- Recommend: A single chunk from MCPP or ADAB ISS with known entities
- Create `tests/fixtures/compression_test_chunk.txt`

---

### Phase 2: grok_json_prompt.md (Day 2) - 2 Batches

**File**: `prompts/extraction/grok_json_prompt.md` (377 lines)

| Batch | Lines | Content | Checkpoint |
|-------|-------|---------|------------|
| 2.1 | 1-200 | Role, PERFORMANCE_METRIC rules, Entity Types 1-10 | Test extraction |
| 2.2 | 201-377 | Entity Types 11-17, Domain Rules, JSON Output | Test extraction |

**Workflow Per Batch**:
```
1. Read lines N to N+199 from original
2. Apply ONLY structural compression:
   - Remove blank lines (keep single newlines)
   - Remove markdown `---` horizontal rules
   - Compact JSON examples (single line)
3. Write to optimized file
4. Run test extraction
5. Compare: entity count, relationship count, type distribution
6. If ≥99% parity → proceed to next batch
7. If <99% parity → STOP, identify problematic compression
```

**Validation Gate**: ≥99% entity parity after each batch

---

### Phase 3: entity_detection_rules.md (Days 3-4) - 9 Batches

**File**: `prompts/extraction/entity_detection_rules.md` (1,613 lines)

| Batch | Lines | Content | Risk |
|-------|-------|---------|------|
| 3.1 | 1-200 | Priority Detection (PERFORMANCE_METRIC patterns) | HIGH - critical rules |
| 3.2 | 201-400 | STRATEGIC_THEME detection, Core Principle | MEDIUM |
| 3.3 | 401-600 | UCF Reference (Section A-M mapping) | MEDIUM |
| 3.4 | 601-800 | Non-Standard Labels, Agency Variations | MEDIUM |
| 3.5 | 801-1000 | EVALUATION_FACTOR detection patterns | HIGH - critical rules |
| 3.6 | 1001-1200 | SUBMISSION_INSTRUCTION patterns | MEDIUM |
| 3.7 | 1201-1400 | REQUIREMENT patterns, CLAUSE detection | HIGH - critical rules |
| 3.8 | 1401-1600 | DELIVERABLE, SECTION patterns | MEDIUM |
| 3.9 | 1601-1613 | Final section | LOW |

**HIGH-RISK Batches (3.1, 3.5, 3.7)**: Apply ONLY whitespace compression, keep ALL content verbatim.

**Validation Gate**: ≥98% entity parity, verify specific entity types affected by each batch.

---

### Phase 4: entity_extraction_prompt.md (Days 5-8) - 16 Batches

**File**: `prompts/extraction/entity_extraction_prompt.md` (3,173 lines)

| Batch | Lines | Content | Risk |
|-------|-------|---------|------|
| 4.1 | 1-200 | Header, PERFORMANCE_METRIC vs REQUIREMENT | HIGH |
| 4.2 | 201-400 | Entity naming normalization rules | HIGH |
| 4.3 | 401-600 | Entity type rules, forbidden types | HIGH |
| 4.4 | 601-800 | Domain knowledge patterns | MEDIUM |
| 4.5 | 801-1000 | Decision tree for ambiguous cases | HIGH |
| 4.6 | 1001-1200 | Relationship extraction rules | MEDIUM |
| 4.7 | 1201-1400 | Examples section 1 | MEDIUM |
| 4.8 | 1401-1600 | Examples section 2 | MEDIUM |
| 4.9 | 1601-1800 | Examples section 3 | MEDIUM |
| 4.10 | 1801-2000 | Examples section 4 | MEDIUM |
| 4.11 | 2001-2200 | Real RFP examples | LOW |
| 4.12 | 2201-2400 | Real RFP examples | LOW |
| 4.13 | 2401-2600 | Real RFP examples | LOW |
| 4.14 | 2601-2800 | Real RFP examples | LOW |
| 4.15 | 2801-3000 | Real RFP examples | LOW |
| 4.16 | 3001-3173 | Final examples, closing | LOW |

**Validation Gate**: ≥95% entity parity, ≥95% relationship parity

---

### Phase 5: Relationship Inference Files (Days 9-10) - 13 Files

Each file is already modular (100-300 lines each). Process one file at a time.

| Order | File | Lines | Risk |
|-------|------|-------|------|
| 5.1 | system_prompt.md | 26 | LOW |
| 5.2 | document_section_linking.md | ~100 | LOW |
| 5.3 | orphan_resolution.md | ~150 | LOW |
| 5.4 | sow_deliverable_linking.md | ~130 | LOW |
| 5.5 | evaluation_hierarchy.md | ~200 | MEDIUM |
| 5.6 | clause_clustering.md | ~260 | MEDIUM |
| 5.7 | deliverable_traceability.md | ~300 | MEDIUM |
| 5.8 | attachment_section_linking.md | ~380 | MEDIUM |
| 5.9 | instruction_evaluation_linking.md | ~330 | HIGH |
| 5.10 | semantic_concept_linking.md | ~400 | MEDIUM |
| 5.11 | requirement_evaluation.md | ~440 | HIGH |
| 5.12 | workload_enrichment.md | ~450 | HIGH |
| 5.13 | document_hierarchy.md | ~730 | MEDIUM |

**Validation Gate**: Test relationship inference after each file

---

### Phase 6: Configuration Toggle (Day 11)

**Tasks**:
1. Add `PROMPT_FORMAT` environment variable to `.env`:
   ```
   PROMPT_FORMAT=optimized  # or "original" for rollback
   ```
2. Modify `src/extraction/json_extractor.py` to load appropriate prompts:
   ```python
   def _load_full_system_prompt(self) -> str:
       format_type = os.getenv("PROMPT_FORMAT", "original")
       if format_type == "optimized":
           return self._load_optimized_prompts()
       return self._load_original_prompts()
   ```
3. Update `src/core/prompt_loader.py` for format awareness

**Deliverables**:
- Modified `src/extraction/json_extractor.py`
- Updated `src/core/prompt_loader.py`
- Documentation in `.env.example`

---

### Phase 7: Full A/B Validation (Day 12)

**Tasks**:
1. Run existing test: `tests/test_compressed_prompts.py`
2. Run full extraction on complete RFP (not just chunks)
3. Compare entity/relationship totals
4. Verify all 18 entity types present
5. Check Section L↔M mapping accuracy

**Success Criteria**:
- Entity count: ≥95% of baseline
- Relationship count: ≥95% of baseline
- Workload drivers: ≥95% completeness
- All 18 entity types extractable
- Processing time: ≤+10%

---

### Phase 8: Production Deployment (Day 13)

**Tasks**:
1. Update documentation with compression metrics
2. Set `PROMPT_FORMAT=optimized` in production `.env`
3. Monitor first production run for anomalies
4. Document rollback procedure

---

## Batch Validation Workflow

### For EACH 100-200 Line Batch:

```
┌─────────────────────────────────────────────────────────┐
│ BATCH PROCESSING WORKFLOW                               │
├─────────────────────────────────────────────────────────┤
│ 1. READ original lines N to N+199                       │
│ 2. APPLY structural compression only:                   │
│    • Remove excessive blank lines                       │
│    • Remove markdown horizontal rules (---)             │
│    • Compact JSON to single lines                       │
│    • Keep ALL semantic content                          │
│ 3. APPEND to optimized file                             │
│ 4. RUN test extraction on fixture chunk                 │
│ 5. COMPARE metrics:                                     │
│    • Entity count (must be ≥95% of baseline)            │
│    • Entity type distribution (no missing types)        │
│    • Relationship count (must be ≥95% of baseline)      │
│ 6. DECISION:                                            │
│    • If PASS → commit batch, proceed to next            │
│    • If FAIL → revert batch, analyze which line broke   │
│ 7. COMMIT after each successful batch:                  │
│    git add prompts/extraction_optimized/                │
│    git commit -m "feat(prompts): compress [file] lines N-M" │
└─────────────────────────────────────────────────────────┘
```

### Batch Tracking Table

Use this table to track progress:

```markdown
| Batch | File | Lines | Status | Entity Parity | Notes |
|-------|------|-------|--------|---------------|-------|
| 2.1 | grok_json_prompt.md | 1-200 | ⬜ | - | |
| 2.2 | grok_json_prompt.md | 201-377 | ⬜ | - | |
| 3.1 | entity_detection_rules.md | 1-200 | ⬜ | - | |
| ... | ... | ... | ⬜ | - | |
```

Status: ⬜ Pending, 🔄 In Progress, ✅ Passed, ❌ Failed, ⏸️ Blocked

---

## Validation Protocol

### Automated Tests

```python
# tests/test_prompt_compression_validation.py

VALIDATION_CRITERIA = {
    "entity_parity": 0.95,       # ≥95% of baseline entities
    "relationship_parity": 0.95, # ≥95% of baseline relationships
    "workload_completeness": 0.95,  # ≥95% labor_drivers captured
    "type_coverage": 1.0,        # 100% entity types extractable
    "performance_delta": 0.10,   # ≤10% processing time increase
}
```

### Manual Spot Checks

For EACH prompt file, verify these intelligence elements are present:

| Intelligence Element | Verification Method |
|---------------------|---------------------|
| 18 entity type definitions | Search for each type name |
| PERFORMANCE_METRIC triggers | Search for "PO-X", "QASP", "Threshold" |
| SPLIT RULE | Search for "Two entities" or "two entities" |
| Naming normalization | Search for "Title Case", "FAR 52.212-1" |
| JSON schema requirements | Search for "entity_name", "entity_type" |
| Forbidden types list | Search for "NEVER" + type names |
| Decision trees | Search for numbered decision steps |
| Relationship inference rules | Each algorithm file must be complete |
| Brief rationales ("why") | Grok 4 learns from reasoning |

---

## Risk Mitigation

### Risk 1: Extraction Quality Degradation
**Mitigation**: 
- Incremental compression with validation gates
- Immediate rollback capability via `PROMPT_FORMAT=original`
- Keep original prompts permanently (no deletion)

### Risk 2: Entity Type Gaps
**Mitigation**:
- Test extraction on diverse RFP sections (Section C, L, M, J)
- Verify all 18 types appear in test extraction
- Compare entity type distribution before/after

### Risk 3: Relationship Loss
**Mitigation**:
- Focus validation on Section L↔M mapping (highest value)
- Ensure relationship inference prompts are complete
- Test with known relationship patterns

### Risk 4: Workload Driver Loss
**Mitigation**:
- Workload extraction is cost driver for BOE
- Test Appendix F extraction specifically
- Require ≥95% labor_driver completeness

---

## Files to Modify/Create

### New Files
```
prompts/extraction_optimized/
├── grok_json_prompt.txt
├── entity_detection_rules.txt
└── entity_extraction_prompt.txt

prompts/relationship_inference_optimized/
├── attachment_section_linking.txt
├── clause_clustering.txt
├── deliverable_traceability.txt
├── document_hierarchy.txt
├── document_section_linking.txt
├── evaluation_hierarchy.txt
├── instruction_evaluation_linking.txt
├── orphan_resolution.txt
├── requirement_evaluation.txt
├── semantic_concept_linking.txt
├── sow_deliverable_linking.txt
├── system_prompt.txt
└── workload_enrichment.txt

tests/
├── test_prompt_compression_baseline.py
└── test_prompt_compression_validation.py

docs/implementation_plans/
└── ISSUE_014_PROMPT_COMPRESSION.md (this file)
```

### Modified Files
```
src/extraction/json_extractor.py   # Add prompt format selection
src/core/prompt_loader.py          # Add format-aware loading
.env.example                       # Add PROMPT_FORMAT documentation
```

---

## Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Token Reduction | **30-50%** (Grok 4 target) | tiktoken count before/after |
| Entity Parity | ≥95% | Extraction comparison test |
| Relationship Parity | ≥95% | Extraction comparison test |
| Workload Completeness | ≥95% | labor_driver field inspection |
| Type Coverage | 100% | All 18 types in test output |
| Processing Time | ≤+10% | Timed extraction runs |
| Cost Savings | ~$0.25-0.42/RFP | 30-50% of ~$0.84 input cost |

### Token Reduction Breakdown (Expected)

| Compression Technique | Expected Savings |
|----------------------|------------------|
| Remove decorative symbols (⚠️⚡✅❌) | 2-3% |
| Remove markdown headers (#, ##) | 3-5% |
| Remove bold/italics formatting | 2-3% |
| Table-to-list conversion | 10-15% |
| Prose-to-bullet conversion | 10-15% |
| Example consolidation (to 3-5 per category) | 10-15% |
| Whitespace/blank line removal | 3-5% |
| **Total Expected** | **30-50%** |

---

## Rollback Procedure

If extraction quality degrades in production:

1. **Immediate**: Set `PROMPT_FORMAT=original` in `.env`
2. **Restart**: Restart the server to reload prompts
3. **Verify**: Run test extraction to confirm baseline quality restored
4. **Investigate**: Compare specific entity extraction failures
5. **Iterate**: Revert problematic compression while keeping safe optimizations

---

## Timeline (Cautious 100-200 Line Batches)

| Day | Phase | Batches | Deliverable |
|-----|-------|---------|-------------|
| 1 | Setup & Baseline | - | Branch created, directories, baseline script |
| 2 | grok_json_prompt.md | 2.1, 2.2 | First optimized file complete |
| 3-4 | entity_detection_rules.md | 3.1-3.9 | 9 batches, detection rules complete |
| 5-8 | entity_extraction_prompt.md | 4.1-4.16 | 16 batches, largest file complete |
| 9-10 | Relationship inference | 5.1-5.13 | 13 files optimized |
| 11 | Configuration Toggle | - | PROMPT_FORMAT env var, loader changes |
| 12 | Full A/B Validation | - | Complete extraction comparison |
| 13 | Production Deployment | - | Switch to optimized prompts |

**Total Effort**: ~13 days (cautious approach prioritizes quality over speed)

**Batches per Day**: ~4-5 batches maximum to allow thorough validation

---

## Appendix: Intelligence Inventory

### Entity Type Detection Patterns (MUST PRESERVE)

```
REQUIREMENT: "Contractor shall...", "must", "will" + action verb
EVALUATION_FACTOR: "will be evaluated", "adjectival rating", "most important"
SUBMISSION_INSTRUCTION: "page limit", "font size", "proposal shall"
DELIVERABLE: "CDRL", "Data Item", "submit [document]"
CLAUSE: "FAR 52.", "DFARS 252.", "incorporated by reference"
PERFORMANCE_METRIC: "PO-X", "Threshold:", "AQL", "QASP", "99.9%"
STRATEGIC_THEME: "emphasizes", "critical to", "paramount", weighted >30%
STATEMENT_OF_WORK: "Task [number]", "PWS", "SOW", "contractor shall perform"
SECTION: "Section [A-M]", "Attachment", "Annex", "Exhibit"
DOCUMENT: "Attachment J-", "[Standard] ISO/MIL-STD", referenced files
ORGANIZATION: Agency names, unit names, company names
PROGRAM: Named initiatives (MCPP II, Navy MBOS, JADC2)
EQUIPMENT: Model numbers, physical assets (M1A1 Tank, Generator Set)
LOCATION: Base names, geographic references (Camp Pendleton)
PERSON: Named individuals (rare in RFPs)
TECHNOLOGY: Software, systems, tools (SharePoint, ERP System)
CONCEPT: Abstract ideas, catch-all for non-categorized entities
EVENT: Deadlines, milestones, submission dates
```

### Critical Decision Rules (MUST PRESERVE)

1. **SPLIT RULE**: "Clean daily with 95% accuracy" → 2 entities (requirement + metric)
2. **Government skip**: "Government shall provide..." → Skip (not contractor obligation)
3. **Dual extraction**: "J-02000 PWS" → DOCUMENT + STATEMENT_OF_WORK
4. **Normalization**: Multiple formats → One entity (Section C.4 = SECTION C.4 = section c.4)
5. **Forbidden types**: Never use "other", "UNKNOWN", "process", "table", "plan", "policy", "standard", "system"

---

**Document Version**: 1.1  
**Author**: Implementation Planning Agent  
**Last Updated**: December 9, 2025  
**Methodology**: Cautious 100-200 lines per batch with validation gates  
**Review Required Before**: Branch creation
