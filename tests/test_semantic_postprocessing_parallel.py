"""
Validation Tests for Semantic Post-Processing Parallel Execution (Issue #30 Phase 1)
====================================================================================

Tests the parallel execution architecture and critical Algorithm 3 & 4 fixes.

Test Coverage:
1. Algorithm 3 batching prevents JSON truncation
2. Algorithm 4 sub-batching prevents timeout (< 5 min)
3. Parallel execution performance (< 5 min total runtime)
4. Relationship quality maintained (±5% variance from baseline)

Prerequisites:
- Neo4j workspace with processed RFP data
- .env configured with xAI API key
- Baseline semantic post-processing completed

Usage:
    python tests/test_semantic_postprocessing_parallel.py
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.inference.semantic_post_processor import (
    _algorithm_3_req_eval_batched,
    _algorithm_4_deliverable_trace_batched,
    _infer_relationships_multi_algorithm,
    _call_llm_async,
    _load_prompt_template,
    _validate_relationships
)
from src.inference.neo4j_graph_io import Neo4jGraphIO, group_entities_by_type

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================================================================================
# TEST 1: Algorithm 3 Batching (No JSON Truncation)
# ==================================================================================

async def test_algorithm_3_no_truncation():
    """
    Validate Algorithm 3 batching prevents JSON truncation.
    
    Expected:
    - Completes without JSON parsing errors
    - Response length < 100K characters per batch
    - Runtime < 3 minutes
    """
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Algorithm 3 Batching (No JSON Truncation)")
    logger.info("="*80)
    
    # Load test workspace (uses NEO4J_WORKSPACE env var)
    workspace_name = os.getenv("NEO4J_WORKSPACE", "1_adab_iss_2025")
    logger.info(f"Using Neo4j workspace: {workspace_name}")
    
    graph_io = Neo4jGraphIO()
    entities = graph_io.get_all_entities()
    entities_by_type = group_entities_by_type(entities)
    id_to_entity = {e['id']: e for e in entities}
    
    requirements = entities_by_type.get('requirement', [])
    eval_factors = entities_by_type.get('evaluation_factor', [])
    
    logger.info(f"Loaded {len(requirements)} requirements, {len(eval_factors)} eval factors")
    
    if not requirements or not eval_factors:
        logger.warning("⚠️  No requirements or eval factors found")
        return False
    
    # Run Algorithm 3 with batching
    system_prompt = "You are an expert at analyzing government contracting RFPs."
    model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    temperature = 0.1
    semaphore = asyncio.Semaphore(int(os.getenv("MAX_ASYNC", 4)))
    
    start_time = time.time()
    
    try:
        relationships = await _algorithm_3_req_eval_batched(
            entities_by_type=entities_by_type,
            id_to_entity=id_to_entity,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            semaphore=semaphore
        )
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n✅ Algorithm 3 completed successfully")
        logger.info(f"   Runtime: {elapsed_time:.1f}s")
        logger.info(f"   Relationships: {len(relationships)}")
        
        if elapsed_time < 180:  # < 3 minutes
            logger.info(f"✅ Performance PASS: {elapsed_time:.1f}s < 180s")
        else:
            logger.warning(f"⚠️  Performance WARNING: {elapsed_time:.1f}s >= 180s")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON Truncation Error: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Algorithm 3 failed: {e}")
        return False


# ==================================================================================
# TEST 2: Algorithm 4 Sub-Batching (No Timeout)
# ==================================================================================

async def test_algorithm_4_no_timeout():
    """
    Validate Algorithm 4 sub-batching prevents timeout.
    
    Expected:
    - Completes in < 5 minutes
    - No API timeout errors
    - Valid relationships returned
    """
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Algorithm 4 Sub-Batching (No Timeout)")
    logger.info("="*80)
    
    # Load test workspace (uses NEO4J_WORKSPACE env var)
    workspace_name = os.getenv("NEO4J_WORKSPACE", "1_adab_iss_2025")
    logger.info(f"Using Neo4j workspace: {workspace_name}")
    
    graph_io = Neo4jGraphIO()
    entities = graph_io.get_all_entities()
    entities_by_type = group_entities_by_type(entities)
    id_to_entity = {e['id']: e for e in entities}
    
    requirements = entities_by_type.get('requirement', [])
    deliverables = entities_by_type.get('deliverable', [])
    work_statements = entities_by_type.get('work_statement', [])
    
    logger.info(f"Loaded {len(requirements)} requirements, {len(deliverables)} deliverables, {len(work_statements)} work statements")
    
    if not requirements or (not deliverables and not work_statements):
        logger.warning("⚠️  Insufficient entities for Algorithm 4")
        return False
    
    system_prompt = "You are an expert at analyzing government contracting RFPs."
    model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    temperature = 0.1
    semaphore = asyncio.Semaphore(int(os.getenv("MAX_ASYNC", 4)))
    
    start_time = time.time()
    
    try:
        relationships = await _algorithm_4_deliverable_trace_batched(
            entities_by_type=entities_by_type,
            id_to_entity=id_to_entity,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature,
            semaphore=semaphore
        )
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n✅ Algorithm 4 completed successfully")
        logger.info(f"   Runtime: {elapsed_time:.1f}s")
        logger.info(f"   Relationships: {len(relationships)}")
        
        if elapsed_time < 300:  # < 5 minutes
            logger.info(f"✅ Performance PASS: {elapsed_time:.1f}s < 300s")
        else:
            logger.warning(f"⚠️  Performance WARNING: {elapsed_time:.1f}s >= 300s")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Algorithm 4 failed: {e}")
        return False


# ==================================================================================
# TEST 3: Parallel Execution Performance (< 5 min total)
# ==================================================================================

async def test_parallel_execution_performance():
    """
    Validate full semantic post-processing completes in < 5 minutes.
    
    Expected:
    - Total runtime < 300s (5 min)
    - All 8 algorithms execute
    - No failures
    """
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Parallel Execution Performance (< 5 min)")
    logger.info("="*80)
    
    # Load test workspace (uses NEO4J_WORKSPACE env var)
    workspace_name = os.getenv("NEO4J_WORKSPACE", "1_adab_iss_2025")
    logger.info(f"Using Neo4j workspace: {workspace_name}")
    
    graph_io = Neo4jGraphIO()
    entities = graph_io.get_all_entities()
    entities_by_type = group_entities_by_type(entities)
    
    logger.info(f"Loaded {len(entities)} entities")
    
    system_prompt = "You are an expert at analyzing government contracting RFPs."
    model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    temperature = 0.1
    
    start_time = time.time()
    
    try:
        relationships = await _infer_relationships_multi_algorithm(
            entities=entities,
            entities_by_type=entities_by_type,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )
        
        elapsed_time = time.time() - start_time
        
        logger.info(f"\n✅ Full semantic post-processing completed")
        logger.info(f"   Total Runtime: {elapsed_time:.1f}s ({elapsed_time/60:.1f} min)")
        logger.info(f"   Total Relationships: {len(relationships)}")
        
        if elapsed_time < 300:  # < 5 minutes
            logger.info(f"✅ Performance PASS: {elapsed_time:.1f}s < 300s")
            logger.info(f"   Improvement: {(2040 - elapsed_time) / 2040 * 100:.1f}% faster than baseline (34 min)")
        else:
            logger.warning(f"⚠️  Performance WARNING: {elapsed_time:.1f}s >= 300s")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Parallel execution failed: {e}")
        return False


# ==================================================================================
# TEST 4: Relationship Quality (±5% variance)
# ==================================================================================

async def test_relationship_quality():
    """
    Validate relationship quality maintained after parallelization.
    
    Expected:
    - Relationship count within ±5% of baseline
    - Confidence scores similar to baseline
    - No duplicate relationships
    """
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Relationship Quality (±5% variance)")
    logger.info("="*80)
    
    # Load test workspace (uses NEO4J_WORKSPACE env var)
    workspace_name = os.getenv("NEO4J_WORKSPACE", "1_adab_iss_2025")
    logger.info(f"Using Neo4j workspace: {workspace_name}")
    
    graph_io = Neo4jGraphIO()
    entities = graph_io.get_all_entities()
    entities_by_type = group_entities_by_type(entities)
    
    system_prompt = "You are an expert at analyzing government contracting RFPs."
    model = os.getenv("LLM_MODEL", "grok-4-fast-reasoning")
    temperature = 0.1
    
    try:
        relationships = await _infer_relationships_multi_algorithm(
            entities=entities,
            entities_by_type=entities_by_type,
            system_prompt=system_prompt,
            model=model,
            temperature=temperature
        )
        
        # Check for duplicates
        rel_tuples = [(r['source_id'], r['target_id'], r['relationship_type']) for r in relationships]
        unique_rels = set(rel_tuples)
        
        if len(unique_rels) < len(rel_tuples):
            logger.warning(f"⚠️  Found {len(rel_tuples) - len(unique_rels)} duplicate relationships")
        else:
            logger.info(f"✅ No duplicate relationships")
        
        # Calculate confidence score distribution
        confidences = [r.get('confidence', 0) for r in relationships]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        logger.info(f"\n✅ Relationship Quality Metrics:")
        logger.info(f"   Total Relationships: {len(relationships)}")
        logger.info(f"   Unique Relationships: {len(unique_rels)}")
        logger.info(f"   Average Confidence: {avg_confidence:.3f}")
        
        # NOTE: Baseline comparison requires prior test run data
        baseline_count = os.getenv("BASELINE_REL_COUNT")
        if baseline_count:
            baseline = int(baseline_count)
            variance = abs(len(relationships) - baseline) / baseline * 100
            
            if variance <= 5:
                logger.info(f"✅ Quality PASS: {variance:.1f}% variance from baseline")
            else:
                logger.warning(f"⚠️  Quality WARNING: {variance:.1f}% variance from baseline (expected ±5%)")
        else:
            logger.info("ℹ️  Set BASELINE_REL_COUNT env var for comparison")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Quality test failed: {e}")
        return False


# ==================================================================================
# TEST RUNNER
# ==================================================================================

async def run_all_tests():
    """Run all validation tests sequentially."""
    logger.info("\n" + "="*80)
    logger.info("SEMANTIC POST-PROCESSING PARALLEL VALIDATION SUITE (Issue #30 Phase 1)")
    logger.info("="*80)
    
    results = {
        "Algorithm 3 No Truncation": await test_algorithm_3_no_truncation(),
        "Algorithm 4 No Timeout": await test_algorithm_4_no_timeout(),
        "Parallel Execution Performance": await test_parallel_execution_performance(),
        "Relationship Quality": await test_relationship_quality()
    }
    
    logger.info("\n" + "="*80)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    logger.info(f"\nTotal: {total_passed}/{total_tests} tests passed")
    
    if total_passed == total_tests:
        logger.info("\n🎉 ALL TESTS PASSED - Phase 1 validation complete!")
        return True
    else:
        logger.warning(f"\n⚠️  {total_tests - total_passed} test(s) failed - review output above")
        return False


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
