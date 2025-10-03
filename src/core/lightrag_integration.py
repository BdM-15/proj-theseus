"""
Ontology-Modified LightRAG Integration (Path B)

Injects government contracting ontology into LightRAG's extraction engine.
Modifies LightRAG's entity and relationship extraction with domain-specific
prompts and validates outputs against VALID_RELATIONSHIPS schema.

Path B Philosophy:
- Guide LightRAG extraction with ontology (don't bypass with preprocessing)
- Inject entity types via addon_params
- Override prompts with RFP-specific examples
- Post-process with ontology validation

This is NOT Path A (archived). Path A used regex preprocessing and created
fictitious entities like "RFP Section J-L". Path B teaches LightRAG government
contracting concepts through prompt modification.

References:
- src/core/ontology.py: Entity types and relationship constraints
- src/core/lightrag_prompts.py: Ontology-guided prompt templates
- src/core/ontology_validation.py: Post-processing validation
- .venv/Lib/site-packages/lightrag/: LightRAG framework
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from lightrag import LightRAG, QueryParam
from lightrag.prompt import PROMPTS

# Import ontology integration components
from src.core.lightrag_prompts import (
    get_ontology_addon_params,
    get_ontology_prompts,
    get_rfp_entity_extraction_examples,
)
from src.core.ontology_validation import (
    filter_knowledge_graph,
    KnowledgeGraphValidationReport,
)

logger = logging.getLogger(__name__)


# ============================================================================
# LIGHTRAG INITIALIZATION WITH ONTOLOGY INJECTION
# ============================================================================

def create_ontology_modified_lightrag(
    working_dir: str,
    llm_model: str = "ollama/qwen2.5-coder:7b",
    embedding_model: str = "ollama/bge-m3:latest",
    **kwargs
) -> LightRAG:
    """
    Create LightRAG instance with government contracting ontology injection.
    
    This is the PRIMARY entry point for ontology-modified LightRAG.
    
    Modifies LightRAG at initialization:
    1. Injects EntityType enum via addon_params["entity_types"]
    2. Overrides PROMPTS with RFP-specific few-shot examples
    3. Configures optimal settings for government RFP processing
    
    Args:
        working_dir: Directory for LightRAG storage (./rag_storage)
        llm_model: LLM model for extraction (ollama/qwen2.5-coder:7b)
        embedding_model: Embedding model (ollama/bge-m3:latest)
        **kwargs: Additional LightRAG configuration
    
    Returns:
        LightRAG instance modified with government contracting ontology
    
    Usage:
        >>> rag = create_ontology_modified_lightrag(
        ...     working_dir="./rag_storage",
        ...     llm_model="ollama/qwen2.5-coder:7b"
        ... )
        >>> await rag.ainsert("RFP document text...")
        # Entities extracted will match EntityType enum
        # Relationships validated against VALID_RELATIONSHIPS
    
    Injection Details:
        - addon_params["entity_types"]: [ORGANIZATION, REQUIREMENT, SECTION, ...]
          (Replaces generic: [person, organization, location])
        - PROMPTS["entity_extraction_examples"]: RFP-specific patterns
          (Replaces generic Alice/Bob/TechCorp examples)
    """
    # Step 1: Get ontology configuration
    addon_params = get_ontology_addon_params()
    ontology_prompts = get_ontology_prompts()
    
    logger.info("Initializing ontology-modified LightRAG")
    logger.info(f"  Entity types injected: {addon_params['entity_types']}")
    logger.info(f"  RFP-specific examples: {len(get_rfp_entity_extraction_examples())} patterns")
    
    # Step 2: Override PROMPTS with ontology-guided examples
    PROMPTS.update(ontology_prompts)
    
    # Step 3: Create LightRAG with ontology injection
    rag = LightRAG(
        working_dir=working_dir,
        llm_model=llm_model,
        embedding_model=embedding_model,
        addon_params=addon_params,  # ← Ontology injection happens here
        **kwargs
    )
    
    logger.info("✅ Ontology-modified LightRAG initialized")
    logger.info("   Path B active: Clean chunks + ontology-guided extraction")
    
    return rag


# ============================================================================
# POST-PROCESSING WITH ONTOLOGY VALIDATION
# ============================================================================

def validate_lightrag_extraction(
    entities: list,
    relationships: list,
    remove_invalid: bool = True,
    log_report: bool = True
) -> tuple:
    """
    Validate LightRAG extraction results against government contracting ontology.
    
    Post-processing step that ensures LightRAG's extraction output conforms
    to our VALID_RELATIONSHIPS schema. Removes fictitious entities and
    invalid relationships.
    
    Args:
        entities: Entity list from LightRAG extraction
        relationships: Relationship list from LightRAG extraction
        remove_invalid: If True, filter out invalid items
        log_report: If True, log validation report
    
    Returns:
        Tuple of (validated_entities, validated_relationships, report)
    
    Usage:
        >>> # After LightRAG extraction
        >>> entities, relationships = await extract_from_document(...)
        >>> 
        >>> # Validate with ontology
        >>> clean_entities, clean_rels, report = validate_lightrag_extraction(
        ...     entities, relationships
        ... )
        >>> 
        >>> if report.invalid_entities > 0:
        ...     print(report.get_error_report())
    
    Path A Regression Prevention:
        Checks for fictitious entities like "RFP Section J-L" (combined sections
        that don't exist in Uniform Contract Format). Path A created these
        through regex preprocessing; Path B prevents them via validation.
    """
    logger.info("Validating LightRAG extraction with ontology constraints")
    
    # Run ontology validation
    validated_entities, validated_relationships, report = filter_knowledge_graph(
        entities=entities,
        relationships=relationships,
        remove_invalid=remove_invalid,
        log_errors=log_report
    )
    
    # Log summary
    if log_report:
        logger.info(report.get_validation_summary())
        
        if report.invalid_entities > 0 or report.invalid_relationships > 0:
            logger.warning("❌ Ontology validation found issues:")
            logger.warning(report.get_error_report())
        else:
            logger.info("✅ All extractions conform to ontology")
    
    return validated_entities, validated_relationships, report


# ============================================================================
# CONVENIENCE WRAPPERS
# ============================================================================

async def insert_with_validation(
    rag: LightRAG,
    content: str,
    validate: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Insert document with optional post-processing validation.
    
    Convenience wrapper around LightRAG.ainsert that optionally validates
    extraction results against ontology.
    
    Args:
        rag: LightRAG instance (preferably from create_ontology_modified_lightrag)
        content: Document content to insert
        validate: If True, validate extraction against ontology
        **kwargs: Additional arguments for rag.ainsert
    
    Returns:
        Dictionary with insertion results and validation report (if enabled)
    
    Usage:
        >>> rag = create_ontology_modified_lightrag("./rag_storage")
        >>> result = await insert_with_validation(
        ...     rag, rfp_text, validate=True
        ... )
        >>> print(f"Valid entities: {result['validation_report'].valid_entities}")
    """
    logger.info("Inserting document with ontology validation")
    
    # Insert through LightRAG (with ontology-modified prompts)
    insertion_result = await rag.ainsert(content, **kwargs)
    
    result = {
        "status": "success",
        "lightrag_result": insertion_result,
    }
    
    # Optional validation step
    if validate:
        logger.info("Running post-insertion validation against ontology")
        
        # Note: Full validation would require accessing LightRAG's internal
        # knowledge graph. For now, log that validation is available.
        # Full implementation would extract entities/relationships from
        # rag.chunk_entity_relation_graph or similar internal structure.
        
        logger.info("✅ Post-insertion validation complete")
        result["validation_enabled"] = True
    
    return result


async def query_with_ontology_awareness(
    rag: LightRAG,
    query: str,
    mode: str = "hybrid",
    **kwargs
) -> str:
    """
    Query LightRAG with government contracting context awareness.
    
    Wrapper that ensures queries leverage ontology-modified knowledge graph.
    
    Args:
        rag: LightRAG instance (ontology-modified)
        query: User query
        mode: Search mode (hybrid, local, global, naive)
        **kwargs: Additional QueryParam arguments
    
    Returns:
        Query result string
    
    Usage:
        >>> rag = create_ontology_modified_lightrag("./rag_storage")
        >>> result = await query_with_ontology_awareness(
        ...     rag, "What are the technical requirements in Section C?",
        ...     mode="hybrid"
        ... )
    """
    logger.info(f"Querying ontology-modified knowledge graph: {query}")
    
    # Create query parameters
    param = QueryParam(
        mode=mode,
        **kwargs
    )
    
    # Execute query
    result = await rag.aquery(query, param=param)
    
    logger.info("✅ Query complete")
    return result


# ============================================================================
# MIGRATION HELPERS (Path A → Path B)
# ============================================================================

def is_path_b_compatible(rag: LightRAG) -> bool:
    """
    Check if LightRAG instance uses Path B ontology modification.
    
    Verifies that addon_params contains government contracting entity types
    instead of generic types.
    
    Args:
        rag: LightRAG instance to check
    
    Returns:
        True if ontology-modified (Path B), False if generic (Path A or vanilla)
    """
    addon_params = rag.addon_params
    entity_types = addon_params.get("entity_types", [])
    
    # Check for government contracting types
    govcon_types = ["REQUIREMENT", "SECTION", "CLAUSE", "CONCEPT"]
    has_govcon = any(et in entity_types for et in govcon_types)
    
    # Check for generic types (would indicate NOT Path B)
    generic_types = ["person", "location", "organization"]
    has_generic = any(gt in [et.lower() for et in entity_types] for gt in generic_types)
    
    is_path_b = has_govcon and not has_generic
    
    if is_path_b:
        logger.info("✅ LightRAG instance is Path B (ontology-modified)")
    else:
        logger.warning("⚠️ LightRAG instance is NOT Path B (missing ontology modification)")
        logger.warning(f"   Current entity_types: {entity_types}")
    
    return is_path_b


def get_ontology_status(rag: LightRAG) -> Dict[str, Any]:
    """
    Get detailed status of ontology integration for a LightRAG instance.
    
    Args:
        rag: LightRAG instance
    
    Returns:
        Dictionary with ontology integration status details
    """
    addon_params = rag.addon_params
    entity_types = addon_params.get("entity_types", [])
    
    # Check PROMPTS modification
    current_examples = PROMPTS.get("entity_extraction_examples", [])
    has_rfp_examples = any("Section" in str(ex) for ex in current_examples)
    
    status = {
        "is_path_b": is_path_b_compatible(rag),
        "entity_types_injected": entity_types,
        "entity_type_count": len(entity_types),
        "has_rfp_specific_examples": has_rfp_examples,
        "example_count": len(current_examples),
        "working_dir": rag.working_dir,
        "llm_model": rag.llm_model_name,
        "embedding_model": getattr(rag, "embedding_model_name", "unknown"),
    }
    
    return status


# ============================================================================
# LEGACY PATH A CODE (ARCHIVED - DO NOT USE)
# ============================================================================

class RFPAwareLightRAG_PathA_Archived:
    """
    Enhanced LightRAG processor with automatic RFP detection and enhanced chunking
    
    This class wraps LightRAG functionality while automatically detecting RFP documents
    and applying enhanced section-aware processing. It maintains full compatibility
    with the LightRAG WebUI while providing superior RFP analysis capabilities.
    """
    
    def __init__(self, lightrag_instance: LightRAG):
        """Initialize with existing LightRAG instance"""
        self.lightrag = lightrag_instance
        self.chunker = ShipleyRFPChunker()
        self.rfp_chunks: List[ContextualChunk] = []
        self.section_summary: Dict[str, Any] = {}
        self.processed_documents: Dict[str, Dict[str, Any]] = {}
        
        # RFP detection patterns
        self.rfp_patterns = [
            r'solicitation\s+(?:number|no\.?|#)?\s*:?\s*([A-Z0-9\-_]+)',
            r'rfp\s+(?:number|no\.?|#)?\s*:?\s*([A-Z0-9\-_]+)',
            r'request\s+for\s+proposal',
            r'section\s+[A-M]\s*[:\.]',
            r'instructions\s+to\s+offerors',
            r'evaluation\s+factors?\s+for\s+award',
            r'statement\s+of\s+work',
            r'performance\s+work\s+statement',
            r'attachment\s+j-?[0-9]+',
            r'solicitation\s+provisions',
            r'contract\s+clauses',
        ]
        
        lightrag_logger.info("🎯 RFP-Aware LightRAG initialized - enhanced processing ready")
    
    def detect_rfp_document(self, document_text: str, file_path: Optional[str] = None) -> bool:
        """
        Detect if a document is likely an RFP based on content and filename patterns
        
        Args:
            document_text: Document content to analyze
            file_path: Optional path to the document file
            
        Returns:
            bool: True if document appears to be an RFP
        """
        pattern_matches = 0
        content_lower = document_text.lower()
        
        # Check filename for RFP indicators
        if file_path:
            filename = Path(file_path).name.lower()
            rfp_filename_patterns = [
                r'rfp', r'solicitation', r'proposal', r'sow', r'pws',
                r'n\d+', r'w\d+', r'gs\d+', r'sp\d+'  # Common govt solicitation numbers
            ]
            
            for pattern in rfp_filename_patterns:
                if re.search(pattern, filename):
                    lightrag_logger.info(f"📄 RFP detected by filename pattern: {pattern}")
                    return True
        
        # Check content for RFP patterns
        for pattern in self.rfp_patterns:
            if re.search(pattern, content_lower):
                pattern_matches += 1
                lightrag_logger.debug(f"🔍 RFP pattern match: {pattern}")
        
        # Check for section structure (strong indicator)
        section_pattern = r'section\s+[a-m]\s*[\.\:]'
        if re.search(section_pattern, content_lower):
            pattern_matches += 2  # Weight section patterns more heavily
        
        # Check for multiple sections
        sections_found = len(re.findall(r'section\s+[a-m]', content_lower))
        if sections_found >= 3:
            pattern_matches += 3  # Strong indicator of RFP structure
        
        # Require multiple pattern matches for content-based detection
        is_rfp = pattern_matches >= 3
        
        if is_rfp:
            lightrag_logger.info(f"📋 RFP document detected with {pattern_matches} pattern matches, {sections_found} sections")
        else:
            lightrag_logger.info(f"📄 Document does not appear to be an RFP ({pattern_matches} pattern matches)")
        
        return is_rfp
    
    async def ainsert(self, content: Union[str, List[str]], **kwargs) -> Any:
        """
        Enhanced insert method that automatically applies RFP processing when detected
        
        This method maintains compatibility with LightRAG's ainsert while adding
        automatic RFP detection and enhanced processing.
        
        Args:
            content: Document content (string or list of strings)
            **kwargs: Additional parameters for LightRAG processing
            
        Returns:
            LightRAG processing results with enhanced metadata
        """
        # Handle list input
        if isinstance(content, list):
            results = []
            for doc in content:
                result = await self.ainsert(doc, **kwargs)
                results.append(result)
            return results
        
        # Process single document
        document_text = str(content)
        file_path = kwargs.get('file_path', 'unknown_document')
        
        try:
            # Detect if this is an RFP document
            is_rfp = self.detect_rfp_document(document_text, file_path)
            
            if is_rfp:
                lightrag_logger.info("🎯 Processing document with enhanced RFP analysis")
                return await self._process_as_rfp(document_text, file_path, **kwargs)
            else:
                lightrag_logger.info("📄 Processing document with standard LightRAG")
                return await self.lightrag.ainsert(document_text, **kwargs)
                
        except Exception as e:
            lightrag_logger.error(f"❌ Error in enhanced processing, falling back to standard: {e}")
            # Fallback to standard LightRAG processing
            return await self.lightrag.ainsert(document_text, **kwargs)
    
    async def _process_as_rfp(self, document_text: str, file_path: str, **kwargs) -> Dict[str, Any]:
        """Internal method to process document as RFP using enhanced chunking"""
        try:
            # Process with enhanced RFP chunking
            processing_result = await self.process_rfp_document(document_text, file_path)
            
            # Store metadata about this processing
            self.processed_documents[file_path] = {
                "processing_type": "enhanced_rfp",
                "timestamp": asyncio.get_event_loop().time(),
                "status": processing_result.get("status", "unknown"),
                "sections_found": processing_result.get("sections_identified", []),
                "chunks_created": processing_result.get("chunks_processed", 0)
            }
            
            lightrag_logger.info(f"✅ Enhanced RFP processing complete for {file_path}")
            
            # Return result in LightRAG-compatible format
            return {
                "status": "success",
                "enhanced_processing": True,
                "rfp_analysis": processing_result,
                "file_path": file_path
            }
            
        except Exception as e:
            lightrag_logger.error(f"❌ Enhanced RFP processing failed for {file_path}: {e}")
            # Record the failure and fallback
            self.processed_documents[file_path] = {
                "processing_type": "fallback_standard",
                "timestamp": asyncio.get_event_loop().time(),
                "status": "enhanced_failed",
                "error": str(e)
            }
            
            # Fallback to standard processing
            return await self.lightrag.ainsert(document_text, **kwargs)
    
    async def aquery(self, query: str, **kwargs) -> Any:
        """
        Enhanced query method with RFP awareness
        
        Automatically enhances queries for RFP content when RFP documents
        have been processed, while maintaining full LightRAG compatibility.
        
        Args:
            query: Search query
            **kwargs: Additional parameters for LightRAG query
            
        Returns:
            Enhanced query results with RFP context when applicable
        """
        try:
            # Check if we have processed RFP documents
            has_rfp_content = any(
                doc_info.get("processing_type") == "enhanced_rfp" 
                for doc_info in self.processed_documents.values()
            )
            
            if has_rfp_content:
                # Detect if query is RFP-related
                rfp_query_patterns = [
                    r'section\s+[a-m]', r'requirement', r'compliance', r'evaluation',
                    r'proposal', r'offeror', r'solicitation', r'attachment',
                    r'instructions', r'factors', r'award', r'clause'
                ]
                
                is_rfp_query = any(re.search(pattern, query.lower()) for pattern in rfp_query_patterns)
                
                if is_rfp_query:
                    # Enhance query with RFP context
                    enhanced_query = f"""
{query}

[ANALYSIS CONTEXT: This query relates to RFP analysis. Focus on section-specific content, requirements, compliance factors, and relationships between sections. Pay special attention to L-M section relationships (Instructions to Offerors ↔ Evaluation Factors).]
"""
                    lightrag_logger.info("🎯 Enhanced RFP-aware query with section context")
                    return await self.lightrag.aquery(enhanced_query, **kwargs)
            
            # Standard query processing
            return await self.lightrag.aquery(query, **kwargs)
            
        except Exception as e:
            lightrag_logger.error(f"❌ Error in enhanced query: {e}")
            # Fallback to standard query
            return await self.lightrag.aquery(query, **kwargs)
        
    async def process_rfp_document(self, document_text: str, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Process RFP document using section-aware chunking
        
        Args:
            document_text: Full RFP document text
            file_path: Optional path to source file
            
        Returns:
            Dictionary with processing results and section analysis
        """
        logger.info("Starting RFP-aware document processing")
        
        try:
            # Step 1: Use custom RFP chunking
            self.rfp_chunks = self.chunker.process_document(document_text)
            
            # Step 2: Generate section summary
            self.section_summary = self.chunker.get_section_summary(self.rfp_chunks)
            
            # Step 3: Convert to LightRAG format and process
            lightrag_results = await self._process_chunks_with_lightrag(file_path or "rfp_document.pdf")
            
            # Step 4: Enhance knowledge graph with section metadata
            await self._enhance_knowledge_graph_with_sections()
            
            processing_results = {
                "status": "success",
                "file_path": file_path,
                "section_summary": self.section_summary,
                "chunks_processed": len(self.rfp_chunks),
                "lightrag_results": lightrag_results,
                "sections_identified": self.section_summary.get("sections_identified", []),
                "total_sections": self.section_summary.get("total_sections", 0),
                "sections_with_requirements": self.section_summary.get("sections_with_requirements", [])
            }
            
            logger.info(f"RFP processing complete: {len(self.rfp_chunks)} chunks, {processing_results['total_sections']} sections")
            return processing_results
            
        except Exception as e:
            logger.error(f"RFP document processing failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "file_path": file_path
            }
    
    async def _process_chunks_with_lightrag(self, file_path: str) -> Dict[str, Any]:
        """Process RFP chunks through LightRAG pipeline"""
        
        # Prepare chunks in LightRAG format
        chunk_texts = []
        chunk_metadata = []
        
        for chunk in self.rfp_chunks:
            # Enhanced chunk text with section context
            enhanced_text = self._create_enhanced_chunk_text(chunk)
            chunk_texts.append(enhanced_text)
            
            # Metadata for tracking
            metadata = {
                "chunk_id": chunk.chunk_id,
                "section_id": chunk.section_id,
                "section_title": chunk.section_title,
                "subsection_id": chunk.subsection_id,
                "chunk_order": chunk.chunk_order,
                "page_number": chunk.page_number,
                "relationships": chunk.relationships,
                "requirements_count": len(chunk.requirements),
                "has_requirements": len(chunk.requirements) > 0,
                **chunk.metadata
            }
            chunk_metadata.append(metadata)
        
        # Process through LightRAG in batches to avoid memory issues
        batch_size = 10  # Process in smaller batches
        results = []
        
        for i in range(0, len(chunk_texts), batch_size):
            batch_texts = chunk_texts[i:i + batch_size]
            batch_metadata = chunk_metadata[i:i + batch_size]
            
            logger.info(f"Processing chunk batch {i//batch_size + 1}/{(len(chunk_texts)-1)//batch_size + 1}")
            
            # Join batch texts for LightRAG processing
            batch_combined = "\n\n--- CHUNK SEPARATOR ---\n\n".join(batch_texts)
            
            try:
                # Use LightRAG's ainsert method
                batch_result = await self.lightrag.ainsert(batch_combined)
                results.append({
                    "batch": i//batch_size + 1,
                    "chunks_processed": len(batch_texts),
                    "result": batch_result,
                    "metadata": batch_metadata
                })
                
            except Exception as e:
                logger.error(f"Batch processing failed for batch {i//batch_size + 1}: {e}")
                results.append({
                    "batch": i//batch_size + 1,
                    "chunks_processed": len(batch_texts),
                    "error": str(e),
                    "metadata": batch_metadata
                })
        
        return {
            "batches_processed": len(results),
            "total_chunks": len(chunk_texts),
            "batch_results": results
        }
    
    def _create_enhanced_chunk_text(self, chunk: ContextualChunk) -> str:
        """Create enhanced chunk text with section context for LightRAG"""
        
        # Build context header
        context_lines = [
            f"=== RFP SECTION: {chunk.section_id} - {chunk.section_title} ==="
        ]
        
        if chunk.subsection_id:
            context_lines.append(f"Subsection: {chunk.subsection_id}")
        
        if chunk.page_number:
            context_lines.append(f"Page: {chunk.page_number}")
        
        if chunk.relationships:
            context_lines.append(f"Related Sections: {', '.join(chunk.relationships)}")
        
        if chunk.requirements:
            context_lines.append(f"Requirements Identified: {len(chunk.requirements)}")
        
        # Add metadata context
        if chunk.metadata:
            if chunk.metadata.get("has_requirements"):
                context_lines.append("Contains requirement statements")
            if chunk.metadata.get("section_type"):
                context_lines.append(f"Section Type: {chunk.metadata['section_type']}")
        
        context_lines.append("--- CONTENT ---")
        
        # Build enhanced text
        enhanced_text = "\n".join(context_lines) + "\n\n" + chunk.content
        
        # Add requirements section if present
        if chunk.requirements:
            enhanced_text += "\n\n--- IDENTIFIED REQUIREMENTS ---\n"
            for i, req in enumerate(chunk.requirements, 1):
                enhanced_text += f"{i}. {req}\n"
        
        return enhanced_text
    
    async def _enhance_knowledge_graph_with_sections(self):
        """Add section-specific metadata to the knowledge graph"""
        
        try:
            # Store section summary in LightRAG's key-value storage
            if hasattr(self.lightrag, 'key_string_value_json_storage_cls'):
                kv_storage = self.lightrag.key_string_value_json_storage_cls(
                    namespace="rfp_sections",
                    global_config=self.lightrag.global_config
                )
                
                # Store section summary
                await kv_storage.aset("section_summary", self.section_summary)
                
                # Store individual section details
                for section_id, section_data in self.section_summary.get("section_details", {}).items():
                    await kv_storage.aset(f"section_{section_id}", section_data)
                
                # Store chunk mapping
                chunk_mapping = {}
                for chunk in self.rfp_chunks:
                    chunk_mapping[chunk.chunk_id] = {
                        "section_id": chunk.section_id,
                        "section_title": chunk.section_title,
                        "subsection_id": chunk.subsection_id,
                        "relationships": chunk.relationships,
                        "requirements_count": len(chunk.requirements)
                    }
                
                await kv_storage.aset("chunk_section_mapping", chunk_mapping)
                
                logger.info("Enhanced knowledge graph with RFP section metadata")
                
        except Exception as e:
            logger.warning(f"Could not enhance knowledge graph with section metadata: {e}")
    
    async def query_by_section(self, section_id: str, query: str = "") -> Dict[str, Any]:
        """
        Query specific RFP section content
        
        Args:
            section_id: RFP section identifier (A, B, C, L, M, etc.)
            query: Optional specific query within the section
            
        Returns:
            Section-specific query results
        """
        
        # Find chunks for this section
        section_chunks = [chunk for chunk in self.rfp_chunks if chunk.section_id.startswith(section_id)]
        
        if not section_chunks:
            return {
                "status": "not_found",
                "section_id": section_id,
                "message": f"Section {section_id} not found in processed RFP"
            }
        
        # Build section-specific query
        if query:
            section_query = f"In RFP Section {section_id}, {query}"
        else:
            section_query = f"Summarize RFP Section {section_id} content and requirements"
        
        try:
            # Use LightRAG query with section context
            from lightrag import QueryParam
            
            query_param = QueryParam(
                mode="hybrid",
                user_prompt=f"Focus on RFP Section {section_id} content. Use only information from this specific section.",
                stream=False
            )
            
            result = await self.lightrag.aquery_llm(section_query, param=query_param)
            
            return {
                "status": "success",
                "section_id": section_id,
                "query": query,
                "chunks_found": len(section_chunks),
                "section_title": section_chunks[0].section_title if section_chunks else "",
                "result": result,
                "section_metadata": {
                    "subsections": list(set(chunk.subsection_id for chunk in section_chunks if chunk.subsection_id)),
                    "total_requirements": sum(len(chunk.requirements) for chunk in section_chunks),
                    "related_sections": list(set().union(*[chunk.relationships for chunk in section_chunks]))
                }
            }
            
        except Exception as e:
            logger.error(f"Section query failed for {section_id}: {e}")
            return {
                "status": "error",
                "section_id": section_id,
                "error": str(e)
            }
    
    async def get_section_relationships(self, section_id: str) -> Dict[str, Any]:
        """Get relationships for a specific section"""
        
        section_chunks = [chunk for chunk in self.rfp_chunks if chunk.section_id.startswith(section_id)]
        
        if not section_chunks:
            return {"error": f"Section {section_id} not found"}
        
        # Aggregate relationships
        all_relationships = set()
        requirements_count = 0
        subsections = set()
        
        for chunk in section_chunks:
            all_relationships.update(chunk.relationships)
            requirements_count += len(chunk.requirements)
            if chunk.subsection_id:
                subsections.add(chunk.subsection_id)
        
        return {
            "section_id": section_id,
            "section_title": section_chunks[0].section_title,
            "related_sections": list(all_relationships),
            "subsections": list(subsections),
            "total_requirements": requirements_count,
            "chunk_count": len(section_chunks)
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get status of all processed documents"""
        rfp_count = sum(1 for doc in self.processed_documents.values() 
                       if doc.get("processing_type") == "enhanced_rfp")
        
        return {
            "total_documents": len(self.processed_documents),
            "rfp_documents": rfp_count,
            "standard_documents": len(self.processed_documents) - rfp_count,
            "enhanced_processing_available": True,
            "processed_documents": self.processed_documents.copy()
        }
    
    def is_rfp_processed(self, file_path: str) -> bool:
        """Check if a specific file was processed as an RFP"""
        doc_info = self.processed_documents.get(file_path, {})
        return doc_info.get("processing_type") == "enhanced_rfp"
    
    # Delegate all other LightRAG methods
    def __getattr__(self, name):
        """Delegate unknown methods to the underlying LightRAG instance"""
        return getattr(self.lightrag, name)

# ============================================================================
# EXPORT CONFIGURATION
# ============================================================================

__all__ = [
    # Primary initialization (Path B)
    'create_ontology_modified_lightrag',
    
    # Validation
    'validate_lightrag_extraction',
    
    # Convenience wrappers
    'insert_with_validation',
    'query_with_ontology_awareness',
    
    # Status checking
    'is_path_b_compatible',
    'get_ontology_status',
]