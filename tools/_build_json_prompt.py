"""
One-shot builder for prompts/extraction/govcon_lightrag_json.txt

Phase 1.2 of issue #124 (LightRAG tuple→JSON migration).

Transforms govcon_lightrag_native.txt:
- Replaces the file header with a JSON-mode header.
- Rewrites the 11 inline tuple-format mini-examples in Parts B/C/F/G as
  JSON-equivalent snippets (entity_name→name, entity_type→type, drops the
  literal "entity"/"relation" prefix, swaps {tuple_delimiter} parsing for
  proper JSON object syntax).
- Replaces Part J (tuple output format) with the strict JSON contract.
- Replaces Part K (8 tuple examples) with the same 8 examples reformatted
  as JSON objects.
- Keeps Part L (quality checks) verbatim — they're format-agnostic except
  for the trailing "{completion_delimiter}" footer which is removed.
- Drops the DELIMITER REFERENCE footer (no delimiters in JSON mode).

Run:
    .\.venv\Scripts\python.exe tools\_build_json_prompt.py

This script is idempotent — re-running overwrites the JSON file.
The native.txt source is read-only here.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "prompts" / "extraction" / "govcon_lightrag_native.txt"
DST = ROOT / "prompts" / "extraction" / "govcon_lightrag_json.txt"


def tuple_to_json_entity(name: str, etype: str, desc: str, indent: str = "") -> str:
    name = name.replace('"', '\\"')
    desc = desc.replace('"', '\\"')
    return f'{indent}{{"name": "{name}", "type": "{etype}", "description": "{desc}"}}'


def tuple_to_json_relation(src: str, tgt: str, kw: str, desc: str, indent: str = "") -> str:
    src = src.replace('"', '\\"')
    tgt = tgt.replace('"', '\\"')
    desc = desc.replace('"', '\\"')
    return f'{indent}{{"source": "{src}", "target": "{tgt}", "keywords": "{kw}", "description": "{desc}"}}'


# Parse a single tuple line like:
#   entity{tuple_delimiter}Name{tuple_delimiter}type{tuple_delimiter}desc
# or
#   relation{tuple_delimiter}src{tuple_delimiter}tgt{tuple_delimiter}KW{tuple_delimiter}desc
def parse_tuple_line(line: str) -> str | None:
    parts = line.split("{tuple_delimiter}")
    if len(parts) < 4:
        return None
    head = parts[0].strip()
    if head.endswith("entity") and len(parts) == 4:
        return tuple_to_json_entity(parts[1], parts[2], parts[3].rstrip())
    if head.endswith("relation") and len(parts) == 5:
        return tuple_to_json_relation(parts[1], parts[2], parts[3], parts[4].rstrip())
    return None


def transform_inline_tuples(text: str) -> str:
    """Convert the 11 inline tuple mini-examples in Parts A-I to JSON snippets."""
    out_lines = []
    for ln in text.splitlines():
        if "{tuple_delimiter}" in ln:
            j = parse_tuple_line(ln)
            if j is not None:
                out_lines.append(j)
                continue
            # Lines that mention the placeholder but aren't tuple records (e.g. prose)
            # — fall through to keep as-is (then be scrubbed below if needed).
        out_lines.append(ln)
    return "\n".join(out_lines)


# ============================================================================
# NEW HEADER
# ============================================================================
NEW_HEADER = """GOVCON ONTOLOGY - LIGHTRAG NATIVE JSON FORMAT
======================================================================
Model: xAI Grok (response_format=json_object)
Output: LightRAG JSON Structured Output (entities[] + relationships[])
Version: 7.0 (Phase 1.2 - Tuple-Delimited → JSON Migration, issue #124)
Source: Converted from govcon_lightrag_native.txt v6.5
Total Size: ~35K tokens (full domain intelligence preserved)

CONTRACT NOTE:
This prompt drives LightRAG 1.5.0+ JSON extraction (entity_extraction_use_json=true).
The 33 govcon entity types and 43 canonical relationship types are unchanged.
The canonical relationship type token (e.g. GUIDES, CHILD_OF, MEASURED_BY) is
emitted as the FIRST comma-separated token of each relationship's `keywords`
field — this matches LightRAG's storage contract (operate.py stores keywords
identically for tuple and JSON paths) and preserves all downstream typed
inference (vdb_sync.normalize_relationship_type)."""


# ============================================================================
# NEW PART J (replaces tuple output format spec)
# ============================================================================
NEW_PART_J = """================================================================================
PART J: OUTPUT FORMAT (LightRAG Native JSON Structured Output)
================================================================================

CONTRACT: Return ONE valid JSON object with TWO top-level arrays — `entities`
and `relationships`. NO markdown code fences. NO commentary before or after.
NO trailing text. The HTTP layer requests `response_format={"type":"json_object"}`,
so anything that is not a valid JSON object will be rejected by the server.

TOP-LEVEL SHAPE:
{
  "entities": [ ... ],
  "relationships": [ ... ]
}

ENTITY OBJECT (3 required fields):
{
  "name":        "<canonical entity name, Title Case for proper nouns>",
  "type":        "<one of the 33 valid entity types, lowercase_with_underscores>",
  "description": "<full description with ALL type-specific metadata embedded>"
}

RELATIONSHIP OBJECT (4 required fields):
{
  "source":      "<source entity name, must match an entity in `entities`>",
  "target":      "<target entity name, must match an entity in `entities`>",
  "keywords":    "<CANONICAL_TYPE[, optional, semantic, keywords]>",
  "description": "<complete sentence explaining the relationship>"
}

CRITICAL: `keywords` MUST begin with the canonical UPPERCASE relationship type
as its first comma-separated token. Optional additional semantic keywords MAY
follow after a comma. Examples:
  "keywords": "GUIDES"
  "keywords": "GUIDES, golden thread, L↔M mapping"
  "keywords": "CHILD_OF"
  "keywords": "MEASURED_BY, threshold, monthly inspection"

The first token is parsed by downstream inference as the typed edge label.
Extra tokens enrich VDB embedding semantics but never override the type.

VALID ENTITY TYPES (33 — see Part D / {entity_types_guidance}):
requirement, clause, document_section, document, deliverable, evaluation_factor,
proposal_instruction, proposal_volume, program, equipment, strategic_theme,
work_scope_item, contract_line_item, workload_metric, labor_category, subfactor,
regulatory_reference, performance_standard, pricing_element, government_furnished_item,
compliance_artifact, transition_activity, technical_specification,
past_performance_reference, customer_priority, pain_point, amendment,
organization, technology, concept, location, event, person

VALID RELATIONSHIP TYPES (32 extraction-time — UPPERCASE_WITH_UNDERSCORES):

─── STRUCTURAL (Document Hierarchy & Cross-References) ───
CHILD_OF           Source is a child/subsection of target
ATTACHMENT_OF      Source document is attached to target section or document
CONTAINS           Target is contained within source
AMENDS             Source amendment modifies target document/section/requirement
SUPERSEDED_BY      Source version is replaced by target (newer) version
REFERENCES         Source entity mentions or cites target entity by name

─── EVALUATION & PROPOSAL (Section L↔M Golden Thread) ───
GUIDES             Source instruction/volume guides response to target factor
EVALUATED_BY       Source requirement/deliverable/work_scope is evaluated under target
HAS_SUBFACTOR      Source evaluation factor has target as a subfactor
MEASURED_BY        Source requirement is measured by target performance standard
EVIDENCES          Source evidence/artifact evidences target theme/factor

─── WORK & DELIVERABLES (Traceability Chain) ───
PRODUCES           Source work scope/transition activity produces target deliverable
SATISFIED_BY       Source requirement is satisfied by target deliverable/capability
TRACKED_BY         Source deliverable is tracked by target CDRL identifier
SUBMITTED_TO       Source deliverable is submitted to target organization
STAFFED_BY         Source requirement/work scope is staffed by target labor category
PRICED_UNDER       Source deliverable/requirement is priced under target CLIN
FUNDS              Source CLIN funds target requirement or deliverable
QUANTIFIES         Source workload metric quantifies target service requirement

─── AUTHORITY & GOVERNANCE ───
GOVERNED_BY        Source requirement is governed by target policy/regulation
MANDATES           Source clause/regulation mandates target requirement
CONSTRAINED_BY     Source work/pricing is constrained by target authority/spec
DEFINES            Source entity defines or explains target entity
APPLIES_TO         Source standard applies to target equipment/volume

─── RESOURCE & OPERATIONAL ───
HAS_EQUIPMENT      Source location has target equipment
PROVIDED_BY        Source GFM/GFI is provided by target organization
COORDINATED_WITH   Source activity is coordinated with target organization
REPORTED_TO        Source documentation/report is reported to target organization

─── STRATEGIC & CAPTURE INTELLIGENCE ───
ADDRESSES          Source requirement/capability addresses target priority/pain
RESOLVES           Source requirement/deliverable/activity resolves target pain
SUPPORTS           Source entity enables or supports target entity
RELATED_TO         Generic semantic similarity (use sparingly — prefer typed edges)

SOURCE → TARGET DIRECTIONALITY (enforce strictly):
  CHILD_OF:        child_entity → parent_entity
  ATTACHMENT_OF:   attachment → parent_section/document
  GUIDES:          proposal_instruction/proposal_volume → evaluation_factor
  EVALUATED_BY:    requirement/deliverable/work_scope → evaluation_factor
  HAS_SUBFACTOR:   evaluation_factor → subfactor
  MEASURED_BY:     requirement → performance_standard
  PRODUCES:        work_scope_item/transition_activity → deliverable
  SATISFIED_BY:    requirement → deliverable/compliance_artifact
  TRACKED_BY:      deliverable → deliverable (CDRL)
  SUBMITTED_TO:    deliverable → organization
  STAFFED_BY:      requirement/work_scope → labor_category
  PRICED_UNDER:    deliverable/requirement → contract_line_item
  FUNDS:           contract_line_item → requirement/deliverable
  QUANTIFIES:      workload_metric → requirement
  GOVERNED_BY:     requirement → document/regulatory_reference/clause
  MANDATES:        clause/regulatory_reference → requirement
  CONSTRAINED_BY:  work_scope_item/pricing_element → regulation/spec
  HAS_EQUIPMENT:   location → equipment
  PROVIDED_BY:     government_furnished_item → organization
  EVIDENCES:       past_performance/compliance_artifact → theme/factor
  APPLIES_TO:      requirement/standard → equipment; instruction → volume
  ADDRESSES:       requirement/work_scope → customer_priority/pain_point
  RESOLVES:        requirement/deliverable/transition → pain_point

CRITICAL OUTPUT RULES:
1. ENTITY name: Title Case for proper nouns; preserve exact citations for clauses (e.g. "FAR 52.212-1").
2. ENTITY type: MUST be EXACTLY one of the 33 valid types (lowercase_with_underscores). Anything else → entity is dropped.
3. ENTITY description: Comprehensive — embed ALL type-specific metadata inline:
   - requirement: criticality (MANDATORY/IMPORTANT/OPTIONAL/INFORMATIONAL), modal_verb (shall/should/may/must/will/can), labor drivers
   - evaluation_factor: weight (%), importance (Most Important / Significantly More Important / Equal / Less Important), subfactors
   - proposal_instruction: page_limit, format_reqs (font, margins, file type)
   - performance_standard: threshold, measurement_method (Periodic Inspection / Random Sampling / 100% Inspection / Customer Complaints)
   - clause: clause_number, regulation (FAR/DFARS/agency-supplement)
   - labor_category: position_title, skill_level, clearance_level
   - workload_metric: quantity, unit, period
   - subfactor: parent_factor, subfactor_number, weight
   - work_scope_item: task_number, scope_description
   - proposal_volume: volume_id, purpose
   - pricing_element: pricing_type, value_or_percentage, basis
4. RELATIONSHIP keywords: FIRST token = canonical UPPERCASE type. Extra tokens MAY follow.
5. RELATIONSHIP description: complete sentence; explains WHY the two entities connect.
6. Only emit relationships whose `source` AND `target` both appear in `entities` (or are valid cross-chunk references to known canonical entities).
7. Avoid forced relationships — see Example 8 anti-pattern. RELATED_TO is a last resort.
8. NO MARKDOWN, NO COMMENTARY, NO CODE FENCES — JUST THE JSON OBJECT.
"""


# ============================================================================
# NEW PART K (8 examples in JSON form)
# ============================================================================
NEW_PART_K = '''================================================================================
PART K: ANNOTATED RFP EXAMPLES (Full Domain Intelligence - 8 Examples, JSON form)
================================================================================

EXAMPLE 1: Section L ↔ Section M Mapping

Input Text:
Section L.3.1 Technical Volume
The Technical Volume shall address Evaluation Factors 1 and 2 (Technical Approach and Maintenance Approach) and shall not exceed 25 pages, 12-point font, Times New Roman. Include system architecture diagrams and integration plans.

Section M: Evaluation Factors
Factor 1: Technical Approach (Most Important, 40%)
The Government will evaluate the offeror's understanding of technical requirements, including system architecture and integration methodology.

Factor 2: Maintenance Approach (Significantly More Important, 30%)
The Government will evaluate the offeror's maintenance strategy and sustainment plans.

Output:
{
  "entities": [
    {"name": "Technical Volume", "type": "proposal_instruction", "description": "The Technical Volume shall address Evaluation Factors 1 and 2 (Technical Approach and Maintenance Approach) and shall not exceed 25 pages, 12-point font, Times New Roman. Include system architecture diagrams and integration plans. Page limit: 25 pages. Format: 12pt Times New Roman."},
    {"name": "Factor 1 Technical Approach", "type": "evaluation_factor", "description": "Factor 1: Technical Approach (Most Important, 40%). The Government will evaluate the offeror's understanding of technical requirements, including system architecture and integration methodology. Weight: 40%. Importance: Most Important."},
    {"name": "Factor 2 Maintenance Approach", "type": "evaluation_factor", "description": "Factor 2: Maintenance Approach (Significantly More Important, 30%). The Government will evaluate the offeror's maintenance strategy and sustainment plans. Weight: 30%. Importance: Significantly More Important."}
  ],
  "relationships": [
    {"source": "Technical Volume", "target": "Factor 1 Technical Approach", "keywords": "GUIDES, golden thread, L↔M mapping", "description": "Submission instruction addresses content evaluated in this factor."},
    {"source": "Technical Volume", "target": "Factor 2 Maintenance Approach", "keywords": "GUIDES, golden thread, L↔M mapping", "description": "Submission instruction addresses content evaluated in this factor."}
  ]
}

---

EXAMPLE 2: Requirements with Criticality and Workload Drivers

Input Text:
F.2. COMMUNITY RECREATIONAL PROGRAM (CRP): The Contractor shall implement and maintain the CRP to support all morale welfare and recreation events and activities described in this section of the PWS. Approximately 1,600 customers visit all CRP locations on a daily basis. The Contractor shall ensure all personnel supporting the CRP are trained and all locations' customer service desks are always covered with no more than two (2) customer service desks coverage discrepancies allowed per month. Unless otherwise stated, the Contractor shall support the CRP 24 hours a day / 7 days a week.

The Government shall provide facilities for CRP operations.

Output:
{
  "entities": [
    {"name": "F.2 Community Recreational Program Implementation", "type": "requirement", "description": "F.2. COMMUNITY RECREATIONAL PROGRAM (CRP): The Contractor shall implement and maintain the CRP to support all morale welfare and recreation events and activities described in this section of the PWS. Approximately 1,600 customers visit all CRP locations on a daily basis. Criticality: MANDATORY. Modal verb: shall. Labor drivers: 1,600 customers daily, 24/7 operations."},
    {"name": "F.2 CRP Customer Service Desk Coverage", "type": "requirement", "description": "The Contractor shall ensure all personnel supporting the CRP are trained and all locations' customer service desks are always covered. Criticality: MANDATORY. Modal verb: shall. Labor drivers: all locations, always covered."},
    {"name": "F.2 CRP 24/7 Support", "type": "requirement", "description": "Unless otherwise stated, the Contractor shall support the CRP 24 hours a day / 7 days a week. Criticality: MANDATORY. Modal verb: shall. Labor drivers: 24 hours/day, 7 days/week, continuous operations."},
    {"name": "Customer Service Desk Coverage Threshold", "type": "performance_standard", "description": "No more than two (2) customer service desks coverage discrepancies allowed per month. Threshold: no more than 2 discrepancies per month. Measurement: Periodic Inspection (Monthly)."},
    {"name": "Government Furnished Facilities", "type": "government_furnished_item", "description": "The Government shall provide facilities for CRP operations. Customer-provided facilities supporting CRP operations. Government-furnished asset, not contractor obligation."}
  ],
  "relationships": [
    {"source": "F.2 CRP Customer Service Desk Coverage", "target": "Customer Service Desk Coverage Threshold", "keywords": "MEASURED_BY, threshold, monthly inspection", "description": "Coverage requirement is measured by discrepancy threshold."},
    {"source": "F.2 Community Recreational Program Implementation", "target": "F.2 CRP 24/7 Support", "keywords": "CONTAINS", "description": "CRP implementation includes 24/7 support requirement."},
    {"source": "F.2 Community Recreational Program Implementation", "target": "Appendix F Recreational Services", "keywords": "CHILD_OF", "description": "F.2 CRP requirement is contained within Appendix F."},
    {"source": "F.2 CRP Customer Service Desk Coverage", "target": "F.2 Community Recreational Program Implementation", "keywords": "CHILD_OF", "description": "F.2 Customer Service requirement is part of F.2 CRP."},
    {"source": "F.2 CRP 24/7 Support", "target": "F.2 Community Recreational Program Implementation", "keywords": "CHILD_OF", "description": "F.2 24/7 support requirement is part of F.2 CRP."}
  ]
}

---

EXAMPLE 3: FAR and DFARS Clauses

Input Text:
SECTION I - CONTRACT CLAUSES

52.203-3 GRATUITIES (APR 1984)
52.203-5 COVENANT AGAINST CONTINGENT FEES (MAY 2014)
52.204-7 System for Award Management (OCT 2018)
52.212-4 CONTRACT TERMS AND CONDITIONS—COMMERCIAL ITEMS (FEB 2024)
252.204-7012 SAFEGUARDING COVERED DEFENSE INFORMATION AND CYBER INCIDENT REPORTING (JAN 2023)
252.225-7001 BUY AMERICAN AND BALANCE OF PAYMENTS PROGRAM (DEC 2017)

Output:
{
  "entities": [
    {"name": "Section I Contract Clauses", "type": "document_section", "description": "SECTION I - CONTRACT CLAUSES. Contains incorporated FAR and DFARS clauses."},
    {"name": "FAR 52.203-3 Gratuities", "type": "clause", "description": "52.203-3 GRATUITIES (APR 1984). Clause number: 52.203-3. Regulation: FAR."},
    {"name": "FAR 52.203-5 Contingent Fees", "type": "clause", "description": "52.203-5 COVENANT AGAINST CONTINGENT FEES (MAY 2014). Clause number: 52.203-5. Regulation: FAR."},
    {"name": "FAR 52.204-7 SAM Registration", "type": "clause", "description": "52.204-7 System for Award Management (OCT 2018). Clause number: 52.204-7. Regulation: FAR."},
    {"name": "FAR 52.212-4 Contract Terms Commercial", "type": "clause", "description": "52.212-4 CONTRACT TERMS AND CONDITIONS—COMMERCIAL ITEMS (FEB 2024). Clause number: 52.212-4. Regulation: FAR."},
    {"name": "DFARS 252.204-7012 Cybersecurity", "type": "clause", "description": "252.204-7012 SAFEGUARDING COVERED DEFENSE INFORMATION AND CYBER INCIDENT REPORTING (JAN 2023). Clause number: 252.204-7012. Regulation: DFARS. Cybersecurity compliance requirement."},
    {"name": "DFARS 252.225-7001 Buy American", "type": "clause", "description": "252.225-7001 BUY AMERICAN AND BALANCE OF PAYMENTS PROGRAM (DEC 2017). Clause number: 252.225-7001. Regulation: DFARS."}
  ],
  "relationships": [
    {"source": "FAR 52.203-3 Gratuities", "target": "Section I Contract Clauses", "keywords": "CHILD_OF", "description": "Clause incorporated in Section I."},
    {"source": "FAR 52.203-5 Contingent Fees", "target": "Section I Contract Clauses", "keywords": "CHILD_OF", "description": "Clause incorporated in Section I."},
    {"source": "FAR 52.204-7 SAM Registration", "target": "Section I Contract Clauses", "keywords": "CHILD_OF", "description": "Clause incorporated in Section I."},
    {"source": "FAR 52.212-4 Contract Terms Commercial", "target": "Section I Contract Clauses", "keywords": "CHILD_OF", "description": "Clause incorporated in Section I."},
    {"source": "DFARS 252.204-7012 Cybersecurity", "target": "Section I Contract Clauses", "keywords": "CHILD_OF", "description": "Clause incorporated in Section I."},
    {"source": "DFARS 252.225-7001 Buy American", "target": "Section I Contract Clauses", "keywords": "CHILD_OF", "description": "Clause incorporated in Section I."}
  ]
}

---

EXAMPLE 4: Operational Requirements with Workload Metrics (CRITICAL EXAMPLE)

Input Text:
F.2.3.1. C.A.C Customer Service Counter and Indoor Bar: The Contractor shall handle resale requirements to include alcohol sales. The Contractor shall service:
1) One (1) inside bar with two (2) registers located in the C.A.C.
2) One (1) additional outside bar with two (2) registers during special events.
3) One (1) additional bar with one (1) register located in Phantom Auditorium during special events and reserved activities.

Cash registers require USN staff personnel only. The Contractor shall verify all resale supplies necessary to ensure items are properly stocked at all times. The Contractor shall notify the Government when resale supply levels are low, and items need to be ordered. The Government will procure the resale supplies. Contractor personnel shall provide retail services at minimum rates of one (1) customer per minute during normal operations and three (3) customers per minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100) or during special events. The Contractor shall open the outside bar for special events as requested by the COR. The Government will send requests to open the outside bar for special events in writing a minimum of seven (7) calendar days prior to the event. This is estimated to occur 100 times per year.

Output:
{
  "entities": [
    {"name": "F.2.3.1 C.A.C. Customer Service Counter and Indoor Bar", "type": "requirement", "description": "F.2.3.1. C.A.C Customer Service Counter and Indoor Bar: The Contractor shall handle resale requirements to include alcohol sales. Criticality: MANDATORY. Modal verb: shall."},
    {"name": "F.2.3.1 Bar Service Configuration", "type": "requirement", "description": "The Contractor shall service: 1) One (1) inside bar with two (2) registers located in the C.A.C. 2) One (1) additional outside bar with two (2) registers during special events. 3) One (1) additional bar with one (1) register located in Phantom Auditorium during special events and reserved activities. Criticality: MANDATORY. Modal verb: shall. Equipment counts: 3 bars, 5 total registers."},
    {"name": "F.2.3.1 Resale Supply Verification", "type": "requirement", "description": "The Contractor shall verify all resale supplies necessary to ensure items are properly stocked at all times. The Contractor shall notify the Government when resale supply levels are low, and items need to be ordered. Criticality: MANDATORY. Modal verb: shall."},
    {"name": "F.2.3.1 Retail Service Rate Standard", "type": "requirement", "description": "Contractor personnel shall provide retail services at minimum rates of one (1) customer per minute during normal operations and three (3) customers per minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100) or during special events. Criticality: MANDATORY. Modal verb: shall. Service rates: 1 customer/minute (normal), 3 customers/minute (peak)."},
    {"name": "F.2.3.1 Outside Bar Special Events Support", "type": "requirement", "description": "The Contractor shall open the outside bar for special events as requested by the COR. The Government will send requests to open the outside bar for special events in writing a minimum of seven (7) calendar days prior to the event. This is estimated to occur 100 times per year. Criticality: MANDATORY. Modal verb: shall. Frequency: estimated 100 times per year. Lead time: 7 calendar days advance notice."},
    {"name": "Peak Service Hours", "type": "workload_metric", "description": "Peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100). Service rate increases to 3 customers per minute during these periods. Quantity: 3 customers/minute. Period: peak hours (4 windows daily)."},
    {"name": "Special Events Frequency", "type": "workload_metric", "description": "Special events estimated to occur 100 times per year. Key workload driver for outside bar operations and staffing. Quantity: 100. Unit: events. Period: per year."}
  ],
  "relationships": [
    {"source": "F.2.3.1 Retail Service Rate Standard", "target": "Peak Service Hours", "keywords": "REFERENCES", "description": "Service rate requirement references peak service hours."},
    {"source": "F.2.3.1 Outside Bar Special Events Support", "target": "Special Events Frequency", "keywords": "REFERENCES", "description": "Outside bar support requirement references event frequency."},
    {"source": "F.2.3.1 Bar Service Configuration", "target": "F.2.3.1 C.A.C. Customer Service Counter and Indoor Bar", "keywords": "CHILD_OF", "description": "Bar configuration is part of C.A.C. requirement."},
    {"source": "F.2.3.1 Resale Supply Verification", "target": "F.2.3.1 C.A.C. Customer Service Counter and Indoor Bar", "keywords": "CHILD_OF", "description": "Resale supply verification is part of F.2.3.1."},
    {"source": "F.2.3.1 Retail Service Rate Standard", "target": "F.2.3.1 C.A.C. Customer Service Counter and Indoor Bar", "keywords": "CHILD_OF", "description": "Retail service rate is part of F.2.3.1."},
    {"source": "F.2.3.1 Outside Bar Special Events Support", "target": "F.2.3.1 C.A.C. Customer Service Counter and Indoor Bar", "keywords": "CHILD_OF", "description": "Outside bar support is part of F.2.3.1."}
  ]
}

---

EXAMPLE 5: Equipment Inventory Tables with Building-Level Data

Input Text (TABLE + Narrative):
H.1.4.6. Preventive Maintenance: The Contractor shall ensure machines are maintained according to the manufacturer's recommendations by performing preventive maintenance tasks. The Contractor shall perform weekly operational/electrical checks to ensure all machines operate safely, are clean, and are free of corrosion.

TABLE H.2. APPLIANCE LISTING, LOCATION, AND REPAIR SCHEDULE:

WEEKLY:
Building 2959: 69 washers, 69 dryers
Building 3880: 44 washers, 50 dryers
Building 4505: 49 washers, 61 dryers
Machine Accountability Totals: 370 washers, 399 dryers (769 total units)

MONTHLY:
Building 4863 A/B: 1 washer, 1 dryer
Building 4864 C/D: 1 washer, 1 dryer
Monthly Machine Totals: 4 washers, 4 dryers (8 total units)

ON-CALL:
Building 4860 A/B: 1 washer, 1 dryer
Building 4861 C/D: 1 washer, 1 dryer
On-Call Machine Totals: 11 washers, 11 dryers (22 total units)

Output:
{
  "entities": [
    {"name": "Table H.2 Appliance Listing", "type": "document", "description": "TABLE H.2. APPLIANCE LISTING, LOCATION, AND REPAIR SCHEDULE. Contains building-level equipment inventory with maintenance schedules."},
    {"name": "H.1.4.6 Preventive Maintenance Requirement", "type": "requirement", "description": "H.1.4.6. Preventive Maintenance: The Contractor shall ensure machines are maintained according to the manufacturer's recommendations by performing preventive maintenance tasks. The Contractor shall perform weekly operational/electrical checks to ensure all machines operate safely, are clean, and are free of corrosion. Criticality: MANDATORY. Modal verb: shall. Labor drivers: weekly operational/electrical checks, 769 units weekly, 8 units monthly, 22 units on-call."},
    {"name": "Building 2959 Laundry Facility", "type": "location", "description": "Building 2959. Equipment counts: 69 washers, 69 dryers (138 total units). Maintenance schedule: Weekly."},
    {"name": "Building 3880 Laundry Facility", "type": "location", "description": "Building 3880. Equipment counts: 44 washers, 50 dryers (94 total units). Maintenance schedule: Weekly."},
    {"name": "Building 4505 Laundry Facility", "type": "location", "description": "Building 4505. Equipment counts: 49 washers, 61 dryers (110 total units). Maintenance schedule: Weekly."},
    {"name": "Building 4863 A/B Laundry Facility", "type": "location", "description": "Building 4863 A/B. Equipment counts: 1 washer, 1 dryer (2 total units). Maintenance schedule: Monthly."},
    {"name": "Building 4864 C/D Laundry Facility", "type": "location", "description": "Building 4864 C/D. Equipment counts: 1 washer, 1 dryer (2 total units). Maintenance schedule: Monthly."},
    {"name": "Building 4860 A/B Laundry Facility", "type": "location", "description": "Building 4860 A/B. Equipment counts: 1 washer, 1 dryer (2 total units). Maintenance schedule: On-Call."},
    {"name": "Building 4861 C/D Laundry Facility", "type": "location", "description": "Building 4861 C/D. Equipment counts: 1 washer, 1 dryer (2 total units). Maintenance schedule: On-Call."},
    {"name": "Weekly Maintenance Equipment Inventory", "type": "equipment", "description": "Weekly maintenance schedule equipment. Total: 370 washers, 399 dryers (769 total units across Buildings 2959, 3880, 4505)."},
    {"name": "Monthly Maintenance Equipment Inventory", "type": "equipment", "description": "Monthly maintenance schedule equipment. Total: 4 washers, 4 dryers (8 total units in Buildings 4863-4864)."},
    {"name": "On-Call Maintenance Equipment Inventory", "type": "equipment", "description": "On-call maintenance schedule equipment. Total: 11 washers, 11 dryers (22 total units in Buildings 4860-4861)."}
  ],
  "relationships": [
    {"source": "Building 2959 Laundry Facility", "target": "Weekly Maintenance Equipment Inventory", "keywords": "HAS_EQUIPMENT", "description": "Building location has weekly maintenance equipment."},
    {"source": "Building 3880 Laundry Facility", "target": "Weekly Maintenance Equipment Inventory", "keywords": "HAS_EQUIPMENT", "description": "Building location has weekly maintenance equipment."},
    {"source": "Building 4505 Laundry Facility", "target": "Weekly Maintenance Equipment Inventory", "keywords": "HAS_EQUIPMENT", "description": "Building location has weekly maintenance equipment."},
    {"source": "H.1.4.6 Preventive Maintenance Requirement", "target": "Weekly Maintenance Equipment Inventory", "keywords": "APPLIES_TO", "description": "Maintenance requirement applies to weekly equipment."},
    {"source": "Table H.2 Appliance Listing", "target": "Appendix H Equipment Maintenance", "keywords": "CHILD_OF", "description": "Table is part of Appendix H."},
    {"source": "H.1.4.6 Preventive Maintenance Requirement", "target": "Appendix H Equipment Maintenance", "keywords": "CHILD_OF", "description": "H.1.4.6 requirement is contained within Appendix H."}
  ]
}

---

EXAMPLE 6: Special Events and Training Requirements

Input Text:
F.2.4. Special Events: The Contractor shall arrange special events including live bands, shows, Armed Forces Entertainment, game shows, theme nights, and other similar events. Special events may require coordination through the 380 AEW. The COR must be notified of special events at least two (2) weeks prior to each planned event to ensure proper coordination.

F.2.3.2. Alcohol Management: All Contractor personnel must complete DRAM shop training prior to serving/selling alcohol and have proper training documentation on file with the Community Services Flight Chief. The Contractor shall use the approved Alcohol Management System provided by the Government. The Contractor shall track alcohol sales and strictly enforce alcohol limitations IAW AFCENT and 380 AEW alcohol policies with no violations allowed.

Output:
{
  "entities": [
    {"name": "F.2.4 Special Events Arrangement", "type": "requirement", "description": "F.2.4. Special Events: The Contractor shall arrange special events including live bands, shows, Armed Forces Entertainment, game shows, theme nights, and other similar events. Criticality: MANDATORY. Modal verb: shall."},
    {"name": "F.2.4 Special Events Notification", "type": "requirement", "description": "The COR must be notified of special events at least two (2) weeks prior to each planned event to ensure proper coordination. Criticality: MANDATORY. Modal verb: must. Lead time: 2 weeks advance notice."},
    {"name": "F.2.3.2 DRAM Shop Training Requirement", "type": "requirement", "description": "All Contractor personnel must complete DRAM shop training prior to serving/selling alcohol and have proper training documentation on file with the Community Services Flight Chief. Criticality: MANDATORY. Modal verb: must. Applies to: all personnel serving/selling alcohol."},
    {"name": "F.2.3.2 Alcohol Management System Usage", "type": "requirement", "description": "The Contractor shall use the approved Alcohol Management System provided by the Government. Criticality: MANDATORY. Modal verb: shall. System: Government-provided Alcohol Management System."},
    {"name": "F.2.3.2 Alcohol Policy Compliance", "type": "requirement", "description": "The Contractor shall track alcohol sales and strictly enforce alcohol limitations IAW AFCENT and 380 AEW alcohol policies with no violations allowed. Criticality: MANDATORY. Modal verb: shall. Performance standard: zero violations."},
    {"name": "380 AEW", "type": "organization", "description": "380th Air Expeditionary Wing (380 AEW). Coordination point for special events. Source of alcohol policies."},
    {"name": "Community Services Flight Chief", "type": "organization", "description": "Community Services Flight Chief. Maintains training documentation files for contractor personnel."},
    {"name": "AFCENT Alcohol Policy", "type": "document", "description": "Air Forces Central Command (AFCENT) alcohol policies. Governs alcohol limitations and enforcement."}
  ],
  "relationships": [
    {"source": "F.2.4 Special Events Arrangement", "target": "380 AEW", "keywords": "COORDINATED_WITH", "description": "Special events may require coordination through 380 AEW."},
    {"source": "F.2.3.2 DRAM Shop Training Requirement", "target": "Community Services Flight Chief", "keywords": "REPORTED_TO", "description": "Training documentation filed with Community Services Flight Chief."},
    {"source": "F.2.3.2 Alcohol Policy Compliance", "target": "AFCENT Alcohol Policy", "keywords": "GOVERNED_BY", "description": "Compliance requirement governed by AFCENT policy."},
    {"source": "F.2.4 Special Events Arrangement", "target": "Appendix F Recreational Services", "keywords": "CHILD_OF", "description": "F.2.4 requirement is contained within Appendix F."},
    {"source": "F.2.4 Special Events Notification", "target": "F.2.4 Special Events Arrangement", "keywords": "CHILD_OF", "description": "Notification requirement is part of F.2.4 Special Events."},
    {"source": "F.2.3.2 DRAM Shop Training Requirement", "target": "Appendix F Recreational Services", "keywords": "CHILD_OF", "description": "F.2.3.2 requirement is contained within Appendix F."},
    {"source": "F.2.3.2 Alcohol Management System Usage", "target": "F.2.3.2 DRAM Shop Training Requirement", "keywords": "CHILD_OF", "description": "System usage is part of F.2.3.2 Alcohol Management."},
    {"source": "F.2.3.2 Alcohol Policy Compliance", "target": "F.2.3.2 DRAM Shop Training Requirement", "keywords": "CHILD_OF", "description": "Policy compliance is part of F.2.3.2 Alcohol Management."}
  ]
}

---

EXAMPLE 7: GFP and CDRL Requirements

Input Text:
Government Furnished Property Reporting – The Contractor shall report GFP to the Contracting Officer within the task order specific time limits and using the current version of Government-furnished forms. [CDRL A016]. The Contractor shall report GFP: within 30 calendar days after the start of the period of performance, not later than 30 calendar days prior to the end of the period of performance, and at a minimum annually. The Contractor shall base reports on physical inventories.

Date of First Submission: Thirty (30) calendar days after the start of the Period of Performance (POP)
Frequency: As required

Output:
{
  "entities": [
    {"name": "Government Furnished Property Reporting", "type": "requirement", "description": "Government Furnished Property Reporting – The Contractor shall report GFP to the Contracting Officer within the task order specific time limits and using the current version of Government-furnished forms. [CDRL A016]. Criticality: MANDATORY. Modal verb: shall. CDRL reference: A016."},
    {"name": "GFP Report Initial Submission", "type": "deliverable", "description": "The Contractor shall report GFP within 30 calendar days after the start of the period of performance. Due date: 30 calendar days after POP start."},
    {"name": "GFP Report Final Submission", "type": "deliverable", "description": "GFP report due not later than 30 calendar days prior to the end of the period of performance. Due date: NLT 30 calendar days prior to POP end."},
    {"name": "GFP Physical Inventory Requirement", "type": "requirement", "description": "The Contractor shall base reports on physical inventories. Criticality: MANDATORY. Modal verb: shall."},
    {"name": "CDRL A016", "type": "deliverable", "description": "CDRL A016. Government Furnished Property reporting deliverable."},
    {"name": "Contracting Officer", "type": "organization", "description": "Contracting Officer. Receives GFP reports from contractor."}
  ],
  "relationships": [
    {"source": "Government Furnished Property Reporting", "target": "CDRL A016", "keywords": "TRACKED_BY", "description": "GFP reporting tracked by CDRL A016."},
    {"source": "GFP Report Initial Submission", "target": "Government Furnished Property Reporting", "keywords": "CHILD_OF", "description": "Initial submission is part of GFP reporting requirement."},
    {"source": "Government Furnished Property Reporting", "target": "Contracting Officer", "keywords": "SUBMITTED_TO", "description": "GFP reports submitted to Contracting Officer."}
  ]
}

---

EXAMPLE 8: ANTI-PATTERN — NOT Extracting Forced Relationships

When entities have NO semantic connection, do NOT create relationships just to connect them.

Input (Two unrelated entities in same chunk):
- Payment Terms (concept): "Net 30 payment terms apply to all invoices"
- Cybersecurity Controls (requirement): "Contractor shall implement NIST 800-171 controls"

WRONG Output (DO NOT DO THIS):
{
  "entities": [
    {"name": "Payment Terms", "type": "concept", "description": "Net 30 payment terms apply to all invoices."},
    {"name": "Cybersecurity Controls", "type": "requirement", "description": "Contractor shall implement NIST 800-171 controls."}
  ],
  "relationships": [
    {"source": "Payment Terms", "target": "Cybersecurity Controls", "keywords": "RELATED_TO", "description": "Both are contract requirements."}
  ]
}

Why this is WRONG:
- Payment terms and cybersecurity have NO semantic connection
- Different topics, no shared keywords, no logical relationship
- Creating such relationships dilutes the knowledge graph with noise
- Makes semantic search less accurate

CORRECT Output:
{
  "entities": [
    {"name": "Payment Terms", "type": "concept", "description": "Net 30 payment terms apply to all invoices."},
    {"name": "Cybersecurity Controls", "type": "requirement", "description": "Contractor shall implement NIST 800-171 controls. Criticality: MANDATORY. Modal verb: shall."}
  ],
  "relationships": []
}

ANTI-PATTERN SIGNALS (DO NOT create relationships when):
- Entities are in same chunk but discuss different topics
- Only connection is "both are requirements" or "both in same section"
- No shared domain keywords
- No logical business or technical dependency
- Just trying to "connect everything" without semantic justification
'''


# ============================================================================
# NEW PART L (quality checks - format-agnostic, lightly tweaked)
# ============================================================================
NEW_PART_L = """================================================================================
PART L: QUALITY CHECKS BEFORE OUTPUT
================================================================================

Before emitting the JSON object, validate:

1. NO ORPHAN ENTITIES: Every entity should link to at least one other entity
   (where a meaningful semantic connection exists).

2. CONSISTENT NAMING (CANONICALIZATION):
   - Same entity referenced with consistent naming across chunks
   - Normalize "FAR 52.212-1" vs "far 52.212-1" to a single form
   - Use canonical names (Title Case for sections, exact citations for clauses)
   - CRITICAL: If "ISS" and "Installation Support Services (ISS)" both appear,
     use "Installation Support Services (ISS)" for BOTH references
   - Do NOT create two separate entities for the same concept with different names

3. METADATA COMPLETENESS (embedded in `description`):
   - Requirements: criticality, modal_verb, labor drivers
   - Evaluation factors: weight, importance, subfactors
   - Submission instructions: page_limit, format_reqs
   - Performance standards: threshold, measurement_method
   - Clauses: clause_number, regulation
   - Labor categories: position_title, skill_level, clearance_level
   - Workload metrics: quantity, unit, period

4. SUBJECT VALIDATION:
   - "Contractor shall…" → REQUIREMENT (MANDATORY)
   - "Government shall…" → CONCEPT or GOVERNMENT_FURNISHED_ITEM (NOT a requirement!)

5. CONTENT OVER LABELS:
   - Don't trust "Section M" label blindly; verify it contains evaluation criteria
   - SOW/PWS may be in Section C OR in an attachment

6. QUANTITATIVE PRESERVATION:
   - All numbers, rates, frequencies preserved verbatim
   - Service rates include time windows
   - Equipment counts include building locations
   - Dollar volumes include ranges and conditions

7. REQUIRED FIELD VALIDATION (per object):
   - Entity: `name`, `type`, `description` all present and non-empty
   - Relationship: `source`, `target`, `keywords`, `description` all present and non-empty
   - `keywords` first token MUST be one of the 32 canonical UPPERCASE relationship types

8. RELATIONSHIP TYPE VALIDATION:
   - First comma-separated token of `keywords` must match VALID RELATIONSHIP TYPES exactly
   - Direction must follow SOURCE → TARGET DIRECTIONALITY rules in Part J
   - Use RELATED_TO only as a last resort

9. CROSS-REFERENCE INTEGRITY:
   - EVALUATION_FACTOR ↔ PROPOSAL_INSTRUCTION GUIDES edges exist where both are present
   - REQUIREMENT → EVALUATION_FACTOR EVALUATED_BY edges exist where both are present
   - APPENDIX/ATTACHMENT entities have a CHILD_OF edge to their parent
   - CLAUSE → SECTION attribution is consistent

10. ENUM VALIDATION (for descriptions):
    - criticality ∈ MANDATORY, IMPORTANT, OPTIONAL, INFORMATIONAL
    - theme_type ∈ DISCRIMINATOR, PROOF_POINT, WIN_THEME
    - modal_verb ∈ shall, should, may, must, will, can, encouraged
    - work_type ∈ SOW, PWS, SOO

11. JSON VALIDITY:
    - Output is a single object: `{"entities": [...], "relationships": [...]}`
    - All strings properly escaped (double-quote, backslash, control chars)
    - No trailing commas, no comments, no markdown fences, no commentary

================================================================================
"""


# Genuine substitution placeholders that .format(**context_base) WILL fill.
# Everything else with literal { } must be escaped to {{ }} so str.format() doesn't choke.
LEGIT_PLACEHOLDERS = {
    "entity_types_guidance",
    "language",
    "examples",
    "max_total_records",
    "max_entity_records",
    "input_text",
    "completion_delimiter",  # may still appear in surviving prose; we drop it below
    "tuple_delimiter",
}


def escape_literal_braces(text: str) -> str:
    """
    Escape every literal `{` and `}` to `{{` `}}` so the upstream
    `.format(**context_base)` call doesn't try to parse JSON examples as
    Python format placeholders. Preserve genuine `{name}` placeholders for
    LEGIT_PLACEHOLDERS.

    Strategy: tokenize on the `{name}` placeholder pattern, replace literal
    braces in the surrounding chunks, leave matched placeholders alone.
    """
    placeholder_re = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
    out = []
    last = 0
    for m in placeholder_re.finditer(text):
        chunk = text[last:m.start()]
        out.append(chunk.replace("{", "{{").replace("}", "}}"))
        name = m.group(1)
        if name in LEGIT_PLACEHOLDERS:
            out.append(m.group(0))  # keep as-is for .format()
        else:
            # Treat unknown {x} as literal text — escape it
            out.append("{{" + name + "}}")
        last = m.end()
    tail = text[last:]
    out.append(tail.replace("{", "{{").replace("}", "}}"))
    return "".join(out)


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    lines = raw.splitlines()

    # Find where Part J starts in the source (it's the first "PART J:" header line)
    part_j_start = None
    for i, ln in enumerate(lines):
        if ln.startswith("PART J:"):
            # The "===" rule line is one above; back up to that line.
            part_j_start = i - 1
            break
    if part_j_start is None:
        raise RuntimeError("Could not locate PART J: header in native.txt")

    # Slice Parts A through I (everything before Part J's rule line)
    body_a_through_i = "\n".join(lines[:part_j_start])

    # Convert the 11 inline tuple mini-examples to JSON
    body_a_through_i = transform_inline_tuples(body_a_through_i)

    # Replace the file header (first 8 lines: title + rule + 6 metadata lines)
    body_lines = body_a_through_i.splitlines()
    # The original header is the first block ending at the blank line before PART A.
    # Find the first "PART A:" line.
    first_part_a = None
    for i, ln in enumerate(body_lines):
        if ln.startswith("PART A:"):
            first_part_a = i
            break
    if first_part_a is None:
        raise RuntimeError("Could not locate PART A: header in native.txt")
    # The "===" rule line is at first_part_a - 1; another rule line at first_part_a + 1.
    # Header block ends at first_part_a - 2 inclusive (the ==== rule above PART A).
    after_header = "\n".join(body_lines[first_part_a - 1:])

    # Assemble final document
    final = "\n".join([
        NEW_HEADER,
        "",
        after_header.rstrip(),
        "",
        NEW_PART_J.rstrip(),
        "",
        NEW_PART_K.rstrip(),
        "",
        NEW_PART_L.rstrip(),
        "",
    ])

    DST.write_text(escape_literal_braces(final), encoding="utf-8", newline="\n")
    final_written = DST.read_text(encoding="utf-8")
    print(f"Wrote {DST} ({len(final_written):,} chars, {final_written.count(chr(10)):,} lines)")
    # Sanity 1: confirm no leftover {tuple_delimiter} or {completion_delimiter}
    leaks = re.findall(r"(?<!\{)\{tuple_delimiter\}|(?<!\{)\{completion_delimiter\}", final_written)
    if leaks:
        raise RuntimeError(f"Tuple/completion placeholder leaked into JSON prompt: {len(leaks)} occurrences")
    # Sanity 2: confirm str.format() succeeds with stub kwargs
    try:
        final_written.format(
            entity_types_guidance="<stub>",
            language="English",
            examples="<stub>",
            max_total_records=200,
            max_entity_records=160,
            input_text="<stub>",
            completion_delimiter="<|COMPLETE|>",
            tuple_delimiter="<|#|>",
        )
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError(f"Prompt fails .format() smoke test: {e}") from e
    print("OK — no tuple_delimiter / completion_delimiter leaks; .format() smoke passes.")


if __name__ == "__main__":
    main()
