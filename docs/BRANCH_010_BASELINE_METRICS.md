# Branch 010 Baseline Metrics - MCPP II RFP Knowledge Graph

**RFP**: M6700425R0007 MCPP II DRAFT RFP 23 MAY 25  
**Processing Date**: Branch 010 (merged to main)  
**Extraction Prompts Used**:

- `entity_extraction_prompt.md` (~1,450 lines)
- `entity_detection_rules.md` (~1,155 lines)
- **Total**: ~2,605 lines of extraction guidance

**No domain enhancement libraries** - this is the baseline before FAR/DFARS, Agency, or Proposal intelligence integration.

---

## Graph Structure Metrics

| Metric                   | Value  | Notes                                   |
| ------------------------ | ------ | --------------------------------------- |
| **Total Entities**       | 4,793  | Nodes in knowledge graph                |
| **Total Relationships**  | 5,932  | Edges connecting entities               |
| **Graph Density**        | 0.0005 | Sparse graph (normal for RFP documents) |
| **Connected Components** | 1,622  | Number of disconnected subgraphs        |
| **Average Node Degree**  | 2.48   | Average connections per entity          |
| **Max Node Degree**      | 1,120  | MCMC organization (most connected)      |
| **Min Node Degree**      | 0      | Isolated entities with no relationships |

---

## Entity Type Distribution

| Entity Type                | Count | Percentage | Notes                              |
| -------------------------- | ----- | ---------- | ---------------------------------- |
| **concept**                | 978   | 20.40%     | Abstract ideas, technical concepts |
| **document**               | 854   | 17.82%     | Referenced documents, attachments  |
| **deliverable**            | 522   | 10.89%     | CDRLs, reports, work products      |
| **organization**           | 338   | 7.05%      | Contractors, agencies, departments |
| **equipment**              | 337   | 7.03%      | Physical items, systems            |
| **program**                | 314   | 6.55%      | Programs like MCPP II              |
| **section**                | 308   | 6.43%      | RFP sections (UCF structure)       |
| **requirement**            | 302   | 6.30%      | Must/shall obligations             |
| **technology**             | 209   | 4.36%      | IT systems, technical platforms    |
| **clause**                 | 208   | 4.34%      | FAR/DFARS/NMCARS clauses           |
| **person**                 | 88    | 1.84%      | POCs, contracting officers         |
| **evaluation_factor**      | 83    | 1.73%      | Section M evaluation criteria      |
| **location**               | 80    | 1.67%      | Geographies, facilities            |
| **submission_instruction** | 74    | 1.54%      | Section L format requirements      |
| **event**                  | 43    | 0.90%      | Deadlines, milestones              |
| **strategic_theme**        | 26    | 0.54%      | Win themes, key messages           |
| **statement_of_work**      | 15    | 0.31%      | SOW/PWS documents                  |
| **unknown**                | 12    | 0.25%      | Unclassified entities              |
| **contract**               | 2     | 0.04%      | Contract vehicles                  |

**Total**: 4,793 entities across 19 types

---

## Top 20 Relationship Types

| Relationship Type                              | Count | Percentage | Notes                           |
| ---------------------------------------------- | ----- | ---------- | ------------------------------- |
| **belongs_to, contained_in, part_of**          | 1,338 | 22.56%     | Hierarchical relationships      |
| **CHILD_OF**                                   | 925   | 15.59%     | Parent-child structure          |
| **#\|IAW**                                     | 54    | 0.91%      | "In accordance with" compliance |
| **EVALUATED_BY**                               | 34    | 0.57%      | Requirement→Factor linking      |
| **GUIDES**                                     | 22    | 0.37%      | Instruction→Evaluation linking  |
| **grade classification, wage association**     | 22    | 0.37%      | Labor category relationships    |
| **governance, requirement**                    | 21    | 0.35%      | Regulatory relationships        |
| **classification, listing**                    | 21    | 0.35%      | Categorization                  |
| **#\|per**                                     | 20    | 0.34%      | "Per specification" references  |
| **deadline compliance, reporting requirement** | 20    | 0.34%      | Temporal obligations            |
| **compliance, timeline**                       | 20    | 0.34%      | Schedule constraints            |
| **categorization, inclusion**                  | 20    | 0.34%      | Grouping relationships          |
| **association, task grouping**                 | 15    | 0.25%      | Task clustering                 |
| **PRODUCES**                                   | 14    | 0.24%      | Output generation               |
| **REFERENCES**                                 | 12    | 0.20%      | Cross-references                |
| **role mapping, wage assignment**              | 12    | 0.20%      | Labor role definitions          |
| **governs, requirement**                       | 11    | 0.19%      | Governing constraints           |
| **#\|use**                                     | 9     | 0.15%      | Usage specifications            |
| **frequency assignment, submission timing**    | 9     | 0.15%      | Temporal patterns               |
| **LMC**                                        | 9     | 0.15%      | Lifecycle Management Code       |

**Remaining 3,262 relationships**: Distributed across hundreds of other types

---

## Entity Description Quality

| Metric                            | Value         | Notes                                    |
| --------------------------------- | ------------- | ---------------------------------------- |
| **Entities with descriptions**    | 4,781 (99.7%) | Nearly all entities have context         |
| **Entities without descriptions** | 12 (0.3%)     | Minimal missing descriptions             |
| **Average description length**    | 134.7 chars   | Good contextual detail                   |
| **Median description length**     | 102.0 chars   | Typical entity has ~100 char description |
| **Min description length**        | 12 chars      | Shortest description                     |
| **Max description length**        | 3,467 chars   | MCMC organization (most detailed)        |

---

## Relationship Description Quality

| Metric                                 | Value          | Notes                               |
| -------------------------------------- | -------------- | ----------------------------------- |
| **Relationships with descriptions**    | 5,932 (100.0%) | All relationships have context      |
| **Relationships without descriptions** | 0 (0.0%)       | Complete relationship documentation |
| **Average description length**         | 96.0 chars     | Concise but informative             |
| **Median description length**          | 92.0 chars     | Typical relationship ~90 chars      |
| **Min description length**             | 12 chars       | Shortest relationship description   |
| **Max description length**             | 1,806 chars    | Most detailed relationship          |

---

## Top 10 Most Connected Entities

| Entity                                  | Type              | Connections | Description (first 60 chars)                                    |
| --------------------------------------- | ----------------- | ----------- | --------------------------------------------------------------- |
| **MCMC**                                | organization      | 1,120       | The Marine Corps Maintenance Contractor (MCMC) is a key cont... |
| **Section J**                           | section           | 463         | Section J includes CDRLs, referenced in CLIN X0007...           |
| **Section I**                           | section           | 192         | Section I of Past Performance Questionnaire is completed by...  |
| **Section L**                           | section           | 98          | Section L is INSTRUCTIONS, CONDITIONS, AND NOTICES TO OFFERO... |
| **Section M-4**                         | section           | 82          | Section M-4 of the RFP applies adjectival ratings to Factors... |
| **NAV-P**                               | organization      | 76          | NAV-P, the Navy Prepositioning Department, serves as a key g... |
| **Federal Equivalent Wage Rates Table** | clause            | 67          | This table lists job classes (e.g., mechanics, technicians)...  |
| **Past Performance**                    | evaluation_factor | 58          | Past Performance is assessed for relevance, recency, and qua... |
| **Government**                          | organization      | 56          | The Government, particularly the United States Government an... |
| **MCPP II CLIN X002/X003 Deliverables** | deliverable       | 54          | This table details 33 required reports and deliverables...      |

---

## Sample Rich Entity Descriptions

### 1. MCMC (organization) - 3,467 chars

```
The Marine Corps Maintenance Contractor (MCMC) is a key contracting entity responsible for
a wide array of maintenance, logistics, and support services for the Marine Corps
Prepositioning Program (MCPP). The MCMC supports critical operations across multiple global
locations, including MCPP-Norway, MCPP-PHIL (Philippines), and other prepositioning sites,
ensuring that equipment and systems are mission-ready at all times...
```

### 2. MCPP-PHIL (location) - 2,137 chars

```
The Marine Corps Prepositioning Program - Philippines (MCPP-PHIL) is a land-based
prepositioning initiative established in Subic Bay, Philippines, designed to support rapid
deployment capabilities for Marine Corps operations in the Indo-Pacific region. The program
maintains critical equipment sets, vehicles, and supplies in a state of high readiness...
```

### 3. Contracting Officer (person) - 2,066 chars

```
The Contracting Officer is an authorized official responsible for overseeing and managing
various aspects of government contracts, ensuring compliance with federal acquisition
regulations (FAR), Defense Federal Acquisition Regulation Supplement (DFARS), and agency-
specific requirements...
```

---

## Key Observations (Baseline Quality)

### Strengths

✅ **High entity coverage** - 4,793 entities extracted from 71-page RFP  
✅ **Nearly universal descriptions** - 99.7% of entities have contextual descriptions  
✅ **100% relationship documentation** - All relationships include descriptive context  
✅ **Good description depth** - Average 134.7 chars per entity provides meaningful context  
✅ **Strong structural detection** - UCF sections (L, M, I, J) correctly identified and highly connected  
✅ **Proper entity typing** - 19 distinct entity types with reasonable distribution

### Potential Weaknesses (Areas for Enhancement)

⚠️ **Low EVALUATED_BY coverage** - Only 34 relationships (0.57%) link requirements to evaluation factors  
⚠️ **Low GUIDES coverage** - Only 22 relationships (0.37%) link Section L to Section M  
⚠️ **Sparse FAR/DFARS intelligence** - 208 clauses extracted but limited operational context  
⚠️ **Limited evaluation factor richness** - Only 83 evaluation factors (1.73% of entities)  
⚠️ **Missing agency patterns** - No explicit DoD vs civilian scoring methodology recognition  
⚠️ **No win theme extraction** - Only 26 strategic themes (0.54% of entities)  
⚠️ **Fragmented graph** - 1,622 connected components suggests missing relationships

---

## Comparison Points for Option A Testing

When testing with enhanced extraction prompts (Option A - lean domain guidance), measure:

### Quantitative Metrics

- [ ] Total entities (target: maintain or increase from 4,793)
- [ ] Total relationships (target: maintain or increase from 5,932)
- [ ] EVALUATED_BY relationships (target: increase from 34)
- [ ] GUIDES relationships (target: increase from 22)
- [ ] Evaluation factor entities (target: increase from 83)
- [ ] Strategic theme entities (target: increase from 26)
- [ ] Average entity description length (target: maintain or increase from 134.7 chars)
- [ ] Connected components (target: decrease from 1,622 - better connectivity)

### Qualitative Metrics

- [ ] FAR/DFARS clauses have operational context (deadline implications, flowdown, cost impact)
- [ ] Evaluation factors include scoring methodology patterns (adjectival vs numerical)
- [ ] Agency-specific patterns recognized (DoD vs civilian tendencies)
- [ ] Win themes extracted with FAB framework (Feature-Advantage-Benefit)
- [ ] Section L↔M relationships more comprehensive (instruction→evaluation linkage)
- [ ] Requirement→Factor mapping improved (SOW obligations → scoring criteria)

---

## Processing Performance (Branch 010 Baseline)

**Estimated metrics** (user-reported for MCPP RFP):

- Processing time: ~45 minutes
- Processing cost: $0.65 - $1.00
- Extraction prompts: 2,605 lines (entity_extraction_prompt + entity_detection_rules)

**Note**: Option A will add ~2,000 lines of domain guidance (FAR/DFARS, Agency, Proposal intelligence), representing ~77% increase in prompt size but only ~3% of 2M context window.

---

**Next Step**: Process same MCPP RFP with Option A (lean domain extraction prompts) and compare metrics.

**Version**: 1.0  
**Date**: January 26, 2025  
**Branch**: 010 baseline (merged to main)
