"""
RAG-Anything Server with LightRAG WebUI
Multimodal RAG system for government contracting documents

Architecture:
- src/server/config.py: Configuration (33 entity types, API credentials, chunking)
- src/server/initialization.py: RAGAnything initialization (tri-LLM, custom prompts)
- src/server/routes.py: FastAPI endpoints + semantic post-processing
- This file: Main entry point + server orchestration

Workflow:
1. Document Upload → /insert endpoint → UCF detection
2. Dual-Path Processing → Section-aware OR standard extraction
3. Entity Extraction → 33 custom types (extraction LLM: non-reasoning)
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

# Import centralized settings AFTER load_dotenv
from src.core import get_settings

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
    settings = get_settings()

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
    logger.info("✅ Custom endpoints registered: /insert, /documents/upload")
    logger.info("✅ Use LightRAG's native /query/data endpoint for structured data retrieval (agent workflows)")

    # Consolidated startup banner — full pipeline detail in docs/ARCHITECTURE.md
    graph_storage = global_args.graph_storage if hasattr(global_args, 'graph_storage') else "NetworkXStorage"
    from src.utils.logging_config import log_banner, Colors
    from importlib.metadata import version as _pkg_version, PackageNotFoundError
    from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES
    c = Colors

    def _ver(pkg: str) -> str:
        try:
            return _pkg_version(pkg)
        except PackageNotFoundError:
            return "unknown"

    mineru_ver = _ver("mineru")
    device = settings.mineru_device_mode.upper()
    device_color = c.GREEN if device == "CUDA" else c.YELLOW

    def _format_reranker_line() -> str:
        """Format the reranker status line for the startup banner."""
        if not settings.enable_rerank:
            return f"{c.DIM}disabled{c.RESET}"
        rd = settings.rerank_device
        rd_color = c.GREEN if rd.lower() == "cuda" else c.YELLOW
        fp = "FP16" if settings.rerank_use_fp16 else "FP32"
        return (
            f"{c.CYAN}{settings.rerank_model}{c.RESET}  "
            f"·  Device: {c.BOLD}{rd_color}{rd.upper()}{c.RESET}  "
            f"·  {c.YELLOW}{fp}{c.RESET}  "
            f"·  Min Score: {c.DIM}{settings.min_rerank_score}{c.RESET}"
        )

    # Knowledge ontology modules stacked for query enrichment
    # Scope: Shipley Phase 4-6 (Proposal Planning → Proposal Development → Post-Submittal Activities)
    kg_modules = [
        ("Shipley Methodology",   "proposal mechanics · writing craft · color teams"),
        ("Evaluation",            "Section M · SSEB · source-selection mechanics"),
        ("Regulations",           "FAR / DFARS clauses · compliance anchors"),
        ("Workload & Pricing",    "BOE · indirect rates · pricing discipline"),
        ("Lessons Learned",       "anti-patterns · explicit benefit linkage rule"),
        ("Company Capabilities",  "KBR platforms · proof points · past performance"),
        ("Capture (Phase 0-3)",   "pre-RFP terminology · upstream reference only"),
    ]

    startup_items = [
        # ── Workspace ────────────────────────────────────────────────────────────
        ("Workspace",    f"{c.BOLD}{c.WHITE}{settings.workspace}{c.RESET}"),
        ("Storage",      f"{c.YELLOW}{graph_storage}{c.RESET}  ·  {c.DIM}{global_args.working_dir}{c.RESET}"),
        ("", ""),
        # ── Models ───────────────────────────────────────────────────────────────
        ("Extraction",      f"{c.CYAN}{settings.extraction_llm_name}{c.RESET}"),
        ("Post-Processing", f"{c.YELLOW}{settings.post_processing_llm_name}{c.RESET}"),
        ("Reasoning",       f"{c.MAGENTA}{settings.reasoning_llm_name}{c.RESET}"),
        ("Embeddings",   f"{c.CYAN}{settings.embedding_model}{c.RESET}  {c.DIM}({settings.embedding_dim}D){c.RESET}"),
        ("Reranker",     _format_reranker_line()),
        ("", ""),
        # ── Stack Versions ───────────────────────────────────────────────────────
        ("LightRAG",     f"{c.DIM}{_ver('lightrag-hku')}{c.RESET}"),
        ("RAG-Anything", f"{c.DIM}{_ver('raganything')}{c.RESET}"),
        ("MinerU",       f"{c.DIM}{mineru_ver}{c.RESET}  ·  Device: {c.BOLD}{device_color}{device}{c.RESET}  ·  Method: {c.YELLOW}{settings.parse_method.upper()}{c.RESET}"),
        ("Multimodal",   f"Images · Tables · Equations · Formulas  {c.GREEN}▸ ENABLED{c.RESET}"),
        ("", ""),
        # ── Ontology Schema ──────────────────────────────────────────────────────
        ("Schema",       f"{c.BOLD}{c.YELLOW}{len(VALID_ENTITY_TYPES)}{c.RESET} entity types  ·  {c.BOLD}{c.YELLOW}{len(VALID_RELATIONSHIP_TYPES)}{c.RESET} relationship types"),
        ("Inference",    f"{c.CYAN}3 LLM algorithms{c.RESET}  {c.DIM}(L↔M mapping · document structure · orphan resolution){c.RESET}"),
        ("", ""),
        # ── Knowledge Ontologies ─────────────────────────────────────────────────
        ("Knowledge KG", f"{c.BOLD}{c.MAGENTA}{len(kg_modules)} domain ontologies{c.RESET}  {c.DIM}injected for query enrichment{c.RESET}"),
    ] + [
        (f"  {c.MAGENTA}▸{c.RESET} {name}", f"{c.DIM}{desc}{c.RESET}")
        for name, desc in kg_modules
    ] + [
        ("Scope", f"{c.DIM}Shipley Phase 4-6 — Proposal Planning → Proposal Development → Post-Submittal Activities{c.RESET}"),
        ("", ""),
        # ── Endpoints ────────────────────────────────────────────────────────────
        ("WebUI",        f"{c.BLUE}http://{host}:{port}/webui{c.RESET}"),
        ("API Docs",     f"{c.BLUE}http://{host}:{port}/docs{c.RESET}"),
    ]
    if graph_storage == "Neo4JStorage":
        startup_items.append(("Neo4j", f"{c.BLUE}http://localhost:7474{c.RESET}"))

    log_banner(f"{c.BOLD}✅ PROJECT THESEUS — READY{c.RESET}", items=startup_items, logger=logger, force_print=True)

    # Step 5: Start server
    config = uvicorn.Config(app=app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


if __name__ == "__main__":
    asyncio.run(main())
