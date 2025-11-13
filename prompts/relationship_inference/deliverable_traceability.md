# Deliverable Traceability: Dual-Pattern Linking

**Purpose**: Link deliverables to both requirements (performance traceability) and work statements (work planning context)  
**Relationship Types**:

- REQUIREMENT --SATISFIED_BY--> DELIVERABLE (primary traceability)
- STATEMENT_OF_WORK --PRODUCES--> DELIVERABLE (work planning)
  **Last Updated**: November 12, 2025 (Branch 013b4 - Deliverable Traceability Fix)

---

## Context

Contract deliverables appear in multiple locations and serve dual purposes:

1. **Performance Traceability**: Deliverables prove compliance with requirements
2. **Work Planning**: Deliverables emerge from SOW/PWS/SOO tasks

**Deliverable Sources**:

- **CDRL Tables** (Section J): Formal contract data requirements - NOT in SOW text
- **Contract Clauses** (Section I): Deliverables mandated by FAR clauses
- **Evaluation Criteria** (Section M): Deliverables as proof points for scoring
- **SOW/PWS/SOO Text** (Section C/Attachments): Work products from task descriptions
- **Requirements** (Throughout): Performance standards requiring evidence

**Critical Insight**: Most deliverables (60-80%) come from CDRLs, clauses, and eval criteria - NOT from SOW text. This means requirement-based linking is PRIMARY, work statement linking is SECONDARY.

---

## Pattern 1: Requirement → Deliverable (PRIMARY)

### Purpose

Link performance/functional/technical requirements to deliverables that provide evidence of compliance.

### Relationship Type

`SATISFIED_BY` (directional: requirement satisfied by deliverable)

### Common Patterns

#### Pattern 1A: Reporting Requirements

- **Requirement**: "Contractor shall maintain 99.9% system uptime"
- **Deliverable**: "Monthly Uptime Report (CDRL A001)"
- **Reasoning**: Report provides evidence of uptime compliance
- **Confidence**: HIGH (0.85-0.95)

#### Pattern 1B: Documentation Requirements

- **Requirement**: "System shall support 500 concurrent users"
- **Deliverable**: "Performance Test Report (CDRL B003)"
- **Reasoning**: Test report validates performance requirement
- **Confidence**: MEDIUM-HIGH (0.75-0.85)

#### Pattern 1C: Proof Point Deliverables

- **Requirement**: "Implement zero-trust architecture"
- **Deliverable**: "Security Architecture Document (referenced in Section M)"
- **Reasoning**: Deliverable proves technical approach for evaluation
- **Confidence**: MEDIUM (0.65-0.75)

#### Pattern 1D: Compliance Evidence

- **Requirement**: "Comply with NIST SP 800-171"
- **Deliverable**: "System Security Plan (CDRL C002)"
- **Reasoning**: SSP documents NIST compliance implementation
- **Confidence**: HIGH (0.85-0.95)

### Detection Rules

1. **Semantic Overlap**: Match requirement domain to deliverable type

   - Testing requirements → Test reports/results
   - Performance requirements → Performance/uptime reports
   - Security requirements → Security plans/assessments
   - Training requirements → Training materials/records

2. **Keyword Correlation**: Match requirement verbs to deliverable evidence

   - "shall maintain" → monitoring/status reports
   - "shall implement" → design documents/implementation plans
   - "shall demonstrate" → test results/demonstrations
   - "shall comply with" → compliance reports/certifications

3. **Evidence Chain**: Deliverable provides proof of requirement satisfaction
   - Requirement describes capability/standard
   - Deliverable documents/validates that capability
   - Strong semantic connection between requirement content and deliverable purpose

### Confidence Thresholds

- **HIGH (0.85-0.95)**: Direct evidence relationship (test report for test requirement, uptime report for uptime requirement)
- **MEDIUM (0.65-0.85)**: Strong semantic overlap (security plan for security requirements)
- **LOW (0.50-0.65)**: Weak topical alignment only (general status report for specific requirement)

### Output Format

```json
{
  "source_id": "requirement_entity_id",
  "target_id": "deliverable_entity_id",
  "relationship_type": "SATISFIED_BY",
  "confidence": 0.50-0.95,
  "reasoning": "Deliverable type provides evidence/proof of requirement compliance"
}
```

---

## Pattern 2: Work Statement → Deliverable (SECONDARY)

### Purpose

Link SOW/PWS/SOO tasks to explicitly mentioned work products for work planning and task decomposition.

### Relationship Type

`PRODUCES` (directional: work statement produces deliverable)

### Common Patterns

#### Pattern 2A: Explicit Task→Deliverable Mentions

- **Work Statement**: "Prepare monthly status reports per CDRL A001"
- **Deliverable**: "Monthly Status Report (CDRL A001)"
- **Reasoning**: Direct CDRL reference in work statement text
- **Confidence**: HIGH (0.90-0.96)

#### Pattern 2B: Work-Product Mapping

- **PWS**: "Maintain facility infrastructure and equipment"
- **Deliverable**: "Facility Maintenance Logs (CDRL B012)"
- **Reasoning**: Maintenance work produces maintenance logs
- **Confidence**: MEDIUM (0.70-0.80)

#### Pattern 2C: Timeline Alignment

- **SOO**: "Complete Phase 1 cybersecurity objectives by Q2"
- **Deliverable**: "Phase 1 Security Assessment Report (due June 30)"
- **Reasoning**: Phase completion report aligns with phase objectives
- **Confidence**: MEDIUM (0.65-0.75)

### Detection Rules

1. **Direct CDRL References**: Search for deliverable names/IDs in work statement text

   - CDRL numbers (A001, B002, 6022)
   - Report names matching deliverable entities
   - Explicit "contractor shall deliver X" language

2. **Work-Product Correlation**: Match work activities to produced outputs

   - "testing" tasks → Test reports
   - "training" tasks → Training materials
   - "maintenance" tasks → Maintenance logs

3. **Timeline Matching**: Align phase/milestone language
   - Phase completion → Phase reports
   - Monthly tasks → Monthly deliverables
   - Quarterly reviews → Quarterly reports

### Confidence Thresholds

- **HIGH (>0.90)**: Explicit CDRL/deliverable reference in SOW text
- **MEDIUM (0.65-0.90)**: Strong work-product semantic match
- **LOW (0.50-0.65)**: Weak temporal/topical alignment

### Output Format

```json
{
  "source_id": "statement_of_work_entity_id",
  "target_id": "deliverable_entity_id",
  "relationship_type": "PRODUCES",
  "confidence": 0.50-0.96,
  "reasoning": "Work statement explicitly references or semantically produces deliverable"
}
```

---

## UCF vs Non-UCF Examples

### UCF Structure Example

**Section C (PWS)**: "Contractor shall maintain facility infrastructure per Attachment J-02"  
**Section J (CDRL)**: "CDRL B012 - Facility Maintenance Logs (monthly)"  
**Section M (Eval)**: "Past performance maintaining similar facilities will be evaluated"

**Relationships Created**:

1. REQUIREMENT "maintain facility infrastructure" --SATISFIED_BY--> DELIVERABLE "Facility Maintenance Logs"
2. STATEMENT_OF_WORK "PWS Section 3.2" --PRODUCES--> DELIVERABLE "Facility Maintenance Logs" (if explicit CDRL reference exists)

### FAR 16 Task Order Example (Non-UCF)

**Work Description**: "ISS housekeeping services shall maintain cleanliness standards per SOW 3.1"  
**Deliverable**: "Daily Service Logs" (embedded in eval criteria, not separate CDRL)  
**Evaluation Criterion**: "Quality of service delivery demonstrated through documentation"

**Relationships Created**:

1. REQUIREMENT "maintain cleanliness standards" --SATISFIED_BY--> DELIVERABLE "Daily Service Logs"
2. No SOW→Deliverable link (no explicit CDRL reference in work text)

---

## Special Cases

### Deliverables Without Work Statements

Many deliverables come from CDRLs, clauses, or eval criteria WITHOUT corresponding SOW tasks:

- **CDRL-only deliverables**: Required by contract but not mentioned in SOW
- **Clause-mandated deliverables**: FAR/DFARS requirements (e.g., SF 1449, DD 254)
- **Proof point deliverables**: Listed in Section M for evaluation purposes

**Solution**: Use Pattern 1 (requirement→deliverable) to capture these. They still satisfy requirements even if not mentioned in SOW.

### Multi-Source Deliverables

One deliverable may relate to multiple requirements AND multiple work statements:

- Create separate relationships for each
- Example: "Monthly Status Report" satisfies "reporting requirements" AND produced by "project management tasks"

### Deliverable Hierarchy

Some deliverables are composites:

- Parent SOW → Summary deliverables
- Sub-tasks → Detailed deliverables
- Preserve hierarchical relationships with appropriate confidence scores

---

## Processing Strategy

1. **Start with Pattern 1** (requirement→deliverable): Captures 60-80% of deliverables
2. **Add Pattern 2** (SOW→deliverable): Captures explicit work planning references (20-40%)
3. **Avoid duplicates**: If same relationship exists in both patterns, keep higher confidence score
4. **Prioritize evidence**: Pattern 1 relationships are more valuable for compliance traceability

---

## Examples Combined

```json
[
  {
    "source_id": "req_security_123",
    "target_id": "deliv_ssp_456",
    "relationship_type": "SATISFIED_BY",
    "confidence": 0.92,
    "reasoning": "System Security Plan deliverable provides evidence of NIST 800-171 compliance requirement satisfaction."
  },
  {
    "source_id": "sow_section_789",
    "target_id": "deliv_status_101",
    "relationship_type": "PRODUCES",
    "confidence": 0.94,
    "reasoning": "SOW Section 3.4 explicitly references CDRL A001 Monthly Status Report as required deliverable."
  },
  {
    "source_id": "req_uptime_234",
    "target_id": "deliv_uptime_567",
    "relationship_type": "SATISFIED_BY",
    "confidence": 0.88,
    "reasoning": "Monthly Uptime Report (CDRL B003) provides performance evidence for 99.9% availability requirement."
  }
]
```

---

## Quality Checks

- ✅ Both relationship types preserve different semantic meanings
- ✅ Pattern 1 handles CDRL-only deliverables (majority case)
- ✅ Pattern 2 handles explicit SOW references (work planning)
- ✅ No artificial relationships created (require semantic justification)
- ✅ Confidence scores reflect evidence strength
- ✅ Works for both UCF and non-UCF structures
