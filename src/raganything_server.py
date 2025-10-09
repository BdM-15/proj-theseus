"""
RAG-Anything Server with LightRAG WebUI
Multimodal RAG system for government contracting documents

Architecture (Post-Phase 4 Refactor):
- src/server/config.py: Configuration (entity types, API credentials, chunking)
- src/server/initialization.py: RAGAnything initialization (custom prompts, LLM wrappers)
- src/server/routes.py: FastAPI endpoints + Phase 6.1 auto-processing
- This file: Main entry point + server orchestration

Workflow:
1. Document Upload → /insert endpoint → UCF detection
2. Dual-Path Processing → Section-aware OR standard extraction
3. LightRAG Extraction → 12 entity types + relationships
4. Phase 6.1 Auto-Run → 5 core semantic inference algorithms
5. Knowledge Graph Updated → GraphML + kv_store files
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import LightRAG server
from lightrag.api.lightrag_server import create_app
from lightrag.api.config import global_args
import uvicorn

# Import Phase 4 modular components
from src.server.config import configure_raganything_args
from src.server.initialization import initialize_raganything, get_rag_instance
from src.server.routes import create_insert_endpoint, create_documents_upload_endpoint, phase6_auto_processor

# Set up logging
logger = logging.getLogger(__name__)


async def main():
    """Main server startup with RAG-Anything + LightRAG WebUI
    
    Architecture:
    - RAG-Anything: Document ingestion (MinerU multimodal parser)
    - LightRAG: WebUI + query endpoints (knowledge graph queries)
    - Phase 6.1: Automatic semantic relationship inference
    
    Custom Features:
    - /insert endpoint: Overrides default LightRAG to add Phase 6.1
    - Background monitor: Auto-detects WebUI uploads, triggers Phase 6.1
    - UCF detection: Section-aware extraction for federal RFPs
    """
    print("🎯 Starting GovCon Capture Vibe with RAG-Anything...")
    print("   Architecture: RAG-Anything (ingestion) + LightRAG (WebUI/queries)")
    print("   Multimodal: images, tables, equations via MinerU parser\n")
    
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
    
    # Step 4: Override endpoints to use RAG-Anything + Phase 6.1
    # Remove original LightRAG endpoints
    new_routes = []
    found_insert = False
    found_upload = False
    for route in app.router.routes:
        # Skip the original /insert POST endpoint
        if hasattr(route, 'path') and route.path == '/insert' and hasattr(route, 'methods') and 'POST' in route.methods:
            found_insert = True
            continue
        # Skip the original /documents/upload POST endpoint (WebUI uses this!)
        if hasattr(route, 'path') and route.path == '/documents/upload' and hasattr(route, 'methods') and 'POST' in route.methods:
            found_upload = True
            continue
        new_routes.append(route)
    app.router.routes = new_routes
    
    if found_insert:
        print("   ✅ Overriding /insert endpoint with RAG-Anything + Phase 6.1")
    if found_upload:
        print("   ✅ Overriding /documents/upload endpoint with RAG-Anything + Phase 6.1")
    
    # Add our custom endpoints with RAG-Anything multimodal processing
    create_insert_endpoint(app, rag_instance)
    create_documents_upload_endpoint(app, rag_instance)
    
    # Step 5: Start background monitoring task for auto Phase 6.1
    asyncio.create_task(phase6_auto_processor(rag_instance))
    
    # Print startup info
    print(f"\n🎯 GovCon Capture Vibe Server Ready:")
    print(f"   ├─ Host: {host}")
    print(f"   ├─ Port: {port}")
    print(f"   ├─ WebUI: http://{host}:{port}/")
    print(f"   ├─ API Docs: http://{host}:{port}/docs")
    print(f"   ├─ /insert endpoint: RAG-Anything + Phase 6.1 ✅")
    print(f"   ├─ /documents/upload endpoint: RAG-Anything + Phase 6.1 ✅ (WebUI uses this!)")
    print(f"   ├─ Background Monitor: Auto-detects WebUI uploads ✅")
    print(f"   └─ Architecture: RAG-Anything (ingestion) + LightRAG (queries) + Phase 6.1 (semantic)\n")
    print(f"\n✨ Phase 6.1 Features:")
    print(f"   ├─ Automatic: Runs after every document upload (WebUI or /insert)")
    print(f"   ├─ LLM-Powered: Semantic relationship inference (no regex)")
    print(f"   ├─ 5 Core Algorithms: Section L↔M, document hierarchy, attachment linking, clause clustering, requirement evaluation")
    print(f"   └─ Transparent: No user interaction required\n")
    
    logger.info(f"Server starting on {host}:{port}")
    
    # Step 6: Start server
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
