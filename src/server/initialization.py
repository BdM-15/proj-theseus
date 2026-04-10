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

# Apply MinerU 3.0 compatibility patch (removes -d and --source CLI flags)
from tools.patches.raganything_mineru3_compat import apply_patch as _apply_mineru3_patch
_apply_mineru3_patch()

# V3 unified prompt loaded directly from file - no prompt_loader needed
from src.ontology.schema import VALID_ENTITY_TYPES
from src.core import get_settings

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
    - Chunking: 4K tokens (overlap: ~600) - Multiple focused extraction passes
    
    Architecture Note:
    LightRAG chunks documents at 4096 tokens. Same chunks go to BOTH:
    - LLM entity extraction (multiple focused passes = comprehensive entity coverage)
    - Embedding generation (fits within 8192 token limit, no truncation needed)
    Smaller chunks prevent LLM attention decay that caused 50K chunk extraction failure.
    
    Returns:
        RAGAnything: Configured instance ready for document ingestion
    """
    global _rag_anything
    
    # Get validated settings from centralized config
    settings = get_settings()
    
    # API credentials from centralized config
    xai_api_key = settings.llm_binding_api_key
    xai_base_url = settings.llm_binding_host
    openai_api_key = settings.embedding_binding_api_key
    working_dir = global_args.working_dir
    
    # Government contracting entity types - SINGLE SOURCE OF TRUTH from schema.py
    # This ensures consistency between:
    # - LightRAG/RAG-Anything extraction (this list)
    # - Semantic post-processing validation (schema.py InferredRelationship)
    # - Post-processing (schema.py VALID_ENTITY_TYPES)
    entity_types = list(VALID_ENTITY_TYPES)
    logger.info(f"📋 Loaded {len(entity_types)} entity types from schema.py")
    
    # MinerU configuration from centralized settings
    parser = settings.parser
    parse_method = settings.parse_method
    enable_image = settings.enable_image_processing
    enable_table = settings.enable_table_processing
    enable_equation = settings.enable_equation_processing
    device = settings.mineru_device_mode
    
    # CRITICAL: MinerU reads MINERU_DEVICE_MODE from environment, NOT from RAGAnythingConfig
    # Ensure it's set in the current process environment so MinerU subprocess inherits it
    # NOTE: MinerU 3.0 removed the -d CLI flag; device is managed internally by the API service.
    # The environment variable is still read by MinerU's internal configuration.
    os.environ["MINERU_DEVICE_MODE"] = device
    
    # CRITICAL: Disable MinerU cross-page table merging (Issue #65, MinerU #4311)
    # When tables span multiple pages, MinerU's merge logic keeps only the first page's
    # img_path and table_body, resulting in EMPTY data for continuation pages.
    # Per MinerU maintainer @myhloli: Set MINERU_TABLE_MERGE_ENABLE=0 to preserve per-page data.
    # Our context-aware processing + semantic inference will connect related tables via CHILD_OF.
    table_merge_value = "1" if settings.mineru_table_merge_enable else "0"
    os.environ["MINERU_TABLE_MERGE_ENABLE"] = table_merge_value
    logger.info(f"✅ MinerU table merge: {'ENABLED' if settings.mineru_table_merge_enable else 'DISABLED (preserves per-page data)'}")
    
    # Note: All other MinerU variables (MINERU_LANG, MINERU_FORMULA_ENABLE,
    # MINERU_PDF_RENDER_TIMEOUT, CUDA_VISIBLE_DEVICES, HF_TOKEN, HF_HUB_DISABLE_SYMLINKS_WARNING, etc.)
    # are automatically inherited by MinerU subprocess from os.environ after dotenv loads .env
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # RAG-ANYTHING CONTEXT-AWARE PROCESSING (Issue #62)
    # ═══════════════════════════════════════════════════════════════════════════════
    # When processing multimodal content (tables, images, equations), RAG-Anything
    # can extract surrounding page context to provide section awareness.
    #
    # Without context: Table on p53 → "table_p53" (isolated node, no relationships)
    # With context: Table on p53 → "AL JABER AIR BASE workload table from Appendix H"
    #              → CHILD_OF relationship to APPENDIX_H_WORKLOAD_DATA
    #
    # This enables Algorithm 7 (CDRL/Section patterns) to infer parent relationships.
    #
    # IMPORTANT: Context settings are read by RAGAnythingConfig from env vars:
    #   CONTEXT_WINDOW, CONTEXT_MODE, CONTENT_FORMAT, MAX_CONTEXT_TOKENS,
    #   INCLUDE_HEADERS, INCLUDE_CAPTIONS, CONTEXT_FILTER_CONTENT_TYPES
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Create RAG-Anything configuration - it reads context settings from env vars automatically
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser=parser,
        parse_method=parse_method,
        enable_image_processing=enable_image,
        enable_table_processing=enable_table,
        enable_equation_processing=enable_equation,
        # Context settings are automatically loaded from env vars by RAGAnythingConfig
    )
    
    # Log context-aware processing configuration (read from config after env var loading)
    logger.info(f"✅ RAG-Anything context-aware processing: {'ENABLED' if config.context_window > 0 else 'DISABLED'}")
    logger.info(f"   - context_window: {config.context_window} pages")
    logger.info(f"   - context_mode: {config.context_mode}")
    logger.info(f"   - content_format: {config.content_format}")
    logger.info(f"   - max_context_tokens: {config.max_context_tokens}")
    logger.info(f"   - include_headers: {config.include_headers}")
    logger.info(f"   - include_captions: {config.include_captions}")
    logger.info(f"   - context_filter_content_types: {getattr(config, 'context_filter_content_types', ['text'])}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DUAL-MODEL LLM ROUTING (Extraction vs Query)
    # ═══════════════════════════════════════════════════════════════════════════════
    # LightRAG recommends non-reasoning models for extraction because:
    # - Extraction needs literal format compliance (exact delimiters)
    # - Reasoning models "over-interpret" → entity names become sentences
    # - Hallucination rate: 12% (reasoning) vs 4% (non-reasoning)
    #
    # Query needs reasoning models because:
    # - Users ask nuanced questions requiring synthesis
    # - Need to draw conclusions from knowledge graph
    # - Provide contextual explanations
    #
    # Detection: Extraction prompts contain "tuple_delimiter" or entity extraction markers
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Model configuration from centralized settings
    extraction_model = settings.extraction_llm_name
    reasoning_model = settings.reasoning_llm_name
    
    # Extraction detection markers (from LightRAG prompts)
    EXTRACTION_MARKERS = [
        "tuple_delimiter",           # Core extraction delimiter
        "entity_types",              # Entity type specification
        "completion_delimiter",      # Extraction completion marker
        "record_delimiter",          # Record separator
        "-Real Data-",               # Extraction input marker
        "extract entities",          # Direct extraction instruction
    ]
    
    def is_extraction_task(prompt: str, system_prompt: str) -> bool:
        """Detect if this is an extraction task vs query task"""
        combined = f"{system_prompt or ''} {prompt or ''}".lower()
        return any(marker.lower() in combined for marker in EXTRACTION_MARKERS)
    
    async def base_llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        # Route to appropriate model based on task type
        if is_extraction_task(prompt, system_prompt):
            model = extraction_model
        else:
            model = reasoning_model
        
        return await openai_complete_if_cache(
            model,
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Native LightRAG Extraction with Output Sanitization (Issue #56)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Using LightRAG's native tuple-delimited extraction format with a lightweight
    # sanitization wrapper that fixes common LLM malformation patterns:
    # - #|requirement → requirement (hash prefix from delimiter leakage)
    # - Extra pipes in descriptions causing field count errors
    # 
    # This approach preserves native LightRAG performance while preventing entity drops.
    # Our GovCon ontology is injected via addon_params and PROMPTS override.
    # ═══════════════════════════════════════════════════════════════════════════════
    from src.extraction.output_sanitizer import create_sanitizing_wrapper
    
    llm_model_func = create_sanitizing_wrapper(base_llm_model_func)
    logger.info("✅ Using native LightRAG extraction with output sanitization (Issue #56)")
    logger.info(f"✅ DUAL-MODEL routing enabled:")
    logger.info(f"   Extraction: {extraction_model} (non-reasoning for literal format compliance)")
    logger.info(f"   Query:      {reasoning_model} (reasoning for nuanced answers)")
    logger.info(f"   Sanitizer:  Fixes malformed delimiters (#|type → type)")
    
    # Define vision function (multimodal Grok wrapper)
    # NOTE: Vision/multimodal processing is extraction (generating descriptions for tables/images)
    #       so it uses the extraction model for literal format compliance
    async def vision_model_func(prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs):
        if messages:
            return await openai_complete_if_cache(
                extraction_model, "", system_prompt=None, history_messages=[],
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
                extraction_model, "", system_prompt=None, history_messages=[],
                messages=messages,
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            # Use base function (which auto-routes based on task)
            return await base_llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Define embedding function with safety truncation (chunks can slightly exceed 8192 embedding limit)
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
        
        # IMPORTANT: lightrag's `openai_embed` symbol is wrapped with default attrs
        # (embedding_dim=1536 for text-embedding-3-small). When our `.env` uses
        # `text-embedding-3-large` (3072 dims) and dimensions are not explicitly sent,
        # the wrapper can mis-validate and raise a "Vector count mismatch".
        #
        # Use the unwrapped function (`openai_embed.func`) to avoid that mismatch.
        embed_impl = getattr(openai_embed, "func", openai_embed)
        return await embed_impl(
            truncated_texts,
            model=settings.embedding_model,
            api_key=openai_api_key,
        )
    
    # Get embedding dimension from centralized settings
    embedding_dim = settings.embedding_dim
    
    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,  # OpenAI text-embedding-3-large limit
        func=safe_embed_func,
    )
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Prompt Configuration (govcon_prompt.py architecture)
    # ═══════════════════════════════════════════════════════════════════════════════
    # All prompts are now centralized in prompts/govcon_prompt.py:
    # - entity_extraction_system_prompt: GovCon extraction instructions
    # - entity_extraction_examples: 7 GovCon-specific examples (L↔M, requirements, clauses, etc.)
    # - summarize_entity_descriptions: Preserve quantitative details
    # - rag_response / naive_rag_response: Shipley lifecycle support
    # - keywords_extraction: GovCon query understanding
    # 
    # Prompts are applied via PROMPTS.update(GOVCON_PROMPTS) after RAG-Anything init
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Build lightrag_kwargs with configuration
    # LLM timeout configuration for complex chunks (360s default was insufficient for chunk 8)
    llm_timeout = settings.llm_timeout
    
    lightrag_kwargs = {
        "addon_params": {
            "entity_types": entity_types,
            # NOTE: entity_extraction_system_prompt and examples are now handled via 
            # PROMPTS.update(GOVCON_PROMPTS) after RAG-Anything initialization
            "language": "English",
        },
        # Chunking configuration comes from environment variables:
        # - CHUNK_SIZE controls chunk_token_size (default: 4096)
        # - CHUNK_OVERLAP_SIZE controls chunk_overlap_token_size (default: 600)
        # LightRAG reads these at dataclass field initialization time
        
        # LLM timeout: default 180s causes Worker timeout (2×=360s) failures on complex chunks
        # Increased to 600s (10 min) to handle extraction from dense requirement tables
        "default_llm_timeout": llm_timeout,
    }
    
    # Add Neo4j configuration if enabled (from config.py global_args setup)
    # Note: Neo4j connection details come from environment variables (NEO4J_URI, etc.)
    # LightRAG reads these automatically - we only need to specify graph_storage type
    if hasattr(global_args, 'graph_storage') and global_args.graph_storage == "Neo4JStorage":
        lightrag_kwargs["graph_storage"] = global_args.graph_storage
    
    # LLM function ready for RAG-Anything (no adapter wrapping needed)
    llm_model_func_wrapped = llm_model_func
    
    _rag_anything = RAGAnything(
        config=config,
        llm_model_func=llm_model_func_wrapped,
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CRITICAL FIX: Extend VDB meta_fields to preserve entity_type and description
    # ═══════════════════════════════════════════════════════════════════════════════
    # LightRAG's default meta_fields only includes: {entity_name, source_id, content, file_path}
    # Our GovCon ontology requires entity_type and description for proper filtering and retrieval.
    # Without this fix, entity_type and description are stripped during VDB storage!
    # 
    # Root cause: lightrag.py line 598 hardcodes meta_fields without entity_type/description
    # Fix: Extend meta_fields AFTER LightRAG initialization but BEFORE document processing
    # ═══════════════════════════════════════════════════════════════════════════════
    lightrag_instance = _rag_anything.lightrag
    
    # Extend entities VDB meta_fields
    original_entity_meta = lightrag_instance.entities_vdb.meta_fields
    extended_entity_meta = original_entity_meta | {"entity_type", "description"}
    lightrag_instance.entities_vdb.meta_fields = extended_entity_meta
    logger.info(f"✅ Extended entities_vdb.meta_fields: {extended_entity_meta}")
    
    # Extend relationships VDB meta_fields (for keywords and description)
    original_rel_meta = lightrag_instance.relationships_vdb.meta_fields
    extended_rel_meta = original_rel_meta | {"keywords", "description"}
    lightrag_instance.relationships_vdb.meta_fields = extended_rel_meta
    logger.info(f"✅ Extended relationships_vdb.meta_fields: {extended_rel_meta}")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Register GovconMultimodalProcessor for tables/images/equations
    # ═══════════════════════════════════════════════════════════════════════════════
    # Issue #54 Architecture (Back to Basics - Native LightRAG):
    # 
    # MULTIMODAL Flow:
    # 1. MinerU: Parses table images → textualized HTML (table_body)
    # 2. GovconProcessor: Generates govcon-focused text description
    # 3. LightRAG: Native tuple-delimited extraction
    # 
    # TEXT Flow:
    # 1. RAG-Anything: Chunks text content
    # 2. LightRAG: Native extraction with our entity_types + injected domain knowledge
    # 
    # Key Points:
    # - Native LightRAG tuple-delimited format: entity<|#|>name<|#|>type<|#|>desc
    # - Our ontology injected via PROMPTS["entity_extraction_system_prompt"]
    # - Post-processing Step 2 cleans up any malformed entity types
    # ═══════════════════════════════════════════════════════════════════════════════
    from src.processors import GovconMultimodalProcessor
    
    # Get the context_extractor that RAGAnything created during _ensure_lightrag_initialized()
    # This is properly configured with the context settings from RAGAnythingConfig
    context_extractor = _rag_anything.context_extractor
    if context_extractor:
        logger.info(f"✅ Context extractor available: window={context_extractor.config.context_window}, mode={context_extractor.config.context_mode}")
    else:
        logger.warning("⚠️ Context extractor not available - tables will be processed without section context")
    
    govcon_processor = GovconMultimodalProcessor(
        lightrag=_rag_anything.lightrag,
        modal_caption_func=llm_model_func_wrapped,
        context_extractor=context_extractor
    )
    
    # Override RAG-Anything's default processors with our ontology-aware processor
    _rag_anything.modal_processors["table"] = govcon_processor
    _rag_anything.modal_processors["image"] = govcon_processor
    _rag_anything.modal_processors["equation"] = govcon_processor
    
    logger.info("✅ GovconMultimodalProcessor registered (Issue #54 - Native LightRAG)")
    logger.info("   - MinerU: table images → textualized HTML")
    logger.info("   - Processor: Generates govcon-focused text descriptions")
    logger.info("   - LightRAG: Native tuple-delimited entity extraction")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CRITICAL: REPLACE LightRAG's ENTIRE prompt system with GovCon versions
    # ═══════════════════════════════════════════════════════════════════════════════
    # LightRAG uses multiple prompts that work together:
    # - entity_extraction_system_prompt: Extract entities/relationships
    # - entity_extraction_examples: GovCon-specific extraction examples
    # - summarize_entity_descriptions: Merge duplicate entities
    # - rag_response: Answer queries using KG + documents
    # - naive_rag_response: Answer queries using documents only
    # - keywords_extraction: Parse user queries for retrieval
    # - fail_response: When no context found
    # 
    # ALL prompts are customized for government contracting / Shipley methodology
    # ═══════════════════════════════════════════════════════════════════════════════
    from lightrag.prompt import PROMPTS
    
    # Import comprehensive GovCon prompts (govcon_prompt.py - Issue #54 architecture)
    # This module contains all LightRAG-compatible prompts with GovCon domain intelligence
    from prompts.govcon_prompt import GOVCON_PROMPTS
    
    # FULL REPLACEMENT: Apply ALL GovCon prompt overrides
    # This replaces: extraction prompts, examples, summarization, RAG responses, keywords, fail_response
    PROMPTS.update(GOVCON_PROMPTS)
    
    # Log full domain intelligence stats
    extraction_prompt = GOVCON_PROMPTS.get('entity_extraction_system_prompt', '')
    extraction_chars = len(extraction_prompt)
    extraction_lines = extraction_prompt.count('\n')
    
    logger.info("✅ REPLACED LightRAG prompt system with FULL GovCon domain intelligence")
    logger.info(f"   Extraction prompt: {extraction_chars:,} chars (~{extraction_chars//4:,} tokens), {extraction_lines:,} lines")
    logger.info(f"   Source: govcon_lightrag_native.txt (Parts A-L)")
    logger.info(f"   Domain Intelligence:")
    logger.info(f"     • 8 Shipley user personas (Capture, Proposal, Cost, Contracts, etc.)")
    logger.info(f"     • 18 GovCon entity types with metadata requirements")
    logger.info(f"     • 50+ relationship inference rules (L↔M, clause clustering, etc.)")
    logger.info(f"     • 12 annotated RFP examples (requirements, clauses, CDRLs, etc.)")
    logger.info(f"     • Quantitative preservation rules for BOE development")
    logger.info(f"     • Decision tree for ambiguous cases")
    logger.info(f"   Keywords examples: {len(GOVCON_PROMPTS.get('keywords_extraction_examples', []))} GovCon-specific")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Startup Configuration Summary
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # Use centralized color codes
    from src.utils.logging_config import Colors
    c = Colors
    
    logger.info("")
    logger.info(f"{c.CYAN}{'═' * 80}{c.RESET}")
    logger.info(f"{c.BOLD}{c.MAGENTA}🎯 CONFIGURATION{c.RESET}")
    logger.info(f"{c.CYAN}{'═' * 80}{c.RESET}")
    logger.info(f"{c.GREEN}Entity Types:{c.RESET} {c.BOLD}{len(entity_types)}{c.RESET} specialized (organization, requirement, evaluation_factor, etc.)")
    try:
        from importlib import metadata as _metadata
        mineru_version = _metadata.version("mineru")
    except Exception:
        mineru_version = "unknown"
    logger.info(
        f"{c.GREEN}Parser:{c.RESET} {c.BOLD}MinerU {mineru_version}{c.RESET} | Device: {c.BOLD}{c.GREEN if device == 'cuda' else c.YELLOW}{device.upper()}{c.RESET} | Method: {parse_method.upper()}"
    )
    logger.info(f"{c.GREEN}Multimodal:{c.RESET} Images, Tables, Equations {c.BOLD}{c.GREEN}ENABLED{c.RESET}")
    logger.info(f"{c.GREEN}Advanced:{c.RESET} Formula Recognition, Table Merge {c.BOLD}{c.GREEN}ENABLED{c.RESET} | Timeout: {c.YELLOW}600s{c.RESET}")
    logger.info(f"{c.CYAN}{'═' * 80}{c.RESET}")
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # MinerU Model Warmup - Download VLM model at startup, not during processing
    # ═══════════════════════════════════════════════════════════════════════════════
    # MinerU 2.7.0 uses a VLM model (MinerU2.5-2509-1.2B) that must be downloaded
    # from HuggingFace Hub. Without warmup, this happens on first document upload,
    # causing unexpected delays and potential timeout/permission errors.
    #
    # The warmup runs `mineru --version` which triggers model download without
    # parsing any document. HF_HUB_DISABLE_SYMLINKS=1 in .env prevents Windows
    # symlink permission errors during download.
    # ═══════════════════════════════════════════════════════════════════════════════
    await warmup_mineru_model()
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # DOMAIN ONTOLOGY BOOTSTRAP (Issue #68)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pre-load curated GovCon domain knowledge into the workspace. This provides:
    # - Zero-document queries: "What is a Color Team review?" works immediately
    # - Enhanced retrieval: Domain concepts (Shipley, FAR, BOE) connect to extracted entities
    # - Evaluation grounding: Rating scales, compliance patterns available for analysis
    #
    # Bootstrap happens ONCE per workspace (marker file prevents re-run).
    # Set AUTO_BOOTSTRAP_ONTOLOGY=False in .env to disable for testing.
    # ═══════════════════════════════════════════════════════════════════════════════
    if settings.auto_bootstrap_ontology:
        try:
            from src.ontology.bootstrap import bootstrap_govcon_ontology
            
            # CRITICAL: Use workspace-specific path, not base working_dir
            # working_dir is ./rag_storage, but workspace data is in ./rag_storage/{workspace}
            workspace_path = os.path.join(working_dir, settings.workspace)
            
            bootstrap_result = await bootstrap_govcon_ontology(
                lightrag=_rag_anything.lightrag,
                working_dir=workspace_path,
                force=settings.ontology_bootstrap_force,
            )
            
            if bootstrap_result["status"] == "success":
                logger.info(f"✅ GovCon ontology bootstrapped: {bootstrap_result['entities_added']} entities, "
                          f"{bootstrap_result['relationships_added']} relationships")
            elif bootstrap_result["status"] == "already_bootstrapped":
                logger.info(f"📚 GovCon ontology already bootstrapped ({bootstrap_result['bootstrapped_at']})")
            else:
                logger.warning(f"⚠️ Ontology bootstrap: {bootstrap_result.get('error', 'unknown issue')}")
                
        except Exception as e:
            # Non-fatal - ontology is enhancement, not required for core functionality
            logger.warning(f"⚠️ Ontology bootstrap failed: {e} - continuing without domain knowledge")
    else:
        logger.info("📚 Ontology auto-bootstrap DISABLED (AUTO_BOOTSTRAP_ONTOLOGY=False)")
    
    return _rag_anything


async def warmup_mineru_model():
    """Pre-download MinerU models at startup to avoid delays and symlink issues.
    
    MinerU 3.0 launches a subprocess API service that calls snapshot_download
    internally. On Windows without Developer Mode, symlink creation fails
    (WinError 1314). By pre-downloading both models in our main process with
    HF_HUB_DISABLE_SYMLINKS=1, the subprocess finds cached real files and
    skips the download entirely.
    """
    import asyncio
    import os
    
    logger.info("🔄 Warming up MinerU models (downloading if needed)...")
    
    try:
        # CRITICAL: Set env vars BEFORE importing huggingface_hub
        # These must be set before the HF library reads them
        os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"
        os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
        
        from huggingface_hub import snapshot_download
        
        # 1. Pipeline backend model (layout detection, OCR, table recognition)
        # Required by MinerU 3.0 "pipeline" backend for PDF processing
        pipeline_path = await asyncio.to_thread(
            snapshot_download,
            "opendatalab/PDF-Extract-Kit-1.0"
        )
        logger.info(f"✅ MinerU pipeline model ready: {pipeline_path}")
        
        # 2. VLM model (vision-language for image/table understanding)
        vlm_path = await asyncio.to_thread(
            snapshot_download,
            "opendatalab/MinerU2.5-2509-1.2B"
        )
        logger.info(f"✅ MinerU VLM model ready: {vlm_path}")
        
    except Exception as e:
        # Non-fatal - MinerU will attempt download on first document
        logger.warning(f"⚠️ MinerU warmup: {e} - will download on first document")


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
