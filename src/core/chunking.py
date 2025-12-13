"""
Structure-aware chunking helpers.

LightRAG's upstream default chunking is token-window sliding (`chunking_by_token_size`).
For federal RFPs (UCF A–M + attachments), a light structure-first split improves coherence:
sections/attachments stay together when possible, then we fall back to token windows.
"""

from __future__ import annotations

import re
from typing import Any

from lightrag.operate import chunking_by_token_size
from lightrag.utils import Tokenizer


_UCF_MARKERS = [
    # UCF sections
    "\nSECTION A",
    "\nSECTION B",
    "\nSECTION C",
    "\nSECTION D",
    "\nSECTION E",
    "\nSECTION F",
    "\nSECTION G",
    "\nSECTION H",
    "\nSECTION I",
    "\nSECTION J",
    "\nSECTION K",
    "\nSECTION L",
    "\nSECTION M",
    # common variants
    "\nSection A",
    "\nSection B",
    "\nSection C",
    "\nSection D",
    "\nSection E",
    "\nSection F",
    "\nSection G",
    "\nSection H",
    "\nSection I",
    "\nSection J",
    "\nSection K",
    "\nSection L",
    "\nSection M",
    # attachments / appendices / exhibits
    "\nAttachment",
    "\nATTACHMENT",
    "\nAppendix",
    "\nAPPENDIX",
    "\nExhibit",
    "\nEXHIBIT",
]


def chunking_by_ucf_then_tokens(
    tokenizer: Tokenizer,
    content: str,
    split_by_character: str | None = None,  # kept for compatibility with LightRAG signature
    split_by_character_only: bool = False,  # kept for compatibility
    chunk_overlap_token_size: int = 100,
    chunk_token_size: int = 1200,
) -> list[dict[str, Any]]:
    """
    1) Split on UCF/attachment markers to preserve structure
    2) Token-chunk each segment to enforce strict limits
    """
    if not content:
        return []

    text = content.replace("\r\n", "\n")

    # Create a regex that splits *before* markers while keeping them.
    # We use a lookahead so the marker remains at the start of the next segment.
    marker_re = "(" + "|".join(re.escape(m) for m in _UCF_MARKERS) + ")"
    parts = re.split(rf"(?={marker_re})", text)
    # Remove empty parts and keep reasonable minimum content
    segments = [p.strip() for p in parts if p and p.strip()]

    # If we didn't find structure, fall back to vanilla token chunking.
    if len(segments) <= 1:
        return chunking_by_token_size(
            tokenizer=tokenizer,
            content=text,
            chunk_overlap_token_size=chunk_overlap_token_size,
            chunk_token_size=chunk_token_size,
        )

    results: list[dict[str, Any]] = []
    chunk_order_index = 0
    for seg in segments:
        seg_chunks = chunking_by_token_size(
            tokenizer=tokenizer,
            content=seg,
            chunk_overlap_token_size=chunk_overlap_token_size,
            chunk_token_size=chunk_token_size,
        )
        for c in seg_chunks:
            c = dict(c)
            c["chunk_order_index"] = chunk_order_index
            chunk_order_index += 1
            results.append(c)
    return results

