"""
Server Configuration for RAG-Anything + LightRAG

Configures global_args for LightRAG server with government contracting ontology.
Uses xAI Grok for LLM and OpenAI for embeddings.
"""

# CRITICAL: Load .env BEFORE importing LightRAG modules
# LightRAG's chunk_token_size default: int(os.getenv("CHUNK_SIZE", 1200))
# Must set environment variables before LightRAG classes are defined
import os
from dotenv import load_dotenv
load_dotenv()

# Now safe to import LightRAG
import logging
from lightrag.api.config import global_args
from lightrag.operate import chunking_by_token_size

logger = logging.getLogger(__name__)


def configure_raganything_args():
    """
    Configure global_args for LightRAG server to use with RAG-Anything.
    
    We'll configure the LightRAG server normally, then RAG-Anything will
    wrap the storage/processing with multimodal capabilities.
    """
    # Get API credentials (using RAG-Anything official variable names)
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = os.getenv("WORKING_DIR", "./rag_storage")
    
    # Working directory
    global_args.working_dir = working_dir
    global_args.input_dir = os.getenv("INPUT_DIR", "./inputs/uploaded")
    
    # Server configuration
    global_args.host = os.getenv("HOST", "localhost")
    global_args.port = int(os.getenv("PORT", "9621"))
    
    # LLM Configuration - xAI Grok
    global_args.llm_binding = "openai"
    # Dual-LLM support: default extraction/reasoning split. These env vars allow
    # selecting a deterministic extraction LLM for ingestion and a stronger
    # reasoning LLM for query-time reasoning. If unset, fall back to LLM_MODEL.
    global_args.llm_model_name = os.getenv("LLM_MODEL", os.getenv("EXTRACTION_LLM_NAME", "grok-4-fast-reasoning"))
    global_args.llm_extraction_model_name = os.getenv("EXTRACTION_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-fast-non-reasoning"))
    global_args.llm_reasoning_model_name = os.getenv("REASONING_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-fast-reasoning"))
    global_args.llm_binding_host = xai_base_url
    global_args.llm_api_key = xai_api_key
    
    # Embedding Configuration - OpenAI (MUST use OpenAI endpoint, not xAI!)
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = "text-embedding-3-large"
    global_args.embedding_binding_host = "https://api.openai.com/v1"  # OpenAI endpoint for embeddings
    global_args.embedding_api_key = openai_api_key
    global_args.embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))  # Environment-driven for flexibility
    
    # Government contracting entity types (17 specialized types - consolidated for flexibility)
    # Semantic-first detection: Content determines entity type, not section labels
    # NOTE: LightRAG normalizes to lowercase internally - use lowercase for consistency
    global_args.entity_types = [
        # Core entities
        "organization",
        "concept",
        "event",
        "technology",
        "person",
        "location",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "requirement",
        
        # Structural entities
        "clause",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "section",                  # Stores both structural_label + semantic_type
        "document",                 # References: specs, standards, manuals, regulations, attachments, annexes
        "deliverable",
        
        # Hierarchical program entities
        "program",                  # Major named programs/initiatives (MCPP II, Navy MBOS, DEIP)
        
        # Physical assets and equipment
        "equipment",                # Physical assets: MHE, generators, batteries, GSE, CESE, watercraft, vehicles
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        # (placeholder - semantic detection handled via prompts and Pydantic validation)
        "evaluation_factor",        # Scoring criteria (Section M content)
        "submission_instruction",   # Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (Capture planning patterns)
        "strategic_theme",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (Semantic detection regardless of location)
        "statement_of_work",        # PWS/SOW/SOO content (may be Section C or attachment)
    ]
    
    # Chunking configuration (leverages Grok-4's 2M context window)
    # CHUNK_SIZE: Document chunking for BOTH LLM entity extraction and embeddings
    # - LLM processes full 50K chunks (utilizing Grok-4's massive context)
    # - Embeddings auto-truncate to 8192 via EmbeddingFunc.max_token_size
    global_args.chunking_func = chunking_by_token_size
    # Default chunk size should match .env (8192) unless overridden explicitly.
    # Use conservative defaults here to avoid accidental huge LLM requests.
    global_args.chunk_token_size = int(os.getenv("CHUNK_SIZE", "8192"))
    # Default overlap tuned for RFP-style documents
    global_args.chunk_overlap_token_size = int(os.getenv("CHUNK_OVERLAP_SIZE", "1200"))
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    logger.info("=" * 80)
    logger.info("⚙️  CONFIGURATION SUMMARY")
    logger.info("=" * 80)
    # Show dual-LLM configuration: extraction (ingestion) vs reasoning (query-time)
    try:
        extraction_name = global_args.llm_extraction_model_name
    except Exception:
        extraction_name = os.getenv("EXTRACTION_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-fast-non-reasoning"))
    try:
        reasoning_name = global_args.llm_reasoning_model_name
    except Exception:
        reasoning_name = os.getenv("REASONING_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-fast-reasoning"))
    # Temperatures can be overridden per-role via env vars
    extraction_temp = os.getenv("EXTRACTION_LLM_TEMPERATURE", os.getenv("LLM_MODEL_TEMPERATURE", "0.0"))
    reasoning_temp = os.getenv("REASONING_LLM_TEMPERATURE", os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))

    # Allow explicit context override (e.g. '2M', '128k') via env
    extraction_ctx = os.getenv("EXTRACTION_LLM_CONTEXT")
    reasoning_ctx = os.getenv("REASONING_LLM_CONTEXT")

    # Deterministic mapping only for known models. Do NOT attempt best-effort guesses.
    def map_known_context(model_name: str) -> str:
        if not model_name:
            return None
        nm = model_name.lower()
        # Known mappings
        if "grok-4" in nm:
            return "2M"
        if "gpt-4o" in nm or "gpt-4" in nm:
            return "128k"
        return None

    if extraction_ctx is None:
        extraction_ctx = map_known_context(extraction_name)
    if reasoning_ctx is None:
        reasoning_ctx = map_known_context(reasoning_name)

    # If still unspecified, make the message explicit so operators can act.
    if extraction_ctx is None:
        extraction_ctx = "UNSPECIFIED - set EXTRACTION_LLM_CONTEXT to a known context (e.g. '2M')"
    else:
        extraction_ctx = f"{extraction_ctx} context"

    if reasoning_ctx is None:
        reasoning_ctx = "UNSPECIFIED - set REASONING_LLM_CONTEXT to a known context (e.g. '128k')"
    else:
        reasoning_ctx = f"{reasoning_ctx} context"

    logger.info(f"  Extraction LLM: {extraction_name} ({extraction_ctx}, temp={extraction_temp})")
    logger.info(f"  Reasoning LLM: {reasoning_name} ({reasoning_ctx}, temp={reasoning_temp})")
    logger.info(f"  Embeddings: text-embedding-3-large (3072-dim, auto-truncate at 8192 tokens)")
    logger.info(f"  Chunking: {global_args.chunk_token_size} tokens (overlap: {global_args.chunk_overlap_token_size})")
    logger.info(f"  → LLM processes full {global_args.chunk_token_size}-token chunks")
    logger.info(f"  → Embeddings auto-truncate via EmbeddingFunc.max_token_size=8192")
    logger.info(f"  Concurrency: {os.getenv('MAX_ASYNC', '32')} parallel LLM requests")
    # Log entity types explicitly so operators can verify the exact ontology at startup
    try:
        etypes = global_args.entity_types
    except Exception:
        etypes = []
    logger.info(f"  Entity Types ({len(etypes)}): {etypes}")
    logger.info(f"  Semantic Inference: 6 algorithms (L↔M, hierarchy, attachments, clauses, requirements, concepts)")
    logger.info(f"  Working Dir: {working_dir}")
    logger.info("=" * 80)
