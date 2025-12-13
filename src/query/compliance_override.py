"""
Compliance Override Helpers (Query-Time)
=======================================

Keeps the /query/stream compliance override modular:
- Intent classification (submission checklist vs proposal outline)
- QueryParam tuning for recall and deterministic behavior
- Prompt templates loaded from prompts/ (NOT hardcoded)
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple

from lightrag.base import QueryParam

from src.core.prompt_loader import load_prompt

logger = logging.getLogger(__name__)


def is_exhaustive_compliance_query(query: str) -> bool:
    """
    Detect queries that should return an exhaustive compliance checklist.

    These are the cases where users mean "do not miss any instructions", which
    is a recall problem unless we widen retrieval and force a strict, source-grounded structure.
    """
    q = (query or "").lower()
    if "submission instruction" in q or "proposal submission" in q or "section l" in q:
        if any(x in q for x in ("all", "every", "complete", "entire", "don't miss", "do not miss", "full list")):
            return True
    if "non compliant" in q or "noncompliant" in q or "compliance" in q:
        if any(x in q for x in ("all", "every", "complete", "entire", "full list")):
            return True
    return False


def classify_compliance_intent(query: str) -> str:
    """
    Classify which compliance-style output template we should use.

    Returns:
        str: One of:
          - "submission_checklist": exhaustive submission instructions / Section L checklist (no solutioning)
          - "proposal_outline": proposal outline (compliance + content specifics + pain points + solutioning)
    """
    q = (query or "").lower()

    outline_markers = (
        "proposal outline",
        "outline",
        "volume i",
        "volume ii",
        "volume iii",
        "volume iv",
        "volume v",
        "volume vi",
        "volume vii",
        "volume viii",
        "volume ix",
    )
    solutioning_markers = (
        "pain point",
        "pain points",
        "solutioning",
        "win theme",
        "hot button",
        "discriminator",
        "favor in the award",
        "award decision",
        "strength",
        "weakness",
        "deficiency",
    )
    checklist_markers = (
        "submission instruction",
        "submission instructions",
        "proposal submission",
        "submit",
        "due date",
        "closing date",
        "page limit",
        "page limits",
        "format requirements",
        "font",
        "margin",
        "cd",
        "hardcopy",
        "hard copy",
        "address",
        "delivery",
        "label",
        "mark envelope",
        "section l",
        "instructions to offerors",
    )

    if any(m in q for m in outline_markers) and any(m in q for m in ("compliance", "compliance check", "compliance checks")):
        return "proposal_outline"
    if any(m in q for m in solutioning_markers) and any(m in q for m in ("outline", "proposal")):
        return "proposal_outline"
    if any(m in q for m in checklist_markers):
        return "submission_checklist"

    # Default conservative behavior for exhaustive compliance override:
    # treat it as submission checklist unless user clearly asked for outline/solutioning.
    return "submission_checklist"


def _load_override_prompt(profile: str) -> str:
    if profile == "proposal_outline":
        return load_prompt("query/compliance_proposal_outline_override")
    return load_prompt("query/compliance_submission_checklist_override")


def apply_compliance_override(param: QueryParam, query: str) -> Tuple[QueryParam, str]:
    """
    Apply compliance override settings to QueryParam.

    Returns:
        (param, profile): Mutated param and selected profile name.
    """
    profile = classify_compliance_intent(query)

    # Always ensure references are enabled for source-of-truth compliance queries.
    param.include_references = True

    # Mode selection:
    # - For exhaustive submission checklists we want BOTH KG + chunk evidence, so prefer "mix".
    # - If user selected "bypass", force to something usable.
    if param.mode == "bypass":
        param.mode = "mix" if profile == "submission_checklist" else "global"
    elif profile == "submission_checklist":
        # Even if user picked global, mix tends to recover page limits / copy matrices more reliably.
        param.mode = "mix"

    # Rerank adds noise if no rerank model is configured (and spams warnings).
    # For compliance checklists, prefer deterministic retrieval breadth.
    param.enable_rerank = False

    # Increase recall for "ALL instructions" style queries.
    param.chunk_top_k = max(getattr(param, "chunk_top_k", 0) or 0, 200)
    param.top_k = max(getattr(param, "top_k", 0) or 0, 120)

    # With description enrichment enabled, entity/relation context can grow large and crowd out the
    # text chunks that contain exact compliance requirements (page limits, CDs, etc.).
    # For exhaustive Section L checklists, prioritize chunk evidence over KG summaries.
    param.max_entity_tokens = min(getattr(param, "max_entity_tokens", 6000) or 6000, 2500)
    param.max_relation_tokens = min(getattr(param, "max_relation_tokens", 8000) or 8000, 3500)
    param.max_total_tokens = max(getattr(param, "max_total_tokens", 0) or 0, 60000)
    # Force Markdown-ish bullet behavior (LightRAG rag_response uses this label verbatim).
    param.response_type = "Markdown Bullet Points"

    # Provide stable keywords to avoid keyword-extraction variance.
    if not param.hl_keywords:
        if profile == "proposal_outline":
            param.hl_keywords = [
                "Section L",
                "Section M",
                "proposal outline",
                "compliance",
                "evaluation factors",
                "proposal instructions",
                "page limits",
                "volumes",
            ]
        else:
            param.hl_keywords = [
                "Section L",
                "proposal submission",
                "proposal instructions",
                "format requirements",
                "page limits",
                "volumes",
                "due date",
                "SF 33",
                "Block 9",
                "delivery address",
            ]

    if not param.ll_keywords:
        if profile == "proposal_outline":
            param.ll_keywords = [
                "volume",
                "submission_instruction",
                "page limit",
                "evaluation_factor",
                "Section L",
                "Section M",
                "font",
                "margin",
            ]
        else:
            param.ll_keywords = [
                "submission_instruction",
                "page limit",
                "volume",
                "font",
                "margin",
                "tabs/dividers",
                "electronic submission",
                "CD",
                "hard copy",
                "SF 33 Block 9",
                "SF33 Block 9",
                "Block 9",
                "closing date",
                "closing time",
                "closing",
                "June",
                "Jun",
                "2026",
                "late proposal",
            ]

    # Prompts live in prompts/ (sustainment-friendly).
    try:
        param.user_prompt = _load_override_prompt(profile)
    except Exception as e:
        # Graceful degradation: fallback to empty user_prompt rather than failing the query.
        logger.warning("Failed to load compliance override prompt for profile=%s: %s", profile, e)
        param.user_prompt = None

    return param, profile


