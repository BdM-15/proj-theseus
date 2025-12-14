"""
Algorithm 6: Semantic Concept Linking

Links concepts/strategic themes to high-value entities.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def algo_6_concept_linking(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Algorithm 6: Semantic Concept Linking
    
    Links concepts and strategic themes to high-value entities
    with INFORMS, IMPACTS, GUIDES relationships.
    """
    concepts = entities_by_type.get('concept', [])[:100]  # Limit for performance
    strategic_themes = entities_by_type.get('strategic_theme', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])
    requirements = entities_by_type.get('requirement', [])
    deliverables = entities_by_type.get('deliverable', [])
    
    concept_pool = concepts + strategic_themes
    
    if not concept_pool or not eval_factors:
        return []
    
    logger.info(f"  [Algo 6] Concept Linking: {len(concept_pool)} concepts/themes")
    
    prompt_instructions = await load_prompt_template("semantic_concept_linking.md")
    
    # Build mixed entity pool
    high_value_entities = requirements[:30] + deliverables[:20] + eval_factors[:20]
    
    prompt_json = json.dumps([{
        'id': e['id'],
        'name': e['entity_name'],
        'type': e.get('entity_type'),
        'description': e.get('description', '')[:5000]
    } for e in concept_pool + high_value_entities], indent=2)
    
    prompt = f"""{prompt_instructions}

ENTITIES (concepts, themes, and high-value targets):
{prompt_json}

Apply the semantic inference algorithms.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "concept_id", "target_id": "entity_id", "relationship_type": "INFORMS|IMPACTS|DETERMINES|GUIDES|ADDRESSED_BY|RELATED_TO", "confidence": 0.6-0.9, "reasoning": "semantic connection"}}
]
"""
    
    try:
        response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        rels = parse_llm_json_response(response, "Algorithm 6")
        if not rels:
            return []
        valid_rels = validate_relationships(rels, id_to_entity, "Algorithm 6")
        logger.info(f"    → Algo 6: {len(valid_rels)} relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 6 failed: {e}")
        return []

