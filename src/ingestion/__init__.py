"""
Document Ingestion Module

This module handles UCF (Uniform Contract Format) detection and section-aware processing:
- detector.py: Detects if document follows FAR 15.204-1 UCF structure
- processor.py: Prepares sections with enhanced context for LLM extraction

Usage:
    from src.ingestion.detector import detect_ucf_format, UCFDetectionResult
    from src.ingestion.processor import prepare_ucf_sections_for_llm, UCFSection
"""

from src.ingestion.detector import (
    detect_ucf_format,
    extract_section_boundaries,
    get_section_text,
    UCFDetectionResult,
    UCF_SECTION_PATTERNS,
    CRITICAL_UCF_SECTIONS,
    SUPPORTING_UCF_SECTIONS,
)

from src.ingestion.processor import (
    prepare_ucf_sections_for_llm,
    get_section_aware_extraction_prompt,
    UCFSection,
    SECTION_SEMANTIC_MAPPING,
)

__all__ = [
    # Detector exports
    "detect_ucf_format",
    "extract_section_boundaries",
    "get_section_text",
    "UCFDetectionResult",
    "UCF_SECTION_PATTERNS",
    "CRITICAL_UCF_SECTIONS",
    "SUPPORTING_UCF_SECTIONS",
    # Processor exports
    "prepare_ucf_sections_for_llm",
    "get_section_aware_extraction_prompt",
    "UCFSection",
    "SECTION_SEMANTIC_MAPPING",
]
