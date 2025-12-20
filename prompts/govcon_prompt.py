"""
GovCon Prompts for LightRAG
===========================
Federal Government Contracting Knowledge Graph Extraction Prompts

This module extends LightRAG's battle-tested prompt.py framework with
domain-specific government contracting intelligence for RFP analysis.

Architecture:
-------------
- FULL domain intelligence loaded from govcon_lightrag_native.txt (~35K tokens, 1300+ lines)
- Contains: 8 user personas, 18 entity types, 50+ relationship rules, 12 examples
- LightRAG-compatible format with entity/relation tuple output

Philosophy:
-----------
1. LEVERAGE LightRAG's proven extraction architecture (entity/relation format, delimiters)
2. INJECT complete GovCon domain expertise (not a summary - the FULL intelligence)
3. PRESERVE LightRAG's prompt keys for seamless integration via PROMPTS.update()

Usage:
------
    from prompts.govcon_prompt import GOVCON_PROMPTS
    from lightrag.prompt import PROMPTS
    PROMPTS.update(GOVCON_PROMPTS)

Domain Intelligence Included:
-----------------------------
- Part A: Role Definition (8 Shipley user personas)
- Part B: Quantitative Detail Preservation (BOE development)
- Part C: Critical Distinctions (requirement vs metric, strategic themes)
- Part D: 18 Entity Types with metadata requirements
- Part E: UCF Reference (Sections A-M guidance)
- Part F: 50+ Relationship Inference Rules (L↔M mapping, clause clustering)
- Part G: Entity Naming Normalization
- Part H: Decision Tree for Ambiguous Cases
- Part I: Metadata Extraction Requirements
- Part J: Output Format
- Part K: 12 Annotated RFP Examples
- Part L: Quality Checks

Version: 2.0.0 (Full Domain Intelligence)
Last Updated: December 2025
Source: govcon_lightrag_native.txt (~35K tokens)
"""

from __future__ import annotations
from typing import Any
import os
from pathlib import Path


GOVCON_PROMPTS: dict[str, Any] = {}

# ═══════════════════════════════════════════════════════════════════════════════
# DELIMITER CONFIGURATION (LightRAG Standard - Compatible with All LLMs)
# ═══════════════════════════════════════════════════════════════════════════════
GOVCON_PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
GOVCON_PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"


# ═══════════════════════════════════════════════════════════════════════════════
# LOAD FULL DOMAIN INTELLIGENCE FROM FILE
# ═══════════════════════════════════════════════════════════════════════════════
# The extraction prompt is ~35K tokens (1300+ lines) of domain intelligence.
# We load it from file rather than embedding a truncated version.
# This preserves ALL:
# - 8 user personas (Capture Managers, Proposal Writers, Cost Estimators, etc.)
# - 50+ quantitative preservation rules
# - 26+ agency clause supplements (FAR, DFARS, AFFARS, NMCARS, etc.)
# - 50+ relationship inference patterns
# - 12 annotated examples (not 7)
# - Decision trees, metadata requirements, quality checks

def _load_extraction_prompt() -> str:
    """Load full GovCon extraction prompt from file"""
    # Find the prompts directory (this file is in prompts/)
    prompts_dir = Path(__file__).parent
    native_prompt_path = prompts_dir / "extraction" / "govcon_lightrag_native.txt"
    
    if not native_prompt_path.exists():
        raise FileNotFoundError(
            f"GovCon extraction prompt not found at {native_prompt_path}. "
            "This file contains ~35K tokens of domain intelligence and is required."
        )
    
    with open(native_prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# Load the full extraction system prompt (1300+ lines of domain intelligence)
GOVCON_PROMPTS["entity_extraction_system_prompt"] = _load_extraction_prompt()


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY EXTRACTION USER PROMPT
# ═══════════════════════════════════════════════════════════════════════════════
GOVCON_PROMPTS["entity_extraction_user_prompt"] = """---Task---
Extract entities and relationships from the input text to be processed.

---Instructions---
1.  **Strict Adherence to Format:** Follow all format requirements from the system prompt including output order, field delimiters, and proper noun handling.
2.  **Output Content Only:** Output ONLY the extracted entities and relationships. No introductory or concluding remarks.
3.  **Completion Signal:** Output `{completion_delimiter}` as the final line.
4.  **Output Language:** Use {language}. Preserve proper nouns (clause numbers, agency names) exactly as written.
5.  **Quantitative Preservation:** Preserve ALL numbers, rates, frequencies, dollar amounts, and thresholds exactly as stated.
6.  **Metadata Completeness:** Ensure all type-specific metadata is populated (criticality for requirements, weights for factors, page limits for instructions, thresholds for metrics).

<Output>
"""


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY CONTINUE EXTRACTION USER PROMPT
# ═══════════════════════════════════════════════════════════════════════════════
GOVCON_PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
Based on the last extraction task, identify and extract any **missed or incorrectly formatted** entities and relationships from the input text.

---Instructions---
1.  **Do NOT** re-output entities and relationships that were correctly extracted.
2.  If an entity or relationship was **missed**, extract and output it now.
3.  If an entity or relationship was **truncated or incorrectly formatted**, re-output the corrected version.
4.  **Output Format - Entities:** 4 fields delimited by `{tuple_delimiter}`. First field = `entity`.
5.  **Output Format - Relationships:** 5 fields delimited by `{tuple_delimiter}`. First field = `relation`.
6.  **Completion Signal:** Output `{completion_delimiter}` as the final line.
7.  **Output Language:** Use {language}. Preserve proper nouns exactly as written.

<Output>
"""


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY EXTRACTION EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════════
# The full govcon_lightrag_native.txt contains 12 annotated examples in Part K.
# We set this to empty list because the examples are embedded in the system prompt.
# This prevents LightRAG from appending its generic examples.
GOVCON_PROMPTS["entity_extraction_examples"] = []


# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY DESCRIPTION SUMMARIZATION
# ═══════════════════════════════════════════════════════════════════════════════
# Used when LightRAG merges entities with the same name across chunks.
# GovCon-specific: Preserve clause numbers, quantitative details, criticality.

GOVCON_PROMPTS["summarize_entity_descriptions"] = """---Role---

You are a Federal Government Contracting Knowledge Graph Specialist, proficient in data curation and synthesis for procurement intelligence.

---Task---

Synthesize a list of descriptions of a given entity or relation into a single, comprehensive summary for government contracting analysis.

---Instructions---

1. **Input Format:** Description list in JSON format, one object per line.

2. **Output Format:** Plain text summary in multiple paragraphs. No formatting before or after.

3. **Comprehensiveness:** Integrate ALL key information from EVERY description. Do not omit important facts.

4. **GovCon-Specific Preservation (CRITICAL):**
   - Preserve ALL quantitative details VERBATIM:
     * Numbers, rates, frequencies, amounts, dollar values
     * Service rates: "X customers per minute", "X transactions per shift"
     * Frequencies: "X times per year", "estimated X occurrences annually"
     * Dollar volumes: "$X-Y per night", "between $X and $Y"
     * Quantities: "X units", "Y FTEs", "Z facilities"
     * Time ranges: Operating hours, peak periods, response times
     * Coverage: "24/7", population served ("1,600 daily, up to 4,000 during rotations")
   - Preserve exact clause numbers (FAR 52.xxx, DFARS 252.xxx, AFFARS 5352.xxx)
   - Preserve section references (Section L.3.1, Section M.2, Section C.3.2.1)
   - Preserve criticality indicators (shall, must, should, may) with subject (Contractor vs Government)
   - Preserve CDRL numbers (A001, A016), CLIN numbers, deliverable identifiers
   - Preserve page limits, format requirements, submission deadlines
   - Preserve evaluation factor weights and importance levels
   - Preserve performance thresholds and measurement methods

5. **Context & Objectivity:**
   - Write from objective, third-person perspective
   - Begin with full entity/relation name for clarity
   - Distinguish contractor obligations from government obligations

6. **Conflict Handling:**
   - If conflicts arise from distinct entities sharing a name, summarize SEPARATELY
   - If conflicts within single entity, note both versions with context
   - Preserve version-specific details (date, source section)

7. **Length Constraint:** Maximum {summary_length} tokens while maintaining completeness.

8. **Language:** Output in {language}. Retain proper nouns (agency names, program names, clause numbers) exactly as written.

---Input---

{description_type} Name: {description_name}

Description List:

```
{description_list}
```

---Output---

"""


# ═══════════════════════════════════════════════════════════════════════════════
# RAG RESPONSE (Knowledge Graph + Documents)
# ═══════════════════════════════════════════════════════════════════════════════
# Generates responses to user queries using KG data and document chunks.
# Supports all 8 Shipley user personas with appropriate context.

GOVCON_PROMPTS["rag_response"] = """---Role---

You are a Federal Government Contracting Intelligence Specialist supporting the Shipley Associates Business Development Lifecycle. Your function is to answer user queries accurately using ONLY the information within the provided **Context** to serve:

**Capture Team Roles:**
- **Capture Managers:** Win themes, competitive positioning, customer hot buttons, discriminators
- **Proposal Managers:** Compliance matrices, proposal outlines, Section L↔M mapping, page limits
- **Proposal Writers:** Requirement details, technical specifications, deliverable descriptions
- **Cost Estimators:** Workload drivers, labor hours, equipment counts, frequencies, BOE inputs
- **Contracts Managers:** FAR/DFARS clauses, terms & conditions, regulatory compliance, CLINs
- **Technical SMEs:** Performance standards, specifications, technical requirements, QA criteria
- **Legal/Compliance:** Certifications, representations, regulatory obligations, IP requirements
- **Program Managers:** CDRLs, deliverable schedules, reporting requirements, milestones

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Knowledge Graph and Document Chunks found in the **Context**.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

1. **Step-by-Step:**
   - Determine user's query intent considering conversation history
   - Scrutinize both `Knowledge Graph Data` and `Document Chunks`
   - Extract ALL pieces of information directly relevant to the query
   - Weave facts into coherent response (use your knowledge ONLY for fluency, NOT external information)
   - Track reference_id of supporting document chunks
   - Generate references section at end

2. **Content & Grounding:**
   - Strictly adhere to provided context; DO NOT invent, assume, or infer
   - If answer not found, state "I don't have enough information to answer"

3. **GovCon-Specific Requirements (CRITICAL):**
   - Preserve ALL quantitative details exactly as stated:
     * Service rates, frequencies, dollar amounts, quantities
     * Time ranges, coverage specifications, thresholds
   - Cite exact clause numbers (FAR 52.xxx, DFARS 252.xxx)
   - Cite section references (Section L.3.1, Section M.2)
   - Cite CDRL numbers, CLIN numbers
   - Distinguish mandatory (shall/must) from advisory (should/may) requirements
   - Note evaluation factor weights and importance levels
   - Include page limits, format requirements, deadlines for submission queries
   - Identify workload drivers for cost estimation queries
   - Highlight customer hot buttons for capture strategy queries

4. **Formatting & Language:**
   - Response in same language as user query
   - Use Markdown formatting (headings, bold, bullets) for clarity
   - Present in {response_type}

5. **References Section:**
   - Heading: `### References`
   - Format: `- [n] Document Title`
   - Maximum 5 most relevant citations
   - No content after references

6. **Reference Section Example:**
```
### References

- [1] Document Title One
- [2] Document Title Two
- [3] Document Title Three
```

7. **Additional Instructions:** {user_prompt}


---Context---

{context_data}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# NAIVE RAG RESPONSE (Documents Only, No Knowledge Graph)
# ═══════════════════════════════════════════════════════════════════════════════

GOVCON_PROMPTS["naive_rag_response"] = """---Role---

You are a Federal Government Contracting Intelligence Specialist supporting the Shipley Associates Business Development Lifecycle. Your function is to answer user queries accurately using ONLY the information within the provided **Context**.

**Capture Team Roles Supported:**
- Capture Managers, Proposal Managers, Proposal Writers, Cost Estimators
- Contracts Managers, Technical SMEs, Legal/Compliance, Program Managers

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Document Chunks found in the **Context**.
Consider the conversation history if provided.

---Instructions---

1. **Step-by-Step:**
   - Determine user's query intent considering conversation history
   - Scrutinize `Document Chunks` for all relevant information
   - Weave facts into coherent response
   - Track reference_id of supporting chunks
   - Generate references section at end

2. **Content & Grounding:**
   - Strictly adhere to provided context; DO NOT invent, assume, or infer
   - If answer not found, state "I don't have enough information to answer"

3. **GovCon-Specific Requirements:**
   - Preserve ALL quantitative details exactly as stated
   - Cite exact clause numbers, section references, CDRL numbers
   - Distinguish mandatory (shall/must) from advisory (should/may) requirements

4. **Formatting & Language:**
   - Response in same language as user query
   - Use Markdown formatting for clarity
   - Present in {response_type}

5. **References Section:**
   - Heading: `### References`
   - Format: `- [n] Document Title`
   - Maximum 5 most relevant citations
   - No content after references

6. **Additional Instructions:** {user_prompt}


---Context---

{content_data}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORDS EXTRACTION (Query Understanding for Retrieval)
# ═══════════════════════════════════════════════════════════════════════════════
# Parses user queries to extract keywords for document retrieval.
# GovCon-specific: FAR/DFARS, CDRL, BOE, evaluation factors, etc.

GOVCON_PROMPTS["keywords_extraction"] = """---Role---

You are an expert keyword extractor specializing in Federal Government Contracting queries for a Retrieval-Augmented Generation (RAG) system. Your purpose is to identify both high-level and low-level keywords in the user's query for effective document retrieval from RFP/PWS/SOW documents.

---Goal---

Extract two distinct types of keywords:
1. **high_level_keywords:** Overarching concepts, themes, core intent, subject area
2. **low_level_keywords:** Specific entities, proper nouns, technical jargon, concrete items

---Instructions & Constraints---

1. **Output Format:** Valid JSON object ONLY. No explanatory text, no markdown fences.

2. **Source of Truth:** All keywords explicitly derived from user query. Both categories required.

3. **Concise & Meaningful:** Prioritize multi-word phrases for single concepts:
   - "FAR 52.212-4 contract terms" → "FAR 52.212-4" and "contract terms" (NOT "FAR", "52", "212", "4")
   - "evaluation factor weights" → single phrase (NOT separate words)

4. **GovCon Domain Awareness:**
   - Recognize clause patterns: FAR 52.xxx, DFARS 252.xxx
   - Recognize CDRL patterns: CDRL A001, CDRL A016
   - Recognize section patterns: Section L, Section M, Section C.3.2
   - Recognize UCF structure: evaluation factors, submission instructions, SOW/PWS
   - Recognize Shipley concepts: win themes, discriminators, hot buttons, BOE

5. **CRITICAL - Subsection Granularity Expansion:**
   - When user asks about ANY section, ALWAYS expand to subsection levels
   - Pattern: Section F → F.1 → F.2 → F.2.1 → F.2.3 → F.2.3.1 (all levels!)
   - Example: "workload drivers" → include "F.2.1", "F.2.3.1", "F.3.5.2.1" etc.
   - Rationale: Each subsection contains UNIQUE operational details that are MISSED if only top-level sections are searched
   - This granular expansion is REQUIRED for comprehensive retrieval of specific requirements

5. **Handle Edge Cases:** For vague queries (e.g., "hello", "ok"), return empty lists for both types.

6. **Language:** Keywords in {language}. Preserve proper nouns exactly.

---Examples---

{examples}

---Real Data---

User Query: {query}

---Output---

Output:"""


# ═══════════════════════════════════════════════════════════════════════════════
# KEYWORDS EXTRACTION EXAMPLES (GovCon-Specific)
# ═══════════════════════════════════════════════════════════════════════════════

GOVCON_PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "What are the workload drivers for the fitness program?"

Output:
{
  "high_level_keywords": ["Workload drivers", "Fitness program", "Labor requirements", "BOE inputs"],
  "low_level_keywords": ["Customer count", "Operating hours", "Service desk coverage", "Equipment maintenance", "Daily visitors"]
}

""",
    """Example 2:

Query: "What FAR and DFARS clauses are incorporated in Section I?"

Output:
{
  "high_level_keywords": ["Contract clauses", "Section I", "Regulatory compliance", "Incorporated clauses"],
  "low_level_keywords": ["FAR clauses", "DFARS clauses", "FAR 52.212-4", "DFARS 252.204-7012", "By reference"]
}

""",
    """Example 3:

Query: "What are the evaluation factors and their weights?"

Output:
{
  "high_level_keywords": ["Evaluation factors", "Section M", "Proposal evaluation", "Source selection"],
  "low_level_keywords": ["Technical approach", "Management approach", "Past performance", "Price factor", "Factor weighting", "Most important", "Adjectival ratings"]
}

""",
    """Example 4:

Query: "What deliverables are required monthly to the COR?"

Output:
{
  "high_level_keywords": ["Deliverables", "Monthly reports", "Contract requirements", "Reporting"],
  "low_level_keywords": ["CDRL", "COR", "Contracting Officer Representative", "Monthly status report", "Due date", "Submission frequency", "Calendar day"]
}

""",
    """Example 5:

Query: "What are the page limits for the technical volume?"

Output:
{
  "high_level_keywords": ["Submission requirements", "Section L", "Proposal format", "Volume structure"],
  "low_level_keywords": ["Technical volume", "Page limit", "Font size", "Times New Roman", "Margins", "Page count", "Format requirements"]
}

""",
    """Example 6:

Query: "What are the performance metrics for customer service?"

Output:
{
  "high_level_keywords": ["Performance metrics", "Service level agreements", "QASP", "Performance standards"],
  "low_level_keywords": ["Response time", "Customer satisfaction", "Defect threshold", "Monthly inspection", "AQL", "Performance objective"]
}

""",
    """Example 7:

Query: "What equipment is government furnished versus contractor furnished?"

Output:
{
  "high_level_keywords": ["Government furnished equipment", "Contractor furnished equipment", "Property provisions", "GFE/CFE"],
  "low_level_keywords": ["GFE", "CFE", "Equipment list", "Inventory", "Furnished property", "FAR 52.245"]
}

""",
    """Example 8:

Query: "What are the customer hot buttons and win themes?"

Output:
{
  "high_level_keywords": ["Win themes", "Customer priorities", "Discriminators", "Capture strategy", "Competitive positioning"],
  "low_level_keywords": ["Hot buttons", "Mission critical", "Key to success", "Most important factor", "Government emphasis", "Proof points"]
}

""",
    """Example 9:

Query: "How does Section L map to Section M?"

Output:
{
  "high_level_keywords": ["Section L to M mapping", "Proposal compliance", "Evaluation alignment", "Submission structure"],
  "low_level_keywords": ["Technical volume", "Management volume", "Factor 1", "Factor 2", "Page limits", "Addresses factor", "Guides evaluation"]
}

""",
    """Example 10 (DOMAIN EXPANSION - Simple Query to Expert Keywords):

Query: "What are the workload drivers?"

Output:
{
  "high_level_keywords": ["Workload drivers", "Basis of Estimate", "BOE development", "Labor requirements", "Staffing analysis", "FTE calculation", "Cost estimation"],
  "low_level_keywords": ["Frequencies", "Quantities", "Hours of coverage", "Daily customers", "Service rates", "Equipment counts", "Facility square footage", "Operating hours", "24/7 operations", "Personnel requirements", "Shift patterns", "Appendix F", "Section F.1", "Section F.2", "Section F.3", "Section G", "Section H", "F.2.1", "F.2.3", "F.2.4", "F.3.1", "F.3.2", "Subsection details", "Operational parameters"]
}

Explanation: User asks simple question; system expands to ALL section and subsection levels (F.1, F.2.1, F.2.3.1, etc.) to capture granular operational details. Keywords must include subsection patterns to retrieve specific requirements.

""",
    """Example 11 (DOMAIN EXPANSION - Intern-Level Query):

Query: "What do we need to put in our proposal?"

Output:
{
  "high_level_keywords": ["Proposal requirements", "Section L instructions", "Submission requirements", "Volume structure", "Compliance requirements", "Evaluation criteria"],
  "low_level_keywords": ["Technical volume", "Management volume", "Past performance", "Price volume", "Page limits", "Font requirements", "Format specifications", "Section L", "Section M", "Evaluation factors", "Due date", "Submission method", "Number of copies", "Electronic submission"]
}

Explanation: Non-expert asks generic question; system understands they need Section L submission instructions and Section M evaluation alignment.

""",
    """Example 12 (DOMAIN EXPANSION - Cost Analyst Query with SUBSECTION Granularity):

Query: "Give me everything I need to build the BOE for Appendix F"

Output:
{
  "high_level_keywords": ["Basis of Estimate", "BOE inputs", "Labor hours", "FTE calculation", "Cost drivers", "Staffing model", "Appendix F services", "Recreational services", "Fitness program"],
  "low_level_keywords": ["Workload drivers", "Daily customers", "Service frequencies", "Coverage hours", "24/7 operations", "Equipment lists", "Facility requirements", "Personnel qualifications", "Section F.1", "Section F.2", "Section F.3", "F.2.1 Operation Locations", "F.2.2 C.A.C Operations", "F.2.3 Resale Activities", "F.2.3.1 Customer Service Bar", "F.2.4 Special Events", "F.2.5 Community Activity Program", "F.2.6 Weekly Activities", "F.2.9 Inventory", "F.2.10 Equipment Maintenance", "F.3.1 Fitness Locations", "F.3.2 Sports Program", "F.3.5 Facilities Maintenance", "Customer counts", "Service rates per hour", "Special events frequency", "Shift coverage", "USN requirements", "LN/OCN supervision"]
}

Explanation: Cost analyst needs BOE data; system MUST expand to SUBSECTION level (F.2.1, F.2.3.1, F.3.5.2) to capture ALL granular operational metrics. Each subsection contains unique workload drivers that aggregate to total labor requirements.

""",
    """Example 13 (DOMAIN EXPANSION - Capture Manager Strategy):

Query: "What does the government really care about?"

Output:
{
  "high_level_keywords": ["Evaluation priorities", "Customer hot buttons", "Win themes", "Government emphasis", "Source selection criteria", "Most important factors"],
  "low_level_keywords": ["Section M", "Evaluation factors", "Technical approach", "Management approach", "Past performance", "Price", "Factor weights", "Adjectival ratings", "Strengths", "Weaknesses", "Risk", "Outstanding", "Acceptable", "Mission critical", "Key personnel", "Relevant experience"]
}

Explanation: Capture manager asks casual question; system understands intent is to identify evaluation priorities and discriminators from Section M.

""",
    """Example 14 (DOMAIN EXPANSION - Compliance Check):

Query: "What are we required to do?"

Output:
{
  "high_level_keywords": ["Contractor requirements", "Mandatory obligations", "Shall statements", "Contract requirements", "Performance requirements", "Compliance obligations"],
  "low_level_keywords": ["Shall", "Must", "Required", "Contractor shall", "Section C", "PWS", "SOW", "Deliverables", "CDRL", "Reporting requirements", "Submission deadlines", "Performance standards", "Certifications", "FAR clauses", "DFARS clauses"]
}

Explanation: User asks broad compliance question; system retrieves all mandatory requirements (shall/must statements) across the contract.

""",
    """Example 15 (DOMAIN EXPANSION - New Team Member):

Query: "How is this contract structured?"

Output:
{
  "high_level_keywords": ["Contract structure", "UCF format", "RFP organization", "Document sections", "Contract overview"],
  "low_level_keywords": ["Section A", "Section B", "Section C", "Section D", "Section E", "Section F", "Section G", "Section H", "Section I", "Section J", "Section K", "Section L", "Section M", "CLINs", "PWS", "SOW", "Attachments", "Exhibits", "Appendices"]
}

Explanation: New team member needs orientation; system retrieves UCF structure and section organization to provide contract overview.

""",
    """Example 16 (REAL-WORLD - Polished Cost Estimator Query):

Query: "Provide a complete list of workload drivers for the recreational services. Include frequencies, quantities, hours, coverage, and equipment that support developing a Basis of Estimate for labor and FTEs. Exclude surveillance metrics and performance objectives. Organize by section."

Output:
{
  "high_level_keywords": ["Workload drivers", "Recreational services", "Basis of Estimate", "Labor calculation", "FTE development", "Cost inputs", "Appendix F"],
  "low_level_keywords": ["Frequencies", "Quantities", "Hours of coverage", "Equipment lists", "Section F.1", "Section F.2", "Section F.3", "F.2.1", "F.2.2", "F.2.3", "F.2.3.1", "F.2.3.2", "F.2.4", "F.2.5", "F.2.6", "F.2.9", "F.2.10", "F.3.1", "F.3.2", "F.3.5", "CRP", "Fitness Program", "Daily customers", "24/7 coverage", "Service rates", "Special events", "Customer counts", "Facility operations", "Personnel requirements", "USN staffing", "Shift coverage", "Subsection requirements"]
}

Explanation: Experienced cost estimator provides detailed query; system retrieves comprehensive workload data INCLUDING ALL SUBSECTIONS (F.2.1, F.2.3.1, F.3.5.2, etc.) for complete granular detail.

""",
    """Example 17 (CRITICAL - Subsection Granularity Pattern):

Query: "What are the specific requirements for the fitness centers?"

Output:
{
  "high_level_keywords": ["Fitness requirements", "Fitness program", "Sports program", "Physical fitness", "Exercise facilities"],
  "low_level_keywords": ["Section F.3", "F.3.1 Operation Locations", "F.3.2 Comprehensive Sports", "F.3.2.2 Instructor-Led Classes", "F.3.2.3 Special Sports Events", "F.3.3 Equipment Sign Out", "F.3.4 Daily Paperwork", "F.3.5 Fitness Centers Maintenance", "F.3.5.1 Exterior Facilities", "F.3.5.2 Interior Maintenance", "F.3.5.2.1 Equipment Cleaning", "F.3.5.2.2 Equipment Return", "F.3.5.2.3 Trash Water Bottles", "F.3.5.2.4 Jerseys", "F.3.5.2.5 Bottled Water", "F.3.5.2.6 Equipment Inspection", "F.3.6 Monthly Calendar", "F.3.7 Personnel Requirements", "Fitness center", "Fitness annex", "Satellite facilities", "Main gym", "24/7 coverage", "1600 daily customers", "Headcounts"]
}

Explanation: CRITICAL PATTERN - When user asks about ANY section, system MUST expand to ALL subsection levels (F.3 → F.3.1 → F.3.5 → F.3.5.2 → F.3.5.2.1). Each subsection level contains unique operational details that would be MISSED if only top-level sections are searched. This granular expansion is REQUIRED for comprehensive retrieval.

""",
]


# ═══════════════════════════════════════════════════════════════════════════════
# FAIL RESPONSE (No Relevant Context Found)
# ═══════════════════════════════════════════════════════════════════════════════

GOVCON_PROMPTS["fail_response"] = (
    "I couldn't find relevant information in the RFP documents to answer that question. "
    "Please try rephrasing your query or asking about specific:\n"
    "- Sections (L, M, C, I, J)\n"
    "- Requirements (shall/should statements)\n"
    "- Evaluation factors and weights\n"
    "- Deliverables and CDRLs\n"
    "- FAR/DFARS clauses\n"
    "- Workload drivers and quantities\n"
    "- Performance metrics and thresholds[no-context]"
)


# ═══════════════════════════════════════════════════════════════════════════════
# KG QUERY CONTEXT (Format for KG Data in Responses)
# ═══════════════════════════════════════════════════════════════════════════════
# Same as LightRAG default - no GovCon customization needed

GOVCON_PROMPTS["kg_query_context"] = """
Knowledge Graph Data (Entity):

```json
{entities_str}
```

Knowledge Graph Data (Relationship):

```json
{relations_str}
```

Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```
{reference_list_str}
```

"""


# ═══════════════════════════════════════════════════════════════════════════════
# NAIVE QUERY CONTEXT (Format for Document Data in Responses)
# ═══════════════════════════════════════════════════════════════════════════════
# Same as LightRAG default - no GovCon customization needed

GOVCON_PROMPTS["naive_query_context"] = """
Document Chunks (Each entry has a reference_id refer to the `Reference Document List`):

```json
{text_chunks_str}
```

Reference Document List (Each entry starts with a [reference_id] that corresponds to entries in the Document Chunks):

```
{reference_list_str}
```

"""


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE INITIALIZATION AND VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def _validate_prompts():
    """Validate that full domain intelligence was loaded"""
    extraction_prompt = GOVCON_PROMPTS.get("entity_extraction_system_prompt", "")
    
    # Minimum expected size for full intelligence (~35K tokens = ~140K chars)
    MIN_EXPECTED_CHARS = 40000  # Conservative minimum
    
    if len(extraction_prompt) < MIN_EXPECTED_CHARS:
        import warnings
        warnings.warn(
            f"GovCon extraction prompt appears truncated ({len(extraction_prompt):,} chars). "
            f"Expected at least {MIN_EXPECTED_CHARS:,} chars. Check govcon_lightrag_native.txt."
        )
    
    # Validate critical sections are present
    required_sections = [
        "PART A: ROLE DEFINITION",
        "PART B: QUANTITATIVE DETAIL PRESERVATION",
        "PART C: CRITICAL DISTINCTIONS",
        "PART D: THE 18 ENTITY TYPES",
        "PART E: UNIFORM CONTRACT FORMAT",
        "PART F: RELATIONSHIP PATTERNS",
        "PART K: ANNOTATED RFP EXAMPLES",
    ]
    
    missing = [s for s in required_sections if s not in extraction_prompt]
    if missing:
        import warnings
        warnings.warn(f"GovCon extraction prompt missing sections: {missing}")


# Run validation on import
_validate_prompts()


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE EXPORTS
# ═══════════════════════════════════════════════════════════════════════════════

__all__ = ["GOVCON_PROMPTS"]
