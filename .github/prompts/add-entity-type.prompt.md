# Add Entity Type

Add a new entity type to the GovCon Capture Vibe ontology.

## Instructions

Adding a new entity type requires changes to multiple files:

1. **Schema Definition** (`src/ontology/schema.py`)

   - Add Pydantic model with type-specific fields
   - Include in the EntityType enum

2. **Configuration** (`src/server/config.py`)

   - Add to `global_args.entity_types` list (lowercase)

3. **Extraction Prompt** (`prompts/extraction/entity_extraction_prompt.md`)

   - Add examples showing how to extract this entity type
   - Include edge cases and common patterns

4. **Tests** (`tests/test_json_extraction.py`)
   - Add test case for new entity type

## Checklist

- [ ] Pydantic model created in `schema.py`
- [ ] Entity type added to `config.py` (lowercase)
- [ ] Extraction examples added to prompt
- [ ] Test case added
- [ ] Documentation updated

## Example: Adding WORKLOAD_DRIVER

```python
# schema.py
class WorkloadDriver(BaseModel):
    """Factor that drives effort/cost estimation."""
    entity_name: str
    entity_type: Literal["workload_driver"] = "workload_driver"
    description: str
    driver_type: Optional[str] = None  # "volume", "frequency", "complexity"
    unit_of_measure: Optional[str] = None

# config.py
global_args.entity_types = [
    ...,
    "workload_driver",  # lowercase!
]
```
