# Orphan Resolution Rules

## ⚠️ CRITICAL: Entity ID Usage

**MANDATORY**: When generating relationships, you MUST use the EXACT `id` values from the entity JSON input.

- ❌ **NEVER** invent or fabricate IDs (e.g., "requirement_001", "equipment_trash", "person_pm")
- ❌ **NEVER** use example IDs from this prompt documentation
- ✅ **ALWAYS** copy the `id` field value exactly as provided in the input entities
- ✅ Entity IDs are the `entity_name` values provided in the JSON (human-readable names)

**Example of CORRECT usage:**

```json
Input orphan: {"id": "Trash Receptacle Requirements", "name": "Trash Receptacle Requirements", "type": "requirement"}
Input candidate: {"id": "55-Gallon Trash Receptacles", "name": "55-Gallon Trash Receptacles", "type": "equipment"}

Output relationship:
{
  "source_id": "Trash Receptacle Requirements",  // ← Copied EXACTLY from input
  "target_id": "55-Gallon Trash Receptacles",    // ← Copied EXACTLY from input
  "relationship_type": "REQUIRES",
  "confidence": 0.85,
  "reasoning": "Requirement specifies trash receptacles must be emptied"
}
```

**Example of WRONG usage (causes validation failures):**

```json
{
  "source_id": "req_trash_001",       // ← WRONG: Fabricated ID, will be rejected!
  "target_id": "equipment_trash",     // ← WRONG: Fabricated ID, will be rejected!
  ...
}
```

---

## Purpose

Resolve orphaned entities - entities that were extracted correctly but have no relationships to other entities in the knowledge graph. These represent missed connections that impact graph completeness.

**Why This Matters**: Orphaned entities reduce knowledge graph utility. A "Program Manager" with no relationships to deliverables or requirements is an isolated node that won't surface in queries.

---

## Relationship Patterns

### REQUIREMENT-CENTRIC

| Relationship   | Pattern                           | Example                                              |
| -------------- | --------------------------------- | ---------------------------------------------------- |
| `REQUIRES`     | Requirement → Equipment/Resource  | "Trash must be emptied daily" → trash receptacles    |
| `ENABLED_BY`   | Requirement → Gov't-provided Tech | "Using GFE laptops" → Government Furnished Equipment |
| `SATISFIED_BY` | Requirement → Deliverable         | "Submit monthly report" → Monthly Status Report      |

**Trigger Phrases for REQUIRES:**

- "must be", "shall be", "are required"
- Quantified items: "X receptacles", "Y workstations"
- Frequency: "daily", "weekly", "per shift"

**Trigger Phrases for ENABLED_BY:**

- "Government furnished", "GFE", "Gov't provided"
- "contractor-acquired", "furnished by Government"

### PERSON-CENTRIC

| Relationship      | Pattern              | Example                                |
| ----------------- | -------------------- | -------------------------------------- |
| `RESPONSIBLE_FOR` | Person → Deliverable | Program Manager → Quality Control Plan |
| `SUPERVISES`      | Person → Person      | Site Manager → Custodial Staff         |

**Trigger Phrases:**

- "shall submit", "is responsible for", "prepares"
- "oversees", "manages", "supervises"

### DOCUMENT-CENTRIC

| Relationship | Pattern                       | Example                                 |
| ------------ | ----------------------------- | --------------------------------------- |
| `FIELD_IN`   | Data element → Table/Document | DODAAC field → WAWF Invoice Table       |
| `PART_OF`    | Sub-component → Parent        | Appendix A → Performance Work Statement |
| `REFERENCES` | Document → Document           | SOW Section 3 → FAR 52.212-4            |

**Trigger Phrases:**

- "field in", "column in", "data element"
- "part of", "appendix to", "attachment"
- "references", "per", "in accordance with"

---

## Special Patterns to Detect

1. **Quantified Equipment**: "X receptacles must be Y" → `REQUIRES(requirement → equipment)`
2. **Government-Provided**: "furnished by Government" → `ENABLED_BY(requirement → technology)`
3. **Conditional Requirements**: "may substitute", "or equivalent" → `REQUIRES(requirement → equipment)`
4. **Table/Data References**: "field in X table" → `FIELD_IN(concept → document)`
5. **Person Submissions**: "shall submit" → `RESPONSIBLE_FOR(person → deliverable)`

---

## Output Format

Return ONLY a valid JSON array. Each relationship must have:

```json
[
  {
    "source_id": "exact_id_from_orphan_or_candidate",
    "target_id": "exact_id_from_orphan_or_candidate",
    "relationship_type": "REQUIRES|ENABLED_BY|SATISFIED_BY|RESPONSIBLE_FOR|FIELD_IN|PART_OF|REFERENCES",
    "confidence": 0.7,
    "reasoning": "Brief explanation of why this relationship exists"
  }
]
```

**Rules:**

- Source should typically be an orphaned entity (needs connections)
- Target should be a candidate entity (potential link target)
- Confidence: 0.6-0.7 for inferred, 0.8-0.9 for explicit, 0.95+ for direct text match
- If no relationships found, return `[]`

---

## Quality Guidelines

1. **Prioritize orphans**: Focus on creating relationships FROM orphaned entities
2. **Evidence-based**: Only create relationships with textual evidence in descriptions
3. **Specificity**: Prefer specific relationship types over generic ones
4. **No duplicates**: Don't create relationships that likely already exist
5. **Conservative**: When uncertain, prefer higher confidence threshold (0.7+)
