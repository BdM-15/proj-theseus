"""
Server Configuration v2 for RAG-Anything + LightRAG (Simplified Ontology)

This configuration module provides:
- Simplified 12-entity ontology (from 18)
- Feature flags for semantic post-processing
- Optimized chunking settings
- Query-time inference settings

Usage:
    # In initialization.py
    from src.server.config_v2 import configure_simplified_args
    configure_simplified_args()
"""

import os
from dotenv import load_dotenv
load_dotenv()

import logging
from lightrag.api.config import global_args
from lightrag.operate import chunking_by_token_size

from src.ontology.schema_v2 import get_entity_types_for_extraction, VALID_ENTITY_TYPES_V2

logger = logging.getLogger(__name__)


# =============================================================================
# FEATURE FLAGS (Environment Variable Controlled)
# =============================================================================

def is_simplified_ontology_enabled() -> bool:
    """Check if simplified 12-entity ontology is enabled."""
    return os.getenv("USE_SIMPLIFIED_ONTOLOGY", "true").lower() == "true"


def is_semantic_postprocessing_enabled() -> bool:
    """
    Check if 8-algorithm semantic post-processing is enabled.
    
    When DISABLED (recommended for v2):
    - Rely on LightRAG's native relationship inference
    - Skip custom Neo4j algorithms
    - Faster processing, simpler graph
    
    When ENABLED:
    - Run all 8 algorithms after document processing
    - May create redundant relationships
    """
    return os.getenv("ENABLE_SEMANTIC_POSTPROCESSING", "false").lower() == "true"


def is_workload_enrichment_enabled() -> bool:
    """
    Check if workload enrichment is enabled.
    
    When DISABLED (recommended for v2):
    - Workload analysis happens at query time
    - Use full description text for inference
    - No BOE metadata on requirement entities
    
    When ENABLED:
    - Add has_workload_metric, workload_categories, etc. to requirements
    - Requires additional LLM calls
    """
    return os.getenv("ENABLE_WORKLOAD_ENRICHMENT", "false").lower() == "true"


def get_query_inference_mode() -> str:
    """
    Get the query-time inference mode.
    
    Options:
    - "lightweight": Use LightRAG defaults, minimal custom prompts
    - "shipley": Add Shipley methodology guidance to queries
    - "full": Use complete GovCon ontology context (may reduce precision)
    """
    return os.getenv("QUERY_INFERENCE_MODE", "shipley")


# =============================================================================
# SIMPLIFIED RAGANYTHING CONFIGURATION
# =============================================================================

def configure_simplified_args():
    """
    Configure global_args for LightRAG server with simplified ontology.
    
    Changes from v1:
    - 12 entity types (from 18)
    - Larger chunks (8192 tokens) for better context
    - Simplified addon_params
    - No custom relationship types in config
    """
    # Get API credentials
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = os.getenv("WORKING_DIR", "./rag_storage")
    
    # Working directory
    global_args.working_dir = working_dir
    global_args.input_dir = os.getenv("INPUT_DIR", "./inputs/uploaded")
    
    # Graph Storage Configuration
    graph_storage_type = os.getenv("GRAPH_STORAGE", "NetworkXStorage")
    if graph_storage_type == "Neo4JStorage":
        neo4j_config = {
            "uri": os.getenv("NEO4J_URI", "neo4j://localhost:7687"),
            "username": os.getenv("NEO4J_USERNAME", "neo4j"),
            "password": os.getenv("NEO4J_PASSWORD"),
            "database": os.getenv("NEO4J_DATABASE", "neo4j"),
        }
        global_args.graph_storage = "Neo4JStorage"
        global_args.neo4j_config = neo4j_config
    else:
        global_args.graph_storage = "NetworkXStorage"
    
    # Server configuration
    global_args.host = os.getenv("HOST", "localhost")
    global_args.port = int(os.getenv("PORT", "9621"))
    
    # LLM Configuration - xAI Grok
    global_args.llm_binding = "openai"
    global_args.llm_model_name = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    global_args.llm_binding_host = xai_base_url
    global_args.llm_api_key = xai_api_key
    
    # Embedding Configuration - OpenAI
    global_args.embedding_binding = "openai"
    global_args.embedding_model_name = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
    global_args.embedding_binding_host = "https://api.openai.com/v1"
    global_args.embedding_api_key = openai_api_key
    global_args.embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    # =======================================================================
    # SIMPLIFIED ENTITY TYPES (12 core types)
    # =======================================================================
    if is_simplified_ontology_enabled():
        entity_types = get_entity_types_for_extraction()
        logger.info(f"✅ Using SIMPLIFIED ontology: {len(entity_types)} entity types")
    else:
        # Fall back to original 18 types
        entity_types = [
            "organization", "concept", "event", "technology", "person", "location",
            "requirement", "clause", "section", "document", "deliverable",
            "evaluation_factor", "submission_instruction", "program", "equipment",
            "strategic_theme", "statement_of_work", "performance_metric"
        ]
        logger.info(f"⚠️ Using ORIGINAL ontology: {len(entity_types)} entity types")
    
    global_args.entity_types = entity_types
    
    # =======================================================================
    # SIMPLIFIED ADDON_PARAMS
    # =======================================================================
    global_args.addon_params = {
        "language": "English",
        "entity_types": entity_types,
        # NOTE: entity_extraction_system_prompt set in initialization.py
    }
    
    # Parallel processing
    max_async = int(os.getenv("MAX_ASYNC", "16"))
    global_args.max_parallel_insert = max_async
    
    # =======================================================================
    # CHUNKING CONFIGURATION
    # Optimal for Grok-4's 2M context: larger chunks preserve context
    # =======================================================================
    global_args.chunking_func = chunking_by_token_size
    
    chunk_size = os.getenv("CHUNK_SIZE")
    chunk_overlap = os.getenv("CHUNK_OVERLAP_SIZE")
    
    if not chunk_size or not chunk_overlap:
        # Safe defaults for simplified ontology
        chunk_size = "8192"  # Large chunks for better context
        chunk_overlap = "1200"  # ~15% overlap
        logger.warning(f"CHUNK_SIZE/CHUNK_OVERLAP_SIZE not set, using defaults: {chunk_size}/{chunk_overlap}")
    
    global_args.chunk_token_size = int(chunk_size)
    global_args.chunk_overlap_token_size = int(chunk_overlap)
    
    # Multimodal support
    global_args.enable_multimodal = True
    
    # =======================================================================
    # LOG CONFIGURATION SUMMARY
    # =======================================================================
    _log_configuration_summary(entity_types)


def _log_configuration_summary(entity_types: list):
    """Log a summary of the configuration."""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    logger.info("")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{BOLD}SIMPLIFIED ONTOLOGY CONFIGURATION v2.0{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{GREEN}Entity Types:{RESET} {BOLD}{len(entity_types)}{RESET} (simplified from 18)")
    logger.info(f"{GREEN}Types:{RESET} {', '.join(entity_types[:6])}...")
    logger.info("")
    logger.info(f"{GREEN}Feature Flags:{RESET}")
    logger.info(f"  - Simplified Ontology:     {BOLD}{GREEN}ENABLED{RESET}" if is_simplified_ontology_enabled() else f"  - Simplified Ontology:     {YELLOW}DISABLED{RESET}")
    logger.info(f"  - Semantic Post-Process:   {YELLOW}DISABLED{RESET}" if not is_semantic_postprocessing_enabled() else f"  - Semantic Post-Process:   {BOLD}ENABLED{RESET}")
    logger.info(f"  - Workload Enrichment:     {YELLOW}DISABLED{RESET}" if not is_workload_enrichment_enabled() else f"  - Workload Enrichment:     {BOLD}ENABLED{RESET}")
    logger.info(f"  - Query Inference Mode:    {BOLD}{get_query_inference_mode()}{RESET}")
    logger.info("")
    logger.info(f"{GREEN}Chunking:{RESET} {global_args.chunk_token_size} tokens, {global_args.chunk_overlap_token_size} overlap")
    logger.info(f"{GREEN}Storage:{RESET} {global_args.graph_storage}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")


# =============================================================================
# QUERY-TIME INFERENCE HELPERS
# =============================================================================

def get_workload_analysis_prompt() -> str:
    """
    Return prompt for query-time workload analysis.
    
    Used when user asks about workload/staffing/BOE.
    This replaces extraction-time workload enrichment.
    """
    return """
When the user asks about workload, staffing, or basis of estimate (BOE):

1. **Extract from requirement descriptions**: Look for volumes, frequencies, shifts, quantities
   - "500 calls per day" → Labor driver
   - "24/7 operations" → Shift coverage
   - "100 receptacles emptied daily" → Workload volume
   
2. **Categorize into BOE categories**:
   - Labor: FTEs, roles, shifts, coverage
   - Materials: Equipment, supplies, consumables
   - ODCs: Travel, licenses, subcontracts
   - QA: Inspections, audits, quality control
   - Logistics: Transportation, delivery
   - Lifecycle: Maintenance, sustainment
   - Compliance: Certifications, documentation

3. **Preserve specificity**: Include the exact numbers from requirements
   - Do NOT generalize "500 calls/day" to just "high volume"
   - Keep frequency details: "monthly", "quarterly", "as needed"

4. **Link to requirements**: Cite which requirements drive each workload element
"""


def get_shipley_methodology_prompt() -> str:
    """
    Return prompt for Shipley capture methodology queries.
    
    Adds Shipley-specific guidance for win strategy queries.
    """
    return """
For Shipley Associates capture methodology queries:

**Pursuit Decision Phase**:
- Identify opportunity fit and probability of win (Pwin)
- Extract customer hot buttons from RFP emphasis language
- Note competitor intelligence from incumbent references

**Capture Planning Phase**:
- Identify discriminators: What sets us apart?
- Proof points: What evidence validates claims?
- Win themes: Overarching positioning messages

**Proposal Development Phase**:
- Pink Team: Compliance check, outline review
- Red Team: Persuasiveness, win themes visible
- Gold Team: Final quality review

**Color Review Mapping**:
- From Section L (instructions): Compliance checklist
- From Section M (evaluation): Scoring criteria
- Link requirements → factors for traceability matrix

**Risk Identification**:
- Capture risks: Can we compete effectively?
- Execution risks: Can we perform if awarded?
- Technical risks: Technology/capability gaps
- Programmatic risks: Schedule, cost, staffing
"""


def get_entity_type_definitions() -> str:
    """
    Return concise entity type definitions for query context.
    
    Lighter weight than full extraction rules.
    """
    return """
Entity Types in this knowledge graph:

- **requirement**: Contractual obligations (shall/must statements)
- **deliverable**: CDRLs, reports, work products
- **evaluation_factor**: Section M scoring criteria
- **compliance_item**: Section L format/submission instructions
- **win_strategy**: Themes, discriminators, proof points
- **risk**: Capture and execution risks
- **section**: RFP sections (A-M, SOW/PWS)
- **document**: Attachments, standards, references
- **regulation**: FAR/DFARS/agency clauses
- **organization**: Agencies, contractors
- **program**: Contract/program names
- **reference**: Miscellaneous important references

Workload details (volumes, frequencies, staffing) are in requirement descriptions.
"""
