"""
LLM Client Utilities - Centralized async LLM wrapper for xAI Grok
=================================================================

Single source of truth for all LLM calls in the system.
Based on Branch 040 pattern but adapted for current architecture.

Key Features:
- Environment variable configuration (no hardcoding)
- Async support with optional batching
- JSON mode for structured outputs
- Consistent error handling

Usage:
    from src.utils.llm_client import call_llm_async, call_llm_batch
    
    # Simple text response
    response = await call_llm_async("What is 2+2?")
    
    # Batch processing with parallelization
    responses = await call_llm_batch(prompts, max_concurrent=8)
"""

import os
import asyncio
import logging
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


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
    - LLM_MODEL: Model name (default: grok-4-fast-reasoning)
    
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
    if model is None:
        model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    
    # Create AsyncOpenAI client with xAI endpoint (env vars, no hardcoding)
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
    
    if max_tokens:
        call_kwargs["max_tokens"] = max_tokens
    
    if json_mode:
        call_kwargs["response_format"] = {"type": "json_object"}
    
    try:
        response = await client.chat.completions.create(**call_kwargs)
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LLM API call failed: {e}")
        raise


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
    if max_concurrent is None:
        max_concurrent = int(os.getenv("MAX_ASYNC", "8"))
    
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
    """
    return {
        "model": os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
        "extraction_model": os.getenv("EXTRACTION_LLM_NAME", "grok-4-fast-reasoning"),
        "api_host": os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1"),
        "api_key_set": bool(os.getenv("LLM_BINDING_API_KEY")),
        "max_async": int(os.getenv("MAX_ASYNC", "8")),
        "max_retries": int(os.getenv("LLM_MAX_RETRIES", "5"))
    }

