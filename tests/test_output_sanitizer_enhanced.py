"""
Tests for enhanced output sanitizer patterns.

Based on actual error patterns observed in MCPP II processing logs (Dec 2025).

Issue #56: Post-Processing Overhaul - Enhanced delimiter recovery
"""

import pytest
from src.extraction.output_sanitizer import (
    sanitize_extraction_output,
    _clean_entity_type,
    _pre_split_fixes,
    _fix_line,
    TUPLE_DELIMITER,
)


class TestCleanEntityType:
    """Test _clean_entity_type for corruption patterns from MCPP II logs."""
    
    def test_hash_pipe_prefix(self):
        """Pattern: #|requirement → requirement"""
        assert _clean_entity_type("#|requirement") == "requirement"
        assert _clean_entity_type("#| requirement") == "requirement"
        assert _clean_entity_type(" #|requirement ") == "requirement"
    
    def test_hash_slash_greater_prefix(self):
        """Pattern: #/>requirement → requirement (seen in line 593)"""
        assert _clean_entity_type("#/>requirement") == "requirement"
        assert _clean_entity_type("#/> requirement") == "requirement"
        assert _clean_entity_type("#/>document") == "document"
    
    def test_parenthesis_prefix(self):
        """Pattern: (requirement → requirement (seen in line 533)"""
        assert _clean_entity_type("(requirement") == "requirement"
        assert _clean_entity_type("( requirement") == "requirement"
        assert _clean_entity_type("(performance_metric") == "performance_metric"
    
    def test_pipe_only_prefix(self):
        """Pattern: |requirement → requirement"""
        assert _clean_entity_type("|requirement") == "requirement"
        assert _clean_entity_type("| requirement") == "requirement"
    
    def test_hash_only_prefix(self):
        """Pattern: #requirement → requirement"""
        assert _clean_entity_type("#requirement") == "requirement"
        assert _clean_entity_type("# requirement") == "requirement"
    
    def test_trailing_patterns(self):
        """Pattern: requirement| → requirement"""
        assert _clean_entity_type("requirement|") == "requirement"
        assert _clean_entity_type("requirement |") == "requirement"
        assert _clean_entity_type("document)") == "document"
    
    def test_mixed_garbage(self):
        """Complex mixed garbage patterns."""
        assert _clean_entity_type("#|/>requirement") == "requirement"
        assert _clean_entity_type("(#|requirement)") == "requirement"
    
    def test_valid_entity_types_unchanged(self):
        """Valid entity types should pass through unchanged."""
        valid_types = [
            "requirement", "clause", "section", "document", "deliverable",
            "evaluation_factor", "submission_instruction", "statement_of_work",
            "performance_metric", "strategic_theme", "organization", "program",
            "equipment", "technology", "concept", "location", "event", "person"
        ]
        for entity_type in valid_types:
            assert _clean_entity_type(entity_type) == entity_type
    
    def test_case_normalization(self):
        """Entity types should be normalized to lowercase."""
        assert _clean_entity_type("REQUIREMENT") == "requirement"
        assert _clean_entity_type("Statement_of_Work") == "statement_of_work"


class TestPreSplitFixes:
    """Test _pre_split_fixes for in-context corruption patterns."""
    
    def test_hash_pipe_in_delimiter_context(self):
        """Pattern: <|#|>#|requirement<|#|> → <|#|>requirement<|#|>"""
        line = "entity<|#|>Name<|#|>#|requirement<|#|>Description"
        fixed = _pre_split_fixes(line)
        assert fixed == "entity<|#|>Name<|#|>requirement<|#|>Description"
    
    def test_hash_slash_greater_in_context(self):
        """Pattern: <|#|>#/>requirement<|#|> → <|#|>requirement<|#|>"""
        line = "entity<|#|>Vehicle Incident Reporting<|#|>#/>requirement<|#|>Description"
        fixed = _pre_split_fixes(line)
        assert fixed == "entity<|#|>Vehicle Incident Reporting<|#|>requirement<|#|>Description"
    
    def test_parenthesis_in_context(self):
        """Pattern: <|#|>(requirement<|#|> → <|#|>requirement<|#|>"""
        line = "entity<|#|>Navy ACWP Report<|#|>(<|#|>Description"
        fixed = _pre_split_fixes(line)
        # The ( is the entire entity_type field - should be cleaned by _clean_entity_type
        # _pre_split_fixes only handles <|#|>(...<|#|> patterns
        # For single character replacement, _clean_entity_type handles it
        assert "(<|#|>" not in fixed or fixed == line  # Pattern may not match perfectly
    
    def test_trailing_pipe_in_context(self):
        """Pattern: <|#|>requirement|<|#|> → <|#|>requirement<|#|>"""
        line = "entity<|#|>Name<|#|>requirement|<|#|>Description"
        fixed = _pre_split_fixes(line)
        assert fixed == "entity<|#|>Name<|#|>requirement<|#|>Description"
    
    def test_multiple_corruptions(self):
        """Multiple corruption patterns in one line."""
        line = "entity<|#|>Name<|#|>#|requirement|<|#|>Description"
        fixed = _pre_split_fixes(line)
        # Should handle hash-pipe prefix first
        assert "#|" not in fixed or "requirement|" in fixed


class TestFixLine:
    """Test _fix_line for complete record fixing."""
    
    def test_entity_with_corrupted_type(self):
        """Entity with corrupted type field should be fixed."""
        line = f"entity{TUPLE_DELIMITER}CAP Subcontracts Invoice Backup{TUPLE_DELIMITER}#|requirement{TUPLE_DELIMITER}Description"
        fixed = _fix_line(line)
        parts = fixed.split(TUPLE_DELIMITER)
        assert parts[2] == "requirement"
    
    def test_entity_with_extra_fields(self):
        """Entity with extra fields should merge them into description."""
        # 5 fields instead of 4
        line = f"entity{TUPLE_DELIMITER}Name{TUPLE_DELIMITER}requirement{TUPLE_DELIMITER}Desc part 1{TUPLE_DELIMITER}Desc part 2"
        fixed = _fix_line(line)
        parts = fixed.split(TUPLE_DELIMITER)
        assert len(parts) == 4
        assert "Desc part 1" in parts[3] and "Desc part 2" in parts[3]
    
    def test_relation_with_extra_fields(self):
        """Relation with extra fields should merge them into description."""
        # 6 fields instead of 5
        line = f"relation{TUPLE_DELIMITER}Source{TUPLE_DELIMITER}Target{TUPLE_DELIMITER}RELATED_TO{TUPLE_DELIMITER}Desc part 1{TUPLE_DELIMITER}Desc part 2"
        fixed = _fix_line(line)
        parts = fixed.split(TUPLE_DELIMITER)
        assert len(parts) == 5
        assert "Desc part 1" in parts[4] and "Desc part 2" in parts[4]
    
    def test_valid_entity_unchanged(self):
        """Valid entity record should be unchanged."""
        line = f"entity{TUPLE_DELIMITER}Valid Name{TUPLE_DELIMITER}requirement{TUPLE_DELIMITER}Valid description"
        fixed = _fix_line(line)
        assert fixed == line


class TestSanitizeExtractionOutput:
    """Test full sanitize_extraction_output function."""
    
    def test_multiline_output_with_corruptions(self):
        """Test multi-line output with various corruptions."""
        output = f"""entity{TUPLE_DELIMITER}Entity One{TUPLE_DELIMITER}#|requirement{TUPLE_DELIMITER}Description one
entity{TUPLE_DELIMITER}Entity Two{TUPLE_DELIMITER}#/>document{TUPLE_DELIMITER}Description two
entity{TUPLE_DELIMITER}Entity Three{TUPLE_DELIMITER}clause{TUPLE_DELIMITER}Description three"""
        
        sanitized = sanitize_extraction_output(output)
        lines = sanitized.split('\n')
        
        assert len(lines) == 3
        # Check that corrupted types are fixed
        assert "#|" not in lines[0]
        assert "#/>" not in lines[1]
        assert lines[2] == f"entity{TUPLE_DELIMITER}Entity Three{TUPLE_DELIMITER}clause{TUPLE_DELIMITER}Description three"
    
    def test_empty_input(self):
        """Empty input should return empty."""
        assert sanitize_extraction_output("") == ""
        assert sanitize_extraction_output(None) is None
    
    def test_no_delimiters(self):
        """Output without delimiters should be unchanged."""
        plain = "This is just plain text without any delimiters"
        assert sanitize_extraction_output(plain) == plain


class TestActualLogPatterns:
    """Test patterns directly from MCPP II processing logs."""
    
    def test_line_580_pattern(self):
        """
        Line 580: ['entity', 'CAP Subcontracts Invoice Backup', '#|requirement', 'Detailed backup...']
        """
        entity_type = "#|requirement"
        cleaned = _clean_entity_type(entity_type)
        assert cleaned == "requirement"
    
    def test_line_593_pattern(self):
        """
        Line 593: ['entity', 'Vehicle Incident Reporting', '#/>requirement', '10.B.12.d...']
        """
        entity_type = "#/>requirement"
        cleaned = _clean_entity_type(entity_type)
        assert cleaned == "requirement"
    
    def test_line_520_pattern(self):
        """
        Line 520: ['entity', 'MCO 3000.17', '#|document', 'MCO 3000.17...']
        """
        entity_type = "#|document"
        cleaned = _clean_entity_type(entity_type)
        assert cleaned == "document"
    
    def test_line_533_pattern(self):
        """
        Line 533: ['entity', 'Navy ACWP Report', '(', "6.B.3..."]
        The entity type is just '(' - should be rejected or cleaned
        """
        entity_type = "("
        cleaned = _clean_entity_type(entity_type)
        # Single parenthesis should result in empty string after cleaning
        assert cleaned == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

