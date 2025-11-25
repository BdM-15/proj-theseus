import os
import json
import logging
from typing import Optional, Dict, Any
from xai_sdk import AsyncClient
from xai_sdk.chat import system, user
from src.ontology.schema import ExtractionResult
from src.utils.logging_config import log_graceful_failure

logger = logging.getLogger(__name__)

class JsonExtractor:
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-fast-reasoning")
        self.max_output_tokens = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "524288"))
        
        if not self.api_key:
            # Fallback for development/testing if env var not set, though it should be
            logger.warning("LLM_BINDING_API_KEY not found, checking XAI_API_KEY")
            self.api_key = os.getenv("XAI_API_KEY")
            
        if not self.api_key:
             raise ValueError("LLM_BINDING_API_KEY or XAI_API_KEY not found in environment variables")

        # Initialize native xAI SDK client (gRPC-based, more reliable than OpenAI HTTP wrapper)
        # The xAI SDK uses XAI_API_KEY env var by default, but we pass explicitly for clarity
        self.client = AsyncClient(api_key=self.api_key)
        
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

    async def extract(self, text: str) -> ExtractionResult:
        """
        Extracts entities from the given text using Grok 4 in JSON mode.
        Returns empty result on malformed JSON to allow graceful continuation.
        """
        try:
            # Log chunk size for debugging
            import tiktoken
            tokenizer = tiktoken.get_encoding("cl100k_base")
            token_count = len(tokenizer.encode(text))
            logger.info(f"Sending extraction request to {self.model} via xAI SDK (Length: {len(text)} chars, ~{token_count} tokens)")
            
            # Use native xAI SDK (gRPC-based) instead of OpenAI HTTP wrapper
            # This should be more reliable for large JSON responses
            chat = self.client.chat.create(
                model=self.model,
                messages=[system(self.system_prompt)]
            )
            chat.append(user(text))
            
            # Sample the response (non-streaming, complete response)
            response = await chat.sample()
            content = response.content
            
            if not content:
                raise ValueError("Empty response from LLM")

            # Parse JSON with error handling for malformed responses
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response preview (first 500 chars): {content[:500]}")
                
                # Try to extract JSON from markdown code blocks if present
                if "```json" in content:
                    logger.info("Attempting to extract JSON from markdown code block...")
                    import re
                    json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                    if json_match:
                        content = json_match.group(1)
                        data = json.loads(content)
                    else:
                        logger.warning(f"⚠️ Malformed JSON - skipping chunk and continuing")
                        return ExtractionResult(entities=[], relationships=[])
                else:
                    logger.warning(f"⚠️ Malformed JSON - skipping chunk and continuing")
                    return ExtractionResult(entities=[], relationships=[])
            
            # Pre-validate and clean relationships before Pydantic validation
            # Handle both old format (strings) and new format (entity objects)
            if "relationships" in data:
                cleaned_relationships = []
                for i, rel in enumerate(data["relationships"]):
                    # Handle both string and dict formats for backwards compatibility
                    source = rel.get("source_entity") if isinstance(rel, dict) else None
                    target = rel.get("target_entity") if isinstance(rel, dict) else None
                    
                    # Skip if not a dict at all
                    if not isinstance(rel, dict):
                        logger.warning(f"⚠️ Relationship #{i} is not a dict, skipping: {rel}")
                        continue
                    
                    # Convert string format to dict format if needed
                    if isinstance(source, str):
                        source = {"entity_name": source, "entity_type": "unknown"}
                        rel["source_entity"] = source
                    if isinstance(target, str):
                        target = {"entity_name": target, "entity_type": "unknown"}
                        rel["target_entity"] = target
                    
                    # Validate we have entity objects now
                    if not isinstance(source, dict) or not source.get("entity_name"):
                        logger.warning(f"⚠️ Relationship #{i} missing valid 'source_entity', skipping: {rel}")
                        continue
                    if not isinstance(target, dict) or not target.get("entity_name"):
                        logger.warning(f"⚠️ Relationship #{i} missing valid 'target_entity', skipping: {rel}")
                        continue
                    if not rel.get("relationship_type"):
                        logger.warning(f"⚠️ Relationship #{i} missing 'relationship_type', skipping: {rel}")
                        continue
                    
                    cleaned_relationships.append(rel)
                
                skipped_count = len(data["relationships"]) - len(cleaned_relationships)
                if skipped_count > 0:
                    logger.warning(f"⚠️ Skipped {skipped_count} malformed relationships (total: {len(data['relationships'])})")
                
                data["relationships"] = cleaned_relationships
            
            # Validate against Pydantic Schema
            # This ensures the output strictly adheres to our ontology
            result = ExtractionResult(**data)
            
            # CRITICAL: Rescue entities with partial data instead of dropping them
            # We want to capture ALL potential intelligence, even if imperfect.
            # source_text is the ONLY content field - no description field exists anymore
            valid_entities = []
            for e in result.entities:
                # Case 1: Missing source_text (REQUIRED field) -> Try to rescue from entity_name
                if not e.source_text or not e.source_text.strip():
                    if e.entity_name and e.entity_name.strip():
                        # Use entity name as source_text (last resort)
                        e.source_text = e.entity_name
                        logger.info(f"🔧 Rescued entity using entity_name as source_text: '{e.entity_name}'")
                    else:
                        # Truly empty -> Garbage
                        logger.warning(f"⚠️ Dropping empty entity (no source_text or name): {e}")
                        continue

                # Case 2: Missing Name -> Generate from source_text
                if not e.entity_name or not e.entity_name.strip():
                    snippet = e.source_text[:50].strip() + "..." if len(e.source_text) > 50 else e.source_text
                    e.entity_name = f"[{e.entity_type.upper()}] {snippet}"
                    logger.info(f"🔧 Rescued entity with missing name from source_text: '{e.entity_name}'")

                valid_entities.append(e)
            
            result.entities = valid_entities
            
            logger.info(f"Successfully extracted {len(result.entities)} entities")
            return result
            
        except Exception as e:
            logger.error(f"❌ Unexpected error during extraction: {e}")
            logger.error(f"Returning empty result to allow processing to continue")
            return ExtractionResult(entities=[], relationships=[])

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw content: {content}")
            raise
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            raise
    
    async def extract_from_text(self, text: str, chunk_id: str) -> ExtractionResult:
        """
        Extract entities from arbitrary text using govcon ontology.
        
        Used by modal processors (tables, images) to analyze converted descriptions.
        This method applies the SAME ontology extraction as text processing,
        ensuring consistent entity types and relationships.
        
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
            # Use native xAI SDK (gRPC-based) for table/image extraction
            chat = self.client.chat.create(
                model=self.model,
                messages=[system(self.system_prompt)]
            )
            chat.append(user(user_prompt))
            
            response = await chat.sample()
            content = response.content
            
            # Parse JSON (with markdown extraction if needed)
            if "```json" in content:
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                if json_match:
                    content = json_match.group(1)
            
            data = json.loads(content)
            
            # Clean relationships (same as extract_entities_and_relationships)
            if "relationships" in data:
                cleaned_relationships = []
                for i, rel in enumerate(data["relationships"]):
                    source = rel.get("source_entity") if isinstance(rel, dict) else None
                    target = rel.get("target_entity") if isinstance(rel, dict) else None
                    
                    if not isinstance(rel, dict):
                        continue
                    
                    # Convert string format to dict format if needed
                    if isinstance(source, str):
                        source = {"entity_name": source, "entity_type": "unknown"}
                        rel["source_entity"] = source
                    if isinstance(target, str):
                        target = {"entity_name": target, "entity_type": "unknown"}
                        rel["target_entity"] = target
                    
                    # Validate
                    if not isinstance(source, dict) or not source.get("entity_name"):
                        continue
                    if not isinstance(target, dict) or not target.get("entity_name"):
                        continue
                    if not rel.get("relationship_type"):
                        continue
                    
                    cleaned_relationships.append(rel)
                
                data["relationships"] = cleaned_relationships
            
            # Validate against Pydantic schema
            result = ExtractionResult(**data)
            
            logger.info(
                f"📝 Extracted from text ({chunk_id}): "
                f"{len(result.entities)} entities, {len(result.relationships)} relationships"
            )
            
            return result
            
        except Exception as e:
            log_graceful_failure(logger, "Entity extraction", e, chunk_id)
            return ExtractionResult(entities=[], relationships=[])
