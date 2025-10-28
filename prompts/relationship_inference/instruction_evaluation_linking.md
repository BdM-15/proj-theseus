# Instruction-Evaluation Linking: Section L↔M Relationship Inference

**Purpose**: Map submission instructions (Section L) to evaluation factors (Section M)  
**Focus**: GUIDES relationships (Submission Instruction → Evaluation Factor)  
**Confidence Target**: ≥0.80 for all relationships  
**Pattern**: Explicit cross-references and topic alignment  
**Last Updated**: October 28, 2025 (Proven Patterns)

---

## The Core Pattern: GUIDES

```
SUBMISSION_INSTRUCTION --GUIDES--> EVALUATION_FACTOR
```

This maps how submission instructions (page limits, format rules) guide and constrain evaluation factors.

---

## Pattern 1: Explicit Cross-Reference (Confidence: 0.98)

**Rule**: Section L explicitly references Section M factors

### Examples

```
"Technical Volume limited to 25 pages, addressing Section M Factors 1.1, 1.2, and 1.3"
→ GUIDES (Confidence 0.98)

"Volume addressing Section M.1 (Technical Approach) shall not exceed 30 pages"
→ GUIDES (Confidence 0.98)

"See Section L.3.2 for page limits applicable to Section M.2 evaluation"
→ GUIDES (Confidence 0.98)
```

**Extraction**:
```
Source: "Technical Volume Page Limit: 25 pages"
Target: "Section M.1: Technical Approach (40% weight)"
Type: GUIDES
Confidence: 0.98
Reasoning: "Explicit: 'addressing Section M Factors 1.1, 1.2, and 1.3'"
```

---

## Pattern 2: Topic Alignment (Confidence: 0.85-0.90)

**Rule**: Submission instruction topic matches evaluation factor topic

### Topic Matching Table

| Submission Topic              | Evaluation Topic           | Relationship | Confidence |
| ----------------------------- | -------------------------- | ------------ | ---------- |
| Technical volume format       | Technical Approach factor  | GUIDES       | 0.90       |
| Management volume format      | Management Approach factor | GUIDES       | 0.90       |
| Page limit for proposal       | Primary evaluation factor  | GUIDES       | 0.90       |
| Font/margin requirements      | All factors in that volume | GUIDES       | 0.85       |
| Cost volume format            | Cost/Price factor          | GUIDES       | 0.85       |
| Past Performance volume       | Past Performance factor    | GUIDES       | 0.90       |
| Executive Summary format      | Overall evaluation         | GUIDES       | 0.80       |

**Examples**:
```
"Management Volume shall address the following key areas:
- Staffing plan
- Quality assurance
- Risk management"

→ Links to "Section M.2: Management Approach"
```

**Extraction**:
```
Source: "Management Volume Submission Format"
Target: "Section M.2: Management Approach (35% weight)"
Type: GUIDES
Confidence: 0.85
Reasoning: "Topic alignment: Management volume format guides Management factor evaluation"
```

---

## Pattern 3: Embedded Evaluation Criteria (Confidence: 0.80-0.85)

**Rule**: Section M criteria embedded within Section L submission instructions

### Examples

```
"Section L.2: Technical Volume

The Technical Volume shall demonstrate:
1. Solution Architecture and Design
2. Innovation and Advanced Capabilities
3. Risk Management Strategy

[These subfactors are defined in Section M.1.1, M.1.2, M.1.3]"
```

**Extraction**:
```
Source: "Technical Volume Submission Instructions"
Target: "Solution Architecture Subfactor (Section M.1.1)"
Type: GUIDES
Confidence: 0.85
Reasoning: "Submission instructions specify subfactor requirements"
```

---

## Pattern 4: Implicit Format Constraints (Confidence: 0.75-0.80)

**Rule**: Page limit implicitly guides evaluation strategy

### Examples

```
"Technical Approach limited to 15 pages"
+ "Technical Approach is 40% of evaluation"

→ GUIDES relationship (high weight × tight page limit = constrained evaluation)
```

**Extraction**:
```
Source: "Technical Approach Volume: 15 pages maximum"
Target: "Section M.1: Technical Approach (40% weight)"
Type: GUIDES
Confidence: 0.75
Reasoning: "Page constraint implicitly guides proposal strategy for 40% weight factor"
```

---

## Special Cases: Multiple Targets

### Rule: One instruction may guide multiple factors

```
"Total volume (Technical + Management) limited to 50 pages"
→ GUIDES Section M.1 (Technical)
→ GUIDES Section M.2 (Management)

Extract BOTH relationships:
```

**Extraction**:
```
Source: "Combined Technical-Management Volume: 50 pages"
Target 1: "Section M.1: Technical Approach"
Type: GUIDES
Confidence: 0.80

Target 2: "Section M.2: Management Approach"
Type: GUIDES
Confidence: 0.80
```

---

## When to Create vs Reject

### ✅ CREATE

```
Source: "Technical Volume Format (Section L.3): 25 pages"
Target: "Factor 1: Technical Approach (Section M.1)"
Type: GUIDES
Confidence: 0.98
Reasoning: "Explicit: 'Technical Volume limited to 25 pages, 
evaluates Section M Technical Approach'"
```

```
Source: "Cost Volume Format (Section L.2.2)"
Target: "Factor 4: Cost/Price"
Type: GUIDES
Confidence: 0.90
Reasoning: "Topic alignment: Cost submission format guides cost evaluation"
```

### ❌ REJECT (< 0.70)

```
Source: "General Submission Instructions"
Target: "Some evaluation factor"
Confidence: 0.50 [TOO LOW]
Reason: "No clear connection between instructions and specific factor"
```

---

## Output Checklist

✅ Source is a SUBMISSION_INSTRUCTION entity  
✅ Target is an EVALUATION_FACTOR entity  
✅ Type is exactly `GUIDES`  
✅ Confidence ≥ 0.70 (use patterns above)  
✅ Reasoning explains which pattern was used  
✅ Multiple targets handled correctly (separate relationships)  
✅ No duplicate relationships (same source/target)  
✅ Directional: Instruction → Factor (not reversed)
