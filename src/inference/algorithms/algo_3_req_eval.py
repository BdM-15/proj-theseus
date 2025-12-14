"""
Algorithm 3: Requirement-Evaluation Mapping

Maps requirements → main evaluation factors with EVALUATED_BY relationships.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, is_main_evaluation_factor, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def algo_3_req_eval(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Algorithm 3: Requirement-Evaluation Mapping
    
    Links requirements to MAIN evaluation factors only.
    Excludes rating scales, metrics, and thresholds.
    """
    requirements = entities_by_type.get('requirement', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])
    main_eval_factors = [f for f in eval_factors if is_main_evaluation_factor(f)]
    
    if not requirements or not main_eval_factors:
        return []
    
    logger.info(f"  [Algo 3] Req-Eval: {len(requirements)} reqs × {len(main_eval_factors)} main factors (filtered from {len(eval_factors)})")
    
    prompt_instructions = await load_prompt_template("requirement_evaluation.md")
    
    reqs_json = json.dumps([{
        'id': r['id'],
        'name': r['entity_name'],
        'type': r.get('entity_type'),
        'description': r.get('description', '')[:5000]
    } for r in requirements], indent=2)
    
    factors_json = json.dumps([{
        'id': f['id'],
        'name': f['entity_name'],
        'type': f.get('entity_type'),
        'description': f.get('description', '')[:5000]
    } for f in main_eval_factors], indent=2)
    
    prompt = f"""{prompt_instructions}

REQUIREMENTS:
{reqs_json}

EVALUATION_FACTORS:
{factors_json}

CRITICAL INSTRUCTION - Use factor descriptions for semantic matching:
- Factor names may be generic (Factor A, Factor B, Factor 1, etc.)
- Factor descriptions contain evaluation criteria and topics
- Match requirement CONTENT to factor DESCRIPTION topics

Use entity IDs from 'id' field (NOT names).
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "factor_id", "relationship_type": "EVALUATED_BY", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
    
    try:
        response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        rels = parse_llm_json_response(response, "Algorithm 3")
        if not rels:
            return []
        valid_rels = validate_relationships(rels, id_to_entity, "Algorithm 3")
        logger.info(f"    → Algo 3: {len(valid_rels)} relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 3 failed: {e}")
        return []

