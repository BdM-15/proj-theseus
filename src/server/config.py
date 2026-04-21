"""
Server Configuration for RAG-Anything + LightRAG

Configures global_args for LightRAG server with government contracting ontology.
Uses xAI Grok for LLM and OpenAI for embeddings.

Configuration is loaded from src/core/config.py (centralized Settings class).
"""

# CRITICAL: Load .env BEFORE importing LightRAG modules
# LightRAG's chunk_token_size default: int(os.getenv("CHUNK_SIZE", 1200))
# Must set environment variables before LightRAG classes are defined
from dotenv import load_dotenv
load_dotenv()

# Now safe to import LightRAG and our config
import logging
from lightrag.api.config import global_args
from lightrag.operate import chunking_by_token_size  # noqa: F401  # kept for reference / fallback
from src.extraction.govcon_chunking import govcon_chunking_func

from src.core.config import get_settings

logger = logging.getLogger(__name__)


def configure_raganything_args():
    """
    Configure global_args for LightRAG server to use with RAG-Anything.
    
    We'll configure the LightRAG server normally, then RAG-Anything will
    wrap the storage/processing with multimodal capabilities.
    
    All configuration values come from the centralized Settings class.
    """
    # Get validated settings from centralized config
    settings = get_settings()
    
    # Working directory
    global_args.working_dir = settings.working_dir
    global_args.input_dir = settings.input_dir

    # Canonical LightRAG state stays on local file-backed storage for this repo.
    # Neo4j remains the graph backend, while KV/doc status/vector persistence lives
    # under rag_storage/<workspace>/ using LightRAG's default local implementations.
    global_args.kv_storage = "JsonKVStorage"
    global_args.vector_storage = "NanoVectorDBStorage"
    global_args.doc_status_storage = "JsonDocStatusStorage"
    
    # Graph Storage Configuration - Neo4j vs NetworkX
    if settings.graph_storage == "Neo4JStorage":
        from lightrag.kg.neo4j_impl import Neo4JStorage
        
        neo4j_config = {
            "uri": settings.neo4j_uri,
            "username": settings.neo4j_username,
            "password": settings.neo4j_password,
            "database": settings.neo4j_database,
        }
        
        # Create Neo4j storage instance
        global_args.graph_storage = "Neo4JStorage"  # Tell LightRAG to use Neo4j
        global_args.neo4j_config = neo4j_config     # Pass Neo4j connection details
    else:
        global_args.graph_storage = "NetworkXStorage"
    
    # Server configuration
    global_args.host = settings.host
    global_args.port = settings.port
    
    # LLM Configuration - xAI Grok (Dual-Model: Extraction uses non-reasoning, Query uses reasoning)
    global_args.llm_binding = "openai"

    # IMPORTANT: LightRAG's API server uses `llm_model` (from env `LLM_MODEL`) for /query.
    # We explicitly bind queries to the reasoning model to avoid "compliance-only" answers.
    #
    # Extraction is handled separately by RAG-Anything via src/server/initialization.py (dual-model router),
    # so setting the query model here will NOT force extraction to use reasoning.
    query_model = settings.reasoning_llm_name

    # Keep legacy fields (some older code paths may read these), but ensure the canonical fields are set.
    global_args.llm_model = query_model
    global_args.llm_model_name = query_model
    global_args.llm_binding_host = settings.llm_binding_host
    global_args.llm_binding_api_key = settings.llm_binding_api_key
    global_args.llm_api_key = settings.llm_binding_api_key
    
    # Embedding Configuration - OpenAI (MUST use OpenAI endpoint, not xAI!)
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = settings.embedding_model
    global_args.embedding_binding_host = settings.embedding_binding_host
    global_args.embedding_binding_api_key = settings.embedding_binding_api_key
    global_args.embedding_api_key = settings.embedding_binding_api_key
    global_args.embedding_dim = settings.embedding_dim
    
    # Government contracting entity types (18 specialized types)
    # LightRAG reads entity_types ONLY from addon_params (operate.py line 2908).
    # Single source of truth — no dual injection needed.
    entity_types = [
        # Core entities
        "organization",
        "concept",
        "event",
        "technology",
        "person",
        "location",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "requirement",
        
        # Structural entities
        "clause",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "document_section",         # Numbered/heading-based structural units regardless of UCF
        "document",                 # References: specs, standards, manuals, regulations, attachments, annexes
        "amendment",                # Solicitation changes, modifications, and updates
        "deliverable",
        
        # Hierarchical program entities
        "program",                  # Major named programs/initiatives (MCPP II, Navy MBOS, DEIP)
        
        # Physical assets and equipment
        "equipment",                # Physical assets: MHE, generators, batteries, GSE, CESE, watercraft, vehicles
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        "evaluation_factor",        # Scoring criteria (Section M content)
        "proposal_instruction",     # Format/page limits and submission mechanics regardless of section
        "proposal_volume",          # Volume containers and named proposal parts
        
        # Strategic entities (Capture planning patterns)
        "strategic_theme",          # Win themes, hot buttons, discriminators, proof points
        "customer_priority",        # Explicit importance signals from government language
        "pain_point",               # Problems, deficiencies, and issues government wants solved
        
        # Work scope (Semantic detection regardless of location)
        "work_scope_item",          # PWS/SOW/SOO tasks, objectives, and work packages
        "transition_activity",      # Phase-in / phase-out work items
        
        # Performance, pricing, and execution structure
        "performance_standard",     # KPIs, SLAs, QASP thresholds, acceptance criteria
        "contract_line_item",       # CLINs/SLINs and priced line items
        "pricing_element",          # Rates, fees, escalation, indirect pricing logic
        "workload_metric",          # Quantitative BOE drivers
        "labor_category",           # Named labor roles when explicitly stated
        "subfactor",                # Child evaluation criteria
        "regulatory_reference",     # DAFI, NIST, MIL-STD, AR, etc.
        "technical_specification",  # ICDs, drawings, MIL-DTL, TDPs, engineering specs
        "government_furnished_item",# GFE/GFP/GFI/GOTS provided by customer
        "compliance_artifact",      # Certifications, accreditations, authorizations
        "past_performance_reference"# Reference contracts, PPQs, CPARS artifacts
    ]
    
    # addon_params is the sole path LightRAG uses for entity_types in extraction
    global_args.addon_params = {
        "language": "English",
        "entity_types": entity_types,
    }
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PARALLELIZATION CONFIGURATION (Semantic naming from centralized config)
    # ═══════════════════════════════════════════════════════════════════════════
    # LightRAG has three concurrency controls:
    # - max_parallel_insert: Document-level parallelism (files processed concurrently)
    # - max_async / llm_model_max_async: Chunk-level LLM concurrency within each document
    # - embedding_func_max_async: Embedding API concurrency
    #
    # Our centralized config uses semantic names for clarity:
    # - settings.max_parallel_insert → document-level (recommended: llm_max_async / 3)
    # - settings.llm_max_async → extraction LLM concurrency (higher for throughput)
    # - settings.embedding_max_async → embedding concurrency
    # - settings.post_processing_max_async → semantic inference (lower for stability)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Document-level parallelism (how many files processed at once)
    global_args.max_parallel_insert = settings.max_parallel_insert
    
    # Chunk-level LLM concurrency (extraction throughput)
    effective_llm_async = settings.get_effective_llm_max_async()
    global_args.max_async = effective_llm_async
    
    # Embedding API concurrency
    effective_embedding_async = settings.get_effective_embedding_max_async()
    global_args.embedding_func_max_async = effective_embedding_async
    
    # Chunking configuration (optimized for focused extraction)
    # CHUNK_SIZE: Document chunking for BOTH LLM entity extraction and embeddings
    # - 8K chunks = multiple focused extraction passes = comprehensive coverage
    # - Embeddings auto-truncate to model limits via EmbeddingFunc.max_token_size
    #
    # govcon_chunking_func wraps LightRAG's native chunking_by_token_size and
    # prepends a [GOVCON_DOC: type=...; note=...] banner to each chunk based on
    # filename echoes and structural signals (templates, solicitations, PWS,
    # CDRL exhibits). Non-invasive — uses the documented chunking_func seam,
    # no library patches. See src/extraction/govcon_chunking.py.
    global_args.chunking_func = govcon_chunking_func
    
    # Validate required chunking settings (centralized validation)
    settings.validate_required_settings()
    global_args.chunk_token_size = settings.chunk_size
    global_args.chunk_overlap_token_size = settings.chunk_overlap_size
    
    # Extraction input token limit (Grok supports 131K, default 100K for headroom)
    global_args.max_extract_input_tokens = settings.max_extract_input_tokens
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    logger.info(f"  Parallelization: max_parallel_insert={settings.max_parallel_insert}, "
                f"llm_max_async={effective_llm_async}, embedding_max_async={effective_embedding_async}")
    logger.info(f"  Post-processing will use: max_async={settings.get_effective_post_processing_max_async()}")
    logger.info(
        "  Local state storage: kv=%s, vector=%s, doc_status=%s",
        global_args.kv_storage,
        global_args.vector_storage,
        global_args.doc_status_storage,
    )
    
    # Configuration complete - detailed startup logging happens in initialization.py
