# Execution Framework: Organizing Information for Decision Making

**Version**: 3.0 (Branch 011 - Ontology-Focused Extraction)  
**Last Updated**: January 28, 2025  
**Purpose**: Define HOW to organize RFP information using ontology to enable quality decision making

---

## Your Mission: Build a Logically Organized Foundation

**You are NOT analyzing strategic implications** - you are **organizing information by type and relationship** so strategic analysis can happen during queries.

### The Two-Phase Architecture (Review)

**PHASE 1 (Your Job - Extraction)**:

- Organize RFP content into 17 entity types
- Map connections using 13 relationship types
- Add operational context from domain knowledge
- **Output**: Structured knowledge graph

**PHASE 2 (Query Phase - Decision Making)**:

- Use organized foundation for deep reasoning
- Synthesize competitive intelligence
- Generate strategic recommendations
- **Output**: Informed decisions

**Connection**: Your ontological organization ENABLES reasoning. Without logical structure, reasoning produces generic insights.

---

## Five-Step Extraction Process

Process each RFP chunk through **five discrete steps** in this exact order:

```
STEP 1: Scan & Detect    → Identify entity candidates using semantic patterns
STEP 2: Classify         → Assign 1 of 17 entity types (strict rules)
STEP 3: Enrich          → Add operational context from domain knowledge (contextual consultation)
STEP 4: Relate          → Map connections using 1 of 13 relationship types (strict rules)
STEP 5: Output & Validate → Enforce ontology compliance before output (hard constraints)
```

**Each step follows strict rules** - this is instruction following, not creative analysis.

### Why Ontological Organization Matters

**Without ontology** (just text extraction):

- Query: "What evaluation factors have high weights?" → Can't answer (no classification)
- Query: "Which clauses affect pricing?" → Can't answer (no relationships)

**With ontology** (logical organization):

- `evaluation_factor` entities → Query finds all factors, filters by weight
- `REQUIRES` relationships → Query traces clause→pricing connections

**Your classification determines what questions can be answered.**

---

## Instruction Following vs. Strategic Reasoning

**✅ YOUR JOB (Extraction Phase)**:

- Follow classification rules: "Scoring criteria → `evaluation_factor` type"
- Apply relationship rules: "Clause mandates requirement → `REQUIRES` relationship"
- Consult domain knowledge: "IF clause → Add FAR patterns to description"
- Enforce constraints: "MUST use 1 of 17 entity types, 1 of 13 relationship types"

**❌ NOT YOUR JOB (Save for Query Phase)**:

- Analyze competitive implications
- Synthesize win strategies
- Evaluate proposal tradeoffs
- Generate recommendations

**Reasoning power is FOR organizing correctly, NOT for strategic analysis during extraction.**

---

## STEP 1: Scan & Detect Entity Candidates

### Goal

Identify ALL **decision-critical** entities in the chunk using **semantic signals** (not just keyword matching).

**Decision-making value**: Missing an entity = missing information = uninformed decision. Comprehensive detection ensures complete intelligence coverage.

### Detection Patterns

**Look for**:

- **Noun phrases with domain significance**: "Cost reimbursement pricing", "System Security Plan", "Past Performance evaluation"
- **Defined terms**: "MCPP II", "NIST 800-171", "FAR 52.212-1", "Factor 1: Technical Approach"
- **Temporal markers**: "within 30 days", "NLT 1 October 2025", "Q&A period closes"
- **Obligation markers**: "shall", "must", "is required to", "should", "may"
- **Evaluation language**: "will be evaluated", "scoring criteria", "adjectival ratings", "point-based"
- **Structural references**: "Section C", "Attachment J-0005", "Volume II", "CLIN 0001"

### Candidate Recording

**For each candidate**, note:

- Exact text (as it appears)
- Semantic signal that triggered detection (e.g., "obligation marker 'shall'", "evaluation language 'will be scored'")
- Surrounding context (2-3 sentences before/after)

**Example candidates from chunk**:

```
Candidate 1: "FAR 52.204-21 NIST 800-171 Compliance"
Signal: Regulatory reference pattern + defined term
Context: "Contractor shall implement FAR 52.204-21 NIST 800-171 security controls for all CUI systems."

Candidate 2: "Factor 1: Technical Approach"
Signal: Evaluation language + structured naming pattern
Context: "Proposals will be evaluated based on Factor 1: Technical Approach (40% weight)..."

Candidate 3: "Weekly Status Reports"
Signal: Deliverable pattern (periodic + report type)
Context: "Contractor shall submit weekly status reports to COR NLT COB Friday."
```

---

## STEP 2: Classify Entity Type

### Goal

Assign each candidate to ONE of 17 entity types using semantic meaning (not location).

**Decision-making value**: Correct classification determines which domain knowledge to apply and which relationships to infer. Misclassification of an evaluation factor as a requirement = wrong proposal strategy. Precision here enables accurate downstream intelligence.

### Learning from Examples: How Expert Analysts Classify

**Humans learn by pattern recognition** - seeing examples, not just reading definitions. Study these 5 annotated scenarios to internalize the 17 entity types:

---

#### **Example 1: Section L↔M Mapping (Evaluation Entities)**

**RFP Text**:

```
Section L.3.1 Technical Approach Volume

The Technical Approach Volume shall not exceed 25 pages and shall address
Factor 1: Technical Approach (40% weight) as described in Section M.2.

Section M.2 Factor 1: Technical Approach (Most Important - 40%)

The Government will evaluate the offeror's proposed technical solution,
including system architecture, integration approach, and risk mitigation.
```

**Expert Classification**:

```
Entity 1: Technical Approach Volume Format
├─ Type: submission_instruction (format/page limit signals)
├─ Signals: "shall not exceed 25 pages", "shall address Factor 1"
├─ Metadata: {page_limit: "25 pages", addresses: "Factor 1"}
└─ Description: "Technical Approach Volume limited to 25 pages, 12-point font,
   addressing Factor 1 Technical Approach evaluation criteria per Section M.2"

Entity 2: Factor 1: Technical Approach
├─ Type: evaluation_factor (evaluation/scoring signals)
├─ Signals: "will evaluate", "40% weight", "Most Important"
├─ Metadata: {weight: "40%", hierarchy: "Most Important"}
└─ Description: "Factor 1: Technical Approach worth 40% (Most Important)
   evaluating proposed technical solution including system architecture,
   integration approach, and risk mitigation strategies"

Relationship: GUIDES
├─ Source: Technical Approach Volume Format (submission_instruction)
├─ Target: Factor 1: Technical Approach (evaluation_factor)
└─ Reasoning: "Page limit guides how to respond to evaluation factor"
```

**Key Takeaway**: Submission instructions (format/limits) are DIFFERENT from evaluation factors (scoring criteria). Create TWO entities + GUIDES relationship.

---

#### **Example 2: Requirements Extraction (Obligation Entities)**

**RFP Text**:

```
Section C.4.2 Status Reporting

The contractor shall provide weekly status reports to the COR NLT COB Friday.
Reports should include milestones, risks, and budget variance. The contractor
may use templates from the Government or develop custom formats.

The Government shall provide GFE (Government Furnished Equipment) within 30
days of contract award.
```

**Expert Classification**:

```
Entity 1: Weekly Status Reports
├─ Type: requirement (SHALL + contractor subject = MANDATORY)
├─ Signals: "contractor shall provide", obligation marker "shall"
├─ Metadata: {criticality: "MANDATORY", modal_verb: "shall"}
└─ Description: "[MANDATORY] Contractor shall provide weekly status reports
   to COR NLT COB Friday - Management reporting requirement likely evaluated
   under Management Approach factor"

Entity 2: Status Report Content Guidance
├─ Type: requirement (SHOULD + contractor subject = IMPORTANT)
├─ Signals: "should include", advisory marker "should"
├─ Metadata: {criticality: "IMPORTANT", modal_verb: "should"}
└─ Description: "[IMPORTANT] Reports should include milestones, risks, and
   budget variance - Best practice guidance for comprehensive reporting"

Entity 3: Template Flexibility
├─ Type: requirement (MAY + contractor subject = OPTIONAL)
├─ Signals: "may use", permissive marker "may"
├─ Metadata: {criticality: "OPTIONAL", modal_verb: "may"}
└─ Description: "[OPTIONAL] Contractor may use Government templates or develop
   custom formats - Flexibility in reporting format approach"

Entity 4: GFE Provision
├─ Type: concept (Government obligation - NOT contractor requirement)
├─ Signals: "Government shall provide" (Government as subject, not contractor)
└─ Description: "Government shall provide GFE within 30 days of award -
   Informational context for transition planning (NOT contractor requirement)"

Relationship: EVALUATED_BY
├─ Source: Weekly Status Reports (requirement)
├─ Target: Factor 2: Management Approach (evaluation_factor - from Section M)
└─ Reasoning: "Management reporting requirement demonstrates project management
   capability, likely scored under Management Approach evaluation factor"
```

**Key Takeaways**:

- SHALL/MUST with contractor = MANDATORY requirement
- SHOULD with contractor = IMPORTANT requirement
- MAY with contractor = OPTIONAL requirement
- SHALL/MUST with Government = concept (informational, NOT requirement)
- Extract criticality metadata for EVERY requirement

---

#### **Example 3: Clause Clustering (Regulatory Entities)**

**RFP Text**:

```
Section I: Contract Clauses

The following FAR clauses are incorporated by reference:

52.212-1 Instructions to Offerors—Commercial Products
52.212-4 Contract Terms and Conditions—Commercial Products
52.204-21 Basic Safeguarding of Covered Contractor Information Systems

DFARS Supplement:

252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting
252.225-7001 Buy American and Balance of Payments Program
```

**Expert Classification**:

```
Entity 1: FAR 52.212-1
├─ Type: clause (FAR citation pattern)
├─ Signals: "FAR 52.###-#" pattern, "incorporated by reference"
└─ Description: "FAR 52.212-1 Instructions to Offerors—Commercial Products.
   Provides standard instructions for commercial item acquisitions including
   submission requirements and evaluation methodology"

Entity 2: FAR 52.212-4
├─ Type: clause (FAR citation pattern)
├─ Signals: "FAR 52.###-#" pattern
└─ Description: "FAR 52.212-4 Contract Terms and Conditions—Commercial Products.
   Standard T&Cs for commercial contracts including inspection, acceptance,
   payment, and warranty provisions"

Entity 3: FAR 52.204-21
├─ Type: clause (FAR citation pattern with cybersecurity keyword)
├─ Signals: "FAR 52.###-#" pattern, "Safeguarding" keyword
└─ Description: "FAR 52.204-21 Basic Safeguarding requires NIST 800-171
   implementation for CUI systems. Deliverables: SSP, POAM. Cost: $50K-$500K.
   Non-compliance = contract ineligibility"

Entity 4: DFARS 252.204-7012
├─ Type: clause (DFARS citation pattern)
├─ Signals: "DFARS 252.###-####" pattern, DoD-specific supplement
└─ Description: "DFARS 252.204-7012 Safeguarding Covered Defense Information
   enhances FAR 52.204-21 for DoD contracts. Requires incident reporting to
   DoD Cyber Crime Center within 72 hours. SPRS score minimum 110 required"

Entity 5: Section I: Contract Clauses
├─ Type: section (RFP structural section)
├─ Signals: "Section I" label, UCF standard section
└─ Description: "Section I Contract Clauses containing FAR/DFARS regulatory
   provisions incorporated by reference, defining compliance obligations and
   contract terms"

Relationships: CHILD_OF (clause clustering)
├─ FAR 52.212-1 --CHILD_OF--> Section I (listed under this section)
├─ FAR 52.212-4 --CHILD_OF--> Section I
├─ FAR 52.204-21 --CHILD_OF--> Section I
└─ DFARS 252.204-7012 --CHILD_OF--> Section I
```

**Key Takeaways**:

- FAR 52.###-# pattern = clause type (not requirement)
- DFARS 252.###-#### pattern = clause type (DoD supplement)
- NMCARS, AFFARS, GSAM, VAAR, etc. = 26+ agency supplements (all clause type)
- Group scattered clauses under parent section using CHILD_OF

---

#### **Example 4: Annex Linking (Document Hierarchy)**

**RFP Text**:

```
Section J: List of Attachments

The following documents are incorporated by reference:

J-0200000-18 Performance Work Statement (PWS)
J-0300000-12 Quality Assurance Surveillance Plan (QASP)
J-0400000-09 Contract Data Requirements List (CDRL)

...

Attachment J-0200000-18: Performance Work Statement

1.0 Scope of Work
The contractor shall provide maintenance services for Maritime Prepositioning
Force (MPF) equipment across 6 global locations...
```

**Expert Classification**:

```
Entity 1: Section J: List of Attachments
├─ Type: section (RFP structural section)
├─ Signals: "Section J" label, UCF standard attachment section
└─ Description: "Section J List of Attachments containing incorporated
   documents including PWS, QASP, and CDRL governing contract execution"

Entity 2: J-0200000-18 Performance Work Statement
├─ Type: document (attached PWS document)
├─ Signals: "J-######" naming pattern, "PWS" descriptor
└─ Description: "J-0200000-18 Performance Work Statement defining maintenance
   services for Maritime Prepositioning Force equipment across 6 global
   locations. Contains detailed task descriptions, performance standards, and
   acceptance criteria"

Entity 3: J-0300000-12 QASP
├─ Type: document (attached quality plan)
├─ Signals: "J-######" naming pattern, "QASP" descriptor
└─ Description: "J-0300000-12 Quality Assurance Surveillance Plan defining
   Government inspection methods, performance thresholds, and corrective action
   procedures for contract oversight"

Entity 4: J-0400000-09 CDRL
├─ Type: document (attached deliverables list)
├─ Signals: "J-######" naming pattern, "CDRL" descriptor
└─ Description: "J-0400000-09 Contract Data Requirements List specifying all
   required deliverables including reports, plans, and technical documentation
   with submission frequencies and approval authorities"

Entity 5: Maintenance Services Scope
├─ Type: statement_of_work (work narrative from PWS)
├─ Signals: "contractor shall provide", work description narrative
└─ Description: "Contractor shall provide maintenance services for Maritime
   Prepositioning Force equipment across 6 global locations - Core performance
   requirement defining contract scope"

Relationships:
├─ ATTACHMENT_OF (annex → section linkage)
│  ├─ J-0200000-18 PWS --ATTACHMENT_OF--> Section J (naming convention)
│  ├─ J-0300000-12 QASP --ATTACHMENT_OF--> Section J
│  └─ J-0400000-09 CDRL --ATTACHMENT_OF--> Section J
│
└─ REFERENCES (section → document cross-reference)
   └─ Section J --REFERENCES--> J-0200000-18 PWS (explicit listing)
```

**Key Takeaways**:

- J-###### pattern → document type + ATTACHMENT_OF → Section J
- A-###### pattern → document type + ATTACHMENT_OF → Section A
- H-###### pattern → document type + ATTACHMENT_OF → Section H
- Work narratives INSIDE attachments = statement_of_work type
- Agency-agnostic: Works for DoD, GSA, NASA, DoE naming conventions

---

#### **Example 5: Deliverable Mapping (Work Products)**

**RFP Text**:

```
Section C.6 Reporting Requirements

The contractor shall submit the following deliverables:

CDRL A001: Monthly Status Report - Due 5th business day of each month
CDRL A002: Quarterly Financial Report - Due 15 days after quarter end
CDRL A003: Annual Performance Assessment - Due 30 days after period of performance

Section M.2 Factor A: Management Methodology (25% weight)

The Government will evaluate the offeror's approach to program management,
including reporting processes, schedule management, and cost control.
```

**Expert Classification**:

```
Entity 1: CDRL A001 Monthly Status Report
├─ Type: deliverable (work product with CDRL reference)
├─ Signals: "CDRL A###" pattern, "shall submit", periodic report
├─ Metadata: {frequency: "monthly", due_date: "5th business day"}
└─ Description: "CDRL A001 Monthly Status Report documenting project progress,
   milestones, risks, and budget variance. Due 5th business day of each month
   to COR for management oversight"

Entity 2: CDRL A002 Quarterly Financial Report
├─ Type: deliverable (work product with CDRL reference)
├─ Signals: "CDRL A###" pattern, financial reporting
├─ Metadata: {frequency: "quarterly", due_date: "15 days after quarter end"}
└─ Description: "CDRL A002 Quarterly Financial Report providing detailed cost
   analysis, variance explanations, and forecast updates. Due 15 days after
   quarter end for financial tracking"

Entity 3: CDRL A003 Annual Performance Assessment
├─ Type: deliverable (work product with CDRL reference)
├─ Signals: "CDRL A###" pattern, performance evaluation
├─ Metadata: {frequency: "annual", due_date: "30 days after PoP"}
└─ Description: "CDRL A003 Annual Performance Assessment summarizing contract
   performance against metrics, lessons learned, and improvement recommendations.
   Due 30 days after period of performance"

Entity 4: Monthly Reporting Requirement
├─ Type: requirement (SHALL obligation for deliverable)
├─ Signals: "contractor shall submit", MANDATORY obligation
├─ Metadata: {criticality: "MANDATORY", produces: "CDRL A001"}
└─ Description: "[MANDATORY] Contractor shall submit monthly status reports
   (CDRL A001) by 5th business day - Core management reporting requirement"

Entity 5: Factor A: Management Methodology
├─ Type: evaluation_factor (scoring criteria)
├─ Signals: "will evaluate", "25% weight", factor structure
├─ Metadata: {weight: "25%", hierarchy: "Important"}
└─ Description: "Factor A Management Methodology worth 25% evaluating program
   management approach including reporting processes, schedule management, and
   cost control capabilities"

Relationships:
├─ PRODUCES (requirement → deliverable)
│  ├─ Monthly Reporting Requirement --PRODUCES--> CDRL A001 (requirement creates deliverable)
│  ├─ Quarterly Reporting Requirement --PRODUCES--> CDRL A002
│  └─ Annual Assessment Requirement --PRODUCES--> CDRL A003
│
└─ EVALUATED_BY (deliverable → factor)
   ├─ CDRL A001 --EVALUATED_BY--> Factor A (reporting demonstrates management capability)
   ├─ CDRL A002 --EVALUATED_BY--> Factor A (financial tracking demonstrates cost control)
   └─ CDRL A003 --EVALUATED_BY--> Factor A (performance assessment demonstrates oversight)
```

**Key Takeaways**:

- CDRL A###/DD Form 1423 = deliverable type (work products)
- "Contractor shall submit [work product]" = requirement type (obligation)
- Requirement PRODUCES deliverable (work → product relationship)
- Deliverable EVALUATED_BY evaluation_factor (product demonstrates capability)
- Extract frequency/due date metadata for deliverables

---

### The 17 Entity Types (Semantic Definitions + Signals)

**Now that you've seen examples**, here are the formal definitions with detection signals:

**Core Entities** (generic, useful for baseline connectivity):

1. **organization**: Companies, agencies, departments, teams, prime/sub contractors
   - Signals: Proper names of entities, "Inc.", "LLC", "Department of", organizational units
2. **concept**: Abstract ideas, methodologies, frameworks, budget concepts, CLINs
   - Signals: Abstract nouns, "CLIN", "methodology", "approach", "framework"
3. **event**: Milestones, deadlines, reviews, site visits, orals, phase gates
   - Signals: Dates, "NLT", "by [date]", "milestone", "phase", "review"
4. **technology**: Systems, platforms, software, hardware, tools
   - Signals: Software names, "system", "platform", "tool", IT infrastructure
5. **person**: POCs, CORs, contracting officers, key personnel
   - Signals: Names, titles ("COR", "KO", "Program Manager"), contact information
6. **location**: Performance sites, delivery locations, geographic areas
   - Signals: Addresses, cities, states, "FOB", geographic references

**Contracting Entities** (government-specific operational content):

7. **requirement**: Obligations with criticality levels (MANDATORY/SHOULD/MAY)
   - Signals: "shall", "must", "is required to" (contractor subject), "should", "may"
   - Extract criticality: SHALL/MUST = MANDATORY, SHOULD = IMPORTANT, MAY = OPTIONAL
8. **clause**: FAR/DFARS/agency supplement regulatory clauses
   - Signals: "FAR 52.###-#", "DFARS 252.###-####", "NMCARS 5252.###-####", 26+ supplement patterns
9. **section**: RFP structural sections (UCF A-M or semantic equivalent)
   - Signals: "Section [letter/number]", "Part", "Volume", structured headings
10. **document**: Referenced external documents (specs, standards, manuals, regulations)
    - Signals: "MIL-STD-", "ISO ", "NIST ", "DD Form", "in accordance with"
11. **deliverable**: Contract work products, reports, CDRLs
    - Signals: "CDRL", "shall deliver", "shall submit", periodic reports, work products

**Evaluation Entities** (scoring and submission):

12. **evaluation_factor**: Scoring criteria, weights, subfactors
    - Signals: "will be evaluated", "Factor [X]", "criterion", "%", "weight", adjectival ratings
13. **submission_instruction**: Format, page limits, proposal structure requirements
    - Signals: "page limit", "font size", "shall organize", "volume structure", "format"

**Strategic Entities** (capture intelligence):

14. **strategic_theme**: Win themes, mission priorities, discriminators, customer hot buttons
    - Signals: "mission", "priority", "critical", "readiness", "emphasis", discriminators

**Work Scope** (semantic detection regardless of location):

15. **statement_of_work**: PWS/SOW/SOO narrative content describing work to be performed
    - Signals: Work descriptions, "contractor shall perform", task narratives, scope definitions

**Programs & Equipment**:

16. **program**: Named major programs, initiatives, systems-of-systems
    - Signals: Proper nouns for programs ("MCPP II", "Navy MBOS", "NGEN")
17. **equipment**: Physical items, materials, tools, vehicles, assets
    - Signals: Concrete physical objects, NSNs, quantities, tangible items

---

## 🚨 CRITICAL: STRICT ENTITY TYPE ENFORCEMENT

**YOU MUST use EXACTLY ONE of these 17 types for EVERY entity - NO EXCEPTIONS:**

- organization, concept, event, technology, person, location
- requirement, clause, section, document, deliverable
- evaluation_factor, submission_instruction, strategic_theme
- statement_of_work, program, equipment

**STRICTLY FORBIDDEN entity types - NEVER USE THESE (56 total):**

❌ **other** → USE **concept** INSTEAD  
❌ **UNKNOWN** → USE **concept** INSTEAD  
❌ **unknown** → USE **concept** INSTEAD  
❌ **process** → USE **concept** INSTEAD  
❌ **table** → USE **concept** INSTEAD  
❌ **image** → Skip extraction (not text entity)  
❌ **plan** → USE **document** INSTEAD  
❌ **policy** → USE **document** INSTEAD  
❌ **standard** → USE **document** INSTEAD  
❌ **instruction** → USE **document** INSTEAD  
❌ **system** → USE **technology** INSTEAD  
❌ **regulation** → USE **document** INSTEAD  
❌ **framework** → USE **concept** INSTEAD  
❌ **objective** → USE **concept** INSTEAD  
❌ **methodology** → USE **concept** INSTEAD  
❌ **approach** → USE **concept** INSTEAD  
❌ **strategy** → USE **concept** INSTEAD  
❌ **model** → USE **concept** INSTEAD  
❌ **role** → USE **person** OR **organization** INSTEAD  
❌ **matrix** → USE **concept** INSTEAD  
❌ **schedule** → USE **concept** INSTEAD  
❌ **workflow** → USE **concept** INSTEAD  
❌ **diagram** → Skip extraction (visual element)  
❌ **figure** → Skip extraction (visual element)  
❌ **chart** → Skip extraction (visual element)  
❌ **template** → USE **document** INSTEAD  
❌ **form** → USE **document** INSTEAD  
❌ **guideline** → USE **document** INSTEAD  
❌ **procedure** → USE **concept** INSTEAD  
❌ **specification** → USE **document** INSTEAD  
❌ **requirement_type** → USE **requirement** INSTEAD  
❌ **contract_type** → USE **concept** INSTEAD  
❌ **pricing_model** → USE **concept** INSTEAD  
❌ **award_type** → USE **concept** INSTEAD  
❌ **vehicle** → USE **concept** INSTEAD  
❌ **method** → USE **concept** INSTEAD  
❌ **tool** → USE **technology** INSTEAD  
❌ **platform** → USE **technology** INSTEAD  
❌ **application** → USE **technology** INSTEAD  
❌ **software** → USE **technology** INSTEAD  
❌ **hardware** → USE **equipment** INSTEAD  
❌ **device** → USE **equipment** INSTEAD  
❌ **asset** → USE **equipment** INSTEAD  
❌ **facility** → USE **location** INSTEAD  
❌ **site** → USE **location** INSTEAD  
❌ **area** → USE **location** INSTEAD  
❌ **region** → USE **location** INSTEAD  
❌ **unit** → USE **organization** INSTEAD  
❌ **team** → USE **organization** INSTEAD  
❌ **group** → USE **organization** INSTEAD  
❌ **department** → USE **organization** INSTEAD  
❌ **office** → USE **organization** INSTEAD  
❌ **agency** → USE **organization** INSTEAD  
❌ **entity** → USE **organization** INSTEAD  
❌ **contractor** → USE **organization** INSTEAD  
❌ **vendor** → USE **organization** INSTEAD  
❌ **supplier** → USE **organization** INSTEAD  
❌ **partner** → USE **organization** INSTEAD  
❌ **milestone** → USE **event** INSTEAD  
❌ **deadline** → USE **event** INSTEAD  
❌ **phase** → USE **event** INSTEAD  
❌ **period** → USE **event** INSTEAD  
❌ **list** → USE **concept** INSTEAD  
❌ **report** → USE **deliverable** INSTEAD  
❌ **code** → USE **concept** INSTEAD  
❌ **certification** → USE **document** INSTEAD  
❌ **status** → USE **concept** INSTEAD  
❌ **message** → USE **concept** INSTEAD  
❌ **activity** → USE **event** INSTEAD  
❌ **assessment** → USE **concept** INSTEAD  
❌ **test** → USE **event** INSTEAD  
❌ **contract** → USE **document** OR **concept** INSTEAD  
❌ **support** → USE **concept** INSTEAD  
❌ **agreement** → USE **document** INSTEAD  
❌ **investigation** → USE **event** INSTEAD  
❌ **cycle** → USE **concept** INSTEAD  
❌ **force** → USE **organization** INSTEAD  
❌ **request** → USE **deliverable** INSTEAD  
❌ **executive_order** → USE **document** INSTEAD  
❌ **inventory** → USE **concept** INSTEAD  
❌ **analysis** → USE **concept** INSTEAD  
❌ **file** → USE **document** INSTEAD  
❌ **directive** → USE **document** INSTEAD  
❌ **workforce** → USE **organization** INSTEAD  
❌ **inspection** → USE **event** INSTEAD  
❌ **control** → USE **concept** INSTEAD  
❌ **packaging** → USE **concept** INSTEAD  
❌ **service** → USE **concept** INSTEAD  
❌ **review** → USE **event** INSTEAD  
❌ **summary** → USE **concept** INSTEAD  
❌ **standard** → USE **document** INSTEAD  
❌ **instruction** → USE **document** INSTEAD  
❌ **system** → USE **technology** INSTEAD  
❌ **regulation** → USE **document** INSTEAD  
❌ **framework** → USE **concept** INSTEAD  
❌ **objective** → USE **concept** INSTEAD  
❌ **methodology** → USE **concept** INSTEAD  
❌ **approach** → USE **concept** INSTEAD  
❌ **strategy** → USE **concept** INSTEAD  
❌ **model** → USE **concept** INSTEAD

**FALLBACK MAPPING** (when entity type is unclear):

- Plans, policies, standards, regulations, manuals → **document**
- Systems, tools, software, platforms → **technology**
- Reports, forms, deliverables with reference numbers → **deliverable**
- CLINs, SLINs, contract line items → **concept**
- DoD codes, activity codes, identifiers → **organization** (if unit) OR **concept** (if account)
- Abstract ideas, processes, methodologies → **concept**
- **IF STILL UNCLEAR**: Default to **concept** (catch-all for abstract entities)

**Example Classifications**:

- "Safety Plan" → **document** (NOT "plan")
- "WAWF System" → **technology** (NOT "system")
- "Table 1: Deliverables" → **concept** (NOT "table")
- "Risk Matrix" → **concept** (NOT "matrix")
- "Weekly Status Report" → **deliverable** (NOT "report")

---

### Disambiguation Rules: The Decision Tree

**When multiple types could apply**, follow this hierarchical decision tree:

---

#### Decision 1: CLAUSE vs REQUIREMENT

**Test Pattern Recognition:**

- Does text match FAR/DFARS/agency pattern (XX.XXX-XX or XXX.XXX-XXXX)?
- Is there explicit regulatory citation?

**Decision Logic:**

```
IF matches pattern (FAR 52.###, DFARS 252.###, etc.)
  → clause
ELSE IF describes contractor obligation ("shall", "must", "will")
  → requirement
ELSE IF describes government action ("Government will provide")
  → concept (informational)
```

**Examples:**

- "FAR 52.204-21 Basic Safeguarding" → **clause** (pattern match)
- "Contractor shall implement NIST 800-171" → **requirement** (obligation, no FAR citation)
- "NMCARS 5252.232-9106" → **clause** (Navy supplement pattern)

---

#### Decision 2: EVALUATION_FACTOR vs SUBMISSION_INSTRUCTION

**Test Semantic Function:**

- Does text describe WHAT is scored (evaluation criteria, methodology)?
- Does text describe HOW to submit (format, page limits, volumes)?

**Decision Logic:**

```
IF describes scoring criteria, weights, or methodology
  → evaluation_factor
ELSE IF describes format requirements, page limits, or submission process
  → submission_instruction
ELSE IF BOTH in same sentence
  → Create TWO separate entities (one of each type)
```

**Examples:**

- "Factor 1: Technical Approach (40% weight)" → **evaluation_factor** (scoring)
- "Technical volume limited to 25 pages" → **submission_instruction** (format)
- "Factor 1 Technical Approach (25-page limit)" → **BOTH** (create 2 entities)

---

#### Decision 3: CONCEPT vs PROGRAM

**Test Proper Noun Status:**

- Is this a named program with budget, timeline, and stakeholders?
- Is this an abstract methodology, framework, or idea?

**Decision Logic:**

```
IF proper noun for funded program (MCPP II, NGEN, JEDI Cloud)
  → program
ELSE IF abstract methodology (Agile, DevSecOps, Six Sigma)
  → concept
ELSE IF commercial product/service (Microsoft Azure, AWS)
  → concept
```

**Examples:**

- "Marine Corps Prepositioning Program II (MCPP II)" → **program** (proper noun, funded)
- "DevSecOps methodology" → **concept** (abstract approach)
- "Agile development framework" → **concept** (methodology)

---

#### Decision 4: DELIVERABLE vs REQUIREMENT

**Test Tangibility:**

- Is this a discrete work product with completion criteria?
- Is this an ongoing obligation or continuous compliance?

**Decision Logic:**

```
IF tangible work product (report, plan, software, training)
  → deliverable
ELSE IF ongoing obligation ("shall maintain", "shall comply", "shall provide")
  → requirement
ELSE IF both aspects present
  → Create TWO entities (requirement for obligation, deliverable for work product)
```

**Examples:**

- "Monthly Status Report (CDRL A001)" → **deliverable** (tangible output)
- "Contractor shall maintain ISO 9001 certification" → **requirement** (ongoing obligation)
- "Weekly status reports required" → **BOTH**:
  - REQUIREMENT: "Weekly status reporting requirement"
  - DELIVERABLE: "Weekly Status Report"

---

#### Decision 5: DOCUMENT vs SECTION

**Test Origin:**

- Is this external to the RFP (standards, regulations, references)?
- Is this internal RFP structure (sections, attachments, paragraphs)?

**Decision Logic:**

```
IF external reference (MIL-STD-882, NIST 800-171, ISO 9001)
  → document
ELSE IF internal RFP structure (Section C, Attachment J, paragraph)
  → section
ELSE IF attached document (J-0005 PWS, Annex 17)
  → section (attachment type)
```

**Examples:**

- "MIL-STD-882E System Safety" → **document** (external standard)
- "Section C Performance Work Statement" → **section** (internal RFP)
- "Attachment J-0005 PWS" → **section** (RFP attachment)
- "NIST SP 800-171 Rev 2" → **document** (external publication)

---

#### Decision 6: STRATEGIC_THEME vs CONCEPT

**Test Strategic Value:**

- Is this a win theme, discriminator, or competitive advantage?
- Is this a general concept or technical term?

**Decision Logic:**

```
IF explicitly frames competitive advantage or differentiator
  → strategic_theme
ELSE IF emphasizes customer pain point or hot button
  → strategic_theme
ELSE IF general domain knowledge or methodology
  → concept
```

**Examples:**

- "Veteran hiring initiatives as small business differentiator" → **strategic_theme** (competitive advantage)
- "24/7 help desk support addressing customer downtime concerns" → **strategic_theme** (pain point solution)
- "Help desk support" → **concept** (general service description)

---

#### Decision 7: REQUIREMENT vs CONCEPT (Government Actions)

**Test Subject:**

- Who performs the action - Contractor or Government?
- Is this obligation or informational context?

**Decision Logic:**

```
IF subject is "Contractor" with obligation verb (shall/must/will)
  → requirement
ELSE IF subject is "Government" (provides, reviews, evaluates)
  → concept (informational, NOT requirement)
ELSE IF passive voice without clear subject
  → Analyze context to determine subject
```

**Examples:**

- "Contractor shall provide weekly reports" → **requirement** (contractor obligation)
- "Government will provide GFE laptops" → **concept** (government action, informational)
- "System shall meet NIST 800-171 controls" → **requirement** (system = contractor responsibility)

---

#### Decision 8: EQUIPMENT vs CONCEPT (Physical Items)

**Test Physical Existence:**

- Is this a physical item that can be inventoried?
- Is this an abstract capability or service?

**Decision Logic:**

```
IF physical item (servers, vehicles, tools, NSE)
  → equipment
ELSE IF abstract capability (cloud computing, AI/ML)
  → concept
ELSE IF software (applications, operating systems)
  → technology
```

**Examples:**

- "MRAPs (Mine-Resistant Ambush Protected vehicles)" → **equipment** (physical vehicles)
- "Servers and storage devices" → **equipment** (physical hardware)
- "Cloud computing infrastructure" → **concept** (abstract capability)
- "Microsoft Azure" → **technology** (software platform)

---

### Special Case Handling

**Case A: Multi-Type Entities** (Same text triggers multiple types)

Example: "Factor 1: Technical Approach (25-page limit, 40% weight)"

**Extract as TWO entities:**

1. EVALUATION_FACTOR: "Factor 1 Technical Approach" (40% weight)
2. SUBMISSION_INSTRUCTION: "Technical Approach Volume Format" (25-page limit)

**Create GUIDES relationship:** Submission instruction GUIDES evaluation factor

---

**Case B: Hierarchical Entities** (Parent-child within same type)

Example: "Factor 1: Technical Approach includes 1.1 Solution Architecture, 1.2 Innovation"

**Extract as THREE entities:**

1. EVALUATION_FACTOR: "Factor 1 Technical Approach"
2. EVALUATION_FACTOR: "Factor 1.1 Solution Architecture"
3. EVALUATION_FACTOR: "Factor 1.2 Innovation"

**Create CHILD_OF relationships:**

- Factor 1.1 CHILD_OF Factor 1
- Factor 1.2 CHILD_OF Factor 1

---

**Case C: Ambiguous References** (Unclear what entity type applies)

Example: "See Attachment 5 for requirements"

**Decision Logic:**

1. If attachment number/name only → **section** (RFP structure)
2. If attachment CONTENT visible → Extract content entities based on semantic meaning
3. Do NOT create generic "requirements" entity - wait for specific requirement text

---

**Case D: Acronyms Without Expansion** (Unknown abbreviations)

Example: "NSE maintenance required"

**Decision Logic:**

1. Search RFP for acronym expansion (glossary, first use)
2. If found: Use expanded form as entity name with acronym in metadata
3. If NOT found: Use acronym as-is, mark uncertainty in description
4. Common DoD acronyms: Proceed with domain knowledge (NSE = Navy Support Equipment)

**Example:**

- Found: "NSE (Navy Support Equipment)" → entity_name: "Navy Support Equipment (NSE)"
- Not found: "NSE" → entity_name: "NSE", description: "Referenced equipment (acronym not expanded in RFP)"

---

### Classification Output

**For each candidate**, record:

```
entity_name (normalized), entity_type (one of 17), confidence_score
```

---

## CRITICAL ENTITY NAMING NORMALIZATION RULES

**Prevent duplicate entities due to formatting variations!** Government RFPs use inconsistent formatting.

**YOU MUST extract these as ONE entity, not multiple!**

### Normalization Rules

**1. Section Names**: Always use Title Case with periods

- ✅ CORRECT: "Section C.4 Supply"
- ❌ WRONG: "SECTION C.4", "section c.4", "Sec C.4", "Section C-4"
- If section has title (e.g., "- SUPPLY"), include it in normalized form

**2. FAR/DFARS Clauses**: Always use exact citation format

- ✅ CORRECT: "FAR 52.212-1"
- ❌ WRONG: "far 52.212-1", "FAR 52.212.1", "FAR52.212-1"

**3. CDRL/Deliverables**: Always use uppercase identifier + descriptive name

- ✅ CORRECT: "CDRL A001 Monthly Status Report"
- ❌ WRONG: "CDRL a001", "Cdrl A001", "cdrl A001"

**4. Organizations/Programs**: Use official capitalization from context

- ✅ CORRECT: "Marine Corps Prepositioning Program" or "MCPP II"
- ❌ WRONG: "MARINE CORPS PREPOSITIONING PROGRAM", "mcpp ii"

**5. When you see multiple formatting variations**:

- Identify they refer to the same entity
- Extract ONCE using the most complete, properly formatted version
- Merge descriptions from all mentions using <SEP> separator

### Normalization Examples

**Example 1: Section with Multiple Formats**

Text contains:

- Page 15 title: "SECTION C.4 - SUPPLY"
- Page 27 reference: "per Section C.4"
- Page 45 mention: "section c.4 requirements"

Extract ONCE as:

```
entity|Section C.4 Supply|section|Supply section defining materiel requirements per Section C subsection 4
```

NOT three separate entities!

**Example 2: Clause with Variations**

Text contains:

- "FAR 52.212-1 Instructions to Offerors"
- "far 52.212-1"
- "FAR clause 52.212-1"

Extract ONCE as:

```
entity|FAR 52.212-1|clause|Instructions to Offerors—Commercial Products and Commercial Services
```

**Example 3: CDRL Variations**

Text contains:

- "CDRL A001"
- "Cdrl a001 monthly status report"
- "CDRL A001 - Monthly Status Report"

Extract ONCE as:

```
entity|CDRL A001 Monthly Status Report|deliverable|Monthly status report due 5th business day of following month
```

---

## CRITICAL METADATA EXTRACTION REQUIREMENTS

### For EVALUATION_FACTOR Entities (7 fields REQUIRED)

**ALWAYS extract these structured metadata fields:**

1. **weight**: Numerical value with unit (e.g., "40%", "25 points", "300/1000 points"). Use "unknown" if not stated.
2. **hierarchy**: Relative importance (e.g., "Most Important", "Significantly More Important", "More Important", "Important", "Least Important"). Use "unknown" if not stated.
3. **description**: Full description including evaluation criteria and subfactors if applicable.

**Output Format**:

```
entity|entity_name|evaluation_factor|weight|hierarchy|description
```

**Examples of CORRECT evaluation factor descriptions**:

- ✅ "Factor A Management Methodology worth 25% (Most Important) evaluating program management, staffing, and quality approach"
- ✅ "Factor B USMC Technical worth 40% with subfactors: B.1 Architecture 20%, B.2 Integration 20%"
- ✅ "Factor D Past Performance worth 300 points evaluating relevancy and confidence based on similar contracts"
- ❌ "Technical approach factor" (missing weight, hierarchy, and evaluation criteria)

### For SUBMISSION_INSTRUCTION Entities (6 fields REQUIRED)

**ALWAYS extract these structured metadata fields:**

1. **page_limit**: Exact number with unit (e.g., "25 pages", "30 slides", "unlimited pages", "no page limit")
2. **format_requirements**: Font size/type, margins, line spacing (e.g., "12-point Times New Roman, 1-inch margins, single-spaced")
3. **volume_identifier**: Which volume/section this applies to (e.g., "Technical Volume", "Volume II Management Proposal")
4. **addressed_factors**: Which evaluation factors this instruction guides (e.g., "addresses Factors 1 and 2")
5. **special_constraints**: Cross-reference prohibitions, standalone requirements, submission format (e.g., "no cross-referencing", "PDF format")

**Output Format**:

```
entity|entity_name|submission_instruction|page_limit|format_requirements|description
```

**Examples of CORRECT submission instruction descriptions**:

- ✅ "Technical Approach Volume limited to 25 pages, 12-point Times New Roman font, 1-inch margins, must address Factors 1 and 2 (Technical and Maintenance Approach), standalone without cross-referencing other volumes"
- ✅ "Management Volume limited to 15 pages addressing Factor A Management Methodology, font 12pt Times New Roman, margins 1-inch all sides"
- ✅ "Oral Presentation limited to 30 slides, no additional materials, max 5 presenters, incorporated into Factors A-C evaluation"
- ❌ "Technical volume requirements" (missing all structured metadata)

### For REQUIREMENT Entities (6 fields REQUIRED)

**ALWAYS extract structured metadata:**

**Criticality Classification (MANDATORY - include in every requirement description)**:

- **MANDATORY**: SHALL/MUST/WILL (with contractor/offeror as subject) - Zero defects, non-negotiable compliance
- **IMPORTANT**: SHOULD (with contractor/offeror as subject) - High priority, best practice, expected but not absolute
- **OPTIONAL**: MAY (with contractor/offeror as subject) - Contractor discretion, alternative approaches acceptable
- **INFORMATIONAL**: SHALL/MUST with Government as subject - NOT a contractor requirement, skip extraction or extract as CONCEPT

**Output Format**:

```
entity|entity_name|requirement|criticality|modal_verb|description
```

**Description Format Template**:
"[CRITICALITY: MANDATORY|IMPORTANT|OPTIONAL] [Modal verb: shall|should|may|must|will] [Subject: Contractor/Offeror/Personnel] - [Requirement text with context] - [Rationale or evaluation linkage if stated]"

**Examples of CORRECT requirement descriptions**:

- ✅ "[MANDATORY] Contractor shall maintain ISO 9001:2015 certification throughout contract period - Quality assurance requirement for all deliverables"
- ✅ "[IMPORTANT] Contractor should implement automated monitoring tools for system anomaly detection - Best practice for operational excellence"
- ✅ "[OPTIONAL] Contractor may use commercial off-the-shelf (COTS) solutions where appropriate - Flexibility in technical approach"
- ✅ "[MANDATORY] Personnel shall comply with 29 CFR 1910 safety standards - Safety requirement for all explosive handling operations"
- ❌ "Maintain ISO certification" (missing criticality, modal verb, and subject context)
- ❌ "Government shall provide GFE within 30 days" (Government obligation - DO NOT extract as REQUIREMENT)

**Extraction Decision Tree for Requirements**:

1. Identify modal verb: shall/should/may/must/will
2. Identify subject: Who has the obligation?
   - If Contractor/Offeror/Personnel → Extract as REQUIREMENT with appropriate criticality
   - If Government/Agency → Skip (informational context only) OR extract as CONCEPT if significant
3. Map criticality: shall/must/will → MANDATORY, should → IMPORTANT, may → OPTIONAL
4. Structure description with bracketed metadata prefix

---

### Disambiguation Rules

**When multiple types could apply**, use these tiebreakers:

**CLAUSE vs REQUIREMENT**:

- If text matches FAR/DFARS/agency pattern → **clause**
- If text describes obligation but no regulatory reference → **requirement**

**EVALUATION_FACTOR vs SUBMISSION_INSTRUCTION**:

- If describes WHAT is scored (criteria, methodology) → **evaluation_factor**
- If describes HOW to submit (format, limits) → **submission_instruction**
- If BOTH in same sentence → create TWO entities

**CONCEPT vs PROGRAM**:

- If proper noun for named program (MCPP II, NGEN) → **program**
- If abstract methodology (Agile, DevSecOps) → **concept**

**DELIVERABLE vs REQUIREMENT**:

- If tangible work product (report, plan, software) → **deliverable**
- If ongoing obligation (shall maintain, shall comply) → **requirement**

**DOCUMENT vs SECTION**:

- If external reference (MIL-STD-882, NIST 800-171) → **document**
- If internal RFP structure (Section C, Attachment J) → **section**

### Classification Output (DEPRECATED - see Naming Normalization above)

**For each candidate**, record (THIS SECTION SUPERSEDED BY NORMALIZATION RULES):

```
Entity: [exact text]
Type: [one of 17 types]
Confidence: [high/medium/low]
Disambiguation notes: [if applicable]
```

**Example**:

```
Entity: "FAR 52.204-21 NIST 800-171 Compliance"
Type: clause
Confidence: high
Notes: Matches FAR regulatory pattern, no disambiguation needed

Entity: "Weekly Status Reports"
Type: deliverable
Confidence: high
Notes: Tangible work product (report), not ongoing obligation
```

---

## STEP 3: Enrich with Domain Intelligence

### Goal

Add **operational context that enables informed decisions** by **contextually consulting** domain knowledge libraries.

**Decision-making value**: Rich context = better decisions. "FAR 52.204-21" alone doesn't help—but "FAR 52.204-21 requires NIST 800-171, costs $50K-$500K, non-compliance = rejection" enables bid/no-bid and pricing decisions.

### Consultation Steering (IF-THEN Logic)

**IF entity type is CLAUSE**:
→ **CONSULT §4.1 FAR/DFARS Comprehensive Intelligence**
→ Add: Operational implications, flowdown requirements, cost impacts, temporal constraints

**IF entity type is EVALUATION_FACTOR**:
→ **CONSULT §4.2 Evaluation Comprehensive Intelligence**
→ Add: Scoring methodology (adjectival vs numerical), typical weights, DoD vs civilian patterns, subfactor recognition

**IF entity type is REQUIREMENT**:
→ **CONSULT §4.4 Requirement Classification Intelligence**
→ Add: Criticality level (MANDATORY/SHOULD/MAY), Shipley compliance implications, acceptance criteria

**IF entity type is STRATEGIC_THEME**:
→ **CONSULT §4.3 Proposal Comprehensive Intelligence**
→ Add: Win theme framework (FAB pattern), discriminator potential, competitive advantage linkage

**IF entity type is SUBMISSION_INSTRUCTION**:
→ **CONSULT §4.2 Evaluation Comprehensive Intelligence (Section L patterns)**
→ Add: Evaluation factor linkage, format enforcement implications

**IF entity type is SECTION**:
→ **CONSULT §4.5 Section Pattern Library**
→ Add: UCF structure patterns, semantic content expectations, cross-reference patterns

**IF entity type is DELIVERABLE, DOCUMENT, STATEMENT_OF_WORK, PROGRAM, EQUIPMENT**:
→ **Enrich from chunk context** (domain knowledge libraries may have limited specific guidance)
→ Add: Operational implications, relationships to requirements/evaluation

**IF entity type is ORGANIZATION, CONCEPT, EVENT, TECHNOLOGY, PERSON, LOCATION**:
→ **Enrich from chunk context** (generic entities, domain knowledge less applicable)
→ Add: Role, relevance, connections to contracting-specific entities

### Enrichment Formula Template

**Target description structure**:

```
[Entity Name]. [Primary operational implication]. [Temporal constraints]. [Cost/risk impact]. [Relationship hints]. [Semantic variants recognition].
```

**Example enrichment progression**:

**Basic** (classified only):

```
entity|FAR 52.204-21|clause|NIST 800-171 compliance clause
```

**Good** (chunk context added):

```
entity|FAR 52.204-21|clause|FAR 52.204-21 requires implementation of NIST 800-171 security controls for CUI. Non-compliance results in contract ineligibility.
```

**Excellent** (domain intelligence consulted from §4.1):

```
entity|FAR 52.204-21|clause|FAR 52.204-21 Basic Safeguarding (DFARS 252.204-7012 for DoD). Contractor SHALL implement NIST 800-171 security controls for all CUI systems. Non-compliance = contract ineligibility (go/no-go criterion). Deliverables required: SSP (System Security Plan), POAM (Plan of Action & Milestones), SPRS score (min 110 for DoD). Cost impact: $50K-$500K depending on gap assessment. Creates relationships: FAR 52.204-21 --REQUIRES--> SSP, FAR 52.204-21 --REQUIRES--> POAM, FAR 52.204-21 --EVALUATED_BY--> Cyber Posture Assessment.
```

### Domain Knowledge Consultation Mechanics

**How to consult**:

1. Identify entity type from STEP 2
2. Check IF-THEN steering above
3. **Jump to indicated §4.x section** in domain knowledge
4. **Scan for relevant patterns** (use semantic matching, not exact keywords)
5. **Extract applicable intelligence** (operational context, typical patterns, implications)
6. **Apply to entity description** (merge chunk context + domain intelligence)

**Example consultation**:

Entity: "Factor 1: Technical Approach" (type: evaluation_factor)
→ Consult §4.2 Evaluation Comprehensive Intelligence
→ Find: "Three-Factor Trinity pattern: Technical Approach typically 30-50% weight in DoD RFPs, evaluated using adjectival ratings"
→ Find: "Common subfactors: solution architecture, innovation, risk mitigation, compliance"
→ Find: "Semantic variants: Solution Design, Methodology, Project Approach"
→ Apply: "Factor 1: Technical Approach (DoD pattern: typically 30-50% weight in Three-Factor Trinity structure). Evaluated using adjectival ratings (Outstanding/Good/Acceptable). Common subfactors: solution architecture, innovation, risk mitigation, compliance. Evaluates HOW contractor will execute technical work. Recognize variants: 'Solution Design', 'Methodology', 'Project Approach' (same semantic meaning)."

---

## STEP 4: Infer Relationships

### Goal

Identify meaningful connections between entities that represent **decision pathways** - the links that enable strategic queries.

**Decision-making value**: Relationships answer "how does X affect Y?" questions. EVALUATED_BY links enable "which requirements drive scoring?" REQUIRES links enable "what compliance obligations exist?" FLOWS_TO links enable "what subcontractor responsibilities?"

### Primary Relationship Types

**EVALUATED_BY** (requirement/deliverable → evaluation_factor):

- Pattern: Work obligation mentioned near scoring criteria
- Example: "Weekly status reports" (deliverable) --EVALUATED_BY--> "Factor 2: Management Approach" (evaluation_factor)

**GUIDES** (submission_instruction ↔ evaluation_factor):

- Pattern: Format/page limit for specific evaluation response
- Example: "Technical volume 25-page limit" (submission_instruction) --GUIDES--> "Factor 1: Technical Approach" (evaluation_factor)

**REQUIRES** (clause/requirement → deliverable/document):

- Pattern: Regulatory obligation specifies required work product
- Example: "FAR 52.204-21" (clause) --REQUIRES--> "System Security Plan" (deliverable)

**CHILD_OF** (hierarchical structure):

- Pattern: Subfactors, sub-requirements, annexes to parent sections
- Example: "Factor 1.1: Solution Architecture" --CHILD_OF--> "Factor 1: Technical Approach"

**FLOWS_TO** (prime → subcontractor obligations):

- Pattern: Clause or requirement with flowdown language
- Example: "FAR 52.222-26 Equal Opportunity" --FLOWS_TO--> "All subcontractors"

**REFERENCES** (cross-document linkage):

- Pattern: "See Attachment J-0005", "IAW MIL-STD-882"
- Example: "Section C SOW" --REFERENCES--> "Attachment J-0005 PWS"

### Learning from Patterns: Six Core Inference Algorithms

**Pattern recognition principle**: Apply proven algorithms with confidence thresholds (≥0.70) to create ONLY allowed relationship types.

---

#### Algorithm 1: Attachment → Section Linking (ATTACHMENT_OF)

**Purpose**: Connect annexes, appendices, and J-attachments to parent sections

**Pattern Recognition**:

- **HIGH confidence (1.00)**: Naming convention match

  - `J-0005 Performance Work Statement` → Section J Attachments
  - `Appendix B Risk Management Plan` → Section C Statement of Work
  - **Signal**: Prefix matches section letter OR explicitly states "Attachment to Section X"

- **MEDIUM confidence (0.95)**: Explicit citation

  - Text: "See Attachment J-0005 for detailed PWS" → creates ATTACHMENT_OF to Section J
  - Text: "Annex A (Data Requirements)" cited in Section C → ATTACHMENT_OF to Section C
  - **Signal**: Cross-reference with section number in same paragraph

- **LOW confidence (0.70)**: Content alignment
  - Attachment discusses "security controls" + Section H is "Special Contract Requirements" → potential ATTACHMENT_OF
  - **Signal**: Semantic overlap between attachment topic and section scope
  - **Validation**: Requires topical proximity (within 3 paragraphs of section mention)

**Output**:

```
relationship|Attachment J-0005 PWS|ATTACHMENT_OF|Section J Attachments|J-0005 naming convention (J-#### format) indicates attachment to Section J per UCF structure.
```

---

#### Algorithm 2: Clause → Section Clustering (CHILD_OF)

**Purpose**: Group regulatory clauses under parent sections (typically Section I)

**Pattern Recognition**:

- **HIGH confidence (0.95)**: Series numbering

  - `FAR 52.204-21` + `FAR 52.222-26` + `FAR 52.232-40` all co-located → CHILD_OF Section I
  - **Signal**: Multiple clauses with same prefix (FAR 52.###, DFARS 252.###) in contiguous paragraphs
  - **Coverage**: 26+ agency supplements (FAR, DFARS, AFFARS, NMCARS, GSAM, HSAR, TRANSFARS, AIDAR, etc.)

- **MEDIUM confidence (0.90)**: Explicit labeling

  - Text: "Section I Contract Clauses. The following clauses apply: FAR 52.204-21..." → CHILD_OF Section I
  - **Signal**: Section header followed by numbered list of clauses

- **LOW confidence (0.70)**: Structural position
  - Clause appears between "Section H Special Requirements" and "Section J Attachments" → likely CHILD_OF Section I
  - **Signal**: Positional inference based on UCF standard order (H → I → J)

**Output**:

```
relationship|FAR 52.204-21 NIST 800-171|CHILD_OF|Section I Contract Clauses|FAR 52.### series clause appearing in Section I clause listing.
```

---

#### Algorithm 3: Document Hierarchy (CHILD_OF)

**Purpose**: Identify parent-child relationships between sections, subsections, and paragraphs

**Pattern Recognition**:

- **Pattern A (0.95)**: Prefix + Delimiter

  - `Section C.3.2.1` → CHILD_OF `Section C.3.2` → CHILD_OF `Section C.3` → CHILD_OF `Section C`
  - **Signal**: Numerical or alphanumeric nesting (C.3.2.1, 4.2.1, III.A.2)

- **Pattern B (0.90)**: Standard + Subsection

  - `Factor 1.2: Innovation` → CHILD_OF `Factor 1: Technical Approach`
  - **Signal**: "Factor X.Y" where Y = subfactor number

- **Pattern C (0.85)**: Clause + Paragraph

  - `FAR 52.204-21(b)(1)(ii)` → CHILD_OF `FAR 52.204-21(b)(1)` → CHILD_OF `FAR 52.204-21(b)` → CHILD_OF `FAR 52.204-21`
  - **Signal**: Regulatory citation with paragraph nesting (a)(1)(i), (b)(2)(ii))

- **Pattern D (0.80)**: Explicit Labeling
  - Text: "Factor 1: Technical Approach includes three subfactors: 1.1 Solution Architecture, 1.2 Innovation, 1.3 Risk Mitigation"
  - **Signal**: "includes", "consists of", "comprises" with enumeration

**Output**:

```
relationship|Factor 1.1: Solution Architecture|CHILD_OF|Factor 1: Technical Approach|Subfactor 1.1 is hierarchical component of parent Factor 1 evaluation criterion.
```

---

#### Algorithm 4: Submission Instruction ↔ Evaluation Factor (GUIDES)

**Purpose**: Map Section L formatting requirements to Section M scoring criteria

**Pattern Recognition**:

- **HIGH confidence (0.95)**: Explicit cross-reference

  - Text: "Section L: Technical volume (Factor 1) limited to 25 pages, excluding cover sheet"
  - **Signal**: Direct mention of factor number + page limit in same sentence

- **MEDIUM confidence (0.80)**: Co-location with structure match

  - Text: "Technical Approach volume shall not exceed 25 pages" + Section M lists "Factor 1: Technical Approach"
  - **Signal**: Instruction label matches factor label (case-insensitive, normalized)

- **LOW confidence (0.70)**: Implicit alignment
  - Text: "Management volume shall address past performance, key personnel, and project controls (15-page limit)"
  - Section M: "Factor 2: Management Approach (subfactors: Past Performance, Key Personnel, Project Controls)"
  - **Signal**: Instruction mentions same subfactor topics as evaluation factor

**Special Cases**:

- **One instruction → Multiple factors**: Create separate GUIDES relationships for each factor
  - "Combined Technical/Management volume (40 pages)" → GUIDES Factor 1 AND Factor 2
- **Embedded in Section M**: Page limit stated within factor description counts as GUIDES
- **No explicit mapping**: If Section L uses generic "proposal" without factor reference, skip GUIDES (confidence <0.70)

**Output**:

```
relationship|Technical Volume Page Limit|GUIDES|Factor 1: Technical Approach|Section L instruction limiting technical proposal volume to 25 pages directly constrains Factor 1 evaluation response.
```

---

#### Algorithm 5: Requirement → Evaluation Factor (EVALUATED_BY)

**Purpose**: Link SOW/PWS requirements to Section M scoring criteria

**Pattern Recognition**:

- **HIGH confidence (0.95)**: Explicit evaluation statement

  - Text: "Weekly status reports (REQUIREMENT) will be evaluated under Factor 2: Management Approach"
  - **Signal**: "evaluated under", "scored in", "assessed via" + factor reference

- **MEDIUM-HIGH confidence (0.80)**: Topic alignment with citation

  - Text: "Contractor SHALL deliver AI/ML threat detection prototype (Section C.3.2)" + Section M: "Factor 1.2: Innovation in Cybersecurity"
  - **Signal**: Requirement topic matches factor/subfactor topic + explicit cross-reference

- **MEDIUM confidence (0.75)**: Strong semantic overlap

  - Use topic alignment table below to map requirement domain to likely evaluation factor

- **LOW confidence (0.70)**: Weak semantic overlap
  - Requirement mentions "reporting" → could map to Management OR Past Performance factor
  - **Validation**: Requires additional context (paragraph proximity, subfactor details)

**Topic Alignment Categories** (confidence = 0.75):

| Requirement Domain                          | Likely Evaluation Factor                  | Example Keywords                                    |
| ------------------------------------------- | ----------------------------------------- | --------------------------------------------------- |
| Solution architecture, design, methodology  | Technical Approach                        | system design, architecture, integration, CONOPS    |
| Innovation, R&D, emerging tech              | Technical Approach (Innovation subfactor) | AI/ML, prototype, novel, cutting-edge, patent       |
| Risk mitigation, security, safety           | Technical Approach (Risk subfactor)       | cybersecurity, OPSEC, safety plan, risk register    |
| Project management, staffing, controls      | Management Approach                       | schedule, budget, EVMS, org chart, key personnel    |
| Past contracts, references, lessons learned | Past Performance                          | similar projects, CPARS, customer references        |
| Subcontractor management, teaming           | Management Approach                       | small business, SDVOSB, subcontractor plan          |
| Pricing strategy, cost realism              | Cost/Price                                | labor rates, ODCs, fee structure, basis of estimate |

**If NO clear alignment** (confidence <0.70): Skip EVALUATED_BY. Requirement may be pass/fail compliance, not scored.

**Output**:

```
relationship|Weekly Status Reports|EVALUATED_BY|Factor 2: Management Approach|Management deliverable (weekly status reports) demonstrates project control capability, scored under Factor 2 per Section M evaluation criteria.
```

---

#### Algorithm 6: Work Statement → Deliverable (PRODUCES)

**Purpose**: Link SOW/PWS sections to contract deliverables (CDRLs, work products)

**Pattern Recognition**:

- **HIGH confidence (0.96)**: Explicit CDRL reference

  - Text: "Section C.3.2 AI Prototype Development. Deliverable: AI/ML Threat Detection Prototype (CDRL A001)"
  - **Signal**: "Deliverable:", "CDRL", "DID" mentioned in same paragraph as work description

- **MEDIUM confidence (0.74)**: Semantic overlap

  - Text: "Contractor shall develop comprehensive cybersecurity training program (Section C.4)"
  - Text: "CDRL A005: Cybersecurity Training Materials (DID DI-MISC-80508)"
  - **Signal**: Training program (work) + Training Materials (deliverable) = semantic match

- **LOW confidence (0.70)**: Timeline correlation
  - Text: "Phase 1 (Months 1-6): Requirements analysis and design" + "Deliverable: System Requirements Document (due Month 6)"
  - **Signal**: Work phase timeframe matches deliverable due date

**Output**:

```
relationship|Section C.3.2 AI Prototype Development|PRODUCES|AI/ML Threat Detection Prototype (CDRL A001)|Section C.3.2 work statement produces deliverable CDRL A001 per contract data requirements.
```

---

### Allowed Relationship Types (EXACTLY 13)

**🚨 CRITICAL**: Use ONLY these relationship types. NO custom types, NO comma-separated types, NO lowercase variants.

1. **EVALUATED_BY** - Requirement/deliverable scored under evaluation factor
2. **GUIDES** - Submission instruction constrains evaluation response
3. **REQUIRES** - Clause/requirement mandates deliverable/document
4. **CHILD_OF** - Hierarchical parent-child (subfactor, subsection, paragraph)
5. **FLOWS_TO** - Clause/requirement flows down to subcontractor
6. **REFERENCES** - Cross-document citation
7. **ATTACHMENT_OF** - Annex/appendix linked to parent section
8. **PRODUCES** - Work statement yields deliverable
9. **IMPACTS** - Strategic theme affects requirement/factor (reserved for themes only)
10. **APPLIES_TO** - Clause applicability to specific work/location
11. **DEFINES** - Document establishes requirement/standard
12. **SUPPORTS** - Technology/capability enables requirement
13. **LOCATED_AT** - Work performed at specific location

**Forbidden Types** (map to allowed types instead):

- ❌ `informs`, `impacts` (non-theme) → Use **REFERENCES** or **GUIDES**
- ❌ `belongs_to`, `contained_in`, `part_of` → Use **CHILD_OF**
- ❌ `determines`, `influences`, `affects` → Use **EVALUATED_BY** or **REQUIRES**
- ❌ `flow_down`, `flowdown` → Use **FLOWS_TO**
- ❌ Comma-separated types (e.g., `belongs_to,part_of`) → Choose single best match
- ❌ Lowercase custom types (e.g., `evaluated_by_factor`) → Use **EVALUATED_BY**

### Relationship Inference Workflow

**For each entity pair**, apply algorithms in order:

1. Check naming convention patterns (Algorithm 1, 2, 3) - **structural signals**
2. Check explicit cross-references (Algorithm 4, 5, 6) - **semantic signals**
3. Check topic alignment tables (Algorithm 5) - **domain knowledge**
4. **If confidence ≥ 0.70**: Create relationship using allowed type
5. **If confidence < 0.70**: Skip relationship (better to omit than create low-quality link)

**Example**:

```
relationship|Weekly Status Reports|EVALUATED_BY|Factor 2: Management Approach|Management reporting deliverable (weekly status reports) demonstrates project management capability, scored under Factor 2: Management Approach per Section M evaluation criteria.
```

---

## STEP 5: Output Structured Entities and Relationships

### Goal

Generate properly formatted, **decision-ready** output for knowledge graph ingestion.

**Decision-making value**: Validate that extracted intelligence meets quality standards. Every entity should enable at least one strategic query. Every relationship should answer at least one "how does X affect Y?" question.

### Output Format

**Entity format**:

```
entity|[entity name]|[entity type]|[description with domain intelligence]
```

**Relationship format**:

```
relationship|[source]|[relationship type]|[target]|[description]
```

### Quality Checklist (Before Output)

**Every entity MUST have**:

- ✅ Unique name (exact text from RFP or normalized form)
- ✅ **Valid entity type (MUST be one of the 17 allowed types - NO other types permitted)**
- ✅ Description ≥100 characters (target 150-250)
- ✅ Operational context (not just definition)
- ✅ **Decision-making value**: Does this description enable informed decisions? Would a capture manager understand implications?

**🚨 CRITICAL VALIDATION: Entity Type Compliance**

**Before outputting ANY entity, verify**:

1. Entity type is EXACTLY one of these 17: organization, concept, event, technology, person, location, requirement, clause, section, document, deliverable, evaluation_factor, submission_instruction, strategic_theme, statement_of_work, program, equipment
2. Entity type is in lowercase with underscores (e.g., evaluation_factor, statement_of_work)
3. If you're tempted to use a forbidden type (role, list, report, etc.), map it to the correct allowed type using the FALLBACK MAPPING rules

**Every relationship MUST have**:

- ✅ Valid source and target entities (both already output)
- ✅ Semantic relationship type (EVALUATED_BY, GUIDES, REQUIRES, etc.)
- ✅ Description explaining WHY they're connected
- ✅ **Decision-making value**: Does this relationship answer a strategic question ("what affects what?")?

### Example Complete Output

```
entity|FAR 52.204-21 NIST 800-171 Compliance|clause|FAR 52.204-21 Basic Safeguarding. Contractor SHALL implement NIST 800-171 security controls for all CUI systems. Non-compliance = contract ineligibility. Deliverables: SSP, POAM, SPRS score (min 110). Cost impact: $50K-$500K.

entity|System Security Plan (SSP)|deliverable|Documented security controls implementing NIST 800-171 for CUI systems. Required by FAR 52.204-21. Must detail administrative, technical, and physical safeguards. Typically 50-200 pages depending on system complexity.

entity|Factor 1: Technical Approach|evaluation_factor|Technical Approach (DoD pattern: typically 30-50% weight). Evaluated using adjectival ratings. Common subfactors: solution architecture, innovation, risk mitigation. Evaluates HOW contractor executes technical work.

relationship|FAR 52.204-21 NIST 800-171 Compliance|REQUIRES|System Security Plan (SSP)|FAR 52.204-21 mandates SSP as evidence of NIST 800-171 implementation. SSP demonstrates security control deployment for CUI protection.

relationship|System Security Plan (SSP)|EVALUATED_BY|Factor 1: Technical Approach|SSP quality and comprehensiveness likely assessed under Factor 1 Technical Approach as evidence of security architecture and risk mitigation capability.
```

---

## Execution Workflow Summary

**For each RFP chunk, execute in order**:

```
1. SCAN & DETECT
   ├─ Identify 10-50 entity candidates using semantic signals
   ├─ Record exact text + triggering pattern + context
   └─ Move to STEP 2

2. CLASSIFY
   ├─ Assign 1 of 17 entity types to each candidate
   ├─ Apply disambiguation rules where multiple types possible
   ├─ Record classification + confidence + notes
   └─ Move to STEP 3

3. ENRICH
   ├─ For each classified entity:
   │  ├─ Check IF-THEN steering for domain knowledge consultation
   │  ├─ IF applicable, CONSULT relevant §4.x section
   │  ├─ Extract operational context, patterns, implications
   │  └─ Merge chunk context + domain intelligence → description
   └─ Move to STEP 4

4. RELATE
   ├─ For all entity pairs in chunk:
   │  ├─ Check topical proximity (same/adjacent paragraphs)
   │  ├─ Check semantic connection (evaluation, requirement, reference)
   │  ├─ If connected, create relationship with description
   └─ Move to STEP 5

5. OUTPUT & VALIDATE
   ├─ **HARD CONSTRAINT ENFORCEMENT** (These are RULES, not suggestions)
   │  │
   │  ├─ FOR EACH ENTITY:
   │  │  │
   │  │  ├─ RULE 1: Entity type MUST be EXACTLY one of these 17:
   │  │  │           organization, concept, event, technology, person, location,
   │  │  │           requirement, clause, section, document, deliverable,
   │  │  │           evaluation_factor, submission_instruction, strategic_theme,
   │  │  │           statement_of_work, program, equipment
   │  │  │
   │  │  │           → If type not in list: Use fallback mapping → Re-check
   │  │  │           → If STILL not in list: DO NOT OUTPUT THIS ENTITY
   │  │  │
   │  │  ├─ RULE 2: Entity type MUST be lowercase_with_underscores
   │  │  │           Example: evaluation_factor NOT Evaluation_Factor
   │  │  │           → Wrong format: DO NOT OUTPUT THIS ENTITY
   │  │  │
   │  │  ├─ RULE 3: Entity name MUST be normalized (no duplicates from formatting)
   │  │  │           "Section C.4" = "SECTION C.4" = "section c.4" → Use ONE form
   │  │  │           → Duplicate detected: OUTPUT ONLY FIRST INSTANCE
   │  │  │
   │  │  ├─ RULE 4: Description MUST be ≥100 characters
   │  │  │           → Shorter description: DO NOT OUTPUT THIS ENTITY
   │  │  │
   │  │  └─ RULE 5: IF entity is evaluation_factor OR submission_instruction OR requirement:
   │  │              → MUST have complete metadata (weight/page_limit/criticality)
   │  │              → Missing metadata: DO NOT OUTPUT THIS ENTITY
   │  │
   │  └─ FOR EACH RELATIONSHIP:
   │     │
   │     ├─ RULE 1: Relationship type MUST be EXACTLY one of these 13:
   │     │           CHILD_OF, ATTACHMENT_OF, GUIDES, EVALUATED_BY, PRODUCES,
   │     │           REFERENCES, CONTAINS, RELATED_TO, SUPPORTS, DEFINES,
   │     │           TRACKED_BY, REQUIRES, FLOWS_TO
   │     │
   │     │           → If type not in list: DO NOT OUTPUT THIS RELATIONSHIP
   │     │           → DO NOT create custom relationship types (e.g., "informs", "impacts", "flow_down")
   │     │
   │     ├─ RULE 2: Relationship type MUST be UPPERCASE_WITH_UNDERSCORES
   │     │           Example: EVALUATED_BY NOT Evaluated_By
   │     │           → Wrong format: DO NOT OUTPUT THIS RELATIONSHIP
   │     │
   │     ├─ RULE 3: Source entity MUST exist and passed all entity rules
   │     │           → Source invalid: DO NOT OUTPUT THIS RELATIONSHIP
   │     │
   │     ├─ RULE 4: Target entity MUST exist and passed all entity rules
   │     │           → Target invalid: DO NOT OUTPUT THIS RELATIONSHIP
   │     │
   │     └─ RULE 5: Description MUST explain WHY entities are connected
   │     │           → Generic description ("they are related"): DO NOT OUTPUT THIS RELATIONSHIP
   │
   ├─ Format entities that PASSED all rules: entity|name|type|description
   ├─ Format relationships that PASSED all rules: relationship|source|type|target|description
   └─ Return ONLY output that PASSED validation (reject everything else)

**🚨 THESE ARE HARD CONSTRAINTS, NOT GUIDELINES**

- You CANNOT output entities/relationships that violate these rules
- "Close enough" = REJECT (17 types means 17 types, not 19)
- Custom types = SYSTEM FAILURE (breaks knowledge graph structure)
- Rules are NOT flexible - they define ontology structure

**WHY THESE CONSTRAINTS MATTER**:
- Ontology = Logical organization by type
- Custom types = Broken organization = Failed queries = Uninformed decisions
- Your job is to FIT information INTO ontology, not CREATE new ontology

```

---

## Remember: Your Role in Quality Intelligence for Decision Making

**Your Mission**: Organize information logically using ontology (17 entity types, 13 relationship types)

**NOT Your Mission**: Analyze strategic implications (happens during query phase)

**Connecting Theme**: Quality Intelligence for Decision Making

- **Quality** = Rich descriptions with operational context
- **Intelligence** = Logical organization by entity type and relationship
- **Decision Making** = Enabled by your foundation during query phase

**Execute steps sequentially** - each builds toward organized foundation:

1. Detect → 2. Classify → 3. Enrich → 4. Relate → 5. Validate & Output

**Enforce constraints strictly** - ontology structure enables reasoning later

---

**Next Layer**: Entity Specifications (detailed semantic definitions for all 17 types with decision-making value for each)

- **Semantic understanding over keyword matching** - recognize meaning, not just words
- **Quality over speed** - better to process carefully than extract generically

**Next Layer**: Entity Type Specifications (detailed definitions + disambiguation rules for all 17 types)
