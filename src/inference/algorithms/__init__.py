"""
Relationship Inference Algorithms (Modular - Branch 040 Pattern)

Each algorithm is a separate module for:
- Maintainability: Modify algorithms independently
- Testability: Test each in isolation
- Parallelization: Clean asyncio.gather execution

Usage:
    from src.inference.algorithms import run_all_algorithms_parallel
    
    relationships = await run_all_algorithms_parallel(
        entities, entities_by_type, id_to_entity, neo4j_io, model, temperature
    )
"""

from .algo_1_instruction_eval import algo_1_instruction_eval
from .algo_2_eval_hierarchy import algo_2_eval_hierarchy
from .algo_3_req_eval import algo_3_req_eval
from .algo_4_deliverable_trace import algo_4_deliverable_trace
from .algo_5_doc_hierarchy import algo_5_doc_hierarchy
from .algo_6_concept_linking import algo_6_concept_linking
from .algo_7_heuristic import algo_7_heuristic
from .algo_8_orphan_resolution import algo_8_orphan_resolution
from .orchestrator import run_all_algorithms_parallel

__all__ = [
    'algo_1_instruction_eval',
    'algo_2_eval_hierarchy', 
    'algo_3_req_eval',
    'algo_4_deliverable_trace',
    'algo_5_doc_hierarchy',
    'algo_6_concept_linking',
    'algo_7_heuristic',
    'algo_8_orphan_resolution',
    'run_all_algorithms_parallel',
]

