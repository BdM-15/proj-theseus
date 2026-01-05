"""
LLM Output Sanitizer - Fixes common malformation patterns in LightRAG extraction output.

This module provides a lightweight wrapper that sanitizes LLM output BEFORE LightRAG
parses it. Unlike the Pydantic adapter, this doesn't change the output format - it
just fixes common corruption patterns that cause entity/relationship drops.

Common Issues Fixed:
1. #|entity_type → entity_type (hash prefix from delimiter leakage)
2. |entity_type → entity_type (pipe prefix)
3. entity_type| → entity_type (pipe suffix)
4. #/>entity_type → entity_type (hash-slash-greater-than corruption)
5. (entity_type → entity_type (parenthesis prefix corruption)
6. Extra pipes in descriptions causing field count errors
7. Special characters in entity type field (/, >, <, etc.)

Issue #56: Post-Processing Overhaul
Updated: December 2025 - Enhanced patterns from MCPP II processing logs
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# LightRAG's expected delimiter
TUPLE_DELIMITER = "<|#|>"


def sanitize_extraction_output(raw_output: str) -> str:
    """
    Sanitize LLM extraction output to fix common malformation patterns.
    
    This runs BEFORE LightRAG's parser sees the output, fixing issues that
    would otherwise cause entities/relationships to be silently dropped.
    
    Args:
        raw_output: Raw LLM output string
        
    Returns:
        Sanitized output string
    """
    if not raw_output:
        return raw_output
    
    original_len = len(raw_output)
    output = raw_output
    fixes_applied = []
    
    # Split into lines to process each record
    lines = output.split('\n')
    fixed_lines = []
    
    for line in lines:
        fixed_line = _fix_line(line)
        if fixed_line != line:
            fixes_applied.append(f"Fixed: '{line[:50]}...' → '{fixed_line[:50]}...'")
        fixed_lines.append(fixed_line)
    
    output = '\n'.join(fixed_lines)
    
    # Log if any fixes were applied
    if fixes_applied and len(fixes_applied) <= 5:
        for fix in fixes_applied:
            logger.debug(f"🔧 Output sanitization: {fix}")
    elif fixes_applied:
        logger.info(f"🔧 Output sanitization: {len(fixes_applied)} lines fixed")
    
    return output


def _fix_line(line: str) -> str:
    """Fix a single line of extraction output."""
    if not line.strip():
        return line
    
    # First, apply pre-split fixes for delimiter corruption BEFORE splitting
    # This catches things like "#|requirement" in the middle of the string
    line = _pre_split_fixes(line)
    
    # Split by delimiter
    parts = line.split(TUPLE_DELIMITER)
    
    if len(parts) < 3:
        return line  # Not a valid record, leave as-is
    
    # Check if this is an entity line (4 fields) or relation line (5 fields)
    record_type = parts[0].strip().lower()
    
    if record_type == 'entity' and len(parts) >= 4:
        # Entity: entity<|#|>name<|#|>type<|#|>description
        # Fix the entity_type field (index 2)
        parts[2] = _clean_entity_type(parts[2])
        
        # Fix description field if it has embedded pipes causing field overflow
        if len(parts) > 4:
            # Merge extra fields back into description using space (NOT delimiter!)
            extra_count = len(parts) - 4
            parts[3] = ' '.join(parts[3:])  # Merge with space, not delimiter
            parts = parts[:4]
            _stats.field_count_fixes += 1
            logger.info(f"🔧 Merged {extra_count} extra entity fields into description")
            
    elif record_type in ('relation', 'relationship') and len(parts) >= 5:
        # Relation: relation<|#|>source<|#|>target<|#|>keywords<|#|>description
        # Fix if we have too many fields (pipes in description)
        if len(parts) > 5:
            # Merge extra fields back into description using space (NOT delimiter!)
            extra_count = len(parts) - 5
            parts[4] = ' '.join(parts[4:])  # Merge with space, not delimiter
            parts = parts[:5]
            _stats.field_count_fixes += 1
            logger.info(f"🔧 Merged {extra_count} extra relation fields into description")
    
    return TUPLE_DELIMITER.join(parts)


def _pre_split_fixes(line: str) -> str:
    """
    Apply fixes to the line BEFORE splitting by delimiter.
    
    Catches patterns like: entity<|#|>Name<|#|>#|requirement<|#|>Desc
    Where "#|requirement" has the hash prefix stuck to the entity type.
    
    IMPORTANT: Must handle whitespace EVERYWHERE:
    - <|#|>#|requirement<|#|>      (no spaces)
    - <|#|>#| requirement<|#|>     (space AFTER prefix, BEFORE word)
    - <|#|> #|requirement<|#|>     (space before prefix)
    - <|#|>#|requirement <|#|>     (space after word)
    - <|#|>#/>requirement<|#|>     (hash-slash-greater-than corruption - MCPP II pattern)
    - <|#|>(requirement<|#|>       (parenthesis prefix corruption)
    
    CRITICAL: Handle multi-word entity types like "person role" which (\w+) doesn't match!
    """
    if not line:
        return line
    
    original = line
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern 1: Hash-pipe prefix corruption (MOST COMMON)
    # <|#|>#|requirement<|#|> → <|#|>requirement<|#|>
    # <|#|>#| requirement<|#|> → <|#|>requirement<|#|>
    # <|#|>#|person role<|#|> → <|#|>person role<|#|>  (multi-word!)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Use [^<]+ instead of \w+ to match ANY characters until the next delimiter
    line = re.sub(r'<\|#\|>\s*#\|+\s*([^<]+?)\s*<\|#\|>', r'<|#|>\1<|#|>', line)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern 1b: Simpler hash-pipe at start of field (backup pattern)
    # <|#|>#|word → <|#|>word (for single words)
    # ═══════════════════════════════════════════════════════════════════════════════
    line = re.sub(r'<\|#\|>\s*[#|]+\s*(\w+)\s*<\|#\|>', r'<|#|>\1<|#|>', line)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern 2: Hash-slash-greater-than corruption (seen in MCPP II logs)
    # <|#|>#/>requirement<|#|> → <|#|>requirement<|#|>
    # <|#|>#/> requirement<|#|> → <|#|>requirement<|#|>
    # Also handles: #/>, #\>, #|>, etc.
    # ═══════════════════════════════════════════════════════════════════════════════
    line = re.sub(r'<\|#\|>\s*#[/\\|>]+\s*([^<]+?)\s*<\|#\|>', r'<|#|>\1<|#|>', line)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern 3: Parenthesis prefix corruption (seen in MCPP II logs)
    # <|#|>(requirement<|#|> → <|#|>requirement<|#|>
    # <|#|>( requirement<|#|> → <|#|>requirement<|#|>
    # ═══════════════════════════════════════════════════════════════════════════════
    line = re.sub(r'<\|#\|>\s*\(\s*([^<]+?)\s*<\|#\|>', r'<|#|>\1<|#|>', line)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern 4: Trailing pipe after entity type
    # <|#|>requirement|<|#|> → <|#|>requirement<|#|>
    # ═══════════════════════════════════════════════════════════════════════════════
    line = re.sub(r'<\|#\|>\s*([^<|]+?)\|+\s*<\|#\|>', r'<|#|>\1<|#|>', line)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern 5: General garbage prefix before entity type (single word)
    # <|#|>[symbols]entity_type<|#|> → <|#|>entity_type<|#|>
    # Catches any non-word characters before the actual entity type
    # ═══════════════════════════════════════════════════════════════════════════════
    line = re.sub(r'<\|#\|>\s*[^\w\s]+\s*(\w+(?:_\w+)*)\s*<\|#\|>', r'<|#|>\1<|#|>', line)
    
    # Log if we made any changes (helps diagnose what patterns we're catching)
    if line != original:
        _stats.pre_split_fixes += 1
        logger.debug(f"🔧 Pre-split fix: '{original[:80]}...' → '{line[:80]}...'")
    
    return line


def _clean_entity_type(entity_type: str) -> str:
    """
    Clean entity type field by removing common malformation patterns.
    
    This is the LAST LINE OF DEFENSE before LightRAG's validation rejects entities.
    LightRAG rejects entity types containing: ' ( ) < > | / \
    
    Fixes (observed in processing logs):
    - #|requirement → requirement (hash-pipe prefix - CRITICAL, causes drops)
    - |requirement → requirement (pipe prefix)
    - requirement| → requirement (pipe suffix)
    - #requirement → requirement (hash prefix)
    - #/>requirement → requirement (hash-slash-greater-than)
    - (requirement → requirement (parenthesis prefix)
    - requirement) → requirement (parenthesis suffix)
    - #| person → person (space after corruption prefix)
    """
    if not entity_type:
        return entity_type
    
    original = entity_type
    cleaned = entity_type.strip()
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 1: Handle the CRITICAL #| prefix pattern that causes entity drops
    # This is the most common corruption pattern from LLM delimiter leakage
    # Must handle variants: "#|type", "# |type", "#| type", "# | type"
    # ═══════════════════════════════════════════════════════════════════════════════
    # Remove #| or # | at the start (with optional spaces around)
    cleaned = re.sub(r'^#\s*\|\s*', '', cleaned)
    # Remove |# at the start (reversed order)
    cleaned = re.sub(r'^\|\s*#\s*', '', cleaned)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 2: Remove leading garbage patterns (more comprehensive)
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern: #|, |#, #/, #>, #\, |, #, etc. at the start
    cleaned = re.sub(r'^[#|/\\><\(\)\s]+', '', cleaned)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 3: Remove trailing garbage patterns  
    # ═══════════════════════════════════════════════════════════════════════════════
    # Pattern: |, #, >, etc. at the end
    cleaned = re.sub(r'[#|/\\><\(\)\s]+$', '', cleaned)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 4: Remove any remaining special characters that LightRAG rejects
    # LightRAG validation: any(char in entity_type for char in ["'", "(", ")", "<", ">", "|", "/", "\\"])
    # Entity types should be alphanumeric with underscores only
    # ═══════════════════════════════════════════════════════════════════════════════
    cleaned = re.sub(r'[<>()\'"/\\|#]', '', cleaned)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 5: Normalize - lowercase, convert spaces to underscores
    # Entity types like "statement of work" → "statement_of_work"
    # ═══════════════════════════════════════════════════════════════════════════════
    cleaned = cleaned.strip().lower().replace(' ', '_')
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # Step 6: Final validation - ensure no forbidden characters remain
    # If any slip through, log a warning so we can add patterns
    # ═══════════════════════════════════════════════════════════════════════════════
    forbidden_chars = ["'", "(", ")", "<", ">", "|", "/", "\\"]
    remaining_forbidden = [c for c in forbidden_chars if c in cleaned]
    if remaining_forbidden:
        logger.warning(f"⚠️ Entity type still contains forbidden chars after cleaning: '{cleaned}' (chars: {remaining_forbidden})")
    
    if cleaned != original.strip().lower().replace(' ', '_'):
        _stats.entity_type_fixes += 1
        logger.debug(f"🔧 Entity type sanitized: '{original}' → '{cleaned}'")
    
    return cleaned


class SanitizerStats:
    """Track sanitization statistics for monitoring."""
    def __init__(self):
        self.calls = 0
        self.sanitized = 0
        self.pre_split_fixes = 0
        self.entity_type_fixes = 0
        self.field_count_fixes = 0
    
    def log_summary(self):
        if self.calls > 0:
            logger.info(f"📊 Sanitizer Stats: {self.calls} calls, {self.sanitized} outputs sanitized")
            if self.pre_split_fixes or self.entity_type_fixes or self.field_count_fixes:
                logger.info(f"   Fixes: {self.pre_split_fixes} pre-split, {self.entity_type_fixes} entity types, {self.field_count_fixes} field counts")

# Global stats instance
_stats = SanitizerStats()


def get_sanitizer_stats() -> SanitizerStats:
    """Get current sanitizer statistics."""
    return _stats


def create_sanitizing_wrapper(base_llm_func):
    """
    Create a wrapper that sanitizes LLM output before returning it.
    
    This is a lightweight alternative to the full Pydantic adapter.
    It doesn't change the output format, just fixes common corruption.
    
    Usage in initialization.py:
        from src.extraction.output_sanitizer import create_sanitizing_wrapper
        
        llm_model_func = create_sanitizing_wrapper(base_llm_model_func)
    """
    async def sanitizing_llm_func(
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: list = None,
        **kwargs
    ) -> str:
        # Call the base LLM function
        raw_output = await base_llm_func(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            **kwargs
        )
        
        # Only sanitize extraction outputs (detected by delimiter presence)
        if isinstance(raw_output, str) and TUPLE_DELIMITER in raw_output:
            _stats.calls += 1
            sanitized = sanitize_extraction_output(raw_output)
            if sanitized != raw_output:
                _stats.sanitized += 1
            return sanitized
        
        return raw_output
    
    return sanitizing_llm_func

