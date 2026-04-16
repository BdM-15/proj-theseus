"""
Test Query Prompt Enhancement (Branch 076)
==========================================
Sends targeted queries against a populated workspace to validate:
1. grok-4.20-0309-reasoning model works via xAI API
2. Shipley Mentor Framework produces mentoring-style responses
3. Proactive risk/opportunity flagging triggers
4. FAB chain, discriminator, and compliance matrix concepts appear naturally

Usage:
    python tools/test_query_prompt.py [--workspace WORKSPACE] [--mode MODE] [--query-id Q1]

Defaults to workspace 'afcap_iss_ls' with hybrid mode.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# ─── Setup ────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from src.core import get_settings
from src.extraction.output_sanitizer import create_sanitizing_wrapper
from prompts.govcon_prompt import GOVCON_PROMPTS
from lightrag.prompt import PROMPTS

# Apply GovCon prompts
PROMPTS.update(GOVCON_PROMPTS)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_query_prompt")


# ─── Test queries designed to exercise the mentor persona ─────────────────────

MENTOR_TEST_QUERIES = [
    {
        "id": "M1",
        "category": "Mentor - Non-Expert Guidance",
        "mode": "hybrid",
        "query": "I'm new to this solicitation. What are the most important things I should understand before we start writing our proposal?",
        "expect": "Should explain key concepts (evaluation factors, compliance requirements) in accessible language with Shipley methodology context",
    },
    {
        "id": "M2",
        "category": "Mentor - Strategic Interpretation",
        "mode": "hybrid",
        "query": "What do the evaluation factors tell us about what the government really cares about? How should that shape our proposal strategy?",
        "expect": "Should interpret factors strategically using Shipley concepts (hot buttons, discriminators, win themes), not just list them",
    },
    {
        "id": "M3",
        "category": "Mentor - Risk Identification",
        "mode": "hybrid",
        "query": "Are there any compliance risks or traps in the submission instructions that could get our proposal thrown out?",
        "expect": "Should proactively flag risks with **Risk:** markers, explain L↔M contradictions if present, mention 'ankle biters'",
    },
    {
        "id": "M4",
        "category": "Mentor - Win Theme Development",
        "mode": "global",
        "query": "Help me develop win themes for this pursuit. What discriminators should we emphasize based on the evaluation criteria?",
        "expect": "Should use precise Shipley definitions (discriminator = differs from competitor AND customer values it), FAB chain, theme statement structure",
    },
    {
        "id": "M5",
        "category": "Mentor - Cross-Reference Analysis",
        "mode": "hybrid",
        "query": "How do the Section L instructions map to Section M evaluation criteria? Where are the gaps or misalignments?",
        "expect": "Should explain compliance matrix concept, identify specific L↔M mappings, flag any contradictions with Risk markers",
    },
]


# ─── LightRAG instance creation (from compare_workspaces.py pattern) ─────────

async def create_rag_instance(workspace_name: str) -> tuple[LightRAG, str]:
    settings = get_settings()
    xai_api_key = settings.llm_binding_api_key
    xai_base_url = settings.llm_binding_host
    openai_api_key = settings.embedding_binding_api_key
    extraction_model = settings.extraction_llm_name
    reasoning_model = settings.reasoning_llm_name

    logger.info(f"Reasoning model: {reasoning_model}")
    logger.info(f"Extraction model: {extraction_model}")

    EXTRACTION_MARKERS = [
        "tuple_delimiter", "entity_types", "completion_delimiter",
        "record_delimiter", "-Real Data-", "extract entities",
    ]

    def is_extraction_task(prompt: str, system_prompt: str) -> bool:
        combined = f"{system_prompt or ''} {prompt or ''}".lower()
        return any(m.lower() in combined for m in EXTRACTION_MARKERS)

    async def base_llm_func(prompt, system_prompt=None, history_messages=[], **kwargs):
        model = extraction_model if is_extraction_task(prompt, system_prompt) else reasoning_model
        kwargs.setdefault("max_tokens", settings.llm_max_output_tokens)
        return await openai_complete_if_cache(
            model, prompt,
            system_prompt=system_prompt,
            history_messages=history_messages,
            api_key=xai_api_key,
            base_url=xai_base_url,
            **kwargs,
        )

    llm_func = create_sanitizing_wrapper(base_llm_func)

    from functools import partial
    embed_impl = getattr(openai_embed, "func", openai_embed)
    embed_fn = partial(
        embed_impl,
        model=settings.embedding_model,
        api_key=openai_api_key,
        base_url=settings.embedding_binding_host,
        max_token_size=8192,
    )
    embedding_func = EmbeddingFunc(
        embedding_dim=settings.embedding_dim,
        max_token_size=8192,
        func=embed_fn,
    )

    parent_dir = str(PROJECT_ROOT / "rag_storage")
    lightrag_kwargs = dict(
        working_dir=parent_dir,
        workspace=workspace_name,
        llm_model_func=llm_func,
        embedding_func=embedding_func,
    )

    use_graph_storage = settings.graph_storage or "NetworkXStorage"
    if use_graph_storage == "Neo4JStorage":
        try:
            import socket
            neo4j_host = (os.getenv("NEO4J_URI") or "bolt://localhost:7687").split("://")[-1].split(":")[0]
            neo4j_port = int((os.getenv("NEO4J_URI") or "bolt://localhost:7687").rsplit(":", 1)[-1].split("/")[0])
            with socket.create_connection((neo4j_host, neo4j_port), timeout=2):
                pass
        except (OSError, ValueError):
            logger.warning("Neo4J not reachable — falling back to NetworkXStorage")
            use_graph_storage = "NetworkXStorage"

    lightrag_kwargs["graph_storage"] = use_graph_storage
    rag = LightRAG(**lightrag_kwargs)
    await rag.initialize_storages()
    return rag, use_graph_storage


# ─── Quality assessment criteria for mentor persona ──────────────────────────

MENTOR_SIGNALS = {
    "shipley_terms": [
        "discriminator", "win theme", "theme statement", "hot button",
        "FAB", "feature", "advantage", "benefit", "compliance matrix",
        "color team", "ghost", "pink team", "red team", "gold team",
    ],
    "mentoring_language": [
        "this means", "the reason", "here's why", "what this tells us",
        "you should", "consider", "I'd recommend", "keep in mind",
        "in Shipley terms", "in practice", "the strategic implication",
        "important to understand", "worth noting",
    ],
    "risk_flags": [
        "Risk:", "Watch out:", "risk", "compliance trap", "ankle biter",
        "contradiction", "mismatch", "gap", "ambiguity", "clarification",
    ],
    "reasoning_chain": [
        "because", "therefore", "which means", "this suggests",
        "given that", "as a result", "the implication",
    ],
}


def assess_response(query_id: str, response: str) -> dict:
    """Score a response for mentor persona signals."""
    results = {}
    total_found = 0
    for category, terms in MENTOR_SIGNALS.items():
        found = [t for t in terms if t.lower() in response.lower()]
        results[category] = {"found": found, "count": len(found), "total": len(terms)}
        total_found += len(found)

    word_count = len(response.split())
    has_references = "### References" in response
    has_bold = "**" in response
    has_headers = response.count("##") >= 1

    return {
        "query_id": query_id,
        "word_count": word_count,
        "has_references": has_references,
        "has_bold_terms": has_bold,
        "has_headers": has_headers,
        "signals": results,
        "total_signals": total_found,
    }


# ─── Main ────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Test query prompt enhancement")
    parser.add_argument("--workspace", default="afcap_iss_ls", help="Workspace to query")
    parser.add_argument("--mode", default=None, help="Override query mode for all queries")
    parser.add_argument("--query-id", default=None, help="Run only a specific query (e.g. M1)")
    args = parser.parse_args()

    queries = MENTOR_TEST_QUERIES
    if args.query_id:
        queries = [q for q in queries if q["id"] == args.query_id]
        if not queries:
            logger.error(f"Query ID '{args.query_id}' not found. Available: {[q['id'] for q in MENTOR_TEST_QUERIES]}")
            sys.exit(1)

    logger.info(f"=" * 80)
    logger.info(f"Query Prompt Enhancement Test — Branch 076")
    logger.info(f"Workspace: {args.workspace} | Queries: {len(queries)}")
    logger.info(f"=" * 80)

    rag, graph_storage = await create_rag_instance(args.workspace)
    logger.info(f"Graph storage: {graph_storage}")

    results = []
    for q in queries:
        mode = args.mode or q["mode"]
        logger.info(f"\n{'─' * 80}")
        logger.info(f"[{q['id']}] {q['category']} | mode={mode}")
        logger.info(f"Query: {q['query']}")
        logger.info(f"Expect: {q['expect']}")
        logger.info(f"{'─' * 80}")

        param = QueryParam(mode=mode)
        t0 = time.perf_counter()
        try:
            answer = await rag.aquery(q["query"], param)
            elapsed = time.perf_counter() - t0

            # Print the full response
            print(f"\n{'=' * 80}")
            print(f"[{q['id']}] RESPONSE ({elapsed:.1f}s, {len(answer.split())} words):")
            print(f"{'=' * 80}")
            print(answer)
            print(f"{'=' * 80}\n")

            # Assess quality
            assessment = assess_response(q["id"], answer)
            assessment["elapsed"] = round(elapsed, 1)
            assessment["error"] = None
            results.append(assessment)

            # Print signal summary
            print(f"  Signals found: {assessment['total_signals']}")
            for cat, data in assessment["signals"].items():
                if data["found"]:
                    print(f"    {cat}: {', '.join(data['found'])}")

        except Exception as e:
            elapsed = time.perf_counter() - t0
            logger.error(f"[{q['id']}] ERROR after {elapsed:.1f}s: {e}")
            results.append({
                "query_id": q["id"],
                "elapsed": round(elapsed, 1),
                "error": str(e),
                "total_signals": 0,
            })

    # ─── Summary ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 80}")
    print("SUMMARY — Mentor Persona Quality Assessment")
    print(f"{'=' * 80}")
    print(f"{'ID':<6} {'Time':>6} {'Words':>7} {'Signals':>8} {'Refs':>5} {'Bold':>5} {'Error'}")
    print(f"{'─' * 60}")
    for r in results:
        if r.get("error"):
            print(f"{r['query_id']:<6} {r['elapsed']:>5.1f}s {'—':>7} {'—':>8} {'—':>5} {'—':>5} {r['error'][:40]}")
        else:
            print(f"{r['query_id']:<6} {r['elapsed']:>5.1f}s {r['word_count']:>7} {r['total_signals']:>8} {'✓' if r['has_references'] else '✗':>5} {'✓' if r['has_bold_terms'] else '✗':>5}")

    # Signal breakdown
    print(f"\nSignal Breakdown:")
    for cat in MENTOR_SIGNALS:
        total = sum(r["signals"][cat]["count"] for r in results if "signals" in r)
        print(f"  {cat}: {total} hits across {len(results)} queries")


if __name__ == "__main__":
    asyncio.run(main())
