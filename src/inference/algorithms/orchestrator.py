"""
Orchestrator: Parallel Execution of All Algorithms (Branch 040 Pattern)

Runs algorithms 1-6 and 8 concurrently via asyncio.gather.
Algorithm 7 (heuristic) runs separately (instant, no LLM).
"""
import asyncio
import logging
import os
from typing import Dict, List

from .algo_1_instruction_eval import algo_1_instruction_eval
from .algo_2_eval_hierarchy import algo_2_eval_hierarchy
from .algo_3_req_eval import algo_3_req_eval
from .algo_4_deliverable_trace import algo_4_deliverable_trace
from .algo_5_doc_hierarchy import algo_5_doc_hierarchy
from .algo_6_concept_linking import algo_6_concept_linking
from .algo_7_heuristic import algo_7_heuristic
from .algo_8_orphan_resolution import algo_8_orphan_resolution
from .base import load_prompt_template

logger = logging.getLogger(__name__)

# Parallelization config
MAX_CONCURRENT_LLM_CALLS = int(os.getenv("MAX_ASYNC", "8"))


async def run_all_algorithms_parallel(
    entities: List[Dict],
    entities_by_type: Dict,
    id_to_entity: Dict,
    neo4j_io,
    model: str,
    temperature: float
) -> List[Dict]:
    """
    Execute ALL algorithms in PARALLEL using asyncio.gather.
    
    Branch 040 optimization: 5.1 min → 2 min (60% reduction)
    
    Architecture:
    - Algorithms 1-6, 8: Run concurrently (LLM-powered)
    - Algorithm 7: Runs instantly (regex heuristic, no LLM)
    
    Args:
        entities: All entities to analyze
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID → entity dict mapping
        neo4j_io: Neo4jGraphIO instance for querying
        model: LLM model name
        temperature: LLM temperature
        
    Returns:
        Combined list of all inferred relationships
    """
    logger.info(f"\n⚡ Starting PARALLEL algorithm execution (MAX_ASYNC={MAX_CONCURRENT_LLM_CALLS})")
    
    # Load shared system prompt once
    system_prompt = await load_prompt_template("system_prompt.md")
    
    # =========================================================================
    # PHASE 1: Run all LLM-powered algorithms in parallel
    # =========================================================================
    
    # Create semaphore-wrapped tasks for rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)
    
    async def rate_limited(coro):
        """Wrap coroutine with semaphore for rate limiting."""
        async with semaphore:
            return await coro
    
    # Prepare all algorithm tasks
    tasks = [
        rate_limited(algo_1_instruction_eval(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_2_eval_hierarchy(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_3_req_eval(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_4_deliverable_trace(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_5_doc_hierarchy(
            entities, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_6_concept_linking(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_8_orphan_resolution(
            entities, id_to_entity, neo4j_io, model, temperature, system_prompt
        )),
    ]
    
    # Execute all LLM algorithms in parallel
    logger.info("  Running algorithms 1-6, 8 in parallel...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    all_relationships = []
    algorithm_names = [
        "Algo 1: Instruction-Eval",
        "Algo 2: Eval Hierarchy",
        "Algo 3: Req-Eval Mapping",
        "Algo 4: Deliverable Trace",
        "Algo 5: Doc Hierarchy",
        "Algo 6: Concept Linking",
        "Algo 8: Orphan Resolution"
    ]
    
    for name, result in zip(algorithm_names, results):
        if isinstance(result, Exception):
            logger.error(f"  ❌ {name} failed: {result}")
        elif result:
            all_relationships.extend(result)
            logger.info(f"  ✅ {name}: {len(result)} relationships")
        else:
            logger.info(f"  ⏭️  {name}: skipped (no applicable entities)")
    
    # =========================================================================
    # PHASE 2: Run heuristic algorithm (instant, no LLM)
    # =========================================================================
    
    logger.info("\n  Running Algorithm 7 (heuristic)...")
    heuristic_rels = algo_7_heuristic(entities, entities_by_type)
    all_relationships.extend(heuristic_rels)
    logger.info(f"  ✅ Algo 7: Heuristic: {len(heuristic_rels)} relationships")
    
    # =========================================================================
    # Summary
    # =========================================================================
    
    logger.info(f"\n✅ Total relationships from all algorithms: {len(all_relationships)}")
    
    return all_relationships

