"""
LLM Output Sanitizer - Fixes delimiter corruption in LightRAG extraction output.

Lightweight wrapper that sanitizes LLM output BEFORE LightRAG's parser sees it.
Fixes corruption patterns that occur at the LLM output level (not entity-type
normalization, which LightRAG 1.4.13 handles natively via sanitize_and_normalize_extracted_text).

Patterns Fixed:
1. <|#|>#|requirement<|#|> → <|#|>requirement<|#|>  (hash-pipe prefix leakage)
2. <|#|>#/>requirement<|#|> → <|#|>requirement<|#|>  (hash-slash-greater-than)
3. <|#|>(requirement<|#|>  → <|#|>requirement<|#|>   (parenthesis prefix)
4. <|#|>requirement|<|#|>  → <|#|>requirement<|#|>   (trailing pipe)
5. Extra pipes in descriptions causing field count overflow

Entity type normalization (lowercase, underscore, strip special chars) is handled
natively by LightRAG 1.4.13 (operate.py sanitize_and_normalize_extracted_text + line 441).
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TUPLE_DELIMITER = "<|#|>"


class SanitizerStats:
    """Track sanitization statistics for monitoring."""
    def __init__(self):
        self.calls = 0
        self.sanitized = 0
        self.pre_split_fixes = 0
        self.field_count_fixes = 0

    def log_summary(self):
        if self.calls > 0:
            logger.info(f"📊 Sanitizer Stats: {self.calls} calls, {self.sanitized} outputs sanitized")
            if self.pre_split_fixes or self.field_count_fixes:
                logger.info(f"   Fixes: {self.pre_split_fixes} pre-split, {self.field_count_fixes} field counts")

_stats = SanitizerStats()


def get_sanitizer_stats() -> SanitizerStats:
    """Get current sanitizer statistics."""
    return _stats


def sanitize_extraction_output(raw_output: str) -> str:
    """
    Sanitize LLM extraction output to fix delimiter corruption patterns.

    Runs BEFORE LightRAG's parser, fixing issues that would otherwise
    cause entities/relationships to be silently dropped.
    """
    if not raw_output:
        return raw_output

    lines = raw_output.split('\n')
    fixed_lines = []
    fixes_applied = 0

    for line in lines:
        fixed_line = _fix_line(line)
        if fixed_line != line:
            fixes_applied += 1
        fixed_lines.append(fixed_line)

    if fixes_applied:
        logger.info(f"🔧 Output sanitization: {fixes_applied} lines fixed")

    return '\n'.join(fixed_lines)


def _fix_line(line: str) -> str:
    """Fix a single line of extraction output."""
    if not line.strip():
        return line

    # Fix delimiter corruption BEFORE splitting
    line = _pre_split_fixes(line)

    # Split by delimiter and fix field overflow
    parts = line.split(TUPLE_DELIMITER)
    if len(parts) < 3:
        return line

    record_type = parts[0].strip().lower()

    if record_type == 'entity' and len(parts) > 4:
        # Merge extra fields back into description (pipes in description text)
        extra_count = len(parts) - 4
        parts[3] = ' '.join(parts[3:])
        parts = parts[:4]
        _stats.field_count_fixes += 1
        logger.debug(f"🔧 Merged {extra_count} extra entity fields into description")

    elif record_type in ('relation', 'relationship') and len(parts) > 5:
        extra_count = len(parts) - 5
        parts[4] = ' '.join(parts[4:])
        parts = parts[:5]
        _stats.field_count_fixes += 1
        logger.debug(f"🔧 Merged {extra_count} extra relation fields into description")

    return TUPLE_DELIMITER.join(parts)


def _pre_split_fixes(line: str) -> str:
    """
    Fix delimiter corruption patterns BEFORE splitting by delimiter.

    Catches LLM output corruption where delimiter characters leak into field values:
    - <|#|>#|requirement<|#|> (hash-pipe prefix — most common)
    - <|#|>#/>requirement<|#|> (hash-slash-greater-than)
    - <|#|>(requirement<|#|> (parenthesis prefix)
    - <|#|>requirement|<|#|> (trailing pipe)
    """
    if not line:
        return line

    original = line

    # Pattern 1: Hash-pipe prefix (most common LLM corruption)
    # Handles multi-word: <|#|>#|person role<|#|>
    line = re.sub(r'<\|#\|>\s*#\|+\s*([^<]+?)\s*<\|#\|>', r'<|#|>\1<|#|>', line)

    # Pattern 1b: Simpler hash-pipe for single words (backup)
    line = re.sub(r'<\|#\|>\s*[#|]+\s*(\w+)\s*<\|#\|>', r'<|#|>\1<|#|>', line)

    # Pattern 2: Hash-slash-greater-than corruption
    line = re.sub(r'<\|#\|>\s*#[/\\|>]+\s*([^<]+?)\s*<\|#\|>', r'<|#|>\1<|#|>', line)

    # Pattern 3: Parenthesis prefix
    line = re.sub(r'<\|#\|>\s*\(\s*([^<]+?)\s*<\|#\|>', r'<|#|>\1<|#|>', line)

    # Pattern 4: Trailing pipe after entity type
    line = re.sub(r'<\|#\|>\s*([^<|]+?)\|+\s*<\|#\|>', r'<|#|>\1<|#|>', line)

    # Pattern 5: General garbage prefix before entity type
    line = re.sub(r'<\|#\|>\s*[^\w\s]+\s*(\w+(?:_\w+)*)\s*<\|#\|>', r'<|#|>\1<|#|>', line)

    if line != original:
        _stats.pre_split_fixes += 1
        logger.debug(f"🔧 Pre-split fix applied")

    return line


def create_sanitizing_wrapper(base_llm_func):
    """
    Create a wrapper that sanitizes LLM extraction output before returning it.

    Only activates on extraction outputs (detected by TUPLE_DELIMITER presence).
    """
    async def sanitizing_llm_func(
        prompt: str,
        system_prompt: Optional[str] = None,
        history_messages: list = None,
        **kwargs
    ) -> str:
        raw_output = await base_llm_func(
            prompt,
            system_prompt=system_prompt,
            history_messages=history_messages or [],
            **kwargs
        )

        if isinstance(raw_output, str) and TUPLE_DELIMITER in raw_output:
            _stats.calls += 1
            sanitized = sanitize_extraction_output(raw_output)
            if sanitized != raw_output:
                _stats.sanitized += 1
            return sanitized

        return raw_output
