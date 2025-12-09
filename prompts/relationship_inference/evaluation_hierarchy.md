# Evaluation Hierarchy & Metrics Inference

## ⚠️ CRITICAL: Entity ID Usage

**MANDATORY**: When generating relationships, you MUST use the EXACT `id` or `entity_id` values from the entity JSON input.

- ❌ **NEVER** invent IDs (e.g., "factor_1", "subfactor_1_1")
- ✅ **ALWAYS** copy the `id`/`entity_id` field value exactly as provided in the input entities
- ✅ Entity IDs look like: `"4:f7g8h9i0j1k2:123"` or similar alphanumeric strings

---

## Objective

Identify hierarchical and measurement relationships within evaluation factor entities to model the complete evaluation framework structure.

## Task

Given a list of entities classified as `evaluation_factor`, identify relationships that capture:

1. **Factor Hierarchy** - Main factors and their subfactors
2. **Rating Scales** - Rating levels associated with factors
3. **Metrics & Thresholds** - Performance measures and acceptance criteria
4. **Evaluation Processes** - Analysis methods and procedures

## Input Format

```json
[
  {
    "entity_id": "unique_identifier",
    "entity_name": "Factor 1",
    "description": "Technical Factor encompassing subfactors 1.1 to 1.4..."
  },
  ...
]
```

## Relationship Types

### 1. HAS_SUBFACTOR

Parent evaluation factor contains child subfactors.

**Examples**:

- Factor 1 (Technical Factor) → Subfactor 1.1 (TOMP)
- Factor 1 → Subfactor 1.2 (Mission Essential Plan)
- Factor 2 (Price Factor) → Price Reasonableness

**Pattern**: Look for "Factor X" → "Subfactor X.Y" or explicit parent-child mentions

### 2. HAS_RATING_SCALE

Evaluation factor uses specific rating levels for assessment.

**Examples**:

- Factor 1 → Outstanding
- Factor 1 → Good
- Factor 1 → Acceptable
- Subfactor 1.1 → Marginal
- Subfactor 1.1 → Unacceptable

**Pattern**: Rating terms (Outstanding, Good, Acceptable, Marginal, Unacceptable, Pass, Fail) linked to factors

### 3. MEASURED_BY

Evaluation factor or subfactor is assessed using specific metrics.

**Examples**:

- Subfactor 1.1 → 95% Compliance Rate
- Service Quality → 100% Inspection
- Performance → Zero Discrepancies Allowed
- Maintenance → 95% Operational Rate

**Pattern**: Numeric metrics (%, thresholds, rates) that measure factor performance

### 4. HAS_THRESHOLD

Metric has an associated acceptance threshold or criterion.

**Examples**:

- 95% Compliance Rate → Satisfactory Threshold
- Zero Discrepancies Allowed → 18 objectives
- 100% Inspection → No complaints

**Pattern**: Metrics linked to specific performance levels or criteria

### 5. EVALUATED_USING

Evaluation factor uses a specific process or method.

**Examples**:

- Price Factor → Price Realism Analysis
- Factor 1 → Technical Rating
- Subfactor 1.1 → Pass/Fail Evaluation
- Price → Bid Evaluation

**Pattern**: Evaluation processes, analyses, or methods used to assess factors

### 6. DEFINES_SCALE

Entity defines or describes a rating scale structure.

**Examples**:

- Technical Rating Definitions Table → Acceptable
- Technical/Risk Ratings Evaluation Scale → Outstanding
- Evaluation Factors → Factor 1

**Pattern**: Tables or frameworks that define rating structures

## Classification Rules

### Main Evaluation Factors

Entities that ARE true evaluation factors (keep for Requirement→Factor linking):

- Contains "Factor" followed by number (Factor 1, Factor 2)
- Contains "Subfactor" followed by number (Subfactor 1.1, 1.2, etc.)
- Named evaluation categories (Technical Factor, Price Factor)
- Specific evaluation plans (TOMP, Mission Essential Plan, Quality Control Plan)

### Supporting Entities

Entities that SUPPORT evaluation factors (use for hierarchy only):

- Rating terms: Outstanding, Good, Acceptable, Marginal, Unacceptable, Pass, Fail
- Metrics: Any entity with percentage (95%, 100%), rates, or numeric thresholds
- Processes: Contains "Evaluation", "Analysis", "Assessment", "Rating"
- Thresholds: Contains "Threshold", "Level", "Criteria", "Standard"
- Tables: Contains "(table)" or "Table" with number

## Output Format

Return a JSON array of relationships:

```json
[
  {
    "source_id": "entity_id_of_parent",
    "target_id": "entity_id_of_child",
    "relationship_type": "HAS_SUBFACTOR",
    "confidence": 0.95,
    "reasoning": "Factor 1 explicitly lists Subfactor 1.1 as a component in description"
  },
  {
    "source_id": "entity_id_of_factor",
    "target_id": "entity_id_of_rating",
    "relationship_type": "HAS_RATING_SCALE",
    "confidence": 0.90,
    "reasoning": "Outstanding is a rating level used to assess Factor 1 proposals"
  },
  ...
]
```

## Validation Rules

1. **Confidence Scoring**:

   - 0.95-1.0: Explicit hierarchy mentioned in description
   - 0.85-0.94: Strong contextual evidence (naming patterns, table structures)
   - 0.75-0.84: Moderate evidence (domain knowledge, typical patterns)
   - Below 0.75: Reject (too uncertain)

2. **Relationship Constraints**:

   - HAS_SUBFACTOR: Only from main factors to subfactors
   - HAS_RATING_SCALE: Only to actual rating terms (Outstanding, Good, etc.)
   - MEASURED_BY: Only to entities with numeric/quantifiable measures
   - No circular relationships

3. **Evidence Requirements**:
   - Must cite specific text from entity descriptions
   - Explain why relationship exists
   - Identify relationship type clearly

## Example Analysis

**Input Entities**:

```json
[
  {
    "entity_id": "e1",
    "entity_name": "Factor 1",
    "description": "Technical Factor with subfactors 1.1-1.4"
  },
  {
    "entity_id": "e2",
    "entity_name": "Subfactor 1.1",
    "description": "TOMP rated Outstanding to Unacceptable"
  },
  {
    "entity_id": "e3",
    "entity_name": "Outstanding",
    "description": "Highest rating for exceptional proposals"
  },
  {
    "entity_id": "e4",
    "entity_name": "95% Compliance Rate",
    "description": "Satisfactory threshold example"
  }
]
```

**Expected Output**:

```json
[
  {
    "source_id": "e1",
    "target_id": "e2",
    "relationship_type": "HAS_SUBFACTOR",
    "confidence": 0.95,
    "reasoning": "Factor 1 description explicitly mentions subfactors 1.1-1.4"
  },
  {
    "source_id": "e2",
    "target_id": "e3",
    "relationship_type": "HAS_RATING_SCALE",
    "confidence": 0.92,
    "reasoning": "Subfactor 1.1 uses Outstanding as highest rating level"
  },
  {
    "source_id": "e2",
    "target_id": "e4",
    "relationship_type": "MEASURED_BY",
    "confidence": 0.85,
    "reasoning": "95% Compliance Rate is a performance metric for evaluating subfactor quality"
  }
]
```

## Special Considerations

1. **Tables**: Entities marked as "(table)" often define rating scales or factor structures - create DEFINES_SCALE relationships

2. **Price Analysis**: Price-related entities (Price Realism, Price Reasonableness) should link to Price Factor via EVALUATED_USING

3. **Binary Ratings**: Pass/Fail evaluations are simpler rating scales - still use HAS_RATING_SCALE

4. **Avoid Redundancy**: Don't create both Factor→Rating and Subfactor→Rating if subfactor inherits from factor

5. **Main Factor Identification**: Only entities matching main factor patterns should be marked for direct Requirement linking
