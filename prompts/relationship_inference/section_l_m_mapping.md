# Section L↔M Mapping: SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR

**Purpose**: Link submission instructions (Section L) to evaluation factors (Section M)  
**Relationship Type**: GUIDES (bidirectional)  
**Pattern**: Explicit references, format requirements, semantic overlap  
**Last Updated**: October 10, 2025 (Branch 005 - MinerU Optimization)

---

## Context

Section L (Instructions to Offerors) provides submission guidelines that directly relate to how proposals are evaluated in Section M (Evaluation Factors). Understanding these relationships is critical for proposal compliance and optimization.

## Common Patterns

### Explicit Volume References
- **Section L**: "Technical Approach Volume limited to 25 pages"
- **Section M**: "Factor 1: Technical Approach (40% weight)"
- **Relationship**: Volume name + factor name match

### Format Requirements
- **Section L**: "Past Performance submissions require 5 references"
- **Section M**: "Factor 2: Past Performance (30% weight)"
- **Relationship**: Evaluation factor ties to submission format

### Semantic Overlap
- **Section L**: "Management Approach must address key personnel"
- **Section M**: "Factor 3: Management Approach evaluates staffing plan"
- **Relationship**: Topic alignment + terminology match

## Detection Rules

1. **Direct Name Matching**: Factor/volume names appear in both sections
   - Case-insensitive comparison
   - Partial matches acceptable (e.g., "Technical" matches "Technical Approach")

2. **Topic Alignment**: Semantic similarity between descriptions
   - Use embedding similarity or keyword overlap
   - Threshold: >0.6 similarity score

3. **Structural Hints**: Numbering/ordering patterns
   - "Volume 1" → "Factor 1" (positional correlation)
   - Sub-factors → Sub-instructions

## Confidence Thresholds

- **HIGH (>0.8)**: Exact name match + explicit reference
- **MEDIUM (0.5-0.8)**: Semantic overlap + terminology match
- **LOW (0.3-0.5)**: Weak topic alignment only

## Output Format

Each relationship must include:
- `source_id`: SUBMISSION_INSTRUCTION entity ID
- `target_id`: EVALUATION_FACTOR entity ID
- `relationship_type`: "GUIDES"
- `confidence`: Float 0.0-1.0
- `reasoning`: Explanation (1-2 sentences)

## Examples

```json
[
  {
    "source_id": "instruction_123",
    "target_id": "factor_456",
    "relationship_type": "GUIDES",
    "confidence": 0.95,
    "reasoning": "Technical Approach Volume instructions directly guide Factor 1: Technical Approach evaluation (40% weight)."
  },
  {
    "source_id": "instruction_789",
    "target_id": "factor_101",
    "relationship_type": "GUIDES",
    "confidence": 0.78,
    "reasoning": "Past Performance submission format (5 references) aligns with Factor 2: Past Performance scoring criteria."
  }
]
```

## Special Cases

### Multi-Factor Instructions
- One instruction may guide multiple factors
- Example: "Cost Volume" → "Cost Factor" + "Price Realism Factor"
- Create separate relationships for each

### Sub-Factor Mapping
- Detailed instructions map to sub-factors
- Example: "Key Personnel CVs" → "Management Approach > Staffing Sub-Factor"
- Preserve hierarchical relationships
