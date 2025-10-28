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
- Numbered/lettered factors (Factor 1, Factor 2.1)
- Weight percentages (40%, 30%, 20%)
- Adjectival ratings (Outstanding, Good, Acceptable, Poor)
- Subfactors or criteria listed hierarchically
- Comparison language ("more important than", "most weight")

**SUBMISSION_INSTRUCTION Detection Signals:**

- "shall submit", "volume limited to", "page limit", "font size"
- Format requirements (Arial 12pt, 1-inch margins)
- Deadline language ("due by", "must arrive by", "cutoff")
- Volume structure ("Technical Volume", "Management Proposal", "Cost Volume")
- Submission method ("via email", "uploaded to SAM.gov", "physical copies")

**REQUIREMENT Detection Signals:**

- "shall", "must", "will", "is required" (mandatory)
- "should" (recommended)
- "may", "can" (optional)
- Obligation language ("contractor is responsible for")
- Performance standards ("99.9% uptime", "within 24 hours")

**STATEMENT_OF_WORK Detection Signals:**

- "contractor shall perform", "work includes"
- Task descriptions with verbs (design, develop, test, operate)
- Objective statements ("ensure", "provide", "maintain")
- Appears in Section C, Section J attachments, or Section H
- References to milestones, phases, deliverables

**DELIVERABLE Detection Signals:**

- CDRL identifiers (A001, B002, etc.)
- "report", "document", "plan", "analysis"
- Dates/deadlines attached ("due quarterly", "by end of Phase 1")
- Receives approval/review language ("shall be reviewed", "requires approval")

**CLAUSE Detection Signals:**

- FAR/DFARS/Agency supplement citations ("52.###-##", "252.###-####")
- "incorporated by reference"
- "flow down to subcontractors"
- Regulatory language (FAR cite format)

**STRATEGIC_THEME Detection Signals:**

- Repeated emphasis across sections (multiple factor descriptions)
- Win theme language ("critical to success", "key differentiator")
- Business priority language ("most important", "primary focus")
- Customer priority statements ("mission critical", "top priority")

---

## The 17 Entity Types: Semantic Definitions

### CORE ENTITIES (Foundation Types)

#### 1. ORGANIZATION
Contractors, agencies, government departments, teaming partners, subcontractors.
- **Signal**: Company name, agency acronym, team entity
- **Example**: NAVAIR, Booz Allen Hamilton, SPAWAR

#### 2. PERSON
Key personnel, contracting officers, points of contact, program managers, government representatives.
- **Signal**: Individual name, role title, organization affiliation
- **Example**: "John Doe, CAPT (PM, NAVAIR)"

#### 3. LOCATION
Geographic sites, performance locations, facilities, prepositioning sites, operational areas.
- **Signal**: City, base name, facility address, geographic region
- **Example**: "Patuxent River, MD", "Naval Station Norfolk"

#### 4. CONCEPT
Abstract ideas, methodologies, frameworks, technical approaches, CLIN structures, budget models.
- **Signal**: Methodology name, framework name, procedural pattern, abstract structure
- **Example**: "Agile Development", "DevSecOps", "CLIN structure"

#### 5. EVENT
Milestones, deadlines, reviews, phase gates, site visits, oral presentations, temporal markers.
- **Signal**: Date, deadline, milestone name, phase gate
- **Example**: "Proposal due March 15, 2025", "Q&A deadline", "Kick-off meeting"

#### 6. TECHNOLOGY
Hardware, software, tools, systems, platforms, development environments, infrastructure.
- **Signal**: Product name, tool name, system platform, infrastructure technology
- **Example**: "Kubernetes", "Azure Cloud", "Jira", "GitLab"

### GOVERNMENT CONTRACTING SPECIFIC ENTITIES (Domain Differentiators)

#### 7. SECTION
RFP structural divisions - sections A-M (UCF) or custom section names and divisions.
- **Signal**: Section letter, section heading, "Section" keyword
- **Example**: "Section M: Evaluation Factors", "Section C: Statement of Work"

#### 8. REQUIREMENT
Mandatory, recommended, or optional obligations from contractor or requirements in the statement of work.
- **Signal**: "shall", "must", "should", "may" language + obligation context
- **Example**: "The contractor shall provide 24/7 help desk support"

#### 9. CLAUSE
Contract clauses from FAR, DFARS, agency supplements, or special requirement clauses.
- **Signal**: Citation format (FAR 52.###-##), incorporation language
- **Example**: "FAR 52.212-4 Contract Terms and Conditions"

#### 10. EVALUATION_FACTOR
Scoring criteria, weighting schemes, subfactors, evaluation methodology, and rubrics.
- **Signal**: "will be evaluated", weight percentage, adjectival ratings, subfactors
- **Example**: "Factor 1: Technical Approach (40% weight, evaluated via adjectival ratings)"

#### 11. SUBMISSION_INSTRUCTION
Format requirements, page limits, volume structure, submission method, deadlines for proposal submission.
- **Signal**: "page limit", "volume limited to", "shall submit", format requirements
- **Example**: "Technical Volume limited to 25 pages, 12pt font"

#### 12. DELIVERABLE
Contract deliverables, work products, CDRL items, reports, plans, data deliverables.
- **Signal**: CDRL identifier (A001), "deliverable", report/document name, milestone-tied output
- **Example**: "CDRL A001 - Monthly Status Report"

#### 13. DOCUMENT
Referenced documents (standards, specifications, regulations, attachments, references that are not clause or deliverable).
- **Signal**: Standard name (NIST, MIL-STD), document title, attachment listing
- **Example**: "MIL-STD-882E System Safety Program", "DoD Manual 5220.22-M"

#### 14. STATEMENT_OF_WORK
Description of work, tasks, performance objectives, performance-based statements, work scope.
- **Signal**: "contractor shall perform", task descriptions, performance objectives, work scope language
- **Example**: "Maintain system uptime at 99.9% or higher"

#### 15. EQUIPMENT
Physical items, machinery, vehicles, tools, resources, materials.
- **Signal**: Item name, equipment type, inventory item
- **Example**: "CESE equipment (containers, generators, vehicles)", "Navy combat rubber raiding craft"

#### 16. STRATEGIC_THEME
Win themes, hot buttons, customer priorities, discriminators, competitive differentiators, proof points.
- **Signal**: Repeated emphasis, customer priority, competitive advantage language
- **Example**: "Past performance with similar systems", "Demonstrated cost efficiency"

#### 17. PROGRAM
Named programs, initiatives, major contracts, project names.
- **Signal**: Program acronym/name (MCPP II, Navy MBOS), initiative name
- **Example**: "Marine Corps Prepositioning Program II (MCPP II)"

---

## Disambiguation Decision Tree

When multiple entity types could apply, use this decision tree:

### Decision 1: REQUIREMENT vs CLAUSE
**Question**: Is this a FAR/DFARS citation or a work obligation?
- **FAR/DFARS citation** (FAR 52.###-##) → CLAUSE
- **Work obligation** ("shall perform task X") → REQUIREMENT
- **Example**: "FAR 52.204-21" → CLAUSE; "comply with NIST 800-171" → REQUIREMENT

### Decision 2: EVALUATION_FACTOR vs SUBMISSION_INSTRUCTION
**Question**: Does this describe HOW proposals are scored or HOW proposals are formatted?
- **Describes scoring** ("evaluated on technical approach", "weight 40%") → EVALUATION_FACTOR
- **Describes format** ("25-page limit", "12pt font") → SUBMISSION_INSTRUCTION
- **Example**: "Technical Approach (40% weight)" → EVALUATION_FACTOR; "Technical volume limited to 25 pages" → SUBMISSION_INSTRUCTION

### Decision 3: STATEMENT_OF_WORK vs REQUIREMENT
**Question**: Is this a specific task/work scope or a general obligation?
- **Specific task/scope** ("Design the system architecture") → STATEMENT_OF_WORK
- **General obligation** ("The contractor shall design according to requirements") → REQUIREMENT
- **Example**: "Design system using microservices architecture" → STATEMENT_OF_WORK; "System shall use microservices architecture" → REQUIREMENT

### Decision 4: DELIVERABLE vs DOCUMENT
**Question**: Is this a contract output (CDRL) or a referenced standard/spec?
- **Contract output** (CDRL A001, "report due monthly") → DELIVERABLE
- **Referenced standard** (NIST 800-171, MIL-STD-882E) → DOCUMENT
- **Example**: "CDRL A001 Monthly Status Report" → DELIVERABLE; "NIST 800-171 Rev 2" → DOCUMENT

### Decision 5: STRATEGIC_THEME vs CONCEPT
**Question**: Is this a competitive differentiator or an abstract framework?
- **Competitive differentiator** ("past performance edge", "cost efficiency", "win theme") → STRATEGIC_THEME
- **Abstract framework** ("Agile methodology", "DevSecOps", "CMMI Level 3") → CONCEPT
- **Example**: "Demonstrated cost efficiency in similar programs" → STRATEGIC_THEME; "Agile development approach" → CONCEPT

### Decision 6: ORGANIZATION vs PERSON
**Question**: Is this a company/agency or an individual?
- **Company/Agency** ("Booz Allen", "NAVAIR") → ORGANIZATION
- **Individual** ("John Doe, Program Manager") → PERSON
- **Example**: "Lead contractor: Booz Allen Hamilton" → ORGANIZATION; "Program Manager: Captain John Doe" → PERSON

### Decision 7: LOCATION vs ORGANIZATION
**Question**: Is this a geographic area or an organization at that location?
- **Geographic area** ("Patuxent River, MD", "Norfolk Naval Station area") → LOCATION
- **Organization at location** ("NAVAIR Patuxent River facility") → ORGANIZATION
- **Example**: "Patuxent River, MD" → LOCATION; "Naval Air Systems Command (NAVAIR)" → ORGANIZATION

---

## Detection Algorithm Summary

1. **IDENTIFY content signals** (what language patterns appear?)
2. **MAP to semantic category** (what does this content mean?)
3. **CLASSIFY to entity type** (which of 17 types fits this semantic meaning?)
4. **ENRICH with context** (why does this matter for the proposal?)
5. **LINK to relationships** (what other entities does this connect to?)

**Remember**: Entity type = semantic meaning (content), NOT structural location (where in RFP)
