"""
Query-Time Ontology Context Builder
==================================

Goal: Inject a SMALL, targeted slice of the GovCon ontology into LightRAG query prompts
without creating mega-prompts that harm performance.

This module intentionally uses lightweight heuristics to:
- Detect likely target entity types from the user's query
- Identify metadata focus (e.g., workload/BOE fields)
- Provide compact domain framing (UCF Section L/M, BOE categories)

Design constraints:
- Keep returned context short (a few hundred tokens)
- No additional LLM calls
- No dependence on chunk sizing
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List, Optional

from src.ontology.schema import BOECategory, VALID_ENTITY_TYPES


@dataclass(frozen=True)
class QueryContext:
    target_entity_types: List[str]
    metadata_focus: List[str]
    ucf_hint: Optional[str]
    boe_hint: Optional[str]

    def to_prompt_block(self) -> str:
        lines: List[str] = []

        if self.target_entity_types:
            lines.append(
                "Target entity types (filter/retrieval hint): "
                + ", ".join(self.target_entity_types)
            )

        if self.metadata_focus:
            lines.append("Metadata focus: " + ", ".join(self.metadata_focus))

        if self.ucf_hint:
            lines.append(self.ucf_hint)

        if self.boe_hint:
            lines.append(self.boe_hint)

        # Keep block compact and predictable
        block = "\n".join(lines).strip()
        if len(block) > 1200:
            block = block[:1200].rstrip()
        return block


def build_query_context(query: str) -> QueryContext:
    """
    Build a compact ontology context block for a user query.

    Args:
        query: Raw user query text.

    Returns:
        QueryContext: Small, prompt-ready ontology slice.
    """
    q = _norm(query)

    target_types = _detect_entity_types(q)
    metadata_focus = _detect_metadata_focus(q)
    ucf_hint = _detect_ucf_hint(q)
    boe_hint = _detect_boe_hint(q, metadata_focus)

    # Sanity: only emit valid ontology entity types
    target_types = [t for t in target_types if t in VALID_ENTITY_TYPES]

    return QueryContext(
        target_entity_types=target_types,
        metadata_focus=metadata_focus,
        ucf_hint=ucf_hint,
        boe_hint=boe_hint,
    )


def _norm(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"\s+", " ", text)
    return text


def _detect_entity_types(q: str) -> List[str]:
    hits: List[str] = []

    def add(t: str) -> None:
        if t not in hits:
            hits.append(t)

    # High-signal GovCon patterns
    if any(k in q for k in ["evaluation factor", "evaluation criteria", "source selection", "scoring", "adjectival", "rating"]):
        add("evaluation_factor")
    if any(k in q for k in ["section l", "submission instruction", "page limit", "volume i", "volume ii", "font", "margin"]):
        add("submission_instruction")
    if any(k in q for k in ["requirement", "shall", "must", "should", "may", "compliance", "shall provide"]):
        add("requirement")
    if any(k in q for k in ["performance metric", "threshold", "aql", "qasp", "performance objective"]):
        add("performance_metric")
    if any(k in q for k in ["cdrl", "deliverable", "did", "data item description", "monthly report", "status report"]):
        add("deliverable")
    if any(k in q for k in ["far", "dfars", "clause", "52.212", "252.2"]):
        add("clause")
    if any(k in q for k in ["pws", "sow", "statement of work", "task order", "tasks"]):
        add("statement_of_work")
    if any(k in q for k in ["attachment", "exhibit", "document", "standard", "mil-std"]):
        add("document")
    if any(k in q for k in ["program", "contract vehicle", "idiq", "bpa", "gwac"]):
        add("program")
    if any(k in q for k in ["gfe", "cfe", "equipment", "vehicle", "laptop", "server"]):
        add("equipment")
    if any(k in q for k in ["win theme", "strategic theme", "hot button", "discriminator", "proof point"]):
        add("strategic_theme")
    if any(k in q for k in ["agency", "command", "navy", "air force", "army", "dhs", "va", "organization"]):
        add("organization")
    if any(k in q for k in ["location", "site", "base", "conus", "oconus"]):
        add("location")
    if any(k in q for k in ["contracting officer", "cor", "key personnel", "program manager"]):
        add("person")
    if any(k in q for k in ["aws", "govcloud", "kubernetes", "zero trust", "splunk", "technology"]):
        add("technology")
    if any(k in q for k in ["section", "ucf", "section m", "section c"]):
        add("section")

    return hits


def _detect_metadata_focus(q: str) -> List[str]:
    focus: List[str] = []

    def add(x: str) -> None:
        if x not in focus:
            focus.append(x)

    if any(k in q for k in ["labor", "fte", "staffing", "shift", "coverage", "hours", "workload", "loe", "basis of estimate", "boe"]):
        add("labor_drivers")
        add("boe_category")
    if any(k in q for k in ["materials", "equipment", "supplies", "tools", "gfe", "cfe"]):
        add("material_needs")
    if any(k in q for k in ["weight", "points", "%", "importance"]):
        add("weight")
        add("importance")
    if any(k in q for k in ["criticality", "shall", "must", "should", "may"]):
        add("criticality")
        add("modal_verb")

    return focus


def _detect_ucf_hint(q: str) -> Optional[str]:
    if "section l" in q and "section m" in q:
        return "UCF hint: Section L (instructions) should map to Section M (evaluation factors) when answering."
    if "section l" in q:
        return "UCF hint: Section L contains submission instructions; map to Section M when evaluation is referenced."
    if "section m" in q:
        return "UCF hint: Section M contains evaluation factors/subfactors and weighting/importance signals."
    return None


def _detect_boe_hint(q: str, metadata_focus: List[str]) -> Optional[str]:
    if "boe_category" not in metadata_focus and not any(k in q for k in ["boe", "basis of estimate", "workload", "labor"]):
        return None

    categories = ", ".join([c.value for c in BOECategory])
    return (
        "BOE hint: classify workload signals into categories: "
        f"{categories}. Prefer raw workload drivers (volumes/frequencies/shifts) over invented staffing roles."
    )


