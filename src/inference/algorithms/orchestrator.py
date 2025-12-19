"""
Orchestrator: Parallel Execution of All Algorithms (Branch 040 Pattern)

Runs algorithms 1-6 and 8 concurrently via asyncio.gather.
Algorithm 7 (heuristic) runs separately (instant, no LLM).

Issue #56 Enhancement: Conditional execution for algorithms 3, 4, 6
- These algorithms create relationships that the extraction prompt ALSO creates
- If extraction captured sufficient relationships, skip to save cost
- Threshold: If >50% of target entities have relevant relationships, skip
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

# Conditional execution thresholds (Issue #56)
# DISABLED: Quality over cost - always run all algorithms
# Set thresholds to 1.0 to effectively disable skipping
ALGO_3_COVERAGE_THRESHOLD = float(os.getenv("ALGO_3_THRESHOLD", "1.0"))  # Always run (quality over cost)
ALGO_4_COVERAGE_THRESHOLD = float(os.getenv("ALGO_4_THRESHOLD", "1.0"))  # Always run (quality over cost)
ALGO_6_COVERAGE_THRESHOLD = float(os.getenv("ALGO_6_THRESHOLD", "1.0"))  # Always run (quality over cost)


def check_extraction_coverage(
    entities_by_type: Dict,
    existing_relationships: List[Dict]
) -> Dict[str, float]:
    """
    Check how well extraction captured relationships for algorithms 3, 4, 6.
    
    Returns coverage percentages for each algorithm's target relationship type.
    """
    # Build relationship lookup by source entity
    source_to_rels = {}
    for rel in existing_relationships:
        src = rel.get('source_id') or rel.get('source')
        if src:
            if src not in source_to_rels:
                source_to_rels[src] = []
            source_to_rels[src].append(rel)
    
    # Algo 3: Requirements with EVALUATED_BY relationships
    requirements = entities_by_type.get('requirement', [])
    reqs_with_eval = 0
    for req in requirements:
        req_rels = source_to_rels.get(req['id'], [])
        if any(r.get('relationship_type') == 'EVALUATED_BY' for r in req_rels):
            reqs_with_eval += 1
    algo_3_coverage = reqs_with_eval / len(requirements) if requirements else 0
    
    # Algo 4: Deliverables with SATISFIED_BY or PRODUCES relationships (as targets)
    deliverables = entities_by_type.get('deliverable', [])
    deliverable_ids = {d['id'] for d in deliverables}
    delivs_linked = 0
    for rel in existing_relationships:
        target = rel.get('target_id') or rel.get('target')
        rel_type = rel.get('relationship_type', '')
        if target in deliverable_ids and rel_type in ('SATISFIED_BY', 'PRODUCES', 'TRACKED_BY'):
            delivs_linked += 1
    algo_4_coverage = min(1.0, delivs_linked / len(deliverables)) if deliverables else 0
    
    # Algo 6: Concepts with any relationships
    concepts = entities_by_type.get('concept', [])[:100]  # Match algorithm limit
    strategic_themes = entities_by_type.get('strategic_theme', [])
    concept_pool = concepts + strategic_themes
    concepts_linked = 0
    for concept in concept_pool:
        if concept['id'] in source_to_rels:
            concepts_linked += 1
    algo_6_coverage = concepts_linked / len(concept_pool) if concept_pool else 0
    
    return {
        'algo_3': algo_3_coverage,
        'algo_4': algo_4_coverage,
        'algo_6': algo_6_coverage
    }


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
    Execute algorithms in PARALLEL using asyncio.gather.
    
    Branch 040 optimization: 5.1 min → 2 min (60% reduction)
    Issue #56: Conditional execution for algorithms 3, 4, 6 based on extraction coverage
    
    Architecture:
    - Algorithms 1, 2, 5, 8: Always run (true inference required)
    - Algorithms 3, 4, 6: Conditional (skip if extraction captured sufficient relationships)
    - Algorithm 7: Runs instantly (regex heuristic, no LLM)
    
    Args:
        entities: All entities to analyze
        entities_by_type: Entities grouped by type
        id_to_entity: Entity ID → entity dict mapping
        neo4j_io: Neo4jGraphIO instance for querying
        model: LLM model name
        temperature: LLM temperature
        existing_relationships: Relationships from extraction (for coverage check)
        
    Returns:
        Combined list of all inferred relationships
    """
    logger.info(f"\n⚡ Starting PARALLEL algorithm execution (MAX_ASYNC={MAX_CONCURRENT_LLM_CALLS})")
    
    # Load shared system prompt once
    system_prompt = await load_prompt_template("system_prompt.md")
    
    # =========================================================================
    # Issue #56: Check extraction coverage for conditional algorithms
    # =========================================================================
    run_algo_3 = True
    run_algo_4 = True
    run_algo_6 = True
    
    if existing_relationships:
        coverage = check_extraction_coverage(entities_by_type, existing_relationships)
        
        if coverage['algo_3'] >= ALGO_3_COVERAGE_THRESHOLD:
            run_algo_3 = False
            logger.info(f"  ⏭️  Algo 3: Skipping (extraction coverage {coverage['algo_3']:.0%} >= {ALGO_3_COVERAGE_THRESHOLD:.0%})")
        
        if coverage['algo_4'] >= ALGO_4_COVERAGE_THRESHOLD:
            run_algo_4 = False
            logger.info(f"  ⏭️  Algo 4: Skipping (extraction coverage {coverage['algo_4']:.0%} >= {ALGO_4_COVERAGE_THRESHOLD:.0%})")
        
        if coverage['algo_6'] >= ALGO_6_COVERAGE_THRESHOLD:
            run_algo_6 = False
            logger.info(f"  ⏭️  Algo 6: Skipping (extraction coverage {coverage['algo_6']:.0%} >= {ALGO_6_COVERAGE_THRESHOLD:.0%})")
    
    # =========================================================================
    # PHASE 1: Run LLM-powered algorithms in parallel
    # =========================================================================
    
    # Create semaphore-wrapped tasks for rate limiting
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)
    
    async def rate_limited(coro):
        """Wrap coroutine with semaphore for rate limiting."""
        async with semaphore:
            return await coro
    
    async def noop():
        """No-op coroutine for skipped algorithms."""
        return []
    
    # Prepare algorithm tasks (conditional for 3, 4, 6)
    tasks = [
        rate_limited(algo_1_instruction_eval(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_2_eval_hierarchy(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_3_req_eval(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )) if run_algo_3 else noop(),
        rate_limited(algo_4_deliverable_trace(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )) if run_algo_4 else noop(),
        rate_limited(algo_5_doc_hierarchy(
            entities, id_to_entity, system_prompt, model, temperature
        )),
        rate_limited(algo_6_concept_linking(
            entities_by_type, id_to_entity, system_prompt, model, temperature
        )) if run_algo_6 else noop(),
        rate_limited(algo_8_orphan_resolution(
            entities, id_to_entity, neo4j_io, model, temperature, system_prompt
        )),
    ]
    
    # Execute all LLM algorithms in parallel
    algo_status = [
        "always",
        "always",
        "conditional" if run_algo_3 else "skipped",
        "conditional" if run_algo_4 else "skipped",
        "always",
        "conditional" if run_algo_6 else "skipped",
        "always"
    ]
    running_count = sum(1 for s in algo_status if s != "skipped")
    logger.info(f"  Running {running_count}/7 LLM algorithms...")
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
    
    for name, result, status in zip(algorithm_names, results, algo_status):
        if status == "skipped":
            continue  # Already logged above
        elif isinstance(result, Exception):
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

