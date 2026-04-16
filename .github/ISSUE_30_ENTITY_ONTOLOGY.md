# [ENHANCEMENT] Expand Entity Ontology from 18 to 33 Types for Large-Scale RAG

## 📋 Summary

Expand entity ontology from 18 to 33 types to reduce semantic noise in large-scale knowledge graphs (5,000-10,000 entities), improving query precision from 12% to 90% and reducing concept bucket noise from 38.7% to 5%. Includes 12 structural entity types + 3 strategic intelligence types extractable from RFP content.

## 🎯 Motivation

**Problem**: At scale (RFP + attachments + incorporated documents = 2,900 pages), the current 18-entity ontology creates excessive semantic noise:

- **2,800 concept entities** (38.7% of total) become a "catch-all bucket"
- **Query precision**: 12% (e.g., "aircraft maintenance workload" returns 150 concepts, only 15 relevant)
- **VDB false positives**: 68% (semantic search collides between workload forecasts and abstract processes)
- **Manual disambiguation**: Required for 45% of queries

**Solution**: Add 15 specialized entity types that separate:

- Quantitative workload drivers from abstract concepts
- Contract structure (CLINs) from generic deliverables
- Performance standards from requirements
- Regulatory references from contract documents
- **Strategic intelligence (themes, priorities, pain points) from generic concepts**

Plus disambiguation rules and amendment tracking to ensure extraction consistency.

## 🎓 Research Foundation

**Academic Support**:

- CS-KG paper (350M triples): 179 specific semantic relations outperform generic "RELATES_TO"
- Neo4j case studies: Entity specificity reduces large-scale KG noise quadratically
- Enterprise KG best practices: Domain-specific ontologies scale better than general taxonomies

**Key Insight**: Semantic noise grows **quadratically** with corpus size for generic types, but **linearly** for domain-specific types.

## 📊 Expected Outcomes

### Quantitative Metrics

| Metric                    | Baseline (18 types)      | Target (33 types)   | Improvement   |
| ------------------------- | ------------------------ | ------------------- | ------------- |
| **Concept noise**         | 38.7% (2,800 entities)   | <10% (400 entities) | **-86%**      |
| **Query precision**       | 12% avg                  | >90% avg            | **+650%**     |
| **VDB false positives**   | 68%                      | <15%                | **-78%**      |
| **Query response time**   | 2.8s avg                 | <0.5s avg           | **5x faster** |
| **Manual disambiguation** | 45% of queries           | <5% of queries      | **-89%**      |
| **Token budget**          | 35,284 tokens            | <32,000 tokens      | **-9.6%**     |
| **Strategic coverage**    | 0% (no theme extraction) | >85%                | **NEW**       |

### Qualitative Benefits

**10 User Personas Enabled**:

1. **Technical BOE Estimators**: Direct BOE extraction from `workload_metric` entities (not buried in 2,800 concepts)
2. **Proposal Writers**: Automated subfactor outlines from `subfactor` hierarchy (not flat factor list)
3. **Compliance Officers**: Regulatory traceability via `regulatory_reference` (not generic documents)
4. **Capture Managers**: GFE vs contractor clarity via `government_furnished_item` (not mixed equipment)
5. **Pricing Leads**: Cost model inputs from `pricing_element` (not concept extraction)
6. **Transition Managers**: Phase-in Gantt charts from `transition_activity` (not generic events)
7. **Proposal Coordinators**: Volume compliance from `proposal_volume` (not submission instructions)
8. **Technical SMEs**: Spec traceability via `technical_specification` (not 300 mixed documents)
9. **Solution Architects**: Theme-to-requirement mapping via `win_theme` (strategic alignment)
10. **Volume Leads**: Customer priority awareness via `customer_priority` (emphasis targeting)

## 🆕 New Entity Types (15 additions)

### Group A: Contract Structure & Financial (4 types)

1. **`contract_line_item`**: CLINs, SLINs, ACRNs with pricing
   - Captures: CLIN number, contract type (FFP/CPFF/T&M), unit price, PoP, NAICS/PSC
   - Why: Prevents 200+ CLINs from being misclassified as deliverable/concept
   - Query: "What CLINs are driven by Al Dhafra workload?"

2. **`pricing_element`**: Indirect rates, fees, economic adjustments
   - Captures: Rate type, percentage, basis, escalation method
   - Why: Separates 50-100 pricing rules from generic concepts
   - Query: "Extract indirect rates for labor CLINs"

3. **`government_furnished_item`**: GFE, GFP, GFI, GOTS
   - Captures: NSN, CAGE code, quantity, condition, delivery location
   - Why: Clarifies government vs contractor responsibility (500+ items in logistics contracts)
   - Query: "What GFE do I need to provide maintenance for?"

4. **`workload_metric`**: Quantitative BOE drivers
   - Captures: Quantity, unit of measure, time period, metric type, location
   - Why: Separates 320+ forecasts from 2,800 concepts (95% precision vs 10%)
   - Query: "What drives labor FTEs for CLIN 0001?"

### Group B: Requirements & Compliance (3 types)

5. **`performance_standard`**: QASP standards, SLAs, acceptance criteria
   - Captures: Metric name, target, threshold, measurement method, frequency
   - Why: Distinguishes "what to do" (requirement) from "how it's measured" (standard)
   - Query: "Generate QASP table for janitorial services"

6. **`compliance_artifact`**: Certifications, accreditations, security plans
   - Captures: Standard name, certification body, validity period, scope
   - Why: Ongoing compliance vs one-time deliverables (50-100 certs in complex RFPs)
   - Query: "What certifications are required and when do they expire?"

7. **`transition_activity`**: Phase-in/phase-out tasks
   - Captures: Activity type, duration, prerequisites, deliverables, risks
   - Why: 100+ discrete transition tasks over 90-180 days (auto-generate Gantt charts)
   - Query: "Show critical path for phase-in activities"

### Group C: Evaluation & Proposal Structure (2 types)

8. **`proposal_volume`**: Submission volumes
   - Captures: Volume number, page limit, font requirements, due date, factors addressed
   - Why: Structural containers vs formatting instructions (10-15 volumes in large RFPs)
   - Query: "Validate page counts per Section L requirements"

9. **`subfactor`**: Evaluation subfactor hierarchy
   - Captures: Subfactor number, parent factor, weight, evaluation approach
   - Why: 30-100 subfactors lost in flat evaluation_factor list (enables win theme mapping)
   - Query: "Extract subfactors under Technical Factor with weights"

### Group D: Domain References & Standards (3 types)

10. **`regulatory_reference`**: Incorporated regulations (DAFI, MIL-STD, NIST SP)
    - Captures: Document number, revision, incorporating clause, applicability, supersedes
    - Why: 200+ regulatory refs in DoD contracts (DAFI 21-101 = 437 pages)
    - Query: "Which DAFI sections mandate cybersecurity requirements?"

11. **`technical_specification`**: Technical specs, ICDs, drawings
    - Captures: Spec number, version, classification, format, CDRL reference
    - Why: 300+ technical specs in engineering contracts (enables TDP auto-assembly)
    - Query: "Which MIL-DTL specs define connector interfaces?"

12. **`past_performance_reference`**: Evaluation contract references
    - Captures: Contract number, customer POC, dollar value, PoP, relevance, CPARS
    - Why: 10-30 past performance contracts with evaluation context
    - Query: "Show relevant past performance with CPARS ratings"

### Group E: Strategic Intelligence (3 types)

_These entities are extractable FROM RFP content - themes, priorities, and pain points are embedded in solicitation language._

13. **`win_theme`**: Strategic themes revealed in RFP objectives and emphasis
    - Captures: Theme statement, source section, evaluation alignment, supporting requirements
    - Extraction patterns: SOW objectives ("The Government seeks to..."), repeated performance goals, Section M criteria language, background statements
    - Why: Themes are explicitly and implicitly stated throughout RFPs; enables theme-to-requirement traceability
    - Query: "What themes does the Government emphasize and which requirements support them?"
    - **Disambiguation from `concept`**: Must have strategic/evaluative significance AND connect to evaluation criteria; generic process descriptions remain `concept`

14. **`customer_priority`**: Explicit and implicit priority indicators
    - Captures: Priority statement, emphasis level (critical/important/standard), weighting, source section, evaluation impact
    - Extraction patterns: "Critical", "essential", "paramount", "of utmost importance" language; Section M weighting statements; "significantly more important than" phrases; mandatory vs. desirable distinctions
    - Why: Priority indicators guide proposal emphasis and resource allocation; 20-50 priority signals in typical RFP
    - Query: "What does the Government prioritize and how does that affect evaluation?"
    - **Disambiguation from `requirement`**: Priority describes _importance level_, requirement describes _what must be done_; often co-occur but distinct entities

15. **`pain_point`**: Problem statements and deficiencies the Government wants addressed
    - Captures: Problem statement, impact described, implied solution direction, source section, affected requirements
    - Extraction patterns: Background/context sections, "current contract lacks", "deficiencies in", "lessons learned", performance issues cited, "the Government has experienced"
    - Why: Pain points reveal what the customer wants fixed; enables problem→solution traceability; 10-30 pain points in complex RFPs
    - Query: "What problems does the Government want solved and which requirements address them?"
    - **Disambiguation from `requirement`**: Pain point describes _the problem_; requirement describes _the solution_; pain points often appear in background sections, requirements in Section C

---

## 🔀 Entity Disambiguation Rules

**Critical for Extraction Consistency**: These rules prevent the LLM from misclassifying similar content.

### Decision Tree for Ambiguous Content

```
INPUT: "Contractor shall maintain 98% aircraft availability"
│
├─ Has quantitative metric target? (98%)
│   ├─ YES → Is it measuring performance?
│   │         ├─ YES → performance_standard
│   │         └─ NO → Is it a workload quantity?
│   │                  ├─ YES → workload_metric
│   │                  └─ NO → requirement (with metric)
│   └─ NO → Continue below
│
├─ Has "shall" or "must" (obligatory language)?
│   ├─ YES → requirement
│   └─ NO → Continue below
│
├─ Describes a problem/deficiency?
│   ├─ YES → pain_point
│   └─ NO → Continue below
│
├─ Indicates priority/importance level?
│   ├─ YES → customer_priority
│   └─ NO → Continue below
│
├─ States strategic objective/goal?
│   ├─ YES → win_theme
│   └─ NO → concept (fallback)
```

### Disambiguation Matrix

| Ambiguous Pair                          | Distinguishing Rule                                                                      | Example                                                                                          |
| --------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `requirement` vs `performance_standard` | Requirement = what to do ("shall provide"); Standard = how measured ("98% availability") | "Shall provide maintenance" = requirement; "Measured by 98% availability" = performance_standard |
| `requirement` vs `workload_metric`      | Requirement = obligation; Metric = quantity+UOM+period                                   | "Shall process repairs" = requirement; "500 repairs/month" = workload_metric                     |
| `requirement` vs `customer_priority`    | Requirement = action; Priority = importance level                                        | "Shall secure data" = requirement; "Security is paramount" = customer_priority                   |
| `requirement` vs `pain_point`           | Requirement = solution; Pain point = problem                                             | "Shall reduce delays" = requirement; "Current delays impact mission" = pain_point                |
| `compliance_artifact` vs `deliverable`  | Artifact = ongoing certification; Deliverable = one-time submission                      | "Maintain ISO 27001" = compliance_artifact; "Submit security plan" = deliverable                 |
| `regulatory_reference` vs `document`    | Reference = incorporated by citation; Document = attached to RFP                         | "Per DAFI 21-101" = regulatory_reference; "See Attachment J-3" = document                        |
| `workload_metric` vs `concept`          | Metric = quantity+UOM+period; Concept = abstract                                         | "12,500 sorties/year" = workload_metric; "sortie generation process" = concept                   |
| `win_theme` vs `concept`                | Theme = strategic/evaluative significance; Concept = generic description                 | "Maximize readiness" (in objectives) = win_theme; "readiness planning" (in SOW detail) = concept |
| `win_theme` vs `customer_priority`      | Theme = strategic goal; Priority = importance indicator                                  | "Reduce lifecycle cost" = win_theme; "Cost is critical" = customer_priority                      |
| `subfactor` vs `evaluation_factor`      | Subfactor = child of factor with number; Factor = top-level                              | "Technical Approach" = evaluation_factor; "1.2.3 Staffing Plan" = subfactor                      |

### Co-occurrence Rules

Some content generates MULTIPLE entities (not mutually exclusive):

| Content Pattern                                                           | Entities Generated                     | Relationship                                     |
| ------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------ |
| "Contractor shall maintain 98% availability"                              | `requirement` + `performance_standard` | `performance_standard --MEASURES--> requirement` |
| "Security is critical; contractor shall implement Zero Trust"             | `customer_priority` + `requirement`    | `requirement --ADDRESSES--> customer_priority`   |
| "Current delays impact mission; contractor shall reduce turnaround"       | `pain_point` + `requirement`           | `requirement --RESOLVES--> pain_point`           |
| "The Government seeks to maximize readiness through improved maintenance" | `win_theme` + `requirement`            | `requirement --SUPPORTS--> win_theme`            |

---

## 🔄 Amendment Tracking Patterns

**Critical for Proposal Period**: RFPs typically issue 5-15 amendments during the 30-60 day response window.

### New Relationship Types for Amendment Tracking

| Relationship    | Pattern                                      | Purpose                                     |
| --------------- | -------------------------------------------- | ------------------------------------------- |
| `SUPERSEDED_BY` | `requirement --SUPERSEDED_BY--> requirement` | Track requirement changes across amendments |
| `MODIFIED_BY`   | `clause --MODIFIED_BY--> amendment`          | Track clause additions/deletions            |
| `ADDED_IN`      | `requirement --ADDED_IN--> amendment`        | Track new requirements                      |
| `DELETED_IN`    | `requirement --DELETED_IN--> amendment`      | Track removed requirements                  |

### Amendment Entity Extraction

When processing amendments, extract:

- Amendment number and date
- Changed section references
- Nature of change (add/modify/delete)
- Supersession chain

**Query Examples**:

- "Show requirements changed by Amendment 3"
- "What is the current version of Section C.3.2?"
- "List all superseded requirements"

## 🔧 Implementation Plan

**CRITICAL NOTE**: LightRAG uses **native delimiter format** for extraction, NOT Pydantic. The extraction prompt outputs:

```
entity{tuple_delimiter}Entity Name{tuple_delimiter}entity_type{tuple_delimiter}Description
```

Pydantic schemas in `src/ontology/schema.py` are ONLY used for the 8 semantic post-processing algorithms (workload enrichment, requirement evaluation, etc.), not for main extraction.

### Phase 1: Foundation (Week 1, Days 1-2, 8 hours)

**Tasks**:

1. Fix multimodal type conflict (remove table/image/equation from FORBIDDEN)
2. Update `src/ontology/schema.py` (ONLY for post-processing validation):
   - Add 15 types to `EntityType` Literal
   - Add to `VALID_ENTITY_TYPES` set
   - **NO Pydantic model classes needed** (LightRAG uses native delimiter format, not Pydantic)
3. Delete Part A personas from prompt (650 tokens) → move to system context
4. Token compression: Part K examples (delete 7, keep 5)
5. Add disambiguation decision tree to Part D (new section)

**Files Modified**:

- `prompts/extraction/govcon_lightrag_native.txt` (lines 1-80, 631-650, Part K)
- `src/ontology/schema.py` (lines 14-31 ONLY - just update type lists)
- `src/server/initialization.py` (add personas to system prompt)

**IMPORTANT NOTE**: LightRAG extraction uses native delimiters (`<|#|>` tuple_delimiter, `<|COMPLETE|>` completion_delimiter). The `src/ontology/schema.py` Pydantic models are ONLY used for the 8 semantic inference algorithms (post-processing), NOT for main extraction. We only need to update the type lists, not create new model classes.

**Validation**:

- `python -c "from src.ontology.schema import *; print('Schema valid')"`
- Grep for "Part A" in prompt (should be deleted)
- Verify disambiguation decision tree present in Part D

---

### Phase 2: Entity Definitions (Week 1, Days 3-5, 14 hours)

**Tasks**:

1. Add 15 entity definitions to Part D (tabular format, ~3,200 tokens)
2. Add disambiguation matrix to Part D (prevents LLM confusion)
3. Update FALLBACK MAPPING with new type mappings
4. Update existing examples (change concept→workload_metric in Examples 3, 6)
5. Add 5 new comprehensive examples:
   - Example 13: CLIN pricing table extraction
   - Example 14: Regulatory reference incorporation
   - Example 15: Subfactor hierarchy
   - Example 16: Win theme extraction from SOW objectives
   - Example 17: Pain point with linked requirement

**Files Modified**:

- `prompts/extraction/govcon_lightrag_native.txt` (Part D, lines 595-660)
- Examples section (lines 1370-1700)

**Validation**:

- Count entity types in Part D: Should be exactly 33
- Count examples: Should be 10 total (5 core + 5 new)
- Verify disambiguation matrix covers all 10 ambiguous pairs

---

### Phase 3: Relationship Patterns (Week 2, Days 1-3, 14 hours)

**Tasks**:

1. Compress Part F patterns to decision tree format (saves ~3,000 tokens)
2. Add 35 new relationship patterns for new entity types:
   - `contract_line_item --FUNDED_BY--> clause`
   - `workload_metric --QUANTIFIES--> requirement`
   - `performance_standard --MEASURES--> requirement`
   - `regulatory_reference --MANDATES--> requirement`
   - `win_theme --SUPPORTED_BY--> requirement`
   - `customer_priority --ADDRESSED_BY--> requirement`
   - `pain_point --RESOLVED_BY--> requirement`
   - `requirement --SUPERSEDED_BY--> requirement` (amendment tracking)
   - `clause --MODIFIED_BY--> amendment` (amendment tracking)
   - (+ 26 more patterns)
3. Add vertical hierarchy patterns for efficient traversal:
   - `solicitation --> proposal_volume --> evaluation_factor --> subfactor --> requirement --> performance_standard --> workload_metric`
   - `win_theme --> requirement --> deliverable`
   - `pain_point --> requirement --> solution approach`

**Files Modified**:

- `prompts/extraction/govcon_lightrag_native.txt` (Part F, lines 750-1000)

**Validation**:

- Grep for all 35 new relationship types
- Token count Part F: Should be ~4,500 tokens (down from 7,000)
- Verify amendment tracking patterns present
- Verify strategic relationship patterns (SUPPORTS, ADDRESSES, RESOLVES)

---

### Phase 4: Workload Enrichment Extension (Week 2, Days 4-5, 8 hours)

**Tasks**:

1. Extend `workload_enrichment.py` to process 4 entity types (was 1):
   - `requirement` (existing)
   - `workload_metric` (NEW)
   - `contract_line_item` (NEW)
   - `transition_activity` (NEW)
2. Add type-specific enrichment logic
3. Update Pydantic response schema with type validation

**Files Modified**:

- `src/inference/workload_enrichment.py` (lines 116-122, 220+)
- `src/ontology/schema.py` (WorkloadEnrichmentItem class)

**Validation**:

- Check ENRICHABLE_TYPES list has 4 types
- Add debug logging for type-specific enrichment paths

---

### Phase 5: Validation & Testing (Week 3, Days 1-3, 12 hours)

**Tasks**:

1. Create test workspace: `rag_storage/test_30types`
2. Reprocess SWA TAS solicitation (425 pages + appendices)
3. Run entity distribution analysis:
   ```bash
   python tests/validate_entity_distribution.py
   ```
4. Run query precision tests:
   ```bash
   python tests/test_query_precision.py
   ```
5. Validate workload enrichment:
   ```bash
   python tests/validate_workload_enrichment.py
   ```

**New Files Created**:

- `tests/validate_entity_distribution.py`
- `tests/test_query_precision.py`
- `tests/validate_workload_enrichment.py`

**Success Criteria**:

- [ ] Concept entities <15% (target: 7.5%)
- [ ] Average query precision >80% (target: 85%)
- [ ] Workload enrichment applied to all 4 entity types (>95% rate)
- [ ] New entity types present in KG (12 types with >0 entities)

---

### Phase 6: Documentation (Week 3, Days 4-5, 8 hours)

**Tasks**:

1. Update `docs/ARCHITECTURE.md`:
   - Add "30-Entity Ontology for Scale" section
   - Document scale performance metrics
   - Explain workload enrichment extension
2. Update `docs/neo4j/NEO4J_USER_GUIDE.md`:
   - Add query patterns for 12 new entity types
   - Cypher examples for 8 user personas
3. Create migration guide:
   - `docs/MIGRATION_30_ENTITY_TYPES.md`
   - Document 3 migration options (fresh/gradual/none)
   - Rollback procedures
4. Update `README.md`:
   - Add 30-entity ontology feature section
   - Link to migration guide

**Files Modified**:

- `docs/ARCHITECTURE.md` (after line 250)
- `docs/neo4j/NEO4J_USER_GUIDE.md` (new section)
- `README.md` (features section)

**Files Created**:

- `docs/MIGRATION_30_ENTITY_TYPES.md`

---

## 📝 Detailed Task Checklist

### Foundation

- [ ] Remove table/image/equation from FORBIDDEN types (line 631)
- [ ] Add 15 types to EntityType Literal (schema.py line 14)
- [ ] Add 15 types to VALID_ENTITY_TYPES set (schema.py line 21)
- [ ] ~~Create Pydantic model classes~~ **NOT NEEDED** (LightRAG uses native delimiters, not Pydantic)
- [ ] Delete Part A personas (prompt lines 1-80)
- [ ] Move personas to system context (initialization.py line 150)
- [ ] Delete 7 redundant examples (Part K)
- [ ] Add disambiguation decision tree to Part D

### Entity Definitions

- [ ] Add 15 entity definitions in tabular format (Part D)
- [ ] Add disambiguation matrix (10 ambiguous pairs)
- [ ] Add co-occurrence rules (4 patterns)
- [ ] Update FALLBACK MAPPING (line ~647)
- [ ] Update Example 3: concept → workload_metric
- [ ] Update Example 6: concept → workload_metric
- [ ] Add Example 13: CLIN pricing table
- [ ] Add Example 14: Regulatory reference
- [ ] Add Example 15: Subfactor hierarchy
- [ ] Add Example 16: Win theme from SOW objectives
- [ ] Add Example 17: Pain point with linked requirement

### Relationship Patterns

- [ ] Compress Part F to decision tree format (saves 3,000 tokens)
- [ ] Add F.7: Contract structure relationships (4 patterns)
- [ ] Add F.8: Pricing relationships (3 patterns)
- [ ] Add F.9: GFE relationships (4 patterns)
- [ ] Add F.10: Enhanced workload relationships (5 patterns)
- [ ] Add F.11: Performance standard relationships (4 patterns)
- [ ] Add F.12: Compliance artifact relationships (4 patterns)
- [ ] Add F.13: Transition activity relationships (5 patterns)
- [ ] Add F.14: Proposal volume relationships (3 patterns)
- [ ] Add F.15: Subfactor relationships (4 patterns)
- [ ] Add F.16: Regulatory reference relationships (4 patterns)
- [ ] Add F.17: Technical specification relationships (4 patterns)
- [ ] Add F.18: Past performance relationships (4 patterns)
- [ ] Add F.19: Win theme relationships (4 patterns: SUPPORTED_BY, DEMONSTRATED_BY, ALIGNS_WITH, ADDRESSES)
- [ ] Add F.20: Customer priority relationships (3 patterns: EMPHASIZED_IN, ADDRESSED_BY, WEIGHTED_AS)
- [ ] Add F.21: Pain point relationships (3 patterns: RESOLVED_BY, IMPACTS, DESCRIBED_IN)
- [ ] Add F.22: Amendment tracking relationships (4 patterns: SUPERSEDED_BY, MODIFIED_BY, ADDED_IN, DELETED_IN)
- [ ] Add vertical hierarchy patterns (3 traversal chains)

### Workload Enrichment

- [ ] Add ENRICHABLE_TYPES list (workload_enrichment.py line 116)
- [ ] Update entities_to_enrich filter (line 122)
- [ ] Add type-specific enrichment logic (after line 220)
- [ ] Update WorkloadEnrichmentItem schema validation
- [ ] Add debug logging for enrichment paths

### Testing & Validation

- [ ] Create `tests/validate_entity_distribution.py`
- [ ] Create `tests/test_query_precision.py`
- [ ] Create `tests/validate_workload_enrichment.py`
- [ ] Create test workspace `rag_storage/test_30types`
- [ ] Reprocess SWA TAS solicitation
- [ ] Run all 3 validation scripts
- [ ] Verify concept <15%, precision >80%

### Documentation

- [ ] Update `docs/ARCHITECTURE.md` (30-entity section)
- [ ] Update `docs/neo4j/NEO4J_USER_GUIDE.md` (query patterns)
- [ ] Create `docs/MIGRATION_30_ENTITY_TYPES.md`
- [ ] Update `README.md` (features section)
- [ ] Add query examples for 8 personas
- [ ] Document rollback procedures

## 🔄 Backward Compatibility

**Maintained**:

- ✅ All 18 original entity types still valid
- ✅ Existing entity structure unchanged (entity_name, entity_type, description)
- ✅ Existing Cypher queries continue to work
- ✅ API compatibility preserved

**Enhanced** (optional adoption):

- ✅ New relationship types available for precise queries
- ✅ More specific type filtering reduces false positives
- ✅ Workload enrichment on 4 types (was 1)

**Migration Options**:

1. **Fresh Reprocessing**: Delete workspace data, reprocess (full precision)
2. **Gradual Migration**: New documents use 30 types, old keep 18 (mixed precision)
3. **No Migration**: Continue using 18 types (accept 38% concept noise)

See `docs/MIGRATION_30_ENTITY_TYPES.md` for details.

## ⚠️ Risks & Mitigation

| Risk                    | Impact                                | Probability | Mitigation                                                        |
| ----------------------- | ------------------------------------- | ----------- | ----------------------------------------------------------------- |
| Token budget overflow   | Prompt too large for model            | Low         | Aggressive compression (Part F, Part K) - already budgeted to 31K |
| LLM confusion           | Mixing up new similar types           | Medium      | Clear distinction rules, comprehensive examples                   |
| Query regression        | Existing queries return fewer results | Low         | Backward compatibility maintained, 18 original types unchanged    |
| Performance degradation | Slower extraction                     | Low         | More types = more precise = faster queries (offsetting factor)    |
| Migration complexity    | Users struggle with transition        | Medium      | 3 migration paths documented, rollback procedures provided        |

## 🎯 Success Criteria

### Must Have (P0)

- [ ] Concept entities <10% of total (baseline: 38.7%)
- [ ] Query precision >85% average (baseline: 12%)
- [ ] Token budget <32K (baseline: 35K)
- [ ] All 15 new entity types validated in schema
- [ ] Backward compatibility maintained (18 original types work)
- [ ] Disambiguation rules prevent >95% of misclassifications
- [ ] Amendment tracking functional for multi-amendment RFPs

### Should Have (P1)

- [ ] VDB false positives <15% (baseline: 68%)
- [ ] Query response time <0.5s (baseline: 2.8s)
- [ ] Workload enrichment applies to 4 types with >95% coverage
- [ ] All 35 new relationship patterns documented
- [ ] Migration guide completed with 3 options
- [ ] Strategic intelligence extraction >85% coverage (themes, priorities, pain points)
- [ ] Vertical hierarchy queries execute in single traversal

### Nice to Have (P2)

- [ ] 10 comprehensive examples in prompt
- [ ] Query examples for all 10 user personas
- [ ] Automated regression test suite
- [ ] Performance benchmark suite
- [ ] Theme-to-proof-point traceability queries
- [ ] Pain point resolution tracking dashboard

## 📚 References

**Research**:

- CS-KG paper: "Large-Scale Knowledge Graph in Computer Science" (350M triples, 179 semantic relations)
- Neo4j whitepaper: "Building Knowledge Graphs - Practitioner's Guide" (entity specificity at scale)
- Enterprise Knowledge article: "Best Practices for Enterprise Knowledge Graph Design"

**Code Examples**:

- Zep Graphiti: Custom entity type patterns (Pydantic-based)
- Microsoft Graph RAG: Ontology-driven extraction for domain-specific knowledge

**Internal Docs**:

- `docs/ARCHITECTURE.md`: Current 18-entity system
- `docs/inference/SEMANTIC_POST_PROCESSING.md`: Algorithm 7 (workload enrichment)
- `prompts/relationship_inference/workload_enrichment.md`: BOE category definitions

## 👥 Stakeholders

**Primary**: BdM-15 (user), AI agent implementation team  
**Reviewers**: Domain experts (cost estimators, proposal writers, compliance officers, solution architects)  
**Impacted**: All 10 user personas relying on query precision

## 🕐 Timeline

**Estimated Effort**: 55 hours over 3-4 weeks  
**Target Completion**: TBD (user-managed milestone)  
**Critical Path**: Phase 1 → Phase 2 → Phase 3 → Phase 5

**Milestones**:

- Week 1 End: Schema + definitions + disambiguation completed
- Week 2 End: Patterns (including strategic + amendment) completed
- Week 3 End: Enrichment + testing completed
- Week 4 End: Documentation + validation completed

## 📌 Labels

`enhancement` `ontology` `scale` `tech-debt` `priority:high` `effort:large` `complexity:high` `strategic-intelligence`

---

**Issue created**: January 19, 2026  
**Issue updated**: January 29, 2026 (added strategic intelligence types, disambiguation rules, amendment tracking)  
**Estimated scope**: 55 hours  
**Expected impact**: 650% query precision improvement, 86% noise reduction, NEW strategic intelligence extraction

---

## ⚠️ COMMON MISTAKES TO AVOID

1. **DO NOT create Pydantic model classes for new entity types** - LightRAG uses native delimiter format
2. **DO NOT use Pydantic validators in extraction prompt** - Only update type lists in schema.py
3. **DO NOT modify LightRAG's native extraction format** - Keep `entity{tuple_delimiter}...` format
4. **ONLY update**: EntityType Literal + VALID_ENTITY_TYPES set (2 lines in schema.py)
5. **DO NOT confuse entity types** - Use disambiguation rules; when in doubt, extract BOTH and let relationship link them
6. **DO NOT ignore co-occurrence** - Some content generates multiple entities (e.g., requirement + performance_standard)
7. **DO NOT treat strategic types as pre-RFP only** - win_theme, customer_priority, pain_point ARE extractable from RFP text
8. **DO NOT skip amendment tracking** - Multi-amendment RFPs will have stale data without SUPERSEDED_BY relationships
