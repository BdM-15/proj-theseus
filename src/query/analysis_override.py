"""
Analysis Overrides (Query-Time)
==============================

LightRAG defaults are tuned for general Q&A. For capture/proposal workflows (pain points,
win themes, evaluation-driven strategy) we want:
- Wider retrieval (mix mode) so PWS/SOW + evaluation-factor evidence is included
- Higher token budget for "quality not brevity"
- Deterministic behavior (disable rerank when not configured)
- Modular prompts stored under prompts/query/
"""

from __future__ import annotations

import logging
import os
from typing import Tuple

from lightrag.base import QueryParam

from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


def _rerank_configured() -> bool:
    # LightRAG upstream default is RERANK_BINDING="null"
    return (os.getenv("RERANK_BINDING", "null") or "null").strip().lower() not in {"", "null", "none", "false", "0"}

def is_evaluation_factors_query(query: str) -> bool:
    q = (query or "").lower()
    if "evaluation factor" in q or "evaluation factors" in q:
        return True
    if "section m" in q and any(k in q for k in ("evaluate", "evaluation", "factors", "subfactor", "subfactors")):
        return True
    return False


def is_pain_points_analysis_query(query: str) -> bool:
    q = (query or "").lower()
    # High-signal capture intent (not compliance checklist)
    if "pain point" in q or "pain points" in q:
        return True
    if "win theme" in q or "strategic theme" in q or "hot button" in q or "discriminator" in q:
        return True
    # Common phrasing: "Based on the PWS/SOW and evaluation factors..."
    if ("pws" in q or "sow" in q or "statement of work" in q) and (
        "evaluation factor" in q or "evaluation factors" in q or "section m" in q or "source selection" in q
    ):
        if any(k in q for k in ("pain", "risk", "concern", "challenge", "weakness", "deficiency", "retain", "retention", "recruit", "recruiting")):
            return True
    return False


def apply_pain_points_override(param: QueryParam, query: str) -> Tuple[QueryParam, str]:
    """
    Apply a 'deep analysis' profile for capture-facing pain points questions.

    Returns:
        (param, profile_name)
    """
    profile = "pain_points_analysis"

    # Ensure sources are available.
    param.include_references = True

    # Prefer evidence-rich retrieval (KG + vectors).
    if param.mode == "bypass":
        param.mode = "mix"
    else:
        param.mode = "mix"

    # Enable rerank only when configured (LightRAG recommends mix mode with reranker enabled).
    param.enable_rerank = _rerank_configured()

    # Wider retrieval than defaults, but avoid flooding the generator (quality > quantity).
    param.chunk_top_k = max(getattr(param, "chunk_top_k", 0) or 0, 60)
    param.top_k = max(getattr(param, "top_k", 0) or 0, 50)

    # More room for synthesis (quality > brevity).
    param.max_total_tokens = max(getattr(param, "max_total_tokens", 0) or 0, 40000)

    # Keep some KG context (pain points benefit from evaluation factor structure), but don't let it dominate.
    param.max_entity_tokens = min(getattr(param, "max_entity_tokens", 6000) or 6000, 4500)
    param.max_relation_tokens = min(getattr(param, "max_relation_tokens", 8000) or 8000, 6000)

    param.response_type = "Markdown (Detailed)"

    # Nudge keyword stability toward evaluation + staffing/retention patterns.
    if not param.hl_keywords:
        param.hl_keywords = [
            "customer pain points",
            "government concerns",
            "evaluation factors",
            "PWS",
            "risk",
            "staffing",
            "recruitment",
            "retention",
            "shipboard",
        ]
    if not param.ll_keywords:
        param.ll_keywords = [
            "evaluation_factor",
            "requirement",
            "performance_metric",
            "statement_of_work",
            "quality assurance",
            "transition",
            "staffing",
            "recruiting",
            "retention",
            "shipboard",
        ]

    try:
        param.user_prompt = load_prompt("query/pain_points_analysis_override")
    except Exception as e:
        logger.warning("Failed to load pain points analysis override prompt: %s", e)
        param.user_prompt = None

    return param, profile


def apply_evaluation_factors_override(param: QueryParam, query: str) -> Tuple[QueryParam, str]:
    """
    Apply a 'structured evaluation factors' profile.
    """
    profile = "evaluation_factors"

    param.include_references = True
    param.enable_rerank = _rerank_configured()
    param.mode = "mix" if param.mode != "bypass" else "mix"

    # Pull more evidence than defaults, but keep generation focused.
    param.chunk_top_k = max(getattr(param, "chunk_top_k", 0) or 0, 60)
    param.top_k = max(getattr(param, "top_k", 0) or 0, 50)
    param.max_total_tokens = max(getattr(param, "max_total_tokens", 0) or 0, 40000)

    # Keep KG structure; evaluation factors usually live in a smaller slice of KG.
    param.max_entity_tokens = min(getattr(param, "max_entity_tokens", 6000) or 6000, 6000)
    param.max_relation_tokens = min(getattr(param, "max_relation_tokens", 8000) or 8000, 8000)

    param.response_type = "Markdown Bullet Points"

    if not param.hl_keywords:
        param.hl_keywords = ["Section M", "evaluation factors", "source selection", "tradeoff", "best value"]
    if not param.ll_keywords:
        param.ll_keywords = ["evaluation_factor", "subfactor", "weight", "importance", "adjectival", "rating", "tradeoff"]

    try:
        param.user_prompt = load_prompt("query/evaluation_factors_override")
    except Exception as e:
        logger.warning("Failed to load evaluation factors override prompt: %s", e)
        param.user_prompt = None

    return param, profile


