"""
Workspace Comparison Tool
=========================
Compare two LightRAG workspaces to evaluate extraction quality differences.

Provides two analysis modes:
  1. Statistical analysis   - Entity/relationship counts by type, orphan detection,
                              cross-workspace overlap (no LLM required, fast)
  2. Query comparison       - Run standardized govcon queries against both workspaces,
                              compare answer quality (requires LLM access)

Usage:
    # Statistical only (fast, no LLM calls)
    python tools/compare_workspaces.py --stats-only

    # Full comparison (statistics + LLM queries)
    python tools/compare_workspaces.py

    # Custom workspaces
    python tools/compare_workspaces.py --ws-a afcapv_bos_i --ws-b afcapv_bos_i_t2

    # Single query test
    python tools/compare_workspaces.py --query "What are the evaluation factors?"
"""

from dotenv import load_dotenv
load_dotenv()

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lightrag import LightRAG, QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc

from src.core import get_settings
from src.extraction.output_sanitizer import create_sanitizing_wrapper

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("compare_workspaces")

# ─── Govcon test queries ─────────────────────────────────────────────────────

TEST_QUERIES = [
    {
        "id": "Q1",
        "category": "Entity Discovery",
        "mode": "hybrid",
        "query": "List all evaluation factors and their associated weights or scoring criteria.",
    },
    {
        "id": "Q2",
        "category": "Entity Discovery",
        "mode": "hybrid",
        "query": "What deliverables (CDRLs) are required under this contract? List them with their submission schedules.",
    },
    {
        "id": "Q3",
        "category": "Entity Discovery",
        "mode": "local",
        "query": "What performance metrics or quality thresholds are specified in the PWS?",
    },
    {
        "id": "Q4",
        "category": "Requirement Traceability",
        "mode": "hybrid",
        "query": "How do proposal_instruction items map to evaluation_factor entities (UCF Section L↔M or non-UCF equivalent)? Which instructions correspond to which evaluation factors?",
    },
    {
        "id": "Q5",
        "category": "Requirement Traceability",
        "mode": "global",
        "query": "Which PWS requirements have associated evaluation factors that will be scored during source selection?",
    },
    {
        "id": "Q6",
        "category": "Document Hierarchy",
        "mode": "local",
        "query": "What is the organizational structure of this RFP? List the major sections and their parent-child relationships.",
    },
    {
        "id": "Q7",
        "category": "Cross-Document",
        "mode": "global",
        "query": "What is the relationship between the PWS, the evaluation factors, and the submission instructions? How do they connect?",
    },
    {
        "id": "Q8",
        "category": "Cross-Document",
        "mode": "hybrid",
        "query": "What organizations or personnel types are mentioned and what are their contractual responsibilities?",
    },
    {
        "id": "Q9",
        "category": "Strategic",
        "mode": "global",
        "query": "What are the key discriminators for winning this competition? What aspects will the government emphasize in evaluation?",
    },
    {
        "id": "Q10",
        "category": "Compliance",
        "mode": "local",
        "query": "What mandatory clauses, regulations, or standards must the contractor comply with?",
    },
]


# ─── Statistical analysis ─────────────────────────────────────────────────────

def analyze_workspace_stats(ws_path: Path) -> dict:
    """Analyze a workspace's KV stores without LLM calls."""
    stats = {
        "workspace": ws_path.name,
        "exists": ws_path.exists(),
        "entities": {},
        "relationships": {},
        "total_entities": 0,
        "total_relationships": 0,
        "belongs_to_relationships": 0,
        "orphaned_entities": 0,
        "doc_count": 0,
        "chunk_count": 0,
        "llm_cache_entries": 0,
        "relationship_type_counts": {},
    }

    if not ws_path.exists():
        return stats

    # Count documents
    doc_status_path = ws_path / "kv_store_doc_status.json"
    if doc_status_path.exists():
        with open(doc_status_path, encoding="utf-8") as f:
            doc_status = json.load(f)
        stats["doc_count"] = len(doc_status)

    # Count chunks
    chunks_path = ws_path / "kv_store_text_chunks.json"
    if chunks_path.exists():
        with open(chunks_path, encoding="utf-8") as f:
            chunks = json.load(f)
        stats["chunk_count"] = len(chunks)

    # Analyze entities from VDB
    entities_vdb_path = ws_path / "vdb_entities.json"
    if entities_vdb_path.exists():
        with open(entities_vdb_path, encoding="utf-8") as f:
            vdb = json.load(f)
        entity_data = vdb.get("data", [])
        # data is a list of entity dicts in LightRAG 1.4.13+
        if isinstance(entity_data, list):
            for edata in entity_data:
                if isinstance(edata, dict):
                    etype = (edata.get("entity_type") or "unknown").lower().strip()
                    stats["entities"][etype] = stats["entities"].get(etype, 0) + 1
                    stats["total_entities"] += 1
        elif isinstance(entity_data, dict):
            for eid, edata in entity_data.items():
                if isinstance(edata, dict):
                    etype = (edata.get("entity_type") or "unknown").lower().strip()
                    stats["entities"][etype] = stats["entities"].get(etype, 0) + 1
                    stats["total_entities"] += 1

    # Analyze full_entities KV store for entity type breakdown
    full_entities_path = ws_path / "kv_store_full_entities.json"
    if full_entities_path.exists() and stats["total_entities"] == 0:
        with open(full_entities_path, encoding="utf-8") as f:
            full_ents = json.load(f)
        for doc_id, doc_data in full_ents.items():
            if isinstance(doc_data, dict):
                count = doc_data.get("count", 0)
                stats["total_entities"] += count

    # Analyze relationships from VDB
    rels_vdb_path = ws_path / "vdb_relationships.json"
    if rels_vdb_path.exists():
        with open(rels_vdb_path, encoding="utf-8") as f:
            vdb = json.load(f)
        rel_data = vdb.get("data", [])
        # data is a list of relationship dicts in LightRAG 1.4.13+
        if isinstance(rel_data, list):
            for rdata in rel_data:
                if isinstance(rdata, dict):
                    stats["total_relationships"] += 1
                    keywords = (rdata.get("keywords") or "").lower()
                    for kw in keywords.split(","):
                        kw = kw.strip()
                        if kw:
                            stats["relationship_type_counts"][kw] = (
                                stats["relationship_type_counts"].get(kw, 0) + 1
                            )
        elif isinstance(rel_data, dict):
            for rid, rdata in rel_data.items():
                if isinstance(rdata, dict):
                    stats["total_relationships"] += 1
                    keywords = (rdata.get("keywords") or "").lower()
                    for kw in keywords.split(","):
                        kw = kw.strip()
                        if kw:
                            stats["relationship_type_counts"][kw] = (
                                stats["relationship_type_counts"].get(kw, 0) + 1
                            )

    # Check full_relations for belongs_to count
    full_relations_path = ws_path / "kv_store_full_relations.json"
    if full_relations_path.exists():
        with open(full_relations_path, encoding="utf-8") as f:
            full_rels = json.load(f)
        total_rel_count = 0
        for doc_id, doc_data in full_rels.items():
            if isinstance(doc_data, dict):
                total_rel_count += doc_data.get("count", 0)
        if stats["total_relationships"] == 0:
            stats["total_relationships"] = total_rel_count

    # LLM cache entries
    cache_path = ws_path / "kv_store_llm_response_cache.json"
    if cache_path.exists():
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        stats["llm_cache_entries"] = len(cache)

    # Detect orphaned entities
    # An entity is orphaned if it appears in vdb_entities but not in vdb_relationships
    if stats["total_entities"] > 0 and rels_vdb_path.exists() and entities_vdb_path.exists():
        with open(entities_vdb_path, encoding="utf-8") as f:
            ents_vdb = json.load(f).get("data", [])
        with open(rels_vdb_path, encoding="utf-8") as f:
            rels_vdb = json.load(f).get("data", [])

        ents_list = ents_vdb if isinstance(ents_vdb, list) else list(ents_vdb.values())
        rels_list = rels_vdb if isinstance(rels_vdb, list) else list(rels_vdb.values())

        entity_names = set()
        for edata in ents_list:
            if isinstance(edata, dict):
                name = edata.get("entity_name")
                if name:
                    entity_names.add(name.lower())

        connected_entities = set()
        for rdata in rels_list:
            if isinstance(rdata, dict):
                src = rdata.get("src_id")
                tgt = rdata.get("tgt_id")
                if src:
                    connected_entities.add(src.lower())
                if tgt:
                    connected_entities.add(tgt.lower())

        orphans = entity_names - connected_entities
        stats["orphaned_entities"] = len(orphans)
        stats["orphan_rate"] = (
            f"{len(orphans) / len(entity_names) * 100:.1f}%" if entity_names else "N/A"
        )

    return stats


def print_stats_comparison(ws_a_stats: dict, ws_b_stats: dict, ws_a_label: str, ws_b_label: str):
    """Print a side-by-side statistics comparison."""
    print("\n" + "═" * 80)
    print("  WORKSPACE STATISTICS COMPARISON")
    print("═" * 80)
    print(f"  {'Metric':<40} {ws_a_label:>18} {ws_b_label:>18}")
    print("─" * 80)

    metrics = [
        ("Total Entities", "total_entities"),
        ("Total Relationships", "total_relationships"),
        ("Orphaned Entities", "orphaned_entities"),
        ("Orphan Rate", "orphan_rate"),
        ("Document Count", "doc_count"),
        ("Chunk Count", "chunk_count"),
        ("LLM Cache Entries", "llm_cache_entries"),
    ]

    for label, key in metrics:
        a_val = str(ws_a_stats.get(key, "N/A"))
        b_val = str(ws_b_stats.get(key, "N/A"))
        print(f"  {label:<40} {a_val:>18} {b_val:>18}")

    print("\n  Entity Type Breakdown:")
    print("─" * 80)
    all_types = sorted(set(list(ws_a_stats["entities"].keys()) + list(ws_b_stats["entities"].keys())))
    for etype in all_types:
        a_val = str(ws_a_stats["entities"].get(etype, 0))
        b_val = str(ws_b_stats["entities"].get(etype, 0))
        print(f"    {etype:<38} {a_val:>18} {b_val:>18}")

    print("\n  Top Relationship Keywords:")
    print("─" * 80)
    all_kw = {}
    for k, v in ws_a_stats["relationship_type_counts"].items():
        all_kw[k] = all_kw.get(k, [0, 0])
        all_kw[k][0] = v
    for k, v in ws_b_stats["relationship_type_counts"].items():
        all_kw[k] = all_kw.get(k, [0, 0])
        all_kw[k][1] = v
    # Sort by combined count descending
    sorted_kw = sorted(all_kw.items(), key=lambda x: x[1][0] + x[1][1], reverse=True)
    for kw, counts in sorted_kw[:20]:
        a_val = str(counts[0]) if counts[0] else "0"
        b_val = str(counts[1]) if counts[1] else "0"
        print(f"    {kw:<38} {a_val:>18} {b_val:>18}")

    print("═" * 80)


# ─── LightRAG instance factory ────────────────────────────────────────────────

async def create_lightrag_instance(workspace_name: str) -> LightRAG:
    """Create a read-only LightRAG instance for querying a workspace.

    Uses the server's canonical pattern:
      working_dir = rag_storage/ (parent)
      workspace   = workspace_name  (e.g. "afcapv_bos_i_t4")

    NanoVectorDB resolves data at rag_storage/<workspace_name>/vdb_*.json
    Neo4JStorage uses the workspace name as a Cypher label for isolation.
    Passing workspace explicitly overrides the WORKSPACE env-var.
    """
    settings = get_settings()

    xai_api_key = settings.llm_binding_api_key
    xai_base_url = settings.llm_binding_host
    openai_api_key = settings.embedding_binding_api_key
    extraction_model = settings.extraction_llm_name
    reasoning_model = settings.reasoning_llm_name

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

    # Use openai_embed.func (unwrapped) to avoid @wrap_embedding_func_with_attrs
    # dimension mismatch: openai_embed has embedding_dim=1536 hardcoded but we use
    # text-embedding-3-large (3072 dims). The inner EmbeddingFunc would see 3072/1536=2
    # vectors and raise "expected 1 got 2". Matches initialization.py pattern.
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

    # Parent dir — each workspace is a subdirectory of rag_storage/
    parent_dir = str(PROJECT_ROOT / "rag_storage")

    lightrag_kwargs: dict = dict(
        working_dir=parent_dir,
        workspace=workspace_name,  # Overrides WORKSPACE env-var; used by both NanoVectorDB
                                   # (path suffix) and Neo4JStorage (Cypher label)
        llm_model_func=llm_func,
        embedding_func=embedding_func,
    )
    # Wire graph storage to match server configuration (Neo4J or NetworkX).
    # If the configured storage is Neo4JStorage but the server is not running,
    # fall back to NetworkXStorage so the tool remains usable offline.
    use_graph_storage = settings.graph_storage or "NetworkXStorage"
    if use_graph_storage == "Neo4JStorage":
        try:
            import socket
            neo4j_host = (os.getenv("NEO4J_URI") or "bolt://localhost:7687").split("://")[-1].split(":")[0]
            neo4j_port = int((os.getenv("NEO4J_URI") or "bolt://localhost:7687").rsplit(":", 1)[-1].split("/")[0])
            with socket.create_connection((neo4j_host, neo4j_port), timeout=2):
                pass
        except (OSError, ValueError):
            logger.warning("Neo4J not reachable — falling back to NetworkXStorage (graph queries will use naive mode)")
            use_graph_storage = "NetworkXStorage"
    lightrag_kwargs["graph_storage"] = use_graph_storage

    rag = LightRAG(**lightrag_kwargs)
    await rag.initialize_storages()
    return rag, use_graph_storage


# ─── Query comparison ─────────────────────────────────────────────────────────

async def run_query_on_instance(
    rag: LightRAG, query: str, mode: str, label: str
) -> dict:
    """Run a single query and return the result."""
    param = QueryParam(mode=mode)
    t0 = time.perf_counter()
    try:
        answer = await rag.aquery(query, param)
        elapsed = time.perf_counter() - t0
        return {"label": label, "answer": answer, "elapsed": elapsed, "error": None}
    except Exception as e:
        elapsed = time.perf_counter() - t0
        return {"label": label, "answer": None, "elapsed": elapsed, "error": str(e)}


async def run_query_comparison(
    rag_a: LightRAG,
    rag_b: LightRAG,
    ws_a_label: str,
    ws_b_label: str,
    queries: list,
    output_path: Optional[Path] = None,
    naive_fallback: bool = False,
):
    """Run all test queries against both workspaces and compare results."""
    results = []

    for q in queries:
        qid = q["id"]
        cat = q["category"]
        mode = q["mode"]
        query_text = q["query"]

        print(f"\n  [{qid}] {cat}: {query_text[:60]}...")

        # Run sequentially to avoid EmbeddingFunc batch cross-contamination
        # (two concurrent LightRAG instances on the same event loop share the
        # embedding worker pool, causing "expected N vectors but got 2N" errors)
        print(f"    [{ws_a_label}] querying...", end="", flush=True)
        res_a = await run_query_on_instance(rag_a, query_text, mode, ws_a_label)
        print(f" done ({res_a['elapsed']:.1f}s)")
        print(f"    [{ws_b_label}] querying...", end="", flush=True)
        res_b = await run_query_on_instance(rag_b, query_text, mode, ws_b_label)
        print(f" done ({res_b['elapsed']:.1f}s)")

        results.append({
            "query": q,
            ws_a_label: res_a,
            ws_b_label: res_b,
        })

    # Save report
    if output_path is None:
        output_path = PROJECT_ROOT / f"tools/comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

    write_markdown_report(results, ws_a_label, ws_b_label, output_path, naive_fallback=naive_fallback)
    print(f"\n  Report saved: {output_path}")
    return results


def write_markdown_report(results: list, ws_a_label: str, ws_b_label: str, output_path: Path, naive_fallback: bool = False):
    """Write comparison results to a Markdown file."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        f"# Workspace Query Comparison Report",
        f"",
        f"**Generated:** {ts}  ",
        f"**Workspace A:** `{ws_a_label}`  ",
        f"**Workspace B:** `{ws_b_label}`  ",
        f"",
    ]
    if naive_fallback:
        lines += [
            f"> ⚠️ **Limitation:** Neo4J was not available. All queries ran in `naive` mode, which retrieves",
            f"> the same raw text chunks from both workspaces. Answer length differences reflect LLM",
            f"> temperature variance, **not** ontology quality differences. Rerun with Neo4J running",
            f"> to get meaningful `local`/`global`/`hybrid` comparisons using the entity graph.",
            f"",
        ]
    lines += [
        f"## Executive Summary",
        f"",
        f"| ID | Category | Mode | A Length | B Length | Winner |",
        f"|:---|:---------|:-----|:--------:|:--------:|:------:|",
    ]

    for r in results:
        q = r["query"]
        a_res = r.get(ws_a_label, {})
        b_res = r.get(ws_b_label, {})
        a_ans = a_res.get("answer") or ""
        b_ans = b_res.get("answer") or ""
        a_len = len(a_ans)
        b_len = len(b_ans)

        if a_res.get("error"):
            winner = "B (A error)"
        elif b_res.get("error"):
            winner = "A (B error)"
        elif abs(a_len - b_len) < 100:
            winner = "≈ tie"
        elif a_len > b_len:
            winner = f"A (+{a_len - b_len} chars)"
        else:
            winner = f"B (+{b_len - a_len} chars)"

        lines.append(
            f"| {q['id']} | {q['category']} | `{q['mode']}` | {a_len} | {b_len} | {winner} |"
        )

    lines += ["", "---", ""]

    for r in results:
        q = r["query"]
        a_res = r.get(ws_a_label, {})
        b_res = r.get(ws_b_label, {})

        lines += [
            f"## {q['id']}: {q['category']}",
            f"",
            f"**Query ({q['mode']} mode):** {q['query']}",
            f"",
            f"### {ws_a_label}",
            f"",
        ]

        if a_res.get("error"):
            lines.append(f"> ❌ Error: {a_res['error']}")
        else:
            ans = a_res.get("answer", "")
            lines.append(ans if ans else "_No response_")

        lines += [
            f"",
            f"*Response time: {a_res.get('elapsed', 0):.1f}s*",
            f"",
            f"### {ws_b_label}",
            f"",
        ]

        if b_res.get("error"):
            lines.append(f"> ❌ Error: {b_res['error']}")
        else:
            ans = b_res.get("answer", "")
            lines.append(ans if ans else "_No response_")

        lines += [
            f"",
            f"*Response time: {b_res.get('elapsed', 0):.1f}s*",
            f"",
            f"---",
            f"",
        ]

    output_path.write_text("\n".join(lines), encoding="utf-8")


# ─── CLI entrypoint ──────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Compare LightRAG workspace extraction quality")
    parser.add_argument(
        "--ws-a",
        default="afcapv_bos_i",
        help="Workspace A name (default: afcapv_bos_i)",
    )
    parser.add_argument(
        "--ws-b",
        default="afcapv_bos_i_t2",
        help="Workspace B name (default: afcapv_bos_i_t2)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Only run statistical analysis (no LLM calls)",
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Run a single custom query against both workspaces",
    )
    parser.add_argument(
        "--mode",
        default="hybrid",
        choices=["hybrid", "global", "local", "naive"],
        help="Query mode when using --query (default: hybrid)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output Markdown report path",
    )
    args = parser.parse_args()

    rag_storage = PROJECT_ROOT / "rag_storage"
    ws_a_path = rag_storage / args.ws_a
    ws_b_path = rag_storage / args.ws_b

    # ── Statistical analysis ──
    print(f"\n📊 Analyzing workspace statistics...")
    ws_a_stats = analyze_workspace_stats(ws_a_path)
    ws_b_stats = analyze_workspace_stats(ws_b_path)
    print_stats_comparison(ws_a_stats, ws_b_stats, args.ws_a, args.ws_b)

    if args.stats_only:
        return

    # ── Query comparison ──
    print(f"\n🔍 Initializing LightRAG instances...")
    rag_a, graph_storage_a = await create_lightrag_instance(args.ws_a)
    rag_b, graph_storage_b = await create_lightrag_instance(args.ws_b)
    graph_storage_used = graph_storage_a  # Both use the same setting
    print(f"  ✅ {args.ws_a} ready  (graph: {graph_storage_used})")
    print(f"  ✅ {args.ws_b} ready")

    # When graph storage is NetworkX with an empty graphml, local/global/hybrid
    # queries all return 0 context because the graph was never persisted there
    # (production uses Neo4J). Fall back to naive mode so queries return real answers.
    use_naive_fallback = (graph_storage_used == "NetworkXStorage")
    if use_naive_fallback:
        print("  ⚠️  Graph storage is NetworkX (no persisted graph) — query modes downgraded to 'naive'")
        print("  ℹ️  NOTE: naive mode retrieves identical text chunks from both workspaces.")
        print("       Answer differences reflect LLM variance, not ontology quality.")
        print("       Start Neo4J and rerun to get meaningful local/global/hybrid comparisons.")

    if args.query:
        mode = args.mode if not use_naive_fallback else "naive"
        custom_q = [{"id": "CQ", "category": "Custom", "mode": mode, "query": args.query}]
        queries = custom_q
    else:
        if use_naive_fallback:
            queries = [{**q, "mode": "naive"} for q in TEST_QUERIES]
        else:
            queries = TEST_QUERIES

    output_path = Path(args.output) if args.output else None
    print(f"\n⚡ Running {len(queries)} queries against both workspaces...")
    try:
        await run_query_comparison(rag_a, rag_b, args.ws_a, args.ws_b, queries, output_path, naive_fallback=use_naive_fallback)
    finally:
        await rag_a.finalize_storages()
        await rag_b.finalize_storages()


if __name__ == "__main__":
    asyncio.run(main())
