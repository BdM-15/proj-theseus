"""
Utility modules for GovCon Capture Vibe

Centralized utilities for LLM interactions, parsing, and data quality.
"""

# Logging utilities
from .logging_config import setup_logging, get_log_summary

# LLM Client utilities (async calls to xAI Grok)
from .llm_client import (
    call_llm_async,
    call_llm_with_schema,
    call_llm_batch,
    get_llm_config
)

# LLM Response parsing utilities
from .llm_parsing import (
    extract_json_from_response,
    extract_json_array_from_response,
    parse_with_pydantic,
    create_fallback_response,
    clean_markdown_code_blocks,
    normalize_llm_list_response,
    deduplicate_list_preserve_order
)

__all__ = [
    # Logging
    "setup_logging",
    "get_log_summary",
    
    # LLM Client
    "call_llm_async",
    "call_llm_with_schema",
    "call_llm_batch",
    "get_llm_config",
    
    # LLM Parsing
    "extract_json_from_response",
    "extract_json_array_from_response",
    "parse_with_pydantic",
    "create_fallback_response",
    "clean_markdown_code_blocks",
    "normalize_llm_list_response",
    "deduplicate_list_preserve_order"
]
