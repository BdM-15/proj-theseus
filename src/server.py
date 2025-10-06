"""
GovCon Capture Vibe Server - RAG-Anything with xAI Grok + LightRAG WebUI

Branch 003 Cloud Enhancement: RAG-Anything backend with original LightRAG WebUI.

Features:
- RAG-Anything multimodal document processing (MinerU parser)
- xAI Grok 4 Fast Reasoning for entity extraction
- OpenAI text-embedding-3-large for semantic search
- Government contracting ontology (12 entity types)
- Multimodal: images, tables, equations from RFP documents
- Original LightRAG WebUI for easy document upload and querying

Usage:
    python app.py
    
Then visit: http://localhost:9621/ (WebUI)

Architecture:
- src/govcon_rag.py - RAG-Anything integration with govcon ontology
- src/server.py - LightRAG server with RAG-Anything backend (this file)
- src/lightrag/api/lightrag_server.py - Original WebUI and API routes
"""

import os
import sys
import asyncio
from pathlib import Path

# Import LightRAG from pip library BEFORE adding src to path
# This prevents the fork in src/lightrag/ from shadowing the pip package
from lightrag.api.lightrag_server import create_app
from lightrag.api.config import global_args

# NOW add src to Python path for our custom imports (dotenv, utils, models, etc.)
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# *** CRITICAL: IMPORT LOGGING CONFIG AFTER PATH SETUP ***
from utils.logging_config import setup_logging

# Set up logging
log_config = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    console_output=os.getenv("LOG_CONSOLE", "true").lower() == "true"
)

import logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# ============================================================================
# Configure Global Args for LightRAG Server with RAG-Anything Backend
# ============================================================================

# Configure LightRAG server to use RAG-Anything's internal LightRAG instance
# We'll use the govcon_rag.py integration but expose it through LightRAG's WebUI

def configure_lightrag_args():
    """
    Configure global_args for LightRAG server with RAG-Anything backend.
    
    This sets up the LightRAG server to use our xAI Grok + OpenAI embeddings
    through RAG-Anything's multimodal pipeline.
    """
    # Working directory
    global_args.working_dir = os.getenv("WORKING_DIR", "./rag_storage")
    global_args.input_dir = os.getenv("INPUT_DIR", "./inputs/uploaded")
    
    # Server configuration
    global_args.host = os.getenv("HOST", "localhost")
    global_args.port = int(os.getenv("PORT", "9621"))
    
    # LLM Configuration - Use OpenAI-compatible API for xAI Grok
    global_args.llm_binding = "openai"
    global_args.llm_model_name = "grok-4-fast-reasoning"
    global_args.llm_binding_host = "https://api.x.ai/v1"
    global_args.llm_api_key = os.getenv("XAI_API_KEY")
    
    # Embedding Configuration - OpenAI embeddings
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = "text-embedding-3-large"
    global_args.embedding_binding_host = "https://api.openai.com/v1"
    global_args.embedding_api_key = os.getenv("OPENAI_API_KEY")
    
    # Ontology configuration - 12 entity types for government contracting
    global_args.entity_types = [
        "ORGANIZATION",
        "CONCEPT",
        "EVENT",
        "TECHNOLOGY",
        "PERSON",
        "LOCATION",
        "REQUIREMENT",
        "CLAUSE",
        "SECTION",
        "DOCUMENT",
        "DELIVERABLE",
        "EVALUATION_FACTOR",
    ]
    
    # Chunking configuration
    from lightrag.operate import chunking_by_token_size
    global_args.chunking_func = chunking_by_token_size  # Use LightRAG's default chunking
    global_args.chunk_token_size = 800
    global_args.chunk_overlap_token_size = 100
    
    # Enable multimodal processing (RAG-Anything will be used if available)
    global_args.enable_multimodal = True
    
    # Logging
    global_args.log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logger.info("LightRAG server configured with RAG-Anything backend:")
    logger.info(f"  Working dir: {global_args.working_dir}")
    logger.info(f"  LLM: {global_args.llm_model_name} @ {global_args.llm_binding_host}")
    logger.info(f"  Embeddings: {global_args.embedding_model_name}")
    logger.info(f"  Entity types: {len(global_args.entity_types)} government contracting types")
    logger.info(f"  Multimodal: {global_args.enable_multimodal}")


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main server startup with LightRAG WebUI"""
    
    print("🎯 Starting GovCon Capture Vibe...")
    print("   Enhanced LightRAG server with RFP analysis capabilities")
    print("   Grounded in Shipley methodology for government contracting\n")
    
    # Configure LightRAG server with RAG-Anything backend
    configure_lightrag_args()
    
    # Get server configuration from global_args
    host = global_args.host
    port = global_args.port
    
    print(f"\n🎯 GovCon Capture Vibe Server Ready:")
    print(f"   ├─ Host: {host}")
    print(f"   ├─ Port: {port}")
    print(f"   ├─ WebUI: http://{host}:{port}/ (LightRAG Web Interface)")
    print(f"   ├─ API Docs: http://{host}:{port}/docs")
    print(f"   ├─ Upload: POST http://{host}:{port}/insert")
    print(f"   └─ Query: POST http://{host}:{port}/query\n")
    
    logger.info(f"Server starting on {host}:{port}")
    
    # Create FastAPI app with LightRAG server (includes WebUI)
    app = create_app(global_args)
    
    # Start server using uvicorn
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level=global_args.log_level.lower(),
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
