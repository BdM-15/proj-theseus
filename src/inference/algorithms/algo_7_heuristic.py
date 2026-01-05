"""
Algorithm 7: Heuristic Pattern Matching

CDRL/DID cross-reference detection using regex patterns.
Also detects section cross-references and requirement-deliverable links.
Numbered hierarchy detection (F.1.5.7 → F.1.5 → F.1).
No LLM calls - instant execution.
"""
import re
import logging
from typing import Dict, List, Set, Tuple, Optional

logger = logging.getLogger(__name__)


def _extract_number_prefix(name: str) -> Optional[str]:
    """
    Extract numbered prefix from entity name.
    
    Examples:
        "F.1.5.7 Maintenance Support" → "F.1.5.7"
        "3.2.1 Task Description" → "3.2.1"
        "Section C.5.2" → "C.5.2"
        "PWS 4.3.1 Requirements" → "4.3.1"
        "H.1.4.6 Preventive Maintenance" → "H.1.4.6"
        "Random Entity Name" → None
    """
    # Pattern 1: Letter.numbers (F.1.5.7, C.3.2, H.1.4.6)
    # Pattern 2: Just numbers (3.2.1, 4.3.1.2)
    match = re.match(r'^(?:Section\s+|PWS\s+)?([A-Z]\.\d+(?:\.\d+)*|\d+(?:\.\d+)+)', name, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    return None


def _get_parent_number(number: str) -> Optional[str]:
    """
    Get parent number by dropping last segment.
    
    Examples:
        "F.1.5.7" → "F.1.5"
        "3.2.1" → "3.2"
        "F.1" → "F" (or None if we don't want single letters)
        "3" → None
    """
    parts = number.split('.')
    if len(parts) <= 1:
        return None
    return '.'.join(parts[:-1])


def algo_7_heuristic(entities: List[Dict], entities_by_type: Dict) -> List[Dict]:
    """
    Algorithm 7: Heuristic Pattern Matching (Cross-references + Hierarchy)
    
    Detects:
    - CDRL, DID, DD Form 1423 references
    - Section cross-references (e.g., "see Section 3.1")
    - PWS paragraph references
    - Attachment/Appendix references
    - **Numbered hierarchy** (F.1.5.7 → F.1.5 → F.1) via CHILD_OF
    
    Non-async (no LLM calls).
    
    Returns:
        List of relationship dicts with REFERENCES and CHILD_OF edges
    """
    logger.info(f"  [Algo 7] Heuristic Pattern Matching")
    
    heuristic_rels = []
    seen_pairs: Set[Tuple[str, str]] = set()
    
    deliverables = entities_by_type.get('deliverable', [])
    sections = entities_by_type.get('section', [])
    documents = entities_by_type.get('document', [])
    requirements = entities_by_type.get('requirement', [])
    
    # Patterns
    patterns = {
        'cdrl': r'cdrl\s*[a-z]?\d{3,4}',
        'did': r'di-[a-z]+-\d{5}',
        'section_ref': r'(?:see\s+)?(?:section|paragraph|para\.?)\s+(\d+(?:\.\d+)*)',
        'attachment': r'(?:attachment|appendix|annex|exhibit)\s+([a-z]|\d+)',
        'pws_ref': r'pws\s+(?:section\s+)?(\d+(?:\.\d+)*)',
    }
    
    def add_relationship(source_id: str, target_id: str, rel_type: str, confidence: float, reason: str):
        """Add relationship if not duplicate or self-loop."""
        pair = (source_id, target_id)
        if pair not in seen_pairs and source_id != target_id:
            seen_pairs.add(pair)
            heuristic_rels.append({
                'source_id': source_id,
                'target_id': target_id,
                'relationship_type': rel_type,
                'confidence': confidence,
                'reasoning': f"Heuristic: {reason}"
            })
    
    # =========================================================================
    # NUMBERED HIERARCHY DETECTION (CHILD_OF)
    # =========================================================================
    # Build index: number prefix → entity
    # e.g., "F.1.5.7" → entity, "F.1.5" → entity, "3.2.1" → entity
    number_to_entity: Dict[str, Dict] = {}
    
    for entity in entities:
        name = entity.get('entity_name', '')
        prefix = _extract_number_prefix(name)
        if prefix:
            # Store first entity with this prefix (avoid duplicates)
            if prefix not in number_to_entity:
                number_to_entity[prefix] = entity
    
    logger.info(f"    Found {len(number_to_entity)} entities with numbered prefixes")
    
    # Now find parent-child relationships
    hierarchy_count = 0
    for number, entity in number_to_entity.items():
        parent_number = _get_parent_number(number)
        if parent_number and parent_number in number_to_entity:
            parent_entity = number_to_entity[parent_number]
            add_relationship(
                entity['id'], 
                parent_entity['id'], 
                'CHILD_OF',
                0.98,  # Very high confidence - deterministic pattern
                f"Numbered hierarchy: {number} → {parent_number}"
            )
            hierarchy_count += 1
    
    logger.info(f"    Created {hierarchy_count} CHILD_OF relationships from numbered hierarchy")
    
    # =========================================================================
    # EXISTING CROSS-REFERENCE DETECTION
    # =========================================================================
    # Build lookup indexes for fast matching
    cdrl_index = {}  # "CDRLA001" -> deliverable
    section_index = {}  # "3.1" -> section entity
    doc_index = {}  # "ATTACHMENT A" -> document
    
    for deliv in deliverables:
        name = (deliv.get('entity_name') or '').upper().replace(' ', '')
        desc = (deliv.get('description') or '').upper()
        # Index by CDRL ID
        cdrl_match = re.search(r'CDRL\s*([A-Z]?\d{3,4})', f"{name} {desc}")
        if cdrl_match:
            cdrl_key = f"CDRL{cdrl_match.group(1)}"
            cdrl_index[cdrl_key] = deliv
    
    for sec in sections:
        name = (sec.get('entity_name') or '')
        # Extract section numbers
        sec_match = re.search(r'(\d+(?:\.\d+)+)', name)
        if sec_match:
            section_index[sec_match.group(1)] = sec
    
    for doc in documents:
        name = (doc.get('entity_name') or '').upper()
        # Index by attachment/appendix letter or number
        att_match = re.search(r'(?:ATTACHMENT|APPENDIX|ANNEX)\s*([A-Z]|\d+)', name)
        if att_match:
            doc_index[f"ATTACHMENT{att_match.group(1)}"] = doc
    
    # Process all entities looking for cross-references
    for entity in entities:
        desc = (entity.get('description') or '').lower()
        name = (entity.get('entity_name') or '').lower()
        content = f"{name} {desc}"
        entity_type = entity.get('entity_type', '')
        
        # Skip self-references (deliverables referencing themselves)
        if entity_type == 'deliverable':
            continue
        
        # 1. CDRL references
        for match in re.finditer(patterns['cdrl'], content):
            cdrl_key = match.group().replace(' ', '').upper()
            if cdrl_key in cdrl_index:
                add_relationship(entity['id'], cdrl_index[cdrl_key]['id'], 
                               'REFERENCES', 0.90, f"CDRL cross-ref '{cdrl_key}'")
        
        # 2. DID references
        for match in re.finditer(patterns['did'], content):
            did_id = match.group().upper()
            for deliv in deliverables:
                if did_id in (deliv.get('description') or '').upper():
                    add_relationship(entity['id'], deliv['id'], 
                                   'REFERENCES', 0.90, f"DID cross-ref '{did_id}'")
                    break
        
        # 3. Section cross-references
        for match in re.finditer(patterns['section_ref'], content, re.IGNORECASE):
            sec_num = match.group(1)
            if sec_num in section_index:
                add_relationship(entity['id'], section_index[sec_num]['id'],
                               'REFERENCES', 0.90, f"Section cross-ref '{sec_num}'")
        
        # 4. Attachment/Appendix references  
        for match in re.finditer(patterns['attachment'], content, re.IGNORECASE):
            att_key = f"ATTACHMENT{match.group(1).upper()}"
            if att_key in doc_index:
                add_relationship(entity['id'], doc_index[att_key]['id'],
                               'REFERENCES', 0.90, f"Attachment cross-ref '{match.group()}'")
    
    # 5. Link requirements to deliverables if requirement mentions deliverable by name
    for req in requirements:
        req_desc = (req.get('description') or '').lower()
        for deliv in deliverables:
            deliv_name = (deliv.get('entity_name') or '').lower()
            # Avoid matching generic words
            if len(deliv_name) > 10 and deliv_name in req_desc:
                add_relationship(req['id'], deliv['id'],
                               'REFERENCES', 0.85, f"Requirement mentions deliverable '{deliv_name[:30]}...'")
    
    logger.info(f"    → Algo 7: {len(heuristic_rels)} relationships total")
    return heuristic_rels

