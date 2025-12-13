"""
LLM Client Utilities
====================

Centralized async LLM client wrapper for xAI Grok.
Eliminates code duplication across all modules that call LLMs.

Key Features:
- Single async LLM function used everywhere
- JSON schema mode support (structured outputs)
- Consistent error handling
- Environment variable configuration
- Optional Pydantic response validation

Usage:
    from src.utils.llm_client import call_llm_async, call_llm_with_schema
    
    # Simple text response
    response = await call_llm_async("What is 2+2?")
    
    # Structured output with Pydantic validation
    result = await call_llm_with_schema(
        prompt="Extract entities...",
        response_model=ExtractionResult,
        system_prompt="You are an entity extractor"
    )
"""

import os
import json
import logging
from typing import Optional, Type, TypeVar, List, Dict, Any

from openai import AsyncOpenAI
from pydantic import BaseModel

from src.utils.llm_parsing import parse_with_pydantic

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


async def call_llm_async(
    prompt: str,
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    json_mode: bool = False
) -> str:
    """
    Call xAI Grok LLM asynchronously.
    
    Single source of truth for all LLM calls in the system.
    
    Args:
        prompt: User prompt text
        system_prompt: Optional system prompt (instructions)
        model: LLM model name (default: from LLM_MODEL env var)
        temperature: Sampling temperature 0.0-2.0 (default: 0.1 for deterministic)
        max_tokens: Maximum tokens in response (default: model's max)
        json_mode: Force JSON output mode (adds response_format constraint)
        
    Returns:
        LLM response text
        
    Raises:
        Exception: If API call fails after retries
        
    Examples:
        >>> response = await call_llm_async("What is the capital of France?")
        >>> print(response)
        'Paris'
        
        >>> response = await call_llm_async(
        ...     prompt="Extract entities from: ...",
        ...     system_prompt="You are an entity extractor",
        ...     json_mode=True
        ... )
    """
    if model is None:
        model = os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning")
    
    # Create AsyncOpenAI client with xAI endpoint
    client = AsyncOpenAI(
        api_key=os.getenv("LLM_BINDING_API_KEY"),
        base_url=os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
    )
    
    # Build messages array
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Build API call kwargs
    call_kwargs = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    
    # Add optional parameters
    if max_tokens:
        call_kwargs["max_tokens"] = max_tokens
    
    if json_mode:
        call_kwargs["response_format"] = {"type": "json_object"}
    
    # Make API call
    try:
        response = await client.chat.completions.create(**call_kwargs)
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        raise


async def call_llm_with_schema(
    prompt: str,
    response_model: Type[T],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    inject_schema: bool = True
) -> T:
    """
    Call LLM with JSON schema enforcement and Pydantic validation.
    
    Best practice for structured outputs:
    1. Generates JSON schema from Pydantic model
    2. Injects schema into system prompt (if inject_schema=True)
    3. Forces JSON output mode
    4. Validates response against Pydantic model
    
    Args:
        prompt: User prompt text
        response_model: Pydantic model class for response validation
        system_prompt: Optional system prompt (schema appended if inject_schema=True)
        model: LLM model name
        temperature: Sampling temperature
        inject_schema: Whether to inject JSON schema into system prompt (default: True)
        
    Returns:
        Validated Pydantic model instance
        
    Raises:
        ValueError: If JSON extraction fails
        ValidationError: If Pydantic validation fails
        
    Examples:
        >>> from src.ontology.schema import InferredRelationship
        >>> rel = await call_llm_with_schema(
        ...     prompt="Infer relationship between entity_1 and entity_2",
        ...     response_model=InferredRelationship,
        ...     system_prompt="You are a relationship inference expert"
        ... )
        >>> print(rel.relationship_type)
        'GUIDES'
    """
    # Generate JSON schema from Pydantic model
    schema = response_model.model_json_schema()
    
    # Inject schema into system prompt if requested
    if inject_schema:
        schema_instruction = (
            f"\n\n**CRITICAL OUTPUT FORMAT**:\n"
            f"You MUST respond with valid JSON matching this exact schema:\n"
            f"```json\n{json.dumps(schema, indent=2)}\n```\n\n"
            f"**FORMATTING RULES**:\n"
            f"1. Return ONLY the JSON object - no markdown code blocks\n"
            f"2. No explanations or text outside the JSON\n"
            f"3. All required fields must be present\n"
            f"4. Follow the exact field names and types specified\n"
        )
        
        if system_prompt:
            system_prompt = system_prompt + schema_instruction
        else:
            system_prompt = schema_instruction
    
    # Call LLM with JSON mode enforced
    response_text = await call_llm_async(
        prompt=prompt,
        system_prompt=system_prompt,
        model=model,
        temperature=temperature,
        json_mode=True  # Force JSON output
    )
    
    # Parse and validate with Pydantic
    validated = parse_with_pydantic(
        response=response_text,
        model_class=response_model,
        context=f"call_llm_with_schema({response_model.__name__})",
        allow_partial=False  # Raise on errors
    )
    
    return validated


async def call_llm_batch(
    prompts: List[str],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_concurrent: int = 4
) -> List[str]:
    """
    Call LLM with multiple prompts in parallel (batched).
    
    Useful for processing multiple independent items concurrently.
    
    Args:
        prompts: List of user prompts
        system_prompt: Optional system prompt (same for all)
        model: LLM model name
        temperature: Sampling temperature
        max_concurrent: Maximum concurrent API calls (default: 4)
        
    Returns:
        List of LLM responses (same order as prompts)
        
    Examples:
        >>> prompts = ["What is 2+2?", "What is 3+3?", "What is 4+4?"]
        >>> responses = await call_llm_batch(prompts)
        >>> print(responses)
        ['4', '6', '8']
    """
    import asyncio
    
    # Create semaphore for rate limiting
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def call_with_semaphore(prompt: str) -> str:
        async with semaphore:
            return await call_llm_async(
                prompt=prompt,
                system_prompt=system_prompt,
                model=model,
                temperature=temperature
            )
    
    # Execute all prompts in parallel (up to max_concurrent)
    tasks = [call_with_semaphore(prompt) for prompt in prompts]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to error messages
    results = []
    for i, response in enumerate(responses):
        if isinstance(response, Exception):
            logger.error(f"Batch prompt {i+1}/{len(prompts)} failed: {response}")
            results.append(f"ERROR: {str(response)}")
        else:
            results.append(response)
    
    return results


def get_llm_config() -> Dict[str, Any]:
    """
    Get current LLM configuration from environment variables.
    
    Useful for logging configuration at startup.
    
    Returns:
        Dict with LLM configuration parameters
        
    Examples:
        >>> config = get_llm_config()
        >>> print(config)
        {
            'model': 'grok-4-1-fast-reasoning',
            'api_host': 'https://api.x.ai/v1',
            'api_key_set': True,
            'max_async': 4
        }
    """
    return {
        "model": os.getenv("LLM_MODEL", "grok-4-1-fast-reasoning"),
        "extraction_model": os.getenv("EXTRACTION_LLM_NAME", "grok-4-1-fast-non-reasoning"),
        "api_host": os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1"),
        "api_key_set": bool(os.getenv("LLM_BINDING_API_KEY")),
        "max_async": int(os.getenv("MAX_ASYNC", "4")),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", "5"))
    }
