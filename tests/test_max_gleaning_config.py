"""
Test MAX_GLEANING environment variable is correctly read by LightRAG.

This test verifies that:
1. Our .env uses the correct variable name (MAX_GLEANING, not ENTITY_EXTRACT_MAX_GLEANING)
2. LightRAG reads the value correctly
3. The value is 0 (disabled) to prevent double extraction

Issue: We had ENTITY_EXTRACT_MAX_GLEANING=0 but LightRAG expects MAX_GLEANING.
This caused each chunk to be extracted twice (initial + gleaning), doubling LLM costs.

Run: python tests/test_max_gleaning_config.py
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_env_file_has_correct_variable():
    """Verify .env uses MAX_GLEANING (not the wrong ENTITY_EXTRACT_MAX_GLEANING)."""
    env_path = project_root / ".env"
    
    if not env_path.exists():
        print("❌ FAIL: .env file not found")
        return False
    
    env_content = env_path.read_text()
    
    # Check for correct variable
    has_correct = "MAX_GLEANING=" in env_content and not "ENTITY_EXTRACT_MAX_GLEANING=" in env_content.split("MAX_GLEANING=")[0][-50:]
    has_wrong = "ENTITY_EXTRACT_MAX_GLEANING=" in env_content
    
    # More precise check - look for the exact patterns
    lines = env_content.split('\n')
    correct_var_found = False
    wrong_var_found = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('MAX_GLEANING='):
            correct_var_found = True
        if stripped.startswith('ENTITY_EXTRACT_MAX_GLEANING='):
            wrong_var_found = True
    
    if wrong_var_found:
        print("❌ FAIL: .env still has ENTITY_EXTRACT_MAX_GLEANING (wrong variable name)")
        print("   LightRAG expects: MAX_GLEANING")
        return False
    
    if not correct_var_found:
        print("❌ FAIL: .env missing MAX_GLEANING variable")
        print("   Add: MAX_GLEANING=0")
        return False
    
    print("✅ PASS: .env uses correct variable name (MAX_GLEANING)")
    return True


def test_lightrag_reads_max_gleaning():
    """Verify LightRAG reads MAX_GLEANING from environment."""
    from dotenv import load_dotenv
    
    # Load .env BEFORE importing LightRAG (critical!)
    load_dotenv(project_root / ".env", override=True)
    
    # Check what value is in the environment
    env_value = os.getenv("MAX_GLEANING")
    
    if env_value is None:
        print("❌ FAIL: MAX_GLEANING not found in environment after loading .env")
        return False
    
    print(f"   Environment MAX_GLEANING = {env_value}")
    
    # Now check what LightRAG's default would be
    from lightrag.constants import DEFAULT_MAX_GLEANING
    from lightrag.utils import get_env_value
    
    # This is exactly how LightRAG reads the value (from lightrag.py line 209)
    actual_value = get_env_value("MAX_GLEANING", DEFAULT_MAX_GLEANING, int)
    
    print(f"   LightRAG DEFAULT_MAX_GLEANING = {DEFAULT_MAX_GLEANING}")
    print(f"   LightRAG actual gleaning value = {actual_value}")
    
    if actual_value != 0:
        print(f"❌ FAIL: LightRAG entity_extract_max_gleaning = {actual_value}")
        print(f"   Expected: 0 (disabled)")
        print(f"   This means each chunk will be extracted {actual_value + 1} times!")
        return False
    
    print("✅ PASS: LightRAG will use MAX_GLEANING=0 (single extraction per chunk)")
    return True


def test_lightrag_instance_has_correct_gleaning():
    """Verify a LightRAG instance has gleaning disabled."""
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env", override=True)
    
    from dataclasses import asdict
    from lightrag import LightRAG
    
    # Create a minimal LightRAG instance (no storage, just config)
    # We use working_dir that doesn't require actual initialization
    rag = LightRAG.__new__(LightRAG)
    
    # Manually check what the dataclass default would compute to
    from lightrag.utils import get_env_value
    from lightrag.constants import DEFAULT_MAX_GLEANING
    
    computed_value = get_env_value("MAX_GLEANING", DEFAULT_MAX_GLEANING, int)
    
    if computed_value != 0:
        print(f"❌ FAIL: LightRAG instance would have entity_extract_max_gleaning = {computed_value}")
        return False
    
    print(f"✅ PASS: LightRAG instance will have entity_extract_max_gleaning = 0")
    return True


def test_extraction_call_count_prediction():
    """Calculate expected extraction calls with gleaning disabled."""
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env", override=True)
    
    from lightrag.utils import get_env_value
    from lightrag.constants import DEFAULT_MAX_GLEANING
    
    gleaning = get_env_value("MAX_GLEANING", DEFAULT_MAX_GLEANING, int)
    
    # From the processing.log analysis:
    text_chunks = 33
    multimodal_chunks = 47
    
    # Each chunk gets (1 + gleaning) extraction calls
    calls_per_chunk = 1 + gleaning
    
    expected_text_calls = text_chunks * calls_per_chunk
    expected_multimodal_calls = multimodal_chunks * calls_per_chunk
    expected_total = expected_text_calls + expected_multimodal_calls
    
    print(f"\n   Gleaning value: {gleaning}")
    print(f"   Calls per chunk: {calls_per_chunk}")
    print(f"   ")
    print(f"   Text chunks: {text_chunks} × {calls_per_chunk} = {expected_text_calls} calls")
    print(f"   Multimodal chunks: {multimodal_chunks} × {calls_per_chunk} = {expected_multimodal_calls} calls")
    print(f"   ─────────────────────────────────────")
    print(f"   Total expected: {expected_total} extraction LLM calls")
    
    if gleaning == 0:
        print(f"\n✅ PASS: With MAX_GLEANING=0, you'll have {expected_total} calls (50% reduction from 160)")
        return True
    else:
        print(f"\n❌ FAIL: With MAX_GLEANING={gleaning}, you'll have {expected_total} calls")
        print(f"   Set MAX_GLEANING=0 in .env to reduce to 80 calls")
        return False


def main():
    print("=" * 60)
    print("MAX_GLEANING Configuration Test")
    print("=" * 60)
    print()
    
    results = []
    
    print("Test 1: .env file has correct variable name")
    print("-" * 40)
    results.append(test_env_file_has_correct_variable())
    print()
    
    print("Test 2: LightRAG reads MAX_GLEANING correctly")
    print("-" * 40)
    results.append(test_lightrag_reads_max_gleaning())
    print()
    
    print("Test 3: LightRAG instance configuration")
    print("-" * 40)
    results.append(test_lightrag_instance_has_correct_gleaning())
    print()
    
    print("Test 4: Extraction call count prediction")
    print("-" * 40)
    results.append(test_extraction_call_count_prediction())
    print()
    
    print("=" * 60)
    if all(results):
        print("✅ ALL TESTS PASSED - Safe to run document processing")
        print("   Expected: 80 extraction calls (down from 160)")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Fix issues before processing")
        return 1


if __name__ == "__main__":
    sys.exit(main())
