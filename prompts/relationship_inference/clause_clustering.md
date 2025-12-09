# Clause Clustering Rules

## ⚠️ CRITICAL: Entity ID Usage

**MANDATORY**: When generating relationships, you MUST use the EXACT `id` values from the entity JSON input.

- ❌ **NEVER** invent IDs (e.g., "clause_far_52_212_4", "section_i")
- ✅ **ALWAYS** copy the `id` field value exactly as provided in the input entities
- ✅ Entity IDs look like: `"4:f7g8h9i0j1k2:123"` or similar alphanumeric strings

---

**Purpose**: Group scattered FAR/DFARS/AFFARS clauses under parent sections  
**Why This Matters**: Clauses may be fragmented across document; need logical grouping  
**Method**: LLM-powered semantic inference (26+ agency supplements)

---

## Core Relationship Pattern

```
CLAUSE --CHILD_OF--> SECTION
```

**Meaning**: This contract clause belongs to this parent section

**Example**:

```
CLAUSE "FAR 52.212-4 Contract Terms and Conditions"
  --CHILD_OF-->
SECTION "Section I: Contract Clauses"
```

---

## Three Inference Patterns

### Pattern 1: Numbering/Prefix (Confidence: 0.90)

**Signal**: Clause number belongs to section numbering scheme

**Example**:

```
FAR 52.212-4 → FAR Section 52 series → Section I (Contract Clauses)
DFARS 252.204-7012 → DFARS Section 252 series → Section I
```

**Extraction**:

```json
{
  "source_id": "clause_far_52_212_4",
  "target_id": "section_i",
  "relationship_type": "CHILD_OF",
  "confidence": 0.9,
  "reasoning": "Numbering pattern: FAR 52.### series typically in Section I"
}
```

### Pattern 2: Attribution/Citation (Confidence: 0.95)

**Signal**: Clause listed under section heading

**Example**:

```
Section I: Contract Clauses

52.212-4 Contract Terms and Conditions—Commercial Products
52.212-5 Required Statutes
252.204-7012 Safeguarding Covered Defense Information
```

**Extraction**:

```json
{
  "source_id": "clause_far_52_212_4",
  "target_id": "section_i",
  "relationship_type": "CHILD_OF",
  "confidence": 0.95,
  "reasoning": "Explicit attribution: Listed under 'Section I: Contract Clauses' heading"
}
```

### Pattern 3: Clustering (Confidence: 0.70)

**Signal**: Similar clauses grouped together (even if scattered)

**Example**:

```
FAR 52.212-1 (page 15)
FAR 52.212-4 (page 18)
FAR 52.212-5 (page 22)
```

All are FAR 52.2## series → Group together → Section I

**Extraction**:

```json
[
  { "source": "clause_far_52_212_1", "target": "section_i", "confidence": 0.7 },
  { "source": "clause_far_52_212_4", "target": "section_i", "confidence": 0.7 },
  { "source": "clause_far_52_212_5", "target": "section_i", "confidence": 0.7 }
]
```

---

## 26+ Agency Supplement Patterns

LLM understands ALL federal agency supplements semantically:

### Primary Supplements

- **FAR**: Federal Acquisition Regulation (52.###-##)
- **DFARS**: Defense FAR Supplement (252.###-####)
- **AFFARS**: Air Force FAR Supplement (5352.###-##)
- **NMCARS**: Navy/Marine Corps (5252.###-####)

### Additional Supplements (22 more)

- HSAR (Homeland Security)
- DOSAR (State Department)
- GSAM (General Services Administration)
- VAAR (Department of Veterans Affairs)
- DEAR (Department of Energy)
- NFS (NASA FAR Supplement)
- AIDAR (USAID)
- CAR (Commerce Acquisition Regulation)
- DIAR (Department of Interior)
- DOLAR (Department of Labor)
- EDAR (Department of Education)
- EPAAR (EPA)
- FEHBAR (Office of Personnel Management)
- HHSAR (Health and Human Services)
- HUDAR (HUD)
- IAAR (Broadcasting Board of Governors)
- JAR (Department of Justice)
- LIFAR (Federal Reserve Board)
- NRCAR (Nuclear Regulatory Commission)
- SOFARS (Special Operations Command)
- TAR (Department of Transportation)
- AGAR (Department of Agriculture)

**Key Insight**: LLM recognizes patterns across ALL supplements, not just hardcoded DoD

---

## LLM Inference Prompt Template

```
You are analyzing contract clauses to determine their parent section relationships.

CLAUSES:
{json_list_of_clauses}

SECTIONS:
{json_list_of_sections}

TASK:
For each clause, determine its parent section based on:

1. NUMBERING PATTERN (Confidence 0.90):
   - FAR 52.### → Section I (Contract Clauses)
   - FAR 52.2## → Section K (Representations/Certifications)
   - DFARS 252.### → Section I
   - Agency supplement patterns

2. ATTRIBUTION (Confidence 0.95):
   - Clause listed under section heading
   - "Section I: Contract Clauses" contains...

3. CLUSTERING (Confidence 0.70):
   - Group similar clause series together
   - All FAR 52.212-# clauses → Section I
   - Even if scattered across document

CLAUSE TYPES:
- Contract Terms: FAR 52.### → Section I
- Representations: FAR 52.2## → Section K
- Certifications: FAR 52.2## → Section K
- Special Requirements: May be Section H

OUTPUT FORMAT:
[
  {
    "source_id": "clause_id",
    "target_id": "section_id",
    "relationship_type": "CHILD_OF",
    "confidence": 0.70-0.95,
    "reasoning": "Brief explanation"
  }
]
```

---

## Special Cases

### Case 1: Representations vs. Contract Clauses

**Rule**: FAR 52.2##-## series are typically REPRESENTATIONS (Section K), not contract clauses

**Example**:

```
FAR 52.212-3 Offeror Representations and Certifications → Section K
FAR 52.212-4 Contract Terms and Conditions → Section I
```

### Case 2: Scattered Clauses (Fragmentation Fix)

**Problem**: Clauses spread across multiple pages

**Example**:

```
Page 15: FAR 52.212-1
Page 18: FAR 52.212-4
Page 22: FAR 52.212-5
Page 35: DFARS 252.204-7012
```

**Solution**: Group all under logical parent (Section I) despite physical separation

### Case 3: Special Requirements Clauses

**Pattern**: Some clauses are SPECIAL_REQUIREMENTS (Section H), not standard clauses

**Example**:

```
H-1: Key Personnel Requirements
H-2: Security Clearances
H-3: Facility Access Badges
```

**Extraction**:

```json
{
  "source_id": "clause_h1_key_personnel",
  "target_id": "section_h",
  "relationship_type": "CHILD_OF",
  "confidence": 0.95,
  "reasoning": "Special requirement clause under Section H heading"
}
```

---

## Quality Validation

### Validation Rules

1. ✅ **Every clause has parent**: No orphaned clauses
2. ✅ **Confidence threshold**: ≥0.70
3. ✅ **Correct section attribution**: FAR 52.2## → Section K (not Section I)
4. ✅ **Clustering completeness**: All similar clauses grouped

### Expected Relationship Counts (Baseline)

**Navy MBOS (71-page RFP)**:

- Clauses: ~120 entities
- Expected CHILD_OF relationships: ~120 (100% coverage)
- Section I (Contract Clauses): ~80 clauses
- Section K (Representations): ~30 clauses
- Section H (Special Requirements): ~10 clauses

---

## Examples from Real RFPs

### Example 1: Navy MBOS (Section I)

```
Section I: Contract Clauses

52.212-4 Contract Terms and Conditions—Commercial Products
and Commercial Services (JAN 2024)

52.212-5 Contract Terms and Conditions Required To Implement
Statutes or Executive Orders (JAN 2024)

252.204-7012 Safeguarding Covered Defense Information and
Cyber Incident Reporting (DEC 2019)
```

**Extracted Relationships** (3):

```json
[
  {
    "source_id": "clause_far_52_212_4",
    "target_id": "section_i",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Listed under 'Section I: Contract Clauses'"
  },
  {
    "source_id": "clause_far_52_212_5",
    "target_id": "section_i",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Listed under 'Section I: Contract Clauses'"
  },
  {
    "source_id": "clause_dfars_252_204_7012",
    "target_id": "section_i",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Listed under 'Section I: Contract Clauses'"
  }
]
```

### Example 2: Section K (Representations)

```
Section K: Representations, Certifications, and Other Statements

52.212-3 Offeror Representations and Certifications—Commercial
Products and Commercial Services (JAN 2024)

52.219-1 Small Business Program Representations (NOV 2023)
```

**Extracted Relationships** (2):

```json
[
  {
    "source_id": "clause_far_52_212_3",
    "target_id": "section_k",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Listed under 'Section K: Representations, Certifications'"
  },
  {
    "source_id": "clause_far_52_219_1",
    "target_id": "section_k",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Listed under 'Section K: Representations, Certifications'"
  }
]
```

---

## Error Patterns to Avoid

### ❌ Error 1: Misclassifying Representations as Contract Clauses

```
WRONG:
FAR 52.212-3 Representations → Section I (Contract Clauses)
```

**Correct**: FAR 52.212-3 → Section K (Representations)

### ❌ Error 2: Creating Multiple Parents

```
WRONG:
Clause_X → Section I
Clause_X → Section K
```

**Correct**: One clause, one primary parent

### ❌ Error 3: Ignoring Fragmentation

```
WRONG:
FAR 52.212-1 (page 15) → Section I
FAR 52.212-4 (page 18) → NOT LINKED
```

**Correct**: Group all similar clauses even if scattered

---

## Success Criteria

A successful clause clustering run should:

1. ✅ **100% coverage**: Every clause linked to parent section
2. ✅ **Correct attribution**: Representations → Section K, Contract Clauses → Section I
3. ✅ **Fragmentation handled**: Scattered clauses grouped together
4. ✅ **Agency-agnostic**: Works for all 26+ supplements

---

**Last Updated**: January 2025 (Branch 004)  
**Version**: 2.0 (LLM semantic inference, 26+ agency supplements)  
**Improvement**: Handles fragmentation + all agency supplements (not just DoD)
