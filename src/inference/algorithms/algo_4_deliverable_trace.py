"""
Algorithm 4: Deliverable Traceability

Dual-pattern linking: Requirements + Work Statements → Deliverables.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def algo_4_deliverable_trace(
    entities_by_type: Dict,
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Algorithm 4: Deliverable Traceability
    
    Pattern 1: Requirement → Deliverable (SATISFIED_BY)
    Pattern 2: Work Statement → Deliverable (PRODUCES)
    """
    requirements = entities_by_type.get('requirement', [])
    work_statements = (
        entities_by_type.get('statement_of_work', []) + 
        entities_by_type.get('pws', []) + 
        entities_by_type.get('soo', [])
    )
    deliverables = entities_by_type.get('deliverable', [])
    
    if not deliverables or (not requirements and not work_statements):
        return []
    
    logger.info(f"  [Algo 4] Deliverable Trace: {len(requirements)} reqs + {len(work_statements)} work × {len(deliverables)} delivs")
    
    prompt_instructions = await load_prompt_template("deliverable_traceability.md")
    all_rels = []
    
    # Pattern 1: Requirement → Deliverable
    if requirements:
        reqs_json = json.dumps([{
            'id': r['id'],
            'name': r['entity_name'],
            'type': r.get('entity_type'),
            'description': r.get('description', '')[:5000]
        } for r in requirements], indent=2)
        
        deliv_json = json.dumps([{
            'id': d['id'],
            'name': d['entity_name'],
            'type': d.get('entity_type'),
            'description': d.get('description', '')[:5000]
        } for d in deliverables], indent=2)
        
        prompt = f"""{prompt_instructions}

Apply PATTERN 1 (Requirement → Deliverable) detection rules.

REQUIREMENTS:
{reqs_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on evidence relationships.
Return ONLY valid JSON array:
[
  {{"source_id": "requirement_id", "target_id": "deliverable_id", "relationship_type": "SATISFIED_BY", "confidence": 0.50-0.95, "reasoning": "evidence relationship"}}
]
"""
        try:
            response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = parse_llm_json_response(response, "Algorithm 4 P1")
            if rels:
                pattern1 = validate_relationships(rels, id_to_entity, "Algorithm 4 P1")
                all_rels.extend(pattern1)
                logger.info(f"    → Algo 4 Pattern 1: {len(pattern1)} relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 4 Pattern 1 failed: {e}")
    
    # Pattern 2: Work Statement → Deliverable
    if work_statements:
        work_json = json.dumps([{
            'id': w['id'],
            'name': w['entity_name'],
            'type': w.get('entity_type'),
            'description': w.get('description', '')[:5000]
        } for w in work_statements], indent=2)
        
        deliv_json = json.dumps([{
            'id': d['id'],
            'name': d['entity_name'],
            'type': d.get('entity_type'),
            'description': d.get('description', '')[:5000]
        } for d in deliverables], indent=2)
        
        prompt = f"""{prompt_instructions}

Apply PATTERN 2 (Work Statement → Deliverable) detection rules.

WORK_STATEMENTS:
{work_json}

DELIVERABLES:
{deliv_json}

Use entity IDs from 'id' field. Focus on explicit CDRL references.
Return ONLY valid JSON array:
[
  {{"source_id": "work_statement_id", "target_id": "deliverable_id", "relationship_type": "PRODUCES", "confidence": 0.50-0.96, "reasoning": "work-product relationship"}}
]
"""
        try:
            response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
            rels = parse_llm_json_response(response, "Algorithm 4 P2")
            if rels:
                pattern2 = validate_relationships(rels, id_to_entity, "Algorithm 4 P2")
                all_rels.extend(pattern2)
                logger.info(f"    → Algo 4 Pattern 2: {len(pattern2)} relationships")
        except Exception as e:
            logger.error(f"    ❌ Algorithm 4 Pattern 2 failed: {e}")
    
    logger.info(f"    → Algo 4 Total: {len(all_rels)} relationships")
    return all_rels

