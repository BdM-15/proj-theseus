"""
Orchestrator: Parallel Execution of Inference Algorithms

Issue #85: Reduced from 8 algorithms to 3 after data-driven analysis showed
extraction prompt + specialized entity types now cover algorithms 2-6.

Remaining:
- Algo 1: L↔M instruction-eval linking (cross-document gap, only 3 GUIDES from extraction)
- Algo 7: Heuristic regex (zero LLM cost, deterministic)
- Algo 8: Orphan resolution (13% orphan rate, 86 orphan requirements)
"""
import asyncio
import logging
from typing import Dict, List

from src.core import get_settings
from .algo_1_instruction_eval import algo_1_instruction_eval
from .algo_7_heuristic import algo_7_heuristic
from .algo_8_orphan_resolution import algo_8_orphan_resolution
from .base import load_prompt_template

logger = logging.getLogger(__name__)

_settings = get_settings()
MAX_CONCURRENT_LLM_CALLS = _settings.get_effective_post_processing_max_async()


async def run_all_algorithms_parallel(
    entities: List[Dict],
    entities_by_type: Dict,
    id_to_entity: Dict,
    neo4j_io,
    model: str,
    temperature: float,
    existing_relationships: List[Dict] = None
) -> List[Dict]:
    """
    Execute inference algorithms in parallel via asyncio.gather.
    
    Architecture:
    - Algo 1, 8: LLM-powered, run in parallel with semaphore
    - Algo 7: Instant regex heuristic, runs after LLM phase
    
    Args:
        entities: All entities to analyze
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID → entity dict mapping
        neo4j_io: Neo4jGraphIO instance for querying
        model: LLM model name
        temperature: LLM temperature
        existing_relationships: Relationships from extraction (unused, kept for API compat)
        
    Returns:
        Combined list of all inferred relationships
    """
    logger.info(f"\n⚡ Starting PARALLEL algorithm execution (MAX_ASYNC={MAX_CONCURRENT_LLM_CALLS})")
    
    # Load shared system prompt once
    system_prompt = await load_prompt_template("system_prompt.md")
    
    # =========================================================================
    # PHASE 1: Run LLM-powered algorithms in parallel
    # =========================================================================
    
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)
    
    async def rate_limited(coro):
        async with semaphore:
            return await coro
    
    tasks = [
        rate_limited(algo_1_instruction_eval(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_8_orphan_resolution(
            entities, id_to_entity, neo4j_io, model, temperature, system_prompt
        )),
    ]
    
    algorithm_names = [
        "Algo 1: Instruction-Eval",
        "Algo 8: Orphan Resolution",
    ]
    
    logger.info(f"  Running {len(tasks)}/2 LLM algorithms...")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results
    all_relationships = []
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

