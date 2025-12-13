"""
Government Contracting Processors

NOTE: Custom processors (GovconMultimodalProcessor, GovconKGProcessor) have been
removed as of Issue #42. The lightrag_llm_adapter now handles ALL entity extraction
with the full 121K ontology prompt, eliminating the need for custom processors.

RAG-Anything's default processors generate descriptions for multimodal content,
which then flow through LightRAG's extraction pipeline → lightrag_llm_adapter.
"""

__all__ = []
