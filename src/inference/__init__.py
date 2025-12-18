"""
Relationship Inference Module

LLM-powered semantic relationship inference for Neo4j knowledge graphs.
Implements core algorithms for government contracting RFPs:

1. Instruction-Evaluation Linking: SUBMISSION_INSTRUCTION → EVALUATION_FACTOR (GUIDES)
2. Evaluation Hierarchy: EVALUATION_FACTOR → EVALUATION_FACTOR (CHILD_OF)
3. Deliverable Traceability: DELIVERABLE → REQUIREMENT/EVALUATION_FACTOR (FULFILLS/EVALUATED_BY)
4. Requirement Clustering: REQUIREMENT → REQUIREMENT (RELATED_TO)
5. Annex/Attachment Linking: DOCUMENT → REQUIREMENT/CLAUSE (DEFINES/PROVIDES_CONTEXT)
6. Orphan Resolution: Unconnected entities → related entities
7. PWS Workload Enrichment: BOE metadata extraction for requirements

Architecture (Issue #54 - Back to Basics):
- Entity extraction uses native LightRAG with 18 govcon types
- Post-processing uses Pydantic for relationship validation (InferredRelationship)
- No LLM-based entity type correction needed - native extraction handles it

Usage:
    from src.inference.semantic_post_processor import enhance_knowledge_graph
    from src.inference.neo4j_graph_io import Neo4jGraphIO, group_entities_by_type
    
    stats = await enhance_knowledge_graph(rag_storage_path, llm_func)
"""

from src.inference.neo4j_graph_io import (
    Neo4jGraphIO,
    group_entities_by_type,
)

__all__ = [
    # Neo4j Graph I/O exports
    "Neo4jGraphIO",
    "group_entities_by_type",
]
