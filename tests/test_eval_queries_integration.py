"""Integration evaluation queries for GovCon/Shipley multi-hop retrieval.

These tests are intentionally opt-in and require a running server plus an ingested
workspace with an RFP/proposal corpus.

Run:
  python3 -m pytest -m integration -q

Environment:
  - EVAL_SERVER_URL (default: http://localhost:9621)

Note:
  These validate *query quality symptoms* (granularity, multi-hop linkage, no hand-waving)
  rather than exact string matches.
"""

from __future__ import annotations

import os
import re
import pytest


@pytest.mark.integration
def test_multihop_eval_queries_smoke() -> None:
    try:
        import httpx  # type: ignore
    except Exception:
        pytest.skip("httpx not installed", allow_module_level=True)

    base_url = os.getenv("EVAL_SERVER_URL", "http://localhost:9621").rstrip("/")

    # LightRAG default query endpoint: POST /query/stream (NDJSON)
    url = f"{base_url}/query/stream"

    # Curated multi-hop GovCon/Shipley queries.
    queries = [
        # L ↔ M traceability
        "Map Section L submission instructions to the Section M evaluation factors they drive. Include page limits, required volumes, and how each is evaluated.",
        # Workload → risk drivers (granular)
        "List workload drivers (volumes/frequencies/shifts/locations) that create schedule or staffing risk, and link each risk to the specific requirement(s) that drive it.",
        # Compliance → evaluation impact
        "Identify compliance-critical requirements (shall/must) that are directly evaluated. For each, cite the evaluation factor/subfactor and describe the evaluation signal.",
        # Shipley phase synthesis
        "Propose Pink Team vs Red Team review focus areas using the RFP: tie each focus area to a customer pain point, a compliance requirement, and the evaluation criteria that matter.",
    ]

    # Quality heuristics: the response should not be empty/generic.
    # We check for evidence of structure linking (L/M, evaluation, requirements) and specificity markers.
    must_have_patterns = [
        r"section\s+l",
        r"section\s+m",
        r"evaluation",
        r"requirement|shall|must",
    ]

    with httpx.Client(timeout=120.0) as client:
        for q in queries:
            payload = {
                "query": q,
                # Keep LightRAG defaults as much as possible.
                "mode": "mix",
                "include_references": True,
                "stream": False,
            }
            r = client.post(url, json=payload)
            assert r.status_code == 200, r.text

            # /query/stream returns NDJSON; non-streaming mode returns one or two lines.
            text = r.text
            assert len(text.strip()) > 0

            # Extract the response text from the last JSON line that has "response".
            response_lines = [ln for ln in text.splitlines() if ln.strip()]
            assert response_lines

            response_payloads = []
            for ln in response_lines:
                try:
                    import json

                    response_payloads.append(json.loads(ln))
                except Exception:
                    continue

            response_text = "\n".join(p.get("response", "") for p in response_payloads if isinstance(p, dict))
            assert len(response_text.strip()) > 200  # avoid one-liners

            # Must contain core GovCon linkage signals (heuristic).
            low = response_text.lower()
            for pat in must_have_patterns:
                assert re.search(pat, low), f"Missing pattern '{pat}' in response for query: {q}\n\n{response_text[:800]}"

            # Must avoid obvious generic filler.
            assert "as an ai" not in low
