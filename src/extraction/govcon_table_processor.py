"""
Government Contracting Table Processor
Applies custom ontology to table content using the same Pydantic schema as text processing.

CRITICAL: Uses the SAME prompt infrastructure as JsonExtractor for consistency:
- Stage 1 (table→text): table_description_prompt.md (table-specific)
- Stage 2 (text→entities): JsonExtractor prompts (grok_json_prompt.md, entity_extraction_prompt.md, etc.)

This ensures entity extraction from tables matches text extraction exactly.
"""

import logging
import os
from typing import Dict, Any, Tuple, List, Optional
from src.ontology.schema import ExtractionResult
from src.utils.logging_config import log_graceful_failure

logger = logging.getLogger(__name__)


class GovconTableProcessor:
    """
    Government contracting table processor with ontology awareness.
    
    Follows RAG-Anything's modal processor pattern but applies domain-specific
    entity extraction using the custom Pydantic schema.
    
    Stage 1 uses table_description_prompt.md (the ONLY table-specific prompt).
    Stage 2 reuses ALL JsonExtractor prompts for consistency.
    """
    
    def __init__(self, json_extractor, llm_func):
        """
        Initialize table processor.
        
        Args:
            json_extractor: JsonExtractor instance (reuses ALL text extraction prompts)
            llm_func: Async LLM function for table-to-text conversion
        """
        self.json_extractor = json_extractor
        self.llm_func = llm_func
        # Build Stage 1 system prompt using FULL ontology + table conversion instructions
        self.table_description_prompt = self._build_table_description_system_prompt()
    
    def _build_table_description_system_prompt(self) -> str:
        """
        Build system prompt for Stage 1 (table→text conversion).
        
        CRITICAL: This should include the ontology context so Stage 1 knows
        what information to preserve (requirements, metrics, etc.)
        
        Returns the JsonExtractor's system prompt + table-specific conversion instructions.
        """
        # Use the FULL ontology system prompt from JsonExtractor
        # This includes entity detection rules, examples, relationship inference
        base_ontology = self.json_extractor.system_prompt
        
        # Add table-specific conversion instructions
        table_instructions = """

# TABLE-TO-TEXT CONVERSION INSTRUCTIONS

You are receiving a TABLE from a government contracting RFP. Your task is to convert
this table into a structured text narrative that preserves all information.

**CRITICAL**: You already have the full government contracting ontology above.
Use that knowledge to understand what information the table contains.

**Task**: Convert table rows into natural language prose that:
1. Makes entity types explicit (e.g., "Requirement X states that...")
2. Preserves all quantitative data (thresholds, weights, frequencies)
3. Maintains relationships between columns
4. Uses the surrounding context to classify table content correctly

**Output Format**: Plain text narrative ONLY (no JSON, no markdown tables).
The text will be fed back into the entity extraction system you already know.

**Example**:
Table with modal verbs → "The system shall implement X" (Requirement)
Table with thresholds → "Response time performance metric must be < 2 hours" (PerformanceMetric)
Table with weights → "Technical approach factor is worth 40 points" (EvaluationFactor)
"""
        
        return base_ontology + table_instructions
    
    def _extract_context_for_table(
        self, 
        item_info: Dict[str, Any], 
        content_list: List[Dict[str, Any]],
        context_window: int = 5
    ) -> str:
        """
        Extract surrounding text context for a table.
        
        Follows RAG-Anything's ContextExtractor pattern:
        - Get text blocks BEFORE table (for section headers, requirement statements)
        - Get text blocks AFTER table (for footnotes, clarifications)
        
        Args:
            item_info: Table metadata (page_idx, index)
            content_list: Full MinerU content list
            context_window: Number of blocks before/after to include
        
        Returns:
            Combined context string
        """
        page_idx = item_info.get("page_idx", 0)
        item_index = item_info.get("index", 0)
        
        before_text = []
        after_text = []
        
        # Collect context blocks
        for idx, item in enumerate(content_list):
            if item.get("type") != "text":
                continue  # Only use text blocks for context
            
            # Before context (same page or nearby pages)
            if idx < item_index and len(before_text) < context_window:
                if abs(item.get("page_idx", 0) - page_idx) <= 1:  # Within 1 page
                    before_text.append(item.get("text", "").strip())
            
            # After context (same page or nearby pages)
            elif idx > item_index and len(after_text) < context_window:
                if abs(item.get("page_idx", 0) - page_idx) <= 1:
                    after_text.append(item.get("text", "").strip())
        
        # Combine context
        context_parts = []
        if before_text:
            context_parts.append("CONTEXT BEFORE TABLE:\n" + "\n\n".join(before_text[-3:]))  # Last 3 blocks
        if after_text:
            context_parts.append("CONTEXT AFTER TABLE:\n" + "\n\n".join(after_text[:2]))  # First 2 blocks
        
        return "\n\n---\n\n".join(context_parts) if context_parts else ""
    
    async def generate_table_description(
        self, 
        modal_content: Dict[str, Any],
        item_info: Optional[Dict[str, Any]] = None,
        content_list: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Stage 1: Convert table to structured text description.
        
        Uses table_description_prompt.md (modular prompt) to transform table data into
        text that can be parsed by JsonExtractor.
        
        Args:
            modal_content: Table data (table_body, table_caption, etc.)
            item_info: Table metadata (page_idx, index)
            content_list: Full content list for context extraction
        
        Returns:
            Tuple of (description, basic_entity_info)
        """
        # Extract table structure
        table_body = modal_content.get("table_body", modal_content.get("text", ""))
        table_caption = modal_content.get("table_caption", [])
        table_footnote = modal_content.get("table_footnote", [])
        page_idx = modal_content.get("page_idx", item_info.get("page_idx", 0) if item_info else 0)
        
        # Get surrounding context (CRITICAL for entity classification)
        context = ""
        if item_info and content_list:
            context = self._extract_context_for_table(item_info, content_list)
        
        # Build user message with table data
        user_message = f"""TABLE FROM PAGE {page_idx}

{context}

TABLE CAPTION: {', '.join(table_caption) if table_caption else 'None'}

TABLE DATA:
{table_body}

TABLE FOOTNOTES: {', '.join(table_footnote) if table_footnote else 'None'}
"""
        
        try:
            # Call LLM to generate structured text description
            # Use modular prompt (loaded in __init__) as system prompt
            response = await self.llm_func(
                user_message,
                system_prompt=self.table_description_prompt,  # Use table_description_prompt.md
                temperature=0.1
            )
            
            description = response.choices[0].message.content if hasattr(response, 'choices') else str(response)
            
            logger.info(f"📊 Table description generated: {len(description)} chars from page {page_idx}")
            
            # Return basic entity info (not used in our pipeline, but follows interface)
            entity_info = {
                "entity_name": f"Table (Page {page_idx})",
                "entity_type": "document",
                "source_type": "table"
            }
            
            return description, entity_info
            
        except Exception as e:
            logger.error(f"❌ Table description generation failed: {e}")
            # Fallback: return raw table text
            fallback_desc = f"TABLE: {', '.join(table_caption)}\n\n{table_body}"
            return fallback_desc, {"entity_name": "Table", "entity_type": "document"}
    
    async def process_table(
        self,
        modal_content: Dict[str, Any],
        file_path: str,
        item_info: Optional[Dict[str, Any]] = None,
        content_list: Optional[List[Dict[str, Any]]] = None
    ) -> Tuple[ExtractionResult, str]:
        """
        Stage 2: Extract ontology entities from table description.
        
        Main entry point for table processing. Converts table to text,
        then applies JsonExtractor for entity extraction.
        
        Args:
            modal_content: Table data from MinerU
            file_path: Source file path
            item_info: Table metadata
            content_list: Full content list for context
        
        Returns:
            Tuple of (ExtractionResult, description)
        """
        # Stage 1: Generate structured text description
        description, entity_info = await self.generate_table_description(
            modal_content,
            item_info,
            content_list
        )
        
        # Stage 2: Extract entities using JsonExtractor (same as text processing!)
        page_idx = item_info.get("page_idx", 0) if item_info else 0
        table_idx = item_info.get("index", 0) if item_info else 0
        chunk_id = f"table-page{page_idx}-idx{table_idx}"
        
        try:
            extraction_result = await self.json_extractor.extract_from_text(
                text=description,
                chunk_id=chunk_id
            )
            
            # Tag all entities with table provenance in source_text for identification
            for entity in extraction_result.entities:
                entity.source_text = f"[TABLE-P{page_idx}] {entity.source_text or description[:100]}"
            
            logger.info(
                f"✅ Table processed: {len(extraction_result.entities)} entities, "
                f"{len(extraction_result.relationships)} relationships"
            )
            
            return extraction_result, description
            
        except Exception as e:
            log_graceful_failure(logger, "Table extraction", e, chunk_id)
            # Return empty result on failure (graceful degradation)
            return ExtractionResult(entities=[], relationships=[]), description
