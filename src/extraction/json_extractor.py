import os
import json
import logging
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from src.ontology.schema import ExtractionResult

logger = logging.getLogger(__name__)

class JsonExtractor:
    def __init__(self):
        self.api_key = os.getenv("LLM_BINDING_API_KEY")
        self.base_url = os.getenv("LLM_BINDING_HOST", "https://api.x.ai/v1")
        self.model = os.getenv("EXTRACTION_LLM_NAME", "grok-4-fast-reasoning")
        
        if not self.api_key:
            # Fallback for development/testing if env var not set, though it should be
            logger.warning("LLM_BINDING_API_KEY not found, checking xai-api-key")
            self.api_key = os.getenv("xai-api-key")
            
        if not self.api_key:
             raise ValueError("LLM_BINDING_API_KEY not found in environment variables")

        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        
        self.system_prompt = self._load_full_system_prompt()

    def _load_full_system_prompt(self) -> str:
        """
        Constructs the full system prompt by combining:
        1. Base JSON formatting instructions (grok_json_prompt.md)
        2. Entity Detection Rules (entity_detection_rules.md)
        3. Entity Extraction Prompt (entity_extraction_prompt.md)
        4. Relationship inference rules (prompts/relationship_inference/*.md)
        
        Supports compressed prompts via USE_COMPRESSED_PROMPTS env var for 89% token reduction.
        """
        base_path = os.getcwd()
        prompts_dir = os.path.join(base_path, "prompts")
        
        # Check if compressed prompts should be used (default: False for safety)
        use_compressed = os.getenv("USE_COMPRESSED_PROMPTS", "false").lower() == "true"
        suffix = "_COMPRESSED.txt" if use_compressed else ".md"
        logger.info(f"Loading {'COMPRESSED' if use_compressed else 'ORIGINAL'} prompts (89% token reduction enabled={use_compressed})")
        
        # 1. Base JSON Instructions
        json_prompt_filename = "grok_json_prompt_COMPRESSED.txt" if use_compressed else "grok_json_prompt.md"
        json_prompt_path = os.path.join(prompts_dir, "extraction", json_prompt_filename)
        try:
            with open(json_prompt_path, "r", encoding="utf-8") as f:
                json_instructions = f.read()
        except FileNotFoundError:
            logger.error(f"Base prompt not found at {json_prompt_path}")
            raise

        # 2. Entity Detection Rules (The "Rules")
        detection_rules_filename = "entity_detection_rules_COMPRESSED.txt" if use_compressed else "entity_detection_rules.md"
        detection_rules_path = os.path.join(prompts_dir, "extraction", detection_rules_filename)
        detection_rules = ""
        if os.path.exists(detection_rules_path):
            with open(detection_rules_path, "r", encoding="utf-8") as f:
                detection_rules = f.read()
        else:
            logger.warning(f"Detection rules not found at {detection_rules_path}")

        # 3. Entity Extraction Prompt (The "Prompt" with examples)
        extraction_prompt_filename = "entity_extraction_prompt_COMPRESSED.txt" if use_compressed else "entity_extraction_prompt.md"
        extraction_prompt_path = os.path.join(prompts_dir, "extraction", extraction_prompt_filename)
        extraction_prompt = ""
        if os.path.exists(extraction_prompt_path):
            with open(extraction_prompt_path, "r", encoding="utf-8") as f:
                extraction_prompt = f.read()
                # Strip the "Real Data" section if it exists at the end (only in original .md files)
                if not use_compressed and "---Real Data---" in extraction_prompt:
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
            logger.info(f"Sending extraction request to {self.model} (Length: {len(text)} chars, ~{token_count} tokens)")
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=32000 # Maximize output token limit for large extractions
            )
            
            content = response.choices[0].message.content
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
            valid_entities = []
            for e in result.entities:
                # Case 1: Both missing -> Try to rescue from source_text
                if (not e.entity_name or not e.entity_name.strip()) and \
                   (not e.description or not e.description.strip()):
                    
                    if e.source_text and e.source_text.strip():
                        # Rescue using source_text
                        snippet = e.source_text[:50].strip() + "..." if len(e.source_text) > 50 else e.source_text
                        e.entity_name = f"[{e.entity_type.upper()}] {snippet}"
                        e.description = e.source_text
                        logger.info(f"🔧 Rescued entity using source_text: '{e.entity_name}'")
                    else:
                        # Truly empty (no name, desc, or source_text) -> Garbage
                        logger.warning(f"⚠️ Dropping empty entity (no name, desc, or source_text): {e}")
                        continue

                # Case 2: Missing Name -> Rescue using Description
                if not e.entity_name or not e.entity_name.strip():
                    # Create a descriptive name from the description
                    desc_snippet = e.description[:50].strip() + "..." if len(e.description) > 50 else e.description
                    e.entity_name = f"[{e.entity_type.upper()}] {desc_snippet}"
                    logger.info(f"🔧 Rescued entity with missing name: Set to '{e.entity_name}'")

                # Case 3: Missing Description -> Rescue using Name
                if not e.description or not e.description.strip():
                    e.description = e.entity_name
                    logger.info(f"🔧 Rescued entity with missing description: Set to '{e.description}'")

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
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            
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
            logger.error(f"❌ extract_from_text failed ({chunk_id}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return ExtractionResult(entities=[], relationships=[])
