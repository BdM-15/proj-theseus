# Entity Extraction Prompt

**Purpose**: Extract government contracting entities and relationships from RFP documents  
**Model**: xAI Grok-4-fast-reasoning (2M context window)  
**Prompt Size**: ~5,593 tokens (0.28% of context window)  
**Entity Types**: 17 specialized government contracting types  
**Enhancements**:

- Domain knowledge patterns (FAR/DFARS, UCF, Shipley, CDRL)
- 5 annotated RFP examples (Section L↔M, requirements, attachments, clauses, deliverables)
- 8 decision rules for ambiguous cases (edge case handling)
- Location-agnostic extraction (content over location)  
  **Last Updated**: October 11, 2025 (Branch 005 - Examples + Decision Tree)

---

---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.

---Instructions---

1.  **Entity Extraction & Output:**

    - **Identification:** Identify clearly defined and meaningful entities in the input text.
    - **Entity Details:** For each identified entity, extract the following information:

      - `entity_name`: The name of the entity. If the entity name is case-insensitive, capitalize the first letter of each significant word (title case). Ensure **consistent naming** across the entire extraction process.
      - `entity_type`: Categorize the entity using ONE of these exact types from the list below.

        **CRITICAL: Entity types must be lowercase with underscores (e.g., evaluation_factor).**
        **ONLY use these 17 types. Do NOT use generic fallback types like "process", "other", "table", or "image".**
        **If an entity doesn't clearly fit any type, use "concept" as the fallback.**

        Valid entity types (choose exactly ONE):
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

    - **Domain Knowledge - Government Contracting Patterns:**

      **FAR/DFARS Clause Recognition:**

      - FAR clauses: Format "FAR [Part].[Subpart]-[Number]" (e.g., FAR 52.212-1)
      - DFARS clauses: Format "DFARS 252.[Part]-[Number]" (e.g., DFARS 252.204-7012)
      - Agency supplements: AFFARS, NMCARS, DARS, TRANSFARS, etc.
      - Always extract as CLAUSE type, preserve full citation in entity_name

      **Uniform Contract Format (UCF) Sections:**

      - Section A: Solicitation/Contract Form (cover, dates, contact info)
      - Section B: Supplies/Services & Prices (CLINs, pricing)
      - Section C: Statement of Work (SOW/PWS location varies - may be Section C or attachment)
      - Section H: Special Requirements (security, key personnel)
      - Section I: Contract Clauses (FAR/DFARS - extract individual clauses)
      - Section J: Attachments (various naming: J-0001, Attachment 1, Annex A, Exhibit B)
      - Section L: Instructions to Offerors (page limits - SUBMISSION_INSTRUCTION)
      - Section M: Evaluation Factors (scoring - EVALUATION_FACTOR)
      - Note: Extract SOW/PWS as STATEMENT_OF_WORK regardless of location (section or attachment)

      **Deliverable Patterns (CDRL):**

      - Contract Data Requirements List items: CDRL A001, CDRL 6022, etc.
      - Extract as DELIVERABLE with full identifier preserved
      - DD Form 1423 references indicate deliverable tracking

      **Requirement Criticality (Shipley Methodology):**

      - SHALL/MUST = mandatory requirement (compliance required)
      - SHOULD = important but not mandatory (best practice)
      - MAY = optional (contractor discretion)
      - Extract modal verb context in description

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

      ```
      entity|Technical Volume|SUBMISSION_INSTRUCTION|Proposal section limited to 25 pages, 12-point Times New Roman font, must address Technical Approach and Maintenance Approach factors
      entity|Factor 1 Technical Approach|EVALUATION_FACTOR|Most Important factor worth 40% evaluating technical understanding, system architecture, and integration methodology
      entity|Factor 2 Maintenance Approach|EVALUATION_FACTOR|Significantly More Important factor worth 30% evaluating maintenance strategy and sustainment plans
      ```

      Extracted Relationships:

      ```
      relation|Technical Volume|Factor 1 Technical Approach|GUIDES|Submission instruction explicitly addresses this evaluation factor
      relation|Technical Volume|Factor 2 Maintenance Approach|GUIDES|Submission instruction explicitly addresses this evaluation factor
      ```

      **Example 2: Requirements with Criticality (Section C)**

      Input Text:

      ```
      3.2 System Requirements

      The Contractor shall provide 24/7 help desk support with average response
      time under 4 hours for Priority 1 incidents. The Contractor should implement
      automated monitoring tools to detect system anomalies. The Contractor may
      use commercial off-the-shelf (COTS) solutions where appropriate.
      ```

      Extracted Entities:

      ```
      entity|24/7 Help Desk Support|REQUIREMENT|Mandatory requirement (shall) to provide round-the-clock help desk with 4-hour average response time for Priority 1 incidents
      entity|Automated Monitoring Tools|REQUIREMENT|Important requirement (should) to implement automated monitoring for system anomaly detection
      entity|COTS Solutions|CONCEPT|Optional approach (may) allowing use of commercial off-the-shelf solutions where appropriate
      ```

      Note: "shall" = REQUIREMENT (mandatory), "should" = REQUIREMENT (important), "may" = CONCEPT (option, not requirement)

      **Example 3: Attachment Structure (Section J)**

      Input Text:

      ```
      Section J: List of Attachments

      The following documents are incorporated into this solicitation:

      1. J-02000000 Performance Work Statement (PWS)
      2. J-03000000 Quality Assurance Surveillance Plan (QASP)
      3. J-04000000 Contract Data Requirements List (CDRL)
         3.1 CDRL A001 - Monthly Status Report
         3.2 CDRL A002 - Quarterly Technical Review
      ```

      Extracted Entities:

      ```
      entity|Section J|SECTION|List of attachments and referenced documents for the solicitation
      entity|J-02000000 Performance Work Statement|DOCUMENT|Attachment containing detailed task descriptions and performance objectives
      entity|Performance Work Statement|STATEMENT_OF_WORK|Detailed task descriptions and performance objectives for contract execution
      entity|J-03000000 Quality Assurance Surveillance Plan|DOCUMENT|Quality assurance surveillance plan and inspection procedures
      entity|J-04000000 Contract Data Requirements List|DOCUMENT|List of required contract deliverables with submission schedules
      entity|CDRL A001|DELIVERABLE|Monthly status report due to government
      entity|CDRL A002|DELIVERABLE|Quarterly technical review deliverable
      ```

      Extracted Relationships:

      ```
      relation|J-02000000 Performance Work Statement|Section J|ATTACHMENT_OF|Top-level attachment listed under Section J
      relation|J-03000000 Quality Assurance Surveillance Plan|Section J|ATTACHMENT_OF|Top-level attachment listed under Section J
      relation|J-04000000 Contract Data Requirements List|Section J|ATTACHMENT_OF|Top-level attachment listed under Section J
      relation|CDRL A001|J-04000000 Contract Data Requirements List|CHILD_OF|Deliverable item listed within CDRL attachment
      relation|CDRL A002|J-04000000 Contract Data Requirements List|CHILD_OF|Deliverable item listed within CDRL attachment
      ```

      Note: PWS extracted as BOTH DOCUMENT (structure) and STATEMENT_OF_WORK (semantics)

      **Example 4: FAR Clauses (Section I)**

      Input Text:

      ```
      Section I: Contract Clauses

      The following Federal Acquisition Regulation (FAR) clauses are incorporated
      by reference:

      FAR 52.212-1 Instructions to Offerors—Commercial Products and Commercial Services
      FAR 52.212-4 Contract Terms and Conditions—Commercial Products and Commercial Services
      DFARS 252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting
      ```

      Extracted Entities:

      ```
      entity|Section I|SECTION|Contract clauses incorporated by reference from FAR and DFARS
      entity|FAR 52.212-1|CLAUSE|Instructions to Offerors for commercial products and commercial services acquisitions
      entity|FAR 52.212-4|CLAUSE|Standard contract terms and conditions for commercial products and services
      entity|DFARS 252.204-7012|CLAUSE|DoD cybersecurity requirements for safeguarding covered defense information with NIST SP 800-171 compliance
      ```

      Extracted Relationships:

      ```
      relation|FAR 52.212-1|Section I|CHILD_OF|Clause incorporated in Section I contract clauses
      relation|FAR 52.212-4|Section I|CHILD_OF|Clause incorporated in Section I contract clauses
      relation|DFARS 252.204-7012|Section I|CHILD_OF|Clause incorporated in Section I contract clauses
      ```

      **Example 5: Deliverables from SOW (Content-Location Flexibility)**

      Input Text:

      ```
      Attachment 0001: Performance Work Statement

      Task 3.4: Reporting Requirements

      The Contractor shall submit the following deliverables:
      - Monthly Progress Reports (due 5th business day of following month)
      - Quarterly Risk Assessments (due 15 days after quarter end)
      - Final Project Report (due at contract completion)

      All deliverables shall comply with CDRL A001, A002, and A003 respectively.
      ```

      Extracted Entities:

      ```
      entity|Attachment 0001 Performance Work Statement|DOCUMENT|Attachment containing detailed task descriptions and performance objectives
      entity|Performance Work Statement|STATEMENT_OF_WORK|Detailed task descriptions and performance objectives for contract execution
      entity|Monthly Progress Reports|DELIVERABLE|Monthly progress reports due 5th business day of following month per CDRL A001
      entity|Quarterly Risk Assessments|DELIVERABLE|Quarterly risk assessment deliverables due 15 days after quarter end per CDRL A002
      entity|Final Project Report|DELIVERABLE|Final project report deliverable due at contract completion per CDRL A003
      entity|CDRL A001|DELIVERABLE|Contract data requirement for monthly progress reporting
      entity|CDRL A002|DELIVERABLE|Contract data requirement for quarterly risk assessments
      entity|CDRL A003|DELIVERABLE|Contract data requirement for final project report
      ```

      Extracted Relationships:

      ```
      relation|Performance Work Statement|Monthly Progress Reports|PRODUCES|SOW task defines this deliverable requirement
      relation|Performance Work Statement|Quarterly Risk Assessments|PRODUCES|SOW task defines this deliverable requirement
      relation|Performance Work Statement|Final Project Report|PRODUCES|SOW task defines this deliverable requirement
      ```

      Note: SOW in attachment (not Section C) - extracted based on CONTENT, not LOCATION

      **Example 6: Implicit Section L ↔ M Relationship (Topic Matching)**

      Input Text:

      ```
      Section L.2.1: Technical Volume

      The Technical Volume shall not exceed 20 pages and must include detailed
      system architecture diagrams, cybersecurity controls mapping to NIST SP
      800-171, and integration methodology with existing government systems.

      Section M.1: Factor 1 - Technical Approach (Most Important, 45%)

      The Government will evaluate the offeror's technical solution, including
      system design, security architecture, and integration strategy. Subfactors:
        1.1 System Architecture and Design (20%)
        1.2 Cybersecurity Approach (15%)
        1.3 Integration Methodology (10%)
      ```

      Extracted Entities:

      ```
      entity|Technical Volume|SUBMISSION_INSTRUCTION|Proposal section limited to 20 pages addressing system architecture, cybersecurity, and integration methodology
      entity|Factor 1 Technical Approach|EVALUATION_FACTOR|Most Important factor worth 45% evaluating technical solution including architecture, security, and integration
      entity|Subfactor 1.1 System Architecture|EVALUATION_FACTOR|Subfactor worth 20% evaluating system design and architecture approach
      entity|Subfactor 1.2 Cybersecurity Approach|EVALUATION_FACTOR|Subfactor worth 15% evaluating security architecture and NIST SP 800-171 compliance
      entity|Subfactor 1.3 Integration Methodology|EVALUATION_FACTOR|Subfactor worth 10% evaluating integration strategy with government systems
      ```

      Extracted Relationships (IMPLICIT - based on topic matching):

      ```
      relation|Technical Volume|Factor 1 Technical Approach|GUIDES|Instruction explicitly addresses evaluation factor topics (architecture, security, integration)
      relation|Technical Volume|Subfactor 1.1 System Architecture|GUIDES|Volume requires architecture diagrams matching subfactor evaluation criteria
      relation|Technical Volume|Subfactor 1.2 Cybersecurity Approach|GUIDES|Volume requires NIST 800-171 mapping matching security subfactor
      relation|Technical Volume|Subfactor 1.3 Integration Methodology|GUIDES|Volume requires integration methodology matching subfactor criteria
      relation|Subfactor 1.1 System Architecture|Factor 1 Technical Approach|CHILD_OF|Subfactor component of parent evaluation factor
      relation|Subfactor 1.2 Cybersecurity Approach|Factor 1 Technical Approach|CHILD_OF|Subfactor component of parent evaluation factor
      relation|Subfactor 1.3 Integration Methodology|Factor 1 Technical Approach|CHILD_OF|Subfactor component of parent evaluation factor
      ```

      **Example 7: Requirement → Evaluation Factor (Semantic Matching)**

      Input Text:

      ```
      Section C.3.4: Quality Assurance Requirements

      The Contractor shall maintain ISO 9001:2015 certification throughout the
      contract period. The Contractor shall implement a quality management system
      with documented procedures for defect tracking, root cause analysis, and
      corrective action. The Contractor should achieve 98% on-time delivery rate.

      Section M.3: Factor 3 - Quality Assurance (Significantly Important, 25%)

      The Government will evaluate the contractor's quality management capabilities,
      including ISO certification, quality processes, and performance metrics. Past
      performance on quality will be heavily weighted.
      ```

      Extracted Entities:

      ```
      entity|ISO 9001:2015 Certification Requirement|REQUIREMENT|Mandatory requirement (shall) to maintain ISO 9001:2015 certification throughout contract period
      entity|Quality Management System|REQUIREMENT|Mandatory requirement (shall) to implement QMS with defect tracking, root cause analysis, and corrective action procedures
      entity|On-Time Delivery Rate|REQUIREMENT|Important requirement (should) to achieve 98% on-time delivery performance target
      entity|Factor 3 Quality Assurance|EVALUATION_FACTOR|Significantly Important factor worth 25% evaluating quality management capabilities, ISO certification, and performance metrics
      ```

      Extracted Relationships (IMPLICIT - semantic keyword matching):

      ```
      relation|ISO 9001:2015 Certification Requirement|Factor 3 Quality Assurance|EVALUATED_BY|Quality certification requirement directly evaluated in quality assurance factor
      relation|Quality Management System|Factor 3 Quality Assurance|EVALUATED_BY|QMS implementation requirement evaluated in quality management capabilities factor
      relation|On-Time Delivery Rate|Factor 3 Quality Assurance|EVALUATED_BY|Performance metric requirement evaluated in quality assurance factor
      ```

      Note: All three requirements semantically match Factor 3 (keywords: quality, ISO, processes, metrics)

      **Example 8: Multi-Agency Attachment Patterns (Implicit Hierarchy)**

      Input Text:

      ```
      Section J: List of Documents

      The following attachments are incorporated:
      - Attachment 001: Base Performance Work Statement
      - Attachment 002: Quality Assurance Surveillance Plan
      - Enclosure (1): Security Requirements Addendum
      - Exhibit A: Pricing Template and Instructions
      - Schedule B: Contract Line Item Numbers (CLINs)

      Attachment 001.1: Task Area 1 - Technical Support
      Attachment 001.2: Task Area 2 - Training Services
      ```

      Extracted Entities:

      ```
      entity|Section J|SECTION|List of incorporated documents and attachments for the solicitation
      entity|Attachment 001 Base Performance Work Statement|DOCUMENT|Primary attachment containing base contract work requirements
      entity|Base Performance Work Statement|STATEMENT_OF_WORK|Detailed base contract work requirements and performance objectives
      entity|Attachment 002 Quality Assurance Surveillance Plan|DOCUMENT|Quality assurance surveillance and inspection procedures
      entity|Enclosure (1) Security Requirements|DOCUMENT|Security requirements addendum with classified handling procedures
      entity|Exhibit A Pricing Template|DOCUMENT|Pricing template and instructions for cost proposal submission
      entity|Schedule B Contract Line Items|DOCUMENT|CLIN structure and pricing schedule for contract items
      entity|Attachment 001.1 Task Area 1|DOCUMENT|Sub-attachment defining Technical Support task area requirements
      entity|Attachment 001.2 Task Area 2|DOCUMENT|Sub-attachment defining Training Services task area requirements
      ```

      Extracted Relationships (IMPLICIT - pattern recognition):

      ```
      relation|Attachment 001 Base Performance Work Statement|Section J|ATTACHMENT_OF|Primary attachment listed under Section J
      relation|Attachment 002 Quality Assurance Surveillance Plan|Section J|ATTACHMENT_OF|Quality plan attachment listed under Section J
      relation|Enclosure (1) Security Requirements|Section J|ATTACHMENT_OF|Security addendum listed under Section J (Marine Corps naming pattern)
      relation|Exhibit A Pricing Template|Section J|ATTACHMENT_OF|Pricing exhibit listed under Section J (letter-based naming)
      relation|Schedule B Contract Line Items|Section J|ATTACHMENT_OF|CLIN schedule listed under Section J (schedule naming pattern)
      relation|Attachment 001.1 Task Area 1|Attachment 001 Base Performance Work Statement|CHILD_OF|Sub-attachment decomposition of base PWS (decimal numbering pattern)
      relation|Attachment 001.2 Task Area 2|Attachment 001 Base Performance Work Statement|CHILD_OF|Sub-attachment decomposition of base PWS (decimal numbering pattern)
      ```

      Note: Demonstrates Navy (Attachment ###), Marines (Enclosure (#)), and civilian (Exhibit/Schedule) patterns

      **Example 9: SOW → Deliverable Production (Semantic + CDRL Linking)**

      Input Text:

      ```
      Attachment J-04: Performance Work Statement

      Task 4.3: Program Management and Reporting

      The Contractor shall provide comprehensive program management including:
      - Monthly Program Status Reports analyzing schedule, cost, and technical progress
      - Quarterly Executive Briefings to government leadership
      - Annual Performance Assessment Reports with metrics analysis
      - Incident Reports within 24 hours of any security or safety event

      All reports shall comply with formats specified in CDRL A001-A004.

      Section J.5: Contract Data Requirements List

      CDRL A001: Monthly Status Report (Due 5th business day)
      CDRL A002: Quarterly Executive Briefing (Due 10 days after quarter)
      CDRL A003: Annual Performance Assessment (Due January 31)
      CDRL A004: Incident Report (Due 24 hours after event)
      ```

      Extracted Entities:

      ```
      entity|Attachment J-04 Performance Work Statement|DOCUMENT|Performance work statement attachment with task requirements
      entity|Performance Work Statement|STATEMENT_OF_WORK|Detailed task descriptions and performance objectives including program management
      entity|Monthly Program Status Reports|DELIVERABLE|Monthly status reports analyzing schedule, cost, and technical progress per CDRL A001
      entity|Quarterly Executive Briefings|DELIVERABLE|Quarterly executive briefings to government leadership per CDRL A002
      entity|Annual Performance Assessment Reports|DELIVERABLE|Annual performance assessment with metrics analysis per CDRL A003
      entity|Incident Reports|DELIVERABLE|Security or safety incident reports due within 24 hours per CDRL A004
      entity|CDRL A001|DELIVERABLE|Monthly status report deliverable due 5th business day of following month
      entity|CDRL A002|DELIVERABLE|Quarterly executive briefing deliverable due 10 days after quarter end
      entity|CDRL A003|DELIVERABLE|Annual performance assessment deliverable due January 31 annually
      entity|CDRL A004|DELIVERABLE|Incident report deliverable due 24 hours after qualifying event
      ```

      Extracted Relationships:

      ```
      relation|Performance Work Statement|Monthly Program Status Reports|PRODUCES|PWS task defines monthly reporting deliverable requirement
      relation|Performance Work Statement|Quarterly Executive Briefings|PRODUCES|PWS task defines quarterly briefing deliverable requirement
      relation|Performance Work Statement|Annual Performance Assessment Reports|PRODUCES|PWS task defines annual assessment deliverable requirement
      relation|Performance Work Statement|Incident Reports|PRODUCES|PWS task defines incident reporting deliverable requirement
      relation|Monthly Program Status Reports|CDRL A001|TRACKED_BY|Deliverable tracked and formatted per CDRL specification
      relation|Quarterly Executive Briefings|CDRL A002|TRACKED_BY|Deliverable tracked and formatted per CDRL specification
      relation|Annual Performance Assessment Reports|CDRL A003|TRACKED_BY|Deliverable tracked and formatted per CDRL specification
      relation|Incident Reports|CDRL A004|TRACKED_BY|Deliverable tracked and formatted per CDRL specification
      ```

      **Example 10: Strategic Themes and Win Themes (Concept Clustering)**

      Input Text:

      ```
      Section C.1: Background and Objectives

      The Navy seeks a contractor to provide innovative sustainment solutions
      leveraging predictive maintenance technology and data analytics to reduce
      operational downtime and total cost of ownership. The program emphasizes
      green energy initiatives and environmental sustainability aligned with Navy
      climate action goals. Veterans hiring and small business partnerships are
      critical program priorities.
      ```

      Extracted Entities:

      ```
      entity|Innovative Sustainment Solutions|STRATEGIC_THEME|Win theme emphasizing innovation in maintenance and sustainment approaches
      entity|Predictive Maintenance Technology|STRATEGIC_THEME|Technology-focused win theme highlighting data-driven preventive maintenance
      entity|Reduced Operational Downtime|STRATEGIC_THEME|Performance-focused win theme targeting availability and uptime improvements
      entity|Total Cost of Ownership Reduction|STRATEGIC_THEME|Cost-focused win theme emphasizing lifecycle cost savings
      entity|Green Energy Initiatives|STRATEGIC_THEME|Environmental win theme aligned with Navy climate action and sustainability goals
      entity|Veterans Hiring Priority|STRATEGIC_THEME|Socioeconomic win theme supporting veteran employment objectives
      entity|Small Business Partnerships|STRATEGIC_THEME|Small business win theme emphasizing teaming and subcontracting commitments
      ```

      Extracted Relationships (semantic clustering):

      ```
      relation|Predictive Maintenance Technology|Innovative Sustainment Solutions|SUPPORTS|Technology enabler supporting innovation theme
      relation|Predictive Maintenance Technology|Reduced Operational Downtime|SUPPORTS|Technology approach reduces downtime through prediction
      relation|Reduced Operational Downtime|Total Cost of Ownership Reduction|SUPPORTS|Uptime improvements drive cost savings
      relation|Green Energy Initiatives|Environmental Sustainability|RELATED_TO|Environmental themes aligned with climate action
      relation|Veterans Hiring Priority|Small Business Partnerships|RELATED_TO|Socioeconomic themes supporting diverse teaming
      ```

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
→ Create: `relation|[requirement]|[factor]|EVALUATED_BY|Requirement addresses technical architecture evaluated in this factor`

**2. MANAGEMENT TOPICS**

- Program Management: scheduling, cost control, earned value, risk management
- Quality Assurance: ISO 9001, CMMI, quality metrics, defect tracking, audits
- Staffing: key personnel, labor categories, skill requirements, certifications
- Training: curriculum development, delivery methods, certification programs
- Transition: knowledge transfer, TUPE, phase-in, phase-out, incumbent support

**Inference Rule**: If REQUIREMENT mentions "project schedule" and EVALUATION_FACTOR mentions "management approach":
→ Create: `relation|[requirement]|[factor]|EVALUATED_BY|Schedule management requirement evaluated in management approach`

**3. LOGISTICS TOPICS**

- Supply Chain: procurement, inventory, warehousing, distribution, vendor management
- Maintenance: preventive maintenance, repairs, CMMS, spares management
- Transportation: shipping, handling, packaging, customs, freight forwarding
- Asset Management: tracking, accountability, lifecycle management, disposal
- Configuration Management: baselines, change control, version management

**Inference Rule**: If REQUIREMENT mentions "spare parts inventory" and EVALUATION_FACTOR mentions "logistics support":
→ Create: `relation|[requirement]|[factor]|EVALUATED_BY|Inventory management requirement evaluated in logistics factor`

**4. SECURITY & COMPLIANCE TOPICS**

- Physical Security: access control, badges, perimeter security, surveillance
- Personnel Security: clearances, background checks, insider threat, PERSEC
- Operations Security: OPSEC, classification, handling procedures, SCIF requirements
- Regulatory Compliance: FAR, DFARS, ITAR, EAR, FISMA, privacy laws
- Safety: OSHA, system safety, hazard analysis, mishap reporting

**Inference Rule**: If REQUIREMENT mentions "SECRET clearance" and EVALUATION_FACTOR mentions "security qualifications":
→ Create: `relation|[requirement]|[factor]|EVALUATED_BY|Clearance requirement evaluated in security qualifications factor`

**5. FINANCIAL TOPICS**

- Pricing: CLINs, options, cost breakdowns, labor rates, ODCs
- Invoicing: payment terms, billing cycles, progress payments, retention
- Cost Control: budgeting, variance analysis, cost avoidance, financial reporting
- Contract Types: FFP, CPFF, T&M, hybrid, incentive fees
- Accounting: GAAP, FAR cost principles, indirect rates, cost allocation

**Inference Rule**: If DELIVERABLE mentions "monthly invoice" and REQUIREMENT mentions "billing within 30 days":
→ Create: `relation|[requirement]|[deliverable]|PRODUCES|Invoicing requirement produces monthly invoice deliverable`

**6. DOCUMENTATION TOPICS**

- Technical Documentation: manuals, specifications, drawings, as-built records
- Reporting: status reports, performance metrics, KPIs, dashboards
- Plans: implementation plans, transition plans, CONOPS, test plans
- Compliance Documentation: certifications, audits, assessments, attestations
- Training Materials: guides, CBT, job aids, SOPs, quick reference cards

**Inference Rule**: If DELIVERABLE mentions "monthly status report" and EVALUATION_FACTOR mentions "reporting capability":
→ Create: `relation|[deliverable]|[factor]|EVALUATED_BY|Reporting deliverable demonstrates capability evaluated in this factor`

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
→ Create: `relation|[attachment]|[parent section]|ATTACHMENT_OF|Numbered/lettered attachment of parent section`

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

```
Pattern: "J-02000000-10" and "J-02000000" both exist
Action: relation|J-02000000-10|J-02000000|CHILD_OF|Sub-document of parent attachment
Confidence: 0.95 (high - explicit numbering pattern)
```

**Rule 2: Nested Section References**

```
Pattern: "Section C.3.2.1" and "Section C.3.2" and "Section C" all exist
Action:
  relation|Section C.3.2.1|Section C.3.2|CHILD_OF|Subsection of parent section
  relation|Section C.3.2|Section C|CHILD_OF|Subsection of parent section
Confidence: 0.90 (high - standard section numbering)
```

**Rule 3: Parent-Child by Description**

```
Pattern: Description of entity A mentions "as defined in [entity B]"
Action: relation|A|B|CHILD_OF or DEFINED_IN|Entity references parent/defining entity
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
Action: relation|Monthly Status Report|CDRL A001|TRACKED_BY|Report deliverable tracked by CDRL item
Confidence: 0.75 (medium - co-location inference)
```

---

**Section L ↔ M Mapping Patterns (50 Inference Rules)**

**Pattern 1: Explicit Factor Reference**

```
Section L text: "Volume 2 shall address Evaluation Factor 3"
Action: relation|Volume 2|Factor 3|GUIDES|Explicit reference to evaluation factor
Confidence: 0.95
```

**Pattern 2: Topic Match - Technical**

```
Section L: "Technical Approach Volume (25 pages)"
Section M: "Factor 2: Technical Approach (40%)"
Action: relation|Technical Approach Volume|Factor 2 Technical Approach|GUIDES|Topic matching on technical approach
Confidence: 0.90
```

**Pattern 3: Topic Match - Management**

```
Section L: "Management Volume limited to 15 pages"
Section M: "Factor 3: Management Capability"
Action: relation|Management Volume|Factor 3 Management Capability|GUIDES|Topic matching on management capability
Confidence: 0.90
```

**Pattern 4: Topic Match - Past Performance**

```
Section L: "Past Performance Information (no page limit)"
Section M: "Factor 4: Past Performance (30%)"
Action: relation|Past Performance Information|Factor 4 Past Performance|GUIDES|Topic matching on past performance
Confidence: 0.90
```

**Pattern 5: Page Limit + Factor Co-location**

```
Section M text mentions: "Technical Volume: 25 pages. Evaluates technical approach..."
Action: Infer instruction exists, create: relation|Technical Volume|[factor]|GUIDES|Page limit instruction for this factor
Confidence: 0.80
```

**Pattern 6: Format Requirements Near Factor**

```
Text: "Proposals shall include system diagrams. Factor 1 evaluates system architecture."
Action: relation|System Diagrams Requirement|Factor 1|GUIDES|Format requirement related to evaluated factor
Confidence: 0.75
```

**Pattern 7-20: Semantic Similarity Mapping**

For ANY combination of:

- Section L entities: {Technical Volume, Management Volume, Past Performance, Price Volume, Small Business Subcontracting Plan, Transition Plan, Quality Plan, Staffing Plan, Risk Management Approach, Security Plan}
- Section M entities: {Technical Factor, Management Factor, Past Performance Factor, Price Factor, Small Business Factor, Transition Factor, Quality Factor, Personnel Factor, Risk Factor, Security Factor}

**Algorithm**:

```python
def infer_l_m_relationship(instruction, factor):
    # Extract topic keywords (remove "Volume", "Plan", "Factor", stopwords)
    inst_keywords = extract_keywords(instruction.name)  # e.g., ["technical", "approach"]
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
```

**Pattern 21-30: Cross-Volume References**

If Section L mentions multiple volumes addressing same factor:

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

And Section L mentions specific technical topics:

```
"Include architecture diagrams and integration plans"
Action:
  relation|Architecture Diagrams|Subfactor 1.1|GUIDES|Specific instruction for subfactor
  relation|Integration Plans|Subfactor 1.2|GUIDES|Specific instruction for subfactor
Confidence: 0.80
```

**Pattern 41-50: Implicit Format Instructions**

When factor description implies required content:

```
Factor text: "Evaluate contractor's quality assurance processes and ISO 9001 certification"
Implied instruction: Quality plan must address ISO 9001
Action: Create SUBMISSION_INSTRUCTION entity if not exists, link to factor
Confidence: 0.65 (lower - fully inferred)
```

---

**Requirement → Evaluation Factor Mapping (30 Inference Rules)**

**Rule 1: Direct Topic Match**

```
REQUIREMENT: "Contractor shall maintain ISO 9001 certification"
EVALUATION_FACTOR: "Quality Assurance Approach including ISO compliance"
Action: relation|[requirement]|[factor]|EVALUATED_BY|Quality requirement evaluated in QA factor
Confidence: 0.90
```

**Rule 2: Semantic Keyword Match (Technical)**

```
REQUIREMENT contains: {system, architecture, design, integration, interface}
EVALUATION_FACTOR contains: {technical, approach, methodology, solution}
Action: relation|[requirement]|Technical Factor|EVALUATED_BY|Technical requirement evaluated in technical approach
Confidence: 0.75
```

**Rule 3: Semantic Keyword Match (Management)**

```
REQUIREMENT contains: {schedule, milestone, cost, budget, resource, staff}
EVALUATION_FACTOR contains: {management, program management, project management}
Action: relation|[requirement]|Management Factor|EVALUATED_BY|Management requirement evaluated in management approach
Confidence: 0.75
```

**Rule 4: Semantic Keyword Match (Personnel)**

```
REQUIREMENT contains: {clearance, personnel, staff, labor category, skill, certification}
EVALUATION_FACTOR contains: {staffing, personnel, qualifications, experience, key personnel}
Action: relation|[requirement]|Personnel Factor|EVALUATED_BY|Staffing requirement evaluated in personnel factor
Confidence: 0.75
```

**Rule 5: Semantic Keyword Match (Security)**

```
REQUIREMENT contains: {security, clearance, SCIF, classified, NIST, cybersecurity}
EVALUATION_FACTOR contains: {security, protection, safeguarding, compliance}
Action: relation|[requirement]|Security Factor|EVALUATED_BY|Security requirement evaluated in security factor
Confidence: 0.80
```

**Rule 6-15: Deliverable-Driven Evaluation**

If REQUIREMENT produces DELIVERABLE and EVALUATION_FACTOR mentions deliverables:

```
REQUIREMENT: "Submit monthly status reports"
DELIVERABLE: "Monthly Status Report"
EVALUATION_FACTOR: "Reporting capability and quality metrics"
Action:
  relation|[requirement]|[deliverable]|PRODUCES
  relation|[requirement]|[factor]|EVALUATED_BY
  relation|[deliverable]|[factor]|EVALUATED_BY
Confidence: 0.85
```

**Rule 16-30: SOW Section to Factor Mapping**

For each SOW section topic, map to corresponding evaluation factor:

- SOW Section 3.1 (Technical Tasks) → Technical Factor
- SOW Section 3.2 (Management Processes) → Management Factor
- SOW Section 3.3 (Quality Assurance) → Quality Factor
- SOW Section 3.4 (Security Requirements) → Security Factor
- SOW Section 3.5 (Transition Activities) → Transition Factor

Algorithm: Extract section number from requirement source, map section to factor by topic

      - `entity_description`: Provide a concise yet comprehensive description of the entity's attributes and activities, based _solely_ on the information present in the input text.

    - **Output Format - Entities:** Output 4 fields for each entity on a single line. The first field must be the word entity.

    **Entity Output Format:**

    Four fields separated by the pipe character (|):
    entity | entity_name | ENTITY_TYPE | description

    **Correct Examples:**

    entity|Annex 17 Transportation|DOCUMENT|Numbered attachment addressing performance methodology for transportation.
    entity|Attachment 0001 Performance Work Statement|DOCUMENT|Attachment containing detailed task descriptions and performance objectives.
    entity|Exhibit B Quality Assurance Plan|DOCUMENT|Quality assurance surveillance plan and inspection procedures.
    entity|Public Law 99-234|DOCUMENT|Federal statute requiring the submission of certified cost or pricing data.
    entity|5 U.S.C. 5332|DOCUMENT|United States Code section governing position classification and General Schedule pay rates.
    entity|MIL-STD-882E|DOCUMENT|Department of Defense standard practice for system safety.
    entity|Veteran-Owned Small Business|CONCEPT|A business owned by veterans eligible for federal contracting preferences.
    entity|FAR 52.212-1|CLAUSE|Instructions to Offerors—Commercial Products and Commercial Services.
    entity|Section J|SECTION|List of attachments and referenced documents for the solicitation.
    entity|CDRL A001|DELIVERABLE|Monthly status report due 5 days after period end.
    entity|MCPP II|PROGRAM|Marine Corps Prepositioning Program II providing prepositioned equipment.
    entity|Navy MBOS|PROGRAM|Navy Maintenance Base Operating Support program for facilities maintenance.
    entity|Concorde RG-24 Battery|EQUIPMENT|12-volt battery for aircraft generators and ground support equipment.
    entity|6200 Tennant Floor Sweeper|EQUIPMENT|Commercial floor cleaning equipment for warehouse maintenance.
    entity|Technical Approach Volume|SUBMISSION_INSTRUCTION|Proposal section limited to 25 pages addressing technical methodology.
    entity|Past Performance Factor|EVALUATION_FACTOR|Evaluation criterion worth 30 points assessing contractor experience.
    entity|Integrated Logistics Support|STRATEGIC_THEME|Cross-cutting capability for supply chain and maintenance coordination.
    entity|Performance Work Statement|STATEMENT_OF_WORK|Detailed task descriptions and performance objectives for contract execution.

2.  **Relationship Extraction & Output:**

    - **CRITICAL INSTRUCTION - Aggressive Relationship Extraction:**

      **YOU MUST EXTRACT BOTH EXPLICIT AND IMPLICIT RELATIONSHIPS!**

      - **Explicit relationships**: Directly stated in text ("addresses Factor 1", "incorporated in Section I")
      - **Implicit relationships**: Inferred from semantic similarity, naming patterns, or structural context
      - **DO NOT limit extraction to only explicitly stated relationships**
      - **USE the relationship patterns described above** to infer connections
      - **PRIORITIZE relationship extraction** - extract MORE relationships rather than fewer
      - **CONFIDENCE is not required** - if semantic connection exists, create the relationship

      Examples of implicit relationships to extract:

      - Topic matching: "Technical Volume" + "Technical Approach Factor" → GUIDES relationship
      - Naming patterns: "J-0001" + "Section J" → ATTACHMENT_OF relationship
      - Semantic similarity: "Help desk support requirement" + "Technical Support Factor" → EVALUATED_BY relationship
      - Co-location: Page limit mentioned in factor description → GUIDES relationship

    - **Identification:** Identify ALL direct and implicit relationships between previously extracted entities.
    - **N-ary Relationship Decomposition:** If a single statement describes a relationship involving more than two entities (an N-ary relationship), decompose it into multiple binary (two-entity) relationship pairs for separate description.
    - **Example:** For "Alice, Bob, and Carol collaborated on Project X," extract binary relationships such as "Alice collaborated with Project X," "Bob collaborated with Project X," and "Carol collaborated with Project X," or "Alice collaborated with Bob," based on the most reasonable binary interpretations.
    - **Relationship Details:** For each binary relationship, extract the following fields:
      - `source_entity`: The name of the source entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
      - `target_entity`: The name of the target entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
      - `relationship_keywords`: One or more high-level keywords summarizing the relationship. Separate multiple keywords with a comma.
      - `relationship_description`: A concise explanation of the nature of the relationship between the source and target entities, providing a clear rationale for their connection.
    - **Output Format - Relationships:** Output 5 fields for each relationship on a single line. The first field must be the word relation.

    **Relationship Output Format:**

    Five fields separated by the pipe character (|):
    relation | source_entity | target_entity | keywords | description

3.  **Field Separator:**

    - Use the pipe character (|) to separate fields, exactly as shown in the examples above.

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

---Real Data---

Extract entities and relationships from the following text. Use the exact output format shown in the examples above.
