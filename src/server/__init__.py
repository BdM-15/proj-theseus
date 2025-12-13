"""
Server module for RAG-Anything + LightRAG integration

This module provides:
- Configuration (config.py): 18 entity types, API credentials, chunking settings
- Initialization (initialization.py): RAGAnything instance with custom prompts
- Routes (routes.py): FastAPI endpoints + semantic post-processing

Usage:
    from src.server.config import configure_raganything_args
    from src.server.initialization import initialize_raganything
    from src.server.routes import create_insert_endpoint
"""

__all__ = [
    "configure_raganything_args",
    "initialize_raganything",
    "get_rag_instance",
    "create_insert_endpoint",
    "create_documents_upload_endpoint",
    "process_document_with_ucf_detection",
    # Legacy function (deprecated - use semantic_post_processor.enhance_knowledge_graph)
    "post_process_knowledge_graph",
]
