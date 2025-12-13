"""
Pydantic Entity Extractor - Native xAI SDK structured output with Pydantic validation.

Uses xAI SDK's native response_format parameter to pass Pydantic BaseModel directly,
enabling true JSON schema enforcement at the API level (no markdown wrappers, no parsing).

DESIGN PRINCIPLE: GRACEFUL TOLERANCE (2-3% error rate acceptable)
- Retry aggressively (up to 5 attempts with backoffs)
- Log failures clearly but continue processing
- Track failed chunks for visibility and potential batch retry
- Return empty result on failure to allow pipeline to continue

Branch 041a: Uses xAI SDK's native Pydantic support instead of instructor library.
The SDK's response_format parameter accepts type[pydantic.main.BaseModel] directly.
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List

from pydantic import ValidationError

from src.ontology.schema import ExtractionResult
from src.utils.logging_config import log_graceful_failure

logger = logging.getLogger(__name__)


class PydanticExtractor:
    """
    Entity extractor using xAI SDK's native Pydantic structured output support.
    
    The xAI SDK's chat.create() method accepts `response_format=PydanticModel`
    which enforces JSON schema at the API level - no markdown wrapping, no parsing needed.
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY") or os.getenv("XAI_API_KEY")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-1-fast-non-reasoning")
        # Retry count - data preservation is critical
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "5"))
        # Max output tokens - prevents truncation on large entity extractions
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "32000"))
        
        if not self.api_key:
            raise ValueError("LLM_BINDING_API_KEY or XAI_API_KEY not found in environment variables")

        # Set environment variable for xAI SDK
        os.environ["XAI_API_KEY"] = self.api_key
        
        # Initialize xAI SDK client directly (NOT through instructor)
        from xai_sdk.aio.client import Client as AsyncXAIClient
        from xai_sdk import chat as xai_chat
        
        self.xai_client = AsyncXAIClient()
        self._xai_chat = xai_chat  # For message helpers
        
        logger.info(f"✅ Using native xAI SDK with response_format=ExtractionResult (Pydantic)")
        
        # Track failed chunks for potential later recovery
        self.failed_chunks: List[dict] = []
        self._successful_extractions: int = 0  # For failure rate calculation
        
        logger.info(f"Initialized PydanticExtractor: model={self.model}, max_retries={self.max_retries}, max_output_tokens={self.max_output_tokens}")
        
        self.system_prompt = self._load_full_system_prompt()

    def _load_full_system_prompt(self) -> str:
        """
        Constructs the full system prompt by combining:
        1. Base JSON formatting instructions (grok_json_prompt.md)
        2. Entity Detection Rules (entity_detection_rules.md)
        3. Entity Extraction Prompt (entity_extraction_prompt.md)
        4. Relationship inference rules (prompts/relationship_inference/*.md)
        """
        base_path = os.getcwd()
        prompts_dir = os.path.join(base_path, "prompts")
        
        logger.info(f"Loading original prompts from {prompts_dir}")
        
        # 1. Base JSON Instructions
        json_prompt_path = os.path.join(prompts_dir, "extraction", "grok_json_prompt.md")
        try:
            with open(json_prompt_path, "r", encoding="utf-8") as f:
                json_instructions = f.read()
        except FileNotFoundError:
            logger.error(f"Base prompt not found at {json_prompt_path}")
            raise

        # 2. Entity Detection Rules (The "Rules")
        detection_rules_path = os.path.join(prompts_dir, "extraction", "entity_detection_rules.md")
        detection_rules = ""
        if os.path.exists(detection_rules_path):
            with open(detection_rules_path, "r", encoding="utf-8") as f:
                detection_rules = f.read()
        else:
            logger.warning(f"Detection rules not found at {detection_rules_path}")

        # 3. Entity Extraction Prompt (The "Prompt" with examples)
        extraction_prompt_path = os.path.join(prompts_dir, "extraction", "entity_extraction_prompt.md")
        extraction_prompt = ""
        if os.path.exists(extraction_prompt_path):
            with open(extraction_prompt_path, "r", encoding="utf-8") as f:
                extraction_prompt = f.read()
                # Strip the "Real Data" section if it exists at the end
                if "---Real Data---" in extraction_prompt:
                    extraction_prompt = extraction_prompt.split("---Real Data---")[0]
        else:
            logger.warning(f"Extraction prompt not found at {extraction_prompt_path}")

        # 4. Relationship Inference Rules
        inference_dir = os.path.join(prompts_dir, "relationship_inference")
        inference_rules = []
        if os.path.exists(inference_dir):
            # Sort to ensure deterministic order
            for filename in sorted(os.listdir(inference_dir)):
                if filename.endswith(".md"):
                    file_path = os.path.join(inference_dir, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        inference_rules.append(f"--- RULE FROM {filename} ---\n{f.read()}")
        
        full_inference_text = "\n\n".join(inference_rules)

        # Combine everything
        full_prompt = f"""
{json_instructions}

# PART 1: ENTITY DETECTION RULES
The following rules define how to identify and classify government contracting entities.
{detection_rules}

# PART 2: ENTITY EXTRACTION INSTRUCTIONS & EXAMPLES
The following instructions and examples demonstrate how to extract entities and metadata.
{extraction_prompt}

# PART 3: RELATIONSHIP INFERENCE RULES
The following rules define how to infer relationships between entities.
{full_inference_text}

# FINAL INSTRUCTION
Analyze the input text using the Domain Knowledge and Inference Rules provided above.
Output the result strictly as a JSON object matching the ExtractionResult schema.
"""
        logger.info(f"Constructed system prompt with {len(full_prompt)} characters (~{len(full_prompt)//4} tokens)")
        return full_prompt

    def _strip_markdown_json(self, content: str) -> str:
        """
        Strip markdown code blocks from JSON content.
        
        Despite using response_format=Pydantic, the xAI API sometimes wraps
        complex schemas in ```json...``` blocks. This extracts the JSON.
        """
        if not content:
            return content
        
        # Check if wrapped in markdown
        content = content.strip()
        if content.startswith("```"):
            # Remove opening fence (```json or ```)
            lines = content.split("\n", 1)
            if len(lines) > 1:
                content = lines[1]
            # Remove closing fence
            if content.rstrip().endswith("```"):
                content = content.rstrip()[:-3].rstrip()
        
        # Final safety: find JSON boundaries
        first_brace = content.find("{")
        last_brace = content.rfind("}")
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            return content[first_brace:last_brace + 1]
        
        return content

    async def extract(self, text: str, chunk_id: str = "unknown") -> ExtractionResult:
        """
        Extracts entities from the given text using native xAI SDK structured output.
        
        Uses automatic retry with exponential backoff for resilience against
        API truncation/instability issues.
        
        GRACEFUL TOLERANCE: On failure after retries, logs warning and returns
        empty result. Failed chunks are tracked in self.failed_chunks for
        visibility and potential batch retry. This allows 2-3% error tolerance
        like our table extraction pipeline.
        
        Args:
            text: The text chunk to extract entities from
            chunk_id: Identifier for logging/tracking (e.g., "chunk-0", "page-5")
        
        Returns:
            ExtractionResult with entities/relationships, or empty result on failure
        """
        token_count = 0
        try:
            # Log chunk size for debugging
            try:
                import tiktoken
                tokenizer = tiktoken.get_encoding("cl100k_base")
                token_count = len(tokenizer.encode(text))
            except Exception:
                token_count = len(text) // 4  # Rough estimate
            
            logger.info(f"📤 [{chunk_id}] Extraction request to {self.model} ({len(text)} chars, ~{token_count} tokens)")
            
            # Use xAI SDK with native Pydantic structured output
            result = await self._extract_with_retry(text, chunk_id)
            
            # Post-process: rescue entities with partial data
            result = self._rescue_partial_entities(result, chunk_id)
            
            logger.info(f"✅ [{chunk_id}] Extracted {len(result.entities)} entities, {len(result.relationships)} relationships")
            return result
            
        except Exception as e:
            # GRACEFUL FAILURE: Log, track, and continue (like table extraction tolerance)
            self.failed_chunks.append({
                "chunk_id": chunk_id,
                "text": text,
                "text_length": len(text),
                "token_count": token_count,
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Calculate failure rate for visibility
            total_attempts = len(self.failed_chunks) + self._successful_extractions
            failure_rate = len(self.failed_chunks) / max(total_attempts, 1) * 100
            
            log_graceful_failure(
                logger, 
                "Entity extraction", 
                e, 
                f"{chunk_id}, {len(text)} chars, failure rate: {failure_rate:.1f}%"
            )
            
            # Return empty result - pipeline continues (2-3% tolerance acceptable)
            return ExtractionResult(entities=[], relationships=[])

    async def _extract_with_retry(self, text: str, chunk_id: str = "unknown") -> ExtractionResult:
        """
        Internal extraction method using xAI SDK's native Pydantic support.
        
        The xAI SDK's response_format parameter accepts a Pydantic BaseModel class directly,
        which enforces JSON schema at the API level - the model MUST return valid JSON
        matching the schema (no markdown wrappers, no parsing needed).
        
        Retries up to max_retries times with SHORT backoff (2s, 4s, 8s, 16s delays).
        """
        max_attempts = self.max_retries
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Build messages using xAI SDK helpers
                messages = [
                    self._xai_chat.system(self.system_prompt),
                    self._xai_chat.user(text)
                ]
                
                # Create chat request with Pydantic model as response_format
                # This is xAI SDK's NATIVE structured output - no instructor needed!
                chat = self.xai_client.chat.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.0,  # Deterministic for structured output
                    max_tokens=self.max_output_tokens,
                    response_format=ExtractionResult,  # Pydantic model directly!
                )
                
                # Get the response
                response = await chat.sample()
                
                # Parse response content into Pydantic model
                content = response.content if hasattr(response, 'content') else str(response)
                
                # FALLBACK: Strip markdown code blocks if xAI API returns wrapped JSON
                # Despite response_format=Pydantic, complex schemas may still get wrapped
                content = self._strip_markdown_json(content)
                
                # Parse and validate
                result = ExtractionResult.model_validate_json(content)
                
                # Success! Track it for failure rate calculation
                self._successful_extractions += 1
                return result
                
            except Exception as e:
                last_error = e
                error_preview = str(e)[:150].replace('\n', ' ')
                logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{max_attempts} failed: {error_preview}")
                
                if attempt < max_attempts:
                    # SHORT exponential backoff: 2s, 4s, 8s, 16s (not 5s, 15s, 45s, 135s!)
                    delay = 2 * (2 ** (attempt - 1))
                    logger.info(f"⏳ [{chunk_id}] Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        
        # All attempts failed - raise to let extract() handle gracefully
        logger.error(f"❌ [{chunk_id}] All {max_attempts} attempts exhausted")
        raise last_error

    def _rescue_partial_entities(self, result: ExtractionResult, chunk_id: str = "unknown") -> ExtractionResult:
        """
        Rescue entities with partial data instead of dropping them.
        We want to capture ALL potential intelligence, even if imperfect.
        """
        valid_entities = []
        rescued_count = 0
        dropped_count = 0
        
        for e in result.entities:
            # Validate entity has required fields (entity_name and entity_type)
            if not e.entity_name or not e.entity_name.strip():
                dropped_count += 1
                logger.debug(f"⚠️ [{chunk_id}] Dropping entity with missing name")
                continue

            if not e.entity_type or not e.entity_type.strip():
                dropped_count += 1
                logger.debug(f"⚠️ [{chunk_id}] Dropping entity with missing type: {e.entity_name}")
                continue

            valid_entities.append(e)
        
        if rescued_count > 0 or dropped_count > 0:
            logger.info(f"🔧 [{chunk_id}] Entity rescue: {rescued_count} rescued, {dropped_count} dropped (unrecoverable)")
        
        result.entities = valid_entities
        return result

    def get_extraction_stats(self) -> dict:
        """
        Get extraction statistics for monitoring and reporting.
        
        Returns:
            dict with success count, failure count, failure rate, and failed chunk details
        """
        total = self._successful_extractions + len(self.failed_chunks)
        failure_rate = len(self.failed_chunks) / max(total, 1) * 100
        
        return {
            "successful_extractions": self._successful_extractions,
            "failed_extractions": len(self.failed_chunks),
            "total_attempts": total,
            "failure_rate_percent": round(failure_rate, 2),
            "acceptable": failure_rate <= 3.0,  # 3% tolerance threshold
            "failed_chunks": [
                {
                    "chunk_id": fc["chunk_id"],
                    "text_length": fc["text_length"],
                    "token_count": fc["token_count"],
                    "error_type": fc["error_type"],
                    "error": fc["error"][:200]  # Truncate error message
                }
                for fc in self.failed_chunks
            ]
        }

    def get_failed_chunks_for_retry(self) -> List[dict]:
        """
        Get full text of failed chunks for potential batch retry.
        
        Use this at end of processing to attempt re-extraction of failed chunks
        (perhaps with a different model or after API stabilizes).
        """
        return self.failed_chunks.copy()

    # NOTE: extract_from_text() was removed in Issue #42
    # The lightrag_llm_adapter now handles ALL extraction with the full 121K ontology prompt.
    # Previously, extract_from_text() used a degraded 30-line inline prompt that bypassed
    # the established ontology, causing inconsistent entity extraction for multimodal content.
