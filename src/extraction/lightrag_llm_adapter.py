"""
LightRAG LLM Adapter - Bridges Pydantic validation with LightRAG's text extraction.

This adapter intercepts entity extraction LLM calls and:
1. Detects extraction requests (vs queries, summaries, etc.)
2. Uses JsonExtractor with Pydantic validation (Instructor + ExtractionResult)
3. Converts validated JSON → pipe-delimited format for LightRAG
4. Returns clean, validated data that LightRAG's parser accepts

NO FALLBACK TO NATIVE: If Pydantic validation fails after retries, the chunk is
skipped. LightRAG's native extraction would produce entities with invalid types
or malformed output that gets silently dropped anyway. Better to skip cleanly
than pollute the knowledge graph with partial/invalid data.

The pipe-delimiter is just a transport format - all actual validation happens via Pydantic.

Issue #56: Post-Processing Overhaul - 100% entity capture
"""

import logging
import re
from typing import Optional, Union, AsyncIterator

from src.extraction.json_extractor import JsonExtractor
from src.ontology.schema import ExtractionResult

logger = logging.getLogger(__name__)

# LightRAG's expected delimiters (from lightrag/prompt.py)
TUPLE_DELIMITER = "<|#|>"
COMPLETION_DELIMITER = "<|COMPLETE|>"


class LightRAGExtractionAdapter:
    """
    Adapter that wraps LLM calls for entity extraction.
    
    When LightRAG calls the llm_model_func for entity extraction, this adapter:
    1. Detects extraction requests (vs queries, summaries, etc.)
    2. Uses JsonExtractor with Pydantic validation
    3. Converts validated JSON → pipe-delimited format
    4. Returns to LightRAG's native parser
    
    Non-extraction calls (queries, summaries, keywords) pass through unchanged.
    """
    
    def __init__(self, base_llm_func, json_extractor: Optional[JsonExtractor] = None):
        """
        Args:
            base_llm_func: The original LLM function for non-extraction calls
            json_extractor: Optional JsonExtractor instance (lazy-initialized if not provided)
        """
        self.base_llm_func = base_llm_func
        self._json_extractor = json_extractor
        
        # Statistics
        self._extraction_count = 0
        self._passthrough_count = 0
        self._pydantic_success = 0
        self._pydantic_failed = 0
    
    @property
    def json_extractor(self) -> JsonExtractor:
        """Lazy initialization of JsonExtractor."""
        if self._json_extractor is None:
            logger.info("🔧 Initializing JsonExtractor for Pydantic validation")
            self._json_extractor = JsonExtractor()
        return self._json_extractor
    
    async def __call__(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: list = None,
        keyword_extraction: bool = False,
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """
        Main entry point - intercepts LLM calls and routes appropriately.
        
        Entity extraction calls go through Pydantic validation.
        All other calls (queries, summaries, keywords) pass through to base LLM.
        """
        history_messages = history_messages or []
        
        # Detect if this is an entity extraction call
        if self._is_extraction_call(system_prompt, prompt):
            return await self._handle_extraction(prompt, system_prompt, **kwargs)
        
        # Pass through to base LLM for all other calls
        self._passthrough_count += 1
        return await self.base_llm_func(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            keyword_extraction=keyword_extraction,
            **kwargs
        )
    
    def _is_extraction_call(self, system_prompt: Optional[str], user_prompt: str) -> bool:
        """
        Detect entity extraction calls by checking for LightRAG's extraction markers.
        
        LightRAG's entity_extraction_system_prompt contains specific markers
        that we can use to identify extraction calls.
        """
        if not system_prompt:
            return False
        
        # Markers from LightRAG's entity_extraction_system_prompt + our GovCon prompt
        extraction_markers = [
            "Knowledge Graph Specialist",
            "extracting entities and relationships",
            "Entity_types:",
            TUPLE_DELIMITER,  # <|#|>
            "Government Contracting Domain Knowledge",  # Our domain prompt
            "PART A: ROLE AND CONTEXT",  # Our govcon_lightrag_native.txt
        ]
        
        # Must have at least 2 markers to be confident it's extraction
        marker_count = sum(1 for marker in extraction_markers if marker in system_prompt)
        return marker_count >= 2
    
    async def _handle_extraction(
        self,
        prompt: str,
        system_prompt: str,
        **kwargs
    ) -> str:
        """
        Handle entity extraction with Pydantic validation.
        
        Returns:
            Pipe-delimited string that LightRAG's parser expects
        """
        self._extraction_count += 1
        chunk_id = kwargs.get('chunk_id') or f"pydantic-chunk-{self._extraction_count}"
        
        try:
            # CRITICAL: LightRAG puts the text content in the SYSTEM prompt
            # The user prompt is just "---Task--- Extract entities..."
            # Actual chunk is in: system_prompt -> "Text:\n```\n{input_text}\n```"
            text_content = self._extract_text_content(system_prompt)
            
            if not text_content or len(text_content.strip()) < 50:
                logger.warning(f"[{chunk_id}] Text content too short or empty - skipping")
                self._pydantic_failed += 1
                return self._empty_result()
            
            # Use JsonExtractor for Pydantic-validated extraction
            logger.info(f"🎯 [{chunk_id}] Pydantic extraction ({len(text_content)} chars)")
            result: ExtractionResult = await self.json_extractor.extract(
                text_content,
                chunk_id=chunk_id
            )
            
            # Check if we got meaningful results
            if not result.entities:
                logger.warning(f"[{chunk_id}] Pydantic extraction returned 0 entities")
                self._pydantic_failed += 1
                return self._empty_result()
            
            # Convert validated result to pipe-delimited format
            pipe_output = self._convert_to_pipe_format(result, chunk_id)
            
            self._pydantic_success += 1
            logger.info(
                f"✅ [{chunk_id}] Pydantic: {len(result.entities)} entities, "
                f"{len(result.relationships)} relationships"
            )
            
            return pipe_output
            
        except Exception as e:
            logger.error(f"❌ [{chunk_id}] Pydantic extraction FAILED ({type(e).__name__}): {str(e)[:200]}")
            self._pydantic_failed += 1
            return self._empty_result()
    
    def _empty_result(self) -> str:
        """Return empty result in LightRAG's expected format."""
        return COMPLETION_DELIMITER
    
    def _extract_text_content(self, system_prompt: str) -> Optional[str]:
        """
        Extract the actual text content from LightRAG's SYSTEM prompt.
        
        CRITICAL: LightRAG embeds the chunk text in the system prompt, NOT the user prompt!
        
        System prompt format:
        ---Real Data to be Processed---
        <Input>
        Entity_types: [...]
        Text:
        ```
        <actual content here>
        ```
        """
        # Pattern 1: Text:\n```\ncontent\n```
        match = re.search(r'Text:\s*\n```\s*\n(.*?)\n```', system_prompt, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: Text:\n<content> (no backticks)
        match = re.search(r'Text:\s*\n(.+?)(?:\n---|\Z)', system_prompt, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if content.endswith('```'):
                content = content[:-3].strip()
            return content
        
        # Pattern 3: Look for content after last ```
        parts = system_prompt.split('```')
        if len(parts) >= 2:
            for i in range(len(parts) - 1, 0, -1):
                content = parts[i].strip()
                if content and len(content) > 100:
                    return content
        
        # Fallback: Everything after "Text:"
        if "Text:" in system_prompt:
            return system_prompt.split("Text:", 1)[1].strip()
        
        return None
    
    def _convert_to_pipe_format(self, result: ExtractionResult, chunk_id: str) -> str:
        """
        Convert Pydantic ExtractionResult to LightRAG's pipe-delimited format.
        
        Entity format: entity<|#|>name<|#|>type<|#|>description
        Relation format: relation<|#|>source<|#|>target<|#|>keywords<|#|>description
        """
        lines = []
        
        # Convert entities
        for entity in result.entities:
            # Use entity's description field
            description = entity.description if hasattr(entity, 'description') and entity.description else ""
            
            # Add specialized metadata for rich entity types
            metadata = self._build_entity_metadata(entity)
            if metadata:
                description = f"{metadata} {description}"
            
            # Escape pipe characters and clean
            name = self._escape_pipes(entity.entity_name)
            entity_type = self._escape_pipes(entity.entity_type)
            description = self._escape_pipes(description)
            
            # Truncate if too long (prevent oversized outputs)
            if len(description) > 2000:
                description = description[:2000] + "..."
            
            line = f"entity{TUPLE_DELIMITER}{name}{TUPLE_DELIMITER}{entity_type}{TUPLE_DELIMITER}{description}"
            lines.append(line)
        
        # Convert relationships
        for rel in result.relationships:
            source_name = rel.source_entity.entity_name if rel.source_entity else "UNKNOWN"
            target_name = rel.target_entity.entity_name if rel.target_entity else "UNKNOWN"
            
            source_name = self._escape_pipes(source_name)
            target_name = self._escape_pipes(target_name)
            rel_type = self._escape_pipes(rel.relationship_type)
            rel_desc = self._escape_pipes(rel.description) if rel.description else ""
            
            # LightRAG format: relation<|#|>source<|#|>target<|#|>keywords<|#|>description
            line = f"relation{TUPLE_DELIMITER}{source_name}{TUPLE_DELIMITER}{target_name}{TUPLE_DELIMITER}{rel_type}{TUPLE_DELIMITER}{rel_desc}"
            lines.append(line)
        
        # Add completion delimiter
        lines.append(COMPLETION_DELIMITER)
        
        return "\n".join(lines)
    
    def _build_entity_metadata(self, entity) -> str:
        """Build metadata string from specialized entity attributes."""
        parts = []
        
        # Requirement metadata
        if hasattr(entity, 'criticality') and entity.criticality:
            parts.append(f"[Criticality: {entity.criticality}]")
        if hasattr(entity, 'modal_verb') and entity.modal_verb:
            parts.append(f"[Modal: {entity.modal_verb}]")
        if hasattr(entity, 'labor_drivers') and entity.labor_drivers:
            drivers = entity.labor_drivers[:3]  # First 3
            parts.append(f"[Workload: {', '.join(drivers)}]")
        
        # EvaluationFactor metadata
        if hasattr(entity, 'weight') and entity.weight:
            parts.append(f"[Weight: {entity.weight}]")
        if hasattr(entity, 'importance') and entity.importance:
            parts.append(f"[Importance: {entity.importance}]")
        
        # Clause metadata
        if hasattr(entity, 'clause_number') and entity.clause_number:
            parts.append(f"[{entity.clause_number}]")
        
        # PerformanceMetric metadata
        if hasattr(entity, 'threshold') and entity.threshold:
            parts.append(f"[Threshold: {entity.threshold}]")
        
        # SubmissionInstruction metadata
        if hasattr(entity, 'page_limit') and entity.page_limit:
            parts.append(f"[Page Limit: {entity.page_limit}]")
        
        return " ".join(parts)
    
    def _escape_pipes(self, text: str) -> str:
        """Escape pipe characters and clean text for pipe-delimited format."""
        if not text:
            return ""
        # Replace pipes with spaces to avoid parsing issues
        text = str(text).replace("|", " ").replace("<|", " ").replace("|>", " ")
        text = text.replace(TUPLE_DELIMITER, " ")
        return text.strip()
    
    def get_stats(self) -> dict:
        """Get adapter statistics."""
        total = self._pydantic_success + self._pydantic_failed
        success_rate = (self._pydantic_success / total * 100) if total > 0 else 0
        
        stats = {
            "extraction_calls": self._extraction_count,
            "passthrough_calls": self._passthrough_count,
            "pydantic_success": self._pydantic_success,
            "pydantic_failed": self._pydantic_failed,
            "pydantic_success_rate": f"{success_rate:.1f}%",
        }
        
        if self._json_extractor:
            stats["json_extractor_stats"] = self._json_extractor.get_extraction_stats()
        
        return stats


def create_extraction_adapter(base_llm_func) -> LightRAGExtractionAdapter:
    """
    Factory function to create an extraction adapter.
    
    Usage in initialization.py:
        from src.extraction.lightrag_llm_adapter import create_extraction_adapter
        
        base_llm_func = create_base_llm_func()
        llm_model_func = create_extraction_adapter(base_llm_func)
    """
    logger.info("🔌 Creating LightRAG extraction adapter with Pydantic validation")
    return LightRAGExtractionAdapter(base_llm_func)

