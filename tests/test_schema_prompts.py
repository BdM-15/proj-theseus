"""
Unit Tests for Schema-Driven LLM Prompt Utilities (Issue #43)
==============================================================

Tests the schema extraction utilities that replace brittle hardcoded
keyword lists with Pydantic schema-driven LLM guidance.

Tests:
1. Single schema extraction (get_schema_guidance)
2. Multi-schema combination (get_multi_schema_guidance)
3. Entity type guidance (get_entity_type_guidance)
4. Specialized guidance functions
5. Schema field description extraction

Usage:
    python -m pytest tests/test_schema_prompts.py -v
    python tests/test_schema_prompts.py
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest


class TestSchemaPrompts(unittest.TestCase):
    """Test schema prompt extraction utilities."""
    
    def test_module_imports(self):
        """Test that schema_prompts module imports correctly."""
        from src.inference import schema_prompts
        self.assertTrue(hasattr(schema_prompts, 'get_schema_guidance'))
        self.assertTrue(hasattr(schema_prompts, 'get_multi_schema_guidance'))
        self.assertTrue(hasattr(schema_prompts, 'get_entity_type_guidance'))
        self.assertTrue(hasattr(schema_prompts, 'get_document_hierarchy_guidance'))
        self.assertTrue(hasattr(schema_prompts, 'get_evaluation_hierarchy_guidance'))
        self.assertTrue(hasattr(schema_prompts, 'get_instruction_evaluation_guidance'))
    
    def test_get_schema_guidance_evaluation_factor(self):
        """Test schema extraction for EvaluationFactor model."""
        from src.inference.schema_prompts import get_schema_guidance
        from src.ontology.schema import EvaluationFactor
        
        guidance = get_schema_guidance(EvaluationFactor)
        
        # Should contain model name
        self.assertIn('EvaluationFactor', guidance)
        
        # Should contain field descriptions from Pydantic schema
        self.assertIn('weight', guidance)
        self.assertIn('importance', guidance)
        self.assertIn('subfactors', guidance)
        
        # Should contain semantic hints for this model type
        self.assertIn('IDENTIFICATION HINTS', guidance)
        self.assertIn('Main factors', guidance)
        self.assertIn('Rating scales', guidance)
    
    def test_get_schema_guidance_submission_instruction(self):
        """Test schema extraction for SubmissionInstruction model."""
        from src.inference.schema_prompts import get_schema_guidance
        from src.ontology.schema import SubmissionInstruction
        
        guidance = get_schema_guidance(SubmissionInstruction)
        
        # Should contain model name
        self.assertIn('SubmissionInstruction', guidance)
        
        # Should contain field descriptions from Pydantic schema
        self.assertIn('page_limit', guidance)
        self.assertIn('format_reqs', guidance)
        self.assertIn('volume', guidance)
        
        # Should contain semantic hints
        self.assertIn('IDENTIFICATION HINTS', guidance)
    
    def test_get_schema_guidance_requirement(self):
        """Test schema extraction for Requirement model."""
        from src.inference.schema_prompts import get_schema_guidance
        from src.ontology.schema import Requirement
        
        guidance = get_schema_guidance(Requirement)
        
        # Should contain model name
        self.assertIn('Requirement', guidance)
        
        # Should contain field descriptions
        self.assertIn('criticality', guidance)
        self.assertIn('modal_verb', guidance)
        self.assertIn('labor_drivers', guidance)
        
        # Should contain semantic hints
        self.assertIn('MANDATORY', guidance)
        self.assertIn('shall', guidance)
    
    def test_get_multi_schema_guidance(self):
        """Test combining multiple schema guidances."""
        from src.inference.schema_prompts import get_multi_schema_guidance
        from src.ontology.schema import EvaluationFactor, SubmissionInstruction
        
        guidance = get_multi_schema_guidance(EvaluationFactor, SubmissionInstruction)
        
        # Should contain both model names
        self.assertIn('EvaluationFactor', guidance)
        self.assertIn('SubmissionInstruction', guidance)
        
        # Should contain fields from both models
        self.assertIn('weight', guidance)
        self.assertIn('page_limit', guidance)
    
    def test_get_entity_type_guidance(self):
        """Test entity type guidance extraction from VALID_ENTITY_TYPES."""
        from src.inference.schema_prompts import get_entity_type_guidance
        
        guidance = get_entity_type_guidance()
        
        # Should contain header
        self.assertIn('VALID ENTITY TYPES', guidance)
        
        # Should contain type categories
        self.assertIn('Document Structure', guidance)
        self.assertIn('Evaluation', guidance)
        self.assertIn('Work Items', guidance)
        
        # Should contain hierarchy patterns
        self.assertIn('HIERARCHY PATTERNS', guidance)
        self.assertIn('CHILD_OF', guidance)
        self.assertIn('ATTACHMENT_OF', guidance)
    
    def test_get_document_hierarchy_guidance(self):
        """Test specialized document hierarchy guidance."""
        from src.inference.schema_prompts import get_document_hierarchy_guidance
        
        guidance = get_document_hierarchy_guidance()
        
        # Should contain document-specific content
        self.assertIn('DOCUMENT HIERARCHY', guidance)
        self.assertIn('DOCUMENT ENTITY TYPES', guidance)
        self.assertIn('HIERARCHY RELATIONSHIP TYPES', guidance)
        
        # Should contain relationship types
        self.assertIn('CHILD_OF', guidance)
        self.assertIn('ATTACHMENT_OF', guidance)
        self.assertIn('AMENDS', guidance)
        
        # Should contain identification patterns
        self.assertIn('Section numbering', guidance)
    
    def test_get_evaluation_hierarchy_guidance(self):
        """Test specialized evaluation hierarchy guidance."""
        from src.inference.schema_prompts import get_evaluation_hierarchy_guidance
        
        guidance = get_evaluation_hierarchy_guidance()
        
        # Should contain evaluation-specific content
        self.assertIn('EvaluationFactor', guidance)
        self.assertIn('EVALUATION HIERARCHY PATTERNS', guidance)
        
        # Should contain relationship types
        self.assertIn('HAS_SUBFACTOR', guidance)
        self.assertIn('HAS_RATING_SCALE', guidance)
        self.assertIn('MEASURED_BY', guidance)
        
        # Should mention discovering all factors regardless of naming
        self.assertIn('Small Business Participation', guidance)
    
    def test_get_instruction_evaluation_guidance(self):
        """Test specialized instruction-evaluation guidance."""
        from src.inference.schema_prompts import get_instruction_evaluation_guidance
        
        guidance = get_instruction_evaluation_guidance()
        
        # Should contain both schema types
        self.assertIn('SubmissionInstruction', guidance)
        self.assertIn('EvaluationFactor', guidance)
        
        # Should contain linking patterns
        self.assertIn('INSTRUCTION-EVALUATION LINKING', guidance)
        self.assertIn('GUIDES', guidance)
        
        # Should mention schema-driven identification
        self.assertIn('page_limit', guidance)
        self.assertIn('format_reqs', guidance)
    
    def test_schema_guidance_no_entity_name_type(self):
        """Test that entity_name and entity_type are excluded from guidance."""
        from src.inference.schema_prompts import get_schema_guidance
        from src.ontology.schema import EvaluationFactor
        
        guidance = get_schema_guidance(EvaluationFactor)
        
        # entity_name and entity_type should be excluded (they're internal)
        lines = guidance.split('\n')
        field_lines = [l for l in lines if l.startswith('- ')]
        
        # None of the field lines should start with entity_name or entity_type
        for line in field_lines:
            self.assertFalse(line.startswith('- entity_name'))
            self.assertFalse(line.startswith('- entity_type'))


class TestSchemaPromptIntegration(unittest.TestCase):
    """Test integration with semantic_post_processor."""
    
    def test_semantic_post_processor_imports_schema_prompts(self):
        """Verify semantic_post_processor imports schema prompt utilities."""
        from src.inference import semantic_post_processor
        
        # Check that schema guidance functions are available
        # (imported at module level for use in algorithms)
        module_source = open('src/inference/semantic_post_processor.py', encoding='utf-8').read()
        
        self.assertIn('from src.inference.schema_prompts import', module_source)
        self.assertIn('get_instruction_evaluation_guidance', module_source)
        self.assertIn('get_evaluation_hierarchy_guidance', module_source)
        self.assertIn('get_document_hierarchy_guidance', module_source)
    
    def test_algorithm_1_uses_schema_guidance(self):
        """Verify Algorithm 1 function uses schema-driven approach."""
        module_source = open('src/inference/semantic_post_processor.py', encoding='utf-8').read()
        
        # Check for schema guidance usage in Algorithm 1
        self.assertIn('get_instruction_evaluation_guidance()', module_source)
        
        # Check that SCHEMA-DRIVEN comment is present
        self.assertIn('SCHEMA-DRIVEN', module_source)
    
    def test_algorithm_2_uses_schema_guidance(self):
        """Verify Algorithm 2 function uses schema-driven approach."""
        module_source = open('src/inference/semantic_post_processor.py', encoding='utf-8').read()
        
        # Check for schema guidance usage in Algorithm 2
        self.assertIn('get_evaluation_hierarchy_guidance()', module_source)
    
    def test_algorithm_5_uses_schema_guidance(self):
        """Verify Algorithm 5 function uses schema-driven approach."""
        module_source = open('src/inference/semantic_post_processor.py', encoding='utf-8').read()
        
        # Check for schema guidance usage in Algorithm 5
        self.assertIn('get_document_hierarchy_guidance()', module_source)


class TestSchemaFieldExtraction(unittest.TestCase):
    """Test Pydantic schema field extraction."""
    
    def test_pydantic_schema_has_descriptions(self):
        """Verify Pydantic models have field descriptions (required for schema guidance)."""
        from src.ontology.schema import EvaluationFactor, SubmissionInstruction, Requirement
        
        # EvaluationFactor should have field descriptions
        ef_schema = EvaluationFactor.model_json_schema()
        ef_props = ef_schema.get('properties', {})
        
        self.assertIn('description', ef_props.get('weight', {}))
        self.assertIn('description', ef_props.get('importance', {}))
        self.assertIn('description', ef_props.get('subfactors', {}))
        
        # SubmissionInstruction should have field descriptions
        si_schema = SubmissionInstruction.model_json_schema()
        si_props = si_schema.get('properties', {})
        
        self.assertIn('description', si_props.get('page_limit', {}))
        self.assertIn('description', si_props.get('format_reqs', {}))
        self.assertIn('description', si_props.get('volume', {}))
        
        # Requirement should have field descriptions
        req_schema = Requirement.model_json_schema()
        req_props = req_schema.get('properties', {})
        
        self.assertIn('description', req_props.get('criticality', {}))
        self.assertIn('description', req_props.get('modal_verb', {}))
    
    def test_valid_entity_types_contains_expected_types(self):
        """Verify VALID_ENTITY_TYPES contains expected document types."""
        from src.ontology.schema import VALID_ENTITY_TYPES
        
        # Document types should be present
        self.assertIn('document', VALID_ENTITY_TYPES)
        self.assertIn('section', VALID_ENTITY_TYPES)
        self.assertIn('clause', VALID_ENTITY_TYPES)
        
        # Evaluation types should be present
        self.assertIn('evaluation_factor', VALID_ENTITY_TYPES)
        self.assertIn('submission_instruction', VALID_ENTITY_TYPES)
        
        # Work types should be present
        self.assertIn('requirement', VALID_ENTITY_TYPES)
        self.assertIn('deliverable', VALID_ENTITY_TYPES)


def run_tests():
    """Run all tests with verbose output."""
    print("\n" + "="*80)
    print("SCHEMA PROMPTS UNIT TESTS (Issue #43)")
    print("="*80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaPrompts))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaPromptIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaFieldExtraction))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(run_tests())

