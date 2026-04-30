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
import sys
from dotenv import load_dotenv
load_dotenv()

# Windows MAX_PATH mitigation for MinerU document processing
# MinerU CLI creates mineru-api-client-{random} temp dirs under the system temp
# directory. Long document names (≥60 chars) push the output path:
#   {TEMP}\mineru-api-client-{8}\output\{uuid-36}\{name-69}\auto\{name-69}_origin.pdf
# to ~259 chars — hitting Windows' 260-char MAX_PATH limit and causing
# FileNotFoundError when MinerU tries to write _origin.pdf.
# Fix: redirect Python's tempfile module to a shorter base path.
if sys.platform == "win32":
    import tempfile
    _mineru_temp = os.environ.get("MINERU_TEMP_DIR", r"C:\T")
    os.makedirs(_mineru_temp, exist_ok=True)
    tempfile.tempdir = _mineru_temp

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
    create_scan_endpoint,
)
from src.server.ui_routes import register_ui

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
    
    # Step 3-pre: Monkey-patch LightRAG inside lightrag.api.lightrag_server so that
    # when create_app() constructs ITS internal LightRAG instance (separate from
    # RAGAnything's _rag_anything.lightrag), the local BGE reranker is auto-injected.
    # The stock API server only supports remote rerank bindings (cohere, jina, ali);
    # this hook adds first-class local FlagReranker support without forking LightRAG.
    from src.extraction.govcon_reranker import make_govcon_rerank_func
    _local_rerank = make_govcon_rerank_func()
    if _local_rerank is not None:
        import lightrag.api.lightrag_server as _lr_api_mod
        _OriginalLightRAG = _lr_api_mod.LightRAG

        class _LightRAGWithLocalRerank(_OriginalLightRAG):
            def __init__(self, *args, **kwargs):
                if kwargs.get("rerank_model_func") is None:
                    kwargs["rerank_model_func"] = _local_rerank
                    logger.info(
                        "🎯 Auto-injecting local BGE reranker into API server's "
                        "LightRAG (workspace=%s)",
                        kwargs.get("workspace", "?"),
                    )
                super().__init__(*args, **kwargs)

        _lr_api_mod.LightRAG = _LightRAGWithLocalRerank

    # Step 3: Create LightRAG server (WebUI + query endpoints)
    app = create_app(global_args)

    # Restore original class to avoid affecting any later code paths
    if _local_rerank is not None:
        _lr_api_mod.LightRAG = _OriginalLightRAG

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
    create_scan_endpoint(app, rag_instance)
    logger.info("✅ Custom endpoints registered: /insert, /documents/upload, /scan-rfp")
    logger.info("✅ Use LightRAG's native /query/data endpoint for structured data retrieval (agent workflows)")

    # Project Theseus custom UI (cyberpunk capture workbench at /ui)
    async def _ui_query(text: str, mode: str, history: list[dict], stream: bool, overrides: dict | None = None):
        """UI query bridge: passes per-workspace QueryParam tunables + reranker score.

        `overrides` is a dict from `_build_query_overrides()` containing any of:
        top_k, chunk_top_k, max_entity_tokens, max_relation_tokens,
        max_total_tokens, enable_rerank, only_need_context, only_need_prompt,
        response_type, user_prompt, min_rerank_score.

        `min_rerank_score` is applied to the LightRAG instance for the call so
        the reranker honors the per-workspace threshold.

        Returns either a string (stream=False) or an AsyncIterator[str]
        (stream=True). The UI router unpacks both shapes.
        """
        from lightrag import QueryParam
        overrides = dict(overrides or {})
        # min_rerank_score isn't a QueryParam field — apply it directly to the
        # LightRAG instance. Safe to mutate per-call: extraction reranker reads
        # this attribute on each invocation.
        min_score = overrides.pop("min_rerank_score", None)
        if min_score is not None:
            try:
                rag_instance.lightrag.min_rerank_score = float(min_score)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed setting min_rerank_score=%r: %s", min_score, exc)
        # Drop any unknown keys to avoid TypeError if QueryParam evolves.
        valid_fields = {f.name for f in QueryParam.__dataclass_fields__.values()}
        param_kwargs = {k: v for k, v in overrides.items() if k in valid_fields}
        return await rag_instance.lightrag.aquery(
            text,
            param=QueryParam(
                mode=mode,
                stream=stream,
                conversation_history=history or [],
                **param_kwargs,
            ),
        )

    async def _ui_query_data(text: str, mode: str, history: list[dict], overrides: dict | None = None):
        """UI data bridge: returns LightRAG aquery_data structured retrieval (chunks/entities/relationships/references) without LLM generation. Used by the chat SSE endpoint to emit a `sources` event before streaming the answer."""
        from lightrag import QueryParam
        overrides = dict(overrides or {})
        min_score = overrides.pop("min_rerank_score", None)
        if min_score is not None:
            try:
                rag_instance.lightrag.min_rerank_score = float(min_score)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed setting min_rerank_score=%r: %s", min_score, exc)
        valid_fields = {f.name for f in QueryParam.__dataclass_fields__.values()}
        param_kwargs = {k: v for k, v in overrides.items() if k in valid_fields}
        # stream is irrelevant for aquery_data (no generation), drop it.
        param_kwargs.pop("stream", None)
        return await rag_instance.lightrag.aquery_data(
            text,
            param=QueryParam(
                mode=mode,
                conversation_history=history or [],
                **param_kwargs,
            ),
        )

    async def _ui_llm(prompt: str) -> str:
        """Skill-invocation bridge: call the underlying LLM directly.

        Used by ``/api/ui/skills/{name}/invoke`` to dispatch a fully-composed
        skill prompt to the configured chat model without routing through the
        RAG query template (skills compose their own prompts that already
        include workspace entity context).
        """
        llm = getattr(rag_instance.lightrag, "llm_model_func", None)
        if llm is None:
            raise RuntimeError("LightRAG instance has no llm_model_func configured")
        result = await llm(prompt, system_prompt=None, history_messages=[])
        return result if isinstance(result, str) else str(result)

    register_ui(app, _ui_query, _ui_query_data, llm_func=_ui_llm)

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
        ("Evaluation",            "Evaluation factors / SSEB / source-selection mechanics (UCF Section M or equiv)"),
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
        # ── Models (LightRAG 1.5.0 per-role dispatch + post-processing) ────────────────
        ("Extract  (LightRAG)",  f"{c.CYAN}{settings.extraction_llm_name}{c.RESET}"),
        ("Keyword  (LightRAG)",  f"{c.CYAN}{settings.keyword_llm_name}{c.RESET}"),
        ("VLM      (LightRAG)",  f"{c.CYAN}{settings.vlm_llm_name}{c.RESET}"),
        ("Query    (LightRAG)",  f"{c.MAGENTA}{settings.reasoning_llm_name}{c.RESET}"),
        ("Post-Process",         f"{c.YELLOW}{settings.post_processing_llm_name}{c.RESET}"),
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
        ("Inference",    f"{c.CYAN}3 LLM algorithms{c.RESET}  {c.DIM}(instruction↔evaluation mapping · document structure · orphan resolution){c.RESET}"),
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
        ("Capture UI",   f"{c.BOLD}{c.CYAN}http://{host}:{port}/ui{c.RESET}  {c.DIM}(new){c.RESET}"),
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
