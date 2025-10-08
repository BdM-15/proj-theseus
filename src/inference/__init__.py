"""
Relationship Inference Module

LLM-powered semantic relationship inference for knowledge graphs.
Implements 5 core algorithms for government contracting RFPs:

1. Document Hierarchy: ANNEX/CLAUSE → SECTION (CHILD_OF)
2. Section L↔M Mapping: SUBMISSION_INSTRUCTION → EVALUATION_FACTOR (GUIDES)
3. Attachment Section Linking: ANNEX → SECTION (ATTACHMENT_OF)
4. Clause Clustering: CLAUSE → SECTION (CHILD_OF)
5. Requirement Evaluation: REQUIREMENT → EVALUATION_FACTOR (EVALUATED_BY)

Usage:
    from src.inference import infer_all_relationships
    from src.inference.graph_io import parse_graphml, save_relationships_to_graphml
    
    nodes, edges = parse_graphml(Path("./rag_storage/graph_chunk_entity_relation.graphml"))
    new_rels = await infer_all_relationships(nodes, edges, llm_func)
    save_relationships_to_graphml(graphml_path, new_rels, nodes)
"""

from src.inference.engine import (
    infer_all_relationships,
    infer_relationships_batch,
    create_relationship_inference_prompt,
)

from src.inference.graph_io import (
    parse_graphml,
    save_relationships_to_graphml,
    save_relationships_to_kv_store,
    group_entities_by_type,
)

__all__ = [
    # Engine exports
    "infer_all_relationships",
    "infer_relationships_batch",
    "create_relationship_inference_prompt",
    # Graph I/O exports
    "parse_graphml",
    "save_relationships_to_graphml",
    "save_relationships_to_kv_store",
    "group_entities_by_type",
]
