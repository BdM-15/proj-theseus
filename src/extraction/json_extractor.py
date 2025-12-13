"""
Entity extraction using Instructor library with xAI Grok.

Issue #6: Migrated from OpenAI SDK to Instructor for:
- Native Pydantic validation (no manual JSON parsing)
- Automatic retry with exponential backoff
- Better error recovery on truncated responses

DESIGN PRINCIPLE: GRACEFUL TOLERANCE (2-3% error rate acceptable)
- Retry aggressively (up to 5 attempts with backoffs)
- Log failures clearly but continue processing (like table extraction tolerance)
- Track failed chunks for visibility and potential batch retry
- Return empty result on failure to allow pipeline to continue
- The orchestrator can check failed_chunks at end of processing
"""

import os
import json
import logging
import asyncio
from typing import Optional, Dict, Any, List

import instructor
from tenacity import retry, stop_after_attempt, wait_exponential, before_log, after_log
from pydantic import ValidationError

from src.ontology.schema import ExtractionResult
from src.utils.logging_config import log_graceful_failure

logger = logging.getLogger(__name__)


class JsonExtractor:
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-fast-reasoning")
        # More aggressive retry count - data preservation is critical
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "5"))
        # Max output tokens - prevents truncation on large entity extractions
        # Default 32K is safe; .env can set higher (e.g., 524288 for Grok's 2M context)
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "32000"))
        
        if not self.api_key:
            logger.warning("LLM_BINDING_API_KEY not found, checking XAI_API_KEY")
            self.api_key = os.getenv("XAI_API_KEY")
            
        if not self.api_key:
            raise ValueError("LLM_BINDING_API_KEY or XAI_API_KEY not found in environment variables")

        # Set XAI_API_KEY for instructor's from_provider
        os.environ["XAI_API_KEY"] = self.api_key
        
        # Initialize instructor with xAI provider (handles retries, validation, etc.)
        # async_client=True for async support
        self.client = instructor.from_provider(
            f"xai/{self.model}",
            async_client=True
        )
        
        # Track failed chunks for potential later recovery
        self.failed_chunks: List[dict] = []
        self._successful_extractions: int = 0  # For failure rate calculation
        
        logger.info(f"Initialized Instructor client with xAI model: {self.model}, max_retries: {self.max_retries}, max_output_tokens: {self.max_output_tokens}")
        
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
Output the result strictly as a JSON object matching the schema defined in the first section.
"""
        logger.info(f"Constructed system prompt with {len(full_prompt)} characters (~{len(full_prompt)//4} tokens)")
        return full_prompt

    async def extract(self, text: str, chunk_id: str = "unknown") -> ExtractionResult:
        """
        Extracts entities from the given text using Instructor + xAI Grok.
        
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
            import tiktoken
            tokenizer = tiktoken.get_encoding("cl100k_base")
            token_count = len(tokenizer.encode(text))
            logger.info(f"📤 [{chunk_id}] Extraction request to {self.model} ({len(text)} chars, ~{token_count} tokens)")
            
            # Use instructor with built-in retry mechanism
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
        Internal extraction method with manual retry logic.
        
        Retries up to max_retries times with exponential backoff (5s, 15s, 45s, 135s delays)
        on any exception (API errors, truncation, validation failures).
        """
        max_attempts = self.max_retries
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"🔄 [{chunk_id}] Extraction attempt {attempt}/{max_attempts}")
                
                result = await self.client.chat.completions.create(
                    model=self.model,
                    response_model=ExtractionResult,
                    max_retries=2,  # Instructor's internal retry for validation errors
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text}
                    ],
                    temperature=0.1,
                    max_tokens=self.max_output_tokens,  # Prevents truncation on large extractions
                )
                
                # Success! Track it for failure rate calculation
                self._successful_extractions += 1
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{max_attempts} failed: {type(e).__name__}: {str(e)[:200]}")
                
                if attempt < max_attempts:
                    # Exponential backoff: 5s, 15s, 45s, 135s
                    delay = 5 * (3 ** (attempt - 1))
                    logger.info(f"⏳ [{chunk_id}] Retrying in {delay} seconds...")
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
