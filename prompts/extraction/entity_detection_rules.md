# Entity Detection Rules: Government Contracting Ontology

**Purpose**: Semantic-first entity extraction rules for federal RFPs  
**Philosophy**: Content determines entity type, NOT section labels  
**Usage**: Guide LLM during entity extraction in RAG-Anything processing

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

| Section       | Purpose                    | Common Entity Types                                  | Content Signals                                                                          |
| ------------- | -------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Section A** | Solicitation/Contract Form | section, organization, person, event                 | SF 1449, cover page, solicitation number, POCs, Q&A deadline                             |
| **Section B** | Supplies/Services & Prices | section, concept, program                            | CLIN/SLIN structure, pricing tables, line items, unit prices                             |
| **Section C** | Statement of Work          | section, statement_of_work, requirement, deliverable | "contractor shall", task descriptions, performance objectives, work scope                |
| **Section H** | Special Requirements       | section, requirement, person, location               | Security clearances, key personnel, organizational conflicts, facility requirements      |
| **Section I** | Contract Clauses           | section, clause                                      | FAR/DFARS citations, "52.###-##" patterns, "incorporated by reference"                   |
| **Section J** | Attachments                | section, document, statement_of_work                 | "Attachment", "Annex", "Exhibit", "J-####", referenced documents                         |
| **Section L** | Instructions to Offerors   | section, submission_instruction                      | Page limits, font requirements, "proposal shall", volume structure, submission deadlines |
| **Section M** | Evaluation Factors         | section, evaluation_factor                           | "will be evaluated", factor hierarchy, relative importance, adjectival ratings           |

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

Capture entity_name, entity_type, and description. Additional structured metadata (factor_id, relative_importance, subfactors) can be enriched during query-time operations.

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
  "entity_type": "EVALUATION_FACTOR",
  "description": "Evaluation of offeror's maintenance approach including staffing, philosophy, and transition",
  "factor_id": "M2",
  "relative_importance": "Most Important",
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
  "entity_type": "EVALUATION_FACTOR",
  "description": "Point-scored evaluation of technical solution quality",
  "factor_id": "TECH_MERIT",
  "evaluated_by_rating": "Point Score",
  "subfactors": [
    "Understanding (40pt)",
    "Solution Quality (35pt)",
    "Risk Mitigation (25pt)"
  ],
  "section_origin": "Selection Criteria"
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

Capture entity_name, entity_type, and description. Additional structured metadata (page_limits, format_requirements, deadlines) can be enriched during query-time operations.

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
  "entity_type": "SUBMISSION_INSTRUCTION",
  "guides_factor": "M1, M2, M3",
  "page_limits": "25 pages maximum",
  "format_requirements": "12pt Times New Roman, 1-inch margins, single-spaced",
  "delivery_method": "Electronic via email to Contracting.Officer@navy.mil",
  "deadline": "2025-03-15T14:00:00-05:00",
  "file_format": "PDF"
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

Capture entity_name, entity_type, and description. Requirement criticality (SHALL/SHOULD/MAY) and modal verb context can be enriched during query-time operations.

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
  "entity_type": "REQUIREMENT",
  "requirement_type": "FUNCTIONAL",
  "criticality_level": "MANDATORY",
  "priority_score": 100,
  "modal_verb": "shall",
  "subject": "Contractor",
  "section_origin": "Section C.3.1.2"
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
  "entity_type": "REQUIREMENT",
  "requirement_type": "INFORMATIONAL",
  "criticality_level": "INFORMATIONAL",
  "priority_score": 0,
  "modal_verb": "will",
  "subject": "Government",
  "section_origin": "Section C.3.2.1"
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
  "entity_type": "REQUIREMENT",
  "requirement_type": "PERFORMANCE",
  "criticality_level": "IMPORTANT",
  "priority_score": 75,
  "modal_verb": "should",
  "subject": "Contractor (implied)",
  "section_origin": "Section C.3.3.1"
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

Capture entity_name, entity_type, and description. Program acronyms and scope details can be enriched during query-time operations.

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
  "entity_type": "PROGRAM",
  "program_name": "Navy Mobile Bay Organic Support",
  "program_acronym": "Navy MBOS",
  "program_scope": "Organic ground support equipment maintenance at NAS locations",
  "parent_organization": "Navy",
  "section_origin": "Document Title, Section C.1.0"
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

Capture entity_name, entity_type, and description. Work statement location and task structure can be enriched during query-time operations.

### Examples from Real RFPs

"performance_standards": true | false (PWS-specific),
"prescription_level": "High (SOW)" | "Medium (PWS)" | "Low (SOO)"
}

```

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

````

**Extracted Entity**:

```json
{
  "entity_name": "Maintenance Services PWS",
  "entity_type": "STATEMENT_OF_WORK",
  "work_type": "PWS",
  "location": "Attachment J-0200000-18",
  "performance_standards": true,
  "prescription_level": "Medium (PWS)"
}
````

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
  "entity_type": "STATEMENT_OF_WORK",
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

Capture entity_name, entity_type, and description. Attachment numbering and parent section linkage can be inferred during relationship inference.

### Examples from Real RFPs

"prefix_pattern": "J-" | "Attachment " | "Annex " | "A-",
"content_type": "SOW" | "Specifications" | "Maps" | "Data" | "Sample" | "Clauses",
"parent_section": "Section J" (inferred from prefix),
"file_reference": "Equipment_List.pdf" (if separate file)
}

```

### Example from Navy MBOS

```

Section J: List of Attachments

The following documents are incorporated by reference:

J-0200000-18: Performance Work Statement (PWS)
J-0300000-12: Equipment List and Specifications
J-0400000-05: Site Layout and Facility Maps

````

**Extracted Entities** (3 annexes):

```json
[
  {
    "entity_name": "J-0200000-18 Performance Work Statement",
    "entity_type": "ANNEX",
    "original_numbering": "J-0200000-18",
    "prefix_pattern": "J-",
    "content_type": "SOW",
    "parent_section": "Section J"
  },
  {
    "entity_name": "J-0300000-12 Equipment List",
    "entity_type": "ANNEX",
    "original_numbering": "J-0300000-12",
    "prefix_pattern": "J-",
    "content_type": "Specifications",
    "parent_section": "Section J"
  },
  {
    "entity_name": "J-0400000-05 Site Layout Maps",
    "entity_type": "ANNEX",
    "original_numbering": "J-0400000-05",
    "prefix_pattern": "J-",
    "content_type": "Maps",
    "parent_section": "Section J"
  }
]
````

---

## Entity Type 7: CLAUSE

### Patterns (26+ Agency Supplements)

- **FAR**: `FAR 52.###-##` (Federal Acquisition Regulation)
- **DFARS**: `DFARS 252.###-####` (Defense FAR Supplement)
- **AFFARS**: `AFFARS 5352.###-##` (Air Force FAR Supplement)
- **NMCARS**: `NMCARS 5252.###-####` (Navy/Marine Corps)
- **HSAR**: `HSAR 3052.###-##` (Homeland Security)
- **Plus**: DOSAR, GSAM, VAAR, DEAR, NFS, AIDAR, CAR, DIAR, DOLAR, EDAR, EPAAR, FEHBAR, HHSAR, HUDAR, IAAR, JAR, LIFAR, NRCAR, SOFARS, TAR

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

Capture entity_name, entity_type, and description. Clause supplements (FAR/DFARS/AFFARS) and parent section clustering are handled during relationship inference.

### Examples from Real RFPs

"clause_number": "FAR 52.212-4" | "DFARS 252.204-7012",
"agency_supplement": "FAR" | "DFARS" | "AFFARS" | "NMCARS",
"clause_title": "Contract Terms and Conditions—Commercial Products and Commercial Services",
"section_attribution": "Section I" | "Section K",
"incorporation_method": "Full Text" | "By Reference",
"date": "JAN 2024" (clause effective date)
}

```

### Example from Navy RFP

```

Section I: Contract Clauses

52.212-4 Contract Terms and Conditions—Commercial Products
and Commercial Services (JAN 2024)

52.212-5 Contract Terms and Conditions Required To Implement
Statutes or Executive Orders—Commercial Products and
Commercial Services (JAN 2024)

252.204-7012 Safeguarding Covered Defense Information and
Cyber Incident Reporting (DEC 2019)

````

**Extracted Entities** (3 clauses):

```json
[
  {
    "entity_name": "FAR 52.212-4 Contract Terms and Conditions",
    "entity_type": "CLAUSE",
    "clause_number": "FAR 52.212-4",
    "agency_supplement": "FAR",
    "clause_title": "Contract Terms and Conditions—Commercial Products and Commercial Services",
    "section_attribution": "Section I",
    "date": "JAN 2024"
  },
  {
    "entity_name": "FAR 52.212-5 Required Statutes",
    "entity_type": "CLAUSE",
    "clause_number": "FAR 52.212-5",
    "agency_supplement": "FAR",
    "section_attribution": "Section I",
    "date": "JAN 2024"
  },
  {
    "entity_name": "DFARS 252.204-7012 Cybersecurity",
    "entity_type": "CLAUSE",
    "clause_number": "DFARS 252.204-7012",
    "agency_supplement": "DFARS",
    "section_attribution": "Section I",
    "date": "DEC 2019"
  }
]
````

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

Capture entity_name, entity_type, and description. Section semantic types and subsection structures can be enriched during relationship inference.

---

## Entity Type 9: STRATEGIC_THEME

### Type Classification

#### CUSTOMER_HOT_BUTTON

Agency priorities, pain points, mission pressures

**Signals**:

- "critical", "essential", "priority"
- "emphasize", "significant concern"
- "mission-critical", "high-priority"

**Examples**:

- "Readiness is the Navy's top priority"
- "Cybersecurity is a critical concern"
- "Mission availability must be maintained"

#### DISCRIMINATOR

Competitive advantages, unique capabilities

**Examples**:

- "Only offeror with on-site repair facility"
- "Proprietary predictive maintenance AI"
- "Incumbent knowledge of legacy systems"
- "Exclusive partnership with OEM"

#### PROOF_POINT

Evidence supporting competitive claims

**Examples**:

- "99.8% uptime on similar Navy contract"
- "CPARS rating: Exceptional (all categories)"
- "CMMI Level 3 certified organization"
- "150 certified technicians on staff"

#### WIN_THEME

Strategic messaging combining discriminator + proof + customer benefit

**Structure**: THEME + DISCRIMINATOR + PROOF POINT + CUSTOMER BENEFIT

**Example**:

```
THEME: "Mission Readiness Through Predictive Maintenance"
DISCRIMINATOR: "Proprietary AI-powered failure prediction"
PROOF POINT: "Reduced unscheduled downtime 40% on similar contract"
CUSTOMER BENEFIT: "Ensures aircraft availability for critical missions"
```

### Basic Attributes

Capture entity_name, entity_type, and description. Theme classification (hot button/discriminator/proof point) and competitive context are advanced analysis best performed during query-time.

---

## Entity Type 10-12: Standard Entities

### ORGANIZATION

Companies, agencies, departments, commands

**Examples**:

- "Naval Air Systems Command (NAVAIR)"
- "General Dynamics Information Technology"
- "Small Business Administration"

### CONCEPT

CLINs, budget items, technical concepts, definitions

**Examples**:

- "CLIN 0001 Base Year Services"
- "Total Small Business Set-Aside"
- "Agile Software Development"

### EVENT

Milestones, delivery dates, reviews, meetings

**Examples**:

- "Kickoff Meeting (30 days after award)"
- "Monthly Progress Review"
- "Final Delivery: September 30, 2026"

### TECHNOLOGY

Systems, tools, platforms, equipment

**Examples**:

- "SINCGARS Radio System"
- "AWS GovCloud Platform"
- "ServiceNow ITSM"

### PERSON

POCs, contracting officers, key personnel

**Examples**:

- "Contracting Officer: Jane Smith"
- "Program Manager: John Doe"
- "COR: Technical Officer Name"

### LOCATION

Performance locations, delivery sites, facilities

**Examples**:

- "Naval Air Station Pensacola, FL"
- "Pentagon, Arlington, VA"
- "CONUS (Continental United States)"

### DELIVERABLE

Contract deliverables, work products, reports

**Examples**:

- "Monthly Status Report"
- "System Design Document"
- "Deployed Application"

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
2. ✅ **Consistent naming**: "Navy MBOS" not "MBOS" in one place and "Navy Mobile Bay Organic Support" in another
3. ✅ **Metadata completeness**: Critical fields populated (factor_id, criticality_level, etc.)
4. ✅ **Subject validation**: "Government shall" ≠ MANDATORY requirement (it's INFORMATIONAL)
5. ✅ **Content over labels**: Don't trust "Section M" label; verify it contains evaluation criteria

---

**Last Updated**: January 2025 (Branch 004)  
**Version**: 2.0 (Enhanced from phase6_prompts.py with examples and clarity improvements)
