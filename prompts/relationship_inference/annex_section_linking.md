# Document Hierarchy: ANNEX → SECTION

**Purpose**: Link numbered attachments (annexes) to their parent sections  
**Relationship Type**: CHILD_OF (directional)  
**Pattern**: Prefix matching, explicit naming  
**Last Updated**: October 10, 2025 (Branch 005 - MinerU Optimization)

---

## Context

Annexes are numbered attachments that belong to parent sections in government RFPs. They follow standard naming conventions that enable semantic linking.

## Common Patterns

### Prefix Matching
- **J-12345** → **Section J** (most common)
- **C-0001** → **Section C**
- **Attachment 17** → **Section J Attachments**

### Explicit Naming
- **Annex 17 Transportation** → **Section J Annexes**
- **Appendix B Technical Specs** → **Section C Appendices**
- **Exhibit 3 Past Performance** → **Section J Exhibits**

## Detection Rules

1. **Numeric Prefixes**: Extract section letter from annex identifier
   - Pattern: `[A-Z]-\d+` → Parent section matches letter
   - Example: `J-0005 PWS` → `Section J`

2. **Semantic Naming**: Match descriptive terms to section content
   - "Transportation", "Logistics" → Section C (SOW)
   - "Past Performance", "References" → Section L (Instructions)

3. **Explicit References**: Look for text mentions
   - "Referenced in Section J" → Parent is Section J
   - "See Attachment to Section C" → Parent is Section C

## Confidence Thresholds

- **HIGH (>0.8)**: Exact prefix match (J-12345 → Section J)
- **MEDIUM (0.5-0.8)**: Semantic overlap + standard naming
- **LOW (0.3-0.5)**: Weak semantic similarity only

## Output Format

Each relationship must include:
- `source_id`: Annex entity ID
- `target_id`: Section entity ID
- `relationship_type`: "CHILD_OF"
- `confidence`: Float 0.0-1.0
- `reasoning`: Explanation (1-2 sentences)

## Examples

```json
[
  {
    "source_id": "annex_123",
    "target_id": "section_456",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Annex J-0005 PWS follows standard prefix pattern linking to Section J Attachments."
  },
  {
    "source_id": "annex_789",
    "target_id": "section_101",
    "relationship_type": "CHILD_OF",
    "confidence": 0.72,
    "reasoning": "Annex 17 Transportation content semantically aligns with Section C Statement of Work."
  }
]
```
