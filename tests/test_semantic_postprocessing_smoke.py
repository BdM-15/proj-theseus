"""
Smoke tests for semantic post-processing module structure.

This is intentionally lightweight:
- No LLM calls
- No Neo4j connection required
- Pure import / signature / constant checks
"""

import inspect
from pathlib import Path

# Add src to path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_semantic_post_processor_imports():
    from src.inference import semantic_post_processor  # noqa: F401


def test_semantic_post_processor_required_functions_exist():
    from src.inference import semantic_post_processor

    required_functions = [
        "_algorithm_1_instruction_eval",
        "_algorithm_2_eval_hierarchy",
        "_algorithm_3_req_eval_batched",
        "_algorithm_4_deliverable_trace_batched",
        "_algorithm_5_doc_hierarchy",
        "_algorithm_6_concept_linking",
        "_algorithm_7_heuristic",
        "_algorithm_8_orphan_resolution",
        "_infer_relationships_multi_algorithm",
    ]

    missing = [f for f in required_functions if not hasattr(semantic_post_processor, f)]
    assert not missing, f"Missing required functions: {missing}"


def test_semantic_post_processor_signatures_smoke():
    from src.inference import semantic_post_processor

    # Algorithms 1/2/5/6: must accept system_prompt/model/temperature.
    for func_name in [
        "_algorithm_1_instruction_eval",
        "_algorithm_2_eval_hierarchy",
        "_algorithm_5_doc_hierarchy",
        "_algorithm_6_concept_linking",
    ]:
        func = getattr(semantic_post_processor, func_name)
        params = list(inspect.signature(func).parameters.keys())
        assert "system_prompt" in params
        assert "model" in params
        assert "temperature" in params

    # Algorithms 3/4: must accept semaphore/system_prompt.
    for func_name in ["_algorithm_3_req_eval_batched", "_algorithm_4_deliverable_trace_batched"]:
        func = getattr(semantic_post_processor, func_name)
        params = list(inspect.signature(func).parameters.keys())
        assert "system_prompt" in params
        assert "semaphore" in params

    # Algorithm 7: heuristic signature.
    func = getattr(semantic_post_processor, "_algorithm_7_heuristic")
    params = list(inspect.signature(func).parameters.keys())
    assert "entities" in params
    assert "entities_by_type" in params

    # Algorithm 8: uses neo4j_io.
    func = getattr(semantic_post_processor, "_algorithm_8_orphan_resolution")
    params = list(inspect.signature(func).parameters.keys())
    assert "neo4j_io" in params
    assert "model" in params
    assert "temperature" in params


def test_semantic_post_processor_required_constants_exist():
    from src.inference import semantic_post_processor

    for const_name in [
        "MAX_CONCURRENT_LLM_CALLS",
        "BATCH_SIZE_ALGO3",
        "BATCH_OVERLAP_ALGO3",
        "BATCH_SIZE_ALGO4",
    ]:
        assert hasattr(semantic_post_processor, const_name), f"Missing constant: {const_name}"
