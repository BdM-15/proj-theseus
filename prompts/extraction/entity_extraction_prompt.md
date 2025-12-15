# Entity Extraction Prompt

**Purpose**: Extract government contracting entities and relationships from RFP documents  
**Model**: xAI Grok-4-fast-reasoning (2M context window, optimized for structured extraction)  
**Prompt Size**: ~5,593 tokens (0.28% of context window)  
**Entity Types**: 18 specialized government contracting types  
**Enhancements**:

- Domain knowledge patterns (FAR/DFARS, UCF, Shipley, CDRL)
- 5 annotated RFP examples (Section L↔M, requirements, attachments, clauses, deliverables)
- 8 decision rules for ambiguous cases (edge case handling)
- Location-agnostic extraction (content over location)
- **Rich descriptions required** (entity_name + description + type-specific metadata)
  **Last Updated**: December 13, 2025 (Branch 041 - Surgical Fix: Restore Descriptions)

---

## ⚠️ CRITICAL: PERFORMANCE_METRIC vs REQUIREMENT DISTINCTION

## ⚠️ CRITICAL: DESCRIPTIONS ARE REQUIRED

**ALWAYS include a `description` field for every entity.**

The description is essential for knowledge graph retrieval quality. Include:
- **Semantic context**: What this entity represents and why it matters
- **Source location**: Where in the document (e.g., "from Section C.3.2", "per PWS paragraph 4.1")
- **Key details**: Quantities, frequencies, constraints, relationships to other entities
- **Domain context**: FAR/DFARS implications, UCF section relevance

**Keep descriptions concise but informative** (50-200 words typical):
- `entity_name` (required)
- `entity_type` (required)
- `description` (required) - Comprehensive semantic context for retrieval
- Type-specific metadata fields (modal_verb, weight, frequency, etc.)

**Good description example**:
> "24/7 Help Desk support requirement from PWS Section 3.2.1. Contractor shall provide Tier 1 and Tier 2 technical support with 15-minute response SLA. Relates to Performance Metric PM-3 (Response Time). Critical for Task Order 0001 staffing."

**Bad description** (too short, no context):
> "Help desk support"

### PERFORMANCE_METRIC = Measurable Standard (How performance is judged)

**Trigger Phrases** - Extract as `performance_metric` when you see:

- "Performance Objective (PO-X)" or "PO-1", "PO-2", etc.
- "Performance Threshold:" or "Threshold:"
- "Acceptable Quality Level (AQL)"
- "Quality Assurance Surveillance Plan (QASP)"
- "Method of Surveillance:"
- Numerical standards: "99.9%", "Zero (0)", "No more than X", "At least Y%"
- "per month", "per week", "per quarter" with a metric value

**Structure Pattern**: Performance metrics often appear in tables with columns:

- Requirement | Standard | Surveillance Method
- Performance Objective | Threshold | Method of Surveillance

### REQUIREMENT = Action/Obligation (What contractor must DO)

**Trigger Phrases** - Extract as `requirement` when you see:

- "Contractor shall...", "Contractor must...", "Contractor will..."
- "The offeror shall...", "Personnel shall..."
- Action verbs: provide, maintain, perform, deliver, ensure, implement

### ⚡ SPLIT RULE: One Sentence → Two Entities

**When a sentence contains BOTH an action AND a metric, extract TWO entities!**

**Example Text:**

> "The Contractor shall clean equipment daily with no more than 2 defects per month."

**Extract as TWO entities:**

```json
{
  "entities": [
    {
      "entity_name": "Daily Equipment Cleaning",
      "entity_type": "requirement",
      "description": "The Contractor shall clean equipment daily.",
      "criticality": "MANDATORY",
      "modal_verb": "shall"
    },
    {
      "entity_name": "Equipment Cleaning Defect Threshold",
      "entity_type": "performance_metric",
      "description": "No more than 2 defects per month for equipment cleaning.",
      "threshold": "No more than 2 defects per month",
      "measurement_method": "Periodic Inspection (Monthly)"
    }
  ],
  "relationships": [
    {
      "source_entity": "Daily Equipment Cleaning",
      "target_entity": "Equipment Cleaning Defect Threshold",
      "relationship_type": "MEASURED_BY",
      "description": "Cleaning requirement performance is measured by defect threshold"
    }
  ]
}
```

### Real QASP Table Example

**Input Table:**
| Performance Objective | Performance Threshold | Surveillance Method |
|-----------------------|----------------------|---------------------|
| PO-1: Escort Monitoring | Zero (0) discrepancies per month | Periodic Inspection (Monthly) |
| PO-2: Equipment Availability | 95% operational per month | 100% Inspection |

**Extract as `performance_metric` entities (NOT requirements):**

```json
{
  "entities": [
    {
      "entity_name": "PO-1 Escort Monitoring Compliance",
      "entity_type": "performance_metric",
      "description": "PO-1: Escort Monitoring - Performance threshold for zero discrepancies in escort monitoring activities.",
      "threshold": "Zero (0) discrepancies per month",
      "measurement_method": "Periodic Inspection (Monthly)"
    },
    {
      "entity_name": "PO-2 Equipment Availability Standard",
      "entity_type": "performance_metric",
      "description": "PO-2: Equipment Availability - Performance threshold requiring 95% equipment operational status.",
      "threshold": "95% operational per month",
      "measurement_method": "100% Inspection"
    }
  ]
}
```

---

## ⚠️ STRATEGIC_THEME Detection (Shipley Capture Intelligence)

**Strategic themes are competitive intelligence extracted from RFP language. They reveal customer priorities and proposal positioning opportunities.**

### Theme Types (ThemeType enum)

1. **CUSTOMER_HOT_BUTTON**: Government's explicit emphasis or priority concern
2. **DISCRIMINATOR**: Key differentiator between competitors
3. **PROOF_POINT**: Evidence/past performance that validates capability
4. **WIN_THEME**: Overarching proposal messaging/positioning

### Detection Patterns

**CUSTOMER_HOT_BUTTON Detection:**

- "The Government places emphasis on..."
- "Critical to mission success is..."
- "Of paramount importance..."
- Evaluation factor weighted >30% (signals priority)
- "Key to success is..."
- "Offerors must demonstrate..."
- "Past performance demonstrating [X] is essential"
- Repeated emphasis on specific capability areas

**WIN_THEME / DISCRIMINATOR Detection:**

- Unique capability requirements that favor specific approaches
- Technology or methodology preferences stated in RFP
- Emphasis on innovation, cost savings, or efficiency
- References to lessons learned from previous contracts

**Example Extractions:**

**From Evaluation Criteria:**

> "Past performance demonstrating successful base operations support in austere environments is critical to source selection."

```json
{
  "entity_name": "Austere Environment Operations Experience",
  "entity_type": "strategic_theme",
  "description": "Past performance demonstrating successful base operations support in austere environments is critical to source selection.",
  "theme_type": "CUSTOMER_HOT_BUTTON"
}
```

**From PWS Emphasis:**

> "The Government emphasizes the importance of cultural sensitivity when managing OCN/LN workforce in host nation environments."

```json
{
  "entity_name": "Cultural Sensitivity in OCN/LN Management",
  "entity_type": "strategic_theme",
  "description": "Government emphasis on cultural sensitivity when managing OCN/LN workforce in host nation environments.",
  "theme_type": "CUSTOMER_HOT_BUTTON"
}
```

**From Weighted Factors:**

> "Factor 1: Mission Support Capability (45%) - Most Important"

```json
{
  "entity_name": "Mission Support Capability Priority",
  "entity_type": "strategic_theme",
  "description": "Mission Support Capability is weighted 45% and rated Most Important, indicating Government's top priority area.",
  "theme_type": "CUSTOMER_HOT_BUTTON"
}
```

---

---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.

---Instructions---

1.  **Entity Extraction & Output:**

    - **Identification:** Identify clearly defined and meaningful entities in the input text.
    - **Entity Details:** For each identified entity, extract the following information:

      - `entity_name`: The name of the entity. If the entity name is case-insensitive, capitalize the first letter of each significant word (title case). Ensure **consistent naming** across the entire extraction process.
      - `entity_type`: Categorize the entity using ONE of these exact types from the list below.

        **CRITICAL ENTITY NAMING NORMALIZATION RULES:**

        **Prevent duplicate entities due to formatting variations!** Government RFPs use inconsistent formatting:

        - Page titles: "SECTION C.4 - SUPPLY" (ALL CAPS)
        - Text references: "Section C.4" (Title Case)
        - Inline mentions: "section c.4" (lowercase)
        - Cross-references: "Sec C.4", "C.4", "Section C-4"

        **YOU MUST extract these as ONE entity, not multiple!**

        **Normalization Rules:**

        1. **Section Names**: Always use Title Case with periods

           - ✅ CORRECT: "Section C.4 Supply"
           - ❌ WRONG: "SECTION C.4", "section c.4", "Sec C.4", "Section C-4"
           - If section has a title (e.g., "- SUPPLY"), include it in normalized form

        2. **FAR/DFARS Clauses**: Always use exact citation format

           - ✅ CORRECT: "FAR 52.212-1"
           - ❌ WRONG: "far 52.212-1", "FAR 52.212.1", "FAR52.212-1"

        3. **CDRL/Deliverables**: Always use uppercase identifier + descriptive name

           - ✅ CORRECT: "CDRL A001 Monthly Status Report"
           - ❌ WRONG: "CDRL a001", "Cdrl A001", "cdrl A001"

        4. **Organizations/Programs**: Use official capitalization from context

           - ✅ CORRECT: "Marine Corps Prepositioning Program" or "MCPP II"
           - ❌ WRONG: "MARINE CORPS PREPOSITIONING PROGRAM", "mcpp ii"

        5. **When you see multiple formatting variations**:
           - Identify they refer to the same entity
           - Extract ONCE using the most complete, properly formatted version
           - Merge descriptions from all mentions using <SEP> separator

        **Example - Section with Multiple Formats:**

        Text contains:

        - Page 15 title: "SECTION C.4 - SUPPLY"
        - Page 27 reference: "per Section C.4"
        - Page 45 mention: "section c.4 requirements"

        Extract ONCE as:

        ```json
        {
          "entities": [
            {
              "entity_name": "Section C.4 Supply",
              "entity_type": "section",
              "description": "SECTION C.4 - SUPPLY. This section defines materiel requirements and supply chain specifications for the contract."
            }
          ],
          "relationships": []
        }
        ```

        NOT three separate entities!

        **Example - Clause with Variations:**

        Text contains:

        - "FAR 52.212-1 Instructions to Offerors"
        - "far 52.212-1"
        - "FAR clause 52.212-1"

        Extract ONCE as:

        ```json
        {
          "entities": [
            {
              "entity_name": "FAR 52.212-1",
              "entity_type": "clause",
              "description": "FAR 52.212-1 Instructions to Offerors—Commercial Products and Commercial Services (SEP 2023)",
              "clause_number": "52.212-1",
              "regulation": "FAR"
            }
          ],
          "relationships": []
        }
        ```

        **CRITICAL ENTITY TYPE RULES:**

        1. **Entity types MUST be lowercase with underscores** (e.g., evaluation_factor, statement_of_work)

        2. **You MUST use EXACTLY ONE of these 18 types for EVERY entity - NO EXCEPTIONS:**
           • organization
           • concept
           • event
           • technology
           • person
           • location
           • requirement
           • clause
           • section
           • document
           • deliverable
           • program
           • equipment
           • evaluation_factor
           • submission_instruction
           • strategic_theme
           • statement_of_work
           • performance_metric

        3. **STRICTLY FORBIDDEN entity types - NEVER USE THESE:**

           ❌ **other** - USE concept INSTEAD
           ❌ **UNKNOWN** - USE concept INSTEAD
           ❌ process - USE concept INSTEAD
           ❌ table - USE concept INSTEAD
           ❌ image - Skip extraction (not text entity)
           ❌ plan - USE document INSTEAD
           ❌ policy - USE document INSTEAD
           ❌ standard - USE document INSTEAD
           ❌ instruction - USE document INSTEAD
           ❌ system - USE technology INSTEAD
           ❌ regulation - USE document INSTEAD
           ❌ framework - USE concept INSTEAD
           ❌ objective - USE concept INSTEAD
           ❌ methodology - USE concept INSTEAD
           ❌ approach - USE concept INSTEAD
           ❌ strategy - USE concept INSTEAD
           ❌ model - USE concept INSTEAD

        4. **FALLBACK MAPPING (use when entity type is ambiguous):**

           - Business concepts, accounts, codes → **concept**
             Example: "MMFAQ9", "MMV200", "Business Systems" → concept

           - Plans, policies, standards, regulations, manuals → **document**
             Example: "Major Subordinate Element Plan", "Safety Plan" → document

           - Systems, tools, software, platforms → **technology**
             Example: "Electro-Optical" (tech category) → technology

           - Reports, forms, deliverables with reference numbers → **deliverable**
             Example: "10.B.8.a", "Mishap Report", "Selective Interchange Request" → deliverable

           - CLINs, SLINs, contract line items → **concept**
             Example: "CLIN 9005", "CLIN 0001 Base Year" → concept

           - DoD codes, activity codes, identifiers → **organization** (if unit) OR **concept** (if account)
             Example: "DODAAC M38450" → organization, "Account MMV200" → concept

           - Abstract ideas, processes, methodologies → **concept**
             Example: "Prepositioned Assets", "Supply Operations", "Column Headers" → concept

           - Size standards, classifications, categories → **concept**
             Example: "Small Business Size Standard" → concept

           **IF STILL UNCLEAR**: Default to **concept** (catch-all for abstract entities)

        5. **Example Classifications** (follow these patterns):

           **Plans/Policies/Standards → document:**

           - "Safety Plan" → document (NOT "plan")
           - "Quality Assurance Plan" → document (NOT "plan")
           - "Security Policy" → document (NOT "policy")
           - "Privacy Policy" → document (NOT "policy")
           - "MIL-STD-882E" → document (NOT "standard")
           - "ISO 9001:2015" → document (NOT "standard")
           - "Work Instruction 123" → document (NOT "instruction")
           - "DoD 5220.22-M" → document (NOT "regulation")
           - "Training Manual" → document (NOT "manual")

           **Systems/Tools → technology:**

           - "WAWF System" → technology (NOT "system")
           - "RFID System" → technology (NOT "system")
           - "ERP System" → technology (NOT "system")
           - "Microsoft Project" → technology (NOT "tool")
           - "Oracle Database" → technology (NOT "software")

           **Tables/Lists/Schedules → concept:**

           - "Table 1: Deliverables Schedule" → concept (NOT "table")
           - "Milestone Schedule" → concept (NOT "schedule")
           - "Pricing Matrix" → concept (NOT "matrix" or "table")
           - "Risk Matrix" → concept (NOT "matrix")
           - "Compliance Matrix" → concept (NOT "matrix")

           **Processes/Workflows → concept:**

           - "Continuous Process Improvement" → concept (NOT "process")
           - "Change Control Process" → concept (NOT "process")
           - "Approval Workflow" → concept (NOT "workflow")
           - "Shipley Methodology" → concept (NOT "methodology")

           **Ambiguous Technical Terms → Use context:**

           - "MCPP Program" → program (named initiative)
           - "MCPP II" → program (named initiative)
           - "Prepositioning Concept" → concept (abstract idea)
           - "Equipment Maintenance" → concept (activity/service)
           - "M1A1 Tank" → equipment (physical asset)
           - "Generator Set" → equipment (physical asset)

    - **Domain Knowledge - Government Contracting Patterns:**

      **FAR/DFARS Clause Recognition:**

      - FAR clauses: Format "FAR [Part].[Subpart]-[Number]" (e.g., FAR 52.212-1)
      - DFARS clauses: Format "DFARS 252.[Part]-[Number]" (e.g., DFARS 252.204-7012)
      - Agency supplements: AFFARS, NMCARS, DARS, TRANSFARS, etc.
      - Always extract as CLAUSE type, preserve full citation in entity_name

      **Deliverable Patterns (CDRL):**

      - Contract Data Requirements List items: CDRL A001, CDRL 6022, etc.
      - Extract as DELIVERABLE with full identifier preserved
      - DD Form 1423 references indicate deliverable tracking

      **Requirement Criticality (Shipley Methodology):**

      - SHALL/MUST = mandatory requirement (compliance required)
      - SHOULD = important but not mandatory (best practice)
      - MAY = optional (contractor discretion)
      - Extract modal verb context in description

      **Performance Metrics vs. Requirements (QASP Separation):**

      - **REQUIREMENT (Action)**: "Contractor shall clean equipment daily" (Workload)
      - **PERFORMANCE_METRIC (Measurement)**: "No more than 2 errors per month" (Surveillance)
      - **CRITICAL**: If a sentence contains BOTH, extract TWO entities!
        - Text: "Clean daily with 95% accuracy."
        - Entity 1 (REQUIREMENT): "Daily cleaning"
        - Entity 2 (PERFORMANCE_METRIC): "95% accuracy"

      **Program and Equipment Identification:**

      - Major acquisition programs: MCPP II, Navy MBOS, JPALS, etc.
      - Equipment with model numbers: Concorde RG-24, 6200 Tennant
      - Distinguish PROGRAM (services/initiatives) from EQUIPMENT (physical items)

    - **Decision Tree for Ambiguous Cases:**

      **Q: Document with "J-02000000 Performance Work Statement" - What entity type?**
      A: Extract as BOTH:

      - DOCUMENT type: "J-02000000 Performance Work Statement" (for section linkage)
      - STATEMENT_OF_WORK type: "Performance Work Statement" (for semantic content)
        Why: Preserves both structural (attachment) and semantic (work definition) relationships

      **Q: Text says "Clean daily; no more than 2 errors per month" - One entity or two?**
      A: TWO entities!

      - REQUIREMENT: "Daily cleaning" (The work to be done)
      - PERFORMANCE_METRIC: "No more than 2 errors per month" (The standard)
        Why: Workload (cost driver) must be separated from Surveillance (risk driver).

      **Q: Text says "Contractor shall have 5 years experience" - REQUIREMENT or EVALUATION_FACTOR?**
      A: REQUIREMENT (experience requirement)

      - If also mentioned in Section M, create second entity as EVALUATION_FACTOR
      - Link them: REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR
        Why: Requirements and evaluation are different concepts (what vs how scored)

      **Q: Clause text "The Government shall provide GFE within 30 days" - Extract as REQUIREMENT?**
      A: NO - Skip government obligations

      - Only extract contractor obligations (shall/must/should/may)
      - Government obligations are informational context, not requirements
        Why: Requirements = contractor obligations only

      **Q: Text says "CDRL A001 Monthly Status Report" in both Section C and Section J?**
      A: Extract ONCE as DELIVERABLE with full identifier "CDRL A001"

      - Link to both source sections if mentioned in multiple locations
      - Avoid duplicate entities (same CDRL = same deliverable)
        Why: Physical deliverables are unique, even if referenced multiple times

      **Q: "Navy MBOS Program" vs "Concorde RG-24 Battery" - How to distinguish?**
      A: Look for model numbers and physical characteristics:

      - PROGRAM: Services, initiatives, no model numbers (Navy MBOS, MCPP II)
      - EQUIPMENT: Model numbers, physical items (Concorde RG-24, 6200 Tennant)
        Why: Programs are abstract services; equipment is tangible hardware

      **Q: Section H says "Contractor shall maintain security clearances" - What type?**
      A: REQUIREMENT (special requirement from Section H)

      - Section H requirements are still requirements (location doesn't change type)
      - Extract modal verb (shall) and subject (security clearances)
        Why: Content-based typing, not location-based

      **Q: "Exhibit A - Pricing Schedule" - DOCUMENT or something else?**
      A: DOCUMENT (pricing attachment)

      - Extract individual prices/CLINs as CONCEPT entities if detailed
      - Link to Section B (Supplies/Prices) with ATTACHMENT_OF relationship
        Why: Pricing exhibits are documents containing structured data

      **Q: Text references "MIL-STD-882E" but document not attached?**
      A: DOCUMENT (referenced standard)

      - Extract with description noting it's referenced (not attached)
      - Create REFERENCES relationship from citing section
        Why: Referenced standards are still entities (even if external)

    - **Annotated RFP Examples:**

      **CRITICAL METADATA EXTRACTION REQUIREMENTS:**

      **For EVALUATION_FACTOR entities - ALWAYS extract:**

      1. **Relative importance hierarchy**: "Most Important", "Significantly More Important", "More Important", "Least Important"
      2. **Numerical weight (CRITICAL)**: Extract exact percentage or points if stated (e.g., "40%", "25 points", "300 points out of 1000")
      3. **Subfactor structure**: List subfactors with their individual weights if hierarchical (e.g., "B.1 Architecture 20%, B.2 Integration 15%")
      4. **Evaluation criteria**: What aspects/capabilities are evaluated (technical proficiency, past performance quality, staffing approach, etc.)

      **Examples of CORRECT evaluation factor descriptions:**

      - ✅ "Factor A Management Methodology worth 25% (Most Important) evaluating program management, staffing, and quality approach"
      - ✅ "Factor B USMC Technical worth 40% with subfactors: B.1 Architecture 20%, B.2 Integration 20%"
      - ✅ "Factor D Past Performance worth 300 points evaluating relevancy and confidence based on similar contracts"
      - ❌ "Technical approach factor" (missing weight, hierarchy, and evaluation criteria)

      **For SUBMISSION_INSTRUCTION entities - ALWAYS extract:**

      1. **Page limit**: Exact number with unit (e.g., "25 pages", "30 slides", "unlimited pages", "no page limit")
      2. **Format requirements**: Font size/type, margins, line spacing (e.g., "12-point Times New Roman, 1-inch margins, single-spaced")
      3. **Volume identifier**: Which volume/section this applies to (e.g., "Technical Volume", "Volume II Management Proposal")
      4. **Addressed factors**: Which evaluation factors this instruction guides (e.g., "addresses Factors 1 and 2")
      5. **Special constraints**: Cross-reference prohibitions, standalone requirements, submission format (e.g., "no cross-referencing", "PDF format")

      **Examples of CORRECT submission instruction descriptions:**

      - ✅ "Technical Approach Volume limited to 25 pages, 12-point Times New Roman font, 1-inch margins, must address Factors 1 and 2 (Technical and Maintenance Approach), standalone without cross-referencing other volumes"
      - ✅ "Management Volume limited to 15 pages addressing Factor A Management Methodology, font 12pt Times New Roman, margins 1-inch all sides"
      - ✅ "Oral Presentation limited to 30 slides, no additional materials, max 5 presenters, incorporated into Factors A-C evaluation"
      - ❌ "Technical volume requirements" (missing all structured metadata)

      **For REQUIREMENT entities - ALWAYS extract structured metadata:**

      **Criticality Classification (MANDATORY - include in every requirement description):**

      - **MANDATORY**: SHALL/MUST/WILL (with contractor/offeror as subject) - Zero defects, non-negotiable compliance
      - **IMPORTANT**: SHOULD (with contractor/offeror as subject) - High priority, best practice, expected but not absolute
      - **OPTIONAL**: MAY (with contractor/offeror as subject) - Contractor discretion, alternative approaches acceptable
      - **INFORMATIONAL**: SHALL/MUST with Government as subject - NOT a contractor requirement, skip extraction or extract as CONCEPT

      **Description Format Template:**
      "[CRITICALITY: MANDATORY|IMPORTANT|OPTIONAL] [Modal verb: shall|should|may|must|will] [Subject: Contractor/Offeror/Personnel] - [Requirement text with context including ALL quantitative metrics, hours, counts, and frequencies] - [Rationale or evaluation linkage if stated]"

      **CRITICAL: QUANTITATIVE PRECISION**
      You MUST include specific numbers, hours, dollars, frequencies, and equipment counts in the description.

      - ❌ Generic: "Contractor shall provide help desk support."
      - ✅ Specific: "Contractor shall provide 24/7 help desk support with 4-hour response time for 500 users."
      - ❌ Generic: "Contractor shall clean the facility."
      - ✅ Specific: "Contractor shall clean 50,000 sq ft facility daily and strip floors semi-annually."

      **Examples of CORRECT requirement descriptions:**

      - ✅ "[MANDATORY] Contractor shall maintain ISO 9001:2015 certification throughout contract period - Quality assurance requirement for all deliverables"
      - ✅ "[IMPORTANT] Contractor should implement automated monitoring tools for system anomaly detection - Best practice for operational excellence"
      - ✅ "[OPTIONAL] Contractor may use commercial off-the-shelf (COTS) solutions where appropriate - Flexibility in technical approach"
      - ✅ "[MANDATORY] Personnel shall comply with 29 CFR 1910 safety standards - Safety requirement for all explosive handling operations"
      - ❌ "Maintain ISO certification" (missing criticality, modal verb, and subject context)
      - ❌ "Government shall provide GFE within 30 days" (Government obligation - DO NOT extract as REQUIREMENT)

      **Extraction Decision Tree for Requirements:**

      1. Identify modal verb: shall/should/may/must/will
      2. Identify subject: Who has the obligation?
         - If Contractor/Offeror/Personnel → Extract as REQUIREMENT with appropriate criticality
         - If Government/Agency → Skip (informational context only) OR extract as CONCEPT if significant
      3. Map criticality: shall/must/will → MANDATORY, should → IMPORTANT, may → OPTIONAL
      4. Structure description with bracketed metadata prefix

      **Example 1: Section L ↔ Section M Mapping**

      Input Text:

      ```
      Section L.3.1 Technical Volume

      The Technical Volume shall address Evaluation Factors 1 and 2 (Technical
      Approach and Maintenance Approach) and shall not exceed 25 pages, 12-point
      font, Times New Roman. Include system architecture diagrams and integration
      plans.

      Section M: Evaluation Factors

      Factor 1: Technical Approach (Most Important, 40%)
      The Government will evaluate the offeror's understanding of technical
      requirements, including system architecture and integration methodology.

      Factor 2: Maintenance Approach (Significantly More Important, 30%)
      The Government will evaluate the offeror's maintenance strategy and
      sustainment plans.
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Technical Volume",
          "entity_type": "submission_instruction",
          "description": "The Technical Volume shall address Evaluation Factors 1 and 2 (Technical Approach and Maintenance Approach) and shall not exceed 25 pages, 12-point font, Times New Roman. Include system architecture diagrams and integration plans.",
          "page_limit": "25 pages",
          "format_reqs": "12pt Times New Roman"
        },
        {
          "entity_name": "Factor 1 Technical Approach",
          "entity_type": "evaluation_factor",
          "description": "Factor 1: Technical Approach (Most Important, 40%) The Government will evaluate the offeror's understanding of technical requirements, including system architecture and integration methodology.",
          "weight": "40%",
          "importance": "Most Important"
        },
        {
          "entity_name": "Factor 2 Maintenance Approach",
          "entity_type": "evaluation_factor",
          "description": "Factor 2: Maintenance Approach (Significantly More Important, 30%) The Government will evaluate the offeror's maintenance strategy and sustainment plans.",
          "weight": "30%",
          "importance": "Significantly More Important"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Technical Volume",
            "entity_type": "submission_instruction"
          },
          "target_entity": {
            "entity_name": "Factor 1 Technical Approach",
            "entity_type": "evaluation_factor"
          },
          "relationship_type": "GUIDES"
        },
        {
          "source_entity": {
            "entity_name": "Technical Volume",
            "entity_type": "submission_instruction"
          },
          "target_entity": {
            "entity_name": "Factor 2 Maintenance Approach",
            "entity_type": "evaluation_factor"
          },
          "relationship_type": "GUIDES"
        }
      ]
      ```

      **Example 2: Requirements with Criticality and Workload Drivers (Real PWS)**

      Input Text:

      ```
      F.2. COMMUNITY RECREATIONAL PROGRAM (CRP): The Contractor shall implement
      and maintain the CRP to support all morale welfare and recreation events
      and activities described in this section of the PWS. Approximately 1,600
      customers visit all CRP locations on a daily basis. The Contractor shall
      ensure all personnel supporting the CRP are trained and all locations'
      customer service desks are always covered with no more than two (2) customer
      service desks coverage discrepancies allowed per month. Unless otherwise
      stated, the Contractor shall support the CRP 24 hours a day / 7 days a week.

      The Government shall provide facilities for CRP operations.
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Community Recreational Program Implementation",
          "entity_type": "requirement",
          "description": "The Contractor shall implement and maintain the CRP to support all morale welfare and recreation events and activities described in this section of the PWS. Approximately 1,600 customers visit all CRP locations on a daily basis.",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "req_type": "FUNCTIONAL",
          "labor_drivers": [
            "1,600 customers daily",
            "24 hours a day / 7 days a week"
          ],
          "material_needs": []
        },
        {
          "entity_name": "CRP Customer Service Desk Coverage",
          "entity_type": "requirement",
          "description": "The Contractor shall ensure all personnel supporting the CRP are trained and all locations' customer service desks are always covered with no more than two (2) customer service desks coverage discrepancies allowed per month.",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "req_type": "PERFORMANCE",
          "labor_drivers": [
            "customer service desks always covered",
            "no more than 2 discrepancies per month"
          ],
          "material_needs": []
        },
        {
          "entity_name": "CRP 24/7 Support",
          "entity_type": "requirement",
          "description": "Unless otherwise stated, the Contractor shall support the CRP 24 hours a day / 7 days a week.",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "req_type": "FUNCTIONAL",
          "labor_drivers": ["24 hours a day", "7 days a week"],
          "material_needs": []
        },
        {
          "entity_name": "Customer Service Desk Coverage Threshold",
          "entity_type": "performance_metric",
          "description": "no more than two (2) customer service desks coverage discrepancies allowed per month",
          "threshold": "no more than 2 discrepancies per month",
          "measurement_method": "Periodic Inspection (Monthly)"
        },
        {
          "entity_name": "Government Furnished Facilities",
          "entity_type": "concept",
          "description": "The Government shall provide facilities for CRP operations."
        }
      ]
      ```

      Note:

      - "Contractor shall" → REQUIREMENT with MANDATORY criticality
      - Workload drivers captured: "1,600 customers daily", "24/7"
      - Performance metric separated from requirement
      - "Government shall" → CONCEPT (not a contractor requirement)

      **Example 3: PWS Appendix Structure (Real PWS)**

      Input Text:

      ```
      1.1. SCOPE. The Contractor shall provide support as specified in this PWS
      for an average base population of 1,600 personnel of various categories,
      to include transient, permanent party, and rotational personnel during
      the year. During rotational periods, the base population can increase up
      to 4,000 personnel. This Performance Work Statement (PWS) addresses the
      following requirements:

      1.1.1. Appendix F – Recreational Services
      1.1.2. Appendix G – Lodging Logistics Operations and Linen Support
      1.1.3. Appendix H - Equipment and Appliance Maintenance
      1.1.4. Appendix I – Water Delivery
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "PWS Scope",
          "entity_type": "statement_of_work",
          "description": "The Contractor shall provide support as specified in this PWS for an average base population of 1,600 personnel of various categories, to include transient, permanent party, and rotational personnel during the year. During rotational periods, the base population can increase up to 4,000 personnel."
        },
        {
          "entity_name": "Appendix F Recreational Services",
          "entity_type": "document",
          "description": "Appendix F – Recreational Services"
        },
        {
          "entity_name": "Appendix G Lodging Logistics",
          "entity_type": "document",
          "description": "Appendix G – Lodging Logistics Operations and Linen Support"
        },
        {
          "entity_name": "Appendix H Equipment Maintenance",
          "entity_type": "document",
          "description": "Appendix H - Equipment and Appliance Maintenance"
        },
        {
          "entity_name": "Appendix I Water Delivery",
          "entity_type": "document",
          "description": "Appendix I – Water Delivery"
        },
        {
          "entity_name": "Base Population Workload",
          "entity_type": "concept",
          "description": "average base population of 1,600 personnel of various categories, to include transient, permanent party, and rotational personnel during the year. During rotational periods, the base population can increase up to 4,000 personnel."
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Appendix F Recreational Services",
            "entity_type": "document"
          },
          "target_entity": {
            "entity_name": "PWS Scope",
            "entity_type": "statement_of_work"
          },
          "relationship_type": "CHILD_OF"
        },
        {
          "source_entity": {
            "entity_name": "Appendix H Equipment Maintenance",
            "entity_type": "document"
          },
          "target_entity": {
            "entity_name": "PWS Scope",
            "entity_type": "statement_of_work"
          },
          "relationship_type": "CHILD_OF"
        }
      ]
      ```

      Note: PWS extracted with appendix hierarchy. Workload drivers (1,600-4,000 personnel) captured as concept.

      **Example 4: FAR and DFARS Clauses (from Section I)**

      Input Text:

      ```
      SECTION I - CONTRACT CLAUSES

      52.203-3 GRATUITIES (APR 1984)
      52.203-5 COVENANT AGAINST CONTINGENT FEES (MAY 2014)
      52.204-7 System for Award Management (OCT 2018)
      52.212-4 CONTRACT TERMS AND CONDITIONS—COMMERCIAL ITEMS (FEB 2024)
      252.204-7012 SAFEGUARDING COVERED DEFENSE INFORMATION AND CYBER INCIDENT REPORTING (JAN 2023)
      252.225-7001 BUY AMERICAN AND BALANCE OF PAYMENTS PROGRAM (DEC 2017)
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Section I Contract Clauses",
          "entity_type": "section",
          "description": "SECTION I - CONTRACT CLAUSES"
        },
        {
          "entity_name": "FAR 52.203-3 Gratuities",
          "entity_type": "clause",
          "description": "52.203-3 GRATUITIES (APR 1984)"
        },
        {
          "entity_name": "FAR 52.204-7 System for Award Management",
          "entity_type": "clause",
          "description": "52.204-7 System for Award Management (OCT 2018)"
        },
        {
          "entity_name": "FAR 52.212-4 Contract Terms Commercial Items",
          "entity_type": "clause",
          "description": "52.212-4 CONTRACT TERMS AND CONDITIONS—COMMERCIAL ITEMS (FEB 2024)"
        },
        {
          "entity_name": "DFARS 252.204-7012 Cybersecurity",
          "entity_type": "clause",
          "description": "252.204-7012 SAFEGUARDING COVERED DEFENSE INFORMATION AND CYBER INCIDENT REPORTING (JAN 2023)"
        },
        {
          "entity_name": "DFARS 252.225-7001 Buy American",
          "entity_type": "clause",
          "description": "252.225-7001 BUY AMERICAN AND BALANCE OF PAYMENTS PROGRAM (DEC 2017)"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "FAR 52.203-3 Gratuities",
            "entity_type": "clause"
          },
          "target_entity": {
            "entity_name": "Section I Contract Clauses",
            "entity_type": "section"
          },
          "relationship_type": "CHILD_OF"
        },
        {
          "source_entity": {
            "entity_name": "DFARS 252.204-7012 Cybersecurity",
            "entity_type": "clause"
          },
          "target_entity": {
            "entity_name": "Section I Contract Clauses",
            "entity_type": "section"
          },
          "relationship_type": "CHILD_OF"
        }
      ]
      ```

      Note: Clause citations extracted verbatim with date references preserved.

      **Example 5: Deliverables and CDRL Linkage (from real PWS)**

      Input Text:

      ```
      PWS Section 3.4: Reporting Requirements

      The Contractor shall provide monthly status reports to the Contracting Officer
      Representative (COR) no later than the 10th calendar day following each month.
      Reports shall include program metrics, performance issues, and corrective actions.

      The Contractor shall maintain all documentation in the Government-provided
      electronic management system IAW CDRL A001 through CDRL A005.
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Monthly Status Reports",
          "entity_type": "deliverable",
          "description": "The Contractor shall provide monthly status reports to the Contracting Officer Representative (COR) no later than the 10th calendar day following each month.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Program Metrics Documentation",
          "entity_type": "deliverable",
          "description": "Reports shall include program metrics, performance issues, and corrective actions.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "CDRL A001",
          "entity_type": "deliverable",
          "description": "The Contractor shall maintain all documentation in the Government-provided electronic management system IAW CDRL A001 through CDRL A005."
        },
        {
          "entity_name": "Contracting Officer Representative",
          "entity_type": "organization",
          "description": "The Contractor shall provide monthly status reports to the Contracting Officer Representative (COR)"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Monthly Status Reports",
            "entity_type": "deliverable"
          },
          "target_entity": {
            "entity_name": "CDRL A001",
            "entity_type": "deliverable"
          },
          "relationship_type": "TRACKED_BY"
        },
        {
          "source_entity": {
            "entity_name": "Monthly Status Reports",
            "entity_type": "deliverable"
          },
          "target_entity": {
            "entity_name": "Contracting Officer Representative",
            "entity_type": "organization"
          },
          "relationship_type": "SUBMITTED_TO"
        }
      ]
      ```

      Note: Deliverables extracted with verbatim PWS language including due dates and CDRL references.

      **Example 6: Section L ↔ M Relationship (Evaluation Factors)**

      Input Text:

      ```
      Section L.4.2: Technical Capability Volume

      The Technical Capability Volume shall not exceed 30 pages and must address
      all technical requirements in the PWS. Offerors shall demonstrate their
      approach to meeting performance standards and quality requirements.

      Section M.2: Evaluation Factor 2 - Technical Capability (40%)

      The Government will evaluate the offeror's technical approach, including:
      (a) Understanding of requirements
      (b) Approach to performance standards
      (c) Quality management methodology
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Technical Capability Volume",
          "entity_type": "submission_instruction",
          "description": "The Technical Capability Volume shall not exceed 30 pages and must address all technical requirements in the PWS.",
          "page_limit": "30 pages",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Evaluation Factor 2 Technical Capability",
          "entity_type": "evaluation_factor",
          "description": "Section M.2: Evaluation Factor 2 - Technical Capability (40%)",
          "weight": "40%"
        },
        {
          "entity_name": "Understanding of Requirements",
          "entity_type": "evaluation_factor",
          "description": "(a) Understanding of requirements",
          "importance": "subfactor"
        },
        {
          "entity_name": "Approach to Performance Standards",
          "entity_type": "evaluation_factor",
          "description": "(b) Approach to performance standards",
          "importance": "subfactor"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Technical Capability Volume",
            "entity_type": "submission_instruction"
          },
          "target_entity": {
            "entity_name": "Evaluation Factor 2 Technical Capability",
            "entity_type": "evaluation_factor"
          },
          "relationship_type": "GUIDES"
        },
        {
          "source_entity": {
            "entity_name": "Understanding of Requirements",
            "entity_type": "evaluation_factor"
          },
          "target_entity": {
            "entity_name": "Evaluation Factor 2 Technical Capability",
            "entity_type": "evaluation_factor"
          },
          "relationship_type": "CHILD_OF"
        }
      ]
      ```

      Note: Section L submission instructions GUIDE Section M evaluation factors - critical for proposal development.

      **Example 7: Quality Requirements with Performance Standards**

      Input Text:

      ```
      PWS Section 4.2: Quality Control Requirements

      The Contractor shall maintain a Quality Control Program (QCP) that ensures
      all services meet the performance standards specified herein. The QCP shall
      include deficiency identification, corrective action procedures, and root
      cause analysis methodology.

      The Contractor shall achieve a minimum 95% customer satisfaction rating
      as measured by quarterly surveys. Response time for emergency work orders
      shall not exceed 4 hours.
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Quality Control Program",
          "entity_type": "requirement",
          "description": "The Contractor shall maintain a Quality Control Program (QCP) that ensures all services meet the performance standards specified herein.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Deficiency Identification Procedures",
          "entity_type": "requirement",
          "description": "The QCP shall include deficiency identification, corrective action procedures, and root cause analysis methodology.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Customer Satisfaction Rating Standard",
          "entity_type": "requirement",
          "description": "The Contractor shall achieve a minimum 95% customer satisfaction rating as measured by quarterly surveys.",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "performance_standard": "95% minimum"
        },
        {
          "entity_name": "Emergency Response Time Standard",
          "entity_type": "requirement",
          "description": "Response time for emergency work orders shall not exceed 4 hours.",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "performance_standard": "4 hours maximum"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Customer Satisfaction Rating Standard",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "Quality Control Program",
            "entity_type": "requirement"
          },
          "relationship_type": "SUPPORTS"
        },
        {
          "source_entity": {
            "entity_name": "Deficiency Identification Procedures",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "Quality Control Program",
            "entity_type": "requirement"
          },
          "relationship_type": "CHILD_OF"
        }
      ]
      ```

      Note: Requirements extracted with verbatim performance standards. Modal verbs (shall/should) indicate criticality.

      **Example 8: Operational Requirements with Workload Metrics (from real PWS)**

      Input Text:

      ```
      F.2.3.1. C.A.C Customer Service Counter and Indoor Bar: The Contractor shall handle resale
      requirements to include alcohol sales. The Contractor shall service:
      1) One (1) inside bar with two (2) registers located in the C.A.C.
      2) One (1) additional outside bar with two (2) registers during special events.
      3) One (1) additional bar with one (1) register located in Phantom Auditorium during special
      events and reserved activities.

      Cash registers require USN staff personnel only. The Contractor shall verify all resale supplies
      necessary to ensure items are properly stocked at all times. The Contractor shall notify the
      Government when resale supply levels are low, and items need to be ordered. The Government
      will procure the resale supplies. Contractor personnel shall provide retail services at minimum
      rates of one (1) customer per minute during normal operations and three (3) customers per
      minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100) or during special
      events (e.g., concerts, 4-drink nights, community events, all calls, promotions, wing ceremonies,
      etc.). The Contractor shall open the outside bar for special events as requested by the COR. The
      Government will send requests to open the outside bar for special events in writing a minimum
      of seven (7) calendar days prior to the event. This is estimated to occur 100 times per year.
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "C.A.C. Customer Service Counter and Indoor Bar",
          "entity_type": "requirement",
          "description": "F.2.3.1. C.A.C Customer Service Counter and Indoor Bar: The Contractor shall handle resale requirements to include alcohol sales.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Bar Service Configuration",
          "entity_type": "requirement",
          "description": "The Contractor shall service: 1) One (1) inside bar with two (2) registers located in the C.A.C. 2) One (1) additional outside bar with two (2) registers during special events. 3) One (1) additional bar with one (1) register located in Phantom Auditorium during special events and reserved activities.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Resale Supply Verification",
          "entity_type": "requirement",
          "description": "The Contractor shall verify all resale supplies necessary to ensure items are properly stocked at all times. The Contractor shall notify the Government when resale supply levels are low, and items need to be ordered.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Retail Service Rate Standard",
          "entity_type": "requirement",
          "description": "Contractor personnel shall provide retail services at minimum rates of one (1) customer per minute during normal operations and three (3) customers per minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100) or during special events",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "performance_standard": "1 customer/min normal, 3 customers/min peak"
        },
        {
          "entity_name": "Outside Bar Special Events Support",
          "entity_type": "requirement",
          "description": "The Contractor shall open the outside bar for special events as requested by the COR. The Government will send requests to open the outside bar for special events in writing a minimum of seven (7) calendar days prior to the event. This is estimated to occur 100 times per year.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Peak Service Hours",
          "entity_type": "concept",
          "description": "peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100) or during special events (e.g., concerts, 4-drink nights, community events, all calls, promotions, wing ceremonies, etc.)"
        },
        {
          "entity_name": "Special Events Frequency",
          "entity_type": "concept",
          "description": "This is estimated to occur 100 times per year."
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Retail Service Rate Standard",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "Peak Service Hours",
            "entity_type": "concept"
          },
          "relationship_type": "REFERENCES"
        },
        {
          "source_entity": {
            "entity_name": "Outside Bar Special Events Support",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "Special Events Frequency",
            "entity_type": "concept"
          },
          "relationship_type": "REFERENCES"
        },
        {
          "source_entity": {
            "entity_name": "Bar Service Configuration",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "C.A.C. Customer Service Counter and Indoor Bar",
            "entity_type": "requirement"
          },
          "relationship_type": "CHILD_OF"
        }
      ]
      ```

      Note: Verbatim extraction preserves performance standards (1 customer/min, 3 customers/min), time windows, and workload estimates (100 times/year). Modal verb "shall" indicates mandatory requirements.

      **Example 9: Government Furnished Property and CDRL Requirements (from real PWS)**

      Input Text:

      ```
      Government Furnished Property Reporting – The Contractor shall report GFP to the
      Contracting Officer within the task order specific time limits and using the current
      version of Government-furnished forms. [CDRL A016]. The Contractor shall report GFP:
      within 30 calendar days after the start of the period of performance, not later than
      30 calendar days prior to the end of the period of performance, and at a minimum annually.
      The Contractor shall base reports on physical inventories.

      Date of First Submission: Thirty (30) calendar days after the start of the Period of
      Performance (POP)
      Frequency: As required
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Government Furnished Property Reporting",
          "entity_type": "requirement",
          "description": "Government Furnished Property Reporting – The Contractor shall report GFP to the Contracting Officer within the task order specific time limits and using the current version of Government-furnished forms. [CDRL A016].",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "GFP Report Initial Submission",
          "entity_type": "deliverable",
          "description": "The Contractor shall report GFP: within 30 calendar days after the start of the period of performance",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "GFP Report Final Submission",
          "entity_type": "deliverable",
          "description": "not later than 30 calendar days prior to the end of the period of performance",
          "criticality": "MANDATORY"
        },
        {
          "entity_name": "GFP Physical Inventory Requirement",
          "entity_type": "requirement",
          "description": "The Contractor shall base reports on physical inventories.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "CDRL A016",
          "entity_type": "deliverable",
          "description": "[CDRL A016]"
        },
        {
          "entity_name": "Contracting Officer",
          "entity_type": "organization",
          "description": "The Contractor shall report GFP to the Contracting Officer"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Government Furnished Property Reporting",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "CDRL A016",
            "entity_type": "deliverable"
          },
          "relationship_type": "TRACKED_BY"
        },
        {
          "source_entity": {
            "entity_name": "GFP Report Initial Submission",
            "entity_type": "deliverable"
          },
          "target_entity": {
            "entity_name": "Government Furnished Property Reporting",
            "entity_type": "requirement"
          },
          "relationship_type": "CHILD_OF"
        },
        {
          "source_entity": {
            "entity_name": "Government Furnished Property Reporting",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "Contracting Officer",
            "entity_type": "organization"
          },
          "relationship_type": "SUBMITTED_TO"
        }
      ]
      ```

      Note: CDRL references extracted verbatim. Due dates and frequency preserved exactly as stated in source.

      **Example 10: Special Events and Training Requirements (from real PWS)**

      Input Text:

      ```
      F.2.4. Special Events: The Contractor shall arrange special events including live bands,
      shows, Armed Forces Entertainment, game shows, theme nights, and other similar events.
      Special events may require coordination through the 380 AEW. The COR must be notified
      of special events at least two (2) weeks prior to each planned event to ensure proper
      coordination.

      F.2.3.2. Alcohol Management: All Contractor personnel must complete DRAM shop training
      prior to serving/selling alcohol and have proper training documentation on file with the
      Community Services Flight Chief. The Contractor shall use the approved Alcohol Management
      System provided by the Government. The Contractor shall track alcohol sales and strictly
      enforce alcohol limitations IAW AFCENT and 380 AEW alcohol policies with no violations allowed.
      ```

      Extracted Entities:

      ```json
      [
        {
          "entity_name": "Special Events Arrangement",
          "entity_type": "requirement",
          "description": "F.2.4. Special Events: The Contractor shall arrange special events including live bands, shows, Armed Forces Entertainment, game shows, theme nights, and other similar events.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Special Events Notification",
          "entity_type": "requirement",
          "description": "The COR must be notified of special events at least two (2) weeks prior to each planned event to ensure proper coordination.",
          "criticality": "MANDATORY",
          "modal_verb": "must"
        },
        {
          "entity_name": "DRAM Shop Training Requirement",
          "entity_type": "requirement",
          "description": "All Contractor personnel must complete DRAM shop training prior to serving/selling alcohol and have proper training documentation on file with the Community Services Flight Chief.",
          "criticality": "MANDATORY",
          "modal_verb": "must"
        },
        {
          "entity_name": "Alcohol Management System Usage",
          "entity_type": "requirement",
          "description": "The Contractor shall use the approved Alcohol Management System provided by the Government.",
          "criticality": "MANDATORY",
          "modal_verb": "shall"
        },
        {
          "entity_name": "Alcohol Policy Compliance",
          "entity_type": "requirement",
          "description": "The Contractor shall track alcohol sales and strictly enforce alcohol limitations IAW AFCENT and 380 AEW alcohol policies with no violations allowed.",
          "criticality": "MANDATORY",
          "modal_verb": "shall",
          "performance_standard": "zero violations"
        },
        {
          "entity_name": "380 AEW",
          "entity_type": "organization",
          "description": "Special events may require coordination through the 380 AEW."
        },
        {
          "entity_name": "Community Services Flight Chief",
          "entity_type": "organization",
          "description": "have proper training documentation on file with the Community Services Flight Chief"
        },
        {
          "entity_name": "AFCENT Alcohol Policy",
          "entity_type": "document",
          "description": "IAW AFCENT and 380 AEW alcohol policies"
        }
      ]
      ```

      Extracted Relationships:

      ```json
      [
        {
          "source_entity": {
            "entity_name": "Special Events Arrangement",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "380 AEW",
            "entity_type": "organization"
          },
          "relationship_type": "COORDINATED_WITH"
        },
        {
          "source_entity": {
            "entity_name": "DRAM Shop Training Requirement",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "Community Services Flight Chief",
            "entity_type": "organization"
          },
          "relationship_type": "REPORTED_TO"
        },
        {
          "source_entity": {
            "entity_name": "Alcohol Policy Compliance",
            "entity_type": "requirement"
          },
          "target_entity": {
            "entity_name": "AFCENT Alcohol Policy",
            "entity_type": "document"
          },
          "relationship_type": "GOVERNED_BY"
        }
      ]
      ```

      Note: Training requirements and compliance standards extracted verbatim. Zero-tolerance policy ("no violations allowed") captured as performance_standard.

    - **Relationship Patterns to Recognize:**

      **CRITICAL MANDATE: Extract ALL Implicit Relationships**

      You MUST extract relationships even when not explicitly stated. Use semantic understanding:

      - If entities share topics/keywords → Create RELATED_TO relationship
      - If naming patterns suggest hierarchy → Create CHILD_OF/ATTACHMENT_OF relationship
      - If content similarity indicates connection → Create appropriate relationship
      - DO NOT require explicit phrases like "addresses Factor 1" - INFER from context!
      - **AGGRESSIVE EXTRACTION**: Create 5-10 relationships per entity on average (not 1-2)
      - **SEMANTIC CONNECTIONS**: Use domain knowledge to infer unstated relationships
      - **CROSS-REFERENCE**: Link entities across different sections based on topic similarity

      **Section L ↔ Section M Links (AGGRESSIVE EXTRACTION):**

      - Submission instructions (Section L) often correspond to evaluation factors (Section M)
      - Extract relationships based on:
        1. **Explicit cross-reference**: "Volume addresses Factor 2" → GUIDES (confidence: 0.95)
        2. **Topic matching**: "Technical Volume" + "Technical Approach factor" → GUIDES (confidence: 0.80)
        3. **Keyword overlap**: Similar terms in both descriptions → GUIDES (confidence: 0.70)
      - Create GUIDES relationships for ANY semantic connection, not just explicit mentions
      - If page limits mentioned near factor → Create GUIDES relationship
      - If instruction discusses same topic as factor → Create GUIDES relationship

      **Attachment/Annex Hierarchy (Semantic + Pattern-Based):**

      - Attachments vary by agency: J-0001, Attachment 1, Annex A, Exhibit B, Enclosure 1
      - Extract ATTACHMENT_OF relationships based on:
        1. **Explicit listing**: "Section J: List of Attachments" → ATTACHMENT_OF
        2. **Naming patterns**: "J-0001" prefix + "Section J" reference → ATTACHMENT_OF
        3. **Structural context**: Document mentioned within section → ATTACHMENT_OF
      - SOW/PWS location varies: May be Section C, attachment, or annex
      - Requirements may appear in: Section C, attachments, Section H, or technical annexes
      - Extract with full identifier preserved, type based on content not location
      - Link DOCUMENT entities to their parent SECTION using ATTACHMENT_OF or CHILD_OF

      **Clause Clustering (Pattern + Semantic):**

      - FAR/DFARS clauses in Section I belong to that section
      - Create CHILD_OF relationships when:
        1. Clause mentioned within Section I description
        2. Clause has FAR/DFARS pattern and Section I exists
        3. Multiple clauses share same parent section
      - Group related clauses even if not explicitly stated

      **Requirement Traceability (Semantic Linking):**

      - Requirements may appear in: Section C (SOW), attachments (PWS), Section H (special requirements)
      - All requirements may be evaluated in Section M regardless of source location
      - Extract EVALUATED_BY relationships when:
        1. Requirement topic matches evaluation factor topic
        2. Requirement mentions evaluation-related terms (scoring, assessment, review)
        3. Semantic similarity between requirement description and factor description
      - Deliverables (CDRL) stem from requirements wherever they appear
      - Link REQUIREMENT to EVALUATION_FACTOR using EVALUATED_BY when semantic connection exists
      - Type based on content (SHALL/MUST/SHOULD/MAY), not document location

      **Deliverable Production (Semantic + Pattern):**

      - Create PRODUCES relationships when:
        1. SOW/PWS mentions deliverable names (explicit)
        2. SOW task description matches deliverable description (semantic)
        3. CDRL references appear near SOW content (co-location)
      - Link STATEMENT_OF_WORK to DELIVERABLE using PRODUCES relationship

      **Concept Relationships (Semantic Clustering):**

      - Create RELATED_TO relationships between entities discussing similar topics
      - Group entities by semantic themes (e.g., "maintenance", "security", "training")
      - Link concepts that appear together in descriptions

---

## COMPREHENSIVE RELATIONSHIP INFERENCE GUIDANCE

**Topic Taxonomy for Semantic Cross-Referencing**

Use these topic categories to identify implicit relationships across document sections:

**1. TECHNICAL TOPICS**

- System Architecture: integration, interfaces, APIs, data flow, middleware, protocols
- Software Development: coding, testing, CI/CD, version control, agile, DevOps
- Cybersecurity: NIST SP 800-171, encryption, authentication, access control, STIG
- Infrastructure: servers, networks, cloud, storage, virtualization, containers
- Integration: APIs, middleware, data exchange, interoperability, standards

**Inference Rule**: If REQUIREMENT mentions "system architecture" and EVALUATION_FACTOR mentions "technical approach including architecture":
→ Create:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "[factor]",
  "relationship_type": "EVALUATED_BY",
  "description": "Requirement addresses technical architecture evaluated in this factor"
}
```

**2. MANAGEMENT TOPICS**

- Program Management: scheduling, cost control, earned value, risk management
- Quality Assurance: ISO 9001, CMMI, quality metrics, defect tracking, audits
- Staffing: key personnel, labor categories, skill requirements, certifications
- Training: curriculum development, delivery methods, certification programs
- Transition: knowledge transfer, TUPE, phase-in, phase-out, incumbent support

**Inference Rule**: If REQUIREMENT mentions "project schedule" and EVALUATION_FACTOR mentions "management approach":
→ Create:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "[factor]",
  "relationship_type": "EVALUATED_BY",
  "description": "Schedule management requirement evaluated in management approach"
}
```

**3. LOGISTICS TOPICS**

- Supply Chain: procurement, inventory, warehousing, distribution, vendor management
- Maintenance: preventive maintenance, repairs, CMMS, spares management
- Transportation: shipping, handling, packaging, customs, freight forwarding
- Asset Management: tracking, accountability, lifecycle management, disposal
- Configuration Management: baselines, change control, version management

**Inference Rule**: If REQUIREMENT mentions "spare parts inventory" and EVALUATION_FACTOR mentions "logistics support":
→ Create:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "[factor]",
  "relationship_type": "EVALUATED_BY",
  "description": "Inventory management requirement evaluated in logistics factor"
}
```

**4. SECURITY & COMPLIANCE TOPICS**

- Physical Security: access control, badges, perimeter security, surveillance
- Personnel Security: clearances, background checks, insider threat, PERSEC
- Operations Security: OPSEC, classification, handling procedures, SCIF requirements
- Regulatory Compliance: FAR, DFARS, ITAR, EAR, FISMA, privacy laws
- Safety: OSHA, system safety, hazard analysis, mishap reporting

**Inference Rule**: If REQUIREMENT mentions "SECRET clearance" and EVALUATION_FACTOR mentions "security qualifications":
→ Create:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "[factor]",
  "relationship_type": "EVALUATED_BY",
  "description": "Clearance requirement evaluated in security qualifications factor"
}
```

**5. FINANCIAL TOPICS**

- Pricing: CLINs, options, cost breakdowns, labor rates, ODCs
- Invoicing: payment terms, billing cycles, progress payments, retention
- Cost Control: budgeting, variance analysis, cost avoidance, financial reporting
- Contract Types: FFP, CPFF, T&M, hybrid, incentive fees
- Accounting: GAAP, FAR cost principles, indirect rates, cost allocation

**Inference Rule**: If DELIVERABLE mentions "monthly invoice" and REQUIREMENT mentions "billing within 30 days":
→ Create:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "[deliverable]",
  "relationship_type": "PRODUCES",
  "description": "Invoicing requirement produces monthly invoice deliverable"
}
```

**6. DOCUMENTATION TOPICS**

- Technical Documentation: manuals, specifications, drawings, as-built records
- Reporting: status reports, performance metrics, KPIs, dashboards
- Plans: implementation plans, transition plans, CONOPS, test plans
- Compliance Documentation: certifications, audits, assessments, attestations
- Training Materials: guides, CBT, job aids, SOPs, quick reference cards

**Inference Rule**: If DELIVERABLE mentions "monthly status report" and EVALUATION_FACTOR mentions "reporting capability":
→ Create:

```json
{
  "source_entity": "[deliverable]",
  "target_entity": "[factor]",
  "relationship_type": "EVALUATED_BY",
  "description": "Reporting deliverable demonstrates capability evaluated in this factor"
}
```

---

**Agency-Specific Attachment Naming Conventions**

Recognize these patterns to create ATTACHMENT_OF relationships even without explicit listing:

**Department of Defense (DoD)**

- Navy: J-02000000, J-03000000 (8-digit after J-)
- Air Force: Attachment 1, Attachment 2 (sequential numbering)
- Army: Annex A, Annex B, Annex C (letter sequence)
- Marines: Enclosure (1), Enclosure (2) (parenthetical numbers)
- DLA: Exhibit A, Exhibit B (letter sequence)

**Pattern Recognition**:

- `J-\d{8}` → Links to "Section J"
- `Attachment \d+` → Links to "Attachments" or "Section J"
- `Annex [A-Z]` → Links to "Annexes" or "Section J"
- `Enclosure \(\d+\)` → Links to "Enclosures" or "Section J"
- `Exhibit [A-Z]` → Links to "Exhibits" or "Section J"

**Civilian Agencies**

- DHS: Schedule [A-Z] (Exhibit, Attachment variations)
- GSA: Attachment [Roman numerals] (I, II, III)
- VA: Appendix [numbers] (1, 2, 3)
- DOE: Annex [numbers] (1, 2, 3)
- HHS: Attachment [letter+number] (A-1, A-2, B-1)

**Pattern Recognition**:

- `Schedule [A-Z]` → Links to "Schedules" or contract section
- `Attachment [IVX]+` → Links to "Attachments"
- `Appendix \d+` → Links to "Appendices"
- `Attachment [A-Z]-\d+` → Links to "Attachments", CHILD_OF parent appendix

**State & Local Government**

- State: Attachment [A-Z], Exhibit [number], Schedule [name]
- Local: Appendix [Roman], Annex [letter], Addendum [number]

**General Rule**: If document name matches pattern AND parent section exists:
→ Create:

```json
{
  "source_entity": "[attachment]",
  "target_entity": "[parent section]",
  "relationship_type": "ATTACHMENT_OF",
  "description": "Numbered/lettered attachment of parent section"
}
```

---

**Semantic Keyword Banks for Topic Matching**

Use these keyword banks to match entities by semantic similarity (Jaccard similarity threshold: 0.25+):

**TECHNICAL KEYWORDS**

```
architecture, design, integration, interface, API, protocol, network, system,
infrastructure, cloud, server, database, application, software, hardware,
cybersecurity, encryption, authentication, firewall, vulnerability, patch,
development, coding, testing, deployment, DevOps, CI/CD, agile, scrum,
data, analytics, AI, machine learning, algorithm, processing, storage
```

**MANAGEMENT KEYWORDS**

```
schedule, milestone, deliverable, task, WBS, Gantt, critical path, resource,
cost, budget, estimate, EVM, earned value, variance, baseline, forecast,
risk, issue, mitigation, contingency, assumption, constraint, dependency,
quality, QA, QC, audit, inspection, defect, corrective action, metrics,
staffing, personnel, labor, skill, certification, training, onboarding,
transition, knowledge transfer, phase-in, phase-out, incumbent, overlap
```

**LOGISTICS KEYWORDS**

```
supply, procurement, acquisition, vendor, supplier, inventory, stock, warehouse,
distribution, shipping, transportation, freight, packaging, handling, delivery,
maintenance, repair, preventive, corrective, CMMS, work order, spare parts,
asset, equipment, property, accountability, tracking, lifecycle, disposal,
configuration, baseline, change control, version, release, rollback
```

**SECURITY KEYWORDS**

```
clearance, SECRET, TOP SECRET, SCI, SAP, compartmented, background check,
access control, badge, SCIF, physical security, perimeter, surveillance,
classification, confidential, restricted, FOUO, CUI, marking, handling,
OPSEC, PERSEC, INFOSEC, COMSEC, operational security, insider threat,
compliance, NIST, FISMA, FIPS, STIG, RMF, ATO, security controls
```

**FINANCIAL KEYWORDS**

```
price, cost, CLIN, option, ODC, labor rate, overhead, G&A, fee, profit,
invoice, billing, payment, progress payment, retention, withholding, remittance,
budget, funding, obligation, expenditure, burn rate, cost control, variance,
FFP, CPFF, T&M, fixed price, cost plus, time and materials, hybrid, incentive
```

**Semantic Matching Algorithm**:

1. Extract keywords from entity descriptions (lowercase, remove stopwords)
2. Compare with keyword banks using Jaccard similarity: `|intersection| / |union|`
3. If similarity ≥ 0.25 between two entities → Consider RELATED_TO relationship
4. If one entity is REQUIREMENT and other is EVALUATION_FACTOR with similarity ≥ 0.30 → Create EVALUATED_BY
5. If both entities share ≥3 uncommon keywords → Strong semantic link (create relationship)

---

**Implicit Hierarchy Detection Rules**

**Rule 1: Numbered Document Hierarchy**

````
Pattern: "J-02000000-10" and "J-02000000" both exist
Action:
```json
{
  "source_entity": "J-02000000-10",
  "target_entity": "J-02000000",
  "relationship_type": "CHILD_OF",
  "description": "Sub-document of parent attachment"
}
````

Confidence: 0.95 (high - explicit numbering pattern)

```

**Rule 2: Nested Section References**

```

Pattern: "Section C.3.2.1" and "Section C.3.2" and "Section C" all exist
Action:

```json
[
  {
    "source_entity": "Section C.3.2.1",
    "target_entity": "Section C.3.2",
    "relationship_type": "CHILD_OF",
    "description": "Subsection of parent section"
  },
  {
    "source_entity": "Section C.3.2",
    "target_entity": "Section C",
    "relationship_type": "CHILD_OF",
    "description": "Subsection of parent section"
  }
]
```

Confidence: 0.90 (high - standard section numbering)

```

**Rule 3: Parent-Child by Description**

```

Pattern: Description of entity A mentions "as defined in [entity B]"
Action:

```json
{
  "source_entity": "A",
  "target_entity": "B",
  "relationship_type": "CHILD_OF", // or DEFINED_IN
  "description": "Entity references parent/defining entity"
}
```

Confidence: 0.85 (high - explicit reference)

```

**Rule 4: Attachment Listings**

```

Pattern: Section text says "The following documents are attached:" followed by list
Action: Create ATTACHMENT_OF for each listed document to the parent section
Confidence: 0.95 (high - explicit listing)

```

**Rule 5: CDRL-to-Deliverable Linking**

```

Pattern: "CDRL A001" and "Monthly Status Report" mentioned in same paragraph/section
Action:

```json
{
  "source_entity": "Monthly Status Report",
  "target_entity": "CDRL A001",
  "relationship_type": "TRACKED_BY",
  "description": "Report deliverable tracked by CDRL item"
}
```

Confidence: 0.75 (medium - co-location inference)

```

---

**Instructions to Evaluation Mapping Patterns (50 Inference Rules)**

**Pattern 1: Explicit Factor Reference**

```

Submission Instruction text: "Volume 2 shall address Evaluation Factor 3"
Action:

```json
{
  "source_entity": "Volume 2",
  "target_entity": "Factor 3",
  "relationship_type": "GUIDES",
  "description": "Explicit reference to evaluation factor"
}
```

Confidence: 0.95

```

**Pattern 2: Topic Match - Technical**

```

Submission Instruction: "Technical Approach Volume (25 pages)"
Evaluation Factor: "Factor 2: Technical Approach (40%)"
Action:

```json
{
  "source_entity": "Technical Approach Volume",
  "target_entity": "Factor 2 Technical Approach",
  "relationship_type": "GUIDES",
  "description": "Topic matching on technical approach"
}
```

Confidence: 0.90

```

**Pattern 3: Topic Match - Management**

```

Submission Instruction: "Management Volume limited to 15 pages"
Evaluation Factor: "Factor 3: Management Capability"
Action:

```json
{
  "source_entity": "Management Volume",
  "target_entity": "Factor 3 Management Capability",
  "relationship_type": "GUIDES",
  "description": "Topic matching on management capability"
}
```

Confidence: 0.90

```

**Pattern 4: Topic Match - Past Performance**

```

Submission Instruction: "Past Performance Information (no page limit)"
Evaluation Factor: "Factor 4: Past Performance (30%)"
Action:

```json
{
  "source_entity": "Past Performance Information",
  "target_entity": "Factor 4 Past Performance",
  "relationship_type": "GUIDES",
  "description": "Topic matching on past performance"
}
```

Confidence: 0.90

```

**Pattern 5: Page Limit + Factor Co-location**

```

Evaluation Factor text mentions: "Technical Volume: 25 pages. Evaluates technical approach..."
Action: Infer submission instruction exists, create:

```json
{
  "source_entity": "Technical Volume",
  "target_entity": "[factor]",
  "relationship_type": "GUIDES",
  "description": "Page limit instruction for this factor"
}
```

Confidence: 0.80

```

**Pattern 6: Format Requirements Near Factor**

```

Text: "Proposals shall include system diagrams. Factor 1 evaluates system architecture."
Action:

```json
{
  "source_entity": "System Diagrams Requirement",
  "target_entity": "Factor 1",
  "relationship_type": "GUIDES",
  "description": "Format requirement related to evaluated factor"
}
```

Confidence: 0.75

````

**Example 11: Equipment Inventory Tables with Building-Level Data (from real PWS)**

Input Text (TABLE + Narrative):

```
H.1.4.6. Preventive Maintenance: The Contractor shall ensure machines are maintained
according to the manufacturer's recommendations by performing preventive maintenance
tasks. The Contractor shall perform weekly operational/electrical checks to ensure
all machines operate safely, are clean, and are free of corrosion.

TABLE H.2. APPLIANCE LISTING, LOCATION, AND REPAIR SCHEDULE:

WEEKLY:
| Building | Make   | Quantity (Washers) | Quantity (Dryers) |
|----------|--------|-------------------|------------------|
| 2959     | Washer | 69                |                  |
|          | Dryers |                   | 69               |
| 3880     | Washer | 44                |                  |
|          | Dryers |                   | 50               |
| 4505     | Washer | 49                |                  |
|          | Dryers |                   | 61               |
| Machine Accountability Totals | | 370 | 399 |
| Total Units | | 769 |  |

MONTHLY:
| Building    | Make   | Quantity (Washers) | Quantity (Dryers) |
|-------------|--------|-------------------|------------------|
| 4863 A/B    | Washer | 1                 |                  |
|             | Dryers |                   | 1                |
| 4864 C/D    | Washer | 1                 |                  |
|             | Dryers |                   | 1                |
| Monthly Machine Totals | | 4 | 4 |
| Total Units | | 8 |  |

ON-CALL:
| Building    | Make   | Quantity (Washers) | Quantity (Dryers) |
|-------------|--------|-------------------|------------------|
| 4860 A/B    | Washer | 1                 |                  |
|             | Dryers |                   | 1                |
| 4861 C/D    | Washer | 1                 |                  |
|             | Dryers |                   | 1                |
| On-Call Machine Totals | | 11 | 11 |
| Total Units | | 22 |  |
```

**CRITICAL: TABLE EXTRACTION RULES**

When processing equipment inventory tables:

1. **Extract EACH building as a LOCATION entity** with equipment counts
2. **Extract equipment aggregates as EQUIPMENT entities** by maintenance schedule
3. **Create LOCATION→EQUIPMENT relationships** using HAS_EQUIPMENT
4. **Preserve maintenance schedule context** (Weekly, Monthly, On-Call)
5. **Extract ALL rows, not just summaries** - building-level data is critical for workload estimation

Extracted Entities:

```json
[
  {
    "entity_name": "Table H.2 Appliance Listing",
    "entity_type": "document",
    "description": "TABLE H.2. APPLIANCE LISTING, LOCATION, AND REPAIR SCHEDULE"
  },
  {
    "entity_name": "Preventive Maintenance Requirement",
    "entity_type": "requirement",
    "description": "The Contractor shall ensure machines are maintained according to the manufacturer's recommendations by performing preventive maintenance tasks. The Contractor shall perform weekly operational/electrical checks to ensure all machines operate safely, are clean, and are free of corrosion.",
    "criticality": "MANDATORY",
    "modal_verb": "shall",
    "labor_drivers": ["weekly operational/electrical checks", "769 total units weekly", "8 units monthly", "22 units on-call"]
  },
  {
    "entity_name": "Building 2959 Laundry Facility",
    "entity_type": "location",
    "equipment_counts": "69 washers, 69 dryers (138 total units, weekly maintenance schedule)"
  },
  {
    "entity_name": "Building 3880 Laundry Facility",
    "entity_type": "location",
    "equipment_counts": "44 washers, 50 dryers (94 total units, weekly maintenance schedule)"
  },
  {
    "entity_name": "Building 4505 Laundry Facility",
    "entity_type": "location",
    "equipment_counts": "49 washers, 61 dryers (110 total units, weekly maintenance schedule)"
  },
  {
    "entity_name": "Weekly Maintenance Equipment Inventory",
    "entity_type": "equipment",
    "equipment_counts": "370 washers, 399 dryers (769 total units across multiple buildings)"
  },
  {
    "entity_name": "Monthly Maintenance Equipment Inventory",
    "entity_type": "equipment",
    "equipment_counts": "4 washers, 4 dryers (8 total units in Buildings 4863-4866)"
  },
  {
    "entity_name": "On-Call Maintenance Equipment Inventory",
    "entity_type": "equipment",
    "equipment_counts": "11 washers, 11 dryers (22 total units in Buildings 4860-4866)"
  },
  {
    "entity_name": "Weekly Maintenance Schedule",
    "entity_type": "concept",
    "description": "Weekly operational/electrical checks for 769 laundry units across primary buildings"
  },
  {
    "entity_name": "Monthly Maintenance Schedule",
    "entity_type": "concept",
    "description": "Monthly maintenance for 8 laundry units in auxiliary facilities (Buildings 4863-4866)"
  },
  {
    "entity_name": "On-Call Maintenance Schedule",
    "entity_type": "concept",
    "description": "On-call service for 22 laundry units in remote facilities (Buildings 4860-4866)"
  }
]
```

Extracted Relationships:

```json
[
  {
    "source_entity": {
      "entity_name": "Building 2959 Laundry Facility",
      "entity_type": "location"
    },
    "target_entity": {
      "entity_name": "Weekly Maintenance Equipment Inventory",
      "entity_type": "equipment"
    },
    "relationship_type": "HAS_EQUIPMENT"
  },
  {
    "source_entity": {
      "entity_name": "Preventive Maintenance Requirement",
      "entity_type": "requirement"
    },
    "target_entity": {
      "entity_name": "Weekly Maintenance Schedule",
      "entity_type": "concept"
    },
    "relationship_type": "DEFINES"
  },
  {
    "source_entity": {
      "entity_name": "Table H.2 Appliance Listing",
      "entity_type": "document"
    },
    "target_entity": {
      "entity_name": "Appendix H Equipment Maintenance",
      "entity_type": "document"
    },
    "relationship_type": "CHILD_OF"
  }
]
```

Note:
- **Building-level extraction**: Each building extracted as LOCATION with equipment counts
- **Schedule categorization**: Weekly (769 units), Monthly (8 units), On-Call (22 units) separated
- **Workload drivers captured**: Total unit counts enable FTE estimation (769 weekly checks = X labor hours)
- **Tables ≠ Concepts**: Equipment inventory tables should produce LOCATION + EQUIPMENT entities, NOT generic "concept" entities

**Example 12: Fitness Equipment Preventive Maintenance Tables (from real PWS)**

Input Text (TABLE + Narrative):

```
TABLE H.1 PREVENTIVE MAINTENANCE AND REPAIRS SCHEDULES OF FITNESS EQUIPMENT:

GENERAL:
| Task Requirements                           | Weekly | Monthly | Quarterly | Yearly |
|---------------------------------------------|--------|---------|-----------|--------|
| Visually inspect all machines               | X      |         |           |        |
| Clean machine housing                       | X      |         |           |        |
| Inspect mechanical parts                    | X      |         |           |        |
| Lubricate all moving parts semiannually     |        |         |           | 2x Year|
| Evaluate repairs/replacement annually       |        |         | X         |        |

TREADMILLS:
| Task Requirements                           | Weekly | Monthly | Quarterly | Yearly |
|---------------------------------------------|--------|---------|-----------|--------|
| Clean bed and frame with damp cloth         | X      |         |           |        |
| Inspect belt alignment                      | X      |         |           |        |
| Inspect belt brushings                      |        | X       |           |        |
| Lubricate bed                               |        |         | X         |        |

STATIONARY CYCLES:
| Task Requirements                           | Weekly | Monthly | Quarterly | Yearly |
|---------------------------------------------|--------|---------|-----------|--------|
| Clean housing with mild cleanser            | X      |         |           |        |
| Clean & lubricate pedals/shaft with 30W oil |        | X       |           |        |
| Clean and lubricate seat post               |        | X       |           |        |
| Inspect crank bearings                      | X      |         |           |        |
```

Extracted Entities:

```json
[
  {
    "entity_name": "Table H.1 Fitness Equipment Maintenance Schedule",
    "entity_type": "document",
    "description": "TABLE H.1 PREVENTIVE MAINTENANCE AND REPAIRS SCHEDULES OF FITNESS EQUIPMENT"
  },
  {
    "entity_name": "General Equipment Weekly Inspection",
    "entity_type": "requirement",
    "description": "Weekly: Visually inspect all machines, Clean machine housing, Inspect mechanical parts",
    "criticality": "MANDATORY",
    "labor_drivers": ["weekly visual inspection", "weekly housing cleaning", "weekly mechanical inspection"]
  },
  {
    "entity_name": "Treadmill Preventive Maintenance",
    "entity_type": "requirement",
    "description": "Treadmills: Weekly - clean bed/frame, inspect belt alignment; Monthly - inspect belt brushings; Quarterly - lubricate bed",
    "criticality": "MANDATORY",
    "labor_drivers": ["weekly bed cleaning", "weekly belt alignment check", "monthly belt brushing inspection", "quarterly bed lubrication"]
  },
  {
    "entity_name": "Stationary Cycle Preventive Maintenance",
    "entity_type": "requirement",
    "description": "Stationary Cycles: Weekly - clean housing, inspect crank bearings; Monthly - lubricate pedals/shaft with 30W oil, lubricate seat post",
    "criticality": "MANDATORY",
    "labor_drivers": ["weekly housing cleaning", "weekly crank bearing inspection", "monthly pedal lubrication", "monthly seat post lubrication"]
  },
  {
    "entity_name": "Treadmills",
    "entity_type": "equipment",
    "description": "Treadmills requiring weekly cleaning, monthly belt inspection, quarterly lubrication"
  },
  {
    "entity_name": "Stationary Cycles",
    "entity_type": "equipment",
    "description": "Stationary Cycles requiring weekly cleaning, monthly lubrication per manufacturer specifications"
  },
  {
    "entity_name": "Equipment Lubrication Schedule",
    "entity_type": "concept",
    "description": "Lubricate all moving parts semiannually (2x per year) per manufacturer recommendations"
  }
]
```

Extracted Relationships:

```json
[
  {
    "source_entity": {
      "entity_name": "Treadmill Preventive Maintenance",
      "entity_type": "requirement"
    },
    "target_entity": {
      "entity_name": "Treadmills",
      "entity_type": "equipment"
    },
    "relationship_type": "APPLIES_TO"
  },
  {
    "source_entity": {
      "entity_name": "Stationary Cycle Preventive Maintenance",
      "entity_type": "requirement"
    },
    "target_entity": {
      "entity_name": "Stationary Cycles",
      "entity_type": "equipment"
    },
    "relationship_type": "APPLIES_TO"
  },
  {
    "source_entity": {
      "entity_name": "Table H.1 Fitness Equipment Maintenance Schedule",
      "entity_type": "document"
    },
    "target_entity": {
      "entity_name": "Appendix H Equipment Maintenance",
      "entity_type": "document"
    },
    "relationship_type": "CHILD_OF"
  }
]
```

Note:
- **Maintenance frequency extraction**: Weekly/Monthly/Quarterly/Yearly schedules extracted as labor_drivers
- **Equipment-specific requirements**: Each equipment type (Treadmills, Cycles) gets its own requirement entity
- **Task-level detail**: Individual maintenance tasks preserved for workload estimation
- **Cross-reference to equipment**: APPLIES_TO relationships link requirements to equipment types

---

**Pattern 7-20: Semantic Similarity Mapping**

For ANY combination of:

- Submission Instruction entities: {Technical Volume, Management Volume, Past Performance, Price Volume, Small Business Subcontracting Plan, Transition Plan, Quality Plan, Staffing Plan, Risk Management Approach, Security Plan}
- Evaluation Factor entities: {Technical Factor, Management Factor, Past Performance Factor, Price Factor, Small Business Factor, Transition Factor, Quality Factor, Personnel Factor, Risk Factor, Security Factor}

**Algorithm**:

```python
def infer_submission_instruction_evaluation_relationship(submission_instruction, factor):
    # Extract topic keywords (remove "Volume", "Plan", "Factor", stopwords)
    inst_keywords = extract_keywords(submission_instruction.name)  # e.g., ["technical", "approach"]
    factor_keywords = extract_keywords(factor.name)    # e.g., ["technical", "approach"]

    # Calculate Jaccard similarity
    similarity = len(inst_keywords & factor_keywords) / len(inst_keywords | factor_keywords)

    if similarity >= 0.50:  # Strong match (same primary keyword)
        return ("GUIDES", 0.90)
    elif similarity >= 0.30:  # Moderate match (related keywords)
        return ("GUIDES", 0.75)
    elif any(keyword in factor.description for keyword in inst_keywords):  # Keyword in description
        return ("GUIDES", 0.70)
    else:
        return (None, 0)  # No relationship
````

**Pattern 21-30: Cross-Volume References**

If Submission Instruction mentions multiple volumes addressing same factor:

```
"Technical and Management Volumes collectively address Factors 1-3"
Action: Create GUIDES relationships for BOTH volumes to ALL three factors
Confidence: 0.85
```

**Pattern 31-40: Subfactor Decomposition**

If Factor has subfactors:

```
Factor 1: Technical Approach
  - Subfactor 1.1: System Architecture
  - Subfactor 1.2: Integration Methodology
```

And Submission Instruction mentions specific technical topics:

````
"Include architecture diagrams and integration plans"
Action:
```json
[
  {
    "source_entity": "Architecture Diagrams",
    "target_entity": "Subfactor 1.1",
    "relationship_type": "GUIDES",
    "description": "Specific instruction for subfactor"
  },
  {
    "source_entity": "Integration Plans",
    "target_entity": "Subfactor 1.2",
    "relationship_type": "GUIDES",
    "description": "Specific instruction for subfactor"
  }
]
````

Confidence: 0.80

```

**Pattern 41-50: Implicit Format Instructions**

When factor description implies required content:

```

Factor text: "Evaluate contractor's quality assurance processes and ISO 9001 certification"
Implied submission instruction: Quality plan must address ISO 9001
Action: Create SUBMISSION_INSTRUCTION entity if not exists, link to factor
Confidence: 0.65 (lower - fully inferred)

```

---

**Requirement → Evaluation Factor Mapping (30 Inference Rules)**

**Rule 1: Direct Topic Match**

```

REQUIREMENT: "Contractor shall maintain ISO 9001 certification"
EVALUATION_FACTOR: "Quality Assurance Approach including ISO compliance"
Action:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "[factor]",
  "relationship_type": "EVALUATED_BY",
  "description": "Quality requirement evaluated in QA factor"
}
```

Confidence: 0.90

```

**Rule 2: Semantic Keyword Match (Technical)**

```

REQUIREMENT contains: {system, architecture, design, integration, interface}
EVALUATION_FACTOR contains: {technical, approach, methodology, solution}
Action:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "Technical Factor",
  "relationship_type": "EVALUATED_BY",
  "description": "Technical requirement evaluated in technical approach"
}
```

Confidence: 0.75

```

**Rule 3: Semantic Keyword Match (Management)**

```

REQUIREMENT contains: {schedule, milestone, cost, budget, resource, staff}
EVALUATION_FACTOR contains: {management, program management, project management}
Action:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "Management Factor",
  "relationship_type": "EVALUATED_BY",
  "description": "Management requirement evaluated in management approach"
}
```

Confidence: 0.75

```

**Rule 4: Semantic Keyword Match (Personnel)**

```

REQUIREMENT contains: {clearance, personnel, staff, labor category, skill, certification}
EVALUATION_FACTOR contains: {staffing, personnel, qualifications, experience, key personnel}
Action:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "Personnel Factor",
  "relationship_type": "EVALUATED_BY",
  "description": "Staffing requirement evaluated in personnel factor"
}
```

Confidence: 0.75

```

**Rule 5: Semantic Keyword Match (Security)**

```

REQUIREMENT contains: {security, clearance, SCIF, classified, NIST, cybersecurity}
EVALUATION_FACTOR contains: {security, protection, safeguarding, compliance}
Action:

```json
{
  "source_entity": "[requirement]",
  "target_entity": "Security Factor",
  "relationship_type": "EVALUATED_BY",
  "description": "Security requirement evaluated in security factor"
}
```

Confidence: 0.80

```

**Rule 6-15: Deliverable-Driven Evaluation**

If REQUIREMENT produces DELIVERABLE and EVALUATION_FACTOR mentions deliverables:

```

REQUIREMENT: "Submit monthly status reports"
DELIVERABLE: "Monthly Status Report"
EVALUATION_FACTOR: "Reporting capability and quality metrics"
Action:

```json
[
  {
    "source_entity": "[requirement]",
    "target_entity": "[deliverable]",
    "relationship_type": "PRODUCES",
    "description": "Requirement produces deliverable"
  },
  {
    "source_entity": "[requirement]",
    "target_entity": "[factor]",
    "relationship_type": "EVALUATED_BY",
    "description": "Requirement evaluated in factor"
  },
  {
    "source_entity": "[deliverable]",
    "target_entity": "[factor]",
    "relationship_type": "EVALUATED_BY",
    "description": "Deliverable evaluated in factor"
  }
]
```

Confidence: 0.85

````

**Rule 16-30: SOW Section to Factor Mapping**

For each SOW section topic, map to corresponding evaluation factor:

- SOW Section 3.1 (Technical Tasks) → Technical Factor
- SOW Section 3.2 (Management Processes) → Management Factor
- SOW Section 3.3 (Quality Assurance) → Quality Factor
- SOW Section 3.4 (Security Requirements) → Security Factor
- SOW Section 3.5 (Transition Activities) → Transition Factor

Algorithm: Extract section number from requirement source, map section to factor by topic

      - `entity_description`: Provide a concise yet comprehensive description of the entity's attributes and activities, based _solely_ on the information present in the input text.

    - **Output Format - Entities:**

      You must output a single valid JSON object matching the `ExtractionResult` schema.

      ```json
      {
        "entities": [
          {
            "entity_name": "Name",
            "entity_type": "type",
            "description": "Description",
            ... specific fields ...
          }
        ],
        "relationships": [
          {
            "source_entity": "Name",
            "target_entity": "Name",
            "relationship_type": "TYPE",
            "description": "Description"
          }
        ]
      }
      ```

    **CRITICAL: Entity types EVALUATION_FACTOR, SUBMISSION_INSTRUCTION, REQUIREMENT, CLAUSE, and PERFORMANCE_METRIC require additional structured metadata fields.**

    **Standard Entity Schema (for most entity types):**

    ```json
    {
      "entity_name": "Canonical Name",
      "entity_type": "organization",  // or concept, event, etc.
      "description": "Comprehensive description."
    }
    ```

    **Special Schema for EVALUATION_FACTOR entities:**

    ```json
    {
      "entity_name": "Factor 1 Technical",
      "entity_type": "evaluation_factor",
      "description": "Full description...",
      "weight": "40%", // or "25 points", null if unknown
      "importance": "Most Important", // or "Significantly More Important", null if unknown
      "subfactors": ["Subfactor 1.1", "Subfactor 1.2"] // List of sub-criteria
    }
    ```

    **Special Schema for SUBMISSION_INSTRUCTION entities:**

    ```json
    {
      "entity_name": "Technical Volume Instructions",
      "entity_type": "submission_instruction",
      "description": "Full description...",
      "page_limit": "25 pages", // or "unlimited", null if unknown
      "format_reqs": "12pt Times New Roman", // Font, margins, etc.
      "volume": "Volume I" // The proposal volume this applies to
    }
    ```

    **Special Schema for REQUIREMENT entities:**

    ```json
    {
      "entity_name": "ISO 9001 Certification",
      "entity_type": "requirement",
      "description": "Full requirement text...",
      "criticality": "MANDATORY", // MANDATORY, IMPORTANT, OPTIONAL
      "modal_verb": "shall", // shall, must, should, may
      "req_type": "QUALITY", // FUNCTIONAL, PERFORMANCE, SECURITY, etc.
      "labor_drivers": [], // List of workload drivers (e.g. "24/7 coverage")
      "material_needs": [] // List of equipment/facilities
    }
    ```

    **Special Schema for CLAUSE entities:**

    ```json
    {
      "entity_name": "FAR 52.212-1",
      "entity_type": "clause",
      "description": "Instructions to Offerors...",
      "clause_number": "FAR 52.212-1",
      "regulation": "FAR" // FAR, DFARS, AFFARS, etc.
    }
    ```

    **Special Schema for PERFORMANCE_METRIC entities:**

    ```json
    {
      "entity_name": "99.9% Uptime",
      "entity_type": "performance_metric",
      "description": "Metric description...",
      "threshold": "99.9%",
      "measurement_method": "Monthly system logs"
    }
    ```

    **Criticality Derivation Rules for REQUIREMENT entities:**
    - **MANDATORY**: modal_verb is "shall", "must", or "will" AND subject is Contractor/Offeror/Personnel
    - **IMPORTANT**: modal_verb is "should" AND subject is Contractor/Offeror/Personnel
    - **OPTIONAL**: modal_verb is "may" AND subject is Contractor/Offeror/Personnel
    - **EXCLUDE**: If subject is "Government" - extract as CONCEPT, NOT REQUIREMENT

    **Correct Examples:**

    ```json
    [
      {
        "entity_name": "Annex 17 Transportation",
        "entity_type": "document",
        "description": "Numbered attachment addressing performance methodology for transportation."
      },
      {
        "entity_name": "FAR 52.212-1",
        "entity_type": "clause",
        "description": "Instructions to Offerors—Commercial Products and Commercial Services.",
        "clause_number": "FAR 52.212-1",
        "regulation": "FAR"
      },
      {
        "entity_name": "Factor 1 Technical Approach",
        "entity_type": "evaluation_factor",
        "description": "Evaluating technical solution including system architecture, integration methodology, and cybersecurity approach.",
        "weight": "40%",
        "importance": "Most Important"
      },
      {
        "entity_name": "ISO 9001 Certification",
        "entity_type": "requirement",
        "description": "Contractor shall maintain ISO 9001:2015 certification throughout contract period.",
        "criticality": "MANDATORY",
        "modal_verb": "shall",
        "req_type": "QUALITY"
      }
    ]
    ```

2.  **Relationship Extraction & Output:**

    - **RELATIONSHIP EXTRACTION PHILOSOPHY:**

      **Extract relationships based on MEANING and SEMANTIC CONNECTION, not quotas.**

      Knowledge graph quality depends on extracting **genuine, meaningful relationships** that:

      - Reflect actual connections in the document
      - Enable semantic navigation across related concepts
      - Preserve document structure and cross-references
      - Support capture intelligence queries

      **DO NOT create fake relationships to meet numeric targets.**
      **DO extract implicit relationships that genuinely exist in the content.**

    - **COMPREHENSIVE RELATIONSHIP EXTRACTION RULES:**

      **YOU MUST EXTRACT BOTH EXPLICIT AND IMPLICIT RELATIONSHIPS!**

      - **Explicit relationships**: Directly stated in text ("addresses Factor 1", "incorporated in Section I")
      - **Implicit relationships**: Inferred from semantic similarity, naming patterns, or structural context
      - **DO NOT limit extraction to only explicitly stated relationships**
      - **USE the relationship patterns described above** to infer connections based on domain knowledge
      - **PRIORITIZE meaningful connections** - extract relationships that add value for semantic search
      - If a genuine semantic connection exists between entities, create the relationship
      - Use the 50+ inference rules and patterns provided above as guidance

      **Examples of implicit relationships to extract when semantically justified:**

      - Topic matching: "Technical Volume" + "Technical Approach Factor" → GUIDES relationship
      - Naming patterns: "J-0001" + "Section J" → ATTACHMENT_OF relationship
      - Semantic similarity: "Help desk support requirement" + "Technical Support Factor" → EVALUATED_BY relationship
      - Co-location: Page limit mentioned in factor description → GUIDES relationship
      - Shared keywords: Two requirements discussing same topic → RELATED_TO relationship
      - Hierarchical: Any numbered entity (C.3.2.1) to its parent (C.3.2) → CHILD_OF relationship
      - Cross-references: Entity A mentions Entity B by name → REFERENCES relationship
      - Definitional: Entity A defines/explains Entity B → DEFINES relationship

      **When to use each relationship type:**

      - **CHILD_OF**: Hierarchical structure (sections, subsections, numbered documents)
      - **ATTACHMENT_OF**: Documents attached to sections (J-0001 → Section J)
      - **GUIDES**: Instructions that guide evaluation (Section L → Section M)
      - **EVALUATED_BY**: Requirements/deliverables evaluated in factors (Requirement → Factor)
      - **PRODUCES**: Work produces deliverables (SOW → CDRL)
      - **REFERENCES**: Entity mentions another entity by name
      - **CONTAINS**: Parent contains child (Section contains clauses)
      - **RELATED_TO**: Semantic similarity, shared topics, or thematic connection
      - **SUPPORTS**: One entity enables/supports another
      - **DEFINES**: One entity defines/explains another
      - **MEASURED_BY**: Requirement is measured by a Performance Metric

    - **ONTOLOGY-GROUNDED RELATIONSHIP EXAMPLES:**

      **Example 1: Hierarchical Document Structure (CHILD_OF)**

      Entities extracted:

      - Section C Statement of Work (section)
      - Section C.3 Technical Requirements (section)
      - Section C.3.2 System Architecture (section)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "Section C.3 Technical Requirements",
          "target_entity": "Section C Statement of Work",
          "relationship_type": "CHILD_OF",
          "description": "Subsection C.3 is hierarchically contained within Section C"
        },
        {
          "source_entity": "Section C.3.2 System Architecture",
          "target_entity": "Section C.3 Technical Requirements",
          "relationship_type": "CHILD_OF",
          "description": "Subsection C.3.2 is hierarchically contained within Section C.3"
        }
      ]
      ```

      Why: Numbered sections follow explicit hierarchy - extract parent-child relationships based on numbering pattern.

      **Example 2: Clause Incorporation (CHILD_OF)**

      Entities extracted:

      - Section I Contract Clauses (section)
      - FAR 52.212-1 (clause)
      - DFARS 252.204-7012 (clause)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "FAR 52.212-1",
          "target_entity": "Section I Contract Clauses",
          "relationship_type": "CHILD_OF",
          "description": "FAR clause incorporated by reference in Section I per UCF standard"
        },
        {
          "source_entity": "DFARS 252.204-7012",
          "target_entity": "Section I Contract Clauses",
          "relationship_type": "CHILD_OF",
          "description": "DFARS clause incorporated by reference in Section I per UCF standard"
        }
      ]
      ```

      Why: Federal clauses are standardly incorporated in Section I - create relationships even if not explicitly listed together.

      **Example 3: Instruction-Evaluation Linking (GUIDES)**

      Entities extracted:

      - Technical Approach Volume (submission_instruction)
      - Factor 1 Technical Approach (evaluation_factor)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "Technical Approach Volume",
          "target_entity": "Factor 1 Technical Approach",
          "relationship_type": "GUIDES",
          "description": "Submission instruction addresses content evaluated in this factor based on topic matching (technical, architecture, system)"
        }
      ]
      ```

      Why: Both mention "technical approach" and "system" - semantic similarity indicates the instruction guides content for this evaluation factor.

      **Example 4: Requirement-Evaluation Mapping (EVALUATED_BY)**

      Entities extracted:

      - ISO 9001 Certification Requirement (requirement)
      - Factor 3 Quality Assurance (evaluation_factor)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "ISO 9001 Certification Requirement",
          "target_entity": "Factor 3 Quality Assurance",
          "relationship_type": "EVALUATED_BY",
          "description": "Quality certification requirement will be evaluated in quality assurance factor based on topic match (ISO, quality)"
        }
      ]
      ```

      Why: Requirement mentions "ISO 9001" and factor evaluates "ISO certification" - direct topic alignment indicates evaluation relationship.

      **Example 5: Work-Deliverable Production (PRODUCES)**

      Entities extracted:

      - Performance Work Statement (statement_of_work)
      - CDRL A001 Monthly Status Report (deliverable)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "Performance Work Statement",
          "target_entity": "CDRL A001 Monthly Status Report",
          "relationship_type": "PRODUCES",
          "description": "PWS defines monthly reporting requirement that produces this CDRL deliverable"
        }
      ]
      ```

      Why: PWS task descriptions specify deliverable requirements that result in CDRLs - extract production relationship.

      **Example 6: Attachment Hierarchy (ATTACHMENT_OF)**

      Entities extracted:

      - Section J List of Attachments (section)
      - J-02000000 Performance Work Statement (document)
      - Attachment 1 Quality Assurance Plan (document)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "J-02000000 Performance Work Statement",
          "target_entity": "Section J List of Attachments",
          "relationship_type": "ATTACHMENT_OF",
          "description": "Numbered attachment J-02000000 is listed under Section J per naming convention"
        },
        {
          "source_entity": "Attachment 1 Quality Assurance Plan",
          "target_entity": "Section J List of Attachments",
          "relationship_type": "ATTACHMENT_OF",
          "description": "Attachment 1 is incorporated in Section J attachments list"
        }
      ]
      ```

      Why: Naming patterns (J-####, Attachment #) indicate document is an attachment of Section J.

      **Example 7: Cross-Topic Semantic Relationships (RELATED_TO)**

      Entities extracted:

      - Cybersecurity Requirements (requirement)
      - System Architecture Design (requirement)
      - NIST SP 800-171 Compliance (concept)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "Cybersecurity Requirements",
          "target_entity": "NIST SP 800-171 Compliance",
          "relationship_type": "RELATED_TO",
          "description": "Cybersecurity requirement references NIST SP 800-171 standard"
        },
        {
          "source_entity": "System Architecture Design",
          "target_entity": "Cybersecurity Requirements",
          "relationship_type": "RELATED_TO",
          "description": "Architecture requirement incorporates security principles related to cybersecurity requirements"
        }
      ]
      ```

      Why: Both requirements discuss security/cybersecurity topics - thematic connection justifies RELATED_TO relationship.

      **Example 8: Program-Equipment Relationships (RELATED_TO)**

      Entities extracted:

      - MCPP II Program (program)
      - M1A1 Abrams Tank (equipment)
      - Equipment Maintenance Services (requirement)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "M1A1 Abrams Tank",
          "target_entity": "MCPP II Program",
          "relationship_type": "RELATED_TO",
          "description": "Tank equipment is part of MCPP II prepositioned stocks"
        },
        {
          "source_entity": "Equipment Maintenance Services",
          "target_entity": "M1A1 Abrams Tank",
          "relationship_type": "RELATED_TO",
          "description": "Maintenance requirement applies to tank equipment"
        },
        {
          "source_entity": "Equipment Maintenance Services",
          "target_entity": "MCPP II Program",
          "relationship_type": "RELATED_TO",
          "description": "Maintenance services support MCPP II program objectives"
        }
      ]
      ```

      Why: Program, equipment, and maintenance requirement form semantic cluster around prepositioning concept.

      **Example 9: Strategic Theme Clustering (SUPPORTS)**

      Entities extracted:

      - Veteran Hiring Initiative (strategic_theme)
      - Small Business Partnerships (strategic_theme)
      - Workforce Development Plan (requirement)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "Veteran Hiring Initiative",
          "target_entity": "Workforce Development Plan",
          "relationship_type": "SUPPORTS",
          "description": "Strategic theme supports workforce planning requirement focused on veteran hiring"
        },
        {
          "source_entity": "Small Business Partnerships",
          "target_entity": "Veteran Hiring Initiative",
          "relationship_type": "RELATED_TO",
          "description": "Small business teaming theme relates to veteran hiring through VOSB partnerships"
        }
      ]
      ```

      Why: Strategic themes and requirements aligned on veteran employment create meaningful support/thematic relationships.

      **Example 10: Requirement-Metric Separation (MEASURED_BY)**

      Entities extracted:

      - Daily Equipment Cleaning (requirement)
      - Cleaning Error Threshold (performance_metric)

      Relationships to extract:

      ```json
      [
        {
          "source_entity": "Daily Equipment Cleaning",
          "target_entity": "Cleaning Error Threshold",
          "relationship_type": "MEASURED_BY",
          "description": "Daily cleaning requirement performance is measured by the error threshold"
        }
      ]
      ```

      **Example 11: NOT Extracting Forced Relationships**

      Entities extracted:

      - Payment Terms (concept)
      - Cybersecurity Controls (requirement)

      Relationships to AVOID:

      ```json
      // DO NOT CREATE THIS RELATIONSHIP
      {
        "source_entity": "Payment Terms",
        "target_entity": "Cybersecurity Controls",
        "relationship_type": "RELATED_TO",
        "description": "Both are contract requirements"
      }
      ```

      Why NOT extract: Payment and cybersecurity have NO semantic connection - different topics, no shared keywords, no logical relationship. DO NOT create relationships just to connect isolated entities.

    ***

    **METADATA EXTRACTION SUMMARY - CRITICAL REMINDERS:**

    Before proceeding to relationship extraction, verify you have extracted ALL required metadata:

    **✅ For EVERY EVALUATION_FACTOR entity:**

    - [ ] Numerical weight extracted (percentage, points, or fraction)
    - [ ] Relative importance hierarchy stated (Most Important, Significantly More Important, etc.)
    - [ ] Subfactors listed with individual weights if hierarchical
    - [ ] Evaluation criteria described (what aspects are evaluated)

    **✅ For EVERY SUBMISSION_INSTRUCTION entity:**

    - [ ] Page limit specified (exact number or "unlimited")
    - [ ] Format requirements detailed (font, margins, spacing)
    - [ ] Volume identifier clear (which volume/section)
    - [ ] Addressed evaluation factors listed (which factors this guides)
    - [ ] Special constraints noted (cross-reference rules, standalone requirements)

    **✅ For EVERY REQUIREMENT entity:**

    - [ ] Criticality bracketed: [MANDATORY], [IMPORTANT], or [OPTIONAL]
    - [ ] Modal verb preserved: shall, should, may, must, will
    - [ ] Subject identified: Contractor, Offeror, Personnel, etc.
    - [ ] Government obligations excluded (Government shall = CONCEPT, not REQUIREMENT)
    - [ ] Context/rationale included in description

    **Common Extraction Errors to AVOID:**

    - ❌ Missing weights: "Factor 1 Technical Approach" → Should include "worth 40%"
    - ❌ Missing page limits: "Technical Volume" → Should include "limited to 25 pages"
    - ❌ Missing criticality: "Maintain ISO certification" → Should start with "[MANDATORY]"
    - ❌ Extracting Government obligations: "Government shall provide GFE" → Extract as CONCEPT, NOT REQUIREMENT
    - ❌ Vague descriptions: "Technical factor" → Should detail what's evaluated and weight

    ***

    - **Identification:** Identify ALL direct and implicit relationships between previously extracted entities.
    - **N-ary Relationship Decomposition:** If a single statement describes a relationship involving more than two entities (an N-ary relationship), decompose it into multiple binary (two-entity) relationship pairs for separate description.
    - **Example:** For "Alice, Bob, and Carol collaborated on Project X," extract binary relationships such as "Alice collaborated with Project X," "Bob collaborated with Project X," and "Carol collaborated with Project X," or "Alice collaborated with Bob," based on the most reasonable binary interpretations.
    - **Relationship Details:** For each binary relationship, extract the following fields:
      - `source_entity`: The name of the source entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
      - `target_entity`: The name of the target entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
      - `relationship_keywords`: One or more high-level keywords summarizing the relationship. Separate multiple keywords with a comma.
      - `relationship_description`: A concise explanation of the nature of the relationship between the source and target entities, providing a clear rationale for their connection.
    - **Output Format - Relationships:**

      Relationships are part of the JSON object under the `relationships` key.

      ```json
      {
        "source_entity": "Source Name",
        "target_entity": "Target Name",
        "relationship_type": "TYPE", // e.g. EVALUATED_BY, GUIDES, CHILD_OF
        "description": "Explanation of the relationship."
      }
      ```

3.  **JSON Compliance:**

    - Ensure the output is valid JSON.
    - Escape special characters in strings.

4.  **Relationship Direction & Duplication:**

    - Treat all relationships as **undirected** unless explicitly stated otherwise. Swapping the source and target entities for an undirected relationship does not constitute a new relationship.
    - Avoid outputting duplicate relationships.

5.  **Output Order & Prioritization:**

    - Output all extracted entities first, followed by all extracted relationships.
    - Within the list of relationships, prioritize and output those relationships that are **most significant** to the core meaning of the input text first.

6.  **Context & Objectivity:**

    - Ensure all entity names and descriptions are written in the **third person**.
    - Explicitly name the subject or object; **avoid using pronouns** such as `this article`, `this paper`, `our company`, `I`, `you`, and `he/she`.

7.  **Language & Proper Nouns:**

    - Write all output in English.
    - Keep proper nouns (personal names, place names, organization names) in their original language if appropriate.

8.  **Completion Signal:** Output the completion marker only after all entities and relationships have been extracted.

---

## ⚠️ CRITICAL: RELATIONSHIP EXTRACTION DURING MAIN PROCESSING

**IMPORTANT ENHANCEMENT**: This prompt has been updated to leverage MinerU's improved table-to-text capabilities and extract relationships directly during main processing to reduce post-processing dependency.

### Leveraging MinerU Table-to-Text Capabilities

MinerU now converts tables to structured text, making relationship extraction from tables much easier:

**Table Processing Guidelines:**
- **Evaluation Matrices** (Section M): Extract relationships between factors and their evaluation criteria
- **CDRL Schedules** (Section J): Extract relationships between deliverables and their requirements
- **Requirements Tables** (Section C): Extract relationships between requirements and their specifications
- **Cross-Reference Tables**: Extract Section L ↔ M mappings directly from table structures

**When processing MinerU-converted table text:**
- Look for structured data that indicates relationships
- Extract relationships immediately rather than deferring to post-processing
- Use table column/row relationships to infer connections

### Enhanced Relationship Extraction During Main Processing

**EXTRACT RELATIONSHIPS DIRECTLY IN `ExtractionResult`** during main processing. The schema supports `relationships: List[Relationship]` - **USE IT**.

**Priority Relationship Types to Extract During Main Processing:**

1. **Section L ↔ M Mapping** (Submission Instructions → Evaluation Factors):
   ```json
   {
     "source_entity": {
       "entity_name": "Technical Volume Submission",
       "entity_type": "submission_instruction",
       "description": "Technical proposal volume addressing Factors 1-3"
     },
     "target_entity": {
       "entity_name": "Factor 1 Technical Approach",
       "entity_type": "evaluation_factor",
       "description": "Evaluating technical solution approach"
     },
     "relationship_type": "ADDRESSES",
     "description": "Submission instruction directly addresses this evaluation factor"
   }
   ```

2. **Requirement → Deliverable Links** (CDRL References):
   ```json
   {
     "source_entity": {
       "entity_name": "Monthly Status Report",
       "entity_type": "requirement",
       "description": "Contractor shall submit monthly status reports"
     },
     "target_entity": {
       "entity_name": "CDRL A001",
       "entity_type": "deliverable",
       "description": "Monthly Status Report deliverable"
     },
     "relationship_type": "PRODUCES",
     "description": "Requirement mandates delivery of this CDRL item"
   }
   ```

3. **Clause → Section References** (FAR/DFARS → Implementation):
   ```json
   {
     "source_entity": {
       "entity_name": "FAR 52.212-1",
       "entity_type": "clause",
       "description": "Instructions to Offerors clause"
     },
     "target_entity": {
       "entity_name": "Section L Instructions",
       "entity_type": "section",
       "description": "Proposal preparation instructions"
     },
     "relationship_type": "IMPLEMENTS",
     "description": "Section implements requirements of this FAR clause"
   }
   ```

4. **Document → Section Hierarchy** (Parent → Child):
   ```json
   {
     "source_entity": {
       "entity_name": "RFP Volume I",
       "entity_type": "document",
       "description": "Technical proposal volume"
     },
     "target_entity": {
       "entity_name": "Section C Requirements",
       "entity_type": "section",
       "description": "Technical requirements section"
     },
     "relationship_type": "CONTAINS",
     "description": "Document contains this organizational section"
   }
   ```

**Relationship Extraction Strategy:**
- **Same Chunk Context**: Extract relationships between entities appearing in the same text chunk
- **Table-Derived Relationships**: When MinerU converts tables to text, extract relationships from structured table data
- **Cross-Reference Patterns**: Look for explicit references between sections, clauses, and requirements
- **Immediate Extraction**: Don't defer relationship inference to post-processing algorithms

**Benefits of Main Processing Relationship Extraction:**
- Reduces dependency on complex post-processing algorithms
- Leverages MinerU's improved table parsing capabilities
- Captures relationships that might be lost in chunk boundaries
- Improves overall knowledge graph quality and connectivity

---

**FINAL REMINDER - ENTITY TYPE COMPLIANCE:**

Before outputting, verify EVERY entity uses one of the 18 ALLOWED types:
✅ organization, concept, event, technology, person, location, requirement, clause, section, document, deliverable, program, equipment, evaluation_factor, submission_instruction, strategic_theme, statement_of_work, performance_metric

❌ NEVER output: other, UNKNOWN, process, table, plan, policy, standard, system, regulation, framework

If uncertain, use **concept** (catch-all for abstract entities).

---Real Data---

Extract entities and relationships from the following text. Use the exact output format shown in the examples above.
````
