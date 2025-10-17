# Work to Deliverables: STATEMENT_OF_WORK → DELIVERABLE

**Purpose**: Link work statements (SOW/PWS/SOO) to contract deliverables  
**Relationship Type**: PRODUCES (directional)  
**Pattern**: Task→deliverable mentions, work-product mapping, timeline alignment  
**Last Updated**: October 10, 2025 (Branch 005 - MinerU Optimization)

---

## Context

Statement of Work (SOW), Performance Work Statement (PWS), and Statement of Objectives (SOO) define tasks/objectives that produce specific deliverables. These work statements may appear in Section C (inline), as attachments (Section J), or in technical annexes.

**Location Variability**: SOW/PWS/SOO content location varies by agency and RFP structure:

- **Section C**: Traditional inline SOW
- **Attachment**: Separate PWS document (common in DoD - e.g., "J-02000000 PWS")
- **Section H**: Special requirements that define work scope
- **Technical Annexes**: Detailed task descriptions in appendices

Understanding these relationships enables work planning and CDRL mapping regardless of document location.

## SOW Type Variations

### SOW (Prescriptive)

- **Definition**: Detailed task descriptions with specific methods
- **Example**: "Conduct weekly system backups using approved tools"
- **Deliverable**: Backup logs, compliance reports

### PWS (Performance-Based)

- **Definition**: Performance objectives without prescribing methods
- **Example**: "Maintain 99.9% system uptime"
- **Deliverable**: Uptime reports, SLA compliance metrics

### SOO (Objective-Based)

- **Definition**: High-level mission objectives
- **Example**: "Enhance cybersecurity posture"
- **Deliverable**: Security assessment reports, remediation plans

## Common Patterns

### Explicit Task→Deliverable Mentions

- **Work Statement**: "Prepare monthly status reports..." (may be in Section C, attachment, or Section H)
- **Deliverable**: "CDRL A001 - Monthly Status Report"
- **Relationship**: Direct text reference
- **Location-agnostic**: Works regardless of where work statement appears

### Work-Product Mapping

- **PWS**: "Maintain facility infrastructure..."
- **Deliverable**: "Maintenance logs, inspection reports"
- **Relationship**: Implied work products

### Timeline Alignment

- **SOO**: "Complete Phase 1 objectives by Q2..."
- **Deliverable**: "Phase 1 Summary Report (due June 30)"
- **Relationship**: Temporal correlation

## Detection Rules

1. **Direct References**: Search for deliverable names/IDs in work statement text

   - CDRL numbers (A001, B002)
   - Report names (Status Report, Technical Manual)
   - Works across Section C, attachments, and Section H content

2. **Semantic Overlap**: Match work scope to deliverable descriptions

   - Task keywords → Deliverable type
   - Example: "testing" → "Test Report"

3. **Timeline Correlation**: Match milestones to deliverable due dates
   - Phase completion → Phase report
   - Monthly tasks → Monthly deliverables

## Confidence Thresholds

- **HIGH (>0.8)**: Explicit CDRL reference in SOW text
- **MEDIUM (0.5-0.8)**: Strong semantic overlap + terminology match
- **LOW (0.3-0.5)**: Weak topic alignment only

## Output Format

Each relationship must include:

- `source_id`: STATEMENT_OF_WORK entity ID
- `target_id`: DELIVERABLE entity ID
- `relationship_type`: "PRODUCES"
- `confidence`: Float 0.0-1.0
- `reasoning`: Explanation (1-2 sentences)

## Examples

```json
[
  {
    "source_id": "sow_123",
    "target_id": "deliverable_456",
    "relationship_type": "PRODUCES",
    "confidence": 0.96,
    "reasoning": "Performance Work Statement explicitly references CDRL A001 Monthly Status Report as required deliverable."
  },
  {
    "source_id": "sow_789",
    "target_id": "deliverable_101",
    "relationship_type": "PRODUCES",
    "confidence": 0.74,
    "reasoning": "Facility maintenance tasks semantically align with Maintenance Log deliverable (CDRL B003)."
  }
]
```

## Special Cases

### Multi-Deliverable Tasks

- One SOW section may produce multiple deliverables
- Example: "System testing" → Test Plan + Test Report + Test Data
- Create separate relationships for each

### Deliverable Hierarchy

- Parent SOW → Summary deliverables
- Sub-tasks → Detailed deliverables
- Preserve hierarchical relationships

### CDRL Cross-References

- Look for Contract Data Requirements List (CDRL) item numbers
- Pattern: `CDRL [A-Z]\d{3}`
- High confidence when matched
