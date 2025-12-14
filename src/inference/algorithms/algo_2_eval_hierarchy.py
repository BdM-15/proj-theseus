"""
Algorithm 2: Evaluation Hierarchy & Metrics

Structures evaluation framework with HAS_SUBFACTOR, MEASURED_BY relationships.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def algo_2_eval_hierarchy(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Algorithm 2: Evaluation Hierarchy
    
    Identifies parent-child relationships between evaluation factors,
    rating scales, metrics, and thresholds.
    """
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    if not eval_factors:
        return []
    
    logger.info(f"  [Algo 2] Eval Hierarchy: {len(eval_factors)} factors")
    
    prompt_instructions = await load_prompt_template("evaluation_hierarchy.md")
    
    factors_json = json.dumps([{
        'id': f['id'],
        'name': f['entity_name'],
        'type': f.get('entity_type'),
        'description': f.get('description', '')[:5000]
    } for f in eval_factors], indent=2)
    
    prompt = f"""{prompt_instructions}

EVALUATION_FACTOR_ENTITIES:
{factors_json}

Apply the hierarchy inference patterns. Use entity IDs from 'id' field (NOT names).
Return ONLY valid JSON array:
[
  {{"source_id": "parent_id", "target_id": "child_id", "relationship_type": "HAS_SUBFACTOR|HAS_RATING_SCALE|MEASURED_BY|HAS_THRESHOLD|EVALUATED_USING|DEFINES_SCALE", "confidence": 0.75-0.95, "reasoning": "pattern explanation"}}
]
"""
    
    try:
        response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        rels = parse_llm_json_response(response, "Algorithm 2")
        if not rels:
            return []
        valid_rels = validate_relationships(rels, id_to_entity, "Algorithm 2")
        logger.info(f"    → Algo 2: {len(valid_rels)} relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 2 failed: {e}")
        return []

