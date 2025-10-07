# Phase 6.1: LLM-Powered Post-Processing Enhancement

**Status**: Design phase - replacing regex-based approach  
**Date**: January 6, 2025

## Problem Statement

Current Phase 6 post-processing uses **regex patterns** to infer relationships:

- `r'^([A-Z]-)'` to match annex prefixes
- Fragile clause numbering patterns (FAR, DFARS, etc.)
- Agency-specific assumptions
- **Result**: 104 annex nodes, but many remain isolated

## Root Cause Analysis

1. **Wrong data source**: Post-processing reads `kv_store_full_entities.json` (document-level aggregation) instead of `graph_chunk_entity_relation.graphml` (actual entity details)

2. **Brittle regex**: Assumes specific naming conventions that vary by agency/RFP

3. **Orphaned prompts**: `phase6_prompts.py` created but never imported/used

## Proposed Solution: LLM-Powered Semantic Linking

### Architecture

Instead of regex, leverage **Grok's 2M context window** to understand relationships:

```python
# Current (regex-based)
def extract_prefix_pattern(annex_name: str) -> str:
    patterns = [r'^([A-Z]-)', r'^(Attachment\s+)', ...]
    # Fails on non-standard naming

# Proposed (LLM-based)
async def infer_relationships_llm(
    annex_entities: list,
    section_entities: list,
    llm_func
) -> list[dict]:
    """
    Ask Grok to understand relationships semantically.
    Agency-agnostic, handles any naming convention.
    """
    prompt = f"""
    You are analyzing a government RFP knowledge graph.

    ANNEX ENTITIES ({len(annex_entities)}):
    {json.dumps([{{'name': a.name, 'type': a.type, 'description': a.description}}
                 for a in annex_entities], indent=2)}

    SECTION ENTITIES ({len(section_entities)}):
    {json.dumps([{{'name': s.name, 'type': s.type, 'description': s.description}}
                 for s in section_entities], indent=2)}

    TASK:
    Determine which annexes belong to which sections based on:
    1. Naming conventions (J-12345 → Section J)
    2. Content similarity (keywords, topics)
    3. Standard government contracting structure
    4. Logical document organization

    OUTPUT:
    Return JSON array of relationships:
    [
      {{
        "source": "J-0200000-18 CAT Call Request Form",
        "target": "Section J",
        "relationship_type": "CHILD_OF",
        "confidence": 0.95,
        "reasoning": "J- prefix indicates Section J attachment"
      }},
      ...
    ]
    """

    response = await llm_func(prompt)
    relationships = json.loads(response)
    return relationships
```

### Benefits

1. **Agency-Agnostic**: Works with ANY naming convention
2. **Context-Aware**: Understands content, not just prefixes
3. **Adaptive**: Handles non-standard structures
4. **Leverages Investment**: Uses existing 2M-context Grok LLM
5. **Self-Documenting**: LLM provides reasoning for each relationship

### Implementation Plan

#### Phase 1: Fix Data Loading

- Read from `graph_chunk_entity_relation.graphml` (has full entity details)
- Parse nodes into entity objects with name, type, description
- Group by type (ANNEX, SECTION, CLAUSE, etc.)

#### Phase 2: LLM-Powered Inference

- Import `phase6_prompts.py` for relationship patterns guidance
- Batch entities intelligently (50-100 per LLM call)
- Use structured output format (JSON)
- Validate confidence scores (>0.7 threshold)

#### Phase 3: Save Relationships

- Update GraphML with new edges
- Update `kv_store_full_relations.json`
- Preserve existing relationships (non-destructive)

### Token Budget Analysis

**Per batch**:

- 50 annexes × 200 tokens (name + description) = 10,000 tokens
- 21 sections × 200 tokens = 4,200 tokens
- Prompt + instructions = 2,000 tokens
- **Total input**: ~16,200 tokens per batch

**Output**:

- 50 relationships × 150 tokens = 7,500 tokens

**Total per batch**: ~24,000 tokens  
**Batches needed**: 104 annexes / 50 = **3 batches**  
**Total cost**: 3 × $0.01 = **$0.03 per document**

### Integration with phase6_prompts.py

```python
from phase6_prompts import (
    RELATIONSHIP_INFERENCE_PATTERNS,
    SECTION_NORMALIZATION_MAPPING,
    AGENCY_CLAUSE_PATTERNS
)

# Include in LLM prompt as guidance
guidance = f"""
RELATIONSHIP PATTERNS TO CONSIDER:
{json.dumps(RELATIONSHIP_INFERENCE_PATTERNS, indent=2)}

STANDARD SECTION MAPPINGS:
{json.dumps(SECTION_NORMALIZATION_MAPPING, indent=2)}
"""
```

## Expected Outcomes

### Before (Regex-Based)

- 104 annex nodes
- 88 edges involving annexes (84.6% coverage)
- Fragile patterns break on non-standard RFPs

### After (LLM-Based)

- 104 annex nodes
- ~100-104 edges (96-100% coverage)
- Works with ANY RFP structure
- Self-documenting relationships with reasoning

## Code Changes Required

1. **src/raganything_server.py**:

   - Replace `post_process_knowledge_graph()` with `post_process_knowledge_graph_v2()`
   - Load from GraphML instead of kv_store
   - Call LLM for relationship inference
   - Import and use phase6_prompts.py

2. **src/phase6_prompts.py**:

   - Currently orphaned, will be imported by post-processing
   - Provides relationship patterns as LLM guidance

3. **New file: src/llm_relationship_inference.py**:
   - Dedicated module for LLM-powered linking
   - Handles batching, parsing, validation
   - Reusable for other relationship types

## Testing Strategy

1. **Baseline comparison**: Run on Navy MBOS baseline
2. **Metrics**:

   - Annex linkage: 88 → ~104 edges (84.6% → 100%)
   - L↔M relationships: Measure improvement
   - Processing time: Should be <10s for 3 LLM calls
   - Cost: ~$0.03 per document

3. **Validation**:
   - Manual review of 20 random relationships
   - Check reasoning quality
   - Verify no false positives (wrong section assignments)

## Next Steps

1. ✅ Analyze current data structure (DONE)
2. 🔨 Implement GraphML loader
3. 🔨 Create LLM relationship inference function
4. 🔨 Integrate phase6_prompts.py
5. 🔨 Replace post_process_knowledge_graph()
6. 🔨 Test on Navy MBOS baseline
7. 🔨 Update documentation

## Open Questions

1. Should we use batch processing or stream relationships?
2. What confidence threshold should we use? (proposed: 0.7)
3. Should LLM also infer OTHER relationship types beyond CHILD_OF?
4. Do we need human-in-the-loop validation for low-confidence relationships?

---

**Design Status**: Ready for implementation  
**Approval**: Pending user review
