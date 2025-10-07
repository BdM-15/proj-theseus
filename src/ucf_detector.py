"""
UCF (Uniform Contract Format) Detector

Detects if a document follows standard Uniform Contract Format (FAR 15.204-1)
to enable deterministic parsing for higher precision.

UCF Structure (FAR 15.204):
- Section A: Solicitation/Contract Form
- Section B: Supplies or Services and Prices/Costs  
- Section C: Description/Specs/Work Statement
- Section D: Packaging and Marking
- Section E: Inspection and Acceptance
- Section F: Deliveries or Performance
- Section G: Contract Administration Data
- Section H: Special Contract Requirements
- Section I: Contract Clauses
- Section J: List of Attachments
- Section K: Representations, Certifications, and Other Statements
- Section L: Instructions, Conditions, and Notices to Offerors
- Section M: Evaluation Factors for Award

Reference: docs/archive/BRANCH_003_IMPLEMENTATION.md, phase6_prompts.py
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class UCFDetectionResult:
    """Result of UCF format detection"""
    is_ucf: bool
    confidence: float  # 0.0-1.0
    detected_sections: List[str]  # e.g., ["Section A", "Section B", "Section L", "Section M"]
    missing_critical_sections: List[str]  # Critical sections not found
    section_pattern_type: str  # "standard_ucf", "task_order", "non_standard"
    reasons: List[str]  # Human-readable detection rationale


# UCF Section Patterns (FAR 15.204-1)
UCF_SECTION_PATTERNS = {
    "Section A": [
        r"Section\s+A[:\s]",
        r"SF\s*1449",  # Standard Form 1449
        r"Solicitation[,/]?\s*Offer[,]?\s*and\s*Award",
        r"SF\s*33",  # Solicitation, Offer and Award
    ],
    "Section B": [
        r"Section\s+B[:\s]",
        r"Supplies\s+(?:or|and)\s+Services",
        r"CLIN\s+\d{4}",  # Contract Line Item Number
        r"Prices?[/]Costs?",
    ],
    "Section C": [
        r"Section\s+C[:\s]",
        r"Description[/]Specs?[/]Work\s+Statement",
        r"Statement\s+of\s+Work",
        r"Performance\s+Work\s+Statement",
        r"SOW|PWS",
    ],
    "Section H": [
        r"Section\s+H[:\s]",
        r"Special\s+Contract\s+Requirements",
        r"H-\d+",  # H-clause numbering
    ],
    "Section I": [
        r"Section\s+I[:\s]",
        r"Contract\s+Clauses",
        r"FAR\s+52\.\d{3}-\d+",  # FAR clause pattern
        r"DFARS\s+252\.\d{3}-\d+",  # DFARS clause pattern
    ],
    "Section J": [
        r"Section\s+J[:\s]",
        r"List\s+of\s+Attachments",
        r"J-\d{7}",  # J-attachment numbering
        r"Annex(?:es)?",
    ],
    "Section L": [
        r"Section\s+L[:\s]",
        r"Instructions[,]?\s+Conditions[,]?\s+and\s+Notices\s+to\s+Offerors",
        r"Instructions\s+to\s+Offerors",
        r"Proposal\s+(?:Preparation|Submission)\s+Instructions",
        r"L\.\d+",  # L.1, L.2 subsection numbering
    ],
    "Section M": [
        r"Section\s+M[:\s]",
        r"Evaluation\s+Factors?\s+for\s+Award",
        r"Source\s+Selection\s+(?:Criteria|Plan)",
        r"M\.\d+",  # M.1, M.2 subsection numbering
        r"Factor\s+\d+",  # Factor 1, Factor 2
    ],
}


# Critical sections for UCF detection
# If document has L + M + (H or I or J), likely UCF
CRITICAL_UCF_SECTIONS = ["Section L", "Section M"]
SUPPORTING_UCF_SECTIONS = ["Section H", "Section I", "Section J", "Section B"]


# Task Order / Non-Standard Patterns
TASK_ORDER_PATTERNS = {
    "Proposal Instructions": [
        r"Proposal\s+Instructions",
        r"Submission\s+(?:Instructions|Requirements)",
        r"Quote\s+Instructions",
    ],
    "Selection Criteria": [
        r"Selection\s+Criteria",
        r"Evaluation\s+(?:Criteria|Methodology)",
        r"Award\s+Criteria",
    ],
    "Technical Requirements": [
        r"Technical\s+Requirements",
        r"Statement\s+of\s+Objectives",
        r"SOO",
    ],
}


def detect_ucf_format(document_text: str, file_name: str = "") -> UCFDetectionResult:
    """
    Detect if document follows Uniform Contract Format (FAR 15.204-1).
    
    Args:
        document_text: Full document text
        file_name: Optional filename for additional heuristics
        
    Returns:
        UCFDetectionResult with confidence score and detected sections
        
    Detection Logic:
        - HIGH confidence (0.9+): L + M + 2+ supporting sections (H/I/J/B)
        - MEDIUM confidence (0.7-0.9): L + M present, 1 supporting section
        - LOW confidence (0.5-0.7): Either L or M present + supporting sections
        - NOT UCF (<0.5): Neither L nor M, or task order patterns detected
    """
    detected_sections = []
    detection_reasons = []
    
    # Check for standard UCF sections
    for section_name, patterns in UCF_SECTION_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, document_text, re.IGNORECASE | re.MULTILINE):
                detected_sections.append(section_name)
                detection_reasons.append(f"Found {section_name} pattern: {pattern}")
                break  # Move to next section after first match
    
    # Remove duplicates
    detected_sections = list(set(detected_sections))
    
    # Check critical sections
    has_section_l = "Section L" in detected_sections
    has_section_m = "Section M" in detected_sections
    
    # Count supporting sections
    supporting_count = sum(1 for sec in SUPPORTING_UCF_SECTIONS if sec in detected_sections)
    
    # Check for task order patterns (indicates non-UCF)
    task_order_matches = 0
    for alt_section, patterns in TASK_ORDER_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, document_text, re.IGNORECASE):
                task_order_matches += 1
                detection_reasons.append(f"Found task order pattern: {alt_section}")
                break
    
    # Calculate confidence score
    confidence = 0.0
    pattern_type = "non_standard"
    missing_critical = []
    
    if has_section_l and has_section_m:
        # Both critical sections present
        if supporting_count >= 2:
            confidence = 0.95  # HIGH: Strong UCF signal
            pattern_type = "standard_ucf"
            detection_reasons.append("HIGH confidence: L + M + multiple supporting sections")
        elif supporting_count == 1:
            confidence = 0.85  # MEDIUM-HIGH: Likely UCF
            pattern_type = "standard_ucf"
            detection_reasons.append("MEDIUM-HIGH confidence: L + M + one supporting section")
        else:
            confidence = 0.70  # MEDIUM: Possible UCF
            pattern_type = "standard_ucf"
            detection_reasons.append("MEDIUM confidence: L + M present, few supporting sections")
    elif has_section_l or has_section_m:
        # One critical section present
        if supporting_count >= 2:
            confidence = 0.65  # MEDIUM-LOW: Partial UCF
            pattern_type = "standard_ucf"
            missing_critical.append("Section M" if has_section_l else "Section L")
            detection_reasons.append(f"MEDIUM-LOW: Missing {missing_critical[0]} but has supporting sections")
        else:
            confidence = 0.50  # LOW: Weak UCF signal
            pattern_type = "partial_ucf"
            missing_critical.append("Section M" if has_section_l else "Section L")
            detection_reasons.append(f"LOW confidence: Only one critical section present")
    else:
        # No critical sections
        if task_order_matches >= 2:
            confidence = 0.20  # Task order format
            pattern_type = "task_order"
            missing_critical = ["Section L", "Section M"]
            detection_reasons.append("Task order format detected (non-UCF)")
        else:
            confidence = 0.10  # Non-standard
            pattern_type = "non_standard"
            missing_critical = ["Section L", "Section M"]
            detection_reasons.append("No UCF critical sections found")
    
    # Filename heuristics (bonus)
    if file_name:
        if re.search(r"(?i)(rfp|solicitation|n\d{13})", file_name):
            confidence = min(1.0, confidence + 0.05)
            detection_reasons.append("Filename suggests RFP/solicitation")
    
    # Determine if UCF (threshold: 0.70+)
    is_ucf = confidence >= 0.70
    
    logger.info(f"UCF Detection: is_ucf={is_ucf}, confidence={confidence:.2f}, sections={detected_sections}")
    
    return UCFDetectionResult(
        is_ucf=is_ucf,
        confidence=confidence,
        detected_sections=sorted(detected_sections),
        missing_critical_sections=missing_critical,
        section_pattern_type=pattern_type,
        reasons=detection_reasons
    )


def extract_section_boundaries(document_text: str, detected_sections: List[str]) -> Dict[str, Tuple[int, int]]:
    """
    Extract character offsets for each detected section.
    
    Args:
        document_text: Full document text
        detected_sections: List of section names from UCF detection
        
    Returns:
        Dict mapping section name to (start_offset, end_offset)
        
    Example:
        {
            "Section L": (45000, 52000),
            "Section M": (52000, 60000)
        }
    """
    section_boundaries = {}
    
    for section in detected_sections:
        patterns = UCF_SECTION_PATTERNS.get(section, [])
        
        for pattern in patterns:
            match = re.search(pattern, document_text, re.IGNORECASE | re.MULTILINE)
            if match:
                start_offset = match.start()
                
                # Find next section or end of document
                remaining_text = document_text[start_offset:]
                next_section_match = re.search(
                    r"(?i)section\s+[a-m][\s:]",  # Next section pattern
                    remaining_text[100:]  # Skip 100 chars to avoid matching current section
                )
                
                if next_section_match:
                    end_offset = start_offset + 100 + next_section_match.start()
                else:
                    end_offset = len(document_text)
                
                section_boundaries[section] = (start_offset, end_offset)
                break
    
    return section_boundaries


def get_section_text(document_text: str, section_name: str) -> str:
    """
    Extract text for a specific section.
    
    Args:
        document_text: Full document text
        section_name: Section to extract (e.g., "Section L")
        
    Returns:
        Section text or empty string if not found
    """
    boundaries = extract_section_boundaries(document_text, [section_name])
    
    if section_name in boundaries:
        start, end = boundaries[section_name]
        return document_text[start:end]
    
    return ""
