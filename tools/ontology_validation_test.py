"""
Ontology usefulness smoke test.

Runs a spread of queries that each exercise a different ontology surface
and writes answers + signal-scan results to a markdown report.
Workspace is read from the WORKSPACE env var (default: afcapv_bos_i_t11).
"""
from dotenv import load_dotenv
load_dotenv()

import json
import os
import re
import sys
import time
from pathlib import Path

import requests

BASE = "http://localhost:9621"
WORKSPACE = os.environ.get("WORKSPACE", "afcapv_bos_i_t11")
OUT = Path(f"tools/ontology_validation_report_{WORKSPACE}.md")

QUERIES = [
    {
        "id": "Q1-ComplianceMatrix",
        "target_modules": ["shipley", "evaluation", "regulations"],
        "mode": "hybrid",
        "query": (
            "Build me the start of a compliance matrix for this RFP. "
            "Pull every Section L submission instruction and map it to the Section M "
            "evaluation factor/subfactor it supports. Flag any L instruction that has "
            "no M hook and any M factor with no L instruction."
        ),
    },
    {
        "id": "Q2-LtoM-Traceability",
        "target_modules": ["shipley", "evaluation"],
        "mode": "hybrid",
        "query": (
            "Walk me through how Section L Factor 1 (Mission Capability) instructions "
            "connect to the Section M evaluation subfactors. Call out specific subfactor "
            "numbers (1.1, 1.2, 1.3) and the page-limit / format rules the proposal must honor."
        ),
    },
    {
        "id": "Q3-WinThemes-InScope",
        "target_modules": ["shipley", "lessons_learned", "company_capabilities"],
        "mode": "hybrid",
        "query": (
            "Based on this RFP, draft three candidate win themes. For each theme apply the "
            "Explicit Benefit Linkage Rule: tie a KBR platform or proof point to a specific "
            "RFP requirement and show the quantified benefit the evaluator will see. No market-hype adjectives."
        ),
    },
    {
        "id": "Q4-BOE-Pricing",
        "target_modules": ["workload", "regulations"],
        "mode": "hybrid",
        "query": (
            "I'm writing the cost volume. Summarize the workload drivers (FTEs, labor categories, "
            "hours, CLINs, option years) and the FAR cost-principle constraints I have to honor "
            "when building the basis of estimate. Where are the indirect-rate and transition-pricing traps?"
        ),
    },
    {
        "id": "Q5-ComplianceClauses",
        "target_modules": ["regulations"],
        "mode": "local",
        "query": (
            "List every FAR/DFARS clause cited in this RFP and group them by purpose "
            "(ordering/IDIQ, labor/trafficking, small business, data rights, security). "
            "For each group say what the proposal team has to produce to comply."
        ),
    },
    {
        "id": "Q6-OutOfScope-BidNoBid",
        "target_modules": ["scope_enforcement"],
        "mode": "hybrid",
        "query": (
            "Should we bid this opportunity? Give me a Pwin estimate and a bid/no-bid recommendation."
        ),
    },
    {
        "id": "Q7-LessonsLearned",
        "target_modules": ["lessons_learned", "shipley"],
        "mode": "global",
        "query": (
            "What are the top three anti-patterns I need to avoid when writing the Mission Essential "
            "Plan and Quality Control Plan for this BOS-I procurement? Reference debrief lessons, "
            "weak-claim patterns, and what evaluators specifically do NOT infer."
        ),
    },
    {
        "id": "Q8-DeliverablesCDRLs",
        "target_modules": ["shipley", "workload"],
        "mode": "local",
        "query": (
            "List the CDRLs this contract requires, their submission cadence, and which PWS tasks "
            "they support. Call out the top three CDRLs that carry the most proposal-writing risk and why."
        ),
    },
]

# ─── Signal scan ───────────────────────────────────────────────────────────────

SIGNALS = {
    "shipley_terms": [
        r"compliance matrix", r"win theme", r"discriminator", r"proof point",
        r"ghost", r"FAB", r"feature.*advantage.*benefit", r"color team",
        r"pink team", r"red team", r"gold team", r"orange team", r"black hat",
        r"storyboard", r"action caption", r"executive summary",
        r"Section [LM]", r"Factor [0-9]", r"Subfactor",
    ],
    "regulations": [
        r"FAR [0-9]+\.[0-9]+", r"DFARS", r"FAR 52\.", r"CDRL", r"NAICS",
        r"section 889", r"section 508", r"FAR 15\.",
    ],
    "mentoring_language": [
        r"\brecommend\b", r"\bconsider\b", r"\btrap\b", r"\brisk\b",
        r"\bevaluator", r"\bhere'?s (how|why|what)", r"\bavoid\b",
        r"the key is", r"watch out", r"pitfall",
    ],
    "quantified_benefits": [
        r"\b[0-9]+%", r"\$[0-9]", r"\b[0-9]+\s*(hours|FTE|days|months)",
        r"\breduce[ds]?\s+(by\s+)?[0-9]",
    ],
    "scope_enforcement": [
        r"(out of scope|outside.*scope|not.*theseus|phase [0-3]|capture phase|pre-RFP|pre-rfp)",
        r"(bid.?no.?bid|P\.?win|competitive intel)",
    ],
    "explicit_benefit_rule": [
        r"Explicit Benefit Linkage",
        r"evaluators? (do )?not (infer|assume)",
        r"quantified benefit",
        r"tie[sd]? (back )?to (a )?(requirement|RFP)",
    ],
    "hallucination_flags": [
        r"I don'?t (know|have)", r"insufficient (information|context)",
        r"not (found|mentioned|available) in (the )?(RFP|document|knowledge)",
    ],
}


def scan_signals(text: str) -> dict:
    if not text:
        return {k: 0 for k in SIGNALS}
    out = {}
    for k, patterns in SIGNALS.items():
        hits = 0
        for p in patterns:
            hits += len(re.findall(p, text, re.IGNORECASE))
        out[k] = hits
    return out


def post_query(query: str, mode: str, timeout: int = 180) -> dict:
    """Call the running server's /query endpoint."""
    url = f"{BASE}/query"
    payload = {"query": query, "mode": mode}
    t0 = time.perf_counter()
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        elapsed = time.perf_counter() - t0
        if r.status_code != 200:
            return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:300]}", "elapsed": elapsed}
        data = r.json()
        # Response shape: {"response": "..."}
        return {"ok": True, "answer": data.get("response", ""), "elapsed": elapsed}
    except Exception as e:
        return {"ok": False, "error": str(e), "elapsed": time.perf_counter() - t0}


def main():
    print(f"Running {len(QUERIES)} queries against {BASE} (workspace {WORKSPACE})...\n")
    results = []
    for q in QUERIES:
        print(f"[{q['id']}] ({q['mode']}) ... ", end="", flush=True)
        res = post_query(q["query"], q["mode"])
        if res["ok"]:
            signals = scan_signals(res["answer"])
            print(f"done in {res['elapsed']:.1f}s  len={len(res['answer'])}  signals={signals}")
        else:
            print(f"FAIL ({res['elapsed']:.1f}s): {res['error'][:120]}")
            signals = {}
        results.append({"q": q, "res": res, "signals": signals})

    # Write markdown report
    OUT.parent.mkdir(exist_ok=True, parents=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write(f"# Ontology Validation Report — {WORKSPACE}\n\n")
        f.write(f"Queries: {len(QUERIES)}  |  Endpoint: {BASE}\n\n")
        f.write("## Signal Summary\n\n")
        f.write("| ID | Mode | Targets | Time | Len | Shipley | Reg | Mentor | Quant | Scope | Benefit | Halluc |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for r in results:
            q = r["q"]; res = r["res"]; s = r["signals"]
            if not res["ok"]:
                f.write(f"| {q['id']} | {q['mode']} | {','.join(q['target_modules'])} | FAIL | - | - | - | - | - | - | - | - |\n")
                continue
            f.write(
                f"| {q['id']} | {q['mode']} | {','.join(q['target_modules'])} | {res['elapsed']:.0f}s | "
                f"{len(res['answer'])} | {s.get('shipley_terms',0)} | {s.get('regulations',0)} | "
                f"{s.get('mentoring_language',0)} | {s.get('quantified_benefits',0)} | "
                f"{s.get('scope_enforcement',0)} | {s.get('explicit_benefit_rule',0)} | "
                f"{s.get('hallucination_flags',0)} |\n"
            )
        f.write("\n---\n\n")
        for r in results:
            q = r["q"]; res = r["res"]
            f.write(f"## {q['id']} — {q['mode']}\n\n")
            f.write(f"**Target modules:** {', '.join(q['target_modules'])}\n\n")
            f.write(f"**Query:** {q['query']}\n\n")
            if not res["ok"]:
                f.write(f"**ERROR:** {res['error']}\n\n")
                continue
            f.write(f"**Elapsed:** {res['elapsed']:.1f}s  |  **Length:** {len(res['answer'])} chars\n\n")
            f.write(f"**Signals:** `{json.dumps(r['signals'])}`\n\n")
            f.write("**Answer:**\n\n")
            f.write(res["answer"])
            f.write("\n\n---\n\n")
    print(f"\n✅ Report written: {OUT}")


if __name__ == "__main__":
    main()
