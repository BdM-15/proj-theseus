"""
Custom Project Theseus UI routes.

Mounts a single-page cyberpunk capture-management UI at /ui and exposes a
small set of JSON endpoints under /api/ui/* for things the upstream
LightRAG WebUI does not provide:

- Dashboard rollups
- File-based chat persistence (one JSON file per chat,
  rag_storage/<workspace>/chats/<chat_id>.json)
- Shipley phase 4-6 suggested-prompt library

All RAG/graph/document data continues to flow through the upstream
LightRAG endpoints (`/query`, `/graphs`, `/documents`, etc.) plus our
custom `/insert`, `/documents/upload`, and `/scan-rfp`. This module
intentionally adds zero new Python dependencies.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Awaitable, Callable, Optional, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from lightrag.api.config import global_args
from pydantic import BaseModel, Field

# query_func signature: (text, mode, history, stream, overrides) -> str | AsyncIterator[str]
# - history: list of {"role": "user"|"assistant", "content": str}
# - overrides: dict of QueryParam tunables (top_k, chunk_top_k, max_*_tokens,
#   enable_rerank, only_need_context, only_need_prompt, response_type, user_prompt)
#   plus an optional "min_rerank_score" applied to the LightRAG instance for the call.
# - stream=False returns awaitable str; stream=True returns awaitable AsyncIterator[str]
QueryFunc = Callable[
    [str, str, list[dict], bool, dict],
    Awaitable[Union[str, AsyncIterator[str]]],
]

# data_func signature: (text, mode, history, overrides) -> dict
# Returns LightRAG aquery_data shape: {status, message, data: {chunks, entities, relationships, references}}.
QueryDataFunc = Callable[
    [str, str, list[dict], dict],
    Awaitable[dict],
]

from src.core import get_settings, reset_settings
from src.ontology.schema import VALID_ENTITY_TYPES, VALID_RELATIONSHIP_TYPES
from src.server.chat_store import ChatStore
from src.server.mcp_ui_routes import register_mcp_ui_routes
from src.server.query_settings import (
    QuerySettingsStore,
    register_query_settings_routes,
)
from src.server.reasoning_filter import ThinkStripper, strip_think
from src.server.skill_ui_routes import register_skill_ui_routes

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_THIS_DIR = Path(__file__).resolve().parent
_STATIC_DIR = (_THIS_DIR.parent / "ui" / "static").resolve()


def _workspace_dir() -> Path:
    """Return the active workspace directory under rag_storage/."""
    settings = get_settings()
    return Path(global_args.working_dir) / settings.workspace


def _chats_dir() -> Path:
    """Return (and create) the chats persistence directory for this workspace."""
    folder = _workspace_dir() / "chats"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class ChatCreate(BaseModel):
    title: str = Field(default="New chat", max_length=120)
    mode: str = Field(default="mix")
    rfp_context: Optional[str] = Field(default=None, max_length=200)


class ChatUpdate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=120)
    mode: Optional[str] = Field(default=None)
    rfp_context: Optional[str] = Field(default=None, max_length=200)


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=20000)


class WorkspaceSwitch(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    create: bool = Field(default=False, description="Create the folder if it does not exist.")


class WorkspaceDeleteScope(BaseModel):
    """Which buckets of a workspace to delete. At least one must be true."""

    neo4j: bool = Field(default=False, description="Delete the workspace's Neo4j subgraph.")
    rag_storage: bool = Field(default=False, description="Delete rag_storage/<ws>/ (KV stores, VDBs, chats, log).")
    inputs: bool = Field(default=False, description="Delete inputs/<ws>/ source documents (irrecoverable).")


class WipeAllScope(BaseModel):
    """Clean-slate wipe. Requires the literal confirmation phrase."""

    neo4j: bool = Field(default=False)
    rag_storage: bool = Field(default=False)
    inputs: bool = Field(default=False)
    confirm: str = Field(..., description="Must equal 'DELETE ALL'.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SAFE_WS = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


from src.utils.time_utils import now_local_iso as _now_local_iso


def _now_iso() -> str:
    """ISO timestamp in America/Chicago (CST/CDT)."""
    return _now_local_iso(timespec="seconds")


# Maximum characters per chunk preview shipped to the UI. Keeps the SSE event
# small and the chat-file footprint reasonable on long conversations.
_SOURCE_PREVIEW_CHARS = 800


def _trim_sources(data: dict) -> dict:
    """Project LightRAG aquery_data['data'] into a compact UI payload.

    Keeps only the fields the Sources panel needs and truncates chunk text to
    `_SOURCE_PREVIEW_CHARS`. The full chunk content already lives in LightRAG
    storage; the UI only needs enough to preview and link back.
    """
    chunks_in = data.get("chunks") or []
    refs_in = data.get("references") or []
    ents_in = data.get("entities") or []
    rels_in = data.get("relationships") or []

    chunks_out = []
    for c in chunks_in:
        if not isinstance(c, dict):
            continue
        content = str(c.get("content") or "")
        truncated = len(content) > _SOURCE_PREVIEW_CHARS
        preview = content[:_SOURCE_PREVIEW_CHARS] + ("\u2026" if truncated else "")
        chunks_out.append(
            {
                "reference_id": str(c.get("reference_id") or ""),
                "chunk_id": str(c.get("chunk_id") or ""),
                "file_path": str(c.get("file_path") or ""),
                "preview": preview,
                "char_count": len(content),
                "truncated": truncated,
            }
        )

    refs_out = [
        {
            "reference_id": str(r.get("reference_id") or ""),
            "file_path": str(r.get("file_path") or ""),
        }
        for r in refs_in
        if isinstance(r, dict)
    ]

    return {
        "chunks": chunks_out,
        "references": refs_out,
        "counts": {
            "chunks": len(chunks_out),
            "entities": len(ents_in),
            "relationships": len(rels_in),
            "references": len(refs_out),
        },
    }


# ---------------------------------------------------------------------------
# Suggested prompt library (Shipley phases 3-6)
#
# Design rules:
#  - Pattern-based, not keyword-based: prompts assume Theseus has indexed the
#    RFP's structure (sections, requirements, eval criteria, deliverables) and
#    refer to those abstractions rather than literal headings.
#  - Agnostic: no company, customer, agency, or program names. Use neutral
#    placeholders like {topic}, {section_or_task}, {capability}, {discriminator},
#    {requirement_id}, {volume_or_section}.
#  - Adaptable: each prompt works against any RFP the user has loaded into the
#    active workspace.
#  - Shipley-aligned: phases mirror Shipley capture/proposal lifecycle phases
#    3 (Capture), 4 (Planning), 5 (Development), 6 (Color Reviews & Submittal).
# ---------------------------------------------------------------------------

_PROMPT_LIBRARY: list[dict[str, str]] = [
    # ═════════════════ Phase 3 — Capture / RFP Discovery ═════════════════
    {"phase": "3", "category": "Discovery", "title": "Acquisition snapshot",
     "prompt": "Summarize this acquisition in one page: customer, mission need, contract vehicle, NAICS, set-aside, period of performance, estimated value, place of performance, and incumbent (if known). Cite the clauses you used."},
    {"phase": "3", "category": "Discovery", "title": "Customer priorities & pain points",
     "prompt": "Identify and describe the customer's top priorities and pain points based on the indexed scope/PWS/SOO. For each priority, quote the source language, classify it (modernization, integration, security, schedule, cost, mission readiness, workforce, etc.), and explain why it matters to the customer's mission outcome."},
    {"phase": "3", "category": "Discovery", "title": "Mission objectives & end-state",
     "prompt": "Extract the customer's stated mission objectives and the end-state they want to reach by end of period of performance. Distinguish 'must-achieve' from 'aspirational' language. Cite source paragraphs."},
    {"phase": "3", "category": "Discovery", "title": "Hot buttons (stated + implied)",
     "prompt": "Extract every hot button — stated and implied. For each: quote the source, classify it (cost / schedule / performance / risk / mission / workforce / security / sustainability), score how strongly it is signaled, and propose the response posture we should adopt."},
    {"phase": "3", "category": "Discovery", "title": "Size, scope, and complexity assessment",
     "prompt": "Describe the size, scope, and complexity of the requirements. Cover: breadth of tasks, integration burden, technology stack, security/clearance posture, geographic footprint, dependencies on external organizations, methodologies prescribed, and the deliverables tempo. Cite the source for each claim."},
    {"phase": "3", "category": "Discovery", "title": "Incumbent & competitor signals",
     "prompt": "Surface every clue about the incumbent or likely competitors: transition language, GFE/GFI references, resume requirements, oddly specific past-performance asks, named tools/standards, license counts, transition timelines. List each clue with the cited source and what it implies."},
    {"phase": "3", "category": "Discovery", "title": "Bid / no-bid scoring inputs",
     "prompt": "Score this opportunity against standard bid/no-bid factors (customer fit, capability fit, competition, win probability, profitability, strategic value, risk). Cite RFP language supporting each score and surface unknowns we still need to chase."},
    {"phase": "3", "category": "Strategy", "title": "Capture plan kickoff",
     "prompt": "Outline a Shipley-style capture plan for this opportunity. Cover: opportunity background, customer mission and known procurement details, capture strategy (hot buttons, likely competitors, our discriminators), capture milestones (gate reviews, solution checkpoints, submission deadlines), capture team roles, and the intelligence-gathering / shaping / positioning actions required. Flag readiness risks and gaps."},
    {"phase": "3", "category": "Strategy", "title": "Competitive landscape analysis",
     "prompt": "List the steps you would take to analyze the competitive landscape for this scope, then execute them against the indexed RFP. Identify likely bidders, their probable positioning, and the discriminators we would need to neutralize each one."},
    {"phase": "3", "category": "Strategy", "title": "SWOT vs this opportunity",
     "prompt": "Build a SWOT analysis of our likely bid posture against this specific opportunity: strengths we can prove, weaknesses to mitigate, opportunities to ghost competitors, threats from incumbent advantage or scope drift. Anchor each entry in cited RFP language."},

    # ═════════════════ Phase 4 — Proposal Planning ═════════════════
    {"phase": "4", "category": "Compliance", "title": "Full Compliance Matrix (Instructions ↔ Evaluation)",
     "prompt": "Generate a full proposal-instruction ↔ evaluation-factor compliance matrix. For every proposal_instruction (UCF Section L or equivalent — non-UCF task orders, FOPRs, BPA calls, OTAs may name the section differently or embed instructions inline in the PWS), list the linked evaluation_factor (UCF Section M or equivalent — including adjectival or LPTA schemes), the responsible proposal volume, page-limit constraints, and any unmatched items as gaps. Tag each row with instruction_source (UCF-L | non-UCF | PWS-inline | attachment) and evaluation_source (UCF-M | non-UCF | adjectival | LPTA). Do NOT emit GAP merely because an entity lacks a literal 'Section L' / 'Section M' heading."},
    {"phase": "4", "category": "Compliance", "title": "Cross-reference matrix (9-column)",
     "prompt": "Create a proposal cross-reference matrix with nine columns: Section Number, Section Title, Proposal Instructions, Evaluation Criteria, SOW/PWS, Other, Author, Pages, Status. Populate Section Number/Title from the proposal outline implied by the proposal_instruction entities, the Proposal Instructions column from those proposal_instruction entities (UCF Section L or equivalent), the Evaluation Criteria column from the evaluation_factor entities (UCF Section M or equivalent), and the SOW/PWS column from the statement-of-work paragraphs. Works for UCF and non-UCF formats (FAR 16 task orders, FOPRs, BPA calls, OTAs, agency-specific). Leave Author/Pages/Status blank for the team to fill."},
    {"phase": "4", "category": "Compliance", "title": "Verify outline accuracy",
     "prompt": "Verify the accuracy of the draft outline language against the actual proposal_instruction entities (UCF Section L or equivalent — may live in a named attachment or inline in the PWS for non-UCF solicitations), then verify the Evaluation Criteria column language against the actual evaluation_factor entities (UCF Section M or equivalent — including adjectival or LPTA schemes), then verify the SOW/PWS column references against the actual statement of work. Surface any drift, paraphrase that loses meaning, or missing requirements."},
    {"phase": "4", "category": "Compliance", "title": "Page limits & format constraints",
     "prompt": "List every page limit, font, margin, line spacing, file-format, naming-convention, and submission-mechanic constraint stated anywhere in the RFP. Cite the source clause for each. Flag conflicts."},
    {"phase": "4", "category": "Compliance", "title": "Submission checklist",
     "prompt": "Build a submission checklist: every artifact required (volumes, certifications, reps & certs, oral-presentation slides, pricing files, model contract), the format, the page limit, the section that imposes the requirement, and the responsible owner."},
    {"phase": "4", "category": "Discovery", "title": "Unclear requirements & questions to ask",
     "prompt": "Identify requirements that are ambiguous, contradictory, or missing detail. For each: quote the source, explain why it is unclear, and draft 2-3 specific questions we should ask the contracting officer (or address in our assumptions section)."},
    {"phase": "4", "category": "Strategy", "title": "Win themes & discriminators",
     "prompt": "Identify candidate win themes, discriminators, and proof points implied by the indexed RFP. Map each to the customer priority or pain point it addresses, and to the evaluation factor it would influence. Distinguish true discriminators (likely unique to us) from table stakes."},
    {"phase": "4", "category": "Strategy", "title": "Solution architecture brief",
     "prompt": "Sketch a solution architecture brief: technical approach pillars, management approach pillars, staffing model assumptions, transition approach, and risk mitigations. Tie each pillar to the evaluation_factor it earns credit against (UCF Section M or equivalent — including adjectival or LPTA schemes) and to the customer pain point it addresses."},
    {"phase": "4", "category": "Strategy", "title": "Ghost language opportunities",
     "prompt": "Identify themes and language we can ghost to highlight likely competitor weaknesses without naming them. Anchor each ghost in a customer pain point, a likely competitor gap, and the evaluation factor it would influence."},
    {"phase": "4", "category": "Pricing", "title": "Workload & BOE drivers",
     "prompt": "Pull every workload metric, performance standard, deliverable count, frequency, surge condition, and skill-mix indicator that drives basis of estimate. For each: cite the RFP location, note the unit of measure, and flag where the data is ambiguous or missing."},
    {"phase": "4", "category": "Pricing", "title": "Labor category mapping",
     "prompt": "For task {section_or_task} (or every task if none specified): identify the most suitable labor categories and skill levels from the contract vehicle's labor matrix. For each: name the category, the skill level, the matching responsibilities, and a justification tying experience-level requirements to the task complexity. Flag any task that does not map cleanly to a defined category."},
    {"phase": "4", "category": "Risk", "title": "Risk register & mitigations",
     "prompt": "Build a risk register from the RFP: technical, schedule, cost, transition, security, supply-chain, and integration risks. For each: cite the source language, score likelihood × impact (Low/Med/High), name the owner, propose a mitigation, and identify the proposal section that will describe the mitigation."},
    {"phase": "4", "category": "Risk", "title": "Detailed project risk assessment",
     "prompt": "Perform a detailed risk assessment for the as-bid solution. Categorize risks as technical, financial, operational, strategic, and compliance. For each risk: probability (L/M/H), impact severity (L/M/H), risk score (probability × impact), specific mitigation strategies, required resources for mitigation, and the responsible owner. Format the output as a prioritized risk matrix with recommended actions."},
    {"phase": "4", "category": "Risk", "title": "Vague-language / scrutiny risk scan",
     "prompt": "Review the indexed scope/PWS for vague, consultative, or non-outcome-based language (assess, analyze, support, recommendations, strategic planning, evaluating, developing models, conducting research). Compute a high-risk-verbiage percentage = (high-risk term occurrences / total word count) × 100. Classify: >4% Critical, 2.5-4% High, 1-2.5% Moderate, <1% Low. Then compute a positive-verbiage percentage for outcome-based terms (readiness, capability, mission, deliverable, performance) using the same formula. Surface the most concerning paragraphs for rewrite or risk-section coverage."},

    # ═════════════════ Phase 5 — Proposal Development ═════════════════
    {"phase": "5", "category": "Traceability", "title": "Requirements → Deliverables → BOE",
     "prompt": "Trace every shall/will requirement to its satisfying deliverable, performance standard, and workload metric. Flag any requirement with no satisfying deliverable as a coverage gap, and any deliverable with no parent requirement as scope creep."},
    {"phase": "5", "category": "Writing", "title": "Volume outline (Shipley-aligned)",
     "prompt": "Produce a Shipley-aligned proposal volume outline. For each volume, list its sections, the page budget derived from the relevant proposal_instruction entities (UCF Section L or equivalent), the evaluation_factor entities it must answer (UCF Section M or equivalent — including adjectival or LPTA schemes), and the win theme(s) it should carry."},
    {"phase": "5", "category": "Writing", "title": "Executive summary intro (pain → value prop)",
     "prompt": "Write the executive summary introduction by opening with the customer's most painful problem (framed as a burning question), then present our value proposition as the solution to that problem, then introduce our win theme and the relevant capabilities that prove we can deliver. Use active voice, short sentences, and no jargon. Cite the source for each customer pain point."},
    {"phase": "5", "category": "Writing", "title": "Executive summary full draft",
     "prompt": "Draft a full executive summary: open with the customer's mission challenge, state our solution promise, surface three discriminators each backed by a quantified proof point, and close with a benefit-anchored call to action. Stay within the page limit imposed by the relevant proposal_instruction entities (UCF Section L or equivalent — may live inline in the PWS or in a named attachment for non-UCF solicitations); default to 4 pages if no limit is stated."},
    {"phase": "5", "category": "Writing", "title": "Section storyboard",
     "prompt": "Storyboard a single proposal section: the proposal_instruction it answers (UCF Section L or equivalent), the evaluation_factor entities it earns (UCF Section M or equivalent), the win theme it carries, the proof points it cites, the graphic concepts, and the action caption for each graphic. Include placeholder counts for words and graphics so authors can budget."},
    {"phase": "5", "category": "Writing", "title": "Why-What-Who-How-When-Where-Wow framework",
     "prompt": "Develop a proposal section using the Why-What-Who-How-When-Where-Wow framework. Step 1 (Why): introductory paragraphs framed by the highest inherent risk and how our approach mitigates it. Step 2 (What): paragraphs detailing the benefits of our approach. Step 3 (Who): a sentence (with placeholder for names) describing who performs the work and their roles. Step 4 (How): paragraphs diving into implementation detail, mapped to the relevant statement-of-work paragraphs. Step 5 (When/Where): schedule and place-of-performance integration. Step 6 (Wow): the discriminator that lifts this section above competitor responses."},
    {"phase": "5", "category": "Writing", "title": "Capability narrative (active voice, 200-250 words)",
     "prompt": "Generate a clear, concise, compelling response in active voice that showcases our capabilities in {capability}. Structure: (1) strong assertive opening (1-2 sentences); (2) 3-4 key capabilities or achievements with specific metrics or outcomes (bullets); (3) brief success-story example (3-4 sentences); (4) examples of programs/platforms where we have implemented {capability} (include legacy platforms); (5) forward-looking conclusion tying us to future challenges (1-2 sentences). Active voice throughout. No jargon. Short impactful sentences. 200-250 words total."},
    {"phase": "5", "category": "Writing", "title": "Past performance narrative",
     "prompt": "Turn our past performance around {capability} into a narrative that shows we are a strong vendor/partner selection for the customer agency. For each cited past performance: name the customer, the period, the scope and scale, the outcomes (quantified), and the direct relevance to this opportunity's requirements and evaluation factors."},
    {"phase": "5", "category": "Writing", "title": "Past performance ↔ requirement match",
     "prompt": "For requirement {requirement_id} (or every requirement if none specified): list the past performances that demonstrate we have done this before, what we delivered, the customer outcome, and the evidence we can cite. Flag requirements with no matching past performance as proof-point gaps."},
    {"phase": "5", "category": "Writing", "title": "Task-driven proposal section",
     "prompt": "For task {section_or_task}: construct a compelling proposal response with these elements integrated into a natural narrative — Task Number; Task Heading; our step-by-step approach (name specific tools/methods, identify analysis steps, name the customer organizations we coordinate with); Discriminators (unique qualities, methods, or partnerships); Features and benefits that exceed the task requirements (efficiency, alignment, sustainability, risk reduction, mission outcomes); Proof Points (past projects with quantified outcomes). Cite source paragraphs for each claim and label any AI-pre-existing-knowledge content separately from indexed-document content."},
    {"phase": "5", "category": "Writing", "title": "Convert structured response to paragraph",
     "prompt": "Convert the previous structured (heading + bullet) response into proposal-ready paragraph form. Preserve every claim, every metric, every citation. Use active voice. No section headings within the paragraphs except the task heading."},
    {"phase": "5", "category": "Writing", "title": "RFI question response",
     "prompt": "Respond to the RFI question: '{requirement_text}'. Use the indexed past-performance and capability content. Make the response substantive (not just keyword-checking), use the keywords once each, and add concrete examples, metrics, and past customer outcomes that demonstrate we have done this before."},
    {"phase": "5", "category": "Strategy", "title": "FAB chain for top discriminator",
     "prompt": "For our most defensible discriminator, write a Feature → Advantage → Benefit chain grounded in cited proof points and tied to the relevant evaluation_factor (UCF Section M or equivalent) and customer hot button."},
    {"phase": "5", "category": "Strategy", "title": "Strength & benefit identification (eval-anchored)",
     "prompt": "Identify 3-4 strengths in our draft that meet the formal definition: 'an aspect of the proposal that has merit or exceeds specified requirements in a way advantageous to the government during contract performance.' For each strength: name the unique capability/method/technology, cite the proposal text, tie it to the specific evaluation_factor it influences (UCF Section M or equivalent — including adjectival or LPTA schemes), and articulate the quantifiable benefit (positive outcome) the customer gains. A benefit must be tangible, tied to evaluation criteria, and not merely 'potential value.'"},
    {"phase": "5", "category": "Strategy", "title": "Strength/benefit conciseness rewrite",
     "prompt": "Rewrite the provided strengths and benefits to be clear, concise, and table-cell-sized while preserving every quantitative claim and tie-back to evaluation criteria. Distinguish whether each item is genuinely a strength versus a benefit and reorganize accordingly. Output ready for a strength table."},
    {"phase": "5", "category": "Risk", "title": "Risk to operations from requirements",
     "prompt": "Identify and describe requirements that may pose a risk to operations after award. For each: quote the source language, name the risk category (integration, security, dependency, methodology, scale, complexity, transition), describe how it would manifest, and propose the mitigation we will offer in our management volume."},

    # ═════════════════ Phase 6 — Color Reviews & Submittal ═════════════════
    {"phase": "6", "category": "Review", "title": "Pink team feedback prompts",
     "prompt": "Generate Pink team review prompts for each volume: are win themes visible, are discriminators substantiated with cited proof, are graphics earning their space (action captions tied to themes), is compliance language unambiguous, are FAB chains complete, is the customer's mission outcome the subject of the verbs?"},
    {"phase": "6", "category": "Review", "title": "Red team challenge questions",
     "prompt": "Generate Red team challenge questions a tough source-selection evaluator would ask. For each: point to the proposal section that should answer it and the specific proof point that should land it. Flag questions our current draft cannot answer."},
    {"phase": "6", "category": "Review", "title": "Red team rewrite (Shipley expert)",
     "prompt": "Act as a Shipley-process expert performing a Red team review. For each response: provide detailed strengths, detailed weaknesses, and specific recommendations. Then provide a rewritten version of the answer that incorporates the recommendations. The rewrite must use active voice, mirror the existing response tone, reference appropriate doctrine where relevant, avoid blustery or overly complex language, avoid language patterns that signal LLM-generated text, and avoid em-dashes/en-dashes. Recommendations must be unbiased and worded as recommendations (not as commitments we are making)."},
    {"phase": "6", "category": "Review", "title": "Gold team executive narrative check",
     "prompt": "Read the executive summary and management volume openers as a Gold team would. Flag any place the customer's mission outcome is not the subject of the verbs, where benefits are not quantified, where discriminators read as table stakes, or where compliance language is missing."},
    {"phase": "6", "category": "Review", "title": "Gap analysis vs evaluation factors",
     "prompt": "Run a gap analysis: for each evaluation_factor and subfactor (UCF Section M or equivalent — including adjectival or LPTA schemes), list the proposal sections, deliverables, and proof points that respond to it. Highlight unanswered factors, weakly-answered factors, and factors answered in the wrong volume."},
    {"phase": "6", "category": "Review", "title": "Compliance review checklist",
     "prompt": "Generate a Pink/Red-team-executable compliance review checklist organized by proposal_instruction (UCF Section L or equivalent), with the matching evaluation_factor pass/fail criteria (UCF Section M or equivalent), the responsible volume, and a column for reviewer pass/fail/comment."},
    {"phase": "6", "category": "Review", "title": "Strengths & benefits enhancement review",
     "prompt": "Review the draft strength table. For each row: assess whether the strength is genuinely advantageous to the customer (not just a feature), whether the benefit is tied to evaluation criteria, and whether the language is clear and concise. Provide specific suggestions: quantify outcomes, tighten unique-capability language, add a brief success story, detail forward benefits, and (if available) cite a customer testimonial. Output a revised, table-ready version."},
    {"phase": "6", "category": "Review", "title": "Reflect on win strategy",
     "prompt": "Review the win strategies and themes we've adopted. Identify any risks we haven't considered, opportunities we haven't pursued, competitor counter-moves we haven't anticipated, and proof gaps that would weaken the strategy under Red-team scrutiny."},
    {"phase": "6", "category": "Submission", "title": "Final compliance sweep",
     "prompt": "Final pre-submission sweep: confirm every proposal_instruction (UCF Section L or equivalent) is answered, every evaluation_factor (UCF Section M or equivalent — including adjectival or LPTA schemes) is addressed, every page limit is met, every required artifact (volumes, certifications, reps & certs, pricing, model contract, oral slides) is named, every cross-reference is intact, and every page footer/header complies with format constraints."},
]


# ---------------------------------------------------------------------------
# Stats helpers
# ---------------------------------------------------------------------------

def _safe_count_json_keys(path: Path) -> int:
    """Count records in a LightRAG storage JSON file. Returns 0 on any error.

    Handles two on-disk shapes used by LightRAG:
    - kv_store_*.json: top-level dict keyed by record id -> count via len(dict)
    - vdb_*.json:      {"embedding_dim": N, "data": [...records...], "matrix": "..."}
                       -> count via len(data)

    Results are cached by (path, mtime, size) so the multi-MB vdb files are
    only re-read when they actually change.
    """
    try:
        if not path.exists():
            return 0
        st = path.stat()
        key = (str(path), st.st_mtime_ns, st.st_size)
        cached = _COUNT_CACHE.get(key)
        if cached is not None:
            return cached
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            inner = data.get("data")
            count = len(inner) if isinstance(inner, list) else len(data)
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 0
        # Drop any prior cached entries for this path before storing the new one
        for k in [k for k in _COUNT_CACHE if k[0] == str(path)]:
            _COUNT_CACHE.pop(k, None)
        _COUNT_CACHE[key] = count
        return count
    except Exception:
        return 0


_COUNT_CACHE: dict[tuple[str, int, int], int] = {}


def _stack_versions() -> dict[str, Optional[str]]:
    """Read installed package versions for the engine stack. Cached at import."""
    global _STACK_CACHE  # noqa: PLW0603
    if _STACK_CACHE is not None:
        return _STACK_CACHE
    from importlib.metadata import PackageNotFoundError, version  # local

    out: dict[str, Optional[str]] = {}
    for key, dist in (
        ("lightrag", "lightrag-hku"),
        ("raganything", "raganything"),
        ("mineru", "mineru"),
        ("transformers", "transformers"),
    ):
        try:
            out[key] = version(dist)
        except PackageNotFoundError:
            try:
                out[key] = version(key)  # fall back to bare name
            except PackageNotFoundError:
                out[key] = None
    _STACK_CACHE = out
    return out


_STACK_CACHE: Optional[dict[str, Optional[str]]] = None


def _ui_chat_history_pairs() -> int:
    """Resolve the per-query conversation_history cap (in user+assistant pairs)."""
    try:
        return max(0, int(os.getenv("UI_CHAT_HISTORY_TURNS", "20")))
    except ValueError:
        return 20


def _gather_stats() -> dict[str, Any]:
    settings = get_settings()
    ws = _workspace_dir()
    inference_only_relationship_types = {"REQUIRES", "ENABLED_BY", "RESPONSIBLE_FOR"}
    return {
        "workspace": settings.workspace,
        "graph_storage": getattr(global_args, "graph_storage", "NetworkXStorage"),
        "working_dir": str(ws),
        "documents": _safe_count_json_keys(ws / "kv_store_doc_status.json"),
        "entities": _safe_count_json_keys(ws / "vdb_entities.json"),
        "relationships": _safe_count_json_keys(ws / "vdb_relationships.json"),
        "chunks": _safe_count_json_keys(ws / "vdb_chunks.json"),
        "chats": sum(1 for _ in _chats_dir().glob("*.json")),
        "chat": {
            # How many recent user+assistant pairs travel with each query.
            # Mirrored from UI_CHAT_HISTORY_TURNS so the chat header can render
            # an accurate "N turns in context" indicator.
            "history_pairs_cap": _ui_chat_history_pairs(),
        },
        "ontology": {
            "entity_type_count": len(VALID_ENTITY_TYPES),
            "relationship_type_count": len(VALID_RELATIONSHIP_TYPES),
            "extraction_relationship_type_count": len(
                VALID_RELATIONSHIP_TYPES - inference_only_relationship_types
            ),
        },
        "models": {
            "extraction": settings.extraction_llm_name,
            "reasoning": settings.reasoning_llm_name,
            "embedding": settings.embedding_model,
            "rerank": settings.rerank_model if settings.enable_rerank else None,
            "rerank_enabled": settings.enable_rerank,
        },
        "stack": _stack_versions(),
        "timestamp": _now_iso(),
    }


# ---------------------------------------------------------------------------
# Knowledge graph snapshot (workspace-scoped, backend-agnostic)
# ---------------------------------------------------------------------------

# Cap at 5000 nodes — beyond this Cytoscape/fcose becomes unusably slow in
# the browser even with WebGL. Bumped well above LightRAG's default 1000.
_GRAPH_HARD_CAP = 5000
_GRAPH_DEFAULT = 2000


def _json_safe(value: Any) -> Any:
    """Coerce neo4j/numpy/datetime values into JSON-serializable scalars."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    # neo4j.time.DateTime / Date / Time / Duration, numpy scalars, etc.
    for attr in ("isoformat", "iso_format", "to_native"):
        if hasattr(value, attr):
            try:
                v = getattr(value, attr)()
                if isinstance(v, datetime):
                    return v.isoformat()
                return _json_safe(v)
            except Exception:  # noqa: BLE001
                pass
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return None


async def _load_graph_neo4j(workspace: str, max_nodes: int, entity_type: Optional[str]) -> dict[str, Any]:
    """Pull a Cytoscape-friendly subgraph from Neo4j, top-degree nodes first."""
    from neo4j import AsyncGraphDatabase  # local import — neo4j is an optional dep

    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    label = workspace  # workspace is also the Neo4j label

    type_filter = ""
    params: dict[str, Any] = {"max_nodes": int(max_nodes)}
    if entity_type:
        type_filter = "WHERE toLower(n.entity_type) = toLower($etype)"
        params["etype"] = entity_type

    nodes_q = f"""
        MATCH (n:`{label}`)
        {type_filter}
        WITH n, COUNT {{ (n)--() }} AS degree
        ORDER BY degree DESC
        LIMIT $max_nodes
        RETURN elementId(n) AS nid, n AS node, degree
    """
    total_q = f"MATCH (n:`{label}`) {type_filter} RETURN count(n) AS total"
    edges_q = f"""
        MATCH (a:`{label}`)-[r]->(b:`{label}`)
        WHERE elementId(a) IN $ids AND elementId(b) IN $ids
        RETURN elementId(r) AS rid, elementId(a) AS src, elementId(b) AS tgt, type(r) AS rtype, properties(r) AS props
    """

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    try:
        async with driver.session(database=database, default_access_mode="READ") as session:
            total_res = await session.run(total_q, **({"etype": entity_type} if entity_type else {}))
            total = (await total_res.single())["total"]
            await total_res.consume()

            nodes_res = await session.run(nodes_q, **params)
            nodes_payload: list[dict[str, Any]] = []
            ids: list[str] = []
            async for rec in nodes_res:
                nid = rec["nid"]
                node = rec["node"]
                props = _json_safe(dict(node))
                ids.append(nid)
                nodes_payload.append({
                    "id": str(nid),
                    "labels": [str(props.get("entity_id", nid))],
                    "properties": {**props, "_degree": int(rec["degree"] or 0)},
                })
            await nodes_res.consume()

            edges_payload: list[dict[str, Any]] = []
            if ids:
                edges_res = await session.run(edges_q, ids=ids)
                async for rec in edges_res:
                    edges_payload.append({
                        "id": str(rec["rid"]),
                        "source": str(rec["src"]),
                        "target": str(rec["tgt"]),
                        "type": rec["rtype"],
                        "properties": _json_safe(dict(rec["props"] or {})),
                    })
                await edges_res.consume()
    finally:
        await driver.close()

    return {
        "backend": "neo4j",
        "workspace": workspace,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "total_nodes": int(total),
        "returned_nodes": len(nodes_payload),
        "returned_edges": len(edges_payload),
        "is_truncated": int(total) > len(nodes_payload),
    }


def _load_graph_networkx(workspace: str, max_nodes: int, entity_type: Optional[str]) -> dict[str, Any]:
    """Read graph_chunk_entity_relation.graphml directly and build a payload."""
    import networkx as nx  # already a transitive dep of LightRAG

    ws_dir = Path(global_args.working_dir) / workspace
    graphml = ws_dir / "graph_chunk_entity_relation.graphml"
    if not graphml.exists():
        return {
            "backend": "networkx",
            "workspace": workspace,
            "nodes": [],
            "edges": [],
            "total_nodes": 0,
            "returned_nodes": 0,
            "returned_edges": 0,
            "is_truncated": False,
        }

    g = nx.read_graphml(str(graphml))
    if entity_type:
        keep = [
            n for n, d in g.nodes(data=True)
            if str(d.get("entity_type", "")).lower() == entity_type.lower()
        ]
        g = g.subgraph(keep).copy()

    total = g.number_of_nodes()
    if total > max_nodes:
        # Top-degree subgraph
        top = sorted(g.degree(), key=lambda kv: kv[1], reverse=True)[:max_nodes]
        keep = [n for n, _ in top]
        g = g.subgraph(keep).copy()

    nodes_payload: list[dict[str, Any]] = []
    for n, d in g.nodes(data=True):
        props = _json_safe(dict(d))
        nodes_payload.append({
            "id": str(n),
            "labels": [str(props.get("entity_id", n))],
            "properties": {**props, "_degree": int(g.degree(n))},
        })
    edges_payload: list[dict[str, Any]] = []
    for i, (u, v, d) in enumerate(g.edges(data=True)):
        props = _json_safe(dict(d))
        rtype = props.pop("relationship_type", None) or props.get("keywords") or "RELATED_TO"
        edges_payload.append({
            "id": str(i),
            "source": str(u),
            "target": str(v),
            "type": str(rtype),
            "properties": props,
        })
    return {
        "backend": "networkx",
        "workspace": workspace,
        "nodes": nodes_payload,
        "edges": edges_payload,
        "total_nodes": int(total),
        "returned_nodes": len(nodes_payload),
        "returned_edges": len(edges_payload),
        "is_truncated": total > len(nodes_payload),
    }


# ---------------------------------------------------------------------------
# Workspace discovery & switching
# ---------------------------------------------------------------------------

def _discover_workspaces() -> list[dict[str, Any]]:
    """List candidate workspaces under the configured working_dir.

    A directory is considered a valid workspace if it contains at least one
    of the LightRAG storage signature files. We also report empty/new
    directories so the UI can show them.
    """
    root = Path(global_args.working_dir)
    if not root.exists():
        return []
    sig_files = ("kv_store_doc_status.json", "vdb_entities.json", "vdb_chunks.json")
    out: list[dict[str, Any]] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.name.startswith((".", "_")):
            continue
        has_data = any((child / f).exists() for f in sig_files)
        out.append({
            "name": child.name,
            "has_data": has_data,
            "documents": _safe_count_json_keys(child / "kv_store_doc_status.json"),
            "entities": _safe_count_json_keys(child / "vdb_entities.json"),
            "chats": sum(1 for _ in (child / "chats").glob("*.json")) if (child / "chats").exists() else 0,
        })
    return out


def _set_env_var(key: str, value: str) -> None:
    """Update or append KEY=value in the project .env file (atomic)."""
    env_path = Path.cwd() / ".env"
    lines: list[str] = []
    found = False
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            stripped = raw.lstrip()
            if stripped.startswith(f"{key}=") and not stripped.startswith("#"):
                lines.append(f"{key}={value}")
                found = True
            else:
                lines.append(raw)
    if not found:
        lines.append(f"{key}={value}")
    tmp = env_path.with_suffix(".env.tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp.replace(env_path)
    os.environ[key] = value
    reset_settings()


def _self_restart() -> None:
    """Re-exec the current python process with the same argv."""
    logger.warning("♻️  Re-execing process: %s %s", sys.executable, sys.argv)
    try:
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as exc:  # pragma: no cover
        logger.exception("Self-restart failed: %s", exc)
        os._exit(1)


# ---------------------------------------------------------------------------
# RFP Intelligence — L↔M matrix, traceability, coverage, gaps
# ---------------------------------------------------------------------------

def _load_vdb(name: str) -> list[dict[str, Any]]:
    """Load a vdb_*.json file's `data` array. Returns [] on any failure."""
    path = _workspace_dir() / name
    try:
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw.get("data") or []
    except Exception as exc:
        logger.warning("Failed reading %s: %s", path, exc)
        return []


def _split_keywords(value: Any) -> list[str]:
    """Relationship `keywords` is sometimes a comma/space-joined string."""
    if not value:
        return []
    if isinstance(value, list):
        return [str(v).strip().upper() for v in value if v]
    return [tok.strip().upper() for tok in re.split(r"[,\s]+", str(value)) if tok.strip()]


def _compute_intel() -> dict[str, Any]:
    """
    Build the RFP Intelligence rollup from the workspace's VDB JSON stores.

    Returns:
        {
            "lm_matrix":     [{instruction, evaluator, factor_id, ...}],
            "traceability":  [{requirement, deliverable, standard, metric}],
            "coverage":      [{factor, subfactors, instructions, deliverables, score}],
            "gaps":          {requirements_no_satisfaction: [...], factors_no_instruction: [...], deliverables_no_measure: [...]},
            "totals":        {entities, relationships, by_type: {...}},
        }
    """
    entities = _load_vdb("vdb_entities.json")
    relations = _load_vdb("vdb_relationships.json")

    # name → entity record (entity_id stored in `entity_name` or top-level keys)
    by_name: dict[str, dict[str, Any]] = {}
    for e in entities:
        name = e.get("entity_name") or e.get("entity_id") or e.get("__id__")
        if not name:
            continue
        by_name[str(name).strip()] = e

    # type buckets (lowercased entity_type)
    buckets: dict[str, list[str]] = {}
    for name, ent in by_name.items():
        t = (ent.get("entity_type") or "concept").lower()
        buckets.setdefault(t, []).append(name)

    # adjacency keyed by (src, tgt) → set of canonical relation types
    out_edges: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    in_edges: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
    for r in relations:
        s, t = r.get("src_id"), r.get("tgt_id")
        if not s or not t:
            continue
        types = _split_keywords(r.get("keywords") or r.get("relationship_type"))
        for rt in types:
            out_edges.setdefault(s, []).append((rt, t, r))
            in_edges.setdefault(t, []).append((rt, s, r))

    def _outgoing(name: str, rel: str) -> list[str]:
        return [t for (rt, t, _) in out_edges.get(name, []) if rt == rel]

    def _incoming(name: str, rel: str) -> list[str]:
        return [s for (rt, s, _) in in_edges.get(name, []) if rt == rel]

    def _summarize(name: str, n: int = 110) -> dict[str, Any]:
        ent = by_name.get(name) or {}
        desc = (ent.get("description") or ent.get("content") or "").strip().replace("\n", " ")
        return {
            "id": name,
            "type": (ent.get("entity_type") or "concept").lower(),
            "description": (desc[:n] + "…") if len(desc) > n else desc,
        }

    # --- L ↔ M matrix ----------------------------------------------------
    # Instructions GUIDES factors; factors EVALUATED_BY their evidence.
    # We surface: instruction → linked factor (or factor → guiding instruction).
    lm_rows: list[dict[str, Any]] = []
    instructions = sorted(buckets.get("proposal_instruction", []))
    for instr in instructions:
        guided = sorted(set(_outgoing(instr, "GUIDES") + _outgoing(instr, "EVALUATED_BY")))
        lm_rows.append({
            "instruction": _summarize(instr),
            "factors": [_summarize(f) for f in guided],
            "covered": bool(guided),
        })
    # Also surface factors with NO inbound instruction (gap signal)
    factor_names = sorted(set(buckets.get("evaluation_factor", []) + buckets.get("subfactor", [])))
    factor_rows: list[dict[str, Any]] = []
    for f in factor_names:
        guides = sorted(set(_incoming(f, "GUIDES") + _incoming(f, "EVALUATED_BY")))
        factor_rows.append({
            "factor": _summarize(f),
            "instructions": [_summarize(i) for i in guides],
            "covered": bool(guides),
        })

    # --- Traceability: requirement → deliverable → standard / metric -----
    trace_rows: list[dict[str, Any]] = []
    for req in sorted(buckets.get("requirement", [])):
        delivs = sorted(set(_outgoing(req, "SATISFIED_BY")))
        if not delivs:
            trace_rows.append({
                "requirement": _summarize(req),
                "deliverables": [],
                "standards": [],
                "metrics": [],
                "complete": False,
            })
            continue
        for d in delivs:
            stds = sorted(set(_outgoing(d, "MEASURED_BY")))
            mets = sorted(set(_outgoing(d, "TRACKED_BY") + _outgoing(d, "QUANTIFIES")))
            trace_rows.append({
                "requirement": _summarize(req),
                "deliverables": [_summarize(d)],
                "standards": [_summarize(s) for s in stds],
                "metrics": [_summarize(m) for m in mets],
                "complete": bool(stds or mets),
            })

    # --- Coverage heatmap by evaluation factor ---------------------------
    coverage_rows: list[dict[str, Any]] = []
    for f in sorted(buckets.get("evaluation_factor", [])):
        subs = sorted(set(_outgoing(f, "HAS_SUBFACTOR") + _outgoing(f, "CHILD_OF")))
        instrs = sorted(set(_incoming(f, "GUIDES")))
        # walk: factor → instruction → SATISFIED_BY deliverable
        delivs: set[str] = set()
        for i in instrs:
            for r in (by_name.get(i, {}),):  # placeholder
                pass
        # broader: any deliverable mentioning the factor via SUPPORTS / EVIDENCES / ADDRESSES
        for rel in ("SUPPORTS", "EVIDENCES", "ADDRESSES"):
            delivs.update(_incoming(f, rel))
        score = (1 if instrs else 0) + (1 if subs else 0) + (1 if delivs else 0)  # 0..3
        coverage_rows.append({
            "factor": _summarize(f),
            "subfactor_count": len(subs),
            "instruction_count": len(instrs),
            "evidence_count": len(delivs),
            "score": score,  # 0=red, 1=amber, 2=cyan, 3=lime
        })

    # --- Gaps -------------------------------------------------------------
    gaps_req: list[dict[str, Any]] = [
        _summarize(r) for r in sorted(buckets.get("requirement", []))
        if not _outgoing(r, "SATISFIED_BY")
    ]
    gaps_factor: list[dict[str, Any]] = [
        _summarize(f) for f in factor_names
        if not (_incoming(f, "GUIDES") or _incoming(f, "EVALUATED_BY"))
    ]
    gaps_deliv: list[dict[str, Any]] = [
        _summarize(d) for d in sorted(buckets.get("deliverable", []))
        if not (_outgoing(d, "MEASURED_BY") or _outgoing(d, "TRACKED_BY"))
    ]

    return {
        "generated_at": _now_iso(),
        "totals": {
            "entities": len(by_name),
            "relationships": len(relations),
            "by_type": {k: len(v) for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1]))},
        },
        "lm_matrix": {
            "instructions": lm_rows,
            "factors": factor_rows,
        },
        "traceability": trace_rows,
        "coverage": coverage_rows,
        "gaps": {
            "requirements_no_satisfaction": gaps_req,
            "factors_no_instruction": gaps_factor,
            "deliverables_no_measure": gaps_deliv,
        },
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

LlmFunc = Callable[[str], Awaitable[str]]


def register_ui(
    app: FastAPI,
    query_func: QueryFunc,
    data_func: QueryDataFunc | None = None,
    llm_func: LlmFunc | None = None,
) -> None:
    """
    Register the Project Theseus UI routes on an existing FastAPI app.

    Args:
        app: The FastAPI app produced by lightrag.api.lightrag_server.create_app.
        query_func: Async callable (query_text, mode, history, stream, overrides)
                    -> str | AsyncIterator[str]. The conversation_history is a
                    list of {role, content} dicts; when stream=True the return
                    is an async iterator of token chunks.
        data_func: Optional async callable (query_text, mode, history, overrides)
                    -> dict that returns LightRAG aquery_data structured retrieval
                    (chunks/entities/relationships/references). Used by the chat
                    SSE endpoint to emit a `sources` event before streaming the
                    answer. If None, no sources event is emitted.
    """
    if not _STATIC_DIR.exists():
        logger.warning("UI static dir missing: %s — UI will not be mounted", _STATIC_DIR)
        return

    # The Documents tab tails the active workspace's processing log file
    # (``rag_storage/<workspace>/<workspace>_processing.log``) — that file is
    # the long-lived audit trail and is workspace-scoped by design, which is
    # exactly the per-workspace activity view the UI wants.
    from src.server.workspace_log_tailer import (
        read_snapshot as _read_log_snapshot,
        stream_events as _stream_log_events,
    )

    query_settings = QuerySettingsStore(
        workspace_dir=_workspace_dir,
        settings_provider=get_settings,
    )
    chat_store = ChatStore(
        workspace_dir=_workspace_dir,
        now=_now_iso,
        history_pairs=_ui_chat_history_pairs,
    )

    # ---- Static SPA at /ui ------------------------------------------------
    app.mount(
        "/ui",
        StaticFiles(directory=str(_STATIC_DIR), html=True),
        name="theseus-ui",
    )

    # ---- Dashboard stats --------------------------------------------------
    @app.get("/api/ui/stats", tags=["theseus-ui"])
    async def ui_stats() -> JSONResponse:
        """Return dashboard rollup metrics for the active workspace."""
        return JSONResponse(_gather_stats())

    # ---- Processing log: snapshot + live stream --------------------------
    @app.get("/api/ui/processing-log", tags=["theseus-ui"])
    async def ui_processing_log_snapshot(limit: int = 500) -> JSONResponse:
        """Return the most-recent events from the workspace activity log.

        Reads from ``rag_storage/<workspace>/<workspace>_processing.log`` —
        the same log file that survives server restarts and is the canonical
        per-workspace audit trail. ``limit`` is clamped to [1, 2000].
        """
        snapshot = _read_log_snapshot(limit=limit)
        return JSONResponse(snapshot)

    @app.get("/api/ui/processing-log/stream", tags=["theseus-ui"])
    async def ui_processing_log_stream(limit: int = 200):
        """Stream new workspace-log events to the Documents tab via SSE.

        Sends an initial ``snapshot`` event with the recent entries, then one
        ``event`` per newly-appended entry as it's tailed off disk (~1.5s
        polling). 15s heartbeat comments keep idle proxies from disconnecting.
        """

        async def event_stream():
            try:
                yield "event: open\ndata: {}\n\n"
                async for item in _stream_log_events(initial_limit=limit):
                    if item["type"] == "snapshot":
                        yield (
                            "event: snapshot\ndata: "
                            + json.dumps(
                                {"events": item["events"], "path": item.get("path")}
                            )
                            + "\n\n"
                        )
                    elif item["type"] == "event":
                        yield (
                            "event: event\ndata: "
                            + json.dumps(item["event"])
                            + "\n\n"
                        )
                    else:  # ping
                        yield ": ping\n\n"
            except asyncio.CancelledError:
                # Client disconnected — let the generator unwind cleanly.
                raise

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",
            },
        )


    # ---- Prompt library ---------------------------------------------------
    @app.get("/api/ui/prompt-library", tags=["theseus-ui"])
    async def ui_prompt_library() -> JSONResponse:
        """Return the curated Shipley phase 4-6 suggested-prompt catalog."""
        return JSONResponse({"prompts": _PROMPT_LIBRARY})

    # ---- Chats: list/create ----------------------------------------------
    @app.get("/api/ui/chats", tags=["theseus-ui"])
    async def list_chats() -> JSONResponse:
        """List all saved chats for the active workspace, newest first."""
        return JSONResponse({"chats": chat_store.list_summaries()})

    @app.post("/api/ui/chats", tags=["theseus-ui"])
    async def create_chat(payload: ChatCreate) -> JSONResponse:
        """Create a new persistent chat session."""
        chat = chat_store.create(
            title=payload.title,
            mode=payload.mode,
            rfp_context=payload.rfp_context,
        )
        return JSONResponse(chat_store.summary(chat), status_code=201)

    # ---- Chats: read/update/delete ---------------------------------------
    @app.get("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def get_chat(chat_id: str) -> JSONResponse:
        """Return full chat including all messages."""
        return JSONResponse(chat_store.read(chat_id))

    @app.patch("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def update_chat(chat_id: str, payload: ChatUpdate) -> JSONResponse:
        """Rename a chat or update its mode / RFP context."""
        chat = chat_store.update(
            chat_id,
            title=payload.title,
            mode=payload.mode,
            rfp_context=payload.rfp_context,
        )
        return JSONResponse(chat_store.summary(chat))

    @app.delete("/api/ui/chats/{chat_id}", tags=["theseus-ui"])
    async def delete_chat(chat_id: str) -> JSONResponse:
        """Permanently delete a chat."""
        chat_store.delete(chat_id)
        return JSONResponse({"status": "deleted", "id": chat_id})

    # ---- Chats: send message (calls LightRAG /query under the hood) ------
    # LightRAG itself does NOT trim conversation_history (operate.py forwards
    # it raw to the LLM), so we cap here. The cap lives in
    # ``_ui_chat_history_pairs`` and is also surfaced via /api/ui/stats so the
    # chat header can render an accurate "N turns in context" indicator.

    @app.post("/api/ui/chats/{chat_id}/messages", tags=["theseus-ui"])
    async def post_message(chat_id: str, payload: ChatMessageCreate) -> JSONResponse:
        """Append a user message, invoke RAG query, persist the assistant reply."""
        chat = chat_store.read(chat_id)
        user_msg = {
            "role": "user",
            "content": payload.content,
            "ts": _now_iso(),
        }
        chat["messages"].append(user_msg)

        history = chat_store.build_history(chat, exclude_last=True)
        overrides = query_settings.build_overrides()
        try:
            answer = await query_func(
                payload.content, chat.get("mode", "mix"), history, False, overrides
            )
        except Exception as exc:
            logger.exception("Query failed for chat %s: %s", chat_id, exc)
            answer = f"⚠️ Query failed: {exc}"

        assistant_msg = {
            "role": "assistant",
            "content": strip_think(str(answer)),
            "ts": _now_iso(),
            "mode": chat.get("mode", "mix"),
        }
        chat["messages"].append(assistant_msg)
        chat["updated_at"] = _now_iso()

        # Auto-title the chat from the first user prompt.
        if chat.get("title") in (None, "", "New chat") and len(chat["messages"]) <= 2:
            chat_store.maybe_autotitle(chat, payload.content)

        chat_store.write(chat)
        return JSONResponse({
            "user": user_msg,
            "assistant": assistant_msg,
            "chat": chat_store.summary(chat),
        })

    # ---- Chats: streaming variant (Server-Sent Events) -------------------
    @app.post("/api/ui/chats/{chat_id}/messages/stream", tags=["theseus-ui"])
    async def post_message_stream(chat_id: str, payload: ChatMessageCreate):
        """Stream the assistant reply token-by-token via SSE.

        Event format (one SSE event per chunk):
            event: token
            data: {"text": "..."}

        Final event when complete:
            event: done
            data: {"assistant": {...full message...}, "chat": {...summary...}}

        Error event (terminal):
            event: error
            data: {"message": "..."}
        """
        chat = chat_store.read(chat_id)
        user_msg = {
            "role": "user",
            "content": payload.content,
            "ts": _now_iso(),
        }
        chat["messages"].append(user_msg)
        # Persist the user turn immediately so a dropped connection doesn't lose it.
        if chat.get("title") in (None, "", "New chat") and len(chat["messages"]) <= 1:
            chat_store.maybe_autotitle(chat, payload.content)
        chat_store.write(chat)

        history = chat_store.build_history(chat, exclude_last=True)
        mode = chat.get("mode", "mix")
        overrides = query_settings.build_overrides()

        async def event_stream():
            # SSE preamble keeps proxies from buffering and signals the client
            # that the stream is alive even before the first model token.
            yield "event: open\ndata: {}\n\n"
            # Tell the UI we're working on retrieval/rerank. LightRAG's aquery
            # does retrieval + rerank + first-token-prefill *before* it returns
            # the iterator, so this status covers that whole prep window.
            yield (
                "event: status\ndata: "
                + json.dumps({"phase": "retrieving", "label": "Retrieving context\u2026"})
                + "\n\n"
            )
            collected: list[str] = []
            stripper = ThinkStripper()
            t_start = time.perf_counter()
            t_first_token: float | None = None
            token_count = 0
            error_message: str | None = None
            sources_payload: dict | None = None
            try:
                # Pre-flight: fetch retrieved chunks/entities/relationships so
                # the UI can render a Sources panel and wire the inline citation
                # chips to actual source content. Failures here are non-fatal —
                # the answer still streams normally.
                if data_func is not None and mode != "bypass":
                    try:
                        data_result = await data_func(payload.content, mode, history, overrides)
                        if isinstance(data_result, dict) and data_result.get("status") == "success":
                            sources_payload = _trim_sources(data_result.get("data", {}))
                            yield (
                                "event: sources\ndata: "
                                + json.dumps(sources_payload)
                                + "\n\n"
                            )
                    except Exception as exc:  # noqa: BLE001
                        logger.warning(
                            "Sources pre-flight failed for chat %s: %s", chat_id, exc
                        )
                result = await query_func(payload.content, mode, history, True, overrides)
                retrieve_ms = int((time.perf_counter() - t_start) * 1000)
                # Iterator is in hand \u2014 LLM has started generating.
                yield (
                    "event: status\ndata: "
                    + json.dumps(
                        {
                            "phase": "generating",
                            "label": "Generating response\u2026",
                            "retrieve_ms": retrieve_ms,
                        }
                    )
                    + "\n\n"
                )
                if hasattr(result, "__aiter__"):
                    async for chunk in result:
                        if not chunk:
                            continue
                        text = stripper.feed(str(chunk))
                        if not text:
                            continue
                        if t_first_token is None:
                            t_first_token = time.perf_counter()
                        collected.append(text)
                        token_count += 1
                        yield f"event: token\ndata: {json.dumps({'text': text})}\n\n"
                    # Emit any trailing buffered text (e.g. final close tag absent).
                    tail = stripper.flush()
                    if tail:
                        if t_first_token is None:
                            t_first_token = time.perf_counter()
                        collected.append(tail)
                        token_count += 1
                        yield f"event: token\ndata: {json.dumps({'text': tail})}\n\n"
                else:
                    text = strip_think(str(result))
                    collected.append(text)
                    token_count = 1
                    t_first_token = time.perf_counter()
                    yield f"event: token\ndata: {json.dumps({'text': text})}\n\n"
            except Exception as exc:
                logger.exception("Streaming query failed for chat %s", chat_id)
                error_message = str(exc)
                yield f"event: error\ndata: {json.dumps({'message': error_message})}\n\n"
                # Persist the error so the chat reflects what the user saw.
                collected.append(f"\u26a0\ufe0f Query failed: {exc}")

            t_end = time.perf_counter()
            total_ms = int((t_end - t_start) * 1000)
            ttft_ms = (
                int((t_first_token - t_start) * 1000) if t_first_token else None
            )
            generate_ms = (
                int((t_end - t_first_token) * 1000) if t_first_token else None
            )

            full_text = "".join(collected)
            timing = {
                "total_ms": total_ms,
                "ttft_ms": ttft_ms,
                "generate_ms": generate_ms,
                "chunk_count": token_count,
                "char_count": len(full_text),
            }
            assistant_msg = {
                "role": "assistant",
                "content": full_text,
                "ts": _now_iso(),
                "mode": mode,
                "timing": timing,
            }
            if sources_payload is not None:
                assistant_msg["sources"] = sources_payload
            # Re-read so we don't clobber concurrent edits to the same chat file.
            try:
                latest = chat_store.read(chat_id)
            except HTTPException:
                latest = chat
            latest["messages"].append(assistant_msg)
            latest["updated_at"] = _now_iso()
            chat_store.write(latest)

            logger.info(
                "[chat] mode=%s ttft=%sms total=%sms chunks=%s chars=%s%s",
                mode,
                ttft_ms if ttft_ms is not None else "-",
                total_ms,
                token_count,
                len(full_text),
                f" error={error_message!r}" if error_message else "",
            )

            yield (
                "event: done\ndata: "
                + json.dumps(
                    {
                        "assistant": assistant_msg,
                        "chat": chat_store.summary(latest),
                        "timing": timing,
                    }
                )
                + "\n\n"
            )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-transform",
                "X-Accel-Buffering": "no",  # disable nginx buffering if proxied
                "Connection": "keep-alive",
            },
        )

    # ---- Entity → source chunks (for KG explorer click-through) ----------
    @app.get("/api/ui/entity/{name}/chunks", tags=["theseus-ui"])
    async def entity_chunks(name: str, limit: int = 8) -> JSONResponse:
        """Return the source text chunks that mention an entity, for KG drill-down."""
        ws = _workspace_dir()
        ec_path = ws / "kv_store_entity_chunks.json"
        tc_path = ws / "kv_store_text_chunks.json"
        if not ec_path.exists() or not tc_path.exists():
            return JSONResponse({"entity": name, "chunks": []})
        try:
            entity_chunks_map = json.loads(ec_path.read_text(encoding="utf-8"))
            text_chunks = json.loads(tc_path.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Failed reading chunk stores: %s", exc)
            return JSONResponse({"entity": name, "chunks": []})

        # entity_chunks_map can key by raw name or by quoted variants
        chunk_ids = (
            entity_chunks_map.get(name)
            or entity_chunks_map.get(name.strip('"'))
            or []
        )
        if isinstance(chunk_ids, dict):
            chunk_ids = list(chunk_ids.keys())

        out = []
        for cid in list(chunk_ids)[:limit]:
            chunk = text_chunks.get(cid) or {}
            content = chunk.get("content") or chunk.get("text") or ""
            out.append({
                "chunk_id": cid,
                "file_path": chunk.get("file_path") or chunk.get("full_doc_id"),
                "chunk_order_index": chunk.get("chunk_order_index"),
                "snippet": content[:600] + ("…" if len(content) > 600 else ""),
            })
        return JSONResponse({"entity": name, "chunks": out})

    # ---- RFP Intelligence (L↔M matrix, traceability, coverage, gaps) -----
    @app.get("/api/ui/intel/summary", tags=["theseus-ui"])
    async def intel_summary() -> JSONResponse:
        """Compute L↔M matrix, traceability chains, factor coverage, and gaps."""
        return JSONResponse(_compute_intel())

    # ---- Knowledge graph snapshot (workspace-scoped, sanitized) ----------
    @app.get("/api/ui/graph", tags=["theseus-ui"])
    async def ui_graph(
        max_nodes: int = _GRAPH_DEFAULT,
        entity_type: Optional[str] = None,
    ) -> JSONResponse:
        """Return a Cytoscape-friendly subgraph for the active workspace.

        Bypasses LightRAG's `/graphs` (which hard-caps at 1000 and is prone
        to serialization errors with non-JSON Neo4j property types). Reads
        directly from Neo4j or NetworkX based on GRAPH_STORAGE.

        Args:
            max_nodes: 1..5000 (default 2000). Top-degree nodes are kept.
            entity_type: Optional case-insensitive filter (e.g. "requirement").
        """
        try:
            cap = max(1, min(int(max_nodes), _GRAPH_HARD_CAP))
        except (TypeError, ValueError):
            cap = _GRAPH_DEFAULT
        ws = get_settings().workspace
        backend = (getattr(global_args, "graph_storage", "") or "").lower()
        try:
            if "neo4j" in backend:
                payload = await _load_graph_neo4j(ws, cap, entity_type)
            else:
                payload = _load_graph_networkx(ws, cap, entity_type)
            return JSONResponse(payload)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Graph snapshot failed for workspace=%s: %s", ws, exc)
            raise HTTPException(500, f"Graph snapshot failed: {exc}") from exc

    # ---- Workspaces (list / switch / restart) ------------------------------
    @app.get("/api/ui/workspaces", tags=["theseus-ui"])
    async def list_workspaces() -> JSONResponse:
        """List discovered workspace directories under rag_storage/."""
        return JSONResponse({
            "active": get_settings().workspace,
            "workspaces": _discover_workspaces(),
        })

    @app.post("/api/ui/workspaces/switch", tags=["theseus-ui"])
    async def switch_workspace(payload: WorkspaceSwitch) -> JSONResponse:
        """Persist WORKSPACE=<name> in .env and schedule a graceful self-restart.

        The server returns immediately and re-execs the python process ~750ms
        later so the response can flush. The browser polls /health and will
        reconnect when the new process is up.
        """
        name = payload.name.strip()
        if not _SAFE_WS.match(name):
            raise HTTPException(400, "Invalid workspace name (use alphanumerics, _, -)")
        existing = {w["name"] for w in _discover_workspaces()}
        if not payload.create and name not in existing:
            raise HTTPException(404, f"Workspace '{name}' does not exist")
        # Create folder if requested
        ws_root = Path(global_args.working_dir)
        ws_root.mkdir(parents=True, exist_ok=True)
        (ws_root / name).mkdir(parents=True, exist_ok=True)
        # Persist
        try:
            _set_env_var("WORKSPACE", name)
        except Exception as exc:
            raise HTTPException(500, f"Failed updating .env: {exc}") from exc
        # Schedule restart
        asyncio.get_event_loop().call_later(0.75, _self_restart)
        logger.warning("🔄 Workspace switch requested → '%s'. Restarting server…", name)
        return JSONResponse({
            "status": "restarting",
            "workspace": name,
            "message": "Server is restarting. The UI will reconnect automatically.",
        })

    # ---- Workspace inventory + deletion (Settings → Danger Zone) ---------
    #
    # The deletion paths intentionally reuse the same helpers as the
    # `tools/workspace_cleanup.py` CLI — no second implementation. That
    # keeps the two surfaces (CLI for ops, UI for end-users) in lockstep.

    def _ws_inventory() -> dict[str, Any]:
        """Combine rag_storage, Neo4j, and inputs/ views into one table."""
        from tools.workspace_cleanup import (
            _inputs_root,
            _inputs_workspaces,
            _neo4j_workspaces,
            _rag_storage_root,
            _storage_workspaces,
        )

        rag_root = _rag_storage_root()
        inputs_root = _inputs_root()
        storage_ws = _storage_workspaces(rag_root)
        inputs_ws = _inputs_workspaces(inputs_root)

        # Neo4j enumeration is best-effort — the driver may be unreachable in
        # NetworkX-only deployments. Fall back to an empty map so the UI can
        # still render rag_storage + inputs columns.
        neo4j_ws: dict[str, int] = {}
        backend = (getattr(global_args, "graph_storage", "") or "").lower()
        if "neo4j" in backend:
            try:
                from src.inference.neo4j_graph_io import Neo4jGraphIO

                io = Neo4jGraphIO()
                try:
                    neo4j_ws = _neo4j_workspaces(io)
                finally:
                    io.close()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Neo4j inventory failed: %s", exc)

        all_names = sorted(
            set(neo4j_ws) | set(storage_ws) | set(inputs_ws)
        )
        active = get_settings().workspace
        rows: list[dict[str, Any]] = []
        for name in all_names:
            inp = inputs_ws.get(name)
            rows.append({
                "name": name,
                "is_active": name == active,
                "neo4j_nodes": neo4j_ws.get(name, 0),
                "storage_mb": storage_ws.get(name),
                "inputs_files": inp[0] if inp else 0,
                "inputs_mb": inp[1] if inp else 0.0,
            })
        return {
            "active": active,
            "rag_storage_root": str(rag_root),
            "inputs_root": str(inputs_root),
            "neo4j_available": "neo4j" in backend,
            "workspaces": rows,
        }

    @app.get("/api/ui/workspaces/inventory", tags=["theseus-ui"])
    async def workspaces_inventory() -> JSONResponse:
        """Per-workspace inventory: Neo4j node count, rag_storage size, inputs/ files."""
        return JSONResponse(await asyncio.to_thread(_ws_inventory))

    def _delete_workspace_sync(
        name: str, scope: WorkspaceDeleteScope
    ) -> dict[str, Any]:
        """Worker thread: run the actual deletion using cleanup-tool helpers."""
        from tools.workspace_cleanup import (
            _delete_inputs_workspace,
            _delete_neo4j_workspace,
            _delete_storage_workspace,
            _inputs_root,
            _rag_storage_root,
        )

        result: dict[str, Any] = {"workspace": name, "deleted": {}}

        if scope.neo4j:
            backend = (getattr(global_args, "graph_storage", "") or "").lower()
            if "neo4j" in backend:
                try:
                    from src.inference.neo4j_graph_io import Neo4jGraphIO

                    io = Neo4jGraphIO()
                    try:
                        nodes = _delete_neo4j_workspace(io, name)
                        result["deleted"]["neo4j_nodes"] = nodes
                    finally:
                        io.close()
                except Exception as exc:  # noqa: BLE001
                    result["deleted"]["neo4j_error"] = str(exc)
            else:
                result["deleted"]["neo4j_skipped"] = "backend is not Neo4j"

        if scope.rag_storage:
            try:
                existed = _delete_storage_workspace(name, _rag_storage_root())
                result["deleted"]["rag_storage"] = existed
            except Exception as exc:  # noqa: BLE001
                result["deleted"]["rag_storage_error"] = str(exc)

        if scope.inputs:
            try:
                count, mb = _delete_inputs_workspace(name, _inputs_root())
                # Also drop the now-empty inputs/<ws>/ dir so it disappears
                # from the workspace list entirely.
                ws_inputs = _inputs_root() / name
                if ws_inputs.exists() and ws_inputs.is_dir() and not any(ws_inputs.iterdir()):
                    try:
                        ws_inputs.rmdir()
                    except OSError:
                        pass
                result["deleted"]["inputs_files"] = count
                result["deleted"]["inputs_mb"] = mb
            except Exception as exc:  # noqa: BLE001
                result["deleted"]["inputs_error"] = str(exc)

        return result

    @app.post("/api/ui/workspaces/{name}/delete", tags=["theseus-ui"])
    async def delete_workspace(
        name: str, scope: WorkspaceDeleteScope
    ) -> JSONResponse:
        """Delete one workspace's selected buckets (Neo4j / rag_storage / inputs).

        Refuses to delete the currently-active workspace — switch first.
        Source documents (`inputs/<ws>/`) are irrecoverable; the UI is
        responsible for surfacing a type-to-confirm guard before calling
        this endpoint with `inputs=true`.
        """
        if not _SAFE_WS.match(name):
            raise HTTPException(400, "Invalid workspace name (use alphanumerics, _, -)")
        if not (scope.neo4j or scope.rag_storage or scope.inputs):
            raise HTTPException(400, "At least one scope (neo4j/rag_storage/inputs) must be true.")
        if name == get_settings().workspace:
            raise HTTPException(
                409,
                "Cannot delete the active workspace. Switch to another workspace first.",
            )
        logger.warning(
            "🗑️  Deleting workspace '%s' (neo4j=%s, rag_storage=%s, inputs=%s)",
            name, scope.neo4j, scope.rag_storage, scope.inputs,
        )
        result = await asyncio.to_thread(_delete_workspace_sync, name, scope)
        return JSONResponse(result)

    @app.post("/api/ui/workspaces/wipe-all", tags=["theseus-ui"])
    async def wipe_all_workspaces(scope: WipeAllScope) -> JSONResponse:
        """Clean-slate wipe across every workspace. Requires confirm='DELETE ALL'.

        Triggers a server self-restart afterwards so the next boot lands on a
        clean state. The active workspace folder is recreated empty so the
        next process can start without crashing on a missing working dir.
        """
        if scope.confirm != "DELETE ALL":
            raise HTTPException(400, "Confirmation phrase must equal 'DELETE ALL'.")
        if not (scope.neo4j or scope.rag_storage or scope.inputs):
            raise HTTPException(400, "At least one scope (neo4j/rag_storage/inputs) must be true.")

        def _wipe_all_sync() -> dict[str, Any]:
            inv = _ws_inventory()
            names = [row["name"] for row in inv["workspaces"]]
            results: list[dict[str, Any]] = []
            per_scope = WorkspaceDeleteScope(
                neo4j=scope.neo4j,
                rag_storage=scope.rag_storage,
                inputs=scope.inputs,
            )
            for nm in names:
                results.append(_delete_workspace_sync(nm, per_scope))
            # Make sure the active workspace's rag_storage folder still
            # exists — LightRAG's storages assume it on next boot.
            try:
                from tools.workspace_cleanup import _rag_storage_root

                (_rag_storage_root() / get_settings().workspace).mkdir(
                    parents=True, exist_ok=True
                )
            except Exception:  # noqa: BLE001
                pass
            return {"deleted": results, "workspaces": len(results)}

        logger.warning(
            "🚨 WIPE ALL WORKSPACES requested (neo4j=%s, rag_storage=%s, inputs=%s)",
            scope.neo4j, scope.rag_storage, scope.inputs,
        )
        result = await asyncio.to_thread(_wipe_all_sync)
        # Restart so the UI reconnects to a clean process state.
        asyncio.get_event_loop().call_later(0.75, _self_restart)
        result["restarting"] = True
        return JSONResponse(result)

    @app.post("/api/ui/restart", tags=["theseus-ui"])
    async def restart_server() -> JSONResponse:
        """Schedule a graceful self-restart of the server process.

        Identical mechanism to the workspace switch: re-execs ~750ms after
        responding so the HTTP reply can flush. Browser polls /api/ui/stats
        and reconnects automatically.
        """
        asyncio.get_event_loop().call_later(0.75, _self_restart)
        logger.warning("🔄 Manual restart requested via Settings page.")
        return JSONResponse({
            "status": "restarting",
            "workspace": get_settings().workspace,
            "message": "Server is restarting. The UI will reconnect automatically.",
        })

    register_query_settings_routes(
        app,
        workspace_name=lambda: get_settings().workspace,
        store=query_settings,
    )

    register_skill_ui_routes(
        app,
        workspace_dir=_workspace_dir,
        data_func=data_func,
        llm_func=llm_func,
    )

    register_mcp_ui_routes(
        app,
        set_env_var=lambda key, value: _set_env_var(key, value),
        schedule_restart=lambda delay: asyncio.get_event_loop().call_later(
            delay, _self_restart
        ),
    )

    logger.info("✅ Project Theseus UI mounted at /ui (static: %s)", _STATIC_DIR)
