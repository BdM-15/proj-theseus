#!/usr/bin/env python3
"""
Standalone Workload Enrichment Test Script
==========================================

Runs ONLY the workload enrichment step against an existing Neo4j workspace.
Use this to test workload enrichment fixes without re-processing the entire RFP.

Usage:
    python tools/test_workload_enrichment_only.py
    
    # Override concurrency (default: 4 to match Branch 040)
    TEST_MAX_WORKERS=2 python tools/test_workload_enrichment_only.py

Prerequisites:
    - Neo4j must be running with an existing workspace containing requirements
    - .env must have valid API keys (XAI_API_KEY, etc.)
"""

import asyncio
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

# CRITICAL: Override worker count BEFORE importing modules that use it
# With batch_size=25 (smaller batches), we can run more workers in parallel
# 8 workers × 25 reqs/batch = 200 reqs processed per wave
os.environ.setdefault("WORKLOAD_MAX_WORKERS", os.getenv("TEST_MAX_WORKERS", "8"))

# Configure logging BEFORE imports that use it
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def run_workload_enrichment_only():
    """Run workload enrichment on existing Neo4j workspace."""
    
    print("=" * 80)
    print("WORKLOAD ENRICHMENT TEST (Standalone)")
    print("=" * 80)
    
    # Import after path setup
    from src.inference.neo4j_graph_io import Neo4jGraphIO
    from src.inference.workload_enrichment import enrich_workload_metadata
    
    # Get config from environment
    # Use REASONING model for enrichment (not extraction model)
    model = os.getenv("REASONING_LLM_NAME", os.getenv("LLM_MODEL", "grok-4-fast-reasoning"))
    temperature = float(os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))
    batch_size = int(os.getenv("WORKLOAD_BATCH_SIZE", "5"))  # No truncation, ~94K tokens max (under 128K)
    max_workers = os.getenv("WORKLOAD_MAX_WORKERS", os.getenv("MAX_ASYNC", "8"))  # More workers for smaller batches
    max_output_tokens = os.getenv("LLM_MAX_OUTPUT_TOKENS", "128000")
    max_retries = os.getenv("LLM_MAX_RETRIES", "3")
    
    print(f"\nConfiguration:")
    print(f"  LLM Model:        {model}")
    print(f"  Temperature:      {temperature}")
    print(f"  Batch Size:       {batch_size}")
    print(f"  Max Workers:      {max_workers}")
    print(f"  Max Output Tokens:{max_output_tokens}")
    print(f"  Max Retries:      {max_retries} (Instructor with error feedback)")
    print(f"  Neo4j URI:        {os.getenv('NEO4J_URI', 'bolt://localhost:7687')}")
    print(f"  Workspace:        {os.getenv('NEO4J_WORKSPACE', 'default')}")
    print(f"\n  Using Instructor for Pydantic-enforced structured output")
    
    # Initialize Neo4j connection
    print("\n[1/3] Connecting to Neo4j...")
    neo4j_io = Neo4jGraphIO()
    
    try:
        # Check current state
        print("\n[2/3] Checking existing data...")
        entities = neo4j_io.get_all_entities()
        requirements = [e for e in entities if e.get('entity_type') == 'requirement']
        
        print(f"  Total entities:    {len(entities)}")
        print(f"  Requirements:      {len(requirements)}")
        
        if not requirements:
            print("\n[ERROR] No requirements found in workspace!")
            print("  Make sure you have processed an RFP first.")
            return {"status": "error", "reason": "no_requirements"}
        
        # Check how many already have workload metadata
        already_enriched = sum(1 for r in requirements if r.get('has_workload_metric') is not None)
        print(f"  Already enriched:  {already_enriched}")
        print(f"  Need enrichment:   {len(requirements) - already_enriched}")
        
        # Run workload enrichment
        print("\n[3/3] Running workload enrichment...")
        print("-" * 60)
        
        start_time = time.time()
        
        stats = await enrich_workload_metadata(
            neo4j_io=neo4j_io,
            batch_size=batch_size,
            model=model,
            temperature=temperature
        )
        
        elapsed = time.time() - start_time
        
        # Report results
        enriched = stats.get('requirements_enriched', 0)
        total = stats.get('total_requirements', 0) or len(requirements)
        rate = stats.get('enrichment_rate', (enriched / total * 100) if total > 0 else 0)
        
        print("\n" + "=" * 80)
        print("WORKLOAD ENRICHMENT RESULTS")
        print("=" * 80)
        print(f"  Requirements Total:   {total}")
        print(f"  Requirements Enriched:{enriched}")
        print(f"  Enrichment Rate:      {rate:.1f}%")
        print(f"  Processing Time:      {elapsed:.1f}s")
        
        # Category distribution
        categories = stats.get('category_distribution', {})
        if categories:
            print(f"\n  BOE Category Distribution:")
            for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                if count > 0:
                    print(f"    {cat:15s}: {count:4d}")
        
        print("=" * 80)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error during workload enrichment: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}
    finally:
        neo4j_io.close()


def main():
    """Entry point."""
    # Check for required env vars
    if not os.getenv("XAI_API_KEY"):
        print("[ERROR] XAI_API_KEY not set in environment")
        print("  Make sure .env file exists with valid API keys")
        sys.exit(1)
    
    # Run async function
    result = asyncio.run(run_workload_enrichment_only())
    
    # Exit with appropriate code
    enriched = result.get("requirements_enriched", 0)
    total = result.get("total_requirements", 0)
    
    if enriched > 0 and total > 0:
        success_rate = (enriched / total) * 100
        if success_rate >= 95:
            print(f"\n[PASS] Enrichment rate {success_rate:.1f}% >= 95% target")
            sys.exit(0)
        else:
            print(f"\n[WARN] Enrichment rate {success_rate:.1f}% below 95% target")
            sys.exit(1)
    elif result.get("error"):
        print(f"\n[FAIL] {result.get('error')}")
        sys.exit(1)
    else:
        print(f"\n[INFO] No requirements to enrich or results unclear")
        sys.exit(0)


if __name__ == "__main__":
    main()

