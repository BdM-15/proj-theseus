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
from pathlib import Path

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
        
        logger.info(f"Initialized Instructor client with xAI model: {self.model}, max_retries: {self.max_retries}")
        
        self.system_prompt = self._load_full_system_prompt()

    def _strip_markdown_formatting(self, text: str) -> str:
        """
        Strip markdown formatting overhead while preserving ALL content and intelligence.
        
        Removes:
        - Header markers (# ## ### etc.) but keeps the text
        - Code fence markers (```) but keeps the code content
        - Excessive blank lines (collapse to single)
        - Leading/trailing whitespace per line
        
        Preserves:
        - All actual content, examples, rules, and instructions
        - Bullet points and numbered lists (they're semantic)
        - Indentation structure
        - JSON examples and code blocks (just removes the ``` markers)
        """
        import re
        
        lines = text.split('\n')
        result = []
        in_code_block = False
        
        for line in lines:
            # Track code blocks but don't add the fence markers
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue  # Skip the fence marker itself
            
            # Strip header markers but keep the text
            # Match # at start of line followed by space
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # Keep the header text, just remove the # markers
                result.append(header_match.group(2))
                continue
            
            # Keep everything else as-is
            result.append(line)
        
        # Collapse multiple blank lines to single
        text = '\n'.join(result)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()

    def _load_full_system_prompt(self) -> str:
        """
        Load modular prompt components and assemble into full system prompt.
        
        V2 Architecture (prompts/extraction_v2/) - Self-contained, examples inline with rules:
        - 01_core_extraction_philosophy.txt: Core philosophy and quality requirements
        - 02_entity_classification_rules.txt: Entity detection patterns + 12 annotated examples
        - 03_json_schema_specification.txt: JSON schema specification and validation
        - 04_relationship_extraction_rules.txt: Relationship patterns + 11 annotated examples
        - _schema_mirror/*.txt: 18 auto-generated entity type definitions from Pydantic models
        
        Returns assembled prompt ~32K tokens (23% reduction from original 42K).
        """
        base_path = os.getcwd()
        prompts_dir = os.path.join(base_path, "prompts", "extraction_v2")

        logger.info(f"Loading modular prompts from {prompts_dir}")
        
        components = []
        
        # Core components (required) - ALL from V2 architecture
        # Examples are now inline with their respective rule files
        core_files = [
            ("01_core_extraction_philosophy.txt", "CORE PHILOSOPHY"),
            ("02_entity_classification_rules.txt", "ENTITY CLASSIFICATION RULES"),
            ("03_json_schema_specification.txt", "JSON SCHEMA SPECIFICATION"),
            ("04_relationship_extraction_rules.txt", "RELATIONSHIP EXTRACTION RULES"),
        ]
        
        for filename, section_name in core_files:
            filepath = os.path.join(prompts_dir, filename)
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Required prompt component missing: {filepath}")
            
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            components.append(f"{'=' * 80}\n{section_name}\n{'=' * 80}\n\n{content}")
            logger.debug(f"  ✅ {filename}: {len(content)} chars")
        
        # 2. Schema-mirror entity definitions (auto-generated from Pydantic)
        schema_mirror_dir = os.path.join(prompts_dir, "_schema_mirror")
        entity_defs = []
        
        if os.path.exists(schema_mirror_dir):
            for entity_file in sorted(Path(schema_mirror_dir).glob("*.txt")):
                if entity_file.name != "README.txt":
                    with open(entity_file, "r", encoding="utf-8") as f:
                        entity_defs.append(f.read())
            
            if entity_defs:
                components.append(
                    f"{'=' * 80}\nENTITY TYPE DEFINITIONS (Schema-Aligned)\n{'=' * 80}\n\n" 
                    + "\n".join(entity_defs)
                )
                logger.debug(f"  ✅ {len(entity_defs)} entity type definitions")
        
        # Assemble final prompt
        full_prompt = "\n\n".join(components)
        full_prompt += f"\n\n{'=' * 80}\nEXTRACTION TASK\n{'=' * 80}\n"
        full_prompt += "Extract entities and relationships from the input text using the rules above.\n"
        full_prompt += "\n---Real Data---\n"
        
        logger.info(f"✅ Assembled prompt: {len(full_prompt)} chars (~{len(full_prompt)//4} tokens)")
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

    async def extract_from_text(self, text: str, chunk_id: str) -> ExtractionResult:
        """
        Extract entities from arbitrary text using govcon ontology.
        
        Used by modal processors (tables, images) to analyze converted descriptions.
        
        Args:
            text: Text to extract entities from (e.g., table description)
            chunk_id: Identifier for provenance tracking (e.g., "table-page42-idx15")
        
        Returns:
            ExtractionResult with entities and relationships
        """
        user_prompt = f"""Extract entities and relationships from this government contracting content.

SOURCE: {chunk_id}

CONTENT:
{text}

Extract all relevant entities following the government contracting ontology:
- Requirements (with criticality: MANDATORY/IMPORTANT/OPTIONAL)
- Performance metrics (with thresholds and measurement methods)
- Evaluation factors (with weights and subfactors)
- Deliverables (with formats and due dates)
- Strategic themes (customer hot buttons, discriminators, proof points)
- Other entity types as appropriate

Return structured JSON using the ExtractionResult schema."""

        try:
            result = await self._extract_with_retry(user_prompt, chunk_id)
            
            logger.info(
                f"📝 Extracted from text ({chunk_id}): "
                f"{len(result.entities)} entities, {len(result.relationships)} relationships"
            )
            
            return result
            
        except Exception as e:
            log_graceful_failure(logger, "Entity extraction", e, chunk_id)
            return ExtractionResult(entities=[], relationships=[])
