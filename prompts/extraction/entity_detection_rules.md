# Entity Detection Rules: Government Contracting Ontology

**Purpose**: Semantic-first entity extraction rules for federal RFPs  
**Philosophy**: Content determines entity type, NOT section labels  
**Usage**: Guide LLM during entity extraction in RAG-Anything processing  
**Last Updated**: November 26, 2025 (Branch 026 - Extraction Enhancements)

---

## ⚠️ PRIORITY DETECTION: Performance Metrics (QASP/PO-X Patterns)

**CRITICAL**: Performance Objectives and QASP metrics are commonly misclassified as requirements. Use these patterns to correctly identify `performance_metric` entities.

### Trigger Phrases (Extract as `performance_metric`)

| Pattern                                      | Example                             | Entity Type        |
| -------------------------------------------- | ----------------------------------- | ------------------ |
| Performance Objective (PO-X)                 | "PO-1: Escort Monitoring"           | performance_metric |
| Performance Threshold:                       | "Threshold: Zero (0) discrepancies" | performance_metric |
| Method of Surveillance:                      | "Surveillance: Periodic Inspection" | performance_metric |
| Acceptable Quality Level (AQL)               | "AQL: 98% accuracy"                 | performance_metric |
| QASP table entries                           | Any row from QASP table             | performance_metric |
| Numerical standards with timeframe           | "99.9% uptime per month"            | performance_metric |
| "No more than X per [timeframe]"             | "No more than 2 errors per week"    | performance_metric |
| "At least X% [metric]"                       | "At least 95% operational"          | performance_metric |
| "Zero (0) [violations/errors/discrepancies]" | "Zero security violations"          | performance_metric |

### NOT Performance Metrics (Extract as `requirement`)

| Pattern                      | Example                                 | Entity Type |
| ---------------------------- | --------------------------------------- | ----------- |
| Contractor shall [action]    | "Contractor shall clean daily"          | requirement |
| Contractor must [action]     | "Contractor must provide reports"       | requirement |
| Personnel shall [action]     | "Personnel shall complete training"     | requirement |
| Action verbs without metrics | "Maintain equipment", "Provide support" | requirement |

### Split Rule: Combined Sentences

When a sentence contains BOTH action AND metric:

**Input:** "Contractor shall provide 24/7 support with 99.9% uptime."

**Output:**

1. `requirement`: "24/7 Support Provision" (the action)
2. `performance_metric`: "99.9% Uptime Standard" (the measurement)
3. Relationship: requirement --MEASURED_BY--> performance_metric

---

## ⚠️ PRIORITY DETECTION: Strategic Themes (Shipley Capture Intelligence)

**Purpose**: Extract competitive intelligence from RFP language that reveals customer priorities and proposal positioning opportunities.

### Theme Type Classification

| ThemeType           | Definition                                | Detection Signals                                                      |
| ------------------- | ----------------------------------------- | ---------------------------------------------------------------------- |
| CUSTOMER_HOT_BUTTON | Government's explicit priority or concern | "emphasizes", "critical to", "paramount", "essential", heavy weighting |
| DISCRIMINATOR       | Key differentiator between competitors    | Unique requirements, specialized capabilities, innovation emphasis     |
| PROOF_POINT         | Evidence validating capability            | Past performance references, certifications, demonstrated experience   |
| WIN_THEME           | Overarching proposal positioning          | Alignment language, value proposition signals                          |

### Customer Hot Button Detection Patterns

**Explicit Emphasis Language:**

- "The Government places emphasis on..."
- "Critical to mission success..."
- "Of paramount importance..."
- "The Government's primary concern is..."
- "Essential to successful performance..."
- "Key to award decision..."

**Weighting Signals (>30% = hot button):**

- "Factor A (45%) - Most Important"
- "Technical Approach weighted twice as important as price"
- "Past Performance is significantly more important than cost"

**Repeated Themes:**

- Same capability mentioned 3+ times across different sections
- Capability appears in both PWS and evaluation factors
- Special emphasis sections (Section H) highlighting specific concerns

### Strategic Theme Examples

**From Evaluation Weighting:**

```
"Factor 1: Mission Readiness (50%) - Most Important"
```

→ Extract as: `strategic_theme` with `theme_type: "CUSTOMER_HOT_BUTTON"`
→ Name: "Mission Readiness Priority"

**From PWS Emphasis:**

```
"Cultural sensitivity in host nation operations is essential to contract success."
```

→ Extract as: `strategic_theme` with `theme_type: "CUSTOMER_HOT_BUTTON"`
→ Name: "Host Nation Cultural Sensitivity"

**From Past Performance Requirements:**

```
"Offerors must demonstrate relevant experience in austere environment operations."
```

→ Extract as: `strategic_theme` with `theme_type: "CUSTOMER_HOT_BUTTON"`  
→ Name: "Austere Environment Experience Requirement"

---

## Core Principle: Semantic-First Detection

Traditional approach (FRAGILE):

```
IF section_label == "Section L" → entity_type = "SECTION"
```

Our approach (ADAPTIVE):

```
IF contains_evaluation_criteria_language() → entity_type = "EVALUATION_FACTOR"
section_origin = detect_section(context)  # Could be L, M, or custom
```

**Why This Matters**: Federal RFPs vary wildly in structure. Task Orders may use "Selection Criteria" instead of "Section M". Content signals are universal; labels are not.

---

## Uniform Contract Format (UCF) Reference

### Standard Federal RFP Structure (FAR 15.210)

Federal solicitations use standard lettered sections A-M. **Note**: Extract entities based on CONTENT, not just section labels.

| Section       | Purpose                    | Common Entity Types                                                      | Content Signals                                                                          |
| ------------- | -------------------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------- |
| **Section A** | Solicitation/Contract Form | section, organization, person, event                                     | SF 1449, cover page, solicitation number, POCs, Q&A deadline                             |
| **Section B** | Supplies/Services & Prices | section, concept, program                                                | CLIN/SLIN structure, pricing tables, line items, unit prices                             |
| **Section C** | Statement of Work          | section, statement_of_work, requirement, deliverable, performance_metric | "contractor shall", task descriptions, performance objectives, QASP tables               |
| **Section H** | Special Requirements       | section, requirement, person, location                                   | Security clearances, key personnel, organizational conflicts, facility requirements      |
| **Section I** | Contract Clauses           | section, clause                                                          | FAR/DFARS citations, "52.###-##" patterns, "incorporated by reference"                   |
| **Section J** | Attachments                | section, document, statement_of_work                                     | "Attachment", "Annex", "Exhibit", "J-####", referenced documents                         |
| **Section L** | Instructions to Offerors   | section, submission_instruction                                          | Page limits, font requirements, "proposal shall", volume structure, submission deadlines |
| **Section M** | Evaluation Factors         | section, evaluation_factor, strategic_theme                              | "will be evaluated", factor hierarchy, relative importance, adjectival ratings           |

### Non-Standard Label Mapping

Task Orders and Fair Opportunity Requests often use different terminology:

| Non-Standard Label            | Standard Equivalent | Detection Strategy                       |
| ----------------------------- | ------------------- | ---------------------------------------- |
| Request for Quote (RFQ)       | Section A           | Cover page content signals               |
| Technical Requirements        | Section C           | Task descriptions, requirements language |
| Work Requirements             | Section C           | "shall perform" statements               |
| Statement of Objectives (SOO) | Section C           | Outcome-based language                   |
| Proposal Instructions         | Section L           | Page limits, format requirements         |
| Submission Requirements       | Section L           | Submission deadlines, volume structure   |
| Selection Criteria            | Section M           | Evaluation factor language               |
| Evaluation Methodology        | Section M           | Adjectival ratings, scoring methodology  |
| Source Selection Plan         | Section M           | Tradeoff approach, best value language   |

### Agency-Specific Variations

Different agencies use custom terminology:

| Agency Term                      | Standard Equivalent | Entity Type Guidance                 |
| -------------------------------- | ------------------- | ------------------------------------ |
| Scope of Work                    | Section C           | Extract as statement_of_work         |
| Performance Work Statement (PWS) | Section C           | Extract as statement_of_work         |
| Special Contract Requirements    | Section H           | Extract requirements as requirement  |
| Applicable Clauses               | Section I           | Extract individual clauses as clause |
| Required Certifications          | Section K           | Extract as requirement (compliance)  |

### Content-Based Detection Rules

When section labels are ambiguous or missing:

**EVALUATION_FACTOR Detection Signals:**

- "will be evaluated", "evaluation factor", "most important"
- "adjectival rating", "source selection", "significantly more important"
- Factor numbering (M1, M2, M2.1), Point scores (100 points total)

**SUBMISSION_INSTRUCTION Detection Signals:**

- "page limit", "font size", "proposal shall", "volume structure"
- "submit by", "electronic submission", "format requirements"
- "Times New Roman 12pt", "1-inch margins"

**CLAUSE Detection Signals:**

- FAR/DFARS/AFFARS/NMCARS patterns: "52.###-##", "252.###-####"
- "incorporated by reference", "clause title", "full text"

**STATEMENT_OF_WORK Detection Signals:**

- Task descriptions, performance objectives, deliverables lists
- "contractor shall perform", Task numbering (1.0, 1.1, 1.1.1)
- "SOW", "PWS", "SOO" labels

### Mixed Content Handling

Some sections contain multiple entity types:

**Example 1: Section M with Embedded Instructions**

```
Section M: Evaluation Factors

Factor 1: Technical Approach (Most Important)
[Evaluation criteria...]
The Technical Volume shall be limited to 25 pages...
```

**Extract**:

- EVALUATION_FACTOR: "Factor 1: Technical Approach"
- SUBMISSION_INSTRUCTION: "Technical Volume page limit"
- Link them: SUBMISSION_INSTRUCTION --EVALUATED_BY--> EVALUATION_FACTOR

**Example 2: Section C as Attachment**

```
Section C: Description/Specifications/Data
See Attachment J-0200000-18 for Performance Work Statement.
```

**Extract**:

- SECTION: "Section C"
- DOCUMENT: "Attachment J-0200000-18"
- STATEMENT_OF_WORK: "Performance Work Statement"
- Link them: SECTION --REFERENCES--> DOCUMENT --CONTAINS--> STATEMENT_OF_WORK

### Section Attribution for Ambiguous Entities

**Clause Attribution:**

- All FAR/DFARS clauses → Section I (Contract Clauses)
- Representations/certifications (52.2##-## series) → Section K

**Annex Attribution (Prefix-Based):**

- `J-######` → Section J
- `Attachment #` → Section J
- `Annex ##` → Section J or standalone
- Letter prefix → Corresponding section (A-#### → Section A)

**Requirement Attribution:**

- Default to Section C (SOW)
- Unless labeled "Section H" → Special Requirements
- Or part of Section I/K → Clauses/Certifications

---

## Entity Type 1: EVALUATION_FACTOR

### Content Signals

- "will be evaluated"
- "evaluation factor"
- "adjectival rating"
- "scoring methodology"
- "most important"
- "significantly more important than price"

### Structural Patterns

- **Hierarchy**: Factor 1 → Subfactor 1.1 → Subfactor 1.1.1
- **Numbering**: M1, M2, M2.1, M2.1.1
- **Ratings**: "Excellent", "Good", "Acceptable", "Marginal", "Unacceptable"

### Context Clues

- Near relative importance statements
- Point scores (100 points total)
- Adjectival ratings
- Tradeoff methodology descriptions

### Location

- **Primary**: Section M (Evaluation Factors for Award)
- **Alternate**: Section L (sometimes embedded)
- **Non-standard**: "Selection Criteria", "Source Selection Plan"

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (factor_id, relative_importance, subfactors). Additional structured metadata can be enriched during query-time operations.

### Examples from Real RFPs

**Example 1: Navy MBOS (Standard Format)**

```
Factor 2: Maintenance Approach (Most Important)

The Government will evaluate the offeror's understanding of and approach
to performing organic maintenance requirements. This factor has three
subfactors:

2.1 Staffing Plan (Significantly More Important)
2.2 Maintenance Philosophy
2.3 Transition Plan
```

**Extracted Entity**:

```json
{
  "entity_name": "Factor 2: Maintenance Approach",
  "entity_type": "evaluation_factor",
  "importance": "Most Important",
  "subfactors": [
    "M2.1 Staffing Plan",
    "M2.2 Maintenance Philosophy",
    "M2.3 Transition Plan"
  ]
}
```

**Example 2: Task Order (Non-Standard Format)**

```
Selection Criteria:

Technical Merit (100 points)
- Demonstrated understanding of mission requirements (40 points)
- Quality of proposed solution (35 points)
- Risk mitigation approach (25 points)
```

**Extracted Entity**:

```json
{
  "entity_name": "Technical Merit",
  "entity_type": "evaluation_factor",
  "weight": "100 points",
  "subfactors": [
    "Understanding (40pt)",
    "Solution Quality (35pt)",
    "Risk Mitigation (25pt)"
  ]
}
```

---

## Entity Type 2: SUBMISSION_INSTRUCTION

### Content Signals

- "page limit"
- "font size", "margins"
- "format requirements"
- "volume structure"
- "technical proposal shall address"
- "management volume limited to"

### Structural Patterns

- Maps to evaluation factors (e.g., "Technical Volume addresses Factor 2")
- Submission deadlines
- Electronic vs. hard copy requirements
- Proposal organization (Volume I, Volume II)

### Context Clues

- Near format specifications
- PDF/Word file requirements
- Email addresses for submission
- Due dates/times

### Location

- **Primary**: Section L (Instructions to Offerors)
- **Alternate**: Embedded within Section M (NON-STANDARD but common!)
- **Non-standard**: "Proposal Instructions", "Submission Requirements"

### CRITICAL: Embedded Instructions Pattern

**Problem**: Some RFPs embed submission instructions WITHIN evaluation factor descriptions.

**Example**:

```
Factor 1: Technical Approach (Most Important)

[Evaluation criteria text...]

The Technical Volume shall be limited to 25 pages, 12pt Times New Roman,
1-inch margins, single-spaced. The offeror shall address each subfactor
in separate sections.
```

**Solution**: Create SEPARATE `SUBMISSION_INSTRUCTION` entity and link to `EVALUATION_FACTOR`:

```
SUBMISSION_INSTRUCTION "Technical Volume Format" → GUIDES → EVALUATION_FACTOR "Factor 1"
```

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (page_limits, format_requirements, deadlines). Additional structured metadata can be enriched during query-time operations.

### Examples from Real RFPs

**Example 1: Standard Section L**

```
L.3.1 Technical Volume

The Technical Volume shall not exceed 25 pages and shall address
Evaluation Factors 1-3. Use 12-point Times New Roman font, 1-inch
margins, single-spaced. Submit as a single PDF file via email to
Contracting.Officer@navy.mil by March 15, 2025, 2:00 PM EST.
```

**Extracted Entity**:

```json
{
  "entity_name": "Technical Volume Submission Requirements",
  "entity_type": "submission_instruction",
  "page_limit": "25 pages maximum",
  "format_reqs": "12pt Times New Roman, 1-inch margins, single-spaced, PDF format",
  "volume": "Technical Volume"
}
```

**Example 2: Embedded in Section M**

```
Factor 2: Management Approach (Significantly More Important)

[Evaluation criteria...]

Offerors shall limit the Management Volume to 15 pages. Include
organizational chart, resumes for key personnel, and project schedule.
```

**Extracted Entities** (TWO):

1. `EVALUATION_FACTOR` "Factor 2: Management Approach"
2. `SUBMISSION_INSTRUCTION` "Management Volume Format" (linked via GUIDES relationship)

---

## Entity Type 3: REQUIREMENT (with Classification)

### Criticality Detection (MANDATORY Analysis)

**CRITICAL RULE**: Check the SUBJECT of the sentence!

#### MANDATORY (Priority Score: 100)

- **Pattern**: "Contractor shall", "Offeror must", "The offeror shall"
- **Subject**: Contractor/Offeror (external party)
- **Examples**:
  - ✅ "Contractor shall provide 24/7 help desk support"
  - ✅ "Offeror must submit staffing plan"
  - ✅ "The contractor shall maintain 99.9% uptime"

#### INFORMATIONAL (Priority Score: 0)

- **Pattern**: "Government will", "Agency shall", "The Government shall"
- **Subject**: Government/Agency (NOT a requirement for contractor!)
- **Examples**:
  - ❌ "Government will provide office space" (NOT a requirement)
  - ❌ "Agency shall conduct site visits" (NOT a requirement)
  - ❌ "The Government will pay within 30 days" (NOT a requirement)

#### IMPORTANT (Priority Score: 75)

- **Pattern**: "should", "encouraged to", "preferred", "desirable"
- **Subject**: Contractor/Offeror
- **Examples**:
  - "Contractor should use Agile methodology"
  - "Offeror is encouraged to propose innovative solutions"
  - "Preferred: ISO 27001 certification"

#### OPTIONAL (Priority Score: 25)

- **Pattern**: "may", "can", "has the option to"
- **Subject**: Contractor/Offeror
- **Examples**:
  - "Contractor may use subcontractors"
  - "Offeror can propose alternative approaches"

### Type Classification (Content-Based)

#### FUNCTIONAL

- **Pattern**: "provide", "deliver", "perform", "execute" + service/product
- **Examples**:
  - "Contractor shall provide 24/7 help desk support"
  - "Perform preventive maintenance on all equipment"
  - "Deliver monthly status reports"

#### PERFORMANCE

- **Pattern**: SLA language, metrics, measurable outcomes
- **Examples**:
  - "99.9% system uptime"
  - "Response within 24 hours of incident report"
  - "Process 1000 transactions per hour"
  - "First-time fix rate ≥ 95%"

#### SECURITY

- **Pattern**: NIST references, FedRAMP, clearance levels, cybersecurity
- **Examples**:
  - "FedRAMP Moderate authorization required"
  - "Personnel require Secret clearance"
  - "Implement NIST 800-53 controls"
  - "Comply with CMMC Level 2"

#### TECHNICAL

- **Pattern**: Technology stack, platforms, software versions, infrastructure
- **Examples**:
  - "Deploy on AWS GovCloud"
  - "Use Java 11 or higher"
  - "PostgreSQL database required"
  - "Kubernetes orchestration"

#### INTERFACE

- **Pattern**: Integration points, data exchange, APIs, system connections
- **Examples**:
  - "Integrate with agency ERP system"
  - "Support HTTPS/TLS 1.3"
  - "RESTful API with OAuth 2.0"
  - "FHIR-compliant health data exchange"

#### MANAGEMENT

- **Pattern**: Reporting, governance, oversight, project management
- **Examples**:
  - "Submit monthly status reports"
  - "Use Agile/Scrum methodology"
  - "PMI-certified Project Manager required"
  - "Weekly progress meetings with COR"

#### DESIGN

- **Pattern**: Standards compliance, architectural mandates, design constraints
- **Examples**:
  - "Section 508 accessibility compliance"
  - "Follow agency branding guidelines"
  - "Microservices architecture"
  - "Responsive web design"

#### QUALITY

- **Pattern**: QA processes, testing, verification, validation
- **Examples**:
  - "Automated test coverage ≥ 80%"
  - "ISO 9001 certification"
  - "Peer code review required"
  - "User acceptance testing (UAT)"

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (criticality, modal_verb, labor_drivers). Requirement criticality (SHALL/SHOULD/MAY) and modal verb context can be enriched during query-time operations.

### Examples from Real RFPs

**Example 1: MANDATORY FUNCTIONAL**

```
3.1.2 Help Desk Support

The Contractor shall provide Tier 1 and Tier 2 help desk support
24 hours per day, 7 days per week, including Federal holidays.
```

**Extracted Entity**:

```json
{
  "entity_name": "24/7 Help Desk Support Requirement",
  "entity_type": "requirement",
  "req_type": "FUNCTIONAL",
  "criticality": "MANDATORY",
  "modal_verb": "shall",
  "labor_drivers": ["24/7 coverage", "Tier 1 support", "Tier 2 support"],
  "material_needs": []
}
```

**Example 2: INFORMATIONAL (NOT A REQUIREMENT)**

```
3.2.1 Government-Furnished Equipment

The Government will provide office space and desktop computers for
contractor personnel working on-site.
```

**Extracted Entity**:

```json
{
  "entity_name": "Government-Furnished Office Space",
  "entity_type": "concept"
}
```

**Example 3: IMPORTANT PERFORMANCE**

```
3.3.1 System Availability

The system should maintain 99.9% uptime during business hours
(6 AM - 6 PM EST, Monday-Friday).
```

**Extracted Entity**:

```json
{
  "entity_name": "99.9% Uptime SLA",
  "entity_type": "requirement",
  "req_type": "PERFORMANCE",
  "criticality": "IMPORTANT",
  "modal_verb": "should",
  "labor_drivers": [],
  "material_needs": []
}
```

---

## Entity Type 4: PROGRAM

### Semantic Purpose

Top-level organizational container representing a major acquisition program, initiative, or system.

### Content Signals

- Program names in document title
- Major acquisition titles
- Portfolio-level initiatives
- System names

### Naming Patterns

- **Full names**: "Marine Corps Prepositioning Program II", "Navy Mobile Bay Organic Support"
- **Acronyms**: "MCPP II", "Navy MBOS", "AFLMI"
- **System names**: "F-35 Lightning II Program", "Joint Strike Fighter Program"

### Hierarchical Position

**Top-level container** that CONTAINS:

- Requirements
- Deliverables
- Technologies
- Statement of Work
- Sections

### Relationship Patterns

```
SECTION (C) → CONTAINS → PROGRAM (section describes program)
PROGRAM → CONTAINS → REQUIREMENT (program has requirements)
PROGRAM → CONTAINS → TECHNOLOGY (program uses technologies)
PROGRAM → CONTAINS → DELIVERABLE (program expects deliverables)
```

### Detection Criteria

- Appears in document title
- Section C header or SOW introduction
- Capitalized or emphasized as primary subject
- Referenced throughout document as umbrella

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (acronym, scope). Program acronyms and scope details can be enriched during query-time operations.

### Example from Navy MBOS RFP

```
Title: "Navy Mobile Bay Organic Support (Navy MBOS) Contract"

Section C: Statement of Work

1.0 BACKGROUND

The Navy Mobile Bay Organic Support (Navy MBOS) program provides organic
maintenance for ground support equipment at Naval Air Station (NAS) locations...
```

**Extracted Entity**:

```json
{
  "entity_name": "Navy Mobile Bay Organic Support",
  "entity_type": "program"
}
```

---

## Entity Type 5: STATEMENT_OF_WORK

### CRITICAL: Semantic Equivalence

The entity type `STATEMENT_OF_WORK` represents **ANY** of these three formats:

#### SOW (Statement of Work)

- **Style**: Prescriptive, detailed
- **Focus**: **HOW** to perform work
- **Example**: "Contractor shall mow grass weekly using rotary mower with 3-inch blade height"

#### PWS (Performance Work Statement)

- **Style**: Performance-based
- **Focus**: **WHAT** outcomes required (contractor chooses HOW)
- **Example**: "Contractor shall maintain grounds to standard X (50% green coverage, no weeds >6 inches)"

#### SOO (Statement of Objectives)

- **Style**: Objective-based
- **Focus**: **WHY** / objectives (contractor creates PWS from SOO)
- **Example**: "Objective: Provide aesthetically pleasing grounds consistent with Navy image"

### Content Signals

- Task descriptions
- Performance objectives
- Deliverables
- Work scope
- Outcomes

### Structure

- Often hierarchical:
  - **SOW**: Task 1 → Subtask 1.1 → Subtask 1.1.1
  - **PWS**: Objective 1 → Performance Standard 1.1 → Metric 1.1.1
  - **SOO**: Goal 1 → Objective 1.1 → Success Criterion 1.1.1

### Identifiers (any of these)

- "PWS", "Performance Work Statement"
- "SOW", "Statement of Work"
- "SOO", "Statement of Objectives"
- "Section C" (typical location)
- "Attachment X - PWS"

### Location

- **Primary**: Section C (Description/Specs/Data)
- **Alternate**: Separate attachment (J-#### PWS)
- **Embedded**: Within Section C as subsection

### Detection: CONTENT-BASED

**Do NOT rely on labels alone!** Focus on:

- Work scope/tasks/objectives/deliverables
- Task hierarchy and numbering
- Performance standards and metrics
- Deliverable schedules

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (work_type, location, performance_standards). Work statement location and task structure can be enriched during query-time operations.

### Examples from Real RFPs

**Example 1: PWS (Performance-Based)**

```
Attachment J-0200000-18: Performance Work Statement

3.1 MAINTENANCE SERVICES

The Contractor shall perform scheduled and unscheduled maintenance
on all GSE to achieve:

- 95% equipment availability
- 98% first-time fix rate
- Mean time between failures (MTBF) ≥ 500 hours

Performance shall be measured monthly against these standards.
```

**Extracted Entity**:

```json
{
  "entity_name": "Maintenance Services PWS",
  "entity_type": "statement_of_work",
  "work_type": "PWS",
  "location": "Attachment J-0200000-18",
  "performance_standards": true,
  "prescription_level": "Medium (PWS)"
}
```

**Example 2: SOW (Prescriptive)**

```
Section C: Statement of Work

Task 1: Software Development

1.1 The Contractor shall use Agile/Scrum methodology with 2-week sprints.
1.2 The Contractor shall conduct daily stand-up meetings at 9:00 AM.
1.3 The Contractor shall use Jira for task tracking and GitHub for version control.
```

**Extracted Entity**:

```json
{
  "entity_name": "Software Development SOW",
  "entity_type": "statement_of_work",
  "work_type": "SOW",
  "location": "Section C",
  "hierarchical_structure": true,
  "prescription_level": "High (SOW)"
}
```

---

## Entity Type 6: ANNEX / ATTACHMENT

### Naming Patterns

- `J-######`: "J-0200000-18 Equipment List"
- `Attachment #`: "Attachment 5 - Site Map"
- `Annex ##`: "Annex 17 Transportation"
- `Appendix X`: "Appendix C - Data Dictionary"
- `X-######`: "A-1234567 Specifications"

### Link to Parent Section

Based on naming prefix patterns:

- `J-####` → Section J (List of Attachments)
- `Attachment #` → Usually Section J
- `Annex ##` → Could be Section J or standalone
- Prefix letter → Corresponding section (A-#### → Section A)

### Content Determines Subtype

An annex/attachment can contain:

- SOW/PWS (work statement)
- Technical specifications
- Maps and diagrams
- Data sheets
- Sample documents
- Contract clauses

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (prefix_pattern, content_type, parent_section). Attachment numbering and parent section linkage can be inferred during relationship inference.

### Examples from Real RFPs

**Example from Navy MBOS**

```
Section J: List of Attachments

The following documents are incorporated by reference:

J-0200000-18: Performance Work Statement (PWS)
J-0300000-12: Equipment List and Specifications
J-0400000-05: Site Layout and Facility Maps
```

**Extracted Entities** (3 annexes):

```json
[
  {
    "entity_name": "J-0200000-18 Performance Work Statement",
    "entity_type": "document",
    "prefix_pattern": "J-",
    "content_type": "SOW",
    "parent_section": "Section J"
  },
  {
    "entity_name": "J-0300000-12 Equipment List",
    "entity_type": "document",
    "prefix_pattern": "J-",
    "content_type": "Specifications",
    "parent_section": "Section J"
  },
  {
    "entity_name": "J-0400000-05 Site Layout Maps",
    "entity_type": "document",
    "prefix_pattern": "J-",
    "content_type": "Maps",
    "parent_section": "Section J"
  }
]
```

---

## Entity Type 7: CLAUSE

### Patterns (26+ Agency Supplements)

**Major Federal Agencies**:

- **FAR**: `FAR 52.###-##` (Federal Acquisition Regulation - Base regulation)
- **DFARS**: `DFARS 252.###-####` (Defense FAR Supplement)
- **AFFARS**: `AFFARS 5352.###-##` (Air Force FAR Supplement)
- **NMCARS**: `NMCARS 5252.###-####` (Navy/Marine Corps FAR Supplement)

**Other Agency Supplements** (22+ additional):

- **HSAR**: Homeland Security
- **DOSAR**: State Department
- **GSAM**: General Services Administration
- **VAAR**: Veterans Affairs
- **DEAR**: Energy
- **NFS**: NASA
- **AIDAR**: USAID
- **CAR**: Commerce
- **DIAR**: USDA
- **DOLAR**: Labor
- **EDAR**: Education
- **EPAAR**: EPA
- **FEHBAR**: Health/Human Services (Federal Employees)
- **HHSAR**: Health/Human Services
- **HUDAR**: HUD
- **IAAR**: Interior
- **JAR**: Justice
- **LIFAR**: Broadcasting Board of Governors
- **NRCAR**: Nuclear Regulatory Commission
- **SOFARS**: State/Broadcasting
- **TAR**: Treasury
- **Plus others**: Check clause number prefix pattern

### Agency Supplement Recognition

Extract the supplement name from the clause number:

- `FAR 52.212-4` → supplement = "FAR"
- `DFARS 252.204-7012` → supplement = "DFARS"
- `AFFARS 5352.201-9001` → supplement = "AFFARS"

### Should Cluster by Parent Section

Even if clauses are scattered throughout the document, link them to logical parent:

- FAR 52.### clauses → Section I (Contract Clauses)
- Representation clauses → Section K (Reps and Certs)

### Group Similar Clauses

Even if not adjacent in document:

- All FAR 52.2##-# (Supplies/Services) together
- All FAR 52.3##-# (Delivery) together
- All security clauses together

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (clause_number, regulation, date). Clause supplements (FAR/DFARS/AFFARS) and parent section clustering are handled during relationship inference.

### Examples from Real RFPs

**Example from Navy RFP**

```
Section I: Contract Clauses

52.212-4 Contract Terms and Conditions—Commercial Products
and Commercial Services (JAN 2024)

52.212-5 Contract Terms and Conditions Required To Implement
Statutes or Executive Orders—Commercial Products and
Commercial Services (JAN 2024)

252.204-7012 Safeguarding Covered Defense Information and
Cyber Incident Reporting (DEC 2019)
```

**Extracted Entities** (3 clauses):

```json
[
  {
    "entity_name": "FAR 52.212-4 Contract Terms and Conditions",
    "entity_type": "clause",
    "clause_number": "FAR 52.212-4",
    "regulation": "FAR",
    "section_attribution": "Section I",
    "incorporation_method": "Full Text",
    "date": "JAN 2024"
  },
  {
    "entity_name": "FAR 52.212-5 Required Statutes",
    "entity_type": "clause",
    "clause_number": "FAR 52.212-5",
    "regulation": "FAR",
    "section_attribution": "Section I",
    "incorporation_method": "Full Text",
    "date": "JAN 2024"
  },
  {
    "entity_name": "DFARS 252.204-7012 Cybersecurity",
    "entity_type": "clause",
    "clause_number": "DFARS 252.204-7012",
    "regulation": "DFARS",
    "section_attribution": "Section I",
    "incorporation_method": "Full Text",
    "date": "DEC 2019"
  }
]
```

---

## Entity Type 8: SECTION

### Extract BOTH Structural AND Semantic

**Structural Label**: What the document calls it  
**Semantic Type**: What it actually IS

### Standard UCF (Uniform Contract Format)

| Section | Structural Label | Semantic Type           |
| ------- | ---------------- | ----------------------- |
| A       | Section A        | SOLICITATION_FORM       |
| B       | Section B        | SUPPLIES_SERVICES       |
| C       | Section C        | DESCRIPTION_SPECS       |
| H       | Section H        | SPECIAL_REQUIREMENTS    |
| I       | Section I        | CONTRACT_CLAUSES        |
| J       | Section J        | ATTACHMENTS             |
| K       | Section K        | REPRESENTATIONS         |
| L       | Section L        | SUBMISSION_INSTRUCTIONS |
| M       | Section M        | EVALUATION_CRITERIA     |

### Non-Standard Mapping

Many RFPs use different labels:

| Non-Standard Label       | Maps To   | Semantic Type           |
| ------------------------ | --------- | ----------------------- |
| "Selection Criteria"     | Section M | EVALUATION_CRITERIA     |
| "Technical Requirements" | Section C | DESCRIPTION_SPECS       |
| "Proposal Instructions"  | Section L | SUBMISSION_INSTRUCTIONS |
| "Request for Quote"      | Section A | SOLICITATION_FORM       |
| "Statement of Work"      | Section C | DESCRIPTION_SPECS       |

### Note Mixed Content

Some sections contain multiple content types:

**Example**: Section M that includes both evaluation criteria AND submission instructions

```json
{
  "structural_label": "Section M",
  "semantic_type": "EVALUATION_CRITERIA",
  "also_contains": ["SUBMISSION_INSTRUCTION"],
  "confidence": 0.95
}
```

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (structural_label, semantic_type). Section semantic types and subsection structures can be enriched during relationship inference.

---

## Entity Type 9: STRATEGIC_THEME

**Purpose**: Extract competitive intelligence from RFP language that reveals customer priorities, evaluation emphasis, and proposal positioning opportunities. Based on Shipley Capture Management methodology.

### Type Classification

#### CUSTOMER_HOT_BUTTON

**Definition**: Agency priorities, pain points, or mission pressures explicitly or implicitly emphasized in the RFP.

**Detection Signals**:

- "critical", "essential", "priority", "paramount"
- "emphasize", "significant concern", "of utmost importance"
- "mission-critical", "high-priority", "key to success"
- "The Government places emphasis on..."
- Evaluation factors weighted >30%
- Repeated mention across multiple sections

**Real-World Examples**:

- "Readiness is the Navy's top priority" → Hot button: operational readiness
- "Cybersecurity is a critical concern for this acquisition" → Hot button: security posture
- "Mission availability must be maintained at all times" → Hot button: uptime/reliability
- "Past performance demonstrating success in austere environments is essential" → Hot button: relevant experience
- "Cultural sensitivity in host nation operations is paramount" → Hot button: cultural competence

**Extraction Pattern**:

```json
{
  "entity_name": "Austere Environment Operations Experience",
  "entity_type": "strategic_theme",
  "description": "Past performance demonstrating successful operations in austere/expeditionary environments is emphasized as essential to source selection.",
  "theme_type": "CUSTOMER_HOT_BUTTON"
}
```

#### DISCRIMINATOR

**Definition**: Competitive advantages, unique capabilities, or differentiators that could set one offeror apart.

**Detection Signals**:

- Specialized requirements (unique certifications, rare capabilities)
- Technology or methodology preferences in RFP
- References to innovation or modernization
- Incumbent-specific knowledge requirements
- OEM partnerships or exclusive access requirements

**Real-World Examples**:

- "Only offeror with on-site repair facility"
- "Proprietary predictive maintenance capability"
- "Incumbent knowledge of legacy systems required"
- "Exclusive OEM partnership for parts supply"
- "Contractor must have existing FedRAMP High authorization"

#### PROOF_POINT

**Definition**: Evidence that validates capability claims or demonstrates past performance.

**Detection Signals**:

- Specific past performance requirements
- CPARS rating references
- Certification requirements (CMMI, ISO, etc.)
- Quantified experience (years, contract values, staff size)
- Similar contract references

**Real-World Examples**:

- "99.8% uptime demonstrated on similar Navy contracts"
- "CPARS rating: Exceptional in all categories required"
- "CMMI Level 3 certification required"
- "Minimum 5 years experience in base operations support"
- "Three similar contracts valued at $50M+ in last 5 years"

#### WIN_THEME

**Definition**: Overarching strategic messaging combining discriminator + proof + customer benefit. Typically synthesized during capture, but RFP language may reveal positioning opportunities.

**Structure**: THEME = DISCRIMINATOR + PROOF POINT → CUSTOMER BENEFIT

**Example Synthesis**:

```
THEME: "Mission Readiness Through Predictive Maintenance"
DISCRIMINATOR: "Proprietary AI-powered failure prediction"
PROOF POINT: "Reduced unscheduled downtime 40% on similar contract"
CUSTOMER BENEFIT: "Ensures aircraft availability for critical missions"
```

### Strategic Theme from Evaluation Factor Weighting

**When evaluation factors reveal priorities, extract as strategic_theme:**

**RFP Text:**

> "Factor 1: Mission Support Capability (45%) - Most Important. The Government will evaluate the offeror's ability to provide uninterrupted mission support..."

**Extract BOTH entities:**

```json
[
  {
    "entity_name": "Factor 1 Mission Support Capability",
    "entity_type": "evaluation_factor",
    "description": "Factor 1: Mission Support Capability (45%) - Most Important.",
    "weight": "45%",
    "importance": "Most Important"
  },
  {
    "entity_name": "Mission Support Capability as Top Priority",
    "entity_type": "strategic_theme",
    "description": "Mission Support Capability is weighted 45% and rated Most Important, indicating this is the Government's primary concern for this acquisition.",
    "theme_type": "CUSTOMER_HOT_BUTTON"
  }
]
```

### Basic Attributes

- `entity_name`: Descriptive name of the theme
- `entity_type`: strategic_theme
- `description`: Full context from RFP showing the emphasis
- `theme_type`: CUSTOMER_HOT_BUTTON, DISCRIMINATOR, PROOF_POINT, or WIN_THEME

---

## Entity Type 10: DELIVERABLE

### Content Signals

- **CDRL References**: "CDRL A001", "CDRL 6022", "DD Form 1423"
- **Report Types**: "Monthly Status Report", "Quarterly Review", "Final Report"
- **Documentation**: "System Design Document", "Technical Manual", "User Guide"
- **Work Products**: "Deployed Application", "Training Materials", "Test Results"
- **Submission Language**: "shall submit", "shall deliver", "shall provide"

### Structural Patterns

- CDRL numbering: A001, B012, 6022
- Series references: "8000 Series deliverables"
- Explicit labels: "Deliverable 1.2", "Work Product 3"

### Context Clues

- Near submission schedules ("due 5th business day")
- Listed in "List of Deliverables" sections
- Referenced in SOW tasks ("Task 1.2 deliverable")
- DD Form 1423 mentions (official CDRL form)

### Location

- **Primary**: Section J attachments (CDRL lists)
- **Alternate**: Section C SOW (embedded in tasks)
- **Embedded**: Requirements text ("contractor shall deliver...")

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (cdrl_id, due_date, format). CDRL identifiers and due dates can be enriched during query-time operations.

---

## Entity Type 11: DOCUMENT

### Content Signals

- **Attachment References**: "Attachment 1", "J-0200000-18", "Annex A", "Exhibit B"
- **Referenced Documents**: "See Section X for...", "Incorporated by reference"
- **Standards**: "MIL-STD-882E", "ISO 9001", "NIST SP 800-53"
- **Forms**: "SF 1449", "DD Form 254", "Standard Form 30"
- **Prior Documents**: "Previous contract N00024-18-C-1234"

### Structural Patterns

- Attachment numbering: J-####, Attachment #, Annex ##
- Standard identifiers: MIL-STD-###, ISO ####, NIST SP ###-##
- Form numbers: SF ###, DD ###

### Context Clues

- "See Attachment X for details"
- "Incorporated by reference"
- "Listed in Section J"
- "Reference documents include..."

### Location

- **Primary**: Section J (List of Attachments)
- **Alternate**: Throughout RFP (referenced documents)
- **Embedded**: Requirements citing standards

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (document_number, reference_location). Document numbers and reference locations can be enriched during query-time operations.

---

## Entity Type 12: CONCEPT

### Content Signals

- **Budget/Pricing**: "CLIN 0001", "Base Year Services", "Option Period 2"
- **Technical Concepts**: "Agile Development", "DevSecOps", "Zero Trust Architecture"
- **Business Concepts**: "Small Business Set-Aside", "Joint Venture", "Teaming Arrangement"
- **Processes**: "Change Control Process", "Risk Management", "Quality Assurance"
- **Abstract Ideas**: "Readiness", "Sustainability", "Interoperability"
- **Definitions**: Terms being defined in glossary or text

### Structural Patterns

- CLIN/SLIN numbering: "CLIN 0001", "SLIN 0001AA"
- Abstract nouns (no physical form)
- Process names ending in "-ing" or "Process"
- Methodologies and frameworks

### Context Clues

- Near definitions ("means", "defined as", "refers to")
- In glossary sections
- Pricing tables (CLINs)
- Conceptual discussions (not physical items)

### Detection: Differentiation

**NOT concept if**:

- Physical item with model number → equipment
- Scheduled activity → event
- Named military unit → organization
- Software with version → technology

**IS concept if**:

- Abstract idea or process
- Business term or methodology
- CLIN/budget line item
- Term being defined

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (concept_category, definition). Abstract nature can be described during query-time operations.

---

## Entity Type 13: EQUIPMENT

### Content Signals

- **Model Numbers**: "M1A1 Tank", "Concorde RG-24", "6200 Tennant Floor Scrubber"
- **Military Equipment**: "TAMCN numbers", "End Item codes", "NSN (National Stock Number)"
- **Physical Assets**: "Generator Set", "HVAC System", "Forklift", "Test Equipment"
- **Vehicles**: "HMMWV", "MRAP", "Aircraft", "Ships"
- **Hardware**: "Servers", "Workstations", "Network Equipment"

### Structural Patterns

- Model numbers with alphanumerics: "M1A1", "RG-24", "6200"
- TAMCN format: 5-character codes
- NSN format: ####-##-###-####
- Make/model format: "Manufacturer ModelNumber"

### Context Clues

- Near maintenance language
- In equipment lists or inventories
- Quantities specified ("100 each", "12 units")
- Physical descriptions (weight, dimensions, specifications)

### Detection: Equipment vs Technology

**EQUIPMENT**: Physical item you can touch

- "M1A1 Tank" → equipment
- "Generator Set" → equipment
- "Server Hardware" → equipment

**TECHNOLOGY**: Software, system, or platform

- "Windows Server 2022" → technology
- "ServiceNow Platform" → technology
- "SINCGARS Radio System" → technology (if referring to system concept)

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (model_number, manufacturer, specifications). Model numbers and specifications can be enriched during query-time operations.

---

## Entity Type 14: TECHNOLOGY

### Content Signals

- **Software**: "Windows Server 2022", "Oracle Database 19c", "Python 3.11"
- **Platforms**: "AWS GovCloud", "Azure Government", "ServiceNow"
- **Systems**: "SINCGARS Radio System", "GCSS-MC", "TBMCS"
- **Protocols**: "TLS 1.3", "HTTPS", "SFTP"
- **Standards**: "IPv6", "802.11ac", "Ethernet"

### Structural Patterns

- Version numbers: "Windows 10", "Python 3.11", "TLS 1.3"
- Acronyms for systems: "GCSS-MC", "TBMCS", "DEERS"
- Platform names: "AWS", "Azure", "ServiceNow"

### Context Clues

- Near technical requirements
- In system architecture descriptions
- Software stack discussions
- IT infrastructure sections

### Detection: Technology vs Equipment

**TECHNOLOGY**: Software, logical system, protocol

- "AWS GovCloud" → technology
- "SINCGARS System" → technology (system concept)
- "Windows Server" → technology

**EQUIPMENT**: Physical hardware

- "Dell Server" → equipment
- "SINCGARS Radio Unit" → equipment (physical radio)
- "Network Switch" → equipment

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (version, platform, vendor). Versions and platforms can be enriched during query-time operations.

---

## Entity Type 15: ORGANIZATION

### Content Signals

- **Companies**: "General Dynamics IT", "Lockheed Martin", "Small Business Name"
- **Agencies**: "Department of Defense", "GSA", "DLA"
- **Military Units**: "Marine Corps", "NAVAIR", "SPAWAR", "I MEF"
- **Commands**: "Naval Air Systems Command", "Marine Corps Logistics Command"
- **Departments**: "Contracting Office", "Program Management Office"

### Structural Patterns

- Acronyms: "NAVAIR", "SPAWAR", "GSA", "DLA"
- "Inc.", "LLC", "Corp." suffixes
- Military designations: "I MEF", "3rd Battalion"
- Command structures

### Context Clues

- Near organizational roles
- In past performance descriptions
- Teaming arrangements
- Points of contact affiliations

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (acronym, full_name, org_type). Acronyms and full names can be enriched during query-time operations.

---

## Entity Type 16: EVENT

### Content Signals

- **Milestones**: "Kickoff Meeting", "Final Delivery", "Contract Award"
- **Scheduled Activities**: "Monthly Review", "Quarterly Assessment", "Annual Update"
- **Deadlines**: "Q&A Deadline: March 15, 2025", "Proposal Due Date"
- **Periods**: "Base Period", "Option Year 2", "Ship Availability"
- **Processes with Timing**: "CAL Signing", "Annual Inspection"

### Structural Patterns

- Dates: "March 15, 2025", "30 days after award"
- Recurring patterns: "Monthly", "Quarterly", "Annual"
- Event + timing: "Review (15 days)", "Meeting (30 days after award)"

### Context Clues

- Calendar dates
- Time-bound language ("within X days", "by date")
- Scheduling sections
- Milestone charts

### Detection: Event vs Concept

**EVENT**: Scheduled, time-bound activity

- "Monthly Review" → event (scheduled)
- "Kickoff Meeting" → event (scheduled)
- "Annual Update" → event (recurring)

**CONCEPT**: Process without schedule

- "Review Process" → concept (methodology)
- "Meeting Protocol" → concept (procedure)
- "Update Procedure" → concept (process)

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (event_date, frequency, milestone_type). Dates and frequencies can be enriched during query-time operations.

---

## Entity Type 17: PERSON and LOCATION

### PERSON: Content Signals

- **Names**: "Jane Smith", "John Doe", "CDR Michael Johnson"
- **Titles**: "Contracting Officer", "Program Manager", "COR", "Technical POC"
- **Roles**: "Key Personnel", "Project Lead", "Security Officer"
- **Contact Info**: Near email, phone, office

### PERSON: Context Clues

- "Contact: Name"
- "POC: Title/Name"
- Signature blocks
- Key personnel sections

### LOCATION: Content Signals

- **Bases**: "Naval Air Station Pensacola", "Camp Lejeune", "Fort Bragg"
- **Cities/States**: "Arlington, VA", "San Diego, CA"
- **Facilities**: "Building 123", "Warehouse 5", "Depot Maintenance"
- **Geographic Areas**: "CONUS", "OCONUS", "PACOM AOR"
- **Countries**: "Host Nation", "Japan", "Germany"

### LOCATION: Context Clues

- Near performance location language
- Delivery addresses
- Site visit information
- Geographic scoping

### Basic Attributes

Capture entity_name, entity_type, and type-specific metadata (title, role, contact_info for PERSON; address, facility_type for LOCATION). Contact details and addresses can be enriched during query-time operations.

---

## Summary: Priority Order for Entity Extraction

When processing an RFP, prioritize extraction in this order:

1. **PROGRAM** - Identify top-level program FIRST (provides context for all others)
2. **SECTION** - Map document structure (provides location context)
3. **EVALUATION_FACTOR** - Critical for proposal planning
4. **SUBMISSION_INSTRUCTION** - Determines proposal structure
5. **REQUIREMENT** - Core work obligations
6. **STATEMENT_OF_WORK** - Work scope definition
7. **ANNEX** - Supporting documents and references
8. **CLAUSE** - Regulatory compliance requirements
9. **STRATEGIC_THEME** - Competitive intelligence
10. **Standard Entities** - Organizations, concepts, events, etc.

**Why This Order Matters**: Early entities provide context for later entities. Knowing the PROGRAM helps classify requirements. Knowing SECTIONS helps attribute entities to locations.

---

## Quality Checks

Before finalizing entity extraction, validate:

1. ✅ **No orphan entities**: Every entity should link to at least one other entity
2. ✅ **Consistent naming (Canonicalization)**:
   - Normalize names to their canonical form.
   - Example: If "ISS" and "Installation Support Services (ISS)" both appear, use "Installation Support Services (ISS)" for BOTH.
   - Do NOT create two separate entities for the same concept.
3. ✅ **Metadata completeness**: Critical fields populated (factor_id, criticality_level, etc.)
4. ✅ **Subject validation**: "Government shall" ≠ MANDATORY requirement (it's INFORMATIONAL)
5. ✅ **Content over labels**: Don't trust "Section M" label; verify it contains evaluation criteria

---

## Entity Extraction Quality Validation

Before finalizing entity extraction for a document chunk:

### 1. Required Field Validation

- ✅ `entity_name`: Present and descriptive (not generic)
- ✅ `entity_type`: Valid type from 17-type ontology
- ✅ `section_origin`: Traceable location reference (optional)
- ✅ Type-specific metadata: Appropriate fields for entity type (importance, criticality, etc.)

### 2. Format Validation

- ✅ Dates: ISO 8601 format (YYYY-MM-DDTHH:MM:SS±HH:MM)
- ✅ Numbers: Numeric values (not strings for scores/counts)
- ✅ Booleans: true/false (not "yes"/"no" strings)
- ✅ Arrays: Properly formatted JSON arrays

### 3. Cross-Reference Integrity

- ✅ EVALUATION_FACTOR.factor_id → SUBMISSION_INSTRUCTION.guides_factor
- ✅ REQUIREMENT → EVALUATION_FACTOR relationship exists
- ✅ ANNEX prefix → Parent SECTION linkage valid
- ✅ CLAUSE → SECTION attribution consistent

### 4. Enum Validation

- ✅ criticality_level ∈ {MANDATORY, IMPORTANT, OPTIONAL, INFORMATIONAL}
- ✅ theme_type ∈ {CUSTOMER_HOT_BUTTON, DISCRIMINATOR, PROOF_POINT, WIN_THEME}
- ✅ modal_verb ∈ {shall, should, may, must, will, can, encouraged}
- ✅ work_type ∈ {SOW, PWS, SOO}
- ✅ agency_supplement ∈ {FAR, DFARS, AFFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, AIDAR, CAR, DIAR, DOLAR, EDAR, EPAAR, FEHBAR, HHSAR, HUDAR, IAAR, JAR, LIFAR, NRCAR, SOFARS, TAR} (26+ total)

### 5. Consistency Checks

- ✅ Same entity referenced with consistent naming across chunks
- ✅ Section numbering follows document hierarchy
- ✅ Requirement IDs unique within document
- ✅ Modal verb matches criticality level (shall=MANDATORY, should=IMPORTANT, may=OPTIONAL)

---

**Last Updated**: January 2025 (Branch 010 - Added quality validation rules)  
**Version**: 3.1 (Enhanced with metadata validation and agency supplement enumeration)
