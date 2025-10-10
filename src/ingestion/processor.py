"""
UCF Section-Aware Processor

Enhances LLM extraction for Uniform Contract Format (UCF) documents by:
1. Using regex to detect section boundaries (Section L, M, C, etc.)
2. Injecting section-aware context into LLM extraction prompts
3. Letting LLM extract ALL entities (not regex) with better accuracy

Architecture:
    UCF Path:
    - Regex finds: "Section M starts at char 8000, ends at char 12000"
    - LLM extracts from Section M WITH CONTEXT: "This is Section M (Evaluation Factors), 
      expect EVALUATION_FACTOR entities with relative_importance, subfactors, etc."
    - Same 18 entity types as Generic RAG, just better relationship accuracy
    
    Generic RAG Path:
    - No section detection
    - LLM extracts from full document without section context
    - Same entity types, same metadata extraction

Reference: docs/CAPTURE_INTELLIGENCE_PATTERNS.md
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


# Section semantic type mapping
# Maps UCF section names to semantic types and expected entities
SECTION_SEMANTIC_MAPPING = {
    "Section A": {
        "semantic_type": "SOLICITATION_FORM",
        "expected_entities": ["REQUIREMENT (admin)", "DEADLINE", "ELIGIBILITY_CRITERIA"],
        "extraction_focus": "Proposal deadlines, submission methods, eligibility requirements"
    },
    "Section B": {
        "semantic_type": "SUPPLIES_SERVICES",
        "expected_entities": ["DELIVERABLE", "CLIN", "PERIOD_OF_PERFORMANCE"],
        "extraction_focus": "Contract line items, quantities, pricing structure"
    },
    "Section C": {
        "semantic_type": "STATEMENT_OF_WORK",
        "expected_entities": ["REQUIREMENT", "STATEMENT_OF_WORK", "DELIVERABLE", "TASK"],
        "extraction_focus": """Performance requirements (8 types: FUNCTIONAL, PERFORMANCE, SECURITY, etc.), tasks, deliverables.
NOTE: STATEMENT_OF_WORK entity type semantically includes:
  - SOW (Statement of Work): Prescriptive, detailed HOW instructions
  - PWS (Performance Work Statement): Performance-based WHAT outcomes
  - SOO (Statement of Objectives): High-level OBJECTIVES
Extract as STATEMENT_OF_WORK regardless of which format customer uses."""
    },
    "Section H": {
        "semantic_type": "SPECIAL_REQUIREMENTS",
        "expected_entities": ["REQUIREMENT", "CLAUSE"],
        "extraction_focus": "H-clauses, special contract requirements, agency-specific mandates"
    },
    "Section I": {
        "semantic_type": "CONTRACT_CLAUSES",
        "expected_entities": ["CLAUSE"],
        "extraction_focus": "FAR 52.###-##, DFARS 252.###-####, and 20+ agency supplements"
    },
    "Section J": {
        "semantic_type": "ATTACHMENTS",
        "expected_entities": ["ANNEX", "ATTACHMENT", "STATEMENT_OF_WORK"],
        "extraction_focus": "J-###### annexes, attachments, supplemental documents"
    },
    "Section L": {
        "semantic_type": "SUBMISSION_INSTRUCTIONS",
        "expected_entities": ["SUBMISSION_INSTRUCTION", "REQUIREMENT (admin)"],
        "extraction_focus": "Page limits, format requirements, volume structure, proposal organization"
    },
    "Section M": {
        "semantic_type": "EVALUATION_CRITERIA",
        "expected_entities": ["EVALUATION_FACTOR", "SUBMISSION_INSTRUCTION"],
        "extraction_focus": "Evaluation factors with hierarchy (M1 → M1.1), relative importance, tradeoff methodology"
    },
}


@dataclass
class UCFSection:
    """Section metadata for section-aware LLM extraction
    
    Attributes:
        section_name: Section identifier (e.g., "Section L", "Section M")
        section_text: Raw text content of the section
        char_start: Character offset start position
        char_end: Character offset end position
        semantic_type: Semantic classification (e.g., "SUBMISSION_INSTRUCTIONS")
        expected_entities: Entity types likely found in this section
        extraction_context: Enhanced prompt context for LLM guidance
    """
    section_name: str
    section_text: str
    char_start: int
    char_end: int
    semantic_type: str
    expected_entities: List[str]
    extraction_context: str


def extract_section_boundaries(document_text: str) -> Dict[str, Tuple[int, int]]:
    """
    Use regex to detect section boundaries in UCF documents.
    
    Searches for multiple section header patterns and determines
    boundaries by finding the start of the next section.
    
    Returns:
        Dict mapping section names to (start_char, end_char) tuples
        
    Example:
        {"Section L": (5000, 8000), "Section M": (8001, 12000)}
    """
    # Standard UCF section patterns
    section_patterns = [
        (r"Section\s+([A-M])[:\s]", "standard"),  # "Section L:" or "Section M "
        (r"SECTION\s+([A-M])[:\s]", "uppercase"),  # "SECTION L:"
        (r"([A-M])\.\s+[A-Z]", "abbreviated"),  # "L. Instructions to Offerors"
    ]
    
    section_markers = []
    
    # Find all section markers
    for pattern, pattern_type in section_patterns:
        for match in re.finditer(pattern, document_text, re.IGNORECASE):
            section_letter = match.group(1).upper()
            section_name = f"Section {section_letter}"
            position = match.start()
            
            section_markers.append({
                "name": section_name,
                "position": position,
                "pattern_type": pattern_type
            })
    
    # Sort by position
    section_markers.sort(key=lambda x: x["position"])
    
    # Remove duplicates (keep first occurrence)
    seen_sections = set()
    unique_markers = []
    for marker in section_markers:
        if marker["name"] not in seen_sections:
            unique_markers.append(marker)
            seen_sections.add(marker["name"])
    
    # Create boundaries
    boundaries = {}
    for i, marker in enumerate(unique_markers):
        start = marker["position"]
        # End is either the start of next section or end of document
        end = unique_markers[i + 1]["position"] if i + 1 < len(unique_markers) else len(document_text)
        boundaries[marker["name"]] = (start, end)
    
    logger.info(f"📋 UCF Section Boundaries Detected: {list(boundaries.keys())}")
    return boundaries


def get_section_text(document_text: str, section_name: str, boundaries: Dict[str, Tuple[int, int]]) -> str:
    """Extract text for a specific section using pre-computed boundaries
    
    Args:
        document_text: Full document text
        section_name: Section to extract (e.g., "Section L")
        boundaries: Pre-computed section boundaries from extract_section_boundaries()
        
    Returns:
        Section text or empty string if not found
    """
    if section_name not in boundaries:
        return ""
    
    start, end = boundaries[section_name]
    return document_text[start:end]


def prepare_section_for_llm(section_name: str, section_text: str, char_start: int, char_end: int) -> UCFSection:
    """
    Prepare a section with enhanced context for LLM extraction.
    
    This does NOT extract entities - it just prepares the context.
    The LLM will do all entity extraction using the full 12-type ontology.
    
    Args:
        section_name: Section identifier
        section_text: Raw section content
        char_start: Start character offset
        char_end: End character offset
        
    Returns:
        UCFSection with extraction context for LLM guidance
    """
    section_info = SECTION_SEMANTIC_MAPPING.get(section_name, {
        "semantic_type": "UNKNOWN",
        "expected_entities": ["REQUIREMENT"],
        "extraction_focus": "General requirements and entities"
    })
    
    # Build extraction context for LLM
    extraction_context = f"""
SECTION CONTEXT: {section_name} ({section_info['semantic_type']})

EXPECTED ENTITY TYPES: {', '.join(section_info['expected_entities'])}

EXTRACTION FOCUS: {section_info['extraction_focus']}

IMPORTANT: Extract ALL entities using the full government contracting ontology (18 specialized types) with capture intelligence metadata:
- REQUIREMENT: requirement_type (FUNCTIONAL, PERFORMANCE, SECURITY, TECHNICAL, INTERFACE, MANAGEMENT, DESIGN, QUALITY)
- REQUIREMENT: criticality_level (MANDATORY via "shall/must", IMPORTANT via "should", OPTIONAL via "may")
- EVALUATION_FACTOR: relative_importance ("Most Important", "Significantly More Important than Price")
- EVALUATION_FACTOR: subfactors (M1 → M1.1 → M1.1.1 hierarchy)
- SUBMISSION_INSTRUCTION: page_limits, format_requirements, volume_name
- CLAUSE: FAR/DFARS/AFFARS patterns with agency supplement identification
- ANNEX: J-###### patterns with linkage to parent section
- STATEMENT_OF_WORK: Semantically includes SOW (prescriptive), PWS (performance-based), SOO (objective-based)
  Extract as STATEMENT_OF_WORK regardless of customer terminology

Section boundaries are provided to improve relationship mapping (e.g., Section L instruction → Section M factor).
Use section context to validate entity types and improve accuracy.
""".strip()
    
    return UCFSection(
        section_name=section_name,
        section_text=section_text,
        char_start=char_start,
        char_end=char_end,
        semantic_type=section_info["semantic_type"],
        expected_entities=section_info["expected_entities"],
        extraction_context=extraction_context
    )


def prepare_ucf_sections_for_llm(document_text: str, detected_sections: List[str]) -> List[UCFSection]:
    """
    Main function: Detect section boundaries and prepare sections for LLM extraction.
    
    Workflow:
    1. Use regex to detect section boundaries (ONLY structural detection)
    2. For each detected section, extract text and prepare context
    3. Return list of UCFSection objects with enhanced LLM guidance
    
    Args:
        document_text: Full document text
        detected_sections: List of section names from detector.py
    
    Returns:
        List of UCFSection objects ready for LLM extraction with enhanced context
    """
    # Step 1: Regex detects boundaries (ONLY structural detection, no entity extraction)
    boundaries = extract_section_boundaries(document_text)
    
    # Step 2: Prepare sections with context for LLM
    sections = []
    for section_name in detected_sections:
        if section_name in boundaries:
            start, end = boundaries[section_name]
            section_text = document_text[start:end]
            
            ucf_section = prepare_section_for_llm(section_name, section_text, start, end)
            sections.append(ucf_section)
            
            logger.info(f"✅ Prepared {section_name} ({ucf_section.semantic_type}): {len(section_text)} chars")
    
    if not sections:
        logger.warning("⚠️ No UCF sections prepared - falling back to generic RAG")
    
    return sections


def get_section_aware_extraction_prompt(section: UCFSection, base_prompt: str) -> str:
    """
    Enhance base extraction prompt with section-aware context.
    
    This is used to inject section context into LightRAG's extraction prompts.
    
    Args:
        section: UCFSection with context metadata
        base_prompt: Original LightRAG extraction prompt
        
    Returns:
        Enhanced prompt with section-specific guidance
    """
    enhanced_prompt = f"""
{section.extraction_context}

---

{base_prompt}

---

SECTION TEXT ({section.section_name}):
{section.section_text}
""".strip()
    
    return enhanced_prompt
