"""
RAG-Anything Server with LightRAG WebUI
Multimodal RAG system for government contracting documents

Architecture:
- src/server/config.py: Configuration (16 entity types, API credentials, chunking)
- src/server/initialization.py: RAGAnything initialization (custom prompts, LLM wrappers)
- src/server/routes.py: FastAPI endpoints + semantic post-processing
- This file: Main entry point + server orchestration

Workflow:
1. Document Upload → /insert endpoint → UCF detection
2. Dual-Path Processing → Section-aware OR standard extraction
3. LightRAG Extraction → 16 entity types + relationships
4. Semantic Post-Processing → 5 LLM inference algorithms
5. Knowledge Graph Updated → GraphML + kv_store files
"""

# CRITICAL: Load .env BEFORE any imports that might import LightRAG
# LightRAG's dataclass field defaults evaluate os.getenv() at import time:
#   chunk_token_size: int = field(default=int(os.getenv("CHUNK_SIZE", 1200)))
# If .env isn't loaded first, it uses the hardcoded 1200 default
import os
from dotenv import load_dotenv
load_dotenv()

# Now safe to import modules that may import LightRAG
import asyncio
import logging

# Suppress verbose logging from libraries
logging.getLogger("raganything").setLevel(logging.WARNING)
logging.getLogger("lightrag").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Import LightRAG server
from lightrag.api.lightrag_server import create_app
from lightrag.api.config import global_args
import uvicorn

# Import modular components (AFTER load_dotenv() so they see environment variables)
from src.server.config import configure_raganything_args
from src.server.initialization import initialize_raganything, get_rag_instance
from src.server.routes import create_insert_endpoint, create_documents_upload_endpoint

# Set up logging
logger = logging.getLogger(__name__)


async def main():
    """Main server startup with RAG-Anything + LightRAG WebUI
    
    Architecture:
    - RAG-Anything: Document ingestion (MinerU multimodal parser)
    - LightRAG: WebUI + query endpoints (knowledge graph queries)
    - Semantic Post-Processing: Automatic LLM-powered relationship inference
    
    Custom Features:
    - /insert endpoint: Overrides default LightRAG for semantic enhancement
    - Background monitor: Auto-detects WebUI uploads, triggers inference
    - UCF detection: Section-aware extraction for federal RFPs
    """
    # Initialization message moved to app.py for cleaner startup
    
    # Step 1: Configure LightRAG global_args
    configure_raganything_args()
    
    # Step 2: Initialize RAG-Anything for document processing
    await initialize_raganything()
    rag_instance = get_rag_instance()
    
    if not rag_instance:
        raise RuntimeError("Failed to initialize RAG-Anything instance")
    
    host = global_args.host
    port = global_args.port
    
    # Step 3: Create LightRAG server (WebUI + query endpoints)
    app = create_app(global_args)
    
    # Step 4: Override endpoints to use RAG-Anything + semantic post-processing
    # Remove original LightRAG endpoints
    print(f"DEBUG: Total routes before removal: {len(app.router.routes)}")
    new_routes = []
    found_insert = False
    found_upload = False
    for route in app.router.routes:
        # Skip the original /insert POST endpoint
        if hasattr(route, 'path') and route.path == '/insert' and hasattr(route, 'methods') and 'POST' in route.methods:
            print(f"DEBUG: Found and REMOVING /insert endpoint")
            found_insert = True
            continue
        # Skip the original /documents/upload POST endpoint (WebUI uses this!)
        if hasattr(route, 'path') and route.path == '/documents/upload' and hasattr(route, 'methods') and 'POST' in route.methods:
            print(f"DEBUG: Found and REMOVING /documents/upload endpoint")
            found_upload = True
            continue
        new_routes.append(route)
    app.router.routes = new_routes
    print(f"DEBUG: Total routes after removal: {len(new_routes)}")
    print(f"DEBUG: Successfully removed /insert: {found_insert}")
    print(f"DEBUG: Successfully removed /documents/upload: {found_upload}")
    
    # Add our custom endpoints with RAG-Anything multimodal processing
    print("DEBUG: About to call create_insert_endpoint()...")
    create_insert_endpoint(app, rag_instance)
    print("DEBUG: create_insert_endpoint() completed")
    
    print("DEBUG: About to call create_documents_upload_endpoint()...")
    create_documents_upload_endpoint(app, rag_instance)
    print("DEBUG: create_documents_upload_endpoint() completed")
    
    # Debug: List all registered routes
    print("DEBUG: Checking app.router.routes...")
    post_routes = []
    for route in app.router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods') and 'POST' in route.methods:
            post_routes.append(route.path)
    print(f"DEBUG: Found POST routes: {post_routes}")
    logger.info(f"✅ Custom endpoints registered: /insert, /documents/upload")
    logger.info(f"🔍 All POST routes: {post_routes}")
    
    # Print concise startup info
    print(f"\n✅ Server Ready:")
    print(f"   WebUI: http://{host}:{port}/")
    print(f"   API Docs: http://{host}:{port}/docs")
    print(f"   Features: Multimodal extraction + semantic post-processing")
    print(f"   Custom endpoints: /insert, /documents/upload (17 entity types)")
    print(f"   Background monitor: Removed (synchronous post-processing)\n")
    
    # Step 6: Start server
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
