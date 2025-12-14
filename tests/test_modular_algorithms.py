"""Test modular algorithm architecture"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('=== Testing Modular Algorithm Architecture ===\n')

# Test algorithm module imports
try:
    from src.inference.algorithms import (
        algo_1_instruction_eval,
        algo_2_eval_hierarchy,
        algo_3_req_eval,
        algo_4_deliverable_trace,
        algo_5_doc_hierarchy,
        algo_6_concept_linking,
        algo_7_heuristic,
        algo_8_orphan_resolution,
        run_all_algorithms_parallel,
    )
    print('✅ All algorithm modules imported successfully')
except Exception as e:
    print(f'❌ Algorithm import failed: {e}')
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test heuristic algorithm (sync, no LLM)
test_entities = [
    {'id': '1', 'entity_name': 'Section 3.1 Requirements', 'description': 'See CDRL A001 for details', 'entity_type': 'requirement'},
    {'id': '2', 'entity_name': 'CDRL A001 Deliverable', 'description': 'Monthly status report', 'entity_type': 'deliverable'},
]
test_by_type = {
    'requirement': [test_entities[0]],
    'deliverable': [test_entities[1]],
}

rels = algo_7_heuristic(test_entities, test_by_type)
print(f'✅ Algorithm 7 (heuristic): Found {len(rels)} relationships')
if rels:
    r = rels[0]
    print(f'   Example: {r["source_id"]} -> {r["target_id"]} ({r["relationship_type"]})')

# Test base utilities
from src.inference.algorithms.base import is_main_evaluation_factor, validate_relationships, MAX_CONCURRENT_LLM_CALLS

test_factor_main = {'entity_name': 'Factor A - Technical Approach'}
test_factor_supporting = {'entity_name': 'Outstanding Rating Scale'}

result1 = is_main_evaluation_factor(test_factor_main)
result2 = is_main_evaluation_factor(test_factor_supporting)
print(f'✅ is_main_evaluation_factor("Factor A"): {result1} (expected: True)')
print(f'✅ is_main_evaluation_factor("Outstanding Rating"): {result2} (expected: False)')

assert result1 == True, "Factor A should be main factor"
assert result2 == False, "Rating scale should NOT be main factor"

# Test Pydantic validation
from src.ontology.schema import InferredRelationship
test_rel = {'source_id': '1', 'target_id': '2', 'relationship_type': 'guides', 'confidence': 0.8, 'reasoning': 'test'}
try:
    validated = InferredRelationship.model_validate(test_rel)
    print(f'✅ Pydantic validation: {validated.relationship_type} (normalized to uppercase)')
except Exception as e:
    print(f'❌ Pydantic validation failed: {e}')
    sys.exit(1)

# Test self-loop rejection
test_self_loop = {'source_id': '1', 'target_id': '1', 'relationship_type': 'GUIDES', 'confidence': 0.8}
try:
    InferredRelationship.model_validate(test_self_loop)
    print('❌ Self-loop should have been rejected!')
    sys.exit(1)
except Exception:
    print('✅ Self-loop correctly rejected by Pydantic')

# Test orchestrator config
print(f'✅ Orchestrator MAX_CONCURRENT_LLM_CALLS: {MAX_CONCURRENT_LLM_CALLS}')

# Test semantic_post_processor import
from src.inference.semantic_post_processor import enhance_knowledge_graph
print('✅ enhance_knowledge_graph imported from semantic_post_processor')

print('\n=== All Tests Passed! ===')

