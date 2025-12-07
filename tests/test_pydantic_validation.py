"""
Test Pydantic Validation for InferredRelationship Models
=========================================================

Quick validation that Phase 3 Pydantic models work correctly:
- InferredRelationship field validators
- Self-loop prevention
- Graceful error handling
"""

from src.ontology.schema import InferredRelationship, InferredRelationshipBatch
from pydantic import ValidationError


def test_valid_relationship():
    """Test that valid relationship passes validation."""
    rel = InferredRelationship(
        source_id="entity_1",
        target_id="entity_2",
        relationship_type="evaluated_by",
        confidence=0.9,
        reasoning="Section L guides requirements in Section C"
    )
    
    assert rel.source_id == "entity_1"
    assert rel.target_id == "entity_2"
    assert rel.relationship_type == "EVALUATED_BY"  # Should be normalized to uppercase
    assert rel.confidence == 0.9
    assert rel.reasoning == "Section L guides requirements in Section C"
    print("✅ Valid relationship passes validation")


def test_self_loop_prevention():
    """Test that self-loops are prevented."""
    try:
        rel = InferredRelationship(
            source_id="entity_1",
            target_id="entity_1",  # Same as source - should fail
            relationship_type="GUIDES"
        )
        print("❌ Self-loop should have been prevented!")
        assert False, "Self-loop was not prevented"
    except ValidationError as e:
        assert "Self-loop detected" in str(e)
        print("✅ Self-loop prevention works")


def test_relationship_type_normalization():
    """Test that relationship types are normalized to uppercase."""
    rel = InferredRelationship(
        source_id="entity_1",
        target_id="entity_2",
        relationship_type="evaluated_by"  # lowercase
    )
    
    assert rel.relationship_type == "EVALUATED_BY"  # Should be uppercase
    print("✅ Relationship type normalization works")


def test_reasoning_cleanup():
    """Test that markdown is stripped from reasoning."""
    rel = InferredRelationship(
        source_id="entity_1",
        target_id="entity_2",
        relationship_type="GUIDES",
        reasoning="**This** is *formatted*  with   extra   spaces"
    )
    
    # Should remove markdown and collapse spaces
    assert "**" not in rel.reasoning
    assert "*" not in rel.reasoning
    assert "   " not in rel.reasoning
    print("✅ Reasoning cleanup works")


def test_batch_response_handling():
    """Test that InferredRelationshipBatch handles various formats."""
    # Format 1: Standard dict with relationships key
    batch1 = InferredRelationshipBatch(relationships=[
        {"source_id": "e1", "target_id": "e2", "relationship_type": "GUIDES"}
    ])
    assert len(batch1.relationships) == 1
    
    # Format 2: Direct array (use model_validate to trigger validator)
    batch2 = InferredRelationshipBatch.model_validate([
        {"source_id": "e1", "target_id": "e2", "relationship_type": "GUIDES"}
    ])
    assert len(batch2.relationships) == 1
    
    # Format 3: Alternative key (results)
    batch3 = InferredRelationshipBatch.model_validate({
        "results": [{"source_id": "e1", "target_id": "e2", "relationship_type": "GUIDES"}]
    })
    assert len(batch3.relationships) == 1
    
    print("✅ Batch response format handling works")


def test_confidence_bounds():
    """Test that confidence is bounded 0.0-1.0."""
    # Valid confidence
    rel1 = InferredRelationship(
        source_id="e1",
        target_id="e2",
        relationship_type="GUIDES",
        confidence=0.5
    )
    assert rel1.confidence == 0.5
    
    # Invalid confidence (too high)
    try:
        rel2 = InferredRelationship(
            source_id="e1",
            target_id="e2",
            relationship_type="GUIDES",
            confidence=1.5  # > 1.0
        )
        print("❌ Confidence > 1.0 should have failed!")
        assert False
    except ValidationError:
        pass
    
    # Invalid confidence (negative)
    try:
        rel3 = InferredRelationship(
            source_id="e1",
            target_id="e2",
            relationship_type="GUIDES",
            confidence=-0.1
        )
        print("❌ Negative confidence should have failed!")
        assert False
    except ValidationError:
        pass
    
    print("✅ Confidence bounds validation works")


def test_to_dict_conversion():
    """Test backward compatibility with to_dict()."""
    rel = InferredRelationship(
        source_id="entity_1",
        target_id="entity_2",
        relationship_type="GUIDES",
        confidence=0.8,
        reasoning="Test reasoning"
    )
    
    d = rel.to_dict()
    assert isinstance(d, dict)
    assert d['source_id'] == "entity_1"
    assert d['target_id'] == "entity_2"
    assert d['relationship_type'] == "GUIDES"
    assert d['confidence'] == 0.8
    assert d['reasoning'] == "Test reasoning"
    
    print("✅ to_dict() backward compatibility works")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("PYDANTIC VALIDATION TESTS (Phase 3)")
    print("="*80 + "\n")
    
    test_valid_relationship()
    test_self_loop_prevention()
    test_relationship_type_normalization()
    test_reasoning_cleanup()
    test_batch_response_handling()
    test_confidence_bounds()
    test_to_dict_conversion()
    
    print("\n" + "="*80)
    print("🎉 ALL PYDANTIC VALIDATION TESTS PASSED")
    print("="*80 + "\n")
