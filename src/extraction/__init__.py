"""
Extraction module for entity extraction utilities.

Provides:
- create_sanitizing_wrapper: Lightweight output sanitization for native LightRAG
- sanitize_extraction_output: Fix common LLM malformation patterns

Issue #56: Output sanitizer fixes malformed LLM output before LightRAG parses it.
"""

from src.extraction.output_sanitizer import (
    create_sanitizing_wrapper,
    sanitize_extraction_output,
    get_sanitizer_stats,
)

__all__ = [
    "create_sanitizing_wrapper",
    "sanitize_extraction_output",
    "get_sanitizer_stats",
]
