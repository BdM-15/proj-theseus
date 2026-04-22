"""Smoke test for local BGE reranker.

Loads model, scores 4 docs against an SLA query, prints sorted results.
Run from workspace root:  .venv\\Scripts\\python.exe tools/test_reranker_smoke.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# Ensure workspace root is on sys.path so `src.*` imports resolve when invoked directly
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(message)s")

from dotenv import load_dotenv

load_dotenv()

from src.extraction.govcon_reranker import make_govcon_rerank_func


async def main() -> None:
    rerank = make_govcon_rerank_func()
    assert rerank is not None, "rerank func should be enabled (check ENABLE_RERANK)"

    docs = [
        "The contractor shall provide 24/7 NOC support with a 15-minute response SLA.",
        "Lunch will be served at the kickoff meeting.",
        "Section M evaluation criteria weight Technical Approach at 40%.",
        "The PWS requires monthly performance reports submitted on CDRL A001.",
    ]
    result = await rerank("What are the response SLAs for NOC support?", docs)

    print("\n=== RERANK RESULT (sorted by score) ===")
    for r in result:
        idx = r["index"]
        print(f"  {r['relevance_score']:.4f}  [#{idx}]  {docs[idx][:70]}")


if __name__ == "__main__":
    asyncio.run(main())
