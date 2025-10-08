# Requirement → Evaluation Factor Mapping Rules

**Purpose**: Link requirements to the evaluation factors that score them  
**Why This Matters**: Enables effort allocation and proposal outline optimization  
**Method**: LLM-powered semantic inference (topic alignment + criticality)

---

## Core Relationship Pattern

```
REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR
```

**Meaning**: This requirement is scored under this evaluation factor

**Example**:
```
REQUIREMENT "Weekly status reports" (criticality: MANDATORY)
  --EVALUATED_BY-->
EVALUATION_FACTOR "Management Approach" (weight: 30%)
```

**Business Value**: Proposal teams allocate effort based on factor weights

---

## Four Inference Patterns

### Pattern 1: Topic Alignment (Confidence: 0.80)

**Signal**: Requirement topic matches evaluation factor topic

**Example**:
```
REQUIREMENT: "The contractor shall provide 24/7 help desk support"
EVALUATION_FACTOR: "Technical Approach - Help Desk Operations"
```

**Topic Match**: "help desk support" ↔ "Help Desk Operations"

**Extraction**:
```json
{
  "source_id": "requirement_helpdesk_247",
  "target_id": "factor_technical_helpdesk",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.80,
  "reasoning": "Topic alignment: help desk requirement → help desk factor"
}
```

### Pattern 2: Criticality Mapping (Confidence: 0.75)

**Signal**: MANDATORY requirements → high-weight factors

**Example**:
```
REQUIREMENT: "shall provide weekly status reports" (criticality: MANDATORY)
EVALUATION_FACTOR: "Management Approach" (weight: 30%)
```

**Logic**: Management requirements typically scored under Management Approach

**Extraction**:
```json
{
  "source_id": "requirement_status_reports",
  "target_id": "factor_management_approach",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.75,
  "reasoning": "Criticality mapping: MANDATORY reporting requirement → Management Approach factor"
}
```

### Pattern 3: Content Proximity (Confidence: 0.70)

**Signal**: Requirement and factor appear near each other in document

**Example**:
```
Section M: Evaluation Factor 2 - Technical Approach (40%)

Section C: The contractor shall implement a cybersecurity framework
compliant with NIST 800-171.
```

**Proximity**: Cybersecurity requirement discussed near Technical Approach factor

**Extraction**:
```json
{
  "source_id": "requirement_cybersecurity_nist",
  "target_id": "factor_technical_approach",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.70,
  "reasoning": "Content proximity: Cybersecurity requirement referenced near Technical Approach factor"
}
```

### Pattern 4: Explicit Cross-Reference (Confidence: 0.95)

**Signal**: Requirement explicitly mentions evaluation factor

**Example**:
```
"The contractor shall provide a quality assurance plan (see Section M,
Factor 3: Quality Control)"
```

**Extraction**:
```json
{
  "source_id": "requirement_qa_plan",
  "target_id": "factor_quality_control",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.95,
  "reasoning": "Explicit cross-reference: 'see Section M, Factor 3: Quality Control'"
}
```

---

## Topic Alignment Categories

### Category 1: Technical Requirements
**Typical Factors**:
- Technical Approach
- Technical Capability
- System Architecture
- Technology Solution

**Examples**:
```
"shall integrate with existing IT systems" → Technical Approach
"shall support 99.9% uptime" → Technical Capability
"shall use cloud infrastructure" → System Architecture
```

### Category 2: Management Requirements
**Typical Factors**:
- Management Approach
- Program Management
- Project Management Plan
- Risk Management

**Examples**:
```
"shall provide weekly status reports" → Management Approach
"shall maintain project schedule" → Program Management
"shall identify and mitigate risks" → Risk Management
```

### Category 3: Performance Requirements
**Typical Factors**:
- Past Performance
- Demonstrated Experience
- Relevant Experience
- Corporate Experience

**Examples**:
```
"Contractor must have 5 years experience" → Past Performance
"Similar contracts within last 3 years" → Demonstrated Experience
```

### Category 4: Personnel Requirements
**Typical Factors**:
- Key Personnel
- Staffing Approach
- Personnel Qualifications
- Team Composition

**Examples**:
```
"Program Manager shall have PMP certification" → Key Personnel
"shall provide resumes for all proposed staff" → Personnel Qualifications
```

### Category 5: Quality Requirements
**Typical Factors**:
- Quality Control
- Quality Assurance Plan
- Quality Management
- Performance Standards

**Examples**:
```
"shall maintain ISO 9001 certification" → Quality Control
"shall conduct quarterly quality audits" → Quality Assurance Plan
```

### Category 6: Transition Requirements
**Typical Factors**:
- Transition Plan
- Transition Approach
- Phase-In Plan
- Continuity of Operations

**Examples**:
```
"shall complete transition within 90 days" → Transition Plan
"shall ensure zero downtime during transition" → Continuity of Operations
```

---

## LLM Inference Prompt Template

```
You are analyzing government contract requirements to map them to evaluation factors.

REQUIREMENTS:
{json_list_of_requirements}

EVALUATION_FACTORS:
{json_list_of_evaluation_factors}

TASK:
For each requirement, determine which evaluation factor(s) will score it based on:

1. TOPIC ALIGNMENT (Confidence 0.80):
   - Requirement topic matches factor topic
   - Help desk requirement → Help Desk factor
   - Cybersecurity requirement → Security factor

2. CRITICALITY MAPPING (Confidence 0.75):
   - MANDATORY requirements → high-weight factors
   - Management requirements → Management Approach
   - Technical requirements → Technical Approach

3. CONTENT PROXIMITY (Confidence 0.70):
   - Requirement discussed near factor in document
   - Section C requirement referenced in Section M factor

4. EXPLICIT CROSS-REFERENCE (Confidence 0.95):
   - "see Section M, Factor 3"
   - "evaluated under Technical Approach"

TOPIC CATEGORIES:
- Technical: IT systems, uptime, cloud, integration
- Management: status reports, schedules, risk management
- Personnel: qualifications, staffing, key personnel
- Quality: ISO certification, quality audits, standards
- Performance: experience, past performance, similar contracts
- Transition: phase-in, continuity, zero downtime

SPECIAL RULES:
- One requirement may map to MULTIPLE factors (e.g., cybersecurity → Technical + Security)
- MANDATORY requirements with criticality_level > 0.80 → higher confidence
- Use requirement.requirement_type to guide factor selection:
  - FUNCTIONAL → Technical Approach
  - PERFORMANCE → Performance Standards
  - SECURITY → Security Factor (if exists) or Technical Approach
  - MANAGEMENT → Management Approach

OUTPUT FORMAT:
[
  {
    "source_id": "requirement_id",
    "target_id": "factor_id",
    "relationship_type": "EVALUATED_BY",
    "confidence": 0.70-0.95,
    "reasoning": "Brief explanation with pattern name"
  }
]
```

---

## Special Cases

### Case 1: One Requirement → Multiple Factors

**Example**:
```
REQUIREMENT: "The contractor shall implement NIST 800-171 cybersecurity controls"
```

**Maps to**:
1. Factor 2: Technical Approach (cybersecurity implementation)
2. Factor 4: Security Compliance (NIST 800-171 compliance)

**Extraction**:
```json
[
  {
    "source_id": "requirement_nist_800_171",
    "target_id": "factor_technical_approach",
    "relationship_type": "EVALUATED_BY",
    "confidence": 0.75,
    "reasoning": "Topic alignment: cybersecurity implementation → Technical Approach"
  },
  {
    "source_id": "requirement_nist_800_171",
    "target_id": "factor_security_compliance",
    "relationship_type": "EVALUATED_BY",
    "confidence": 0.85,
    "reasoning": "Explicit compliance requirement → Security Compliance factor"
  }
]
```

### Case 2: INFORMATIONAL Requirements

**Rule**: Government obligations (Government shall) do NOT map to evaluation factors

**Example**:
```
REQUIREMENT: "The Government shall provide GFE within 30 days"
(criticality: INFORMATIONAL, priority_score: 0)
```

**Action**: Skip this requirement (government obligation, not contractor)

### Case 3: No Clear Factor Match

**Rule**: If no semantic match found, check if requirement is truly INFORMATIONAL

**Example**:
```
REQUIREMENT: "Contract period: 5 years with 5 option years"
(criticality: INFORMATIONAL)
```

**Action**: Skip (administrative detail, not performance requirement)

### Case 4: Requirement Type Overrides

**Rule**: Use requirement_type field for high-confidence mappings

**Example**:
```
REQUIREMENT: "shall conduct risk assessments quarterly"
requirement_type: MANAGEMENT
requirement_classification: MANAGEMENT
```

**Override**: Even though "risk" might match Security factor, MANAGEMENT type → Management Approach

**Extraction**:
```json
{
  "source_id": "requirement_risk_assessments",
  "target_id": "factor_management_approach",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.85,
  "reasoning": "Requirement type override: MANAGEMENT classification → Management Approach"
}
```

---

## Quality Validation

### Validation Rules

1. ✅ **MANDATORY requirements mapped**: criticality_level ≥ 0.80 → has EVALUATED_BY relationship
2. ✅ **Confidence threshold**: ≥0.70
3. ✅ **No INFORMATIONAL mappings**: Government obligations skipped
4. ✅ **Topic category alignment**: Technical requirements → Technical factors

### Expected Relationship Counts (Baseline)

**Navy MBOS (71-page RFP)**:
- Requirements: ~80 entities (REQUIREMENT type)
- MANDATORY requirements: ~50 (criticality_level ≥ 0.80)
- Evaluation factors: 5 factors (Section M)
- Expected EVALUATED_BY relationships: ~60 (75% of requirements)

**Why not 100%?**: Some requirements are INFORMATIONAL (government obligations) or administrative details

---

## Examples from Real RFPs

### Example 1: Navy MBOS - Management Requirements

**Requirement**:
```
REQUIREMENT_043: "The Contractor shall provide weekly status reports
to the COR (Contracting Officer's Representative)."
- criticality: MANDATORY
- criticality_level: 1.0
- requirement_type: MANAGEMENT
- requirement_classification: MANAGEMENT
```

**Factor**:
```
EVALUATION_FACTOR_M2: "Factor 2: Management Approach (30%)"
- Description: "The Government will evaluate the offeror's understanding
  of management, including reporting, schedule management, and risk mitigation."
```

**Extracted Relationship**:
```json
{
  "source_id": "requirement_043",
  "target_id": "evaluation_factor_m2",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.85,
  "reasoning": "Topic alignment: status reporting requirement → Management Approach factor (reporting subcategory)"
}
```

### Example 2: Navy MBOS - Technical Requirements

**Requirement**:
```
REQUIREMENT_012: "The Contractor shall integrate the solution with
the Navy's existing Enterprise Resource Planning (ERP) system."
- criticality: MANDATORY
- criticality_level: 1.0
- requirement_type: FUNCTIONAL
- requirement_classification: INTERFACE
```

**Factor**:
```
EVALUATION_FACTOR_M1: "Factor 1: Technical Approach (40%)"
- Description: "The Government will evaluate the offeror's understanding
  of technical requirements, including system integration and architecture."
```

**Extracted Relationship**:
```json
{
  "source_id": "requirement_012",
  "target_id": "evaluation_factor_m1",
  "relationship_type": "EVALUATED_BY",
  "confidence": 0.90,
  "reasoning": "Topic alignment: system integration requirement → Technical Approach factor (integration subcategory)"
}
```

### Example 3: Navy MBOS - Multiple Factor Mapping

**Requirement**:
```
REQUIREMENT_027: "The Contractor shall implement NIST 800-171 cybersecurity
controls and provide quarterly compliance reports to the Government."
- criticality: MANDATORY
- criticality_level: 1.0
- requirement_type: SECURITY
- requirement_classification: SECURITY
```

**Factors**:
```
EVALUATION_FACTOR_M1: "Factor 1: Technical Approach (40%)"
EVALUATION_FACTOR_M2: "Factor 2: Management Approach (30%)"
```

**Extracted Relationships** (2):
```json
[
  {
    "source_id": "requirement_027",
    "target_id": "evaluation_factor_m1",
    "relationship_type": "EVALUATED_BY",
    "confidence": 0.85,
    "reasoning": "Topic alignment: cybersecurity implementation → Technical Approach"
  },
  {
    "source_id": "requirement_027",
    "target_id": "evaluation_factor_m2",
    "relationship_type": "EVALUATED_BY",
    "confidence": 0.75,
    "reasoning": "Topic alignment: quarterly compliance reporting → Management Approach"
  }
]
```

---

## Error Patterns to Avoid

### ❌ Error 1: Mapping INFORMATIONAL Requirements
```
WRONG:
"Government shall provide GFE" → Technical Approach factor
```

**Correct**: Skip INFORMATIONAL requirements (government obligations)

### ❌ Error 2: Ignoring Requirement Type
```
WRONG:
"shall conduct risk assessments" → Security factor (because "risk" keyword)
```

**Correct**: requirement_type: MANAGEMENT → Management Approach factor

### ❌ Error 3: Low Confidence Guessing
```
WRONG:
"The contractor shall..." → Technical Approach (confidence: 0.50)
```

**Correct**: Only create relationship if confidence ≥0.70

### ❌ Error 4: Missing Multiple Factor Mappings
```
WRONG:
"implement NIST 800-171 cybersecurity controls" → Technical Approach only
```

**Correct**: Maps to BOTH Technical Approach (implementation) AND Management Approach (if compliance reporting required)

---

## Integration with Proposal Development

### Use Case 1: Effort Allocation

**Query**: "How much effort should we allocate to Management Approach?"

**Logic**:
1. Count EVALUATED_BY relationships to Management Approach factor
2. Weight by requirement criticality_level
3. Multiply by factor weight (30%)

**Result**: "15 MANDATORY requirements → 30% factor weight → allocate 12% of total proposal effort"

### Use Case 2: Proposal Outline Optimization

**Query**: "What requirements must be addressed in Technical Approach section?"

**Logic**:
1. Find all requirements with EVALUATED_BY → Technical Approach
2. Group by requirement_classification (FUNCTIONAL, PERFORMANCE, INTERFACE, etc.)
3. Order by criticality_level (MANDATORY first)

**Result**: Optimized proposal outline with all requirements mapped to correct sections

### Use Case 3: Compliance Matrix

**Query**: "Generate compliance matrix for Section M evaluation"

**Logic**:
1. For each evaluation factor, list all EVALUATED_BY requirements
2. Include requirement criticality, requirement_id, description
3. Add proposal page reference (to be filled by proposal team)

**Result**: Shipley-compliant requirement→factor traceability matrix

---

## Success Criteria

A successful requirement→evaluation run should:

1. ✅ **75% coverage**: 75% of MANDATORY requirements mapped to factors
2. ✅ **No INFORMATIONAL mappings**: Government obligations skipped
3. ✅ **Multiple factor support**: Requirements map to 1-3 factors as appropriate
4. ✅ **Requirement type respected**: MANAGEMENT → Management Approach (not guessed from keywords)

---

**Last Updated**: January 2025 (Branch 004)  
**Version**: 2.0 (LLM semantic inference with requirement_type override)  
**Improvement**: Preserves requirement_type metadata for high-confidence mapping
