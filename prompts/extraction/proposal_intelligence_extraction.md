# Proposal Intelligence Extraction Patterns

**Purpose**: Extract win themes, discriminators, compliance patterns, and competitive intelligence  
**Philosophy**: Recognize proposal-critical intelligence regardless of RFP terminology  
**Usage**: Loaded during RAG-Anything extraction to enrich strategic_theme and competitive intelligence entities  
**Last Updated**: January 26, 2025 (Branch 011 - Option A Lean Extraction)

---

## Extraction Philosophy

When extracting proposal intelligence, **recognize strategic intent** underlying RFP language:

```
❌ BASIC: entity|Cost-effectiveness is important|strategic_theme|Mentions cost-effectiveness

✅ ENHANCED: entity|Budget Constraints - Maximize Value|strategic_theme|"cost-effectiveness" language signals budget sensitivity (likely civilian agency or constrained environment). Win theme opportunity: demonstrate cost savings, process efficiency, lifecycle cost reduction. FAB framework: Feature (automated processes) → Advantage (reduced labor hours) → Benefit (20% cost savings vs manual approach). Discriminator: quantified cost reduction evidence from past performance.
```

**Key Pattern**: LLM should infer proposal strategy opportunities from RFP priorities and language patterns

---

## Section 1: Win Theme Detection (FAB Framework)

> **REMEMBER**: Win themes are proposal strategy constructs, NOT explicitly stated in RFPs. Extract signals that INDICATE win theme opportunities.

### FAB Framework Pattern Recognition

**Feature-Advantage-Benefit structure**:

- **Feature**: What you offer (capability, process, tool, methodology)
- **Advantage**: Why that feature is superior (competitive differentiator)
- **Benefit**: What customer gains (mission impact, cost savings, risk reduction)

**RFP signals → Win theme extraction**:

**Signal**: "mission-critical 24/7 availability required"  
**Win theme opportunity**:

```
entity|High Availability Win Theme|strategic_theme|Mission-critical 24/7 availability requirement signals win theme opportunity. FAB: Feature (99.99% uptime SLA with automated failover) → Advantage (exceeds 99.9% RFP requirement) → Benefit (minimal mission disruption, only 52 minutes downtime/year vs 8.76 hours at minimum). Discriminator: past performance evidence of uptime achievement (CPARS documentation).
```

**Signal**: "incumbent contractor performance issues noted"  
**Win theme opportunity**:

```
entity|Transition Excellence Win Theme|strategic_theme|Performance issues language signals incumbent weakness, transition risk concern. FAB: Feature (dedicated transition team, 90-day knowledge transfer) → Advantage (minimal disruption vs typical 30-day transitions) → Benefit (zero service gaps, continuity of operations). Discriminator: successful transition experience from past performance (similar size/complexity contract takeover).
```

**Signal**: "innovation encouraged", "new approaches welcomed"  
**Win theme opportunity**:

```
entity|Innovation Win Theme|strategic_theme|Innovation language signals customer openness to non-traditional approaches. FAB: Feature (AI-powered automation for routine tasks) → Advantage (faster response time, reduced human error) → Benefit (30% efficiency gain, freed staff for high-value work). Discriminator: proven innovation deployment (past performance with similar technology).
```

---

## Section 2: Discriminator Extraction

**Discriminators** = Competitive differentiators that distinguish your proposal from competitors

### Pattern 1: Technical Discriminators

**Detection signals** in RFP:

- "preferred but not required" → Optional capabilities that few competitors may offer
- "state-of-the-art", "cutting-edge" → Advanced technical capability emphasis
- Specific tool/technology mentions → Proprietary or niche expertise signals

**Extraction pattern**:

```
entity|Cloud-Native Architecture Discriminator|strategic_theme|RFP mentions "cloud migration planned within 2 years" (not mandatory). Discriminator opportunity: cloud-native solution from day 1 (vs lift-and-shift approach). Advantage: zero future migration cost/risk. Benefit: faster time-to-market for new features, inherent scalability. Evidence needed: past performance with cloud-native implementations.
```

### Pattern 2: Past Performance Discriminators

**Detection signals**:

- "relevant experience" with specific customer types → Exact-match experience
- Contract size/complexity thresholds → Demonstrated capability at scale
- Specific technical domains → Deep expertise in niche areas

**Extraction pattern**:

```
entity|Navy-Specific Experience Discriminator|strategic_theme|RFP emphasizes "experience with Navy customers and Navy-unique systems (NMCI, NGEN)". Discriminator opportunity: direct Navy contract performance (vs generic DoD). Advantage: understanding Navy cybersecurity constraints, approval processes, unique systems. Benefit: faster ramp-up, reduced learning curve risk. Evidence: Navy past performance references with CPARS ratings.
```

### Pattern 3: Management Discriminators

**Detection signals**:

- Security clearance requirements → Cleared workforce availability
- Geographic requirements → Local presence
- Key personnel qualifications → Specific expertise availability

**Extraction pattern**:

```
entity|Pre-Cleared Workforce Discriminator|strategic_theme|100% of staff requires TS/SCI clearances, no "will obtain" acceptable. Discriminator opportunity: 95% of proposed staff already cleared (vs competitors likely proposing to-be-cleared personnel). Advantage: day-one operational capability, zero clearance delay risk. Benefit: immediate mission support, no government wait for clearance processing. Evidence: current cleared headcount data.
```

---

## Section 3: Compliance Matrix Pattern Recognition

**Compliance matrices** track requirement → proposal response mapping. Extract requirements that MUST appear in matrix:

### MANDATORY Requirement Detection

**Criticality signals** (extract as high-priority requirements):

- "shall", "must", "is required to" → Mandatory obligations
- "failure to comply will result in rejection" → Go/no-go criteria
- "non-negotiable" → Absolute requirements

**Extraction pattern with compliance tracking**:

```
entity|FAR 52.204-21 NIST 800-171 Compliance|requirement|MANDATORY cybersecurity requirement (FAR 52.204-21 Basic Safeguarding). Contractor SHALL implement NIST 800-171 security controls for CUI. Non-compliance = contract ineligibility. Compliance evidence: SSP (System Security Plan), POAM (Plan of Action & Milestones), SPRS score (min 110).

relationship|NIST 800-171 Compliance|MUST_BE_IN|Compliance Matrix|traceability|Mandatory requirement requires explicit compliance statement in proposal
```

### SHOULD Requirement Detection

**Guidance signals** (extract as best-practice requirements):

- "should", "expected to", "normally would" → Strong preferences but not absolute
- "desirable" → Competitive advantages
- "preferred approach" → Evaluation scoring factors

**Extraction pattern**:

```
entity|Agile Development Methodology|requirement|SHOULD use Agile methodology (not mandatory, but RFP states "preferred approach"). Compliance enhances technical evaluation scoring. Evidence: Agile process descriptions, sprint planning examples, past performance with Agile delivery.

relationship|Agile Methodology|EVALUATED_BY|Factor 1: Technical Approach|scoring_factor|Should-level requirement contributes to technical factor scoring
```

### MAY Requirement Detection

**Optional signals** (extract as value-add opportunities):

- "may", "can", "optionally" → Contractor discretion
- "if applicable" → Conditional requirements
- "additional services may include" → Expansion opportunities

**Extraction pattern**:

```
entity|Optional Training Services|requirement|MAY provide additional training beyond base requirement (optional CLIN). Opportunity for value-add differentiation. If included: demonstrate cost-effectiveness, training methodology, certification programs.

relationship|Optional Training|CREATES|Competitive Advantage|strategy|Going beyond minimum shows commitment, may influence best-value tradeoff
```

---

## Section 4: Risk Scoring Patterns

**Extract risk language** from RFP to inform proposal risk mitigation strategy:

### High-Risk Indicators

**Detection signals**:

- "critical mission", "mission-essential" → Failure = mission impact
- "no single point of failure acceptable" → Redundancy required
- "continuous operations during transition" → Zero-downtime requirement
- "incumbent performance deficiencies" → Heightened scrutiny

**Extraction pattern**:

```
entity|Mission-Critical Uptime Risk|strategic_theme|"mission-essential 24/7 operations" language indicates HIGH-RISK environment. Government concerns: service interruptions = mission failure. Proposal strategy: emphasize redundancy (dual infrastructure, failover automation), past performance with zero unplanned outages, robust incident response (15-minute MTTR). Risk mitigation: detailed DR/COOP plan, SLA penalties demonstrate commitment.
```

### Transition Risk Indicators

**Detection signals**:

- "current contractor transition out" → Knowledge transfer concerns
- "minimize disruption during transition" → Continuity requirements
- "incumbent will provide limited support" → Potential knowledge gaps

**Extraction pattern**:

```
entity|Incumbent Transition Risk|strategic_theme|Limited incumbent cooperation signals transition risk (knowledge gaps, system documentation deficiencies). Proposal strategy: extended transition period (90 days vs minimum 30), reverse shadowing approach, independent system discovery/documentation, parallel operations overlap. Evidence: past performance with successful transitions from uncooperative incumbents.
```

### Security/Clearance Risk Indicators

**Detection signals**:

- "all personnel require TS/SCI" → Clearance availability risk
- "facility must be SCIF-certified" → Physical security requirements
- "customer site access requires SAP approval" → Access delay risk

**Extraction pattern**:

```
entity|Clearance Availability Risk|strategic_theme|100% TS/SCI requirement = significant risk if proposing to-be-cleared personnel (12-24 month processing time). Proposal strategy: 95%+ already-cleared staff, bench depth for attrition, FSO support for expedited processing. Discriminator vs competitors: day-one operational capability, zero clearance delay.
```

---

## Section 5: Strategic Theme Extraction from RFP Priorities

**Strategic themes** = Overarching proposal messages aligned with customer priorities

### Pattern 1: Mission Alignment Themes

**Detection signals**:

- Agency mission statements in Section C (SOW)
- "in support of [mission]" language
- Strategic goals referenced in RFP

**Extraction pattern**:

```
entity|Mission Readiness Strategic Theme|strategic_theme|RFP references "support Navy Fleet readiness" 17 times across SOW. Primary strategic theme: everything we do enhances Fleet operational readiness. Tie technical approach to readiness (faster depot turnaround), management to readiness (surge capacity for deployments), past performance to readiness (zero mission delays from IT issues). Evaluation linkage: likely unstated subfactor under technical/management evaluation.
```

### Pattern 2: Cost Consciousness Themes

**Detection signals**:

- "budget constraints", "fiscal environment" mentions
- "cost-effective", "best value" emphasis
- LPTA evaluation methodology (price-focused)

**Extraction pattern**:

```
entity|Fiscal Stewardship Strategic Theme|strategic_theme|"constrained budget environment" language (3 mentions) + "cost-effectiveness" emphasis signals fiscal sensitivity. Strategic theme: maximize taxpayer value through efficiency. Tie solutions to cost savings: automation reduces labor hours, cloud reduces infrastructure costs, process improvement reduces waste. Quantify: "20% cost reduction vs current spend while improving service levels".
```

### Pattern 3: Innovation/Modernization Themes

**Detection signals**:

- "modernization", "legacy system replacement" language
- "innovative solutions encouraged"
- Technology refresh mentions

**Extraction pattern**:

```
entity|Digital Transformation Strategic Theme|strategic_theme|"modernize legacy systems" appears in SOW objectives. Strategic theme: lead customer digital transformation journey. Propose modern tech stack (cloud-native, microservices, API-first), change management for user adoption, phased migration (minimize risk). Past performance: successful modernization projects, legacy-to-cloud migrations, user adoption metrics.
```

---

## Section 6: Competitive Intelligence Extraction

**Extract signals about competitive environment** to inform proposal strategy:

### Incumbent Advantage/Disadvantage Signals

**Incumbent advantage signals**:

- "incumbent may propose" → Incumbent participation expected
- "current contractor knowledge transfer" → Incumbent has institutional knowledge
- "continuity of operations" emphasis → Incumbent has lower transition risk

**Incumbent disadvantage signals**:

- "performance issues" mentions → Incumbent vulnerability
- "new approaches welcomed" → Customer dissatisfaction with status quo
- "fresh perspective" language → Customer wants change

**Extraction pattern**:

```
entity|Incumbent Vulnerability|strategic_theme|RFP mentions "recent performance issues with current support" and "interested in innovative approaches to improve service delivery". Signal: incumbent weakness, customer openness to change. Proposal strategy: emphasize transition excellence (mitigate change risk), innovation (address performance gaps), past performance (proof of better results). Avoid incumbent bashing - focus on our strengths.
```

### Set-Aside/Socioeconomic Signals

**Detection signals**:

- "100% small business set-aside" → Only small businesses can prime
- "8(a) set-aside" → Restricted competition
- "subcontracting plan required" → Unrestricted but SB goals matter

**Extraction pattern**:

```
entity|Small Business Strategy|strategic_theme|100% small business set-aside restricts competition to small businesses. Prime must be small at proposal submission AND award. Strategy: verify size standard compliance (NAICS 541512, $19M), avoid affiliation issues, demonstrate small business advantages (agility, local presence, lower overhead). Evaluation: SBA certification documentation required.
```

---

## Section 7: Section L → Proposal Structure Mapping

**Extract submission instructions** that guide proposal organization:

### Volume/Section Organization

**Detection pattern**:

```
entity|Technical Volume Organization|submission_instruction|Section L.3: Technical proposal organized as follows: 1) Technical Approach (25 pages), 2) Management Approach (15 pages), 3) Past Performance (10 pages, separate volume). Total technical: 50 pages, 12pt font, 1-inch margins. Cover, TOC, resumes excluded from page count.

relationship|Technical Volume Format|GUIDES|Factor 1-2: Technical and Management|structure|Volume organization maps directly to evaluation factors - maintain same structure in proposal
```

### Mandatory Response Format

**Detection signals**:

- "shall respond to each requirement in order presented" → Compliance matrix format
- "use provided template" → Prescribed structure
- "cross-reference RFP section numbers" → Traceability requirement

**Extraction pattern**:

```
entity|Compliance Matrix Requirement|submission_instruction|Section L.4: Contractor shall provide compliance matrix with columns: RFP Section | Requirement | Compliance (Yes/No/Exception) | Proposal Reference (section/page). Mandatory format - non-compliance may result in proposal rejection. Matrix must address ALL shall/must requirements.

relationship|Compliance Matrix|TRACES|MANDATORY Requirements|traceability|Matrix provides evaluator roadmap to find compliance evidence
```

---

## Extraction Guidelines Summary

### Entity Type Selection

**Primary types**:

- `strategic_theme` - Win themes, discriminators, competitive intelligence, risk themes
- `submission_instruction` - Proposal format, page limits, required structures
- `requirement` - Extracted with criticality level (MANDATORY/SHOULD/MAY)

**Related entities**:

- `concept` - Methodologies, frameworks (Agile, DevSecOps, ITIL)
- `event` - Proposal milestones, Q&A deadlines, oral presentation dates

### Description Enrichment Formula

**Strategic Theme Template**: `[RFP Signal] ([Frequency/Emphasis]). [Strategic Theme Name]: [Core Message]. [Proposal Strategy]: [How to address]. [Evidence Needed]: [Past performance/proof points]. [Evaluation Linkage]: [Which factors this supports].`

**Example**:

```
entity|Transition Excellence Theme|strategic_theme|"minimize disruption during transition" (5 mentions in SOW) + "incumbent limited support" signal. Strategic Theme: Seamless Transition with Zero Service Gaps. Proposal Strategy: 90-day transition (vs 30-day minimum), reverse shadowing, independent discovery, parallel operations. Evidence: Past performance - 3 successful transitions from uncooperative incumbents, zero service interruptions. Evaluation Linkage: Management Approach (transition plan), Risk Mitigation (continuity assurance).
```

### Relationship Prioritization

**High-priority relationships**:

1. `strategic_theme --SUPPORTS--> evaluation_factor` - Themes aligned to scoring
2. `strategic_theme --ADDRESSES--> requirement` - Themes respond to RFP needs
3. `submission_instruction --GUIDES--> evaluation_factor` - Format → factor mapping
4. `discriminator --DIFFERENTIATES_FROM--> competitors` - Competitive advantages
5. `risk_theme --MITIGATED_BY--> past_performance` - Risk evidence

---

## Pattern Recognition Over Prescription

**CRITICAL REMINDER**: These patterns represent OBSERVATIONS from proposal development best practices, NOT requirements the RFP imposes.

**LLM should**:

- ✅ Recognize RFP language patterns that SIGNAL proposal strategy opportunities
- ✅ Extract strategic themes that ALIGN with customer priorities
- ✅ Identify discriminators based on competitive landscape INFERENCES
- ✅ Understand semantic variance ("solution design" = "technical approach")

**LLM should NOT**:

- ❌ Invent requirements not in RFP
- ❌ Assume all RFPs follow same structure
- ❌ Apply patterns rigidly when RFP contradicts
- ❌ Ignore explicit RFP guidance in favor of "typical" patterns

**Philosophy**: Use these patterns as CONTEXT for semantic understanding, not as RULES that override RFP content.

---

**Version**: 1.0 (Option A - Lean Extraction)  
**Lines**: ~550 (vs 746 in original library)  
**Focus**: Win theme detection, discriminators, compliance patterns, competitive intelligence  
**Integration**: Load alongside FAR/DFARS and evaluation factor patterns for complete domain coverage
