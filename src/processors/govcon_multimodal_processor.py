"""
Government Contracting Multimodal Processor

Extends RAG-Anything's BaseModalProcessor to apply government contracting ontology
to multimodal content from MinerU (tables, images, equations).

Architecture:
- MinerU: Vision model that textualizes ALL content (runs once during parsing)
- This processor: Text analysis with domain ontology (runs on textualized content)
- RAG-Anything: Handles chunking, storage, indexing, and graph merging

Key Design Decision:
We override ONLY generate_description_only() - RAG-Anything handles everything else
(chunk creation, entity storage, vector indexing, graph merging).
"""

import logging
from typing import Dict, Any, Tuple
from raganything.modalprocessors import BaseModalProcessor
from src.extraction.json_extractor import JsonExtractor

logger = logging.getLogger(__name__)


class GovconMultimodalProcessor(BaseModalProcessor):
    """
    Applies government contracting ontology to multimodal content.
    
    Handles: tables (HTML), images (OCR text), equations (LaTeX)
    All content is already textualized by MinerU's vision models.
    
    This processor extends RAG-Anything's pipeline to use our custom
    entity extraction (Requirements, Metrics, Deliverables, etc.) instead
    of generic descriptions.
    """
    
    def __init__(self, lightrag, modal_caption_func, context_extractor=None):
        """
        Initialize with RAG-Anything's standard components.
        
        Args:
            lightrag: LightRAG instance for storage/indexing
            modal_caption_func: LLM function (Grok-4 for text analysis)
            context_extractor: RAG-Anything's context extraction utility
        """
        super().__init__(lightrag, modal_caption_func, context_extractor)
        self.json_extractor = JsonExtractor()
        logger.info("🏛️ GovconMultimodalProcessor initialized with ontology awareness")
    
    async def generate_description_only(
        self,
        modal_content: Dict[str, Any],
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        OVERRIDE: Apply govcon ontology instead of generic description.
        
        This is the ONLY method we override - RAG-Anything handles:
        - Chunk creation
        - Entity storage
        - Vector indexing
        - Graph merging
        
        Args:
            modal_content: MinerU output (textualized content)
            content_type: "table", "image", "equation"
            item_info: Page/index info for context extraction
            entity_name: Optional predefined entity name
        
        Returns:
            (description, entity_info) for RAG-Anything's pipeline
        """
        # Extract textualized content (MinerU already did vision work)
        text_content, caption = self._extract_text_content(
            modal_content, content_type
        )
        
        # Get document context (RAG-Anything's context extractor)
        doc_context = ""
        if item_info and self.context_extractor:
            doc_context = self._get_context_for_item(item_info)
        
        # Build ontology-aware prompt
        ontology_prompt = self._build_ontology_prompt(
            doc_context, caption, text_content, content_type
        )
        
        # Extract govcon entities using our JsonExtractor
        page_idx = modal_content.get("page_idx", item_info.get("page_idx", 0) if item_info else 0)
        chunk_id = f"govcon_{content_type}_p{page_idx}"
        
        extraction_result = await self.json_extractor.extract_from_text(
            text=ontology_prompt,
            chunk_id=chunk_id
        )
        
        # Format for RAG-Anything's pipeline
        description, entity_info = self._format_for_raganything(
            extraction_result,
            entity_name,
            content_type,
            modal_content
        )
        
        logger.info(
            f"✅ Extracted {len(extraction_result.entities)} govcon entities "
            f"from {content_type} (page {page_idx})"
        )
        
        return description, entity_info
    
    def _extract_text_content(
        self, modal_content: Dict[str, Any], content_type: str
    ) -> Tuple[str, str]:
        """Extract textualized content from MinerU output."""
        
        if content_type == "table":
            # MinerU already converted table to HTML text
            text_content = modal_content.get("table_body", "")
            caption = ", ".join(modal_content.get("table_caption", []))
        
        elif content_type == "image":
            # MinerU already OCR'd the image
            text_content = modal_content.get("text", "")
            caption = ", ".join(modal_content.get("image_caption", []))
        
        elif content_type == "equation":
            # MinerU already extracted LaTeX
            text_content = modal_content.get("latex", "")
            caption = modal_content.get("equation_caption", "")
        
        else:
            text_content = str(modal_content)
            caption = ""
        
        return text_content, caption
    
    def _build_ontology_prompt(
        self,
        doc_context: str,
        caption: str,
        text_content: str,
        content_type: str
    ) -> str:
        """Build ontology-aware prompt for entity extraction."""
        
        context_section = f"Document Context:\n{doc_context}\n\n" if doc_context else ""
        caption_section = f"{content_type.title()}: {caption}\n\n" if caption else ""
        
        return f"""
{context_section}{caption_section}Content:
{text_content}

Extract government contracting entities from this {content_type}:

1. REQUIREMENTS - Compliance criteria, specifications, constraints
   - Include frequencies, standards, completion criteria
   - Tag with requirement type (performance, technical, delivery)

2. METRICS - Quantifiable measures for estimation
   - Quantities (counts, volumes, capacities)
   - Frequencies (daily, weekly, monthly, yearly)
   - Coverage (hours, days, locations)
   - Thresholds (minimums, maximums, ranges)

3. DELIVERABLES - Work outputs, reports, schedules
   - Document types and formats
   - Submission frequencies and deadlines
   - Review/approval processes

4. RESOURCES - Equipment, personnel, facilities, materials
   - Specific models/types
   - Quantities required
   - Qualifications/certifications

5. RELATIONSHIPS - How entities connect
   - Requirements ↔ Metrics (compliance measurement)
   - Deliverables ↔ Requirements (evidence of compliance)
   - Resources ↔ Requirements (capability enablers)

Focus on workload drivers and basis of estimate elements.
"""
    
    def _format_for_raganything(
        self,
        extraction_result,
        entity_name: str,
        content_type: str,
        modal_content: Dict[str, Any]
    ) -> Tuple[str, Dict[str, Any]]:
        """Format extraction results for RAG-Anything's pipeline.
        
        Note: We only output entity_type and entity_name. The verbatim source
        text is already preserved in the chunk - no need to duplicate it.
        """
        
        # Create description from extracted entities (type: name format)
        # This becomes the "Analysis:" section appended to the chunk
        entity_summaries = []
        for entity in extraction_result.entities:
            entity_summaries.append(
                f"{entity.entity_type}: {entity.entity_name}"
            )
        
        description = "\n".join(entity_summaries) if entity_summaries else f"No govcon entities found in {content_type}"
        
        # Create entity_info compatible with RAG-Anything
        page_idx = modal_content.get("page_idx", 0)
        entity_info = {
            "entity_name": entity_name or f"govcon_{content_type}_p{page_idx}",
            "entity_type": f"govcon_{content_type}",
            "summary": description,
            # Preserve our extraction results for downstream use
            # source_text is empty - verbatim text is in the chunk
            "govcon_entities": [
                {
                    "name": e.entity_name,
                    "type": e.entity_type
                } for e in extraction_result.entities
            ],
            "govcon_relationships": [
                {
                    "source": r.source_entity.entity_name,
                    "target": r.target_entity.entity_name,
                    "type": r.relationship_type
                } for r in extraction_result.relationships
            ]
        }
        
        return description, entity_info
