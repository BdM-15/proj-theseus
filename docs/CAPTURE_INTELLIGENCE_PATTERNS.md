# Federal Capture Intelligence Patterns

**Purpose**: Document proven patterns for government contracting capture and proposal intelligence, extracted from industry best practices, federal acquisition methodology, and Branch 002 prompt engineering artifacts.

**Scope**: Ontology enhancement patterns for Phase 6 implementation - generic, non-proprietary framework applicable across federal contracting domain.

**Sources**:

- Industry capture management best practices (web research 2025)
- Federal acquisition methodology patterns
- Branch 002 prompt templates (prompts/ directory)
- Curated capture reference documentation (docs/SHIPLEY_LLM_CURATED_REFERENCE.md)

---

## Pattern Categories

### 1. Requirement Classification Framework

**Current State**: Generic REQUIREMENT entity with no subtyping or classification.

**Industry Pattern**: Federal RFPs contain 8 distinct requirement types, each requiring different compliance approaches and proposal strategies.

**Classification Schema**:

1. **Functional Requirements**

   - **Definition**: What the system, service, or solution must accomplish
   - **Examples**: "Shall provide 24/7 help desk support", "Must process transactions within 2 seconds"
   - **Compliance Strategy**: Demonstrate capability through past performance, technical approach
   - **Ontology Field**: `requirement_type = "FUNCTIONAL"`

2. **Performance Requirements**

   - **Definition**: Measurable outcomes, service levels, or quality metrics
   - **Examples**: "99.9% uptime", "Response within 4 hours", "Process 1000 transactions/hour"
   - **Compliance Strategy**: Quantified commitments, SLA frameworks, monitoring plans
   - **Ontology Field**: `requirement_type = "PERFORMANCE"`

3. **Interface Requirements**

   - **Definition**: System connections, data exchanges, interoperability standards
   - **Examples**: "Integrate with agency ERP system", "Support HTTPS/TLS 1.3", "API compatibility"
   - **Compliance Strategy**: Technical architecture diagrams, interface specifications
   - **Ontology Field**: `requirement_type = "INTERFACE"`

4. **Design Requirements**

   - **Definition**: Specific design constraints, standards, or architectural mandates
   - **Examples**: "Follow Section 508 accessibility", "Use NIST 800-53 controls", "Comply with agency branding"
   - **Compliance Strategy**: Standards compliance statements, design documentation
   - **Ontology Field**: `requirement_type = "DESIGN"`

5. **Security Requirements**

   - **Definition**: Cybersecurity, physical security, compliance, authorization needs
   - **Examples**: "FedRAMP Moderate authorization required", "FISMA compliance", "Background checks"
   - **Compliance Strategy**: Certification evidence, security plans, personnel clearances
   - **Ontology Field**: `requirement_type = "SECURITY"`

6. **Technical Requirements**

   - **Definition**: Technology specifications, platforms, tools, infrastructure
   - **Examples**: "AWS GovCloud deployment", "Use Java 11 or higher", "PostgreSQL database"
   - **Compliance Strategy**: Technical stack descriptions, tool certifications
   - **Ontology Field**: `requirement_type = "TECHNICAL"`

7. **Management Requirements**

   - **Definition**: Project management, reporting, governance, oversight
   - **Examples**: "Monthly status reports", "Use Agile/Scrum methodology", "PMI-certified PM"
   - **Compliance Strategy**: Management plans, reporting templates, personnel qualifications
   - **Ontology Field**: `requirement_type = "MANAGEMENT"`

8. **Quality Requirements**
   - **Definition**: Quality assurance, testing, verification, validation processes
   - **Examples**: "Automated test coverage 80%+", "ISO 9001 certification", "Peer review process"
   - **Compliance Strategy**: QA plans, testing frameworks, quality metrics
   - **Ontology Field**: `requirement_type = "QUALITY"`

**Implementation Strategy**:

- Add `requirement_type` metadata field to REQUIREMENT entities
- Parse requirement context during extraction to classify automatically
- Enable filtering by type for compliance matrices and gap analysis
- Map requirement types to evaluation factors for strategic emphasis

**Real-World Application**:
Federal agencies structure RFPs around these categories. Contractors who classify requirements systematically can:

- Allocate proposal effort proportionally (high-weight factors get more resources)
- Identify capability gaps early in capture phase
- Structure technical volumes to mirror government evaluation criteria
- Demonstrate comprehensive understanding of solicitation intent

---

### 2. Compliance Criticality Levels

**Current State**: No criticality tracking, cannot prioritize requirements by mandatory vs. desirable.

**Industry Pattern**: Federal acquisition uses modal verbs to signal requirement criticality. Understanding these distinctions prevents disqualification (missing "shall" items) and optimizes proposal effort.

**Criticality Schema**:

1. **MANDATORY (Shall/Must)**

   - **Signal Words**: "shall", "must", "is required to", "will be required"
   - **Meaning**: Non-negotiable contractor obligations - failure to comply = non-responsive proposal
   - **Government Intent**: Minimum acceptable standard, evaluation threshold
   - **Compliance Strategy**: Full compliance mandatory, highlight with "We comply with..." statements
   - **Priority Score**: 100 (highest)
   - **Examples**:
     - "Contractor shall provide 24/7 on-site support"
     - "Offeror must have FedRAMP Moderate authorization"
   - **Ontology Field**: `criticality_level = "MANDATORY"`

2. **IMPORTANT (Should)**

   - **Signal Words**: "should", "encouraged to", "desirable", "preferred"
   - **Meaning**: Strong government preference, likely evaluated for scoring advantages
   - **Government Intent**: Differentiation criteria, competitive advantage opportunities
   - **Compliance Strategy**: Address if feasible, explain trade-offs if not
   - **Priority Score**: 75
   - **Examples**:
     - "Offerors should propose Agile development methodology"
     - "Solutions are encouraged to include AI/ML capabilities"
   - **Ontology Field**: `criticality_level = "IMPORTANT"`

3. **OPTIONAL (May)**

   - **Signal Words**: "may", "can", "has the option to"
   - **Meaning**: Contractor choice, flexibility granted, potential value-add
   - **Government Intent**: Allow innovation, contractor-proposed enhancements
   - **Compliance Strategy**: Evaluate cost/benefit, propose if strategic advantage
   - **Priority Score**: 25
   - **Examples**:
     - "Contractor may propose alternative hosting solutions"
     - "Offeror can include warranty beyond base requirement"
   - **Ontology Field**: `criticality_level = "OPTIONAL"`

4. **INFORMATIONAL (Will - Government Action)**
   - **Signal Words**: "Government will provide", "Agency will...", "CO will..."
   - **Meaning**: Government commitments/responsibilities, NOT contractor requirements
   - **Government Intent**: Clarify government role, set expectations for collaboration
   - **Compliance Strategy**: Acknowledge in proposal context, plan integration
   - **Priority Score**: 0 (informational only)
   - **Examples**:
     - "Government will provide access to secure facility"
     - "Contracting Officer will issue task orders quarterly"
   - **Ontology Field**: `criticality_level = "INFORMATIONAL"`

**Implementation Strategy**:

- Add `criticality_level` metadata to REQUIREMENT entities
- Parse modal verbs during extraction (regex patterns: `\b(shall|must|should|may|will)\b`)
- Subject-verb analysis: "Contractor shall" = MANDATORY, "Government will" = INFORMATIONAL
- Automatic priority scoring: MANDATORY=100, IMPORTANT=75, OPTIONAL=25, INFORMATIONAL=0
- Flag all MANDATORY requirements for compliance matrix review

**Compliance Matrix Application**:

```
Priority 1: MANDATORY items (criticality_level = MANDATORY, score = 100)
  - Must have explicit compliance statement in proposal
  - Missing = non-responsive proposal risk
  - Section A admin items (deadlines, eligibility) always MANDATORY

Priority 2: IMPORTANT items (criticality_level = IMPORTANT, score = 75)
  - Strong preference, likely scored in evaluation
  - Address unless valid trade-off

Priority 3: OPTIONAL items (criticality_level = OPTIONAL, score = 25)
  - Value-add opportunities
  - Propose if competitive advantage

Ignore: INFORMATIONAL items (criticality_level = INFORMATIONAL)
  - Acknowledge for context, not contractor obligation
```

**Real-World Impact**:

- **Disqualification Prevention**: Contractors who miss "shall" requirements face rejection for non-responsiveness
- **Scoring Optimization**: "Should" items often tie to evaluation scoring - addressing these earns points
- **Effort Allocation**: Avoid wasting proposal pages on "may" items when "shall" compliance gaps exist
- **Risk Mitigation**: Parsing criticality early in capture phase identifies deal-breaker requirements

---

### 3. Evaluation Intelligence (Section L ↔ Section M Mapping)

**Current State**: Generic EVALUATION_FACTOR entity, no structured L↔M mapping, no importance weighting.

**Industry Pattern**: Federal RFPs separate submission instructions (Section L) from evaluation criteria (Section M). Winning contractors master the **L↔M relationship** to allocate proposal effort strategically.

**Section M: Evaluation Factors** (How Government Scores Proposals)

**Factor Structure**:

```json
{
  "factor_id": "M1",
  "factor_name": "Technical Approach",
  "section": "M",
  "relative_importance": "Most Important",
  "subfactors": [
    "Staffing Approach",
    "Maintenance Execution",
    "Transition Plan"
  ],
  "description": "Government evaluates contractor's understanding of requirements...",
  "tradeoff_methodology": "Best Value"
}
```

**Importance Terminology** (Common Federal RFP Patterns):

- **"Most Important"**: Highest weight factor, typically 40-50% of technical score
- **"Significantly More Important than Price"**: Best Value tradeoff favoring technical merit
- **"Significantly More Important than [Factor X]"**: Relative ranking (e.g., "Technical > Past Performance")
- **"Equal to [Factor Y]"**: Same weight in evaluation
- **"Less Important than [Factor Z]"**: Lower priority, but still evaluated
- **Point Allocation**: Explicit scoring (e.g., "Technical Approach: 40 points, Past Performance: 30 points")
- **Adjectival Ratings**: "Exceptional, Good, Acceptable, Marginal, Unacceptable" (color teams)

**Tradeoff Methodologies**:

- **Best Value**: Government can pay more for superior technical solution
- **Lowest Price Technically Acceptable (LPTA)**: Cheapest compliant proposal wins
- **Cost/Technical Tradeoff**: Balanced analysis with specified weighting

**Section L: Proposal Submission Instructions** (What to Submit)

**Instruction Patterns**:

```json
{
  "section_l_reference": "L.3.1",
  "volume_name": "Technical Volume",
  "page_limits": "25 pages",
  "format_requirements": "12pt Times New Roman, 1-inch margins, single-spaced",
  "content_required": "Address Technical Approach per Section M.2",
  "evaluated_by": "M2"
}
```

**L↔M Traceability**:

```
Section L.3.1: "Submit Technical Volume (25 pages) addressing Section M.2"
    ↓
Section M.2: "Technical Approach (Most Important) - Subfactors: Staffing, Maintenance, Transition"
    ↓
Proposal Strategy: Allocate 25 pages proportionally:
  - Staffing: 10 pages (critical differentiator)
  - Maintenance: 10 pages (high-weight requirement type)
  - Transition: 5 pages (lower risk, standard approach)
```

**Strategic Mistakes Contractors Make**:

1. ❌ **Ignoring Importance**: Spending 15 pages on low-weight factor, 5 pages on "Most Important" factor
2. ❌ **Missing Subfactors**: Addressing "Technical Approach" but skipping "Transition Plan" subfactor = point loss
3. ❌ **Page Limit Violations**: Exceeding L.3.1 "25 pages" = evaluators stop reading or disqualify
4. ❌ **Format Non-Compliance**: Using 10pt font when L specifies 12pt = non-responsive
5. ❌ **L↔M Misalignment**: Submitting Management Volume content in Technical Volume

**Enhanced EVALUATION_FACTOR Schema**:

```json
{
  "factor_id": "M2",
  "factor_name": "Technical Approach",
  "section": "M",
  "relative_importance": "Most Important",
  "subfactors": [
    "M2.1 Staffing Approach",
    "M2.2 Maintenance Execution",
    "M2.3 Transition Plan"
  ],
  "description": "Complete Section M text describing evaluation criteria",
  "tradeoff_methodology": "Best Value - Technical Merit significantly more important than Price",
  "section_l_reference": "L.3.1",
  "page_limits": "25 pages",
  "format_requirements": "12pt Times New Roman, 1-inch margins",
  "evaluated_by_rating": "Adjectival (Exceptional/Good/Acceptable/Marginal/Unacceptable)",
  "snippet": "Same as description field"
}
```

**Implementation Strategy**:

- Enhance EVALUATION_FACTOR entity with `relative_importance`, `subfactors`, `section_l_reference`, `page_limits`
- Parse Section M for factor hierarchy (M1 → M1.1 → M1.1.1)
- Parse Section L for submission instructions mapped to Section M factors
- Create L↔M relationship: `SECTION_L_INSTRUCTION → GUIDES_SUBMISSION_FOR → EVALUATION_FACTOR`
- Flag missing subfactors during compliance assessment
- Calculate recommended page allocation: `(factor_importance_weight / total_weight) * total_page_limit`

**Real-World Capture Application**:

**Capture Phase (Pre-RFP)**:

- Analyze past awards from agency to identify typical factor patterns
- Predict Section M structure based on agency evaluation history
- Pre-position past performance references matching likely factors

**Proposal Phase (Post-RFP Release)**:

1. **Day 1**: Extract all Section M factors and Section L instructions
2. **Day 2**: Create L↔M traceability matrix in compliance tool
3. **Week 1**: Allocate page budget per factor importance
4. **Throughout**: Validate every proposal section maps to Section M factor
5. **Final Review**: Verify subfactor coverage, page compliance, format adherence

**Evaluation Intelligence Example** (Navy MBOS RFP Pattern):

```
Section M.2: Technical Approach (Most Important)
  Subfactors:
    M.2.1: Staffing Approach
    M.2.2: Maintenance Execution Plan
    M.2.3: Transition/Phase-In Strategy

Section L.3.1: Technical Volume (25 pages)
  Address Section M.2 factors
  Include organizational chart (not counted toward page limit)
  Use 12pt font, 1-inch margins

Winning Strategy:
  - Staffing (40%): 10 pages, emphasize retention, surge capacity, clearances
  - Maintenance (40%): 10 pages, SLA commitments, tools, GFE management
  - Transition (20%): 5 pages, phased approach, knowledge transfer, risk mitigation
  - Organizational chart: Separate appendix (free pages)
  - Format: Strict 12pt Times, verify margins before submission
```

---

### 4. Competitive Positioning Themes

**Current State**: No competitive theme entity type, no strategic capture concepts in ontology.

**Industry Pattern**: Federal capture management emphasizes **strategic positioning** before RFP release and **competitive themes** during proposal development. These concepts differentiate winning proposals from merely compliant responses.

**Capture Phase Positioning** (Pre-RFP):

**Core Elements**:

1. **Customer Hot Buttons**

   - **Definition**: Agency's critical pain points, priorities, mission pressures
   - **Discovery**: Stakeholder interviews, agency strategic plans, past debriefs
   - **Examples**: "Reduce maintenance backlog", "Improve readiness rates", "Modernize legacy systems"
   - **Application**: Align solution messaging to address hot buttons explicitly
   - **Ontology Entity**: `STRATEGIC_THEME` with `theme_type = "CUSTOMER_HOT_BUTTON"`

2. **Competitive Discriminators**

   - **Definition**: Unique capabilities, approaches, or advantages vs. competitors
   - **Types**:
     - **Capability Discriminators**: Proprietary tools, certified personnel, facility access
     - **Approach Discriminators**: Innovative methodology, risk mitigation, proven process
     - **Relationship Discriminators**: Incumbent knowledge, agency familiarity, teaming strength
   - **Examples**: "Only offeror with on-site test facility", "Patented diagnostic tool", "Incumbent knowledge"
   - **Application**: Highlight discriminators that competitors cannot easily match
   - **Ontology Entity**: `STRATEGIC_THEME` with `theme_type = "DISCRIMINATOR"`

3. **Proof Points**

   - **Definition**: Evidence supporting competitive claims (past performance, metrics, references)
   - **Types**:
     - **Performance Metrics**: "99.8% uptime on similar contract", "40% cost savings delivered"
     - **Past Performance**: "Exceptional CPARS ratings on 3 Navy contracts"
     - **Certifications**: "CMMI Level 3", "ISO 20000", "FedRAMP In-Process"
     - **Customer Testimonials**: "Agency CIO endorsement letter"
   - **Examples**: "Achieved 98% first-time fix rate on current IDIQ", "Reduced backlog 60% in 6 months"
   - **Application**: Cite proof points immediately after discriminator claims
   - **Ontology Entity**: `STRATEGIC_THEME` with `theme_type = "PROOF_POINT"`
   - **Relationship**: `PROOF_POINT → VALIDATES → DISCRIMINATOR`

4. **Ghosting Strategy** (Ethical Competitive Intelligence)
   - **Definition**: Emphasizing strengths that expose competitor weaknesses WITHOUT naming them
   - **Ethical Approach**: Focus on positive framing, avoid disparagement
   - **Examples**:
     - "Our on-site team ensures rapid response" (ghosts remote-only competitors)
     - "20-year incumbent knowledge of agency systems" (ghosts new entrants)
     - "Cross-trained workforce eliminates single-point failures" (ghosts understaffed competitors)
   - **Application**: Structure proposal themes to highlight gaps competitors likely have
   - **Ontology Entity**: Not explicitly modeled, derived from `DISCRIMINATOR` analysis

**Proposal Phase Themes** (Post-RFP):

**Win Theme Framework**:

**Definition**: High-level strategic messages tying solution benefits to customer outcomes and evaluation factors.

**Win Theme Structure**:

```
THEME STATEMENT + DISCRIMINATOR + PROOF POINT + CUSTOMER BENEFIT

Example:
"Our HYBRID STAFFING MODEL [discriminator] delivers surge capacity within 48 hours
[proof: demonstrated on 3 Navy contracts] ensuring mission-critical maintenance
never delays fleet operations [customer benefit: readiness focus]."
```

**Win Theme Categories**:

1. **Technical Superiority**: Solution innovation, methodology, tools
2. **Management Excellence**: Proven processes, risk mitigation, quality controls
3. **Past Performance Strength**: Relevant experience, customer satisfaction, metrics
4. **Cost Effectiveness**: Value engineering, cost control, ROI
5. **Mission Understanding**: Agency familiarity, domain expertise, cultural fit

**Win Theme → Requirement Mapping**:

```
WIN_THEME: "Hybrid Staffing Model ensures surge capacity"
  ↓ SUPPORTS
REQUIREMENT: "Contractor shall respond to urgent maintenance within 24 hours" (REQ-C045)
  ↓ EVALUATED_BY
EVALUATION_FACTOR: "M.2.1 Staffing Approach" (Most Important subfactor)
  ↓ COMPETITIVE_ADVANTAGE
DISCRIMINATOR: "On-site + on-call team structure" (vs. remote-only competitors)
  ↓ VALIDATED_BY
PROOF_POINT: "Achieved 2.1-hour average response time on similar contract"
```

**Implementation Strategy**:

- Add `STRATEGIC_THEME` entity type with subtypes:
  - `theme_type = "CUSTOMER_HOT_BUTTON"`: Agency priorities
  - `theme_type = "DISCRIMINATOR"`: Competitive advantages
  - `theme_type = "PROOF_POINT"`: Evidence/metrics
  - `theme_type = "WIN_THEME"`: Proposal messaging
- Relationships:
  - `STRATEGIC_THEME → ADDRESSES → REQUIREMENT`
  - `STRATEGIC_THEME → SUPPORTS → EVALUATION_FACTOR`
  - `STRATEGIC_THEME → DIFFERENTIATED_BY → ORGANIZATION` (prime/sub capabilities)
  - `PROOF_POINT → VALIDATES → DISCRIMINATOR`
  - `WIN_THEME → COMBINES → [DISCRIMINATOR + PROOF_POINT + CUSTOMER_HOT_BUTTON]`

**Extraction Sources**:

- Section L instructions: Often include "emphasize" or "describe approach" language (hot buttons)
- Section M evaluation criteria: High-importance factors signal what government values
- RFP background (Section B/C): Agency mission, challenges, goals
- Past performance requirements: Types of relevant experience (discriminator opportunities)

**Real-World Capture Application**:

**Capture Planning** (6-12 months pre-RFP):

```
1. Customer Hot Button Discovery:
   - Interview program manager: "What keeps you up at night?"
   - Review agency strategic plan: Identify mission priorities
   - Analyze incumbent challenges: Where are current gaps?

2. Discriminator Development:
   - Competitive analysis: What do we have that others don't?
   - Team with partners: Fill capability gaps before RFP drops
   - Invest in certifications: Build discriminators (e.g., FedRAMP authorization)

3. Proof Point Collection:
   - Gather metrics from current contracts: Response times, uptime %, cost savings
   - Request CPARS ratings: Document "Exceptional" ratings
   - Secure testimonials: Agency POC endorsements

4. Ghosting Strategy:
   - Incumbent weaknesses: If known, build strengths that expose their gaps
   - New entrant risks: Emphasize experience, relationships, knowledge
   - Large prime concerns: Highlight agility, direct access, flexibility
```

**Proposal Development** (Post-RFP):

```
1. Win Theme Generation (Day 1-3):
   - Map hot buttons to evaluation factors
   - Align discriminators to high-weight subfactors
   - Pair each discriminator with 2-3 proof points

2. Requirement Traceability (Week 1):
   - Link win themes to MANDATORY requirements (criticality = 100)
   - Ensure every "Most Important" factor has 3+ win themes

3. Proposal Writing (Throughout):
   - Open every section with win theme statement
   - Support with proof points (metrics, past performance)
   - Tie to customer benefit (mission outcomes)

4. Review Gates:
   - Pink Team: Do themes resonate? Any missing hot buttons?
   - Red Team: Are discriminators credible? Proof points sufficient?
   - Gold Team: Consistent messaging? Themes reinforce each other?
```

**Navy MBOS Example**:

```
Hot Button (from agency interviews): "Maintenance backlog reducing fleet readiness"

Discriminator: "Hybrid staffing model (on-site + on-call surge team)"

Proof Point: "Reduced backlog 60% in 6 months on current Navy contract (CPARS: Exceptional)"

Win Theme: "Our proven hybrid staffing approach eliminates maintenance delays, ensuring
aircraft availability for critical missions—validated by 60% backlog reduction and
Exceptional CPARS ratings on 3 Navy facilities."

Requirement Link: REQ-C045 "Contractor shall respond within 24 hours" (MANDATORY)
Evaluation Link: M.2.1 "Staffing Approach" (Most Important subfactor)
```

---

### 5. Coverage Assessment Framework

**Current State**: No compliance scoring methodology, cannot quantify proposal quality vs. requirements.

**Industry Pattern**: Proposal teams use **graduated coverage scoring** (0-100 scale) during internal reviews (Pink/Red/Gold teams) to assess compliance quality and identify gaps before submission.

**Coverage Scoring Scale** (Industry Standard):

| Score   | Rating             | Definition                                                                   | Compliance Status | Action Required               |
| ------- | ------------------ | ---------------------------------------------------------------------------- | ----------------- | ----------------------------- |
| **100** | **Exact**          | Explicit compliance statement + sufficient context + proof point             | Fully Compliant   | None - maintain quality       |
| **95**  | **Complete**       | Clear compliance, minor clarity improvement possible (e.g., add proof point) | Compliant         | Optional enhancement          |
| **85**  | **Mostly Covered** | Addresses requirement but missing 1 substantive detail or proof              | Compliant         | Strengthen with detail/metric |
| **70**  | **Present**        | Requirement addressed but structural weakness (over page limit, weak proof)  | At Risk           | Fix structural issue          |
| **50**  | **Mention Only**   | Requirement acknowledged without substantive response                        | Non-Compliant     | Major rewrite needed          |
| **30**  | **Indirect**       | Implied or inferred compliance, not explicitly stated                        | Non-Compliant     | Add explicit statement        |
| **10**  | **Bare Hint**      | Relevant term appears once, no actual coverage                               | Non-Compliant     | Full response required        |
| **0**   | **Missing**        | Requirement not addressed anywhere in proposal                               | Non-Compliant     | Critical gap - add content    |

**Scoring Application by Criticality**:

**MANDATORY Requirements** (criticality_level = "MANDATORY"):

- **Threshold**: 85+ required (anything below = high risk)
- **Target**: 95-100 for all "shall/must" requirements
- **Rationale**: Non-compliance with mandatory items = non-responsive proposal

**IMPORTANT Requirements** (criticality_level = "IMPORTANT"):

- **Threshold**: 70+ acceptable, 85+ competitive
- **Target**: 95+ for high-weight evaluation factors
- **Rationale**: "Should" requirements often scored - full coverage earns points

**OPTIONAL Requirements** (criticality_level = "OPTIONAL"):

- **Threshold**: 0-100 (propose if strategic advantage)
- **Target**: 85+ if included (don't propose half-measures)
- **Rationale**: Better to skip than propose weak optional approach

**Gap Analysis Metadata**:

For requirements scoring <95, document:

```json
{
  "req_id": "REQ-C045",
  "coverage_score": 70,
  "proposal_evidence": "Section 3.2 page 15: 'We will provide rapid response maintenance'",
  "gaps": [
    "No specific response time commitment (requirement says 24 hours)",
    "Missing staffing details for surge capacity",
    "No past performance metric validating response times"
  ],
  "risk_level": "HIGH",
  "risk_rationale": "MANDATORY requirement (shall), high-weight subfactor (M.2.1 Staffing)",
  "suggestion": "Add explicit '24-hour response guarantee' with proof point from Navy contract (avg 2.1-hour response time, Exceptional CPARS). Reference page 55 compliance matrix for traceability.",
  "estimated_fix_effort": "2 hours - rewrite paragraph, add proof point, update compliance matrix"
}
```

**Risk Assessment Framework**:

**Risk Level Calculation**:

```
risk_level = f(criticality, coverage_score, evaluation_weight, competitive_context)

HIGH RISK:
- MANDATORY requirement + coverage_score < 85
- "Most Important" evaluation factor + coverage_score < 85
- Section A admin item (deadlines, eligibility) + coverage_score < 100
- Known competitor strength + coverage_score < 95

MEDIUM RISK:
- IMPORTANT requirement + coverage_score 70-84
- High-weight factor + coverage_score 85-94
- Discriminator claim without proof point

LOW RISK:
- OPTIONAL requirement + any coverage_score
- IMPORTANT requirement + coverage_score 85+
- Low-weight factor + coverage_score 70+
```

**Risk Factors**:

1. **Technical Risk**: Unproven capability, immature technology, skill gaps
2. **Schedule Risk**: Tight timeline, dependency on government, aggressive milestones
3. **Cost Risk**: Unrealistic pricing, insufficient cost basis, hidden costs
4. **Compliance Risk**: Ambiguous requirement interpretation, format violations, missing sections

**Critical Summary Generation**:

After scoring all requirements, generate executive-level summary:

```json
{
  "summary": {
    "total_reqs": 347,
    "mandatory_reqs": 189,
    "important_reqs": 124,
    "optional_reqs": 34,
    "overall_compliance_rate": 87.3,
    "mandatory_compliance_rate": 91.2,
    "critical_gaps": 12,
    "high_risk_reqs": ["REQ-A002", "REQ-C045", "REQ-L018"],
    "section_coverage": {
      "Section A (Admin)": 95.8,
      "Section C (SOW)": 85.1,
      "Section L (Instructions)": 88.7,
      "Section M (Evaluation)": 89.4
    },
    "factor_coverage": {
      "M.2.1 Staffing Approach (Most Important)": 82.5,
      "M.2.2 Maintenance Execution": 91.3,
      "M.3 Past Performance": 96.7,
      "M.4 Cost/Price": 78.2
    },
    "critical_themes_coverage": {
      "24/7 Rapid Response": 70.0,
      "GFE Management": 88.5,
      "Transition/Phase-In": 93.2
    },
    "recommendation": "Address 12 critical gaps (coverage < 85 on MANDATORY requirements). Priority: REQ-A002 (proposal deadline), REQ-C045 (response time), REQ-L018 (page limits)."
  }
}
```

**Implementation Strategy**:

- Add metadata to REQUIREMENT entities:
  - `coverage_score`: 0-100 integer
  - `proposal_evidence`: String (quote from proposal with page ref)
  - `gaps`: Array of strings (specific missing elements)
  - `risk_level`: "HIGH" | "MEDIUM" | "LOW"
  - `risk_factors`: Array of risk types
  - `suggestion`: String (fix recommendation with effort estimate)
- Generate `critical_summary` JSON during compliance assessment
- Prioritize review cycles based on risk levels (High Risk = Pink Team focus)
- Track coverage score improvements across color team reviews

**Proposal Review Process**:

**Pink Team** (Early Draft - 60% Complete):

- **Focus**: Concept validation, theme resonance, outline compliance
- **Coverage Target**: 70+ average (concepts present, details emerging)
- **Action**: Identify missing sections, validate L↔M mapping, confirm themes

**Red Team** (Mature Draft - 90% Complete):

- **Focus**: Compliance rigor, customer perspective, competitive positioning
- **Coverage Target**: 85+ average, 95+ on MANDATORY requirements
- **Action**: Score every requirement, document gaps, assign fix responsibilities

**Gold Team** (Final Draft - 99% Complete):

- **Focus**: Consistency, polish, format compliance, final quality check
- **Coverage Target**: 95+ average, 100 on Section A admin items
- **Action**: Verify gap fixes, confirm page limits, final proofread

**Real-World Application**:

**Compliance Matrix Generation** (Red Team Output):

```
Requirement: REQ-C045 "Contractor shall respond to urgent maintenance within 24 hours"
Criticality: MANDATORY (shall)
Requirement Type: PERFORMANCE (measurable SLA)
Evaluated By: M.2.1 Staffing Approach (Most Important subfactor)
Relative Importance: Most Important (40% of technical score)

Proposal Evidence: "Section 3.2.1 page 15: 'Our hybrid staffing model ensures rapid response...'"
Coverage Score: 70 (Present but missing specifics)

Gaps:
  - No explicit "24-hour" commitment stated
  - Missing staffing details for surge capacity
  - No proof point validating response times

Risk Level: HIGH
Risk Rationale: MANDATORY + Most Important factor + score < 85 = non-responsive risk

Suggestion:
  "Revise Section 3.2.1 to include explicit commitment: 'We guarantee 24-hour response
  to urgent maintenance requests via our hybrid staffing model (6 on-site technicians +
  4 on-call surge team). Our proven approach delivered 2.1-hour average response time on
  similar Navy contract (CPARS: Exceptional).' Add to compliance matrix page 55."

Estimated Fix Effort: 2 hours (rewrite paragraph, add proof point, update matrix)
Assigned To: Technical Volume Lead
Due Date: Red Team iteration close (3 days)
```

**Post-Submission Application**:

- Debriefs: Compare internal coverage scores to government evaluation feedback
- Lessons Learned: Calibrate scoring methodology based on win/loss outcomes
- Process Improvement: Adjust scoring thresholds for future proposals

---

## Phase 6 Implementation Roadmap

### Ontology Enhancements

**1. REQUIREMENT Entity Enhancements**:

```python
# Add metadata fields
requirement_type: Literal["FUNCTIONAL", "PERFORMANCE", "INTERFACE", "DESIGN",
                          "SECURITY", "TECHNICAL", "MANAGEMENT", "QUALITY"]
criticality_level: Literal["MANDATORY", "IMPORTANT", "OPTIONAL", "INFORMATIONAL"]
priority_score: int  # 0-100 derived from criticality
coverage_score: int  # 0-100 from compliance assessment
proposal_evidence: str  # Quote from proposal with page reference
gaps: List[str]  # Specific missing elements if coverage_score < 95
risk_level: Literal["HIGH", "MEDIUM", "LOW"]
risk_factors: List[str]  # ["TECHNICAL", "SCHEDULE", "COST", "COMPLIANCE"]
suggestion: str  # Fix recommendation with effort estimate
```

**2. EVALUATION_FACTOR Entity Enhancements**:

```python
# Add structured fields
factor_id: str  # "M1", "M2.1", etc.
relative_importance: str  # "Most Important", "Significantly More Important than Price"
subfactors: List[str]  # ["M2.1 Staffing", "M2.2 Maintenance", "M2.3 Transition"]
section_l_reference: str  # "L.3.1" mapping to submission instructions
page_limits: str  # "25 pages" from Section L
format_requirements: str  # "12pt Times New Roman, 1-inch margins"
tradeoff_methodology: str  # "Best Value", "LPTA"
evaluated_by_rating: str  # "Adjectival", "Point Score", "Pass/Fail"
```

**3. STRATEGIC_THEME Entity (NEW)**:

```python
# New entity type for competitive positioning
entity_type = "STRATEGIC_THEME"
theme_type: Literal["CUSTOMER_HOT_BUTTON", "DISCRIMINATOR", "PROOF_POINT", "WIN_THEME"]
theme_statement: str  # Full theme description
competitive_context: str  # "Incumbent advantage", "New entrant gap", etc.
evidence: str  # Proof points, metrics, past performance
customer_benefit: str  # Mission outcome, agency value
```

**4. Relationship Enhancements**:

```python
# New relationships
STRATEGIC_THEME → ADDRESSES → REQUIREMENT
STRATEGIC_THEME → SUPPORTS → EVALUATION_FACTOR
STRATEGIC_THEME → DIFFERENTIATED_BY → ORGANIZATION (prime/sub)
PROOF_POINT → VALIDATES → DISCRIMINATOR
WIN_THEME → COMBINES → [DISCRIMINATOR + PROOF_POINT + CUSTOMER_HOT_BUTTON]
SECTION_L_INSTRUCTION → GUIDES_SUBMISSION_FOR → EVALUATION_FACTOR
REQUIREMENT → EVALUATED_BY → EVALUATION_FACTOR (with weight/importance)
```

### Extraction Prompt Updates

**Requirements Extraction**:

- Add requirement type classification logic (8 types)
- Parse modal verbs for criticality levels (shall/should/may/will)
- Calculate priority scores automatically
- Extract Section M factors with full metadata
- Map Section L instructions to Section M factors

**Compliance Assessment**:

- Implement 0-100 scoring scale with gradations
- Generate gap analysis for coverage_score < 95
- Calculate risk levels based on criticality + coverage + evaluation weight
- Produce critical summary with factor coverage breakdown

**Strategic Theme Extraction**:

- Parse Section L/M for customer hot button language ("emphasize", "critical", "essential")
- Identify evaluation factor importance statements as hot button signals
- Extract RFP background (Section B/C) for mission priorities
- Generate theme placeholders for capture team to populate with discriminators/proof points

### Validation Test Case

**Navy MBOS Baseline Gap Analysis**:
User preserved Navy MBOS knowledge graph externally (594 entities, 584 relationships) with noted gaps: "there were some gaps or data that should have been connected, but were not."

**Phase 6 Validation**:

1. Re-process Navy MBOS RFP with enhanced ontology
2. Compare entity counts and relationship density vs. baseline
3. Measure gap improvements:
   - Requirement classification coverage (% with requirement_type)
   - Criticality parsing accuracy (MANDATORY "shall" detection rate)
   - L↔M mapping completeness (% of Section M factors linked to Section L)
   - Strategic theme extraction (hot buttons, discriminators from evaluation factors)
4. Document connection gaps filled vs. baseline
5. Validate 417x speedup maintained (69 seconds target)

**Success Criteria**:

- ≥90% requirements classified by type
- ≥95% criticality levels parsed correctly
- 100% Section M factors mapped to Section L instructions
- ≥3 strategic themes extracted per "Most Important" evaluation factor
- Zero performance regression (≤80 seconds processing time)

---

## Terminology Reference

**Industry-Standard Terms Used** (Non-Proprietary):

- **Capture Management**: Pre-RFP strategic positioning, opportunity qualification
- **Compliance Matrix**: Requirement-to-proposal traceability tool
- **Coverage Assessment**: Proposal quality scoring methodology
- **Criticality Levels**: Requirement importance classification (Mandatory/Important/Optional)
- **Customer Hot Buttons**: Agency priorities, pain points, mission pressures
- **Discriminator**: Competitive advantage, unique capability
- **Evaluation Factor**: Section M criteria used to score proposals
- **Ghosting**: Ethical competitive strategy emphasizing strengths that expose competitor gaps
- **L↔M Mapping**: Section L (submission instructions) to Section M (evaluation criteria) traceability
- **Proof Point**: Evidence supporting competitive claims (metrics, past performance)
- **Requirement Types**: Standard classification (Functional, Performance, Interface, Design, Security, Technical, Management, Quality)
- **Risk Assessment**: Proposal compliance risk evaluation framework
- **Win Theme**: Strategic messaging tying solution to customer outcomes and evaluation factors

**FAR-Based Terminology**:

- **Best Value**: Tradeoff methodology allowing government to pay more for superior technical solution
- **LPTA (Lowest Price Technically Acceptable)**: Tradeoff methodology where cheapest compliant proposal wins
- **Section A-M**: Standard federal RFP structure (A: Solicitation Form, B: Supplies/Services, C: SOW/PWS, L: Instructions, M: Evaluation)
- **Subfactor**: Hierarchical evaluation criteria under main factors (e.g., M.2.1 under M.2)
- **Tradeoff Methodology**: Government's approach to balancing technical merit vs. cost

**Avoided Proprietary Terms**:

- No vendor-specific methodology names referenced in code or ontology
- All patterns described using generic industry-standard language
- Documentation references methodology concepts, not trademarked frameworks

---

## Document Metadata

**Version**: 1.0  
**Created**: 2025-01-06  
**Purpose**: Phase 5 extraction deliverable - Ontology enhancement patterns for Phase 6 implementation  
**Sources**: Industry research, federal acquisition methodology, Branch 002 prompt artifacts  
**Next Phase**: Implement enhancements in `src/raganything_server.py` ontology configuration  
**Validation**: Re-process Navy MBOS RFP, measure gap improvements vs. baseline (594 entities, 584 relationships)

---

**End of Document**
