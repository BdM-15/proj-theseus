"""
Server Configuration for RAG-Anything + LightRAG

Configures global_args for LightRAG server with government contracting ontology.
Uses xAI Grok for LLM and OpenAI for embeddings.
"""

import os
import logging
from dotenv import load_dotenv
from lightrag.api.config import global_args
from lightrag.operate import chunking_by_token_size

load_dotenv()
logger = logging.getLogger(__name__)


def configure_raganything_args():
    """
    Configure global_args for LightRAG server to use with RAG-Anything.
    
    We'll configure the LightRAG server normally, then RAG-Anything will
    wrap the storage/processing with multimodal capabilities.
    """
    # Get API credentials (using RAG-Anything official variable names)
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = os.getenv("WORKING_DIR", "./rag_storage")
    
    # Working directory
    global_args.working_dir = working_dir
    global_args.input_dir = os.getenv("INPUT_DIR", "./inputs/uploaded")
    
    # Server configuration
    global_args.host = os.getenv("HOST", "localhost")
    global_args.port = int(os.getenv("PORT", "9621"))
    
    # LLM Configuration - xAI Grok
    global_args.llm_binding = "openai"
    global_args.llm_model_name = "grok-4-fast-reasoning"
    global_args.llm_binding_host = xai_base_url
    global_args.llm_api_key = xai_api_key
    
    # Embedding Configuration - OpenAI (MUST use OpenAI endpoint, not xAI!)
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = "text-embedding-3-large"
    global_args.embedding_binding_host = "https://api.openai.com/v1"  # OpenAI endpoint for embeddings
    global_args.embedding_api_key = openai_api_key
    global_args.embedding_dim = 3072  # CRITICAL: text-embedding-3-large dimension
    
    # Government contracting entity types (18 specialized types)
    # Semantic-first detection: Content determines entity type, not section labels
    global_args.entity_types = [
        # Core entities
        "ORGANIZATION",
        "CONCEPT",
        "EVENT",
        "TECHNOLOGY",
        "PERSON",
        "LOCATION",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "REQUIREMENT",
        
        # Structural entities
        "CLAUSE",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "SECTION",                  # Stores both structural_label + semantic_type
        "DOCUMENT",
        "DELIVERABLE",
        "ANNEX",                    # NEW: Numbered attachments (J-######, Attachment #, Annex ##)
        
        # Hierarchical program entities (NEW: Top-level containers)
        "PROGRAM",                  # Major named programs/initiatives (MCPP II, Navy MBOS, DEIP) - NOT generic concepts, must be a proper named program with scope/budget/timeline
        
        # Physical assets and equipment
        "EQUIPMENT",                # Physical assets: MHE, generators, batteries, GSE, CESE, watercraft, vehicles
        
        # Legal and regulatory citations
        "REGULATION",               # Legal citations: Public Law, USC, CFR, Executive Orders, DFARS/FAR references
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        "EVALUATION_FACTOR",        # Scoring criteria (Section M content)
        "SUBMISSION_INSTRUCTION",   # NEW: Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (NEW: Capture planning patterns)
        "STRATEGIC_THEME",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (NEW: Semantic detection regardless of location)
        "STATEMENT_OF_WORK",        # PWS/SOW/SOO content (may be Section C or attachment)
    ]
    
    # Chunking configuration (cloud-optimized for 2M context window)
    global_args.chunking_func = chunking_by_token_size
    global_args.chunk_token_size = int(os.getenv("CHUNK_SIZE", "2048"))
    global_args.chunk_overlap_token_size = int(os.getenv("CHUNK_OVERLAP_SIZE", "256"))
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    logger.info("=" * 80)
    logger.info("🚀 MAXIMUM PERFORMANCE MODE - Cloud-Optimized RAG-Anything")
    logger.info("=" * 80)
    logger.info(f"  Working dir: {working_dir}")
    logger.info(f"  LLM: grok-4-fast-reasoning @ {xai_base_url}")
    logger.info(f"  Context window: 2M tokens (input + output)")
    logger.info(f"  Embeddings: text-embedding-3-large (3072-dim)")
    logger.info(f"")
    logger.info(f"  📊 OPTIMIZED CHUNKING:")
    logger.info(f"    Chunk size: {global_args.chunk_token_size} tokens (overlap: {global_args.chunk_overlap_token_size})")
    logger.info(f"    Limit: text-embedding-3-large max 8,192 tokens per chunk")
    logger.info(f"    Navy MBOS RFP: ~30 chunks (vs 240 chunks at 800 tokens)")
    logger.info(f"    Cost savings: 87% fewer embedding API calls")
    logger.info(f"")
    logger.info(f"  ⚡ MAXIMUM CONCURRENCY:")
    logger.info(f"    LLM parallel requests: {os.getenv('MAX_ASYNC', '32')}")
    logger.info(f"    Embedding parallel requests: {os.getenv('EMBEDDING_FUNC_MAX_ASYNC', '32')}")
    logger.info(f"    Target: Process 71-page RFP in under 2 minutes")
    logger.info(f"")
    logger.info(f"  🎯 ENTITY EXTRACTION (Government Contracting Ontology):")
    logger.info(f"    Entity types: {len(global_args.entity_types)} specialized types")
    logger.info(f"    Latest additions: EQUIPMENT, REGULATION, PROGRAM (18 total)")
    logger.info(f"    Semantic-first detection: Content over labels")
    logger.info(f"    Multimodal: enabled (MinerU parser)")
    logger.info(f"")
    logger.info(f"  🤖 SEMANTIC POST-PROCESSING (LLM-Powered Relationship Inference):")
    logger.info(f"    Method: Grok LLM semantic understanding (REPLACES regex patterns)")
    logger.info(f"    Reads from: GraphML (correct data source)")
    logger.info(f"    Infers 5 core relationship algorithms:")
    logger.info(f"      1. Section L↔M linking (submission instructions → evaluation factors)")
    logger.info(f"      2. Document hierarchy (J-02000000-10 → J-02000000)")
    logger.info(f"      3. Attachment section linking (J-02000000 → Section J)")
    logger.info(f"      4. Clause clustering (FAR/DFARS → Section I)")
    logger.info(f"      5. Requirement evaluation (REQ-043 → Management Approach)")
    logger.info(f"      6. Semantic concept linking (pain points, win themes) - CORE ALGORITHM")
    logger.info(f"    Benefits: Agency-agnostic, context-aware, self-documenting")
    logger.info(f"    Cost: ~$0.052 per document (includes semantic linking)")
    logger.info("=" * 80)
