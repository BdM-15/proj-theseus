"""
Relationship Inference Algorithms (Modular - Branch 040 Pattern)

Each algorithm is a separate module for:
- Maintainability: Modify algorithms independently
- Testability: Test each in isolation
- Parallelization: Clean asyncio.gather execution

Remaining algorithms after Issue #85 cleanup:
- Algo 1: L↔M Instruction-Eval linking (cross-document, cannot be solved by extraction)
- Algo 7: Heuristic regex patterns (zero LLM cost, deterministic)
- Algo 8: Orphan resolution (13% orphan rate justifies rescue pass)

Dropped (extraction prompt + specialized entities now cover these):
- Algo 2: Eval hierarchy (HAS_SUBFACTOR, MEASURED_BY, EVALUATED_BY from extraction)
- Algo 3: Req-eval mapping (EVALUATED_BY from extraction Part F.3)
- Algo 4: Deliverable traceability (98% connected via SATISFIED_BY/PRODUCES from extraction)
- Algo 5: Doc hierarchy (637 CHILD_OF from extraction + algo 7 heuristic)
- Algo 6: Concept linking (87% connected via ADDRESSES/RESOLVES/SUPPORTS)

Usage:
    from src.inference.algorithms import run_all_algorithms_parallel
    
    relationships = await run_all_algorithms_parallel(
        entities, entities_by_type, id_to_entity, neo4j_io, model, temperature
    )
"""

from .algo_1_instruction_eval import algo_1_instruction_eval
from .algo_7_heuristic import algo_7_heuristic
from .algo_8_orphan_resolution import algo_8_orphan_resolution
from .orchestrator import run_all_algorithms_parallel

__all__ = [
    'algo_1_instruction_eval',
    'algo_7_heuristic',
    'algo_8_orphan_resolution',
    'run_all_algorithms_parallel',
]

