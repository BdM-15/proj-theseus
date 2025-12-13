# Entity Extraction Prompt v2.0 (Simplified)

**Purpose**: Extract government contracting entities using 12 core types  
**Philosophy**: Broad entity types + rich descriptions > narrow types + strict fields  
**Target**: ~15K characters (vs ~120K in v1)

---

## Entity Types (12 Core Types)

Extract entities into these 12 types:

### Document Structure
| Type | Description | Extract When You See |
|------|-------------|---------------------|
| `section` | RFP sections, SOW/PWS | "Section C", "PWS", "Statement of Work" |
| `document` | Attachments, standards | "Attachment J-1", "MIL-STD-882", "Exhibit A" |
| `regulation` | FAR/DFARS clauses | "FAR 52.212-4", "DFARS 252.204-7012" |

### Procurement Entities
| Type | Description | Extract When You See |
|------|-------------|---------------------|
| `requirement` | All obligations (shall/must/should) | "Contractor shall", "must provide", "should maintain" |
| `deliverable` | CDRLs, reports, outputs | "CDRL A001", "Monthly Status Report", "shall deliver" |
| `program` | Contract/program name | "MCPP II", "Navy MBOS", "DEIP" |

### Evaluation & Compliance
| Type | Description | Extract When You See |
|------|-------------|---------------------|
| `evaluation_factor` | Section M criteria | "Factor 1", "will be evaluated", "most important" |
| `compliance_item` | Section L instructions | "page limit", "font size", "proposal shall address" |

### Strategy & Risk
| Type | Description | Extract When You See |
|------|-------------|---------------------|
| `win_strategy` | Themes, discriminators | "critical to mission", "key priority", "emphasizes" |
| `risk` | Capture/execution risks | "risk", "challenge", "concern", "mitigation" |

### Context
| Type | Description | Extract When You See |
|------|-------------|---------------------|
| `organization` | Agencies, contractors | "Navy", "NAVAIR", "DoD", company names |
| `reference` | Misc references | Anything that doesn't fit above but is important |

---

## Extraction Rules

### 1. Requirement Detection (Most Important)

**SHALL/MUST = requirement**
- "Contractor shall provide..." → requirement
- "Personnel must complete..." → requirement
- "The offeror shall demonstrate..." → requirement

**Government actions are NOT requirements**
- "Government will provide office space" → NOT a requirement (informational)
- "Agency shall conduct reviews" → NOT a requirement for contractor

**Include ALL obligations in description**
- Capture workload details (volumes, frequencies, shifts) in description
- Capture equipment/material mentions in description
- Do NOT split into separate workload entities

### 2. Evaluation Factor Detection

**Section M content**
- "Factor 1: Technical Approach (40%)" → evaluation_factor
- "Subfactor 2.1: Staffing Plan" → evaluation_factor
- Capture weight/importance in description

**Rating scales are NOT factors**
- "Outstanding", "Acceptable", "Marginal" → NOT evaluation_factor
- These are rating values, not factors to extract

### 3. Compliance Item Detection

**Section L instructions**
- "Technical Volume: 25 pages maximum" → compliance_item
- "Use 12-point Times New Roman" → compliance_item
- "Submit via email by March 15" → compliance_item

**Embedded in Section M**
- If evaluation criteria contain format instructions, extract BOTH:
  - evaluation_factor for the criteria
  - compliance_item for the instructions

### 4. Win Strategy Detection (Shipley Methodology)

**Customer priorities (hot buttons)**
- "The Government emphasizes..." → win_strategy
- "Critical to mission success..." → win_strategy
- "Paramount importance..." → win_strategy
- High-weighted factors (>30%) → win_strategy

**Discriminators**
- Unique requirements → win_strategy
- Specialized capabilities → win_strategy
- Innovation emphasis → win_strategy

### 5. Entity Name Guidelines

- Use Title Case: "Monthly Status Report" not "monthly status report"
- Be specific: "24/7 Help Desk Support Requirement" not just "Support"
- Include identifiers: "CDRL A001 Monthly Report" not just "Monthly Report"
- Remove LLM artifacts: No leading #, **, or __

---

## Output Format

Return JSON with this structure:

```json
{
  "entities": [
    {
      "entity_name": "24/7 Help Desk Support Requirement",
      "entity_type": "requirement",
      "description": "Contractor shall provide Tier 1 and Tier 2 help desk support 24 hours per day, 7 days per week, including Federal holidays. Support includes incident logging, first-call resolution, and escalation procedures."
    },
    {
      "entity_name": "Factor 1: Technical Approach",
      "entity_type": "evaluation_factor",
      "description": "Technical Approach (45%) - Most Important. The Government will evaluate the offeror's understanding of requirements and proposed technical solution."
    }
  ],
  "relationships": [
    {
      "source_entity": "Help Desk Requirements",
      "target_entity": "Factor 1: Technical Approach",
      "relationship_type": "EVALUATED_BY",
      "confidence": 0.85,
      "reasoning": "Help desk requirements will be evaluated under Technical Approach factor"
    }
  ]
}
```

---

## Relationship Types (7 Focused Types)

| Type | Pattern | Example |
|------|---------|---------|
| `HAS_REQUIREMENT` | Section → Requirement | Section C HAS_REQUIREMENT Help Desk Support |
| `EVALUATED_BY` | Requirement → EvaluationFactor | Support Req EVALUATED_BY Technical Factor |
| `PRODUCES` | Requirement → Deliverable | Reporting Req PRODUCES Monthly Report |
| `PART_OF` | Child → Parent | Subfactor 1.1 PART_OF Factor 1 |
| `REFERENCES` | Entity → Document/Regulation | Requirement REFERENCES MIL-STD-882 |
| `ADDRESSES` | WinStrategy → Requirement | Mission Focus ADDRESSES Uptime Req |
| `MITIGATES` | WinStrategy → Risk | Proven Process MITIGATES Schedule Risk |

---

## Critical Instructions

1. **CAPTURE EVERYTHING IN DESCRIPTION**: Workload volumes, frequencies, shifts, equipment, materials - all go in description field. No separate entities.

2. **PREFER BROAD TYPES**: When uncertain, use broader type (requirement > reference)

3. **NEVER DROP ENTITIES**: If type is unclear, use `reference` as fallback

4. **RICH DESCRIPTIONS**: Copy relevant source text into description. This enables query-time analysis.

5. **RELATIONSHIPS ARE OPTIONAL**: If relationships aren't clear, return empty array. Better to have entities without relationships than hallucinate connections.

---

## Examples

### Input Text
```
Section C: Statement of Work

3.1 Help Desk Support
The Contractor shall provide Tier 1 and Tier 2 help desk support 24 hours per day, 7 days per week. The help desk shall handle approximately 500 calls per day with average handle time of 8 minutes. Support includes incident logging, troubleshooting, and escalation to Tier 3 as needed.

3.2 System Maintenance  
The Contractor shall maintain 99.9% system uptime during business hours.
```

### Expected Output
```json
{
  "entities": [
    {
      "entity_name": "Section C: Statement of Work",
      "entity_type": "section",
      "description": "Statement of Work section containing help desk and system maintenance requirements"
    },
    {
      "entity_name": "24/7 Help Desk Support Requirement",
      "entity_type": "requirement",
      "description": "Contractor shall provide Tier 1 and Tier 2 help desk support 24 hours per day, 7 days per week. The help desk shall handle approximately 500 calls per day with average handle time of 8 minutes. Support includes incident logging, troubleshooting, and escalation to Tier 3 as needed."
    },
    {
      "entity_name": "99.9% System Uptime Requirement",
      "entity_type": "requirement",
      "description": "Contractor shall maintain 99.9% system uptime during business hours."
    }
  ],
  "relationships": [
    {
      "source_entity": "Section C: Statement of Work",
      "target_entity": "24/7 Help Desk Support Requirement",
      "relationship_type": "HAS_REQUIREMENT",
      "confidence": 0.95,
      "reasoning": "Help desk requirement is defined in Section C"
    },
    {
      "source_entity": "Section C: Statement of Work",
      "target_entity": "99.9% System Uptime Requirement",
      "relationship_type": "HAS_REQUIREMENT",
      "confidence": 0.95,
      "reasoning": "Uptime requirement is defined in Section C"
    }
  ]
}
```

### Key Points in Example
- Workload details (500 calls/day, 8 min handle time) are in requirement description
- NOT extracted as separate "workload_driver" entities
- This preserves context for query-time analysis
- 99.9% uptime is a requirement, NOT a separate performance_metric

---

*Simplified extraction = better retrieval. Trust description fields for granular details.*
