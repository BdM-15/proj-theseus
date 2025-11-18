# Capture Manager Query Library

**Purpose**: Production-ready queries for capture/proposal development that non-experts can copy-paste into chat without understanding the underlying user_prompt system.

**Audience**: Capture Managers, Proposal Managers, Technical Writers, BD Professionals (no RAG expertise required)

**Methodology**: Shipley Capture Guide + Proposal Guide principles integrated into every query

**Usage**:

1. Find query matching your task in categories below
2. Copy entire query (including example text if shown)
3. Paste into chat input box
4. Replace [PLACEHOLDERS] with your RFP-specific terms
5. Get structured, actionable intelligence

**Why This Works**: Each query is designed to trigger optimal RAG retrieval + Shipley-aligned response formatting. You're getting the benefit of specialized prompts without needing to inject them programmatically.

---

## Category 1: Compliance & Requirements Analysis

**When to Use**: Before proposal writing begins, after RFP release, after amendments issued.

### Query 1.1: Complete Compliance Checklist (Shipley Pre-Writing Foundation)

```
Generate a comprehensive compliance checklist showing all mandatory, important, and optional requirements from this RFP. For each requirement, show:
- Exact RFP reference (Section L Para X.X, PWS Para Y.Y)
- Modal verb (SHALL/MUST/SHOULD/MAY)
- Which evaluation factor assesses it
- Submission format requirements
- Our capability status (compliant/gap/mitigation needed)

Organize by criticality level and flag any requirements we don't currently meet.
```

**Why This Works**: Triggers compliance_checklist.md user prompt behavior by requesting "comprehensive compliance checklist" + "organized by criticality" + "capability gaps." Even without programmatic injection, query phrasing aligns with Shipley compliance matrix methodology.

**What You'll Get**:

- ✅ All MANDATORY requirements (SHALL/MUST) with showstopper flags
- ⚠️ Important requirements (SHOULD) with scoring impact
- ℹ️ Optional requirements (MAY) with strategic value assessment
- 📊 Compliance summary matrix (% compliant, gaps, teaming needs)
- 🎯 Section L ↔ Section M mapping (submission instructions → evaluation factors)

**Shipley Principle**: "Compliance is the foundation, not the ceiling. Know 100% of requirements BEFORE writing begins."

---

### Query 1.2: Mandatory Requirements Only (Showstopper Check)

```
List all MANDATORY requirements (SHALL/MUST modal verbs OR criticality ≥0.80) and confirm our compliance posture. For any gaps, recommend mitigation strategies (teaming, subcontracting, commit-to-obtain).
```

**Why This Works**: Focuses on showstoppers by explicitly requesting "MANDATORY" + "SHALL/MUST" + "compliance gaps" + "mitigation."

**What You'll Get**:

- Filtered list of only MANDATORY requirements
- Compliance status: ✅ Compliant | ⚠️ Partial | ❌ Gap
- Mitigation options for gaps (teaming partner, certification timeline, subcontractor)
- Risk assessment (HIGH if any mandatory gap = rejection risk)

**Use Case**: Bid/No-Bid decision - if any mandatory gap can't be mitigated, consider no-bid.

---

### Query 1.3: Section L ↔ Section M Cross-Check (Compliance Trap Detection)

```
Verify all Section L submission instructions map to Section M evaluation factors. Flag any orphaned instructions not linked to scoring, and identify evaluation factors without clear submission guidance.
```

**Why This Works**: Requests "Section L ↔ M mapping" + "orphaned instructions" + "missing guidance" - triggers cross-reference analysis.

**What You'll Get**:

- ✅ Properly mapped instructions (e.g., "10-page technical volume" → Factor 1: Technical Approach)
- ❌ Orphaned instructions (required but not scored - administrative only)
- ⚠️ Evaluation factors without clear submission format (opportunity for Q&A question)

**Shipley Principle**: "If Section L doesn't say it, you can't submit it. If Section M doesn't score it, don't waste pages on it."

---

## Category 2: Proposal Outline & Structure (Shipley Page Allocation)

**When to Use**: After compliance checklist complete, before proposal kickoff, during outline review.

### Query 2.1: Complete Proposal Outline with Page Allocations

```
Generate a complete proposal outline aligned to Section M evaluation factors. For each section:
- Page allocation proportional to factor weight
- Requirements addressed in that section
- Win theme opportunities
- Submission format (font, margins, volume)
- Section assignment recommendation (who should write)

Include compliance cross-check to verify 100% requirement coverage.
```

**Why This Works**: Requests "outline aligned to evaluation factors" + "page allocation by weight" + "requirement mapping" + "compliance cross-check" - triggers proposal_outline_generation.md behavior.

**What You'll Get**:

- 📋 Full proposal structure (Volume I: Technical, Volume II: Management, Volume III: Past Performance, Volume IV: Cost)
- 📏 Page budgets per section (weighted by evaluation factor importance)
- 📌 Requirement-to-section mapping (ensures 100% coverage)
- 🎯 Win theme integration points (where to emphasize discriminators)
- 👥 Section assignment guide (effort estimates, writer recommendations)

**Shipley Principle**: "Outline to the evaluation criteria. Evaluators score what they can find, not what you intended to say."

---

### Query 2.2: Page Allocation Optimization

```
I have [X] total pages for [Volume Name]. Show how to allocate pages across sections proportionally to evaluation factor weights, with adjustments for mandatory requirement density and past performance evidence needs.
```

**Example**: "I have 30 pages for Technical Volume. Show page allocation across sections."

**Why This Works**: Specifies page limit + requests "proportional allocation" + "weight-based" + "mandatory requirement adjustments."

**What You'll Get**:

```
Technical Approach (40% weight): 12 pages (40% × 30)
  - Adjustment: +2 pages (high requirement density - 18 mandatory requirements)
  - Final: 14 pages

Management Approach (30% weight): 9 pages (30% × 30)
  - Adjustment: -1 page (fewer requirements - 8 total)
  - Final: 8 pages

Past Performance (20% weight): 6 pages (20% × 30)
  - Adjustment: +1 page (need 5 project references per Section L)
  - Final: 7 pages

Buffer for Graphics/Tables: 1 page
Total: 30 pages (within limit)
```

**Shipley Principle**: "Allocate pages to scoring weights. Don't spend 10 pages on a 10% factor."

---

### Query 2.3: Section-Specific Guidance

```
For proposal Section [X.X: Section Name], provide:
- Requirements to address in this section
- Page allocation and content priorities
- Win theme opportunities
- Action caption ideas for graphics
- Proof points needed (past performance, metrics, certifications)
```

**Example**: "For Section 1.2: Quality Assurance, provide content guidance."

**Why This Works**: Focuses on specific section + requests "requirements" + "win themes" + "proof points" + "action captions."

**What You'll Get**:

- Detailed content outline for that section
- Shipley action caption examples ("ISO 9001 Certified QC Process Eliminates Costly Rework")
- Past performance references to include as proof
- Warning about page budget (if section has many requirements but few pages)

---

## Category 1: Evaluation Factor Analysis

## Category 3: Win Theme Development (Shipley Benefit-Discriminator-Proof Formula)

**When to Use**: After customer pain points identified, before proposal writing, during capture strategy development.

### Query 3.1: Generate Win Themes from Customer Pain Points

```
Based on customer pain points identified in the RFP (Section C, Section M emphasis, incumbent issues), generate 3-7 major win themes using Shipley's formula: Customer Benefit + Your Discriminator + Proof.

For each theme:
- Show what customer GETS (specific, measurable benefit)
- Show what sets us apart (capability competitors lack or can't prove)
- Provide concrete proof (metrics, CPARs, certifications, testimonials)
- Recommend where to emphasize in proposal (exec summary, volume openers, sections)
```

**Why This Works**: Requests "win themes" + "Shipley formula" + "customer benefit" + "discriminator" + "proof" triggers win_theme_identification.md behavior.

**What You'll Get**:

```
WIN THEME 1: Zero-Downtime Transition

Customer Benefit: "You will experience zero service disruptions during transition"
Your Discriminator: "because our 90-day phased methodology minimizes operational risk"
Proof: "validated by 12 incumbent transitions with 99.7% on-time delivery and zero contract deficiencies"

Where to Use:
✅ Executive Summary (lead theme)
✅ Technical Volume Opener
✅ Section 2.4: Transition Plan (primary location)
✅ Action Caption: "Proven 90-Day Phased Transition Eliminates Downtime"
```

**Shipley Principle**: "Theme statements link customer benefits to discriminating features. Strategies = things to do. Themes = things to say."

---

### Query 3.2: Competitive Differentiation Matrix

```
Create a competitive analysis matrix comparing our discriminators to likely competitors [Competitor A, Incumbent, Competitor B]. Highlight strengths to emphasize and weaknesses to address with ghost themes.
```

**Why This Works**: Requests "competitive matrix" + "discriminators" + "ghost themes" triggers competitive analysis + subtle differentiation strategy.

**What You'll Get**:

```
┌─────────────────────────┬────────┬──────────┬────────┬────────┐
│ Discriminator           │ Your Co│ Comp A   │ Incumb │ Comp B │
├─────────────────────────┼────────┼──────────┼────────┼────────┤
│ Navy MBOS Experience    │  15 yrs│    0 yrs │  5 yrs │  3 yrs │
│ On-Time Delivery Rate   │  99.7% │    ?     │   87%  │  92%   │
│ ISO 9001 Certified      │  ✅    │    ❌    │   ✅   │  ✅    │
│ CMMI Level 3            │  ✅    │    ❌    │   ❌   │  ❌    │
└─────────────────────────┴────────┴──────────┴────────┴────────┘

Your Strongest Differentiators:
1. Navy MBOS Experience (15 years vs. 0-5 for competitors)
2. CMMI Level 3 (only company with this certification)

Ghost Theme Opportunity:
"You will receive consistent process maturity through CMMI Level 3 certified methodology, ensuring predictable quality and eliminating the rework cycles that plague ad-hoc approaches."
→ Emphasizes YOUR strength (CMMI) while implying competitor weakness (no certification = ad-hoc = rework)
```

**Shipley Principle**: "Ghost themes highlight competitor weaknesses WITHOUT naming them. Focus on customer benefit of YOUR strength."

---

### Query 3.3: Action Caption Generator

```
For [Section Name or Theme], generate Shipley-style action captions for graphics, tables, and figures that reinforce win themes. Use formula: Customer Benefit + How We Do It.
```

**Example**: "For Quality Assurance section, generate action captions."

**Why This Works**: Requests "action captions" + "Shipley formula" + "win themes" + "customer benefit" triggers visual reinforcement strategy.

**What You'll Get**:

```
THEME: Performance Excellence / Quality Assurance

❌ Weak Caption: "Quality Control Process"
✅ Strong Caption (Action): "ISO 9001 Certified QC Process Eliminates Costly Rework and Delays"

❌ Weak Caption: "Project Timeline"
✅ Strong Caption (Action): "Proven 90-Day Phased Transition Minimizes Operational Downtime"

❌ Weak Caption: "Organizational Chart"
✅ Strong Caption (Action): "SDVOSB Partnership Achieves Socioeconomic Goals While Delivering Technical Excellence"
```

**Shipley Principle**: "Action captions should answer 'So what?' - start with customer benefit, use active verbs, include proof when possible."

---

## Category 4: Questions for Government (Shipley Intel Gathering)

**When to Use**: After RFP release, before proposal kickoff, after amendments issued.

### Query 4.1: Generate Strategic Clarification Questions

```
Identify ambiguous, conflicting, or unclear requirements that should be clarified through Questions for the Government (Q&A submission). Prioritize questions that:
1. Reduce our proposal risk (ambiguity clarification)
2. Validate technical feasibility assumptions
3. Expose gaps requiring government amendment
4. Clarify evaluation criteria for better targeting

Generate 15-25 questions ready to submit to the Contracting Officer, with exact RFP paragraph references.
```

**Why This Works**: Requests "clarification questions" + "ambiguities" + "risk reduction" + "evaluation criteria" triggers generate_qfg.md behavior.

**What You'll Get**:

```
CATEGORY 1: RISK REDUCTION - AMBIGUITY CLARIFICATION (5 questions)

QUESTION 1:
RFP Reference: Section L Para 4.3.1, Section M Para 5.2.3
Risk: Unclear page limit scope
Recommended Question:
"Section L, Paragraph 4.3.1 specifies a 30-page limit for the Technical Volume. Section M, Paragraph 5.2.3 requires detailed past performance narratives. Does the 30-page limit include past performance narratives, or are they submitted as a separate attachment not counted against the page limit?"

Strategic Value:
- PRIMARY: Clarifies page limit → enables accurate proposal planning
- SECONDARY: If separate attachment allowed, increases space for win themes
- COMPETITIVE: Competitors may not catch this, risk exceeding limit

---

CATEGORY 2: COMPLIANCE VERIFICATION - TECHNICAL FEASIBILITY (4 questions)
[... additional questions ...]

CATEGORY 3: COMPETITIVE POSITIONING - SHAPING QUESTIONS (3 questions)
[... subtle shaping questions that favor your discriminators ...]
```

**Shipley Principle**: "Ask questions that reduce YOUR risk while increasing COMPETITORS' uncertainty. Never ask questions that expose your weaknesses."

---

### Query 4.2: Amendment Impact & Follow-Up Questions

```
What changed in Amendment [NUMBER]? Provide summary of modifications and generate recommended Q&A questions triggered by ambiguities or conflicts in the amendment.
```

**Example**: "What changed in Amendment 0002?"

**Why This Works**: Requests "amendment changes" + "Q&A questions" + "ambiguities" triggers change analysis + strategic question generation.

**What You'll Get**:

- Amendment summary (additions, modifications, removals)
- Impact assessment (HIGH/MEDIUM/LOW priority changes)
- Triggered Q&A questions (new ambiguities introduced by amendment)
- Proposal revision recommendations (which sections need rework)

---

## Category 5: Past Performance Strategy (Shipley Confidence Assessment)

**When to Use**: After RFP analysis, before proposal kickoff, during past performance volume development.

### Query 5.1: Identify Most Relevant Past Performance Projects

```
Which of our past contracts are most relevant to this RFP based on:
- Scope similarity (technical requirements, services, deliverables)
- Contract value similarity (total dollars, annual spend)
- Recency (within past 3-5 years per Section M)
- Performance quality (CPARS ratings, customer testimonials)
- Same customer/agency preference

Rank by relevance score and recommend top 3-5 for proposal inclusion.
```

**Why This Works**: Requests "relevant past performance" + "scope similarity" + "recency" + "quality" triggers past performance selection algorithm.

**What You'll Get**:

```
HIGHLY RELEVANT (Score 95/100):
Contract ABC-2021 (Navy IT Modernization)
├─ Scope Similarity: 95% (cloud migration, NIST 800-171, 24/7 support)
├─ Value Similarity: $45M vs. $50M target (90% match)
├─ Recency: 2021-2024 (within 3 years)
├─ Performance: Excellent (CPARS 4.8/5.0)
├─ Customer: Same (Navy)
└─ Use in: Factor 3 - Past Performance (primary reference)

MEDIUM RELEVANT (Score 75/100):
Contract DEF-2022 (DoD Help Desk)
├─ Scope Similarity: 75% (help desk, ITIL, different domain)
├─ Value Similarity: $30M vs. $50M target (60% match)
[... analysis continues ...]
```

**Shipley Principle**: "Past performance confidence = relevance + recency + quality. Government evaluators assign HIGH/SUBSTANTIAL/LIMITED/NO confidence based on these factors."

---

### Query 5.2: Predict Past Performance Confidence Rating

```
Based on our proposed past performance references, predict the government's confidence assessment rating (HIGH/SUBSTANTIAL/LIMITED/NO confidence) and justify the prediction.
```

**Why This Works**: Requests "confidence prediction" + "past performance assessment" triggers Shipley confidence scoring methodology.

**What You'll Get**:

```
PREDICTED CONFIDENCE: SUBSTANTIAL CONFIDENCE

Rationale:
✅ 3 highly relevant contracts (scope 85%+ match)
✅ All CPARS ratings ≥ 4.5/5.0 (Excellent/Very Good)
✅ No adverse performance incidents
✅ 2 of 3 references are Same Customer (Navy)
✅ All within past 5 years (recency met)

Risks to Confidence:
⚠️ Contract ABC completed 1 year ago (reference less current)
⚠️ Contract DEF ongoing (no final CPARS until completion)

Mitigation:
- Supplement with customer testimonial letters
- Provide interim CPARS for Contract DEF
- Emphasize zero deficiencies across all contracts
```

**Shipley Principle**: "Government assigns confidence, not just ratings. You need relevant + recent + quality to get SUBSTANTIAL or HIGH confidence."

---

## Category 6: Compliance Assessment (Shipley Red Team Methodology)

**When to Use**: After proposal draft complete, during Pink Team (50% review), during Red Team (75% review).

**NOTE**: These queries require uploading your proposal draft file to the system.

### Query 6.1: Full Compliance Assessment (Red Team Review)

```
Assess my proposal draft for compliance against all RFP requirements using Shipley's 4-level scale:
- COMPLIANT (fully meets requirement with proof)
- PARTIALLY COMPLIANT (addresses requirement but weak/incomplete)
- NON-COMPLIANT (does not meet requirement)
- NOT ADDRESSED (requirement not mentioned - automatic rejection)

For each non-compliant or not addressed requirement:
- Show exact RFP reference and requirement text
- Explain why it's non-compliant
- Provide specific fix actions with effort estimates
- Assess scoring impact if not fixed

Prioritize fixes by rejection risk (mandatory gaps) vs. scoring risk (important gaps).
```

**Why This Works**: Requests "compliance assessment" + "Shipley 4-level" + "non-compliant" + "fix actions" triggers compliance_assessment.md behavior.

**What You'll Get**:

```
┌─────────────────────────────────────────────────────────┐
│          COMPLIANCE ASSESSMENT SUMMARY                  │
├─────────────────────────────────────────────────────────┤
│ OVERALL COMPLIANCE: 87% (174 of 200 requirements)       │
│                                                          │
│ ✅ COMPLIANT:            150 requirements (75%)         │
│ ⚠️ PARTIALLY COMPLIANT:  24 requirements (12%)          │
│ ❌ NON-COMPLIANT:         3 requirements (1.5%)         │
│ ⭕ NOT ADDRESSED:         23 requirements (11.5%)       │
│                                                          │
│ RISK ASSESSMENT: HIGH RISK                              │
│ Reason: 3 MANDATORY requirements NOT ADDRESSED          │
│ Action: Fix before submission or recommend no-bid       │
└─────────────────────────────────────────────────────────┘

PRIORITY 1 - SHOWSTOPPERS (3 requirements - FIX IMMEDIATELY):

❌ NOT ADDRESSED: REQ-055 - ISO 9001 Certification
RFP Reference: Section H-2, Para 3.1
Why Critical: MANDATORY requirement (SHALL provide certification)
Current Status: NOT MENTIONED in proposal
Required Fix:
1. Add to Quality Assurance section (2.3)
2. If NOT certified: Commit to certification within 6 months
3. Provide draft QMS documentation in appendix
4. Get COR approval for commit-to-obtain plan
Effort: HIGH (40 hours if commit-to-obtain, or no-bid if not acceptable)
Deadline: Red Team review (3 days)

[... continue for all showstoppers ...]
```

**Shipley Principle**: "Score your own proposal like the government will score it. Fix gaps before Red Team, not after submission."

---

### Query 6.2: Section-Specific Compliance Check

```
How compliant is [Section Name] in my proposal draft? Show which requirements are addressed, which are missing, and what needs strengthening.
```

**Example**: "How compliant is Section 1.2: Technical Approach?"

**Why This Works**: Focuses on specific section + requests "compliance" + "missing requirements" + "strengthening actions."

**What You'll Get**:

- Section compliance score (% of assigned requirements addressed)
- Compliant requirements (✅ well-addressed with proof)
- Partially compliant requirements (⚠️ addressed but weak - needs strengthening)
- Not addressed requirements (⭕ missing - must add)
- Effort estimate to bring section to 100% compliance

---

## Category 7: Workload & Cost Analysis

**When to Use**: Before pricing, during labor estimate development, for BOM/FFP analysis.

### Query 7.1: Extract Operational Workload Metrics

```
Extract workload metrics from the PWS/SOW to support labor/BOM estimation:
- Service volumes (users, transactions, tickets, sites)
- Performance standards (SLAs, response times, availability)
- Operational tempo (24/7 vs. 8x5, peak periods, seasonal variations)
- Deliverables (CDRLs with frequency and effort)
- Staffing indicators (labor categories, FTE levels, skill requirements)

Calculate implied FTE requirements and compare to government staffing exhibits if provided.
```

**Why This Works**: Requests "workload metrics" + "labor estimation" + "FTE calculation" triggers workload_analysis.md behavior.

**What You'll Get**:

```
WORKLOAD ANALYSIS SUMMARY:

Service Volumes:
├─ User Base: 2,500 users (Section C Para 3.1)
├─ Ticket Volume: 500/month average (Section C Para 3.2.1)
├─ Sites Supported: 3 locations (CONUS + 2 OCONUS)
└─ Equipment: 1,200 assets requiring maintenance

Performance Standards:
├─ Availability: 99.9% uptime (43 min downtime/month max)
├─ Response Times:
│  ├─ P1 incidents: 15 minutes (requires 24/7 NOC)
│  ├─ P2 incidents: 4 hours
│  └─ P3 incidents: 8 hours
└─ Resolution Times:
   ├─ P1: 4 hours
   └─ P2: 24 hours

IMPLIED FTE CALCULATION:
├─ Help Desk (24/7 coverage): 5.0 FTE
├─ Field Technicians (8x5): 6.0 FTE
├─ Network Engineers (8x5 + on-call): 3.0 FTE
├─ Program Manager: 1.0 FTE
├─ QAPM: 0.5 FTE
└─ TOTAL: 15.5 FTE

COMPARISON TO GOVERNMENT ESTIMATE:
Government Exhibit B suggests: 14.0 FTE
Our Estimate: 15.5 FTE (+1.5 FTE variance)
Justification: 99.9% uptime + 15-min P1 response requires additional NOC coverage
```

**Use Case**: Provides BOM foundation for pricing + cost realism justification.

---

## Category 1: Evaluation Factor Analysis

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

---

## How to Use This Library Effectively

### For Non-Experts (No RAG Knowledge Required)

1. **Find Your Task**: Scan category headers to find what you're trying to accomplish
2. **Read "Why This Works"**: Understand how the query triggers optimal results
3. **Copy Entire Query**: Select full query text (including example if shown)
4. **Customize Placeholders**: Replace [BRACKETS] with your RFP-specific terms
5. **Paste Into Chat**: Use query as-is in the chat input box
6. **Iterate if Needed**: Refine based on results, try related queries for deeper analysis

### Query Chaining for Comprehensive Analysis

**Capture Strategy Workflow**:

```
1. Category 1, Query 1.1: Compliance Checklist
   ↓
2. Category 2, Query 2.1: Proposal Outline
   ↓
3. Category 3, Query 3.1: Win Themes
   ↓
4. Category 4, Query 4.1: Questions for Government
   ↓
5. Category 7, Query 7.1: Workload Analysis (for pricing)
```

**Proposal Development Workflow**:

```
1. Generate outline (Cat 2, Query 2.1)
   ↓
2. Get section-specific guidance (Cat 2, Query 2.3) for each section
   ↓
3. Generate win themes and action captions (Cat 3, Query 3.1 + 3.3)
   ↓
4. Write proposal using guidance
   ↓
5. Assess compliance (Cat 6, Query 6.1) - Pink Team at 50%, Red Team at 75%
```

### Understanding Response Quality

**High-Quality Response Indicators**:

- ✅ Specific RFP paragraph references (Section L Para 4.3.1, not "Section L")
- ✅ Exact requirement text quoted from RFP
- ✅ Shipley methodology applied (benefit-discriminator-proof, page allocation by weight)
- ✅ Actionable recommendations with effort estimates
- ✅ Prioritization by impact (mandatory vs. important, high-risk vs. low-risk)

**Low-Quality Response Indicators** (Try refining your query):

- ❌ Generic answers that could apply to any RFP
- ❌ No specific RFP citations or evidence
- ❌ Missing Shipley principles (e.g., win themes without proof, outlines not aligned to factors)
- ❌ Incomplete analysis (e.g., compliance checklist but no gap analysis)

### Tips for Power Users

**Explicit Intent Specification** (Skip automatic routing):

```
Prefix your query with intent category if you want to force specific prompt behavior:

[COMPLIANCE_CHECKLIST] What are the requirements?
[PROPOSAL_OUTLINE] Structure the technical volume
[WIN_THEMES] Show competitive differentiation
```

**Context Stacking** (Multi-turn conversations):

```
Turn 1: "Generate compliance checklist"
Turn 2: "Now create outline based on those requirements"  ← Context-aware, knows you have checklist
Turn 3: "For Section 1.2 from that outline, show win themes"  ← References previous outline
```

**Handling Amendments**:

```
Always re-run compliance checklist after amendments:
"Compare baseline to Amendment 0002 - what changed?"
↓
"Regenerate compliance checklist incorporating Amendment 0002"
↓
"How does Amendment 0002 affect our current proposal draft?"
```

---

## Shipley Methodology Quick Reference

**Core Principles Embedded in These Queries**:

1. **Compliance First**: Address 100% of requirements BEFORE attempting differentiation
2. **Outline to Evaluation**: Proposal structure mirrors Section M factors
3. **Page Budget = Scoring Weight**: Allocate pages proportionally to factor importance
4. **Win Theme Formula**: Customer Benefit + Your Discriminator + Proof
5. **Action Captions**: Graphics answer "So what?" with customer benefits
6. **4-Level Compliance**: COMPLIANT | PARTIALLY COMPLIANT | NON-COMPLIANT | NOT ADDRESSED
7. **Past Performance Confidence**: Relevance + Recency + Quality = Confidence Rating
8. **Questions for Government**: Reduce YOUR risk, increase COMPETITORS' uncertainty

**Shipley Resources Referenced**:

- Shipley Capture Guide: Chapters on compliance, gap analysis, Q&A strategy, past performance
- Shipley Proposal Guide: Chapters on outlining, win themes, action captions, color team reviews

---

## Version History

**Version 2.0** (November 18, 2025 - Branch 020):

- ✅ Enhanced with Shipley methodology integration
- ✅ Added "Why This Works" explanations for non-experts
- ✅ Reorganized by capture/proposal workflow stages
- ✅ Added query chaining recommendations
- ✅ Integrated 6 specialized prompt behaviors (compliance_checklist, proposal_outline, win_themes, generate_qfg, compliance_assessment, workload_analysis)
- ✅ Expanded from 11 categories to 7 workflow-aligned categories
- ✅ Added amendment-specific queries (change detection, impact analysis)

**Version 1.0** (January 2025 - Branch 004):

- Initial query library based on Phase 1 RFP analysis capabilities

---

**Last Updated**: November 18, 2025 (Branch 020 - User Prompt Integration)  
**Methodology**: Shipley Capture Guide + Proposal Guide + LightRAG user_prompt system  
**Status**: Production-Ready - Copy-Paste Queries for End Users  
**Related Documentation**:

- `prompts/user_queries/README.md` (User query system overview)
- `docs/conditional_routing_design.md` (LLM-based intent classification architecture)
- Individual user prompts: `compliance_checklist.md`, `proposal_outline_generation.md`, `win_theme_identification.md`, `generate_qfg.md`, `compliance_assessment.md`, `workload_analysis.md`

**Future Enhancements**:

- Add RFP-type-specific query templates (Task Orders, IDIQs, GSA Schedule, SeaPort-e, OASIS)
- Expand amendment queries with delta analysis (before/after comparisons)
- Add competitive intelligence queries (FPDS research, past awardee analysis)
- Include evaluation factor weighting calculator queries
- Add Red Team checklist generator queries

---

**End of Enhanced Copy-Paste Query Library**

---

## Appendix: Original Category Structure (Preserved for Reference)

The following categories contain the original query structure from Version 1.0. These queries still work but may not have the enhanced "Why This Works" explanations or Shipley integration of Version 2.0 queries above.

### Category 1: Evaluation Factor Analysis (Original)
