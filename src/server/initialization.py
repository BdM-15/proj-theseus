"""
RAG-Anything Initialization Module

This module handles the initialization of the RAG-Anything instance with:
- Custom entity extraction prompts (simplified for clarity)
- Government contracting ontology (18 specialized entity types)
- Multimodal document processing (MinerU parser)
- Cloud LLM integration (xAI Grok + OpenAI embeddings)
"""

# CRITICAL: Ensure .env is loaded before LightRAG imports
# This file is imported by raganything_server.py which loads .env first
# But we import it here too for safety if this module is used standalone
import os
from dotenv import load_dotenv
load_dotenv()

# Now safe to import LightRAG and related modules
import logging
from lightrag.api.config import global_args
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)

# Global RAG-Anything instance
_rag_anything = None


async def initialize_raganything():
    """Initialize RAG-Anything instance for multimodal document processing
    
    Configuration:
    - Parser: MinerU (multimodal - images, tables, equations)
    - Entity Types: 18 government contracting types (semantic-first detection)
    - LLM: xAI Grok-4-fast-reasoning (cloud processing, 2M context)
    - Embeddings: OpenAI text-embedding-3-large (3072-dim, 8192 token limit)
    - Chunking: 8K tokens (1200 token overlap) - Multiple focused extraction passes
    
    Architecture Note:
    LightRAG chunks documents at 8192 tokens. Same chunks go to BOTH:
    - LLM entity extraction (multiple focused passes = comprehensive entity coverage)
    - Embedding generation (fits within 8192 token limit, no truncation needed)
    Smaller chunks prevent LLM attention decay that caused 50K chunk extraction failure.
    
    Returns:
        RAGAnything: Configured instance ready for document ingestion
    """
    global _rag_anything
    
    # Get API credentials (using RAG-Anything official variable names)
    xai_api_key = os.getenv("LLM_BINDING_API_KEY")
    xai_base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    openai_api_key = os.getenv("EMBEDDING_BINDING_API_KEY")
    working_dir = global_args.working_dir
    
    # Government contracting entity types (18 specialized types)
    # Semantic-first detection: Content determines entity type, not section labels
    # NOTE: LightRAG normalizes to lowercase internally - use lowercase for consistency
    entity_types = [
        # Core entities
        "organization", "concept", "event", "technology", "person", "location",
        
        # Requirements (semantic detection with metadata: requirement_type, criticality_level)
        "requirement",
        
        # Structural entities
        "clause",                   # FAR/DFARS/AFFARS patterns, will cluster by parent section
        "section",                  # Stores both structural_label + semantic_type
        "document",                 # References: specs, standards, manuals, regulations, attachments, annexes
        "deliverable",
        
        # Evaluation entities (semantic detection, may be embedded in non-standard sections)
        "evaluation_factor",        # Scoring criteria (Section M content)
        "submission_instruction",   # Format/page limits (Section L content, may be IN Section M)
        
        # Strategic entities (Capture planning patterns)
        "strategic_theme",          # Win themes, hot buttons, discriminators, proof points
        
        # Work scope (Semantic detection regardless of location)
        "statement_of_work",        # PWS/SOW/SOO content (may be Section C or attachment)
        
        # Programs and equipment
        "program",                  # Major programs (MCPP II, Navy MBOS, etc.)
        "equipment",                # Physical items (batteries, vehicles, tools)
        
        # Performance standards (QASP, surveillance, metrics)
        "performance_metric",       # Distinct from requirements: accuracy, frequency, response times
    ]
    
    # MinerU configuration from environment variables
    parser = os.getenv("PARSER", "mineru")
    parse_method = os.getenv("PARSE_METHOD", "auto")
    enable_image = os.getenv("ENABLE_IMAGE_PROCESSING", "true").lower() == "true"
    enable_table = os.getenv("ENABLE_TABLE_PROCESSING", "true").lower() == "true"
    enable_equation = os.getenv("ENABLE_EQUATION_PROCESSING", "true").lower() == "true"
    device = os.getenv("MINERU_DEVICE_MODE", "auto")  # cuda, cpu, or auto (MinerU reads this directly)
    
    # CRITICAL: MinerU reads MINERU_DEVICE_MODE from environment, NOT from RAGAnythingConfig
    # Ensure it's set in the current process environment so MinerU subprocess inherits it
    os.environ["MINERU_DEVICE_MODE"] = device
    
    # Note: All other MinerU variables (MINERU_LANG, MINERU_FORMULA_ENABLE, MINERU_TABLE_MERGE_ENABLE,
    # MINERU_PDF_RENDER_TIMEOUT, CUDA_VISIBLE_DEVICES, HF_TOKEN, HF_HUB_DISABLE_SYMLINKS_WARNING, etc.)
    # are automatically inherited by MinerU subprocess from os.environ after dotenv loads .env
    
    # Create RAG-Anything configuration (does NOT accept device parameter)
    config = RAGAnythingConfig(
        working_dir=working_dir,
        parser=parser,
        parse_method=parse_method,
        enable_image_processing=enable_image,
        enable_table_processing=enable_table,
        enable_equation_processing=enable_equation,
    )
    
    # Define LLM function (xAI Grok wrapper)
    async def llm_model_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        return await openai_complete_if_cache(
            os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )
    
    # Define vision function (multimodal Grok wrapper)
    async def vision_model_func(prompt, system_prompt=None, history_messages=[], image_data=None, messages=None, **kwargs):
        if messages:
            return await openai_complete_if_cache(
                os.getenv("LLM_MODEL", "grok-4-fast-reasoning"), "", system_prompt=None, history_messages=[],
                messages=messages, api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        elif image_data:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}},
                    ],
                }
            ]
            if system_prompt:
                messages.insert(0, {"role": "system", "content": system_prompt})
            return await openai_complete_if_cache(
                os.getenv("LLM_MODEL", "grok-4-fast-reasoning"), "", system_prompt=None, history_messages=[],
                messages=messages,
                api_key=xai_api_key, base_url=xai_base_url, **kwargs
            )
        else:
            return await llm_model_func(prompt, system_prompt, history_messages, **kwargs)
    
    # Define embedding function with safety truncation (8K chunks can slightly exceed 8192 due to overlap)
    async def safe_embed_func(texts):
        """Truncate texts to 8192 tokens before embedding to handle edge cases"""
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")  # OpenAI tokenizer
        
        truncated_texts = []
        for text in texts:
            tokens = enc.encode(text)
            if len(tokens) > 8192:
                # Truncate to 8192 tokens and decode back to text
                truncated_tokens = tokens[:8192]
                truncated_text = enc.decode(truncated_tokens)
                truncated_texts.append(truncated_text)
            else:
                truncated_texts.append(text)
        
        return await openai_embed(truncated_texts, model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"), api_key=openai_api_key)
    
    # Get embedding dimension from environment (flexibility for different models)
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "3072"))
    
    embedding_func = EmbeddingFunc(
        embedding_dim=embedding_dim,
        max_token_size=8192,  # OpenAI text-embedding-3-large limit
        func=safe_embed_func,
    )
    
    # V2 Prompt Architecture: Prompts now load in json_extractor.py
    # Branch 037: V2 modular extraction prompts (~32K tokens, 23% reduction)
    # Architecture: prompts/extraction_v2/ with examples inline
    # - 01_core_extraction_philosophy.txt
    # - 02_entity_classification_rules.txt (includes 12 entity examples)
    # - 03_json_schema_specification.txt  
    # - 04_relationship_extraction_rules.txt (includes 11 relationship examples)
    # - _schema_mirror/*.txt (18 auto-generated entity definitions)
    # Loading handled by src/extraction/json_extractor.py _load_full_system_prompt()

    # Initialize RAG-Anything with custom configuration
    # IMPORTANT: LightRAG reads chunk_token_size from environment at import time
    # Don't override via lightrag_kwargs - let it use CHUNK_SIZE from .env
    
    # Build lightrag_kwargs with Neo4j configuration if enabled
    lightrag_kwargs = {
        "addon_params": {
            "entity_types": entity_types,
            # NOTE: V2 prompts load in json_extractor.py via _load_full_system_prompt()
            # NOTE: Fictional examples disabled via PROMPTS override below
        },
        # Chunking configuration comes from environment variables:
        # - CHUNK_SIZE controls chunk_token_size (default: 8192)
        # - CHUNK_OVERLAP_SIZE controls chunk_overlap_token_size (default: 1200)
        # LightRAG reads these at dataclass field initialization time
    }
    
    # Add Neo4j configuration if enabled (from config.py global_args setup)
    # Note: Neo4j connection details come from environment variables (NEO4J_URI, etc.)
    # LightRAG reads these automatically - we only need to specify graph_storage type
    if hasattr(global_args, 'graph_storage') and global_args.graph_storage == "Neo4JStorage":
        lightrag_kwargs["graph_storage"] = global_args.graph_storage
    
    _rag_anything = RAGAnything(
        config=config,
        llm_model_func=llm_model_func,
        vision_model_func=vision_model_func,
        embedding_func=embedding_func,
        lightrag_kwargs=lightrag_kwargs,
    )
    
    # CRITICAL: Ensure LightRAG is initialized BEFORE any document processing
    # This is required because process_document_complete_lightrag_api() accesses
    # self.lightrag.doc_status BEFORE calling _ensure_lightrag_initialized()
    result = await _rag_anything._ensure_lightrag_initialized()
    if not result.get("success", False):
        error_msg = result.get("error", "Unknown error")
        logger.error(f"Failed to initialize LightRAG: {error_msg}")
        raise RuntimeError(f"LightRAG initialization failed: {error_msg}")
    
    # CRITICAL: Override LightRAG's PROMPTS for government contracting precision
    # LightRAG always uses PROMPTS["entity_extraction_examples"] (does NOT check addon_params)
    # These examples contain Alex/Taylor/Jordan with conflicting entity types (person, equipment)
    # that contaminate our government contracting ontology (requirement, organization, etc.)
    from lightrag.prompt import PROMPTS
    PROMPTS["entity_extraction_examples"] = []  # Empty list = no examples injected
    logger.info("✅ Disabled LightRAG's fictional example entities (prevents ontology contamination)")
    
    # Override the main RAG response template (used by ALL query modes: local, global, naive, hybrid/mix)
    # Comprehensive government contracting-specific prompt modeled after LightRAG's structure
    PROMPTS["rag_response"] = """---Role---
You are an expert government contracting analyst and capture manager with deep expertise in federal RFP analysis, proposal development, and FAR/DFARS compliance. Your primary function is to synthesize information from a knowledge graph of RFP entities (requirements, evaluation factors, deliverables, clauses) and source document chunks to provide actionable capture intelligence.

---Goal---
Generate comprehensive, capture-grade responses that integrate facts from both the Knowledge Graph Data (entities/relationships) and Document Chunks in the **Context**. Provide professional analysis with technical depth suitable for capture teams, proposal managers, and business development professionals.

Consider the conversation history if provided to maintain conversational flow and avoid repeating information.

---Instructions---

1. Step-by-Step Synthesis Process:
   - Carefully determine the user's query intent in the context of the conversation history to fully understand their information need.
   - Scrutinize both `Knowledge Graph Data` (entities/relationships) and `Document Chunks` in the **Context**. Identify and extract ALL pieces of information directly relevant to answering the user query.
   - Weave the extracted facts into a coherent, professional narrative. Your knowledge must ONLY be used to formulate fluent sentences and connect ideas, NOT to introduce any external information.
   - Track the reference_id of document chunks that directly support the facts presented in the response.
   - Correlate reference_id with entries in the `Reference Document List` to generate appropriate citations.
   - Generate a **References** section at the end of the response. Each reference document must directly support the facts presented.
   - Do not generate anything after the reference section.

2. Government Contracting Domain Expertise:

   **A. Preserve RFP-Specific Terminology:**
   - Federal regulations: FAR clauses (FAR 52.219-9), DFARS provisions (DFARS 252.217-7028), agency supplements (AFFARS, NMCARS)
   - Contract structures: Section L (submission instructions), Section M (evaluation factors), Section C (PWS/SOW), Section H (special requirements)
   - Technical standards: ISO 9001:2015, NIST SP 800-171, NAVFAC P-307, TM 4790-14/2, MCO 4400.201
   - Deliverables: CDRL numbers (CDRL A001), DD Form 1423, submission frequencies
   - Logistics terminology: GCSS-MC, OMMS-NG, MCPIC, AMAL/ADAL blocks, CAPSET, CESE, prepositioning objectives
   - Procurement types: FFP, CPFF, T&M, IDIQ, cost realism analysis, unbalanced pricing
   - Evaluation methodology: Best value tradeoff, adjectival ratings (Outstanding/Good/Acceptable/Marginal/Unacceptable), past performance confidence assessments

   **B. Include Entity Metadata Contextually:**
   
   When discussing **Evaluation Factors**:
   - Numerical weights (percentage, points, or fraction): "Factor A: 40%"
   - Relative importance hierarchy: "significantly more important", "most important", "equal weight"
   - Subfactors with individual weights if hierarchical
   - Scoring criteria and evaluation methodology
   - Adjectival rating definitions specific to the factor
   
   When discussing **Requirements**:
   - Criticality level: MANDATORY (shall/must/will), IMPORTANT (should), OPTIONAL (may), INFORMATIONAL
   - Modal verbs: Exact phrasing from contract ("shall provide", "must ensure", "is responsible for")
   - Requirement type: FUNCTIONAL, PERFORMANCE, SECURITY, TECHNICAL, INTERFACE, MANAGEMENT, DESIGN, QUALITY
   - Labor drivers: Quantities, frequencies, coverage hours, shift requirements, staffing ratios
   - Material needs: Equipment lists, consumables, Government-Furnished Property (GFP)
   
   When discussing **Submission Instructions**:
   - Page limits: Exact numbers and what counts toward limits
   - Format requirements: Font size, margins, spacing, volume assignments
   - Submission deadlines and delivery methods
   - Restrictions: Cross-referencing rules, standalone requirements
   
   When discussing **Deliverables**:
   - CDRL identifiers and DD Form 1423 references
   - Submission frequency: Daily, weekly, monthly, quarterly, ad-hoc
   - Acceptance criteria and government approval processes
   - Relationships to requirements they fulfill or track
   
   When discussing **Clauses**:
   - Full clause numbers: FAR 52.219-9 Alternate II, DFARS 252.242-7005
   - Regulation type: FAR, DFARS, AFFARS, agency-specific supplements
   - Compliance implications and flow-down requirements
   
   When discussing **Performance Metrics**:
   - Measurement thresholds: "95% on-time delivery", "< 2% error rate"
   - Measurement methods: Inspection procedures, quality control plans
   - Distinction from requirements: Metrics MEASURE performance, requirements DEFINE obligations

   **C. Query-Specific Response Patterns:**
   
   For **Workload Analysis** queries (Basis of Estimate, FTE calculations, labor drivers):
   - Focus on quantifiable workload drivers: frequencies, quantities, hours, coverage requirements, equipment counts, facility sizes, customer volumes
   - EXCLUDE surveillance metrics, inspection measurements, and performance objectives (these measure outcomes, not workload)
   - Organize by operational area, facility, or SOW section for clarity
   - Include: Staffing requirements, shift coverage (24/7, peak hours), service frequencies, event counts, maintenance schedules, inventory cycles
   - Include: Equipment/facility scope (number of locations, square footage, capacity)
   - Include: Volume drivers (customer counts, transaction rates, deliverable frequencies)
   - Provide contextual summary of the section/appendix before detailed workload drivers
   
   For **Evaluation Factor** queries:
   - Provide regulatory context: FAR 15.3 best value, source selection methodology
   - List factors in descending order of importance with explicit weights
   - Detail subfactors, scoring criteria, and evaluation philosophy for each
   - Explain tradeoff methodology: How technical superiority is weighed against cost
   - Include submission guidance: Which volume addresses each factor, page limits
   - Highlight discriminators: Areas where proposals can differentiate (e.g., ISO certification, risk mitigation approaches)
   
   For **Compliance Analysis** queries:
   - Map Section L instructions to Section M evaluation factors (identify orphaned instructions or missing guidance)
   - Identify mandatory requirements (shall/must) vs. discretionary (may/can)
   - Flag potential traps: Conflicting requirements, ambiguous language, hidden page limit rules
   - Cite exact RFP sections for traceability: "PWS Para 3.2.1.4", "Section M.5.2.b"
   
   For **Requirement Traceability** queries:
   - Show requirement → evaluation factor mappings via EVALUATED_BY relationships
   - Identify requirements without clear evaluation linkage (scoring gaps)
   - Connect requirements to deliverables that track/fulfill them (TRACKED_BY, FULFILLS relationships)
   - Group by criticality level or evaluation factor for prioritization
   
   For **Win Theme / Discriminator** queries:
   - Identify strategic themes from the knowledge graph (STRATEGIC_THEME entities)
   - Connect themes to requirements and evaluation factors they support
   - Highlight areas of evaluation emphasis: Past performance relevance criteria, technical approach focus areas, management methodology priorities
   - Suggest proof points: Relevant experience, certifications, process maturity indicators

   **D. Cite RFP Sources Explicitly:**
   - Document sections: "Section M.5.2", "PWS Para 3.4.1.2", "Appendix F.2.3.1"
   - Clause references: "FAR 52.219-8", "DFARS 252.217-7028 (Over and Above Work)"
   - Entity source_id fields from Knowledge Graph Data for traceability
   - Relationship descriptions that explain connections between entities
   - Document chunks via reference_id correlated to Reference Document List

3. Professional Narrative Structure:
   - Use markdown formatting: Headings (##, ###), bold text, bullet points, numbered lists for clarity
   - Provide context before detail: Regulatory framework, evaluation philosophy, scope of work overview
   - Group logically: By evaluation factor, requirement type, compliance area, organizational structure, operational phase, or facility location
   - Maintain analytical flow: Explain significance, relationships, tradeoffs, and capture implications (not just lists)
   - Include technical depth: Specific subfactors, compliance standards, performance metrics, risk areas, staffing qualifications
   - Use structured formats for complex data: Tables for comparisons, bullet hierarchies for subfactors, numbered lists for processes

4. Content Grounding & Accuracy:
   - Strictly adhere to the provided **Context**; DO NOT invent, assume, or infer any information not explicitly stated in the Knowledge Graph Data or Document Chunks.
   - If the answer cannot be found in the **Context**, state clearly: "I do not have enough information in the provided RFP documents to answer this question." Do not attempt to guess or use external knowledge.
   - The response MUST be in the same language as the user query.
   - The response MUST utilize Markdown formatting for enhanced clarity and structure.
   - The response should be presented in {response_type}.

5. References Section Format:
   - The References section should be under heading: `### References`
   - Reference list entries should adhere to the format: `- [n] Document Title` (do not include a caret `^` after opening square bracket `[`)
   - The Document Title in the citation must retain its original language
   - Output each citation on an individual line
   - Provide maximum of 5 most relevant citations
   - Do not generate footnotes section or any comment, summary, or explanation after the references

6. Reference Section Example:
```
### References
- [1] M6700425R0007 MCPP II DRAFT RFP 23 MAY 25.pdf
- [2] Atch 1 ADAB ISS PWS_4 April 25.pdf
- [3] Section M Evaluation Factors.pdf
```

7. Additional Instructions: {user_prompt}

---Context---
{context_data}"""
    
    logger.info("✅ Overrode LightRAG rag_response with comprehensive government contracting domain prompt")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Startup Configuration Summary
    # ═══════════════════════════════════════════════════════════════════════════════
    
    # ANSI color codes
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    logger.info("")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{BOLD}{MAGENTA}🎯 CONFIGURATION{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info(f"{GREEN}Entity Types:{RESET} {BOLD}{len(entity_types)}{RESET} specialized (organization, requirement, evaluation_factor, etc.)")
    logger.info(f"{GREEN}Parser:{RESET} {BOLD}MinerU 2.6.4{RESET} | Device: {BOLD}{GREEN if device == 'cuda' else YELLOW}{device.upper()}{RESET} | Method: {parse_method.upper()}")
    logger.info(f"{GREEN}Multimodal:{RESET} Images, Tables, Equations {BOLD}{GREEN}ENABLED{RESET}")
    logger.info(f"{GREEN}Advanced:{RESET} Formula Recognition, Table Merge {BOLD}{GREEN}ENABLED{RESET} | Timeout: {YELLOW}600s{RESET}")
    logger.info(f"{CYAN}{'═' * 80}{RESET}")
    logger.info("")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # COMPATIBILITY FIX: RAG-Anything 1.2.8 + LightRAG 1.4.9.3 doc_status schema
    # ═══════════════════════════════════════════════════════════════════════════════
    # Issue: RAG-Anything writes extra fields that LightRAG 1.4.9.3 doesn't support:
    #        - 'multimodal_processed' (bool) - tracks multimodal processing completion
    #        - 'multimodal_content' (list) - multimodal item metadata
    #        - 'scheme_name' (str) - document scheme identifier
    #
    # RAG-Anything also uses 'handling' status (not in LightRAG's DocStatus enum)
    #
    # Solution: Wrap BOTH write (upsert) and read (get_by_id, get_docs_paginated) to
    #           filter incompatible fields and normalize statuses
    # ═══════════════════════════════════════════════════════════════════════════════
    from lightrag.base import DocStatus
    original_upsert = _rag_anything.lightrag.doc_status.upsert
    original_get_by_id = _rag_anything.lightrag.doc_status.get_by_id
    original_get_docs_paginated = _rag_anything.lightrag.doc_status.get_docs_paginated
    
    # Fields that RAG-Anything writes but LightRAG 1.4.9.3 DocProcessingStatus doesn't accept
    INCOMPATIBLE_FIELDS = {'multimodal_processed', 'multimodal_content', 'scheme_name'}
    
    # Valid LightRAG statuses (from lightrag/base.py DocStatus enum)
    VALID_STATUSES = {
        DocStatus.PENDING.value,      # 'pending'
        DocStatus.PROCESSING.value,   # 'processing'
        DocStatus.PREPROCESSED.value, # 'multimodal_processed'
        DocStatus.PROCESSED.value,    # 'processed'
        DocStatus.FAILED.value,       # 'failed'
    }
    
    def filter_doc_data(doc_data: dict) -> dict:
        """Remove incompatible fields from doc_data"""
        return {k: v for k, v in doc_data.items() if k not in INCOMPATIBLE_FIELDS}
    
    async def filtered_upsert(data: dict):
        """Filter incompatible fields and normalize statuses for LightRAG 1.4.9.3"""
        filtered_data = {}
        for doc_id, doc_data in data.items():
            # Create a copy without incompatible fields
            filtered_doc_data = filter_doc_data(doc_data)
            
            # Normalize RAG-Anything statuses to LightRAG statuses
            if 'status' in filtered_doc_data:
                status = filtered_doc_data['status']
                # Handle both string and enum values
                status_value = status.value if hasattr(status, 'value') else status
                
                # Map RAG-Anything statuses to valid LightRAG statuses
                if status_value == 'handling':
                    filtered_doc_data['status'] = DocStatus.PROCESSING.value
                elif status_value == 'ready':
                    filtered_doc_data['status'] = DocStatus.PENDING.value
                elif status_value not in VALID_STATUSES:
                    logger.warning(f"Unknown status '{status_value}' for doc {doc_id}, mapping to PROCESSING")
                    filtered_doc_data['status'] = DocStatus.PROCESSING.value
            
            filtered_data[doc_id] = filtered_doc_data
        return await original_upsert(filtered_data)
    
    async def filtered_get_by_id(doc_id: str):
        """Get doc_status with incompatible fields filtered"""
        result = await original_get_by_id(doc_id)
        if result and isinstance(result, dict):
            return filter_doc_data(result)
        return result
    
    async def filtered_get_docs_paginated(*args, **kwargs):
        """Get paginated docs with incompatible fields filtered"""
        result = await original_get_docs_paginated(*args, **kwargs)
        if result and isinstance(result, tuple) and len(result) >= 2:
            docs_with_ids, total_count = result[0], result[1]
            # Filter each document's data
            filtered_docs = []
            for doc_id, doc_data in docs_with_ids:
                filtered_docs.append((doc_id, filter_doc_data(doc_data)))
            return (filtered_docs, total_count), *result[2:]
        return result
    
    _rag_anything.lightrag.doc_status.upsert = filtered_upsert
    _rag_anything.lightrag.doc_status.get_by_id = filtered_get_by_id
    _rag_anything.lightrag.doc_status.get_docs_paginated = filtered_get_docs_paginated
    # ═════════════════════════════════════════════════════════════════════════════
    
    return _rag_anything


def get_rag_instance():
    """Get the global RAG-Anything instance
    
    Returns:
        RAGAnything: The initialized instance, or None if not yet initialized
    """
    return _rag_anything
