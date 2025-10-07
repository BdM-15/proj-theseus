"""
GovCon Capture Vibe - Ontology-Based RAG for Government Contracting

Phase 2+3: Ontology-Modified LightRAG System

A sophisticated RFP analysis system built on LightRAG with ontology-guided extraction.
Implements Shipley methodology through structured PydanticAI agents.

Architecture (Phase 2+3):
- core/: Ontology-modified LightRAG integration (Path B)
  - ontology.py: Entity types and relationship constraints  
  - lightrag_prompts.py: Ontology-guided extraction prompts
  - ontology_validation.py: Post-processing validation
  - lightrag_integration.py: Path B initialization
- agents/: PydanticAI structured agents for Shipley methodology
- models/: Pydantic models defining RFP data structures
- api/: FastAPI routes for RFP analysis endpoints
- utils/: Logging, performance monitoring, and utilities

This system injects government contracting ontology into LightRAG's extraction engine,
combining knowledge graphs with structured AI agents for comprehensive RFP analysis.
"""

# Core ontology components (Phase 2+3)
from .core import (
    EntityType,
    RelationshipType,
    VALID_RELATIONSHIPS,
    create_ontology_modified_lightrag,
    get_government_contracting_entity_types,
)

# Structured AI agents
from .agents import RFPAnalysisAgents, RequirementsExtractionOutput, RFPContext

# Data models
from .models import (
    RFPRequirement, ComplianceAssessment, RFPAnalysisResult,
    ComplianceLevel, RequirementType, ComplianceStatus, RiskLevel
)

# Utilities
from .utils import setup_logging, get_monitor

__version__ = "3.0.0"  # Phase 3: DELIVERABLE entity added
__all__ = [
    # Core ontology (Phase 2+3)
    'EntityType',
    'RelationshipType',
    'VALID_RELATIONSHIPS',
    'create_ontology_modified_lightrag',
    'get_government_contracting_entity_types',
    
    # AI agents
    'RFPAnalysisAgents',
    'RequirementsExtractionOutput',
    'RFPContext',
    
    # Data models
    'RFPRequirement',
    'ComplianceAssessment',
    'RFPAnalysisResult',
    'ComplianceLevel',
    'RequirementType',
    'ComplianceStatus', 
    'RiskLevel',
    
    # Utilities
    'setup_logging',
    'get_monitor'
]
