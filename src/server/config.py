"""
Server Configuration for RAG-Anything + LightRAG

Configures global_args for LightRAG server with government contracting ontology.
Uses xAI Grok for LLM and OpenAI for embeddings.
"""

# CRITICAL: Load .env BEFORE importing LightRAG modules
import os
from dotenv import load_dotenv
load_dotenv()

# Now safe to import LightRAG
import logging
from lightrag.api.config import global_args
from lightrag.operate import chunking_by_token_size
# Import the single source of truth for entity types
from src.ontology.schema import VALID_ENTITY_TYPES

logger = logging.getLogger(__name__)


def configure_raganything_args():
    """
    Configure global_args for LightRAG server to use with RAG-Anything.
    """
    # Get API credentials
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = os.getenv("WORKING_DIR", "./rag_storage")
    
    # Working directory
    global_args.working_dir = working_dir
    global_args.input_dir = os.getenv("INPUT_DIR", "./inputs/uploaded")
    
    # Graph Storage Configuration - Simplified to NetworkX for reliability
    # User requested removing over-engineered features like Neo4j if redundant
    global_args.graph_storage = "NetworkXStorage"
    
    # Server configuration
    global_args.host = os.getenv("HOST", "localhost")
    global_args.port = int(os.getenv("PORT", "9621"))
    
    # LLM Configuration - xAI Grok 4 (Primary)
    global_args.llm_binding = "openai"
    global_args.llm_model_name = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    global_args.llm_binding_host = xai_base_url
    global_args.llm_api_key = xai_api_key
    
    # Embedding Configuration - OpenAI
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    global_args.embedding_binding_host = "https://api.openai.com/v1"
    global_args.embedding_api_key = openai_api_key
    global_args.embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    # Government contracting entity types - Loaded from Schema
    global_args.entity_types = list(VALID_ENTITY_TYPES)
    
    # Set addon_params with our entity types
    global_args.addon_params = {
        "language": "English",
        "entity_types": global_args.entity_types,
    }
    
    # Parallel processing configuration
    max_async = int(os.getenv("MAX_ASYNC", "16"))
    global_args.max_parallel_insert = max_async
    
    # Chunking configuration - Optimized for Grok 4 (8192 context)
    global_args.chunking_func = chunking_by_token_size
    
    # Use defaults if env vars not set, as per simplified requirements
    chunk_size = os.getenv("CHUNK_SIZE", "8192")
    chunk_overlap = os.getenv("CHUNK_OVERLAP_SIZE", "1200")
    
    global_args.chunk_token_size = int(chunk_size)
    global_args.chunk_overlap_token_size = int(chunk_overlap)
    
    # Multimodal support
    global_args.enable_multimodal = True
