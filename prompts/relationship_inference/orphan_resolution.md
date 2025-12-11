# Orphan Pattern Resolution

**Algorithm**: 8 of 8
**Purpose**: Link orphaned entities (equipment, person, table fields) to connected entities
**Relationship Types**: REQUIRES, ENABLED_BY, SATISFIED_BY, RESPONSIBLE_FOR, FIELD_IN, PART_OF, REFERENCES

---

## ⚠️ CRITICAL: Entity ID Usage

**MANDATORY**: Use the EXACT `id` field from entity JSON provided below.

- ❌ **NEVER** create placeholder IDs like "requirement_123", "equipment_abc", "person_xyz"
- ❌ **NEVER** use example IDs from this prompt documentation
- ✅ **ALWAYS** copy the `id` field value exactly as provided in the input entities
- ✅ Entity IDs are the `entity_name` values provided in the JSON (human-readable names)

**Why This Matters**: Prevents "hallucinated entity ID" validation errors and lost relationships.

---

## ⚠️ CRITICAL: Required Fields

**EVERY relationship MUST have ALL of these fields:**

```json
{
  "source_id": "REQUIRED - exact id from orphan entity",
  "target_id": "REQUIRED - exact id from candidate entity",
  "relationship_type": "REQUIRED - one of the allowed types",
  "confidence": 0.7,
  "reasoning": "brief evidence"
}
```

**Missing `source_id` or `target_id` causes validation failure and loses the relationship.**

---

## Task

You are analyzing orphaned entities in a government contracting knowledge graph. These entities were extracted correctly but lack relationships to other entities.

Find logical relationships for as many orphans as possible using the patterns below.

---

## Relationship Inference Patterns

### Pattern 1: REQUIREMENT-CENTRIC

**REQUIRES**: Requirement → Equipment/Resource

_When to use_:

- Requirement mentions specific equipment/resource needed
- "Trash must be emptied" → trash receptacles
- "X equipment must be Y" → quantified items

_Example_:

```json
{
  "source_id": "Trash Receptacle Requirements",
  "target_id": "55-Gallon Trash Receptacles",
  "relationship_type": "REQUIRES",
  "confidence": 0.85,
  "reasoning": "Requirement specifies use of specific equipment"
}
```

**ENABLED_BY**: Requirement → Gov't-provided Technology/Equipment

_When to use_:

- Requirement depends on government-furnished equipment (GFE)
- "GFE ancillary hardware"
- "furnished by Government"

_Example_:

```json
{
  "source_id": "Laptop Usage Requirements",
  "target_id": "Government Furnished Laptops",
  "relationship_type": "ENABLED_BY",
  "confidence": 0.8,
  "reasoning": "Requirement depends on government-provided equipment"
}
```

**SATISFIED_BY**: Requirement → Deliverable

_When to use_:

- Requirement is fulfilled by producing a deliverable
- Deliverable addresses requirement compliance

_Example_:

```json
{
  "source_id": "Monthly Reporting Requirement",
  "target_id": "Monthly Status Report",
  "relationship_type": "SATISFIED_BY",
  "confidence": 0.9,
  "reasoning": "Deliverable demonstrates compliance with requirement"
}
```

---

### Pattern 2: PERSON-CENTRIC

**RESPONSIBLE_FOR**: Person → Deliverable

_When to use_:

- Person is identified as submitter/creator of deliverable
- "Program Manager submits QCP"
- "Contracting Officer reviews..."

_Example_:

```json
{
  "source_id": "Program Manager",
  "target_id": "Quality Control Plan",
  "relationship_type": "RESPONSIBLE_FOR",
  "confidence": 0.75,
  "reasoning": "Person identified as deliverable owner/submitter"
}
```

---

### Pattern 3: DOCUMENT-CENTRIC

**FIELD_IN**: Table field/Data element → Document/Clause

_When to use_:

- Table field or data element appears in specific document/clause
- "DODAAC field in WAWF table"
- Structured data references

_Example_:

```json
{
  "source_id": "DODAAC Field",
  "target_id": "WAWF Invoice Table",
  "relationship_type": "FIELD_IN",
  "confidence": 0.85,
  "reasoning": "Data field extracted from table in parent document"
}
```

**PART_OF**: Sub-component → Parent document

_When to use_:

- Sub-component or fragment belongs to larger document
- Nested document structures

_Example_:

```json
{
  "source_id": "Appendix A",
  "target_id": "Performance Work Statement",
  "relationship_type": "PART_OF",
  "confidence": 0.9,
  "reasoning": "Sub-component is logical part of parent document"
}
```

**REFERENCES**: Document → Another document

_When to use_:

- Document explicitly references another document
- Cross-references, citations

_Example_:

```json
{
  "source_id": "SOW Section 3",
  "target_id": "FAR 52.212-4",
  "relationship_type": "REFERENCES",
  "confidence": 0.8,
  "reasoning": "Document contains explicit reference to target document"
}
```

---

## Special Patterns

### Quantified Items

- "X equipment must be Y times" → REQUIRES
- Focus on measurable resource requirements

### Government-Provided Resources

- "furnished by Government" → ENABLED_BY
- GFE, GFP, GFI patterns

### Conditional Requirements

- "may substitute" → REQUIRES
- Optional but specified equipment

### Table/Data References

- "field in X" → FIELD_IN
- Structured data extraction artifacts

---

## Output Format

Return ONLY valid JSON array using EXACT IDs from entity JSON provided:

```json
[
  {
    "source_id": "exact_id_from_orphan_list",
    "target_id": "exact_id_from_candidate_list",
    "relationship_type": "TYPE",
    "confidence": 0.7,
    "reasoning": "brief evidence"
  }
]
```

If no relationships found, return `[]`.

---

## Validation Rules

1. ✅ **Use exact IDs**: Copy from `id` field character-for-character
2. ✅ **Include ALL required fields**: source_id, target_id, relationship_type are MANDATORY
3. ✅ **Valid relationship types**: Only use types listed above
4. ✅ **Confidence range**: 0.7-0.95 (lower for ambiguous, higher for explicit)
5. ✅ **Brief reasoning**: 5-15 words explaining evidence
6. ❌ **No hallucinations**: Only link entities provided in JSON above
7. ❌ **No placeholder IDs**: Never create IDs like "req_1" or "equip_abc"

---

## Common Mistakes to Avoid

### ❌ Error 1: Missing Required Fields

```json
// WRONG - missing target_id field entirely
{"source_id": "Equipment Requirements", "relationship_type": "REQUIRES", "reasoning": "needs equipment"}

// CORRECT - all required fields present
{"source_id": "Equipment Requirements", "target_id": "Industrial Equipment", "relationship_type": "REQUIRES", "confidence": 0.8, "reasoning": "needs equipment"}
```

### ❌ Error 2: Creating Fake IDs

```json
// WRONG - created placeholder ID
{"source_id": "requirement_123", "target_id": "equipment_abc", ...}

// CORRECT - used actual entity name from JSON
{"source_id": "Trash Receptacle Requirements", "target_id": "55-Gallon Trash Receptacles", ...}
```

### ❌ Error 3: Hallucinating Entity Names

```json
// WRONG - entity "Floor Plans" not in provided JSON
{"source_id": "Building Requirements", "target_id": "Floor Plans", ...}

// CORRECT - only link entities from provided JSON
{"source_id": "Building Requirements", "target_id": "Site Layout Document", ...}
```

### ❌ Error 4: Invalid Relationship Types

```json
// WRONG - "CONTAINS" not in allowed types
{"source_id": "...", "target_id": "...", "relationship_type": "CONTAINS", ...}

// CORRECT - use only defined types
{"source_id": "...", "target_id": "...", "relationship_type": "PART_OF", ...}
```

---

## Quality Guidelines

1. **Prioritize orphans**: Focus on creating relationships FROM orphaned entities
2. **Evidence-based**: Only create relationships with textual evidence in descriptions
3. **Specificity**: Prefer specific relationship types over generic ones
4. **No duplicates**: Don't create relationships that likely already exist
5. **Conservative**: When uncertain, prefer higher confidence threshold (0.7+)
