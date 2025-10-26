# Agency Evaluation Intelligence Library

**Purpose**: Evaluation factor patterns, scoring methodologies, and proposal strategies across federal agencies  
**Usage**: Referenced during entity extraction and query responses for agency-specific evaluation intelligence  
**Scope**: Common evaluation patterns + agency-specific tendencies (DoD, civilian, combat, logistics, healthcare, law enforcement, etc.)  
**Philosophy**: **PATTERN RECOGNITION using LLM semantic understanding, NOT rigid deterministic rules**  
**Size**: ~10,000 tokens (evaluation pattern expertise)  
**Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements - Flexibility Emphasis)

---

## How to Use This Library

**During Extraction**: When LLM encounters evaluation factors (Section M), use this library to:

1. **Identify evaluation methodology** - Best Value Tradeoff vs LPTA vs Two-Step
2. **Recognize agency patterns** - DoD prioritizes past performance, civilian prioritizes management, healthcare prioritizes personnel qualifications
3. **Extract scoring weights** - Adjectival (Excellent/Good/Acceptable) vs numerical (0-100 points)
4. **Predict unstated factors** - What agencies ALWAYS evaluate even if not explicit
5. **Tailor proposal strategy** - Agency-specific hot buttons and evaluation culture

**NOT a replacement** for RFP Section M - this is **pattern recognition** to understand what agencies VALUE beyond what they write.

---

## Section 1: Common Evaluation Patterns (Pattern Recognition, Not Rigid Rules)

> **CRITICAL PHILOSOPHY**: These patterns represent COMMON observations from federal RFPs, NOT universal requirements. RFPs vary widely in structure, factor naming, and organization. **Use LLM semantic understanding** to recognize evaluation INTENT regardless of specific factor names. Example: "Solution Design" + "Implementation Plan" = Technical approach (split into 2 sub-factors with different naming). **ADAPT to each RFP's unique structure** rather than forcing patterns.

### Pattern 1: The Three-Factor Trinity (Observed in ~80% of RFPs, But NOT Universal)

**Common Pattern** (recognize semantically, NOT as rigid template):

1. **Technical Approach** (30-50% weight) - HOW you'll do the work  
   _Also appears as_: "Solution Design", "Methodology", "Project Approach", "Technical Solution"
2. **Management Approach** (20-35% weight) - HOW you'll manage the work  
   _Also appears as_: "Program Management", "Team Organization", "Management Plan", "Project Controls"
3. **Past Performance** (20-40% weight) - PROOF you've done it before  
   _Also appears as_: "Relevant Experience", "Corporate Experience", "Past Contract Performance"

**IMPORTANT**: RFPs may use 2 factors, 5+ factors, or completely novel naming. **Recognize WHAT IS BEING EVALUATED** (technical capability vs management capability vs proven track record) rather than matching exact factor names.

**Price Treatment**:

- **Best Value Tradeoff**: Price evaluated separately, tradeoff against technical
- **LPTA (Lowest Price Technically Acceptable)**: Technical pass/fail, award to lowest price
- **Two-Step**: Technical qualification first, then price competition among qualified offerors

**Common Sub-Factors** (frequently observed, but names and organization vary widely):

- **Technical**: Architecture, approach, innovation, compliance, risk mitigation  
  _Pattern recognition_: May appear as separate sub-factors ("Technical Approach" + "Risk Mitigation" + "Innovation") or combined
- **Management**: Organization, staffing, quality assurance, schedule, subcontractor management  
  _Pattern recognition_: May split into "Staffing Plan" + "Quality Assurance" + "Schedule Management" as distinct factors
- **Past Performance**: Relevance, recency, quality of performance (CPARS ratings)  
  _Pattern recognition_: May appear as "Corporate Experience", "Relevant Contract History", or "References"

**Shipley Alignment Strategy**:

- Allocate proposal pages proportional to evaluation weights
- Lead each factor with your strongest discriminator
- Cross-reference technical approach → past performance (prove you've done it)

---

### Pattern 2: Adjectival vs Numerical Scoring

#### Adjectival Scoring (DoD Standard)

**Rating Scale**:

- **Outstanding**: Exceeds requirements, minimal risk, significant strengths
- **Good**: Meets requirements, low risk, some strengths
- **Acceptable**: Meets minimum requirements, moderate risk, no strengths
- **Marginal**: Does not meet some requirements, high risk, weaknesses outweigh strengths
- **Unacceptable**: Does not meet requirements, unacceptable risk, significant weaknesses

**Scoring Philosophy**:

- "Outstanding" is RARE (reserved for truly exceptional approaches)
- Most competitive proposals receive "Good" or "Outstanding"
- "Acceptable" proposals rarely win (unless LPTA)
- Any "Marginal" or "Unacceptable" sub-factor = proposal likely loses

**Proposal Strategy**:

- Target "Outstanding" on highest-weighted factors (your discriminators)
- Ensure "Good" minimum on all other factors (no weaknesses)
- Avoid vague claims that evaluators can't rate (unprovable = "Acceptable" at best)

#### Numerical Scoring (GSA, Civilian Agencies Common)

**Point Scale**:

- **100 points maximum** per factor (typical)
- **0 points** = non-responsive/unacceptable
- **50-69 points** = minimally acceptable
- **70-84 points** = good/competitive
- **85-100 points** = excellent/outstanding

**Scoring Methodology**:

- Each sub-factor assigned point range (e.g., "Architecture: 0-20 points")
- Evaluators score based on strengths/weaknesses
- Total score determines competitive ranking

**Proposal Strategy**:

- Identify highest point-value sub-factors (focus discriminators there)
- Provide quantified proof for high-point claims (past performance metrics)
- Avoid losing "easy points" on format compliance (page limits, required sections)

---

### Pattern 3: Past Performance Relevance Scoring

**Common Criteria** (typical patterns, but specific criteria and rating scales vary by RFP):

#### Relevance (How similar to this RFP?)

- **Very Relevant**: Same scope, same customer type, same size/complexity
- **Relevant**: Similar scope, similar customer, comparable size
- **Somewhat Relevant**: Related work but different scope/customer/size
- **Not Relevant**: Unrelated work (don't submit these!)

**Example (IT Services RFP)**:

```
Very Relevant: Navy enterprise help desk, $10M/year, 50,000 users, 5-year contract
Relevant: Army desktop support, $8M/year, 30,000 users, 3-year contract
Somewhat Relevant: Commercial IT outsourcing, $15M/year, 100,000 users (not government)
Not Relevant: Software development contract (not help desk/support)
```

#### Recency (How recent is this experience?)

- **Highly Recent**: Currently performing OR completed within last 3 years
- **Recent**: Completed 3-5 years ago
- **Not Recent**: Completed >5 years ago (use only if no better examples)

**Agency Nuance**:

- **DoD**: Prefers contracts performed in last 3 years (technology changes fast)
- **Civilian**: More flexible on recency if mission/scope highly relevant
- **Healthcare/Law Enforcement**: Strongly prefer current contracts (regulatory compliance changes)

#### Quality (How well did you perform?)

- **Exceptional**: CPARS "Exceptional" overall, zero defaults, award fees earned
- **Very Good**: CPARS "Very Good" or better, no major issues
- **Satisfactory**: CPARS "Satisfactory", some issues but resolved
- **Marginal/Unsatisfactory**: CPARS below "Satisfactory" (DON'T SUBMIT!)

**Shipley Strategy**:

- Submit 3-5 past performance contracts (RFP typically requests 3)
- Prioritize: Very Relevant + Highly Recent + Exceptional Quality
- If you lack "Very Relevant", submit 2 Relevant + 1 Very Relevant (breadth + depth)
- NEVER submit contracts with CPARS below "Satisfactory" (automatic weakness)

---

## Section 2: Agency Category Patterns (Agency-Agnostic Taxonomy)

### Category A: Combat Operations Agencies (DoD Combat Commands)

**Agencies**: Navy, Air Force, Army, Marine Corps, SOCOM, Space Force, Coast Guard (combat missions)

**Evaluation Priorities**:

1. **Mission Criticality**: Proven performance in high-stakes, mission-critical environments
2. **Security Clearances**: Personnel clearances (SECRET/TS/SCI) MUST be in place (not "will obtain")
3. **Operational Tempo**: 24/7/365 operations, rapid response, minimal downtime tolerance
4. **Combat Experience**: Prior work with combat units, forward-deployed operations, OCONUS locations
5. **Flexibility**: Ability to adapt to changing mission requirements (surge capacity)

**Hot Buttons**:

- "Mission failure is not an option" (zero-defect mentality)
- Cleared personnel ready Day 1 (no 12-month clearance delays)
- Proven OCONUS performance (Kuwait, Germany, Japan, etc.)
- Experience with classified systems (SIPR, JWICS, SAP)

**Proposal Strategy**:

- Lead with past performance on combat missions (not just "DoD" - specify combat units)
- Highlight cleared personnel percentages (e.g., "85% of proposed staff already SECRET-cleared")
- Describe surge capacity (can scale 20% in 30 days if mission demands)
- Include OCONUS experience (specific countries, not just "deployed overseas")

**Common Weaknesses**:

- Generic "DoD experience" without combat specificity
- "Will obtain clearances" (unacceptable - mission can't wait 12 months)
- No OCONUS performance (red flag for combat agencies)
- Commercial-focused past performance (not mission-critical enough)

---

### Category B: Logistics & Sustainment Agencies (DoD/Civilian Logistics)

**Agencies**: Defense Logistics Agency (DLA), GSA, USTRANSCOM, Army Materiel Command, Navy Supply Systems Command

**Evaluation Priorities**:

1. **Supply Chain Management**: Proven logistics planning, inventory management, distribution
2. **Cost Efficiency**: Demonstrated cost savings, process improvements, lean methodologies
3. **Quality Assurance**: ISO 9001, Six Sigma, defect reduction, on-time delivery metrics
4. **Scale**: Ability to handle large volumes (millions of parts, global distribution)
5. **ERP Systems**: SAP, Oracle, government systems (DLA EMALL, GSA Advantage)

**Hot Buttons**:

- "On-time delivery" (95%+ is table stakes, 98%+ is competitive)
- Cost savings (quantified: "Reduced inventory costs 15% over 3 years")
- Quality certifications (ISO 9001, AS9100 for aerospace)
- Global reach (distribution to 50+ countries, multi-modal transport)

**Proposal Strategy**:

- Lead with quantified logistics metrics (on-time %, inventory turns, order accuracy)
- Highlight cost savings examples ($X saved through process improvement Y)
- Include quality certifications (ISO 9001 certificate as proposal attachment)
- Describe scale of prior work (e.g., "Managed 2M SKUs across 40 distribution centers")

**Common Weaknesses**:

- Vague "logistics experience" without metrics (no on-time delivery %, no cost savings)
- No quality certifications (ISO 9001 expected for serious competitors)
- Small-scale examples (managed 10 warehouses when RFP needs 100)
- No ERP expertise (SAP/Oracle skills critical for enterprise logistics)

---

### Category C: Healthcare & Life Sciences Agencies (HHS, VA, NIH, CDC, FDA)

**Agencies**: Department of Health & Human Services (HHS), Veterans Affairs (VA), National Institutes of Health (NIH), CDC, FDA, CMS

**Evaluation Priorities**:

1. **Clinical Expertise**: Licensed healthcare professionals (RN, MD, pharmacist, lab tech), board certifications
2. **Regulatory Compliance**: HIPAA, 21 CFR Part 11 (FDA), CLIA (lab certifications), Joint Commission
3. **Patient Safety**: Proven track record of zero adverse events, patient satisfaction scores
4. **Electronic Health Records (EHR)**: Epic, Cerner, VistA (VA), interoperability (HL7, FHIR)
5. **Research Integrity**: IRB approval processes, clinical trial management (if research-focused)

**Hot Buttons**:

- "Patient safety is paramount" (zero tolerance for adverse events)
- HIPAA compliance (mandatory, not negotiable)
- Clinical staff qualifications (RN with BSN preferred over ADN)
- EHR system expertise (specific platform experience, not generic IT)

**Proposal Strategy**:

- Lead with clinical credentials (percentage of staff with advanced degrees/certifications)
- Highlight regulatory compliance (HIPAA, CLIA certs, Joint Commission accreditation)
- Quantify patient outcomes (satisfaction scores, readmission rates, adverse event rates)
- Describe EHR platform expertise (e.g., "Implemented Epic at 15 VA facilities")

**Common Weaknesses**:

- IT staff without healthcare background (evaluators want clinical + IT hybrid skills)
- No HIPAA compliance examples (automatic red flag for healthcare agencies)
- Generic "healthcare experience" without patient outcome metrics
- No EHR platform specificity (saying "EHR experience" without naming Epic/Cerner/VistA)

---

### Category D: Law Enforcement & Border Security (DHS, CBP, ICE, TSA, Secret Service)

**Agencies**: Department of Homeland Security (DHS), Customs & Border Protection (CBP), ICE, TSA, Secret Service, DEA, FBI, ATF

**Evaluation Priorities**:

1. **Law Enforcement Background**: Former LEO, law enforcement training, clearances (Public Trust, Secret)
2. **Operational Security**: FOUO handling, law enforcement sensitive (LES) data, chain of custody
3. **24/7 Operations**: Around-the-clock support, rapid response to incidents, surge capacity
4. **Interagency Coordination**: Experience working across federal/state/local agencies, task forces
5. **Technology Integration**: Biometrics, surveillance systems, data analytics, AI/ML for threat detection

**Hot Buttons**:

- "Officer safety" (technology/processes that protect LEOs in the field)
- Chain of custody (evidence handling, forensic integrity)
- Real-time intelligence (actionable intelligence within minutes, not hours)
- Border security mission (specific CBP/ICE experience highly valued)

**Proposal Strategy**:

- Lead with law enforcement credentials (percentage of staff with LEO background)
- Highlight security clearances/background checks (Public Trust minimum, Secret preferred)
- Describe 24/7 operational experience (e.g., "Supported 300 CBP officers across 5 ports of entry")
- Quantify operational outcomes (e.g., "Reduced border wait times 20% through AI-powered analytics")

**Common Weaknesses**:

- No law enforcement background (civilian IT staff without LEO context)
- Generic "DHS experience" without CBP/ICE/TSA specificity
- No real-time operations examples (batch processing when mission needs real-time)
- Missing interagency coordination (LEO agencies work across jurisdictions constantly)

---

### Category E: Research & Development Agencies (DARPA, NASA, DOE, NIST, NSF)

**Agencies**: DARPA, NASA, Department of Energy (DOE National Labs), NIST, NSF, NIH (research divisions)

**Evaluation Priorities**:

1. **Technical Expertise**: PhD-level researchers, subject matter experts, publications/patents
2. **Innovation**: Cutting-edge approaches, novel methodologies, high-risk/high-reward research
3. **Collaboration**: University partnerships, FFRDCs, international collaborations
4. **Publication Record**: Peer-reviewed publications, conference presentations, citation impact
5. **Technology Transfer**: Commercialization potential, patents, industry partnerships

**Hot Buttons**:

- "Advancing the state of the art" (not incremental improvements, but breakthroughs)
- Academic credentials (PhD preferred, postdoc experience valued)
- Peer-reviewed publications (citation counts, h-index, journal impact factors)
- Interdisciplinary teams (physics + biology + computer science collaborations)

**Proposal Strategy**:

- Lead with researcher credentials (PhDs, postdocs, publication counts, h-index)
- Highlight innovation examples (patents filed, novel methodologies developed)
- Describe collaboration networks (university partnerships, international teams)
- Quantify research impact (publications in Nature/Science, patent citations, technology adoption)

**Common Weaknesses**:

- Industry practitioners without academic credentials (MS acceptable but PhD preferred)
- No publication record (evaluators check Google Scholar, ResearchGate)
- Incremental work when agency wants breakthrough innovation
- No collaboration examples (R&D agencies value multi-institutional teams)

---

### Category F: Financial Management & Audit Agencies (Treasury, IRS, GAO, DCAA, OMB)

**Agencies**: Department of Treasury, IRS, GAO, DCAA, OMB, SEC, FDIC, Federal Reserve

**Evaluation Priorities**:

1. **Financial Certifications**: CPA, CMA, CIA, CISA, CFE (fraud examination)
2. **Audit Experience**: Federal audit standards (Yellow Book/GAGAS), financial statement audits
3. **Regulatory Compliance**: Sarbanes-Oxley, FISMA, OMB circulars, federal accounting standards
4. **Data Analytics**: ACL, IDEA, SAS, Python for financial analysis
5. **Security Clearances**: Financial data often sensitive (Secret clearance common)

**Hot Buttons**:

- "Audit-ready" (accurate financial reporting, no findings)
- CPA certification (mandatory for senior audit staff)
- GAGAS compliance (Yellow Book standards for federal audits)
- Data analytics (forensic accounting, fraud detection algorithms)

**Proposal Strategy**:

- Lead with certifications (percentage of staff with CPA, CIA, CISA, CFE)
- Highlight audit experience (federal financial statement audits, no findings)
- Describe data analytics capabilities (ACL/IDEA tools, fraud detection algorithms)
- Quantify audit outcomes (e.g., "Identified $10M in cost savings through forensic analysis")

**Common Weaknesses**:

- No CPA staff (unacceptable for federal audit work)
- Commercial audit experience without federal GAGAS knowledge
- No data analytics expertise (manual audits when agencies want AI-powered fraud detection)
- Missing security clearances (financial data often classified or sensitive)

---

## Section 3: Agency-Specific Evaluation Nuances (Pattern Recognition)

### DoD Agencies (Cross-Category Patterns)

**Unique Evaluation Characteristics**:

- **Adjectival scoring** (Outstanding/Good/Acceptable) vs numerical points
- **Past performance heavily weighted** (30-40% typical, sometimes equal to technical)
- **CPARS ratings scrutinized** (anything below "Very Good" is a competitive disadvantage)
- **Security clearances critical** ("Will obtain" is unacceptable for SECRET/TS positions)
- **DFARS compliance assumed** (NIST 800-171, specialty metals, trade agreements)

**Frequently Observed Unstated Factors** (DoD often evaluates these even when not explicitly listed in Section M):

- Transition risk (if successor contract, how smooth will transition be? - _recognize transition language throughout RFP_)
- Incumbent advantage (is current contractor proposing? Do they have continuity? - _not universal, depends on procurement_)
- Small business utilization (even on unrestricted contracts, strong SB plan often valued - _varies by command priorities_)
- Mission understanding (do you understand WHY this work matters, not just HOW to do it? - _infer from RFP context, not always explicit_)

**Proposal Strategy**:

- Dedicate 1-2 pages to "Mission Understanding" (restate DoD strategic objectives)
- If incumbent, emphasize continuity (same PM, same staff, zero learning curve)
- If not incumbent, highlight transition plan (minimize disruption, rapid ramp-up)
- Include SB plan even if not required (shows commitment to DoD priorities)

---

### Civilian Agencies (Cross-Category Patterns)

**Unique Evaluation Characteristics**:

- **Numerical scoring** (0-100 points) more common than adjectival
- **Management approach often highest weight** (35-45% vs 20-30% for DoD)
- **Personnel qualifications critical** (specific degrees, certifications, licenses)
- **Diversity & inclusion valued** (Section 508 compliance, EEO policies)
- **Cost control emphasized** (efficiency, cost savings, taxpayer stewardship)

**Frequently Observed Unstated Factors** (Civilian agencies often consider these even when not explicit):

- Budget consciousness (can you deliver within constrained budgets? - _infer from cost control language in SOW_)
- Transparency (clear reporting, no surprises, open communication - _more emphasized than DoD_)
- Accessibility (Section 508 compliance for disabilities, not just IT systems - _only relevant if public-facing_)
- Environmental sustainability (green initiatives, LEED certifications - _varies widely by agency priorities_)

**Proposal Strategy**:

- Quantify cost savings examples ("Reduced operating costs 15% through process automation")
- Highlight Section 508 compliance (accessible websites, documents, systems)
- Describe sustainability initiatives (energy efficiency, waste reduction, LEED buildings)
- Emphasize transparency (monthly reports, open-door policy, stakeholder engagement)

---

## Section 4: Evaluation Methodology Recognition (FAR Part 15)

### Best Value Tradeoff (Most Common for Complex Services)

**Evaluation Statement** (typical RFP language):

```
"Award will be made to the offeror whose proposal represents the best value to the
Government, price and other factors considered. Technical and past performance are
significantly more important than price."
```

**What This Means**:

- Price is evaluated but NOT the deciding factor
- Higher-priced proposal CAN win if technically superior
- Government performs tradeoff analysis (is technical advantage worth price premium?)

**Proposal Strategy**:

- Focus on technical discriminators (price premium must be justified)
- Quantify value proposition (e.g., "Our approach saves $2M over life of contract despite 5% higher proposal price")
- Don't be the lowest price (signals you don't understand requirement or will cut corners)
- Don't be the highest price (unless VERY strong technical justification)

**Competitive Positioning**:

- Target pricing: Within 10% of independent government estimate (IGE)
- Technical strategy: "Outstanding" on highest-weighted factors, "Good" on rest
- Value messaging: "Our higher upfront cost delivers $X savings over contract life"

---

### LPTA (Lowest Price Technically Acceptable)

**Evaluation Statement** (typical RFP language):

```
"Award will be made to the lowest priced, technically acceptable offeror. Technical
proposals will be evaluated as acceptable or unacceptable. Price will determine award
among technically acceptable offerors."
```

**What This Means**:

- Technical is pass/fail (Acceptable vs Unacceptable)
- Price is the ONLY discriminator among acceptable proposals
- No credit for exceeding requirements (don't waste proposal real estate)

**Proposal Strategy**:

- Meet minimum requirements EXACTLY (no gold-plating)
- Shortest compliant proposal (save evaluation time = goodwill, but don't skip requirements)
- Aggressive pricing (every dollar counts - this is a price shootout)
- Risk mitigation in cost (show you can deliver at low price without quality compromise)

**Competitive Positioning**:

- Target pricing: At or below IGE (preferably 5-10% below competitors)
- Technical strategy: "Acceptable" on ALL factors (any "Unacceptable" = elimination)
- Efficiency messaging: "Our lean processes enable low price without sacrificing quality"

**Common Mistakes in LPTA**:

- ❌ Gold-plating proposal (exceeding requirements doesn't help, wastes evaluation time)
- ❌ Pricing above IGE (likely uncompetitive unless all competitors also high)
- ❌ Weak technical response (trying to save evaluation effort but risk "Unacceptable")

---

### Two-Step Sealed Bidding (Less Common, Used for Complex Acquisitions)

**Step 1**: Technical proposals evaluated (no price), offerors deemed qualified or unqualified  
**Step 2**: Qualified offerors submit sealed bids (price only), award to lowest bidder

**What This Means**:

- Technical qualification is gate (must pass Step 1 to compete in Step 2)
- Price is ONLY factor in Step 2 (pure price competition among qualified)
- Can't win on technical excellence in Step 2 (already qualified in Step 1)

**Proposal Strategy**:

- **Step 1**: Demonstrate technical competence (meet ALL qualification criteria)
- **Step 2**: Aggressive pricing (lowest bid wins among qualified)
- Front-load technical effort (Step 1 is the gate, Step 2 is the race)

---

## Section 5: Integration with Ontology

### How Agency Intelligence Enhances Entity Extraction

**Before Agency Library** (generic extraction):

```json
{
  "entity_name": "Factor 1: Technical Approach",
  "entity_type": "EVALUATION_FACTOR",
  "weight": "40%",
  "description": "Evaluates contractor's technical solution"
}
```

**After Agency Library** (enhanced extraction):

```json
{
  "entity_name": "Factor 1: Technical Approach",
  "entity_type": "EVALUATION_FACTOR",
  "weight": "40%",
  "agency_category": "Combat Operations (Navy)",
  "evaluation_methodology": "Best Value Tradeoff (Adjectival Scoring)",
  "rating_scale": [
    "Outstanding",
    "Good",
    "Acceptable",
    "Marginal",
    "Unacceptable"
  ],
  "agency_hot_buttons": [
    "Mission-critical 24/7/365 operations (zero downtime tolerance)",
    "Cleared personnel Day 1 (SECRET minimum, TS preferred)",
    "OCONUS operational experience (forward-deployed units)",
    "Classified system integration (SIPR, JWICS)"
  ],
  "unstated_evaluation_criteria": [
    "Transition risk (incumbent continuity vs new contractor ramp-up)",
    "CPARS history (anything below 'Very Good' is competitive disadvantage)",
    "Small business utilization (good SB plan = plus even if unrestricted)"
  ],
  "proposal_strategy": "Lead with combat mission past performance (not generic DoD). Highlight 85% of staff SECRET-cleared (ready Day 1). Describe OCONUS experience (Kuwait, Germany, Japan - specific). Include 2-page Mission Understanding section explaining Navy IT modernization strategy and how your solution supports fleet readiness. If incumbent, emphasize continuity (same PM, same staff). If not, detailed transition plan minimizing service disruption.",
  "competitive_positioning": "Target 'Outstanding' on Technical Approach (highest weight). Quantify past performance (e.g., '99.8% uptime on 3 Navy contracts, zero mission failures'). Price within 10% of IGE (higher acceptable if strong technical justification). Avoid LPTA mindset - Navy values quality over lowest price.",
  "common_weaknesses_to_avoid": [
    "Generic 'DoD experience' without Navy/combat specificity",
    "'Will obtain clearances' (unacceptable - mission can't wait 12 months)",
    "Commercial IT examples (not mission-critical enough for combat operations)",
    "No OCONUS performance (red flag for Navy/combat agencies)"
  ]
}
```

**Benefit**: LLM extracts evaluation factors WITH agency-specific intelligence, not just RFP text!

---

## Section 6: Query Response Enhancements

### User Query: "What does the agency care about most?"

**Generic Response** (without agency library):

```
The agency cares about technical approach (40% weight), management approach (30%),
and past performance (30%). Focus your proposal on these three factors.
```

**Enhanced Response** (with agency library):

```
Based on agency category analysis, this is a **Navy (Combat Operations)** RFP with
**Best Value Tradeoff** evaluation. Here's what Navy REALLY cares about (beyond the RFP text):

**STATED Priorities** (Section M):
- Technical Approach (40% weight)
- Management Approach (30%)
- Past Performance (30%)

**UNSTATED Priorities** (Navy cultural patterns):
1. **Mission Criticality**: 24/7/365 operations supporting fleet readiness - zero tolerance
   for downtime. Your proposal MUST convey "mission failure is not an option" mindset.

2. **Cleared Personnel**: SECRET minimum, TS/SCI preferred. "Will obtain clearances" is
   UNACCEPTABLE (Navy can't wait 12 months). Highlight: "85% of proposed staff already
   SECRET-cleared, 40% have TS/SCI."

3. **OCONUS Experience**: Forward-deployed operations (Kuwait, Bahrain, Japan, Guam). Navy
   evaluators look for "been there, done that" proof. Generic "international" doesn't count -
   specify countries and units supported.

4. **Classified Systems**: SIPR, JWICS, NMCI, CANES integration. Commercial IT experience
   is NOT valued - Navy wants Navy-specific past performance.

5. **CPARS Track Record**: Anything below "Very Good" is competitive disadvantage. If you
   have 100% "Exceptional" on Navy contracts, LEAD with this (rare achievement).

6. **Transition Risk** (if successor contract): Incumbent has advantage (continuity,
   relationships, zero learning curve). If you're NOT incumbent, dedicate 10-15% of proposal
   to transition plan showing how you'll minimize service disruption.

**Proposal Strategy**:
- **Technical Volume**: Lead with combat mission past performance, not generic DoD. Describe
  24/7 ops center architecture. Include classified system integration diagram (UNCLASS version).

- **Management Volume**: Highlight cleared personnel pipeline (how you'll maintain 100%
  cleared staffing). Describe OCONUS support model (time zones, logistics, force protection).

- **Past Performance**: Submit 3 Navy contracts (not Army/Air Force). Emphasize CPARS ratings,
  zero mission failures, uptime metrics (99.8%+). If you supported forward-deployed units,
  highlight (major discriminator).

**Competitive Positioning**:
- Target "Outstanding" on Technical (40% weight) - your discriminators go here
- Ensure "Good" minimum on Management and Past Performance (no weaknesses)
- Price within 10% of IGE (Navy values quality - don't underbid and signal risk)

**Red Flags to Avoid**:
- ❌ Generic "DoD experience" without Navy specificity
- ❌ "Will obtain clearances" language (instant weakness)
- ❌ No OCONUS examples (Navy is global - evaluators expect this)
- ❌ Commercial IT examples when you have Navy contracts (use Navy, not commercial)
```

**Benefit**: 5-10 hours of capture intelligence research saved per RFP!

---

## Conclusion

This Agency Evaluation Intelligence library provides **pattern-based, agency-agnostic** evaluation knowledge that works across:

**6 Agency Categories** (extensible to all federal agencies):

1. Combat Operations (Navy, USAF, Army, USMC, SOCOM, Coast Guard)
2. Logistics & Sustainment (DLA, GSA, USTRANSCOM, Supply Commands)
3. Healthcare & Life Sciences (HHS, VA, NIH, CDC, FDA, CMS)
4. Law Enforcement & Border Security (DHS, CBP, ICE, TSA, Secret Service, DEA, FBI, ATF)
5. Research & Development (DARPA, NASA, DOE, NIST, NSF)
6. Financial Management & Audit (Treasury, IRS, GAO, DCAA, OMB, SEC)

**Common Patterns Across Agencies** (recognize these semantically, adapt to RFP specifics):

- Three-Factor Trinity (Technical/Management/Past Performance) - _observed in ~80% of RFPs, but NOT universal_
- Adjectival vs Numerical Scoring methodologies - _recognize scoring system, don't assume one or the other_
- Past Performance Relevance/Recency/Quality assessment - _specific criteria and timeframes vary widely_
- Best Value vs LPTA vs Two-Step evaluation approaches - _identify from Section M language, not predetermined_

**Agency-Specific Tendencies** (patterns, NOT rules):

- DoD: _Tends toward_ adjectival scoring, higher past performance weights, CPARS emphasis, security clearance requirements
- Civilian: _More commonly uses_ numerical scoring, higher management factor weights, diversity/sustainability language, cost control emphasis

> **REMEMBER**: These are TENDENCIES based on historical observation. Always prioritize what the SPECIFIC RFP states over these general patterns.

**Integration**: Append this library to `entity_extraction_prompt.md` as Section 10 reference material.

**Cost Justification**: 10K tokens = 0.50% of 2M budget, but automates 5-10 hours of capture intelligence per RFP.

**Extensibility**: Pattern-based design allows LLM to apply intelligence to ANY federal agency (not just Navy/USAF/Army).

---

**Version**: 1.0  
**Last Updated**: January 26, 2025  
**Next Review**: June 2025 (post-proposal season - add new agency patterns from wins/losses)  
**Maintainer**: Branch 011 - Prompt Enhancements Team
