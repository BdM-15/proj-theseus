# Workload Driver Retrieval Contamination: Root Cause Analysis

**Date**: November 19, 2025  
**Branch**: main  
**Issue**: QASP surveillance metrics contaminating operational workload driver queries

---

## Executive Summary

**Problem**: When users query for operational workload drivers (frequencies, quantities, hours, equipment counts) to build labor Basis of Estimates (BOE), the system returns QASP surveillance metrics (performance thresholds, inspection criteria, acceptable quality levels) instead of operational data.

**Root Cause**: Entity extraction conflates operational requirements and surveillance metrics into single `REQUIREMENT (PERFORMANCE)` entities because PWS text combines them in the same sentence.

**Impact**: Capture teams receive inspection thresholds instead of workload data, making BOE development impossible.

---

## The Problem

### User Intent

Extract operational workload drivers to build labor Basis of Estimates:

- Operational hours (24/7 coverage)
- Frequencies (daily, weekly, monthly tasks)
- Quantities (equipment counts, facility sizes)
- Volumes (customer counts, delivery frequencies)
- Scope (square footage, number of locations)

### Actual Results

System returns QASP surveillance metrics instead:

- Performance thresholds (≤2 discrepancies/month)
- Acceptable quality levels (95% operational rate)
- Inspection criteria (zero violations allowed)
- Surveillance metrics (≤4 missed cleanings/month)

### Example Contamination

**User Query**: "Review the PWS and provide workload drivers for Appendix F services"

**Expected Response** (Operational Data):

```
Facilities & Coverage:
- 5 facilities totaling 64,000 sq ft
- 24/7 operations required
- C.A.C.: 39,656 sq ft (2 stories)
- Main Fitness: 22,550 sq ft (2 stories)
- 1,600 daily CRP customers

Workload Frequencies:
- Daily: equipment cleaning, inventories, trash/towel pickup, housekeeping
- Weekly: activity events
- Monthly: 8-10 special sports events, inventory submittals, equipment checks

Equipment Maintenance:
- All fitness equipment (specific counts in appendices)
- Electronic, recreational, and facility equipment
- Daily cleaning protocols with sanitizing solution
```

**Actual Response** (QASP Contamination):

```
Performance Objectives by Section:

F.2: Community Recreational Program Operations
- PO-C1: ≤2 coverage discrepancies/month (periodic monthly inspection)
- PO-F1: Zero alcohol violations (100% inspection surveillance)
- PO-F3: ≤2 late daily inventory submittals/month
- PO-F4: ≤1 late monthly inventory submittal/quarter
- PO-F5: ≤2 par level discrepancies/month
- PO-F9: ≤2 bottled water outages/month

F.3: Fitness Center Program
- PO-F10: ≤2 coverage discrepancies/month (24/7 customer service)
- PO-F11: ≤1 canceled class for lack of instructor/month
- PO-F12: 8-10 special sports events/month, zero discrepancies (100% inspection)
- PO-F13: ≤4 missed equipment cleanings/month
- PO-F14: ≤2 missed trash/towel pickups/week
- PO-F15: ≤2 bottled water outages/month

F.2.10: Equipment Preventive Maintenance
- PO-F6: 95% operational rate for electronic equipment
- PO-F7: 95% operational rate for recreational equipment
- PO-F8: 95% operational rate for facility equipment
```

**Analysis**: Response is 90%+ surveillance thresholds, 10% operational data (buried in PO descriptions).

---

## Root Causes

### 1. Entity Extraction Conflation

The ontology's `REQUIREMENT (PERFORMANCE)` type conflates two distinct concepts:

**Operational Workload** (what we want):

```
"Contractor shall clean all fitness equipment daily with sanitizing solution"
→ Workload: Daily frequency, equipment scope
```

**Surveillance Metrics** (QASP contamination):

```
"No more than 4 missed equipment cleanings per month"
→ Surveillance: Acceptable quality level for inspection
```

**Current Reality**: Both get extracted as single `REQUIREMENT (PERFORMANCE)` entity because the PWS text combines them:

```
PWS Text: "PO-F13: Clean all fitness equipment daily; ≤4 missed cleanings/month"

Extracted Entity:
{
  "entity_name": "PO-F13 Equipment Cleaning",
  "entity_type": "REQUIREMENT",
  "requirement_type": "PERFORMANCE",
  "description": "Clean all fitness equipment daily with sanitizing solution;
                  no more than 4 missed cleanings per month"
}
```

**Why This is Wrong**:

- Workload driver: "Daily cleaning" (operational frequency)
- Surveillance metric: "≤4 missed/month" (QASP threshold)
- Both stored in same entity → query contamination inevitable

---

### 2. Entity Detection Rules Ambiguity

From `entity_detection_rules.md` (lines 408-415):

```markdown
#### PERFORMANCE

- **Pattern**: SLA language, metrics, measurable outcomes
- **Examples**:
  - "99.9% system uptime"
  - "Response within 24 hours of incident report"
  - "Process 1000 transactions per hour"
  - "First-time fix rate ≥ 95%"
```

**Problem**: These examples are **surveillance metrics**, not operational workload.

The LLM correctly extracts them per the rules, but the rules don't distinguish:

- **Operational performance**: "Provide 24/7 support" (workload driver - describes work to be done)
- **Surveillance performance**: "≥95% uptime" (QASP threshold - measures quality of work done)

**Example Extraction Confusion**:

```
PWS: "Provide 24/7 customer service desk coverage; no more than 2 coverage
      discrepancies per month (periodic monthly inspection)"

Current Extraction:
- Entity: "24/7 Customer Service Coverage"
- Type: REQUIREMENT (PERFORMANCE)
- Description: "Provide 24/7 coverage; ≤2 discrepancies/month; periodic inspection"
- Result: Mixed operational + surveillance in single entity

What Should Happen:
Entity 1:
- Entity: "24/7 Customer Service Desk Coverage"
- Type: REQUIREMENT (OPERATIONAL)
- Description: "Contractor shall provide customer service desk coverage 24 hours
                per day, 7 days per week across all CRP locations"

Entity 2:
- Entity: "PO-C1 Customer Service Coverage Surveillance"
- Type: PERFORMANCE_OBJECTIVE
- Description: "Surveillance threshold: No more than 2 coverage discrepancies
                allowed per month; periodic monthly inspection; 100% compliance required"
```

---

### 3. LightRAG Retrieval Behavior

LightRAG prioritizes **entity labels** over **descriptions** during semantic search.

**Entities in Graph**:

```json
{
  "entity_name": "PO-F13 Equipment Cleaning",
  "entity_type": "REQUIREMENT",
  "requirement_type": "PERFORMANCE",
  "description": "Clean all fitness equipment daily with sanitizing solution;
                  no more than 4 missed cleanings per month; periodic monthly inspection"
}
```

**User Query**: "workload drivers for frequencies and quantities"

**LightRAG Matching Logic**:

1. Label "Equipment Cleaning" → semantically relevant to workload query ✓
2. Description contains "daily" → frequency keyword match ✓
3. **BUT** description also contains "≤4 missed/month" (surveillance) ✗
4. **Result**: Returns entity with mixed operational + surveillance content

**Why This Fails**:

- LightRAG can't separate operational from surveillance within single entity description
- Semantic similarity matches the label, not the intent
- Both "daily cleaning" and "≤4 missed/month" are about cleaning, so both seem relevant

---

### 4. Previous Fix Attempts That Failed

#### Attempt 1: Add `WORKLOAD` Entity Type

**Approach**:

```json
{
  "entity_name": "Daily Equipment Cleaning",
  "entity_type": "WORKLOAD",
  "description": "Clean all fitness equipment daily with sanitizing solution"
}
```

**Why It Failed**:

- LightRAG weighted generic label "Daily Equipment Cleaning" too heavily
- Descriptions didn't differentiate enough in ranking
- Still retrieved QASP entities with similar labels (e.g., "Equipment Cleaning Standard")
- **Regression**: Query quality degraded because labels became too vague/similar

**Lesson**: Adding entity types alone doesn't solve the problem if extraction still conflates content.

---

#### Attempt 2: Relationship Inference (Algorithm 6+)

**Approach**:

```
REQUIREMENT "Clean equipment daily"
  --DRIVES_WORKLOAD-->
WORKLOAD "Daily cleaning frequency"
```

**Why It Failed**:

- Created derivative entities from requirements via relationship inference
- But source `REQUIREMENT` entity still contained mixed operational + QASP data
- Can't cleanly split what was already extracted as single entity
- Added architectural complexity without solving extraction conflation
- **Result**: 0 relationships inferred, cascading errors in processing pipeline

**Lesson**: Relationship inference can't fix what's broken at extraction time.

---

## The Core Issue

**Extraction happens BEFORE the split**:

```
┌─────────────────────────────────────────────────────────────┐
│ PWS Text: "PO-F13: Clean equipment daily; ≤4 missed/month" │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Extraction (single pass): REQUIREMENT entity created        │
│ Entity stores: "Clean equipment daily; ≤4 missed/month"     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Neo4j Storage: Mixed operational + surveillance in single   │
│ entity description                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Query "workload drivers": LightRAG retrieves mixed entity   │
│ User gets: "Clean daily; ≤4 missed/month" (contaminated!)   │
└─────────────────────────────────────────────────────────────┘
```

**What's needed**:

```
┌─────────────────────────────────────────────────────────────┐
│ PWS Text: "PO-F13: Clean equipment daily; ≤4 missed/month" │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Extraction (single pass): REQUIREMENT entity created        │
│ Entity stores: "Clean equipment daily; ≤4 missed/month"     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Post-extraction decomposition: LLM analyzes for QASP        │
│ patterns and splits entity into two:                        │
│                                                              │
│ Entity 1 (REQUIREMENT - Operational):                       │
│   "Clean all fitness equipment daily"                       │
│                                                              │
│ Entity 2 (PERFORMANCE_OBJECTIVE - Surveillance):            │
│   "≤4 missed cleanings per month; periodic inspection"      │
│                                                              │
│ Link: Entity 1 --MEASURED_BY--> Entity 2                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Neo4j Storage: Clean separation                             │
│ - REQUIREMENT: Pure operational workload                    │
│ - PERFORMANCE_OBJECTIVE: Pure surveillance                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Query "workload drivers": Returns only REQUIREMENT entities │
│ Query "QASP thresholds": Returns only PERFORMANCE_OBJECTIVE │
│ Clean separation, no contamination!                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Why Standard Solutions Don't Work

### ❌ Can't fix with better prompts

**Why**: The PWS text genuinely combines workload + surveillance in same sentence. No amount of prompt engineering can separate content that's intermingled in source text during single-pass extraction.

### ❌ Can't fix with entity types alone

**Why**: LightRAG label-weighting means similar labels retrieve together regardless of type. "Equipment Cleaning" (workload) vs "Equipment Cleaning Standard" (QASP) both match workload queries.

### ❌ Can't fix with relationships only

**Why**: Requires clean source entities first. If source entities are contaminated, derived relationships are also contaminated.

### ❌ Can't fix with query filters alone

**Why**: LightRAG already retrieved contaminated entities; Neo4j filtering is post-hoc bandaid. Doesn't solve root cause at extraction time.

---

## Required Solution: Two-Phase Approach

### Phase 1: Post-Extraction Decomposition (Fixes Root Cause)

**When**: After RAG-Anything extracts entities, BEFORE Neo4j storage

**Process**:

1. LLM analyzes each `REQUIREMENT (PERFORMANCE)` entity
2. Detects QASP patterns:
   - "no more than X"
   - "≤ X per month/week"
   - "zero violations"
   - "95% operational rate"
   - "discrepancy", "threshold", "AQL"
   - "periodic inspection", "surveillance"
3. Splits into TWO entities:
   - **REQUIREMENT**: Operational workload (contractor action)
   - **PERFORMANCE_OBJECTIVE**: Surveillance metric (government measurement)
4. Links via relationship: `REQUIREMENT --MEASURED_BY--> PERFORMANCE_OBJECTIVE`

**Example Decomposition**:

**Input Entity** (from extraction):

```json
{
  "entity_name": "PO-F13 Equipment Cleaning",
  "entity_type": "REQUIREMENT",
  "requirement_type": "PERFORMANCE",
  "description": "Clean all fitness equipment daily with sanitizing solution;
                  no more than 4 missed cleanings per month; periodic monthly inspection"
}
```

**Output Entities** (after decomposition):

```json
[
  {
    "entity_name": "Daily Fitness Equipment Cleaning",
    "entity_type": "REQUIREMENT",
    "requirement_type": "OPERATIONAL",
    "description": "Contractor shall clean all fitness equipment daily with sanitizing solution.
                    Scope: Main Fitness Center (22,550 sq ft), Satellite Centers (4,927 sq ft),
                    Fitness Annex (187 sq ft). Frequency: Daily (7 days/week).",
    "workload_driver": true
  },
  {
    "entity_name": "PO-F13 Equipment Cleaning Surveillance",
    "entity_type": "PERFORMANCE_OBJECTIVE",
    "description": "Surveillance threshold for fitness equipment cleaning compliance.
                    Acceptable Quality Level: ≤4 missed cleanings per month.
                    Inspection: Periodic monthly. Zero tolerance for chronic violations.",
    "qasp_threshold": true,
    "measured_requirement_id": "Daily Fitness Equipment Cleaning"
  }
]
```

**Relationship Created**:

```
REQUIREMENT "Daily Fitness Equipment Cleaning"
  --MEASURED_BY-->
PERFORMANCE_OBJECTIVE "PO-F13 Equipment Cleaning Surveillance"
```

---

### Phase 2: Neo4j Query Filtering (Defense in Depth)

**When**: During query execution (post-retrieval)

**Process**: Even with decomposition, add pattern filters to catch edge cases where decomposition misses QASP language.

**Filter Patterns** (Cypher query):

```cypher
// User query: "workload drivers"
// LightRAG returns: Mix of REQUIREMENT entities (operational + potential QASP leakage)

// Neo4j post-filter:
MATCH (r:REQUIREMENT)
WHERE r.workload_driver = true
  OR (
    NOT r.entity_name STARTS WITH 'PO-'
    AND NOT r.description CONTAINS 'no more than'
    AND NOT r.description CONTAINS 'discrepancy'
    AND NOT r.description CONTAINS 'threshold'
    AND NOT r.description CONTAINS 'periodic inspection'
    AND NOT r.description CONTAINS '≤'
    AND NOT r.description CONTAINS 'surveillance'
    AND NOT r.description CONTAINS 'AQL'
    AND NOT r.description CONTAINS 'zero violations'
  )
RETURN r
ORDER BY r.entity_name
```

**Why This Helps**:

- Catches entities where decomposition missed QASP language
- Provides safety net for edge cases
- Doesn't rely on perfect decomposition logic
- Can be tuned based on contamination patterns observed

---

## Implementation Strategy

### Step 1: Add `PERFORMANCE_OBJECTIVE` Entity Type

**Location**: `prompts/extraction/entity_detection_rules.md`

**New Section**:

```markdown
## Entity Type 18: PERFORMANCE_OBJECTIVE

### Semantic Purpose

QASP surveillance metrics, inspection criteria, and acceptable quality levels that
measure contractor performance. These are NOT operational workload drivers—they are
government measurement standards.

### Content Signals

- **Threshold Language**: "no more than X", "≤ X per month/week", "zero violations"
- **Percentage Targets**: "95% operational rate", "≥ 99% uptime", "98% first-time fix"
- **Inspection References**: "periodic monthly inspection", "100% inspection", "surveillance"
- **AQL Patterns**: "acceptable quality level", "discrepancy limits", "tolerance thresholds"
- **PO Identifiers**: "PO-C1", "PO-F13", "Performance Objective"

### Context Clues

- Near QASP sections or quality surveillance plans
- In performance monitoring sections
- Associated with inspection schedules
- Referenced in contractor performance evaluation

### Detection: PERFORMANCE_OBJECTIVE vs REQUIREMENT

**PERFORMANCE_OBJECTIVE** (Surveillance - NOT workload):

- "≤4 missed equipment cleanings per month" → QASP threshold
- "95% equipment operational rate" → Quality target
- "Zero alcohol violations allowed" → Compliance standard

**REQUIREMENT (OPERATIONAL)** (Workload driver):

- "Clean all fitness equipment daily" → Operational frequency
- "Maintain equipment to 95% operational rate" → Operational goal
- "Enforce alcohol limitations per DAFI 34-107" → Operational duty

### Basic Attributes

Capture entity_name, entity_type, and description. QASP identifiers (PO-XX) and
surveillance thresholds preserved in natural language.
```

---

### Step 2: Post-Extraction Decomposition Pipeline

**Location**: New file `src/inference/qasp_decomposition.py`

**Logic**:

```python
def decompose_performance_requirements(entities: list[dict]) -> list[dict]:
    """
    Post-extraction decomposition: Split REQUIREMENT (PERFORMANCE) entities
    into operational workload vs surveillance metrics.

    Returns: Enhanced entity list with PERFORMANCE_OBJECTIVE entities added.
    """
    decomposed_entities = []

    for entity in entities:
        if entity['entity_type'] == 'REQUIREMENT' and entity.get('requirement_type') == 'PERFORMANCE':
            # Check for QASP contamination patterns
            if has_qasp_pattern(entity['description']):
                # Split into two entities
                operational, surveillance = llm_decompose(entity)
                decomposed_entities.extend([operational, surveillance])
            else:
                # No QASP detected, keep as-is
                decomposed_entities.append(entity)
        else:
            # Not a performance requirement, keep as-is
            decomposed_entities.append(entity)

    return decomposed_entities

def has_qasp_pattern(description: str) -> bool:
    """Detect QASP surveillance language in entity description."""
    qasp_indicators = [
        'no more than',
        '≤', '>=', '≥',
        'discrepancy', 'discrepancies',
        'threshold',
        'periodic inspection',
        'surveillance',
        'zero violations',
        'AQL',
        '% operational rate',
        'PO-C', 'PO-F',  # Performance Objective identifiers
        'acceptable quality level'
    ]
    return any(indicator.lower() in description.lower() for indicator in qasp_indicators)

def llm_decompose(entity: dict) -> tuple[dict, dict]:
    """
    Use LLM to split REQUIREMENT (PERFORMANCE) into:
    1. REQUIREMENT (OPERATIONAL) - workload driver
    2. PERFORMANCE_OBJECTIVE - QASP surveillance
    """
    prompt = f"""
Decompose this government contracting requirement into TWO separate entities:

Original Entity:
{json.dumps(entity, indent=2)}

Rules:
1. REQUIREMENT (OPERATIONAL): Extract the contractor's operational workload
   - Focus: What work must be done (frequency, scope, method)
   - Examples: "daily cleaning", "24/7 coverage", "maintain equipment"

2. PERFORMANCE_OBJECTIVE (QASP): Extract surveillance/inspection criteria
   - Focus: How performance is measured/inspected
   - Examples: "≤4 missed/month", "95% operational rate", "zero violations"

Return JSON:
{{
  "operational_requirement": {{
    "entity_name": "...",
    "description": "...",
    "workload_driver": true
  }},
  "surveillance_objective": {{
    "entity_name": "...",
    "description": "...",
    "qasp_threshold": true,
    "measured_requirement_id": "..."
  }}
}}
"""

    response = llm_call(prompt)
    decomposed = json.loads(response)

    # Build operational requirement
    operational = {
        **entity,
        'entity_name': decomposed['operational_requirement']['entity_name'],
        'entity_type': 'REQUIREMENT',
        'requirement_type': 'OPERATIONAL',
        'description': decomposed['operational_requirement']['description'],
        'workload_driver': True
    }

    # Build surveillance objective
    surveillance = {
        'entity_name': decomposed['surveillance_objective']['entity_name'],
        'entity_type': 'PERFORMANCE_OBJECTIVE',
        'description': decomposed['surveillance_objective']['description'],
        'qasp_threshold': True,
        'measured_requirement_id': operational['entity_name'],
        'section_origin': entity.get('section_origin', 'Unknown')
    }

    return operational, surveillance
```

---

### Step 3: Integration into Processing Pipeline

**Location**: `src/raganything_server.py` (insert after entity extraction, before Neo4j storage)

```python
from src.inference.qasp_decomposition import decompose_performance_requirements

# After entity extraction completes
entities = extract_entities(document)

# BEFORE Neo4j storage - decompose QASP contamination
entities = decompose_performance_requirements(entities)

# Now store clean entities in Neo4j
store_in_neo4j(entities)
```

---

### Step 4: Neo4j Query Enhancement

**Location**: Query routing logic in LightRAG

**Add Workload Query Filter**:

```python
def query_workload_drivers(user_query: str) -> str:
    """
    Enhanced query for workload drivers with QASP filtering.
    """
    # LightRAG semantic retrieval (may include some QASP leakage)
    entities = lightrag_query(user_query)

    # Neo4j post-filter to remove QASP contamination
    filtered_entities = neo4j.run("""
        MATCH (e)
        WHERE e.id IN $entity_ids
          AND (
            e.workload_driver = true
            OR (
              e.entity_type = 'REQUIREMENT'
              AND NOT e.entity_name STARTS WITH 'PO-'
              AND NOT e.description CONTAINS 'no more than'
              AND NOT e.description CONTAINS 'discrepancy'
              AND NOT e.description CONTAINS 'threshold'
              AND NOT e.description CONTAINS '≤'
            )
          )
        RETURN e
    """, entity_ids=[e.id for e in entities])

    return generate_response(filtered_entities)
```

---

## Success Criteria

After implementing the two-phase solution:

### ✅ Functional Requirements

1. **Workload queries return only operational data**:
   - Frequencies: Daily, weekly, monthly
   - Quantities: Equipment counts, facility sizes
   - Hours: 24/7 coverage, operating hours
   - Volumes: Customer counts, delivery frequencies
2. **QASP queries return only surveillance metrics**:

   - Thresholds: ≤X per month/week
   - Percentages: 95% operational rate
   - Inspection: Periodic monthly, 100% inspection
   - Compliance: Zero violations

3. **Zero cross-contamination**:
   - Workload query → 0 PERFORMANCE_OBJECTIVE entities returned
   - QASP query → 0 REQUIREMENT (OPERATIONAL) entities returned

### ✅ Quality Metrics

1. **Entity Decomposition Accuracy**: ≥95% of PERFORMANCE requirements correctly split
2. **Query Precision**: ≥90% of workload query results are operational data
3. **Query Recall**: ≥85% of operational workload drivers retrieved
4. **Processing Time**: Post-extraction decomposition adds ≤20% to total processing time

---

## Timeline & Effort Estimate

### Phase 1: Entity Type Addition (2-4 hours)

- Update `entity_detection_rules.md` with `PERFORMANCE_OBJECTIVE` type
- Add examples and detection patterns
- Test extraction with new type

### Phase 2: Decomposition Pipeline (8-12 hours)

- Implement `qasp_decomposition.py` with LLM logic
- Create QASP pattern detection (regex + LLM)
- Build entity splitting logic with relationship creation
- Unit tests for decomposition accuracy

### Phase 3: Integration (4-6 hours)

- Integrate into `raganything_server.py` processing pipeline
- Test end-to-end with ISS PWS
- Validate Neo4j storage of split entities

### Phase 4: Query Enhancement (4-6 hours)

- Add Neo4j post-filter logic
- Create workload-specific query templates
- Test query precision/recall

### Phase 5: Validation (4-6 hours)

- Process 3 test RFPs (ISS, MCPP, AUAB)
- Run workload queries, measure contamination
- Tune decomposition prompts based on results
- Document edge cases

**Total Estimated Effort**: 22-34 hours (3-4 days)

---

## Alternative Approaches Considered

### Option A: Fix Extraction Prompts Only

**Approach**: Modify entity extraction prompts to separate workload from QASP during initial extraction.

**Why Rejected**:

- PWS text combines them in same sentence—single-pass extraction can't separate
- Would require radical ontology changes breaking existing data
- Doesn't solve LightRAG label-weighting issue

### Option B: Query-Time LLM Filtering Only

**Approach**: Let LightRAG retrieve contaminated entities, use LLM to filter results.

**Why Rejected**:

- Too slow (LLM call per query)
- Wasteful (retrieves then discards contaminated data)
- Doesn't fix root cause at storage layer

### Option C: Manual Entity Annotation

**Approach**: Human review marks each entity as workload vs QASP.

**Why Rejected**:

- Not scalable (1000s of entities per RFP)
- Defeats purpose of automated extraction
- Introduces human error and inconsistency

---

## Conclusion

The workload driver contamination is a **systemic extraction issue**, not a retrieval or query problem. The solution requires:

1. **Post-extraction decomposition** to split conflated entities into clean operational vs surveillance entities
2. **New entity type** (`PERFORMANCE_OBJECTIVE`) to explicitly model QASP surveillance
3. **Query-time filtering** as defense-in-depth to catch edge cases

This approach fixes the root cause (extraction conflation) while providing safety nets (Neo4j filtering) to ensure clean workload queries.

---

**Document Version**: 1.0  
**Last Updated**: November 19, 2025  
**Author**: Development Team  
**Status**: Ready for Implementation
