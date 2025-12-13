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
from src.server.lightrag_global_args import global_args
import uvicorn

# Import modular components (AFTER load_dotenv() so they see environment variables)
from src.server.config import configure_raganything_args
from src.server.initialization import initialize_raganything, get_rag_instance
from src.server.routes import (
    create_insert_endpoint,
    create_documents_upload_endpoint,
    create_query_stream_endpoint,
    create_graphs_endpoint,
)

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
    # Remove original LightRAG endpoints that don't support multimodal processing
    new_routes = []
    for route in app.router.routes:
        # Skip the original /insert and /documents/upload POST endpoints
        if hasattr(route, 'path') and hasattr(route, 'methods') and 'POST' in route.methods:
            if route.path in ['/insert', '/documents/upload', '/query/stream']:
                continue
        # Skip the original /graphs endpoint (Neo4j temporal types can break JSON serialization)
        if hasattr(route, "path") and route.path == "/graphs":
            continue
        new_routes.append(route)
    app.router.routes = new_routes
    
    # Add our custom endpoints with RAG-Anything multimodal processing + semantic inference
    create_insert_endpoint(app, rag_instance)
    create_documents_upload_endpoint(app, rag_instance)
    create_query_stream_endpoint(app, rag_instance)
    create_graphs_endpoint(app, rag_instance)
    
    logger.info(f"✅ Custom endpoints registered: /insert, /documents/upload, /query/stream")
    
    # Print startup summary with pipeline flow
    chunk_size = os.getenv("CHUNK_SIZE", "8192")
    graph_storage = global_args.graph_storage if hasattr(global_args, 'graph_storage') else "NetworkXStorage"
    
    # ANSI color codes
    CYAN = '\033[96m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    logger.info("")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{BOLD}{MAGENTA}🔄 PROCESSING PIPELINE FLOW{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{YELLOW}1.{RESET} {BOLD}Document Upload{RESET}")
    logger.info(f"   {CYAN}└─>{RESET} MinerU multimodal parser (images/tables/equations)")
    logger.info("")
    logger.info(f"{YELLOW}2.{RESET} {BOLD}LightRAG Chunking{RESET} {CYAN}({chunk_size} tokens, 15% overlap){RESET}")
    logger.info(f"   {CYAN}└─>{RESET} Multiple focused extraction passes (prevents attention decay)")
    logger.info("")
    logger.info(f"{YELLOW}3.{RESET} {BOLD}Entity Extraction{RESET} {CYAN}(17 custom types){RESET}")
    logger.info(f"   {CYAN}├─>{RESET} Custom extraction prompts (~2,605 lines)")
    logger.info(f"   {CYAN}├─>{RESET} Grok-4-fast-reasoning LLM")
    logger.info(f"   {CYAN}└─>{RESET} Semantic-first detection (UCF patterns)")
    logger.info("")
    logger.info(f"{YELLOW}4.{RESET} {BOLD}Relationship Extraction{RESET}")
    logger.info(f"   {CYAN}└─>{RESET} LightRAG automatic relationship inference")
    logger.info("")
    logger.info(f"{YELLOW}5.{RESET} {BOLD}Semantic Post-Processing{RESET} {GREEN}(Auto-triggered){RESET}")
    logger.info(f"   {CYAN}├─>{RESET} Entity type correction")
    logger.info(f"   {CYAN}├─>{RESET} LLM relationship inference (Section L↔M, Annex linkage)")
    logger.info(f"   {CYAN}└─>{RESET} Metadata enrichment")
    logger.info("")
    logger.info(f"{YELLOW}6.{RESET} {BOLD}Knowledge Graph Storage{RESET} {CYAN}({graph_storage}){RESET}")
    if graph_storage == "Neo4JStorage":
        logger.info(f"   {CYAN}├─>{RESET} Neo4j enterprise graph database")
        logger.info(f"   {CYAN}├─>{RESET} Multi-workspace isolation")
        logger.info(f"   {CYAN}└─>{RESET} APOC subgraph queries for cross-RFP intelligence")
    else:
        logger.info(f"   {CYAN}└─>{RESET} Local GraphML files")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")
    
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{BOLD}{MAGENTA}🌐 SERVER ENDPOINTS{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{GREEN}WebUI:{RESET}              {BLUE}http://{host}:{port}/webui{RESET}")
    logger.info(f"{GREEN}API Docs:{RESET}           {BLUE}http://{host}:{port}/docs{RESET}")
    if graph_storage == "Neo4JStorage":
        logger.info(f"{GREEN}Neo4j Browser:{RESET}      {BLUE}http://localhost:7474{RESET}")
        logger.info(f"{GREEN}Neo4j Aura:{RESET}         {BLUE}https://console.neo4j.io{RESET} {YELLOW}(recommended){RESET}")
    logger.info("")
    logger.info(f"{YELLOW}Working Directory:{RESET}  {global_args.working_dir}")
    logger.info(f"{YELLOW}Current Workspace:{RESET}  {BOLD}{os.getenv('WORKSPACE', 'default')}{RESET}")
    logger.info("")
    logger.info(f"{GREEN}▸ LLM Configuration:{RESET}")
    logger.info(f"  {CYAN}Extraction:{RESET}       {os.getenv('EXTRACTION_LLM_NAME', 'grok-4-fast-reasoning')}")
    logger.info(f"  {CYAN}Reasoning:{RESET}        {os.getenv('REASONING_LLM_NAME', 'grok-4-fast-reasoning')}")
    logger.info(f"  {CYAN}Embeddings:{RESET}       {os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')} ({os.getenv('EMBEDDING_DIM', '3072')}D)")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")
    
    # Step 5: Start server
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
