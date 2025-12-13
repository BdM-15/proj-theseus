"""
Optional integration test: workload_analysis user prompt via LightRAG query path.

Skipped by default; enable with RUN_LLM_EVALS=true and ensure a populated rag_storage workspace exists.
"""

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv


@pytest.mark.skipif(
    (os.getenv("RUN_LLM_EVALS", "") or "").strip().lower() not in {"1", "true", "yes", "y"},
    reason="Set RUN_LLM_EVALS=true to run live workload query prompt test",
)
@pytest.mark.asyncio
async def test_workload_user_query_prompt_executes():
    load_dotenv()

    from lightrag import LightRAG

    prompt_path = Path("prompts/user_queries/workload_analysis.md")
    if not prompt_path.exists():
        pytest.skip(f"Prompt not found: {prompt_path}")

    # Target workspace folder under rag_storage/
    ws = os.getenv("WORKSPACE") or os.getenv("NEO4J_WORKSPACE") or "default"
    working_dir_path = Path("rag_storage") / ws
    if not working_dir_path.exists():
        pytest.skip(f"Workspace not found: {working_dir_path} (ingest documents first)")

    rag = LightRAG(working_dir=str(working_dir_path))
    query = "Provide a total list of workload drivers (volumes/frequencies/shifts) for the services described."
    resp = await rag.aquery(query)
    assert isinstance(resp, str)
    assert len(resp) > 200

