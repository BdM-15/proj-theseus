"""
Ontology-Aware Table Processor for Government Contracting

Simple approach: MinerU parses tables excellently. 
We just format the output clearly for LLM extraction.

Architecture:
1. MinerU parses PDF → provides table HTML/structure
2. THIS PROCESSOR → cleans and formats for readability
3. LightRAG → lightrag_llm_adapter → extracts GovCon entities

Issue #46: Tables contain critical data (eval matrices, CDRLs, labor, pricing).
"""

import logging
import re
from typing import Dict, Any, Tuple

from raganything.modalprocessors import BaseModalProcessor

logger = logging.getLogger(__name__)


class OntologyTableProcessor(BaseModalProcessor):
    """
    Formats MinerU's table output for optimal LLM extraction.
    
    MinerU does the hard work of parsing. We just clean up the output.
    """
    
    def __init__(self, lightrag, modal_caption_func, context_extractor=None):
        super().__init__(lightrag, modal_caption_func, context_extractor)
        logger.info("📊 OntologyTableProcessor: Using MinerU's table parsing")
    
    async def generate_description_only(
        self,
        modal_content: Dict[str, Any],
        content_type: str,
        item_info: Dict[str, Any] = None,
        entity_name: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Format MinerU's table output for LLM extraction.
        """
        page_idx = modal_content.get("page_idx", 0)
        if item_info:
            page_idx = item_info.get("page_idx", page_idx)
        
        # Get caption if available
        caption = self._get_caption(modal_content)
        
        # Get table content - MinerU provides this
        table_content = self._get_table_content(modal_content)
        
        # Format for LLM
        if caption:
            description = f"TABLE: {caption}\n\n{table_content}"
        else:
            description = f"TABLE (Page {page_idx}):\n\n{table_content}"
        
        # Entity info for RAG-Anything
        entity_info = {
            "entity_name": entity_name or caption or f"Table_Page_{page_idx}",
            "entity_type": "table",
            "page_idx": page_idx,
        }
        
        # Log table size
        row_count = table_content.count('\n')
        logger.info(f"📊 Table (page {page_idx}): ~{row_count} lines → LLM extraction")
        
        return description, entity_info
    
    def _get_caption(self, modal_content: Dict[str, Any]) -> str:
        """Get table caption from MinerU output."""
        caption = modal_content.get("table_caption", [])
        if isinstance(caption, list):
            return " ".join(str(c).strip() for c in caption if c)
        return str(caption).strip() if caption else ""
    
    def _get_table_content(self, modal_content: Dict[str, Any]) -> str:
        """
        Extract and clean table content from MinerU.
        
        MinerU provides table data in various formats:
        - table_body: HTML string or list of lists
        - text: Plain text representation
        """
        # Try table_body first (MinerU's primary output)
        table_body = modal_content.get("table_body", "")
        
        if table_body:
            if isinstance(table_body, str):
                # HTML table - clean it up
                return self._html_to_text(table_body)
            elif isinstance(table_body, list):
                # List of lists - format as rows
                return self._lists_to_text(table_body)
        
        # Fallback to text field
        text = modal_content.get("text", "")
        if text:
            return str(text).strip()
        
        # Last resort - stringify the whole thing
        return str(modal_content)
    
    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML table to clean text.
        
        MinerU gives us well-structured HTML. Just clean it up.
        """
        lines = []
        
        # Extract rows
        tr_pattern = r"<tr[^>]*>(.*?)</tr>"
        for tr_match in re.finditer(tr_pattern, html, re.IGNORECASE | re.DOTALL):
            tr_content = tr_match.group(1)
            
            # Extract cells (th or td)
            cell_pattern = r"<t[hd][^>]*>(.*?)</t[hd]>"
            cells = re.findall(cell_pattern, tr_content, re.IGNORECASE | re.DOTALL)
            
            if cells:
                # Clean each cell
                clean_cells = [self._clean_html(cell) for cell in cells]
                # Filter empty cells but preserve structure
                row_text = " | ".join(c if c else "-" for c in clean_cells)
                if row_text.replace("-", "").replace("|", "").strip():
                    lines.append(row_text)
        
        if lines:
            return "\n".join(lines)
        
        # If no rows found, just strip all HTML
        return self._clean_html(html)
    
    def _lists_to_text(self, data: list) -> str:
        """Convert list-of-lists to text."""
        lines = []
        for row in data:
            if isinstance(row, list):
                cells = [str(c).strip() for c in row]
                lines.append(" | ".join(c if c else "-" for c in cells))
            else:
                lines.append(str(row).strip())
        return "\n".join(lines)
    
    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and normalize whitespace."""
        # Remove tags
        text = re.sub(r"<[^>]+>", " ", html)
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
