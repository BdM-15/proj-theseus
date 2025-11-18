# Proposal Outline Generation User Query Prompt

**Purpose**: Generate comprehensive proposal structure with page allocations, section assignments, and compliance requirements BEFORE proposal kickoff.

**Target User**: Proposal managers organizing proposal structure, capture managers planning resource allocation, section leads understanding scope.

**Value Proposition**: Shipley-based outline generation aligns proposal structure to evaluation factors, allocates pages proportionally to scoring weights, and maps requirements to sections. Replaces 10-20 hours of manual outline development.

**Shipley Methodology**: Proposal organization per Shipley Proposal Guide - "Outline to the evaluation criteria, allocate pages to scoring weights, assign requirements to appropriate sections."

---

## Response Format Instructions

When the user requests a proposal outline, structure, or asks "how should I organize my proposal," analyze the knowledge graph and respond using this structure:

### 1. PROPOSAL STRUCTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                   PROPOSAL STRUCTURE SUMMARY                         │
├─────────────────────────────────────────────────────────────────────┤
│ RFP: [RFP name/number]                                              │
│ Submission Deadline: [date from Section A]                          │
│ Total Page Limit: [from Section L] (excludes covers, TOC, resumes)  │
│                                                                      │
│ VOLUME STRUCTURE (per Section L):                                   │
│   ├─ Volume I: Technical Proposal ([X pages])                       │
│   ├─ Volume II: Management Proposal ([X pages])                     │
│   ├─ Volume III: Past Performance ([X pages])                       │
│   └─ Volume IV: Cost Proposal (not page limited)                    │
│                                                                      │
│ EVALUATION APPROACH (per Section M):                                │
│   ├─ Technical: [weight %] → [page allocation]                      │
│   ├─ Management: [weight %] → [page allocation]                     │
│   ├─ Past Performance: [weight %] → [page allocation]               │
│   └─ Price: [weight %] (Cost Realism Analysis)                      │
│                                                                      │
│ PROPOSAL DEVELOPMENT TIMELINE:                                       │
│   ├─ Kickoff: [recommended date - RFP release + 5 days]             │
│   ├─ Pink Team: [midpoint - 50% of available time]                  │
│   ├─ Red Team: [75% mark]                                           │
│   └─ Final Review: [submission - 48 hours]                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. VOLUME I: TECHNICAL PROPOSAL

**Page Allocation Strategy**: Distribute pages proportionally to evaluation factor weights + requirement complexity.

```
VOLUME I: TECHNICAL PROPOSAL (Total: [X] pages per Section L)

Evaluation Factor: [Factor 1 name, e.g., "Technical Approach"]
Weight: [40%] → Page Allocation: [12 pages] (40% of 30-page limit)

Section 1.0: [Section Title - derived from evaluation factor or Section L instruction]
Allocated Pages: [4 pages]

1.1 [Subsection Title]
   ├─ Allocated Pages: [2 pages]
   ├─ Addresses Requirements:
   │  ├─ REQ-[id]: [requirement name] (MANDATORY - Section L Para X.X)
   │  ├─ REQ-[id]: [requirement name] (IMPORTANT - PWS Para Y.Y)
   │  └─ [count] total requirements
   ├─ Evaluation Criteria (Section M):
   │  └─ "[excerpt from Section M showing what evaluators will assess]"
   ├─ Win Theme Opportunities:
   │  ├─ Theme 1: [customer pain point + your discriminator]
   │  └─ Theme 2: [strategic differentiation based on eval criteria]
   └─ Content Guidance:
      ├─ Lead with customer benefit (Shipley: answer "So what?")
      ├─ Provide proof points (past performance, metrics, examples)
      ├─ Address risk mitigation for complex requirements
      └─ Include graphics/diagrams (count against page limit)

1.2 [Subsection Title]
   [... repeat structure ...]

Section 2.0: [Next major section]
[... continue for all technical sections ...]

---

TECHNICAL VOLUME SUMMARY:
├─ Total Pages Allocated: [X] (within [Y] page limit)
├─ Page Buffer: [Y-X] pages remaining (for flexibility)
├─ Mandatory Requirements Addressed: [count]
├─ Important Requirements Addressed: [count]
└─ Evaluation Factor Coverage: [list all factors addressed in this volume]
```

### 3. VOLUME II: MANAGEMENT PROPOSAL

**Focus**: Project management, quality assurance, staffing, risk management, transition.

```
VOLUME II: MANAGEMENT PROPOSAL (Total: [X] pages per Section L)

Evaluation Factor: [Factor name, e.g., "Management Approach"]
Weight: [30%] → Page Allocation: [9 pages] (30% of 30-page limit)

Section 2.0: Management Approach
Allocated Pages: [9 pages]

2.1 Project Management
   ├─ Allocated Pages: [3 pages]
   ├─ Addresses Requirements:
   │  ├─ REQ-[id]: Weekly status reports (MANDATORY)
   │  ├─ REQ-[id]: Program Manager qualifications (MANDATORY)
   │  └─ [count] total requirements
   ├─ Required Content (Section M criteria):
   │  ├─ Organizational structure (org chart)
   │  ├─ Communication plan (government + internal)
   │  ├─ Meeting cadence (weekly, monthly, quarterly)
   │  └─ Risk management approach
   └─ Win Theme Opportunities:
      └─ Emphasize proactive communication, real-time dashboards, experienced PM

2.2 Quality Assurance
   ├─ Allocated Pages: [2 pages]
   ├─ Addresses Requirements:
   │  ├─ REQ-[id]: Quality Control Plan (MANDATORY - references QASP)
   │  ├─ REQ-[id]: ISO 9001 certification (if required)
   │  └─ [count] total requirements
   └─ Content Guidance:
      ├─ Reference QASP from Attachment J-03
      ├─ Map QC processes to SOW deliverables
      └─ Demonstrate continuous improvement methodology

2.3 Staffing Plan
   ├─ Allocated Pages: [2 pages]
   ├─ Addresses Requirements:
   │  ├─ REQ-[id]: Labor categories from CLIN structure
   │  ├─ REQ-[id]: Clearance requirements (Section H)
   │  └─ Staffing levels from PWS workload analysis
   └─ Content Guidance:
      ├─ Staffing matrix (FTEs by labor category)
      ├─ Recruitment/retention strategy
      └─ Transition plan (if incumbent replacement)

2.4 Risk Management
   ├─ Allocated Pages: [2 pages]
   └─ Content: Risk register with mitigation strategies for technical + management risks

---

MANAGEMENT VOLUME SUMMARY:
├─ Total Pages Allocated: [X] (within [Y] page limit)
├─ Mandatory Requirements Addressed: [count]
└─ Key Personnel Resumes: [count] (typically in separate attachment)
```

### 4. VOLUME III: PAST PERFORMANCE

**Focus**: Demonstrate relevant experience, customer references, CPARS excellence.

```
VOLUME III: PAST PERFORMANCE (Total: [X] pages per Section L)

Evaluation Factor: Past Performance Confidence Assessment
Weight: [20%] → Page Allocation: [6 pages] (20% of 30-page limit)

Section 3.0: Relevant Experience
Allocated Pages: [6 pages] ([2 pages per project reference])

3.1 Project Reference 1: [Project Name]
   ├─ Allocated Pages: [2 pages]
   ├─ Relevance: [95% - scope similarity, same customer, similar dollar value]
   ├─ Required Content (Section L Para 4.3):
   │  ├─ Customer POC (name, phone, email)
   │  ├─ Contract Number & Period of Performance
   │  ├─ Contract Value (total + annual)
   │  ├─ Scope Summary (100-150 words)
   │  ├─ Deliverables Completed
   │  └─ Performance Quality (CPARS ratings if available)
   ├─ Addresses Requirements:
   │  ├─ Technical similarity to SOW tasks
   │  ├─ Management complexity (multi-site, OCONUS, 24/7 ops)
   │  └─ Past performance factors from Section M
   └─ Win Theme Opportunities:
      ├─ Emphasize zero deficiencies, customer testimonials
      ├─ Highlight innovations/cost savings delivered
      └─ Demonstrate responsiveness to changes (amendments, mods)

3.2 Project Reference 2: [Project Name]
   [... repeat structure for each reference ...]

3.3 Project Reference 3: [Project Name]
   [... up to maximum allowed per Section L ...]

---

PAST PERFORMANCE SUMMARY:
├─ Total References: [count] (max allowed: [X] per Section L)
├─ Recency: [all within past 5 years per Section M]
├─ Relevance: [avg similarity score 85%+]
├─ Quality: [avg CPARS rating 4.5/5.0]
└─ Predicted Confidence Rating: SUBSTANTIAL CONFIDENCE (High/Substantial/Limited/No)
```

### 5. VOLUME IV: COST PROPOSAL (Not Page Limited)

**Focus**: Pricing strategy, cost realism, basis of estimate.

```
VOLUME IV: COST PROPOSAL (No page limit - follows Section B/CLIN structure)

CLIN Structure (from Section B):
├─ CLIN 0001: [Base Period - Year 1]
├─ CLIN 0002: [Option Period - Year 2]
├─ CLIN 0003: [Option Period - Year 3]
└─ [... additional CLINs ...]

Required Cost Elements (Section L):
├─ SF 1449 or SF 1442 (filled out completely)
├─ Cost Summary by CLIN
├─ Labor Categories & Rates
│  └─ Basis: GSA Schedule, SCA wage determination, market rates
├─ Materials & Equipment (if applicable)
├─ Other Direct Costs (ODCs)
│  ├─ Travel (if applicable)
│  ├─ Subcontracts
│  └─ Facilities/equipment rental
└─ Basis of Estimate (BOE)
   ├─ Labor: Hours by task/labor category
   ├─ Materials: Quantities from workload analysis
   └─ Cost Realism Narrative (why costs are reasonable/realistic)

Price-to-Win Strategy:
├─ Government Budget: [estimated from market research]
├─ Incumbent Pricing: [if known from FPDS]
├─ Our IGCE: [independent cost estimate]
└─ Competitive Target: [recommended bid price with justification]

---

COST VOLUME SUMMARY:
├─ Total Contract Value: $[X]M (all CLINs)
├─ Price Strategy: [% below/above estimated budget]
└─ Cost Realism Risks: [high-risk areas requiring justification]
```

### 6. ATTACHMENTS & APPENDICES

```
REQUIRED ATTACHMENTS (per Section L):

Attachment A: Key Personnel Resumes
├─ Program Manager: [name] (resume not counted against page limit)
├─ [Other key positions from Section H]
└─ Format: [SF 330 Part I, or narrative per Section L instructions]

Attachment B: Organizational Chart
├─ Shows reporting structure
└─ Includes government COR/COTR interface

Attachment C: Letters of Commitment (if teaming)
├─ Subcontractor A: [capability area]
└─ Subcontractor B: [capability area]

Attachment D: Certifications
├─ Representations and Certifications (FAR 52.204-8)
├─ Small Business Subcontracting Plan (if applicable)
└─ [Any other required certifications from Section K]

Attachment E: Past Performance Questionnaire
└─ DD Form 254 or equivalent (if required by Section L)

---

ATTACHMENT SUMMARY:
├─ Total Attachments Required: [count]
├─ Page Count Impact: [resumes/certs typically NOT counted]
└─ Submission Format: [PDF, Word, Excel per Section L]
```

### 7. COMPLIANCE CROSS-CHECK

**Purpose**: Verify outline addresses ALL mandatory requirements and evaluation factors.

```
COMPLIANCE VERIFICATION:

SECTION L REQUIREMENTS:
✅ Volume structure matches Section L instructions
✅ Page limits not exceeded (buffer: [X] pages remaining)
✅ Format requirements met (font, margins, headers per Section L)
✅ Required attachments included
✅ Submission method confirmed (electronic via [portal] or hardcopy)

SECTION M EVALUATION FACTORS:
✅ Technical Approach: [page allocation = weight %]
✅ Management Approach: [page allocation = weight %]
✅ Past Performance: [page allocation = weight %]
✅ Price: [included in Cost Volume]

MANDATORY REQUIREMENTS COVERAGE:
├─ Total Mandatory Requirements: [count]
├─ Assigned to Sections: [count] (should equal total)
├─ Unassigned Requirements: [count] (should be ZERO - flag if not)
└─ Orphaned Sections: [sections not linked to requirements - remove if unnecessary]

RISK ASSESSMENT:
├─ Page Allocation Risks: [sections with insufficient pages vs. requirement count]
├─ Resource Risks: [sections requiring specialized expertise]
└─ Timeline Risks: [sections with long lead items - e.g., new certifications]
```

### 8. SECTION ASSIGNMENT GUIDE

**Purpose**: Help proposal manager assign sections to writers.

```
SECTION ASSIGNMENT RECOMMENDATIONS:

TECHNICAL SECTIONS:
Section 1.1-1.3: Technical Approach
├─ Recommended Writer: [Chief Engineer, Technical Director]
├─ SME Support: [domain experts for specific requirements]
├─ Complexity: HIGH (core evaluation factor, 40% weight)
├─ Estimated Effort: [40 hours across kickoff → pink team]
└─ Dependencies: Requires completed workload analysis, past performance data

Section 2.1: Project Management
├─ Recommended Writer: [Proposed Program Manager]
├─ Complexity: MEDIUM (standard PM processes)
└─ Estimated Effort: [16 hours]

PAST PERFORMANCE SECTIONS:
Section 3.1-3.3: Project References
├─ Recommended Writer: [Capture Manager or Contracts]
├─ Coordination: Must contact customer POCs early (2+ weeks for references)
└─ Estimated Effort: [24 hours including customer coordination]

COST VOLUME:
├─ Recommended Writer: [Pricing/Contracts team]
├─ Dependencies: Requires approved staffing plan, BOE from technical team
└─ Estimated Effort: [60 hours for pricing + cost realism narrative]

---

TOTAL ESTIMATED EFFORT:
├─ Writing: [X hours]
├─ Review (Pink/Red Team): [Y hours]
├─ Graphics/Formatting: [Z hours]
└─ TOTAL: [X+Y+Z hours] → [FTE estimate for proposal duration]
```

---

## Metadata Fields to Query

Use these exact field names when building proposal outline:

| Field Name            | Entity Type            | Description                                           |
| --------------------- | ---------------------- | ----------------------------------------------------- |
| `factor_name`         | EVALUATION_FACTOR      | Section M evaluation factor title                     |
| `relative_importance` | EVALUATION_FACTOR      | Weight (0.40 = 40%)                                   |
| `page_limits`         | SUBMISSION_INSTRUCTION | Total pages per volume from Section L                 |
| `volume_name`         | SUBMISSION_INSTRUCTION | Technical, Management, Past Performance, Cost         |
| `format_requirements` | SUBMISSION_INSTRUCTION | Font, margins, spacing from Section L                 |
| `submission_deadline` | RFP_METADATA           | Proposal due date from Section A                      |
| `criticality_level`   | REQUIREMENT            | Prioritize mandatory (0.80+) in outline               |
| `requirement_type`    | REQUIREMENT            | Technical, Management, Performance, Administrative    |
| `source_section`      | REQUIREMENT            | Maps requirement to RFP section for content reference |

**Relationship Types to Traverse**:

- `EVALUATION_FACTOR` -[:HAS_SUBFACTOR]-> `EVALUATION_SUBFACTOR`
- `EVALUATION_FACTOR` -[:ASSESSED_BY]-> `SUBMISSION_INSTRUCTION`
- `REQUIREMENT` -[:ADDRESSED_IN]-> `PROPOSAL_SECTION` (inferred from factor linkage)
- `REQUIREMENT` -[:REQUIRES_EVIDENCE]-> `PAST_PERFORMANCE_PROJECT`

---

## Query Examples & Expected Behavior

### Example 1: Complete Proposal Outline

**User Query**: "Generate proposal outline" OR "What should my proposal structure look like?"

**Expected Response**:

- Full 4-volume structure with page allocations per volume
- Section-by-section breakdown with page budgets proportional to weights
- Requirement assignments showing which requirements addressed in each section
- Compliance cross-check verifying 100% coverage
- Section assignment recommendations with effort estimates

### Example 2: Technical Volume Only

**User Query**: "Outline the technical volume" OR "How should I organize technical approach?"

**Expected Response**:

- Technical volume sections based on Section M technical evaluation factors
- Page allocation proportional to factor weights
- Requirement mapping showing which technical requirements in each section
- Win theme opportunities per section
- Content guidance (lead with benefits, provide proof points, address risks)

### Example 3: Page Budget Optimization

**User Query**: "How should I allocate [X] pages across evaluation factors?"

**Expected Response**:

- Page allocation formula: (factor_weight / sum_weights) × total_pages
- Adjustments for mandatory requirements (add pages if high requirement density)
- Adjustments for past performance (may need more pages despite lower weight for CPARS)
- Buffer pages (hold 10% for flexibility/graphics)

### Example 4: Section Assignment Help

**User Query**: "Who should write each section?"

**Expected Response**:

- Section-by-section writer recommendations based on complexity
- SME support needs for specialized requirements
- Effort estimates per section
- Dependencies (e.g., cost volume needs technical staffing plan first)
- Timeline recommendations (sections with long lead items start early)

---

## Important Reminders

### What This Prompt DOES:

✅ Generate complete proposal outline aligned to Section L/M  
✅ Allocate pages proportionally to evaluation factor weights  
✅ Map requirements to proposal sections for assignment  
✅ Identify win theme opportunities per section  
✅ Provide compliance cross-check (100% coverage verification)  
✅ Estimate effort and recommend section assignments  
✅ Save 10-20 hours of manual outline development

### What This Prompt DOES NOT DO:

❌ Write proposal content (writers use outline as framework)  
❌ Make technical/management decisions (outline shows WHAT to address, not HOW)  
❌ Replace proposal kickoff meeting (outline is input to kickoff, not output)  
❌ Guarantee proposal compliance (writers must follow outline + address requirements)

**Shipley Philosophy**: "Outline to the evaluation criteria. Evaluators score what they can find, not what you intended to say."

---

## Quality Indicators

**High-Quality Response Includes**:

- Page allocations match evaluation factor weights (±10% acceptable for adjustment)
- Every mandatory requirement assigned to a section (zero orphans)
- Section titles derived from evaluation factor language (mirror Section M)
- Content guidance showing HOW to address requirements (not just WHAT)
- Win theme opportunities tied to customer pain points and discriminators
- Effort estimates realistic for proposal timeline

**Low-Quality Response Includes**:

- Generic proposal outline not tailored to RFP (could apply to any solicitation)
- Page allocations don't reflect factor weights (e.g., 40% factor gets 10% of pages)
- Missing requirement-to-section mapping (writers don't know what to address where)
- No win theme guidance (outline enables compliance, not differentiation)
- Unrealistic effort estimates (e.g., 40-page technical section = 8 hours)

---

## Shipley Proposal Guide Integration

**Key Principles** (Shipley Proposal Guide, p. 90-110):

1. **Outline to Evaluation Criteria**: Section titles/structure mirror Section M factors
2. **Page Allocation = Weight**: Distribute pages proportionally to scoring importance
3. **Compliance Foundation**: Every requirement assigned to a section BEFORE writing
4. **Win Theme Integration**: Outline shows WHERE to emphasize discriminators
5. **Proposal Reuse**: Well-structured outline enables section reuse across similar RFPs

**Proposal Organization Best Practices**:

- Lead sections with executive summaries (answer "So what?" up front)
- Use action captions as section headers (customer benefit + proof)
- Place win themes in first paragraph of each major section
- Include compliance matrix as front matter (requirement → page reference)

---

**Version**: 1.0  
**Created**: November 18, 2025  
**Branch**: 020-user-prompt-integration  
**Methodology**: Shipley Proposal Guide (Proposal Organization & Planning)  
**Related Prompts**: Use `compliance_checklist.md` first, then generate outline
