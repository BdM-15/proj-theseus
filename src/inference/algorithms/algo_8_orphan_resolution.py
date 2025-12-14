"""
Algorithm 8: Orphan Pattern Resolution

Identifies orphan entities and suggests relationships.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def algo_8_orphan_resolution(
    entities: List[Dict],
    id_to_entity: Dict,
    neo4j_io,
    model: str,
    temperature: float,
    system_prompt: str = None
) -> List[Dict]:
    """
    Algorithm 8: Orphan Pattern Resolution
    
    Identifies entities with no relationships and suggests
    connections based on content similarity.
    """
    logger.info(f"  [Algo 8] Orphan Resolution")
    
    orphans = []
    try:
        if neo4j_io:
            # Use the proper Neo4jGraphIO method
            orphan_ids = neo4j_io.get_orphaned_entity_ids()
            
            # Build orphan list from id_to_entity lookup
            for orphan_id in orphan_ids[:50]:  # Limit to 50 for LLM context
                if orphan_id in id_to_entity:
                    orphans.append(id_to_entity[orphan_id])
    except Exception as e:
        logger.warning(f"    Could not query orphans: {e}")
    
    if not orphans:
        logger.info(f"    No orphans detected (graph is well-connected)")
        return []
    
    logger.info(f"    Found {len(orphans)} orphan entities")
    
    non_orphan_entities = [e for e in entities if e['id'] not in {o['id'] for o in orphans}][:50]
    
    if not non_orphan_entities:
        return []
    
    if not system_prompt:
        system_prompt = await load_prompt_template("system_prompt.md")
    
    orphans_json = json.dumps([{
        'id': o['id'],
        'name': o.get('entity_name', ''),
        'type': o.get('entity_type', ''),
        'description': (o.get('description') or '')[:3000]
    } for o in orphans], indent=2)
    
    targets_json = json.dumps([{
        'id': e['id'],
        'name': e['entity_name'],
        'type': e.get('entity_type', ''),
        'description': e.get('description', '')[:3000]
    } for e in non_orphan_entities], indent=2)
    
    prompt = f"""Analyze orphan entities that have no relationships.
Suggest connections to other entities based on semantic similarity.

ORPHAN ENTITIES:
{orphans_json}

TARGET ENTITIES:
{targets_json}

Return ONLY valid JSON array:
[{{"source_id": "orphan_id", "target_id": "target_id", "relationship_type": "RELATED_TO|SUPPORTS", "confidence": 0.6-0.85, "reasoning": "explanation"}}]
"""
    
    try:
        response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        rels = parse_llm_json_response(response, "Algorithm 8")
        if not rels:
            return []
        valid_rels = validate_relationships(rels, id_to_entity, "Algorithm 8")
        logger.info(f"    -> Algo 8: {len(valid_rels)} relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    Algorithm 8 failed: {e}")
        return []

