"""
RAG-Anything Initialization Module

This module handles the initialization of the RAG-Anything instance with:
- Custom entity extraction prompts (simplified for clarity)
- Government contracting ontology (18 specialized entity types)
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

from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

# Global RAG-Anything instance
_rag_anything = None


async def initialize_raganything():
    """Initialize RAG-Anything instance for multimodal document processing
    
    Configuration:
    - Parser: MinerU (multimodal - images, tables, equations)
    - Entity Types: 18 government contracting types (semantic-first detection)
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
    
    # Government contracting entity types (18 specialized types)
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
    
    # MinerU configuration from environment variables
    parser = os.getenv("PARSER", "mineru")
    parse_method = os.getenv("PARSE_METHOD", "auto")
    enable_image = os.getenv("ENABLE_IMAGE_PROCESSING", "true").lower() == "true"
    enable_table = os.getenv("ENABLE_TABLE_PROCESSING", "true").lower() == "true"
    enable_equation = os.getenv("ENABLE_EQUATION_PROCESSING", "true").lower() == "true"
    
    # Note: HF_TOKEN and HF_HUB_DISABLE_SYMLINKS_WARNING are automatically
    # inherited by MinerU subprocess if set in environment
    
    # Create RAG-Anything configuration
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser=parser,
        parse_method=parse_method,
        enable_image_processing=enable_image,
        enable_table_processing=enable_table,
        enable_equation_processing=enable_equation,
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
    
    # Load entity extraction prompt from external file
    # Philosophy: Prompts are training data, not code (2M context = detailed examples)
    custom_entity_extraction_prompt = load_prompt("entity_extraction/entity_extraction_prompt")

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
    
    # CRITICAL: Ensure LightRAG is initialized BEFORE any document processing
    # This is required because process_document_complete_lightrag_api() accesses
    # self.lightrag.doc_status BEFORE calling _ensure_lightrag_initialized()
    result = await _rag_anything._ensure_lightrag_initialized()
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Failed to initialize LightRAG: {error_msg}")
        raise RuntimeError(f"LightRAG initialization failed: {error_msg}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMPATIBILITY FIX: RAG-Anything + LightRAG doc_status schema
    # ═══════════════════════════════════════════════════════════════════════════════
    # Issue: RAG-Anything writes 'multimodal_processed' field to doc_status after
    #        multimodal content processing, but LightRAG's DocProcessingStatus
    #        dataclass doesn't accept this field (causes 500 error in WebUI).
    #
    # Official Workaround (from RAG-Anything examples/lmstudio_integration_example.py):
    #   "Compatibility: avoid writing unknown field 'multimodal_processed' to 
    #    LightRAG doc_status. Older LightRAG versions may not accept this extra 
    #    field in DocProcessingStatus"
    #
    # Solution: Replace _mark_multimodal_processing_complete() with no-op function
    #           to prevent writing the incompatible field.
    # ═══════════════════════════════════════════════════════════════════════════════
    async def _noop_mark_multimodal(doc_id: str):
        """No-op replacement to prevent writing multimodal_processed field."""
        return None
    
    _rag_anything._mark_multimodal_processing_complete = _noop_mark_multimodal
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Use print() instead of logger to ensure output visibility during startup
    print("✅ RAG-Anything initialized")
    print(f"   Parser: MinerU ({parse_method}) - multimodal enabled")
    print(f"   Entity types: {len(entity_types)} specialized types")
    print(f"   LightRAG storages: Ready")
    print(f"   500 error fix: Applied ✅")
    
    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
