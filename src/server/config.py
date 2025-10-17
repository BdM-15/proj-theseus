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
    global_args.llm_model_name = "grok-4-fast-reasoning"
    global_args.llm_binding_host = xai_base_url
    global_args.llm_api_key = xai_api_key
    
    # Embedding Configuration - OpenAI (MUST use OpenAI endpoint, not xAI!)
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = "text-embedding-3-large"
    global_args.embedding_binding_host = "https://api.openai.com/v1"  # OpenAI endpoint for embeddings
    global_args.embedding_api_key = openai_api_key
    global_args.embedding_dim = 3072  # CRITICAL: text-embedding-3-large dimension
    
    # Government contracting entity types (16 specialized types - consolidated for flexibility)
    # Semantic-first detection: Content determines entity type, not section labels
    global_args.entity_types = [
        # Core entities
        "ORGANIZATION",
        "CONCEPT",
        "EVENT",
        "TECHNOLOGY",
        "PERSON",
        "LOCATION",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "REQUIREMENT",
        
        # Structural entities
        "CLAUSE",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "SECTION",                  # Stores both structural_label + semantic_type
        "DOCUMENT",                 # References: specs, standards, manuals, regulations, attachments, annexes
        "DELIVERABLE",
        
        # Hierarchical program entities
        "PROGRAM",                  # Major named programs/initiatives (MCPP II, Navy MBOS, DEIP)
        
        # Physical assets and equipment
        "EQUIPMENT",                # Physical assets: MHE, generators, batteries, GSE, CESE, watercraft, vehicles
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        "EVALUATION_FACTOR",        # Scoring criteria (Section M content)
        "SUBMISSION_INSTRUCTION",   # Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (Capture planning patterns)
        "STRATEGIC_THEME",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (Semantic detection regardless of location)
        "STATEMENT_OF_WORK",        # PWS/SOW/SOO content (may be Section C or attachment)
    ]
    
    # Chunking configuration (leverages Grok-4's 2M context window)
    # CHUNK_SIZE: Document chunking for BOTH LLM entity extraction and embeddings
    # - LLM processes full 50K chunks (utilizing Grok-4's massive context)
    # - Embeddings auto-truncate to 8192 via EmbeddingFunc.max_token_size
    global_args.chunking_func = chunking_by_token_size
    global_args.chunk_token_size = int(os.getenv("CHUNK_SIZE", "50000"))
    global_args.chunk_overlap_token_size = int(os.getenv("CHUNK_OVERLAP_SIZE", "1000"))
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    logger.info("=" * 80)
    logger.info("⚙️  CONFIGURATION SUMMARY")
    logger.info("=" * 80)
    logger.info(f"  LLM: grok-4-fast-reasoning (2M context)")
    logger.info(f"  Embeddings: text-embedding-3-large (3072-dim, auto-truncate at 8192 tokens)")
    logger.info(f"  Chunking: {global_args.chunk_token_size} tokens (overlap: {global_args.chunk_overlap_token_size})")
    logger.info(f"  → LLM processes full {global_args.chunk_token_size}-token chunks")
    logger.info(f"  → Embeddings auto-truncate via EmbeddingFunc.max_token_size=8192")
    logger.info(f"  Concurrency: {os.getenv('MAX_ASYNC', '32')} parallel LLM requests")
    logger.info(f"  Entity Types: {len(global_args.entity_types)} specialized govcon types")
    logger.info(f"  Semantic Inference: 6 algorithms (L↔M, hierarchy, attachments, clauses, requirements, concepts)")
    logger.info(f"  Working Dir: {working_dir}")
    logger.info("=" * 80)
