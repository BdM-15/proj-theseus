# Entity Extraction Framework: 5 Annotated Examples + Proven Patterns

**Purpose**: Demonstrate how to extract entities from real RFP content with operational context  
**Model**: xAI Grok-4-fast-reasoning (2M context window)  
**Approach**: Semantic-first detection with topic taxonomy and 6 inference algorithms  
**Last Updated**: October 28, 2025 (Architecture Redesign - Proven Patterns)

---

## Philosophy: Learn from Real Examples

This framework shows you exactly how successful extraction works by walking through **5 annotated RFP examples**—not abstract rules, but real government contracting scenarios.

Each example demonstrates:
1. How to detect entity candidates
2. Why they're classified as specific types
3. What operational context matters
4. How relationships form naturally from content

---

## EXAMPLE 1: Section L↔M Relationship (Submission Instructions → Evaluation Factors)

### RFP Text (from Navy MBOS)

```
Section L.3.2 Technical Volume Format Requirements:

The Technical Volume shall not exceed 25 pages, using 12-point Times New Roman font,
single-spaced, with 1-inch margins on all sides. Graphics and diagrams are not counted
toward the page limit. The Technical Volume shall address Section M evaluation factors
1.1, 1.2, and 1.3 (Technical Approach, Innovation, Risk Mitigation).

Section M.1 Technical Approach (40% weight):

The Government will evaluate the proposed technical approach based on:
- Solution Architecture and design quality (30% of factor weight)
- Demonstrated innovation and advanced capabilities (30% of factor weight)  
- Risk identification and mitigation strategies (40% of factor weight)

The Technical Volume limited to 25 pages (see Section L) is evaluated using adjectival
ratings: Outstanding, Good, Acceptable, Marginal, Unacceptable.
```

### Extraction (Annotated)

#### Entity 1: SUBMISSION_INSTRUCTION
```
Type: SUBMISSION_INSTRUCTION
Name: Technical Volume Page Limit and Format
Description: Technical Volume limited to 25 pages maximum, 12pt Times New Roman, 
single-spaced, 1-inch margins. Graphics not counted toward page limit. Evaluates 
addressing of Section M Technical Approach factors 1.1-1.3. Violation = content 
on pages 26+ not reviewed. Strategic implication: 25-page constraint requires 
high-density technical content, favor graphics (unlimited), prioritize discriminators.

Extracted from: Section L.3.2
Confidence: 1.0 (explicit format specification)
Key signals: "shall not exceed", "pages", "font", "margins"
```

#### Entity 2: EVALUATION_FACTOR
```
Type: EVALUATION_FACTOR
Name: Factor 1: Technical Approach (40% weight)
Description: PRIMARY evaluation factor (highest weight in Three-Factor Trinity 
structure). Weight: 40% of total score (Section M Para 1). Methodology: Adjectival 
ratings (Outstanding/Good/Acceptable/Marginal/Unacceptable) per FAR 15.305. Subfactors: 
1.1 Solution Architecture (30% of factor), 1.2 Innovation (30%), 1.3 Risk Mitigation (40%). 
Evaluates HOW contractor will execute technical work. Page limit: 25 pages (see L.3.2) - 
this is HIGH constraint, requires content prioritization. Strategic opportunity: 
Outstanding rating requires innovation + proven approach + risk detail.

Extracted from: Section M.1
Confidence: 1.0 (explicit factor definition with weights)
Key signals: "will be evaluated", "40% weight", "Outstanding/Good/Acceptable", "subfactors"
```

#### Relationship 1: SUBMISSION_INSTRUCTION --GUIDES--> EVALUATION_FACTOR
```
Source: Technical Volume Page Limit and Format (SUBMISSION_INSTRUCTION)
Target: Factor 1: Technical Approach (EVALUATION_FACTOR)
Type: GUIDES
Description: Section L page limit (25 pages) guides how Technical Approach is 
evaluated and presented. Format constraint (12pt, 1-inch margins) affects proposal 
outline strategy. Page limit directly impacts how much content can address each 
subfactor (1.1, 1.2, 1.3). Proposal teams must prioritize highest-value content 
within 25-page envelope.

Confidence: 0.95 (explicit Section L→M cross-reference)
Key signals: "see Section L", "limited to 25 pages", "evaluates addressing of"
Business value: Proposal teams know to spend ~6 pages on Solution Architecture 
(1.1, 30% of factor), ~6 pages on Innovation (1.2, 30%), ~9 pages on Risk Mitigation 
(1.3, 40%), leaving 4 pages for executive summary and integration.
```

---

## EXAMPLE 2: Requirements Classification with Criticality Levels

### RFP Text (from MCPP II)

```
Section C.2.1 Help Desk Support Service

The contractor SHALL provide Tier 1, 2, and 3 help desk support to all 185,000 
active users across CONUS and OCONUS locations. The contractor SHALL maintain 
a maximum 60-second answer rate >90% for all inbound calls and 4-hour resolution 
time for Priority 1 incidents (critical system outages). The contractor SHOULD 
aim for first-call resolution >70%. The contractor MAY provide advanced 
self-service portal capabilities beyond basic ticket submission.

Performance is monitored via SCCM integrations and scored on Section M.2 
Management Approach factor.
```

### Extraction (Annotated)

#### Entity 1: REQUIREMENT (Mandatory)
```
Type: REQUIREMENT
Criticality: MANDATORY (SHALL)
Name: Help Desk Tier 1-3 Support for 185,000 Users
Description: Contractor SHALL provide Tier 1, 2, and 3 help desk support for 
185,000 active users across CONUS and OCONUS locations (Section C.2.1). Non-compliance 
= contract failure (mandatory obligation). Performance measured via SCCM monitoring, 
scored under Factor M.2 (Management Approach). Staffing implications: Need ~15 FTEs 
for 24/7 coverage, all requiring Security+ certification and Secret clearance (from 
Section H.5.2). Cost impact: ~$1.2M annually for staffing + infrastructure. Risk: 
OCONUS coverage difficult (only 3 major bases, limited contractor presence).

Extracted from: Section C.2.1
Confidence: 1.0 (explicit "SHALL" language)
Key signals: "shall provide", "all users", "monitored via", "scored on"
Criticality: MANDATORY (non-compliance = rejection)
```

#### Entity 2: REQUIREMENT (Recommended)
```
Type: REQUIREMENT
Criticality: RECOMMENDED (SHOULD)
Name: Help Desk First-Call Resolution >70%
Description: Contractor SHOULD aim for first-call resolution >70% (Section C.2.1). 
Non-compliance = reduced score, not rejection (recommended, not mandatory). This KPI 
affects quality evaluation under Factor M.2. Industry benchmark: 60-75% typical for 
large help desk environments (185K users makes >70% ambitious). Implications: Need 
experienced Tier 1 technicians, comprehensive knowledge management system, good 
documentation. Proposal strategy: If achievable based on past performance, commit to 70%+ 
(competitive advantage); if risky, propose 65% with escalation path.

Extracted from: Section C.2.1
Confidence: 0.95 ("should aim for" = recommended)
Key signals: "should aim for", "KPI", "quality"
Criticality: RECOMMENDED (non-compliance = scoring penalty, not rejection)
```

#### Entity 3: REQUIREMENT (Optional)
```
Type: REQUIREMENT
Criticality: OPTIONAL (MAY)
Name: Advanced Self-Service Portal Capabilities
Description: Contractor MAY provide advanced self-service portal capabilities 
beyond basic ticket submission (Section C.2.1). Discretionary capability—no penalty 
for not providing, but could be competitive advantage if offered. Examples: AI chatbots, 
knowledge base search, user community forums. This likely evaluates under Factor M.2 
or Factor 1 (Technical Approach) as innovation discriminator. Cost: $100K-$500K depending 
on sophistication. Risk: If proposed, must commit to supporting it (service degradation 
= negative past performance).

Extracted from: Section C.2.1
Confidence: 1.0 ("may provide" = optional)
Key signals: "may provide", "beyond basic", "discretionary"
Criticality: OPTIONAL (discretionary, no compliance penalty)
```

---

## EXAMPLE 3: Clause with Operational Context and Flowdown Implications

### RFP Text

```
Section I: Contract Clauses

52.204-21 Basic Safeguarding of Covered Defense Information. The contractor 
shall implement NIST SP 800-171 Rev 2 for all Covered Unclassified Information (CUI). 
Contractor must achieve System Security Plan (SSP) approval within 30 days of award. 
Non-compliance = contract ineligibility for award. This clause flows down to all 
subcontractors handling CUI.
```

### Extraction (Annotated)

#### Entity: CLAUSE with Domain Intelligence
```
Type: CLAUSE
Name: FAR 52.204-21 Basic Safeguarding of Covered Defense Information
Description: MANDATORY cybersecurity compliance clause per Section I (incorporated 
by reference per FAR 52.252-2). Requires implementation of NIST SP 800-171 Rev 2 
(110 security controls) for all Covered Unclassified Information (CUI) and Controlled 
Technical Information (CTI). Deliverables: System Security Plan (SSP) due within 30 
days of award, Plan of Action & Milestones (POA&M) for gaps, SPRS score upload 
(minimum 110 points recommended). Non-compliance = contract INELIGIBILITY for award 
(absolute gate). Flowdown: YES—mandatory flowdown to ALL subcontractors handling CUI 
(affects teaming agreements, subcontractor selection). Cost impact: Gap assessment 
$10K-$50K, remediation $50K-$500K depending on current NIST maturity. Timeline: 
SSP due 30 days post-award = fast-track requirement (plan in proposal, execute immediately 
after award). Evaluation: Likely assessed under "Technical Approach - Security Architecture" 
as discriminator (higher SPRS score = competitive advantage). Related FAR clauses: 52.204-25 
(Prohibition on Kaspersky software), DFARS 252.204-7012 (CMMC successor).

Domain context: Many small businesses fail this gate; if already compliant at SPRS 100+, 
emphasize as major differentiator.

Extracted from: Section I
Confidence: 1.0 (explicit FAR citation)
Key signals: "52.204-21", "NIST 800-171", "flows down", "non-compliance = ineligibility"
```

#### Relationship: CLAUSE --REQUIRES--> DOCUMENT
```
Source: FAR 52.204-21 (CLAUSE)
Target: NIST SP 800-171 Rev 2 (DOCUMENT)
Type: REQUIRES
Description: FAR 52.204-21 mandates implementation of NIST SP 800-171 Rev 2 as 
compliance framework. Contractor must understand all 110 controls, assess current state, 
identify gaps, develop POA&M, achieve SPRS score. This is absolute requirement, not optional.

Confidence: 1.0 (explicit requirement in clause)
Business value: Guides bid/no-bid decision (can we achieve NIST 800-171 compliance?), 
affects cost estimate, influences teaming decisions (need security SMEs?).
```

---

## EXAMPLE 4: Attachment/Annex Linkage with Agency-Specific Naming

### RFP Text

```
Section J: List of Attachments

J-02000000   Performance Work Statement (PWS)
J-03000000   Quality Assurance Surveillance Plan (QASP)
J-04000000   Contract Data Requirements List (CDRL)
J-05000000   DD Form 254 (Security Requirements)
J-07000000   Past Performance Forms
```

### Extraction (Annotated)

#### Entity 1: DOCUMENT (PWS)
```
Type: DOCUMENT (also could classify as STATEMENT_OF_WORK for content)
Name: J-02000000 Performance Work Statement (PWS)
Description: Primary statement of work for contract (Attachment J-02000000). Contains 
detailed task descriptions, performance requirements, staffing levels, deliverables 
by milestone, key performance indicators (KPIs). Location: Section J, explicitly 
listed as attachment. Agency pattern: DoD/Navy uses "J-########" naming convention 
for all Section J attachments (this is standard, not variant). Expected content: 
Services scope, performance objectives, performance periods, location(s), labor 
categories, CLIN mapping.

Extracted from: Section J attachment list
Confidence: 1.0 (explicit attachment listing)
Key signals: "J-02000000", "Performance Work Statement", "Section J"
```

#### Entity 2: DOCUMENT (QASP)
```
Type: DOCUMENT
Name: J-03000000 Quality Assurance Surveillance Plan (QASP)
Description: Government's quality monitoring plan defining how contractor performance 
will be measured and monitored (Attachment J-03000000). Typical content: Performance 
metrics, inspection frequency, acceptance criteria, surveillance methods, reporting 
requirements. Critical to understand BEFORE proposal (tells you how government scores 
compliance). Location: Section J, explicitly listed. Agency pattern: QASP always follows 
PWS (standard DoD/Navy sequence).

Extracted from: Section J attachment list
Confidence: 1.0 (explicit attachment listing)
Key signals: "J-03000000", "Quality Assurance Surveillance Plan", "Section J"
```

#### Entity 3: DOCUMENT (CDRL)
```
Type: DOCUMENT
Name: J-04000000 Contract Data Requirements List (CDRL)
Description: Government's formal list of contract deliverables with deliverable 
due dates, formats, submission requirements (Attachment J-04000000). Includes CDRL 
line items (A001, B002, etc.), Data Item Descriptions (DIDs), delivery schedules. 
Critical: Must price each CDRL item separately (labor hours × rate). Location: 
Section J, explicitly listed.

Extracted from: Section J attachment list
Confidence: 1.0 (explicit attachment listing)
Key signals: "J-04000000", "Contract Data Requirements List", "Section J"
```

#### Relationships: Multiple DOCUMENTS --ATTACHMENT_OF--> SECTION
```
Source 1: J-02000000 PWS
Target: Section J (List of Attachments)
Type: ATTACHMENT_OF
Confidence: 1.0 (explicit listing in Section J)

Source 2: J-03000000 QASP
Target: Section J (List of Attachments)
Type: ATTACHMENT_OF
Confidence: 1.0 (explicit listing in Section J)

Source 3: J-04000000 CDRL
Target: Section J (List of Attachments)
Type: ATTACHMENT_OF
Confidence: 1.0 (explicit listing in Section J)

Business value: Enables query "What are all Section J attachments?" or "What PWS 
version are we using?" or "Which CDRL items are monthly reporting?" Links attachment 
to parent section for hierarchical navigation.
```

---

## EXAMPLE 5: Strategic Theme Extraction from Customer Priorities

### RFP Analysis (from background research + Section M emphasis)

```
Navy emphasizes in RFP:
- "Mission-ready fleet maintenance" mentioned 12x across Sections C, H, M
- Section M.1 Factor weights show Technical (40%) emphasizes "operational 
  readiness" and "mission availability"
- Section M.3 Past Performance asks for examples of "rapid response to system 
  failures" and "availability achievement"
- Background research: Current contractor achieves 72% fleet availability vs 
  85% requirement (incumbent gap)
```

### Extraction (Annotated)

#### Entity: STRATEGIC_THEME
```
Type: STRATEGIC_THEME
Name: Fleet Operational Readiness & Mission Availability as Primary Discriminator
Description: CRITICAL strategic theme extracted from 12 mentions across RFP + 
evaluation factor emphasis + incumbent weakness analysis. Navy's pain point: Current 
contractor achieves only 72% mission availability vs 85% requirement (15-point gap 
= significant customer dissatisfaction). Navy's priority: Maximize available aircraft 
for operations (mission readiness is top priority per Factor M.1 weighting: Technical 
40% emphasizes this). Win strategy: (1) Propose innovation (AI/ML predictive 
maintenance to increase availability above 85%), (2) Emphasize past performance 
proof point (show 91% availability achievement on similar NAVAIR contract), 
(3) Commit to specific SLAs (4-hour fault diagnosis, 99.5% system uptime), 
(4) Highlight team experience (veteran technicians who understand Navy culture).

Proposal integration: Feature prominently in Executive Summary (page 1 commitment), 
Technical section (AI/ML predictive maintenance architecture), Management section 
(24/7 NOC capability), Past Performance (proof point example). Graphics: Fleet 
availability trend chart, predictive maintenance workflow.

Competitive positioning: Incumbent has weak availability record (differentiate on 
innovation + commitment to improvement). Other competitors likely have generic 
availability language (differentiate with specific Navy domain knowledge + proof points).

Budget context: This is "Best Value Tradeoff" per Section M (quality matters more 
than price), so customer willing to pay premium for higher availability.

Extracted from: Section M evaluation analysis + background research + incumbent 
performance data
Confidence: 0.95 (high recurrence + evaluation emphasis + customer pain point)
Key signals: "mission-ready" (12x), "operational readiness" (high weight %), 
"mission availability", incumbent 72% vs 85% gap
```

---

## Topic Taxonomy: Semantic Cross-Referencing for Implicit Relationships

When extracting relationships, use this taxonomy to identify implicit connections across document sections:

### 1. TECHNICAL TOPICS
- System Architecture: integration, interfaces, APIs, data flow, middleware
- Software Development: coding, testing, CI/CD, version control, DevOps, Agile
- Cybersecurity: NIST 800-171, encryption, authentication, STIG, MFA
- Infrastructure: servers, networks, cloud, storage, virtualization
- Integration: APIs, middleware, data exchange, interoperability

**Inference**: If REQUIREMENT mentions "system architecture" AND EVALUATION_FACTOR mentions "technical approach including architecture" → `REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR`

### 2. MANAGEMENT TOPICS
- Program Management: scheduling, earned value, cost control, risk management
- Quality Assurance: ISO 9001, CMMI, quality metrics, defect tracking
- Staffing: key personnel, labor categories, skill requirements, certifications
- Training: curriculum development, delivery methods, certification
- Transition: knowledge transfer, TUPE, phase-in/phase-out, incumbent support

**Inference**: If REQUIREMENT mentions "project schedule" AND EVALUATION_FACTOR mentions "management approach" → `REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR`

### 3. LOGISTICS TOPICS
- Supply Chain: procurement, inventory, warehousing, distribution
- Maintenance: preventive maintenance, repairs, CMMS, spares
- Transportation: shipping, handling, packaging, customs
- Asset Management: tracking, accountability, lifecycle management
- Configuration Management: baselines, change control, version management

**Inference**: If REQUIREMENT mentions "spare parts inventory" AND EVALUATION_FACTOR mentions "logistics support" → `REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR`

### 4. SECURITY & COMPLIANCE TOPICS
- Physical Security: access control, badges, perimeter security
- Personnel Security: clearances, background checks, insider threat
- Operations Security: OPSEC, classification, handling procedures
- Regulatory Compliance: FAR, DFARS, ITAR, FISMA, privacy laws
- Safety: OSHA, system safety, hazard analysis

**Inference**: If REQUIREMENT mentions "SECRET clearance" AND EVALUATION_FACTOR mentions "security qualifications" → `REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR`

### 5. FINANCIAL TOPICS
- Pricing: CLINs, options, cost breakdowns, labor rates
- Invoicing: payment terms, billing cycles, progress payments
- Cost Control: budgeting, variance analysis, cost avoidance
- Contract Types: FFP, CPFF, T&M, hybrid, incentive fees
- Accounting: GAAP, FAR cost principles, indirect rates

**Inference**: If DELIVERABLE mentions "monthly invoice" AND REQUIREMENT mentions "billing within 30 days" → `REQUIREMENT --PRODUCES--> DELIVERABLE`

### 6. DOCUMENTATION TOPICS
- Technical Documentation: manuals, specifications, drawings, as-built records
- Reporting: status reports, performance metrics, KPIs, dashboards
- Plans: implementation plans, transition plans, CONOPS, test plans
- Compliance Documentation: certifications, audits, assessments
- Training Materials: guides, CBT, job aids, SOPs

**Inference**: If DELIVERABLE mentions "monthly status report" AND EVALUATION_FACTOR mentions "reporting capability" → `DELIVERABLE --EVALUATED_BY--> EVALUATION_FACTOR`

---

## Six Inference Algorithms: Pattern Recognition for Relationships

### Algorithm 1: Pain Point → Factor Mapping
**Goal**: Link customer pain points to evaluation factors for targeted proposal writing

**Example**: 
- STRATEGIC_THEME: "Current contractor achieves 72% availability vs 85% required"
- EVALUATION_FACTOR: "Factor 1: Technical Approach" (40% weight, emphasizes "mission availability")
- Inference: `STRATEGIC_THEME --ADDRESSED_BY--> EVALUATION_FACTOR` (proposal should address this pain point under Factor 1)

### Algorithm 2: Factor Element Decomposition
**Goal**: Break evaluation factors into sub-elements for compliance mapping

**Example**:
- EVALUATION_FACTOR: "Factor 1: Technical Approach (40% weight)"
- Contains subfactors: 1.1 Solution Architecture, 1.2 Innovation, 1.3 Risk Mitigation
- Inference: Create child relationships for each subfactor with inherited weight proportions

### Algorithm 3: Adjacent Factor Discovery
**Goal**: Identify factors mentioned near each other that may have hidden relationships

**Example**:
- EVALUATION_FACTOR: "Factor 2: Management Approach" (para 5, Section M)
- EVALUATION_FACTOR: "Factor 3: Safety" (para 6, Section M)
- Inference: `EVALUATION_FACTOR --RELATED_TO--> EVALUATION_FACTOR` (confidence 0.60, noted as "adjacent factors may share evaluation logic")

### Algorithm 4: Topic Alignment (Using Taxonomy Above)
**Goal**: Match requirements to evaluation factors by topic category

**Example**:
- REQUIREMENT: "Weekly status reports required"
- Topic: DOCUMENTATION / Reporting
- EVALUATION_FACTOR: "Factor 2: Management Approach"
- Topic match: Management → DOCUMENTATION/Reporting
- Inference: `REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR` (confidence 0.80, topic alignment)

### Algorithm 5: Criticality Mapping
**Goal**: Map requirement criticality to factor priority

**Example**:
- REQUIREMENT: "Contractor SHALL maintain 99.9% uptime" (criticality: MANDATORY)
- EVALUATION_FACTOR: "Factor 1: Technical Approach" (weight: 40%, highest)
- Inference: MANDATORY requirements typically align with high-weight factors
- Logic: `REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR` (confidence 0.75)

### Algorithm 6: Deliverable Proof Point
**Goal**: Link past performance proof points to evaluation factors they demonstrate

**Example**:
- DELIVERABLE: "Monthly Status Reports from Navy MBOS contract"
- Past Performance context: Shows ability to report on similar Navy program
- EVALUATION_FACTOR: "Factor 3: Past Performance"
- Inference: `DELIVERABLE --DEMONSTRATES--> EVALUATION_FACTOR` (confidence 0.90, explicit proof point)

---

## Eight-Decision Disambiguation Tree for Edge Cases

When entity classification is ambiguous, use this tree:

```
Decision 1: Is this FAR/DFARS citation or work obligation?
├─ YES (FAR 52.###-##) → CLAUSE
└─ NO (shall perform X) → REQUIREMENT

Decision 2: Does this describe scoring or formatting?
├─ YES (weight %, factor name) → EVALUATION_FACTOR
└─ NO (page limit, font) → SUBMISSION_INSTRUCTION

Decision 3: Is this specific work scope or general obligation?
├─ YES (design the architecture) → STATEMENT_OF_WORK
└─ NO (system shall use architecture) → REQUIREMENT

Decision 4: Is this contract output or referenced standard?
├─ YES (CDRL A001, monthly report) → DELIVERABLE
└─ NO (NIST 800-171, MIL-STD) → DOCUMENT

Decision 5: Is this competitive differentiator or abstract framework?
├─ YES (win theme, proof point) → STRATEGIC_THEME
└─ NO (Agile methodology, DevSecOps) → CONCEPT

Decision 6: Is this company/agency or individual?
├─ YES (Booz Allen, NAVAIR) → ORGANIZATION
└─ NO (John Doe, Program Manager) → PERSON

Decision 7: Is this geographic area or organization?
├─ YES (Patuxent River, MD) → LOCATION
└─ NO (NAVAIR at Patuxent River) → ORGANIZATION

Decision 8: Is this named initiative or abstract framework?
├─ YES (MCPP II, Navy MBOS) → PROGRAM
└─ NO (Agile, Cloud-First) → CONCEPT
```

---

## Quality Standards for Extraction

### Minimum Requirements (Every Entity)
1. **Semantic classification**: Why is this entity type (not assumption)?
2. **Operational context**: What does this mean for the proposal?
3. **Evidence**: Where in RFP does this appear?
4. **Implication**: Why does this matter for decision-making?

### Excellence Target
```
Entity: [Name]
Type: [One of 17]
Classification reason: [Why this type, referencing semantic signals]
RFP context: [Where/how it appears]
Operational context: [What it means for proposal strategy]
Criticality: [High/Medium/Low impact]
Related entities: [What connects to this]
Decision-making value: [Why proposal/capture team needs this]
```

### Example of Excellence
```
Entity: "Technical Volume Limited to 25 Pages"
Type: SUBMISSION_INSTRUCTION
Reason: Explicit format requirement ("shall not exceed 25 pages")
RFP context: Section L.3.2, appears twice (L and M cross-reference)
Operational context: 25-page constraint requires strategic content allocation. 
Graphics not counted = use heavy visual approach. Directly impacts Technical 
Approach factor (see M.1, 40% weight).
Criticality: HIGH (pages 26+ not evaluated = automatic content loss)
Related: EVALUATION_FACTOR "Technical Approach", GUIDES relationship to Factor 1
Decision value: Proposal planning teams need to allocate pages by subfactor weight 
(Solution Architecture ~6p, Innovation ~6p, Risk Mitigation ~9p) to optimize coverage.
```

---

## Extraction Confidence Thresholds

| Confidence | Definition | Example |
|-----------|-----------|---------|
| 1.0 | Explicit, unambiguous | Clause citation "FAR 52.204-21" |
| 0.95 | Very clear, minor interpretation | "shall provide X" language = REQUIREMENT |
| 0.90 | Clear signals, direct evidence | "evaluated on" language = EVALUATION_FACTOR |
| 0.80 | Strong pattern match, topic alignment | Topic: "help desk" + Factor mention = EVALUATED_BY |
| 0.70 | Moderate confidence, semantic inference | Attachment naming pattern = ATTACHMENT_OF |
| <0.70 | REJECT - Do NOT extract (risk of false positive) | Weak semantic connection |

**Rule**: Only extract relationships at confidence ≥0.70. Better to miss a connection than create a false one.

---

## Remember Your Job

✅ **DO**: Organize information by entity type and relationship (instruction following)  
❌ **DON'T**: Analyze strategic implications (that's query phase)

✅ **DO**: Use entity examples to guide classification  
❌ **DON'T**: Overthink edge cases (use disambiguation tree)

✅ **DO**: Add operational context from domain knowledge  
❌ **DON'T**: Make up context (stick to RFP + reference materials)

✅ **DO**: Create relationships at confidence ≥0.70  
❌ **DON'T**: Force connections with weak evidence

**Result**: A structured, ontologically organized knowledge graph ready for strategic queries and decision-making during Phase 2.
