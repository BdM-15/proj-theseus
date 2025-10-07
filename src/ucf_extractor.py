"""
UCF (Uniform Contract Format) Extractor

Deterministic extraction for standard UCF documents using pattern matching.
Higher precision than semantic RAG for well-structured government contracts.

Extracts:
- Section L: Submission instructions, page limits, format requirements
- Section M: Evaluation factors with hierarchy, relative importance
- Section H: Special requirements (H-clauses)
- Section I: Contract clauses (FAR/DFARS patterns)
- Section J: Attachments/Annexes (J-###### patterns)
- CLINs/SLINs: Contract line items

Reference: 
- docs/archive/prompts_branch_002/extract_requirements_prompt.txt
- docs/archive/prompts_branch_002/shipley_requirements_extraction.txt
- src/phase6_prompts.py (SECTION_NORMALIZATION_MAPPING)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class EvaluationFactor:
    """Evaluation factor from Section M"""
    factor_id: str  # "M1", "M2.1", "M2.1.1"
    factor_name: str
    description: str
    relative_importance: Optional[str] = None  # "Most Important", "More Important than Price"
    subfactors: List[str] = field(default_factory=list)
    page_limit: Optional[str] = None  # From Section L
    section_l_reference: Optional[str] = None  # Which L subsection addresses this
    level: int = 1  # Hierarchy depth (1=top, 2=subfactor, 3=sub-subfactor)


@dataclass
class SubmissionInstruction:
    """Submission instruction from Section L"""
    instruction_id: str  # "L.1", "L.3.1"
    instruction_type: str  # "page_limit", "format", "deadline", "volume_structure"
    description: str
    guides_factor: Optional[str] = None  # Which evaluation factor this instructs (e.g., "M2")
    volume_name: Optional[str] = None  # "Technical Volume", "Management Volume"
    page_limit: Optional[str] = None
    format_requirements: Optional[str] = None


@dataclass
class Clause:
    """FAR/DFARS clause from Section I or H"""
    clause_number: str  # "FAR 52.212-4", "DFARS 252.204-7012"
    clause_title: str
    section: str  # "Section I", "Section H"
    agency_supplement: str  # "FAR", "DFARS", "AFFARS", etc.


@dataclass
class Annex:
    """Attachment/Annex from Section J"""
    annex_id: str  # "J-1234567", "Attachment 5"
    annex_title: str
    prefix: str  # "J-", "Attachment "


@dataclass
class UCFExtractionResult:
    """Complete UCF extraction result"""
    evaluation_factors: List[EvaluationFactor]
    submission_instructions: List[SubmissionInstruction]
    clauses: List[Clause]
    annexes: List[Annex]
    section_l_m_mappings: List[Tuple[str, str]]  # (L_subsection, M_factor) pairs


# Pattern: Factor 1 - Technical Approach (Most Important)
# Pattern: M.2 Past Performance (Significantly More Important than Price)
# Pattern: M.2.1 Relevant Contract Experience
FACTOR_PATTERNS = [
    # Top-level factors
    r"(?:Factor|M\.?)\s*(\d+)[\s\-:]+([^\n\(]+?)(?:\s*\(([^\)]+)\))?(?:\n|$)",
    # Subfactors
    r"(?:Subfactor|M\.)(\d+\.\d+)[\s\-:]+([^\n]+)",
    # Sub-subfactors
    r"(?:M\.)(\d+\.\d+\.\d+)[\s\-:]+([^\n]+)",
]


# Pattern: L.3.1 Technical Volume
# Pattern: L.3.1.1 Page Limits (25 pages maximum)
INSTRUCTION_PATTERNS = [
    r"L\.(\d+(?:\.\d+)*)[\s\-:]+([^\n]+?)(?:\s*\(([^\)]+)\))?(?:\n|$)",
    r"(?i)(?:volume|proposal)\s+(?:shall|must|should)\s+(?:not\s+exceed|be\s+limited\s+to)\s+(\d+)\s+pages?",
    r"(?i)(?:page\s+limit|maximum\s+pages?)[\s:]+(\d+)",
]


# FAR/DFARS clause patterns
CLAUSE_PATTERNS = {
    "FAR": r"(?:FAR\s+)?52\.(\d{3})-(\d{1,2})(?:\s+(.+?)(?:\(|$))?",
    "DFARS": r"(?:DFARS\s+)?252\.(\d{3})-(\d{4})(?:\s+(.+?)(?:\(|$))?",
    "AFFARS": r"(?:AFFARS\s+)?5352\.(\d{3})-(\d{4})(?:\s+(.+?)(?:\(|$))?",
    "NMCARS": r"(?:NMCARS\s+)?5252\.(\d{3})-(\d{4})(?:\s+(.+?)(?:\(|$))?",
}


# Annex patterns
ANNEX_PATTERNS = [
    r"(J-\d{7})[\s\-:]+([^\n]+)",
    r"(Attachment\s+\d+)[\s\-:]+([^\n]+)",
    r"(Annex\s+\d+)[\s\-:]+([^\n]+)",
]


def extract_evaluation_factors(section_m_text: str) -> List[EvaluationFactor]:
    """
    Extract evaluation factors from Section M with hierarchy.
    
    Returns factors ordered by hierarchy (Factor 1, Factor 1.1, Factor 1.1.1, Factor 2, ...)
    """
    factors = []
    
    for pattern in FACTOR_PATTERNS:
        matches = re.finditer(pattern, section_m_text, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            factor_id = match.group(1)
            factor_name = match.group(2).strip()
            relative_importance = match.group(3).strip() if match.lastindex >= 3 and match.group(3) else None
            
            # Determine hierarchy level
            level = factor_id.count('.') + 1
            
            # Extract full description (text until next factor or section end)
            factor_start = match.start()
            remaining_text = section_m_text[factor_start:]
            
            # Find next factor
            next_factor_match = re.search(
                r"(?:Factor|M\.?)\s*\d+(?:\.\d+)*[\s\-:]",
                remaining_text[20:]  # Skip current factor
            )
            
            if next_factor_match:
                description = remaining_text[:20 + next_factor_match.start()].strip()
            else:
                description = remaining_text[:500].strip()  # Limit to 500 chars
            
            factors.append(EvaluationFactor(
                factor_id=f"M{factor_id}",
                factor_name=factor_name,
                description=description,
                relative_importance=relative_importance,
                level=level
            ))
    
    # Build subfactor relationships
    for i, factor in enumerate(factors):
        if factor.level > 1:
            # Find parent factor
            parent_id = '.'.join(factor.factor_id.split('.')[:-1])
            for parent in factors:
                if parent.factor_id == parent_id:
                    parent.subfactors.append(factor.factor_id)
                    break
    
    return factors


def extract_submission_instructions(section_l_text: str) -> List[SubmissionInstruction]:
    """
    Extract submission instructions from Section L.
    
    Captures:
    - Volume structure (L.3.1 Technical Volume)
    - Page limits (25 pages maximum)
    - Format requirements (12pt Times, 1-inch margins)
    - Deadlines
    """
    instructions = []
    
    for pattern in INSTRUCTION_PATTERNS:
        matches = re.finditer(pattern, section_l_text, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            if "L." in match.group(0):  # L.X.X pattern
                instruction_id = f"L.{match.group(1)}"
                description = match.group(2).strip()
                detail = match.group(3).strip() if match.lastindex >= 3 and match.group(3) else None
                
                # Determine instruction type
                instruction_type = "general"
                if "page" in description.lower() or (detail and "page" in detail.lower()):
                    instruction_type = "page_limit"
                elif "format" in description.lower() or "font" in description.lower():
                    instruction_type = "format"
                elif "volume" in description.lower():
                    instruction_type = "volume_structure"
                elif "deadline" in description.lower() or "due" in description.lower():
                    instruction_type = "deadline"
                
                # Extract page limit if present
                page_limit = None
                if detail and "page" in detail.lower():
                    page_match = re.search(r"(\d+)\s+pages?", detail, re.IGNORECASE)
                    if page_match:
                        page_limit = f"{page_match.group(1)} pages"
                
                instructions.append(SubmissionInstruction(
                    instruction_id=instruction_id,
                    instruction_type=instruction_type,
                    description=description,
                    page_limit=page_limit,
                    volume_name=description if "volume" in description.lower() else None
                ))
            
            elif "page" in match.group(0).lower():  # Standalone page limit
                page_count = match.group(1)
                instructions.append(SubmissionInstruction(
                    instruction_id="L.page_limit",
                    instruction_type="page_limit",
                    description=f"Page limit: {page_count} pages",
                    page_limit=f"{page_count} pages"
                ))
    
    return instructions


def extract_clauses(section_text: str, section_name: str) -> List[Clause]:
    """
    Extract FAR/DFARS clauses from Section I or H.
    
    Patterns:
    - FAR 52.212-4 Contract Terms and Conditions
    - DFARS 252.204-7012 Safeguarding Covered Defense Information
    """
    clauses = []
    
    for agency, pattern in CLAUSE_PATTERNS.items():
        matches = re.finditer(pattern, section_text, re.MULTILINE)
        
        for match in matches:
            part1 = match.group(1)
            part2 = match.group(2)
            title = match.group(3).strip() if match.lastindex >= 3 and match.group(3) else "Unknown Title"
            
            clause_number = f"{agency} {part1}.{part1}-{part2}" if agency == "FAR" else f"{agency} {part1}.{part1}-{part2}"
            
            clauses.append(Clause(
                clause_number=clause_number,
                clause_title=title,
                section=section_name,
                agency_supplement=agency
            ))
    
    return clauses


def extract_annexes(section_j_text: str) -> List[Annex]:
    """
    Extract attachments/annexes from Section J.
    
    Patterns:
    - J-1234567 Equipment List
    - Attachment 5 - Site Map
    - Annex 12 - Security Requirements
    """
    annexes = []
    
    for pattern in ANNEX_PATTERNS:
        matches = re.finditer(pattern, section_j_text, re.MULTILINE | re.IGNORECASE)
        
        for match in matches:
            annex_id = match.group(1).strip()
            annex_title = match.group(2).strip()
            
            # Extract prefix
            prefix = annex_id.split('-')[0] + '-' if '-' in annex_id else annex_id.rstrip('0123456789') + ' '
            
            annexes.append(Annex(
                annex_id=annex_id,
                annex_title=annex_title,
                prefix=prefix
            ))
    
    return annexes


def map_section_l_to_m(section_l_text: str, section_m_text: str, 
                       factors: List[EvaluationFactor], 
                       instructions: List[SubmissionInstruction]) -> List[Tuple[str, str]]:
    """
    Map Section L submission instructions to Section M evaluation factors.
    
    Patterns:
    - Explicit: "Technical Volume addresses Factor 2"
    - Implicit: "L.3.1 Technical Approach" → "M.2 Technical Approach" (name matching)
    - Proximity: Page limit near factor description
    
    Returns:
        List of (L_subsection, M_factor) pairs, e.g., [("L.3.1", "M2")]
    """
    mappings = []
    
    # Pattern 1: Explicit references
    for instruction in instructions:
        # Search for "Factor X" or "M.X" in instruction description
        factor_ref_match = re.search(r"(?i)(?:factor|M\.)\s*(\d+(?:\.\d+)*)", instruction.description)
        if factor_ref_match:
            factor_id = f"M{factor_ref_match.group(1)}"
            mappings.append((instruction.instruction_id, factor_id))
            continue
        
        # Pattern 2: Name matching (e.g., "Technical Approach" appears in both L and M)
        instruction_words = set(re.findall(r'\b\w+\b', instruction.description.lower()))
        
        for factor in factors:
            factor_words = set(re.findall(r'\b\w+\b', factor.factor_name.lower()))
            
            # Check for significant word overlap (>50% of smaller set)
            overlap = instruction_words & factor_words
            min_words = min(len(instruction_words), len(factor_words))
            
            if min_words > 0 and len(overlap) / min_words > 0.5:
                mappings.append((instruction.instruction_id, factor.factor_id))
                # Also update factor with Section L reference
                factor.section_l_reference = instruction.instruction_id
                if instruction.page_limit:
                    factor.page_limit = instruction.page_limit
                break
    
    return mappings


def extract_ucf_document(document_text: str, detected_sections: List[str]) -> UCFExtractionResult:
    """
    Extract all UCF components from document.
    
    Args:
        document_text: Full document text
        detected_sections: Sections detected by UCF detector
        
    Returns:
        UCFExtractionResult with all extracted entities and relationships
    """
    from ucf_detector import get_section_text
    
    # Extract section texts
    section_l_text = get_section_text(document_text, "Section L") if "Section L" in detected_sections else ""
    section_m_text = get_section_text(document_text, "Section M") if "Section M" in detected_sections else ""
    section_h_text = get_section_text(document_text, "Section H") if "Section H" in detected_sections else ""
    section_i_text = get_section_text(document_text, "Section I") if "Section I" in detected_sections else ""
    section_j_text = get_section_text(document_text, "Section J") if "Section J" in detected_sections else ""
    
    # Extract components
    factors = extract_evaluation_factors(section_m_text) if section_m_text else []
    instructions = extract_submission_instructions(section_l_text) if section_l_text else []
    
    clauses_h = extract_clauses(section_h_text, "Section H") if section_h_text else []
    clauses_i = extract_clauses(section_i_text, "Section I") if section_i_text else []
    clauses = clauses_h + clauses_i
    
    annexes = extract_annexes(section_j_text) if section_j_text else []
    
    # Map L ↔ M relationships
    l_m_mappings = map_section_l_to_m(section_l_text, section_m_text, factors, instructions)
    
    logger.info(f"UCF Extraction complete: {len(factors)} factors, {len(instructions)} instructions, "
                f"{len(clauses)} clauses, {len(annexes)} annexes, {len(l_m_mappings)} L↔M mappings")
    
    return UCFExtractionResult(
        evaluation_factors=factors,
        submission_instructions=instructions,
        clauses=clauses,
        annexes=annexes,
        section_l_m_mappings=l_m_mappings
    )
