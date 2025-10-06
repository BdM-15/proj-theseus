"""
Government Contracting Extensions for LightRAG

Provides domain-specific enhancements for federal RFP analysis:
- Semantic document structure understanding (LLM-native, NO regex)
- Ontology-enhanced extraction with government contracting entity types
- PydanticAI validation for guaranteed structure and zero contamination
- Document isolation verification
"""

from .semantic_analyzer import SemanticRFPAnalyzer
from .ontology_integration import OntologyInjector
from .pydantic_validation import ExtractionValidator
from .quality_assurance import QualityAssuranceFramework

__all__ = [
    'SemanticRFPAnalyzer',
    'OntologyInjector', 
    'ExtractionValidator',
    'QualityAssuranceFramework',
]
