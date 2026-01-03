"""
Government Contracting Multimodal Processor

Extends RAG-Anything's BaseModalProcessor to apply government contracting ontology
to multimodal content from MinerU (tables, images, equations).

Architecture (Issue #54 - Back to Basics, Issue #62 - Context-Aware Processing):
- Uses RAG-Anything's native multimodal processing
- Generates text descriptions that LightRAG processes natively
- Extracts surrounding page context for section awareness
- No Pydantic/JSON extraction - pure text for tuple-delimited extraction

Issue #62 Enhancement:
Tables/images are processed with surrounding page context, enabling:
- Section-aware entity names ("Appendix H Workload Table" vs "table_p53")
- CHILD_OF relationships inferred by Algorithm 7
- Better VDB embeddings that capture section semantics
"""

import logging
from typing import Dict, Any, Tuple, Optional
from raganything.modalprocessors import BaseModalProcessor

logger = logging.getLogger(__name__)


class GovconMultimodalProcessor(BaseModalProcessor):
    """
    Multimodal processor that generates government contracting focused descriptions.
    
    Issue #54: Simplified to use native LightRAG extraction.
    Issue #62: Enhanced with context-aware processing for section awareness.
    
    Tables/images/equations get descriptive text with surrounding context
    → LightRAG extracts entities natively with parent section relationships.
    """
    
    def __init__(self, lightrag, modal_caption_func, context_extractor):
        """
        Initialize with RAG-Anything components.
        
        Args:
            lightrag: LightRAG instance for storage/indexing
            modal_caption_func: LLM function (Grok-4 for text analysis)
            context_extractor: RAG-Anything's context extraction utility (Issue #62)
        """
        super().__init__(lightrag, modal_caption_func, context_extractor)
        self._content_list = None
        self._content_format = None
        logger.info("🏛️ GovconMultimodalProcessor initialized (context-aware processing enabled)")
    
    def set_content_source(self, content_list, content_format):
        """
        Set the document content for context extraction.
        
        Called by RAG-Anything before processing multimodal items.
        Stores content_list for extract_surrounding_context().
        
        Args:
            content_list: MinerU parsed content (pages/items)
            content_format: Parser format ("minerU", etc.)
        """
        super().set_content_source(content_list, content_format)
        self._content_list = content_list
        self._content_format = content_format
        logger.debug(f"📄 Content source set: {len(content_list) if content_list else 0} items, format={content_format}")
    
    def _extract_surrounding_context(self, page_idx: int, content_type: str) -> Optional[str]:
        """
        Extract surrounding page context for section awareness (Issue #62).
        
        Uses RAG-Anything's context_extractor to get text from surrounding pages,
        enabling tables to know what section/appendix they belong to.
        
        Args:
            page_idx: Page index of the multimodal item
            content_type: Type of content ("table", "image", "equation")
            
        Returns:
            Surrounding context text, or None if unavailable
        """
        if not self.context_extractor or not self._content_list:
            logger.debug(f"⚠️ Context extraction unavailable for {content_type} on page {page_idx}")
            return None
        
        try:
            # Use RAG-Anything's context extractor
            context = self.context_extractor.extract_context(
                content_list=self._content_list,
                target_page_idx=page_idx,
                content_format=self._content_format
            )
            
            if context and len(context) > 50:
                logger.info(f"📖 Extracted {len(context)} chars of context for {content_type} on page {page_idx}")
                return context
            else:
                logger.debug(f"📖 Minimal context for {content_type} on page {page_idx}")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Context extraction failed for {content_type} on page {page_idx}: {e}")
            return None
    
    async def generate_description_only(
        self,
        modal_content: Dict[str, Any],
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate government contracting focused description with context awareness.
        
        Issue #54: Returns text description that LightRAG processes natively.
        Issue #62: Includes surrounding page context for section awareness.
        
        Args:
            modal_content: MinerU output (textualized content)
            content_type: "table", "image", "equation"
            item_info: Page/index info
            entity_name: Optional predefined entity name
            
        Returns:
            (description, entity_info) - Text description + metadata
        """
        page_idx = modal_content.get("page_idx", item_info.get("page_idx", 0) if item_info else 0)
        
        # Issue #62: Extract surrounding context for section awareness
        surrounding_context = self._extract_surrounding_context(page_idx, content_type)
        context_section = ""
        if surrounding_context:
            context_section = f"""
DOCUMENT CONTEXT (from surrounding pages):
{surrounding_context[:2000]}

Use this context to understand what SECTION, APPENDIX, or ATTACHMENT this {content_type} belongs to.
Include the parent section name in your description (e.g., "This table from Appendix H - Workload Data...").

"""
        
        if content_type == "table":
            table_body = modal_content.get("table_body", "")
            table_caption = modal_content.get("table_caption", [])
            caption_text = ', '.join(table_caption) if isinstance(table_caption, list) else str(table_caption or '')
            
            # Generate descriptive prompt for LLM with context awareness
            prompt = f"""Analyze this government contracting table and provide a comprehensive description.
{context_section}
Focus on extracting:
- DOCUMENT LOCATION: Section, Appendix, or Attachment this table belongs to
- WORKLOAD DRIVERS: Frequencies, quantities, hours, coverage, service rates
- REQUIREMENTS: Specifications, standards, performance criteria, modal verbs (shall/must/will)
- PERFORMANCE METRICS: KPIs, thresholds, SLAs, measurement methods
- RESOURCES: Equipment counts, personnel requirements, materials
- DELIVERABLES: Reports, data items, CDRLs

Caption: {caption_text}

Table Content:
{table_body}

IMPORTANT: Start your description with the section/appendix location if known from context.
Include ALL quantitative data (numbers, rates, frequencies, dollar amounts).
Include exact values - never generalize "100 times per year" to "frequent"."""

            # Use modal_caption_func to generate description
            try:
                description = await self.modal_caption_func(prompt)
                if not description:
                    description = f"Table from page {page_idx}: {caption_text or 'No caption'}"
                logger.info(f"✅ Generated govcon description for {content_type} (page {page_idx})")
            except Exception as e:
                logger.warning(f"⚠️ LLM description failed for {content_type} (page {page_idx}): {e}")
                # Fallback to raw table content
                description = f"Table from page {page_idx}:\n{caption_text}\n{table_body[:2000]}"
        
        elif content_type == "image":
            image_caption = modal_content.get("img_caption", [])
            caption_text = ', '.join(image_caption) if isinstance(image_caption, list) else str(image_caption or '')
            
            # Include context for images too
            if surrounding_context:
                description = f"Image from page {page_idx} ({surrounding_context[:500]}): {caption_text}" if caption_text else f"Image from page {page_idx} (context: {surrounding_context[:300]})"
            else:
                description = f"Image from page {page_idx}: {caption_text}" if caption_text else f"Image from page {page_idx}"
            
        elif content_type == "equation":
            equation_content = modal_content.get("content", "")
            
            # Include context for equations
            if surrounding_context:
                description = f"Equation from page {page_idx} ({surrounding_context[:300]}): {equation_content[:500]}"
            else:
                description = f"Equation from page {page_idx}: {equation_content[:500]}"
            
        else:
            # Generic fallback
            description = str(modal_content.get("content", modal_content))[:500]
        
        # Create entity info metadata
        entity_info = {
            "entity_name": entity_name or f"{content_type}_p{page_idx}",
            "entity_type": content_type,
            "summary": description[:200],
            "page_idx": page_idx,
        }
        
        return description, entity_info
    
    async def process_multimodal_content(
        self,
        modal_content: Dict[str, Any],
        content_type: str = None,
        item_info: Dict[str, Any] = None,
        **kwargs  # Accept any extra args RAG-Anything might pass (e.g., file_path)
    ) -> Dict[str, Any]:
        """
        Process multimodal content and insert into LightRAG.
        
        This method is called by RAG-Anything's fallback processing when batch
        processing fails. It generates a description and inserts it into LightRAG.
        
        Args:
            modal_content: MinerU output (textualized content)
            content_type: "table", "image", "equation" (auto-detected if None)
            item_info: Page/index info
            
        Returns:
            dict: Processing result with status and entity info
        """
        # Auto-detect content type if not provided
        if content_type is None:
            content_type = modal_content.get("type", "unknown")
        
        # Generate description using our govcon-focused method
        description, entity_info = await self.generate_description_only(
            modal_content=modal_content,
            content_type=content_type,
            item_info=item_info
        )
        
        # Insert the description into LightRAG for native extraction
        try:
            if description and len(description) > 10:
                await self.lightrag.ainsert(description)
                logger.info(f"✅ Inserted {content_type} description into LightRAG ({len(description)} chars)")
                return {
                    "status": "success",
                    "entity_info": entity_info,
                    "description_length": len(description)
                }
            else:
                logger.warning(f"⚠️ Skipped {content_type} - description too short")
                return {
                    "status": "skipped",
                    "reason": "description_too_short"
                }
        except Exception as e:
            logger.error(f"❌ Failed to insert {content_type} into LightRAG: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
