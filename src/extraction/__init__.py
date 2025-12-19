"""
Extraction module for entity extraction utilities.

Provides:
- JsonExtractor: Pydantic-validated extraction using Instructor + xAI Grok (experimental)
- LightRAGExtractionAdapter: Wraps LLM calls for Pydantic validation (experimental)
- create_sanitizing_wrapper: Lightweight output sanitization for native LightRAG

Issue #56: Post-Processing Overhaul
- Pydantic adapter was tested but caused entity count degradation
- Output sanitizer is the preferred approach for fixing malformed output
"""

from src.extraction.json_extractor import JsonExtractor
from src.extraction.lightrag_llm_adapter import (
    LightRAGExtractionAdapter,
    create_extraction_adapter,
)
from src.extraction.output_sanitizer import (
    create_sanitizing_wrapper,
    sanitize_extraction_output,
    get_sanitizer_stats,
)

__all__ = [
    "JsonExtractor",
    "LightRAGExtractionAdapter",
    "create_extraction_adapter",
    "create_sanitizing_wrapper",
    "sanitize_extraction_output",
    "get_sanitizer_stats",
]
