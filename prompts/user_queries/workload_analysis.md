# Workload Analysis User Query Prompt

**Purpose**: Extract operational workload metrics from requirements for labor staffing and bill-of-materials (BOM) analysis.

**Target User**: Capture managers building pricing models, staffing plans, and equipment lists.

**Value Proposition**: LLM extracts WHAT operational parameters exist (volumes, frequencies, hours, locations, surges), capture manager decides HOW to staff/resource creatively.

---

## Response Format Instructions

When the user asks about workload, labor requirements, staffing needs, or operational metrics, analyze the knowledge graph and respond using this structure:

### 1. HIGH-COMPLEXITY REQUIREMENTS (Complexity >= 7)

For each high-complexity requirement:

```
REQUIREMENT: [entity_id]
Complexity: [complexity_score]/10
Rationale: [complexity_rationale]

BOE Categories: [workload_categories as comma-separated list]
Confidence Scores: [boe_relevance showing top 3 categories with confidence]

OPERATIONAL METRICS (What needs to happen):
- [labor_drivers - volumes, frequencies, hours, locations, surges]
- Focus on OPERATIONAL PARAMETERS, not staffing solutions
- Examples: "500 meals/day", "24/7 operations", "3 locations", "150-foot proximity"

MATERIAL NEEDS (For BOM buildout):
- [material_needs - equipment, supplies, quantities]
- Focus on WHAT is needed, not specifications
- Examples: "Commercial kitchen capacity: 500 meals/day", "HAZMAT storage facility"

EFFORT ESTIMATE: [effort_estimate]

---
```

### 2. MODERATE-COMPLEXITY REQUIREMENTS (Complexity 4-6)

Condensed format:

```
REQUIREMENT: [entity_id] (Complexity: [score]/10)
BOE: [top 2 categories]
Key Metrics: [top 2 labor_drivers]
Effort: [effort_estimate]
```

### 3. WORKLOAD SUMMARY BY BOE CATEGORY

```
LABOR WORKLOAD:
- [Count] requirements with Labor BOE category
- Key drivers: [Most common labor_drivers across requirements]
- Avg complexity: [Average complexity_score for Labor requirements]

MATERIALS WORKLOAD:
- [Count] requirements with Materials BOE category
- Key needs: [Most common material_needs across requirements]
- Avg complexity: [Average complexity_score for Materials requirements]

[Repeat for: ODCs, QA, Logistics, Lifecycle, Compliance]
```

### 4. STAFFING & BOM BUILDOUT GUIDANCE

```
LABOR STAFFING CONSIDERATIONS:
- Total requirements with labor indicators: [count]
- High-volume operations: [requirements with volume metrics like "500/day"]
- Continuous operations: [requirements with 24/7, shifts, etc.]
- Specialized skills: [requirements with qualifications, clearances, certifications]

MATERIAL/EQUIPMENT NEEDS:
- Total requirements with material indicators: [count]
- High-value equipment: [requirements with major equipment/infrastructure]
- Consumables: [requirements with ongoing supply needs]
- Infrastructure: [requirements with facility/space needs]

PRICING RISK FACTORS:
- Requirements with low confidence scores (< 0.7): [list]
- Ambiguous workload indicators: [requirements missing specific metrics]
- Recommend Questions for Government (QFG) on: [specific clarifications needed]
```

### 5. CREATIVE STAFFING OPPORTUNITIES

```
OPTIMIZATION OPPORTUNITIES:
Based on operational metrics extracted, consider:
- Multi-skilled positions: [requirements that could share personnel]
- Technology solutions: [requirements with automation potential]
- Subcontracting: [requirements suited for specialized subs]
- Economies of scale: [requirements with volume discounts possible]

Note: These are SUGGESTIONS based on patterns. Apply your capture expertise to determine best approach.
```

---

## Metadata Fields to Query

Use these exact field names when retrieving workload-enriched requirements:

| Field Name             | Type    | Description                                       |
| ---------------------- | ------- | ------------------------------------------------- |
| `has_workload_metric`  | Boolean | True if requirement has been enriched             |
| `workload_categories`  | Array   | BOE categories: Labor, Materials, ODCs, QA, etc.  |
| `boe_relevance`        | Object  | Confidence scores per BOE category (0.0-1.0)      |
| `labor_drivers`        | Array   | Operational metrics: volumes, hours, locations    |
| `material_needs`       | Array   | Equipment, supplies, quantities needed            |
| `complexity_score`     | Integer | 1-10 scale (Simple 1-3, Moderate 4-6, High 7-10)  |
| `complexity_rationale` | String  | Explanation of complexity assessment              |
| `effort_estimate`      | String  | High-level effort description                     |
| `enriched_by`          | String  | Version identifier (e.g., "workload_analysis_v1") |

---

## Query Examples & Expected Behavior

### Example 1: General Workload Query

**User Query**: "What are the labor-intensive requirements?"

**Expected Response**:

- List requirements with Labor BOE category
- Show operational metrics (NOT staffing solutions)
- Display complexity scores
- Summarize total labor workload across all requirements

### Example 2: BOM Buildout Query

**User Query**: "What equipment and materials are needed?"

**Expected Response**:

- List requirements with Materials BOE category
- Extract material_needs (equipment, supplies, quantities)
- Show requirements with infrastructure/facility needs
- Provide BOM starting point (user applies specifications)

### Example 3: Complexity Analysis

**User Query**: "What are the most complex requirements to staff?"

**Expected Response**:

- Sort by complexity_score (highest first)
- Show complexity_rationale explaining WHY complex
- Display labor_drivers showing operational challenges
- Suggest where to focus pricing/staffing effort

### Example 4: BOE Category Breakdown

**User Query**: "Break down workload by cost category"

**Expected Response**:

- Group requirements by workload_categories
- Show count and avg complexity per BOE category
- List top requirements in each category
- Provide effort estimates per category

---

## Important Reminders

### What This Prompt DOES:

✅ Extract operational metrics: volumes, frequencies, hours, locations, surges  
✅ Identify BOE cost categories: Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance  
✅ Assess complexity and effort levels  
✅ Provide data foundation for creative staffing/BOM decisions

### What This Prompt DOES NOT DO:

❌ Make staffing recommendations (e.g., "hire 12 FTEs")  
❌ Specify equipment models/brands  
❌ Calculate pricing or rates  
❌ Replace capture manager expertise

**Philosophy**: LLM finds the FACTS (500 meals/day, 24/7, 3 locations), YOU apply CREATIVITY (efficient staffing model, automation, subcontracting strategy).

---

## Quality Indicators

**High-Quality Response Includes**:

- Actual metrics from requirements (not generic statements)
- Confidence scores showing extraction reliability
- Complexity rationales explaining effort drivers
- Clear separation between WHAT (metrics) and HOW (solutions)
- Actionable starting points for pricing/staffing models

**Low-Quality Response Includes**:

- Generic statements without specific numbers
- Staffing recommendations (defeats the purpose)
- Missing confidence scores
- Equipment specifications (user determines these)

---

**Version**: 1.0  
**Created**: November 11, 2025  
**Branch**: 013b2-workload-enrichment  
**Algorithm**: Workload Enrichment (Algorithm 7/7)
