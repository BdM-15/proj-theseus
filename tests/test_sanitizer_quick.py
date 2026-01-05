"""Quick validation tests for output sanitizer enhancements."""

from src.extraction.output_sanitizer import (
    sanitize_extraction_output,
    _clean_entity_type,
    _pre_split_fixes,
)


def test_clean_entity_type_hash_pipe():
    """Test _clean_entity_type removes #| prefix."""
    result = _clean_entity_type('#|person')
    assert result == 'person', f'Expected person, got {result}'
    print('✅ Test 1 PASSED: #|person → person')


def test_clean_entity_type_with_spaces():
    """Test _clean_entity_type handles space variations."""
    result = _clean_entity_type('# | person')
    assert result == 'person', f'Expected person, got {result}'
    print('✅ Test 2 PASSED: "# | person" → person')


def test_clean_entity_type_multiword():
    """Test _clean_entity_type handles multi-word entity types (spaces → underscores)."""
    result = _clean_entity_type('#|person role')
    # Note: _clean_entity_type converts spaces to underscores for valid entity types
    assert result == 'person_role', f'Expected "person_role", got {result}'
    print('✅ Test 3 PASSED: #|person role → person_role')


def test_clean_entity_type_reversed():
    """Test _clean_entity_type handles reversed |# pattern."""
    result = _clean_entity_type('|#person')
    assert result == 'person', f'Expected person, got {result}'
    print('✅ Test 4 PASSED: |#person → person')


def test_pre_split_fixes_multiword():
    """Test _pre_split_fixes handles multi-word entity types."""
    line = 'entity<|#|>COR<|#|>#|person role<|#|>Description'
    result = _pre_split_fixes(line)
    assert '#|person' not in result, f'#|person still in result: {result}'
    # Pre-split preserves multi-word; _clean_entity_type handles underscore conversion later
    assert '<|#|>person role<|#|>' in result or '<|#|>person_role<|#|>' in result, f'Expected person field, got: {result}'
    print(f'✅ Test 5 PASSED: Pre-split fixes multi-word')
    print(f'   Input:  {line}')
    print(f'   Output: {result}')


def test_full_sanitization_pipeline():
    """Test complete sanitization pipeline catches #|person."""
    text = '''(entity<|#|>COR Contracting Officer Representative<|#|>#|person<|#|>A government official)
(relationship<|#|>COR<|#|>Government<|#|>works_for<|#|>COR works for government)'''
    result = sanitize_extraction_output(text)
    assert '<|#|>person<|#|>' in result, f'Expected person field, got: {result}'
    assert '#|person' not in result, f'#|person should be removed'
    print('✅ Test 6 PASSED: Full pipeline sanitization')


def test_edge_cases():
    """Test various edge cases."""
    # Multiple hash-pipes
    assert _clean_entity_type('#|#|person') == 'person'
    print('✅ Test 7a: #|#|person → person')
    
    # Trailing pipe
    assert _clean_entity_type('person|') == 'person'
    print('✅ Test 7b: person| → person')
    
    # Hash-slash-greater
    assert _clean_entity_type('#/>requirement') == 'requirement'
    print('✅ Test 7c: #/>requirement → requirement')


if __name__ == '__main__':
    print('=' * 60)
    print('Output Sanitizer Enhancement Tests')
    print('=' * 60)
    
    test_clean_entity_type_hash_pipe()
    test_clean_entity_type_with_spaces()
    test_clean_entity_type_multiword()
    test_clean_entity_type_reversed()
    test_pre_split_fixes_multiword()
    test_full_sanitization_pipeline()
    test_edge_cases()
    
    print('=' * 60)
    print('🎉 All tests passed!')
    print('=' * 60)
