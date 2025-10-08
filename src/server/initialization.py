"""
RAG-Anything Initialization Module

This module handles the initialization of the RAG-Anything instance with:
- Custom entity extraction prompts (fixes "#/>CONCEPT" format issues)
- Government contracting entity types (12 Phase 6 enhanced types)
- Multimodal document processing (MinerU parser)
- Cloud LLM integration (xAI Grok + OpenAI embeddings)
"""

import os
import logging
from lightrag.api.config import global_args
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig
from lightrag.operate import chunking_by_token_size

logger = logging.getLogger(__name__)

# Global RAG-Anything instance
_rag_anything = None


async def initialize_raganything():
    """Initialize RAG-Anything instance for multimodal document processing
    
    Configuration:
    - Parser: MinerU (multimodal - images, tables, equations)
    - Entity Types: 12 government contracting types (semantic-first detection)
    - LLM: xAI Grok-4-fast-reasoning (cloud processing, 2M context)
    - Embeddings: OpenAI text-embedding-3-large (3072-dim, 8192 max tokens)
    - Chunking: 2048 tokens, 256 overlap (87% fewer embedding calls vs 800)
    
    Returns:
        RAGAnything: Configured instance ready for document ingestion
    """
    global _rag_anything
    
    # Get API credentials (using RAG-Anything official variable names)
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = global_args.working_dir
    
    # Government contracting entity types (Phase 6 Enhanced)
    # Semantic-first detection: Content determines entity type, not section labels
    entity_types = [
        # Core entities
        "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", "PERSON", "LOCATION",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "REQUIREMENT",
        
        # Structural entities
        "CLAUSE",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "SECTION",                  # Stores both structural_label + semantic_type
        "DOCUMENT",
        "DELIVERABLE",
        "ANNEX",                    # NEW: Numbered attachments (J-######, Attachment #, Annex ##)
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        "EVALUATION_FACTOR",        # Scoring criteria (Section M content)
        "SUBMISSION_INSTRUCTION",   # NEW: Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (NEW: Capture planning patterns)
        "STRATEGIC_THEME",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (NEW: Semantic detection regardless of location)
        "STATEMENT_OF_WORK",        # PWS/SOW/SOO content (may be Section C or attachment)
    ]
    
    # Create RAG-Anything configuration
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser="mineru",  # Multimodal parser
        parse_method="auto",
        enable_image_processing=True,
        enable_table_processing=True,
        enable_equation_processing=True,
    )
    
    # Define LLM function (xAI Grok wrapper)
    def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return openai_complete_if_cache(
            "grok-4-fast-reasoning",
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )
    
    # Define vision function (multimodal Grok wrapper)
    def vision_model_func(prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs):
        if messages:
            return openai_complete_if_cache(
                "grok-4-fast-reasoning", "", system_prompt=None, history_messages=[],
                messages=messages, api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        elif image_data:
            return openai_complete_if_cache(
                "grok-4-fast-reasoning", "", system_prompt=None, history_messages=[],
                messages=[
                    {"role": "system", "content": system_prompt} if system_prompt else None,
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                        ],
                    } if image_data else {"role": "user", "content": prompt},
                ],
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            return llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Define embedding function (OpenAI wrapper)
    embedding_func = EmbeddingFunc(
        embedding_dim=3072,
        max_token_size=8192,
        func=lambda texts: openai_embed(texts, model="text-embedding-3-large", api_key=openai_api_key),
    )
    
    # Custom extraction prompt to fix entity type format issues
    # Problem: LightRAG sometimes outputs "#/>CONCEPT" instead of "CONCEPT"
    # Solution: Explicit format rules with correct/wrong examples
    custom_entity_extraction_prompt = """---Role---
You are a Knowledge Graph Specialist responsible for extracting entities and relationships from the input text.  

---Instructions---
1.  **Entity Extraction & Output:**
    *   **Identification:** Identify clearly defined and meaningful entities in the input text.
    *   **Entity Details:** For each identified entity, extract the following information:
        *   `entity_name`: The name of the entity. If the entity name is case-insensitive, capitalize the first letter of each significant word (title case). Ensure **consistent naming** across the entire extraction process.
        *   `entity_type`: Categorize the entity using one of the following types: `{entity_types}`. 
            
            ═══════════════════════════════════════════════════════════════════════════════
            ⚠️  CRITICAL - Entity Type Format Rules (READ CAREFULLY):
            ═══════════════════════════════════════════════════════════════════════════════
            
            ✅ CORRECT FORMAT:
               Output ONLY the plain entity type name exactly as shown in {entity_types}
               Example: ANNEX
               Example: CLAUSE
               Example: REQUIREMENT
               Example: DOCUMENT
               Example: CONCEPT
               Example: SECTION
            
            ❌ WRONG FORMATS (DO NOT USE ANY OF THESE):
               ❌ "#/>CONCEPT"      → NEVER add hash (#) or angle brackets (< >)
               ❌ "#>|DOCUMENT"     → NEVER add hash (#), angle bracket (>), or pipe (|)
               ❌ "#|CLAUSE"        → NEVER add hash (#) or pipe (|) before type
               ❌ "<|CONCEPT|>"     → NEVER add angle brackets or pipes around type
               ❌ "CLAUSE#|"        → NEVER add special characters AFTER the type
               ❌ " ANNEX "         → NEVER add spaces before or after the type
               ❌ "concept"         → ALWAYS use UPPERCASE as specified in {entity_types}
            
            ═══════════════════════════════════════════════════════════════════════════════
            ✅ CORRECT EXAMPLE (FULL LINE):
            entity{tuple_delimiter}Annex 17 Transportation{tuple_delimiter}ANNEX{tuple_delimiter}Annex 17 Transportation addresses performance methodology for transportation.
            
            ❌ WRONG EXAMPLE (FULL LINE):
            entity{tuple_delimiter}Veteran-Owned Small Business{tuple_delimiter}#/>CONCEPT{tuple_delimiter}A business owned by veterans.
            
            ✅ CORRECTED VERSION:
            entity{tuple_delimiter}Veteran-Owned Small Business{tuple_delimiter}CONCEPT{tuple_delimiter}A business owned by veterans.
            ═══════════════════════════════════════════════════════════════════════════════
            
            If none of the provided entity types apply, classify it as `OTHER`.
        *   `entity_description`: Provide a concise yet comprehensive description of the entity's attributes and activities, based *solely* on the information present in the input text.
    *   **Output Format - Entities:** Output a total of 4 fields for each entity, delimited by `{tuple_delimiter}`, on a single line. The first field *must* be the literal string `entity`.
    
    ═══════════════════════════════════════════════════════════════════════════════
    📋 ENTITY OUTPUT FORMAT (EXACT TEMPLATE):
    ═══════════════════════════════════════════════════════════════════════════════
    
    entity{tuple_delimiter}[ENTITY_NAME]{tuple_delimiter}[ENTITY_TYPE]{tuple_delimiter}[DESCRIPTION]
    
    Where:
    - [ENTITY_NAME] = Name with consistent capitalization
    - [ENTITY_TYPE] = PLAIN UPPERCASE TYPE from {entity_types} (NO special characters!)
    - [DESCRIPTION] = Concise description from input text
    
    ✅ CORRECT EXAMPLES:
    entity{tuple_delimiter}Annex 17 Transportation{tuple_delimiter}ANNEX{tuple_delimiter}Annex 17 Transportation addresses performance methodology for transportation.
    entity{tuple_delimiter}Veteran-Owned Small Business{tuple_delimiter}CONCEPT{tuple_delimiter}A business owned by veterans.
    entity{tuple_delimiter}FAR 52.212-1{tuple_delimiter}CLAUSE{tuple_delimiter}Instructions to Offerors—Commercial Products and Commercial Services.
    
    ❌ WRONG EXAMPLES (LEARN FROM THESE MISTAKES):
    entity{tuple_delimiter}Veteran-Owned Small Business{tuple_delimiter}#/>CONCEPT{tuple_delimiter}A business owned by veterans.
    entity{tuple_delimiter}FAR 52.212-1{tuple_delimiter}#>|CLAUSE{tuple_delimiter}Instructions to Offerors.
    entity{tuple_delimiter}Section J{tuple_delimiter}#|SECTION{tuple_delimiter}List of attachments.
    
    ═══════════════════════════════════════════════════════════════════════════════

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
    
    ═══════════════════════════════════════════════════════════════════════════════
    🔧 DELIMITER RULES:
    ═══════════════════════════════════════════════════════════════════════════════
    
    ✅ CORRECT: Use {tuple_delimiter} EXACTLY as shown, with NO modifications
    ❌ WRONG: Do NOT add content inside the delimiter
    ❌ WRONG: Do NOT modify the delimiter characters
    ❌ WRONG: Do NOT use alternative delimiters
    
    Examples:
    ❌ WRONG: entity{tuple_delimiter}Tokyo<|location|>Tokyo is the capital of Japan.
    ✅ CORRECT: entity{tuple_delimiter}Tokyo{tuple_delimiter}LOCATION{tuple_delimiter}Tokyo is the capital of Japan.
    
    ═══════════════════════════════════════════════════════════════════════════════

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

    # Initialize RAG-Anything with custom configuration
    _rag_anything = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
        lightrag_kwargs={
            "addon_params": {
                "entity_types": entity_types,
                "entity_extraction_system_prompt": custom_entity_extraction_prompt,
            },
            "chunking_func": chunking_by_token_size,
            "chunk_token_size": int(os.getenv("CHUNK_SIZE", "2048")),
            "chunk_overlap_token_size": int(os.getenv("CHUNK_OVERLAP_SIZE", "256")),
        },
    )
    
    logger.info("✅ RAG-Anything initialized")
    logger.info(f"   Working dir: {working_dir}")
    logger.info(f"   Parser: MinerU (multimodal)")
    logger.info(f"   Entity types: {len(entity_types)} govcon types (Phase 6 enhanced)")
    logger.info(f"   Custom extraction prompt: Enabled (clean entity type format)")
    
    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
