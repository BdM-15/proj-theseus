# Document Hierarchy Rules# Annex Linking Rules



**Purpose**: Build hierarchical relationships between parent and child documents  **Purpose**: Link numbered attachments (J-####, Annex ##) to parent sections  

**Why This Matters**: Prevents orphaned sub-documents (J-02000000-10 isolated from J-02000000)  **Why This Matters**: 100% annex coverage (vs 84.6% with regex patterns)  

**Method**: LLM-powered pattern detection across DOCUMENT, CLAUSE, and ANNEX entity types**Method**: LLM-powered semantic inference (agency-agnostic)



------



## Core Relationship Pattern## Core Relationship Pattern



``````

DOCUMENT/CLAUSE/ANNEX --CHILD_OF--> DOCUMENT/CLAUSE/ANNEXANNEX --ATTACHMENT_OF--> SECTION

``````



**Meaning**: This document/standard/clause is a subsection or part of a parent document**Meaning**: This annex/attachment belongs to this parent section



**Examples**:**Example**:

``````

J-02000000-10 (Technical Requirements) --CHILD_OF--> J-02000000 (PWS)ANNEX "J-0200000-18 Performance Work Statement"

NIST 800-171 3.1.1 (Access Control) --CHILD_OF--> NIST 800-171 Rev 2  --ATTACHMENT_OF-->

DFARS 252.204-7012(b)(2) --CHILD_OF--> DFARS 252.204-7012SECTION "Section J: List of Attachments"

MIL-STD-882E Task 101 --CHILD_OF--> MIL-STD-882E```

```

---

---

## Three Inference Patterns

## Document Types Covered

### Pattern 1: Naming Convention (Confidence: 1.0)

### Type 1: Attached Documents (ANNEX entities)

**Physically included in RFP package****Signal**: Prefix matches section letter

- Navy: J-02000000, J-02000000-10, J-02000000-20

- GSA: Exhibit A, Exhibit A.1, Exhibit A.2**Patterns**:

- NASA: Annex XVII, Annex XVII-A, Annex XVII-B- `J-######` → Section J

- `A-######` → Section A

### Type 2: Referenced Standards (DOCUMENT entities)- `H-######` → Section H

**External standards cited but not attached**- `Attachment #` → Section J (default)

- Technical: MIL-STD-882E, MIL-STD-882E Task 101- `Annex ##` → Section J (default)

- Cybersecurity: NIST 800-171 Rev 2, NIST 800-171 3.1.1

- Quality: ISO 9001:2015, ISO 9001:2015 8.2.3**Examples**:

- Other: CMMI Level 3, IEEE 802.11ac```

"J-0200000-18" → prefix "J-" → Section J (confidence: 1.0)

### Type 3: Referenced Clauses (CLAUSE entities)"Attachment 5" → default Section J (confidence: 1.0)

**FAR/DFARS clauses with paragraph citations**"A-1234567" → prefix "A-" → Section A (confidence: 1.0)

- Parent: DFARS 252.204-7012```

- Child: DFARS 252.204-7012(b)(2)

- Grandchild: DFARS 252.204-7012(b)(2)(ii)(A)**Extraction**:

```json

---{

  "source_id": "annex_j0200000_18",

## Four Hierarchical Patterns  "target_id": "section_j",

  "relationship_type": "ATTACHMENT_OF",

### Pattern 1: Prefix + Delimiter (Navy, DoD, DoE)  "confidence": 1.0,

  "reasoning": "Naming convention: 'J-' prefix matches Section J"

**Signal**: Shared prefix with delimiter-separated hierarchical suffix}

```

**Examples**:

```### Pattern 2: Explicit Citation (Confidence: 0.95)

J-02000000          (parent: base pattern)

J-02000000-10       (child: adds -10)**Signal**: Document explicitly lists attachment under section

J-02000000-20       (child: adds -20)

J-02000000-10-A     (grandchild: adds -A to -10)**Example**:

```

H-1                 (parent: Section H requirement)Section J: List of Attachments

H-1.1               (child: adds .1)

H-1.2               (child: adds .2)The following documents are incorporated by reference:



PWS-001             (parent: performance requirement)J-0200000-18: Performance Work Statement (PWS)

PWS-001-A           (child: adds -A)J-0300000-12: Equipment List and Specifications

``````



**Detection Logic**:**Extraction**:

- Extract prefix (everything before last delimiter)```json

- Check if prefix matches another entity's full ID{

- If match: Create CHILD_OF relationship  "source_id": "annex_j0200000_18",

  "target_id": "section_j",

**Confidence**: 0.95 (unambiguous pattern)  "relationship_type": "ATTACHMENT_OF",

  "confidence": 0.95,

---  "reasoning": "Explicit citation: Listed under 'Section J: List of Attachments'"

}

### Pattern 2: Standard + Subsection (Technical Specs)```



**Signal**: Standard name followed by section/task/control number### Pattern 3: Content Alignment (Confidence: 0.70)



**Examples**:**Signal**: Annex content matches section topic

```

MIL-STD-882E                    (parent: standard)**Example**:

MIL-STD-882E Task 101           (child: task reference)```

MIL-STD-882E Appendix A         (child: appendix)Section C: Performance Work Statement

See Attachment X-1 for detailed task descriptions.

NIST 800-171 Rev 2              (parent: standard)

NIST 800-171 3.1.1              (child: control 3.1.1)Attachment X-1: [Contains task hierarchy and deliverables]

NIST 800-171 3.5.2              (child: control 3.5.2)```



ISO 9001:2015                   (parent: standard)**Extraction**:

ISO 9001:2015 8.2.3             (child: section 8.2.3)```json

{

CMMI-DEV v2.0                   (parent: framework)  "source_id": "annex_attachment_x1",

CMMI-DEV v2.0 PA 1.1            (child: practice area)  "target_id": "section_c",

```  "relationship_type": "ATTACHMENT_OF",

  "confidence": 0.70,

**Detection Logic**:  "reasoning": "Content alignment: Section C references this attachment for PWS details"

- Extract base standard name (before "Task", section numbers, "Appendix")}

- Check if base name matches another entity```

- If match: Create CHILD_OF relationship

---

**Confidence**: 0.90 (common pattern, slight ambiguity with versioning)

## LLM Inference Prompt Template

---

```

### Pattern 3: Clause + Paragraph (FAR/DFARS)You are analyzing annexes/attachments and sections to determine parent-child relationships.



**Signal**: Clause number followed by paragraph notation (a), (b)(1), etc.ANNEXES/ATTACHMENTS:

{json_list_of_annexes}

**Examples**:

```SECTIONS:

FAR 52.212-4                    (parent: clause){json_list_of_sections}

FAR 52.212-4(a)                 (child: paragraph a)

FAR 52.212-4(a)(1)              (child: subparagraph a.1)TASK:

For each annex, determine its parent section based on:

DFARS 252.204-7012              (parent: clause)

DFARS 252.204-7012(b)           (child: paragraph b)1. NAMING CONVENTION (Confidence 1.0):

DFARS 252.204-7012(b)(2)        (child: subparagraph b.2)   - Prefix patterns: "J-######" → Section J

DFARS 252.204-7012(b)(2)(ii)    (child: sub-subparagraph b.2.ii)   - Standard patterns: "Attachment #" → Section J

DFARS 252.204-7012(b)(2)(ii)(A) (grandchild: letter A)   - Letter prefix: "X-######" → Section X

```

2. EXPLICIT CITATION (Confidence 0.95):

**Detection Logic**:   - Listed under section heading

- Extract base clause number (before parentheses)   - "The following documents are incorporated..."

- Check if base clause matches another entity

- If match: Create CHILD_OF relationship3. CONTENT ALIGNMENT (Confidence 0.70):

   - Referenced in section text

**Confidence**: 0.95 (unambiguous pattern)   - Annex content topic matches section topic



---SPECIAL RULE: 

Works for ANY naming convention - not just Navy patterns!

### Pattern 4: Decimal Notation (GSA, Commercial Specs)- DoD: "J-0200000-18"

- GSA: "Exhibit A", "Appendix 1"

**Signal**: Decimal point-separated hierarchical numbering- NASA: "Annex XVII"

- Custom: "Attachment PWS-001"

**Examples**:

```OUTPUT FORMAT:

Exhibit A                       (parent: attachment)Return JSON array of relationships with confidence ≥ 0.70:

Exhibit A.1                     (child: section 1)

Exhibit A.1.1                   (grandchild: subsection 1.1)[

Exhibit A.2                     (child: section 2)  {

    "source_id": "annex_id",

Section 3                       (parent: document section)    "target_id": "section_id",

Section 3.1                     (child: subsection 1)    "relationship_type": "ATTACHMENT_OF",

Section 3.1.2                   (grandchild: sub-subsection 1.2)    "confidence": 0.70-1.0,

    "reasoning": "Brief explanation"

Specification 5000              (parent: spec)  }

Specification 5000.1            (child: sub-spec)]

``````



**Detection Logic**:---

- Extract prefix (everything before last decimal point)

- Check if prefix matches another entity's full ID## Agency-Specific Patterns (Examples)

- If match: Create CHILD_OF relationship

### Department of Defense (Navy, Marine Corps)

**Confidence**: 0.90 (common pattern, can conflict with version numbers)```

J-0200000-18 → Section J

---J-0300000-12 → Section J

```

## LLM Inference Prompt Template

### General Services Administration (GSA)

``````

You are analyzing document references to build hierarchical relationships (parent-child structure).Exhibit A → Section J

Appendix 1 → Section J

ENTITIES:Attachment I → Section J

{json_list_of_documents_clauses_annexes}```



TASK:### Department of Energy (DOE)

For each entity, determine if it is a CHILD of another entity based on:```

Annex 1 → Section J

1. PREFIX + DELIMITER (Confidence 0.95):Attachment A → Section J

   - J-02000000-10 is child of J-02000000 (shares prefix, adds -10)```

   - H-1.1 is child of H-1 (shares prefix, adds .1)

### NASA

2. STANDARD + SUBSECTION (Confidence 0.90):```

   - "MIL-STD-882E Task 101" is child of "MIL-STD-882E"Annex XVII → Section J

   - "NIST 800-171 3.1.1" is child of "NIST 800-171 Rev 2"Exhibit 1 → Section J

   - "ISO 9001:2015 8.2.3" is child of "ISO 9001:2015"```



3. CLAUSE + PARAGRAPH (Confidence 0.95):### Department of State

   - "FAR 52.212-4(a)" is child of "FAR 52.212-4"```

   - "DFARS 252.204-7012(b)(2)" is child of "DFARS 252.204-7012(b)"Attachment 1 → Section J

Appendix A → Section J

4. DECIMAL NOTATION (Confidence 0.90):```

   - "Exhibit A.1" is child of "Exhibit A"

   - "Section 3.1.2" is child of "Section 3.1"**Key Insight**: LLM understands ALL these patterns semantically, not via hardcoded regex!



HIERARCHICAL RULES:---

- A document can have MULTIPLE children (1-to-many)

- A document has AT MOST ONE parent (many-to-1)## Special Cases

- Multi-level nesting is allowed (grandchildren, great-grandchildren)

- Confidence threshold: ≥0.70### Case 1: Section C References J Annex



ENTITY TYPES:**Example**:

- ANNEX: RFP attachments (J-02000000, Exhibit A, Annex XVII)```

- DOCUMENT: Referenced standards (MIL-STD, NIST, ISO, IEEE)Section C: Description/Specifications

- CLAUSE: FAR/DFARS clauses with paragraph citationsSee Attachment J-0200000-18 for Performance Work Statement.

```

OUTPUT FORMAT:

[**Solution**: Create TWO relationships

  {```json

    "source_id": "child_document_id",[

    "target_id": "parent_document_id",  {

    "relationship_type": "CHILD_OF",    "source": "annex_j0200000_18",

    "confidence": 0.70-0.95,    "target": "section_j",

    "reasoning": "Pattern name and specific match details"    "type": "ATTACHMENT_OF",

  }    "confidence": 1.0,

]    "reasoning": "Naming convention"

```  },

  {

---    "source": "section_c",

    "target": "annex_j0200000_18",

## Special Cases    "type": "REFERENCES",

    "confidence": 0.95,

### Case 1: Multi-Level Nesting (Grandchildren)    "reasoning": "Section C explicitly references this annex"

  }

**Problem**: Three-level hierarchy (parent → child → grandchild)]

```

**Example**:

```### Case 2: Standalone Annex (No Clear Section)

J-02000000              (parent: PWS)

J-02000000-10           (child: Technical Requirements)**When**: Annex has no prefix pattern and no section mentions it

J-02000000-10-A         (grandchild: Hardware Requirements)

```**Solution**: Default to Section J (confidence 0.60)



**Solution**: Create TWO relationships**Example**:

```json```

["Technical Specifications Document"

  {```

    "source_id": "annex_j_02000000_10",

    "target_id": "annex_j_02000000",**Extraction**:

    "relationship_type": "CHILD_OF",```json

    "confidence": 0.95{

  },  "source_id": "annex_tech_specs",

  {  "target_id": "section_j",

    "source_id": "annex_j_02000000_10_a",  "relationship_type": "ATTACHMENT_OF",

    "target_id": "annex_j_02000000_10",  "confidence": 0.60,

    "relationship_type": "CHILD_OF",  "reasoning": "No prefix pattern; defaulting to Section J (List of Attachments)"

    "confidence": 0.95}

  }```

]

```### Case 3: Multi-Level Attachments



**Result**: Full tree navigation via transitive relationships**Example**:

```

---J-0200000-18: PWS

  - Sub-Annex J-0200000-18-A: Equipment List

### Case 2: Version Numbers vs. Subsections  - Sub-Annex J-0200000-18-B: Site Map

```

**Problem**: Decimal notation can be version OR hierarchy

**Solution**: Create hierarchy

**Examples**:```json

```[

AMBIGUOUS:  {

ISO 9001:2015           (version year, NOT hierarchy)    "source": "annex_j0200000_18",

NIST 800-53 Rev 5       (revision, NOT hierarchy)    "target": "section_j",

    "type": "ATTACHMENT_OF"

HIERARCHICAL:  },

ISO 9001:2015 8.2.3     (section 8.2.3, IS hierarchy)  {

NIST 800-53 Rev 5 AC-1  (control AC-1, IS hierarchy)    "source": "sub_annex_j0200000_18_a",

```    "target": "annex_j0200000_18",

    "type": "CHILD_OF"

**Detection Rule**:  },

- If suffix is 4 digits (year) → Version, NOT hierarchy  {

- If suffix is "Rev N" → Version, NOT hierarchy    "source": "sub_annex_j0200000_18_b",

- If suffix is X.Y.Z or letter-number → Hierarchy    "target": "annex_j0200000_18",

    "type": "CHILD_OF"

**Action**: Only create CHILD_OF if hierarchical suffix detected  }

]

---```



### Case 3: Similar But Not Related---



**Problem**: Documents with similar names that are NOT parent-child## Quality Validation



**Example**:### Validation Rules

```

NOT RELATED:1. ✅ **100% coverage**: Every annex must link to at least one section

MIL-STD-882E (System Safety)2. ✅ **Confidence threshold**: ≥0.60 minimum

MIL-STD-881D (Work Breakdown Structure)3. ✅ **Naming convention preferred**: Use prefix pattern when available (confidence 1.0)

→ Similar prefix but different standards (NOT parent-child)4. ✅ **No orphans**: Every annex has ATTACHMENT_OF relationship



FAR 52.212-4 (Contract Terms)### Expected Relationship Counts (Baseline)

FAR 52.212-5 (Required Statutes)

→ Sequential numbering but different clauses (NOT parent-child)**Navy MBOS (71-page RFP)**:

```- Annexes: 88 entities

- Expected ATTACHMENT_OF relationships: 88 (100% coverage)

**Detection Rule**:

- Full parent ID must be PREFIX of child ID**Branch 002 Baseline (Regex)**: 84.6% coverage (74/88 linked)  

- NOT just similar or overlapping text**Branch 003 Goal (LLM)**: 100% coverage (88/88 linked) ✅



------



### Case 4: Cross-Type Hierarchy (ANNEX → DOCUMENT)## Examples from Real RFPs



**Problem**: Annex may reference a standard, creating cross-type hierarchy### Example 1: Navy MBOS (Standard Pattern)

```

**Example**:Section J: List of Attachments

```

J-02000000 "PWS - Cybersecurity Requirements per NIST 800-171"J-0200000-18: Performance Work Statement

NIST 800-171 3.1.1 (specific control)J-0300000-12: Equipment List

```J-0400000-05: Site Layout Maps

```

**Question**: Is NIST 800-171 3.1.1 a child of J-02000000?

**Extracted Relationships** (3):

**Answer**: NO - Use REFERENCES relationship instead```json

```[

J-02000000 --REFERENCES--> NIST 800-171  {

NIST 800-171 3.1.1 --CHILD_OF--> NIST 800-171    "source_id": "annex_j0200000_18",

```    "target_id": "section_j",

    "relationship_type": "ATTACHMENT_OF",

**Rule**: CHILD_OF relationships stay within same document family (J-annexes, NIST controls, FAR clauses)    "confidence": 1.0,

    "reasoning": "Naming convention: 'J-' prefix"

---  },

  {

## Integration with Other Relationship Types    "source_id": "annex_j0300000_12",

    "target_id": "section_j",

### Relationship 1: ATTACHMENT_OF (Section Linkage)    "relationship_type": "ATTACHMENT_OF",

    "confidence": 1.0,

**Purpose**: Link top-level attachments to RFP sections    "reasoning": "Naming convention: 'J-' prefix"

  },

**Example**:  {

```    "source_id": "annex_j0400000_05",

J-02000000 --ATTACHMENT_OF--> Section J    "target_id": "section_j",

```    "relationship_type": "ATTACHMENT_OF",

    "confidence": 1.0,

**When to Use**: Top-level annexes/attachments linking to parent RFP section    "reasoning": "Naming convention: 'J-' prefix"

  }

**Different from CHILD_OF**: ]

- ATTACHMENT_OF: Document → Section (cross-type)```

- CHILD_OF: Document → Document (same-type hierarchy)

### Example 2: GSA RFP (Non-Standard Pattern)

---```

Section 7: Attachments

### Relationship 2: CHILD_OF (Clause Clustering)

Exhibit A: Statement of Work

**Purpose**: Link clauses to parent sectionsAppendix 1: Price Schedule

Attachment I: Sample Invoice

**Example**:```

```

FAR 52.212-4 --CHILD_OF--> Section I**Extracted Relationships** (3):

``````json

[

**Note**: This is DIFFERENT from clause paragraph hierarchy!  {

- Section linkage: `FAR 52.212-4 --CHILD_OF--> Section I` (which section?)    "source_id": "annex_exhibit_a",

- Paragraph hierarchy: `FAR 52.212-4(a) --CHILD_OF--> FAR 52.212-4` (which paragraph?)    "target_id": "section_7",

    "relationship_type": "ATTACHMENT_OF",

**Both relationships coexist**:    "confidence": 0.95,

```    "reasoning": "Explicit citation: Listed under 'Section 7: Attachments'"

FAR 52.212-4 --CHILD_OF--> Section I (clause_clustering.md)  },

FAR 52.212-4(a) --CHILD_OF--> FAR 52.212-4 (document_hierarchy.md)  {

```    "source_id": "annex_appendix_1",

    "target_id": "section_7",

---    "relationship_type": "ATTACHMENT_OF",

    "confidence": 0.95,

### Relationship 3: REFERENCES (Content Citation)    "reasoning": "Explicit citation: Listed under 'Section 7: Attachments'"

  },

**Purpose**: Document mentions/cites another document  {

    "source_id": "annex_attachment_i",

**Example**:    "target_id": "section_7",

```    "relationship_type": "ATTACHMENT_OF",

Section C "SOW" --REFERENCES--> MIL-STD-882E    "confidence": 0.95,

Section C "SOW" --REFERENCES--> NIST 800-171    "reasoning": "Explicit citation: Listed under 'Section 7: Attachments'"

```  }

]

**Different from CHILD_OF**:```

- REFERENCES: Semantic citation (content-based)

- CHILD_OF: Structural hierarchy (numbering-based)---



---## Error Patterns to Avoid



## Quality Validation### ❌ Error 1: Ignoring Prefix Patterns

```

### Validation RulesWRONG:

"J-0200000-18" linked to Section C (because content is PWS)

1. ✅ **Acyclic graph**: No circular parent-child relationships```

2. ✅ **Single parent**: Each document has ≤1 parent (not multiple)

3. ✅ **Confidence threshold**: ≥0.70**Correct**: Link to Section J based on "J-" prefix (confidence 1.0), THEN create REFERENCES relationship from Section C

4. ✅ **Same document family**: CHILD_OF stays within J-annexes, NIST controls, FAR clauses (no cross-family)

### ❌ Error 2: Creating Circular References

### Expected Relationship Counts (Baseline)```

WRONG:

**Navy MBOS (71-page RFP)**:Annex A → Section J

- Annexes: ~88 entities (ANNEX type)Section J → Annex A

- Top-level annexes: ~15 (J-02000000, J-03000000, etc.)```

- Sub-annexes: ~73 (J-02000000-10, J-02000000-20, etc.)

- Expected CHILD_OF relationships: ~73 (100% coverage of sub-annexes)**Correct**: Only child→parent (ATTACHMENT_OF)



**Improvement from Regex Baseline**:### ❌ Error 3: Leaving Orphans

- Phase 6.0 (regex patterns): 84.6% coverage (74 of 88 linked)```

- Phase 6.1 (LLM semantic): 100% target coverage (88 of 88 linked)WRONG:

Annex has no ATTACHMENT_OF relationship

---```



## Examples from Real RFPs**Correct**: Default to Section J if no clear parent (confidence 0.60)



### Example 1: Navy MBOS - J-Annex Hierarchy---



**Entities**:## Success Criteria

```

ANNEX_001: J-02000000 "Performance Work Statement (PWS)"A successful annex linking run should:

ANNEX_002: J-02000000-10 "Technical Requirements"

ANNEX_003: J-02000000-20 "Security Requirements"1. ✅ **100% coverage**: Every annex linked to at least one section

ANNEX_004: J-02000000-30 "Data Requirements"2. ✅ **High confidence average**: ≥0.90 (most are naming convention matches)

ANNEX_005: J-03000000 "Quality Assurance Surveillance Plan"3. ✅ **Agency-agnostic**: Works for DoD, GSA, NASA, DoE, State, etc.

ANNEX_006: J-03000000-10 "Performance Standards"4. ✅ **Zero orphans**: No unlinked annexes

```

---

**Extracted Relationships** (5):

```json**Last Updated**: January 2025 (Branch 004)  

[**Version**: 2.0 (LLM semantic inference replaces regex patterns)  

  {**Achievement**: 100% coverage (vs 84.6% regex baseline)

    "source_id": "annex_002",
    "target_id": "annex_001",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Pattern 1: Prefix match J-02000000-10 → J-02000000"
  },
  {
    "source_id": "annex_003",
    "target_id": "annex_001",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Pattern 1: Prefix match J-02000000-20 → J-02000000"
  },
  {
    "source_id": "annex_004",
    "target_id": "annex_001",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Pattern 1: Prefix match J-02000000-30 → J-02000000"
  },
  {
    "source_id": "annex_006",
    "target_id": "annex_005",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Pattern 1: Prefix match J-03000000-10 → J-03000000"
  }
]
```

**Result**: Zero orphaned sub-annexes, full tree navigation

---

### Example 2: NIST 800-171 Control Hierarchy

**Entities**:
```
DOCUMENT_010: "NIST 800-171 Rev 2"
DOCUMENT_011: "NIST 800-171 3.1.1 Access Control Policy"
DOCUMENT_012: "NIST 800-171 3.1.2 Account Management"
DOCUMENT_013: "NIST 800-171 3.5.1 Identification"
```

**Extracted Relationships** (3):
```json
[
  {
    "source_id": "document_011",
    "target_id": "document_010",
    "relationship_type": "CHILD_OF",
    "confidence": 0.90,
    "reasoning": "Pattern 2: Standard+subsection match NIST 800-171 3.1.1 → NIST 800-171 Rev 2"
  },
  {
    "source_id": "document_012",
    "target_id": "document_010",
    "relationship_type": "CHILD_OF",
    "confidence": 0.90,
    "reasoning": "Pattern 2: Standard+subsection match NIST 800-171 3.1.2 → NIST 800-171 Rev 2"
  },
  {
    "source_id": "document_013",
    "target_id": "document_010",
    "relationship_type": "CHILD_OF",
    "confidence": 0.90,
    "reasoning": "Pattern 2: Standard+subsection match NIST 800-171 3.5.1 → NIST 800-171 Rev 2"
  }
]
```

**Result**: Control family structure preserved

---

### Example 3: DFARS Paragraph Hierarchy

**Entities**:
```
CLAUSE_020: "DFARS 252.204-7012 Safeguarding Covered Defense Information"
CLAUSE_021: "DFARS 252.204-7012(b)(2) Cyber incident reporting"
CLAUSE_022: "DFARS 252.204-7012(c)(1) Subcontract flowdown"
```

**Extracted Relationships** (2):
```json
[
  {
    "source_id": "clause_021",
    "target_id": "clause_020",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Pattern 3: Clause+paragraph match DFARS 252.204-7012(b)(2) → DFARS 252.204-7012"
  },
  {
    "source_id": "clause_022",
    "target_id": "clause_020",
    "relationship_type": "CHILD_OF",
    "confidence": 0.95,
    "reasoning": "Pattern 3: Clause+paragraph match DFARS 252.204-7012(c)(1) → DFARS 252.204-7012"
  }
]
```

**Result**: Clause paragraph structure linked to parent

---

## Error Patterns to Avoid

### ❌ Error 1: Version Numbers as Hierarchy
```
WRONG:
"NIST 800-171 Rev 2" --CHILD_OF--> "NIST 800-171" (revision, not subsection)
```

**Correct**: Rev 2 is a version identifier, NOT a child document

---

### ❌ Error 2: Similar But Unrelated Documents
```
WRONG:
"MIL-STD-881D" --CHILD_OF--> "MIL-STD-882E" (different standards)
```

**Correct**: Shared prefix "MIL-STD" doesn't mean parent-child relationship

---

### ❌ Error 3: Cross-Family Hierarchies
```
WRONG:
"NIST 800-171 3.1.1" --CHILD_OF--> "J-02000000" (wrong document family)
```

**Correct**: Use REFERENCES instead:
```
"J-02000000" --REFERENCES--> "NIST 800-171"
"NIST 800-171 3.1.1" --CHILD_OF--> "NIST 800-171"
```

---

### ❌ Error 4: Multiple Parents
```
WRONG:
"J-02000000-10" --CHILD_OF--> "J-02000000"
"J-02000000-10" --CHILD_OF--> "Section J" (two parents!)
```

**Correct**: One structural parent only:
```
"J-02000000" --ATTACHMENT_OF--> "Section J" (section linkage)
"J-02000000-10" --CHILD_OF--> "J-02000000" (document hierarchy)
```

---

## Success Criteria

A successful document hierarchy run should:

1. ✅ **100% sub-document coverage**: Every hierarchical document linked to parent
2. ✅ **Acyclic graph**: No circular dependencies
3. ✅ **Single parent rule**: Each document has ≤1 CHILD_OF parent
4. ✅ **Multi-level support**: Grandchildren linked correctly (transitive closure works)
5. ✅ **Agency-agnostic**: Works for Navy, GSA, NASA, DoD, civilian agencies

---

**Last Updated**: January 2025 (Branch 004 - Phase 1 Refactor)  
**Version**: 2.0 (Generalized from annex-specific to document-wide hierarchy)  
**Key Improvement**: Handles DOCUMENT, CLAUSE, ANNEX entity types with 4 universal patterns (not just Navy J-annexes)  
**Impact**: Solves orphaned sub-documents across all RFP types and document families
