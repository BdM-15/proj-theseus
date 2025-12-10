# Prompt Refactoring Plan: Schema-Aligned Intelligence-First Architecture

**Branch**: 037-prompt-compression-intelligence-first (continuation)  
**Issue**: #14 - Prompt Compression & Optimization  
**Created**: December 9, 2025  
**Status**: Planning Phase  
**Priority**: HIGH - Directly impacts extraction quality and cost efficiency

---

## Executive Summary

### Problem Statement

The current prompts (~78K tokens) were built early in the application lifecycle and suffer from:

1. **Structural Misalignment**: Prompts don't mirror Pydantic schema organization
2. **Redundancy**: Same concepts explained multiple times across different sections
3. **Markdown Overhead**: ~6% token waste on formatting (minimal savings achieved)
4. **Content Organization**: Mixed abstraction levels - high-level philosophy alongside detailed examples
5. **Schema Drift**: Prompts reference old patterns not aligned with current Pydantic models
6. **Grok-4 Sub-Optimization**: Not structured for Grok-4's fast-reasoning capabilities

### Opportunity

By refactoring prompts to be **schema-aligned**, **logically structured**, and **Grok-4 optimized**, we can achieve:

- **30-40% token reduction** through content reorganization (not just formatting)
- **Higher extraction quality** through clearer entity type boundaries
- **Better Pydantic compliance** through schema-mirrored prompt structure
- **Easier maintenance** through single-source-of-truth alignment
- **Lower cost** through more efficient token usage

### Strategic Approach

**Intelligence-First Refactoring**:

1. Reorganize content to mirror Pydantic schema hierarchy
2. Eliminate redundancy through cross-referential structure
3. Optimize for Grok-4's fast-reasoning (structured decision trees, not prose)
4. Create prompt templates that auto-generate from schema definitions
5. Preserve 100% of extraction intelligence

---

## Current State Analysis

### Prompt Architecture (December 2025)

**Total Tokens**: 78,596 (extraction + relationship inference)

**Current Three-File Structure**:

| Prompt File                       | Tokens     | Chars       | Lines     | Purpose                                              |
| --------------------------------- | ---------- | ----------- | --------- | ---------------------------------------------------- |
| `grok_json_prompt.txt`            | 3,485      | 14,369      | 354       | Core extraction philosophy, entity type definitions  |
| `entity_detection_rules.txt`      | 11,439     | 49,572      | 1,488     | Semantic-first detection patterns, UCF reference     |
| `entity_extraction_prompt.txt`    | 25,403     | 116,078     | 2,883     | Detailed extraction instructions, annotated examples |
| **Extraction Subtotal**           | **40,327** | **180,019** | **4,725** | Entity extraction system prompt                      |
| Relationship inference (13 files) | 33,369     | -           | -         | 8 LLM inference algorithms                           |
| **Grand Total**                   | **73,696** | -           | -         | Full system prompt                                   |

**How They're Combined** (`src/extraction/json_extractor.py`):

```python
full_prompt = f"""{json_instructions}

PART 1: ENTITY DETECTION RULES
{detection_rules}

PART 2: ENTITY EXTRACTION INSTRUCTIONS & EXAMPLES
{extraction_prompt}

PART 3: RELATIONSHIP INFERENCE RULES
{full_inference_text}
"""
```

The three files serve different purposes but are concatenated into a single system prompt for each extraction call.

### Architecture Decision: Keep Three-File Structure ✅

**Decision**: Maintain the current three-file separation. Token reduction will come from reorganizing content **within** each file, not from merging them.

**Three Files**:

1. `grok_json_prompt.txt` - Philosophy, role, output format
2. `entity_detection_rules.txt` - Semantic-first detection patterns, UCF reference
3. `entity_extraction_prompt.txt` - Detailed instructions, examples, metadata

**Rationale**: Better organization and maintainability. The three-file structure enables modular refactoring and future adaptive prompt loading.

### Schema Architecture (src/ontology/schema.py)

**18 Entity Types** organized into logical groups:

```python
# Core Enums
CriticalityLevel = Literal["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"]
RequirementType = Literal["FUNCTIONAL", "PERFORMANCE", "SECURITY", "TECHNICAL", ...]
ThemeType = Literal["CUSTOMER_HOT_BUTTON", "DISCRIMINATOR", "PROOF_POINT", "WIN_THEME"]
BOECategory = Enum("Labor", "Materials", "ODCs", "QA", "Logistics", ...)

# Entity Hierarchy
BaseEntity(BaseModel)
├── Specialized Models:
│   ├── Requirement (criticality, modal_verb, req_type, labor_drivers, material_needs)
│   ├── EvaluationFactor (weight, importance, subfactors)
│   ├── SubmissionInstruction (page_limit, format_reqs, volume)
│   ├── StrategicTheme (theme_type)
│   ├── Clause (clause_number, regulation)
│   └── PerformanceMetric (threshold, measurement_method)
└── Generic: BaseEntity (entity_name, entity_type)

# Relationships
Relationship(source_entity: BaseEntity, target_entity: BaseEntity, relationship_type: str)
```

### Key Misalignments Identified

#### 1. **Structural Disorganization**

**Current**: Prompts explain concepts in narrative prose across multiple sections

```markdown
# Section 1: Philosophy

"You are building a database..."

# Section 2: Entity Types (buried 200 lines down)

"requirement: A specific obligation..."

# Section 3: Examples (1000 lines down)

"For requirements, extract criticality..."
```

**Problem**: LLM must parse 3,000 lines to understand how to extract ONE entity type.

**Better**: Schema-mirrored structure

```markdown
# ENTITY_TYPE: requirement

## Pydantic Model:

- criticality: CriticalityLevel (MANDATORY/IMPORTANT/OPTIONAL/INFORMATIONAL)
- modal_verb: str (exact verb: shall/must/will/should/may)
- req_type: RequirementType (FUNCTIONAL/PERFORMANCE/SECURITY/...)
- labor_drivers: List[str] (volumes, frequencies, shifts)
- material_needs: List[str] (equipment, supplies, facilities)

## Detection Patterns:

- "Contractor shall..." → MANDATORY
- "Contractor should..." → IMPORTANT
- "Contractor may..." → OPTIONAL

## Examples:

[Annotated examples specific to requirements]

## Anti-Patterns:

- ❌ "Government shall..." → NOT a requirement (extract as concept)
- ❌ "99.9% uptime" → NOT a requirement (extract as performance_metric)
```

#### 2. **Redundant Content**

**Duplicate Explanations** found across 3+ locations:

| Concept                                   | Locations                                                               | Total Mentions | Consolidation Opportunity       |
| ----------------------------------------- | ----------------------------------------------------------------------- | -------------- | ------------------------------- |
| QASP/Performance Metric separation        | grok_json_prompt, entity_extraction_prompt, entity_detection_rules      | 5+             | Single authoritative section    |
| Modal verb criticality (shall/should/may) | grok_json_prompt, entity_extraction_prompt (2x), entity_detection_rules | 4+             | CriticalityLevel enum reference |
| Section L↔M mapping                       | entity_extraction_prompt, relationship_inference prompts                | 3+             | Relationship inference only     |
| FAR/DFARS clause patterns                 | entity_detection_rules, entity_extraction_prompt                        | 3+             | Single detection pattern        |

**Estimated Savings**: 15-20% through deduplication

#### 3. **Missing Schema Alignment**

**Pydantic Field Coverage**:

| Pydantic Model          | Fields Defined                                                              | Prompt Coverage                    | Gap                           |
| ----------------------- | --------------------------------------------------------------------------- | ---------------------------------- | ----------------------------- |
| `Requirement`           | 5 fields (criticality, modal_verb, req_type, labor_drivers, material_needs) | 80% - `req_type` under-explained   | Need RequirementType taxonomy |
| `EvaluationFactor`      | 3 fields (weight, importance, subfactors)                                   | 95% - good coverage                | Minor cleanup                 |
| `SubmissionInstruction` | 3 fields (page_limit, format_reqs, volume)                                  | 90% - good coverage                | Volume detection patterns     |
| `StrategicTheme`        | 1 field (theme_type)                                                        | 75% - missing PROOF_POINT examples | Need ThemeType taxonomy       |
| `PerformanceMetric`     | 2 fields (threshold, measurement_method)                                    | 85% - good split rule              | QASP table parsing            |

**Critical Gap**: `RequirementType` enum has 9 values, but prompts only explain 3:

- ✅ Covered: FUNCTIONAL, PERFORMANCE, SECURITY
- ❌ Missing: TECHNICAL, INTERFACE, MANAGEMENT, DESIGN, QUALITY, OTHER

#### 4. **Grok-4 Sub-Optimization**

**Current Format**: Narrative prose optimized for GPT-3.5/4 reasoning

```markdown
The QASP separation is critical. When you see "Contractor shall clean daily with 95% accuracy",
you need to extract two entities because the work (cleaning) is different from the measurement (95%).
This is important for workload analysis because cleaning frequency drives labor while accuracy
drives quality surveillance. The performance metric should capture the threshold...
```

**Grok-4 Optimal**: Structured decision trees

```
QASP_SPLIT_RULE:
IF sentence contains:
  - Contractor action (shall/must/will + verb)
  AND numerical standard (%, count, time)
THEN:
  entity_1 = requirement (action + frequency)
  entity_2 = performance_metric (numerical standard)
  relationship = MEASURED_BY
EXAMPLES:
  ✅ Input: "Clean daily with 95% accuracy"
     Output: [requirement: "Daily Cleaning"], [performance_metric: "95% Accuracy Standard"]
  ✅ Input: "Maintain 500 users with 4hr response"
     Output: [requirement: "500 User Support"], [performance_metric: "4hr Response Time"]
```

**Token Savings**: ~30% for same intelligence through elimination of narrative connectors

#### 5. **Validation Gaps**

**Current Prompts** reference patterns not enforced by Pydantic:

| Prompt Claim                                | Pydantic Reality                    | Fix Needed                        |
| ------------------------------------------- | ----------------------------------- | --------------------------------- |
| "Extract entity_name in Title Case"         | No validator enforces this          | Add field_validator or drop claim |
| "Normalize FAR citations to 'FAR 52.212-1'" | No normalization logic              | Add validator or drop             |
| "Relationship must have description field"  | Schema has NO description field     | Remove from prompt                |
| "Use exact modal_verb (shall/must/will)"    | Field exists but no enum constraint | Document accepted values          |

**Risk**: Prompts promise behavior code doesn't enforce → LLM wastes tokens on unused formatting

---

## Refactoring Strategy

### Phase 1: Schema-First Reorganization

**Objective**: Restructure prompts to mirror Pydantic schema hierarchy

#### 1.1 Create Schema-Aligned Templates

**New Directory Structure**:

```
prompts/
├── extraction_v2/               # Refactored prompts
│   ├── _schema_mirror/          # Auto-generated from schema.py
│   │   ├── base_entity.txt      # BaseEntity rules
│   │   ├── requirement.txt      # Requirement-specific
│   │   ├── evaluation_factor.txt
│   │   ├── submission_instruction.txt
│   │   └── ... (18 entity type files)
│   ├── system_prompt.txt        # Core extraction philosophy (500 tokens)
│   ├── detection_taxonomy.txt   # Semantic-first detection (2000 tokens)
│   └── output_format.txt        # JSON structure (500 tokens)
├── relationship_inference_v2/
│   └── ... (algorithm-specific prompts)
└── extraction/                  # Original prompts (backup)
```

#### 1.2 Schema Auto-Generation Script

**Goal**: Single source of truth - Pydantic schema generates prompt skeletons

```python
# tools/generate_schema_prompts.py
from src.ontology.schema import (
    Requirement, EvaluationFactor, SubmissionInstruction,
    CriticalityLevel, RequirementType, ThemeType
)

def generate_entity_prompt(model_class) -> str:
    """Generate prompt section from Pydantic model."""
    fields = model_class.model_fields

    prompt = f"# ENTITY_TYPE: {model_class.__name__.lower()}\n\n"
    prompt += "## Required Fields:\n"
    for name, field in fields.items():
        prompt += f"- {name}: {field.annotation} - {field.description}\n"

    # Add enum expansions
    if model_class == Requirement:
        prompt += "\n## CriticalityLevel Values:\n"
        for level in get_args(CriticalityLevel):
            prompt += f"- {level}\n"

    return prompt
```

**Benefits**:

- Schema changes auto-propagate to prompts
- Guaranteed alignment between code and instructions
- Reduces maintenance burden by 70%

#### 1.3 Reorganize Content Hierarchy

**Current** (flat, 3000 lines):

```markdown
# Entity Extraction Prompt

[Philosophy 200 lines]
[Naming rules 150 lines]
[17 entity types mixed together 1000 lines]
[Examples 1000 lines]
[Edge cases 400 lines]
[Output format 250 lines]
```

**Refactored** (hierarchical, modular):

```markdown
# Core System Prompt (500 tokens)

- Role: Government contracting knowledge graph specialist
- Task: Extract structured intelligence into JSON
- Philosophy: Structure over inference, semantic-first detection
- Model: xAI Grok-4-fast-reasoning
- Quality: Pydantic validation with 5x retry

# Detection Taxonomy (2000 tokens)

## Priority Detection Patterns

1. QASP/Performance Metrics (most common error)
2. Strategic Themes (Shipley intelligence)
3. Requirements vs Concepts (contractor obligations only)

## Entity Type Taxonomy (organized by Pydantic hierarchy)

[Include: prompts/extraction_v2/_schema_mirror/*.txt]

# Output Format (500 tokens)

- JSON schema from ExtractionResult
- Relationship format (BaseEntity objects, not strings)
- Field name reference (entity_name, entity_type, NOT name/type)

# Examples (12,000 tokens - reduced from 25,000)

[Consolidated, cross-referenced to entity types]
```

**Token Reduction**: 25,403 → ~15,000 (40% savings through reorganization)

### Phase 2: Content Deduplication

**Approach**: Eliminate redundant explanations through cross-referencing

#### 2.1 Single-Source Patterns

| Pattern                | Current Occurrences                                   | Refactored Location                  | Token Savings |
| ---------------------- | ----------------------------------------------------- | ------------------------------------ | ------------- |
| Modal verb criticality | 4x (grok_json, entity_extraction 2x, detection_rules) | CriticalityLevel enum expansion (1x) | ~600 tokens   |
| QASP split rule        | 3x (grok_json, entity_extraction, detection_rules)    | Priority detection patterns (1x)     | ~800 tokens   |
| FAR/DFARS patterns     | 3x (detection_rules, entity_extraction, examples)     | Clause detection section (1x)        | ~400 tokens   |
| Section L↔M mapping    | 3x (entity_extraction, 2x relationship prompts)       | Relationship inference only          | ~500 tokens   |
| Workload drivers       | 2x (entity_extraction, examples)                      | Requirement field description        | ~300 tokens   |

**Total Estimated Savings**: ~2,600 tokens (6.5% of extraction prompts)

#### 2.2 Example Consolidation

**Current Approach**: Full RFP examples repeated for each concept

```markdown
Example 3: PWS Appendix Structure (Real PWS) - 1200 tokens
[Shows: statement_of_work, document, concept extraction]

Example 7: Quality Requirements - 800 tokens
[Shows: SAME PWS content for different entity types]
```

**Refactored Approach**: Canonical examples with cross-references

```markdown
Example 3: PWS Appendix Structure - 1200 tokens
[Comprehensive example showing ALL relevant entity types]

Cross-References:

- statement_of_work extraction → See lines 45-52 of Example 3
- document extraction → See lines 60-68 of Example 3
- requirement extraction → See Example 4 (specific to requirements)
```

**Savings**: ~8,000 tokens through example deduplication (20% of examples)

### Phase 3: Grok-4 Optimization

**Objective**: Restructure content for Grok-4's fast-reasoning architecture

#### 3.1 Decision Tree Format

**Current** (narrative):

```markdown
When you encounter a sentence with both a contractor action and a numerical
standard, you need to carefully separate these into two entities. The action
represents the requirement (what work must be done), while the numerical
standard is the performance metric (how quality is measured). This separation
is critical for workload analysis...
```

**Tokens**: ~80

**Grok-4 Optimal** (structured):

```
QASP_SPLIT_RULE:
  CONDITION: sentence has contractor_action AND numerical_standard
  ACTION: extract_two_entities
    entity_1 = {type: requirement, content: contractor_action}
    entity_2 = {type: performance_metric, content: numerical_standard}
    relationship = MEASURED_BY
  EXAMPLES:
    "Clean daily with 95% accuracy" →
      [requirement: "Daily Cleaning"] + [performance_metric: "95% Accuracy"]
```

**Tokens**: ~55 (31% reduction, same intelligence)

#### 3.2 Pattern-Matching Templates

**Current** (free-form prose):

```markdown
Evaluation factors often include weights expressed as percentages or points.
You might see "40%" or "25 points" or "300 points out of 1000". Sometimes
they use relative importance like "Most Important" or "Significantly More
Important". Make sure to extract these into the weight and importance fields...
```

**Grok-4 Optimal** (regex-like patterns):

```
EVALUATION_FACTOR.weight_patterns:
  - /\d+%/ → "40%"
  - /\d+ points?/ → "25 points"
  - /\d+ points? out of \d+/ → "300 points out of 1000"

EVALUATION_FACTOR.importance_patterns:
  - "Most Important"
  - "Significantly More Important"
  - "More Important"
  - "Least Important"
```

**Benefits**:

- Faster LLM parsing (direct pattern matching vs prose interpretation)
- Higher consistency (deterministic pattern recognition)
- ~25% token reduction for detection patterns

#### 3.3 Enum Value Expansion

**Current**: Enums referenced but not expanded

```markdown
criticality: CriticalityLevel (MANDATORY/IMPORTANT/OPTIONAL/INFORMATIONAL)
```

**Grok-4 Optimal**: Decision matrix

```
CriticalityLevel_detection:
  MANDATORY:
    - modal_verb: shall | must | will
    - subject: Contractor | Offeror | Personnel
    - example: "Contractor shall provide support"
  IMPORTANT:
    - modal_verb: should
    - subject: Contractor | Offeror | Personnel
    - example: "Contractor should maintain 99.9%"
  OPTIONAL:
    - modal_verb: may
    - subject: Contractor | Offeror
    - example: "Contractor may use open-source tools"
  INFORMATIONAL:
    - modal_verb: shall | must
    - subject: Government
    - action: SKIP or extract as concept
```

**Coverage**: Complete RequirementType, ThemeType, BOECategory enums

### Phase 4: Validation Alignment

**Objective**: Ensure prompts only claim behavior enforced by Pydantic

#### 4.1 Audit Prompt Claims vs Schema Reality

| Prompt Claim                           | Code Reality          | Action                                        |
| -------------------------------------- | --------------------- | --------------------------------------------- |
| "Entity names must be Title Case"      | No field_validator    | **ADD** validator or **DROP** claim           |
| "Normalize clause citations"           | No normalization      | **ADD** validator or **DOCUMENT** as optional |
| "Relationships have description field" | Field doesn't exist   | **REMOVE** from prompt                        |
| "Extract exact modal_verb"             | Field exists, no enum | **DOCUMENT** accepted values                  |
| "Equipment must have model numbers"    | No validator          | **ADD** field or **DROP** requirement         |

#### 4.2 Schema-Enforced Validation

**Add Missing Validators**:

```python
class Requirement(BaseEntity):
    # ... existing fields ...

    @field_validator('modal_verb')
    @classmethod
    def validate_modal_verb(cls, v: str) -> str:
        """Ensure modal verb is from accepted set."""
        accepted = {'shall', 'must', 'will', 'should', 'may'}
        cleaned = v.lower().strip()
        if cleaned not in accepted:
            raise ValueError(f"modal_verb must be one of {accepted}, got '{v}'")
        return cleaned

    @field_validator('entity_name')
    @classmethod
    def enforce_title_case(cls, v: str) -> str:
        """Convert entity names to Title Case for consistency."""
        return v.title()
```

**Prompt Simplification**: Remove explanations of behavior enforced by code

- Before: "Entity names should be in Title Case (capitalize first letter of each significant word)"
- After: "Entity names will be auto-formatted to Title Case"

**Token Savings**: ~500 tokens (removed redundant validation explanations)

---

## Implementation Plan

### Milestone 1: Schema Alignment (Week 1)

**Deliverables**:

1. ✅ `tools/generate_schema_prompts.py` - Auto-generate entity type sections from Pydantic
2. ✅ `prompts/extraction_v2/_schema_mirror/` - 18 entity-specific prompt files
3. ✅ Add missing field validators to `src/ontology/schema.py`
4. ✅ Audit prompt claims vs schema reality (validation alignment)

**Validation**:

- Run `test_json_extraction.py` - ensure Pydantic models match prompts
- Manually review auto-generated prompts for completeness

### Milestone 2: Content Reorganization (Week 1-2)

**Deliverables**:

1. ✅ `prompts/extraction_v2/system_prompt.txt` (500 tokens) - Core philosophy
2. ✅ `prompts/extraction_v2/detection_taxonomy.txt` (2000 tokens) - Semantic-first patterns
3. ✅ `prompts/extraction_v2/output_format.txt` (500 tokens) - JSON structure
4. ✅ Consolidate examples into `prompts/extraction_v2/examples/` with cross-references

**Validation**:

- Token count verification: Target ~15,000 tokens for entity_extraction_prompt equivalent
- Content coverage audit: Ensure 100% intelligence preserved

### Milestone 3: Deduplication Pass (Week 2)

**Deliverables**:

1. ✅ Create single-source sections for repeated patterns (QASP, modal verbs, FAR patterns)
2. ✅ Implement cross-referencing system in prompts
3. ✅ Consolidate redundant examples
4. ✅ Update relationship inference prompts to reference extraction base patterns

**Validation**:

- Diff analysis: Compare old vs new content coverage
- Token measurement: Verify ~2,600 token reduction from deduplication

### Milestone 4: Grok-4 Optimization (Week 2-3)

**Deliverables**:

1. ✅ Convert narrative prose to decision trees (QASP split, criticality detection)
2. ✅ Create pattern-matching templates for detection (regex-like format)
3. ✅ Expand all enums with decision matrices (CriticalityLevel, RequirementType, ThemeType)
4. ✅ Restructure examples as test cases with expected outputs

**Validation**:

- Run extraction on MCPP RFP, compare outputs (old vs new prompts)
- Measure token reduction in system prompt

### Milestone 5: Integration & Testing (Week 3)

**Deliverables**:

1. ✅ Update `src/extraction/json_extractor.py` to load v2 prompts
2. ✅ Create A/B test harness comparing old vs new prompts
3. ✅ Run full extraction on 3 RFPs (MCPP, ADAB ISS, ADAB DFAC)
4. ✅ Measure metrics: token usage, extraction quality, entity counts, relationship counts

**Success Criteria**:

- ✅ Token reduction: 30-40% (78K → 47-55K tokens)
- ✅ Entity count parity: ±5% of baseline (v1 prompts)
- ✅ Relationship count improvement: +10% (better schema alignment)
- ✅ Pydantic validation pass rate: >95% (reduced retry attempts)
- ✅ Query quality: Same or better than baseline (user acceptance test)

### Milestone 6: Documentation & Rollout (Week 4)

**Deliverables**:

1. ✅ Update `docs/ARCHITECTURE.md` with v2 prompt architecture
2. ✅ Create `docs/prompts/PROMPT_ENGINEERING_GUIDE.md` for future maintenance
3. ✅ Update `.github/copilot-instructions.md` with v2 prompt patterns
4. ✅ Git branch merge: 037-prompt-compression-intelligence-first → main
5. ✅ Tag release: v2.0-schema-aligned-prompts

---

## Risk Assessment & Mitigation

### Risk 1: Extraction Quality Regression

**Likelihood**: Medium  
**Impact**: HIGH - Broken extraction → broken knowledge graph

**Mitigation**:

- Keep original prompts as backup (`prompts/extraction/`)
- A/B testing before full rollout (v1 vs v2 prompts on same RFPs)
- Gradual rollout: Test on 1 RFP → 3 RFPs → production
- Rollback plan: Revert `json_extractor.py` to load v1 prompts

**Acceptance Criteria**: Entity count within ±5% of baseline, relationship count ±10%

### Risk 2: Token Reduction Below Target

**Likelihood**: Low  
**Impact**: Medium - Still beneficial, but lower ROI

**Mitigation**:

- Conservative estimates: Target 30% reduction (achievable through reorganization alone)
- Phased approach: Start with deduplication (guaranteed 6.5%), then optimize
- Measure at each milestone: Track token reduction incrementally

**Fallback**: Even 20% reduction (78K → 62K tokens) = significant cost savings

### Risk 3: Schema Drift

**Likelihood**: Medium (as app evolves)  
**Impact**: Medium - Prompts become outdated again

**Mitigation**:

- Auto-generation from schema: `tools/generate_schema_prompts.py` re-run on schema changes
- CI/CD validation: Test prompts match schema on every commit
- Copilot instructions: Require schema update when adding entity types
- Quarterly audit: Review prompt-schema alignment

### Risk 4: Grok-4 Format Rejection

**Likelihood**: Low  
**Impact**: Medium - LLM may not parse structured format correctly

**Mitigation**:

- Test early: Validate decision tree format with small extractions
- Hybrid approach: Keep some narrative for context, use trees for rules
- Fallback: Revert to narrative if Grok-4 performance degrades

**Validation**: Compare extraction quality on 10-page RFP sample (v1 vs v2 prompts)

---

## Success Metrics

### Quantitative Targets

| Metric                            | Baseline (v1)                  | Target (v2)                      | Measurement Method                          |
| --------------------------------- | ------------------------------ | -------------------------------- | ------------------------------------------- |
| **Total Tokens**                  | 78,596                         | 47,000-55,000 (30-40% reduction) | tiktoken.get_encoding('cl100k_base')        |
| **Extraction Tokens**             | 40,327                         | 24,000-28,000                    | Measure entity_extraction_prompt equivalent |
| **Entity Count**                  | 1,522 (MCPP RFP)               | 1,445-1,600 (±5%)                | Neo4j count query                           |
| **Relationship Count**            | ~4,000 (MCPP RFP)              | 4,400+ (+10%)                    | Neo4j relationship count                    |
| **Pydantic Validation Pass Rate** | ~85% (5x retry)                | >95% (fewer retries)             | JsonExtractor success rate                  |
| **Cost per RFP**                  | ~$0.40 (78K tokens × 2 passes) | ~$0.24-0.28                      | xAI Grok pricing                            |

### Qualitative Targets

| Metric                   | Success Criteria                                                      |
| ------------------------ | --------------------------------------------------------------------- |
| **Query Quality**        | User acceptance: "Evaluation Factors" query returns same detail as v1 |
| **Schema Alignment**     | 100% of Pydantic fields documented in prompts                         |
| **Maintainability**      | Schema changes auto-propagate to prompts via script                   |
| **Developer Experience** | New entity type addition takes <30 minutes (vs ~2 hours with v1)      |

---

## Long-Term Vision

### Phase 7: Dynamic Prompt Assembly (Future)

**Concept**: Context-aware prompt optimization

- Detect document type (RFP vs amendment vs Q&A)
- Load only relevant entity types (e.g., skip equipment for pure services RFPs)
- Adaptive token budget: 20K for simple docs, 50K for complex multimodal

**Benefits**:

- 50-60% token reduction for simple documents
- Same extraction quality with dynamic context

### Phase 8: Few-Shot Learning Integration

**Concept**: Replace annotated examples with real extraction results

- Extract canonical examples from production runs (MCPP, ADAB, etc.)
- Store in `prompts/extraction_v2/examples_library/`
- Dynamically inject 3-5 most relevant examples based on document similarity

**Benefits**:

- Examples stay current with production patterns
- Reduce example library from 12K → 3K tokens (load on-demand)

### Phase 9: Multi-Model Optimization

**Concept**: Different prompts for different LLMs

- Grok-4: Structured decision trees (current approach)
- Claude: Narrative reasoning with XML structure
- GPT-4: Markdown with strict schema

**Benefits**:

- Optimize for each model's strengths
- Enable A/B testing across models

---

## Appendix A: Token Reduction Breakdown

### Current State (v1 Prompts)

| Section                        | Tokens     | % of Total |
| ------------------------------ | ---------- | ---------- |
| Core philosophy & role         | 800        | 2.0%       |
| Entity type definitions        | 3,500      | 8.7%       |
| Detection patterns             | 11,000     | 27.3%      |
| Annotated examples             | 20,000     | 49.6%      |
| Output format & rules          | 3,000      | 7.4%       |
| Edge cases & anti-patterns     | 2,027      | 5.0%       |
| **Total (extraction prompts)** | **40,327** | **100%**   |

### Proposed State (v2 Prompts)

| Section                                  | Tokens     | Change             | % of Total |
| ---------------------------------------- | ---------- | ------------------ | ---------- |
| Core philosophy & role                   | 500        | -300 (-38%)        | 2.1%       |
| Entity type definitions (schema-aligned) | 2,500      | -1,000 (-29%)      | 10.4%      |
| Detection taxonomy (Grok-4 optimized)    | 6,000      | -5,000 (-45%)      | 25.0%      |
| Consolidated examples                    | 12,000     | -8,000 (-40%)      | 50.0%      |
| Output format (from schema)              | 500        | -2,500 (-83%)      | 2.1%       |
| Edge cases (cross-referenced)            | 2,500      | +473 (+23%)        | 10.4%      |
| **Total (extraction prompts)**           | **24,000** | **-16,327 (-40%)** | **100%**   |

### Cost Impact

**Current Cost** (per 425-page RFP like MCPP):

- Extraction: 78,596 tokens × 2 passes × $5/M = $0.79
- Post-processing: 8 algorithms × 50 items × 10K tokens × $5/M = $0.20
- **Total**: ~$1.00 per RFP

**Projected Cost** (v2 prompts):

- Extraction: 47,000 tokens × 2 passes × $5/M = $0.47
- Post-processing: Same ($0.20)
- **Total**: ~$0.67 per RFP

**Savings**: 33% cost reduction per RFP ($0.33 per doc)

**Annual Impact** (100 RFPs/year): $33/year savings
_Note: Larger impact is extraction quality improvement and maintenance reduction_

---

## Appendix B: Schema-Prompt Alignment Matrix

### Entity Type Coverage Audit

| Entity Type                | Pydantic Fields                                                  | Prompt Coverage | Status        | Notes                            |
| -------------------------- | ---------------------------------------------------------------- | --------------- | ------------- | -------------------------------- |
| **requirement**            | criticality, modal_verb, req_type, labor_drivers, material_needs | 80%             | ⚠️ Partial    | Missing req_type taxonomy        |
| **evaluation_factor**      | weight, importance, subfactors                                   | 95%             | ✅ Good       | Minor cleanup needed             |
| **submission_instruction** | page_limit, format_reqs, volume                                  | 90%             | ✅ Good       | Volume detection patterns        |
| **strategic_theme**        | theme_type                                                       | 75%             | ⚠️ Partial    | Missing PROOF_POINT examples     |
| **clause**                 | clause_number, regulation                                        | 85%             | ✅ Good       | Need normalization examples      |
| **performance_metric**     | threshold, measurement_method                                    | 90%             | ✅ Good       | QASP table parsing solid         |
| **statement_of_work**      | (none - uses BaseEntity)                                         | 70%             | ⚠️ Partial    | Need SOW vs document distinction |
| **deliverable**            | (none - uses BaseEntity)                                         | 85%             | ✅ Good       | CDRL patterns well covered       |
| **document**               | (none - uses BaseEntity)                                         | 90%             | ✅ Good       | Attachment detection solid       |
| **section**                | (none - uses BaseEntity)                                         | 95%             | ✅ Good       | UCF reference comprehensive      |
| **program**                | (none - uses BaseEntity)                                         | 60%             | ⚠️ Needs Work | Program vs equipment unclear     |
| **equipment**              | (none - uses BaseEntity)                                         | 60%             | ⚠️ Needs Work | Model number detection weak      |
| **organization**           | (none - uses BaseEntity)                                         | 75%             | ⚠️ Partial    | Agency vs contractor detection   |
| **concept**                | (none - uses BaseEntity)                                         | 85%             | ✅ Good       | Catch-all well explained         |
| **technology**             | (none - uses BaseEntity)                                         | 70%             | ⚠️ Partial    | Software vs system unclear       |
| **location**               | (none - uses BaseEntity)                                         | 80%             | ✅ Good       | Facility vs geographic detection |
| **person**                 | (none - uses BaseEntity)                                         | 90%             | ✅ Good       | POC detection solid              |
| **event**                  | (none - uses BaseEntity)                                         | 65%             | ⚠️ Needs Work | Event vs milestone unclear       |

**Priority Fixes**:

1. Add `RequirementType` taxonomy to prompts (FUNCTIONAL/PERFORMANCE/SECURITY/TECHNICAL/INTERFACE/MANAGEMENT/DESIGN/QUALITY/OTHER)
2. Expand `ThemeType` examples (add PROOF_POINT, DISCRIMINATOR use cases)
3. Clarify program vs equipment (model numbers, physical characteristics)
4. Add event detection patterns (deadlines, milestones, Q&A sessions)

---

## Appendix C: Example Refactoring

### Before (v1 - Narrative Prose)

```markdown
## ⚠️ CRITICAL: PERFORMANCE_METRIC vs REQUIREMENT DISTINCTION

**This is the #1 extraction error. Read carefully before extracting!**

### PERFORMANCE_METRIC = Measurable Standard (How performance is judged)

**Trigger Phrases** - Extract as `performance_metric` when you see:

- "Performance Objective (PO-X)" or "PO-1", "PO-2", etc.
- "Performance Threshold:" or "Threshold:"
- "Acceptable Quality Level (AQL)"
- "Quality Assurance Surveillance Plan (QASP)"
- "Method of Surveillance:"
- Numerical standards: "99.9%", "Zero (0)", "No more than X", "At least Y%"
- "per month", "per week", "per quarter" with a metric value

### REQUIREMENT = Action/Obligation (What contractor must DO)

**Trigger Phrases** - Extract as `requirement` when you see:

- "Contractor shall...", "Contractor must...", "Contractor will..."
- Action verbs: provide, maintain, perform, deliver, ensure, implement

### ⚡ SPLIT RULE: One Sentence → Two Entities

When a sentence contains BOTH an action AND a metric, extract TWO entities!

**Example**: "Contractor shall clean equipment daily with no more than 2 defects per month."

- Entity 1 (`requirement`): "Daily Equipment Cleaning"
- Entity 2 (`performance_metric`): "Equipment Cleaning Defect Threshold" with threshold "No more than 2 defects per month"
- Relationship: requirement --MEASURED_BY--> performance_metric
```

**Token Count**: ~250 tokens

### After (v2 - Grok-4 Decision Tree)

```
PRIORITY_RULE_1: QASP_SPLIT (Performance Metric vs Requirement)

DETECTION:
  performance_metric_patterns:
    - /Performance Objective \(PO-\d+\)/
    - /Performance Threshold:/
    - /Acceptable Quality Level|AQL/
    - /QASP|Quality Assurance Surveillance/
    - /Method of Surveillance:/
    - /\d+\.?\d*%|\d+ errors?|Zero \(\d+\)|No more than \d+/
    - /per (month|week|quarter|year)/

  requirement_patterns:
    - /Contractor (shall|must|will)/
    - /(provide|maintain|perform|deliver|ensure|implement)/

SPLIT_RULE:
  IF sentence contains requirement_pattern AND performance_metric_pattern:
    EXTRACT_TWO:
      entity_1 = {
        type: requirement
        content: action + frequency
        example: "Daily Equipment Cleaning"
      }
      entity_2 = {
        type: performance_metric
        content: numerical_standard
        threshold: "No more than 2 defects per month"
        example: "Equipment Cleaning Defect Threshold"
      }
      relationship = {
        type: MEASURED_BY
        source: entity_1
        target: entity_2
      }

TEST_CASES:
  ✅ "Clean equipment daily with no more than 2 defects/month"
     → [requirement: "Daily Equipment Cleaning"]
     + [performance_metric: "Equipment Defect Threshold (≤2/month)"]

  ✅ "Maintain 500 users with 4hr response time"
     → [requirement: "500 User Support Maintenance"]
     + [performance_metric: "4-Hour Response Time Standard"]
```

**Token Count**: ~175 tokens (30% reduction)

**Benefits**:

- Clearer structure for Grok-4 fast-reasoning
- Pattern-matching format (deterministic)
- Test cases replace prose examples
- Same intelligence, 30% fewer tokens

---

## Appendix D: Related Documentation

### References

1. **Schema Definition**: `src/ontology/schema.py` - Pydantic models (single source of truth)
2. **Current Prompts**: `prompts/extraction/*.md` - v1 prompts (baseline)
3. **Architecture**: `docs/ARCHITECTURE.md` - System overview
4. **Inference Algorithms**: `docs/inference/SEMANTIC_POST_PROCESSING.md` - 8 LLM algorithms
5. **Copilot Instructions**: `.github/copilot-instructions.md` - Development patterns

### Future Planning Documents

1. **Feature Roadmap**: `docs/capture-intelligence/FEATURE_ROADMAP.md` - Future enhancements
2. **Shipley Reference**: `docs/capture-intelligence/SHIPLEY_LLM_CURATED_REFERENCE.md` - Capture intelligence
3. **Performance Optimization**: `docs/future_features/performance/` - Parallel processing plans

---

**Next Steps**: Review this plan, prioritize milestones, and begin Milestone 1 (Schema Alignment) implementation.
