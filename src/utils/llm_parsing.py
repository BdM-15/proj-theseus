"""
LLM Response Parsing Utilities
================================

Centralized utilities for parsing and validating LLM responses.
Based on Branch 040 pattern but simplified for current needs.

Key Features:
- Robust JSON extraction (handles markdown, extra text, malformed responses)
- Pydantic validation with clear error messages
- Consistent error handling across pipeline
"""

import json
import re
import logging
from typing import Type, TypeVar, Optional, Dict, Any, List, Union

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


def clean_markdown_code_blocks(response: str) -> str:
    """Remove markdown code block markers from LLM response."""
    cleaned = response.strip()
    
    # Remove opening markdown markers
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    
    # Remove closing markdown markers
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    
    return cleaned.strip()


def extract_json_from_response(response: str, allow_array: bool = True) -> Union[Dict, List]:
    """
    Extract JSON from LLM response with robust parsing.
    
    Handles multiple scenarios:
    1. Clean JSON (direct parse)
    2. Markdown code blocks (```json ... ```)
    3. Text before/after JSON (regex extraction)
    4. Arrays vs objects
    
    Args:
        response: Raw LLM response text
        allow_array: Whether to allow JSON arrays (default: True)
    
    Returns:
        Parsed JSON dict or list
    
    Raises:
        ValueError: If no valid JSON found after all attempts
    """
    # Step 1: Clean markdown code blocks
    cleaned = clean_markdown_code_blocks(response)
    
    # Step 2: Try direct JSON parsing
    try:
        parsed = json.loads(cleaned)
        if not allow_array and isinstance(parsed, list):
            logger.warning("LLM returned array but dict expected. Wrapping in 'data' key.")
            return {"data": parsed}
        return parsed
    except json.JSONDecodeError:
        pass
    
    # Step 3: Use regex to find JSON object
    json_pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    json_match = re.search(json_pattern, cleaned, re.DOTALL)
    
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            logger.debug("Extracted JSON object using regex")
            return parsed
        except json.JSONDecodeError:
            pass
    
    # Step 4: Try to find JSON array
    if allow_array:
        array_pattern = r'\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\]'
        array_match = re.search(array_pattern, cleaned, re.DOTALL)
        
        if array_match:
            try:
                parsed = json.loads(array_match.group())
                logger.debug("Extracted JSON array using regex")
                return parsed
            except json.JSONDecodeError:
                pass
    
    # Step 5: All parsing attempts failed
    logger.error(
        f"Failed to extract JSON from LLM response. "
        f"Length: {len(response)} chars, "
        f"First 500 chars: {cleaned[:500]}"
    )
    
    raise ValueError(f"No valid JSON found in LLM response. Preview: {cleaned[:200]}...")


def extract_json_array_from_response(response: str) -> List:
    """
    Extract JSON array from LLM response (for batch operations).
    
    Handles:
    - Direct array: [item1, item2, ...]
    - Wrapped array: {"results": [item1, item2, ...]}
    """
    parsed = extract_json_from_response(response, allow_array=True)
    
    if isinstance(parsed, list):
        return parsed
    
    if isinstance(parsed, dict):
        wrapper_keys = ['results', 'data', 'items', 'relationships', 'entities', 'requirements']
        
        for key in wrapper_keys:
            if key in parsed and isinstance(parsed[key], list):
                logger.debug(f"Unwrapped array from '{key}' key")
                return parsed[key]
        
        available_keys = list(parsed.keys())
        logger.error(f"Expected JSON array or dict with array field. Found dict with keys: {available_keys}")
        raise ValueError(f"Expected JSON array, got dict with keys: {available_keys}")
    
    raise ValueError(f"Expected JSON array, got {type(parsed)}")


def parse_with_pydantic(
    response: str,
    model_class: Type[T],
    context: str = "LLM response",
    allow_partial: bool = False
) -> Optional[T]:
    """
    Parse JSON from LLM response and validate with Pydantic model.
    
    Args:
        response: Raw LLM response text
        model_class: Pydantic model class to validate against
        context: Context string for logging
        allow_partial: If True, returns None on failure instead of raising
    
    Returns:
        Validated Pydantic model instance, or None if allow_partial=True and parsing fails
    """
    try:
        response_json = extract_json_from_response(response, allow_array=True)
        validated = model_class.model_validate(response_json)
        logger.debug(f"{context}: Successfully parsed and validated response")
        return validated
    
    except ValueError as e:
        logger.error(f"{context}: JSON extraction failed: {e}")
        if not allow_partial:
            raise
        return None
    
    except ValidationError as e:
        logger.error(f"{context}: Pydantic validation failed")
        for i, error in enumerate(e.errors()[:3]):
            logger.error(f"{context}: Validation error {i+1}: {error['loc']} - {error['msg']}")
        if len(e.errors()) > 3:
            logger.error(f"{context}: ... and {len(e.errors()) - 3} more errors")
        
        if not allow_partial:
            raise
        return None


def normalize_llm_list_response(value: Any) -> List:
    """
    Normalize various LLM list response formats to Python list.
    
    Handles:
    - None -> []
    - "item" -> ["item"]
    - ["item1", "item2"] -> ["item1", "item2"]
    - ["item", "", "  "] -> ["item"] (removes empty/whitespace)
    """
    if value is None:
        return []
    
    if isinstance(value, str):
        return [value] if value.strip() else []
    
    if isinstance(value, list):
        return [item.strip() for item in value if item and str(item).strip()]
    
    logger.warning(f"Unexpected type for list field: {type(value)}. Converting to string.")
    return [str(value)]


def deduplicate_list_preserve_order(items: List[str]) -> List[str]:
    """Remove duplicates from list while preserving order."""
    seen = set()
    unique_items = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    
    return unique_items

