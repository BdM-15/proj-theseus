# Extraction Examples — Worked

Each example shows source text → expected entities + relationships. Use as few-shot context.

## Example 1 — Section L instruction

**Source (L.3.4):** "The offeror shall submit a Past Performance Volume containing no more than five (5) reference contracts."

```json
{
  "entities": [
    {
      "name": "L.3.4 Past Performance Volume Submission",
      "type": "proposal_instruction"
    },
    { "name": "Past Performance Volume", "type": "proposal_volume" }
  ],
  "relationships": [
    {
      "source": "L.3.4 Past Performance Volume Submission",
      "target": "Past Performance Volume",
      "relationship_type": "REFERENCES"
    }
  ]
}
```

## Example 2 — Section M factor with subfactor

**Source (M.2):** "Factor 2 — Technical Approach (40%) consists of Subfactor 2.1 — Solution Architecture (25%) and Subfactor 2.2 — Staffing (15%)."

```json
{
  "entities": [
    {
      "name": "Factor 2 Technical Approach",
      "type": "evaluation_factor",
      "description": "weight 40%"
    },
    {
      "name": "Subfactor 2.1 Solution Architecture",
      "type": "subfactor",
      "description": "weight 25%"
    },
    {
      "name": "Subfactor 2.2 Staffing",
      "type": "subfactor",
      "description": "weight 15%"
    }
  ],
  "relationships": [
    {
      "source": "Factor 2 Technical Approach",
      "target": "Subfactor 2.1 Solution Architecture",
      "relationship_type": "HAS_SUBFACTOR"
    },
    {
      "source": "Factor 2 Technical Approach",
      "target": "Subfactor 2.2 Staffing",
      "relationship_type": "HAS_SUBFACTOR"
    }
  ]
}
```

## Example 3 — CLIN with priced work

**Source (B):** "CLIN 0001 — Base Year Operations (FFP) — funds work under PWS Task 3.2 Network Operations."

```json
{
  "entities": [
    {
      "name": "CLIN 0001",
      "type": "contract_line_item",
      "description": "Base Year Operations FFP"
    },
    { "name": "PWS Task 3.2 Network Operations", "type": "work_scope_item" }
  ],
  "relationships": [
    {
      "source": "CLIN 0001",
      "target": "PWS Task 3.2 Network Operations",
      "relationship_type": "FUNDS"
    }
  ]
}
```

## Example 4 — Cybersecurity regulatory reference

**Source (C.7.2):** "All systems shall comply with NIST SP 800-171 controls."

```json
{
  "entities": [
    { "name": "C.7.2 Cybersecurity Compliance", "type": "requirement" },
    { "name": "NIST SP 800-171", "type": "regulatory_reference" }
  ],
  "relationships": [
    {
      "source": "NIST SP 800-171",
      "target": "C.7.2 Cybersecurity Compliance",
      "relationship_type": "MANDATES"
    }
  ]
}
```
