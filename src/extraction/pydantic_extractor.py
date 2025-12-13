"""
Pydantic Entity Extractor - Structured extraction using Instructor + xAI Grok.

Uses instructor.from_provider("xai/{model}") for:
- Native xAI API support (proven reliable in branch 040)
- Native Pydantic validation with schema enforcement
- Error feedback to LLM for self-correction on retry
- Type-safe entity extraction matching ontology schema

DESIGN PRINCIPLE: GRACEFUL TOLERANCE (2-3% error rate acceptable)
- Retry aggressively with error feedback to LLM
- Differentiate JSON errors (truncation) vs validation errors (schema)
- Feed specific error messages back to help LLM self-correct
- Return empty result on failure to allow pipeline to continue

Branch 041a: Uses native xAI provider + error feedback pattern.
"""

import os
import json
import logging
import asyncio
from typing import List, Optional

import instructor
from pydantic import ValidationError

from src.ontology.schema import ExtractionResult
from src.utils.logging_config import log_graceful_failure

logger = logging.getLogger(__name__)


class PydanticExtractor:
    """
    Entity extractor using Instructor library with native xAI provider.
    
    Uses instructor.from_provider("xai/{model}") for:
    - Native xAI API support (not OpenAI-compatible wrapper)
    - Automatic Pydantic validation with schema enforcement
    - Built-in retry logic for validation errors
    
    Error feedback pattern:
    - On validation failure, feed error message back to LLM
    - LLM can self-correct based on specific validation issues
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY") or os.getenv("XAI_API_KEY")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-1-fast-non-reasoning")
        # Retry count - data preservation is critical
        self.max_retries = int(os.getenv("LLM_MAX_RETRIES", "5"))
        # Max output tokens - prevents truncation on large entity extractions
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "524288"))
        # Temperature from env (extraction-specific → global → default)
        self.temperature = float(os.getenv("EXTRACTION_LLM_TEMPERATURE", os.getenv("LLM_MODEL_TEMPERATURE", "0.1")))
        
        if not self.api_key:
            raise ValueError("LLM_BINDING_API_KEY or XAI_API_KEY not found in environment variables")
        
        # Set XAI_API_KEY for instructor's from_provider
        os.environ["XAI_API_KEY"] = self.api_key
        
        # Use instructor's native xAI provider (NOT OpenAI-compatible wrapper)
        # This is what worked reliably in branch 040
        self.client = instructor.from_provider(
            f"xai/{self.model}",
            async_client=True
        )
        
        logger.info(f"✅ Using instructor.from_provider('xai/{self.model}')")
        
        # Track failed chunks for potential later recovery
        self.failed_chunks: List[dict] = []
        self._successful_extractions: int = 0  # For failure rate calculation
        
        logger.info(f"Initialized PydanticExtractor: model={self.model}, temp={self.temperature}, max_retries={self.max_retries}, max_tokens={self.max_output_tokens}")
        
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
            try:
                import tiktoken
                tokenizer = tiktoken.get_encoding("cl100k_base")
                token_count = len(tokenizer.encode(text))
            except Exception:
                token_count = len(text) // 4  # Rough estimate
            
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
        Internal extraction method with ERROR FEEDBACK pattern.
        
        Key improvement from ML Mastery article:
        - On validation failure, feed error message back to LLM
        - LLM can self-correct based on specific validation issues
        - Differentiate between JSON errors (truncation) vs validation errors (schema)
        
        Retries up to max_retries times with SHORT backoff (2s, 4s, 8s, 16s delays).
        """
        max_attempts = self.max_retries
        last_error: Optional[str] = None
        last_error_type: Optional[str] = None  # "json", "validation", or "other"
        
        for attempt in range(1, max_attempts + 1):
            try:
                # Build messages - include error feedback on retry
                messages = [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ]
                
                # ERROR FEEDBACK: Include validation error from previous attempt
                if last_error and attempt > 1:
                    feedback = self._build_error_feedback(last_error, last_error_type)
                    messages.append({"role": "user", "content": feedback})
                    logger.info(f"🔄 [{chunk_id}] Attempt {attempt} with {last_error_type} error feedback")
                
                # Use instructor's native xAI provider with Pydantic validation
                result = await self.client.chat.completions.create(
                    model=self.model,
                    response_model=ExtractionResult,
                    max_retries=2,  # Instructor's internal retry for validation errors
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_output_tokens,
                )
                
                # Success! Track it for failure rate calculation
                self._successful_extractions += 1
                return result
                
            except json.JSONDecodeError as e:
                # JSON structure problem - likely truncation or invalid syntax
                last_error = str(e)
                last_error_type = "json"
                error_preview = last_error[:100].replace('\n', ' ')
                logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{max_attempts} JSON error: {error_preview}")
                
            except ValidationError as e:
                # Pydantic validation error - schema mismatch
                last_error = str(e)
                last_error_type = "validation"
                error_preview = last_error[:100].replace('\n', ' ')
                logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{max_attempts} validation error: {error_preview}")
                
            except Exception as e:
                # Other errors (network, rate limit, API errors, etc.)
                error_str = str(e)
                last_error = error_str
                
                # Check if it's actually a JSON/validation error wrapped in another exception
                if "Invalid JSON" in error_str or "EOF" in error_str or "column" in error_str:
                    last_error_type = "json"
                elif "validation error" in error_str.lower():
                    last_error_type = "validation"
                else:
                    last_error_type = "other"
                    
                error_preview = error_str[:100].replace('\n', ' ')
                logger.warning(f"⚠️ [{chunk_id}] Attempt {attempt}/{max_attempts} {last_error_type} error: {error_preview}")
            
            # Backoff before retry
            if attempt < max_attempts:
                # SHORT exponential backoff: 2s, 4s, 8s, 16s
                delay = 2 * (2 ** (attempt - 1))
                logger.info(f"⏳ [{chunk_id}] Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        # All attempts failed - raise to let extract() handle gracefully
        logger.error(f"❌ [{chunk_id}] All {max_attempts} attempts exhausted")
        raise Exception(f"Extraction failed after {max_attempts} attempts: {last_error}")

    def _build_error_feedback(self, error: str, error_type: Optional[str]) -> str:
        """
        Build targeted error feedback message for LLM self-correction.
        
        Pattern from ML Mastery article - specific feedback helps LLM fix issues.
        Truncation errors get special handling to request fewer entities.
        """
        if error_type == "json":
            # JSON structure error - often truncation
            if "EOF" in error or "column" in error or "parsing" in error.lower():
                return (
                    "⚠️ CRITICAL: Your previous response was TRUNCATED (incomplete JSON).\n\n"
                    "The JSON was cut off before completion. To fix this:\n"
                    "1. Output FEWER entities (focus on the 15-20 MOST IMPORTANT ones)\n"
                    "2. Use shorter descriptions (max 50 chars each)\n"
                    "3. Skip relationships - just output entities\n"
                    "4. Ensure JSON ends with proper closing: ]}\n\n"
                    "Try again with a SHORTER, COMPLETE response:"
                )
            else:
                return (
                    f"⚠️ JSON SYNTAX ERROR: {error[:150]}\n\n"
                    "Please output valid JSON only:\n"
                    "- No markdown code blocks (no ```json)\n"
                    "- Start with { end with }\n"
                    "- Properly escape strings\n\n"
                    "Try again:"
                )
        
        elif error_type == "validation":
            # Pydantic validation error - schema mismatch
            return (
                f"⚠️ SCHEMA VALIDATION ERROR:\n{error[:250]}\n\n"
                "Please fix the schema issues:\n"
                "- entity_type must be one of: requirement, clause, section, document, "
                "deliverable, evaluation_factor, submission_instruction, statement_of_work, "
                "performance_metric, strategic_theme, organization, program, equipment, "
                "technology, concept, location, event, person\n"
                "- All entities need entity_name and entity_type\n"
                "- Relationships need source_entity and target_entity as objects\n\n"
                "Try again with corrected JSON:"
            )
        
        else:
            # Generic error
            return (
                f"⚠️ PREVIOUS ATTEMPT FAILED: {error[:150]}\n\n"
                "Please try again with valid JSON output.\n"
                "Output fewer entities if needed to ensure complete response."
            )

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
