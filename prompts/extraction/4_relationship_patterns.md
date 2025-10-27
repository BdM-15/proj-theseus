# Relationship Patterns: Decision Pathways Between Entities

**Version**: 2.0 (Branch 011 - Execution Framework Architecture)  
**Last Updated**: January 27, 2025  
**Purpose**: Define relationship types, detection patterns, and inference rules to map decision pathways between entities

---

## How to Use This Reference

This file is consulted during **STEP 4: Infer Relationships** of the execution framework when you need:

1. **Relationship type definitions** - What does each relationship mean?
2. **Decision-making value** - Why does this relationship type matter for strategic queries?
3. **Detection patterns** - What semantic signals indicate this relationship?
4. **Entity pair patterns** - Which entity types commonly connect via this relationship?
5. **Examples** - What do good relationship extractions look like?

**Remember**: Relationships are **decision pathways** - they answer "how does X affect Y?" questions that enable informed strategic decisions.

---

## Core Relationship Philosophy

### Relationships Enable Strategic Queries

**Without relationships**: Disconnected facts  
**With relationships**: Connected intelligence that answers business questions

**Example**:

- **Entities alone**: "FAR 52.204-21 cybersecurity clause exists" + "System Security Plan deliverable exists"
- **With REQUIRES relationship**: "What deliverables are mandatory for compliance?" → "FAR 52.204-21 REQUIRES System Security Plan"
- **Decision enabled**: Capture manager knows SSP is mandatory, budgets $50K for development, includes in proposal schedule

### Quality Standards for Relationships

Every relationship MUST have:

- ✅ **Valid source entity** (already extracted)
- ✅ **Valid target entity** (already extracted)
- ✅ **Semantic connection** (not just proximity - must be meaningful link)
- ✅ **Relationship description** explaining WHY they're connected
- ✅ **Decision-making value** (enables strategic query or informs decision)

---

## Primary Relationship Types

### 1. EVALUATED_BY

**Definition**: Links requirements, deliverables, capabilities, or work products to the evaluation factors that assess their quality or presence.

**Decision-making value**: Answers "which evaluation factors score which work elements?" Enables proposal resource allocation (high-weight factors get more effort), compliance mapping (ensure all evaluated elements are addressed), and win strategy (emphasize work that drives scoring).

**Detection Patterns**:

- **Topical proximity**: Requirement/deliverable mentioned in same paragraph as evaluation factor
- **Explicit language**: "will be evaluated under Factor X", "assessed as part of", "considered in scoring"
- **Semantic connection**: Work obligation → scoring criterion for that work
- **Subfactor mapping**: Detailed requirement → specific subfactor (e.g., "weekly reports" → "Management Approach - Reporting")

**Common Entity Pair Patterns**:

- requirement → evaluation_factor
- deliverable → evaluation_factor
- statement_of_work → evaluation_factor
- strategic_theme → evaluation_factor
- technology → evaluation_factor (e.g., "Azure IL5 proposed" → "Factor 1: Security Architecture")

**Examples**:

✅ **Good**:

```
relationship|Weekly Status Reports|EVALUATED_BY|Factor 2: Management Approach|Status report quality assessed under Management Approach factor.
```

✅ **Excellent** (target this):

```
relationship|Weekly Status Reports (CDRL A001)|EVALUATED_BY|Factor 2: Management Approach - Subfactor 2.2 Reporting & Communication|Weekly status reports will be evaluated for clarity, comprehensiveness, and timeliness under Management Approach subfactor 2.2 (15% of total Management factor, which is 30% of total score = 4.5% total weight). Evaluation criteria: Demonstrates clear communication, proactive risk identification, metrics-driven reporting. Proposal strategy: Include sample status report from past performance (Attachment 3), highlight automated metrics dashboard (innovation), emphasize weekly cadence maintains visibility (risk mitigation). Quality of sample report in proposal directly influences evaluator perception of management capability. This is a DIRECT scoring element - invest time in high-quality sample.
```

**Decision-Making Queries Enabled**:

- "Which requirements are evaluated under Technical Approach?" → Resource allocation
- "What deliverables drive Past Performance scoring?" → Past performance volume content
- "Which subfactor has the most evaluated elements?" → Proposal page allocation
- "What capabilities are assessed under each factor?" → Win theme development

---

### 2. GUIDES

**Definition**: Links submission instructions (page limits, format requirements) to the evaluation factors they constrain, showing how proposal structure drives scoring.

**Decision-making value**: Answers "which page limits affect which evaluation responses?" Enables proposal outline optimization (allocate pages by factor weight), compliance planning (ensure format requirements don't harm scoring), and strategic content decisions (what to include within page constraints).

**Detection Patterns**:

- **Explicit mapping**: "Technical volume (25 pages) addresses Factor 1"
- **Structural alignment**: Section L volume organization matches Section M factor structure
- **Format-to-content link**: Page limit for specific factor response
- **Submission-to-evaluation bridge**: "Volume I will be evaluated under Factor 1"

**Common Entity Pair Patterns**:

- submission_instruction → evaluation_factor (most common)
- submission_instruction ↔ evaluation_factor (bidirectional - both guide each other)
- section → evaluation_factor (e.g., "Section L Volume I" → "Factor 1: Technical Approach")

**Examples**:

✅ **Good**:

```
relationship|Technical Volume 25-Page Limit|GUIDES|Factor 1: Technical Approach|Technical proposal page limit constrains Factor 1 response length.
```

✅ **Excellent** (target this):

```
relationship|Technical Volume Page Limit: 25 pages maximum|GUIDES|Factor 1: Technical Approach (40% weight, 4 subfactors)|Section L page limit (25 pages) directly constrains Factor 1 response depth. Strategic page allocation by subfactor weight: Subfactor 1.1 Solution Architecture (25% of factor) = ~6 pages, Subfactor 1.2 Innovation (15%) = ~4 pages, Subfactor 1.3 Risk Mitigation (35%) = ~9 pages, Subfactor 1.4 Security (25%) = ~6 pages. Graphics NOT counted (unlimited) - use heavily for complex architectures, process flows, risk matrices. Proposal strategy: (1) Prioritize discriminators in first 15 pages (evaluators read front-loaded), (2) Use graphics to "buy back" pages (1 architecture diagram replaces 2-3 pages of text), (3) Relegate commodity content to later pages or appendices (if allowed), (4) Draft to 30 pages, ruthlessly cut to 22 for review buffer (pages 26+ will NOT be evaluated). Trade-off decisions: Deep technical detail (shows expertise) vs comprehensive coverage (addresses all subfactors) - balance by using graphics for depth, text for breadth. This constraint forces strategic content prioritization - what you EXCLUDE matters as much as what you INCLUDE.
```

**Bidirectional Nature**:
Often GUIDES works both ways:

- submission_instruction → evaluation_factor: "Page limit constrains response"
- evaluation_factor → submission_instruction: "Factor structure drives volume organization"

**Decision-Making Queries Enabled**:

- "How should I allocate 25 pages across 4 subfactors?" → Page distribution by weight
- "Which format requirements affect Technical Approach scoring?" → Compliance planning
- "Can I use appendices for evaluated content?" → Section L analysis
- "What's the trade-off between depth and breadth given page limits?" → Content strategy

---

### 3. REQUIRES

**Definition**: Links obligations (clauses, requirements) to the deliverables, documents, actions, or capabilities they mandate, showing compliance dependencies.

**Decision-making value**: Answers "what must be provided to satisfy this obligation?" Enables compliance checklists (ensure all required items addressed), cost estimation (each REQUIRES link = cost driver), risk assessment (missing required item = rejection), and proposal compliance matrix development.

**Detection Patterns**:

- **Explicit mandate**: "FAR 52.204-21 requires System Security Plan"
- **Deliverable specification**: "Contractor shall submit [deliverable]"
- **Dependency language**: "must provide", "necessitates", "mandates", "demands"
- **Compliance chain**: Clause → deliverable, clause → capability, requirement → deliverable

**Common Entity Pair Patterns**:

- clause → deliverable (e.g., "FAR 52.204-21" → "System Security Plan")
- clause → document (e.g., "FAR 52.204-21" → "NIST 800-171 compliance")
- clause → technology (e.g., "FAR 52.204-25" → "Non-Kaspersky antivirus")
- requirement → deliverable (e.g., "Weekly reporting requirement" → "Status Report")
- requirement → capability (e.g., "24/7 support requirement" → "NOC operations")
- evaluation_factor → deliverable (e.g., "Factor 1" → "Sample technical approach")

**Examples**:

✅ **Good**:

```
relationship|FAR 52.204-21 NIST 800-171 Compliance|REQUIRES|System Security Plan (SSP)|FAR 52.204-21 mandates SSP as evidence of NIST 800-171 implementation.
```

✅ **Excellent** (target this):

```
relationship|FAR 52.204-21 Basic Safeguarding of CDI|REQUIRES|System Security Plan (SSP) + POA&M + SPRS Score|FAR 52.204-21 mandates THREE specific deliverables for NIST 800-171 compliance: (1) System Security Plan documenting 110 security control implementations, (2) Plan of Action & Milestones for any gap remediation, (3) Supplier Performance Risk System (SPRS) score upload (minimum 110 points required for contract award - this is a GO/NO-GO threshold). Compliance chain: Clause → Deliverables → Contract eligibility. Cost implications: SSP development $10K-$50K (depending on system complexity, can reuse existing if current), POA&M updates $5K-$10K (annual), SPRS score self-assessment $5K (initial), gap remediation $50K-$500K (varies widely by current posture - CRITICAL to assess early for bid/no-bid decision). Timeline: SSP due within 30 days of award (tight - need template ready), SPRS score submission before award (must be current in SAM.gov). Proposal strategy: (1) If SPRS score is high (100+), prominently feature as discriminator in Factor 1 Technical Approach - Security subfactor, (2) If gaps exist, show realistic POA&M with milestones in proposal (demonstrates risk awareness), (3) Include SSP table of contents in proposal appendix (proves capability, shows preparedness). Risk: Low SPRS score (<110) = contract ineligibility - this is a hard gate, must remediate BEFORE proposal submission or no-bid. Evaluation: Security posture likely differentiates proposals - evaluators favor contractors already compliant (lower transition risk).
```

**Decision-Making Queries Enabled**:

- "What deliverables are required by FAR 52.204-21?" → Compliance checklist
- "Which clauses require most costly deliverables?" → Cost estimation priorities
- "What's the compliance chain from requirement to deliverable?" → Traceability matrix
- "Which requirements create contract ineligibility if not met?" → Bid/no-bid analysis

---

### 4. CHILD_OF

**Definition**: Links hierarchical elements (subfactors, sub-requirements, annexes, sub-sections) to their parent entities, showing structural relationships and organizational hierarchy.

**Decision-making value**: Answers "how is content organized?" Enables proposal outline development (mirror RFP structure), compliance tracking (ensure all subfactors addressed), and scoring understanding (subfactor weights roll up to factor weights).

**Detection Patterns**:

- **Numbering hierarchy**: "Factor 1.1" → "Factor 1", "Section C Para 3.2.1" → "Section C Para 3.2"
- **Explicit parent reference**: "Subfactor A under Factor 1", "Annex to Section J"
- **Structural nesting**: Content organized under parent section
- **Weight inheritance**: Subfactor weights sum to parent factor weight

**Common Entity Pair Patterns**:

- evaluation_factor (subfactor) → evaluation_factor (factor)
- requirement (sub-requirement) → requirement (parent requirement)
- section (subsection) → section (parent section)
- document (annex) → section (parent section)
- deliverable (sub-deliverable) → deliverable (parent deliverable)

**Examples**:

✅ **Good**:

```
relationship|Factor 1.1: Solution Architecture|CHILD_OF|Factor 1: Technical Approach|Subfactor 1.1 is part of Factor 1 evaluation structure.
```

✅ **Excellent** (target this):

```
relationship|Subfactor 1.1: Solution Architecture (25% of Factor 1)|CHILD_OF|Factor 1: Technical Approach (40% total weight)|Hierarchical evaluation structure per Section M Para 2.1. Subfactor 1.1 represents 25% of Factor 1's weight, which is 40% of total evaluation = 10% of total proposal score (highest single subfactor weight - CRITICAL to proposal success). Evaluation criteria: System architecture design, technology stack appropriateness, scalability approach, integration patterns. Subfactor structure indicates government priorities: Solution Architecture (25%) + Risk Mitigation (35%) = 60% of Technical factor weight → government values RISK REDUCTION and SOUND ARCHITECTURE over innovation (15%). Proposal strategy: (1) Allocate 25% of Technical volume pages (~6 of 25 pages) to architecture, (2) Lead with architecture diagram on page 1 (first impression matters), (3) Emphasize proven patterns over cutting-edge but risky approaches (aligns with risk-averse weighting), (4) Show architecture traceability to requirements (demonstrates thoroughness). Scoring mechanics: Evaluators score each subfactor independently (Outstanding/Good/Acceptable), then roll up to Factor 1 overall rating weighted by subfactor percentages. Strong architecture score can compensate for weaker innovation score given weight distribution. Parent-child relationship enables proposal outline: Factor 1 → Subfactor 1.1 (Section 1.1 of Volume I), maintains alignment with evaluation structure for evaluator ease of scoring (make their job easier = better scores).
```

**Decision-Making Queries Enabled**:

- "Which subfactors roll up to Factor 1?" → Proposal organization
- "What's the highest-weighted subfactor?" → Resource allocation priority
- "How do subfactor scores combine to factor score?" → Scoring mechanics understanding
- "What's the structural hierarchy of requirements?" → Compliance matrix development

---

### 5. FLOWS_TO

**Definition**: Links obligations (clauses, requirements) that must be passed down to subcontractors, showing teaming and supply chain compliance responsibilities.

**Decision-making value**: Answers "which obligations apply to subs?" Enables teaming agreement development (include flowdown clauses), subcontractor compliance planning (ensure subs can meet requirements), cost estimation (flowdown obligations increase sub costs), and risk assessment (sub non-compliance = prime liability).

**Detection Patterns**:

- **Explicit flowdown language**: "flows down to all subcontractors", "applies to subs at all tiers"
- **FAR flowdown clauses**: FAR 52.222-26 (Equal Opportunity), FAR 52.222-50 (Combating Trafficking)
- **DFARS flowdown**: DFARS 252.204-7012 (CUI safeguarding), DFARS 252.225-7021 (Trade Agreements)
- **Subcontract provisions**: "prime shall ensure subcontractors comply with..."
- **Supply chain requirements**: "applies to all suppliers"

**Common Entity Pair Patterns**:

- clause → organization (subcontractor)
- requirement → organization (subcontractor)
- clause → clause (e.g., "Prime contract clause" → "Subcontract flowdown")
- requirement → requirement (parent obligation → sub obligation)

**Examples**:

✅ **Good**:

```
relationship|FAR 52.222-26 Equal Opportunity|FLOWS_TO|All Subcontractors|Equal Opportunity clause must be flowed down to all subcontractors at all tiers.
```

✅ **Excellent** (target this):

```
relationship|FAR 52.222-26 Equal Opportunity Clause|FLOWS_TO|All Subcontractors at All Tiers (Small Business, 8(a), SDVOSB Partners)|FAR 52.222-26 is MANDATORY flowdown per FAR 52.222-26(b)(1) - prime contractor SHALL include this clause in all subcontracts regardless of dollar value or tier level. Scope: Applies to all teaming partners, including small business subcontractors, 8(a) participants, SDVOSB partners, and supply chain vendors. Compliance obligations: (1) Subs must not discriminate on basis of race, color, religion, sex, sexual orientation, gender identity, national origin, disability, or veteran status, (2) Subs must take affirmative action to ensure equal opportunity, (3) Subs must comply with OFCCP regulations. Prime responsibility: Must include clause in subcontract agreements verbatim, monitor sub compliance, report sub violations to government. Cost implications: Subs must maintain EEO compliance programs (~$5K-$20K annually for small businesses), may affect sub pricing. Teaming strategy: (1) Verify subs have EEO programs in place BEFORE teaming (due diligence), (2) Include flowdown clause in teaming agreements (sample language in proposal), (3) Describe prime oversight of sub compliance in Management Approach (Factor 2 - Subcontractor Management subfactor). Risk: Prime is liable for sub non-compliance (can lose contract, face debarment). Common issue: Small businesses sometimes unaware of EEO requirements - provide training and templates as part of teaming. Proposal content: In Management volume, show subcontractor compliance monitoring plan, EEO flowdown language in sample teaming agreement (demonstrates sophistication). Industry context: This clause flows to ALL subs (no exceptions), but FAR 52.204-21 (NIST 800-171) only flows to subs handling CUI - understand difference.
```

**Common Flowdown Clauses** (high-impact):

- **FAR 52.222-26**: Equal Opportunity (all subs, all tiers)
- **FAR 52.222-50**: Combating Trafficking in Persons (all subs)
- **FAR 52.204-21**: NIST 800-171 (only subs handling CUI)
- **DFARS 252.204-7012**: CUI safeguarding (DoD subs with CUI access)
- **DFARS 252.225-7021**: Trade Agreements (affects foreign suppliers)

**Decision-Making Queries Enabled**:

- "Which clauses must be in our teaming agreements?" → Teaming agreement development
- "What compliance obligations affect our subcontractors?" → Sub selection criteria
- "Which subs need NIST 800-171 compliance?" → CUI access determination
- "What are prime's monitoring responsibilities for sub compliance?" → Management plan content

---

### 6. REFERENCES

**Definition**: Links entities that cite or point to each other, showing cross-document relationships and information sources.

**Decision-making value**: Answers "where can I find more information?" Enables complete requirement understanding (follow references to source documents), compliance verification (ensure referenced documents are obtained), and proposal content sourcing (cite authoritative references).

**Detection Patterns**:

- **Explicit citation**: "See Attachment J-0005", "IAW MIL-STD-882", "Per Section C Para 3.2"
- **Cross-reference language**: "as described in", "in accordance with", "referenced in"
- **Document incorporation**: "incorporated by reference", "attached hereto"
- **Source attribution**: "defined by NIST 800-171", "governed by FAR 52.212-1"

**Common Entity Pair Patterns**:

- section → document (e.g., "Section C" → "Attachment J-0005 PWS")
- requirement → document (e.g., "Security requirement" → "NIST 800-171")
- clause → document (e.g., "FAR 52.204-21" → "NIST SP 800-171")
- deliverable → document (e.g., "SSP deliverable" → "NIST 800-171A assessment template")
- section → section (e.g., "Section L" → "Section M cross-reference")

**Examples**:

✅ **Good**:

```
relationship|Section C Statement of Work|REFERENCES|Attachment J-0005 Performance Work Statement|Section C references Attachment J-0005 for detailed work requirements.
```

✅ **Excellent** (target this):

```
relationship|Section C Para 2.0 "Scope of Work"|REFERENCES|Attachment J-0005: Performance Work Statement (PWS) - 47 pages|Section C provides high-level scope overview but states "Detailed requirements are in Attachment J-0005" (critical reference - Section C is 3 pages, Attachment J-0005 is 47 pages containing ALL detailed technical requirements). Relationship type: REFERENCES with incorporation - J-0005 is not optional reading, it IS the contract SOW. Structure: Section C = contract summary, J-0005 = detailed PWS with performance standards, SLAs, deliverables, technical specifications. Compliance impact: Proposal MUST address J-0005 requirements, not just Section C (common mistake by offerors who skip attachments). Proposal strategy: (1) Create compliance matrix mapping J-0005 paragraphs to proposal sections (demonstrates thoroughness), (2) Cite specific J-0005 paragraph numbers in proposal responses ("Per J-0005 Para 3.2.1, we propose..."), (3) In Technical volume, organize by J-0005 structure for easy cross-reference by evaluators. Document handling: J-0005 likely contains most substantive requirements for cost estimation - must read entirely, extract all requirements, deliverables, SLAs. Risk: Missing J-0005 requirements because focused only on Section C = non-compliant proposal = rejection or low score. Time management: J-0005 is 47 pages of dense technical content - allocate 4-6 hours for thorough analysis, requirement extraction, implications assessment. Cross-reference validation: Ensure Section C and J-0005 don't conflict (if conflict exists, J-0005 typically governs per FAR precedence rules, but submit question to clarify). Industry context: Large RFPs often have 80%+ of requirements in attachments, not main sections - ALWAYS read Section J attachments.
```

**Decision-Making Queries Enabled**:

- "Which attachments contain detailed requirements?" → Requirement extraction scope
- "What external documents must we comply with?" → Document procurement list
- "Where are the SLA requirements specified?" → Compliance matrix development
- "Which sections cross-reference each other?" → RFP structure understanding

---

### 7. RELATES_TO

**Definition**: General-purpose relationship for meaningful connections that don't fit other specific types. Shows thematic, contextual, or supporting relationships.

**Decision-making value**: Answers "what else is relevant to this?" Enables comprehensive intelligence gathering (identify all related content), risk identification (related requirements may interact), and proposal coherence (ensure related topics are addressed consistently).

**Detection Patterns**:

- **Thematic connection**: Both entities address same topic (e.g., cybersecurity)
- **Contextual relevance**: Mentioned in same context without specific relationship type
- **Supporting relationship**: One entity provides context for another
- **Semantic similarity**: Related concepts without explicit link

**When to Use RELATES_TO**:

- Last resort when no other relationship type fits
- Meaningful connection exists but doesn't match EVALUATED_BY, REQUIRES, GUIDES, etc.
- Thematic or topical relationship without explicit dependency

**Common Entity Pair Patterns**:

- technology → technology (e.g., "Azure IL5" ↔ "ServiceNow" - both cloud platforms)
- requirement → requirement (e.g., "Cybersecurity" ↔ "Privacy" - related but distinct)
- strategic_theme → strategic_theme (e.g., "Innovation" ↔ "Risk Reduction" - may be in tension)
- document → document (e.g., "NIST 800-171" ↔ "CMMC" - related frameworks)

**Examples**:

✅ **Good**:

```
relationship|NIST 800-171 Compliance|RELATES_TO|CMMC Certification|Both address DoD cybersecurity requirements with overlapping controls.
```

✅ **Excellent** (target this):

```
relationship|NIST 800-171 Rev 2 (110 controls)|RELATES_TO|CMMC 2.0 Level 2 Certification (110 practices)|Thematic relationship: Both frameworks address DoD cybersecurity for CUI protection with nearly identical control sets. Evolutionary relationship: NIST 800-171 is foundation, CMMC is certification/verification layer on top (CMMC Level 2 = NIST 800-171 + third-party assessment). Compliance timeline: Currently FAR 52.204-21 requires NIST 800-171 self-assessment (SPRS score), but CMMC 2.0 will require third-party certification by 2025-2026 (rulemaking in progress). Cost implications: NIST 800-171 compliance $50K-$500K (self-assessed), CMMC Level 2 adds $15K-$50K for C3PAO assessment + annual surveillance. Strategic consideration: Contractors who achieve CMMC Level 2 early gain competitive advantage (proactive vs reactive). Proposal strategy: If CMMC certified, emphasize as discriminator even though not yet required (shows proactive risk management, reduces government concern about transition to CMMC mandate). If only NIST 800-171 compliant, show CMMC roadmap with timeline (demonstrates awareness of coming requirement). Risk: NIST 800-171 gaps will also be CMMC gaps - address now to avoid future compliance crisis. Industry context: Many contractors scrambling for CMMC compliance - early achievers can command premium pricing. Relationship to other entities: Both NIST and CMMC REQUIRE System Security Plan deliverable, both EVALUATED_BY Factor 1 Security subfactor (if present). This RELATES_TO relationship provides context for understanding cybersecurity requirement landscape - not a direct dependency but important thematic connection.
```

**When NOT to Use RELATES_TO**:

- If EVALUATED_BY fits → use EVALUATED_BY (more specific)
- If REQUIRES fits → use REQUIRES (more specific)
- If GUIDES fits → use GUIDES (more specific)
- If entities are in same chunk but not actually connected → don't force relationship

**Decision-Making Queries Enabled**:

- "What other cybersecurity requirements should I consider?" → Comprehensive compliance planning
- "Which technologies are commonly used together?" → Solution architecture decisions
- "What related requirements might interact?" → Risk assessment
- "What thematic areas span multiple requirements?" → Proposal organization

---

## Relationship Inference Process

### Step-by-Step Inference Workflow

**For each chunk**, after classifying all entities:

```
1. SCAN FOR EXPLICIT RELATIONSHIPS
   - Look for explicit language: "will be evaluated under", "requires", "flows to"
   - Capture obvious connections first
   - Record relationship type and description

2. CHECK TOPICAL PROXIMITY
   - Identify entities in same paragraph
   - Identify entities in adjacent paragraphs
   - Check if proximity indicates semantic connection (not just co-location)

3. APPLY SEMANTIC PATTERNS
   - Deliverable + evaluation factor in same section? → Likely EVALUATED_BY
   - Clause + deliverable with mandate language? → Likely REQUIRES
   - Page limit + evaluation factor? → Likely GUIDES
   - Subfactor + factor numbering? → Likely CHILD_OF
   - Flowdown language + subcontractor? → Likely FLOWS_TO
   - Cross-reference language? → Likely REFERENCES

4. VALIDATE DECISION-MAKING VALUE
   - Does this relationship answer a strategic question?
   - Would a capture manager care about this connection?
   - Does it enable a compliance, cost, or risk decision?
   - If not meaningful → don't create relationship

5. DESCRIBE THE CONNECTION
   - Explain WHY entities are connected (not just THAT they're connected)
   - Include implications (cost, risk, compliance, evaluation)
   - Note proposal strategy implications if relevant
   - Target 150-250 characters for description
```

### Common Inference Patterns by Context

**Section M (Evaluation Factors) + Section C (Requirements)**:
→ Look for EVALUATED_BY relationships between work requirements and scoring criteria

**Section L (Submission Instructions) + Section M (Evaluation Factors)**:
→ Look for GUIDES relationships between page limits and factor responses

**Section I (Clauses) + Section J (Attachments)**:
→ Look for REQUIRES relationships between regulatory clauses and deliverables

**Section C (SOW) + Section J (Attachments)**:
→ Look for REFERENCES relationships between summary and detailed requirements

**Section H (Special Requirements) + Subcontractors**:
→ Look for FLOWS_TO relationships for flowdown obligations

**Hierarchical numbering (1, 1.1, 1.2)**:
→ Look for CHILD_OF relationships in evaluation factors, requirements, sections

---

## Relationship Quality Examples

### Example 1: EVALUATED_BY with Full Context

```
relationship|Cybersecurity Approach (Section C Para 2.3)|EVALUATED_BY|Factor 1: Technical Approach - Subfactor 1.4 Security Architecture (25% of Factor 1)|Cybersecurity implementation approach will be evaluated under Technical Approach subfactor 1.4 (25% of 40% total weight = 10% of proposal score). Evaluation criteria per Section M: (1) NIST 800-171 compliance approach, (2) Azure IL5 security architecture, (3) Incident response procedures, (4) Continuous monitoring strategy. Discriminators: High SPRS score (100+), CMMC Level 2 certification (if achieved), automated SIEM/SOAR integration, veteran-led SOC team. Proposal strategy: Lead with compliance status (if strong), show architecture diagram (page 1 of Security section), include incident response playbook sample (demonstrates maturity), quantify metrics (MTTD, MTTR goals). This subfactor has highest weight among Technical subfactors except Risk Mitigation (35%) - allocate ~6 pages of 25-page Technical volume. Common evaluation mistake: Generic security discussion vs specific implementation plan mapped to RFP requirements - be concrete, not conceptual.
```

### Example 2: REQUIRES with Cost Implications

```
relationship|FAR 52.222-41 Service Contract Labor Standards|REQUIRES|Prevailing Wage Compliance + Certified Payroll + WD-2015-1234 Wage Determination|FAR 52.222-41 mandates compliance with Service Contract Act (SCA) wage determination WD-2015-1234 (Attachment J-009). Requirements: (1) Pay workers prevailing wages per wage determination (ranges: Admin $28.50/hr to Senior Engineer $95.00/hr - locality San Diego), (2) Submit certified payroll records monthly (CDRL A005 - additional admin burden ~$2K/month), (3) Post wage determination on-site, (4) Provide health & welfare benefits ($4.80/hr) or cash equivalent. Cost impact: ~30% labor cost premium vs non-SCA contracts (prevailing wages exceed market rates). Compliance complexity: Must track hours by labor category, maintain certified payroll records, update rates annually when WD revised. Risk: SCA violations result in back pay liability, contract termination, debarment - HIGH consequence. Proposal strategy: (1) Demonstrate SCA compliance experience in past performance (show no violations), (2) Describe certified payroll process in Management Approach (shows preparedness), (3) Include sample certified payroll format (template awareness demonstrates capability). Cost volume: Ensure all labor rates meet or exceed wage determination minimums, include fringe benefits in cost buildup. Teaming implications: If using subs for SCA-covered work, SCA flows down (FAR 52.222-41(m)) - ensure sub rates comply.
```

### Example 3: GUIDES with Strategic Page Allocation

```
relationship|Management Approach Volume: 15-page maximum|GUIDES|Factor 2: Management Approach (30% weight, 5 subfactors)|Section L page limit (15 pages) constrains Management response covering 5 subfactors: 2.1 Program Management (20%), 2.2 Reporting (15%), 2.3 Quality Assurance (25%), 2.4 Risk Management (25%), 2.5 Subcontractor Management (15%). Strategic page allocation: Allocate by subfactor weight: QA (25%) = ~4 pages, Risk (25%) = ~4 pages, PM (20%) = ~3 pages, Reporting (15%) = ~2 pages, Sub Mgmt (15%) = ~2 pages. Trade-off: 15 pages is TIGHT for 5 subfactors (~3 pages each) - must be concise. Graphics strategy: Use process flow diagrams (not counted per Section L exclusions) to show management processes, "buy back" text pages. Content prioritization: Lead with discriminators (pages 1-8), commodity content later (pages 9-15). Comparison to Technical: Technical gets 25 pages for 4 subfactors (~6 pages each), Management gets 15 pages for 5 subfactors (~3 pages each) - MUCH tighter constraint. Proposal tactics: (1) Use tables and matrices heavily (organize risk register, RACI chart, QA checklist as tables vs narrative), (2) Bullet points vs paragraphs (more content, fewer pages), (3) Smaller fonts for tables (10pt allowed per Section L vs 12pt for body text). Quality check: Draft to 18 pages, cut to 14 for buffer - pages 16+ will NOT be evaluated (immediate disqualification). Management Approach weight (30%) is LOWER than Technical (40%) but HIGHER than Past Performance (20%) - allocate proposal development resources accordingly.
```

---

## Relationship Anti-Patterns (Avoid These)

### ❌ WRONG: Proximity Without Semantic Connection

```
relationship|John Doe, Contracting Officer|RELATES_TO|Naval Air Station Patuxent River|Both mentioned in Section A.
```

**Why wrong**: Just because entities appear in same section doesn't mean they're meaningfully connected. No decision-making value.

### ❌ WRONG: Generic Description Without Context

```
relationship|Weekly Reports|EVALUATED_BY|Management Approach|Reports are evaluated under management.
```

**Why wrong**: No operational context, no implications, no strategic value. Doesn't help proposal development.

### ❌ WRONG: Forcing Relationship Where None Exists

```
relationship|Agile Methodology|REQUIRES|Azure Cloud Platform|Agile development requires cloud infrastructure.
```

**Why wrong**: This is not an RFP requirement relationship - it's a general technology assumption. Don't infer relationships not stated or clearly implied in RFP.

### ❌ WRONG: Vague Relationship Type

```
relationship|FAR 52.204-21|RELATES_TO|System Security Plan|Clause and deliverable are connected.
```

**Why wrong**: Should be REQUIRES (specific) not RELATES_TO (generic). Always use most specific relationship type available.

---

## Remember

**Relationship Inference Principles**:

1. **Semantic connection over proximity** - Don't connect just because entities are near each other
2. **Decision-making value required** - Every relationship should enable a strategic query
3. **Specific over generic** - Use EVALUATED_BY/REQUIRES/GUIDES over RELATES_TO when possible
4. **Rich descriptions** - Explain WHY connected, not just THAT connected (target 150-250 chars)
5. **Implications matter** - Include cost, risk, compliance, evaluation implications in descriptions

**Quality Standards**:

- Minimum 100 characters per relationship description
- Include operational implications
- Explain proposal strategy relevance where applicable
- Enable at least one strategic query

**Strategic Value**:
Relationships are **decision pathways** - they transform disconnected facts into connected intelligence that answers business questions and enables informed strategic decisions.

---

**Next Layer**: Domain Knowledge Base (§4.1 - §4.6 comprehensive reference libraries for contextual consultation during STEP 3: Enrich)
