"""
RAG-Anything Server with LightRAG WebUI
Multimodal RAG system for government contracting documents

Architecture:
- src/server/config.py: Configuration (18 entity types, API credentials, chunking)
- src/server/initialization.py: RAGAnything initialization (dual LLM, custom prompts)
- src/server/routes.py: FastAPI endpoints + semantic post-processing
- This file: Main entry point + server orchestration

Workflow:
1. Document Upload → /insert endpoint → UCF detection
2. Dual-Path Processing → Section-aware OR standard extraction
3. Entity Extraction → 18 custom types (extraction LLM: non-reasoning)
4. Semantic Post-Processing → 8 LLM inference algorithms (reasoning LLM)
5. Knowledge Graph Storage → Neo4j or local GraphML
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
from src.server.routes import (
    create_insert_endpoint,
    create_documents_upload_endpoint,
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

    # Log the effective model configuration the WebUI /query endpoint will use.
    # LightRAG's API server passes `args.llm_model` directly into openai_complete_if_cache(...)
    # (see: lightrag/api/lightrag_server.py -> create_optimized_openai_llm_func).
    logger.info(f"✅ WebUI Query Model (effective): {getattr(global_args, 'llm_model', None)}")
    logger.info(f"   - Extraction model (env EXTRACTION_LLM_NAME): {os.getenv('EXTRACTION_LLM_NAME')}")
    logger.info(f"   - Reasoning model (env REASONING_LLM_NAME):  {os.getenv('REASONING_LLM_NAME')}")
    
    # Step 4: Override endpoints to use RAG-Anything + semantic post-processing
    # Remove original LightRAG endpoints that don't support multimodal processing
    new_routes = []
    for route in app.router.routes:
        # Skip the original /insert and /documents/upload POST endpoints
        if hasattr(route, 'path') and hasattr(route, 'methods') and 'POST' in route.methods:
            if route.path in ['/insert', '/documents/upload']:
                continue
        new_routes.append(route)
    app.router.routes = new_routes
    
    # Add our custom endpoints with RAG-Anything multimodal processing + semantic inference
    create_insert_endpoint(app, rag_instance)
    create_documents_upload_endpoint(app, rag_instance)
    
    logger.info("✅ Custom endpoints registered: /insert, /documents/upload (multimodal + semantic inference)")
    
    # Print startup summary with pipeline flow
    chunk_size = os.getenv("CHUNK_SIZE", "4096")
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
    logger.info(f"{YELLOW}3.{RESET} {BOLD}Entity Extraction{RESET} {CYAN}(18 custom types){RESET}")
    logger.info(f"   {CYAN}├─>{RESET} Native LightRAG extraction (~22K tokens FULL govcon prompt)")
    logger.info(f"   {CYAN}├─>{RESET} LLM (query model): {getattr(global_args, 'llm_model', os.getenv('LLM_MODEL', 'unknown'))}")
    logger.info(f"   {CYAN}└─>{RESET} Tuple-delimited output (Issue #54 - Back to Basics)")
    logger.info("")
    logger.info(f"{YELLOW}4.{RESET} {BOLD}Relationship Extraction{RESET}")
    logger.info(f"   {CYAN}└─>{RESET} LightRAG automatic relationship inference")
    logger.info("")
    logger.info(f"{YELLOW}5.{RESET} {BOLD}Semantic Post-Processing{RESET} {GREEN}(Auto-triggered){RESET}")
    logger.info(f"   {CYAN}├─>{RESET} 8 LLM inference algorithms (~3,500 lines prompts)")
    logger.info(f"   {CYAN}├─>{RESET} Relationship inference (Section L↔M, Annex linkage)")
    logger.info(f"   {CYAN}└─>{RESET} Workload enrichment + description generation")
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
    logger.info(f"{GREEN}▸ LLM Configuration (Dual-Model):{RESET}")
    logger.info(f"  {CYAN}Extraction:{RESET}       {os.getenv('EXTRACTION_LLM_NAME', 'grok-4-1-fast-non-reasoning')} {YELLOW}(non-reasoning){RESET}")
    logger.info(f"  {CYAN}Reasoning:{RESET}        {os.getenv('REASONING_LLM_NAME', 'grok-4-1-fast-reasoning')} {GREEN}(reasoning){RESET}")
    logger.info(f"  {CYAN}Embeddings:{RESET}       {os.getenv('EMBEDDING_MODEL', 'text-embedding-3-large')} ({os.getenv('EMBEDDING_DIM', '3072')}D)")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")
    
    # Step 5: Start server
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
