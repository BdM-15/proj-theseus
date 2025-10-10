# Capture Manager Query Library

**Purpose**: Pre-built queries for common capture/proposal development tasks  
**Audience**: Capture Managers, Proposal Managers, Technical Writers  
**Methodology**: Based on Shipley Capture Guide and Proposal Guide principles  
**Usage**: Copy query → Paste into chat → Get structured intelligence

---

## Category 1: Evaluation Factor Analysis

### Query 1.1: Factor Breakdown with Elements

```
What are the factor elements for [FACTOR NAME]?

Example: "What are the factor elements for past performance?"
```

**Expected Output**:

- Sub-factors or evaluation criteria
- Relative importance/weights
- Requirements that map to each element
- Page limits or formatting guidance

**Shipley Reference**: Capture Guide p.85-90 (Evaluation Factor Analysis)

---

### Query 1.2: Cross-Factor Relationships

```
What are the evaluation factors regarding [TOPIC]?

Example: "What are the evaluation factors regarding management?"
```

**Expected Output**:

- Primary factors (direct match)
- Adjacent factors (mentioned nearby in Section M)
- Hidden relationships with notes
- Example insight: "Safety Factor - Although not directly related to management approach, safety is mentioned alongside factor 2"

**Shipley Reference**: Proposal Guide p.120-125 (Evaluation Factor Mapping)

---

### Query 1.3: Factor Weight Distribution

```
Show me all evaluation factors ordered by weight, with page limits and requirements count.
```

**Expected Output**:

```
1. Technical Approach - 40% (10 pages, 18 requirements)
2. Management Approach - 30% (8 pages, 12 requirements)
3. Past Performance - 20% (5 pages, 3 requirements)
4. Price - 10% (Not scored, Cost Realism Analysis)
```

**Use Case**: Proposal resource allocation (effort = weight × requirements)

---

## Category 2: Pain Point & Win Theme Analysis

### Query 2.1: Customer Pain Points

```
What are the main pain points of the customer and how would we effectively address them in a proposal? Which evaluation factors would we address them?
```

**Expected Output**:

- Identified pain points from Section C (SOW)
- Affected evaluation factors
- Required capabilities to address
- Competitive opportunities for differentiation

**Shipley Reference**: Capture Guide p.25-35 (Customer Intelligence)

---

### Query 2.2: Win Theme Identification

```
Based on mandatory requirements, high-weight factors, and customer pain points, what are the top 5 win themes for this proposal?
```

**Expected Output**:

```
WIN_THEME_001: Zero-Downtime Migration
- Factor: Technical Approach (40%)
- Pain Point: "Legacy system causing 10% downtime"
- Requirements: REQ-012 (MANDATORY), REQ-015 (IMPORTANT)
- Discriminator: Phased migration during off-hours
- Shipley Score: 95/100
```

**Shipley Reference**: Proposal Guide p.45-55 (Win Theme Development)

---

### Query 2.3: Competitive Analysis Gap

```
What capabilities or past performance do we need to demonstrate that aren't explicitly required but would strengthen our position?
```

**Expected Output**:

- Implicit requirements (should-haves, not must-haves)
- Industry best practices mentioned in Section C
- Adjacent capabilities that score higher
- Ghost requirements (things competitors might miss)

**Shipley Reference**: Capture Guide p.60-70 (Competitive Strategy)

---

## Category 3: Proposal Outline & Structure

### Query 3.1: Complete Proposal Outline

```
Based on the proposal instructions, provide me a bulletized proposal outline and specifics on the content I should address the customer pain points and identify solutioning opportunities that may gain me more favor in the award decision.
```

**Expected Output**:

```
VOLUME I: TECHNICAL PROPOSAL

1. Technical Approach (40% weight, 10 pages)
   1.1 System Architecture
       - REQ-012: Cloud integration (MANDATORY)
       - Pain Point: Legacy system downtime
       - Solution: Zero-downtime phased migration
       - Page allocation: 3 pages

   1.2 Cybersecurity Controls
       - REQ-027: NIST 800-171 compliance (MANDATORY)
       - Pain Point: Data breach risks
       - Solution: Multi-layer defense with SIEM
       - Page allocation: 2 pages

2. Management Approach (30% weight, 8 pages)
   [...]
```

**Shipley Reference**: Proposal Guide p.90-110 (Proposal Organization)

---

### Query 3.2: Compliance Matrix Generation

```
Generate a compliance matrix showing all requirements mapped to proposal sections and evaluation factors.
```

**Expected Output**:
| Requirement ID | Description | Criticality | Proposal Section | Evaluation Factor | Page Ref |
|----------------|-------------|-------------|------------------|-------------------|----------|
| REQ-012 | Cloud integration | MANDATORY | 1.1 System Architecture | Technical Approach | TBD |
| REQ-043 | Weekly status reports | MANDATORY | 2.2 Reporting | Management Approach | TBD |

**Shipley Reference**: Proposal Guide p.150-160 (Compliance Tracking)

---

### Query 3.3: Page Allocation by Factor Weight

```
How should I allocate my [X] pages across evaluation factors to maximize scoring potential?
```

**Expected Output**:

```
Total Pages: 30 (Technical Volume)

Allocation Strategy (Weighted by factor importance):
- Technical Approach (40% weight): 12 pages (40% × 30)
- Management Approach (30% weight): 9 pages (30% × 30)
- Past Performance (20% weight): 6 pages (20% × 30)
- Corporate Experience (10% weight): 3 pages (10% × 30)

Adjustments:
- Add 1 page to Past Performance (low weight but mandatory CPARS)
- Reduce Corporate Experience by 1 page (lower scoring potential)
```

**Shipley Reference**: Proposal Guide p.115-120 (Page Budget Allocation)

---

## Category 4: Compliance & Risk Analysis

### Query 4.1: Mandatory Requirement Check

```
List all MANDATORY requirements and confirm our compliance posture. Flag any gaps.
```

**Expected Output**:

```
COMPLIANT (18 of 20 requirements):
✅ REQ-012: Cloud integration - AWS GovCloud certified
✅ REQ-027: NIST 800-171 - Current certification (exp 2026)
✅ REQ-043: Weekly reports - Standard practice

GAP ANALYSIS (2 requirements):
❌ REQ-055: ISO 9001 certification - NOT CERTIFIED
   Risk: High (MANDATORY requirement)
   Mitigation: Commit to certification within 6 months, provide draft QMS

⚠️ REQ-067: Key Personnel with TS/SCI clearance - Only 2 of 5 have clearance
   Risk: Medium (IMPORTANT requirement)
   Mitigation: Subcontract cleared personnel, start clearance process for 3 staff
```

**Shipley Reference**: Capture Guide p.85-90 (Gap Analysis)

---

### Query 4.2: Section L vs. Section M Cross-Check

```
Are there any submission instructions (Section L) that don't map to an evaluation factor (Section M)? Flag orphaned instructions.
```

**Expected Output**:

```
PROPERLY MAPPED (12 of 14 instructions):
✅ "10-page limit for Technical Approach" → Factor 1: Technical Approach
✅ "Include 3 past performance references" → Factor 3: Past Performance

ORPHANED INSTRUCTIONS (2):
❌ "Submit organizational chart" → NO EVALUATION FACTOR
   Analysis: Likely administrative, not scored
   Action: Include in front matter, not in evaluated volume

⚠️ "Describe teaming arrangements" → UNCLEAR MAPPING
   Analysis: Could affect Management Approach OR Corporate Experience
   Action: Query government during Q&A period
```

**Shipley Reference**: Proposal Guide p.140-145 (L-M Compliance)

---

### Query 4.3: Clause Interpretation

```
Explain the impact of [CLAUSE NUMBER] on our proposal and what we must demonstrate.

Example: "Explain the impact of DFARS 252.204-7012 on our proposal."
```

**Expected Output**:

```
DFARS 252.204-7012: Safeguarding Covered Defense Information

IMPACT:
- Applies to: All CUI (Controlled Unclassified Information) handling
- Requirement: NIST 800-171 compliance (110 security controls)
- Flow-down: Must include in all subcontracts

PROPOSAL DEMONSTRATION:
1. Technical Approach: Describe NIST 800-171 implementation
   - 110 controls mapped to system architecture
   - SIEM for continuous monitoring
   - Incident response plan (DFARS 252.204-7012(b)(2))

2. Management Approach: Show compliance maintenance
   - Annual assessments by certified auditor
   - Quarterly reviews with government
   - Training program for cleared personnel

3. Past Performance: Reference similar contracts with CUI
   - Contract ABC: DoD CUI handling (2021-2024)
   - Zero security incidents reported
```

**Shipley Reference**: Capture Guide p.110-115 (Regulatory Compliance)

---

## Category 5: Section-Specific Analysis

### Query 5.1: Section C (SOW) Deep Dive

```
What are the key performance objectives in the SOW and how do they map to evaluation factors?
```

**Expected Output**:

- Performance objectives extracted from Section C
- Linked evaluation factors (typically Section M Factor 1 or 2)
- Deliverables tied to each objective
- Quality standards or metrics

---

### Query 5.2: Section H (Special Requirements) Impact

```
What special requirements in Section H affect our proposal approach?
```

**Expected Output**:

```
H-1: Key Personnel Requirements
- Impact: Must propose named individuals with resumes
- Proposal Section: Management Approach, Attachment A (Resumes)
- Evaluation Factor: Factor 4 - Key Personnel (15%)

H-3: Security Clearances
- Impact: All staff require Secret clearance minimum
- Proposal Section: Staffing Plan, Security Plan
- Risk: 40% of proposed staff lack clearance (mitigation: sponsor process)
```

---

### Query 5.3: Section J (Attachments) Navigation

```
Show me all Section J attachments in hierarchical order with their purpose.
```

**Expected Output**:

```
Section J: List of Attachments

J-02000000: Performance Work Statement (PWS)
  ├── J-02000000-10: Technical Requirements
  ├── J-02000000-20: Security Requirements (NIST 800-171)
  └── J-02000000-30: Data Requirements (CDRL)

J-03000000: Quality Assurance Surveillance Plan (QASP)
  └── J-03000000-10: Performance Standards (SLA metrics)

J-04000000: Contract Data Requirements List (CDRL)
  - 15 deliverables with due dates
```

---

## Category 6: Past Performance Strategy

### Query 6.1: Relevant Past Performance Identification

```
Which of our past contracts are most relevant to this RFP based on scope, contract value, and recency?
```

**Expected Output**:

```
HIGHLY RELEVANT (3 contracts):
1. Contract ABC-2021 (Navy IT Modernization)
   - Scope similarity: 95% (cloud migration, NIST 800-171)
   - Value similarity: $45M (target: $50M)
   - Recency: 2021-2024 (within 3 years)
   - Performance: Excellent (CPARS 4.8/5.0)
   - Use in: Factor 3 - Past Performance (primary reference)

2. Contract DEF-2022 (DoD Help Desk)
   - Scope similarity: 80% (24/7 support, ITIL framework)
   - Value similarity: $30M (target: $50M)
   - Recency: 2022-Present (ongoing)
   - Performance: Very Good (CPARS 4.5/5.0)
   - Use in: Factor 3 - Past Performance (secondary reference)
```

**Shipley Reference**: Capture Guide p.95-105 (Past Performance Strategy)

---

### Query 6.2: Past Performance Confidence Prediction

```
Based on our proposed past performance references, predict the government's confidence assessment rating.
```

**Expected Output**:

```
PREDICTED CONFIDENCE: SUBSTANTIAL CONFIDENCE

Rationale:
✅ 3 highly relevant contracts (scope + value + recency)
✅ All CPARS ratings ≥ 4.5/5.0 (Excellent/Very Good)
✅ No adverse performance incidents
✅ Similar technical requirements (cloud, cybersecurity)
✅ Same customer (Navy) for 2 of 3 references

Risks:
⚠️ Contract ABC completed 1 year ago (reference may be less strong)
⚠️ Contract DEF ongoing (cannot provide final CPARS until completion)

Mitigation:
- Provide interim CPARS for Contract DEF (if available)
- Supplement with customer testimonial letters
- Emphasize zero deficiencies across all contracts
```

**Shipley Reference**: Capture Guide p.100-105 (Confidence Assessment)

---

## Category 7: Questions for Government (Q&A Strategy)

### Query 7.1: Ambiguity Detection

```
Identify ambiguous or conflicting requirements that should be clarified in a Q&A submission.
```

**Expected Output**:

```
AMBIGUITY_001:
- Issue: Section L states "10-page limit" for Technical Approach
- Conflict: Section M describes 5 sub-factors requiring detailed response
- Question: "Does the 10-page limit for Technical Approach include appendices, or is it limited to the main narrative?"
- Priority: HIGH (affects proposal page budget)

AMBIGUITY_002:
- Issue: Section C requires "24/7 help desk support"
- Conflict: Section B pricing shows "8-hour shifts"
- Question: "Please clarify the required coverage hours for help desk support. Are 24/7 operations required, or is 8x5 coverage acceptable?"
- Priority: CRITICAL (major cost/scope impact)
```

**Shipley Reference**: Capture Guide p.25 (Intel Gathering via Q&A)

---

### Query 7.2: Generate Q&A Submission

```
Generate a list of high-impact questions for government clarification based on RFP analysis.
```

**Expected Output** (Max 7 questions per Shipley best practices):

```
QUESTION 1 (Page Limits):
Does the 10-page limit for Technical Approach include diagrams and appendices, or is it limited to the main narrative text?
Reference: Section L, page 15

QUESTION 2 (Evaluation Weighting):
Section M states Factor 1 (Technical Approach) is "significantly more important than price." Can the Government provide the specific weight or ratio?
Reference: Section M, page 42

QUESTION 3 (Key Personnel):
Section H-1 requires a Program Manager with "5 years of relevant experience." Does this include non-DoD IT project management, or must it be specifically DoD contracts?
Reference: Section H, page 28
```

**Shipley Reference**: Capture Guide p.25 (Q&A Strategy)

---

## Category 8: Shipley Methodology Application

### Query 8.1: Action Caption Check

```
Review Section C and identify opportunities for action captions in our proposal.
```

**Expected Output**:

```
ACTION CAPTION OPPORTUNITIES (15 identified):

1. "Zero-Downtime Migration Eliminates Customer's #1 Pain Point"
   - Requirement: REQ-012 (Cloud migration)
   - Pain Point: "Legacy system causing 10% downtime" (Section C, p.8)
   - Proposal Section: Technical Approach 1.1

2. "Real-Time Dashboard Provides Visibility Past Vendors Couldn't"
   - Requirement: REQ-043 (Weekly status reports)
   - Pain Point: "Poor communication from incumbent" (Implied in Section C)
   - Proposal Section: Management Approach 2.2
```

**Shipley Reference**: Proposal Guide p.175-185 (Action Captions)

---

### Query 8.2: Pink Team Readiness Check

```
Based on the RFP analysis, what are the critical review items for our Pink Team review?
```

**Expected Output**:

```
PINK TEAM REVIEW CHECKLIST:

1. COMPLIANCE (Critical):
   ☐ All 20 MANDATORY requirements addressed
   ☐ Section L page limits met (Technical: 10, Management: 8, PP: 5)
   ☐ Section L format requirements followed (font, margins, headers)
   ☐ All required certifications included (Section K)

2. EVALUATION STRATEGY (High Priority):
   ☐ 40% of content addresses Technical Approach (highest weight)
   ☐ Win themes appear in first paragraph of each section
   ☐ Pain points addressed with solutions in factors >25% weight
   ☐ Past performance references meet recency/relevance requirements

3. DISCRIMINATORS (Medium Priority):
   ☐ Action captions highlight competitive advantages
   ☐ Graphics support technical approach (not filler)
   ☐ Innovation opportunities identified and proposed
   ☐ Risk mitigation for all IMPORTANT+ requirements
```

**Shipley Reference**: Proposal Guide p.250-260 (Color Team Reviews)

---

### Query 8.3: Shipley Compliance Scale Assessment

```
Assess our proposal's compliance level using Shipley's 4-level scale.
```

**Expected Output**:

```
SHIPLEY COMPLIANCE ASSESSMENT:

COMPLIANT (18 requirements - 90%):
✅ REQ-012: Cloud integration - Fully compliant, AWS GovCloud
✅ REQ-027: NIST 800-171 - Current certification, compliance plan
✅ REQ-043: Weekly reports - Standard practice, dashboard proposed

PARTIALLY COMPLIANT (1 requirement - 5%):
⚠️ REQ-067: Key Personnel clearances - 2 of 5 have TS/SCI
   - Gap: 3 personnel lack required clearances
   - Mitigation: Subcontract cleared staff, sponsor clearance process

NON-COMPLIANT (1 requirement - 5%):
❌ REQ-055: ISO 9001 certification - NOT CERTIFIED
   - Gap: No current certification
   - Mitigation: Commit to certification within 6 months, provide draft QMS
   - Risk: May be rated "unacceptable" for this factor

NOT ADDRESSED (0 requirements - 0%):
✅ All requirements have been addressed

OVERALL ASSESSMENT: ACCEPTABLE with mitigations
Recommendation: Strengthen REQ-055 mitigation (ISO 9001) before submission
```

**Shipley Reference**: Capture Guide p.85-90 (Compliance Assessment)

---

## Category 9: Cost/Price Strategy

### Query 9.1: Cost Realism Preparation

```
What requirements will drive cost realism analysis and how should we justify our pricing?
```

**Expected Output**:

```
COST REALISM FACTORS (Section M analysis):

1. Labor Categories & Hours
   - Requirement: REQ-073 (Staffing levels per Section C)
   - Proposed: 15 FTE (mix of engineers, analysts, support)
   - Justification: Historical staffing from Contract ABC (14 FTE for similar scope)
   - Risk: Government may question if 15 FTE is sufficient for 24/7 coverage

2. NIST 800-171 Implementation
   - Requirement: REQ-027 (110 security controls)
   - Proposed: $500K Year 1 (implementation), $100K/year (maintenance)
   - Justification: Industry benchmark for DoD networks ($450-550K range)
   - Risk: Government may challenge if significantly above incumbent

3. Key Personnel Salaries
   - Requirement: H-1 (PM with 10+ years experience)
   - Proposed: $175K fully burdened
   - Justification: GSA Schedule rates + local market data (DC Metro)
   - Risk: Must be competitive but not unrealistically low
```

**Shipley Reference**: Proposal Guide p.220-230 (Price Strategy)

---

### Query 9.2: Price-to-Win Analysis

```
Based on government budget and incumbent pricing, what is our competitive price target?
```

**Expected Output**:

```
PRICE-TO-WIN ANALYSIS:

Government Budget: $50M (5-year IDIQ, estimated)
Incumbent Pricing: $48M (5 years, current contract)
Our Independent Estimate: $52M (5 years)

COMPETITIVE TARGET: $47-49M (2-4% below incumbent)

Rationale:
- Must be ≤$50M to stay within budget
- 2-4% below incumbent shows value
- Cannot go below $46M without sacrificing quality/compliance

Cost Reduction Opportunities:
1. Optimize labor mix (reduce senior staff, add junior)
2. Leverage existing security tools (reduce new software costs)
3. Propose 4-year base + 1-year option (reduce long-term risk premium)

Risk:
⚠️ Our estimate ($52M) is 4% above target
⚠️ Must find $3M in savings without compromising technical approach
```

**Shipley Reference**: Capture Guide p.130-140 (Price-to-Win)

---

## Category 10: Teaming & Subcontracting

### Query 10.1: Capability Gap Analysis

```
What capabilities do we lack that require teaming partners or subcontractors?
```

**Expected Output**:

```
CAPABILITY GAPS (3 identified):

GAP_001: TS/SCI Cleared Personnel
- Requirement: H-3 (All staff require Secret minimum, 5 require TS/SCI)
- Our Capability: 2 of 5 Key Personnel have TS/SCI
- Teaming Need: Subcontractor with cleared workforce
- Recommended Partner: ClearTech Solutions (800+ cleared staff)

GAP_002: ISO 9001 Certification
- Requirement: REQ-055 (ISO 9001 required by contract start)
- Our Capability: Not currently certified (in draft stage)
- Teaming Need: ISO 9001 certified QA subcontractor
- Recommended Partner: QualityFirst Inc. (ISO certified since 2018)

GAP_003: Physical Presence in Jacksonville, FL
- Requirement: Section C (Base Operations Support at NAVSTA Mayport)
- Our Capability: No existing Jacksonville office
- Teaming Need: Local small business with base access
- Recommended Partner: Southeast Support Services (HUBZone certified)
```

**Shipley Reference**: Capture Guide p.50-60 (Teaming Strategy)

---

## Usage Instructions

1. **Copy Query**: Select desired query from categories above
2. **Customize**: Replace [PLACEHOLDERS] with specific terms from your RFP
3. **Paste into Chat**: Use with your RAG-based RFP analysis tool
4. **Iterate**: Refine query based on initial results

**Pro Tip**: Combine multiple queries for comprehensive analysis

```
Example: Run Query 2.1 (Pain Points) → Query 3.1 (Proposal Outline) → Query 8.2 (Pink Team Checklist)
```

---

**Last Updated**: January 2025 (Branch 004 - Phase 1)  
**Version**: 1.0 (Initial query library)  
**Methodology**: Based on Shipley Capture Guide and Proposal Guide  
**Future Enhancement**: Add query templates for specific RFP types (Task Orders, IDIQs, GSA Schedule)
