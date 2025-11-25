# Table-to-Text Conversion for Government Contracting RFPs

You are analyzing a **TABLE** from a government contracting Request for Proposal (RFP) document.

## Task

Convert this table into a **structured text narrative** that preserves all information in a format suitable for downstream entity extraction. The text description will be fed into the same entity extraction system that processes prose paragraphs.

## Critical Requirements

1. **Output Format**: Return ONLY plain text narrative. DO NOT return JSON, markdown tables, or structured data.
2. **Entity Preservation**: Convert table rows into natural language that makes entity types explicit
3. **Context Integration**: Use surrounding paragraphs to understand what type of information the table contains

## Government Contracting Entity Types to Preserve

### 1. Requirements

Look for modal verbs (shall/must/will/should/may) in table cells:

- Convert table rows into full sentences with modal verbs
- Preserve criticality levels based on verb choice
- Include row labels and cell values in complete statements

**Example**:

```
Table Row: | Access Control | Shall | Multi-factor |
Description: "The system shall implement multi-factor authentication for access control."
```

### 2. Performance Metrics

Identify columns with thresholds, targets, or measurement criteria:

- Extract metric name + threshold value + measurement method
- Preserve units and frequencies
- Link metrics to requirements where applicable

**Example**:

```
Table Row: | Response Time | < 2 hours | Monthly average |
Description: "Response Time shall be less than 2 hours measured as a monthly average."
```

### 3. Evaluation Factors

Look for scoring, weighting, or points columns:

- Preserve factor names and point values
- Note subfactors in nested rows
- Include evaluation basis or scoring criteria

**Example**:

```
Table Row: | Technical Approach | 40 points | Past Performance subfactor |
Description: "The Technical Approach evaluation factor is worth 40 points and includes Past Performance as a subfactor."
```

### 4. Workload Drivers

Extract operational volumes and capacity requirements:

- Frequencies (daily, weekly, monthly counts)
- Quantities (customer volumes, transaction counts, meal counts)
- Coverage periods (24/7, business hours, shifts)
- Equipment/facility quantities and specifications

**Example**:

```
Table Row: | Meals | 3 per day | 150 customers | 7 days/week |
Description: "The contractor shall provide meals three times per day to serve 150 customers, operating 7 days per week."
```

### 5. Deliverables

Identify submission items with constraints:

- Document names from first column
- Due dates, formats, page limits from other columns
- Submission recipients or methods

**Example**:

```
Table Row: | Monthly Status Report | 5th business day | PDF | 10 pages max |
Description: "The Monthly Status Report deliverable shall be submitted by the 5th business day in PDF format with a maximum length of 10 pages."
```

### 6. Clauses & Compliance

Regulatory references in table format:

- FAR/DFARS citations with full text where provided
- Compliance requirements from regulatory tables
- Certification or approval requirements

### 7. Submission Instructions

Proposal format requirements in tabular form:

- Section names with page limits
- Volume organization from tables
- Format requirements (font size, margins, binding)

## Conversion Guidelines

### Structure Preservation

- Each table row should become one or more complete sentences
- Maintain relationships between columns (don't isolate values)
- Use row headers as subject context for cell values
- Include column headers as attribute names in the narrative

### Context Integration

If context paragraphs are provided (before/after the table):

- Reference the context to understand table purpose
- Use section headers to classify entity types correctly
- Preserve cross-references between table and surrounding text

### Quantitative Data

- Preserve all numbers with their units
- Include ranges, thresholds, and comparison operators (≤, ≥, <, >)
- Maintain temporal qualifiers (daily, monthly, annually)

### Relationships

- When tables show hierarchical data (parent-child rows), express the hierarchy in text
- When tables map inputs to outputs, describe the mapping relationship
- When tables list alternatives, use "or" to show mutually exclusive options

## Example Transformation

**Input Table**:

```
| Requirement ID | Description | Criticality | Metric |
|----------------|-------------|-------------|---------|
| REQ-001 | Data encryption | Shall | AES-256 |
| REQ-002 | Backup frequency | Must | Daily |
| REQ-003 | Audit logging | Should | Real-time |
```

**Output Narrative**:

```
Requirement REQ-001 states that the system shall implement data encryption using AES-256 standard. Requirement REQ-002 specifies that data backups must be performed on a daily frequency. Requirement REQ-003 indicates that audit logging should operate in real-time mode.
```

## What NOT to Do

❌ **Don't** output JSON or structured data formats  
❌ **Don't** use markdown table syntax in the description  
❌ **Don't** lose information by summarizing (preserve all values)  
❌ **Don't** invent information not present in the table  
❌ **Don't** separate column values from their row context

## Output Expectation

Your response should be a **prose paragraph or series of paragraphs** that reads naturally while preserving all tabular information. The text should be ready for the entity extraction system to identify Requirements, PerformanceMetrics, EvaluationFactors, WorkloadDrivers, Deliverables, Clauses, SubmissionInstructions, and other government contracting entities.
