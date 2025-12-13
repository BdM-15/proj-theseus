"""
Pytest-friendly smoke test for semantic post-processing module structure.

This file used to run as a standalone script and call sys.exit() at import time,
which breaks `pytest` collection. The assertions below provide the same signal
while remaining import-safe.
"""

import inspect


def test_semantic_postprocessing_structure_smoke():
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
    for name in required_functions:
        assert hasattr(semantic_post_processor, name), f"Missing function: {name}"

    # Algorithm signature sanity checks
    for func_name in [
        "_algorithm_1_instruction_eval",
        "_algorithm_2_eval_hierarchy",
        "_algorithm_5_doc_hierarchy",
        "_algorithm_6_concept_linking",
    ]:
        params = list(inspect.signature(getattr(semantic_post_processor, func_name)).parameters.keys())
        assert "system_prompt" in params and "model" in params and "temperature" in params

    params = list(inspect.signature(getattr(semantic_post_processor, "_algorithm_8_orphan_resolution")).parameters.keys())
    assert "neo4j_io" in params and "model" in params and "temperature" in params

    for func_name in ["_algorithm_3_req_eval_batched", "_algorithm_4_deliverable_trace_batched"]:
        params = list(inspect.signature(getattr(semantic_post_processor, func_name)).parameters.keys())
        assert "semaphore" in params and "system_prompt" in params

    params = list(inspect.signature(getattr(semantic_post_processor, "_algorithm_7_heuristic")).parameters.keys())
    assert "entities" in params and "entities_by_type" in params

    params = list(inspect.signature(getattr(semantic_post_processor, "_infer_relationships_multi_algorithm")).parameters.keys())
    assert "entities" in params and "model" in params and "temperature" in params

    for const_name in ["MAX_CONCURRENT_LLM_CALLS", "BATCH_SIZE_ALGO3", "BATCH_OVERLAP_ALGO3", "BATCH_SIZE_ALGO4"]:
        assert hasattr(semantic_post_processor, const_name), f"Missing constant: {const_name}"
