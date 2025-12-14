"""
Algorithm 5: Document Hierarchy

Maps document structure with CHILD_OF, ATTACHMENT_OF relationships.
"""
import json
import logging
from typing import Dict, List

from .base import load_prompt_template, validate_relationships, parse_llm_json_response
from src.utils.llm_client import call_llm_async

logger = logging.getLogger(__name__)


async def algo_5_doc_hierarchy(
    entities: List[Dict],
    id_to_entity: Dict,
    system_prompt: str,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Algorithm 5: Document Hierarchy
    
    Identifies parent-child relationships between documents,
    sections, attachments, annexes, clauses, standards.
    """
    document_types = [
        'document', 'section', 'attachment', 'annex', 'amendment', 
        'clause', 'standard', 'specification', 'regulation', 'exhibit'
    ]
    
    documents = [e for e in entities if e.get('entity_type') in document_types]
    
    if len(documents) <= 1:
        return []
    
    logger.info(f"  [Algo 5] Doc Hierarchy: {len(documents)} documents")
    
    prompt_instructions = await load_prompt_template("document_hierarchy.md")
    
    docs_json = json.dumps([{
        'id': d['id'],
        'name': d['entity_name'],
        'type': d.get('entity_type'),
        'description': d.get('description', '')[:5000]
    } for d in documents], indent=2)
    
    prompt = f"""{prompt_instructions}

DOCUMENTS (all types - attachments, sections, annexes, clauses, standards):
{docs_json}

Apply the inference patterns to identify ALL document relationships.
Use entity IDs from 'id' field.
Return ONLY valid JSON array:
[
  {{"source_id": "child_id", "target_id": "parent_id", "relationship_type": "CHILD_OF|ATTACHMENT_OF", "confidence": 0.7-1.0, "reasoning": "pattern explanation"}}
]
"""
    
    try:
        response = await call_llm_async(prompt, system_prompt=system_prompt, model=model, temperature=temperature)
        rels = parse_llm_json_response(response, "Algorithm 5")
        if not rels:
            return []
        valid_rels = validate_relationships(rels, id_to_entity, "Algorithm 5")
        logger.info(f"    → Algo 5: {len(valid_rels)} relationships")
        return valid_rels
    except Exception as e:
        logger.error(f"    ❌ Algorithm 5 failed: {e}")
        return []

