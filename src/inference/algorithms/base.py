"""
Base utilities shared by all algorithm modules.
"""
import json
import logging
import os
from typing import Dict, List

from pydantic import ValidationError

from src.core import get_settings
from src.ontology.schema import InferredRelationship
from src.utils.llm_client import call_llm_async
from src.utils.llm_parsing import extract_json_from_response

logger = logging.getLogger(__name__)

# Parallelization config from centralized settings
_settings = get_settings()
MAX_CONCURRENT_LLM_CALLS = _settings.get_effective_post_processing_max_async()


async def load_prompt_template(prompt_filename: str) -> str:
    """Load a prompt template from prompts/relationship_inference/"""
    from pathlib import Path
    prompt_path = Path("prompts/relationship_inference") / prompt_filename
    try:
        return prompt_path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logger.error(f"Prompt template not found: {prompt_path}")
        return ""


def validate_relationships(rels: List[Dict], id_to_entity: Dict, algorithm_name: str) -> List[Dict]:
    """
    Validate relationships using Pydantic models (Branch 040 pattern).
    
    Graceful degradation: Validates ONE-BY-ONE, drops bad ones, keeps batch.
    """
    valid_rels = []
    filtered_count = 0
    self_loop_count = 0
    hallucination_count = 0
    
    for rel in rels:
        try:
            validated = InferredRelationship.model_validate(rel)
            
            if validated.source_id not in id_to_entity:
                hallucination_count += 1
                continue
            if validated.target_id not in id_to_entity:
                hallucination_count += 1
                continue
            
            valid_rels.append(validated.to_dict())
            
        except ValidationError as ve:
            filtered_count += 1
            if 'Self-loop' in str(ve):
                self_loop_count += 1
            continue
        except Exception:
            filtered_count += 1
            continue
    
    total = len(rels)
    if filtered_count > 0 or hallucination_count > 0:
        logger.info(f"    {algorithm_name}: {len(valid_rels)}/{total} valid "
                   f"(filtered: {filtered_count}, hallucinated: {hallucination_count})")
    
    return valid_rels


def parse_llm_json_response(response: str, algorithm_name: str) -> List[Dict]:
    """
    Parse LLM response to JSON using robust extraction (Branch 040 pattern).
    
    Handles:
    - Markdown code blocks
    - Truncated responses (returns empty list gracefully)
    - Severely truncated responses (< 50 chars)
    - Various wrapper formats
    
    Returns empty list on failure (graceful degradation).
    
    Updated Dec 2025: Enhanced truncation handling for Algorithm 3/5 failures.
    """
    # Early check for severely truncated responses (seen in MCPP II logs: 41-45 chars)
    if not response or len(response.strip()) < 20:
        logger.warning(f"{algorithm_name}: Response too short ({len(response) if response else 0} chars), returning empty")
        return []
    
    try:
        data = extract_json_from_response(response, allow_array=True)
        
        # Normalize to list
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common wrapper keys
            for key in ['relationships', 'results', 'data', 'items']:
                if key in data:
                    return data[key]
            return [data]  # Single item
        else:
            logger.warning(f"{algorithm_name}: Unexpected response type: {type(data)}")
            return []
            
    except (ValueError, json.JSONDecodeError) as e:
        # Check if this is a truncation issue
        if 'truncated' in str(e).lower() or len(response) < 100:
            logger.warning(f"{algorithm_name}: Likely truncated response ({len(response)} chars), returning empty")
        else:
            logger.error(f"{algorithm_name}: JSON parse failed: {str(e)[:100]}")
        return []
    except Exception as e:
        logger.error(f"{algorithm_name}: Unexpected parse error: {e}")
        return []

