"""
Semantic Post-Processing for Government Contracting RFPs
========================================================

Coordinates all LLM-powered enhancements to the extracted knowledge graph:

1. **Entity Type Correction**: Fix UNKNOWN/forbidden entity types
2. **Relationship Inference**: Infer missing semantic relationships

This replaces the confusing "Phase 6" and "Phase 7" terminology with
clear, operation-based naming.

Usage:
    from src.inference.semantic_post_processor import enhance_knowledge_graph
    
    stats = await enhance_knowledge_graph(
        graphml_path="path/to/graph.graphml",
        llm_func=my_llm_function
    )
"""

import logging
from typing import Dict, Callable, Awaitable
from pathlib import Path

from src.inference.graph_io import parse_graphml, save_enhanced_graphml

logger = logging.getLogger(__name__)


async def enhance_knowledge_graph(
    graphml_path: str,
    llm_func: Callable[[str, str], Awaitable[str]],
    batch_size: int = 50
) -> Dict:
    """
    Run all semantic post-processing on extracted knowledge graph.
    
    Steps:
    1. Load entities/relationships from GraphML
    2. Correct entity types (UNKNOWN → proper types)
    3. Infer missing relationships (semantic understanding)
    4. Save enhanced graph back to GraphML
    
    Args:
        graphml_path: Path to GraphML file from RAG-Anything
        llm_func: Async LLM function for semantic operations
        batch_size: Batch size for LLM calls (default: 50)
    
    Returns:
        Stats dict with:
        - entities_corrected: Number of entities retyped
        - relationships_inferred: Number of new relationships
        - processing_time: Total time in seconds
    """
    logger.info("=" * 80)
    logger.info("🧠 SEMANTIC POST-PROCESSING: LLM-Powered Graph Enhancement")
    logger.info("=" * 80)
    
    import time
    start_time = time.time()
    
    # Step 1: Load graph
    logger.info("\n  [1/3] Loading knowledge graph from GraphML...")
    nodes, edges = parse_graphml(graphml_path)
    logger.info(f"    ✅ Loaded {len(nodes)} entities, {len(edges)} relationships")
    
    if not nodes:
        logger.warning("    ⚠️  No entities found - skipping post-processing")
        return {
            "status": "skipped",
            "reason": "no_entities",
            "entities_corrected": 0,
            "relationships_inferred": 0,
            "processing_time": 0
        }
    
    # Step 2: Entity Type Correction
    logger.info("\n  [2/3] Entity Type Correction...")
    from src.inference.entity_operations import correct_entity_types
    
    nodes, corrections = await correct_entity_types(
        entities=nodes,
        llm_func=llm_func,
        batch_size=batch_size
    )
    
    logger.info(f"    ✅ Corrected {len(corrections)} entity types")
    
    # Save corrected entities immediately
    if corrections:
        save_enhanced_graphml(graphml_path, nodes, edges)
        logger.info(f"    ✅ Saved corrected entities to GraphML")
    
    # Step 3: Relationship Inference
    logger.info("\n  [3/3] Relationship Inference...")
    from src.inference.relationship_operations import infer_relationships
    
    new_relationships = await infer_relationships(
        entities=nodes,
        existing_relationships=edges,
        llm_func=llm_func,
        batch_size=batch_size
    )
    
    logger.info(f"    ✅ Inferred {len(new_relationships)} new relationships")
    
    # Save enhanced graph
    if new_relationships:
        edges.extend(new_relationships)
        save_enhanced_graphml(graphml_path, nodes, edges)
        logger.info(f"    ✅ Saved enhanced graph to GraphML")
    
    # Summary
    elapsed = time.time() - start_time
    logger.info("\n" + "=" * 80)
    logger.info("✅ SEMANTIC POST-PROCESSING COMPLETE")
    logger.info(f"   Entities corrected: {len(corrections)}")
    logger.info(f"   Relationships inferred: {len(new_relationships)}")
    logger.info(f"   Processing time: {elapsed:.1f}s")
    logger.info("=" * 80)
    
    return {
        "status": "success",
        "entities_corrected": len(corrections),
        "relationships_inferred": len(new_relationships),
        "processing_time": elapsed
    }
