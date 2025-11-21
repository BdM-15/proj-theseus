# Prompt Compression Analysis: Intelligence vs. Formatting

**Date**: November 21, 2025  
**Branch**: 022a-prompt-compression (protecting perfect run on 022)  
**Current Prompt**: 284,942 chars (~71,236 tokens) from **15 FILES**  
**Target**: 36-48% reduction WITHOUT losing domain intelligence  
**Critical Requirement**: Preserve ALL government contracting ontology expertise

---

## 🔬 Current State Analysis

### Prompt Source Architecture (15 Files Total)

The system prompt is assembled from:

1. **prompts/extraction/grok_json_prompt.md** - Base JSON formatting instructions
2. **prompts/extraction/entity_detection_rules.md** - Entity classification rules (17 types)
3. **prompts/extraction/entity_extraction_prompt.md** - Main extraction instructions + 10 annotated examples
4. **prompts/relationship_inference/\*.md** (12 files):
   - attachment_section_linking.md
   - clause_clustering.md
   - deliverable_traceability.md
   - document_hierarchy.md
   - document_section_linking.md
   - evaluation_hierarchy.md
   - instruction_evaluation_linking.md
   - requirement_evaluation.md
   - semantic_concept_linking.md
   - sow_deliverable_linking.md
   - system_prompt.md (stub)
   - workload_enrichment.md

**Construction Code**: `src/extraction/json_extractor.py` → `_load_full_system_prompt()`

### Token Economics (Perfect Run - 4 Chunks)

```
System Prompt:  71,236 tokens (284,942 chars from 15 files)
Chunk 1:         8,192 tokens
Chunk 2:         8,192 tokens
Chunk 3:         8,192 tokens
Chunk 4:         8,192 tokens
-----------------
Per Extraction: 103,004 tokens (system + 1 chunk)
Total 4 Chunks: 355,180 tokens

Cost per doc:   $0.057 (input only)
36% compression would save: $0.021 per doc
48% compression would save: $0.027 per doc
```

### The Critical Question

**Is the 285K prompt actually USING those tokens for intelligence, or is most of it formatting waste?**

**Previous Compression Attempt Failed**: The aggressive 89% compression (284K → 30K) removed critical intelligence:

- Result: 111 entities vs 368 baseline (70% regression)
- Cause: Removed examples, domain knowledge, and inference patterns
- Proof: Compression removed SUBSTANCE, not just formatting

**Key Learning**: Must preserve ALL 10 annotated examples, 50+ relationship inference patterns, and decision trees.

---

## 📊 Intelligence vs. Formatting Breakdown

### What We Absolutely CANNOT Lose (The Money Makers)

#### 1. **Entity Type Ontology (18 Types)**

- `requirement`, `evaluation_factor`, `submission_instruction`, `deliverable`, `clause`, `section`, `document`, `statement_of_work`, `performance_metric`, `strategic_theme`, `organization`, `concept`, `event`, `technology`, `person`, `location`, `program`, `equipment`
- **Intelligence**: These are DOMAIN-SPECIFIC, not generic NER
- **Current**: Listed with markdown formatting
- **Compressed**: Comma-separated list (50% reduction, zero intelligence loss)

#### 2. **Normalization Rules (Government RFP Formatting Chaos)**

```
Current (with markdown):
**Normalization Rules:**

1. **Section Names**: Always use Title Case with periods
   - ✅ CORRECT: "Section C.4 Supply"
   - ❌ WRONG: "SECTION C.4", "section c.4", "Sec C.4", "Section C-4"

Compressed (no intelligence loss):
NORMALIZATION:
Section names: Title Case with periods (Section C.4 Supply, NOT SECTION C.4/section c.4/Sec C.4)
FAR clauses: Exact citation (FAR 52.212-1, NOT far 52.212-1/FAR52.212-1)
CDRLs: Uppercase ID + name (CDRL A001 Monthly Status Report, NOT cdrl a001)
Organizations: Official caps from context (Marine Corps Prepositioning Program, NOT MARINE CORPS)
Multiple variations → extract ONCE with most complete format, merge descriptions with <SEP>
```

**Analysis**:

- **Before**: ~800 chars with checkmarks, bold, bullets
- **After**: ~350 chars with same semantic content
- **Savings**: 56% reduction
- **Intelligence Loss**: ZERO (rules are identical, just denser)

#### 3. **UCF Section Mapping (Uniform Contract Format)**

Current approach uses a **MASSIVE table** with markdown:

```markdown
| Section       | Purpose                    | Common Entity Types                  | Content Signals                                              |
| ------------- | -------------------------- | ------------------------------------ | ------------------------------------------------------------ |
| **Section A** | Solicitation/Contract Form | section, organization, person, event | SF 1449, cover page, solicitation number, POCs, Q&A deadline |
| **Section B** | Supplies/Services & Prices | section, concept, program            | CLIN/SLIN structure, pricing tables, line items, unit prices |
```

**Compressed (same intelligence)**:

```
UCF SECTIONS:
A(Solicitation Form): section,organization,person,event | Signals: SF1449,cover,solicitation#,POC,Q&A deadline
B(Supplies/Prices): section,concept,program | Signals: CLIN/SLIN,pricing tables,line items,unit prices
C(SOW): section,statement_of_work,requirement,deliverable | Signals: contractor shall,task descriptions,performance objectives
H(Special Reqs): section,requirement,person,location | Signals: clearances,key personnel,OCI,facility reqs
I(Clauses): section,clause | Signals: FAR/DFARS,52.###-##,incorporated by reference
J(Attachments): section,document,statement_of_work | Signals: Attachment,Annex,Exhibit,J-####
L(Instructions): section,submission_instruction | Signals: page limits,fonts,proposal shall,volume structure,deadlines
M(Evaluation): section,evaluation_factor | Signals: will be evaluated,factor hierarchy,importance,adjectival ratings
```

**Analysis**:

- **Before**: ~2,500 chars (table with markdown)
- **After**: ~800 chars (pipe-separated, densest format)
- **Savings**: 68% reduction
- **Intelligence Loss**: ZERO (exact same mapping rules)

#### 4. **Content Detection Signals (Critical for Semantic-First Extraction)**

**Current (verbose markdown)**:

```markdown
**EVALUATION_FACTOR Detection Signals:**

- "will be evaluated", "evaluation factor", "most important"
- "adjectival rating", "source selection", "significantly more important"
- Factor numbering (M1, M2, M2.1), Point scores (100 points total)

**SUBMISSION_INSTRUCTION Detection Signals:**

- "page limit", "font size", "proposal shall", "volume structure"
- "submit by", "electronic submission", "format requirements"
- "Times New Roman 12pt", "1-inch margins"
```

**Compressed (same intelligence)**:

```
DETECTION SIGNALS:
evaluation_factor: will be evaluated,evaluation factor,most important,adjectival rating,source selection,significantly more important,Factor numbering (M1,M2,M2.1),Point scores
submission_instruction: page limit,font size,proposal shall,volume structure,submit by,electronic submission,format requirements,Times New Roman 12pt,1-inch margins
clause: FAR/DFARS/AFFARS/NMCARS,52.###-##,252.###-####,incorporated by reference,clause title,full text
statement_of_work: Task descriptions,performance objectives,deliverables lists,contractor shall perform,Task numbering (1.0,1.1,1.1.1),SOW,PWS,SOO labels
```

**Analysis**:

- **Before**: ~1,200 chars (bullets, bold, spacing)
- **After**: ~600 chars (comma-separated inline)
- **Savings**: 50% reduction
- **Intelligence Loss**: ZERO (exact same detection rules)

#### 5. **Specialized Entity Metadata (The Unique Value)**

**Current (verbose)**:

```markdown
### Requirement Attributes

class Requirement(BaseEntity):
entity_type: Literal["requirement"] = "requirement"
criticality: CriticalityLevel = Field(..., description="MANDATORY (shall), IMPORTANT (should), OPTIONAL (may).")
modal_verb: str = Field(..., description="The exact verb used (shall, must, will, should, may).")
req_type: RequirementType = Field("OTHER", description="Functional classification of the requirement.")
labor_drivers: List[str] = Field(default_factory=list, description="Raw workload data (volumes, frequencies, shifts, quantities, customer counts) that drive staffing requirements. NOT staffing roles.")
material_needs: List[str] = Field(default_factory=list, description="List of equipment, supplies, or facilities mentioned.")
```

**Compressed (same schema)**:

```
ENTITY SCHEMAS:
Requirement: criticality(MANDATORY/IMPORTANT/OPTIONAL via shall/should/may), modal_verb(exact), req_type(FUNCTIONAL/PERFORMANCE/SECURITY/TECHNICAL/INTERFACE/MANAGEMENT/DESIGN/QUALITY/OTHER), labor_drivers(volumes,frequencies,shifts,quantities,customer counts for BOE - NOT roles), material_needs(equipment,supplies,facilities)
EvaluationFactor: weight(40%,25 points), importance(Most Important), subfactors(list of sub-criteria)
SubmissionInstruction: page_limit, format_reqs(font,margins,file format), volume(Volume I/II/III)
PerformanceMetric: threshold(99.9%,<2 errors), measurement_method(calculation/inspection)
Clause: clause_number(FAR 52.212-1), regulation(FAR/DFARS/AFFARS)
StrategicTheme: theme_type(CUSTOMER_HOT_BUTTON/DISCRIMINATOR/PROOF_POINT/WIN_THEME)
```

**Analysis**:

- **Before**: ~800 chars (Pydantic code with docstrings)
- **After**: ~650 chars (inline schema notation)
- **Savings**: 19% reduction (already pretty dense)
- **Intelligence Loss**: ZERO (same metadata structure)

#### 6. **Examples (The Gold Standard - CANNOT COMPRESS MUCH)**

**Examples are the highest-value tokens** because they show the model EXACTLY what we want. Current examples:

```markdown
**Example 1: Navy MBOS (Standard Format)**
```

Factor 2: Maintenance Approach (Most Important)

The Government will evaluate the offeror's understanding of and approach
to performing organic maintenance requirements. This factor has three
subfactors:

2.1 Staffing Plan (Significantly More Important)
2.2 Maintenance Philosophy
2.3 Transition Plan

````

**Extracted Entity**:

```json
{
  "entity_name": "Factor 2: Maintenance Approach",
  "entity_type": "evaluation_factor",
  "description": "Evaluation of offeror's maintenance approach including staffing, philosophy, and transition (Factor M2)",
  "importance": "Most Important",
  "subfactors": [
    "M2.1 Staffing Plan",
    "M2.2 Maintenance Philosophy",
    "M2.3 Transition Plan"
  ]
}
````

```

**Compressed (minimal formatting)**:
```

EXAMPLE 1: Navy MBOS evaluation factor
Input: "Factor 2: Maintenance Approach (Most Important). The Government will evaluate the offeror's understanding of and approach to performing organic maintenance requirements. This factor has three subfactors: 2.1 Staffing Plan (Significantly More Important), 2.2 Maintenance Philosophy, 2.3 Transition Plan"
Output: {"entity_name":"Factor 2: Maintenance Approach","entity_type":"evaluation_factor","description":"Evaluation of offeror's maintenance approach including staffing, philosophy, and transition (Factor M2)","importance":"Most Important","subfactors":["M2.1 Staffing Plan","M2.2 Maintenance Philosophy","M2.3 Transition Plan"]}

````

**Analysis**:
- **Before**: ~900 chars (markdown code blocks, whitespace)
- **After**: ~650 chars (inline Input/Output)
- **Savings**: 28% reduction
- **Intelligence Loss**: MINIMAL (same example content, just denser)

---

## 🎯 Compression Strategy: Format-Only Elimination

### What Gets REMOVED (Zero Intelligence Loss)

1. **Markdown Headers**: `###`, `##`, `#` → Plain text sections with `:` separator
2. **Bold/Italic**: `**text**`, `_text_` → Plain text (LLMs don't need emphasis)
3. **Code Fences**: ` ```json ``` ` → Direct JSON (no fences needed)
4. **Tables**: `| col | col |` → Pipe-separated inline or colon format
5. **Horizontal Rules**: `---` → Skip (visual separators unnecessary)
6. **Checkmarks**: `✅`, `❌` → CORRECT/WRONG prefix
7. **Numbered Lists**: `1. item` → Inline comma-separated when appropriate
8. **Bullet Lists**: `- item` → Inline comma-separated when appropriate
9. **Whitespace**: Multiple newlines → Single newline between sections

### What Gets PRESERVED (100% Intelligence)

1. **Entity Types**: All 17 types with exact names
2. **Normalization Rules**: Section formatting, clause citations, CDRL format (proven critical in perfect run)
3. **UCF Section Mapping**: A-M sections with entity types and content signals
4. **Detection Signals**: Phrase patterns for semantic-first extraction
5. **Specialized Metadata**: labor_drivers, subfactors, threshold, modal_verb, etc.
6. **ALL 10 ANNOTATED EXAMPLES**: Section L↔M mapping, requirements with criticality, attachment structure, FAR clauses, deliverables from SOW, implicit relationships, requirement→evaluation mapping, multi-agency patterns, SOW→deliverable production, strategic themes
7. **Decision Trees**: 8 decision rules for ambiguous cases (proven to prevent entity loss)
8. **Relationship Types**: EVALUATED_BY, GUIDES, CHILD_OF, ATTACHMENT_OF, PRODUCES, TRACKED_BY, etc.
9. **50+ Relationship Inference Patterns**: Topic taxonomy, agency naming conventions, semantic keyword banks, implicit hierarchy detection, L↔M mapping rules, requirement→factor mapping
10. **Domain Knowledge**: FAR/DFARS patterns, Shipley methodology, QASP separation, UCF variations

---

## 📏 Projected Compression Results

### Conservative Estimate (Format-Only Removal)

````

Current Prompt: 284,942 chars (~71,236 tokens)

Headers/emphasis: -15,000 chars (bold, headers, italics)
Code fences: -8,000 chars (``` blocks)
Tables: -25,000 chars (markdown table formatting)
Horizontal rules: -2,000 chars (---)
Checkmarks/emojis: -3,000 chars (✅ ❌ symbols)
Excess whitespace: -20,000 chars (multiple newlines, spacing)
Bullet/number lists: -30,000 chars (convert to inline)

---

Formatting savings: -103,000 chars

Remaining intelligence: 181,942 chars (~45,485 tokens)
Compression ratio: 36% reduction
Token savings per chunk: 25,751 tokens
Cost savings per doc: $0.021 (4 chunks)

```

### Aggressive Estimate (Ultra-Dense Format)

```

Additional compression:

- Inline examples: -15,000 chars (remove code block formatting)
- Compact schemas: -8,000 chars (Pydantic → inline notation)
- Dense signal lists: -12,000 chars (comma-separated, no bullets)

---

Additional savings: -35,000 chars

Ultra-compressed: 146,942 chars (~36,735 tokens)
Compression ratio: 48% reduction
Token savings per chunk: 34,501 tokens
Cost savings per doc: $0.028 (4 chunks)

````

---

## ⚠️ Critical Safety Checks

### Intelligence Validation Tests

**Before deploying ANY compression, validate against perfect run baseline**:

1. ✅ **Entity Count**: Must extract 355-381 entities (baseline: 368 ±3.5%)
2. ✅ **Relationship Count**: Must extract 147-162 relationships (baseline: 154 ±5%)
3. ✅ **Workload Drivers**: Must capture labor_drivers from workload-dense chunks (chunk 3 proven critical)
4. ✅ **Schema Compliance**: Error rate ≤1.3% (perfect run achieved 1.0%)
5. ✅ **Normalization**: Must merge "SECTION C.4" variants into single entity
6. ✅ **Section Mapping**: Must correctly classify evaluation_factor from Section M
7. ✅ **Detection Signals**: Must extract submission_instruction from embedded L-in-M patterns
8. ✅ **Query Quality**: 98%+ workload query accuracy (validated in perfect run)

### Previous Failure Analysis

**Aggressive Compression Attempt (89% reduction)**:
- Compressed prompts: 284K → 30K chars
- Results: 111 entities (70% regression)
- Error: Chunk 3 Pydantic validation failure (workload-dense section)
- Root cause: Removed critical examples showing how to extract workload requirements
- Lesson: Cannot remove examples/patterns, only formatting

### A/B Testing Protocol

```python
# tests/test_prompt_compression.py
def test_compressed_vs_original():
    """Compare compressed prompt against perfect run baseline"""

    # Test 1: Same document, both prompts
    original_result = extract_with_prompt(doc, ORIGINAL_PROMPT_285K)
    compressed_result = extract_with_prompt(doc, COMPRESSED_PROMPT_150K)

    # Validate counts within 3.5%
    assert abs(len(compressed_result.entities) - 368) <= 13  # ±3.5%
    assert abs(len(compressed_result.relationships) - 154) <= 8  # ±5%

    # Test 2: Workload driver completeness (qualitative)
    original_labor = extract_labor_drivers(original_result)
    compressed_labor = extract_labor_drivers(compressed_result)

    # Must capture same BOE intelligence
    assert len(compressed_labor) >= len(original_labor) * 0.95

    # Test 3: Schema compliance (error rate)
    original_error_rate = original_result.validation_errors / original_result.total_entities
    compressed_error_rate = compressed_result.validation_errors / compressed_result.total_entities

    # Must maintain <1.3% error rate (perfect run: 1.0%)
    assert compressed_error_rate <= 0.013
````

---

## 🚀 Implementation Plan

### Phase 1: Conservative Compression (36% reduction)

**Target**: 182K chars (~45,500 tokens) - removes ONLY formatting, keeps ALL intelligence

**Changes** (apply to all 15 prompt files):

1. Strip markdown headers (`###` → plain text with `:`)
2. Remove bold/italic (`**text**` → text)
3. Eliminate code fences (` ```json ` → direct JSON)
4. Convert tables to pipe-separated inline format
5. Remove horizontal rules
6. Replace checkmarks with CORRECT/WRONG
7. Convert bullet lists to comma-separated inline (preserve lists where structure matters)
8. Reduce whitespace (multiple newlines → single newline)

**Files to Compress**:

- prompts/extraction/grok_json_prompt.md
- prompts/extraction/entity_detection_rules.md
- prompts/extraction/entity_extraction_prompt.md
- prompts/relationship_inference/\*.md (12 files)

**Validation**:

- Run against perfect run document (afcapv_adab_iss_2025_pwstst)
- Assert 368 entities ±3.5% (355-381 range)
- Assert 154 relationships ±5% (147-162 range)
- Validate workload driver completeness (manual review chunk 3)
- Confirm 98%+ workload query accuracy

**Rollback Criteria**:

- Entity count drops below 355 (96.5% of baseline)
- Relationship count drops below 147
- Any workload drivers missing from labor_drivers field
- Workload query accuracy drops below 95%
- Error rate exceeds 1.3%

### Phase 2: Aggressive Compression (48% reduction)

**Target**: 147K chars (~36,750 tokens) - ultra-dense format

**Additional Changes** (ONLY if Phase 1 passes validation):

1. Inline examples (remove multi-line formatting while preserving content)
2. Compact Pydantic schemas to inline notation
3. Ultra-dense signal lists (comma-separated, no formatting)
4. Merge redundant rules across the 12 relationship inference files

**Validation**: Same A/B tests as Phase 1

**Risk**: Higher - may impact example clarity

### Phase 3: Example Optimization (Future - Only if Phase 2 succeeds)

**Hypothesis**: Can we identify lowest-value examples through ablation testing?

Current: 10 annotated examples in entity_extraction_prompt.md  
Target: Identify 3-5 highest-value examples

**Test Protocol**: Remove examples one-by-one, validate extraction quality after each removal

**Safety**: STOP immediately if entity count drops below 355

---

## 🔑 Key Insights

### Why This Matters

1. **Cost Efficiency**: 36-48% token reduction = 36-48% cost reduction ($0.021-$0.027 savings per doc)
2. **Context Window**: More room for larger chunks if needed
3. **Latency**: Fewer tokens = faster inference
4. **Model Compatibility**: Shorter prompts reduce risk of EOF truncation errors

### Why This is Safe

1. **Zero Intelligence Loss**: All domain expertise preserved (entity types, rules, examples, patterns)
2. **Format is Cosmetic**: Markdown helps humans, not LLMs
3. **LLMs Parse Text**: Model doesn't need bold/bullets/tables to understand
4. **Validation Gates**: Won't deploy if quality degrades
5. **Protected Baseline**: Perfect run preserved on branch 022, experiments isolated on 022a

### The Perfect Run Proves the Intelligence Works

The 368 entities / 154 relationships / 98%+ query accuracy happened WITH the bloated 285K prompt across 15 files. **We know the intelligence works**. The previous 89% compression failed because it removed SUBSTANCE (examples, patterns, domain knowledge). This conservative approach removes only PACKAGING (markdown formatting).

### Critical Learnings from Failed Attempt

1. **Cannot compress examples** - The 10 annotated examples are HIGH-VALUE tokens
2. **Cannot compress inference patterns** - 50+ relationship rules are proven critical
3. **Cannot compress decision trees** - Edge case handling prevents entity loss
4. **CAN compress formatting** - Markdown overhead is pure waste for LLMs
5. **Must validate against workload-dense chunks** - Chunk 3 failure revealed compression risk

---

## 📋 Decision: Proceed with Phase 1?

**Recommendation**: YES - Conservative compression (36% reduction) is LOW RISK, HIGH REWARD

**Risk Assessment**:

- **Format-only changes**: Removing markdown has zero semantic impact
- **All intelligence preserved**: 10 examples, 50+ patterns, decision trees intact
- **Validation gates**: Won't deploy unless 368±13 entities achieved
- **Protected baseline**: Branch 022 remains untouched, can rollback instantly
- **Proven failure mode**: We know what NOT to compress (examples/patterns)

**Next Steps**:

1. Create compressed versions of 15 prompt files (format-only changes)
2. Store as `*_COMPRESSED.txt` files alongside originals
3. Update `json_extractor.py` to support feature flag (already implemented)
4. Run A/B test against perfect run document (afcapv_adab_iss_2025_pwstst)
5. Validate all intelligence metrics:
   - Entity count: 368 ±3.5%
   - Relationship count: 154 ±5%
   - Workload drivers: Manual review chunk 3
   - Query accuracy: 98%+ on workload analysis
6. If successful → Commit to 022a, document results, consider Phase 2
7. If failed → Delete 022a, return to 022, document why

**Estimated Timeline**: 3-4 hours for implementation + validation

**Cost Savings if Successful**: $0.021 per document × scale = significant at volume

---

**Branch Structure**:

- `022` (PROTECTED): Perfect run baseline (368 entities, 154 relationships, 1.0% error rate)
- `022a-prompt-compression` (ACTIVE): Experimental compression work
- Rollback strategy: `git checkout 022; git branch -D 022a`

**Awaiting approval to proceed with Phase 1 conservative compression (format-only removal).**
