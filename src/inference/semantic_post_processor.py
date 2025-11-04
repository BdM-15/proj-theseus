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
import time
from typing import Dict, Callable, Awaitable, List
from pathlib import Path

from src.inference.graph_io import parse_graphml, save_enhanced_graphml
from src.inference.neo4j_graph_io import Neo4jGraphIO, group_entities_by_type
from src.inference.entity_operations import ALLOWED_TYPES, FORBIDDEN_TYPES
from lightrag.llm.openai import openai_complete_if_cache
import os

logger = logging.getLogger(__name__)


async def _call_llm_async(prompt: str, system_prompt: str = None, model: str = "grok-4-fast-reasoning", temperature: float = 0.1) -> str:
    """Async wrapper for LLM calls"""
    return await openai_complete_if_cache(
        model=model,
        prompt=prompt,
        system_prompt=system_prompt,
        hashing_kv=None,  # No caching for post-processing
        api_key=os.getenv("LLM_BINDING_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST"),
        temperature=temperature
    )


async def _infer_entity_type(entity_name: str, description: str, model: str, temperature: float) -> str:
    """Infer correct entity type for a single entity"""
    allowed_types_str = ", ".join(ALLOWED_TYPES)
    
    prompt = f"""You are a government contracting expert. Classify this entity into ONE of these types:
{allowed_types_str}

Entity Name: {entity_name}
Description: {description or 'No description'}

Return ONLY the entity type (lowercase with underscores). No explanation."""
    
    try:
        response = await _call_llm_async(prompt, model=model, temperature=temperature)
        new_type = response.strip().lower()
        
        # Validate it's an allowed type
        if new_type in ALLOWED_TYPES:
            return new_type
        else:
            logger.warning(f"  LLM returned invalid type '{new_type}' for {entity_name}, using 'concept'")
            return "concept"
    except Exception as e:
        logger.error(f"  Error inferring type for {entity_name}: {e}")
        return "concept"  # Default fallback


async def _infer_relationships_batch(entities: List[Dict], existing_rels: List[Dict], model: str, temperature: float) -> List[Dict]:
    """Infer missing relationships between entities"""
    # Build context of entities
    entity_summary = "\n".join([
        f"- {e['entity_name']} ({e['entity_type']}): {e.get('description', '')[:100]}"
        for e in entities[:50]  # Limit to 50 entities per batch
    ])
    
    prompt = f"""You are analyzing a government contracting knowledge graph. Identify missing relationships between these entities:

{entity_summary}

Existing relationship types: LINKS_TO, REFERENCES, REQUIRES, PART_OF, APPLIES_TO

Find logical relationships that are missing. For each relationship, provide:
1. Source entity name
2. Target entity name  
3. Relationship type (one of the above)
4. Confidence (0.0-1.0)
5. Brief reasoning

Format your response as JSON array:
[
  {{"source": "entity1", "target": "entity2", "type": "REQUIRES", "confidence": 0.85, "reasoning": "..."}}
]

Return ONLY the JSON array. If no relationships found, return []."""
    
    try:
        response = await _call_llm_async(prompt, model=model, temperature=temperature)
        
        # Parse JSON response
        import json
        relationships = json.loads(response)
        
        # Convert entity names to IDs
        name_to_id = {e['entity_name']: e['id'] for e in entities}
        
        converted = []
        for rel in relationships:
            source_id = name_to_id.get(rel['source'])
            target_id = name_to_id.get(rel['target'])
            
            if source_id and target_id:
                converted.append({
                    'source_id': source_id,
                    'target_id': target_id,
                    'relationship_type': rel['type'],
                    'confidence': rel['confidence'],
                    'reasoning': rel['reasoning']
                })
        
        return converted
        
    except Exception as e:
        logger.error(f"  Error inferring relationships: {e}")
        return []


async def _semantic_post_processor_neo4j(
    llm_model_name: str = "grok-4-fast-reasoning",
    temperature: float = 0.1
) -> Dict:
    """
    Neo4j-native semantic post-processing using Cypher queries.
    
    This function:
    1. Reads entities/relationships from Neo4j
    2. Corrects entity types using LLM inference
    3. Infers missing relationships using LLM inference
    4. Writes updates back to Neo4j via Cypher
    
    Args:
        llm_model_name: Name of LLM model to use
        temperature: Temperature for LLM inference
        
    Returns:
        Dict with processing statistics
    """
    start_time = time.time()
    
    # Initialize Neo4j I/O
    logger.info("\n📊 Initializing Neo4j connection...")
    neo4j_io = Neo4jGraphIO()
    
    try:
        # Step 1: Load entities and relationships
        logger.info("\n📥 Step 1: Loading knowledge graph from Neo4j...")
        entities = neo4j_io.get_all_entities()
        relationships = neo4j_io.get_all_relationships()
        
        if not entities:
            logger.warning("⚠️  No entities found in Neo4j workspace")
            return {
                "status": "skipped",
                "reason": "no_entities",
                "entities_corrected": 0,
                "relationships_inferred": 0,
                "processing_time": 0
            }
        
        # Step 2: Correct entity types
        logger.info("\n🔧 Step 2: Correcting entity types with LLM...")
        entity_updates = []
        grouped = group_entities_by_type(entities)
        
        for entity_type, entity_group in grouped.items():
            # Only process UNKNOWN or forbidden types
            if entity_type in ['unknown', 'event', 'concept']:
                logger.info(f"  Processing {len(entity_group)} {entity_type} entities...")
                
                for entity in entity_group:
                    # Call LLM to infer correct type
                    new_type = await _infer_entity_type(
                        entity_name=entity['entity_name'],
                        description=entity.get('description', ''),
                        model=llm_model_name,
                        temperature=temperature
                    )
                    
                    if new_type and new_type.lower() != entity_type:
                        entity_updates.append({
                            'id': entity['id'],
                            'new_entity_type': new_type
                        })
        
        entities_corrected = 0
        if entity_updates:
            logger.info(f"\n💾 Updating {len(entity_updates)} entity types in Neo4j...")
            entities_corrected = neo4j_io.update_entity_types(entity_updates)
        else:
            logger.info("\n✅ No entity type corrections needed")
        
        # Step 3: Infer missing relationships
        logger.info("\n🔗 Step 3: Inferring missing relationships with LLM...")
        new_relationships = await _infer_relationships_batch(
            entities=entities,
            existing_rels=relationships,
            model=llm_model_name,
            temperature=temperature
        )
        
        relationships_inferred = 0
        if new_relationships:
            logger.info(f"\n💾 Creating {len(new_relationships)} new relationships in Neo4j...")
            relationships_inferred = neo4j_io.create_relationships(new_relationships)
        else:
            logger.info("\n✅ No new relationships inferred")
        
        # Step 4: Summary statistics
        processing_time = time.time() - start_time
        logger.info("\n" + "="*80)
        logger.info("✅ SEMANTIC POST-PROCESSING COMPLETE (Neo4j)")
        logger.info("="*80)
        logger.info(f"  Entities corrected:      {entities_corrected}")
        logger.info(f"  Relationships inferred:  {relationships_inferred}")
        logger.info(f"  Processing time:         {processing_time:.2f}s")
        logger.info("="*80)
        
        # Get updated counts
        type_counts = neo4j_io.get_entity_count_by_type()
        logger.info("\n📊 Entity Type Distribution:")
        for entity_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"  {entity_type:30s}: {count:4d}")
        
        return {
            "status": "success",
            "entities_corrected": entities_corrected,
            "relationships_inferred": relationships_inferred,
            "processing_time": processing_time,
            "entity_type_counts": type_counts
        }
        
    except Exception as e:
        logger.error(f"❌ Error during Neo4j post-processing: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "entities_corrected": 0,
            "relationships_inferred": 0,
            "processing_time": time.time() - start_time
        }
    finally:
        neo4j_io.close()


async def enhance_knowledge_graph(
    rag_storage_path: str,
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
        rag_storage_path: Path to rag_storage directory (e.g., "./rag_storage")
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
    
    # Check if Neo4j storage is enabled - use Cypher-based processing
    import os
    if os.getenv("GRAPH_STORAGE") == "Neo4JStorage":
        logger.info("\n  📊 Neo4j storage detected - using Cypher-based semantic enhancement")
        # Get LLM model from environment
        llm_model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
        llm_temp = float(os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))
        return await _semantic_post_processor_neo4j(
            llm_model_name=llm_model,
            temperature=llm_temp
        )
    
    import time
    start_time = time.time()
    
    # Construct GraphML path from rag_storage_path
    graphml_path = Path(rag_storage_path) / "default" / "graph_chunk_entity_relation.graphml"
    
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
