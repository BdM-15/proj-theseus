"""
LLM Client Utilities - Centralized async LLM wrapper for xAI Grok
=================================================================

Single source of truth for all LLM calls in the system.
Based on Branch 040 pattern but adapted for current architecture.

Key Features:
- Environment variable configuration (no hardcoding)
- Async support with optional batching
- JSON mode for structured outputs
- Instructor integration for Pydantic-enforced responses (post-processing)
- Consistent error handling

Usage:
    from src.utils.llm_client import call_llm_async, call_llm_batch, call_llm_structured
    
    # Simple text response
    response = await call_llm_async("What is 2+2?")
    
    # Batch processing with parallelization
    responses = await call_llm_batch(prompts, max_concurrent=8)
    
    # Pydantic-enforced structured output (uses Instructor)
    result = await call_llm_structured(prompt, MyPydanticModel, max_retries=3)
"""

import os
import asyncio
import logging

from src.core.exceptions import LLMError
from typing import Optional, List, Dict, Any, Type, TypeVar

import instructor
from openai import AsyncOpenAI
from pydantic import BaseModel

from src.core import get_settings

logger = logging.getLogger(__name__)

# Type variable for Pydantic model generic
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
    
    Uses environment variables for configuration (Branch 040 pattern):
    - LLM_BINDING_API_KEY: API key
    - LLM_BINDING_HOST: API endpoint (default: https://api.x.ai/v1)
    - REASONING_LLM_NAME: Model name for inference tasks (default: grok-4-1-fast-reasoning)
    
    Args:
        prompt: User prompt text
        system_prompt: Optional system prompt (instructions)
        model: LLM model name (default: from LLM_MODEL env var)
        temperature: Sampling temperature 0.0-2.0 (default: 0.1 for deterministic)
        max_tokens: Maximum tokens in response
        json_mode: Force JSON output mode
    
    Returns:
        LLM response text
    """
    settings = get_settings()
    if model is None:
        # Default to reasoning model for inference/post-processing tasks (grok-4-1 series)
        model = settings.reasoning_llm_name
    
    # Create AsyncOpenAI client with xAI endpoint
    client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_host
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
    
    if max_tokens:
        call_kwargs["max_tokens"] = max_tokens
    
    if json_mode:
        call_kwargs["response_format"] = {"type": "json_object"}
    
    try:
        response = await client.chat.completions.create(**call_kwargs)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        raise LLMError(f"LLM API call failed", cause=e, model=model)


async def call_llm_batch(
    prompts: List[str],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_concurrent: Optional[int] = None
) -> List[str]:
    """
    Call LLM with multiple prompts in parallel (batched).
    
    Uses asyncio.Semaphore for rate limiting based on MAX_ASYNC env var.
    
    Args:
        prompts: List of user prompts
        system_prompt: Optional system prompt (same for all)
        model: LLM model name
        temperature: Sampling temperature
        max_concurrent: Maximum concurrent API calls (default: from MAX_ASYNC env var)
    
    Returns:
        List of LLM responses (same order as prompts)
    """
    settings = get_settings()
    if max_concurrent is None:
        max_concurrent = settings.get_effective_post_processing_max_async()
    
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


async def call_llm_structured(
    prompt: str,
    response_model: Type[T],
    system_prompt: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: Optional[int] = None,
    max_retries: int = 3
) -> T:
    """
    Call LLM with Pydantic schema enforcement using Instructor library.
    
    Uses Instructor's MD_JSON mode which:
    - Automatically strips markdown code blocks (```json...```)
    - Enforces Pydantic schema at API level (not post-validation)
    - Provides error feedback to LLM for self-correction on retry
    
    This is the RECOMMENDED approach for post-processing tasks that need
    structured JSON output (workload enrichment, relationship inference, etc.)
    
    Args:
        prompt: User prompt text
        response_model: Pydantic model class to enforce (e.g., WorkloadEnrichmentResponse)
        system_prompt: Optional system prompt
        model: LLM model name (default: REASONING_LLM_NAME for post-processing)
        temperature: Sampling temperature (default: 0.1 for deterministic)
        max_tokens: Maximum output tokens (default: LLM_MAX_OUTPUT_TOKENS)
        max_retries: Number of retries with error feedback (default: 3)
    
    Returns:
        Validated Pydantic model instance
    
    Raises:
        Exception: If all retries fail
    """
    settings = get_settings()
    if model is None:
        model = settings.reasoning_llm_name
    
    if max_tokens is None:
        max_tokens = settings.llm_max_output_tokens
    
    # Create OpenAI client wrapped with Instructor
    openai_client = AsyncOpenAI(
        api_key=settings.llm_api_key,
        base_url=settings.llm_host
    )
    
    # MD_JSON mode: automatically extracts JSON from markdown code blocks
    client = instructor.from_openai(openai_client, mode=instructor.Mode.MD_JSON)
    
    # Build messages
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    # Use Instructor with built-in retry and error feedback
    result = await client.chat.completions.create(
        model=model,
        response_model=response_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        max_retries=max_retries,  # Instructor handles retries with error feedback
    )
    
    return result


def get_llm_config() -> Dict[str, Any]:
    """
    Get current LLM configuration from centralized settings.
    Useful for logging configuration at startup.
    """
    settings = get_settings()
    return {
        "model": settings.reasoning_llm_name,
        "extraction_model": settings.extraction_llm_name,
        "api_host": settings.llm_host,
        "api_key_set": bool(settings.llm_api_key),
        "llm_max_async": settings.get_effective_llm_max_async(),
        "post_processing_max_async": settings.get_effective_post_processing_max_async(),
        "max_retries": settings.llm_max_retries
    }

