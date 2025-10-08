# Section Normalization Mapping

**Purpose**: Map non-standard section labels to semantic types  
**Usage**: Normalize RFP structure variations to standard UCF (Uniform Contract Format)  
**Philosophy**: Content determines type, not labels

---

## Standard Uniform Contract Format (UCF)

Per FAR 15.210, federal solicitations use standard lettered sections:

| Section | Semantic Type | Common Aliases |
|---------|--------------|----------------|
| **Section A** | SOLICITATION_FORM | SF 1449, Cover Page, Request for Quote |
| **Section B** | SUPPLIES_SERVICES | CLIN Structure, SLIN, Line Items |
| **Section C** | DESCRIPTION_SPECS | SOW, PWS, SOO, Statement of Work |
| **Section D** | PACKAGING_MARKING | Shipping Instructions, Packaging |
| **Section E** | INSPECTION_ACCEPTANCE | Quality Assurance, QA Plan |
| **Section F** | DELIVERIES_PERFORMANCE | Schedule, Period of Performance (PoP) |
| **Section G** | CONTRACT_ADMIN | Admin Data, CAGE codes, Payment |
| **Section H** | SPECIAL_REQUIREMENTS | H-clauses, Special Terms, Key Personnel |
| **Section I** | CONTRACT_CLAUSES | FAR Clauses, I-clauses, Terms |
| **Section J** | ATTACHMENTS | List of Attachments, Annexes, References |
| **Section K** | REPRESENTATIONS | Reps and Certs, K-clauses, Certifications |
| **Section L** | SUBMISSION_INSTRUCTIONS | Instructions to Offerors, Proposal Format |
| **Section M** | EVALUATION_CRITERIA | Evaluation Factors, Source Selection |

---

## Non-Standard Label Mapping

### Task Orders and Fair Opportunity Requests

Many Task Orders use different terminology:

| Non-Standard Label | Maps To | Semantic Type |
|--------------------|---------|---------------|
| Request for Quote (RFQ) | Section A | SOLICITATION_FORM |
| Technical Requirements | Section C | DESCRIPTION_SPECS |
| Work Requirements | Section C | DESCRIPTION_SPECS |
| Statement of Objectives | Section C | DESCRIPTION_SPECS |
| Proposal Instructions | Section L | SUBMISSION_INSTRUCTIONS |
| Submission Requirements | Section L | SUBMISSION_INSTRUCTIONS |
| Selection Criteria | Section M | EVALUATION_CRITERIA |
| Evaluation Methodology | Section M | EVALUATION_CRITERIA |
| Source Selection Plan | Section M | EVALUATION_CRITERIA |

### Agency-Specific Variations

| Non-Standard Label | Maps To | Semantic Type |
|--------------------|---------|---------------|
| Scope of Work | Section C | DESCRIPTION_SPECS |
| Performance Work Statement | Section C | DESCRIPTION_SPECS |
| Technical Specifications | Section C | DESCRIPTION_SPECS |
| Special Contract Requirements | Section H | SPECIAL_REQUIREMENTS |
| Applicable Clauses | Section I | CONTRACT_CLAUSES |
| Required Certifications | Section K | REPRESENTATIONS |

---

## Content-Based Detection Rules

When section labels are ambiguous or missing, use content signals:

### EVALUATION_CRITERIA Detection
**Signals**:
- "will be evaluated"
- "evaluation factor"
- "most important"
- "adjectival rating"
- "source selection"
- Factor numbering (M1, M2, M2.1)

**Maps To**: Section M

### SUBMISSION_INSTRUCTIONS Detection
**Signals**:
- "page limit"
- "font size"
- "proposal shall"
- "volume structure"
- "submit by"
- "electronic submission"

**Maps To**: Section L

### CONTRACT_CLAUSES Detection
**Signals**:
- FAR/DFARS/AFFARS clause numbers
- "52.###-##" patterns
- "252.###-####" patterns
- "incorporated by reference"
- Clause titles

**Maps To**: Section I or K

### DESCRIPTION_SPECS Detection
**Signals**:
- Task descriptions
- Performance objectives
- Deliverables list
- Work scope
- "contractor shall perform"
- Task numbering (1.0, 1.1, 1.1.1)

**Maps To**: Section C

---

## Mixed Content Handling

Some sections contain multiple content types:

### Example: Section M with Embedded Instructions

**Document Structure**:
```
Section M: Evaluation Factors

Factor 1: Technical Approach (Most Important)

[Evaluation criteria text...]

The Technical Volume shall be limited to 25 pages...
```

**Normalization**:
```json
{
  "section_entity": {
    "structural_label": "Section M",
    "semantic_type": "EVALUATION_CRITERIA",
    "also_contains": ["SUBMISSION_INSTRUCTION"]
  },
  "extraction_note": "Create separate SUBMISSION_INSTRUCTION entity linked to Factor 1"
}
```

### Example: Section C as Attachment

**Document Structure**:
```
Section C: Description/Specifications/Data

See Attachment J-0200000-18 for Performance Work Statement.
```

**Normalization**:
```json
{
  "section_c_entity": {
    "structural_label": "Section C",
    "semantic_type": "DESCRIPTION_SPECS",
    "content_location": "By Reference"
  },
  "annex_entity": {
    "structural_label": "Attachment J-0200000-18",
    "semantic_type": "DESCRIPTION_SPECS",
    "content_type": "PWS"
  },
  "relationship": "Section C → REFERENCES → J-0200000-18"
}
```

---

## Confidence Scoring

Assign confidence to section type detection:

### High Confidence (0.9-1.0)
- Standard UCF label matches content
- Example: "Section M" contains evaluation factors
- Clear content signals present

### Medium Confidence (0.7-0.89)
- Non-standard label but clear content
- Example: "Selection Criteria" contains evaluation language
- Multiple content signals present

### Low Confidence (0.5-0.69)
- Ambiguous label and mixed content
- Example: "Requirements" could be Section C or H
- Few content signals

### Very Low Confidence (<0.5)
- Contradictory signals or insufficient context
- Manual review recommended

---

## Section Attribution Rules

When entities don't have clear section labels:

### Clause Attribution
All FAR/DFARS clauses default to:
- **Section I**: Contract clauses (52.###-##, 252.###-####)
- **Section K**: Representations and certifications (52.2##-## series)

### Annex Attribution
Prefix-based attribution:
- `J-######` → Section J
- `Attachment #` → Section J
- `Annex ##` → Section J or standalone
- Letter prefix → Corresponding section (A-#### → Section A)

### Requirement Attribution
Default to Section C unless:
- Labeled "Section H" → SPECIAL_REQUIREMENTS
- Part of Section I/K → CONTRACT_CLAUSES/REPRESENTATIONS

---

## Examples from Real RFPs

### Example 1: Navy MBOS (Standard UCF)
```
Section A: Solicitation/Contract/Order for Commercial Products and Commercial Services
Section C: Description/Specifications/Work Statement
Section H: Special Contract Requirements
Section I: Contract Clauses
Section J: List of Attachments
Section L: Instructions, Conditions, and Notices to Offerors
Section M: Evaluation Factors for Award
```

**Normalization**: Direct mapping to standard types (confidence: 1.0)

### Example 2: Task Order (Non-Standard)
```
1.0 Request for Quote
2.0 Technical Requirements
3.0 Proposal Instructions
4.0 Selection Criteria
```

**Normalization**:
```json
{
  "1.0": {"maps_to": "Section A", "semantic_type": "SOLICITATION_FORM"},
  "2.0": {"maps_to": "Section C", "semantic_type": "DESCRIPTION_SPECS"},
  "3.0": {"maps_to": "Section L", "semantic_type": "SUBMISSION_INSTRUCTIONS"},
  "4.0": {"maps_to": "Section M", "semantic_type": "EVALUATION_CRITERIA"}
}
```

### Example 3: Ambiguous Structure
```
Requirements Document

Part 1: Work Scope
Part 2: Quality Standards
Part 3: Evaluation Approach
```

**Normalization** (content-based):
```json
{
  "Part 1": {"maps_to": "Section C", "semantic_type": "DESCRIPTION_SPECS", "confidence": 0.85},
  "Part 2": {"maps_to": "Section H or C", "semantic_type": "SPECIAL_REQUIREMENTS or DESCRIPTION_SPECS", "confidence": 0.65},
  "Part 3": {"maps_to": "Section M", "semantic_type": "EVALUATION_CRITERIA", "confidence": 0.90}
}
```

---

## Quality Checks

Before finalizing section normalization:

1. ✅ **Every section has semantic_type**: No unmapped sections
2. ✅ **Content matches type**: Section M actually contains evaluation criteria
3. ✅ **Confidence justified**: High confidence only with clear signals
4. ✅ **Mixed content flagged**: `also_contains` field used when appropriate
5. ✅ **Cross-references resolved**: "See Section X" links validated

---

**Last Updated**: January 2025 (Branch 004)  
**Version**: 2.0 (Enhanced from phase6_prompts.py with confidence scoring and examples)
