"""
RAG-Anything Initialization Module

This module handles the initialization of the RAG-Anything instance with:
- Custom entity extraction prompts (simplified for clarity)
- Government contracting ontology (18 specialized entity types)
- Multimodal document processing (MinerU parser)
- Cloud LLM integration (xAI Grok + OpenAI embeddings)
"""

# CRITICAL: Ensure .env is loaded before LightRAG imports
# This file is imported by raganything_server.py which loads .env first
# But we import it here too for safety if this module is used standalone
import os
from dotenv import load_dotenv
load_dotenv()

# Now safe to import LightRAG and related modules
import logging
from lightrag.api.config import global_args
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

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
    - Embeddings: OpenAI text-embedding-3-large (3072-dim, 8192 token limit)
    - Chunking: 8K tokens (overlap: 1.2K) - Multiple focused extraction passes
    
    Architecture Note:
    LightRAG chunks documents at 8192 tokens. Same chunks go to BOTH:
    - LLM entity extraction (multiple focused passes = comprehensive entity coverage)
    - Embedding generation (fits within 8192 token limit, no truncation needed)
    Smaller chunks prevent LLM attention decay that caused 50K chunk extraction failure.
    
    Returns:
        RAGAnything: Configured instance ready for document ingestion
    """
    global _rag_anything
    
    # Get API credentials (using RAG-Anything official variable names)
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = global_args.working_dir
    
    # Government contracting entity types (17 specialized types)
    # Semantic-first detection: Content determines entity type, not section labels
    # NOTE: LightRAG normalizes to lowercase internally - use lowercase for consistency
    entity_types = [
        # Core entities
        "organization", "concept", "event", "technology", "person", "location",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "requirement",
        
        # Structural entities
        "clause",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "section",                  # Stores both structural_label + semantic_type
        "document",                 # References: specs, standards, manuals, regulations, attachments, annexes
        "deliverable",
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        "evaluation_factor",        # Scoring criteria (Section M content)
        "submission_instruction",   # Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (Capture planning patterns)
        "strategic_theme",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (Semantic detection regardless of location)
        "statement_of_work",        # PWS/SOW/SOO content (may be Section C or attachment)
        
        # Programs and equipment
        "program",                  # Major programs (MCPP II, Navy MBOS, etc.)
        "equipment",                # Physical items (batteries, vehicles, tools)
    ]
    
    # MinerU configuration from environment variables
    parser = os.getenv("PARSER", "mineru")
    parse_method = os.getenv("PARSE_METHOD", "auto")
    enable_image = os.getenv("ENABLE_IMAGE_PROCESSING", "true").lower() == "true"
    enable_table = os.getenv("ENABLE_TABLE_PROCESSING", "true").lower() == "true"
    enable_equation = os.getenv("ENABLE_EQUATION_PROCESSING", "true").lower() == "true"
    device = os.getenv("MINERU_DEVICE_MODE", "auto")  # cuda, cpu, or auto (MinerU reads this directly)
    
    # CRITICAL: MinerU reads MINERU_DEVICE_MODE from environment, NOT from RAGAnythingConfig
    # Ensure it's set in the current process environment so MinerU subprocess inherits it
    os.environ["MINERU_DEVICE_MODE"] = device
    
    # Note: HF_TOKEN and HF_HUB_DISABLE_SYMLINKS_WARNING are automatically
    # inherited by MinerU subprocess if set in environment
    
    # Create RAG-Anything configuration (does NOT accept device parameter)
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser=parser,
        parse_method=parse_method,
        enable_image_processing=enable_image,
        enable_table_processing=enable_table,
        enable_equation_processing=enable_equation,
    )
    
    # Define LLM function (xAI Grok wrapper)
    async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return await openai_complete_if_cache(
            "grok-4-fast-reasoning",
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )
    
    # Define vision function (multimodal Grok wrapper)
    async def vision_model_func(prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs):
        if messages:
            return await openai_complete_if_cache(
                "grok-4-fast-reasoning", "", system_prompt=None, history_messages=[],
                messages=messages, api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        elif image_data:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    ],
                }
            ]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            return await openai_complete_if_cache(
                "grok-4-fast-reasoning", "", system_prompt=None, history_messages=[],
                messages=messages,
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            return await llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Use LightRAG's native embedding function directly
    # CRITICAL: Do NOT wrap openai_embed with custom async functions
    # LightRAG's EmbeddingFunc handles async internally
    # max_token_size parameter handles truncation automatically
    
    # Get embedding dimension from environment (flexibility for different models)
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,  # OpenAI text-embedding-3-large limit - LightRAG auto-truncates
        func=lambda texts: openai_embed(texts, model="text-embedding-3-large", api_key=openai_api_key),
    )
    
    # Load entity extraction prompts with hierarchical execution framework
    # Branch 011: 5-Layer Hierarchical Execution Framework (~8,210 lines)
    # Philosophy: Structured execution (WHO/WHAT/WHY) → Domain intelligence (§4.x) → Decision-making context
    # Architecture: Layers 1-4 (execution framework) + Layer 5 (domain knowledge base)
    
    # Layer 1-4: Execution Framework (3,060 lines)
    execution_framework_prompts = [
        load_prompt("extraction/1_system_role"),                         # ~190 lines - WHO/WHAT/WHY
        load_prompt("extraction/2_execution_framework"),                 # ~470 lines - 5-step process with IF-THEN steering
        load_prompt("extraction/3_entity_specifications"),               # ~1,200 lines - 17 entity types
        load_prompt("extraction/4_relationship_patterns"),               # ~1,000 lines - 7 relationship types
    ]
    
    # Layer 5: Domain Knowledge Base (5,350 lines) - §4.x IF-THEN consultation targets
    domain_knowledge_prompts = [
        load_prompt("extraction/domain_knowledge/4.1_far_dfars_comprehensive"),         # ~700 lines
        load_prompt("extraction/domain_knowledge/4.2_evaluation_comprehensive"),        # ~1,000 lines
        load_prompt("extraction/domain_knowledge/4.3_proposal_comprehensive"),          # ~1,100 lines
        load_prompt("extraction/domain_knowledge/4.4_requirement_classification"),      # ~900 lines
        load_prompt("extraction/domain_knowledge/4.5_section_pattern_library"),         # ~850 lines
        load_prompt("extraction/domain_knowledge/4.6_procurement_vehicle_intelligence"), # ~800 lines
    ]
    
    # Concatenate all layers into system prompt
    custom_entity_extraction_prompt = "\n\n---\n\n".join(execution_framework_prompts + domain_knowledge_prompts)
    
    logger.info(f"📚 Loaded 10 prompts in 5-layer hierarchical framework (~8,210 lines total)")
    logger.info(f"   → Layer 1: System Role - WHO/WHAT/WHY (190 lines)")
    logger.info(f"   → Layer 2: Execution Framework - 5-step process with IF-THEN steering (470 lines)")
    logger.info(f"   → Layer 3: Entity Specifications - 17 entity types (1,200 lines)")
    logger.info(f"   → Layer 4: Relationship Patterns - 7 relationship types (1,000 lines)")
    logger.info(f"   → Layer 5: Domain Knowledge Base - §4.1-4.6 IF-THEN targets (5,350 lines)")
    logger.info(f"   → Decision-making framing: Cost impacts, staffing, bid/no-bid throughout")
    logger.info(f"   → Quality standard: 150-250 char entity enrichment with operational context")

    # Initialize RAG-Anything with custom configuration
    # IMPORTANT: LightRAG reads chunk_token_size from environment at import time
    # Don't override via lightrag_kwargs - let it use CHUNK_SIZE from .env
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
            # Chunking configuration comes from environment variables:
            # - CHUNK_SIZE controls chunk_token_size (default: 8192)
            # - CHUNK_OVERLAP_SIZE controls chunk_overlap_token_size (default: 1200)
            # LightRAG reads these at dataclass field initialization time
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
    # COMPATIBILITY FIX: RAG-Anything 1.2.8 + LightRAG 1.4.9.3 doc_status schema
    # ═══════════════════════════════════════════════════════════════════════════════
    # Issue: RAG-Anything writes extra fields that LightRAG 1.4.9.3 doesn't support:
    #        - 'multimodal_processed' (bool) - tracks multimodal processing completion
    #        - 'multimodal_content' (list) - multimodal item metadata
    #        - 'scheme_name' (str) - document scheme identifier
    #
    # RAG-Anything also uses 'handling' status (not in LightRAG's DocStatus enum)
    #
    # Solution: Wrap BOTH write (upsert) and read (get_by_id, get_docs_paginated) to
    #           filter incompatible fields and normalize statuses
    # ═══════════════════════════════════════════════════════════════════════════════
    from lightrag.base import DocStatus
    original_upsert = _rag_anything.lightrag.doc_status.upsert
    original_get_by_id = _rag_anything.lightrag.doc_status.get_by_id
    original_get_docs_paginated = _rag_anything.lightrag.doc_status.get_docs_paginated
    
    # Fields that RAG-Anything writes but LightRAG 1.4.9.3 DocProcessingStatus doesn't accept
    INCOMPATIBLE_FIELDS = {'multimodal_processed', 'multimodal_content', 'scheme_name'}
    
    # Valid LightRAG statuses (from lightrag/base.py DocStatus enum)
    VALID_STATUSES = {
        DocStatus.PENDING.value,      # 'pending'
        DocStatus.PROCESSING.value,   # 'processing'
        DocStatus.PREPROCESSED.value, # 'multimodal_processed'
        DocStatus.PROCESSED.value,    # 'processed'
        DocStatus.FAILED.value,       # 'failed'
    }
    
    def filter_doc_data(doc_data: dict) -> dict:
        """Remove incompatible fields from doc_data"""
        return {k: v for k, v in doc_data.items() if k not in INCOMPATIBLE_FIELDS}
    
    async def filtered_upsert(data: dict):
        """Filter incompatible fields and normalize statuses for LightRAG 1.4.9.3"""
        filtered_data = {}
        for doc_id, doc_data in data.items():
            # Create a copy without incompatible fields
            filtered_doc_data = filter_doc_data(doc_data)
            
            # Normalize RAG-Anything statuses to LightRAG statuses
            if 'status' in filtered_doc_data:
                status = filtered_doc_data['status']
                # Handle both string and enum values
                status_value = status.value if hasattr(status, 'value') else status
                
                # Map RAG-Anything statuses to valid LightRAG statuses
                if status_value == 'handling':
                    filtered_doc_data['status'] = DocStatus.PROCESSING.value
                elif status_value == 'ready':
                    filtered_doc_data['status'] = DocStatus.PENDING.value
                elif status_value not in VALID_STATUSES:
                    logger.warning(f"Unknown status '{status_value}' for doc {doc_id}, mapping to PROCESSING")
                    filtered_doc_data['status'] = DocStatus.PROCESSING.value
            
            filtered_data[doc_id] = filtered_doc_data
        return await original_upsert(filtered_data)
    
    async def filtered_get_by_id(doc_id: str):
        """Get doc_status with incompatible fields filtered"""
        result = await original_get_by_id(doc_id)
        if result and isinstance(result, dict):
            return filter_doc_data(result)
        return result
    
    async def filtered_get_docs_paginated(*args, **kwargs):
        """Get paginated docs with incompatible fields filtered"""
        result = await original_get_docs_paginated(*args, **kwargs)
        if result and isinstance(result, tuple) and len(result) >= 2:
            docs_with_ids, total_count = result[0], result[1]
            # Filter each document's data
            filtered_docs = []
            for doc_id, doc_data in docs_with_ids:
                filtered_docs.append((doc_id, filter_doc_data(doc_data)))
            return (filtered_docs, total_count), *result[2:]
        return result
    
    _rag_anything.lightrag.doc_status.upsert = filtered_upsert
    _rag_anything.lightrag.doc_status.get_by_id = filtered_get_by_id
    _rag_anything.lightrag.doc_status.get_docs_paginated = filtered_get_docs_paginated
    # ═════════════════════════════════════════════════════════════════════════════
    
    # Use print() instead of logger to ensure output visibility during startup
    print("✅ RAG-Anything initialized")
    print(f"   Parser: MinerU ({parse_method}) - multimodal enabled")
    print(f"   Device: {device.upper()} (GPU acceleration {'enabled' if device == 'cuda' else 'disabled'})")
    print(f"   Entity types: {len(entity_types)} specialized types")
    print(f"   LightRAG storages: Ready")
    print(f"   LightRAG version: 1.4.9.3")
    print(f"   Multimodal processing: Using process_document_complete() (separate text/multimodal paths) ✅")
    
    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
