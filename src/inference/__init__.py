"""
Relationship Inference Module

LLM-powered semantic relationship inference for knowledge graphs.
Implements 8 core algorithms for government contracting RFPs:

1. Instruction-Evaluation Linking: SUBMISSION_INSTRUCTION → EVALUATION_FACTOR (GUIDES)
2. Evaluation Hierarchy: EVALUATION_FACTOR → EVALUATION_FACTOR (CHILD_OF)
3. Deliverable Traceability: DELIVERABLE → REQUIREMENT/EVALUATION_FACTOR (FULFILLS/EVALUATED_BY)
4. Requirement Clustering: REQUIREMENT → REQUIREMENT (RELATED_TO)
5. Annex/Attachment Linking: DOCUMENT → REQUIREMENT/CLAUSE (DEFINES/PROVIDES_CONTEXT)
6. Orphan Resolution: Unconnected entities → related entities
7. PWS Workload Enrichment: BOE metadata extraction for requirements
8. Entity Type Correction: Fix misclassified entities

Usage:
    from src.inference.semantic_post_processor import SemanticPostProcessor
    from src.inference.graph_io import parse_graphml, save_relationships_to_graphml
    
    processor = SemanticPostProcessor(neo4j_io, workspace)
    await processor.process_batch()
"""

from src.inference.graph_io import (
    parse_graphml,
    save_relationships_to_graphml,
    save_relationships_to_kv_store,
    group_entities_by_type,
)

__all__ = [
    # Graph I/O exports
    "parse_graphml",
    "save_relationships_to_graphml",
    "save_relationships_to_kv_store",
    "group_entities_by_type",
]
