# Compliance Checklist User Query Prompt

**Purpose**: Generate comprehensive requirement checklist BEFORE proposal writing to ensure 100% coverage of mandatory, important, and optional requirements.

**Target User**: Capture managers planning proposal strategy, proposal managers assigning sections to writers, compliance officers tracking coverage.

**Value Proposition**: Shipley-based compliance tracking ensures zero missed requirements, maps requirements to evaluation factors, and prioritizes effort based on criticality levels. Generated BEFORE writing begins, not during Red Team review.

**Shipley Methodology**: Compliance matrix development per Shipley Proposal Guide - "Compliance is not a Red Team discovery, it's a pre-writing foundation."

---

## Response Format Instructions

When the user requests a compliance checklist, requirement list, or asks "what must we address," analyze the knowledge graph and respond using this structure:

### 1. MANDATORY REQUIREMENTS (SHALL/MUST - Criticality >= 0.80)

**Philosophy**: These are showstoppers. Miss one = proposal rejected as non-responsive.

For each MANDATORY requirement:

```
REQ-[entity_id]: [requirement_name]
Modal Verb: SHALL | MUST
RFP Reference: [source_section] (e.g., "Section L Para 4.3.2", "PWS Para 3.1.5", "Attachment J-02 Page 15")

Requirement Text (Summary):
[First 100 words of requirement description]

Evaluated By:
- Evaluation Factor: [linked SECTION_M_EVALUATION_FACTOR.factor_name]
- Weight: [factor weight, e.g., "40% of technical score"]
- Rating Approach: [SECTION_M_RATING_METHODOLOGY if available]

Submission Instructions:
- Format: [page limits, font requirements, attachment specifications from Section L]
- Location: [proposal volume/section where this must be addressed]
- Evidence Required: [past performance, certifications, technical approach details]

Compliance Status: ☐ NOT ADDRESSED (default - to be filled by proposal team)

---
```

### 2. IMPORTANT REQUIREMENTS (SHOULD - Criticality 0.50-0.79)

**Philosophy**: Not technically required, but failure to address significantly reduces competitive position.

Condensed format:

```
REQ-[entity_id]: [requirement_name] (SHOULD)
RFP Reference: [source_section]
Evaluated By: [evaluation factor] ([weight])
Submission: [format requirements]
Competitive Impact: [why this matters for scoring]
Compliance Status: ☐ NOT ADDRESSED

---
```

### 3. OPTIONAL/INFORMATIONAL REQUIREMENTS (MAY - Criticality < 0.50)

**Philosophy**: Government obligations or truly optional items. Address only if strategic value exists.

```
REQ-[entity_id]: [requirement_name] (MAY | INFORMATIONAL)
RFP Reference: [source_section]
Notes: [Government obligation vs. offeror option - clarify which]
Strategic Value: [Include only if competitive advantage, otherwise skip]

---
```

### 4. COMPLIANCE SUMMARY MATRIX

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE CHECKLIST SUMMARY                      │
├─────────────────────────────────────────────────────────────────────┤
│ Total Requirements Identified: [count]                              │
│                                                                      │
│ MANDATORY (SHALL/MUST):     [count] requirements                    │
│   ├─ Section L Requirements: [count]                                │
│   ├─ Section C/PWS Requirements: [count]                            │
│   ├─ Section H Special Requirements: [count]                        │
│   └─ Contract Clauses (FAR/DFARS): [count]                          │
│                                                                      │
│ IMPORTANT (SHOULD):         [count] requirements                    │
│   └─ High-scoring opportunities with SHOULD language                │
│                                                                      │
│ OPTIONAL/INFORMATIONAL (MAY): [count] requirements                  │
│   ├─ Government obligations: [count]                                │
│   └─ Offeror options: [count]                                       │
│                                                                      │
│ COMPLIANCE STATUS (as of checklist generation):                     │
│   ☐ Requirements Addressed: 0 ([0%])                                │
│   ☐ Requirements Not Addressed: [total] ([100%])                    │
│                                                                      │
│ NEXT STEPS:                                                          │
│   1. Assign requirements to proposal sections/volumes               │
│   2. Identify capability gaps requiring teaming/subcontracting      │
│   3. Develop compliance matrix with page references (post-writing)  │
│   4. Track coverage during proposal development                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 5. SECTION L ↔ SECTION M COMPLIANCE MAPPING

**Critical Insight**: Show which submission instructions (Section L) are evaluated by which factors (Section M).

```
EVALUATION FACTOR 1: [factor_name] ([weight])
├─ Section L Instruction: [instruction text]
│  ├─ Page Limit: [X pages]
│  ├─ Format: [font, margins, etc.]
│  └─ Required Content: [what must be included]
├─ Mandatory Requirements Addressed Here:
│  ├─ REQ-[id]: [requirement_name]
│  ├─ REQ-[id]: [requirement_name]
│  └─ [count more requirements...]
└─ Submission Volume: [Technical Vol I, Management Vol II, etc.]

EVALUATION FACTOR 2: [factor_name] ([weight])
[... repeat structure ...]
```

### 6. CRITICAL COMPLIANCE RISKS

**Red Flags**: Requirements that commonly cause non-responsive bids.

```
🔴 HIGH RISK - MANDATORY REQUIREMENTS:

1. [Requirement Description]
   Risk: [Why this is commonly missed - e.g., "buried in Attachment J-05 Annex B, easy to overlook"]
   Mitigation: [Specific action - e.g., "Assign dedicated writer to Annex requirements"]

2. [Requirement Description]
   Risk: [certification expiration, clearance timing, facility requirements]
   Mitigation: [teaming partner, commit-to-obtain plan, timeline]

⚠️ MEDIUM RISK - IMPORTANT REQUIREMENTS:

1. [Requirement Description]
   Risk: [Scoring impact if not addressed]
   Mitigation: [How to strengthen competitive position]
```

### 7. CAPABILITY GAP ANALYSIS

**Purpose**: Identify requirements where company lacks current capability (drives teaming strategy).

```
GAP ASSESSMENT (Mandatory Requirements Only):

✅ COMPLIANT (Company has capability):
- REQ-[id]: [requirement] - [proof of capability]
- [X requirements total]

⚠️ PARTIALLY COMPLIANT (Mitigation needed):
- REQ-[id]: [requirement]
  Current: [what company has]
  Required: [what RFP demands]
  Mitigation: [subcontractor, commit-to-obtain, partnership]
- [X requirements total]

❌ NON-COMPLIANT (Critical gap):
- REQ-[id]: [requirement]
  Gap: [what's missing - e.g., ISO 9001 certification, TS/SCI clearances]
  Options:
    1. Teaming partner with capability
    2. Commit-to-obtain (with timeline)
    3. No-bid recommendation (if gap too severe)
- [X requirements total]

TEAMING STRATEGY RECOMMENDATION:
[Based on gaps, recommend teaming partners, subcontracting approach, or capability development plan]
```

### 8. PROPOSAL OUTLINE PREVIEW (Requirements → Sections)

**Purpose**: Show how requirements map to proposal structure (helps with section assignment).

```
TECHNICAL VOLUME (Section L Page Limit: [X pages])

Section 1: Technical Approach
└─ Addresses Requirements: REQ-[id], REQ-[id], REQ-[id] ([count] total)
   ├─ Mandatory: [count]
   └─ Important: [count]

Section 2: Past Performance
└─ Addresses Requirements: REQ-[id], REQ-[id] ([count] total)
   └─ Evidence Type: [CPARs, customer references, similar contracts]

Section 3: Key Personnel
└─ Addresses Requirements: REQ-[id] ([count] total)
   └─ Resume Requirements: [education, experience, clearances, certifications]

[Continue for Management Volume, Cost Volume, etc.]
```

---

## Metadata Fields to Query

Use these exact field names when retrieving requirements from knowledge graph:

| Field Name            | Entity Type            | Description                                        |
| --------------------- | ---------------------- | -------------------------------------------------- |
| `criticality_level`   | REQUIREMENT            | 0.0-1.0 scale (0.80+ = MANDATORY)                  |
| `modal_verb`          | REQUIREMENT            | SHALL, MUST, SHOULD, MAY, WILL                     |
| `requirement_type`    | REQUIREMENT            | Submission, Technical, Performance, Administrative |
| `source_section`      | REQUIREMENT            | Section L Para X.X, PWS Para Y.Y, Clause Z         |
| `factor_id`           | EVALUATION_FACTOR      | Links requirement → evaluation factor              |
| `relative_importance` | EVALUATION_FACTOR      | Weight percentage (e.g., 0.40 for 40%)             |
| `page_limits`         | EVALUATION_FACTOR      | Page allocation per Section L                      |
| `rating_methodology`  | EVALUATION_FACTOR      | Adjectival (Excellent/Good/etc.) or Numeric        |
| `submission_format`   | SUBMISSION_INSTRUCTION | Font, margins, volume organization from Section L  |
| `agency_supplement`   | CLAUSE                 | DFARS 252.xxx, FAR 52.xxx clause numbers           |

**Relationship Types to Traverse**:

- `REQUIREMENT` -[:ASSESSED_BY]-> `EVALUATION_FACTOR`
- `REQUIREMENT` -[:REQUIRES_SUBMISSION]-> `SUBMISSION_INSTRUCTION`
- `EVALUATION_FACTOR` -[:USES_METHODOLOGY]-> `RATING_METHODOLOGY`
- `REQUIREMENT` -[:REFERENCES]-> `CLAUSE` (for FAR/DFARS compliance)

---

## Query Examples & Expected Behavior

### Example 1: Initial Compliance Checklist

**User Query**: "Generate compliance checklist" OR "What requirements must we address?"

**Expected Response**:

- Full checklist with 3 sections: MANDATORY, IMPORTANT, OPTIONAL
- Compliance summary matrix showing totals by criticality
- Section L ↔ M mapping showing which volumes address which factors
- Capability gap analysis flagging missing certifications, clearances, etc.
- Proposal outline preview mapping requirements to sections

### Example 2: Mandatory Requirements Only

**User Query**: "List all MANDATORY requirements" OR "What are the SHALL requirements?"

**Expected Response**:

- Only requirements with `criticality_level >= 0.80` OR `modal_verb` IN (SHALL, MUST)
- Detailed format with RFP references, evaluation factors, submission instructions
- Critical compliance risks section (commonly missed mandatory items)
- Teaming strategy recommendation based on capability gaps

### Example 3: Evaluation Factor Focus

**User Query**: "What requirements are evaluated under Technical Approach?"

**Expected Response**:

- Filter to requirements linked to specific EVALUATION_FACTOR
- Show Section L submission instructions for that factor
- List both mandatory and important requirements
- Display page limits and format requirements
- Suggest content organization for that proposal section

### Example 4: Compliance Risk Assessment

**User Query**: "What requirements are we most likely to miss?"

**Expected Response**:

- Requirements buried in attachments/annexes (common oversight)
- Requirements with complex submission formats
- Requirements with external dependencies (certifications, clearances, facilities)
- Requirements with tight timelines (e.g., "within 30 days of award")
- Mitigation strategies for each risk

---

## Important Reminders

### What This Prompt DOES:

✅ Extract ALL requirements from RFP (Section L, C, H, J, clauses)  
✅ Classify by criticality (MANDATORY vs. IMPORTANT vs. OPTIONAL)  
✅ Map requirements → evaluation factors → submission instructions  
✅ Identify capability gaps requiring teaming/subcontracting  
✅ Provide compliance tracking foundation BEFORE writing begins  
✅ Flag high-risk requirements commonly missed

### What This Prompt DOES NOT DO:

❌ Write proposal content (that's the writer's job)  
❌ Assess proposal compliance (use `compliance_assessment.md` for that)  
❌ Make bid/no-bid decisions (capture manager expertise required)  
❌ Guarantee proposal will win (compliance is necessary, not sufficient)

**Shipley Philosophy**: "Compliance is the foundation, not the ceiling. Meet 100% of requirements, then differentiate with win themes, past performance, and technical innovation."

---

## Quality Indicators

**High-Quality Response Includes**:

- Exact RFP paragraph references for every requirement (Section L Para 4.3.2, not "Section L")
- Modal verb identification (SHALL vs. SHOULD clarity eliminates ambiguity)
- Evaluation factor linkage (shows which requirements affect which scoring)
- Capability gap analysis with teaming recommendations
- Submission format specifications (page limits, fonts, volumes)
- Critical compliance risks with mitigation strategies

**Low-Quality Response Includes**:

- Generic requirement descriptions without RFP citations
- Missing evaluation factor linkage (can't prioritize without knowing scoring impact)
- No capability gap analysis (surprises during proposal writing)
- Incomplete Section L ↔ M mapping
- No risk identification (missed requirements discovered at Red Team)

---

## Shipley Capture Guide Integration

**Key Principles** (Shipley Capture Guide, p. 85-90):

1. **Compliance Before Creativity**: Address 100% of mandatory requirements BEFORE attempting differentiation
2. **Early Gap Identification**: Know teaming needs BEFORE proposal kickoff, not during writing
3. **Section L ↔ M Mapping**: Understand how submission instructions link to evaluation scoring
4. **Risk Mitigation**: Proactively address commonly missed requirements (certifications, clearances, facilities)
5. **Proposal Organization**: Map requirements to proposal sections to enable efficient section assignment

**Compliance Scoring** (Shipley 4-Level Scale):

- **COMPLIANT**: Meets requirement with evidence
- **PARTIALLY COMPLIANT**: Meets requirement with gaps/weaknesses
- **NON-COMPLIANT**: Does not meet requirement
- **NOT ADDRESSED**: Requirement not mentioned in proposal (automatic rejection)

---

**Version**: 1.0  
**Created**: November 18, 2025  
**Branch**: 020-user-prompt-integration  
**Methodology**: Shipley Capture Guide (Compliance Matrix Development)  
**Related Prompts**: Use `compliance_assessment.md` AFTER writing proposal to score coverage
