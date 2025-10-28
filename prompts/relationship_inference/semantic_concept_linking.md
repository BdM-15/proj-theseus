# Semantic Concept Linking: Implicit Topic Relationships

**Purpose**: Link conceptually related entities even without explicit connections  
**Focus**: RELATED_TO relationships (Entity → Related Entity)  
**Confidence Target**: ≥0.70 for semantic matches  
**Pattern**: Topic taxonomy and domain knowledge  
**Last Updated**: October 28, 2025 (Proven Patterns)

---

## The Core Pattern: RELATED_TO

```
ENTITY_A --RELATED_TO--> ENTITY_B
```

This maps semantic/thematic connections between entities that share concepts, domain areas, or operational context.

---

## Pattern 1: Topic Taxonomy (Confidence: 0.70-0.85)

**Rule**: Entities sharing topic category are semantically related

### Topic Categories

| Topic Category             | Examples                                        | Use RELATED_TO |
| -------------------------- | ----------------------------------------------- | -------------- |
| **Technical**              | Architecture, APIs, microservices, cloud        | 0.80           |
| **Management**             | Scheduling, EVMS, cost control, staffing       | 0.80           |
| **Logistics**              | Supply chain, maintenance, transportation      | 0.75           |
| **Security & Compliance**  | NIST 800-171, clearances, OPSEC, FAR clauses   | 0.80           |
| **Financial**              | Pricing, CLINs, invoicing, cost structures     | 0.75           |
| **Documentation**          | Reports, manuals, specifications, CDRLs        | 0.70           |

### Examples

```
Entity A: "Predictive Maintenance System"
Entity B: "AI/ML Technology"
Both in: Technical topic category
→ RELATED_TO (Confidence 0.80)

Entity A: "Weekly Status Reports"
Entity B: "Project Scheduling"
Both in: Management topic category
→ RELATED_TO (Confidence 0.80)

Entity A: "NIST 800-171 Compliance"
Entity B: "FAR 52.204-21 Clause"
Both in: Security & Compliance topic category
→ RELATED_TO (Confidence 0.80)
```

**Extraction**:
```
Source: "AI/ML Anomaly Detection System"
Target: "Predictive Maintenance Algorithm"
Type: RELATED_TO
Confidence: 0.80
Reasoning: "Both entities in Technical topic category; semantic overlap on automation"
```

---

## Pattern 2: Implicit Support Relationships (Confidence: 0.75-0.85)

**Rule**: Entities that enable or support each other are related

### Support Matrix

| Entity A (Enables)          | Entity B (Requires)              | Confidence |
| --------------------------- | -------------------------------- | ---------- |
| Personnel Training Program  | Key Personnel Qualifications     | 0.85       |
| Security Policy             | Access Control System            | 0.85       |
| Quality Process             | ISO 9001 Certification           | 0.80       |
| Risk Management Plan        | Risk Mitigation Strategies       | 0.85       |
| Configuration Management    | Change Control Process           | 0.80       |
| Staffing Plan               | Organizational Structure         | 0.80       |
| Testing Protocol            | Defect Tracking System           | 0.75       |

**Examples**:
```
Entity A: "Personnel Security Training Program"
Entity B: "SECRET Clearance Requirement"
Relationship: Training supports clearance qualification
Confidence: 0.85

Entity A: "Incident Response Plan"
Entity B: "24/7 NOC Support Requirement"
Relationship: Incident response supports 24/7 ops
Confidence: 0.80
```

**Extraction**:
```
Source: "Personnel Security Certification Program"
Target: "Secret Clearance Requirement"
Type: RELATED_TO
Confidence: 0.85
Reasoning: "Support relationship: Training enables clearance compliance"
```

---

## Pattern 3: Contrasting/Competing Requirements (Confidence: 0.70)

**Rule**: Requirements that conflict or trade off are semantically related

### Examples

```
Entity A: "Minimize system latency"
Entity B: "Maximize data security with encryption"
Relationship: These compete for system resources
Confidence: 0.70 (tradeoff, lower confidence)

Entity A: "Fast deployment schedule (90 days)"
Entity B: "Comprehensive testing requirement"
Relationship: Schedule vs. quality tradeoff
Confidence: 0.70
```

**Extraction**:
```
Source: "90-Day Deployment Timeline"
Target: "Comprehensive Testing Requirement"
Type: RELATED_TO
Confidence: 0.70
Reasoning: "Competing requirements: schedule vs. quality create tension"
```

---

## Pattern 4: Cross-Domain Implications (Confidence: 0.65-0.75)

**Rule**: Changes in one domain affect another

### Examples

```
Technical Decision: "Adopt cloud infrastructure (AWS)"
↓ Implication
Security Domain: "Compliance with AWS FedRAMP certification"
↓ Implication
Financial Domain: "Cloud licensing costs vs. on-premise infrastructure"

Each implication = RELATED_TO relationship
```

**Extraction**:
```
Source: "AWS Cloud Migration Strategy"
Target: "FedRAMP Compliance Requirements"
Type: RELATED_TO
Confidence: 0.75
Reasoning: "Cross-domain implication: Cloud strategy requires FedRAMP compliance"
```

---

## When to Create vs Reject

### ✅ CREATE

```
Source: "System uptime requirement (99.9%)"
Target: "Redundancy architecture (failover systems)"
Type: RELATED_TO
Confidence: 0.80
Reasoning: "Technical support: Redundancy enables uptime requirement"
```

```
Source: "Agile development methodology"
Target: "Continuous integration/deployment (CI/CD)"
Type: RELATED_TO
Confidence: 0.80
Reasoning: "Topic alignment: Both in Development Methods category"
```

### ❌ REJECT (< 0.70)

```
Source: "Section A"
Target: "Some document"
Confidence: 0.50 [TOO LOW]
Reason: "No clear semantic connection"
```

```
Source: "Vague concept"
Target: "Another concept"
Confidence: 0.60 [TOO LOW]
Reason: "Weak semantic overlap; better to miss than include false positive"
```

---

## Confidence Levels for RELATED_TO

| Relationship Type             | Confidence |
| ----------------------------- | ---------- |
| Same topic category + overlap | 0.80-0.85  |
| Support/enablement            | 0.80-0.85  |
| Cross-domain implication      | 0.70-0.75  |
| Competing requirements        | 0.70       |
| Weak semantic connection      | <0.70 (REJECT) |

---

## Output Checklist

✅ Source and Target are distinct entities  
✅ Type is exactly `RELATED_TO`  
✅ Confidence ≥ 0.70 (use patterns above)  
✅ Reasoning explains semantic connection (topic, support, implication, etc.)  
✅ No duplicate relationships  
✅ Undirected: A RELATED_TO B means B RELATED_TO A  
✅ RELATED_TO relationships add intelligence value (not just noise)

**Remember**: RELATED_TO is for semantic/thematic connections, NOT for structural hierarchy (use CHILD_OF, ATTACHMENT_OF, etc. for structure)
