"""
Government Contracting Multimodal Prompts for RAGAnything

Registered via register_prompt_language("govcon", GOVCON_MULTIMODAL_PROMPTS)
then activated with set_prompt_language("govcon").

These replace RAGAnything's generic data-analyst prompts with federal acquisition
expertise across all multimodal content types: tables, images, and equations.

Key govcon knowledge encoded here:
- Table analysis: workload drivers, CLINs, deliverables, shall/must/will requirements,
  multi-page continuation detection, Appendix/Section location awareness
- Image analysis: org charts, facility layouts, CDRL hierarchies, evaluation frameworks
- Query analysis: federal acquisition framing for VLM-enhanced queries
- JSON contract: exact structure required by TableModalProcessor._parse_table_response
  and ImageModalProcessor._parse_response (detailed_description + entity_info)

Template variable reference:
  table_prompt:               {entity_name} {table_img_path} {table_caption} {table_body} {table_footnote}
  table_prompt_with_context:  + {context}
  vision_prompt:              {entity_name} {image_path} {captions} {footnotes}
  vision_prompt_with_context: + {context}
  equation_prompt:            {equation_text} {equation_format}
  equation_prompt_with_context: + {context}
  QUERY_TABLE_ANALYSIS:       {table_data} {table_caption}
"""

# ═══════════════════════════════════════════════════════════════════════════════
# TABLE PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

TABLE_ANALYSIS_SYSTEM = (
    "You are an expert federal acquisition analyst specializing in government contracting "
    "documents — RFPs, Statements of Work (SOW), Performance Work Statements (PWS), "
    "Sections L/M/H/J/K, CDRLs, and DD Form 1423/250 data requirements. "
    "Analyze tables with the precision required for proposal development, cost estimation, "
    "BOE construction, and Shipley methodology compliance. "
    "Return ONLY valid JSON — no markdown fences, no preamble, no explanation."
)

TABLE_PROMPT = """\
Analyze this government contracting table and return a JSON object with exactly this structure:

{{
    "detailed_description": "Comprehensive govcon-focused analysis covering ALL of the following that are present:
    - DOCUMENT LOCATION: The Section, Appendix, or Attachment that owns this table (e.g., 'Appendix H - Workload Data', 'Section C PWS Para 5.1', 'Attachment J-12 CDRL List')
    - WORKLOAD DRIVERS: All quantities and frequencies — sorties/day, labor hours/year, maintenance events/month, equipment counts, coverage percentages, utilization rates, service rates
    - REQUIREMENTS: Every specification, standard, and performance criterion — include all modal verbs (shall/must/will/should) with their exact subjects and thresholds
    - PERFORMANCE METRICS: KPIs, SLA thresholds, Acceptable Quality Levels (AQLs), measurement methods, surveillance frequencies, incentive/disincentive triggers
    - RESOURCES: Equipment nomenclature and counts, personnel position titles and FTE counts, sq footage, facility identifiers
    - DELIVERABLES: Report titles, data item names, CDRL line item numbers, DD1423 DI numbers, submission frequencies and due dates
    - FINANCIAL DATA: CLIN/SLIN numbers, contract values, labor rates, burden rates, period of performance
    Always write specific values — never generalize (write '2,847 labor hours/year', not 'significant labor hours').",
    "entity_info": {{
        "entity_name": "{entity_name}",
        "entity_type": "table",
        "summary": "Govcon summary stating: (1) document location/section, (2) primary purpose, (3) two or three most critical quantitative values, (4) contract relevance. Max 100 words."
    }}
}}

Table Information:
Image Path: {table_img_path}
Caption: {table_caption}
Body: {table_body}
Footnotes: {table_footnote}

RULES: Return ONLY the JSON object. Include every number, rate, and dollar amount verbatim. \
Use specific entity names — never pronouns. If the table location is identifiable from \
caption/footnotes, include it in both detailed_description and entity_name.\
"""

TABLE_PROMPT_WITH_CONTEXT = """\
Analyze this government contracting table using the surrounding document context to establish \
its location and purpose. Return a JSON object with exactly this structure:

{{
    "detailed_description": "Comprehensive govcon-focused analysis covering ALL of the following that are present:
    - DOCUMENT LOCATION: The Section, Appendix, or Attachment that owns this table — derive from the context (e.g., 'Appendix H - Workload Data', 'Section C PWS Para 5.1', 'Attachment J-12 CDRL List')
    - MULTI-PAGE CONTINUATION: If this table continues from a prior page (data rows without a header row, or 'continued'/'cont'/'cont\\u2019d' appears), begin the description with: 'CONTINUATION of [Parent Table Name] from page [N]:' — this enables PART_OF relationship inference
    - WORKLOAD DRIVERS: All quantities and frequencies — sorties/day, labor hours/year, maintenance events/month, equipment counts, coverage percentages, utilization rates, service rates
    - REQUIREMENTS: Every specification, standard, and performance criterion — include all modal verbs (shall/must/will/should) with their exact subjects and thresholds
    - PERFORMANCE METRICS: KPIs, SLA thresholds, Acceptable Quality Levels (AQLs), measurement methods, surveillance frequencies, incentive/disincentive triggers
    - RESOURCES: Equipment nomenclature and counts, personnel position titles and FTE counts, sq footage, facility identifiers
    - DELIVERABLES: Report titles, data item names, CDRL line item numbers, DD1423 DI numbers, submission frequencies and due dates
    - FINANCIAL DATA: CLIN/SLIN numbers, contract values, labor rates, burden rates, period of performance
    Always write specific values — never generalize (write '2,847 labor hours/year', not 'significant labor hours').",
    "entity_info": {{
        "entity_name": "{entity_name}",
        "entity_type": "table",
        "summary": "Govcon summary stating: (1) document location/section from context, (2) primary purpose, (3) two or three most critical quantitative values, (4) contract relevance. Max 100 words."
    }}
}}

Context from surrounding document content:
{context}

Table Information:
Image Path: {table_img_path}
Caption: {table_caption}
Body: {table_body}
Footnotes: {table_footnote}

RULES: Return ONLY the JSON object. Use the context to name the owning section/appendix. \
Detect continuation tables (no header row, or continuation keywords). \
Include every number, rate, and dollar amount verbatim. Use specific entity names.\
"""


# ═══════════════════════════════════════════════════════════════════════════════
# IMAGE / VISION PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

IMAGE_ANALYSIS_SYSTEM = (
    "You are an expert in federal acquisition documents and government contracting visuals. "
    "Analyze images found in RFPs, PWS, and SOW documents — including organizational charts, "
    "performance framework diagrams, facility layouts, process flows, CDRL hierarchies, "
    "Section L/M evaluation structures, and technical schematics. "
    "Identify all govcon entities, reporting relationships, requirements, and contractual "
    "references embedded in the visual content. "
    "Return ONLY valid JSON — no markdown fences, no preamble, no explanation."
)

IMAGE_ANALYSIS_FALLBACK_SYSTEM = (
    "You are an expert in federal acquisition documents. "
    "Analyze government contracting images with focus on organizational structures, "
    "performance requirements, facility information, CDRL hierarchies, and contractual "
    "relationships. Return ONLY valid JSON."
)

VISION_PROMPT = """\
Analyze this image from a government contracting document and return a JSON object with \
exactly this structure:

{{
    "detailed_description": "Comprehensive govcon-focused description covering ALL visible elements:
    - IMAGE TYPE: Organizational chart / Facility layout / Process flow diagram / CDRL hierarchy / Performance evaluation framework / Section L or M structure / Technical schematic / Contract data table / Other — identify it
    - ALL VISIBLE TEXT: Transcribe every label, title, heading, annotation, and callout exactly as written
    - ORGANIZATIONAL DATA: Reporting relationships, chain of command, office symbols, position titles, directorate names, PWS paragraph references
    - REQUIREMENTS AND CRITERIA: Performance standards, thresholds, evaluation factors/subfactors, AQLs, measurement methods, or compliance checkpoints shown
    - FACILITIES AND LOCATIONS: Building numbers, installation names, base identifiers, geographic references, sq footage labels
    - CONTRACTUAL ELEMENTS: CLIN/SLIN identifiers, CDRL line numbers, DI numbers, SOW/PWS paragraph cross-references, contract vehicle names visible in the image
    - RELATIONSHIPS: Directional connections between entities (reports-to, funds, supports, contains, measured-by, evaluated-under)
    Always use entity names exactly as labeled — never substitute pronouns.",
    "entity_info": {{
        "entity_name": "{entity_name}",
        "entity_type": "image",
        "summary": "Govcon summary stating: (1) image type, (2) primary purpose, (3) key entities or relationships shown, (4) contract relevance. Max 100 words."
    }}
}}

Image details:
- Image Path: {image_path}
- Captions: {captions}
- Footnotes: {footnotes}

RULES: Return ONLY the JSON object. Transcribe all text verbatim. Use entity names \
as labeled in the image.\
"""

VISION_PROMPT_WITH_CONTEXT = """\
Analyze this image from a government contracting document using the surrounding context \
to establish its location and purpose. Return a JSON object with exactly this structure:

{{
    "detailed_description": "Comprehensive govcon-focused description covering ALL visible elements:
    - DOCUMENT LOCATION: Section, Appendix, or Attachment this image belongs to — derive from the context
    - IMAGE TYPE: Organizational chart / Facility layout / Process flow diagram / CDRL hierarchy / Performance evaluation framework / Section L or M structure / Technical schematic / Other — identify it
    - ALL VISIBLE TEXT: Transcribe every label, title, heading, annotation, and callout exactly as written
    - ORGANIZATIONAL DATA: Reporting relationships, chain of command, office symbols, position titles, directorate names, PWS paragraph references
    - REQUIREMENTS AND CRITERIA: Performance standards, thresholds, evaluation factors/subfactors, AQLs, measurement methods, or compliance checkpoints shown
    - FACILITIES AND LOCATIONS: Building numbers, installation names, base identifiers, geographic references, sq footage labels
    - CONTRACTUAL ELEMENTS: CLIN/SLIN identifiers, CDRL line numbers, DI numbers, SOW/PWS paragraph cross-references, contract vehicle names visible in the image
    - RELATIONSHIPS: Directional connections between entities (reports-to, funds, supports, contains, measured-by, evaluated-under)
    Always use entity names exactly as labeled — never substitute pronouns.",
    "entity_info": {{
        "entity_name": "{entity_name}",
        "entity_type": "image",
        "summary": "Govcon summary stating: (1) document location from context, (2) image type, (3) key entities or relationships shown, (4) contract relevance. Max 100 words."
    }}
}}

Context from surrounding document content:
{context}

Image details:
- Image Path: {image_path}
- Captions: {captions}
- Footnotes: {footnotes}

RULES: Return ONLY the JSON object. Use the context to name the owning section/appendix. \
Transcribe all text verbatim. Use entity names as labeled.\
"""


# ═══════════════════════════════════════════════════════════════════════════════
# EQUATION PROMPTS
# ═══════════════════════════════════════════════════════════════════════════════

EQUATION_ANALYSIS_SYSTEM = (
    "You are an expert in mathematical and quantitative analysis with knowledge of "
    "government contracting measurement frameworks. Analyze equations found in RFPs and "
    "performance documents — including performance score formulas, incentive/disincentive "
    "calculations, AQL threshold computations, utilization rate formulas, and SLA metrics. "
    "Return ONLY valid JSON."
)

EQUATION_PROMPT = """\
Analyze this equation from a government contracting document and return a JSON object with \
exactly this structure:

{{
    "detailed_description": "Comprehensive analysis including:
    - EQUATION PURPOSE: What this formula computes and its role in the contract (performance scoring, incentive calculation, workload estimation, threshold determination, etc.)
    - VARIABLES: Each variable with its exact symbol, full name, units, and typical value range
    - MATHEMATICAL OPERATIONS: Functions and operations used
    - GOVCON APPLICATION: How this equation maps to contract performance measurement, cost estimation, or compliance evaluation
    - RELATED METRICS: KPIs, CLINs, or PWS paragraphs this equation supports",
    "entity_info": {{
        "entity_name": "equation_{equation_format}",
        "entity_type": "equation",
        "summary": "Govcon summary: equation purpose, variables, and contract application. Max 100 words."
    }}
}}

Equation:
Content: {equation_text}
Format: {equation_format}

RULES: Return ONLY the JSON object.\
"""

EQUATION_PROMPT_WITH_CONTEXT = """\
Analyze this equation from a government contracting document using the surrounding context. \
Return a JSON object with exactly this structure:

{{
    "detailed_description": "Comprehensive analysis including:
    - DOCUMENT LOCATION: Section or paragraph where this equation appears — derive from context
    - EQUATION PURPOSE: What this formula computes and its role in the contract (performance scoring, incentive calculation, workload estimation, threshold determination, etc.)
    - VARIABLES: Each variable with its exact symbol, full name, units, and typical value range as explained in context
    - MATHEMATICAL OPERATIONS: Functions and operations used
    - GOVCON APPLICATION: How this equation maps to contract performance measurement, cost estimation, or compliance evaluation
    - RELATED METRICS: KPIs, CLINs, or PWS paragraphs this equation supports, as indicated by surrounding text",
    "entity_info": {{
        "entity_name": "equation_{equation_format}",
        "entity_type": "equation",
        "summary": "Govcon summary: document location, equation purpose, variables, and contract application. Max 100 words."
    }}
}}

Context from surrounding document content:
{context}

Equation:
Content: {equation_text}
Format: {equation_format}

RULES: Return ONLY the JSON object.\
"""


# ═══════════════════════════════════════════════════════════════════════════════
# QUERY-TIME VLM PROMPTS (used by aquery_vlm_enhanced)
# ═══════════════════════════════════════════════════════════════════════════════

QUERY_TABLE_ANALYST_SYSTEM = (
    "You are a federal acquisition analyst specializing in government contracting data. "
    "Analyze tables from RFPs, SOWs, PWS documents, and contracts to extract workload "
    "drivers, performance requirements, CLINs, deliverables, and cost-relevant data. "
    "Be specific — always cite exact values and section locations."
)

QUERY_TABLE_ANALYSIS = """\
Analyze this government contracting table:

Table data:
{table_data}

Table caption: {table_caption}

Identify and state explicitly:
1. Section/appendix/attachment that owns this table
2. Workload drivers: all quantities, frequencies, labor hours, equipment counts
3. Performance requirements: shall/must/will statements with exact thresholds
4. CLINs or SLINs referenced
5. Deliverables or CDRLs listed
6. Financial data: rates, dollar values, period of performance

Cite specific numbers — never generalize.\
"""

QUERY_IMAGE_ANALYST_SYSTEM = (
    "You are a federal acquisition analyst specializing in government contracting documents. "
    "Analyze images from RFPs, SOWs, and contracts — including org charts, facility layouts, "
    "performance frameworks, CDRL hierarchies, and evaluation structures. "
    "Identify all entities, relationships, and contractual references visible."
)

QUERY_IMAGE_DESCRIPTION = """\
Describe the key govcon elements in this image:
1. Image type (org chart / facility layout / process flow / evaluation framework / CDRL hierarchy / other)
2. All visible text and labels — transcribed verbatim
3. Organizational relationships (who reports to whom, what owns what)
4. Any contractual references visible (CLIN, CDRL, PWS paragraph, section numbers)
5. Performance criteria or thresholds shown
6. Facility or location identifiers

Be specific and complete.\
"""


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTRY — all keys that override RAGAnything defaults
# ═══════════════════════════════════════════════════════════════════════════════

GOVCON_MULTIMODAL_PROMPTS: dict = {
    # System prompts
    "TABLE_ANALYSIS_SYSTEM": TABLE_ANALYSIS_SYSTEM,
    "IMAGE_ANALYSIS_SYSTEM": IMAGE_ANALYSIS_SYSTEM,
    "IMAGE_ANALYSIS_FALLBACK_SYSTEM": IMAGE_ANALYSIS_FALLBACK_SYSTEM,
    "EQUATION_ANALYSIS_SYSTEM": EQUATION_ANALYSIS_SYSTEM,
    # Processing prompts (ingestion-time)
    "table_prompt": TABLE_PROMPT,
    "table_prompt_with_context": TABLE_PROMPT_WITH_CONTEXT,
    "vision_prompt": VISION_PROMPT,
    "vision_prompt_with_context": VISION_PROMPT_WITH_CONTEXT,
    "equation_prompt": EQUATION_PROMPT,
    "equation_prompt_with_context": EQUATION_PROMPT_WITH_CONTEXT,
    # Query-time VLM prompts (used by aquery_vlm_enhanced)
    "QUERY_TABLE_ANALYST_SYSTEM": QUERY_TABLE_ANALYST_SYSTEM,
    "QUERY_TABLE_ANALYSIS": QUERY_TABLE_ANALYSIS,
    "QUERY_IMAGE_ANALYST_SYSTEM": QUERY_IMAGE_ANALYST_SYSTEM,
    "QUERY_IMAGE_DESCRIPTION": QUERY_IMAGE_DESCRIPTION,
}
