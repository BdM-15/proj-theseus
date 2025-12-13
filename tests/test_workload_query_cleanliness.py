"""
Optional integration test: workload driver query "cleanliness".

Goal: ensure workload-driver responses are not contaminated with unrelated performance metrics.
Skipped by default; enable with RUN_LLM_EVALS=true.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from src.core.prompt_loader import load_prompt
from src.server.initialization import initialize_raganything, get_rag_instance


@pytest.mark.skipif(
    (os.getenv("RUN_LLM_EVALS", "") or "").strip().lower() not in {"1", "true", "yes", "y"},
    reason="Set RUN_LLM_EVALS=true to run live workload cleanliness test",
)
@pytest.mark.asyncio
async def test_workload_query_cleanliness_live():
    load_dotenv()

    # Require a populated workspace
    ws = os.getenv("WORKSPACE") or "default"
    if not (Path("rag_storage") / ws).exists():
        pytest.skip(f"Workspace not found: rag_storage/{ws} (ingest documents first)")

    await initialize_raganything()
    rag = get_rag_instance()
    assert rag is not None

    prompt_template = load_prompt("user_queries/workload_analysis")
    query = "Provide me a total list of workload drivers for the dining facility."
    response = await rag.aquery(query, mode="mix", user_prompt=prompt_template)

    contamination_markers = ["acceptable quality level", "aql"]
    lower = response.lower()
    assert not any(m in lower for m in contamination_markers)

