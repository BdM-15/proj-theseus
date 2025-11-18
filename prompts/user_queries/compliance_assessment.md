# Compliance Assessment User Query Prompt

**Purpose**: Score completed proposal draft against RFP requirements using Shipley 4-level compliance methodology AFTER writing, identifying gaps before Red Team review.

**Target User**: Proposal managers assessing draft quality, Red Team reviewers conducting formal review, capture managers evaluating go/no-go after Pink Team.

**Value Proposition**: Automated compliance scoring replicates Shipley Red Team methodology, identifying non-compliant sections BEFORE government evaluation. Flags exactly which requirements are not addressed, where they should be, and severity of impact on scoring.

**Shipley Methodology**: Compliance assessment per Shipley Proposal Guide - "Score your own proposal like the government will score it. Fix gaps before submission."

---

## Response Format Instructions

When the user requests compliance assessment, draft review, or asks "how compliant is my proposal," analyze the knowledge graph + uploaded proposal draft and respond using this structure:

### 1. EXECUTIVE COMPLIANCE SUMMARY

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMPLIANCE ASSESSMENT SUMMARY                     │
├─────────────────────────────────────────────────────────────────────┤
│ RFP: [RFP name/number]                                              │
│ Proposal Draft Reviewed: [filename uploaded by user]                │
│ Assessment Date: [current date]                                     │
│ Assessment Type: [Pink Team | Red Team | Final Review]              │
│                                                                      │
│ OVERALL COMPLIANCE RATING:                                           │
│   ┌───────────────────────────────────────────────────────────┐    │
│   │  ███████████████████░░░░░░░░  [X%] COMPLIANT              │    │
│   └───────────────────────────────────────────────────────────┘    │
│                                                                      │
│ SHIPLEY 4-LEVEL SCORING:                                             │
│   ✅ COMPLIANT:            [count] requirements ([X%])               │
│   ⚠️ PARTIALLY COMPLIANT: [count] requirements ([Y%])               │
│   ❌ NON-COMPLIANT:        [count] requirements ([Z%])               │
│   ⭕ NOT ADDRESSED:         [count] requirements ([W%])              │
│                                                                      │
│ CRITICALITY BREAKDOWN:                                               │
│   🔴 MANDATORY (SHALL/MUST): [X] total → [Y] not addressed          │
│   🟡 IMPORTANT (SHOULD):     [X] total → [Y] not addressed          │
│   ⚪ OPTIONAL (MAY):         [X] total → [Y] not addressed          │
│                                                                      │
│ RISK ASSESSMENT:                                                     │
│   ┌─────────────────────────────────────────────────────────┐      │
│   │ REJECTION RISK: [HIGH | MEDIUM | LOW]                   │      │
│   │ Reason: [X mandatory requirements NOT ADDRESSED]        │      │
│   │ Action: [Fix before submission or recommend no-bid]     │      │
│   └─────────────────────────────────────────────────────────┘      │
│                                                                      │
│ RECOMMENDED NEXT STEPS:                                              │
│   1. [Action item 1 - e.g., "Address 3 missing mandatory reqs"]     │
│   2. [Action item 2 - e.g., "Strengthen 5 partial compliance areas"]│
│   3. [Action item 3 - e.g., "Conduct Red Team in 48 hours"]         │
└─────────────────────────────────────────────────────────────────────┘
```

**Risk Thresholds** (Shipley Standards):

- **LOW RISK**: 95%+ compliant, zero mandatory NOT ADDRESSED
- **MEDIUM RISK**: 85-94% compliant, <3 mandatory PARTIALLY COMPLIANT
- **HIGH RISK**: <85% compliant OR any mandatory NOT ADDRESSED → consider no-bid

### 2. NON-COMPLIANT REQUIREMENTS (Immediate Action Required)

**Philosophy**: These are scored Unsatisfactory/Unacceptable by government. Fix immediately or expect proposal rejection.

```
❌ NON-COMPLIANT REQUIREMENTS ([count] total)

REQ-[entity_id]: [requirement_name]
RFP Reference: [Section L Para X.X, PWS Para Y.Y]
Criticality: [MANDATORY | IMPORTANT] (Modal Verb: [SHALL | SHOULD])

Why Non-Compliant:
[Specific reason - e.g., "Requirement states SHALL provide ISO 9001 certification. Proposal states 'we will obtain certification within 90 days' - does not meet SHALL standard."]

Evaluated By:
├─ Evaluation Factor: [factor_name] ([weight %])
└─ Scoring Impact: [estimated point loss - e.g., "-10 points from Technical score"]

Current Proposal Content (if any):
"[excerpt from proposal showing non-compliant response - quote exact text]"
Located at: [Volume X, Section Y.Z, Page N]

Required Fix:
[Specific action - e.g., "Replace 'will obtain' with proof of CURRENT certification. Include cert number + expiration date. Attach copy in Appendix C."]

Effort to Fix: [HIGH | MEDIUM | LOW]
└─ [Explanation - e.g., "HIGH - requires obtaining new certification (6-8 weeks), may need no-bid"]

Responsible Party: [section writer, PM, contracts, capture manager]

---
```

**Repeat for all NON-COMPLIANT requirements.**

### 3. NOT ADDRESSED REQUIREMENTS (Missing Content)

**Philosophy**: Requirement not mentioned anywhere in proposal. Government scores as "Not Addressed" = automatic rejection.

```
⭕ NOT ADDRESSED REQUIREMENTS ([count] total)

REQ-[entity_id]: [requirement_name]
RFP Reference: [Section L Para X.X]
Criticality: [MANDATORY | IMPORTANT] (Modal Verb: [SHALL | SHOULD])

Why Critical:
[Impact - e.g., "MANDATORY submission requirement. Failure to include = non-responsive bid, automatic rejection."]

Evaluated By:
├─ Evaluation Factor: [factor_name] ([weight %])
└─ Scoring Impact: [estimated point loss OR rejection risk]

Expected Location in Proposal:
[Where this should be addressed - e.g., "Technical Volume, Section 2.3 Quality Assurance, Pages 15-17"]

Required Content:
[What must be included - bullet points from requirement text]:
- [Specific item 1 from requirement]
- [Specific item 2 from requirement]
- [Specific item 3 from requirement]

Content Guidance:
[HOW to address requirement]:
1. [Approach 1 - e.g., "Reference QASP from Attachment J-03"]
2. [Approach 2 - e.g., "Provide QC process flowchart"]
3. [Approach 3 - e.g., "Include ISO 9001 certification number"]

Page Budget Impact:
├─ Estimated Pages Needed: [X pages]
└─ Current Volume Page Count: [Y of Z page limit]
    └─ [Within limit | Exceeds limit - requires compression elsewhere]

Effort to Fix: [HIGH | MEDIUM | LOW]
Responsible Party: [section writer]

---
```

**Repeat for all NOT ADDRESSED requirements.**

### 4. PARTIALLY COMPLIANT REQUIREMENTS (Needs Strengthening)

**Philosophy**: Requirement is addressed but weakly, with gaps, or without sufficient proof. Will score lower than competitors.

```
⚠️ PARTIALLY COMPLIANT REQUIREMENTS ([count] total)

REQ-[entity_id]: [requirement_name]
RFP Reference: [Section L Para X.X]
Criticality: [MANDATORY | IMPORTANT]

Current Proposal Content:
"[excerpt from proposal - quote exact text]"
Located at: [Volume X, Section Y.Z, Page N]

Why Partially Compliant:
[Gap analysis - what's missing or weak]:
✅ Addressed: [aspects that ARE covered]
❌ Missing: [aspects that are NOT covered]
⚠️ Weak: [aspects covered but without proof/detail]

Example of Strong Compliance:
"[rewrite of proposal text showing how to strengthen - include proof points, metrics, examples]"

Strengthening Actions:
1. [Action 1 - e.g., "Add past performance example demonstrating this capability"]
2. [Action 2 - e.g., "Include metric: 99.7% on-time delivery rate over 5 years"]
3. [Action 3 - e.g., "Reference specific process/procedure by name (e.g., CMMI Level 3)"]

Competitive Risk:
[Impact if not strengthened - e.g., "Competitors likely to provide stronger proof. Could drop from Excellent to Good rating, -5 points."]

Effort to Fix: [MEDIUM | LOW]
Responsible Party: [section writer]

---
```

**Repeat for all PARTIALLY COMPLIANT requirements.**

### 5. COMPLIANT REQUIREMENTS (Meets Standard)

**Summary Only** - No need to list every compliant requirement in detail during Pink/Red Team.

```
✅ COMPLIANT REQUIREMENTS ([count] total - [X%] of all requirements)

MANDATORY Requirements COMPLIANT: [count]
├─ Technical Requirements: [count]
├─ Management Requirements: [count]
└─ Past Performance Requirements: [count]

IMPORTANT Requirements COMPLIANT: [count]

Strengths to Maintain:
- [Strength 1 - e.g., "Strong past performance section with 5 excellent CPARs"]
- [Strength 2 - e.g., "Clear technical approach with process flowcharts"]
- [Strength 3 - e.g., "Comprehensive staffing plan with labor mix matrix"]

No Action Required - these sections meet or exceed requirements.
```

### 6. SECTION-BY-SECTION COMPLIANCE SCORECARD

**Purpose**: Show proposal managers which sections need the most work.

```
PROPOSAL SECTION SCORECARD:

VOLUME I: TECHNICAL PROPOSAL
Overall Compliance: [X%] ([Y] of [Z] requirements addressed)

Section 1.1: Technical Approach
├─ Requirements Assigned: [count]
├─ Compliant: [count]
├─ Partially Compliant: [count]
├─ Non-Compliant: [count]
├─ Not Addressed: [count]
└─ Section Rating: [STRONG | ADEQUATE | WEAK | FAILING]
    └─ [Action needed: e.g., "Fix 2 missing mandatory requirements"]

Section 1.2: [Next section]
[... repeat for all sections ...]

---

VOLUME II: MANAGEMENT PROPOSAL
Overall Compliance: [X%]

Section 2.1: Project Management
[... repeat structure ...]

---

VOLUME III: PAST PERFORMANCE
Overall Compliance: [X%]

Section 3.1: Relevant Experience
[... repeat structure ...]

---

VOLUME IV: COST PROPOSAL
Overall Compliance: [X%]
└─ Cost Realism Concerns: [flag if costs significantly below/above market]

---

OVERALL PROPOSAL COMPLIANCE BY VOLUME:
├─ Technical:        [X%] compliant → [Rating]
├─ Management:       [Y%] compliant → [Rating]
├─ Past Performance: [Z%] compliant → [Rating]
└─ Cost:            [W%] compliant → [Rating]
```

**Volume Ratings**:

- **STRONG**: 95%+ compliant, ready for submission
- **ADEQUATE**: 85-94% compliant, minor fixes needed
- **WEAK**: 75-84% compliant, significant rework required
- **FAILING**: <75% compliant OR any mandatory NOT ADDRESSED → major rewrite needed

### 7. EVALUATION FACTOR COMPLIANCE ANALYSIS

**Purpose**: Show how proposal will score under Section M evaluation.

```
SECTION M EVALUATION FACTOR COMPLIANCE:

FACTOR 1: [Factor Name, e.g., "Technical Approach"] (Weight: [40%])
Compliance Rating: [EXCELLENT | GOOD | ACCEPTABLE | MARGINAL | UNACCEPTABLE]

Requirements Addressed:
├─ Mandatory: [X of Y] ([Z%])
├─ Important: [A of B] ([C%])
└─ Optional: [D of E] ([F%])

Scoring Prediction:
├─ Current Estimated Rating: [GOOD] (based on partial compliance in 3 areas)
├─ Potential Rating After Fixes: [EXCELLENT] (if 3 gaps addressed)
└─ Point Estimate: [85/100] current → [95/100] after fixes

Weaknesses Affecting Score:
1. [Weakness 1 - requirement not addressed]
2. [Weakness 2 - requirement partially compliant]
3. [Weakness 3 - missing proof points]

Recommended Actions:
1. [Action 1 with priority]
2. [Action 2 with priority]
3. [Action 3 with priority]

---

FACTOR 2: [Next Factor]
[... repeat structure ...]

---

OVERALL PREDICTED TECHNICAL SCORE:
├─ Current: [X/100] ([Rating])
├─ After Recommended Fixes: [Y/100] ([Rating])
└─ Competitive Position: [How this compares to likely competitor scores]
```

### 8. CRITICAL ISSUES & RECOMMENDED ACTIONS

**Purpose**: Prioritized fix list for proposal manager.

```
CRITICAL ISSUES REQUIRING IMMEDIATE ACTION:

PRIORITY 1 - SHOWSTOPPERS (Fix before submission or no-bid):
1. REQ-[id]: [requirement_name]
   ├─ Issue: [NOT ADDRESSED - MANDATORY]
   ├─ Impact: [Automatic rejection - non-responsive bid]
   ├─ Fix: [Specific action required]
   ├─ Effort: [HIGH - may require 40+ hours or new capability]
   ├─ Owner: [responsible party]
   └─ Deadline: [date - must fix by Red Team or recommend no-bid]

[Repeat for all PRIORITY 1 issues]

---

PRIORITY 2 - SCORING RISKS (Fix to remain competitive):
1. REQ-[id]: [requirement_name]
   ├─ Issue: [PARTIALLY COMPLIANT or NON-COMPLIANT]
   ├─ Impact: [-10 points estimated on Technical score]
   ├─ Fix: [Add past performance example + metric]
   ├─ Effort: [MEDIUM - 8-16 hours]
   ├─ Owner: [section writer]
   └─ Deadline: [Red Team review date]

[Repeat for all PRIORITY 2 issues]

---

PRIORITY 3 - QUALITY ENHANCEMENTS (Nice-to-have if time permits):
1. [Enhancement 1 - strengthen win themes]
2. [Enhancement 2 - add graphics to improve readability]
3. [Enhancement 3 - tighten writing to recover page budget]

---

RESOURCE ALLOCATION RECOMMENDATIONS:
├─ Priority 1 Fixes: [X hours] → [Y FTEs for Z days]
├─ Priority 2 Fixes: [A hours] → [B FTEs for C days]
└─ Total Estimated Effort: [X+A hours]
    └─ [Realistic given timeline | Insufficient time - prioritize P1 only]
```

### 9. COMPARISON TO PROPOSAL OUTLINE

**Purpose**: Verify draft followed approved outline (from `proposal_outline_generation.md`).

```
OUTLINE ADHERENCE CHECK:

Approved Outline: [filename of outline generated earlier]
Proposal Draft: [filename of uploaded draft]

Sections Added (not in outline):
├─ [Section X.X]: [title]
│  └─ Recommendation: [Keep if adds value | Remove to stay within page limit]

Sections Missing (in outline but not in draft):
├─ [Section Y.Y]: [title]
│  └─ Impact: [Which requirements are now NOT ADDRESSED due to missing section]

Page Budget Variance:
├─ Planned Pages: [from outline]
├─ Actual Pages: [from draft]
├─ Variance: [+/- X pages]
└─ [Within limit | Exceeds limit - requires compression]

Requirement Coverage Variance:
├─ Requirements Assigned in Outline: [count]
├─ Requirements Addressed in Draft: [count]
├─ Missing Requirements: [count]
└─ [Matches plan | Gaps require immediate attention]
```

---

## Metadata Fields to Query

Use these exact field names when assessing compliance:

| Field Name            | Entity Type       | Description                                   |
| --------------------- | ----------------- | --------------------------------------------- |
| `criticality_level`   | REQUIREMENT       | 0.80+ = MANDATORY (must assess carefully)     |
| `modal_verb`          | REQUIREMENT       | SHALL/MUST = MANDATORY, SHOULD = IMPORTANT    |
| `requirement_text`    | REQUIREMENT       | Full text to compare against proposal content |
| `source_section`      | REQUIREMENT       | RFP citation for traceability                 |
| `compliance_status`   | REQUIREMENT       | User-populated during assessment              |
| `factor_id`           | EVALUATION_FACTOR | Links requirement → scoring                   |
| `relative_importance` | EVALUATION_FACTOR | Weight for scoring impact estimation          |

**Relationship Types to Traverse**:

- `REQUIREMENT` -[:ASSESSED_BY]-> `EVALUATION_FACTOR`
- `REQUIREMENT` -[:ADDRESSED_IN]-> `PROPOSAL_SECTION`
- `PROPOSAL_SECTION` -[:CONTAINS_CONTENT]-> `PROPOSAL_TEXT` (user upload)

---

## Query Examples & Expected Behavior

### Example 1: Full Compliance Assessment

**User Query**: "Assess proposal compliance" OR "How compliant is my draft?" (with uploaded proposal file)

**Expected Response**:

- Executive summary with overall compliance % and risk rating
- Detailed listing of all NON-COMPLIANT, NOT ADDRESSED, PARTIALLY COMPLIANT requirements
- Section-by-section scorecard showing which sections need work
- Prioritized action plan with effort estimates
- Comparison to approved outline

### Example 2: Mandatory Requirements Only

**User Query**: "Are all mandatory requirements addressed?"

**Expected Response**:

- Filter to requirements with `criticality_level >= 0.80` OR `modal_verb` IN (SHALL, MUST)
- Show compliance status for each mandatory requirement
- Flag any mandatory requirements that are NOT ADDRESSED or NON-COMPLIANT
- Risk assessment: HIGH if any mandatory gaps, LOW if all addressed

### Example 3: Section-Specific Assessment

**User Query**: "How compliant is the technical approach section?"

**Expected Response**:

- Filter to requirements assigned to Technical Approach section
- Show compliance breakdown for that section only
- Compare to evaluation factor scoring criteria
- Provide section rating (STRONG/ADEQUATE/WEAK/FAILING)

### Example 4: Pink Team vs Red Team Assessment

**User Query**: "Run Pink Team review" OR "Run Red Team review"

**Expected Response**:

- **Pink Team** (50% review): Focus on NOT ADDRESSED requirements, identify missing sections, flag showstoppers
- **Red Team** (75% review): Full compliance assessment, scoring predictions, competitive analysis, prioritized fix list

---

## Important Reminders

### What This Prompt DOES:

✅ Score proposal draft against RFP requirements (Shipley 4-level methodology)  
✅ Identify NON-COMPLIANT, NOT ADDRESSED, PARTIALLY COMPLIANT requirements  
✅ Predict Section M evaluation scores based on compliance  
✅ Prioritize fixes by impact (rejection risk vs. scoring risk)  
✅ Compare draft to approved outline for adherence  
✅ Provide effort estimates for remediation  
✅ Flag showstoppers requiring no-bid decision

### What This Prompt DOES NOT DO:

❌ Write missing content (identifies gaps, doesn't fill them)  
❌ Replace Red Team reviewers (automated assessment, human judgment still needed)  
❌ Guarantee proposal will win (compliance is necessary, not sufficient)  
❌ Assess competitive differentiation (focuses on meeting requirements, not exceeding them)

**Shipley Philosophy**: "Fix compliance before Red Team, not after. Every hour spent on compliance assessment saves 10 hours of rework."

---

## Quality Indicators

**High-Quality Response Includes**:

- Exact RFP citations for every non-compliant requirement
- Specific fix actions (not generic "address this requirement")
- Effort estimates based on gap severity
- Scoring impact predictions linked to evaluation factors
- Prioritized action plan with deadlines
- Risk-based go/no-bid recommendation

**Low-Quality Response Includes**:

- Generic "proposal is X% compliant" without details
- No specific fix guidance (just lists missing requirements)
- No prioritization (treats mandatory and optional gaps equally)
- No effort estimates (proposal manager can't resource fixes)
- No scoring predictions (can't assess competitive position)

---

## Shipley Proposal Guide Integration

**Key Principles** (Shipley Proposal Guide, p. 110-125):

1. **Compliance Before Differentiation**: Meet 100% of requirements BEFORE focusing on win themes
2. **Red Team as Quality Gate**: Compliance assessment at 75% mark prevents last-minute scrambles
3. **4-Level Scoring**: COMPLIANT | PARTIALLY COMPLIANT | NON-COMPLIANT | NOT ADDRESSED
4. **Risk-Based Prioritization**: Fix mandatory gaps first, then scoring risks, then enhancements
5. **Effort-Based Planning**: Realistic effort estimates enable informed go/no-bid decisions

**Compliance Levels** (Shipley Standards):

- **95%+ Compliant**: Ready for submission (minor cleanup only)
- **85-94% Compliant**: Needs targeted fixes but salvageable
- **75-84% Compliant**: Major rework required, assess timeline feasibility
- **<75% Compliant** OR **any mandatory NOT ADDRESSED**: Recommend no-bid

---

**Version**: 1.0  
**Created**: November 18, 2025  
**Branch**: 020-user-prompt-integration  
**Methodology**: Shipley Proposal Guide (Red Team Compliance Assessment)  
**Related Prompts**: Use after writing proposal, before final submission
