"""
Government Contracting Processors

Issue #46 Part C: OntologyTableProcessor registered for structured table extraction.
Tables contain critical GovCon data (evaluation matrices, CDRLs, labor tables).

Architecture:
- OntologyTableProcessor: Formats tables preserving structure for extraction
- lightrag_llm_adapter: Still handles actual extraction with full ontology prompt
- No duplicate extraction - processor formats, adapter extracts

For text: lightrag_llm_adapter intercepts and uses full ontology prompt
For tables: OntologyTableProcessor formats → lightrag_llm_adapter extracts
"""

from src.processors.ontology_table_processor import OntologyTableProcessor

__all__ = ["OntologyTableProcessor"]
