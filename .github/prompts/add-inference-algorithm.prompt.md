# Add Inference Algorithm

Add a new semantic post-processing algorithm for relationship inference.

## Instructions

Adding a new inference algorithm requires:

1. **Prompt Template** (`prompts/relationship_inference/[algorithm].md`)

   - Clear instructions for the LLM
   - Examples of expected input/output
   - Edge case handling

2. **Implementation** (`src/inference/relationship_operations.py`)

   - Async function following existing patterns
   - Uses batch processor for LLM calls
   - Returns list of new relationships

3. **Registration** (`src/inference/semantic_post_processor.py`)

   - Add to INFERENCE_ALGORITHMS list
   - Configure execution order

4. **Tests** (`tests/test_neo4j_postprocessing.py`)
   - Mock LLM responses
   - Verify relationship creation

## Algorithm Template

```python
async def infer_[algorithm]_relationships(
    entities: List[Dict],
    existing_relationships: List[Dict],
    llm_func: Callable,
    batch_size: int = 50
) -> List[Dict]:
    """
    Infer [relationship type] between [source types] and [target types].

    Algorithm:
    1. Filter entities by relevant types
    2. Create (source, targets) pairs for LLM analysis
    3. Batch process with LLM
    4. Parse responses into relationship dictionaries
    5. Deduplicate against existing relationships

    Returns:
        List of new relationships with keys:
        - source: source entity name
        - target: target entity name
        - relationship_type: e.g., "EVALUATED_BY"
        - confidence: float 0.0-1.0
        - reasoning: human-readable explanation
    """
    pass
```

## Prompt Template Structure

````markdown
# [Algorithm Name] Relationship Inference

## Task

Identify [relationship type] relationships between entities.

## Input Format

You will receive:

- Source entities: [type description]
- Target entities: [type description]

## Output Format

Return JSON array:

```json
[
  {
    "source": "entity name",
    "target": "entity name",
    "confidence": 0.85,
    "reasoning": "explanation"
  }
]
```
````

## Examples

[Provide 2-3 examples]

## Rules

- Only create relationships with strong evidence
- Confidence > 0.7 for inclusion
- [Domain-specific rules]

```

## Existing Algorithms Reference

| Algorithm | Source Type | Target Type | Relationship |
|-----------|-------------|-------------|--------------|
| requirement_evaluation | requirement | evaluation_factor | EVALUATED_BY |
| instruction_evaluation_linking | submission_instruction | evaluation_factor | GUIDES |
| document_hierarchy | document | section | CHILD_OF |
| clause_clustering | clause | section | CHILD_OF |
| sow_deliverable_linking | statement_of_work | deliverable | REQUIRES |
```
