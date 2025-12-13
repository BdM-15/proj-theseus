"""
LightRAG LLM Adapter - Bridges Pydantic validation with LightRAG's text extraction.

This adapter intercepts entity extraction LLM calls and:
1. Requests JSON structured output (using existing PydanticExtractor)
2. Validates with Pydantic (ExtractionResult schema)
3. Converts to pipe-delimited format for LightRAG's parser
4. Returns clean, validated data that LightRAG accepts

The pipe-delimiter is just a transport format - all actual validation happens via Pydantic.

Issue #43: Pydantic validation for text extraction
"""
import logging
import re
from typing import Optional, Union, AsyncIterator

from src.extraction.pydantic_extractor import PydanticExtractor
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
    2. Uses PydanticExtractor with Pydantic validation
    3. Converts validated JSON → pipe-delimited format
    4. Returns to LightRAG's native parser
    """
    
    def __init__(self, base_llm_func, pydantic_extractor: Optional[PydanticExtractor] = None):
        """
        Args:
            base_llm_func: The original LLM function for non-extraction calls
            pydantic_extractor: Optional PydanticExtractor instance (creates one if not provided)
        """
        self.base_llm_func = base_llm_func
        self._pydantic_extractor = pydantic_extractor  # Lazy init
        self._extraction_count = 0
        self._passthrough_count = 0
        self._pydantic_success = 0
        self._pydantic_fallback = 0
        
    @property
    def pydantic_extractor(self) -> PydanticExtractor:
        """Lazy initialization of PydanticExtractor."""
        if self._pydantic_extractor is None:
            logger.info("🔧 Initializing PydanticExtractor for Pydantic validation")
            self._pydantic_extractor = PydanticExtractor()
        return self._pydantic_extractor
    
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
        
        Entity extraction calls are detected by checking for extraction-specific
        markers in the system prompt.
        """
        history_messages = history_messages or []
        
        # Detect if this is an entity extraction call
        if self._is_extraction_call(system_prompt, prompt):
            return await self._handle_extraction(prompt, system_prompt, **kwargs)
        
        # Pass through to base LLM for all other calls (queries, summaries, etc.)
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
        
        # Markers from LightRAG's entity_extraction_system_prompt
        extraction_markers = [
            "Knowledge Graph Specialist",
            "extracting entities and relationships",
            "Entity_types:",
            TUPLE_DELIMITER,  # <|#|>
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
        chunk_id = kwargs.get('chunk_id', f"text-chunk-{self._extraction_count}")
        
        try:
            # CRITICAL: LightRAG puts the text content in the SYSTEM prompt, not the user prompt!
            # The user prompt is just "---Task--- Extract entities..." 
            # The actual chunk is in: system_prompt -> "Text:\n```\n{input_text}\n```"
            text_content = self._extract_text_content(system_prompt)
            
            if not text_content or len(text_content.strip()) < 50:
                logger.warning(f"[{chunk_id}] Text content too short or empty, using passthrough")
                return await self._fallback_to_base(prompt, system_prompt, chunk_id, **kwargs)
            
            # Use PydanticExtractor for Pydantic-validated extraction
            logger.info(f"🎯 [{chunk_id}] Using Pydantic extraction ({len(text_content)} chars)")
            result: ExtractionResult = await self.pydantic_extractor.extract(
                text_content, 
                chunk_id=chunk_id
            )
            
            # Check if we got meaningful results
            if not result.entities:
                logger.warning(f"[{chunk_id}] Pydantic extraction returned 0 entities, using passthrough")
                return await self._fallback_to_base(prompt, system_prompt, chunk_id, **kwargs)
            
            # Convert validated result to pipe-delimited format
            pipe_output = self._convert_to_pipe_format(result, chunk_id)
            
            self._pydantic_success += 1
            logger.info(
                f"✅ [{chunk_id}] Pydantic: {len(result.entities)} entities, "
                f"{len(result.relationships)} relationships"
            )
            
            return pipe_output
            
        except Exception as e:
            logger.warning(f"⚠️ [{chunk_id}] Pydantic extraction failed ({type(e).__name__}), using passthrough: {str(e)[:100]}")
            return await self._fallback_to_base(prompt, system_prompt, chunk_id, **kwargs)
    
    async def _fallback_to_base(
        self,
        prompt: str,
        system_prompt: str,
        chunk_id: str,
        **kwargs
    ) -> str:
        """Fallback to LightRAG's native extraction on Pydantic failure."""
        self._pydantic_fallback += 1
        logger.info(f"🔄 [{chunk_id}] Falling back to LightRAG native extraction")
        return await self.base_llm_func(
            prompt,
            system_prompt=system_prompt,
            history_messages=[],
            **kwargs
        )
    
    def _extract_text_content(self, system_prompt: str) -> Optional[str]:
        """
        Extract the actual text content from LightRAG's SYSTEM prompt.
        
        CRITICAL: LightRAG embeds the chunk text in the system prompt, NOT the user prompt!
        
        System prompt format contains:
        ---Real Data to be Processed---
        <Input>
        Entity_types: [...]
        Text:
        ```
        <actual content here>
        ```
        
        The user prompt is just a short task instruction.
        """
        # Pattern 1: Text:\n```\ncontent\n```
        match = re.search(r'Text:\s*\n```\s*\n(.*?)\n```', system_prompt, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        # Pattern 2: Text:\n<content> (no backticks)
        match = re.search(r'Text:\s*\n(.+?)(?:\n---|\Z)', system_prompt, re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Remove trailing ``` if present
            if content.endswith('```'):
                content = content[:-3].strip()
            return content
        
        # Pattern 3: Look for content after last ```
        parts = system_prompt.split('```')
        if len(parts) >= 2:
            # Get the content between the last pair of ```
            for i in range(len(parts) - 1, 0, -1):
                content = parts[i].strip()
                if content and len(content) > 100:  # Substantial content
                    return content
        
        # Fallback: Return everything after "Text:" if found
        if "Text:" in system_prompt:
            return system_prompt.split("Text:", 1)[1].strip()
        
        return None
    
    def _convert_to_pipe_format(self, result: ExtractionResult, chunk_id: str) -> str:
        """
        Convert Pydantic ExtractionResult to LightRAG's pipe-delimited format.
        
        Entity format: entity<|#|>name<|#|>type<|#|>description
        Relation format: relation<|#|>source<|#|>target<|#|>keywords<|#|>description<|#|>weight
        """
        lines = []
        
        # Convert entities
        for entity in result.entities:
            # Build description from entity attributes
            description = self._build_entity_description(entity)
            
            # Escape any pipe characters in fields
            name = self._escape_pipes(entity.entity_name)
            entity_type = self._escape_pipes(entity.entity_type)
            description = self._escape_pipes(description)
            
            line = f"entity{TUPLE_DELIMITER}{name}{TUPLE_DELIMITER}{entity_type}{TUPLE_DELIMITER}{description}"
            lines.append(line)
        
        # Convert relationships
        for rel in result.relationships:
            # Extract entity names and types from the embedded BaseEntity objects
            source_name = rel.source_entity.entity_name if rel.source_entity else "UNKNOWN"
            source_type = rel.source_entity.entity_type if rel.source_entity else "unknown"
            target_name = rel.target_entity.entity_name if rel.target_entity else "UNKNOWN"
            target_type = rel.target_entity.entity_type if rel.target_entity else "unknown"
            
            # Escape pipes
            source_name = self._escape_pipes(source_name)
            target_name = self._escape_pipes(target_name)
            rel_type = self._escape_pipes(rel.relationship_type)
            
            # LightRAG expects: relation<|#|>source<|#|>target<|#|>keywords<|#|>description
            # Map our rich schema to LightRAG's format:
            # - keywords: relationship_type (e.g., "EVALUATED_BY", "GUIDES")
            # - description: contextual description using entity types
            description = f"{source_name} ({source_type}) {rel_type} {target_name} ({target_type})"
            line = f"relation{TUPLE_DELIMITER}{source_name}{TUPLE_DELIMITER}{target_name}{TUPLE_DELIMITER}{rel_type}{TUPLE_DELIMITER}{description}"
            lines.append(line)
        
        # Add completion delimiter
        lines.append(COMPLETION_DELIMITER)
        
        return "\n".join(lines)
    
    def _build_entity_description(self, entity) -> str:
        """
        Build description for LightRAG pipe format.
        
        Priority: Use actual description field from extraction (Branch 041 fix).
        Metadata tags are appended for additional context but description is primary.
        """
        # PRIMARY: Use the actual description from extraction
        base_desc = ""
        if hasattr(entity, 'description') and entity.description and entity.description.strip():
            base_desc = entity.description.strip()
        
        # SECONDARY: Append critical metadata tags for retrieval
        metadata_parts = []
        
        if hasattr(entity, 'criticality') and entity.criticality:
            metadata_parts.append(f"[Criticality: {entity.criticality}]")
        
        if hasattr(entity, 'modal_verb') and entity.modal_verb:
            metadata_parts.append(f"[Modal: {entity.modal_verb}]")
        
        if hasattr(entity, 'weight') and entity.weight:
            metadata_parts.append(f"[Weight: {entity.weight}]")
        
        if hasattr(entity, 'clause_number') and entity.clause_number:
            metadata_parts.append(f"[Clause: {entity.clause_number}]")
        
        if hasattr(entity, 'threshold') and entity.threshold:
            metadata_parts.append(f"[Threshold: {entity.threshold}]")
        
        if hasattr(entity, 'page_limit') and entity.page_limit:
            metadata_parts.append(f"[Page Limit: {entity.page_limit}]")
        
        # Combine: description first, then metadata
        if base_desc and metadata_parts:
            description = f"{base_desc} {' '.join(metadata_parts)}"
        elif base_desc:
            description = base_desc
        elif metadata_parts:
            description = " ".join(metadata_parts)
        else:
            # Fallback to entity name only if no description or metadata
            description = entity.entity_name
        
        # Clean whitespace (no length truncation - smaller chunks handle this)
        description = re.sub(r"\s+", " ", str(description)).strip()
        
        return description
    
    def _get_relationship_endpoints(self, rel) -> tuple:
        """Extract source and target from relationship (handles different formats)."""
        # New format with entity objects
        if hasattr(rel, 'source_entity') and rel.source_entity:
            source = rel.source_entity.entity_name
        elif hasattr(rel, 'source_id'):
            source = rel.source_id
        else:
            source = "UNKNOWN"
        
        if hasattr(rel, 'target_entity') and rel.target_entity:
            target = rel.target_entity.entity_name
        elif hasattr(rel, 'target_id'):
            target = rel.target_id
        else:
            target = "UNKNOWN"
        
        return source, target
    
    def _escape_pipes(self, text: str) -> str:
        """Escape pipe characters and clean text for pipe-delimited format."""
        if not text:
            return ""
        # Replace pipe with space to avoid parsing issues
        text = str(text).replace("|", " ").replace("<|", " ").replace("|>", " ")
        # Also clean up any accidental delimiters
        text = text.replace(TUPLE_DELIMITER, " ")
        return text.strip()
    
    def get_stats(self) -> dict:
        """Get adapter statistics."""
        total = self._pydantic_success + self._pydantic_fallback
        success_rate = (self._pydantic_success / total * 100) if total > 0 else 0
        
        stats = {
            "extraction_calls": self._extraction_count,
            "passthrough_calls": self._passthrough_count,
            "pydantic_success": self._pydantic_success,
            "pydantic_fallback": self._pydantic_fallback,
            "pydantic_success_rate": f"{success_rate:.1f}%",
        }
        
        if self._pydantic_extractor:
            stats["pydantic_extractor_stats"] = self._pydantic_extractor.get_extraction_stats()
        
        return stats


def create_extraction_adapter(base_llm_func) -> LightRAGExtractionAdapter:
    """
    Factory function to create an extraction adapter.
    
    Usage in config.py:
        from src.extraction.lightrag_llm_adapter import create_extraction_adapter
        
        base_llm_func = create_llm_model_func()
        llm_model_func = create_extraction_adapter(base_llm_func)
    """
    logger.info("🔌 Creating LightRAG extraction adapter with Pydantic validation")
    return LightRAGExtractionAdapter(base_llm_func)
