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

        # Ensure max_tokens is always set — without it the API falls back to the model's
        # conservative default (~4K for grok-4-1-fast-non-reasoning), which truncates
        # large PWS chunks mid-output, resulting in 0 relationships extracted.
        # Exception: structured output calls (response_format present) are small JSON
        # responses — keyword extraction only needs ~200 tokens. Passing 128k causes
        # HTTP 500 on grok-4-1 endpoints for structured format requests.
        # Force-assign (not setdefault) so we override any max_tokens LightRAG passes in.
        if 'response_format' in kwargs:
            kwargs['max_tokens'] = 4096
        else:
            kwargs.setdefault('max_tokens', settings.llm_max_output_tokens)

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
            kwargs.setdefault('max_tokens', settings.llm_max_output_tokens)
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
            kwargs.setdefault('max_tokens', settings.llm_max_output_tokens)
            return await openai_complete_if_cache(
                extraction_model, "", system_prompt=None, history_messages=[],
                messages=messages,
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            # Use base function (which auto-routes based on task)
            return await base_llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Embedding function: use LightRAG's native openai_embed with built-in truncation
    # LightRAG 1.4.13 openai_embed.func accepts max_token_size for auto-truncation.
    # Use .func (unwrapped) to avoid @wrap_embedding_func_with_attrs dimension mismatch
    # when using text-embedding-3-large (3072 dims) vs default text-embedding-3-small (1536).
    from functools import partial
    embed_impl = getattr(openai_embed, "func", openai_embed)
    embed_fn = partial(
        embed_impl,
        model=settings.embedding_model,
        api_key=openai_api_key,
        max_token_size=8192,
    )

    embedding_dim = settings.embedding_dim

    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,
        func=embed_fn,
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
    # Register GovConProcessingCallback with RAG-Anything's callback system
    # ═══════════════════════════════════════════════════════════════════════════════
    from src.server.routes import get_processing_callback
    
    processing_callback = get_processing_callback()
    processing_callback.set_llm_func(llm_model_func_wrapped)
    _rag_anything.callback_manager.register(processing_callback)
    logger.info("✅ GovConProcessingCallback registered with RAG-Anything callback_manager")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CRITICAL FIX: Extend VDB meta_fields to preserve entity_type and description
    # ═══════════════════════════════════════════════════════════════════════════════
    # LightRAG 1.4.13 stores entity_type/description in VDB data (operate.py line 1153)
    # but lightrag.py line 720 meta_fields = {entity_name, source_id, content, file_path}
    # doesn't include them. nano_vector_db filters on meta_fields during upsert (line 112),
    # so entity_type/description get stripped without this extension.
    # TODO: Submit PR upstream to add entity_type/description to default meta_fields.
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
    # Register GovCon multimodal prompts via RAGAnything's prompt registry (Branch #072)
    # ═══════════════════════════════════════════════════════════════════════════════
    # RAGAnything 1.2.10 introduced register_prompt_language() / set_prompt_language()
    # (GitHub issue #85 — prompt language support). This allows atomic, thread-safe
    # replacement of all multimodal analysis prompts without subclassing processors.
    #
    # We register a "govcon" language that overrides TABLE/IMAGE/EQUATION system prompts
    # and the processing prompts used by TableModalProcessor, ImageModalProcessor, and
    # EquationModalProcessor. Native library processors then use these govcon prompts
    # automatically — no custom processor subclass required.
    # ═══════════════════════════════════════════════════════════════════════════════
    from raganything.prompt_manager import register_prompt_language, set_prompt_language
    from prompts.multimodal.govcon_multimodal_prompts import GOVCON_MULTIMODAL_PROMPTS

    register_prompt_language("govcon", GOVCON_MULTIMODAL_PROMPTS)
    set_prompt_language("govcon")
    logger.info(f"✅ Registered and activated 'govcon' prompt language ({len(GOVCON_MULTIMODAL_PROMPTS)} prompt overrides)")
    logger.info("   - TABLE_ANALYSIS_SYSTEM: federal acquisition analyst + workload/CLIN/CDRL focus")
    logger.info("   - table_prompt(_with_context): multi-page continuation detection, govcon directives")
    logger.info("   - IMAGE_ANALYSIS_SYSTEM: org charts, facility layouts, CDRL hierarchies")
    logger.info("   - vision_prompt(_with_context): all visible text + contractual element extraction")
    logger.info("   - EQUATION prompts: performance formulas, incentive calculations")
    logger.info("   - QUERY_TABLE/IMAGE prompts: govcon analyst framing for query-time VLM")

    # ═══════════════════════════════════════════════════════════════════════════════
    # Register library-native modal processors (TableModalProcessor etc.)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Now that govcon prompts are active, the library's native processors use them
    # automatically. No custom subclass needed — GovconMultimodalProcessor removed.
    #
    # Native processor benefits over custom subclass:
    # - Structured JSON response → named entity (not generic "table_p53")
    # - separate entity_info.summary → richer VDB embedding
    # - _parse_table_response / _parse_response fallback handling
    # - context_extractor wired via BaseModalProcessor._get_context_for_item()
    # ═══════════════════════════════════════════════════════════════════════════════
    from raganything.modalprocessors import (
        TableModalProcessor,
        ImageModalProcessor,
        EquationModalProcessor,
    )

    # Get the context_extractor that RAGAnything created during _ensure_lightrag_initialized()
    context_extractor = _rag_anything.context_extractor
    if context_extractor:
        logger.info(f"✅ Context extractor available: window={context_extractor.config.context_window}, mode={context_extractor.config.context_mode}")
    else:
        logger.warning("⚠️ Context extractor not available - tables will be processed without section context")

    _rag_anything.modal_processors["table"] = TableModalProcessor(
        _rag_anything.lightrag, llm_model_func_wrapped, context_extractor
    )
    _rag_anything.modal_processors["image"] = ImageModalProcessor(
        _rag_anything.lightrag, vision_model_func, context_extractor
    )
    _rag_anything.modal_processors["equation"] = EquationModalProcessor(
        _rag_anything.lightrag, llm_model_func_wrapped, context_extractor
    )

    logger.info("✅ Native RAGAnything modal processors registered with govcon prompts")
    logger.info("   table    → TableModalProcessor    (govcon TABLE_ANALYSIS_SYSTEM + table_prompt)")
    logger.info("   image    → ImageModalProcessor    (govcon IMAGE_ANALYSIS_SYSTEM + vision_prompt)")
    logger.info("   equation → EquationModalProcessor (govcon EQUATION_ANALYSIS_SYSTEM + equation_prompt)")
    
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
