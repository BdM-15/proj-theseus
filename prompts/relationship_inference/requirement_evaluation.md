# Requirement-Evaluation Linking: Requirements to Evaluation Factor Mapping

**Purpose**: Map requirements to evaluation factors that will score them  
**Focus**: EVALUATED_BY relationships (Requirement → Evaluation Factor)  
**Confidence Target**: ≥0.75 for all relationships  
**Pattern**: Topic alignment + semantic inference  
**Last Updated**: October 28, 2025 (Proven Patterns)

---

## The Core Pattern: EVALUATED_BY

```
REQUIREMENT --EVALUATED_BY--> EVALUATION_FACTOR
```

This maps which evaluation factor will score a specific requirement.

---

## Pattern 1: Explicit Factor Reference (Confidence: 0.95)

**Rule**: Requirement explicitly references evaluation factor

### Examples

```
"Contractor SHALL maintain 99.5% system uptime, evaluated under Factor 1 (Technical Approach)"
→ EVALUATED_BY (Confidence 0.95)

"Weekly status reporting required. See Factor 2 for scoring methodology."
→ EVALUATED_BY (Confidence 0.95)
```

**Extraction**:
```
Source: "99.5% System Uptime Requirement"
Target: "Section M.1: Technical Approach"
Type: EVALUATED_BY
Confidence: 0.95
Reasoning: "Explicit: 'evaluated under Factor 1 (Technical Approach)'"
```

---

## Pattern 2: Topic Alignment (Confidence: 0.75-0.80)

**Rule**: Requirement topic matches factor topic

### Topic Mapping Table

| Requirement Domain               | Evaluation Factor       | Confidence |
| -------------------------------- | ----------------------- | ---------- |
| System design, architecture      | Technical Approach      | 0.85       |
| Innovation, advanced tech, R&D   | Technical (Innovation)  | 0.85       |
| Security, risk, safety measures  | Technical (Risk)        | 0.80       |
| Project schedule, staffing       | Management Approach     | 0.85       |
| Quality assurance processes      | Management Approach     | 0.80       |
| Past contract performance        | Past Performance        | 0.95       |
| Pricing structure, cost control  | Cost/Price              | 0.95       |
| Small business participation     | Small Business          | 0.95       |
| Environmental compliance         | Management Approach     | 0.75       |

**Examples**:
```
Requirement: "AI/ML-based anomaly detection system"
Topic: Innovation/Advanced Technology
→ Factor: Technical Approach (Innovation subfactor)
Confidence: 0.85
```

**Extraction**:
```
Source: "AI/ML Anomaly Detection Requirement"
Target: "Section M.1.2: Innovation (30% of Technical Approach)"
Type: EVALUATED_BY
Confidence: 0.85
Reasoning: "Topic alignment: Innovation technology → Innovation subfactor"
```

---

## Pattern 3: Criticality-to-Weight Inference (Confidence: 0.70-0.75)

**Rule**: Mandatory requirements typically align with high-weight factors

### Criticality Mapping

| Requirement Criticality | Typical Factor Weight | Inference       | Confidence |
| ----------------------- | -------------------- | --------------- | ---------- |
| MANDATORY (SHALL)       | 30%+ weight          | High importance | 0.75       |
| RECOMMENDED (SHOULD)    | 15-30% weight        | Medium          | 0.70       |
| OPTIONAL (MAY)          | Variable             | Lower priority  | 0.65 (REJECT) |

**Example**:
```
Requirement: "Contractor SHALL provide 24/7 NOC support" (Criticality: MANDATORY)
Factor: "Management Approach" (Weight: 35%, high priority)

Inference: Mandatory requirements typically evaluated under high-weight factors
Confidence: 0.75
```

---

## Pattern 4: Section Proximity (Confidence: 0.65-0.75)

**Rule**: Requirements near evaluation factor are likely scored by that factor

### Examples

```
Section C (SOW) contains: "Requirement for predictive maintenance"
Section M.1 (Technical Approach) mentions: "Innovation in maintenance approach"
Proximity signal: Both discuss maintenance topic
Confidence: 0.70
```

---

## When to Create vs Reject

### ✅ CREATE

```
Source: "SHALL maintain 4-hour resolution time for Priority 1 incidents"
Target: "Section M.2: Management Approach (35% weight)"
Type: EVALUATED_BY
Confidence: 0.80
Reasoning: "Topic alignment: Operational requirement (help desk SLA) 
evaluated under management capability"
```

```
Source: "Proposed technical architecture using microservices"
Target: "Section M.1: Technical Approach (40% weight)"
Type: EVALUATED_BY
Confidence: 0.90
Reasoning: "Explicit technical solution scores under Technical Approach factor"
```

### ❌ REJECT (< 0.70)

```
Source: "Generic compliance requirement"
Target: "Unknown evaluation factor"
Confidence: 0.50 [TOO LOW]
Reason: "Cannot determine which factor will evaluate this requirement"
```

```
Source: "Optional capability (MAY provide)"
Target: "Any factor"
Confidence: 0.65 [TOO LOW - at threshold, best to reject]
Reason: "Optional items may not be formally evaluated"
```

---

## Output Checklist

✅ Source is a REQUIREMENT entity  
✅ Target is an EVALUATION_FACTOR entity  
✅ Type is exactly `EVALUATED_BY`  
✅ Confidence ≥ 0.70 (use patterns above)  
✅ Reasoning explains which pattern was used  
✅ Criticality level considered (MANDATORY → higher weight factors)  
✅ No duplicate relationships  
✅ Directional: Requirement → Factor (not reversed)

**Remember**: Better to miss a requirement-factor link than create a false one (false links create noise in analysis)
