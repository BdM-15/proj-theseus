# SOW-Deliverable Linking: Work Statement to Deliverable Mapping

**Purpose**: Link Statement of Work (SOW) tasks to their corresponding deliverables  
**Focus**: PRODUCES relationships (SOW Task → Deliverable)  
**Confidence Target**: ≥0.80 for all relationships  
**Pattern**: CDRL cross-references and task content matching  
**Last Updated**: October 28, 2025 (Proven Patterns)

---

## The Core Pattern: PRODUCES

```
SOW_TASK --PRODUCES--> DELIVERABLE
```

This maps what work is done (SOW) to what is delivered (CDRL/deliverables).

---

## Pattern 1: Explicit CDRL Reference (Confidence: 0.98)

**Rule**: SOW explicitly references CDRL item number

### Examples

```
"Section 2.3 AI Model Development. Deliverable: CDRL A001 - AI Model Package"
→ PRODUCES (Confidence 0.98)

"Task 4.2 Testing Phase produces: CDRL B003 - Test Report and Metrics"
→ PRODUCES (Confidence 0.98)

"Performance testing (Section 3.1) results in: CDRL C001 Performance Data"
→ PRODUCES (Confidence 0.98)
```

**Extraction**:
```
Source: "Section 2.3 AI Model Development"
Target: "CDRL A001: AI Model Package"
Type: PRODUCES
Confidence: 0.98
Reasoning: "Explicit: 'Deliverable: CDRL A001 - AI Model Package'"
```

---

## Pattern 2: Task-to-Deliverable Content Matching (Confidence: 0.85-0.90)

**Rule**: SOW task content matches deliverable description

### Task-Deliverable Mapping Table

| SOW Task Type              | Typical Deliverable         | Confidence |
| -------------------------- | --------------------------- | ---------- |
| Design phase               | Design Document (CDRL)      | 0.90       |
| Testing/QA phase           | Test Report + Metrics       | 0.90       |
| Implementation phase       | Software Build (code/docs)  | 0.90       |
| Documentation              | Technical Manual/Guide      | 0.90       |
| Training delivery          | Training Materials + Results | 0.85       |
| Status reporting           | Monthly/Weekly Reports      | 0.90       |
| Maintenance support        | Support Logs/Metrics        | 0.85       |
| Integration testing        | Integration Test Report     | 0.90       |
| Risk management            | Risk Register + Mitigation  | 0.85       |

### Examples

```
SOW Task: "Phase 1: Design system architecture"
Deliverable: "Design Document (CDRL A002)"
Content match: Architecture design → design document
Confidence: 0.90

SOW Task: "Conduct system testing and validation"
Deliverable: "Test Report with Metrics (CDRL B001)"
Content match: Testing activity → test deliverable
Confidence: 0.90
```

**Extraction**:
```
Source: "Phase 1: Design System Architecture"
Target: "CDRL A002: System Design Document"
Type: PRODUCES
Confidence: 0.90
Reasoning: "Content match: Design activity produces design document"
```

---

## Pattern 3: Temporal/Sequential Correlation (Confidence: 0.75-0.80)

**Rule**: SOW task occurs before and likely produces nearby deliverable

### Examples

```
SOW Section 2.1 (Months 1-2): Requirements Analysis
CDRL Due Month 3: Requirements Document (CDRL A001)
Temporal signal: Analysis → Document delivery 1 month later
Confidence: 0.80

SOW Section 3.2 (Months 3-5): Integration Testing
CDRL Due Month 6: Integration Test Report (CDRL B001)
Temporal signal: Testing → Report delivery 1 month after testing
Confidence: 0.75
```

**Extraction**:
```
Source: "Requirements Analysis (Months 1-2)"
Target: "Requirements Document (CDRL A001, Due Month 3)"
Type: PRODUCES
Confidence: 0.80
Reasoning: "Temporal correlation: Analysis work concludes, document delivered 1 month later"
```

---

## Pattern 4: Recurring/Periodic Deliverables (Confidence: 0.90)

**Rule**: Recurring SOW activities produce recurring deliverables

### Examples

```
SOW: "Ongoing weekly status meetings and reporting"
Deliverable: "Weekly Status Reports (CDRL C001, recurring)"
Confidence: 0.95 (explicit recurring connection)

SOW: "Monthly performance reviews and optimization"
Deliverable: "Monthly Performance Report (CDRL D001, recurring)"
Confidence: 0.90
```

**Extraction**:
```
Source: "Ongoing Monthly Performance Reviews"
Target: "Monthly Performance Report (CDRL D001)"
Type: PRODUCES
Confidence: 0.90
Reasoning: "Recurring SOW activity produces recurring monthly deliverable"
```

---

## Special Cases: Multiple Deliverables from One Task

### Rule: One SOW task may produce multiple deliverables

```
SOW Task: "System Testing and Quality Assurance"
Deliverable 1: "Test Plan (CDRL B001)"
Deliverable 2: "Test Results (CDRL B002)"
Deliverable 3: "Defect Report (CDRL B003)"

Extract MULTIPLE relationships:
```

**Extraction**:
```
Source: "System Testing and Quality Assurance (Section 3.0)"

Target 1: "Test Plan (CDRL B001)"
Type: PRODUCES
Confidence: 0.95

Target 2: "Test Results (CDRL B002)"
Type: PRODUCES
Confidence: 0.95

Target 3: "Defect Report (CDRL B003)"
Type: PRODUCES
Confidence: 0.90
```

---

## When to Create vs Reject

### ✅ CREATE

```
Source: "Section 2.3: AI Model Development"
Target: "CDRL A001: AI Model Package + Training Data"
Type: PRODUCES
Confidence: 0.98
Reasoning: "Explicit CDRL reference: 'Deliverable: CDRL A001'"
```

```
Source: "Phase 2: Integration Testing (Months 3-4)"
Target: "Integration Test Report (CDRL B002, Due Month 5)"
Type: PRODUCES
Confidence: 0.85
Reasoning: "Content match + temporal correlation: Testing produces report 1 month after completion"
```

### ❌ REJECT (< 0.70)

```
Source: "General SOW section"
Target: "Unrelated deliverable"
Confidence: 0.40 [TOO LOW]
Reason: "No clear work-to-deliverable connection"
```

```
Source: "Background/context information"
Target: "Deliverable"
Confidence: 0.50 [TOO LOW]
Reason: "Background information doesn't produce formal deliverables"
```

---

## Output Checklist

✅ Source is a STATEMENT_OF_WORK (or SOW task entity)  
✅ Target is a DELIVERABLE entity  
✅ Type is exactly `PRODUCES`  
✅ Confidence ≥ 0.70 (use patterns above)  
✅ Reasoning explains which pattern was used  
✅ Multiple deliverables per task handled correctly (separate relationships)  
✅ Recurring deliverables properly identified  
✅ No duplicate relationships  
✅ Directional: SOW Task → Deliverable (not reversed)

**Remember**: Every CDRL deliverable should be traced back to at least one SOW task (shows full traceability)
