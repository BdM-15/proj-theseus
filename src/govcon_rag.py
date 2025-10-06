"""
GovCon RAG-Anything Integration
================================
Branch 003: Cloud-based multimodal RAG with xAI Grok + OpenAI embeddings.

This module integrates RAG-Anything with custom government contracting processors
for comprehensive RFP document processing. Replaces the forked LightRAG approach
with a cleaner RAG-Anything architecture.

Architecture:
- RAG-Anything: Handles document parsing, multimodal extraction, KG construction
- xAI Grok 4 Fast Reasoning: Cloud LLM for entity extraction
- OpenAI text-embedding-3-large: 3072-dim embeddings for semantic search
- Custom Processors: 7 specialized processors for RFP sections A-M
- Ontology Validation: 12 entity types + relationship validation

Processing Flow:
1. RAG-Anything parses PDF with MinerU (multimodal: text, tables, images)
2. Custom processors extract govcon-specific entities from parsed content
3. LightRAG (wrapped by RAG-Anything) builds knowledge graph
4. Query interface provides ontology-aware retrieval

Performance Target:
- Navy MBOS RFP (71 pages): 10-15 minutes vs 8 hours local
- Cost: ~$2-5 per RFP (xAI Grok + OpenAI embeddings)
- Quality: 500-700 entities with 95%+ precision
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

# RAG-Anything imports
from raganything import RAGAnything, RAGAnythingConfig

# LightRAG core imports (used by RAG-Anything under the hood)
from lightrag import QueryParam
from lightrag.utils import EmbeddingFunc
from lightrag.llm.openai import openai_complete_if_cache, openai_embed

# Custom govcon processors
from src.processors.rfp_processors import (
    RFPSectionMetadataProcessor,
    ShipleyRequirementsProcessor,
    EvaluationFactorProcessor,
    CLINPricingProcessor,
    DeliverableProcessor,
    ClauseProcessor,
    AttachmentProcessor,
)

# Ontology validation
from src.core.ontology import (
    EntityType,
    RelationshipType,
    VALID_RELATIONSHIPS,
    is_valid_relationship,
)

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# LLM Function: xAI Grok 4 Fast Reasoning
# ============================================================================

async def xai_grok_llm_func(
    prompt: str,
    system_prompt: Optional[str] = None,
    history_messages: Optional[List[Dict[str, str]]] = None,
    keyword_extraction: bool = False,
    **kwargs
) -> str:
    """
    LLM function for xAI Grok 4 Fast Reasoning.
    
    Uses OpenAI-compatible API via openai_complete_if_cache.
    
    Args:
        prompt: User prompt for the LLM
        system_prompt: Optional system prompt
        history_messages: Optional conversation history
        keyword_extraction: Whether this is a keyword extraction task
        **kwargs: Additional arguments (temperature, max_tokens, etc.)
    
    Returns:
        LLM response string
    """
    return await openai_complete_if_cache(
        model=os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
        prompt=prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=os.getenv("LLM_BINDING_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1"),
        temperature=float(os.getenv("OPENAI_LLM_TEMPERATURE", "0.1")),
        **kwargs
    )


# ============================================================================
# Embedding Function: OpenAI text-embedding-3-large
# ============================================================================

async def openai_embedding_func(texts: List[str]) -> np.ndarray:
    """
    Embedding function for OpenAI text-embedding-3-large (3072-dim).
    
    Args:
        texts: List of text strings to embed
    
    Returns:
        Numpy array of embeddings (shape: [len(texts), 3072])
    """
    return await openai_embed(
        texts=texts,
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-large"),
        api_key=os.getenv("EMBEDDING_BINDING_API_KEY"),
        base_url=os.getenv("EMBEDDING_BINDING_HOST", "https://api.openai.com/v1"),
    )


# ============================================================================
# GovCon RAG-Anything Configuration
# ============================================================================

class GovConRAG:
    """
    Government Contracting RAG system with ontology-aware entity extraction.
    
    Integrates RAG-Anything with custom processors for RFP document processing.
    Validates entities against 12 govcon entity types and relationship schema.
    """
    
    def __init__(
        self,
        working_dir: Optional[str] = None,
        enable_multimodal: bool = True,
    ):
        """
        Initialize GovCon RAG system.
        
        Args:
            working_dir: Storage directory for RAG data
            enable_multimodal: Enable image/table/equation processing
        """
        self.working_dir = working_dir or os.getenv("WORKING_DIR", "./rag_storage")
        self.enable_multimodal = enable_multimodal
        
        # Create working directory if it doesn't exist
        Path(self.working_dir).mkdir(parents=True, exist_ok=True)
        
        # Initialize RAG-Anything
        self.rag: Optional[RAGAnything] = None
        
        logger.info(f"GovConRAG initialized with working_dir: {self.working_dir}")
    
    async def initialize(self):
        """
        Initialize RAG-Anything with custom configuration.
        
        Note: Custom govcon processors are registered separately after initialization.
        RAG-Anything automatically creates ImageModalProcessor, TableModalProcessor,
        EquationModalProcessor based on config. We'll add our custom govcon processors
        to complement the default ones.
        """
        logger.info("Initializing RAG-Anything with govcon configuration...")
        
        # Create embedding function wrapper for LightRAG
        embedding_func_wrapper = EmbeddingFunc(
            embedding_dim=int(os.getenv("EMBEDDING_DIM", "3072")),
            max_token_size=int(os.getenv("EMBEDDING_MAX_TOKEN_SIZE", "8192")),
            func=openai_embedding_func,
        )
        
        # Configure RAG-Anything
        config = RAGAnythingConfig(
            # Working directory for storage
            working_dir=self.working_dir,
            
            # Multimodal processing (MinerU)
            enable_image_processing=self.enable_multimodal and os.getenv("ENABLE_IMAGE_PROCESSING", "true").lower() == "true",
            enable_table_processing=self.enable_multimodal and os.getenv("ENABLE_TABLE_PROCESSING", "true").lower() == "true",
            enable_equation_processing=self.enable_multimodal and os.getenv("ENABLE_EQUATION_PROCESSING", "true").lower() == "true",
            
            # Context extraction for multimodal content
            context_window=int(os.getenv("CONTEXT_WINDOW", "2")),
            context_filter_content_types=os.getenv("CONTEXT_FILTER_CONTENT_TYPES", "text,table,image").split(","),
            
            # Parser configuration
            parser="mineru",  # Use MinerU for multimodal parsing
            parse_method="auto",
            parser_output_dir=os.path.join(self.working_dir, "parser_output"),
            display_content_stats=True,
        )
        
        # Initialize RAG-Anything
        # Note: This will automatically create default modal processors
        # We'll add our custom govcon processors after initialization
        self.rag = RAGAnything(
            config=config,
            llm_model_func=xai_grok_llm_func,
            vision_model_func=xai_grok_llm_func,  # Grok 4 supports multimodal (text+image)
            embedding_func=embedding_func_wrapper,
            lightrag_kwargs={
                # Additional LightRAG configuration
                "llm_model_name": os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
                "llm_model_kwargs": {
                    "timeout": int(os.getenv("LLM_TIMEOUT", "300")),
                },
                "chunk_token_size": int(os.getenv("CHUNK_SIZE", "800")),
                "chunk_overlap_token_size": int(os.getenv("CHUNK_OVERLAP_SIZE", "100")),
                "summary_max_tokens": int(os.getenv("SUMMARY_MAX_TOKENS", "1200")),
                "llm_model_max_async": int(os.getenv("MAX_ASYNC", "5")),
                "embedding_func_max_async": int(os.getenv("EMBEDDING_FUNC_MAX_ASYNC", "8")),
                "embedding_batch_num": int(os.getenv("EMBEDDING_BATCH_NUM", "10")),
                "top_k": int(os.getenv("TOP_K", "40")),
                "chunk_top_k": int(os.getenv("CHUNK_TOP_K", "20")),
                "enable_llm_cache": os.getenv("ENABLE_LLM_CACHE", "true").lower() == "true",
                "log_level": os.getenv("LOG_LEVEL", "INFO"),
                # Govcon-specific: Pass entity types to LightRAG
                "addon_params": {
                    "entity_types": [e.value for e in EntityType],  # 12 govcon entity types
                },
            },
        )
        
        logger.info("RAG-Anything initialized successfully")
        logger.info(f"Entity types: {[e.value for e in EntityType]}")
        logger.info(f"Multimodal processing: image={config.enable_image_processing}, "
                   f"table={config.enable_table_processing}, "
                   f"equation={config.enable_equation_processing}")
        
        # TODO: Register custom govcon processors after initialization
        # Custom processors will complement default ImageModalProcessor, TableModalProcessor
        # by adding govcon-specific entity extraction logic for RFP sections
    
    async def insert_document(self, file_path: str) -> Dict[str, Any]:
        """
        Insert RFP document into RAG system with multimodal processing.
        
        Args:
            file_path: Path to RFP PDF file
        
        Returns:
            Processing statistics (entities, relationships, chunks, etc.)
        """
        if not self.rag:
            raise RuntimeError("RAG not initialized. Call initialize() first.")
        
        logger.info(f"Processing document: {file_path}")
        
        # Process document with RAG-Anything
        # RAG-Anything handles:
        # 1. MinerU parsing (multimodal: text, tables, images)
        # 2. Default modal processor execution (images, tables, equations)
        # 3. LightRAG KG construction
        # Note: Custom govcon processors will be integrated in future enhancement
        await self.rag.process_document_complete(
            file_path=file_path,
            parse_method="auto",  # Auto-detect document type
        )
        
        logger.info(f"Document processed successfully: {file_path}")
        
        # Get statistics from LightRAG
        stats = await self.get_statistics()
        return stats
    
    async def query(
        self,
        query: str,
        mode: str = "hybrid",
        stream: bool = False,
    ) -> str:
        """
        Query the RAG system with ontology-aware retrieval.
        
        Args:
            query: Natural language query
            mode: Query mode ('naive', 'local', 'global', 'hybrid', 'mix')
            stream: Whether to stream the response
        
        Returns:
            Query response string
        """
        if not self.rag:
            raise RuntimeError("RAG not initialized. Call initialize() first.")
        
        logger.info(f"Query: {query} (mode={mode})")
        
        # Execute query using RAG-Anything's aquery method
        response = await self.rag.aquery(
            query=query,
            mode=mode,
            stream=stream,
        )
        
        return response
    
    def validate_entity(self, entity_type: str) -> bool:
        """
        Validate entity type against govcon ontology.
        
        Args:
            entity_type: Entity type string to validate
        
        Returns:
            True if valid entity type
        """
        try:
            EntityType(entity_type)
            return True
        except ValueError:
            logger.warning(f"Invalid entity type: {entity_type}")
            return False
    
    def validate_relationship(
        self,
        source_type: str,
        target_type: str,
        relation_type: str,
    ) -> bool:
        """
        Validate relationship against govcon ontology schema.
        
        Args:
            source_type: Source entity type
            target_type: Target entity type
            relation_type: Relationship type
        
        Returns:
            True if valid relationship
        """
        return is_valid_relationship(source_type, target_type, relation_type)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get RAG system statistics (entities, relationships, chunks, etc.).
        
        Returns:
            Statistics dictionary
        """
        if not self.rag:
            raise RuntimeError("RAG not initialized. Call initialize() first.")
        
        # Get configuration info from RAG-Anything
        config_info = self.rag.get_config_info()
        processor_info = self.rag.get_processor_info()
        
        # Combine into statistics
        stats = {
            "config": config_info,
            "processors": processor_info,
            "working_dir": self.working_dir,
        }
        
        return stats


# ============================================================================
# Convenience Functions
# ============================================================================

async def create_govcon_rag(
    working_dir: Optional[str] = None,
    enable_multimodal: bool = True,
) -> GovConRAG:
    """
    Create and initialize GovCon RAG system.
    
    Args:
        working_dir: Storage directory for RAG data
        enable_multimodal: Enable image/table/equation processing
    
    Returns:
        Initialized GovConRAG instance
    """
    rag = GovConRAG(
        working_dir=working_dir,
        enable_multimodal=enable_multimodal,
    )
    await rag.initialize()
    return rag


# ============================================================================
# Example Usage
# ============================================================================

async def main():
    """
    Example usage of GovCon RAG system.
    """
    # Create and initialize RAG
    rag = await create_govcon_rag()
    
    # Insert Navy MBOS RFP
    rfp_path = "./inputs/uploaded/N6945025R0003.pdf"
    if os.path.exists(rfp_path):
        logger.info(f"Processing RFP: {rfp_path}")
        stats = await rag.insert_document(rfp_path)
        logger.info(f"Processing complete: {stats}")
    else:
        logger.warning(f"RFP not found: {rfp_path}")
    
    # Example queries
    queries = [
        "What are the evaluation factors in Section M?",
        "What are the key requirements from Section L?",
        "What deliverables are required in Section F?",
        "What is the period of performance?",
    ]
    
    for query in queries:
        logger.info(f"\nQuery: {query}")
        response = await rag.query(query, mode="hybrid")
        logger.info(f"Response: {response[:200]}...")
    
    # Get statistics
    stats = await rag.get_statistics()
    logger.info(f"\nRAG Statistics: {stats}")


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Run example
    asyncio.run(main())
