# Semantic Concept Linking Rules

**Purpose**: Infer implicit relationships between concepts that inform proposal evaluation  
**Why This Matters**: Reveals hidden connections (e.g., "Safety Factor mentioned alongside Management Approach")  
**Method**: LLM-powered semantic inference across CONCEPT, STRATEGIC_THEME, EVALUATION_FACTOR entities  
**Status**: CORE ALGORITHM (always enabled) - Required for advanced queries and knowledge graph visualization

---

## Core Relationship Patterns

### Pattern 1: INFORMS (Concept → Evaluation Factor)

```
CONCEPT/STRATEGIC_THEME --INFORMS--> EVALUATION_FACTOR
```

**Meaning**: This concept contributes to evaluation under this factor

**Examples**:

```
"past performance" --INFORMS--> "Proposal Evaluation"
"technical approach themes" --INFORMS--> "Technical Approach Factor"
"performance confidence assessment" --INFORMS--> "Past Performance Factor"
"management principles" --INFORMS--> "Management Approach Factor"
```

---

### Pattern 2: IMPACTS (Weakness/Strength → Rating)

```
CONCEPT --IMPACTS--> CONCEPT (rating-related)
```

**Meaning**: This quality affects scoring outcome

**Examples**:

```
"significant weakness" --REDUCES--> "overall rating"
"significant strength" --INCREASES--> "factor score"
"deficiency" --TRIGGERS--> "discussions"
"past performance confidence" --DETERMINES--> "award decision"
```

---

### Pattern 3: DETERMINES (Factor → Award)

```
EVALUATION_FACTOR --DETERMINES--> EVENT (award decision)
```

**Meaning**: This factor influences contract award outcome

**Examples**:

```
"Proposal Evaluation" --DETERMINES--> "award"
"overall rating" --DETERMINES--> "selection decision"
"competitive range" --DETERMINES--> "discussions eligibility"
```

---

### Pattern 4: GUIDES (Requirements → Evaluation)

```
CONCEPT --GUIDES--> EVALUATION_FACTOR
```

**Meaning**: Solicitation requirements guide evaluation approach

**Examples**:

```
"solicitation requirements" --GUIDES--> "Proposal Evaluation"
"technical factors" --GUIDES--> "Technical Approach scoring"
"performance objectives" --GUIDES--> "Past Performance assessment"
```

---

## Five Semantic Inference Algorithms

### Algorithm 1: Pain Point → Factor Mapping

**Purpose**: Link customer pain points to evaluation factors for targeted proposal writing

**Example Query**: "What are the main pain points of the customer and how would we effectively address them in a proposal? Which evaluation factors would we address them?"

**Inference Logic**:

```
IF STRATEGIC_THEME mentions "pain point" or "challenge"
AND EVALUATION_FACTOR addresses related topic
THEN create: STRATEGIC_THEME --ADDRESSED_BY--> EVALUATION_FACTOR
```

**Real Example**:

```
STRATEGIC_THEME: "Outdated IT infrastructure causing downtime"
  --ADDRESSED_BY-->
EVALUATION_FACTOR: "Technical Approach - System Modernization" (40% weight)
```

**LLM Prompt Snippet**:

```
Identify customer pain points from:
- Section C (SOW) problem statements
- Section L (Instructions) emphasis areas
- Section M (Evaluation) high-weight factors

Link each pain point to:
- Evaluation factor that scores solution
- Requirements that must address pain point
```

---

### Algorithm 2: Factor Element Decomposition

**Purpose**: Break evaluation factors into sub-elements for compliance matrix

**Example Query**: "What are the factor elements for past performance?"

**Inference Logic**:

```
IF EVALUATION_FACTOR has sub-factors or subfactors mentioned
THEN create: EVALUATION_FACTOR (sub) --CHILD_OF--> EVALUATION_FACTOR (parent)
AND: CONCEPT (element) --INFORMS--> EVALUATION_FACTOR (sub)
```

**Real Example**:

```
EVALUATION_FACTOR: "Factor 3 - Past Performance" (20% weight)
  ├── CONCEPT: "relevant contracts" --INFORMS--> Past Performance
  ├── CONCEPT: "contract value similarity" --INFORMS--> Past Performance
  ├── CONCEPT: "performance confidence assessment" --INFORMS--> Past Performance
  ├── CONCEPT: "recency (within 3 years)" --INFORMS--> Past Performance
  └── CONCEPT: "scope similarity" --INFORMS--> Past Performance
```

**From Navy MBOS Section M**:

```
Factor 2 - Management Approach (30%)
  ├── management approach demonstration
  ├── workforce management levels
  ├── labor force competencies
  ├── productivity metrics
  ├── quality management
  ├── scheduling approach
  ├── phase-in plans
  └── hours/staffing levels
```

---

### Algorithm 3: Adjacent Factor Discovery

**Purpose**: Identify factors mentioned near each other that may have hidden relationships

**Example Query**: "What are the evaluation factors regarding management?"

**Insight Generated**: "Safety Factor (from RFP Section M) - Although not directly related to management approach, safety is mentioned alongside factor 2 and could be considered during evaluation"

**Inference Logic**:

```
IF EVALUATION_FACTOR_A and EVALUATION_FACTOR_B appear within N lines/paragraphs
AND they are NOT explicitly linked by Section L
THEN create: EVALUATION_FACTOR_A --RELATED_TO--> EVALUATION_FACTOR_B (confidence: 0.60)
WITH note: "Mentioned adjacently in Section M"
```

**Real Example**:

```
EVALUATION_FACTOR: "Factor 2 - Management Approach" (Section M, para 3)
EVALUATION_FACTOR: "Factor 3 - Safety" (Section M, para 4)

Inference:
"Management Approach" --RELATED_TO--> "Safety"
Confidence: 0.60
Reasoning: "Adjacent factors in Section M may share evaluation criteria"
```

---

### Algorithm 4: Proposal Outline Generation

**Purpose**: Build section-by-section proposal outline based on evaluation weights

**Example Query**: "Based on the proposal instructions provide me a bulletized proposal outline and specifics on the content I should address the customer pain points and identify solutioning opportunities that may gain me more favor in the award decision."

**Inference Logic**:

```
FOR each EVALUATION_FACTOR (ordered by weight DESC):
  1. Find all REQUIREMENT --EVALUATED_BY--> FACTOR
  2. Find all SUBMISSION_INSTRUCTION --GUIDES--> FACTOR
  3. Find all STRATEGIC_THEME --ADDRESSED_BY--> FACTOR
  4. Group by requirement_classification (TECHNICAL, MANAGEMENT, etc.)
  5. Generate outline section with page allocation
```

**Output Structure**:

```
Proposal Outline (Technical Volume)

1. Technical Approach (40% weight, 10 pages max)
   A. System Architecture
      - Requirement REQ-012: Cloud integration (MANDATORY)
      - Pain Point: Legacy system downtime
      - Solution Opportunity: Zero-downtime migration
   B. Cybersecurity Controls
      - Requirement REQ-027: NIST 800-171 compliance (MANDATORY)
      - Pain Point: Data breach risks
      - Solution Opportunity: Multi-layer defense

2. Management Approach (30% weight, 8 pages max)
   A. Workforce Management
      - Requirement REQ-043: Weekly status reports (MANDATORY)
      - Pain Point: Poor communication with past vendors
      - Solution Opportunity: Real-time dashboard
   B. Quality Management
      - Requirement REQ-055: ISO 9001 certification (IMPORTANT)
      - Pain Point: Defect rates above acceptable
      - Solution Opportunity: Six Sigma methodology
```

---

### Algorithm 5: Competitive Advantage Identification

**Purpose**: Identify high-value opportunities for competitive differentiation

**Inference Logic**:

```
FOR each EVALUATION_FACTOR:
  IF factor.weight >= 0.30 (high weight)
  AND related_requirements.criticality == "MANDATORY"
  AND pain_points.count > 0
  THEN: High-value opportunity for differentiation
```

**Example Output**:

```
OPPORTUNITY_001:
  Factor: Technical Approach (40% weight)
  Pain Point: "Outdated IT infrastructure causing downtime"
  Requirement: REQ-012 "System modernization" (MANDATORY)
  Competitive Edge: Propose phased migration with zero downtime
  Rationale: High weight + mandatory requirement + customer pain = max impact

OPPORTUNITY_002:
  Factor: Management Approach (30% weight)
  Pain Point: "Poor communication from incumbent contractor"
  Requirement: REQ-043 "Weekly status reports" (MANDATORY)
  Competitive Edge: Real-time project dashboard with 24/7 access
  Rationale: Addresses pain point + mandatory requirement + differentiator
```

---

## LLM Inference Prompt Template

```
You are analyzing RFP entities to discover implicit semantic relationships.

ENTITIES:
{json_list_of_concepts_themes_factors}

TASK:
Infer semantic relationships based on:

1. PAIN POINT → FACTOR (High value for proposal):
   - STRATEGIC_THEME (pain point) --ADDRESSED_BY--> EVALUATION_FACTOR
   - IF factor has high weight AND addresses pain point → competitive opportunity

2. FACTOR ELEMENTS (Decomposition):
   - Break evaluation factors into sub-elements
   - CONCEPT (element) --INFORMS--> EVALUATION_FACTOR
   - Example: "relevant contracts" --INFORMS--> "Past Performance"

3. ADJACENT FACTORS (Hidden relationships):
   - IF factors mentioned within 5 paragraphs → potential relationship
   - EVALUATION_FACTOR_A --RELATED_TO--> EVALUATION_FACTOR_B (confidence: 0.60)
   - Note: "Mentioned adjacently, may share criteria"

4. CONCEPT → RATING (Impact analysis):
   - "significant weakness" --REDUCES--> "overall rating"
   - "past performance confidence" --DETERMINES--> "award decision"

5. PROPOSAL STRUCTURE (Outline generation):
   - Group requirements by evaluation factor
   - Weight by factor importance (%) and page limits
   - Link pain points to solution opportunities

CONFIDENCE SCORING:
- Explicit mention in same paragraph: 0.90
- Mentioned in same section: 0.75
- Topic alignment: 0.70
- Adjacent factors: 0.60

OUTPUT FORMAT:
[
  {
    "source_id": "concept_or_theme_id",
    "target_id": "factor_or_concept_id",
    "relationship_type": "INFORMS|IMPACTS|DETERMINES|GUIDES|ADDRESSED_BY|RELATED_TO",
    "confidence": 0.60-0.90,
    "reasoning": "Explanation with query use case",
    "business_value": "How this helps proposal development"
  }
]
```

---

## Special Cases

### Case 1: Multi-Factor Pain Points

**Problem**: Pain point affects multiple evaluation factors

**Example**:

```
STRATEGIC_THEME: "Cybersecurity vulnerabilities in legacy systems"

Maps to:
- Technical Approach (40%) - system architecture
- Management Approach (30%) - risk management
- Past Performance (20%) - security track record
```

**Solution**: Create multiple ADDRESSED_BY relationships with confidence based on relevance

---

### Case 2: Unstated but Implied Factors

**Problem**: Section M mentions factor briefly, details scattered elsewhere

**Example**:

```
Section M: "Factor 3 - Safety (although not directly related to management...)"

This IMPLIES:
- Safety is evaluated separately from management
- BUT may consider management practices that affect safety
- Proposal should address safety in both Technical AND Management sections
```

**Solution**: Create RELATED_TO relationship with note explaining adjacency

---

### Case 3: Shipley "Win Themes" Extraction

**Problem**: Identify discriminators that win proposals (Shipley methodology)

**Inference**:

```
IF REQUIREMENT.criticality == "MANDATORY"
AND EVALUATION_FACTOR.weight >= 0.25
AND STRATEGIC_THEME (pain point) exists
THEN: High-value win theme opportunity
```

**Example**:

```
WIN_THEME_001:
  Title: "Zero-Downtime Migration"
  Requirements: REQ-012 (MANDATORY), REQ-015 (IMPORTANT)
  Factor: Technical Approach (40%)
  Pain Point: "Legacy system causing 10% downtime"
  Competitive Edge: Propose phased migration during off-hours
  Shipley Score: 95/100 (high discriminator)
```

---

## Integration with Existing Relationships

### Complements (Not Replaces)

**Existing Prompts** (structural relationships):

- `document_hierarchy.md`: J-02000000-10 → J-02000000
- `requirement_evaluation.md`: REQ-043 → Management Approach
- `section_l_m_linking.md`: Page limit → Technical Approach

**Semantic Linking** (this prompt - conceptual relationships):

- "past performance" → Proposal Evaluation
- "significant weakness" → overall rating
- "safety factor" → management approach (adjacent)

**Combined Query Power**:

```
Query: "What impacts my Management Approach score?"

Structural:
- 15 requirements EVALUATED_BY Management Approach
- 3 submission instructions GUIDES Management Approach
- Section L page limit: 8 pages

Semantic:
- Pain point: "poor communication" ADDRESSED_BY Management Approach
- Adjacent factor: Safety (mentioned alongside in Section M)
- Concept: "workforce management levels" INFORMS Management Approach
- Impact: "significant weakness" REDUCES overall rating
```

---

## Quality Validation

### Validation Rules

1. ✅ **Confidence threshold**: ≥0.60 (lower than structural, these are inferences)
2. ✅ **Business value**: Each relationship must have clear proposal development use
3. ✅ **Avoid over-connection**: Not every concept links to every factor (be selective)
4. ✅ **Adjacent factor notes**: Always explain WHY factors are related

### Expected Relationship Counts (Baseline)

**Navy MBOS (71-page RFP)**:

- Evaluation factors: 5 entities
- Concepts: ~30 entities
- Strategic themes: ~10 entities
- Expected semantic relationships: ~40-50 (8-10 per factor)

**Breakdown**:

- Pain point → Factor: ~10 relationships
- Factor elements (INFORMS): ~20 relationships
- Adjacent factors (RELATED_TO): ~5 relationships
- Concept → Rating (IMPACTS): ~10 relationships

---

## Success Criteria

A successful semantic concept linking run should:

1. ✅ **Reveal hidden connections**: Adjacent factors identified with explanation
2. ✅ **Enable proposal queries**: Answers "What impacts Factor X?" comprehensively
3. ✅ **Support Shipley methodology**: Win themes = mandatory requirements + high-weight factors + pain points
4. ✅ **Proposal outline generation**: Automated structure based on evaluation weights

---

**Last Updated**: January 2025 (Branch 004 - Phase 1)  
**Version**: 1.0 (New - Semantic inference for proposal intelligence)  
**Status**: CORE ALGORITHM - Always enabled (not optional)  
**Impact**: Enables advanced queries: pain point mapping, proposal outlines, competitive analysis, factor decomposition, adjacent factor discovery  
**Cost**: ~$0.01 per RFP (5,000-token context to Grok-beta)  
**Time**: +10-15 seconds processing (15% increase over baseline)  
**Value**: Competitive differentiation - finds relationships humans might miss
