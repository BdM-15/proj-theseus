import asyncio
import json

# Import the module under test
from src.inference import semantic_post_processor as spp

async def mock_llm(prompt, model=None, temperature=None):
    # This mock ignores the prompt and returns a JSON array using IDs
    # It simulates the LLM returning ID-based relationships as instructed.
    resp = [
        {
            "source_id": "entity-2",
            "target_id": "entity-1",
            "type": "EVALUATES",
            "confidence": 0.92,
            "reasoning": "Evaluation factor 2 maps to requirement 1 based on scope overlap"
        }
    ]
    return json.dumps(resp)

async def run_test():
    # Build a tiny entity set mirroring Neo4j structure returned by Neo4jGraphIO.get_all_entities()
    entities = [
        {"id": "entity-1", "entity_name": "Task Order Management Plan (TOMP)", "entity_type": "requirement", "description": "Develop TOMP"},
        {"id": "entity-2", "entity_name": "Subfactor 1.1: Task Order Management Plan (TOMP)", "entity_type": "evaluation_factor", "description": "Evaluation criteria referencing TOMP"},
        {"id": "entity-3", "entity_name": "Monthly Report", "entity_type": "deliverable", "description": "Submit monthly"},
    ]

    # Monkeypatch the module's _call_llm_async with our mock
    spp._call_llm_async = mock_llm

    # Call the async function under test
    relationships = await spp._infer_relationships_batch(
        entities=entities,
        existing_rels=[],
        model="grok-4-fast-reasoning",
        temperature=0.1
    )

    print("\n=== TEST OUTPUT ===\n")
    print(f"Returned {len(relationships)} relationships")
    for r in relationships:
        print(json.dumps(r, indent=2))

    # Basic assertions
    assert len(relationships) == 1, "Expected 1 relationship from mock LLM"
    rel = relationships[0]
    assert rel["source_id"] == "entity-2"
    assert rel["target_id"] == "entity-1"
    assert rel["relationship_type"] == "EVALUATES"
    print("\nTest passed: ID-based relationship inference works as expected")

if __name__ == "__main__":
    asyncio.run(run_test())
