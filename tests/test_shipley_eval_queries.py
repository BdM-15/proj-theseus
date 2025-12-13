import os

import pytest
from dotenv import load_dotenv

from src.server.initialization import initialize_raganything, get_rag_instance


def _enabled() -> bool:
    return (os.getenv("RUN_LLM_EVALS", "") or "").strip().lower() in {"1", "true", "yes", "y"}


@pytest.mark.skipif(not _enabled(), reason="Set RUN_LLM_EVALS=true to run live LLM retrieval evals")
@pytest.mark.asyncio
async def test_shipley_multihop_workload_to_risk_query_has_granular_details():
    """
    Evaluation query requested by user:
    multi-hop retrieval of workload drivers (volumes/frequencies) connected to capture risks.

    This test is intentionally lightweight and only checks for *signals* of granularity
    (numbers/units + risk language). It will be skipped in CI by default.
    """
    load_dotenv()

    await initialize_raganything()
    rag = get_rag_instance()
    assert rag is not None

    query = (
        "What workload volumes/frequencies from this RFP's requirements drive the proposed solution, "
        "and how do they link to Shipley capture risks? "
        "Ground your answer in specific numbers/units (e.g., per day/week/month, hours, shifts, 24/7) "
        "and explain the risk implications (staffing surge, coverage gaps, schedule risk)."
    )

    # Use hybrid/mix mode (vector + graph) per LightRAG guidance.
    response = await rag.aquery(query, mode=os.getenv("EVAL_QUERY_MODE", "mix"))
    assert isinstance(response, str)
    assert len(response) > 400

    lower = response.lower()
    digit_count = sum(ch.isdigit() for ch in response)
    assert digit_count >= 5, "Expected numeric workload evidence (volumes/frequencies/hours)"
    assert any(k in lower for k in ("risk", "mitigation", "concern", "weakness", "schedule")), "Expected capture-risk linkage language"
    assert any(k in lower for k in ("per day", "daily", "weekly", "monthly", "hours", "shift", "24/7")), "Expected workload cadence/coverage language"

