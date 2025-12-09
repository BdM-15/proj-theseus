# Attachment Section Linking Rules

## ⚠️ CRITICAL: Entity ID Usage

**MANDATORY**: When generating relationships, you MUST use the EXACT `id` values from the entity JSON input.

- ❌ **NEVER** invent IDs (e.g., "annex_j_02000000", "section_j")
- ✅ **ALWAYS** copy the `id` field value exactly as provided in the input entities
- ✅ Entity IDs look like: `"4:f7g8h9i0j1k2:123"` or similar alphanumeric strings

---

**Purpose**: Link top-level attachments/annexes to their parent RFP sections  
**Why This Matters**: Enables section-based navigation (find all Section J attachments)  
**Method**: LLM-powered semantic inference (agency-agnostic)

---

## Core Relationship Pattern

```
ANNEX/DOCUMENT --ATTACHMENT_OF--> SECTION
```

**Meaning**: This attachment/document is listed under this parent section

**Example**:

```
ANNEX "J-02000000 Performance Work Statement"
  --ATTACHMENT_OF-->
SECTION "Section J: List of Attachments"
```

**Note**: This is DIFFERENT from document hierarchy (CHILD_OF)

- ATTACHMENT_OF: Top-level annex → RFP section (J-02000000 → Section J)
- CHILD_OF: Sub-annex → Parent annex (J-02000000-10 → J-02000000)

---

## Three Inference Patterns

### Pattern 1: Naming Convention (Confidence: 1.0)

**Signal**: Prefix matches section letter

**Patterns**:

```
J-######        → Section J (List of Attachments)
A-######        → Section A (Solicitation/Contract Form)
H-######        → Section H (Special Requirements)
Attachment #    → Section J (default)
Annex ##        → Section J (default)
Exhibit X       → Section J (default for DoD) OR Section B (GSA pricing)
```

**Examples**:

```
"J-02000000 PWS" → prefix "J-" → Section J (confidence: 1.0)
"Attachment 5" → default Section J (confidence: 1.0)
"A-00000005 SF 1449" → prefix "A-" → Section A (confidence: 1.0)
"H-00000007 Key Personnel" → prefix "H-" → Section H (confidence: 1.0)
```

**Extraction**:

```json
{
  "source_id": "annex_j_02000000",
  "target_id": "section_j",
  "relationship_type": "ATTACHMENT_OF",
  "confidence": 1.0,
  "reasoning": "Naming convention: J-prefix → Section J"
}
```

---

### Pattern 2: Explicit Citation (Confidence: 0.95)

**Signal**: Attachment listed under section heading in document

**Example**:

```
Section J: List of Attachments

The following documents are attached:
1. J-02000000 Performance Work Statement (PWS)
2. J-03000000 Quality Assurance Surveillance Plan (QASP)
3. J-04000000 Contract Data Requirements List (CDRL)
```

**Extraction**:

```json
[
  {
    "source_id": "annex_j_02000000",
    "target_id": "section_j",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 0.95,
    "reasoning": "Explicit citation: Listed under 'Section J: List of Attachments'"
  },
  {
    "source_id": "annex_j_03000000",
    "target_id": "section_j",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 0.95,
    "reasoning": "Explicit citation: Listed under 'Section J: List of Attachments'"
  }
]
```

---

### Pattern 3: Content Alignment (Confidence: 0.70)

**Signal**: Attachment content matches section purpose

**Example**:

```
Exhibit A: Pricing Schedule
Section B: Supplies or Services and Prices/Costs
```

**Logic**: Pricing-related attachment → Section B (pricing section)

**Extraction**:

```json
{
  "source_id": "annex_exhibit_a_pricing",
  "target_id": "section_b",
  "relationship_type": "ATTACHMENT_OF",
  "confidence": 0.7,
  "reasoning": "Content alignment: Pricing schedule → Section B (Supplies/Prices)"
}
```

**Common Content Alignments**:

- Pricing/Cost → Section B
- PWS/SOW/SOO → Section C (or Section J if attached)
- Key Personnel → Section H
- Quality Plans → Section J
- Security Plans → Section H or J
- Deliverables → Section J

---

## Agency-Specific Patterns

### DoD (Navy, Air Force, Army, Marines)

**Standard Pattern**: `J-########` for all attachments

```
J-02000000 PWS
J-03000000 QASP
J-04000000 CDRL
J-05000000 DD Form 254 (Security Requirements)
```

**All map to**: Section J

---

### GSA (General Services Administration)

**Exhibits for pricing**, **Attachments for technical**

```
Exhibit A (Pricing Schedule) → Section B (Supplies/Prices)
Exhibit B (Price/Cost Schedule) → Section B
Attachment 1 (PWS) → Section J
Attachment 2 (QCP) → Section J
```

**Detection Rule**: "Exhibit" + pricing keywords → Section B, otherwise Section J

---

### NASA

**Annexes with Roman numerals**

```
Annex I (SOW) → Section J
Annex II (Data Requirements) → Section J
Annex XVII (Security) → Section J
```

**All map to**: Section J (NASA uses Section J for attachments)

---

### DoE (Department of Energy)

**Mixed naming**: Attachments + Exhibits

```
Attachment A (SOW) → Section J
Exhibit 1 (Pricing) → Section B
Attachment B (QA Plan) → Section J
```

**Detection Rule**: "Exhibit" + pricing → Section B, "Attachment" → Section J

---

### State Department

**Annexes with letters**

```
Annex A (PWS) → Section J
Annex B (Deliverables) → Section J
Annex C (Travel Requirements) → Section J
```

**All map to**: Section J

---

## LLM Inference Prompt Template

```
You are analyzing RFP attachments to link them to parent sections.

ATTACHMENTS:
{json_list_of_annexes_and_documents}

SECTIONS:
{json_list_of_sections}

TASK:
For each attachment, determine which section it belongs to based on:

1. NAMING CONVENTION (Confidence 1.0):
   - J-######## → Section J (List of Attachments)
   - A-######## → Section A (Solicitation Form)
   - H-######## → Section H (Special Requirements)
   - Attachment # → Section J (default)
   - Annex ## → Section J (default)

2. EXPLICIT CITATION (Confidence 0.95):
   - Attachment listed under section heading
   - "Section J includes: J-02000000 PWS..."

3. CONTENT ALIGNMENT (Confidence 0.70):
   - Pricing/Cost documents → Section B
   - PWS/SOW/SOO → Section C or J
   - Key Personnel → Section H
   - Quality Plans → Section J
   - Security Plans → Section H or J

AGENCY PATTERNS:
- DoD: J-######## → Section J
- GSA: Exhibit X (pricing) → Section B, Attachment → Section J
- NASA: Annex ## → Section J
- DoE: Exhibit (pricing) → Section B, Attachment → Section J
- State: Annex X → Section J

RULES:
- Only link TOP-LEVEL attachments (not sub-attachments)
- Sub-attachments use CHILD_OF relationship (see document_hierarchy.md)
- Confidence threshold: ≥0.70

OUTPUT FORMAT:
[
  {
    "source_id": "attachment_id",
    "target_id": "section_id",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 0.70-1.0,
    "reasoning": "Pattern name and specific match details"
  }
]
```

---

## Special Cases

### Case 1: Sub-Attachments (NOT ATTACHMENT_OF)

**Problem**: J-02000000-10 is a sub-attachment, not top-level

**Rule**: Only TOP-LEVEL attachments get ATTACHMENT_OF relationship

**Example**:

```
CORRECT:
J-02000000 --ATTACHMENT_OF--> Section J ✅
J-02000000-10 --CHILD_OF--> J-02000000 ✅

WRONG:
J-02000000-10 --ATTACHMENT_OF--> Section J ❌ (use CHILD_OF instead)
```

**Detection**: If attachment has hierarchical suffix (-10, -A, .1), it's a sub-attachment

---

### Case 2: Work Statement Location (SOW/PWS Flexibility)

**Reality**: Work statements (SOW/PWS/SOO) can appear in multiple locations:

- **Section C** (inline): Traditional location for Statement of Work
- **Section J attachment**: Separate PWS document (e.g., "J-02000000 PWS")
- **Section H**: Special requirements that define work scope
- **Technical Annexes**: Detailed task descriptions (various naming)

**Detection Logic**:

```
IF document has J-prefix AND contains work statement → Section J (attached PWS)
IF document labeled "Section C" → Section C (inline SOW)
IF document in Section H → Section H (special requirements)
IF technical annex with task descriptions → Section J or parent section
```

**Examples**:

```
"J-02000000 Performance Work Statement" → Section J ✅
"Section C: Statement of Work" → Section C ✅
"Attachment 0001 PWS" → Section J ✅
"Section H Special Requirements" → Section H ✅
```

**Key Principle**: Extract work statements as STATEMENT_OF_WORK type regardless of physical location

---

### Case 3: GSA Exhibits (Pricing vs. Technical)

**Problem**: GSA uses "Exhibit" for both pricing and technical

**Detection Rule**:

```
IF Exhibit name contains "Pricing", "Cost", "Price Schedule", "Financial"
  → Section B (Supplies/Prices)
ELSE
  → Section J (List of Attachments)
```

**Examples**:

```
"Exhibit A - Pricing Schedule" → Section B ✅
"Exhibit B - Technical Approach" → Section J ✅
```

---

### Case 4: Referenced But Not Attached

**Problem**: Document cited but not physically attached to RFP

**Example**:

```
"Comply with MIL-STD-882E" (cited in Section C, not attached)
```

**Rule**: Do NOT create ATTACHMENT_OF relationship

**Alternative**: Create REFERENCES relationship instead

```
Section C --REFERENCES--> MIL-STD-882E (not ATTACHMENT_OF)
```

---

## Integration with Document Hierarchy

### Two Complementary Relationships

**ATTACHMENT_OF** (this prompt):

```
J-02000000 --ATTACHMENT_OF--> Section J
```

**CHILD_OF** (document_hierarchy.md):

```
J-02000000-10 --CHILD_OF--> J-02000000
J-02000000-20 --CHILD_OF--> J-02000000
```

### Combined Result

```
Section J
  ├── J-02000000 (ATTACHMENT_OF)
  │   ├── J-02000000-10 (CHILD_OF)
  │   └── J-02000000-20 (CHILD_OF)
  ├── J-03000000 (ATTACHMENT_OF)
  │   └── J-03000000-10 (CHILD_OF)
  └── J-04000000 (ATTACHMENT_OF)
```

**Navigation Queries**:

- "Show all Section J attachments" → Follow ATTACHMENT_OF relationships
- "Show sub-attachments of J-02000000" → Follow CHILD_OF relationships

---

## Quality Validation

### Validation Rules

1. ✅ **Top-level only**: No sub-attachments with ATTACHMENT_OF (use CHILD_OF instead)
2. ✅ **Confidence threshold**: ≥0.70
3. ✅ **Single section**: Each attachment links to exactly ONE section
4. ✅ **Section exists**: Target section must exist in graph

### Expected Relationship Counts (Baseline)

**Navy MBOS (71-page RFP)**:

- Annexes: ~88 entities (ANNEX type)
- Top-level annexes: ~15 (J-02000000, J-03000000, etc.)
- Expected ATTACHMENT_OF relationships: ~15 (one per top-level annex)

**Note**: Sub-annexes (~73) use CHILD_OF, NOT ATTACHMENT_OF

---

## Examples from Real RFPs

### Example 1: Navy MBOS - Section J Attachments

**Entities**:

```
SECTION_J: "Section J: List of Attachments"
ANNEX_001: J-02000000 "Performance Work Statement (PWS)"
ANNEX_005: J-03000000 "Quality Assurance Surveillance Plan"
ANNEX_010: J-04000000 "Contract Data Requirements List (CDRL)"
```

**Extracted Relationships** (3):

```json
[
  {
    "source_id": "annex_001",
    "target_id": "section_j",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 1.0,
    "reasoning": "Naming convention: J-prefix → Section J"
  },
  {
    "source_id": "annex_005",
    "target_id": "section_j",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 1.0,
    "reasoning": "Naming convention: J-prefix → Section J"
  },
  {
    "source_id": "annex_010",
    "target_id": "section_j",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 1.0,
    "reasoning": "Naming convention: J-prefix → Section J"
  }
]
```

---

### Example 2: GSA Schedule - Exhibits

**Entities**:

```
SECTION_B: "Section B: Supplies or Services and Prices/Costs"
SECTION_J: "Section J: List of Attachments"
ANNEX_020: "Exhibit A - Pricing Schedule"
ANNEX_021: "Exhibit B - Technical Capabilities"
```

**Extracted Relationships** (2):

```json
[
  {
    "source_id": "annex_020",
    "target_id": "section_b",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 0.95,
    "reasoning": "Content alignment: Pricing Schedule → Section B (GSA pattern)"
  },
  {
    "source_id": "annex_021",
    "target_id": "section_j",
    "relationship_type": "ATTACHMENT_OF",
    "confidence": 0.7,
    "reasoning": "Content alignment: Technical document → Section J (GSA default)"
  }
]
```

---

## Error Patterns to Avoid

### ❌ Error 1: Sub-Attachments Using ATTACHMENT_OF

```
WRONG:
J-02000000-10 --ATTACHMENT_OF--> Section J
```

**Correct**: Sub-attachments use CHILD_OF

```
J-02000000-10 --CHILD_OF--> J-02000000
J-02000000 --ATTACHMENT_OF--> Section J
```

---

### ❌ Error 2: Referenced Documents as Attachments

```
WRONG:
MIL-STD-882E --ATTACHMENT_OF--> Section J (not attached, just cited)
```

**Correct**: Use REFERENCES for citations

```
Section C --REFERENCES--> MIL-STD-882E
```

---

### ❌ Error 3: Multiple Section Linkages

```
WRONG:
J-02000000 --ATTACHMENT_OF--> Section J
J-02000000 --ATTACHMENT_OF--> Section C (duplicate!)
```

**Correct**: One attachment, one section

```
J-02000000 --ATTACHMENT_OF--> Section J ✅
```

---

## Success Criteria

A successful attachment section linking run should:

1. ✅ **100% top-level coverage**: Every top-level annex linked to section
2. ✅ **No sub-attachment errors**: Sub-annexes use CHILD_OF (not ATTACHMENT_OF)
3. ✅ **Agency patterns respected**: DoD → J, GSA exhibits → B or J, NASA → J
4. ✅ **Single section rule**: Each attachment links to exactly ONE section

---

**Last Updated**: January 2025 (Branch 004 - Phase 1 Refactor)  
**Version**: 2.0 (Split from document_hierarchy.md for separation of concerns)  
**Relationship**: Complements document_hierarchy.md (ATTACHMENT_OF for sections, CHILD_OF for hierarchy)  
**Impact**: Clear separation between section linkage and document hierarchy
