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

## Category 10: Amendment & Change Analysis

### Query 10.1: Amendment Summary

```
What changed in Amendment [NUMBER]? Provide a summary of additions, modifications, and removals.

Example: "What changed in Amendment 0001?"
```

**Expected Output**:

```
AMENDMENT 0001 SUMMARY (Issued: 2025-01-15)

CRITICAL CHANGES (3):
❗ MODIFIED: Section L - Technical Volume page limit
   - Baseline: 10 pages
   - Amendment 1: 15 pages (+5 pages)
   - Impact: More space for technical detail, adjust proposal outline

❗ ADDED: New Attachment J-06 - Cybersecurity Requirements Matrix
   - Content: NIST 800-171 compliance crosswalk (15 pages)
   - Impact: Must address in Technical Approach, add compliance matrix

❗ REMOVED: Requirement REQ-089 - Daily status reports
   - Replaced with: Weekly status reports (REQ-043 modified)
   - Impact: Reduce reporting burden, adjust management approach

MINOR CHANGES (5):
✏️ MODIFIED: Section A - Submission deadline extended
   - Baseline: 2025-02-01
   - Amendment 1: 2025-02-15 (+14 days)

✏️ MODIFIED: Attachment J-02 - PWS Section 3.2.1
   - Added: "Contractor shall provide monthly invoicing"
   - Impact: Administrative change, no technical impact

ADMINISTRATIVE (2):
📋 Corrected typo in Section M (page 42, "evalution" → "evaluation")
📋 Updated POC email address (Section A)

DOCUMENTS SUPERSEDED:
- Attachment J-06 replaces previous J-05-OLD
```

**Use Case**: Immediate impact assessment for proposal teams

---

### Query 10.2: Compare Baseline vs Latest Amendment

```
Show me all differences between the baseline RFP and the current version (after all amendments).

Example: "Compare baseline to Amendment 0003"
```

**Expected Output**:

```
CUMULATIVE CHANGES (Baseline → Amendment 3)

SECTION L (Instructions to Offerors):
├── Page Limits:
│   - Technical Volume: 10 → 15 pages (AMD 1)
│   - Management Volume: 8 → 8 pages (no change)
│   - Past Performance: 5 → 10 pages (AMD 2)
├── Format Requirements:
│   - Font: Times New Roman 12pt → Arial 11pt (AMD 3)
│   - Margins: 1" → 0.75" (AMD 3)

SECTION M (Evaluation Factors):
├── Factor Weights:
│   - Technical: 40% → 45% (AMD 2)
│   - Management: 30% → 25% (AMD 2)
│   - Past Performance: 20% → 20% (no change)
│   - Price: 10% → 10% (no change)

SECTION C (SOW):
├── Performance Period: 5 years → 3 years base + 2 option years (AMD 1)
├── Deliverables: 12 → 15 CDRLs (AMD 2 added 3 new)

REQUIREMENTS:
├── ADDED: 8 new requirements (AMD 1: 3, AMD 2: 5)
├── MODIFIED: 12 requirements (scope/deadline changes)
├── REMOVED: 4 requirements (REQ-089, REQ-104, REQ-127, REQ-133)

NET EFFECT:
- Proposal complexity: +25% (more pages, deliverables, requirements)
- Timeline: +14 days (submission extended)
- Competitive position: Technical factor increased (favors our strengths)
```

**Use Case**: Comprehensive change tracking across all amendments

---

### Query 10.3: Amendment Impact on Our Proposal

```
How does Amendment [NUMBER] affect our current proposal draft? What sections need revision?

Example: "How does Amendment 0002 affect our proposal?"
```

**Expected Output**:

```
AMENDMENT 0002 IMPACT ASSESSMENT

HIGH PRIORITY REVISIONS (3 sections):

1. TECHNICAL APPROACH (Volume I, Section 1)
   - Change: Factor weight increased from 40% to 45%
   - Current Status: 10 pages (within old limit)
   - Required Action: Expand to 15 pages (new limit from AMD 1)
   - Content Gaps: AMD 2 added REQ-156 (AI/ML capabilities) - NOT ADDRESSED
   - Effort: 40 hours (add 5 pages + address new requirement)
   - Deadline: 5 days before submission

2. PAST PERFORMANCE (Volume I, Section 3)
   - Change: Page limit increased from 5 to 10 pages
   - Current Status: 5 pages (at old limit)
   - Required Action: Add 2 more references (AMD 2 requires 5 total, we have 3)
   - Content Gaps: Need DOD AI/ML contracts (align with REQ-156)
   - Effort: 24 hours (2 new references + expand narratives)
   - Deadline: 7 days before submission

3. COST PROPOSAL (Volume II)
   - Change: AMD 2 modified CLIN structure (5 CLINs → 7 CLINs)
   - Current Status: OLD STRUCTURE (invalid)
   - Required Action: Completely rebuild cost proposal
   - Content Gaps: New CLINs for AI/ML services, training
   - Effort: 60 hours (re-price + justify new CLINs)
   - Deadline: 10 days before submission (cost realism review)

LOW PRIORITY REVISIONS (2 sections):
✏️ Management Approach: Update org chart (AMD 2 changed KP requirements)
✏️ Section J Cross-References: Update attachment numbers (J-05 → J-06)

NO IMPACT (1 section):
✅ Corporate Experience: No changes from amendments

RISK ASSESSMENT:
🔴 HIGH RISK: Cost proposal rebuild (60 hours, complex pricing)
🟡 MEDIUM RISK: AI/ML requirement (new capability, limited past performance)
🟢 LOW RISK: Page limit expansions (more space = easier)

RECOMMENDED ACTIONS:
1. Immediately assign cost team to CLIN restructuring
2. Identify AI/ML past performance references by EOD today
3. Schedule technical writers for 5-page expansion (Technical)
4. Hold amendment review meeting tomorrow 9 AM
```

**Use Case**: Real-time proposal revision planning

---

### Query 10.4: Amendment Change Detection (Attachments)

```
Compare Attachment [ID] between baseline and Amendment [NUMBER]. What changed in the document content?

Example: "Compare Attachment J-02 (PWS) between baseline and Amendment 0001"
```

**Expected Output**:

```
ATTACHMENT J-02 CHANGE ANALYSIS (PWS)
Baseline vs. Amendment 0001

DOCUMENT METADATA:
- Baseline: PWS_Baseline_v1.0.docx (45 pages, 2024-11-01)
- Amendment 1: PWS_AMD001_v1.1.docx (52 pages, 2025-01-15)
- Net Change: +7 pages, 78 modifications

SECTION-BY-SECTION CHANGES:

Section 3.1 - System Architecture:
├── ADDED: "3.1.5 AI/ML Integration Requirements" (2 pages)
│   - 8 new technical requirements for ML model deployment
│   - Performance metrics: 95% accuracy, <100ms latency
│   - Impact: Major scope addition, requires AI capability demonstration
├── MODIFIED: "3.1.3 Cybersecurity Controls"
│   - Added requirement for Zero Trust Architecture (ZTA)
│   - Removed reference to NIST 800-53 Rev 4 (replaced with Rev 5)

Section 3.2 - Performance Standards:
├── MODIFIED: "3.2.1 Availability"
│   - Baseline: 99.5% uptime
│   - Amendment 1: 99.9% uptime (+0.4% increase)
│   - Impact: More stringent SLA, affects infrastructure design
├── ADDED: "3.2.5 Response Times"
│   - P1 incidents: 15 minutes → 10 minutes
│   - P2 incidents: 4 hours → 2 hours
│   - Impact: Requires 24/7 staffing model

Section 4.0 - Deliverables (CDRL):
├── ADDED: 3 new deliverables
│   - CDRL 6089: AI/ML Model Documentation (monthly)
│   - CDRL 6090: Zero Trust Implementation Plan (one-time)
│   - CDRL 6091: Performance Dashboard (real-time)
├── MODIFIED: CDRL 6012 - Monthly Status Report
│   - Added requirement for AI/ML metrics
│   - Changed format from Word to PowerPoint

DELETED CONTENT:
├── REMOVED: Section 3.4 - Legacy System Support
│   - Reason: Legacy system decommissioned (no longer in scope)
│   - Impact: Reduces scope, may lower cost

REQUIREMENT TRACEABILITY:
NEW: 12 requirements added (REQ-156 through REQ-167)
MODIFIED: 8 requirements changed (scope/performance/deadline)
REMOVED: 4 requirements deleted (legacy system related)

SPREADSHEET CHANGES (Attachment J-02-ANNEX-A):
- Staffing Matrix: Added "AI/ML Engineer" labor category
- Equipment List: Added GPU servers for ML training
- Pricing Template: Added CLIN 0007 for AI/ML services

ESTIMATED PROPOSAL IMPACT:
📊 Cost Impact: +$2.5M (AI/ML capability, higher SLAs, new deliverables)
⏱️ Schedule Impact: +30 days (AI/ML implementation, ZTA deployment)
👥 Staffing Impact: +3 FTE (AI engineers, 24/7 coverage)
📝 Proposal Rewrite: Technical Approach (Section 1), Management (Section 2), Cost
```

**Use Case**: Deep-dive analysis for complex attachment changes (PWS, SOW, specifications)

---

### Query 10.5: Questions Triggered by Amendment

```
What questions should we ask the government based on Amendment [NUMBER]?

Example: "What questions should we ask based on Amendment 0002?"
```

**Expected Output**:

```
RECOMMENDED Q&A QUESTIONS (Amendment 0002)

CRITICAL QUESTIONS (3):

Q1: AI/ML Requirements Clarification
- Issue: Amendment 2 added Section 3.1.5 "AI/ML Integration" with 95% accuracy requirement
- Ambiguity: What is the baseline dataset for accuracy measurement?
- Question: "For the AI/ML accuracy requirement in Amendment 2 Section 3.1.5, please clarify: (a) What dataset will be used to measure 95% accuracy? (b) Is accuracy measured at deployment or continuously monitored? (c) Are there specific ML frameworks required (TensorFlow, PyTorch, etc.)?"
- Impact: HIGH (affects technical approach, tooling selection, cost)

Q2: Zero Trust Architecture Scope
- Issue: Amendment 2 modified Section 3.1.3 to require "Zero Trust Architecture"
- Ambiguity: Does ZTA apply to entire network or just cloud environment?
- Question: "Amendment 2 Section 3.1.3 requires Zero Trust Architecture implementation. Please clarify: (a) Does ZTA apply to on-premise infrastructure, cloud, or both? (b) What ZTA maturity level is required (CISA ZTA Maturity Model levels 1-5)? (c) Is phased implementation acceptable?"
- Impact: HIGH (major cost/schedule impact depending on scope)

Q3: Availability SLA Conflict
- Issue: Amendment 2 increased uptime from 99.5% to 99.9%
- Conflict: Section C states "8x5 support" but 99.9% typically requires 24/7
- Question: "Amendment 2 Section 3.2.1 requires 99.9% availability, but Section C implies 8x5 support. Please confirm: (a) Is 24/7 NOC required for 99.9% uptime? (b) Are planned maintenance windows allowed? (c) What is the acceptable downtime per month (43 minutes at 99.9%)?"
- Impact: CRITICAL (affects staffing model, cost structure)

MEDIUM PRIORITY QUESTIONS (2):

Q4: CDRL Deliverable Format
- Issue: Amendment 2 changed CDRL 6012 format from Word to PowerPoint
- Question: "Amendment 2 modified CDRL 6012 to require PowerPoint format. Is there a specific template or slide count requirement?"
- Impact: MEDIUM (affects reporting process)

Q5: Past Performance Scoring
- Issue: Amendment 2 increased Past Performance page limit from 5 to 10 pages
- Question: "With the increased page limit for Past Performance (Amendment 2), does the Government prefer more references (5+ instead of 3) or deeper detail on fewer references?"
- Impact: MEDIUM (affects proposal strategy)

DEADLINE: Q&A period closes 2025-01-25 (10 days)
```

**Use Case**: Proactive government engagement after amendments

---

## Category 11: Teaming & Subcontracting

### Query 11.1: Capability Gap Analysis

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
