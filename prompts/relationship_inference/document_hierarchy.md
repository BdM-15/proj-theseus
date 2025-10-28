# Document Hierarchy: Parent-Child Relationships

**Purpose**: Map hierarchical structure within documents (subsections, numbered items)  
**Focus**: CHILD_OF relationships (subsection → parent document)  
**Confidence Target**: ≥0.85 for all relationships  
**Pattern**: Prefix numbering and structural delimiters  
**Last Updated**: October 28, 2025 (Proven Patterns)

---

## The Core Pattern: CHILD_OF for Hierarchies

```
DOCUMENT_SUBSECTION --CHILD_OF--> PARENT_DOCUMENT
```

This maps internal document structure without creating false relationships.

---

## Pattern 1: Prefix + Delimiter Matching (Confidence: 0.95)

**Rule**: Nested numbers indicate parent-child structure

### Examples

```
J-02000000 → Parent (base document)
├─ J-02000000-A → CHILD_OF J-02000000
├─ J-02000000-10 → CHILD_OF J-02000000
├─ J-02000000-Sec-2.3 → CHILD_OF J-02000000
└─ J-02000000-Sec-3.4.2 → CHILD_OF J-02000000 AND CHILD_OF J-02000000-Sec-3

Section C → Parent (base section)
├─ Section C.1 → CHILD_OF Section C
├─ Section C.2 → CHILD_OF Section C
├─ Section C.2.1 → CHILD_OF Section C.2
└─ Section C.2.1.a → CHILD_OF Section C.2.1

FAR 52.204-21 → Parent (base clause)
├─ FAR 52.204-21(a) → CHILD_OF FAR 52.204-21
├─ FAR 52.204-21(b) → CHILD_OF FAR 52.204-21
└─ FAR 52.204-21(b)(1) → CHILD_OF FAR 52.204-21(b)
```

**Extraction**:
```
Source: "Section C.2.1"
Target: "Section C.2"
Type: CHILD_OF
Confidence: 0.95
Reasoning: "Decimal notation (C.2.1 → C.2) indicates subsection hierarchy"
```

---

## Pattern 2: Explicit Subsection Labeling (Confidence: 0.95)

**Rule**: Document explicitly labels subsections

### Examples

```
Section J: List of Attachments

J-02000000 Performance Work Statement

Section 1: Introduction
Section 2: Scope of Work
Section 2.1: Technical Requirements
Section 2.2: Staffing Plan
```

**Extraction**:
```
Source: "Section 2.1: Technical Requirements"
Target: "Section 2: Scope of Work"
Type: CHILD_OF
Confidence: 0.95
Reasoning: "Explicit subsection numbering (2.1 → 2)"
```

---

## Pattern 3: Named Subsections (Confidence: 0.90)

**Rule**: Section references indicate hierarchy even without numbering

### Examples

```
"J-02000000 Performance Work Statement

Paragraph 2.3 Work Schedule
Paragraph 2.3.1 Phase 1 Deliverables"
```

**Extraction**:
```
Source: "Paragraph 2.3.1 Phase 1 Deliverables"
Target: "Paragraph 2.3 Work Schedule"
Type: CHILD_OF
Confidence: 0.90
Reasoning: "Explicit paragraph cross-reference indicates hierarchy"
```

---

## Special Cases: When to Create vs Reject

### ✅ CREATE

```
Source: "FAR 52.204-21(b)(1)(i)"
Target: "FAR 52.204-21(b)(1)"
Type: CHILD_OF
Confidence: 0.95
Reasoning: "Clause paragraph hierarchy (Roman numeral indicates subdivision)"
```

### ❌ REJECT (< 0.70)

```
Source: "Technical Design"
Target: "Architecture Document"
Confidence: 0.50 [TOO LOW]
Reason: "Generic terms, no clear numbering pattern"
```

---

## Output Checklist

✅ Source is a subsection/sub-document  
✅ Target is parent document/section  
✅ Type is `CHILD_OF`  
✅ Confidence ≥ 0.70 (use patterns above)  
✅ Numbering/naming scheme clearly supports relationship  
✅ No orphaned subsections (all subsections should have parent)  
✅ No circular relationships (A CHILD_OF B, B CHILD_OF A)
