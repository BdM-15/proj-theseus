# Implementation Plan: Pydantic Validation for Text Extraction (Option 4)

**Issue**: #43 (proposed)
**Branch**: `043-pydantic-text-extraction-adapter`
**Priority**: HIGH - Fixes entity type validation gap in text extraction pipeline

## Problem Statement

Currently, LightRAG's text extraction uses **pipe-delimited parsing** which:

1. Has no schema validation (entities can have invalid types)
2. Produces format errors when LLM includes extra `|` characters in descriptions
3. Does NOT use our 18 govcon entity types enforced by Pydantic

**Evidence from processing.log**:

```
WARNING: Entity extraction error: invalid entity type in: ['entity', 'Navy CESE', '#|equipment', ...]
WARNING: chunk-xxx: LLM output format error; found 5/4 fields on ENTITY `MCMC` @ `Navy CESE`
```

Our **multimodal pipeline** (tables/images) already uses Pydantic via `JsonExtractor` + `ExtractionResult` schema and works reliably. We need the same validation for text.

## Architecture: JSON Adapter Pattern

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LightRAG Native                              │
│  extract_entities() → llm_model_func() → pipe-delimited parsing     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────────┐
                    │   ADAPTER LAYER (NEW)       │
                    │                             │
                    │  1. Intercept extraction    │
                    │  2. Request JSON output     │
                    │  3. Validate w/ Pydantic    │
                    │  4. Convert → pipe-delim    │
                    │  5. Return to LightRAG      │
                    └────────────┬────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                    xAI Grok-4-fast-reasoning                         │
│        (JSON structured output via Instructor library)               │
└─────────────────────────────────────────────────────────────────────┘
```

## Why This Is NOT a Regression

The pipe-delimiter is **only used internally** as a transport format between our adapter and LightRAG's parser. The actual extraction uses:

- ✅ JSON structured output from xAI Grok
- ✅ Pydantic validation via `ExtractionResult` schema
- ✅ Our 18 govcon entity types
- ✅ Full relationship validation (no ghost nodes)

LightRAG's parser just receives clean, pre-validated data in the format it expects.

## Implementation Tasks

### Task 1: Create Extraction LLM Wrapper (`src/extraction/lightrag_llm_adapter.py`)

````python
"""
LightRAG LLM Adapter - Bridges Pydantic validation with LightRAG's text extraction.

This adapter intercepts entity extraction LLM calls and:
1. Requests JSON structured output (using existing JsonExtractor)
2. Validates with Pydantic (ExtractionResult schema)
3. Converts to pipe-delimited format for LightRAG's parser
4. Returns clean, validated data that LightRAG accepts

The pipe-delimiter is just a transport format - all actual validation happens via Pydantic.
"""
import logging
from typing import Optional, Union, AsyncIterator
from functools import partial

from src.extraction.json_extractor import JsonExtractor
from src.ontology.schema import ExtractionResult, VALID_ENTITY_TYPES

logger = logging.getLogger(__name__)

# LightRAG's expected delimiters (from lightrag/prompt.py)
TUPLE_DELIMITER = "<|#|>"
COMPLETION_DELIMITER = "<|COMPLETE|>"


class LightRAGExtractionAdapter:
    """
    Adapter that wraps LLM calls for entity extraction.

    When LightRAG calls the llm_model_func for entity extraction, this adapter:
    1. Detects extraction requests (vs queries, summaries, etc.)
    2. Uses JsonExtractor with Pydantic validation
    3. Converts validated JSON → pipe-delimited format
    4. Returns to LightRAG's native parser
    """

    def __init__(self, base_llm_func, json_extractor: Optional[JsonExtractor] = None):
        """
        Args:
            base_llm_func: The original LLM function for non-extraction calls
            json_extractor: Optional JsonExtractor instance (creates one if not provided)
        """
        self.base_llm_func = base_llm_func
        self.json_extractor = json_extractor or JsonExtractor()
        self._extraction_count = 0
        self._passthrough_count = 0

    async def __call__(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: list = None,
        keyword_extraction: bool = False,
        **kwargs
    ) -> Union[str, AsyncIterator[str]]:
        """
        Main entry point - intercepts LLM calls and routes appropriately.

        Entity extraction calls are detected by checking for extraction-specific
        markers in the system prompt.
        """
        history_messages = history_messages or []

        # Detect if this is an entity extraction call
        if self._is_extraction_call(system_prompt, prompt):
            return await self._handle_extraction(prompt, system_prompt, **kwargs)

        # Pass through to base LLM for all other calls (queries, summaries, etc.)
        self._passthrough_count += 1
        return await self.base_llm_func(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            keyword_extraction=keyword_extraction,
            **kwargs
        )

    def _is_extraction_call(self, system_prompt: Optional[str], user_prompt: str) -> bool:
        """
        Detect entity extraction calls by checking for LightRAG's extraction markers.

        LightRAG's entity_extraction_system_prompt contains specific markers
        that we can use to identify extraction calls.
        """
        if not system_prompt:
            return False

        # Markers from LightRAG's entity_extraction_system_prompt
        extraction_markers = [
            "Knowledge Graph Specialist",
            "extracting entities and relationships",
            "entity_types",
            TUPLE_DELIMITER,  # <|#|>
        ]

        return any(marker in system_prompt for marker in extraction_markers)

    async def _handle_extraction(
        self,
        prompt: str,
        system_prompt: str,
        **kwargs
    ) -> str:
        """
        Handle entity extraction with Pydantic validation.

        Returns:
            Pipe-delimited string that LightRAG's parser expects
        """
        self._extraction_count += 1
        chunk_id = f"text-chunk-{self._extraction_count}"

        try:
            # Extract text content from the prompt (after "Text:" marker)
            text_content = self._extract_text_content(prompt)

            if not text_content:
                logger.warning(f"[{chunk_id}] Could not extract text content from prompt")
                return COMPLETION_DELIMITER

            # Use JsonExtractor for Pydantic-validated extraction
            result: ExtractionResult = await self.json_extractor.extract(
                text_content,
                chunk_id=chunk_id
            )

            # Convert validated result to pipe-delimited format
            pipe_output = self._convert_to_pipe_format(result, chunk_id)

            logger.info(
                f"✅ [{chunk_id}] Pydantic extraction: "
                f"{len(result.entities)} entities, {len(result.relationships)} relationships"
            )

            return pipe_output

        except Exception as e:
            logger.error(f"❌ [{chunk_id}] Pydantic extraction failed: {e}")
            # Return empty completion - LightRAG will handle gracefully
            return COMPLETION_DELIMITER

    def _extract_text_content(self, prompt: str) -> Optional[str]:
        """
        Extract the actual text content from LightRAG's user prompt.

        LightRAG wraps text in a specific format:
        ```
        Text:
        <actual content here>
        ```
        """
        # Try to find text after "Text:" marker
        markers = ["Text:\n```", "Text:\n", "```\n"]

        for marker in markers:
            if marker in prompt:
                parts = prompt.split(marker, 1)
                if len(parts) > 1:
                    content = parts[1]
                    # Remove trailing ``` if present
                    if "```" in content:
                        content = content.split("```")[0]
                    return content.strip()

        # Fallback: return entire prompt if no markers found
        return prompt.strip()

    def _convert_to_pipe_format(self, result: ExtractionResult, chunk_id: str) -> str:
        """
        Convert Pydantic ExtractionResult to LightRAG's pipe-delimited format.

        Entity format: entity<|#|>name<|#|>type<|#|>description
        Relation format: relation<|#|>source<|#|>target<|#|>keywords<|#|>description<|#|>weight
        """
        lines = []

        # Convert entities
        for entity in result.entities:
            # Get description, handling different entity types
            description = getattr(entity, 'description', '') or ''

            # For specialized entities, build richer description
            if hasattr(entity, 'criticality'):  # Requirement
                description = f"{description} [Criticality: {entity.criticality}]"
            elif hasattr(entity, 'weight'):  # EvaluationFactor
                weight_info = entity.weight or entity.importance or ''
                if weight_info:
                    description = f"{description} [Weight: {weight_info}]"
            elif hasattr(entity, 'clause_number'):  # Clause
                description = f"{description} [{entity.clause_number}]"

            # Escape any pipe characters in the description
            description = description.replace("|", " ")

            line = f"entity{TUPLE_DELIMITER}{entity.entity_name}{TUPLE_DELIMITER}{entity.entity_type}{TUPLE_DELIMITER}{description}"
            lines.append(line)

        # Convert relationships
        for rel in result.relationships:
            # Handle both old string format and new entity object format
            source = rel.source_entity.entity_name if hasattr(rel, 'source_entity') else rel.source_id
            target = rel.target_entity.entity_name if hasattr(rel, 'target_entity') else rel.target_id

            # Escape pipes
            rel_type = rel.relationship_type.replace("|", " ")
            reasoning = (rel.reasoning or '').replace("|", " ")

            # LightRAG expects: relation<|#|>source<|#|>target<|#|>keywords<|#|>description<|#|>weight
            line = f"relation{TUPLE_DELIMITER}{source}{TUPLE_DELIMITER}{target}{TUPLE_DELIMITER}{rel_type}{TUPLE_DELIMITER}{reasoning}{TUPLE_DELIMITER}{rel.confidence}"
            lines.append(line)

        # Add completion delimiter
        lines.append(COMPLETION_DELIMITER)

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """Get adapter statistics."""
        return {
            "extraction_calls": self._extraction_count,
            "passthrough_calls": self._passthrough_count,
            "json_extractor_stats": self.json_extractor.get_extraction_stats()
        }
````

### Task 2: Wire Adapter into LightRAG Configuration (`src/server/config.py`)

Add wrapper initialization after creating the base LLM function:

```python
# After creating llm_model_func, wrap it with the Pydantic adapter
from src.extraction.lightrag_llm_adapter import LightRAGExtractionAdapter

# Create base LLM function
base_llm_func = create_llm_model_func()

# Wrap with Pydantic validation adapter
extraction_adapter = LightRAGExtractionAdapter(base_llm_func)

# Use adapter as the llm_model_func
global_args.llm_model_func = extraction_adapter
```

### Task 3: Update JsonExtractor for Text-Only Mode

The current `JsonExtractor` loads multimodal-specific prompts. Add a text-only mode:

```python
class JsonExtractor:
    def __init__(self, mode: str = "full"):
        """
        Args:
            mode: "full" for multimodal (default), "text" for text-only extraction
        """
        self.mode = mode
        self.system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        if self.mode == "text":
            return self._load_text_extraction_prompt()
        return self._load_full_system_prompt()  # existing multimodal prompt
```

### Task 4: Test Suite

Create `tests/test_lightrag_llm_adapter.py`:

```python
"""Tests for LightRAG LLM Adapter with Pydantic validation."""
import pytest
import asyncio
from src.extraction.lightrag_llm_adapter import LightRAGExtractionAdapter

@pytest.mark.asyncio
async def test_extraction_detection():
    """Verify adapter correctly identifies extraction calls."""
    # ... test implementation

@pytest.mark.asyncio
async def test_pipe_conversion():
    """Verify JSON → pipe-delimited conversion."""
    # ... test implementation

@pytest.mark.asyncio
async def test_entity_type_validation():
    """Verify invalid entity types are coerced to 'concept'."""
    # ... test implementation
```

## File Changes Summary

| File                                     | Action | Purpose                    |
| ---------------------------------------- | ------ | -------------------------- |
| `src/extraction/lightrag_llm_adapter.py` | CREATE | New adapter module         |
| `src/extraction/json_extractor.py`       | MODIFY | Add text-only mode         |
| `src/server/config.py`                   | MODIFY | Wire adapter into LightRAG |
| `tests/test_lightrag_llm_adapter.py`     | CREATE | Test suite                 |

## Validation Criteria

1. **Entity Type Enforcement**: All extracted entities have valid types from `VALID_ENTITY_TYPES`
2. **No Format Errors**: No more "found 5/4 fields" warnings in logs
3. **Relationship Validation**: No ghost nodes (Pydantic's `validate_relationships` enforced)
4. **Backward Compatibility**: Query, summary, and other LLM calls unaffected
5. **Performance**: <5% overhead vs native LightRAG extraction

## Risk Mitigation

| Risk                                      | Mitigation                                      |
| ----------------------------------------- | ----------------------------------------------- |
| Detection false positives                 | Conservative marker matching; extensive testing |
| JSON extraction failures                  | Graceful fallback returns empty completion      |
| Prompt format changes in LightRAG updates | Version pin; marker-based detection is flexible |
| Performance overhead                      | Async throughout; same LLM call count           |

## Implementation Order

1. Create `lightrag_llm_adapter.py` with full implementation
2. Add text-only mode to `JsonExtractor`
3. Wire into `config.py`
4. Create test suite
5. Integration test with MCPP RFP document
6. Compare extraction quality before/after

## Expected Outcomes

- **Before**: `76 Ent + 30 Rel` with format warnings, potentially invalid types
- **After**: `76 Ent + 30 Rel` with zero warnings, all types validated against govcon ontology

This gives us Pydantic validation for ALL extraction (text + multimodal) while keeping LightRAG's internal architecture intact.
