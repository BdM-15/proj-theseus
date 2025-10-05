"""
LightRAG Chunking Extension - Ontology-Based Approach

Provides clean chunking strategy that works WITH LightRAG's ontology-guided semantic extraction.
No complex regex preprocessing - let LightRAG's domain-enhanced prompts identify structure.

Ontology-Based Philosophy:
- Use simple, clean chunking (standard LightRAG tokenization)
- Let ontology-modified extraction prompts identify sections/entities
- Government contracting domain knowledge injected into LLM prompts
- Post-process extracted entities with ontology validation

Usage:
    from core.lightrag_chunking import simple_chunking_func

    rag = LightRAG(
        chunking_func=simple_chunking_func,  # Clean chunks for semantic extraction
        addon_params={
            "entity_types": [e.value for e in EntityType],  # Ontology injection!
            "ontology_injector": injector  # Domain knowledge enhancement
        }
    )
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def simple_chunking_func(
    tokenizer,
    content: str,
    split_by_character: Optional[str] = None,
    split_by_character_only: bool = False,
    chunk_overlap_token_size: int = 100,
    chunk_token_size: int = 1200,
) -> List[Dict[str, Any]]:
    """
    Ontology-based chunking function for government contracting RFP analysis.

    Uses LightRAG's standard chunking without complex preprocessing.
    Let ontology-enhanced extraction prompts identify sections/entities semantically.

    Ontology-Based Philosophy:
    - Clean, simple chunks = better semantic extraction
    - Domain knowledge injected into LLM extraction prompts
    - Government contracting concepts taught through ontology
    - Post-processing validates against domain ontology

    This signature MUST match LightRAG's expectations exactly.

    Args:
        tokenizer: Tokenizer instance for counting tokens
        content: Document text to chunk
        split_by_character: Optional character to split on
        split_by_character_only: If True, split only on specified character
        chunk_overlap_token_size: Overlap between consecutive chunks
        chunk_token_size: Maximum tokens per chunk

    Returns:
        List of chunk dictionaries in LightRAG format:
        [
            {
                'content': str,  # The chunk text
                'tokens': int,   # Token count
                'metadata': dict  # Optional metadata
            },
            ...
        ]
    """
    try:
        logger.info(f"🎯 Ontology-Based Chunking - content length: {len(content):,} chars")
        
        # Use LightRAG's standard chunking - clean and simple
        # Let ontology-enhanced extraction identify structure semantically
        from lightrag.operate import chunking_by_token_size
        
        chunks = chunking_by_token_size(
            tokenizer,
            content,
            split_by_character,
            split_by_character_only,
            chunk_overlap_token_size,
            chunk_token_size,
        )
        
        logger.info(f"✅ Created {len(chunks)} clean chunks for ontology-enhanced extraction")
        return chunks
        
    except Exception as e:
        logger.warning(f"⚠️ Chunking error: {e}, falling back to standard LightRAG chunking")
        # Fall back to standard chunking on error
        from lightrag.operate import chunking_by_token_size
        return chunking_by_token_size(
            tokenizer,
            content,
            split_by_character,
            split_by_character_only,
            chunk_overlap_token_size,
            chunk_token_size,
        )


# ============================================================================
# RFP-Aware Ontology Chunking: Contextual Markers + Domain Knowledge
# ============================================================================

def rfp_aware_chunking_func(
    tokenizer,
    content: str,
    split_by_character: Optional[str] = None,
    split_by_character_only: bool = False,
    chunk_overlap_token_size: int = 100,
    chunk_token_size: int = 1200,
) -> List[Dict[str, Any]]:
    """
    RFP-aware ontology-based chunking with section context markers.
    
    Enhanced Ontology Approach:
    - Detect RFP sections (A-M) using lightweight patterns
    - Add contextual markers: [RFP Section L: Instructions to Offerors]
    - Use LightRAG's standard tokenizer-based chunking
    - Let ontology-enhanced extraction identify entities semantically
    
    Benefits:
    ✅ Section context improves cross-reference extraction (L↔M relationships)
    ✅ Still uses LLM semantic extraction (no fictitious entities)
    ✅ Markers provide structure hints without deterministic preprocessing
    
    Args:
        tokenizer: Tokenizer instance for counting tokens
        content: Document text to chunk
        split_by_character: Optional character to split on
        split_by_character_only: If True, split only on specified character
        chunk_overlap_token_size: Overlap between consecutive chunks
        chunk_token_size: Maximum tokens per chunk
        
    Returns:
        List of chunk dictionaries with section markers
    """
    try:
        logger.info(f"🔍 RFP-Aware Chunking - content length: {len(content):,} chars")
        
        # Detect if this is an RFP document
        is_rfp = _detect_rfp_document(content)
        
        if not is_rfp:
            logger.info("   Not an RFP document - using simple chunking")
            return simple_chunking_func(
                tokenizer, content, split_by_character,
                split_by_character_only, chunk_overlap_token_size, chunk_token_size
            )
        
        logger.info("🎯 RFP document detected - adding section markers")
        
        # Identify RFP sections using lightweight patterns
        sections = _identify_rfp_sections(content)
        logger.info(f"   Found {len(sections)} sections: {[s['id'] for s in sections]}")
        
        # Add section markers to content
        marked_content = _add_section_markers(content, sections)
        
        # Use LightRAG's standard chunking on marked content
        from lightrag.operate import chunking_by_token_size
        chunks = chunking_by_token_size(
            tokenizer,
            marked_content,
            split_by_character,
            split_by_character_only,
            chunk_overlap_token_size,
            chunk_token_size,
        )
        
        logger.info(f"✅ Created {len(chunks)} section-aware chunks")
        return chunks
        
    except Exception as e:
        logger.warning(f"⚠️ RFP chunking error: {e}, falling back to simple chunking")
        return simple_chunking_func(
            tokenizer, content, split_by_character,
            split_by_character_only, chunk_overlap_token_size, chunk_token_size
        )


def _detect_rfp_document(content: str) -> bool:
    """Lightweight detection of RFP documents"""
    rfp_indicators = [
        r'(?i)section\s+[a-m][\s\-:]+',
        r'(?i)solicitation\s+number',
        r'(?i)request\s+for\s+proposal',
        r'(?i)instructions?\s+to\s+offerors?',
        r'(?i)evaluation\s+(?:criteria|factors)',
    ]
    
    import re
    for pattern in rfp_indicators:
        if re.search(pattern, content[:5000]):  # Check first 5000 chars
            return True
    return False


def _identify_rfp_sections(content: str) -> List[Dict[str, Any]]:
    """
    Lightweight RFP section identification.
    Returns list of sections with id, title, start, end positions.
    """
    import re
    
    section_patterns = {
        "A": r'(?i)section\s+a[\s\-:]+(?:solicitation|contract\s+form)',
        "B": r'(?i)section\s+b[\s\-:]+(?:supplies?|services?|prices?|costs?)',
        "C": r'(?i)section\s+c[\s\-:]+(?:statement\s+of\s+work|description|sow)',
        "H": r'(?i)section\s+h[\s\-:]+(?:special\s+contract\s+requirements)',
        "I": r'(?i)section\s+i[\s\-:]+(?:contract\s+clauses)',
        "J": r'(?i)section\s+j[\s\-:]+(?:attachments?|list)',
        "L": r'(?i)section\s+l[\s\-:]+(?:instructions?\s+to\s+offerors?)',
        "M": r'(?i)section\s+m[\s\-:]+(?:evaluation\s+(?:criteria|factors))',
    }
    
    sections = []
    for section_id, pattern in section_patterns.items():
        matches = list(re.finditer(pattern, content))
        for match in matches:
            sections.append({
                'id': section_id,
                'start': match.start(),
                'pattern': pattern
            })
    
    # Sort by position
    sections.sort(key=lambda x: x['start'])
    
    # Assign end positions and titles
    section_titles = {
        "A": "Solicitation/Contract Form",
        "B": "Supplies or Services and Prices",
        "C": "Statement of Work",
        "H": "Special Contract Requirements",
        "I": "Contract Clauses",
        "J": "List of Attachments",
        "L": "Instructions to Offerors",
        "M": "Evaluation Criteria",
    }
    
    for i, section in enumerate(sections):
        section['title'] = section_titles.get(section['id'], f"Section {section['id']}")
        if i + 1 < len(sections):
            section['end'] = sections[i + 1]['start']
        else:
            section['end'] = len(content)
    
    return sections


def _add_section_markers(content: str, sections: List[Dict[str, Any]]) -> str:
    """
    Add section markers to content for better entity extraction context.
    
    Example markers:
    - [RFP Section L: Instructions to Offerors]
    - [RFP Section M: Evaluation Criteria]
    """
    if not sections:
        return content
    
    marked_content = content
    offset = 0  # Track position changes due to insertions
    
    for section in sections:
        marker = f"\n[RFP Section {section['id']}: {section['title']}]\n"
        insert_pos = section['start'] + offset
        
        marked_content = (
            marked_content[:insert_pos] + 
            marker + 
            marked_content[insert_pos:]
        )
        
        offset += len(marker)
    
    return marked_content


# ============================================================================
# Ontology-Based Approach: Enhance LightRAG with Domain Knowledge
# ============================================================================
#
# Previous approaches used complex regex preprocessing that created fictitious
# entities (e.g., "RFP Section J-L" that don't exist in documents).
#
# Current Ontology-Based Philosophy:
# - Use clean, simple chunks (LightRAG's standard tokenization)
# - Inject government contracting ontology into extraction prompts
# - Let LLM with domain knowledge identify sections/entities semantically
# - Post-process with ontology validation for accuracy
#
# RFP-Aware Variant (rfp_aware_chunking_func):
# - Lightweight section detection (adds contextual markers only)
# - Still uses LightRAG's tokenizer and semantic extraction
# - Provides section context without creating fictitious entities
#
# Result: Clean knowledge graph with valid government contracting entities
# extracted by LLM with proper domain understanding through ontology injection
# ============================================================================
