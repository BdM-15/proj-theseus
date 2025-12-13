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
    
    # Graph Storage Configuration - Neo4j vs NetworkX
    graph_storage_type = os.getenv("GRAPH_STORAGE", "NetworkXStorage")
    if graph_storage_type == "Neo4JStorage":
        from lightrag.kg.neo4j_impl import Neo4JStorage
        
        neo4j_config = {
            "uri": os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            "username": os.getenv("NEO4J_USERNAME", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD"),
            "database": os.getenv("NEO4J_DATABASE", "neo4j"),
        }
        
        # Create Neo4j storage instance
        global_args.graph_storage = "Neo4JStorage"  # Tell LightRAG to use Neo4j
        global_args.neo4j_config = neo4j_config     # Pass Neo4j connection details
    else:
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
    
    # Ontology profile selection:
    # - govcon_full: richer extraction (more entity types)
    # - capture_light: fewer, higher-signal types for non-expert capture/proposal users
    ontology_profile = os.getenv("ONTOLOGY_PROFILE", "govcon_full").strip().lower()

    if ontology_profile == "capture_light":
        global_args.entity_types = [
            "organization",
            "requirement",
            "deliverable",
            "evaluation_factor",
            "submission_instruction",
            "clause",
            "section",
            "document",
            "strategic_theme",
            "performance_metric",
            "statement_of_work",
        ]
    else:
        # Default: govcon_full (existing ontology)
        global_args.entity_types = [
            "organization",
            "concept",
            "event",
            "technology",
            "person",
            "location",
            "requirement",
            "clause",
            "section",
            "document",
            "deliverable",
            "program",
            "equipment",
            "evaluation_factor",
            "submission_instruction",
            "strategic_theme",
            "statement_of_work",
            "performance_metric",
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
    max_async = int(os.getenv("MAX_ASYNC", "16"))
    global_args.max_parallel_insert = max_async
    # llm_model_max_async and embedding_func_max_async are set via lightrag_kwargs in initialization.py
    
    # Chunking configuration (balanced for retrieval specificity + extraction quality)
    # NOTE: LightRAG uses the SAME chunks for embeddings and extraction.
    # Very large chunks (e.g., 8192) often reduce retrieval precision and produce generic answers.
    # We provide safe defaults that can be overridden via .env.
    global_args.chunking_func = chunking_by_token_size
    chunk_size = int(os.getenv("CHUNK_SIZE", "1400"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP_SIZE", "200"))
    global_args.chunk_token_size = chunk_size
    global_args.chunk_overlap_token_size = chunk_overlap
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    # Configuration complete - detailed startup logging happens in initialization.py
