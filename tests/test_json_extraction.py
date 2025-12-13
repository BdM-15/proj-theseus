"""
Optional integration test: JsonExtractor end-to-end extraction.

This test requires live LLM credentials (xAI via instructor) and is skipped by default.
Enable with: RUN_LLM_EVALS=true
"""

import os

import pytest
from dotenv import load_dotenv

from src.extraction.json_extractor import JsonExtractor


SAMPLE_RFP_TEXT = """
SECTION L - INSTRUCTIONS TO OFFERORS

L.1.0 GENERAL INSTRUCTIONS
The Offeror shall submit a Technical Volume limited to 25 pages, 12-point Times New Roman font.
This volume must address Factor 1 (Technical Approach) and Factor 2 (Management).

SECTION M - EVALUATION FACTORS

M.2.1 Factor 1: Technical Approach (Most Important, 40%)
The Government will evaluate the Offeror's understanding of the PWS requirements.

M.2.2 Factor 2: Management Approach (Important, 30%)
The Government will evaluate the staffing plan and key personnel.

SECTION C - PERFORMANCE WORK STATEMENT

C.3.1 System Administration
The Contractor shall provide 24/7 system administration support for the Red Hat Linux environment.
The Contractor should maintain 99.9% system availability.
The Contractor may use open-source automation tools.

C.3.2 Cybersecurity
The Contractor shall comply with FAR 52.204-21 and DFARS 252.204-7012.
"""


@pytest.mark.skipif(
    (os.getenv("RUN_LLM_EVALS", "") or "").strip().lower() not in {"1", "true", "yes", "y"},
    reason="Set RUN_LLM_EVALS=true to run live extraction",
)
@pytest.mark.asyncio
async def test_extraction_live():
    load_dotenv()
    extractor = JsonExtractor()
    result = await extractor.extract(SAMPLE_RFP_TEXT, chunk_id="sample-rfp")

    assert result is not None
    assert len(result.entities) > 0

