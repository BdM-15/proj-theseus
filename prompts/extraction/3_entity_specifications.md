# Entity Specifications: 17 Types with Semantic Definitions

**Version**: 2.0 (Branch 011 - Execution Framework Architecture)  
**Last Updated**: January 27, 2025  
**Purpose**: Detailed semantic definitions for all 17 entity types with decision-making value, detection patterns, and disambiguation rules

---

## How to Use This Reference

This file is consulted during **STEP 2: Classify** of the execution framework when you need:

1. **Semantic definition** - What does this entity type mean conceptually?
2. **Decision-making value** - Why does this entity type matter for strategic analysis?
3. **Detection patterns** - What semantic signals indicate this type?
4. **Examples** - What does a good extraction look like?
5. **Disambiguation** - When multiple types could apply, which to choose?

**Remember**: Entity type is determined by **CONTENT (semantic meaning)**, NOT by **LOCATION (where it appears in RFP)**.

---

## Core Entities (6 types)

### 1. ORGANIZATION

**Semantic Definition**: Companies, government agencies, departments, teams, prime contractors, subcontractors, teaming partners, and organizational units.

**Decision-making value**: Organizations drive teaming strategy (who to partner with), competitive intelligence (who are the competitors), and accountability mapping (who is responsible for what). Knowing "NAVAIR" is the requiring activity vs "PEO Digital" affects proposal strategy and relationship leverage.

**Detection Patterns**:

- Company names: "Booz Allen Hamilton", "CACI", "Leidos"
- Government agencies: "NAVAIR", "SPAWAR", "GSA", "DoD"
- Departments/divisions: "Contracts Division", "Program Management Office"
- Team structures: "Prime contractor", "Subcontractor", "Joint Venture"
- Acronyms: "PMO", "PEO", "NAVFAC", "AFWERX"

**Examples**:

✅ **Good**:

```
entity|Naval Air Systems Command (NAVAIR)|organization|Requiring activity for this procurement. Located in Patuxent River, MD. Responsible for acquisition, development, and lifecycle support of naval aircraft and systems.
```

✅ **Excellent** (target this):

```
entity|Naval Air Systems Command (NAVAIR)|organization|Requiring activity and Contracting Officer's organization. NAVAIR PMA-290 is program office for unmanned systems. Incumbent relationship strength affects proposal strategy (emphasize continuity vs innovation). Key decision-makers: CAPT Smith (PM), John Doe (COR). Location: Patuxent River, MD influences performance requirements and site access.
```

**Disambiguation**:

- vs **PERSON**: If refers to individual (John Doe) → person; if organization unit (PMO) → organization
- vs **LOCATION**: If geographic area (Patuxent River) → location; if agency at that location (NAVAIR Patuxent River) → organization

---

### 2. CONCEPT

**Semantic Definition**: Abstract ideas, methodologies, frameworks, technical approaches, budget concepts, CLIN structures, and procedural patterns.

**Decision-making value**: Concepts define HOW work will be approached (Agile vs Waterfall affects team structure), budget understanding (CLIN structure affects pricing strategy), and technical frameworks (DevSecOps implies specific tooling costs).

**Detection Patterns**:

- Methodologies: "Agile", "Waterfall", "DevSecOps", "Continuous Integration"
- Frameworks: "NIST Cybersecurity Framework", "CMMI", "ITIL"
- Budget concepts: "CLIN 0001", "Option Year 2", "Time and Materials pricing"
- Procedural patterns: "Earned Value Management", "Change Control Board"
- Abstract ideas: "Innovation", "Collaboration", "Risk Management"

**Examples**:

✅ **Good**:

```
entity|Agile Development|concept|Iterative development methodology using sprints, user stories, and continuous delivery.
```

✅ **Excellent**:

```
entity|Agile Development Methodology|concept|Required development approach (Section C Para 3.2.1). Mandates 2-week sprints, daily standups, retrospectives. Implies team structure: Product Owner, Scrum Master, Dev Team (5-9 people). Affects staffing plan and proposal organization. DoD often requires hybrid Agile for compliance with acquisition milestones. Common evaluation subfactor under "Technical Approach" or "Management".
```

**Disambiguation**:

- vs **PROGRAM**: If named initiative (MCPP II) → program; if abstract methodology (Agile) → concept
- vs **TECHNOLOGY**: If specific tool (Jira) → technology; if abstract framework (Scrum) → concept
- vs **REQUIREMENT**: If obligation (shall use Agile) → requirement; if description of methodology → concept

---

### 3. EVENT

**Semantic Definition**: Milestones, deadlines, reviews, meetings, phase gates, site visits, oral presentations, and temporal markers.

**Decision-making value**: Events drive proposal timeline (Q&A deadline affects preparation schedule), resource allocation (oral presentation requires rehearsal time), and compliance gates (proposal due date is absolute). Missing an event deadline = rejection.

**Detection Patterns**:

- Absolute dates: "NLT 15 October 2025", "Due 2:00 PM EST on 1 November 2025"
- Relative timeframes: "within 30 days of award", "10 calendar days after receipt"
- Milestones: "Kickoff Meeting", "Critical Design Review", "Final Delivery"
- Review events: "Source Selection Evaluation Board (SSEB) review", "Site visit"
- Phase gates: "Phase 1 completion", "Go/No-Go decision point"

**Examples**:

✅ **Good**:

```
entity|Proposal Due Date|event|Proposals must be submitted by 2:00 PM EST on 1 November 2025.
```

✅ **Excellent**:

```
entity|Proposal Due Date: 1 November 2025 at 2:00 PM EST|event|ABSOLUTE deadline (FAR 52.212-1 applies - no mailbox rule, no grace period). Late submissions WILL NOT be considered (Section A Para 5). Delivery method: SAM.gov electronic submission only. Time zone: Eastern (verify if submitting from other zones). Recommend submit 24 hours early for technical issues. Q&A period closes 10 days prior (22 October 2025). This is a hard gate - miss it and proposal is rejected before evaluation.
```

**Disambiguation**:

- vs **REQUIREMENT**: If describes obligation timing (shall deliver within 30 days) → requirement; if describes discrete event (Kickoff on 15 Jan) → event
- vs **DELIVERABLE**: If work product (Status Report) → deliverable; if meeting to discuss it (Monthly Status Review) → event

---

### 4. TECHNOLOGY

**Semantic Definition**: Specific systems, platforms, software applications, hardware, tools, and technical products.

**Decision-making value**: Technology requirements drive teaming decisions (need partner with Oracle expertise), cost estimation (Microsoft licenses vs open source), and compliance verification (STIG-compliant systems). Knowing "must use IL5 Azure" affects infrastructure costs and security clearance requirements.

**Detection Patterns**:

- Software: "Microsoft SharePoint", "Jira", "Tableau", "Salesforce"
- Platforms: "Azure Government Cloud", "AWS GovCloud", "ServiceNow"
- Hardware: "Dell PowerEdge servers", "Cisco routers", "Fortinet firewalls"
- Systems: "Enterprise Resource Planning (ERP)", "Learning Management System (LMS)"
- Tools: "Selenium", "Jenkins", "GitLab", "Ansible"

**Examples**:

✅ **Good**:

```
entity|Microsoft Azure Government Cloud|technology|Cloud platform required for hosting CUI data.
```

✅ **Excellent**:

```
entity|Microsoft Azure Government IL5|technology|REQUIRED hosting platform (Section C Para 2.3). Impact Level 5 for CUI and Controlled Technical Information (CTI). Requires DoD SRG compliance, FedRAMP High authorization. Cost implications: ~30% premium over commercial Azure. Vendor lock-in considerations for proposal (demonstrate Azure expertise). Must integrate with existing Navy Marine Corps Intranet (NMCI). Likely evaluated under "Technical Approach - Security Architecture" subfactor. Teaming consideration: Need Azure IL5-certified partner or demonstrate existing credentials.
```

**Disambiguation**:

- vs **CONCEPT**: If specific product (Jira) → technology; if abstract methodology (Agile) → concept
- vs **EQUIPMENT**: If IT system (servers, software) → technology; if physical non-IT items (vehicles, tools) → equipment
- vs **DOCUMENT**: If standard/spec (NIST 800-171) → document; if tool implementing it (ACAS scanner) → technology

---

### 5. PERSON

**Semantic Definition**: Named individuals, roles, positions, points of contact (POCs), contracting officers, CORs, key personnel, and decision-makers.

**Decision-making value**: Persons identify who to contact (Q&A POC), who evaluates (Source Selection Authority affects proposal tone), and who are key decision influencers (Program Manager's priorities shape win themes). Understanding "CAPT Smith is PM with aviation background" affects technical depth in proposal.

**Detection Patterns**:

- Named individuals: "John Doe", "CAPT Jane Smith", "Dr. Robert Johnson"
- Roles: "Contracting Officer", "Contracting Officer's Representative (COR)", "Program Manager"
- Positions: "Source Selection Authority (SSA)", "Technical Evaluation Panel Chair"
- POCs: "Questions to: john.doe@navy.mil", "Primary POC for site visit"
- Key personnel: "Proposed Program Manager", "Lead Systems Engineer"

**Examples**:

✅ **Good**:

```
entity|John Doe, Contracting Officer|person|Primary POC for contractual questions. Email: john.doe@navy.mil
```

✅ **Excellent**:

```
entity|CAPT John Doe, Contracting Officer|person|Primary authority for this procurement (Section A). All contractual questions via email: john.doe@navy.mil (responses within 3 business days per Section A Para 8). Background research shows previous procurements emphasize cost control and past performance (FPIF contracts, heavy PP weighting). SSA is RADM Jane Smith (aviation background - emphasize flight safety, mission readiness in proposal). COR is Mike Johnson (technical SME - will evaluate solution architecture). Relationship mapping: Incumbent has strong relationship with PM office, propose innovation to differentiate.
```

**Disambiguation**:

- vs **ORGANIZATION**: If individual (CAPT Smith) → person; if office (Program Management Office) → organization
- vs **EVENT**: If person attends (PM attends review) → person; if meeting itself (Kickoff Meeting) → event

---

### 6. LOCATION

**Semantic Definition**: Geographic areas, performance sites, delivery locations, facilities, bases, and physical addresses.

**Decision-making value**: Locations affect cost (CONUS vs OCONUS pricing), security requirements (work on military base requires clearances), travel budgets, and local labor availability. Knowing "performance at 15 remote sites" affects staffing model and proposal logistics approach.

**Detection Patterns**:

- Cities/States: "San Diego, CA", "Washington, DC", "Norfolk, VA"
- Military bases: "Naval Air Station Patuxent River", "Fort Belvoir", "Camp Pendleton"
- Countries/regions: "CONUS", "OCONUS", "Germany", "Japan", "Middle East"
- Facilities: "Building 2187", "Hangar 5", "Data Center Alpha"
- Geographic areas: "National Capital Region (NCR)", "Pacific Theater"

**Examples**:

✅ **Good**:

```
entity|Naval Air Station Patuxent River, MD|location|Primary performance location for contract execution.
```

✅ **Excellent**:

```
entity|Naval Air Station Patuxent River, MD|location|PRIMARY performance location (80% of work, Section C Para 1.2). Requires Secret facility clearance, DBIDS access, Common Access Card (CAC). Government workspace provided (Building 2187, Room 315) - no offsite work allowed for CUI tasks. Local labor market: Limited cybersecurity talent, propose recruiting from Baltimore/DC (45 min commute) or remote with occasional on-site. Parking constraints - include shuttle costs. Site access delays common (security checks) - build buffer time into schedule. 20% work at remote locations (see separate entities). Cost implications: Higher wages for cleared personnel, relocation costs for key personnel, per diem for site visits.
```

**Disambiguation**:

- vs **ORGANIZATION**: If agency (NAVAIR) → organization; if place (Patuxent River) → location
- vs **EVENT**: If place (Conference Room A) → location; if meeting (Kickoff in Room A) → event

---

## Contracting Entities (5 types)

### 7. REQUIREMENT

**Semantic Definition**: Contractual obligations with criticality levels (MANDATORY "shall"/"must", RECOMMENDED "should", OPTIONAL "may").

**Decision-making value**: Requirements drive compliance (shall = must do or rejected), cost estimation (number of mandatory requirements affects LOE), and risk assessment (high requirement density = high compliance risk). Shipley compliance matrix depends on accurate requirement extraction with criticality levels.

**Detection Patterns**:

- MANDATORY obligations: "shall", "must", "is required to", "will"
- RECOMMENDED obligations: "should", "is encouraged to", "is expected to"
- OPTIONAL obligations: "may", "can", "is permitted to"
- Prohibition: "shall not", "must not", "is prohibited from"
- Conditional: "if...then shall", "when...must"

**Examples**:

✅ **Good**:

```
entity|Weekly Status Reports|requirement|Contractor shall submit weekly status reports to COR every Friday.
```

✅ **Excellent**:

```
entity|Weekly Status Reports Requirement|requirement|MANDATORY (SHALL) obligation per Section C Para 3.5.1. Contractor SHALL submit status reports to COR (mike.johnson@navy.mil) NLT COB Friday each week. Format: PPT (template in Attachment J-007), max 10 slides. Content: tasks completed, tasks planned, risks/issues, metrics. Deliverable relationship: Links to "Weekly Status Report" deliverable. Non-compliance: Negative past performance rating per Section H Para 2.3. Evaluation: Likely assessed under "Management Approach - Reporting and Communication" subfactor. Cost impact: ~4 hours/week PM time = ~$15K/year. Criticality: MEDIUM (administrative, but past performance consequence).
```

**Criticality Levels** (Shipley Methodology):

- **MANDATORY** (shall/must): Non-compliance = rejection or negative evaluation
- **RECOMMENDED** (should): Non-compliance = reduced score but not rejection
- **OPTIONAL** (may): Discretionary, no penalty for non-compliance

**Disambiguation**:

- vs **CLAUSE**: If FAR/DFARS reference (FAR 52.204-21) → clause; if work obligation → requirement
- vs **DELIVERABLE**: If tangible work product (Status Report document) → deliverable; if obligation to produce it (shall submit reports) → requirement
- vs **SUBMISSION_INSTRUCTION**: If proposal format (submit in 3 volumes) → submission_instruction; if contract performance obligation → requirement

---

### 8. CLAUSE

**Semantic Definition**: Federal Acquisition Regulation (FAR), Defense FAR Supplement (DFARS), and agency supplement clauses that impose regulatory requirements, flowdown obligations, and compliance frameworks.

**Decision-making value**: Clauses determine contract type implications (FAR 52.216-7 = cost overruns), flowdown to subcontractors (FAR 52.222-26 flows down, affects teaming), cost impacts (DFARS 252.204-7012 = $50K-$500K cybersecurity), and compliance gates (FAR 52.204-21 = contract ineligibility if non-compliant). Understanding clause operational context enables bid/no-bid decisions and accurate pricing.

**Detection Patterns**:

- FAR clauses: "FAR 52.xxx-xx" (e.g., "FAR 52.212-1", "FAR 52.204-21")
- DFARS clauses: "DFARS 252.xxx-xxxx" (e.g., "DFARS 252.204-7012")
- Agency supplements:
  - NMCARS: "NMCARS 5252.xxx-xxxx" (Navy)
  - AFFARS: "AFFARS 5352.xxx-xxxx" (Air Force)
  - GSAR: "GSAR 552.xxx-xx" (GSA)
  - And 20+ other agency supplements
- Clause titles: "Equal Opportunity clause", "Buy American Act"
- Incorporation by reference: "Clauses incorporated by reference per FAR 52.252-2"

**Examples**:

✅ **Good**:

```
entity|FAR 52.204-21|clause|Basic Safeguarding of Covered Defense Information. Requires NIST 800-171 implementation.
```

✅ **Excellent**:

```
entity|FAR 52.204-21 Basic Safeguarding of Covered Defense Information|clause|MANDATORY compliance (Section I incorporated). Requires implementation of NIST 800-171 Rev 2 (110 controls) for all Covered Defense Information (CDI) and Controlled Unclassified Information (CUI). Deliverables required: System Security Plan (SSP), Plan of Action & Milestones (POA&M), SPRS score upload (minimum 110 points). Non-compliance = contract INELIGIBILITY (cannot award). Cost impact: $50K-$500K depending on current posture (gap assessment needed). Timeline: SSP due within 30 days of award. Flowdown: YES - must flow to all subs handling CUI (affects teaming agreements). Evaluation: Likely assessed under "Technical Approach - Security" as discriminator (higher SPRS score = competitive advantage). Industry context: Many small businesses struggle with this - if compliant, emphasize in proposal. Related: DFARS 252.204-7012 (CMMC successor), FAR 52.204-25 (prohibition on Kaspersky).
```

**Common High-Impact Clauses** (consult §4.1 for full patterns):

- **FAR 52.204-21**: NIST 800-171 cybersecurity ($50K-$500K cost)
- **FAR 52.212-1**: Instructions to Offerors (absolute deadline, no mailbox rule)
- **FAR 52.222-26**: Equal Opportunity (flows to all subs)
- **DFARS 252.204-7012**: Safeguarding CUI (CMMC compliance)
- **DFARS 252.225-7021**: Trade Agreements (affects supply chain)

**Disambiguation**:

- vs **REQUIREMENT**: If regulatory reference pattern → clause; if work obligation without regulatory cite → requirement
- vs **DOCUMENT**: If clause citation (FAR 52.xxx) → clause; if standard/spec (MIL-STD-882) → document

---

### 9. SECTION

**Semantic Definition**: RFP structural sections following Uniform Contract Format (UCF Sections A-M) or semantic equivalents in non-UCF solicitations.

**Decision-making value**: Sections organize proposal response (Section L drives proposal outline), identify evaluation criteria location (Section M = scoring), and map compliance requirements (Section C = SOW to address). Understanding section structure enables efficient requirement extraction and proposal organization. UCF-aware but semantic-first detection means we recognize "Review Criteria" (non-UCF) as semantic equivalent to "Section M" (UCF).

**Detection Patterns**:

- **UCF format**: "Section A" through "Section M", lettered sections
- **Non-UCF formats**: "Part 1", "Volume II", "Review Criteria", "Submission Requirements"
- **Attachments**: "Attachment J-0005", "Annex A", "Exhibit 1"
- **Subsections**: "Section C Para 3.2.1", "Part II.B.3"
- **Cross-references**: "See Section L for instructions", "IAW Section C requirements"

**Uniform Contract Format (UCF) - Common Sections**:

- **Section A**: Solicitation/Contract Form (cover page, deadlines, type)
- **Section B**: Supplies/Services and Prices (CLINs, pricing tables)
- **Section C**: Statement of Work (SOW/PWS) - often references J attachments
- **Section H**: Special Contract Requirements (key personnel, security, SLAs)
- **Section I**: Contract Clauses (FAR/DFARS incorporation)
- **Section J**: List of Attachments (PWS, deliverables, sample documents)
- **Section L**: Instructions to Offerors (page limits, format, submission method)
- **Section M**: Evaluation Factors (scoring criteria, weights, methodology)

**Examples**:

✅ **Good**:

```
entity|Section L: Instructions to Offerors|section|Proposal submission requirements including page limits and format specifications.
```

✅ **Excellent**:

```
entity|Section L: Instructions, Conditions, and Notices to Offerors|section|Proposal submission instructions (UCF standard section). Contains: page limits (Technical 25 pages, Management 15 pages, Past Performance 10 pages), format requirements (12pt Times New Roman, 1-inch margins), volume organization (3 separate volumes), submission method (SAM.gov electronic only, no hard copies), and deadline (1 Nov 2025 2:00 PM EST). CRITICAL for proposal outline - maps to Section M evaluation factors. Key extractions needed: submission_instruction entities for each page limit, GUIDES relationships to evaluation_factor entities in Section M. Non-compliance with Section L = rejection before evaluation per FAR 52.212-1. Also contains Q&A process (due 22 Oct), site visit schedule (15 Oct), and incumbent data access (not provided - blind bid).
```

**Non-UCF Semantic Equivalents**:

- "Review Criteria" or "Evaluation Criteria" = Section M equivalent
- "Submission Requirements" or "Application Instructions" = Section L equivalent
- "Scope of Work" or "Statement of Objectives" = Section C equivalent
- "Terms and Conditions" = Section I equivalent

**Disambiguation**:

- vs **DOCUMENT**: If internal RFP structure (Section J) → section; if external reference (MIL-STD-882) → document
- vs **EVALUATION_FACTOR**: If structural container (Section M) → section; if scoring criterion within it (Factor 1) → evaluation_factor

---

### 10. DOCUMENT

**Semantic Definition**: Referenced external documents including specifications, standards, regulations, manuals, and authoritative sources that govern contract performance.

**Decision-making value**: Documents define compliance frameworks (NIST 800-171 = 110 security controls to implement), technical standards (MIL-STD-882 = safety program requirements), and regulatory obligations (DoD Manual 8140.03 = cybersecurity workforce certification). Understanding document requirements enables accurate cost estimation (implementing CMMC Level 2 = $100K-$500K) and capability assessment (do we have MIL-STD-1553 expertise or need partner?).

**Detection Patterns**:

- Military standards: "MIL-STD-882", "MIL-HDBK-217", "MIL-PRF-12345"
- NIST publications: "NIST 800-53", "NIST 800-171", "NIST Cybersecurity Framework"
- ISO standards: "ISO 9001", "ISO 27001", "ISO 20000"
- DoD directives: "DoD Instruction 8500.01", "DoD Manual 8140.03"
- Industry specs: "IEEE 802.11", "SAE J1939", "ASD-STAN-1234"
- Regulations: "ITAR", "EAR", "HIPAA", "FedRAMP"

**Examples**:

✅ **Good**:

```
entity|NIST Special Publication 800-171|document|Security requirements for protecting Controlled Unclassified Information (CUI) in nonfederal systems.
```

✅ **Excellent**:

```
entity|NIST SP 800-171 Rev 2: Protecting CUI in Nonfederal Systems|document|REQUIRED compliance framework (referenced in FAR 52.204-21, Section I). Defines 110 security controls across 14 families (Access Control, Awareness & Training, Audit, etc.). Current version: Rev 2 (Feb 2020), Rev 3 in draft (verify latest). Implementation: Must document in System Security Plan (SSP), track gaps in POA&M, self-assess via SPRS (score 0-110). Cost impact: Gap assessment ($10K-$50K), remediation ($50K-$500K depending on current state), annual assessment ($20K-$40K). Common gaps: multifactor authentication (3.5.3), incident response (3.6.x), media protection (3.8.x). Industry resources: NIST 800-171A (assessment procedures), DoD CMMC model (certification framework). Proposal strategy: If already compliant with high SPRS score (100+), emphasize as discriminator under "Security Approach" subfactor. If gaps exist, demonstrate clear POA&M with realistic timeline. Related standards: NIST 800-53 (federal systems), ISO 27001 (international), CMMC (DoD certification).
```

**Common High-Impact Documents**:

- **NIST 800-171**: CUI protection (110 controls, $50K-$500K implementation)
- **MIL-STD-882**: System safety (safety program requirements)
- **DoD 8140.03**: Cybersecurity workforce (certification requirements like CISSP, CEH)
- **CMMC**: Cybersecurity Maturity Model Certification (Level 1-3)
- **FedRAMP**: Cloud security authorization (High/Moderate/Low)

**Disambiguation**:

- vs **CLAUSE**: If regulatory clause citation (FAR 52.xxx) → clause; if standard/spec (NIST 800-171) → document
- vs **SECTION**: If external reference (MIL-STD-882) → document; if internal RFP structure (Section C) → section
- vs **TECHNOLOGY**: If standard/spec (NIST framework) → document; if tool implementing it (ACAS scanner) → technology

---

### 11. DELIVERABLE

**Semantic Definition**: Tangible contract work products, reports, plans, software, hardware, CDRLs (Contract Data Requirements List), and artifacts that must be delivered to the government.

**Decision-making value**: Deliverables drive cost estimation (each CDRL = labor hours + review time), schedule planning (deliverable dependencies affect critical path), and compliance tracking (missing deliverable = negative past performance). Understanding deliverable requirements enables accurate pricing and proposal win strategy (demonstrate past deliverable quality in past performance volume).

**Detection Patterns**:

- Reports: "Monthly Status Report", "Final Technical Report", "Lessons Learned"
- Plans: "System Security Plan", "Quality Assurance Plan", "Risk Management Plan"
- Software: "Source code deliverable", "Executable binaries", "API documentation"
- Hardware: "Prototype unit", "Test equipment", "Spare parts"
- CDRLs: "CDRL A001", "Data Item Description (DID)", "DD Form 1423"
- Submission language: "shall deliver", "shall provide", "shall submit"

**Examples**:

✅ **Good**:

```
entity|Monthly Status Report|deliverable|Required monthly report documenting project progress, risks, and metrics.
```

✅ **Excellent**:

```
entity|Monthly Status Report (CDRL A001)|deliverable|MANDATORY deliverable per Section C Para 3.5.2 and CDRL matrix (Attachment J-008). Format: PowerPoint, max 15 slides, template provided. Content: executive summary, tasks completed vs planned, schedule status (Gantt chart), risk register updates, cost/budget status, metrics dashboard (SLA compliance, defect rates). Submission: NLT 5th business day of each month to COR (mike.johnson@navy.mil) and PM (capt.smith@navy.mil). Frequency: Monthly throughout performance period (60 months = 60 deliverables). Acceptance criteria: COR review within 10 days, must address all template sections. Non-compliance: Counts against past performance rating (Section H Para 2.3). Cost impact: ~8 hours/month PM + 4 hours/month staff = ~$30K/year. Evaluation: Quality and comprehensiveness likely assessed under "Management Approach - Reporting" subfactor. Past performance evidence: Include sample monthly reports from similar contracts to demonstrate capability. Related requirements: Weekly Status Reports (separate requirement, different frequency), Quarterly Program Reviews (separate deliverable with different format).
```

**Common Deliverable Categories**:

- **Management deliverables**: Status reports, schedules, risk registers
- **Technical deliverables**: Designs, test reports, source code, documentation
- **Administrative deliverables**: Invoices, timesheets, security documentation
- **Hardware deliverables**: Equipment, prototypes, spare parts

**Disambiguation**:

- vs **REQUIREMENT**: If tangible work product (Status Report document) → deliverable; if obligation to produce it (shall submit reports) → requirement
- vs **DOCUMENT**: If contractor-produced (Status Report) → deliverable; if external reference (NIST 800-171) → document
- vs **EVENT**: If work product (Monthly Report) → deliverable; if meeting to discuss it (Monthly Review Meeting) → event

---

## Evaluation Entities (2 types)

### 12. EVALUATION_FACTOR

**Semantic Definition**: Scoring criteria, weighting schemes, subfactors, evaluation methodology, and rubrics used by government to assess proposal quality.

**Decision-making value**: Evaluation factors drive proposal resource allocation (40% weight factor gets 40% of effort), win theme development (factors reveal what government values), competitive strategy (adjectival vs numerical scoring affects differentiation approach), and compliance mapping (each factor requires specific evidence). Understanding evaluation methodology enables strategic proposal decisions - DoD adjectival scoring (Outstanding/Good/Acceptable) requires different approach than civilian numerical scoring (0-100 points).

**Detection Patterns**:

- Factor language: "Factor 1: Technical Approach", "Criterion 2: Past Performance"
- Scoring language: "will be evaluated", "will be assessed", "will be scored"
- Weight indicators: "40% weight", "most important factor", "equal weight"
- Methodology: "adjectival ratings", "point-based scoring", "color ratings (Blue/Green/Yellow/Red)"
- Subfactor structure: "Factor 1.1", "Subfactor A.2", "Element (a)"
- Rating scales: "Outstanding/Good/Acceptable/Marginal/Unacceptable", "Highly Advantageous/Advantageous/Not Advantageous"

**Examples**:

✅ **Good**:

```
entity|Factor 1: Technical Approach|evaluation_factor|Technical Approach factor worth 40% of total evaluation. Assesses proposed solution and risk mitigation.
```

✅ **Excellent**:

```
entity|Factor 1: Technical Approach (40% weight)|evaluation_factor|PRIMARY evaluation factor in Three-Factor Trinity structure (typical DoD pattern: Technical 30-50%, Management 20-30%, Past Performance 30-40%). Weight: 40% of total score (Section M Para 2.1). Methodology: Adjectival ratings (Outstanding/Good/Acceptable/Marginal/Unacceptable) per FAR 15.305. Subfactors: 1.1 Solution Architecture (25%), 1.2 Innovation and Technology Insertion (15%), 1.3 Risk Mitigation (35%), 1.4 Cybersecurity Approach (25%). Evaluates: HOW contractor will execute technical work, solution design quality, innovation potential, risk management, security architecture. Page limit: 25 pages per Section L Para 3.2 (GUIDES relationship). Common mistakes: Generic solutions (need specificity), inadequate risk mitigation (need concrete plans), weak cybersecurity (given FAR 52.204-21 mandate). Win strategy: Demonstrate deep understanding of Navy MBOS mission, propose innovative automation (AI/ML for predictive maintenance), detailed risk register with mitigation plans, emphasize existing Azure IL5 infrastructure (discriminator). Proposal mapping: Volume I Technical, organized by subfactor, heavy use of graphics (not counted against page limit per Section L), discriminators on pages 8-12, proof points from past performance. Related: Section L instructions (page limits), incumbent solution (innovation vs continuity tradeoff).
```

**Common DoD Evaluation Patterns** (consult §4.2 for full patterns):

- **Three-Factor Trinity**: Technical (30-50%), Management (20-30%), Past Performance (30-40%)
- **Four-Factor Structure**: Technical + Management + Past Performance + Price (varies)
- **LPTA (Lowest Price Technically Acceptable)**: Binary technical (pass/fail), price most important

**Scoring Methodologies**:

- **DoD Adjectival**: Outstanding/Good/Acceptable/Marginal/Unacceptable (color ratings sometimes)
- **Civilian Numerical**: 0-100 points, often with subfactor weights
- **Tradeoff vs LPTA**: Best value tradeoff (quality matters) vs LPTA (price driven)

**Disambiguation**:

- vs **SUBMISSION_INSTRUCTION**: If describes WHAT is scored (criteria, methodology) → evaluation_factor; if describes HOW to submit (format, limits) → submission_instruction
- Note: BOTH can appear in same sentence - create TWO entities if so
- vs **SECTION**: If structural container (Section M) → section; if scoring criterion within it (Factor 1) → evaluation_factor
- vs **REQUIREMENT**: If scoring criterion (will be evaluated on X) → evaluation_factor; if performance obligation (shall do X) → requirement

---

### 13. SUBMISSION_INSTRUCTION

**Semantic Definition**: Proposal format requirements, page limits, volume organization, font specifications, submission methods, and structural guidance for offerors.

**Decision-making value**: Submission instructions determine proposal outline (3-volume structure affects writing team organization), page limits (25 pages technical = strategic content decisions), formatting (12pt vs 10pt affects layout), and compliance gates (electronic-only submission = test upload process). Non-compliance with submission instructions = rejection before evaluation. Understanding these constraints enables proposal planning and resource allocation.

**Detection Patterns**:

- Page limits: "limited to 25 pages", "maximum 15 pages", "not to exceed 10 pages"
- Format specs: "12pt Times New Roman", "1-inch margins", "single-sided", "double-spaced"
- Volume organization: "submit in 3 separate volumes", "Volume I: Technical", "organize as follows"
- Submission method: "electronic submission via SAM.gov", "no hard copies", "email to"
- File format: "PDF only", "Microsoft Word", "native Excel for pricing"
- Exclusions: "graphics not counted against page limit", "cover page excluded", "table of contents does not count"

**Examples**:

✅ **Good**:

```
entity|Technical Volume Page Limit|submission_instruction|Technical proposal volume limited to 25 pages, 12pt font, 1-inch margins.
```

✅ **Excellent**:

```
entity|Technical Volume Page Limit: 25 pages maximum|submission_instruction|HARD LIMIT per Section L Para 3.2. Technical proposal volume (Volume I) SHALL NOT EXCEED 25 pages. Font: 12pt Times New Roman or Arial (no smaller). Margins: 1 inch all sides. Spacing: Single-spaced acceptable. Page size: 8.5x11 inches. EXCLUSIONS (do not count): cover page, table of contents, glossary/acronym list, graphics/figures/diagrams (unlimited), references page. Violation: Pages 26+ will NOT be evaluated (immediate content loss). Strategy: Use graphics heavily (not counted), prioritize discriminators on pages 1-15, relegate commodity content to appendices. Maps to: Factor 1 Technical Approach (GUIDES relationship). Comparison: Management volume 15 pages (tighter), Past Performance 10 pages. Industry norm: 25 pages for technical is GENEROUS (some RFPs limit to 15), allows deep technical detail. Proposal planning: Allocate pages by subfactor weight (Solution Architecture 25% = ~6 pages, Risk Mitigation 35% = ~9 pages). Best practice: Draft to 30 pages, cut to 22 for review buffer, graphics for complex topics.
```

**Common Submission Instructions**:

- **Page limits**: By volume (Technical 25p, Management 15p, Past Performance 10p, Cost separate)
- **Format**: Font (12pt standard, sometimes 10pt allowed), margins (1 inch standard), spacing
- **Organization**: Volume structure (separate volumes vs single document with sections)
- **Submission**: Method (SAM.gov electronic most common), timing (deadline absolute), format (PDF standard)
- **Exclusions**: What doesn't count toward page limits (graphics, TOC, cover, resumes)

**Disambiguation**:

- vs **EVALUATION_FACTOR**: If describes HOW to submit (format, limits) → submission_instruction; if describes WHAT is scored (criteria, methodology) → evaluation_factor
- Note: BOTH can appear together - e.g., "Technical Approach (25 pages, 40% weight)" → create TWO entities
- vs **REQUIREMENT**: If proposal format (submit in 3 volumes) → submission_instruction; if contract performance obligation → requirement
- vs **EVENT**: If format requirement (PDF format) → submission_instruction; if deadline (due 1 Nov) → event

---

## Strategic Entities (1 type)

### 14. STRATEGIC_THEME

**Semantic Definition**: Win themes, customer mission priorities, discriminators, hot buttons, proof points, and strategic messaging that differentiates winning proposals from compliant-but-generic responses.

**Decision-making value**: Strategic themes guide proposal messaging (what to emphasize), competitive positioning (how to differentiate from incumbent/competitors), capture strategy (which customer priorities to address), and win probability assessment (alignment with themes = higher win probability). Understanding strategic themes enables transformation from compliance exercise to persuasive business case.

**Detection Patterns**:

- Mission language: "mission critical", "mission assurance", "operational readiness"
- Priority indicators: "critical priority", "top priority", "emphasis on", "focus on"
- Value language: "maximize", "optimize", "enhance", "improve", "accelerate"
- Hot buttons: "budget constraints", "schedule acceleration", "risk reduction", "innovation"
- Customer pain points: "current challenges", "legacy system limitations", "transition risks"
- Discriminators: Unique capabilities, proprietary approaches, past performance proof points

**Examples**:

✅ **WRONG** (avoid this - too generic/motto):

```
entity|Always Forward, Always Ready|strategic_theme|Navy motto emphasizing readiness.
```

This is NOT a strategic theme - it's a motto/slogan. Strategic themes are ACTIONABLE intelligence about what the customer values and how to win.

✅ **Good**:

```
entity|Operational Readiness Priority|strategic_theme|Navy emphasizes maintaining 80%+ fleet readiness. Proposal should highlight rapid response, preventive maintenance, and minimizing downtime.
```

✅ **Excellent**:

```
entity|Fleet Readiness & Mission Availability as Primary Discriminator|strategic_theme|CRITICAL strategic theme extracted from Section C (appears 15x), Section M evaluation emphasis (Factor 1.3 "Mission Readiness" subfactor = 30% of Technical), and background research on NAVAIR PMA-290 priorities. Customer pain point: Current contractor achieves only 72% mission availability vs 85% requirement (incumbent weakness = opportunity). Customer values: Minimizing aircraft downtime, rapid fault diagnosis (goal <4 hours), predictive maintenance to prevent failures, 24/7 support readiness. Win strategy: (1) Emphasize past performance proof point - achieved 91% availability on similar NAVAIR contract (3x in PP volume), (2) Propose AI/ML predictive maintenance solution (innovation discriminator in Factor 1.2), (3) Commit to 4-hour fault diagnosis SLA (risk mitigation in Factor 1.3), (4) Highlight 24/7 NOC with veteran technicians (veteran hiring = additional win theme). Proposal integration: Feature prominently in executive summary (page 1), technical solution architecture (pages 5-8), management approach (on-call procedures pages 3-5), past performance (proof points pages 2,4,7). Graphics: Fleet availability trend chart showing 91% achievement, predictive maintenance workflow diagram, 24/7 support coverage map. Competitive positioning: Incumbent struggles with availability (emphasize innovation + continuity), other bidders lack aviation domain expertise (emphasize NAVAIR relationships + veteran workforce). Budget context: Customer willing to pay premium for higher availability (not LPTA, best value tradeoff per Section M).
```

**Strategic Theme Categories**:

- **Mission priorities**: Readiness, warfighter support, national security, safety
- **Performance priorities**: Quality, speed, efficiency, cost savings
- **Innovation priorities**: Modernization, automation, AI/ML, cloud migration
- **Risk priorities**: Cybersecurity, supply chain security, transition smoothness
- **Relationship priorities**: Veteran hiring, small business teaming, local presence, incumbent knowledge transfer

**How to Extract Strategic Themes**:

1. **Frequency analysis**: What concepts appear repeatedly in SOW?
2. **Evaluation factor clues**: What gets weighted heavily in Section M?
3. **Background research**: Agency mission statements, past awards, incumbent challenges
4. **Requirement patterns**: High-density requirements in specific areas = priority
5. **Language tone**: "Critical", "essential", "mandatory", "high priority" = strategic emphasis

**Disambiguation**:

- vs **REQUIREMENT**: If performance obligation (shall maintain 85% readiness) → requirement; if strategic messaging (emphasize readiness in proposal) → strategic_theme
- vs **EVALUATION_FACTOR**: If scoring criterion (Factor: Mission Readiness) → evaluation_factor; if strategic approach to addressing it → strategic_theme
- **CRITICAL**: Avoid extracting mottos, slogans, or mission statements as strategic themes. Extract ACTIONABLE intelligence about what customer values and how to win.

---

## Work Scope (1 type)

### 15. STATEMENT_OF_WORK

**Semantic Definition**: Narrative descriptions of work to be performed, performance requirements, scope boundaries, and deliverable expectations. Can appear as Performance Work Statement (PWS), Statement of Work (SOW), Statement of Objectives (SOO), or embedded in other sections.

**Decision-making value**: SOW content defines what must be done (drives cost estimation), how performance is measured (enables risk assessment), and what capabilities are needed (affects teaming strategy). Semantic-first detection means we extract SOW content regardless of whether it's in "Section C", an attachment, or embedded in evaluation factors. Understanding SOW scope enables accurate pricing and capability gap analysis.

**Detection Patterns**:

- Work descriptions: "The contractor shall perform...", "Services include...", "Scope of work encompasses..."
- Performance requirements: "Achieve 99.9% uptime", "Response time <4 hours", "Process 10,000 transactions/day"
- Scope narratives: Detailed descriptions of tasks, workflows, processes, technical approaches
- PWS/SOW/SOO sections: "Performance Work Statement", "Statement of Work", "Statement of Objectives"
- Task descriptions: "Task 1: System Maintenance", "CLIN 0001: Help Desk Support"

**Location-Agnostic Detection** (semantic-first):

- **UCF RFPs**: Usually Section C + Attachments in Section J
- **Non-UCF RFPs**: May be "Scope of Work", "Technical Requirements", "Performance Requirements"
- **Hybrid**: SOW split across multiple sections or embedded in evaluation factors
- **Simplified acquisitions**: SOW may be 2 paragraphs in email

**Examples**:

✅ **Good**:

```
entity|Help Desk Support Services|statement_of_work|Contractor shall provide Tier 1-3 help desk support for 5,000 users, 24/7 coverage, 4-hour response time.
```

✅ **Excellent**:

```
entity|Enterprise Help Desk Support (CLIN 0001 Base Period)|statement_of_work|Core service requirement per Section C Para 2.0 and Attachment J-003 PWS. Scope: Provide Tier 1, 2, and 3 technical support for 5,000 end users across 12 CONUS locations and 3 OCONUS sites. Coverage: 24/7/365 (including federal holidays). Channels: Phone (1-800 number), email (helpdesk@navy.mil), chat (ServiceNow portal), walk-in (Building 2187 hours 0800-1700 EST weekdays). Performance requirements: (1) Answer rate >90% within 60 seconds (Tier 1), (2) Resolution time <4 hours for Priority 1, <8 hours for Priority 2, <24 hours for Priority 3, (3) First-call resolution >70%, (4) Customer satisfaction >4.0/5.0 on monthly surveys. Technology: ServiceNow ITSM platform (government-furnished), integrate with Active Directory, SCCM, Remedy CMDB. Staffing: Minimum 15 FTEs (5 per shift for 24/7 coverage), all require Security+ certification (DoD 8140.03), Secret clearance for 5 FTEs handling classified incidents. Deliverables: Weekly incident reports (CDRL A002), monthly metrics dashboard (CDRL A003), quarterly process improvement recommendations (CDRL A004). Performance monitoring: SLA metrics tracked in ServiceNow, reviewed monthly by COR, tied to Award Fee (Section H Para 3.5 - up to 10% fee at risk). Cost drivers: 24/7 coverage (shift differential ~15%), clearances (cleared help desk analysts $75-95K vs $55-75K uncleared), OCONUS travel for on-site support (~$50K/year). Evaluation: Service delivery approach assessed under Factor 2: Management Approach (30% weight), past performance on similar help desk contracts critical (Factor 3: Past Performance 30% weight). Win strategy: Emphasize ServiceNow expertise (5+ similar implementations), veteran hiring (cleared workforce pool), follow-the-sun model for 24/7 (reduces labor costs vs pure shift work). Incumbent context: Current contractor struggles with after-hours response (opportunity to emphasize reliability). Related: CLIN 0002-0005 Option Years (same scope, potential volume growth to 7,500 users by Year 3).
```

**Common SOW Elements to Extract**:

- **Scope**: What work is included/excluded
- **Performance requirements**: SLAs, metrics, KPIs
- **Staffing**: Required FTEs, qualifications, clearances
- **Technology**: Systems to use, integration requirements
- **Locations**: Where work is performed
- **Deliverables**: What must be produced
- **Performance monitoring**: How quality is measured

**Disambiguation**:

- vs **REQUIREMENT**: If narrative work description → statement_of_work; if discrete obligation (shall deliver X) → requirement
- vs **SECTION**: If work content → statement_of_work; if structural label (Section C) → section
- Note: Can extract BOTH - "Section C Statement of Work" (section entity) + specific work content (statement_of_work entities)

---

## Programs & Equipment (2 types)

### 16. PROGRAM

**Semantic Definition**: Named major programs, initiatives, systems-of-systems, and large-scale efforts with proper noun identifiers.

**Decision-making value**: Program names identify customer context (MCPP II = Marine Corps IT), competitive landscape (incumbent program knowledge = advantage), relationship opportunities (program office contacts), and domain expertise requirements (Navy MBOS = maritime aviation expertise needed). Understanding program context enables targeted win themes and relationship mapping.

**Detection Patterns**:

- DoD programs: "MCPP II", "Navy MBOS", "NGEN", "DISA DECC", "Army WIN-T"
- Agency programs: "GSA Alliant 2", "NASA SEWP V", "VA T4NG"
- Initiative names: "Zero Trust Architecture Initiative", "Cloud First Strategy"
- System programs: "F-35 Joint Strike Fighter", "Aegis Combat System"
- Proper nouns: Capitalized multi-word names with specific identifiers

**Examples**:

✅ **Good**:

```
entity|MCPP II (Marine Corps Common Platform Program II)|program|Marine Corps enterprise IT modernization program providing common infrastructure and applications.
```

✅ **Excellent**:

```
entity|MCPP II (Marine Corps Common Platform Program II)|program|Marine Corps' $800M enterprise IT modernization program (contract ceiling). Predecessor: MCPP I ($400M, 2015-2020, incumbent: CACI). Scope: Provide common IT infrastructure, cloud services (Azure IL5), cybersecurity operations, application hosting, and end-user support for 185,000 Marines globally. Program office: MARCORSYSCOM G-6, PM: COL Johnson (program manager contact for relationship development). Strategic context: Transition from legacy NMCI (Navy Marine Corps Intranet) to independent Marine Corps infrastructure - political priority for Commandant. Key challenges: (1) NMCI separation (complex cutover, 18-month transition), (2) Cybersecurity (must achieve CMMC Level 2, currently Level 1), (3) OCONUS support (12 countries, 45 bases, limited bandwidth). Incumbent: CACI (strong past performance, incumbent advantage, relationship-heavy), competitors: Booz Allen, Leidos, General Dynamics IT. Win themes: Emphasize USMC culture (veteran workforce, Semper Fi values), NMCI separation expertise (past NMCI transitions), global support capability (OCONUS presence). Evaluation: Program knowledge likely discriminator under "Technical Approach - Understanding of Requirements" subfactor. Past performance: Must show similar large-scale IT program (185K+ users, OCONUS, DoD IL5). Related contracts: NGEN (Navy equivalent), DISA DECC (joint program, potential synergies). Market intelligence: Recompete expected 2028 (5-year base + 5 option years), potential for task order growth if budget increases. Proposal strategy: Feature MCPP I lessons learned (continuity), innovation for MCPP II (differentiation), strong program management (risk mitigation).
```

**Disambiguation**:

- vs **CONCEPT**: If proper noun for named program (MCPP II) → program; if abstract methodology (Agile) → concept
- vs **ORGANIZATION**: If program name (Navy MBOS) → program; if organization running it (NAVAIR PMA-290) → organization
- Note: May extract BOTH if context warrants - program as entity, organization as separate entity, linked by relationship

---

### 17. EQUIPMENT

**Semantic Definition**: Physical items, materials, tools, vehicles, assets, and tangible non-IT goods.

**Decision-making value**: Equipment requirements drive procurement costs (10 vehicles = $500K), logistics planning (shipping to OCONUS = $50K), maintenance budgets (tools require calibration), and teaming decisions (specialized equipment vendor partnerships). Understanding equipment needs enables accurate pricing and capability gap identification.

**Detection Patterns**:

- Vehicles: "Trucks", "Vans", "Aircraft", "Ships", "Forklifts"
- Tools: "Hand tools", "Calibration equipment", "Test instruments", "Power tools"
- Materials: "Spare parts", "Consumables", "Raw materials", "Fasteners"
- Physical assets: "Furniture", "Office equipment", "Safety gear", "Uniforms"
- Quantities: "10 vehicles", "500 units", "NSN 1234-56-789-0123" (National Stock Number)

**Examples**:

✅ **Good**:

```
entity|Government-Furnished Vehicles|equipment|10 trucks and 5 vans provided by government for contractor use.
```

✅ **Excellent**:

```
entity|Government-Furnished Equipment (GFE): 10 Trucks, 5 Vans|equipment|Contractor-operated vehicles per Section C Para 4.3 and Attachment J-012 GFE List. Inventory: 10 Ford F-250 trucks (4WD, extended cab, model years 2019-2022), 5 Ford Transit vans (cargo, high roof, 2020-2023). Condition: Maintained by government, contractor responsible for daily inspections and minor maintenance (oil changes, tire rotation). Usage: Transportation of equipment and personnel to 15 remote sites across 3-state region (CA, NV, AZ). Insurance: Government self-insured, contractor must report accidents within 24 hours. Fuel: Government credit card provided (Fleet Services Card), contractor tracks usage in ServiceNow. Maintenance: Government handles major repairs (>$500), contractor reports issues to Fleet Manager (john.doe@navy.mil). Storage: Vehicles garaged at Naval Base San Diego (Building 447, contractor has 24/7 access). Requirements: All drivers must have valid commercial driver's license (CDL Class B minimum), clean driving record, complete government driving training (annual). Cost impact: $0 vehicle acquisition (GFE saves ~$600K capital), but contractor responsible for driver salaries (~$60K/year each, need 15 drivers for coverage), insurance admin (~$10K/year), minor maintenance (~$15K/year total fleet). Risk: GFE can be unreliable (older vehicles, high mileage), recommend backup commercial rental budget ($20K contingency). Evaluation: Fleet management approach likely assessed under "Management Approach - Logistics" subfactor. Past performance: Demonstrate GFE management experience (similar truck fleets, government property accountability). Proposal: Include GFE tracking plan (ServiceNow inventory module), driver training program (safety emphasis), preventive maintenance schedule (minimize downtime). Related: Government-Furnished Property (GFP) clause FAR 52.245-1 (property accountability requirements, annual audits).
```

**Common Equipment Categories**:

- **Vehicles**: Trucks, vans, aircraft, ships, forklifts
- **Tools**: Hand tools, power tools, calibration equipment, test instruments
- **Materials**: Spare parts, consumables, raw materials
- **Facilities equipment**: Furniture, office equipment, safety gear
- **Government-Furnished Equipment (GFE)**: Items provided by government for contractor use

**Disambiguation**:

- vs **TECHNOLOGY**: If IT system (servers, software) → technology; if physical non-IT item (trucks, tools) → equipment
- vs **DELIVERABLE**: If contractor must provide (deliverable vehicles) → deliverable; if government provides for use (GFE vehicles) → equipment
- Note: Context matters - "10 laptops" could be technology (if IT focus) or equipment (if physical asset focus)

---

## Final Reminders

**Classification Priority**:

1. **Read semantic meaning**, not just keywords
2. **Check context**: Same word can be different types in different contexts
3. **Apply disambiguation rules** when multiple types possible
4. **Consult this reference** during STEP 2 for definitions and examples
5. **Remember decision-making value**: Each entity should enable strategic queries

**Quality Standards**:

- Every entity description ≥100 characters (target 150-250)
- Include operational context, not just definitions
- Add decision-making implications
- Note relationships to other entities

**Next Reference**: Relationship Patterns (how entities connect to form decision pathways)
