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

    # NOTE: LLM_TIMEOUT is now set in app.py BEFORE LightRAG imports.
    # LightRAG reads LLM_TIMEOUT at class definition time (dataclass field default),
    # so it must be set before import, not here. See app.py for the fix.
    # Current setting: LLM_TIMEOUT=300 → Worker timeout ~600s
    
    # Government contracting entity types (EXACTLY 18 ontology types)
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

        # Performance standards
        "performance_metric",
    ]
    
    # MinerU configuration: fixed defaults (no feature flags).
    parser = "mineru"
    parse_method = "auto"
    enable_image = True
    enable_table = True
    enable_equation = True
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
    
    # Define base LLM function (xAI Grok wrapper)
    async def base_llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return await openai_complete_if_cache(
            os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )
    
    # Wrap with Pydantic extraction adapter for entity validation.
    # This project treats schema-enforced extraction as mandatory (no feature flags).
    from src.extraction.lightrag_llm_adapter import create_extraction_adapter
    llm_model_func = create_extraction_adapter(base_llm_model_func)
    logger.info("✅ Pydantic text extraction adapter enabled (schema-enforced extraction)")
    
    # Define vision function (multimodal Grok wrapper)
    async def vision_model_func(prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs):
        if messages:
            return await openai_complete_if_cache(
                os.getenv("LLM_MODEL", "grok-4-fast-reasoning"), "", system_prompt=None, history_messages=[],
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
                os.getenv("LLM_MODEL", "grok-4-fast-reasoning"), "", system_prompt=None, history_messages=[],
                messages=messages,
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            # Use base function directly for non-multimodal calls (no adapter needed)
            return await base_llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
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
    
    # Load entity extraction prompts with clear separation of concerns
    # Branch 009: Quality-first refactoring (extraction excellence → query excellence)
    # Philosophy: Thorough extraction enables powerful queries (2M context window)
    # Folder structure: prompts/extraction/ (ingestion-time) vs prompts/query/ (query-time)
    entity_extraction_prompts = [
        load_prompt("extraction/entity_extraction_prompt"),      # ~1,450 lines - WHAT to extract (rules, types, examples)
        load_prompt("extraction/entity_detection_rules"),        # ~1,155 lines - HOW to detect (semantic signals, UCF)
    ]
    custom_entity_extraction_prompt = "\n\n---\n\n".join(entity_extraction_prompts)

    # Initialize RAG-Anything with custom configuration
    # IMPORTANT: LightRAG reads chunk_token_size from environment at import time
    # Don't override via lightrag_kwargs - let it use CHUNK_SIZE from .env
    
    # Parallelization: fixed, no runtime feature flags/toggles.
    # (RAGAnything and LightRAG both accept *_max_async settings via lightrag_kwargs.)
    max_async = 16
    
    # Build lightrag_kwargs (keep within library-supported kwargs; avoid custom query overrides)
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
    logger.info(f"{GREEN}Entity Types:{RESET} {BOLD}{len(entity_types)}{RESET} specialized (organization, requirement, evaluation_factor, etc.)")
    logger.info(f"{GREEN}Parser:{RESET} {BOLD}MinerU 2.6.4{RESET} | Device: {BOLD}{GREEN if device == 'cuda' else YELLOW}{device.upper()}{RESET} | Method: {parse_method.upper()}")
    logger.info(f"{GREEN}Parallelization:{RESET} {BOLD}{GREEN}{max_async}{RESET} concurrent (text chunks + multimodal items)")
    logger.info(f"{GREEN}Multimodal:{RESET} Images, Tables, Equations {BOLD}{GREEN}ENABLED{RESET}")
    logger.info(f"{GREEN}Advanced:{RESET} Formula Recognition, Table Merge {BOLD}{GREEN}ENABLED{RESET} | Timeout: {YELLOW}600s{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")

    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
