# Metadata Extraction Guidance

**Purpose**: Field-level extraction rules for entity metadata  
**Usage**: Guide LLM to extract structured metadata for each entity type  
**Philosophy**: Rich metadata enables advanced queries and relationship inference

---

## REQUIREMENT Entity Metadata

### Schema
```json
{
  "requirement_type": string,       // One of 8 types (FUNCTIONAL, PERFORMANCE, etc.)
  "criticality_level": string,      // MANDATORY | IMPORTANT | OPTIONAL | INFORMATIONAL
  "priority_score": integer,        // 0-100 (auto-calculated from criticality)
  "section_origin": string,         // Where it appeared (e.g., "Section C.3.1.2")
  "semantic_context": string,       // What it IS (e.g., "Performance requirement within maintenance SOW")
  "modal_verb": string,             // Extracted verb: "shall", "should", "may", "will"
  "subject": string                 // Who must comply: "Contractor", "Government", "Offeror"
}
```

### Extraction Rules

#### requirement_type
**Purpose**: Classify by content domain  
**Method**: Keyword pattern matching

- **FUNCTIONAL**: "provide", "deliver", "perform", "execute" + service/product
- **PERFORMANCE**: SLA language, metrics, measurable outcomes (%, time, rate)
- **SECURITY**: NIST, FedRAMP, clearance, cybersecurity, CMMC
- **TECHNICAL**: Technology stack, platforms, software versions, infrastructure
- **INTERFACE**: Integration, APIs, data exchange, system connections
- **MANAGEMENT**: Reporting, governance, oversight, PM methodology
- **DESIGN**: Standards compliance, architectural mandates, design constraints
- **QUALITY**: QA, testing, verification, validation, certification

#### criticality_level
**Purpose**: Determine obligation strength  
**Method**: Parse modal verb AND subject

```python
# Decision tree:
if modal_verb in ["shall", "must", "will"] and subject in ["Contractor", "Offeror"]:
    return "MANDATORY"
elif modal_verb in ["shall", "will"] and subject in ["Government", "Agency"]:
    return "INFORMATIONAL"  # NOT a requirement!
elif modal_verb in ["should", "encouraged"]:
    return "IMPORTANT"
elif modal_verb in ["may", "can", "option"]:
    return "OPTIONAL"
```

#### priority_score
**Purpose**: Numerical ranking for sorting  
**Method**: Auto-calculate from criticality

```python
CRITICALITY_SCORES = {
    "MANDATORY": 100,
    "IMPORTANT": 75,
    "OPTIONAL": 25,
    "INFORMATIONAL": 0
}
```

#### section_origin
**Purpose**: Traceability to source location  
**Method**: Extract hierarchical section reference

**Patterns**:
- "Section C.3.1.2" (full hierarchy)
- "PWS Task 1.2.3" (SOW task number)
- "Attachment J-1234567, Para 3.1" (annex + paragraph)

**Quality Check**: Must be verifiable page reference

#### semantic_context
**Purpose**: Describe what this requirement IS (not just what it says)  
**Method**: Summarize in plain English

**Examples**:
- "Performance requirement within maintenance SOW"
- "Security clearance requirement for key personnel"
- "Reporting requirement for monthly status updates"

#### modal_verb
**Purpose**: Extract the obligation verb  
**Method**: Find primary modal verb in sentence

**Valid Values**: "shall", "should", "may", "must", "will", "can", "encouraged"

**Extraction Pattern**:
```
"The Contractor shall provide..." → modal_verb = "shall"
"Offeror should submit..." → modal_verb = "should"
"Government will conduct..." → modal_verb = "will"
```

#### subject
**Purpose**: Identify who has the obligation  
**Method**: Parse sentence subject

**Valid Values**: "Contractor", "Offeror", "Government", "Agency", "COR"

**CRITICAL**: This determines if it's a real requirement!
- "Contractor shall" → MANDATORY requirement
- "Government shall" → INFORMATIONAL (NOT a requirement for contractor)

---

## EVALUATION_FACTOR Entity Metadata

### Schema
```json
{
  "factor_id": string,              // "M1", "M2.1", "M2.1.1"
  "factor_name": string,            // "Technical Approach", "Staffing Plan"
  "relative_importance": string,    // "Most Important", "Significantly More Important"
  "subfactors": array[string],      // ["M2.1 Staffing", "M2.2 Maintenance"]
  "section_l_reference": string,    // "L.3.1" (link to submission instructions)
  "page_limits": string,            // "25 pages" (from Section L)
  "format_requirements": string,    // "12pt Times, 1-inch margins"
  "tradeoff_methodology": string,   // "Best Value", "LPTA"
  "evaluated_by_rating": string,    // "Adjectival", "Point Score", "Pass/Fail"
  "section_origin": string,         // Where it appeared
  "contains_submission_instructions": boolean  // True if instructions embedded
}
```

### Extraction Rules

#### factor_id
**Purpose**: Unique identifier for factor hierarchy  
**Method**: Extract numbering scheme

**Patterns**:
- "M1", "M2", "M3" (top-level)
- "M2.1", "M2.2" (subfactors)
- "M2.1.1", "M2.1.2" (sub-subfactors)
- "Factor 1", "Factor 2" (non-standard)
- "TECH_MERIT" (custom, if no numbering)

#### relative_importance
**Purpose**: Capture evaluation weight language  
**Method**: Extract exact phrase from document

**Standard Phrases** (FAR 15.304):
- "Most Important"
- "Significantly More Important"
- "More Important"
- "Equal" or "Equal Importance"
- "Less Important"
- "Significantly Less Important"

**Non-Standard Phrases**:
- "40% weight" → "Weighted 40%"
- "100 points" → "Point-scored: 100 points"
- "Pass/Fail" → "Pass/Fail (no weight)"

#### subfactors
**Purpose**: Capture factor hierarchy  
**Method**: Extract nested factor list

**Example**:
```
Factor 2: Maintenance Approach
  2.1 Staffing Plan
  2.2 Maintenance Philosophy
  2.3 Transition Plan
```

**Extracted**:
```json
{
  "factor_id": "M2",
  "subfactors": ["M2.1 Staffing Plan", "M2.2 Maintenance Philosophy", "M2.3 Transition Plan"]
}
```

#### section_l_reference
**Purpose**: Link to corresponding submission instruction  
**Method**: Search for cross-references

**Patterns**:
- "Technical Volume (see Section L.3.1)"
- "Address Factor 2 as specified in L.3.2"
- Implicit: Factor 2 → L.3.2 (by convention)

#### page_limits
**Purpose**: Extract page limit from Section L  
**Method**: Cross-reference or direct mention

**Patterns**:
- "25 pages"
- "50 pages maximum"
- "No page limit"
- "Not to exceed 30 pages"

**Source**: May come from Section L or embedded in Section M

#### format_requirements
**Purpose**: Extract formatting rules  
**Method**: Parse font, margins, spacing

**Example**: "12pt Times New Roman, 1-inch margins, single-spaced"

#### tradeoff_methodology
**Purpose**: Identify source selection approach  
**Method**: Extract methodology statement

**Values**:
- "Best Value" (FAR 15.101-1)
- "LPTA" or "Lowest Price Technically Acceptable" (FAR 15.101-2)
- "Cost/Technical Tradeoff"

#### evaluated_by_rating
**Purpose**: Identify rating scale  
**Method**: Extract rating methodology

**Values**:
- "Adjectival" (Excellent, Good, Acceptable, Marginal, Unacceptable)
- "Point Score" (0-100 points)
- "Pass/Fail"
- "Color Rating" (Blue, Purple, Red, Yellow, Green)

#### contains_submission_instructions
**Purpose**: Flag embedded instructions  
**Method**: Detect format requirements within evaluation section

**Pattern**: If Section M paragraph includes page limits, font size, or format rules → `true`

---

## SUBMISSION_INSTRUCTION Entity Metadata

### Schema
```json
{
  "guides_factor": string,          // Which evaluation factor this instructs
  "volume_name": string,            // "Technical Volume", "Management Volume"
  "page_limits": string,            // "25 pages", "50 pages maximum"
  "format_requirements": string,    // "12pt Times, 1-inch margins, single-spaced"
  "section_origin": string,         // "Section L.3.1" or "Section M.2 (embedded)"
  "delivery_method": string,        // "Electronic via email", "Hard copy"
  "deadline": string,               // ISO 8601 datetime
  "file_format": string             // "PDF", "MS Word", "Both"
}
```

### Extraction Rules

#### guides_factor
**Purpose**: Link instruction to evaluation factor  
**Method**: Parse cross-reference or content alignment

**Patterns**:
- Explicit: "Technical Volume addresses Factor 2"
- Implicit: Technical Volume → Technical Approach factor (by name alignment)

#### volume_name
**Purpose**: Identify proposal volume  
**Method**: Extract volume designation

**Common Values**:
- "Technical Volume"
- "Management Volume"
- "Cost Volume"
- "Past Performance Volume"

#### deadline
**Purpose**: Extract submission due date/time  
**Method**: Parse datetime and convert to ISO 8601

**Example**:
- Input: "March 15, 2025, 2:00 PM EST"
- Output: "2025-03-15T14:00:00-05:00"

---

## SECTION Entity Metadata

### Schema
```json
{
  "structural_label": string,       // What document calls it
  "semantic_type": string,          // What it actually IS
  "also_contains": array[string],   // Mixed content types
  "confidence": float,              // 0.0-1.0 detection confidence
  "page_range": string,             // "15-25"
  "subsections": array[string]      // ["M.1", "M.2", "M.2.1"]
}
```

### Extraction Rules

#### structural_label
**Purpose**: Preserve original document labeling  
**Method**: Extract exact label from document

**Examples**:
- "Section M.2.1"
- "Selection Criteria"
- "Proposal Instructions"

#### semantic_type
**Purpose**: Classify by content type  
**Method**: Map to standard UCF type

**Standard Types**:
- SOLICITATION_FORM
- SUPPLIES_SERVICES
- DESCRIPTION_SPECS
- SPECIAL_REQUIREMENTS
- CONTRACT_CLAUSES
- ATTACHMENTS
- REPRESENTATIONS
- SUBMISSION_INSTRUCTIONS
- EVALUATION_CRITERIA

#### also_contains
**Purpose**: Flag mixed-content sections  
**Method**: Detect multiple content types in one section

**Example**: Section M with embedded submission instructions
```json
{
  "structural_label": "Section M",
  "semantic_type": "EVALUATION_CRITERIA",
  "also_contains": ["SUBMISSION_INSTRUCTION"]
}
```

---

## STRATEGIC_THEME Entity Metadata

### Schema
```json
{
  "theme_type": string,             // CUSTOMER_HOT_BUTTON | DISCRIMINATOR | PROOF_POINT | WIN_THEME
  "theme_statement": string,        // Full theme description
  "competitive_context": string,    // "Incumbent advantage", "New entrant gap"
  "evidence": string,               // Proof points, metrics, past performance
  "customer_benefit": string,       // Mission outcome, agency value
  "related_factors": array[string]  // ["M2", "M3"] evaluation factors
}
```

### Extraction Rules

#### theme_type
**Purpose**: Classify strategic theme  
**Method**: Pattern matching on content

**Types**:
- **CUSTOMER_HOT_BUTTON**: Agency priorities ("critical", "essential", "priority")
- **DISCRIMINATOR**: Competitive advantages ("unique", "only", "proprietary")
- **PROOF_POINT**: Evidence ("99.8% uptime", "CPARS Exceptional")
- **WIN_THEME**: Combined theme + discriminator + proof + benefit

#### competitive_context
**Purpose**: Assess competitive positioning  
**Method**: Analyze incumbent/new entrant status

**Values**:
- "Incumbent advantage" (current contractor knowledge)
- "New entrant gap" (no incumbent knowledge)
- "Competitive parity" (equal footing)

---

## ANNEX Entity Metadata

### Schema
```json
{
  "original_numbering": string,     // "J-1234567", "Attachment 5"
  "prefix_pattern": string,         // "J-", "Attachment "
  "content_type": string,           // "SOW", "Specifications", "Maps"
  "parent_section": string,         // "Section J" (inferred from prefix)
  "file_reference": string          // "Equipment_List.pdf"
}
```

### Extraction Rules

#### prefix_pattern
**Purpose**: Extract prefix for parent section linking  
**Method**: Regex pattern matching

**Patterns**:
```python
PATTERNS = {
    r'^([A-Z]-\d+)': 'Letter-Number',      # "J-1234567"
    r'^(Attachment\s+\d+)': 'Attachment',  # "Attachment 5"
    r'^(Annex\s+\d+)': 'Annex',           # "Annex 17"
    r'^(Appendix\s+[A-Z])': 'Appendix'    # "Appendix C"
}
```

---

## CLAUSE Entity Metadata

### Schema
```json
{
  "clause_number": string,          // "FAR 52.212-4"
  "agency_supplement": string,      // "FAR", "DFARS", "AFFARS"
  "clause_title": string,           // Official clause title
  "section_attribution": string,    // "Section I", "Section K"
  "incorporation_method": string,   // "Full Text", "By Reference"
  "date": string                    // "JAN 2024" (effective date)
}
```

### Extraction Rules

#### agency_supplement
**Purpose**: Identify regulatory source  
**Method**: Extract from clause number

**Patterns**:
- `FAR 52.###-##` → "FAR"
- `DFARS 252.###-####` → "DFARS"
- `AFFARS 5352.###-##` → "AFFARS"

**26+ Agency Supplements**: FAR, DFARS, AFFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, AIDAR, CAR, DIAR, DOLAR, EDAR, EPAAR, FEHBAR, HHSAR, HUDAR, IAAR, JAR, LIFAR, NRCAR, SOFARS, TAR

---

## STATEMENT_OF_WORK Entity Metadata

### Schema
```json
{
  "work_type": string,              // "PWS", "SOW", "SOO"
  "location": string,               // "Section C", "Attachment J-1234567"
  "hierarchical_structure": boolean, // Task hierarchy present
  "task_count": integer,            // Number of tasks (if hierarchical)
  "performance_standards": boolean, // PWS-specific standards present
  "prescription_level": string      // "High (SOW)", "Medium (PWS)", "Low (SOO)"
}
```

### Extraction Rules

#### work_type
**Purpose**: Identify SOW format  
**Method**: Content analysis + label detection

**Detection**:
- **SOW**: Prescriptive language ("shall use", "shall perform with")
- **PWS**: Performance standards ("achieve 95%", "maintain uptime")
- **SOO**: Objective language ("objective: provide", "goal:")

---

## PROGRAM Entity Metadata

### Schema
```json
{
  "program_name": string,           // "Marine Corps Prepositioning Program II"
  "program_acronym": string,        // "MCPP II"
  "program_scope": string,          // Brief mission/purpose
  "parent_organization": string,    // "Marine Corps", "Navy"
  "section_origin": string,         // "Document Title, Section C.1.0"
  "program_type": string            // "Major Acquisition", "IT Modernization"
}
```

---

## Quality Validation Rules

Before finalizing metadata extraction:

1. ✅ **Required fields populated**: All non-optional fields must have values
2. ✅ **Format validation**: Dates in ISO 8601, numbers are numeric
3. ✅ **Cross-reference integrity**: factor_id in EVALUATION_FACTOR matches guides_factor in SUBMISSION_INSTRUCTION
4. ✅ **Enum validation**: Values match allowed options (criticality_level, theme_type, etc.)
5. ✅ **Consistency**: Same entity referenced consistently across metadata

---

**Last Updated**: January 2025 (Branch 004)  
**Version**: 2.0 (Enhanced from phase6_prompts.py with detailed extraction rules)
