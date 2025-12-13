"""
Test LightRAG Default Behavior Restoration
==========================================

Verifies that the query pipeline uses LightRAG defaults without custom overrides.

Test Categories:
1. No query-time PROMPTS modifications
2. No ontology context injection
3. No custom user_prompt loading
4. Clean QueryParam passthrough

Run: python -m pytest tests/test_lightrag_defaults_restored.py -v
"""

import ast
import os


def test_routes_no_ontology_context_import():
    """Verify routes.py doesn't import build_query_context."""
    with open("src/server/routes.py", "r") as f:
        content = f.read()
    
    # Should be commented out or removed
    assert "from src.query.ontology_context import build_query_context" not in content or \
           "# from src.query.ontology_context import build_query_context" in content, \
           "build_query_context should not be actively imported in routes.py"


def test_routes_no_prompt_loader_import():
    """Verify routes.py doesn't import load_prompt."""
    with open("src/server/routes.py", "r") as f:
        content = f.read()
    
    # Should be commented out or removed
    assert "from src.core.prompt_loader import load_prompt" not in content or \
           "# from src.core.prompt_loader import load_prompt" in content, \
           "load_prompt should not be actively imported in routes.py"


def test_initialization_no_prompts_keyword_override():
    """Verify initialization.py doesn't override PROMPTS['keywords_extraction_examples']."""
    with open("src/server/initialization.py", "r") as f:
        content = f.read()
    
    # Should not contain keyword extraction override
    assert 'PROMPTS["keywords_extraction_examples"] = [' not in content, \
           "initialization.py should not override keywords_extraction_examples"


def test_initialization_no_prompts_rag_response_override():
    """Verify initialization.py doesn't override PROMPTS['rag_response']."""
    with open("src/server/initialization.py", "r") as f:
        content = f.read()
    
    # Should not contain rag_response override
    assert 'PROMPTS["rag_response"] = (' not in content, \
           "initialization.py should not override rag_response"


def test_initialization_preserves_entity_extraction_examples_fix():
    """Verify the critical entity_extraction_examples fix is preserved."""
    with open("src/server/initialization.py", "r") as f:
        content = f.read()
    
    # This fix prevents ontology contamination from LightRAG's fictional examples
    assert 'PROMPTS["entity_extraction_examples"] = []' in content, \
           "entity_extraction_examples = [] fix must be preserved to prevent ontology contamination"


def test_query_override_files_deleted():
    """Verify unused query override files are deleted."""
    deleted_files = [
        "src/query/analysis_override.py",
        "src/query/compliance_override.py"
    ]
    
    for filepath in deleted_files:
        assert not os.path.exists(filepath), \
               f"Unused override file should be deleted: {filepath}"


def test_ontology_context_has_deprecation_notice():
    """Verify ontology_context.py has deprecation notice."""
    with open("src/query/ontology_context.py", "r") as f:
        content = f.read()
    
    assert "DEPRECATED" in content, \
           "ontology_context.py should have DEPRECATED notice"


def test_cursor_rules_exist():
    """Verify .cursor/rules protection files exist."""
    required_rules = [
        ".cursor/rules/ontology-protection.mdc",
        ".cursor/rules/prompt-protection.mdc",
        ".cursor/rules/framework-fidelity.mdc"
    ]
    
    for rulefile in required_rules:
        assert os.path.exists(rulefile), \
               f"Cursor rule file should exist: {rulefile}"


def test_ontology_entity_types_unchanged():
    """Verify the 18 entity types are unchanged."""
    with open("src/ontology/schema.py", "r") as f:
        content = f.read()
    
    # The sacred 18 entity types
    expected_types = {
        "organization", "concept", "event", "technology", "person", "location",
        "requirement", "clause", "section", "document", "deliverable",
        "evaluation_factor", "submission_instruction", "program", "equipment",
        "strategic_theme", "statement_of_work", "performance_metric"
    }
    
    for entity_type in expected_types:
        assert f'"{entity_type}"' in content, \
               f"Entity type must be preserved: {entity_type}"


def test_routes_query_endpoint_uses_defaults():
    """Verify query endpoint passes through to LightRAG defaults."""
    with open("src/server/routes.py", "r") as f:
        content = f.read()
    
    # Should have the default behavior comment
    assert "LIGHTRAG DEFAULT BEHAVIOR" in content or "LightRAG defaults" in content, \
           "Query endpoint should document use of LightRAG defaults"
    
    # Should not have hardcoded keywords
    assert "hl_keywords = [" not in content, \
           "Query endpoint should not hardcode hl_keywords"
    assert "ll_keywords = [" not in content, \
           "Query endpoint should not hardcode ll_keywords"


if __name__ == "__main__":
    # Simple test runner if pytest not available
    tests = [
        test_routes_no_ontology_context_import,
        test_routes_no_prompt_loader_import,
        test_initialization_no_prompts_keyword_override,
        test_initialization_no_prompts_rag_response_override,
        test_initialization_preserves_entity_extraction_examples_fix,
        test_query_override_files_deleted,
        test_ontology_context_has_deprecation_notice,
        test_cursor_rules_exist,
        test_ontology_entity_types_unchanged,
        test_routes_query_endpoint_uses_defaults,
    ]
    
    passed = 0
    failed = 0
    
    print("=" * 80)
    print("LightRAG Defaults Restoration Tests")
    print("=" * 80)
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1
    
    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80)
    
    exit(0 if failed == 0 else 1)
