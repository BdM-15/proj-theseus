"""
GovCon Capture Vibe Server - LightRAG with government contracting ontology

Uses LightRAG's NATIVE server with ontology modifications:
- Government contracting entity types injected via addon_params["entity_types"]
- Ontology-constrained relationship patterns for government contracting
- Section-aware chunking for RFP document structure
- All processing through LightRAG's native WebUI and API endpoints

NO CUSTOM ENDPOINTS - Everything works through LightRAG's existing features:
- /webui - Document upload, knowledge graph visualization, query interface
- /insert - Document processing with ontology-modified extraction
- /query - Retrieval with government contracting knowledge graph
- /docs - FastAPI documentation for all endpoints

Usage:
    python app.py
    
Then visit: http://localhost:9621/webui (LightRAG's native WebUI)
"""

import os
import sys
import asyncio
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

# *** CRITICAL: IMPORT LOGGING CONFIG FIRST ***
from utils.logging_config import setup_logging

# Set up logging before other imports
log_config = setup_logging(
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    console_output=os.getenv("LOG_CONSOLE", "true").lower() == "true"
)

import logging
logger = logging.getLogger(__name__)

# Import from forked lightrag library at /src/lightrag/ (NOT pip package)
# Python path already points to /src, so lightrag imports will resolve correctly

from lightrag.lightrag import LightRAG
from lightrag.utils import EmbeddingFunc
from lightrag.llm.ollama import ollama_model_complete, ollama_embed
from lightrag.api.lightrag_server import create_app
import uvicorn
from dotenv import load_dotenv

# Import ontology integration (modifies LightRAG extraction)
from lightrag.govcon.ontology_integration import OntologyInjector

# Import simple chunking (Path B - let ontology-guided LLM extraction identify structure)
from core.lightrag_chunking import simple_chunking_func

# Load environment variables
load_dotenv()

async def main():
    """Main server initialization and startup"""

    print("🚀 Initializing GovCon Capture Vibe Server (using forked lightrag)...")
    print("   ├─ Loading LightRAG from /src/lightrag/ (NOT pip package)")
    print("   ├─ Injecting entity types via addon_params")
    print("   └─ Using ontology-guided LLM extraction (no regex preprocessing)\n")

    logger.info("🚀 GovCon Capture Vibe Server initialization started (forked library)")
    logger.info(f"📁 Log files configured: {log_config}")

    # Parse LightRAG args from environment
    from lightrag.api.config import global_args

    print("🤖 Initializing LightRAG with government contracting ontology...")

    # Initialize ontology injector
    ontology_injector = OntologyInjector()
    logger.info(f"Ontology injector initialized with {len(ontology_injector.entity_types)} entity types")

    # 🔥 INJECT ONTOLOGY INTO GLOBAL_ARGS
    # Modify global_args BEFORE create_app creates the LightRAG instance
    global_args.entity_types = ontology_injector.get_entity_types_for_lightrag()
    global_args.chunking_func = simple_chunking_func
    
    # 🔥 CRITICAL: Add ontology_injector to addon_params for prompt enhancement
    if not hasattr(global_args, 'addon_params') or global_args.addon_params is None:
        global_args.addon_params = {}
    global_args.addon_params['ontology_injector'] = ontology_injector
    
    print("   ✅ Ontology injected into global_args")
    print(f"   ✅ Entity types: {len(global_args.entity_types)} government contracting types")
    print("   ✅ Ontology injector: AVAILABLE for prompt enhancement")
    print("   ✅ Simple chunking: ACTIVE (let ontology-guided LLM identify structure)")
    print("   ✅ All processing through native LightRAG endpoints\n")

    # Create LightRAG server app with native WebUI
    print("🌐 Creating LightRAG server with native endpoints...")

    # Use LightRAG's native create_app
    # It will create LightRAG instance using our modified global_args
    app = create_app(global_args)

    print("   ✅ Server created with native LightRAG endpoints")
    print("   ✅ No custom endpoints - using LightRAG's features\n")

    # Get server configuration from global_args
    host = global_args.host
    port = global_args.port

    print(f"🎯 GovCon Capture Vibe Server Ready:")
    print(f"   ├─ Host: {host}")
    print(f"   ├─ Port: {port}")
    print(f"   ├─ WebUI: http://{host}:{port}/webui (document upload, KG viz, query)")
    print(f"   ├─ API Docs: http://{host}:{port}/docs (FastAPI documentation)")
    print(f"   ├─ Document Processing: Native /insert with ontology extraction")
    print(f"   ├─ Knowledge Graph: Native /kg with government contracting entities")
    print(f"   └─ Query: Native /query with domain-specific retrieval\n")

    logger.info("Server ready - all features using native LightRAG endpoints")

    # Start server using uvicorn
    config = uvicorn.Config(
        app=app,
        host=host,
        port=port,
        log_level=global_args.log_level.lower() if hasattr(global_args, 'log_level') else "info"
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
