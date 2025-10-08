"""
Server module for RAG-Anything + LightRAG integration

This module provides:
- Configuration (config.py): Entity types, API credentials, chunking settings
- Initialization (initialization.py): RAGAnything instance with custom prompts
- Routes (routes.py): FastAPI endpoints + Phase 6.1 auto-processing

Usage:
    from src.server.config import configure_raganything_args
    from src.server.initialization import initialize_raganything
    from src.server.routes import create_insert_endpoint, phase6_auto_processor
"""

__all__ = [
    "configure_raganything_args",
    "initialize_raganything",
    "get_rag_instance",
    "create_insert_endpoint",
    "phase6_auto_processor",
    "process_document_with_ucf_detection",
    "post_process_knowledge_graph",
]
