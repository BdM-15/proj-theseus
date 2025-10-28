# Test Query Reference Guide

Quick reference for testing Branch 010 Phase 1 query prompts with the current baseline data.

## 🚀 Quick Start

```bash
# Full test suite (10 queries across all 5 prompts)
python test_queries_live.py

# Quick single query (edit variables in file first)
python test_query_quick.py
```

---

## 📋 Test Queries by Prompt Type

### 1. Compliance Checklist (`compliance_checklist.md`)

**Purpose**: Pre-writing requirement tracking  
**Metadata Used**: `criticality_level`, `section_origin`, `factor_id`, `modal_verb`

#### Test Queries:

```
1. "Generate a comprehensive compliance checklist for this RFP"
   → Should produce MUST/SHOULD/MAY categorized requirements

2. "List all MUST requirements (criticality_level=MANDATORY) related to staffing"
   → Should filter by metadata field

3. "What requirements from Section L must be addressed in the technical volume?"
   → Should use section_origin metadata

4. "Show me all requirements tied to evaluation factor M-1"
   → Should use factor_id linkage

5. "Generate a deliverables checklist with submission deadlines"
   → Should extract DELIVERABLE entities with dates
```

---

### 2. Proposal Outline Generation (`proposal_outline_generation.md`)

**Purpose**: Proposal structure with page allocations  
**Metadata Used**: `factor_id`, `relative_importance`, `page_limits`, `section_l_reference`

#### Test Queries:

```
1. "Generate a proposal outline for the technical volume with page allocations"
   → Should calculate pages = volume_limit × factor_weight

2. "What are the evaluation factors in Section M and their relative weights?"
   → Should extract factor_id hierarchy with relative_importance

3. "How should I allocate 30 pages across technical subfactors?"
   → Should use factor weights for distribution

4. "What page limits apply to each proposal volume?"
   → Should extract page_limits metadata

5. "Create an outline for Volume II (Management Approach) with subsections"
   → Should use factor_id hierarchy for structure
```

---

### 3. Compliance Assessment (`compliance_assessment.md`)

**Purpose**: Post-writing Shipley 0-100 scoring  
**Metadata Used**: `criticality_level`, `modal_verb`, `requirement_type`, `priority_score`, `factor_id`

#### Test Queries:

```
1. "Assess our technical approach compliance against Section L and Section M"
   → Should score on 0-100 scale with evidence gaps

2. "What MUST requirements are we missing in our management proposal?"
   → Should filter criticality_level=MANDATORY, flag gaps

3. "Score our past performance section compliance"
   → Should use requirement_type and factor_id filtering

4. "Identify weaknesses in our security requirements coverage"
   → Should detect modal_verb="shall" + requirement_type="SECURITY"

5. "What's our compliance score for evaluation factor M-2.1?"
   → Should aggregate by factor_id
```

---

### 4. Questions for Government (`generate_qfg.md`)

**Purpose**: Strategic clarification questions  
**Metadata Used**: `criticality_level`, `section_origin`, `page_limits`, `relative_importance`, `modal_verb`

#### Test Queries:

```
1. "Generate questions for the government about page limit conflicts"
   → Should detect page_limits sum > volume limit

2. "What ambiguous requirements need clarification?"
   → Should flag vague modal_verb + subject combinations

3. "Create questions about evaluation factor weights and scoring methodology"
   → Should reference relative_importance conflicts (multiple "Most Important")

4. "What Section L instructions conflict with Section M evaluation criteria?"
   → Should use section_origin + factor_id cross-reference

5. "Generate 5-7 high-impact questions for the Q&A period"
   → Should prioritize by criticality_level + relative_importance
```

---

### 5. Win Theme Identification (`win_theme_identification.md`)

**Purpose**: Strategic differentiation  
**Metadata Used**: `relative_importance`, `requirement_type`, `factor_id`, `theme_type`, `evaluated_by_rating`

#### Test Queries:

```
1. "Identify win themes aligned with highest-weighted evaluation factors"
   → Should correlate theme_type with relative_importance="Most Important"

2. "What discriminator opportunities exist in technical requirements?"
   → Should find requirement_type="PERFORMANCE" + high factor_id weights

3. "Generate win themes for our past performance strengths"
   → Should link to factor_id for past performance + evaluated_by_rating

4. "What strategic themes differentiate us from competitors?"
   → Should use theme_type + competitive_context

5. "Create 3-5 win themes with requirement traceability"
   → Should map themes → factor_id → requirements
```

---

## 🔬 Advanced Testing Scenarios

### Metadata Field Validation

Test that queries correctly reference actual metadata fields vs. informal terms:

```python
# CORRECT - Uses actual field names
"List requirements where criticality_level=MANDATORY"
"Show factors where relative_importance='Most Important'"

# INCORRECT - Uses informal terms (may still work via NLP but less precise)
"List MUST requirements"
"Show most important factors"
```

### Cross-Prompt Consistency

Same query across different prompts should produce consistent core facts:

```
Query: "List all FAR and DFARS clauses"

compliance_checklist.md    → Should list clauses as checklist items
compliance_assessment.md   → Should list clauses with coverage assessment
generate_qfg.md           → Should reference clauses in questions
```

### Relationship Traversal

Test queries that require relationship inference:

```
"What Section L instructions are evaluated by Section M Factor 2?"
→ Requires: SUBMISSION_INSTRUCTION --EVALUATED_BY--> EVALUATION_FACTOR

"What annexes are attached to Section J?"
→ Requires: DOCUMENT --ATTACHMENT_OF--> SECTION

"What requirements link to deliverable CDRL 6011?"
→ Requires: REQUIREMENT --DELIVERED_VIA--> DELIVERABLE
```

**⚠️ WARNING**: Current baseline has **corrupted relationships** (file paths instead of semantic types). These queries will fail until re-ingestion.

---

## 🎯 Expected Baseline Behavior

Given current data quality issues:

### ✅ Should Work:

- Entity queries: "List all CLAUSE entities"
- Type filtering: "Show REQUIREMENT entities"
- Simple metadata: If fields exist in entity descriptions
- Entity counts: "How many evaluation factors?"

### ⚠️ May Not Work:

- Metadata-driven queries: No structured metadata in current baseline
- Relationship traversal: Corrupted relationship types
- Cross-section linkage: Section L↔M, annex→parent
- Precise field filters: `criticality_level=MANDATORY`

### ❌ Will Definitely Fail:

- Phase 6 relationships: `EVALUATED_BY`, `ATTACHMENT_OF`, etc.
- Agency-specific clauses: 21/26 agencies not in original extraction
- Quality validation: No validation rules applied

---

## 📊 Success Criteria

For each test query, evaluate:

1. **Response Format**: Does output match prompt instructions?
2. **Metadata Usage**: Does response reference actual metadata fields?
3. **RFP Accuracy**: Are entity names/values from actual RFP?
4. **Completeness**: Are critical entities missing?
5. **Structure**: Is output structured per prompt format?

### Rating Scale:

- ✅ **PASS**: Response format correct, uses metadata, RFP-accurate
- ⚠️ **PARTIAL**: Response correct but missing metadata intelligence
- ❌ **FAIL**: Wrong format, hallucinated data, or error

---

## 🔄 Iteration Workflow

1. Run `test_queries_live.py` to get baseline performance
2. Identify failing queries → check baseline data quality
3. For quick iteration, edit `test_query_quick.py` variables
4. Document issues in Branch 010 testing notes
5. Decide: Fix data (re-ingest) or fix prompts (enhance)

---

## 📝 Notes

- **Current baseline**: Pre-Branch 010 (no enhancements)
- **Expected limitations**: See baseline analysis for full breakdown
- **Re-ingestion decision**: Pending based on test results
- **Cost to re-ingest**: ~45 min + $0.62-0.69

---

Last Updated: 2025-10-23 (Branch 010 Phase 1 Testing)
