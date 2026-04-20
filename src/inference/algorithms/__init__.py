"""
Relationship Inference Algorithms (Modular - Branch 040 Pattern)

Each algorithm is a separate module for:
- Maintainability: Modify algorithms independently
- Testability: Test each in isolation
- Parallelization: Clean asyncio.gather execution

Active algorithms after Issue #85 cleanup:
- infer_lm_links: L↔M Instruction-Eval linking (cross-document, cannot be solved by extraction)
- infer_document_structure: Heuristic regex patterns (zero LLM cost, deterministic)
- resolve_orphans: Orphan resolution (13% orphan rate justifies rescue pass)

Dropped (extraction prompt + specialized entities now cover these):
- Algo 2: Eval hierarchy (HAS_SUBFACTOR, MEASURED_BY, EVALUATED_BY from extraction)
- Algo 3: Req-eval mapping (EVALUATED_BY from extraction Part F.3)
- Algo 4: Deliverable traceability (98% connected via SATISFIED_BY/PRODUCES from extraction)
- Algo 5: Doc hierarchy (637 CHILD_OF from extraction + heuristic)
- Algo 6: Concept linking (87% connected via ADDRESSES/RESOLVES/SUPPORTS)

Usage:
    from src.inference.algorithms import run_all_algorithms_parallel
    
    relationships = await run_all_algorithms_parallel(
        entities, entities_by_type, id_to_entity, neo4j_io, model, temperature
    )
"""

from .infer_lm_links import infer_lm_links
from .infer_document_structure import infer_document_structure
from .resolve_orphans import resolve_orphans
from .orchestrator import run_all_algorithms_parallel

__all__ = [
    'infer_lm_links',
    'infer_document_structure',
    'resolve_orphans',
    'run_all_algorithms_parallel',
]

