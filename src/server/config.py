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
    
    # Graph storage: keep LightRAG's default local storage (no Neo4j, no feature flags).
    global_args.graph_storage = "NetworkXStorage"
    
    # Server configuration
    global_args.host = os.getenv("HOST", "localhost")
    global_args.port = int(os.getenv("PORT", "9621"))
    
    # LLM Configuration - xAI Grok
    global_args.llm_binding = "openai"
    global_args.llm_model_name = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    global_args.llm_binding_host = xai_base_url
    global_args.llm_api_key = xai_api_key
    
    # Embedding Configuration - OpenAI (MUST use OpenAI endpoint, not xAI!)
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    global_args.embedding_binding_host = "https://api.openai.com/v1"  # OpenAI endpoint for embeddings
    global_args.embedding_api_key = openai_api_key
    global_args.embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))  # Environment-driven for flexibility
    
    # Government contracting entity types (EXACTLY 18 ontology types)
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
        "evaluation_factor",        # Scoring criteria (Section M content)
        "submission_instruction",   # Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (Capture planning patterns)
        "strategic_theme",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (Semantic detection regardless of location)
        "statement_of_work",        # PWS/SOW/SOO content (may be Section C or attachment)
        
        # Performance standards (QASP, surveillance, metrics)
        "performance_metric",       # Distinct from requirements: accuracy, frequency, response times
    ]
    
    # CRITICAL: Set addon_params with our entity types
    # LightRAG's extract_entities() reads from addon_params.entity_types, NOT global_args.entity_types
    # Without this, text extraction uses LightRAG's generic types (Person, Organization, Location, etc.)
    global_args.addon_params = {
        "language": "English",
        "entity_types": global_args.entity_types,  # Use our govcon ontology for ALL extraction
    }
    
    # Parallel processing configuration
    # NOTE: These global_args settings are for LightRAG SERVER API only (not used by RAGAnything)
    # For RAGAnything: parallelization must be set via lightrag_kwargs in initialization.py
    # max_parallel_insert: controls concurrent document processing (file-level parallelism)
    # Fixed concurrency (no feature flags).
    global_args.max_parallel_insert = 16
    # llm_model_max_async and embedding_func_max_async are set via lightrag_kwargs in initialization.py
    
    # Chunking configuration
    # Keep a single predictable default that matches modern long-context LLM workflows.
    global_args.chunking_func = chunking_by_token_size
    global_args.chunk_token_size = int(os.getenv("CHUNK_SIZE", "8192"))
    global_args.chunk_overlap_token_size = int(os.getenv("CHUNK_OVERLAP_SIZE", "1200"))
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    # Configuration complete - detailed startup logging happens in initialization.py
