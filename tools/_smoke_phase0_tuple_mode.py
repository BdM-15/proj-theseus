"""Phase 0 acceptance item 5: tuple-mode regression smoke test.

Goal: prove upgraded lightrag-hku 1.5.0 doesn't break our existing tuple-mode
extraction path under our config. Single small synthetic chunk, tuple mode forced,
end-to-end through our LightRAG init code path. NOT a full re-process of
afcap5_adab_iss (too slow/expensive).

Throwaway working dir — no real workspace touched.
"""
import os
import sys
import asyncio
import tempfile
import shutil
from pathlib import Path

# Make `src` importable when running from anywhere
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Force tuple mode (current production) BEFORE any lightrag imports
os.environ["ENTITY_EXTRACTION_USE_JSON"] = "false"

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

tmpdir = tempfile.mkdtemp(prefix="smoke_phase0_")
os.environ["WORKING_DIR"] = tmpdir
print(f"Working dir: {tmpdir}")


async def main() -> int:
    from src.server.initialization import initialize_raganything
    import lightrag

    print("Initializing RAG (tuple mode forced)...")
    rag_anything = await initialize_raganything()
    rag = rag_anything.lightrag
    print(f"  lightrag version: {lightrag.__version__}")
    print(f"  entity_extraction_use_json = {rag.entity_extraction_use_json}")
    print(f"  llm_model_name = {rag.llm_model_name}")

    test_text = (
        "Section L.4.2.1: The Offeror shall submit a Technical Approach addressing "
        "PWS Section 3.2 Cybersecurity Requirements. The Government will evaluate "
        "IAW Section M Factor 1 (Technical), Subfactor 1A (Cybersecurity Compliance). "
        "All proposals must comply with FAR 52.204-21."
    )
    print(f"\nInserting test text ({len(test_text)} chars)...")
    await rag.ainsert(test_text)

    full_ents = await rag.full_entities.get_all()
    full_rels = await rag.full_relations.get_all()
    n_ents = sum(len(v.get("entity_names", [])) for v in full_ents.values())
    n_rels = sum(len(v.get("relation_pairs", [])) for v in full_rels.values())

    print("\n=== SMOKE TEST RESULT ===")
    print(f"Entities extracted: {n_ents}")
    print(f"Relationships extracted: {n_rels}")
    if n_ents == 0 and n_rels == 0:
        print("FAIL: tuple-mode extraction returned nothing — REGRESSION")
        return 1
    print("PASS: tuple-mode extraction working under lightrag-hku 1.5.0")
    return 0


try:
    rc = asyncio.run(main())
finally:
    shutil.rmtree(tmpdir, ignore_errors=True)

sys.exit(rc)
