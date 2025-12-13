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
    """Initialize RAG-Anything instance for multimodal document processing.
    
    Configuration:
    - Parser: MinerU (multimodal - images, tables, equations)
    - Entity Types: 18 government contracting types (semantic-first detection)
    - Dual LLM Architecture:
        * Extraction: grok-4-1-fast-non-reasoning (deterministic, structured output)
        * Reasoning: grok-4-1-fast-reasoning (query-time synthesis, 2M context)
    - Embeddings: OpenAI text-embedding-3-large (3072-dim, 8192 token limit)
    - Chunking: 4K tokens (overlap: 600) - Optimized for extraction quality
    
    Architecture Note:
    LightRAG chunks documents into smaller segments. Same chunks go to BOTH:
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DUAL LLM CONFIGURATION (Branch 012 Pattern)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Extraction: Non-reasoning model (deterministic, fast, structured output)
    # Reasoning: Full reasoning model (higher-capacity, query-time synthesis)
    extraction_model_name = os.getenv("EXTRACTION_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-1-fast-non-reasoning"))
    reasoning_model_name = os.getenv("REASONING_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"))
    logger.info(f"🔧 Dual LLM: Extraction={extraction_model_name} | Reasoning={reasoning_model_name}")
    
    # Government contracting entity types (18 specialized types)
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
        
        # Performance standards (QASP, surveillance, metrics)
        "performance_metric",       # Distinct from requirements: accuracy, frequency, response times
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
    
    # Note: All other MinerU variables (MINERU_LANG, MINERU_FORMULA_ENABLE, MINERU_TABLE_MERGE_ENABLE,
    # MINERU_PDF_RENDER_TIMEOUT, CUDA_VISIBLE_DEVICES, HF_TOKEN, HF_HUB_DISABLE_SYMLINKS_WARNING, etc.)
    # are automatically inherited by MinerU subprocess from os.environ after dotenv loads .env
    
    # Create RAG-Anything configuration (does NOT accept device parameter)
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser=parser,
        parse_method=parse_method,
        enable_image_processing=enable_image,
        enable_table_processing=enable_table,
        enable_equation_processing=enable_equation,
    )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # EXTRACTION LLM FUNCTION (deterministic, ingestion-time)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Load extraction prompts from the prompts directory
    entity_extraction_prompts_for_llm = [
        load_prompt("extraction/entity_extraction_prompt"),
        load_prompt("extraction/entity_detection_rules"),
    ]
    custom_entity_extraction_prompt = "\n\n---\n\n".join(entity_extraction_prompts_for_llm)
    
    async def llm_extraction_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        """Extraction LLM: deterministic, low temperature, structured output"""
        temp = float(os.getenv("EXTRACTION_LLM_TEMPERATURE", os.getenv("LLM_MODEL_TEMPERATURE", "0.0")))
        
        # Combine maintained prompts with any caller-provided system prompt
        if system_prompt:
            combined_system_prompt = f"{custom_entity_extraction_prompt}\n\n{system_prompt}"
        else:
            combined_system_prompt = custom_entity_extraction_prompt
        
        if os.getenv("LOG_LLM_CALLS", "false").lower() in ("1", "true", "yes"):
            logger.info(f"[LLM-EXTRACTION] model={extraction_model_name} temperature={temp} prompt_len={len(prompt)}")
        
        return await openai_complete_if_cache(
            extraction_model_name,
            prompt,
            system_prompt=combined_system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            temperature=temp,
            **kwargs,
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REASONING LLM FUNCTION (higher-capacity, query/synthesis-time)
    # ═══════════════════════════════════════════════════════════════════════════════
    async def llm_reasoning_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        """Reasoning LLM: full capacity for query-time synthesis and analysis"""
        temp = float(os.getenv("REASONING_LLM_TEMPERATURE", os.getenv("LLM_MODEL_TEMPERATURE", "0.1")))
        
        if os.getenv("LOG_LLM_CALLS", "false").lower() in ("1", "true", "yes"):
            logger.info(f"[LLM-REASONING] model={reasoning_model_name} temperature={temp} prompt_len={len(prompt)}")
        
        return await openai_complete_if_cache(
            reasoning_model_name,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            temperature=temp,
            **kwargs,
        )
    
    # Wrap extraction function with Pydantic adapter for entity validation
    # Issue #43: Routes extraction calls through PydanticExtractor + schema validation
    # Non-extraction calls pass through to base extraction function
    use_pydantic_extraction = os.getenv("USE_PYDANTIC_TEXT_EXTRACTION", "true").lower() == "true"
    if use_pydantic_extraction:
        from src.extraction.lightrag_llm_adapter import create_extraction_adapter
        llm_model_func = create_extraction_adapter(llm_extraction_func)
        logger.info("✅ Pydantic text extraction adapter ENABLED (USE_PYDANTIC_TEXT_EXTRACTION=true)")
    else:
        llm_model_func = llm_extraction_func
        logger.info("⚠️ Pydantic text extraction adapter DISABLED - using LightRAG native extraction")
    
    # Define vision function (multimodal Grok wrapper - uses reasoning model for image understanding)
    async def vision_model_func(prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs):
        if messages:
            return await openai_complete_if_cache(
                reasoning_model_name, "", system_prompt=None, history_messages=[],
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
                reasoning_model_name, "", system_prompt=None, history_messages=[],
                messages=messages,
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            # Use extraction function for non-multimodal calls
            return await llm_extraction_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Define embedding function with safety truncation (8K chunks can slightly exceed 8192 due to overlap)
    async def safe_embed_func(texts):
        """Truncate texts to 8192 tokens before embedding to handle edge cases"""
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")  # OpenAI tokenizer
        
        truncated_texts = []
        for text in texts:
            tokens = enc.encode(text)
            if len(tokens) > 8192:
                # Truncate to 8192 tokens and decode back to text
                truncated_tokens = tokens[:8192]
                truncated_text = enc.decode(truncated_tokens)
                truncated_texts.append(truncated_text)
            else:
                truncated_texts.append(text)
        
        return await openai_embed(truncated_texts, model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"), api_key=openai_api_key)
    
    # Get embedding dimension from environment (flexibility for different models)
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,  # OpenAI text-embedding-3-large limit
        func=safe_embed_func,
    )
    
    # Initialize RAG-Anything with custom configuration
    # Note: entity_extraction_prompts already loaded above for llm_extraction_func
    # IMPORTANT: LightRAG reads chunk_token_size from environment at import time
    # Don't override via lightrag_kwargs - let it use CHUNK_SIZE from .env
    
    # Parallelization: Controls concurrent chunk extraction within extract_entities()
    # LightRAG uses asyncio.Semaphore(llm_model_max_async) in operate.py extract_entities()
    # RAGAnything uses asyncio.Semaphore(max_parallel_insert) for multimodal item processing
    # MUST be passed via lightrag_kwargs - setting global_args doesn't propagate to RAGAnything!
    max_async = int(os.getenv("MAX_ASYNC", "16"))  # Default 16 workers for parallel extraction
    
    # Build lightrag_kwargs with Neo4j configuration if enabled
    lightrag_kwargs = {
        "addon_params": {
            "entity_types": entity_types,
            "entity_extraction_system_prompt": custom_entity_extraction_prompt,
            # NOTE: entity_extraction_examples is handled at module load time via PROMPTS override
        },
        # CRITICAL: Parallelization settings - must be in lightrag_kwargs to reach LightRAG instance
        # - llm_model_max_async: concurrent LLM calls for text chunk entity extraction
        # - max_parallel_insert: concurrent multimodal item processing (images, tables, equations)
        # - embedding_func_max_async: concurrent embedding calls
        "llm_model_max_async": max_async,
        "max_parallel_insert": max_async,
        "embedding_func_max_async": max_async,
        # Chunking configuration comes from environment variables:
        # - CHUNK_SIZE controls chunk_token_size (default: 8192)
        # - CHUNK_OVERLAP_SIZE controls chunk_overlap_token_size (default: 1200)
        # LightRAG reads these at dataclass field initialization time
    }
    
    # Add Neo4j configuration if enabled (from config.py global_args setup)
    # Note: Neo4j connection details come from environment variables (NEO4J_URI, etc.)
    # LightRAG reads these automatically - we only need to specify graph_storage type
    if hasattr(global_args, 'graph_storage') and global_args.graph_storage == "Neo4JStorage":
        lightrag_kwargs["graph_storage"] = global_args.graph_storage
    
    _rag_anything = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
        lightrag_kwargs=lightrag_kwargs,
    )
    
    # CRITICAL: Ensure LightRAG is initialized BEFORE any document processing
    # This is required because process_document_complete_lightrag_api() accesses
    # self.lightrag.doc_status BEFORE calling _ensure_lightrag_initialized()
    result = await _rag_anything._ensure_lightrag_initialized()
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Failed to initialize LightRAG: {error_msg}")
        raise RuntimeError(f"LightRAG initialization failed: {error_msg}")
    
    # CRITICAL: Disable LightRAG's hardcoded fictional examples to prevent ontology contamination
    # LightRAG always uses PROMPTS["entity_extraction_examples"] (does NOT check addon_params)
    # These examples contain Alex/Taylor/Jordan with conflicting entity types (person, equipment)
    # that contaminate our government contracting ontology (requirement, organization, etc.)
    from lightrag.prompt import PROMPTS
    PROMPTS["entity_extraction_examples"] = []  # Empty list = no examples injected
    logger.info("✅ Disabled LightRAG's fictional example entities (prevents ontology contamination)")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Startup Configuration Summary
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # ANSI color codes
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    logger.info("")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{BOLD}{MAGENTA}🎯 CONFIGURATION{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{GREEN}Dual LLM:{RESET} Extraction={BOLD}{extraction_model_name}{RESET} | Reasoning={BOLD}{reasoning_model_name}{RESET}")
    logger.info(f"{GREEN}Entity Types:{RESET} {BOLD}{len(entity_types)}{RESET} specialized (organization, requirement, evaluation_factor, etc.)")
    logger.info(f"{GREEN}Parser:{RESET} {BOLD}MinerU 2.6.4{RESET} | Device: {BOLD}{GREEN if device == 'cuda' else YELLOW}{device.upper()}{RESET} | Method: {parse_method.upper()}")
    logger.info(f"{GREEN}Parallelization:{RESET} {BOLD}{GREEN}{max_async}{RESET} concurrent (text chunks + multimodal items)")
    logger.info(f"{GREEN}Multimodal:{RESET} Images, Tables, Equations {BOLD}{GREEN}ENABLED{RESET}")
    logger.info(f"{GREEN}Advanced:{RESET} Formula Recognition, Table Merge {BOLD}{GREEN}ENABLED{RESET} | Timeout: {YELLOW}600s{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")
    
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
    
    # ═════════════════════════════════════════════════════════════════════════════
    # QUERY DEFAULT OVERRIDE: Ensure queries use the reasoning LLM by default
    # ═════════════════════════════════════════════════════════════════════════════
    # - Wrap the LightRAG instance's aquery method at the instance level
    # - If a QueryParam is provided with a model_func, respect it
    # - Otherwise inject llm_reasoning_func as the model_func for query-time
    # This is critical: extraction uses non-reasoning model, queries need reasoning!
    from lightrag.base import QueryParam
    
    original_aquery = _rag_anything.lightrag.aquery
    
    async def wrapped_aquery(query: str, param: QueryParam = None, **kwargs):
        """Wrap aquery to inject reasoning LLM for query-time synthesis"""
        # If user passed param explicitly, use it; otherwise create from kwargs
        if param is None:
            param = QueryParam(**kwargs)
        
        # If no model_func specified on the QueryParam, set to reasoning callable
        if getattr(param, "model_func", None) is None:
            param.model_func = llm_reasoning_func
        
        return await original_aquery(query, param=param)
    
    _rag_anything.lightrag.aquery = wrapped_aquery
    logger.info("✅ Query wrapper installed: queries use REASONING_LLM_NAME")
    # ═════════════════════════════════════════════════════════════════════════════
    
    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
