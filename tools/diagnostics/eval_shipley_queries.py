"""
Shipley / GovCon query evaluation harness (HTTP).

Purpose:
- Run a curated set of capture/proposal questions against a running LightRAG/RAGAnything server
- Save answers for manual review and regression comparisons

This is intentionally "thin": it does not require Neo4j locally and does not score with an LLM.
It is designed to support before/after comparisons when you change ontology/extraction/query settings.

Usage:
  python3 tools/diagnostics/eval_shipley_queries.py

Environment:
  LIGHTRAG_HOST=localhost
  LIGHTRAG_PORT=9621
  LIGHTRAG_ENDPOINT=/query          # try /query first; falls back to /chat and /ask
  LIGHTRAG_MODE=hybrid              # typical: hybrid | vector | graph
  LIGHTRAG_TIMEOUT_SECONDS=120
  LIGHTRAG_OUTFILE=logs/query_eval_shipley.json
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SHIPLEY_EVAL_QUERIES: List[Dict[str, Any]] = [
    {
        "id": "shipley-01-opportunity-summary",
        "query": "Summarize the opportunity: customer, scope, period of performance, and key constraints. Cite the exact sections/attachments.",
        "expects": ["section", "attachment", "period", "POP", "shall"],
    },
    {
        "id": "shipley-02-bid-no-bid",
        "query": "What are the top 10 bid/no-bid drivers (must-win requirements, gating clauses, resourcing, schedule risk)? Provide evidence and citations.",
        "expects": ["risk", "requirement", "clause", "deadline"],
    },
    {
        "id": "shipley-03-eval-to-win",
        "query": "What are the evaluation factors and how should we win each one? Map each factor to proposed discriminators and evidence we should include.",
        "expects": ["evaluation", "factor", "discriminator", "evidence"],
    },
    {
        "id": "shipley-04-l-to-m",
        "query": "Build a compliance matrix mapping Section L submission instructions to Section M evaluation criteria. Include any page limits or volume instructions.",
        "expects": ["section l", "section m", "page", "volume", "guides"],
    },
    {
        "id": "shipley-05-win-themes",
        "query": "List the strongest win themes and discriminators implied by the RFP (mission needs, pain points, hot buttons). Cite where each is supported.",
        "expects": ["win theme", "hot button", "discriminator"],
    },
    {
        "id": "shipley-06-risks",
        "query": "Identify the top risks (technical, schedule, compliance, staffing) and propose mitigations tied to specific requirements/clauses.",
        "expects": ["risk", "mitigation", "clause", "requirement"],
    },
    {
        "id": "shipley-07-color-reviews",
        "query": "Propose a Shipley color-team plan (Pink/Red/Gold) for this RFP with review objectives and artifacts (compliance matrix, storyboard, solution outline).",
        "expects": ["pink", "red", "gold", "compliance", "storyboard"],
    },
]


@dataclass(frozen=True)
class EndpointAttempt:
    url: str
    status: str
    error: Optional[str] = None


def _post_json(url: str, payload: Dict[str, Any], timeout_s: int) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=timeout_s) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Some deployments return plain text; normalize.
            return {"raw": raw}


def _extract_answer(response_json: Dict[str, Any]) -> str:
    # Best-effort extraction across common LightRAG/RAGAnything response shapes.
    for key in ("answer", "response", "result", "data", "raw"):
        if key in response_json and isinstance(response_json[key], str):
            return response_json[key]
    # Fall back to JSON string for inspection.
    return json.dumps(response_json, indent=2)[:20000]


def _run_query(
    host: str,
    port: int,
    mode: str,
    timeout_s: int,
    endpoint_override: Optional[str],
    query: str,
) -> Dict[str, Any]:
    endpoints_to_try = []
    if endpoint_override:
        endpoints_to_try.append(endpoint_override)
    endpoints_to_try.extend(["/query", "/chat", "/ask"])

    payload = {"query": query, "mode": mode}
    attempts: List[EndpointAttempt] = []

    for ep in endpoints_to_try:
        url = f"http://{host}:{port}{ep}"
        try:
            resp = _post_json(url, payload=payload, timeout_s=timeout_s)
            attempts.append(EndpointAttempt(url=url, status="ok"))
            return {"ok": True, "endpoint": ep, "url": url, "response": resp, "attempts": [a.__dict__ for a in attempts]}
        except HTTPError as e:
            attempts.append(EndpointAttempt(url=url, status="http_error", error=str(e)))
        except URLError as e:
            attempts.append(EndpointAttempt(url=url, status="url_error", error=str(e)))
        except Exception as e:
            attempts.append(EndpointAttempt(url=url, status="error", error=f"{type(e).__name__}: {e}"))

    return {"ok": False, "attempts": [a.__dict__ for a in attempts]}


def main() -> int:
    host = os.getenv("LIGHTRAG_HOST", "localhost")
    port = int(os.getenv("LIGHTRAG_PORT", "9621"))
    mode = os.getenv("LIGHTRAG_MODE", "hybrid")
    endpoint = os.getenv("LIGHTRAG_ENDPOINT")
    timeout_s = int(os.getenv("LIGHTRAG_TIMEOUT_SECONDS", "120"))
    outfile = os.getenv("LIGHTRAG_OUTFILE", "logs/query_eval_shipley.json")

    results: Dict[str, Any] = {
        "meta": {
            "host": host,
            "port": port,
            "mode": mode,
            "endpoint_override": endpoint,
            "timeout_seconds": timeout_s,
            "started_at_epoch": time.time(),
        },
        "queries": [],
    }

    for item in SHIPLEY_EVAL_QUERIES:
        qid = item["id"]
        query = item["query"]
        expects = item.get("expects", [])

        resp = _run_query(host, port, mode, timeout_s, endpoint, query)
        answer = _extract_answer(resp["response"]) if resp.get("ok") else ""
        answer_lc = answer.lower()
        hit_count = sum(1 for token in expects if token.lower() in answer_lc)

        results["queries"].append(
            {
                "id": qid,
                "query": query,
                "ok": bool(resp.get("ok")),
                "url": resp.get("url"),
                "endpoint": resp.get("endpoint"),
                "attempts": resp.get("attempts", []),
                "answer_preview": answer[:1500],
                "heuristic_hits": {"expected_tokens": expects, "hit_count": hit_count},
            }
        )

    results["meta"]["finished_at_epoch"] = time.time()

    os.makedirs(os.path.dirname(outfile), exist_ok=True)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"Wrote: {outfile}")
    ok_count = sum(1 for q in results["queries"] if q["ok"])
    print(f"Queries ok: {ok_count}/{len(results['queries'])}")
    return 0 if ok_count > 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

