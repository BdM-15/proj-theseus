from __future__ import annotations
from typing import Any

# ============================================================================
# PHASE 3: GOVERNMENT CONTRACTING PROMPT MODIFICATIONS
# ============================================================================
"""
Phase 3 Changes:
1. Replaced generic entity extraction examples with government contracting examples
2. Examples now demonstrate proper RFP entity/relationship patterns:
   - Section references (L, M, C, etc.)
   - CLINs and pricing
   - FAR clauses
   - Requirements (shall/must statements)
   - Deliverables
   - Evaluation factors
3. Examples show valid relationship patterns per ontology:
   - Section L ↔ Section M
   - CLIN → Requirements
   - Section M → Evaluation Factors
   - Deliverables → Contracting Officer

Original generic examples (Alex/Taylor/Jordan, stock market, sports) removed
to prevent contamination and train LLM on domain-specific patterns.

For additional ontology integration, see:
- src/lightrag_govcon/govcon_lightrag.py (wrapper class)
- src/lightrag_govcon/govcon/ontology_integration.py (OntologyInjector)
"""

PROMPTS: dict[str, Any] = {}

# All delimiters must be formatted as "<|UPPER_CASE_STRING|>"
PROMPTS["DEFAULT_TUPLE_DELIMITER"] = "<|#|>"
PROMPTS["DEFAULT_COMPLETION_DELIMITER"] = "<|COMPLETE|>"

PROMPTS["entity_extraction_system_prompt"] = """---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.

---Instructions---
1.  **Entity Extraction & Output:**
    *   **Identification:** Identify clearly defined and meaningful entities in the input text.
    *   **Entity Details:** For each identified entity, extract the following information:
        *   `entity_name`: The name of the entity. If the entity name is case-insensitive, capitalize the first letter of each significant word (title case). Ensure **consistent naming** across the entire extraction process.
        *   `entity_type`: Categorize the entity using one of the following types: `{entity_types}`. If none of the provided entity types apply, do not add new entity type and classify it as `Other`.
        *   `entity_description`: Provide a concise yet comprehensive description of the entity's attributes and activities, based *solely* on the information present in the input text.
    *   **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
        *   Format: `entity{tuple_delimiter}entity_name{tuple_delimiter}entity_type{tuple_delimiter}entity_description`

2.  **Relationship Extraction & Output:**
    *   **Identification:** Identify direct, clearly stated, and meaningful relationships between previously extracted entities.
    *   **N-ary Relationship Decomposition:** If a single statement describes a relationship involving more than two entities (an N-ary relationship), decompose it into multiple binary (two-entity) relationship pairs for separate description.
        *   **Example:** For "Alice, Bob, and Carol collaborated on Project X," extract binary relationships such as "Alice collaborated with Project X," "Bob collaborated with Project X," and "Carol collaborated with Project X," or "Alice collaborated with Bob," based on the most reasonable binary interpretations.
    *   **Relationship Details:** For each binary relationship, extract the following fields:
        *   `source_entity`: The name of the source entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
        *   `target_entity`: The name of the target entity. Ensure **consistent naming** with entity extraction. Capitalize the first letter of each significant word (title case) if the name is case-insensitive.
        *   `relationship_keywords`: One or more high-level keywords summarizing the overarching nature, concepts, or themes of the relationship. Multiple keywords within this field must be separated by a comma `,`. **DO NOT use `{tuple_delimiter}` for separating multiple keywords within this field.**
        *   `relationship_description`: A concise explanation of the nature of the relationship between the source and target entities, providing a clear rationale for their connection.
    *   **Output Format - Relationships:** Output a total of 5 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
        *   Format: `relation{tuple_delimiter}source_entity{tuple_delimiter}target_entity{tuple_delimiter}relationship_keywords{tuple_delimiter}relationship_description`

3.  **Delimiter Usage Protocol:**
    *   The `{tuple_delimiter}` is a complete, atomic marker and **must not be filled with content**. It serves strictly as a field separator.
    *   **Incorrect Example:** `entity{tuple_delimiter}Tokyo<|location|>Tokyo is the capital of Japan.`
    *   **Correct Example:** `entity{tuple_delimiter}Tokyo{tuple_delimiter}location{tuple_delimiter}Tokyo is the capital of Japan.`

4.  **Relationship Direction & Duplication:**
    *   Treat all relationships as **undirected** unless explicitly stated otherwise. Swapping the source and target entities for an undirected relationship does not constitute a new relationship.
    *   Avoid outputting duplicate relationships.

5.  **Output Order & Prioritization:**
    *   Output all extracted entities first, followed by all extracted relationships.
    *   Within the list of relationships, prioritize and output those relationships that are **most significant** to the core meaning of the input text first.

6.  **Context & Objectivity:**
    *   Ensure all entity names and descriptions are written in the **third person**.
    *   Explicitly name the subject or object; **avoid using pronouns** such as `this article`, `this paper`, `our company`, `I`, `you`, and `he/she`.

7.  **Language & Proper Nouns:**
    *   The entire output (entity names, keywords, and descriptions) must be written in `{language}`.
    *   Proper nouns (e.g., personal names, place names, organization names) should be retained in their original language if a proper, widely accepted translation is not available or would cause ambiguity.

8.  **Completion Signal:** Output the literal string `{completion_delimiter}` only after all entities and relationships, following all criteria, have been completely extracted and outputted.

---Examples---
{examples}

---Real Data to be Processed---
<Input>
Entity_types: [{entity_types}]
Text:
```
{input_text}
```
"""

PROMPTS["entity_extraction_user_prompt"] = """---Task---
Extract entities and relationships from the input text to be processed.

---Instructions---
1.  **Strict Adherence to Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system prompt.
2.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
3.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant entities and relationships have been extracted and presented.
4.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.

<Output>
"""

PROMPTS["entity_continue_extraction_user_prompt"] = """---Task---
Based on the last extraction task, identify and extract any **missed or incorrectly formatted** entities and relationships from the input text.

---Instructions---
1.  **Strict Adherence to System Format:** Strictly adhere to all format requirements for entity and relationship lists, including output order, field delimiters, and proper noun handling, as specified in the system instructions.
2.  **Focus on Corrections/Additions:**
    *   **Do NOT** re-output entities and relationships that were **correctly and fully** extracted in the last task.
    *   If an entity or relationship was **missed** in the last task, extract and output it now according to the system format.
    *   If an entity or relationship was **truncated, had missing fields, or was otherwise incorrectly formatted** in the last task, re-output the *corrected and complete* version in the specified format.
3.  **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
4.  **Output Format - Relationships:** Output a total of 5 fields for each relationship, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `relation`.
5.  **Output Content Only:** Output *only* the extracted list of entities and relationships. Do not include any introductory or concluding remarks, explanations, or additional text before or after the list.
6.  **Completion Signal:** Output `{completion_delimiter}` as the final line after all relevant missing or corrected entities and relationships have been extracted and presented.
7.  **Output Language:** Ensure the output language is {language}. Proper nouns (e.g., personal names, place names, organization names) must be kept in their original language and not translated.

<Output>
"""

# ============================================================================
# PHASE 3: GOVERNMENT CONTRACTING EXTRACTION EXAMPLES
# ============================================================================
# Replaced generic examples with government contracting domain-specific examples
# to train LLM on proper RFP entity/relationship extraction patterns

PROMPTS["entity_extraction_examples"] = [
    """<Input Text>
```
Section L.3.1 states that proposals shall not exceed 25 pages for the technical volume and must address all evaluation factors specified in Section M. The offeror shall provide a staffing plan demonstrating experience in base operations support services at naval installations.
```

<Output>
entity{tuple_delimiter}Section L.3.1{tuple_delimiter}section{tuple_delimiter}Section L.3.1 is a subsection of Instructions to Offerors that specifies proposal page limits and content requirements.
entity{tuple_delimiter}Technical Volume{tuple_delimiter}deliverable{tuple_delimiter}The Technical Volume is a required proposal deliverable with a 25-page limit.
entity{tuple_delimiter}25-Page Limit{tuple_delimiter}requirement{tuple_delimiter}The 25-page limit is a mandatory constraint on the technical volume submission.
entity{tuple_delimiter}Section M{tuple_delimiter}section{tuple_delimiter}Section M contains the evaluation factors that must be addressed in proposals.
entity{tuple_delimiter}Staffing Plan{tuple_delimiter}deliverable{tuple_delimiter}The Staffing Plan is a required deliverable demonstrating contractor experience and qualifications.
entity{tuple_delimiter}Base Operations Support Services{tuple_delimiter}concept{tuple_delimiter}Base Operations Support Services refers to the type of work required under the contract at naval installations.
entity{tuple_delimiter}Naval Installations{tuple_delimiter}location{tuple_delimiter}Naval Installations are the performance locations where contract work will be executed.
relation{tuple_delimiter}Section L.3.1{tuple_delimiter}Technical Volume{tuple_delimiter}specifies, constrains{tuple_delimiter}Section L.3.1 specifies requirements for the Technical Volume submission.
relation{tuple_delimiter}Technical Volume{tuple_delimiter}25-Page Limit{tuple_delimiter}constrained by, subject to{tuple_delimiter}The Technical Volume must adhere to the 25-page limit requirement.
relation{tuple_delimiter}Section L.3.1{tuple_delimiter}Section M{tuple_delimiter}references, depends on{tuple_delimiter}Section L.3.1 requires proposals to address evaluation factors specified in Section M.
relation{tuple_delimiter}Staffing Plan{tuple_delimiter}Base Operations Support Services{tuple_delimiter}demonstrates, relates to{tuple_delimiter}The Staffing Plan must demonstrate experience in Base Operations Support Services.
relation{tuple_delimiter}Base Operations Support Services{tuple_delimiter}Naval Installations{tuple_delimiter}performed at, located at{tuple_delimiter}Base Operations Support Services will be performed at Naval Installations.
{completion_delimiter}

""",
    """<Input Text>
```
CLIN 0001 covers base year recurring services at a firm-fixed price of $5,500,000. The contractor shall provide facility maintenance, grounds keeping, and custodial services in accordance with FAR 52.237-2 and the Performance Work Statement in Section C. Deliverables include monthly status reports submitted to the Contracting Officer no later than the 5th business day of each month.
```

<Output>
entity{tuple_delimiter}CLIN 0001{tuple_delimiter}concept{tuple_delimiter}CLIN 0001 is the Contract Line Item Number for base year recurring services with a fixed price.
entity{tuple_delimiter}Base Year Recurring Services{tuple_delimiter}concept{tuple_delimiter}Base Year Recurring Services is the scope of work for the initial contract period.
entity{tuple_delimiter}$5,500,000{tuple_delimiter}concept{tuple_delimiter}$5,500,000 is the firm-fixed price for CLIN 0001 services.
entity{tuple_delimiter}Facility Maintenance{tuple_delimiter}requirement{tuple_delimiter}Facility Maintenance is a required service under the contract.
entity{tuple_delimiter}Grounds Keeping{tuple_delimiter}requirement{tuple_delimiter}Grounds Keeping is a required service under the contract.
entity{tuple_delimiter}Custodial Services{tuple_delimiter}requirement{tuple_delimiter}Custodial Services are required services under the contract.
entity{tuple_delimiter}FAR 52.237-2{tuple_delimiter}clause{tuple_delimiter}FAR 52.237-2 is a Federal Acquisition Regulation clause governing protection of government buildings.
entity{tuple_delimiter}Section C{tuple_delimiter}section{tuple_delimiter}Section C contains the Performance Work Statement defining detailed requirements.
entity{tuple_delimiter}Monthly Status Reports{tuple_delimiter}deliverable{tuple_delimiter}Monthly Status Reports are required deliverables submitted to the Contracting Officer.
entity{tuple_delimiter}Contracting Officer{tuple_delimiter}person{tuple_delimiter}The Contracting Officer is the government official responsible for contract administration.
relation{tuple_delimiter}CLIN 0001{tuple_delimiter}Base Year Recurring Services{tuple_delimiter}covers, includes{tuple_delimiter}CLIN 0001 covers the scope of Base Year Recurring Services.
relation{tuple_delimiter}CLIN 0001{tuple_delimiter}Facility Maintenance{tuple_delimiter}requires, includes{tuple_delimiter}CLIN 0001 requires Facility Maintenance services to be provided.
relation{tuple_delimiter}CLIN 0001{tuple_delimiter}FAR 52.237-2{tuple_delimiter}governed by, subject to{tuple_delimiter}CLIN 0001 services must comply with FAR 52.237-2 requirements.
relation{tuple_delimiter}CLIN 0001{tuple_delimiter}Section C{tuple_delimiter}defined by, references{tuple_delimiter}CLIN 0001 services are detailed in the Performance Work Statement in Section C.
relation{tuple_delimiter}Monthly Status Reports{tuple_delimiter}Contracting Officer{tuple_delimiter}submitted to, received by{tuple_delimiter}Monthly Status Reports must be submitted to the Contracting Officer.
{completion_delimiter}

""",
    """<Input Text>
```
Section M.2 states that Factor 3 - Technical Approach will be evaluated as significantly more important than price. The Government will assess the offeror's understanding of Section C requirements and the proposed methodology for base operations support. Past performance on similar contracts at Department of Defense installations will be considered under Factor 2.
```

<Output>
entity{tuple_delimiter}Section M.2{tuple_delimiter}section{tuple_delimiter}Section M.2 is a subsection of Evaluation Factors for Award defining evaluation criteria and weights.
entity{tuple_delimiter}Factor 3 - Technical Approach{tuple_delimiter}concept{tuple_delimiter}Factor 3 - Technical Approach is an evaluation criterion focused on the contractor's proposed methodology.
entity{tuple_delimiter}Price{tuple_delimiter}concept{tuple_delimiter}Price is an evaluation factor with less importance than Technical Approach.
entity{tuple_delimiter}Section C{tuple_delimiter}section{tuple_delimiter}Section C contains the Statement of Work requirements that must be understood and addressed.
entity{tuple_delimiter}Base Operations Support{tuple_delimiter}concept{tuple_delimiter}Base Operations Support is the core service requirement that will be evaluated.
entity{tuple_delimiter}Past Performance{tuple_delimiter}concept{tuple_delimiter}Past Performance is an evaluation factor assessing contractor track record.
entity{tuple_delimiter}Factor 2{tuple_delimiter}concept{tuple_delimiter}Factor 2 is an evaluation criterion related to past performance assessment.
entity{tuple_delimiter}Department of Defense Installations{tuple_delimiter}location{tuple_delimiter}Department of Defense Installations are relevant locations for assessing past performance.
relation{tuple_delimiter}Section M.2{tuple_delimiter}Factor 3 - Technical Approach{tuple_delimiter}defines, evaluates{tuple_delimiter}Section M.2 defines Factor 3 - Technical Approach as an evaluation criterion.
relation{tuple_delimiter}Factor 3 - Technical Approach{tuple_delimiter}Price{tuple_delimiter}more important than, weighted higher{tuple_delimiter}Factor 3 - Technical Approach is significantly more important than Price in evaluation.
relation{tuple_delimiter}Factor 3 - Technical Approach{tuple_delimiter}Section C{tuple_delimiter}evaluates understanding of, references{tuple_delimiter}Factor 3 evaluates the offeror's understanding of Section C requirements.
relation{tuple_delimiter}Factor 3 - Technical Approach{tuple_delimiter}Base Operations Support{tuple_delimiter}evaluates methodology for, assesses{tuple_delimiter}Factor 3 evaluates the proposed methodology for Base Operations Support.
relation{tuple_delimiter}Factor 2{tuple_delimiter}Past Performance{tuple_delimiter}includes, assesses{tuple_delimiter}Factor 2 includes assessment of Past Performance on similar contracts.
relation{tuple_delimiter}Past Performance{tuple_delimiter}Department of Defense Installations{tuple_delimiter}evaluated at, performed at{tuple_delimiter}Past Performance at Department of Defense Installations will be considered in evaluation.
{completion_delimiter}

""",
]

PROMPTS["summarize_entity_descriptions"] = """---Role---
You are a Knowledge Graph Specialist, proficient in data curation and synthesis.

---Task---
Your task is to synthesize a list of descriptions of a given entity or relation into a single, comprehensive, and cohesive summary.

---Instructions---
1. Input Format: The description list is provided in JSON format. Each JSON object (representing a single description) appears on a new line within the `Description List` section.
2. Output Format: The merged description will be returned as plain text, presented in multiple paragraphs, without any additional formatting or extraneous comments before or after the summary.
3. Comprehensiveness: The summary must integrate all key information from *every* provided description. Do not omit any important facts or details.
4. Context: Ensure the summary is written from an objective, third-person perspective; explicitly mention the name of the entity or relation for full clarity and context.
5. Context & Objectivity:
  - Write the summary from an objective, third-person perspective.
  - Explicitly mention the full name of the entity or relation at the beginning of the summary to ensure immediate clarity and context.
6. Conflict Handling:
  - In cases of conflicting or inconsistent descriptions, first determine if these conflicts arise from multiple, distinct entities or relationships that share the same name.
  - If distinct entities/relations are identified, summarize each one *separately* within the overall output.
  - If conflicts within a single entity/relation (e.g., historical discrepancies) exist, attempt to reconcile them or present both viewpoints with noted uncertainty.
7. Length Constraint:The summary's total length must not exceed {summary_length} tokens, while still maintaining depth and completeness.
8. Language: The entire output must be written in {language}. Proper nouns (e.g., personal names, place names, organization names) may in their original language if proper translation is not available.
  - The entire output must be written in {language}.
  - Proper nouns (e.g., personal names, place names, organization names) should be retained in their original language if a proper, widely accepted translation is not available or would cause ambiguity.

---Input---
{description_type} Name: {description_name}

Description List:

```
{description_list}
```

---Output---
"""

PROMPTS["fail_response"] = (
    "Sorry, I'm not able to provide an answer to that question.[no-context]"
)

PROMPTS["rag_response"] = """---Role---

You are an expert AI assistant specializing in synthesizing information from a provided knowledge base. Your primary function is to answer user queries accurately by ONLY using the information within the provided `Source Data`.

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Knowledge Graph and Document Chunks found in the `Source Data`.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

**1. Step-by-Step Instruction:**
  - Carefully determine the user's query intent in the context of the conversation history to fully understand the user's information need.
  - Scrutinize the `Source Data`(both Knowledge Graph and Document Chunks). Identify and extract all pieces of information that are directly relevant to answering the user query.
  - Weave the extracted facts into a coherent and logical response. Your own knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
  - Track the reference_id of each document chunk. Correlate reference_id with the `Reference Document List` from `Source Data` to generate the appropriate citations.
  - Generate a reference section at the end of the response. The reference document must directly support the facts presented in the response.
  - Do not generate anything after the reference section.

**2. Content & Grounding:**
  - Strictly adhere to the provided context from the `Source Data`; DO NOT invent, assume, or infer any information not explicitly stated.
  - If the answer cannot be found in the `Source Data`, state that you do not have enough information to answer. Do not attempt to guess.

**3. Formatting & Language:**
  - The response MUST be in the same language as the user query.
  - Use Markdown for clear formatting (e.g., headings, bold, lists).
  - The response should be presented in {response_type}.

**4. References Section Format:**
  - The References section should be under heading: `### References`
  - Reference list entries should adhere to the format: `* [n] Document Title`. Do not include a caret (`^`) after opening square bracket (`[`).
  - The Document Title in the citation must retain its original language.
  - Output each citation on an individual line
  - Provide maximum of 5 most relevant citations.
  - Do not generate footnotes section or any text after the references.

**5. Reference Section Example:**
```
### References
* [1] Document Title One
* [2] Document Title Two
* [3] Document Title Three
```

**6. Additional Instructions**: {user_prompt}


---Source Data---
{context_data}
"""

PROMPTS["naive_rag_response"] = """---Role---

You are an expert AI assistant specializing in synthesizing information from a provided knowledge base. Your primary function is to answer user queries accurately by ONLY using the information within the provided `Source Data`.

---Goal---

Generate a comprehensive, well-structured answer to the user query.
The answer must integrate relevant facts from the Document Chunks found in the `Source Data`.
Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

**1. Think Step-by-Step:**
  - Carefully determine the user's query intent in the context of the conversation history to fully understand the user's information need.
  - Scrutinize the `Source Data`(Document Chunks). Identify and extract all pieces of information that are directly relevant to answering the user query.
  - Weave the extracted facts into a coherent and logical response. Your own knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
  - Track the reference_id of each document chunk. Correlate reference_id with the `Reference Document List` from `Source Data` to generate the appropriate citations.
  - Generate a reference section at the end of the response. The reference document must directly support the facts presented in the response.
  - Do not generate anything after the reference section.

**2. Content & Grounding:**
  - Strictly adhere to the provided context from the `Source Data`; DO NOT invent, assume, or infer any information not explicitly stated.
  - If the answer cannot be found in the `Source Data`, state that you do not have enough information to answer. Do not attempt to guess.

**3. Formatting & Language:**
  - The response MUST be in the same language as the user query.
  - Use Markdown for clear formatting (e.g., headings, bold, lists).
  - The response should be presented in {response_type}.

**4. References Section Format:**
  - The References section should be under heading: `### References`
  - Reference list entries should adhere to the format: `* [n] Document Title`. Do not include a caret (`^`) after opening square bracket (`[`).
  - The Document Title in the citation must retain its original language.
  - Output each citation on an individual line
  - Provide maximum of 5 most relevant citations.
  - Do not generate footnotes section or any text after the references.

**5. Reference Section Example:**
```
### References
* [1] Document Title One
* [2] Document Title Two
* [3] Document Title Three
```

**6. Additional Instructions**: {user_prompt}


---Source Data---

Document Chunks:

{content_data}

"""

PROMPTS["kg_query_context"] = """
Entities Data From Knowledge Graph(KG):

```json
{entities_str}
```

Relationships Data From Knowledge Graph(KG):

```json
{relations_str}
```

Original Texts From Document Chunks(DC):

```json
{text_chunks_str}
```

Document Chunks (DC) Reference Document List: (Each entry begins with [reference_id])

{reference_list_str}

"""

PROMPTS["naive_query_context"] = """
Original Texts From Document Chunks(DC):

```json
{text_chunks_str}
```

Document Chunks (DC) Reference Document List: (Each entry begins with [reference_id])

{reference_list_str}

"""

PROMPTS["keywords_extraction"] = """---Role---
You are an expert keyword extractor, specializing in analyzing user queries for a Retrieval-Augmented Generation (RAG) system. Your purpose is to identify both high-level and low-level keywords in the user's query that will be used for effective document retrieval.

---Goal---
Given a user query, your task is to extract two distinct types of keywords:
1. **high_level_keywords**: for overarching concepts or themes, capturing user's core intent, the subject area, or the type of question being asked.
2. **low_level_keywords**: for specific entities or details, identifying the specific entities, proper nouns, technical jargon, product names, or concrete items.

---Instructions & Constraints---
1. **Output Format**: Your output MUST be a valid JSON object and nothing else. Do not include any explanatory text, markdown code fences (like ```json), or any other text before or after the JSON. It will be parsed directly by a JSON parser.
2. **Source of Truth**: All keywords must be explicitly derived from the user query, with both high-level and low-level keyword categories are required to contain content.
3. **Concise & Meaningful**: Keywords should be concise words or meaningful phrases. Prioritize multi-word phrases when they represent a single concept. For example, from "latest financial report of Apple Inc.", you should extract "latest financial report" and "Apple Inc." rather than "latest", "financial", "report", and "Apple".
4. **Handle Edge Cases**: For queries that are too simple, vague, or nonsensical (e.g., "hello", "ok", "asdfghjkl"), you must return a JSON object with empty lists for both keyword types.

---Examples---
{examples}

---Real Data---
User Query: {query}

---Output---
Output:"""

PROMPTS["keywords_extraction_examples"] = [
    """Example 1:

Query: "How does international trade influence global economic stability?"

Output:
{
  "high_level_keywords": ["International trade", "Global economic stability", "Economic impact"],
  "low_level_keywords": ["Trade agreements", "Tariffs", "Currency exchange", "Imports", "Exports"]
}

""",
    """Example 2:

Query: "What are the environmental consequences of deforestation on biodiversity?"

Output:
{
  "high_level_keywords": ["Environmental consequences", "Deforestation", "Biodiversity loss"],
  "low_level_keywords": ["Species extinction", "Habitat destruction", "Carbon emissions", "Rainforest", "Ecosystem"]
}

""",
    """Example 3:

Query: "What is the role of education in reducing poverty?"

Output:
{
  "high_level_keywords": ["Education", "Poverty reduction", "Socioeconomic development"],
  "low_level_keywords": ["School access", "Literacy rates", "Job training", "Income inequality"]
}

""",
]
