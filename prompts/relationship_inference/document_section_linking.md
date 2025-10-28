# Document Section Linking: Content-Based Section Inference

**Purpose**: Link referenced documents to the sections where they appear  
**Focus**: REFERENCES relationships (Document → Referenced entity)  
**Confidence Target**: ≥0.75 for all relationships  
**Pattern**: Explicit citations and semantic matching  
**Last Updated**: October 28, 2025 (Proven Patterns)

---

## The Core Pattern: REFERENCES

```
DOCUMENT --REFERENCES--> DOCUMENT/STANDARD/SPECIFICATION
```

This maps when one document explicitly mentions or references another.

---

## Pattern 1: Explicit Citation (Confidence: 1.0)

**Rule**: If text says "See Document X" or "References MIL-STD-882", create REFERENCES relationship

### Examples

```
"The contractor shall comply with MIL-STD-882E as specified in Section J-02000000 Annex 7"
→ REFERENCES (Confidence 1.0)

"Section C.2 shall be implemented per IEEE 1028 (see Attachment J-05)"
→ REFERENCES (Confidence 1.0)

"Requirements defined in API 654 (Shell Inspection and Rating Code)"
→ REFERENCES (Confidence 1.0)
```

**Extraction**:
```
Source: "Section C"
Target: "MIL-STD-882E"
Type: REFERENCES
Confidence: 1.0
Reasoning: "Explicit citation: 'comply with MIL-STD-882E'"
```

---

## Pattern 2: Implicit Standard Reference (Confidence: 0.90)

**Rule**: Technical terminology signals standards without explicit naming

### Examples

```
"NIST SP 800-171 compliance" → Reference to NIST standards
"ISO 9001 certified" → Reference to ISO standards
"CMMI Level 3" → Reference to CMMI methodology
"IEEE 802.11 secure networks" → Reference to IEEE standards
```

**Extraction**:
```
Source: "Security Requirements (Section H)"
Target: "NIST SP 800-171"
Type: REFERENCES
Confidence: 0.90
Reasoning: "Reference to NIST standard: 'NIST 800-171 compliance required'"
```

---

## Pattern 3: Cross-Section References (Confidence: 0.95)

**Rule**: One section explicitly references another

### Examples

```
"See Section J for attachments" → Section I REFERENCES Section J
"As defined in Section B Statement of Work" → Section C REFERENCES Section B
"Per evaluation criteria in Section M" → Section L REFERENCES Section M
```

**Extraction**:
```
Source: "Section L (Submission Instructions)"
Target: "Section M (Evaluation Factors)"
Type: REFERENCES
Confidence: 0.95
Reasoning: "Explicit cross-reference: 'See Section M evaluation criteria'"
```

---

## Pattern 4: Industry/Regulatory Standards (Confidence: 0.85)

**Rule**: References to well-known standards/regulations

### Common Standards

| Standard          | Type              | Confidence |
| ----------------- | ----------------- | ---------- |
| FAR 15.209        | Regulation        | 1.0        |
| DFARS 224         | Regulation        | 1.0        |
| NIST SP 800-171   | Standard          | 0.95       |
| ISO 9001          | Certification     | 0.90       |
| IEEE 802.11       | Standard          | 0.90       |
| MIL-STD-882E      | Military standard | 0.95       |
| IEEE 1028         | Software standard | 0.90       |
| CMMI              | Maturity model    | 0.90       |
| SOC 2 Type II     | Compliance        | 0.90       |
| ITIL v4           | Framework         | 0.85       |

**Extraction**:
```
Source: "Quality Assurance Plan"
Target: "ISO 9001"
Type: REFERENCES
Confidence: 0.90
Reasoning: "Quality standard referenced in proposal context"
```

---

## When to Create vs Reject

### ✅ CREATE

```
Source: "Performance Work Statement"
Target: "IEEE 1028 Software Reviews and Audits"
Type: REFERENCES
Confidence: 0.95
Reasoning: "Explicit citation in PWS: 'Code reviews per IEEE 1028'"
```

```
Source: "Section C (SOW)"
Target: "MIL-STD-882E"
Type: REFERENCES
Confidence: 0.90
Reasoning: "Risk management approach per MIL-STD-882E standard"
```

### ❌ REJECT (< 0.70)

```
Source: "Security"
Target: "Best Practices"
Confidence: 0.40 [TOO LOW]
Reason: "Generic terms, no specific standard referenced"
```

---

## Output Checklist

✅ Source is a DOCUMENT entity  
✅ Target is a DOCUMENT/STANDARD/SPECIFICATION entity  
✅ Type is `REFERENCES`  
✅ Confidence ≥ 0.70  
✅ Reasoning includes the explicit citation or semantic inference  
✅ Target entity exists in knowledge graph  
✅ No duplicate relationships
