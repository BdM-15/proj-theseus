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
from src.ontology.schema import VALID_ENTITY_TYPES
from src.extraction.lightrag_llm_adapter import create_extraction_adapter

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
    
    # Government contracting entity types - SINGLE SOURCE OF TRUTH from schema.py
    # This ensures consistency between:
    # - LightRAG/RAG-Anything extraction (this list)
    # - Pydantic validation (schema.py EntityType)
    # - Post-processing (schema.py VALID_ENTITY_TYPES)
    entity_types = list(VALID_ENTITY_TYPES)
    logger.info(f"📋 Loaded {len(entity_types)} entity types from schema.py")
    
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
    
    # Define BASE LLM function (xAI Grok wrapper) - Branch 040 pattern (no stream override)
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pydantic Extraction Adapter - NO FALLBACK
    # ═══════════════════════════════════════════════════════════════════════════════
    # Wraps extraction calls to use our full 150KB ontology prompts + Pydantic validation.
    # If validation fails, chunk is SKIPPED - no half measures.
    use_pydantic_extraction = os.getenv("USE_PYDANTIC_EXTRACTION", "true").lower() == "true"
    
    if use_pydantic_extraction:
        from src.extraction.lightrag_llm_adapter import create_extraction_adapter
        llm_model_func = create_extraction_adapter(base_llm_model_func)
        logger.info("✅ Pydantic extraction adapter ENABLED (validated data or skip)")
    else:
        llm_model_func = base_llm_model_func
        logger.info("⚠️ Pydantic extraction adapter DISABLED")
    
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
            # Use base function for vision (not extraction adapter)
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
    
    # Build lightrag_kwargs with Neo4j configuration if enabled
    lightrag_kwargs = {
        "addon_params": {
            "entity_types": entity_types,
            "entity_extraction_system_prompt": custom_entity_extraction_prompt,
            # NOTE: entity_extraction_examples is handled at module load time via PROMPTS override
        },
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
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Layer 2: Pydantic Extraction Adapter
    # ═══════════════════════════════════════════════════════════════════════════════
    # Wraps LLM function to intercept extraction calls and route through:
    # - JsonExtractor (uses our full 150KB extraction prompt)
    # - Pydantic validation (enforces schema)
    # - Converts JSON → pipe-delimited format for LightRAG
    #
    # Falls back to Layer 1 (domain-enhanced LightRAG prompt) on failure
    # ═══════════════════════════════════════════════════════════════════════════════
    use_pydantic_extraction = os.getenv("USE_PYDANTIC_EXTRACTION", "true").lower() == "true"
    
    if use_pydantic_extraction:
        llm_model_func_wrapped = create_extraction_adapter(llm_model_func)
        logger.info("✅ Layer 2 ENABLED: Pydantic extraction adapter wrapping LLM function")
        logger.info("   - Primary: Full 150KB prompts + Pydantic validation")
        logger.info("   - Fallback: Layer 1 (domain-enhanced LightRAG prompt)")
    else:
        llm_model_func_wrapped = llm_model_func
        logger.info("⚠️ Layer 2 DISABLED: Using Layer 1 only (USE_PYDANTIC_EXTRACTION=false)")
    
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
    # CRITICAL: Override LightRAG's extraction prompt with our govcon domain knowledge
    # ═══════════════════════════════════════════════════════════════════════════════
    # LightRAG ONLY uses addon_params for entity_types list and language.
    # The extraction SYSTEM PROMPT always comes from PROMPTS["entity_extraction_system_prompt"].
    # We must override this directly to inject our domain knowledge.
    from lightrag.prompt import PROMPTS
    
    # Disable fictional examples that contaminate our ontology
    PROMPTS["entity_extraction_examples"] = []
    logger.info("✅ Disabled LightRAG's fictional example entities")
    
    # Build a custom extraction prompt that:
    # 1. Prepends our govcon domain knowledge (entity type definitions, detection rules)
    # 2. Keeps LightRAG's required output format (pipe-delimited)
    # 3. Preserves all required placeholders
    
    govcon_domain_knowledge = f"""---Government Contracting Domain Knowledge---

You are extracting entities from US Government RFP (Request for Proposal) documents.

**ENTITY TYPE DEFINITIONS (18 specialized types):**

1. **requirement** - Contractual obligations with modal verbs (shall, must, will, should, may)
   - CRITICAL: Extract ALL workload drivers: quantities, frequencies, volumes, service rates
   - Example: "service rate of 3 customers per minute" → requirement with workload data
   - Example: "100 times per year" → requirement with frequency data

2. **deliverable** - Items contractor must provide (CDRLs, reports, plans, data items)
   - Look for: DD Form 1423, CDRL references, submission requirements

3. **evaluation_factor** - How proposals will be scored (Section M content)
   - Look for: weights, points, importance levels, rating scales

4. **submission_instruction** - How to format/submit proposals (Section L content)
   - Look for: page limits, font requirements, volume structure

5. **performance_metric** - Measurable standards (SLAs, KPIs, thresholds)
   - Look for: percentages, time limits, error rates

6. **clause** - FAR/DFARS regulatory citations
   - Pattern: FAR 52.xxx, DFARS 252.xxx

7. **section** - Document structural elements
8. **document** - Referenced documents, attachments, annexes
9. **organization** - Government agencies, contractors, entities
10. **person** - Roles, positions, personnel categories
11. **equipment** - Physical items, GFE/GFP, materials
12. **program** - Major programs referenced
13. **strategic_theme** - Win themes, discriminators, hot buttons
14. **statement_of_work** - PWS/SOW/SOO content
15. **technology** - Technical systems, software, platforms
16. **concept** - General terms that don't fit other categories
17. **event** - Meetings, milestones, deadlines
18. **location** - Places, facilities, sites

**WORKLOAD EXTRACTION RULES:**
- ALWAYS extract numeric values: quantities, frequencies, volumes
- ALWAYS extract service rates: "X per minute", "Y per hour"
- ALWAYS extract time periods: operating hours, peak times
- ALWAYS extract staffing indicators: personnel counts, shifts
- Include these in the entity_description field

**FALLBACK:** If an entity doesn't clearly fit the above types, use `concept`.

---End Domain Knowledge---

"""
    
    # Get LightRAG's original prompt and prepend our domain knowledge
    original_prompt = PROMPTS.get("entity_extraction_system_prompt", "")
    
    # Replace "Other" with "concept" for fallback
    modified_prompt = original_prompt.replace(
        "classify it as `Other`",
        "classify it as `concept`"
    )
    
    # Prepend our domain knowledge
    PROMPTS["entity_extraction_system_prompt"] = govcon_domain_knowledge + modified_prompt
    
    logger.info("✅ Injected govcon domain knowledge into LightRAG extraction prompt")
    logger.info(f"   Original prompt: {len(original_prompt)} chars")
    logger.info(f"   Enhanced prompt: {len(PROMPTS['entity_extraction_system_prompt'])} chars")
    
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
    
    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
