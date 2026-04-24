"""
Infer L↔M Links: Instruction-Evaluation Linking

Maps proposal instructions → evaluation factors using GUIDES relationships.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def infer_lm_links(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Infer L↔M Links: Instruction-Evaluation Linking
    
    Finds instruction-like entities regardless of type:
    - Traditional proposal_instruction entities
    - Deliverables with submission requirements
    - Requirements with submission verbs
    """
    # Gather all instruction sources
    instructions = (
        entities_by_type.get('instruction', []) + 
        entities_by_type.get('proposal_instruction', []) +
        entities_by_type.get('proposal_volume', [])
    )
    
    deliverables_with_instructions = [
        e for e in entities_by_type.get('deliverable', [])
        if any(term in (str(e.get('description', '')) + str(e.get('entity_name', ''))).lower() 
               for term in ['submit', 'provide', 'page', 'format', 'volume', 'shall include', 
                           'maximum', 'minimum', 'font', 'address', 'respond'])
    ]
    
    requirements_with_instructions = [
        e for e in entities_by_type.get('requirement', [])
        if e.get('modal_verb') in ['shall', 'must'] and 
           any(term in str(e.get('entity_name', '')).lower() 
               for term in ['submit', 'provide', 'proposal', 'response', 'volume', 
                           'page limit', 'format', 'electronic', 'hard copy'])
    ]
    
    all_instruction_entities = instructions + deliverables_with_instructions + requirements_with_instructions
    # Include subfactors as link targets — many RFPs (e.g. afcap6) place evaluation criteria
    # at the subfactor level (e.g. M.3.3 Management Plans), so omitting them caused
    # systematic under-linking of L instructions to M criteria.
    eval_factors = (
        entities_by_type.get('evaluation_factor', [])
        + entities_by_type.get('subfactor', [])
    )
    
    if not all_instruction_entities or not eval_factors:
        return []
    
    n_factors = len(entities_by_type.get('evaluation_factor', []))
    n_sub = len(entities_by_type.get('subfactor', []))
    logger.info(
        f"  [L↔M Links] {len(all_instruction_entities)} instructions × "
        f"{len(eval_factors)} targets ({n_factors} factors + {n_sub} subfactors)"
    )
    
    prompt_instructions = await load_prompt_template("instruction_evaluation_linking.md")
    
    inst_json = json.dumps([{
        'id': i['id'],
        'name': i['entity_name'],
        'type': i.get('entity_type'),
        'description': i.get('description', '')[:5000]
    } for i in all_instruction_entities], indent=2)
    
    factors_json = json.dumps([{
        'id': f['id'],
        'name': f['entity_name'],
        'type': f.get('entity_type'),
        'description': f.get('description', '')[:5000]
    } for f in eval_factors], indent=2)
    
    prompt = f"""{prompt_instructions}

PROPOSAL INSTRUCTIONS (and instruction-like entities):
{inst_json}

EVALUATION CRITERIA/FACTORS:
{factors_json}

Apply the inference patterns. Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "instruction_id", "target_id": "factor_id", "relationship_type": "GUIDES", "confidence": 0.7-0.95, "reasoning": "pattern explanation"}}
]
"""
    
    try:
        response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        rels = parse_llm_json_response(response, "Algorithm 1")
        if not rels:
            return []
        valid_rels = validate_relationships(rels, id_to_entity, "L↔M Links")
        logger.info(f"    → L↔M Links: {len(valid_rels)} relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ L↔M Links failed: {e}")
        return []

