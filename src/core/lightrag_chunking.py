"""
LightRAG Chunking Extension - Path B Simplified Approach

Provides simple chunking strategy that works WITH LightRAG's semantic extraction.
No complex regex preprocessing - let LightRAG's ontology-guided prompts identify structure.

Path B Philosophy:
- Use simple, clean chunking (basic sliding window or standard LightRAG)
- Let ontology-modified extraction prompts identify sections/entities
- Post-process extracted entities with ontology validation
- Don't corrupt input with deterministic regex preprocessing

Usage:
    from src.core.lightrag_chunking import simple_chunking_func

    rag = LightRAG(
        chunking_func=simple_chunking_func,  # Simple, clean chunks
        addon_params={
            "entity_types": [e.value for e in EntityType],  # Ontology injection!
        }
        # ... other params
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
    Simple chunking function for LightRAG - Path B approach.

    Uses LightRAG's standard chunking without complex preprocessing.
    Let ontology-modified extraction prompts identify sections/entities semantically.

    Path B Philosophy:
    - Clean, simple chunks = better semantic extraction
    - Ontology injection teaches LightRAG government contracting concepts
    - Post-processing validates against ontology
    - No regex preprocessing that creates fictitious entities

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
        logger.info(f"🔍 Path B Simple Chunking - content length: {len(content):,} chars")
        
        # Use LightRAG's standard chunking - clean and simple
        # Let ontology-guided extraction identify structure semantically
        from lightrag.operate import chunking_by_token_size
        
        chunks = chunking_by_token_size(
            tokenizer,
            content,
            split_by_character,
            split_by_character_only,
            chunk_overlap_token_size,
            chunk_token_size,
        )
        
        logger.info(f"✅ Created {len(chunks)} clean chunks for ontology-guided extraction")
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
# Path B: Simple Chunking - Let LightRAG Handle Semantic Extraction
# ============================================================================
#
# Previous Path A (archived) used complex regex preprocessing with:
# - ShipleyRFPChunker class (400+ lines)
# - Regex-based section identification
# - Custom relationship mapping
# - Requirement extraction preprocessing
#
# This created fictitious entities like "RFP Section J-L" that don't exist.
#
# Path B Philosophy:
# - Use clean, simple chunks (LightRAG's standard chunking)
# - Inject ontology into addon_params["entity_types"]
# - Let LightRAG's semantic extraction identify sections/entities
# - Post-process with ontology validation
#
# Result: Clean knowledge graph with valid government contracting entities
# ============================================================================