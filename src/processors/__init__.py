"""
Government Contracting Processors Package

GovconMultimodalProcessor: Issue #54 - Native LightRAG Architecture

This processor applies our govcon ontology to MinerU's textualized tables/images/equations.

Architecture (Issue #54 - Back to Basics):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MULTIMODAL:
  Stage 1: GovconMultimodalProcessor.generate_description_only()
    ├─ Generates govcon-focused text description via LLM
    └─ Returns description for LightRAG native extraction
  
  Stage 2-3: RAG-Anything handles chunking, storage, indexing
  
  Stage 4: LightRAG native extraction
    └─ Uses tuple-delimited format: entity<|#|>name<|#|>type<|#|>desc

TEXT:
  Stage 1-3: RAG-Anything chunks and stores text
  
  Stage 4: LightRAG native extraction
    ├─ Entity types from addon_params
    └─ Domain knowledge injected into PROMPTS["entity_extraction_system_prompt"]

RESULT: Native LightRAG extraction, no Pydantic/JSON translation layers
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Key Design Decisions (Issue #54):
- Processor: Generates govcon-focused text descriptions for multimodal
- LightRAG: Native tuple-delimited extraction for ALL content
- No Pydantic/JSON extraction layer (removed as over-engineering)
- RAG-Anything: Handles all chunking, storage, indexing, graph merging

The native LightRAG extraction is sufficient when properly configured:
- 18 entity types via addon_params["entity_types"]
- Domain knowledge prepended to PROMPTS["entity_extraction_system_prompt"]
"""

from src.processors.govcon_multimodal_processor import GovconMultimodalProcessor

__all__ = ["GovconMultimodalProcessor"]
