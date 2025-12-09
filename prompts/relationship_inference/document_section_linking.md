# Document Hierarchy: DOCUMENT → SECTION

## ⚠️ CRITICAL: Entity ID Usage

**MANDATORY**: When generating relationships, you MUST use the EXACT `id` values from the entity JSON input.

- ❌ **NEVER** invent IDs (e.g., "document_j0005", "section_j")
- ✅ **ALWAYS** copy the `id` field value exactly as provided in the input entities
- ✅ Entity IDs look like: `"4:f7g8h9i0j1k2:123"` or similar alphanumeric strings

---

**Purpose**: Link referenced documents (attachments, annexes, specs, standards, regulations) to their parent sections  
**Relationship Type**: CHILD_OF (directional)  
**Pattern**: Prefix matching, explicit naming, content similarity  
**Last Updated**: October 10, 2025 (Branch 005 - Entity Type Consolidation)

---

## Context

Referenced documents (numbered attachments, annexes, specifications, standards, regulations) belong to parent sections in government solicitations. They follow naming conventions and content patterns that enable semantic linking across all agency types.

## Common Patterns

### Prefix Matching (Numbered Attachments)

- **J-12345** → **Section J** (DoD/Navy common)
- **C-0001** → **Section C**
- **Attachment 17** → **Section J Attachments**
- **Annex 17** → **Section J Annexes**

### Explicit Naming

- **Annex 17 Transportation** → **Section J Annexes**
- **Appendix B Technical Specs** → **Section C Appendices**
- **Exhibit 3 Past Performance** → **Section J Exhibits**

### Referenced Standards/Regulations

- **MIL-STD-882E** → **Section C** (SOW references)
- **FAR 52.212-1** → **Section I** (Contract Clauses)
- **Public Law 99-234** → **Section I** or **Section H** (Special Requirements)

## Detection Rules

1. **Numeric Prefixes**: Extract section letter from document identifier

   - Pattern: `[A-Z]-\d+` → Parent section matches letter
   - Example: `J-0005 PWS` → `Section J`
   - Example: `Attachment 17` → `Section J Attachments`

2. **Semantic Naming**: Match descriptive terms to section content

   - "Transportation", "Logistics" → Section C (SOW)
   - "Past Performance", "References" → Section L (Instructions)
   - Standards/Specs → Section C (SOW) or Section J (References)

3. **Explicit References**: Look for text mentions

   - "Referenced in Section J" → Parent is Section J
   - "See Attachment to Section C" → Parent is Section C
   - "Incorporated by reference in Section I" → Parent is Section I

4. **Document Type Patterns**: Match document types to typical sections
   - Standards (MIL-STD, ISO) → Section C or Section J
   - Regulations (FAR, DFARS, USC) → Section I or Section H
   - Attachments/Annexes → Section J (primary)

## Confidence Thresholds

- **HIGH (>0.8)**: Exact prefix match (J-12345 → Section J)
- **MEDIUM (0.5-0.8)**: Semantic overlap + standard naming
- **LOW (0.3-0.5)**: Weak semantic similarity only

## Output Format

Each relationship must include:

- `source_id`: Document entity ID
- `target_id`: Section entity ID
- `relationship_type`: "CHILD_OF"
- `confidence`: Float 0.0-1.0
- `reasoning`: Explanation (1-2 sentences)

## Examples

```json
[
  {
    "source_id": "document_123",
    "target_id": "section_456",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Document J-0005 PWS follows standard prefix pattern linking to Section J Attachments."
  },
  {
    "source_id": "document_789",
    "target_id": "section_101",
    "relationship_type": "CHILD_OF",
    "confidence": 0.82,
    "reasoning": "Annex 17 Transportation content semantically aligns with Section C Statement of Work."
  },
  {
    "source_id": "document_234",
    "target_id": "section_678",
    "relationship_type": "CHILD_OF",
    "confidence": 0.88,
    "reasoning": "MIL-STD-882E is referenced in Section C Performance Work Statement as required standard."
  }
]
```
