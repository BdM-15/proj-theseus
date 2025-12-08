"""
LLM Response Parsing Utilities
================================

Centralized utilities for parsing and validating LLM responses.
Eliminates code duplication across extraction, inference, and enrichment modules.

Key Features:
- Robust JSON extraction (handles markdown, extra text, malformed responses)
- Pydantic validation with clear error messages
- Consistent error handling across pipeline
- Support for both single objects and arrays

Usage:
    from src.utils.llm_parsing import extract_json_from_response, parse_with_pydantic
    
    # Simple JSON extraction
    data = extract_json_from_response(llm_response)
    
    # JSON extraction + Pydantic validation
    validated = parse_with_pydantic(llm_response, MyModel, context="Algorithm 3")
"""

import json
import re
import logging
from typing import Type, TypeVar, Optional, Dict, Any, List, Union

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


def clean_markdown_code_blocks(response: str) -> str:
    """
    Remove markdown code block markers from LLM response.
    
    Handles:
    - ```json ... ```
    - ``` ... ```
    - Mixed markdown with text before/after
    
    Args:
        response: Raw LLM response text
        
    Returns:
        Cleaned response with markdown removed
    """
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
    5. Malformed responses (attempts repair)
    
    Args:
        response: Raw LLM response text
        allow_array: Whether to allow JSON arrays (default: True)
        
    Returns:
        Parsed JSON dict or list
        
    Raises:
        ValueError: If no valid JSON found after all attempts
        
    Examples:
        >>> extract_json_from_response('{"key": "value"}')
        {'key': 'value'}
        
        >>> extract_json_from_response('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}
        
        >>> extract_json_from_response('[{"id": 1}, {"id": 2}]')
        [{'id': 1}, {'id': 2}]
    """
    # Step 1: Clean markdown code blocks
    cleaned = clean_markdown_code_blocks(response)
    
    # Step 2: Try direct JSON parsing
    try:
        parsed = json.loads(cleaned)
        
        # Validate type if array not allowed
        if not allow_array and isinstance(parsed, list):
            logger.warning("LLM returned array but dict expected. Wrapping in 'data' key.")
            return {"data": parsed}
        
        return parsed
        
    except json.JSONDecodeError:
        pass  # Fall through to regex extraction
    
    # Step 3: Use regex to find JSON object (handles text before/after)
    # Match first complete JSON object with nested braces
    json_pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    json_match = re.search(json_pattern, cleaned, re.DOTALL)
    
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            logger.debug("Extracted JSON object using regex")
            return parsed
        except json.JSONDecodeError:
            pass  # Fall through to array extraction
    
    # Step 4: Try to find JSON array (some LLMs return arrays directly)
    if allow_array:
        array_pattern = r'\[(?:[^\[\]]|\[(?:[^\[\]]|\[[^\[\]]*\])*\])*\]'
        array_match = re.search(array_pattern, cleaned, re.DOTALL)
        
        if array_match:
            try:
                parsed = json.loads(array_match.group())
                logger.debug("Extracted JSON array using regex")
                return parsed
            except json.JSONDecodeError:
                pass  # Fall through to error
    
    # Step 5: All parsing attempts failed - log for debugging
    logger.error(
        f"Failed to extract JSON from LLM response. "
        f"Length: {len(response)} chars, "
        f"First 500 chars: {cleaned[:500]}"
    )
    
    raise ValueError(
        f"No valid JSON found in LLM response. "
        f"Response preview: {cleaned[:200]}..."
    )


def extract_json_array_from_response(response: str) -> List:
    """
    Extract JSON array from LLM response (for batch operations).
    
    Handles multiple formats:
    - Direct array: [item1, item2, ...]
    - Wrapped array: {"results": [item1, item2, ...]}
    - Common wrapper keys: results, data, items, relationships, entities
    
    Args:
        response: Raw LLM response text
        
    Returns:
        Parsed JSON list
        
    Raises:
        ValueError: If no valid JSON array found
        
    Examples:
        >>> extract_json_array_from_response('[{"id": 1}, {"id": 2}]')
        [{'id': 1}, {'id': 2}]
        
        >>> extract_json_array_from_response('{"results": [{"id": 1}]}')
        [{'id': 1}]
    """
    # Extract JSON (allow both objects and arrays)
    parsed = extract_json_from_response(response, allow_array=True)
    
    # If already a list, return it
    if isinstance(parsed, list):
        return parsed
    
    # If dict, try to find array in common wrapper keys
    if isinstance(parsed, dict):
        wrapper_keys = ['results', 'data', 'items', 'relationships', 'entities', 'requirements']
        
        for key in wrapper_keys:
            if key in parsed and isinstance(parsed[key], list):
                logger.debug(f"Unwrapped array from '{key}' key")
                return parsed[key]
        
        # No array found in dict
        available_keys = list(parsed.keys())
        logger.error(f"Expected JSON array or dict with array field. Found dict with keys: {available_keys}")
        raise ValueError(f"Expected JSON array, got dict with keys: {available_keys}")
    
    # Neither list nor dict
    raise ValueError(f"Expected JSON array, got {type(parsed)}")


def parse_with_pydantic(
    response: str,
    model_class: Type[T],
    context: str = "LLM response",
    allow_partial: bool = False
) -> Optional[T]:
    """
    Parse JSON from LLM response and validate with Pydantic model.
    
    Combines JSON extraction + Pydantic validation in single function.
    Provides clear error messages for debugging.
    
    Args:
        response: Raw LLM response text
        model_class: Pydantic model class to validate against
        context: Context string for logging (e.g., "Algorithm 3 Batch 5")
        allow_partial: If True, returns None on failure instead of raising
        
    Returns:
        Validated Pydantic model instance, or None if allow_partial=True and parsing fails
        
    Raises:
        ValueError: If JSON extraction fails and allow_partial=False
        ValidationError: If Pydantic validation fails and allow_partial=False
        
    Examples:
        >>> from src.ontology.schema import InferredRelationship
        >>> rel = parse_with_pydantic(
        ...     response='{"source_id": "e1", "target_id": "e2", "relationship_type": "GUIDES"}',
        ...     model_class=InferredRelationship,
        ...     context="Test"
        ... )
        >>> rel.source_id
        'e1'
    """
    try:
        # Step 1: Extract JSON
        response_json = extract_json_from_response(response, allow_array=True)
        
        # Step 2: Validate with Pydantic
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
        
        # Log first few errors for debugging
        if e.errors():
            for i, error in enumerate(e.errors()[:3]):
                logger.error(
                    f"{context}: Validation error {i+1}: "
                    f"{error['loc']} - {error['msg']}"
                )
            if len(e.errors()) > 3:
                logger.error(f"{context}: ... and {len(e.errors()) - 3} more errors")
        
        if not allow_partial:
            raise
        return None


def create_fallback_response(
    model_class: Type[T],
    fallback_data: Dict[str, Any],
    context: str = "LLM response"
) -> T:
    """
    Create a minimal valid Pydantic model instance from fallback data.
    
    Used for graceful degradation when LLM response is malformed but
    we can salvage partial data.
    
    Args:
        model_class: Pydantic model class
        fallback_data: Minimal data to create valid instance
        context: Context string for logging
        
    Returns:
        Valid Pydantic model instance (may have default/minimal values)
        
    Raises:
        ValidationError: If fallback_data is insufficient for required fields
        
    Examples:
        >>> from src.ontology.schema import InferredRelationship
        >>> fallback = create_fallback_response(
        ...     InferredRelationship,
        ...     {"source_id": "e1", "target_id": "e2", "relationship_type": "RELATED_TO"},
        ...     context="Recovery"
        ... )
        >>> fallback.relationship_type
        'RELATED_TO'
    """
    try:
        fallback = model_class.model_validate(fallback_data)
        logger.info(f"{context}: Created fallback response with minimal data")
        return fallback
        
    except ValidationError as e:
        logger.error(
            f"{context}: Fallback creation failed. "
            f"This indicates missing required fields in fallback_data"
        )
        
        # Log what fields are missing
        for error in e.errors():
            logger.error(f"{context}: Missing field: {error['loc']} - {error['msg']}")
        
        raise


def normalize_llm_list_response(value: Any) -> List:
    """
    Normalize various LLM list response formats to Python list.
    
    Handles common LLM variations:
    - None → []
    - "item" → ["item"]
    - ["item1", "item2"] → ["item1", "item2"]
    - ["item", "", "  "] → ["item"] (removes empty/whitespace)
    
    Args:
        value: Raw value from LLM (could be None, str, or list)
        
    Returns:
        Normalized Python list
        
    Examples:
        >>> normalize_llm_list_response(None)
        []
        >>> normalize_llm_list_response("single item")
        ['single item']
        >>> normalize_llm_list_response(["item1", "", "  ", "item2"])
        ['item1', 'item2']
    """
    if value is None:
        return []
    
    if isinstance(value, str):
        return [value] if value.strip() else []
    
    if isinstance(value, list):
        # Remove empty strings and whitespace-only items
        return [item.strip() for item in value if item and str(item).strip()]
    
    # Unexpected type - try to convert
    logger.warning(f"Unexpected type for list field: {type(value)}. Converting to string.")
    return [str(value)]


def deduplicate_list_preserve_order(items: List[str]) -> List[str]:
    """
    Remove duplicates from list while preserving order.
    
    Useful for cleaning LLM responses that sometimes repeat items.
    
    Args:
        items: List with potential duplicates
        
    Returns:
        List with duplicates removed, original order preserved
        
    Examples:
        >>> deduplicate_list_preserve_order(["a", "b", "a", "c", "b"])
        ['a', 'b', 'c']
    """
    seen = set()
    unique_items = []
    
    for item in items:
        if item not in seen:
            seen.add(item)
            unique_items.append(item)
    
    return unique_items
