"""
Government Contracting Multimodal Processor

Extends RAG-Anything's BaseModalProcessor to apply government contracting ontology
to multimodal content from MinerU (tables, images, equations).

Architecture (Issue #54 - Back to Basics):
- Uses RAG-Anything's native multimodal processing
- Generates text descriptions that LightRAG processes natively
- No Pydantic/JSON extraction - pure text for tuple-delimited extraction
"""

import logging
from typing import Dict, Any, Tuple
from raganything.modalprocessors import BaseModalProcessor

logger = logging.getLogger(__name__)


class GovconMultimodalProcessor(BaseModalProcessor):
    """
    Multimodal processor that generates government contracting focused descriptions.
    
    Issue #54: Simplified to use native LightRAG extraction.
    Tables/images/equations get descriptive text → LightRAG extracts entities natively.
    """
    
    def __init__(self, lightrag, modal_caption_func, context_extractor):
        """
        Initialize with RAG-Anything components.
        
        Args:
            lightrag: LightRAG instance for storage/indexing
            modal_caption_func: LLM function (Grok-4 for text analysis)
            context_extractor: RAG-Anything's context extraction utility
        """
        super().__init__(lightrag, modal_caption_func, context_extractor)
        logger.info("🏛️ GovconMultimodalProcessor initialized (native LightRAG extraction)")
    
    async def generate_description_only(
        self,
        modal_content: Dict[str, Any],
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Generate government contracting focused description for multimodal content.
        
        Issue #54: Returns text description that LightRAG processes natively.
        No JSON extraction - LightRAG uses its tuple-delimited format.
        
        Args:
            modal_content: MinerU output (textualized content)
            content_type: "table", "image", "equation"
            item_info: Page/index info
            entity_name: Optional predefined entity name
            
        Returns:
            (description, entity_info) - Text description + metadata
        """
        page_idx = modal_content.get("page_idx", item_info.get("page_idx", 0) if item_info else 0)
        
        if content_type == "table":
            table_body = modal_content.get("table_body", "")
            table_caption = modal_content.get("table_caption", [])
            caption_text = ', '.join(table_caption) if isinstance(table_caption, list) else str(table_caption or '')
            
            # Generate descriptive prompt for LLM
            prompt = f"""Analyze this government contracting table and provide a comprehensive description.

Focus on extracting:
- WORKLOAD DRIVERS: Frequencies, quantities, hours, coverage, service rates
- REQUIREMENTS: Specifications, standards, performance criteria, modal verbs (shall/must/will)
- PERFORMANCE METRICS: KPIs, thresholds, SLAs, measurement methods
- RESOURCES: Equipment counts, personnel requirements, materials
- DELIVERABLES: Reports, data items, CDRLs

Caption: {caption_text}

Table Content:
{table_body}

Provide a detailed description that captures ALL quantitative data (numbers, rates, frequencies, dollar amounts).
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
            description = f"Image from page {page_idx}: {caption_text}" if caption_text else f"Image from page {page_idx}"
            
        elif content_type == "equation":
            equation_content = modal_content.get("content", "")
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
    
    def set_content_source(self, content_list, content_format):
        """Required by BaseModalProcessor for context extraction."""
        super().set_content_source(content_list, content_format)
    
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
