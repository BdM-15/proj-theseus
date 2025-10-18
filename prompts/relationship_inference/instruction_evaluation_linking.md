# Submission Instructions ↔ Evaluation Criteria Linking

**Purpose**: Link submission instructions to their corresponding evaluation factors/criteria  
**Entity Types**: SUBMISSION_INSTRUCTION --GUIDES--> EVALUATION_FACTOR  
**Why This Matters**: Proposal teams need to know which format requirements (page limits, volumes, fonts)
apply to which evaluation factors to optimize compliance and scoring.

**Common Locations**:

- **Federal UCF**: Instructions in Section L, Evaluation in Section M
- **Task Orders**: "Proposal Instructions" → "Selection Criteria"
- **Quotes**: "Response Format" → "Award Methodology"
- **Embedded**: Instructions within evaluation factor descriptions

**Method**: LLM-powered semantic inference (format-agnostic, works across all RFP structures)

---

## Core Relationship Pattern

```
SUBMISSION_INSTRUCTION --GUIDES--> EVALUATION_FACTOR
```

**Meaning**: This submission instruction guides how to respond to this evaluation factor

**Example**:

```
SUBMISSION_INSTRUCTION "Technical Volume Format" (25 pages, 12pt font)
  --GUIDES-->
EVALUATION_FACTOR "Factor 1: Technical Approach"
```

---

## Three Inference Patterns

### Pattern 1: Explicit Cross-Reference (Confidence: 0.95)

**Signal**: Direct mention of factor in instruction

**Examples**:

- "Technical Volume addresses Factor 2"
- "Management proposal (L.3.2) responds to Factors 3-4"
- "Volume I shall address evaluation criteria M1-M3"

**Extraction**:

```json
{
  "source_id": "submission_instruction_tech_volume",
  "target_id": "evaluation_factor_m2",
  "relationship_type": "GUIDES",
  "confidence": 0.95,
  "reasoning": "Explicit cross-reference: 'addresses Factor 2'"
}
```

### Pattern 2: Implicit Co-Location (Confidence: 0.80)

**Signal**: Page limit mentioned near factor description (same paragraph/section)

**Example**:

```
M.2 Management Approach (Most Important)

The Government will evaluate the offeror's management plan...

The Management Volume shall not exceed 15 pages.
```

**Extraction**:

```json
{
  "source_id": "submission_instruction_mgmt_volume",
  "target_id": "evaluation_factor_m2",
  "relationship_type": "GUIDES",
  "confidence": 0.8,
  "reasoning": "Submission instruction embedded within Factor M.2 description"
}
```

### Pattern 3: Content Alignment (Confidence: 0.70)

**Signal**: Instruction topic matches factor topic

**Example**:

```
Section L.3.1: Technical Volume
- Describe your technical approach...
- Include system architecture diagrams...

Section M.1: Technical Approach
- The Government will evaluate the offeror's technical solution...
```

**Extraction**:

```json
{
  "source_id": "submission_instruction_tech_volume",
  "target_id": "evaluation_factor_m1",
  "relationship_type": "GUIDES",
  "confidence": 0.7,
  "reasoning": "Topic alignment: both reference 'technical approach' and 'system architecture'"
}
```

---

## LLM Inference Prompt Template

Use this prompt structure when calling LLM for instruction-evaluation inference:

```
You are analyzing submission instructions and evaluation criteria/factors
to determine which instructions guide which evaluation factors.

NOTE: Instructions may be labeled as "Section L", "Proposal Instructions", 
"Response Format", or embedded within factor descriptions depending on RFP structure.

SUBMISSION INSTRUCTIONS:
{json_list_of_submission_instructions}

EVALUATION CRITERIA/FACTORS:
{json_list_of_evaluation_factors}

TASK:
For each submission instruction, determine which evaluation factor(s) it guides based on:

1. EXPLICIT CROSS-REFERENCES (Confidence 0.95):
   - Direct mentions: "Volume addresses Factor X"
   - Factor IDs in text: "M1", "M2.1"

2. IMPLICIT CO-LOCATION (Confidence 0.80):
   - Instructions embedded within factor description
   - Same paragraph or section

3. CONTENT ALIGNMENT (Confidence 0.70):
   - Topic matching: "Technical Volume" → "Technical Approach factor"
   - Keyword overlap: "staffing", "maintenance", "transition"

OUTPUT FORMAT:
Return JSON array of relationships with confidence ≥ 0.70:

[
  {
    "source_id": "submission_instruction_id",
    "target_id": "evaluation_factor_id",
    "relationship_type": "GUIDES",
    "confidence": 0.70-0.95,
    "reasoning": "Brief explanation (1-2 sentences)"
  }
]
```

---

## Special Cases

### Case 1: One Instruction → Multiple Factors

**Example**:

```
L.3.1 Technical Volume (50 pages)
- Address Factors 1-3
```

**Solution**: Create 3 separate relationships

```json
[
  { "source": "tech_volume", "target": "factor_1", "confidence": 0.95 },
  { "source": "tech_volume", "target": "factor_2", "confidence": 0.95 },
  { "source": "tech_volume", "target": "factor_3", "confidence": 0.95 }
]
```

### Case 2: Embedded Instructions (Section M)

**Example**:

```
M.2 Management Approach

[Evaluation criteria...]

The Management Volume shall be limited to 15 pages...
```

**Solution**:

1. Extract SUBMISSION_INSTRUCTION entity "Management Volume Format"
2. Create GUIDES relationship to Factor M.2
3. Mark section M.2 with `contains_submission_instructions: true`

### Case 3: No Clear Mapping

**When**: Instruction has no clear factor match OR confidence < 0.70

**Solution**: Do NOT create relationship (better to have no link than wrong link)

**Example**:

```
L.2.1 Proposal Delivery
- Submit via email to contracting.officer@navy.mil
- Due date: March 15, 2025, 2:00 PM EST
```

**Analysis**: This is administrative instruction, not tied to specific evaluation factor  
**Action**: No GUIDES relationship created

---

## Quality Validation

### Validation Rules

1. ✅ **Confidence threshold**: Only create relationships with confidence ≥ 0.70
2. ✅ **Reasoning required**: Every relationship must have explanation
3. ✅ **No circular references**: A→B and B→A is invalid
4. ✅ **Valid entity IDs**: Source and target must exist in graph

### Expected Relationship Counts (Baseline)

**Navy MBOS (71-page RFP)**:

- Submission instructions: ~10 entities
- Evaluation factors: ~8 entities (including subfactors)
- Expected L↔M relationships: ~15 (some instructions guide multiple factors)

**Quality Metric**: If relationship count is 0 or >30, investigate extraction issues

---

## Examples from Navy MBOS RFP

### Example 1: Explicit Mapping

```
L.3.1 Technical Volume

The Technical Volume shall address Evaluation Factors 1 and 2
(Technical Approach and Maintenance Approach) and shall not exceed
25 pages.
```

**Extracted Relationships**:

```json
[
  {
    "source_id": "submission_instruction_tech_volume",
    "target_id": "evaluation_factor_m1_technical",
    "relationship_type": "GUIDES",
    "confidence": 0.95,
    "reasoning": "Explicit: 'shall address Evaluation Factor 1'"
  },
  {
    "source_id": "submission_instruction_tech_volume",
    "target_id": "evaluation_factor_m2_maintenance",
    "relationship_type": "GUIDES",
    "confidence": 0.95,
    "reasoning": "Explicit: 'shall address Evaluation Factor 2'"
  }
]
```

### Example 2: Embedded Instructions

```
M.2 Management Approach (Significantly More Important)

The Government will evaluate the offeror's management plan including:
- Staffing approach
- Training program
- Quality assurance

Offerors shall limit the Management Volume to 15 pages, 12-point font.
```

**Extraction**:

1. Create EVALUATION_FACTOR "Factor M.2: Management Approach"
2. Create SUBMISSION_INSTRUCTION "Management Volume Format"
3. Create relationship:

```json
{
  "source_id": "submission_instruction_mgmt_volume",
  "target_id": "evaluation_factor_m2_management",
  "relationship_type": "GUIDES",
  "confidence": 0.8,
  "reasoning": "Embedded instruction within Factor M.2 description paragraph"
}
```

### Example 3: Topic Alignment

```
Section L.3.3: Past Performance Volume
- Provide 3 relevant contracts from last 5 years
- Include CPARS ratings

Section M.3: Past Performance
- The Government will evaluate relevance and quality of past performance
```

**Extracted Relationship**:

```json
{
  "source_id": "submission_instruction_past_perf_volume",
  "target_id": "evaluation_factor_m3_past_perf",
  "relationship_type": "GUIDES",
  "confidence": 0.7,
  "reasoning": "Topic alignment: both sections reference 'past performance' and 'relevant contracts'"
}
```

---

## Error Patterns to Avoid

### ❌ Error 1: Linking Administrative Instructions

```
WRONG:
L.2.1 Proposal Delivery --GUIDES--> M.1 Technical Approach
```

Delivery instructions don't guide technical evaluation

### ❌ Error 2: Linking Unrelated Topics

```
WRONG:
L.3.1 Cost Volume --GUIDES--> M.2 Technical Approach
```

Cost instructions don't guide technical factor

### ❌ Error 3: Creating Duplicate Relationships

```
WRONG:
Tech_Volume --GUIDES--> Factor_1 (confidence: 0.95)
Tech_Volume --GUIDES--> Factor_1 (confidence: 0.70)
```

Only keep highest-confidence relationship

---

## Success Criteria

A successful L↔M inference run should:

1. ✅ Cover ≥80% of evaluation factors with at least one GUIDES relationship
2. ✅ Have average confidence ≥0.80
3. ✅ Contain no administrative instruction links (delivery, format-only)
4. ✅ Match manual review (spot-check 5 random relationships)

---

**Last Updated**: January 2025 (Branch 004)  
**Version**: 2.0 (Enhanced from regex patterns to LLM semantic inference)  
**Replaces**: Brittle Jaccard similarity regex (Phase 6.0) with LLM understanding
