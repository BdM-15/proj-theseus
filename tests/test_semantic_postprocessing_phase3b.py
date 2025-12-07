"""
Structure Validation Tests for Phase 3B (Issue #30)
====================================================

Validates that semantic_post_processor.py implements full cross-algorithm
parallelization (all algorithms run concurrently, not wave-by-wave).

Run: python tests/test_semantic_postprocessing_phase3b.py
"""

import os
import sys
import re

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_phase3b_full_parallelization():
    """Test 1: Verify all algorithms execute in single parallel batch (no waves)"""
    print("\n" + "="*70)
    print("TEST 1: Full Algorithm Parallelization Structure")
    print("="*70)
    
    file_path = "src/inference/semantic_post_processor.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for Phase 3B comment marker
    assert "Issue #30 Phase 3B" in content, "❌ Missing Phase 3B marker comment"
    print("✅ Phase 3B marker comment found")
    
    # Check for single asyncio.gather with all 7 algorithms
    assert "all_tasks = [" in content, "❌ Missing all_tasks list preparation"
    print("✅ all_tasks list preparation found")
    
    # Count algorithm function calls in all_tasks
    algorithm_pattern = r"_algorithm_\d+_\w+"
    matches = re.findall(algorithm_pattern, content)
    all_tasks_section = content[content.find("all_tasks = ["):content.find("algorithm_results = await asyncio.gather")]
    algo_calls_in_tasks = re.findall(algorithm_pattern, all_tasks_section)
    
    assert len(algo_calls_in_tasks) == 7, f"❌ Expected 7 algorithm calls in all_tasks, found {len(algo_calls_in_tasks)}"
    print(f"✅ All 7 LLM algorithms in single parallel task list: {algo_calls_in_tasks}")
    
    # Check for single asyncio.gather call
    gather_count = content.count("algorithm_results = await asyncio.gather(*all_tasks")
    assert gather_count == 1, f"❌ Expected 1 asyncio.gather for algorithms, found {gather_count}"
    print("✅ Single asyncio.gather(*all_tasks) for all algorithms")
    
    # Check for return_exceptions=True
    gather_section = content[content.find("algorithm_results = await asyncio.gather"):content.find("algorithm_results = await asyncio.gather") + 200]
    assert "return_exceptions=True" in gather_section, \
        "❌ Missing return_exceptions=True in gather"
    print("✅ return_exceptions=True for error isolation")
    
    # Verify NO wave-based execution (no Wave 1, Wave 2, Wave 3 sections)
    assert "🌊 Wave 1:" not in content, "❌ Found Wave 1 marker (should be removed in Phase 3B)"
    assert "🌊 Wave 2:" not in content, "❌ Found Wave 2 marker (should be removed in Phase 3B)"
    assert "🌊 Wave 3:" not in content, "❌ Found Wave 3 marker (should be removed in Phase 3B)"
    print("✅ No wave-based sequential execution (all parallel)")
    
    print("\n✅ TEST 1 PASSED: Full parallelization structure validated\n")


def test_phase3b_algorithm_names():
    """Test 2: Verify algorithm name labels for logging"""
    print("\n" + "="*70)
    print("TEST 2: Algorithm Name Labels")
    print("="*70)
    
    file_path = "src/inference/semantic_post_processor.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for algorithm_names list
    assert "algorithm_names = [" in content, "❌ Missing algorithm_names list"
    print("✅ algorithm_names list found")
    
    # Extract algorithm names
    names_section = content[content.find("algorithm_names = ["):content.find("algorithm_names = [") + 800]
    
    expected_names = [
        "Algorithm 1: Instruction-Evaluation",
        "Algorithm 2: Evaluation Hierarchy",
        "Algorithm 3: Requirement-Evaluation",
        "Algorithm 4: Deliverable Traceability",
        "Algorithm 5: Document Hierarchy",
        "Algorithm 6: Concept Linking",
        "Algorithm 8: Orphan Resolution"  # Note: Algorithm 7 is heuristic, runs separately
    ]
    
    for name in expected_names:
        assert name in names_section, f"❌ Missing algorithm name: {name}"
        print(f"✅ Found: {name}")
    
    print("\n✅ TEST 2 PASSED: All algorithm names present\n")


def test_phase3b_semaphore_usage():
    """Test 3: Verify semaphore passed to algorithms that need it"""
    print("\n" + "="*70)
    print("TEST 3: Semaphore Usage for Rate Limiting")
    print("="*70)
    
    file_path = "src/inference/semantic_post_processor.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check semaphore creation
    assert "semaphore = asyncio.Semaphore(MAX_CONCURRENT_LLM_CALLS)" in content, \
        "❌ Missing semaphore creation"
    print("✅ Semaphore created with MAX_CONCURRENT_LLM_CALLS")
    
    # Check algorithms 3 and 4 receive semaphore
    all_tasks_section = content[content.find("all_tasks = ["):content.find("algorithm_results = await asyncio.gather")]
    
    assert "_algorithm_3_req_eval_batched(" in all_tasks_section and ", semaphore)" in all_tasks_section, \
        "❌ Algorithm 3 missing semaphore parameter"
    print("✅ Algorithm 3 receives semaphore")
    
    assert "_algorithm_4_deliverable_trace_batched(" in all_tasks_section and ", semaphore)" in all_tasks_section, \
        "❌ Algorithm 4 missing semaphore parameter"
    print("✅ Algorithm 4 receives semaphore")
    
    print("\n✅ TEST 3 PASSED: Semaphore usage validated\n")


def test_phase3b_heuristic_separate():
    """Test 4: Verify Algorithm 7 (heuristic) runs separately"""
    print("\n" + "="*70)
    print("TEST 4: Heuristic Algorithm Separation")
    print("="*70)
    
    file_path = "src/inference/semantic_post_processor.py"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check that Algorithm 7 is NOT in all_tasks
    all_tasks_section = content[content.find("all_tasks = ["):content.find("algorithm_results = await asyncio.gather")]
    assert "_algorithm_7_heuristic" not in all_tasks_section, \
        "❌ Algorithm 7 should NOT be in all_tasks (no LLM, instant execution)"
    print("✅ Algorithm 7 not in parallel task list (correct)")
    
    # Check that Algorithm 7 runs separately after parallel algorithms
    assert "⚡ Algorithm 7: Heuristic Pattern Matching" in content, \
        "❌ Missing Algorithm 7 execution marker"
    print("✅ Algorithm 7 executes separately (heuristic pattern matching)")
    
    # Verify it runs after asyncio.gather
    gather_pos = content.find("algorithm_results = await asyncio.gather")
    algo7_pos = content.find("⚡ Algorithm 7: Heuristic Pattern Matching")
    assert algo7_pos > gather_pos, "❌ Algorithm 7 should run AFTER asyncio.gather"
    print("✅ Algorithm 7 executes after parallel algorithms complete")
    
    print("\n✅ TEST 4 PASSED: Heuristic algorithm properly separated\n")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PHASE 3B STRUCTURE VALIDATION TESTS")
    print("Full Cross-Algorithm Parallelization (Issue #30)")
    print("="*70)
    
    try:
        test_phase3b_full_parallelization()
        test_phase3b_algorithm_names()
        test_phase3b_semaphore_usage()
        test_phase3b_heuristic_separate()
        
        print("\n" + "="*70)
        print("✅ ALL PHASE 3B TESTS PASSED")
        print("="*70)
        print("\nPhase 3B optimizations validated:")
        print("  • All 7 LLM algorithms execute in parallel")
        print("  • No wave-based sequential execution")
        print("  • Shared semaphore for rate limiting")
        print("  • Algorithm 7 (heuristic) runs separately")
        print("  • Error isolation with return_exceptions=True")
        print("\nExpected performance: 5.1 min → ~2 min (60% reduction)")
        print("="*70 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
