"""
JSON Extractor - Pydantic-validated entity extraction using Instructor.

This module provides schema-enforced LLM extraction that guarantees:
- All entities conform to our 18-type GovCon ontology
- Relationships reference valid entities (no ghost nodes)
- Automatic RECOVERY of malformed output via Instructor's retry mechanism

HOW RECOVERY WORKS:
1. LLM generates output
2. Pydantic validates against ExtractionResult schema
3. On validation failure, Instructor sends the error back to LLM:
   "entity_type 'Equipment' is not valid. Must be one of: requirement, clause..."
4. LLM corrects its output
5. Re-validate → repeat until success or max retries

This is NOT "trying the same thing again" - it's asking the LLM to FIX its output.
With 5 outer retries × 3 inner Instructor retries = up to 15 correction attempts.

Design: Uses Instructor library with xAI Grok for native Pydantic validation.
The extraction prompt is loaded from govcon_lightrag_native.txt to maintain
consistency with LightRAG's native extraction.

Issue #56: Pydantic adapter for 100% entity capture
"""

import os
import logging
import asyncio
from typing import Optional, List

import instructor
from pydantic import ValidationError

from src.ontology.schema import ExtractionResult

logger = logging.getLogger(__name__)


class JsonExtractor:
    """
    Extracts entities and relationships using Pydantic validation.
    
    Uses Instructor library for:
    - Native Pydantic model enforcement
    - Automatic retry with exponential backoff
    - Schema validation at parse time
    """
    
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-1-fast-non-reasoning")
        # Aggressive retry count - Instructor sends validation errors back to LLM for correction
        # Each outer retry has 3 inner Instructor retries = up to 15 total attempts
        self.max_retries = int(os.getenv("PYDANTIC_MAX_RETRIES", "5"))
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "131072"))  # 128K default
        
        if not self.api_key:
            raise ValueError("LLM_BINDING_API_KEY not found in environment variables")
        
        # Set for instructor's from_provider
        os.environ["XAI_API_KEY"] = self.api_key
        
        # Initialize instructor with xAI provider
        self.client = instructor.from_provider(
            f"xai/{self.model}",
            async_client=True
        )
        
        # Statistics tracking
        self._successful_extractions = 0
        self._failed_extractions = 0
        self.failed_chunks: List[dict] = []
        
        # Load extraction prompt (same as LightRAG uses)
        self.system_prompt = self._load_extraction_prompt()
        
        logger.info(f"✅ JsonExtractor initialized: model={self.model}, max_retries={self.max_retries}")
    
    def _load_extraction_prompt(self) -> str:
        """
        Load the SAME extraction prompt that LightRAG uses.
        
        CRITICAL: Must use the exact same GOVCON_PROMPTS["entity_extraction_system_prompt"]
        to maintain extraction quality parity with native LightRAG.
        We only add JSON output instructions as a suffix.
        """
        # Import the SAME prompts that LightRAG uses
        from prompts.govcon_prompt import GOVCON_PROMPTS
        
        # Get the exact extraction system prompt LightRAG uses
        lightrag_prompt = GOVCON_PROMPTS.get("entity_extraction_system_prompt", "")
        
        if not lightrag_prompt:
            logger.warning("Could not load GOVCON_PROMPTS, falling back to file")
            prompt_path = os.path.join(os.getcwd(), "prompts", "extraction", "govcon_lightrag_native.txt")
            try:
                with open(prompt_path, "r", encoding="utf-8") as f:
                    lightrag_prompt = f.read()
            except FileNotFoundError:
                logger.error(f"Domain knowledge not found at {prompt_path}")
                lightrag_prompt = ""
        
        # JSON output instructions - appended to the SAME prompt LightRAG uses
        json_instructions = """

# OUTPUT FORMAT: JSON (Pydantic Schema)

IMPORTANT: Instead of the pipe-delimited format above, output a JSON object:

```json
{
  "entities": [
    {
      "entity_name": "Title Case Entity Name",
      "entity_type": "requirement|clause|section|document|deliverable|evaluation_factor|submission_instruction|statement_of_work|performance_metric|strategic_theme|organization|program|equipment|technology|concept|location|event|person",
      "description": "Comprehensive description with context, values, and relationships.",
      "criticality": "MANDATORY|IMPORTANT|OPTIONAL|INFORMATIONAL",
      "modal_verb": "shall|must|will|should|may",
      "req_type": "FUNCTIONAL|PERFORMANCE|SECURITY|TECHNICAL|INTERFACE|MANAGEMENT|DESIGN|QUALITY|OTHER",
      "labor_drivers": ["list of workload indicators"],
      "material_needs": ["list of equipment/supplies"]
    }
  ],
  "relationships": [
    {
      "source_entity": {"entity_name": "Source Name", "entity_type": "type", "description": "brief description"},
      "target_entity": {"entity_name": "Target Name", "entity_type": "type", "description": "brief description"},
      "relationship_type": "EVALUATED_BY|GUIDES|CHILD_OF|ATTACHMENT_OF|PRODUCES|REFERENCES|REQUIRES|etc",
      "description": "Explanation of the relationship"
    }
  ]
}
```

CRITICAL RULES:
1. entity_type MUST be one of the 18 valid types listed above - NO OTHER VALUES
2. entity_name should be Title Case and consistent across all references
3. All relationships must reference entities that exist in the entities array
4. Output ONLY the JSON object - no markdown, no explanations, no preamble
5. Follow ALL the extraction rules from above - just change the output format to JSON
"""
        
        # Combine: Full LightRAG prompt + JSON output suffix
        full_prompt = f"{lightrag_prompt}\n{json_instructions}"
        
        logger.info(f"📋 Extraction prompt loaded (LightRAG-compatible): {len(full_prompt):,} chars (~{len(full_prompt)//4:,} tokens)")
        return full_prompt
    
    async def extract(self, text: str, chunk_id: str = "unknown") -> ExtractionResult:
        """
        Extract entities and relationships from text using Pydantic validation.
        
        Args:
            text: The text chunk to extract from
            chunk_id: Identifier for logging/tracking
            
        Returns:
            ExtractionResult with validated entities and relationships.
            Returns empty result on failure (graceful degradation).
        """
        try:
            logger.info(f"🔄 [{chunk_id}] Pydantic extraction ({len(text)} chars)")
            
            result = await self._extract_with_retry(text, chunk_id)
            
            self._successful_extractions += 1
            logger.info(f"✅ [{chunk_id}] Extracted {len(result.entities)} entities, {len(result.relationships)} relationships")
            return result
            
        except Exception as e:
            self._failed_extractions += 1
            self.failed_chunks.append({
                "chunk_id": chunk_id,
                "text_length": len(text),
                "error": str(e),
                "error_type": type(e).__name__
            })
            
            # Calculate failure rate
            total = self._successful_extractions + self._failed_extractions
            failure_rate = self._failed_extractions / max(total, 1) * 100
            
            logger.warning(
                f"⚠️ [{chunk_id}] Pydantic extraction failed ({type(e).__name__}): {str(e)[:200]}"
                f" | Failure rate: {failure_rate:.1f}%"
            )
            
            # Graceful degradation - return empty result
            return ExtractionResult(entities=[], relationships=[])
    
    async def _extract_with_retry(self, text: str, chunk_id: str) -> ExtractionResult:
        """
        Internal extraction with manual retry logic.
        
        Uses exponential backoff (5s, 15s, 45s) between retries.
        """
        max_attempts = self.max_retries
        last_error = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                logger.debug(f"[{chunk_id}] Attempt {attempt}/{max_attempts}")
                
                # Instructor's retry mechanism:
                # - On Pydantic validation failure, sends error back to LLM
                # - LLM corrects output (e.g., "entity_type must be one of...")
                # - Re-validates until success or max_retries exhausted
                result = await self.client.chat.completions.create(
                    model=self.model,
                    response_model=ExtractionResult,
                    max_retries=3,  # Instructor sends validation errors to LLM for correction
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": f"Extract entities and relationships from this text:\n\n{text}"}
                    ],
                    temperature=0.1,
                    max_tokens=self.max_output_tokens,
                )
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(f"[{chunk_id}] Attempt {attempt}/{max_attempts} failed: {type(e).__name__}")
                
                if attempt < max_attempts:
                    delay = 5 * (3 ** (attempt - 1))  # 5s, 15s, 45s
                    logger.info(f"[{chunk_id}] Retrying in {delay}s...")
                    await asyncio.sleep(delay)
        
        raise last_error
    
    def get_extraction_stats(self) -> dict:
        """Get extraction statistics for monitoring."""
        total = self._successful_extractions + self._failed_extractions
        failure_rate = self._failed_extractions / max(total, 1) * 100
        
        return {
            "successful_extractions": self._successful_extractions,
            "failed_extractions": self._failed_extractions,
            "total_attempts": total,
            "failure_rate_percent": round(failure_rate, 2),
            "acceptable": failure_rate <= 5.0,  # 5% tolerance
            "failed_chunks": [
                {
                    "chunk_id": fc["chunk_id"],
                    "text_length": fc["text_length"],
                    "error_type": fc["error_type"],
                    "error": fc["error"][:200]
                }
                for fc in self.failed_chunks[-10:]  # Last 10 failures
            ]
        }

