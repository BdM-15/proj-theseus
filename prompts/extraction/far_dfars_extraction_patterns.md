# FAR/DFARS Extraction Patterns

**Purpose**: Extract FAR/DFARS clauses with operational intelligence during entity extraction  
**Philosophy**: Pattern recognition for clause implications, flowdown requirements, and cost impacts  
**Usage**: Loaded during RAG-Anything extraction to enrich clause entities with domain knowledge  
**Last Updated**: January 26, 2025 (Branch 011 - Option A Lean Extraction)

---

## Extraction Philosophy

When extracting FAR/DFARS clause entities, **enrich with operational context** beyond basic citation:

```
❌ BASIC: entity|FAR 52.212-1|clause|Instructions to Offerors

✅ ENHANCED: entity|FAR 52.212-1|clause|Instructions to Offerors—Commercial Products and Commercial Services. Deadline ABSOLUTE (no mailbox rule), electronic submissions timestamped by government server, Q&A typically 10 days before proposal due. Non-compliance = rejection before evaluation.
```

**Key Pattern**: LLM should recognize clause → understand implication → extract enriched entity → create relationships

---

## Section 1: FAR 52.212 Series - Commercial Item Acquisitions

### FAR 52.212-1: Instructions to Offerors

**Entity Enrichment Pattern**:

- Type: `clause`
- Criticality: ABSOLUTE (proposal rejection if violated)
- Operational implications: Deadline is ABSOLUTE, no mailbox rule, electronic submissions timestamped by government server receipt
- Temporal pattern: Q&A deadline typically 10 days before proposal due
- Amendment pattern: Amendments SUPERSEDE all prior instructions

**Relationship Triggers**:

- `FAR 52.212-1 --REQUIRES--> Section L submission method` (compliance relationship)
- `FAR 52.212-1 --DEFINES--> Proposal Deadline` (temporal constraint)
- `FAR 52.212-1 --REFERENCED_BY--> Section A` (typically appears in cover page)

**Rejection Patterns** (enrich EVENT entities):

- Late submission → REJECTED (no grace period)
- Wrong email/portal address after amendment → REJECTED
- File size exceeds limit → NON-RESPONSIVE

---

### FAR 52.212-3: Offeror Representations and Certifications

**Entity Enrichment Pattern**:

- Type: `clause`
- Criticality: HIGH (false certification = criminal liability)
- SAM.gov dependency: Large business must update annually, small business needs solicitation-specific reps
- Size standard: NAICS code-specific (varies 500 employees to $41.5M revenue)
- Trade compliance: TAA (designated countries), BAA (domestic preference), Chinese telecom prohibition

**Relationship Triggers**:

- `FAR 52.212-3 --REQUIRES--> SAM.gov Registration` (prerequisite)
- `FAR 52.212-3 --PROHIBITS--> Chinese Telecommunications Equipment` (Huawei, ZTE, Hytera, Hikvision, Dahua)
- `FAR 52.212-3 --FLOWS_TO--> All Subcontractors` (telecommunications screening)

**Risk Patterns**:

- NAICS size standard violation → PROTEST RISK (competitor challenge)
- TAA non-compliance → FALSE CLAIMS ACT exposure
- Affiliate revenue ignored → SIZE DETERMINATION RISK

**Entity Type Guidance**:

- Extract "SAM.gov registration" as REQUIREMENT entity
- Extract "NAICS size standard" as REQUIREMENT entity
- Extract specific prohibitions (Huawei, ZTE) as REQUIREMENT entities with criticality: MANDATORY

---

### FAR 52.212-4: Contract Terms and Conditions

**Entity Enrichment Pattern**:

- Type: `clause`
- Criticality: HIGHEST (core contract obligations)
- Inspection: Government right to inspect at all reasonable times, acceptance at destination
- Changes: Unilateral (in-scope) vs bilateral (out-of-scope), 30-day REA deadline
- Payments: Prompt Payment Act (30 days from invoice), Treasury rate + 1% interest if late
- Excusable delays: Force majeure notice within 10 days, COVID-19 typically NOT excusable

**Relationship Triggers**:

- `FAR 52.212-4 --ESTABLISHES--> Payment Terms` (30-day payment requirement)
- `FAR 52.212-4 --DEFINES--> Inspection Rights` (government acceptance authority)
- `FAR 52.212-4 --REQUIRES--> REA Notice` (30-day deadline for equitable adjustment)

**Temporal Pattern Recognition**:

- Extract "30 days from invoice" as EVENT entity with type: payment_deadline
- Extract "10 days notice for excusable delay" as EVENT entity with type: notification_requirement

---

## Section 2: FAR 52.219 Series - Small Business Programs

### FAR 52.219-9: Small Business Subcontracting Plan

**Entity Enrichment Pattern**:

- Type: `clause`
- Threshold: Required for large businesses on contracts >$750K (>$1.5M for construction)
- Goals: Percentage targets for small business, WOSB, VOSB, HUBZone, SDB categories
- Flowdown: Prime must flow small business requirements to subs
- Reporting: ISR (Individual Subcontract Report) and SSR (Summary Subcontract Report) required

**Relationship Triggers**:

- `FAR 52.219-9 --REQUIRES--> Small Business Subcontracting Plan` (deliverable)
- `FAR 52.219-9 --FLOWS_TO--> Major Subcontractors` (>$750K subs)
- `FAR 52.219-9 --EVALUATED_BY--> Past Performance` (CPARS scoring includes SB compliance)

**Evaluation Pattern**:

- Small business plan often evaluated even when not explicitly listed in Section M
- CPARS ratings include small business utilization
- Extract as both CLAUSE entity and DELIVERABLE entity (the plan itself)

---

### FAR 52.219-28: Post-Award Small Business Program Rerepresentation

**Entity Enrichment Pattern**:

- Type: `clause`
- Trigger: Within 120 days of contract completion, contractor must rerepresent size status
- Implication: If contractor grows beyond size standard, future options may not receive small business credit
- Long-term contract risk: Growth during 5-year IDIQ may affect option years

**Relationship Triggers**:

- `FAR 52.219-28 --AFFECTS--> Contract Options` (size status at option exercise)
- `FAR 52.219-28 --REQUIRES--> Annual Rerepresentation` (120 days before completion)

---

## Section 3: FAR 52.222 Series - Labor Standards

### FAR 52.222-6: Construction Wage Rate Requirements—Davis-Bacon Act

**Entity Enrichment Pattern**:

- Type: `clause`
- Applicability: Construction contracts >$2,000
- Wage determination: Department of Labor prevailing wage rates by location and trade
- Posting requirement: Physical posting at worksite
- Payroll submission: Weekly certified payrolls to contracting officer

**Relationship Triggers**:

- `FAR 52.222-6 --REQUIRES--> Wage Determination` (DOL document)
- `FAR 52.222-6 --CREATES--> Weekly Payroll Reporting` (deliverable)
- `FAR 52.222-6 --FLOWS_TO--> Construction Subcontractors` (all tiers)

**Cost Pattern**: Prevailing wage typically 20-40% higher than commercial rates in high-wage areas

---

### FAR 52.222-41: Service Contract Labor Standards

**Entity Enrichment Pattern**:

- Type: `clause`
- Applicability: Service contracts >$2,500 where services are principal purpose
- Wage determination: DOL Service Contract Act directory by locality
- Health/welfare benefits: $5.36/hour minimum (2024 rate, adjusted annually)
- Successor contractor: Must pay incumbent wages for first year (see FAR 52.222-43)

**Relationship Triggers**:

- `FAR 52.222-41 --REQUIRES--> SCA Wage Determination` (attachment in Section J)
- `FAR 52.222-41 --REFERENCES--> FAR 52.222-43` (successor contractor wages)
- `FAR 52.222-41 --CREATES--> Payroll Reporting Requirement` (monthly certified payrolls)

**Cost Pattern**: Budget $5.36/hour health/welfare + wage rate from DOL directory

**Predecessor Wage Pattern**:

- If successor contract, FAR 52.222-43 requires paying incumbent wages
- Extract incumbent wage table as EQUIPMENT or CONCEPT entity with cost implications

---

## Section 4: DFARS 252.204 Series - Cybersecurity

### DFARS 252.204-7012: Safeguarding Covered Defense Information

**Entity Enrichment Pattern**:

- Type: `clause`
- Standard: NIST 800-171 compliance required
- SSP requirement: System Security Plan must be submitted
- Incident reporting: 72-hour reporting to DoD Cyber Crime Center
- Cost impact: $0.5M - $2M annual compliance cost for mature programs
- Assessment: DoD may request NIST 800-171 assessment results

**Relationship Triggers**:

- `DFARS 252.204-7012 --REQUIRES--> NIST 800-171 Compliance` (security requirement)
- `DFARS 252.204-7012 --REQUIRES--> System Security Plan` (deliverable)
- `DFARS 252.204-7012 --REQUIRES--> 72-Hour Incident Reporting` (event/requirement)
- `DFARS 252.204-7012 --FLOWS_TO--> All Subcontractors with CUI Access` (any tier)

**Evaluation Pattern**:

- Often evaluated under "Management Approach" or "Information Assurance" factors
- Extract SSP as DELIVERABLE entity
- Extract 72-hour reporting as REQUIREMENT entity with criticality: MANDATORY

**Cost Enrichment**:

- Annual compliance: $500K-$2M (mature programs)
- Initial implementation: $1M-$5M (includes SIEM, encryption, access controls)
- Extract these costs as attributes when clause appears with budget discussions

---

### DFARS 252.204-7021: Cybersecurity Maturity Model Certification (CMMC)

**Entity Enrichment Pattern**:

- Type: `clause`
- CMMC levels: Level 1 (basic cyber hygiene), Level 2 (intermediate), Level 3 (advanced/persistent threats)
- Assessment: Third-party C3PAO assessment required (except Level 1 self-assessment)
- Timeline: Assessment typically takes 3-6 months, valid 3 years
- Cost: Level 2 assessment $15K-$50K, Level 3 $100K-$300K

**Relationship Triggers**:

- `DFARS 252.204-7021 --REQUIRES--> CMMC Level X Certification` (requirement)
- `DFARS 252.204-7021 --REQUIRES--> C3PAO Assessment` (third-party audit)
- `DFARS 252.204-7021 --SUPERSEDES--> DFARS 252.204-7012` (for Level 2+)

**Temporal Pattern**:

- 3-year certification validity
- Extract expiration date as EVENT entity if mentioned
- Extract assessment timeline (3-6 months) as planning constraint

---

## Section 5: DFARS 252.225 Series - Trade Agreements

### DFARS 252.225-7021: Trade Agreements

**Entity Enrichment Pattern**:

- Type: `clause`
- Country restrictions: Berry Amendment (domestic preference for food, clothing, textiles)
- Designated countries: TAA countries, Caribbean Basin, NAFTA (now USMCA)
- Specialty metals: DFARS 252.225-7014 requires domestic melting/production
- Exception authority: Head of Contracting Activity may waive for non-availability

**Relationship Triggers**:

- `DFARS 252.225-7021 --REQUIRES--> Country of Origin Verification` (supply chain audit)
- `DFARS 252.225-7021 --PROHIBITS--> Non-Designated Country Components` (trade restriction)
- `DFARS 252.225-7014 --REQUIRES--> Domestic Specialty Metals` (steel, titanium, nickel alloys)

**Supply Chain Pattern**:

- Extract "specialty metals" as REQUIREMENT entity with domestic source requirement
- Extract country restrictions as REQUIREMENT entities with criticality: MANDATORY
- Create relationships to EQUIPMENT entities affected by trade restrictions

---

### DFARS 252.225-7049: Prohibition on Acquisition of Certain Foreign Commercial Satellite Services

**Entity Enrichment Pattern**:

- Type: `clause`
- Prohibition: No commercial satellite services from China, Russia, Iran, North Korea, or entities controlled by these countries
- Waiver: National interest waiver possible but rare
- Due diligence: Contractor must verify satellite ground stations, operations, and data routing

**Relationship Triggers**:

- `DFARS 252.225-7049 --PROHIBITS--> Chinese/Russian Satellite Services` (compliance)
- `DFARS 252.225-7049 --REQUIRES--> Satellite Service Verification` (due diligence)

---

## Section 6: Agency-Specific Supplements

### NMCARS 5252.204-9103: Protection of Government Data (Navy)

**Entity Enrichment Pattern**:

- Type: `clause`
- Navy-specific: Additional cybersecurity requirements beyond DFARS 252.204-7012
- Data protection: Government-furnished data must be encrypted at rest and in transit
- Removable media: Prohibited unless specifically authorized
- Network separation: Government data networks isolated from contractor commercial networks

**Relationship Triggers**:

- `NMCARS 5252.204-9103 --SUPPLEMENTS--> DFARS 252.204-7012` (additional requirements)
- `NMCARS 5252.204-9103 --REQUIRES--> Data Encryption` (security control)
- `NMCARS 5252.204-9103 --PROHIBITS--> Removable Media` (policy constraint)

**Pattern Recognition**: When "NMCARS" appears, recognize as Navy-specific supplement requiring enhanced security controls

---

### AFFARS 5352.242-9000: Contractor Access to Air Force Installations (Air Force)

**Entity Enrichment Pattern**:

- Type: `clause`
- Base access: Contractor personnel require base pass, background checks
- Security clearances: May require interim SECRET for installation access even if unclassified work
- Vehicle registration: POV and contractor vehicles must be registered
- Escort requirements: Uncleared personnel require escort on installation

**Relationship Triggers**:

- `AFFARS 5352.242-9000 --REQUIRES--> Base Access Pass` (credential)
- `AFFARS 5352.242-9000 --REQUIRES--> Background Investigation` (prerequisite)
- `AFFARS 5352.242-9000 --MAY_REQUIRE--> Interim Security Clearance` (conditional requirement)

**Pattern Recognition**: When work location includes "Air Force Base" or "AFB", expect this clause and extract base access as REQUIREMENT

---

## Extraction Guidelines Summary

### Entity Type Selection for Clauses

**Primary entity type**: `clause` (always)

**Additional entities to extract**:

- Deliverables required by clause → `deliverable` (SSP, payroll reports, subcontracting plans)
- Deadlines imposed by clause → `event` (30-day payment, 72-hour incident reporting, 10-day force majeure notice)
- Requirements imposed by clause → `requirement` (NIST 800-171 compliance, wage determinations, trade restrictions)
- Prohibitions in clause → `requirement` with negative framing (no Chinese telecom, no removable media)

### Relationship Pattern Recognition

**Flowdown patterns**:

- `clause --FLOWS_TO--> Subcontractor` when clause explicitly requires subcontractor compliance
- Extract flowdown as relationship with keywords: "flowdown, compliance cascade"

**Evaluation patterns**:

- `clause --EVALUATED_BY--> Evaluation Factor` when clause requirements are scored in Section M
- Example: Small business plan → Past Performance factor, NIST 800-171 → Management Approach factor

**Dependency patterns**:

- `clause --REQUIRES--> Prerequisite` when clause needs prior action
- Example: FAR 52.212-3 --REQUIRES--> SAM.gov Registration

**Cost impact patterns**:

- When clause has cost implications, enrich entity description with cost range
- Example: "DFARS 252.204-7012 compliance typically costs $500K-$2M annually"

### Description Enrichment Formula

**Template**: `[Clause Title]. [Primary Implication]. [Temporal Constraints]. [Cost Impact]. [Flowdown/Evaluation Linkage].`

**Example**:

```
entity|DFARS 252.204-7012|clause|Safeguarding Covered Defense Information and Cyber Incident Reporting. Requires NIST 800-171 compliance, System Security Plan submission, 72-hour incident reporting to DoD Cyber Crime Center. Annual compliance cost typically $500K-$2M. Flows to all subcontractors with CUI access. Often evaluated under Management Approach or Information Assurance factors.
```

---

**Version**: 1.0 (Option A - Lean Extraction)  
**Lines**: ~400 (vs 894 in original library)  
**Focus**: Pure extraction guidance, removed human checklists/strategy  
**Integration**: Load in `src/server/initialization.py` alongside entity_extraction_prompt and entity_detection_rules
