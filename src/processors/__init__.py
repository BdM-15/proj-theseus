"""
Government Contracting Modal Processors

Custom processors for RAG-Anything that apply domain-specific ontology
to multimodal content (tables, images, equations).
"""

from .govcon_multimodal_processor import GovconMultimodalProcessor

__all__ = ["GovconMultimodalProcessor"]
