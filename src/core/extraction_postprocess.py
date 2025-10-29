"""Tolerant LLM output post-processing utilities

Provides a robust parser that accepts a variety of LLM output formats and
attempts to recover structured entity dictionaries. The goal is to reduce
noise during ingestion by preserving raw output, extracting best-effort
structured fields, and exposing hooks for Pydantic validation.

This module is intentionally conservative: it never raises on malformed
LLM output. Instead it returns a list of records with 'raw', 'parsed' and
'error' fields so the caller can decide whether to persist, audit or drop
the extraction.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple


COMMON_DELIMITERS = ["\n\n", "<|#|>", "|||", "\n- ", "\n", "||", "\t"]


def split_into_chunks(raw: str) -> List[str]:
    """Split raw LLM output into plausible chunks using common delimiters.

    Tries a sequence of delimiters from most-specific to fallback newline.
    """
    if not raw:
        return []

    # First, try to parse as JSON array/object in whole
    try:
        parsed = json.loads(raw)
        # If top-level is a list, treat each item as a chunk
        if isinstance(parsed, list):
            return [json.dumps(item) for item in parsed]
        # Single JSON object -> single chunk
        return [raw]
    except Exception:
        pass

    for d in COMMON_DELIMITERS:
        parts = [p.strip() for p in raw.split(d) if p and p.strip()]
        if len(parts) > 1:
            return parts

    # Fallback: return whole raw as single chunk
    return [raw.strip()]


def try_parse_json(text: str) -> Optional[Any]:
    try:
        return json.loads(text)
    except Exception:
        return None


def heuristic_parse_line(line: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """Try to parse a single chunk heuristically.

    Returns (parsed_dict_or_None, error_message_or_None)
    """
    # Try JSON first
    j = try_parse_json(line)
    if j is not None:
        if isinstance(j, dict):
            return j, None
        # If JSON is a scalar or list, wrap it
        return {"value": j}, None

    # Common pattern: "EntityText | entity_type | confidence: 0.92"
    # Split by pipes or tabs or double-colon patterns
    for sep in ["|", "\t", "::", " - "]:
        if sep in line and line.count(sep) >= 1:
            parts = [p.strip() for p in line.split(sep) if p.strip()]
            if len(parts) >= 2:
                # Heuristic mapping: last part numeric -> confidence
                parsed = {"text": parts[0], "type": parts[1]}
                # Attempt to extract confidence from remaining parts
                for p in parts[2:]:
                    m = re.search(r"([0-9]*\.?[0-9]+)", p)
                    if m:
                        try:
                            parsed["confidence"] = float(m.group(1))
                            break
                        except Exception:
                            pass
                return parsed, None

    # If nothing matched, return minimal structure
    if len(line) < 400:
        # short raw line -> treat as text
        return {"text": line.strip()}, None

    # Otherwise, give up and return None with an explanatory message
    return None, "unparsed: no known pattern matched"


def tolerant_parse_entities(raw_output: str) -> List[Dict[str, Any]]:
    """Parse raw LLM output into a list of records.

    Each record is a dict with keys:
      - raw: original chunk string
      - parsed: dict or None
      - error: None if parsed, otherwise a short error message
      - validated: dict with validation result (optional, filled if validation attempted)
    """
    chunks = split_into_chunks(raw_output)
    results: List[Dict[str, Any]] = []

    for c in chunks:
        parsed, err = heuristic_parse_line(c)
        rec: Dict[str, Any] = {"raw": c, "parsed": parsed, "error": err}

        # Try lightweight Pydantic validation if available
        try:
            from src.models.rfp_models import validate_extraction_payload

            # validate_extraction_payload expects a shaped dict (e.g., {'entities': [...]})
            # If parsed looks like a single entity/requirement, wrap it into the expected container
            if isinstance(parsed, dict) and any(k in parsed for k in ("type", "text", "id", "requirements", "requirements_text")):
                try_payload = {"entities": [parsed]}
            else:
                try_payload = parsed if parsed is not None else {"text": c}

            valid, details = validate_extraction_payload(try_payload)
            rec.setdefault("validated", {})
            rec["validated"]["ok"] = valid
            rec["validated"]["details"] = details
        except Exception:
            # validation is optional; silence import/validation errors
            pass

        results.append(rec)

    return results


def summarize_parse_results(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Return a small summary of parsed vs unparsed counts."""
    parsed = sum(1 for r in results if r.get("parsed"))
    unparsed = len(results) - parsed
    validated = sum(1 for r in results if r.get("validated", {}).get("ok") is True)
    return {"total": len(results), "parsed": parsed, "unparsed": unparsed, "validated": validated}
