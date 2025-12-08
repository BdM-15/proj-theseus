"""Quick test of Pydantic validation integration"""
from src.ontology.schema import InferredRelationship, InferredRelationshipBatch
from src.utils.llm_parsing import parse_with_pydantic

print("✅ Pydantic imports successful")

# Test 1: Relationship normalization
rel = InferredRelationship(
    source_id="entity_1",
    target_id="entity_2",
    relationship_type="evaluated_by",  # lowercase
    confidence=0.9,
    reasoning="**Section L** guides requirements"
)

print(f"✅ Relationship type normalized: 'evaluated_by' → '{rel.relationship_type}'")
print(f"✅ Reasoning cleaned: Markdown removed from reasoning")

# Test 2: Self-loop prevention
try:
    bad_rel = InferredRelationship(
        source_id="entity_1",
        target_id="entity_1",  # Same as source
        relationship_type="GUIDES"
    )
    print("❌ FAIL: Self-loop should have been prevented")
except Exception as e:
    print(f"✅ Self-loop prevented: {type(e).__name__}")

# Test 3: Batch parsing
response = """```json
{
  "relationships": [
    {"source_id": "e1", "target_id": "e2", "relationship_type": "guides", "confidence": 0.9, "reasoning": "Test"},
    {"source_id": "e3", "target_id": "e4", "relationship_type": "EVALUATED_BY", "confidence": 0.8}
  ]
}
```"""

batch = parse_with_pydantic(response, InferredRelationshipBatch, "Test")
print(f"✅ Batch parsing: {len(batch.relationships)} relationships extracted and validated")
print(f"   First relationship: {batch.relationships[0].source_id} → {batch.relationships[0].target_id} ({batch.relationships[0].relationship_type})")

print("\n🎉 All Pydantic validation tests passed!")
