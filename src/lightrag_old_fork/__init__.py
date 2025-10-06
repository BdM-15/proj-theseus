"""
lightrag-govcon: Government Contracting Fork of LightRAG

Production fork specialized for federal RFP analysis with:
- LLM-native semantic document understanding (NO regex preprocessing)
- Government contracting ontology integration
- PydanticAI validation for guaranteed structure and zero contamination

Based on: lightrag-hku v1.4.9
Fork Version: v1.0.0-alpha
Fork Date: October 4, 2025
"""

from .lightrag import LightRAG as LightRAG, QueryParam as QueryParam

# Original LightRAG metadata
__lightrag_version__ = "v1.4.9"
__lightrag_author__ = "Zirui Guo"
__lightrag_url__ = "https://github.com/HKUDS/LightRAG"

# Fork metadata
__version__ = "v1.0.0-alpha"
__fork_name__ = "lightrag-govcon"
__fork_purpose__ = "Government Contracting RFP Analysis"
__fork_date__ = "2025-10-04"
__fork_author__ = "BdM-15"
__fork_url__ = "https://github.com/BdM-15/govcon-capture-vibe"

# Key modifications
__modifications__ = [
    "LLM-native semantic document structure analysis (replaces regex preprocessing)",
    "Government contracting ontology injection into extraction prompts",
    "PydanticAI validation pipeline for guaranteed structure",
    "Document isolation verification to prevent LLM contamination",
    "Domain-specific entity types: SECTION, REQUIREMENT, CLIN, FAR_CLAUSE, etc.",
    "Relationship constraints for valid government contracting patterns",
]
