# Issue #14: Intelligence Inventory for Prompt Consolidation

**Purpose**: Comprehensive catalog of all unique intelligence across extraction prompts for unified prompt creation  
**Date**: December 15, 2025  
**Version**: 1.0  
**Issue**: [GitHub Issue #14 - Holistic Prompt Overhaul](https://github.com/BdM-15/govcon-capture-vibe/issues/14)

---

## Executive Summary

This document catalogs ALL unique intelligence from the current prompt architecture:
- **3 Extraction Prompts**: `grok_json_prompt.md`, `entity_detection_rules.md`, `entity_extraction_prompt.md`
- **13 Relationship Inference Prompts**: `prompts/relationship_inference/*.md`

**Goal**: Create unified `govcon_ontology_v3.txt` that:
1. Preserves 100% of critical intelligence
2. Eliminates redundancy (currently ~40% duplication across files)
3. Moves applicable inference patterns upstream to reduce LLM calls
4. Achieves ~50% token reduction through format optimization (not content removal)

---

## Part 1: Main Extraction Prompts Analysis

### 1.1 grok_json_prompt.md (377 lines, ~5,000 tokens)

#### Unique Critical Content:
| Section | Content | Preservation Priority |
|---------|---------|----------------------|
| PERFORMANCE_METRIC vs REQUIREMENT | Trigger phrases, split rule, QASP tables | **CRITICAL** - #1 extraction error |
| STRATEGIC_THEME Detection | Shipley: hot buttons, discriminators, proof points | **CRITICAL** - Competitive intelligence |
| 18 Entity Type Definitions | Complete type definitions with examples | **CRITICAL** - Single source of truth |
| Domain Rules A-F | Shall/Will, Section L↔M, Workload, Agnostic, Naming, Tables | **CRITICAL** - Core logic |
| JSON Output Instructions | Schema structure, field names, relationship format | **CRITICAL** - Output compliance |

#### Redundancy with Other Files:
- PERF_METRIC vs REQUIREMENT (duplicated in all 3 files)
- Strategic Theme detection (duplicated in entity_detection_rules.md)
- Entity type list (duplicated in entity_extraction_prompt.md)

---

### 1.2 entity_detection_rules.md (1,612 lines, ~18,000 tokens)

#### Unique Critical Content:
| Section | Content | Preservation Priority |
|---------|---------|----------------------|
| Priority Detection: QASP/PO-X | Trigger phrase tables, NOT patterns | **CRITICAL** |
| Strategic Theme Type Classification | ThemeType enum with detection patterns | **CRITICAL** |
| UCF Reference Table | Section A-M mapping with entity types and signals | **HIGH** - Agency-agnostic |
| Non-Standard Label Mapping | FAR 16 Task Order terminology | **HIGH** |
| Content-Based Detection Rules | EVAL_FACTOR, SUBMISSION signals | **HIGH** |
| 17 Entity Type Deep Dives | EVALUATION_FACTOR, SUBMISSION_INSTRUCTION, REQUIREMENT, PROGRAM, STATEMENT_OF_WORK, ANNEX, CLAUSE, SECTION, STRATEGIC_THEME, DELIVERABLE, DOCUMENT, CONCEPT, EQUIPMENT, TECHNOLOGY, ORGANIZATION, EVENT, PERSON/LOCATION | **HIGH** |
| Quality Checks | Validation rules, format validation | **MEDIUM** |

#### Redundancy with Other Files:
- PERF_METRIC trigger phrases (3x duplication)
- Strategic Theme patterns (2x duplication)
- 18 entity types list (3x duplication)
- Criticality detection (MANDATORY/IMPORTANT/OPTIONAL) (2x duplication)

---

### 1.3 entity_extraction_prompt.md (3,304 lines, ~32,000 tokens)

#### Unique Critical Content:
| Section | Content | Preservation Priority |
|---------|---------|----------------------|
| Description Requirements | 20-50 word guidance, good/bad examples | **CRITICAL** |
| Entity Naming Normalization | Section formats, clause formats, CDRL formats, merging | **CRITICAL** |
| Entity Type Rules | 18 types with FORBIDDEN types list | **CRITICAL** |
| Fallback Mapping Table | Ambiguous type → correct type mappings | **HIGH** |
| Domain Knowledge Patterns | FAR/DFARS, CDRL, Shipley, QASP | **HIGH** |
| Decision Tree (8 cases) | Document+SOW, Split rule, Experience, Gov obligations, CDRL dedup, Program vs Equipment, Section H, Exhibits | **CRITICAL** - Edge case handling |
| 5 Annotated RFP Examples | Section L↔M, Requirements with workload, PWS Appendix, Clause extraction, Evaluation criteria | **CRITICAL** - Must preserve verbatim |
| Metadata Extraction Requirements | EVALUATION_FACTOR (weight, hierarchy, subfactors), SUBMISSION_INSTRUCTION (page limit, format), REQUIREMENT (criticality, drivers) | **CRITICAL** |

#### Redundancy with Other Files:
- PERF_METRIC vs REQUIREMENT (3x duplication)
- Strategic Theme detection (3x duplication)
- 18 entity types (3x duplication)
- Modal verb → criticality mapping (3x duplication)

---

## Part 2: Relationship Inference Prompts Analysis

### 2.1 Patterns That CAN Move Upstream to Main Extraction

These patterns can be detected during initial extraction when both entities are in the same chunk:

| Prompt File | Pattern | Relationship Type | Detection Signal | Move Upstream? |
|-------------|---------|-------------------|------------------|----------------|
| **deliverable_traceability.md** | Requirement mentions deliverable | SATISFIED_BY | "CDRL A001" in requirement text | ✅ YES |
| **deliverable_traceability.md** | SOW mentions deliverable | PRODUCES | Explicit CDRL reference in SOW | ✅ YES |
| **evaluation_hierarchy.md** | Factor → Subfactor numbering | HAS_SUBFACTOR | "Factor 1" → "Subfactor 1.1" | ✅ YES |
| **instruction_evaluation_linking.md** | Explicit L→M cross-reference | GUIDES | "addresses Factor 2" text | ✅ YES |
| **document_hierarchy.md** | Sub-document numbering | CHILD_OF | J-02000000-10 → J-02000000 | ✅ YES |
| **clause_clustering.md** | Clause numbering to section | CHILD_OF | FAR 52.### → Section I | ✅ YES |
| **attachment_section_linking.md** | Prefix pattern | ATTACHMENT_OF | J-prefix → Section J | ✅ YES |
| **sow_deliverable_linking.md** | Explicit CDRL mention in SOW | PRODUCES | "per CDRL A001" | ✅ YES |

**Estimated Savings**: 8 of 13 inference prompts have patterns detectable during extraction

---

### 2.2 Patterns That MUST Remain Post-Processing

These patterns require the full entity list or cross-chunk analysis:

| Prompt File | Pattern | Relationship Type | Why Post-Processing? |
|-------------|---------|-------------------|----------------------|
| **requirement_evaluation.md** | Topic alignment | EVALUATED_BY | Needs all requirements + all factors |
| **semantic_concept_linking.md** | Pain point → Factor mapping | ADDRESSED_BY, INFORMS | Cross-section semantic analysis |
| **orphan_resolution.md** | Orphan detection | REQUIRES, ENABLED_BY | Needs full graph to find orphans |
| **workload_enrichment.md** | BOE categorization | (metadata) | Classification across all requirements |

**Estimated Post-Processing Retained**: 4-5 algorithms still needed

---

### 2.3 Inference Prompt Intelligence to Preserve

#### deliverable_traceability.md
- **Key Pattern**: 60-80% of deliverables come from CDRLs/clauses/eval criteria, NOT SOW text
- **Confidence Thresholds**: HIGH (0.85-0.95) for direct evidence, MEDIUM (0.65-0.85) for semantic
- **Special Case**: Multi-source deliverables → create separate relationships

#### evaluation_hierarchy.md
- **6 Relationship Types**: HAS_SUBFACTOR, HAS_RATING_SCALE, MEASURED_BY, HAS_THRESHOLD, EVALUATED_USING, DEFINES_SCALE
- **Classification Rules**: Main factors vs supporting entities (ratings, metrics, processes)
- **Validation**: Confidence 0.95-1.0 for explicit hierarchy

#### instruction_evaluation_linking.md
- **4 Inference Patterns**: Explicit cross-ref (0.95), Implicit co-location (0.80), Content alignment (0.70), Agnostic detection (0.75-0.90)
- **Key Insight**: Non-UCF structures embed instructions in deliverables/requirements
- **Special Case**: One instruction → Multiple factors

#### workload_enrichment.md
- **7 BOE Categories**: Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance
- **Invalid Mapping Table**: Security → Compliance, Training → ODCs, Business Performance → Labor
- **Labor Driver Extraction**: Explicit (3 FTE, 24/7) and implicit (continuous operations)
- **Material Needs**: Equipment quantities, facility square footage
- **Complexity Scoring**: 1-10 scale with rationale

#### document_hierarchy.md
- **4 Hierarchical Patterns**: Prefix+Delimiter, Standard+Subsection, Clause+Paragraph, Decimal Notation
- **Version vs Hierarchy Rule**: 4-digit year = version (NOT hierarchy), X.Y.Z = hierarchy
- **Cross-Family Prevention**: NIST controls → NIST parent (not J-annex)

#### requirement_evaluation.md
- **4 Inference Patterns**: Topic alignment, Criticality mapping, Content proximity, Explicit cross-ref
- **6 Topic Categories**: Technical, Management, Performance, Personnel, Quality, Transition
- **Requirement Type Override**: requirement_type field takes precedence over keyword matching

#### clause_clustering.md
- **26+ Agency Supplements**: FAR, DFARS, AFFARS, NMCARS, HSAR, DOSAR, GSAM, VAAR, DEAR, NFS, AIDAR, CAR, DIAR, DOLAR, EDAR, EPAAR, FEHBAR, HHSAR, HUDAR, IAAR, JAR, LIFAR, NRCAR, SOFARS, TAR, AGAR
- **Section Attribution**: FAR 52.2## → Section K (Representations), FAR 52.### → Section I (Clauses)

#### semantic_concept_linking.md
- **5 Algorithms**: Pain Point → Factor, Factor Decomposition, Adjacent Factor Discovery, Proposal Outline Generation, Competitive Advantage Identification
- **Shipley Win Theme Formula**: MANDATORY requirement + High-weight factor + Pain point = Win theme

#### attachment_section_linking.md
- **Agency Patterns**: DoD (J-########), GSA (Exhibit pricing → B, Attachment → J), NASA (Annex → J), DoE (mixed)
- **Key Rule**: Only TOP-LEVEL attachments get ATTACHMENT_OF; sub-attachments use CHILD_OF

---

## Part 3: Consolidation Strategy

### 3.1 Redundancy Elimination

| Content | Appearances | Consolidation Action |
|---------|-------------|---------------------|
| PERF_METRIC vs REQUIREMENT | 3 files | Single authoritative section |
| Strategic Theme detection | 3 files | Single section with all ThemeTypes |
| 18 Entity Types list | 3 files | Single definitive list |
| Modal verb → Criticality | 3 files | Single mapping table |
| UCF Section reference | 2 files | Single table with all columns |
| JSON output format | 2 files | Single schema definition |

**Estimated Token Savings from Deduplication**: ~15,000 tokens (40%)

### 3.2 Format Optimization (Preserve Content)

| Optimization | Before | After | Savings |
|--------------|--------|-------|---------|
| Remove markdown headers | ## Header | SECTION: | 3% |
| Compress tables to lists | Full tables | Key-value pairs | 10% |
| Remove redundant examples | 5 similar examples | 2 diverse examples | 15% |
| Inline minor rules | Separate sections | Integrated | 5% |

**Estimated Additional Savings**: ~5,000 tokens (15%)

### 3.3 Upstream Pattern Integration

Add to main extraction prompt (new section):

```
## RELATIONSHIP DETECTION DURING EXTRACTION

When extracting entities, also detect these relationships:

1. EXPLICIT REFERENCES (Confidence: 0.95+)
   - "addresses Factor 2" → GUIDES relationship
   - "CDRL A001" mentioned in requirement → SATISFIED_BY
   - "per PWS Section 3.2" → PRODUCES
   
2. NUMBERING HIERARCHIES (Confidence: 0.95)
   - J-02000000-10 → CHILD_OF → J-02000000
   - Subfactor 1.1 → HAS_SUBFACTOR → Factor 1
   - FAR 52.212-4 → CHILD_OF → Section I
   
3. PREFIX PATTERNS (Confidence: 1.0)
   - J-prefix → ATTACHMENT_OF → Section J
   - H-prefix → ATTACHMENT_OF → Section H
   
4. CONTENT CO-LOCATION (Confidence: 0.80)
   - Submission instruction in same paragraph as factor → GUIDES
   - Performance metric with requirement → MEASURED_BY
```

---

## Part 4: Annotated Examples Preservation

### 4.1 Examples That MUST Be Preserved Verbatim

| Example | Source File | Lines | Why Critical |
|---------|-------------|-------|--------------|
| Section L ↔ M Mapping | entity_extraction_prompt.md | 606-684 | Core L→M relationship extraction |
| Requirements with Workload | entity_extraction_prompt.md | 686-756 | CRP example with labor_drivers, metrics split |
| PWS Appendix Structure | entity_extraction_prompt.md | 765-850 | Appendix hierarchy extraction |
| Clause Extraction | entity_detection_rules.md | 985-1033 | FAR/DFARS with dates |
| QASP Table | grok_json_prompt.md | 222-237 | Performance metric extraction |

### 4.2 Examples That Can Be Condensed

| Example | Source | Action |
|---------|--------|--------|
| Navy MBOS Factor example | entity_detection_rules.md | Merge with general factor example |
| Task Order non-standard | entity_detection_rules.md | Keep but shorten |
| Multiple equipment examples | grok_json_prompt.md | Reduce to 1 comprehensive example |

---

## Part 5: Critical Distinctions to Preserve

### 5.1 The "Big 3" Distinctions

1. **PERFORMANCE_METRIC vs REQUIREMENT**
   - Trigger phrases for each
   - Split rule: one sentence → two entities
   - MEASURED_BY relationship
   
2. **STRATEGIC_THEME Classification**
   - CUSTOMER_HOT_BUTTON detection patterns
   - DISCRIMINATOR, PROOF_POINT, WIN_THEME definitions
   - Weight-based detection (>30% = hot button)
   
3. **EVALUATION_FACTOR vs SUBMISSION_INSTRUCTION**
   - Section M content = EVALUATION_FACTOR
   - Section L content = SUBMISSION_INSTRUCTION
   - Embedded instructions in M → extract separately

### 5.2 Entity Type Disambiguation Rules

| Invalid Type | Map To | Example |
|--------------|--------|---------|
| plan | document | "Safety Plan" |
| policy | document | "Security Policy" |
| standard | document | "ISO 9001" |
| system | technology | "ERP System" |
| process | concept | "Change Control Process" |
| table | concept | "Deliverables Schedule" |
| other/UNKNOWN | concept | Catch-all |

### 5.3 Criticality Mapping

| Modal Verb | Criticality | Priority Score |
|------------|-------------|----------------|
| shall/must/will (contractor) | MANDATORY | 100 |
| should | IMPORTANT | 75 |
| may | OPTIONAL | 25 |
| shall (government) | INFORMATIONAL | 0 |

---

## Part 6: Token Metrics

### 6.1 Current State

| File | Lines | Est. Tokens |
|------|-------|-------------|
| grok_json_prompt.md | 377 | ~5,000 |
| entity_detection_rules.md | 1,612 | ~18,000 |
| entity_extraction_prompt.md | 3,304 | ~32,000 |
| **Main Extraction Total** | **5,293** | **~55,000** |
| Relationship inference (13 files) | ~3,500 | ~25,000 |
| **Grand Total** | **~8,800** | **~80,000** |

### 6.2 Target State (Unified Prompt)

| Component | Est. Tokens | Notes |
|-----------|-------------|-------|
| Core Identity & Schema | 500 | Role, output format |
| Entity Types (18) | 2,000 | Single authoritative list |
| Critical Distinctions | 1,500 | PERF_METRIC, STRATEGIC, EVAL |
| Domain Rules | 1,000 | Shall/Will, L↔M, Naming |
| Upstream Relationship Patterns | 1,500 | From inference prompts |
| Annotated Examples (5) | 2,500 | Preserved verbatim |
| Validation Rules | 500 | Quality checks |
| **Unified Total** | **~10,000** | **82% reduction** |

### 6.3 Post-Processing Prompts (Retained)

| Algorithm | Est. Tokens | Notes |
|-----------|-------------|-------|
| requirement_evaluation | 1,500 | Needs full entity list |
| semantic_concept_linking | 2,000 | Cross-section analysis |
| orphan_resolution | 1,000 | Graph completion |
| workload_enrichment | 1,500 | BOE classification |
| **Post-Processing Total** | **~6,000** | |

---

## Part 7: Validation Baseline (ADAB ISS PWS)

### 7.1 51_iss_full_test Workspace Metrics

| Metric | Expected Value | Tolerance |
|--------|----------------|-----------|
| Total Entities | ~400 | ±5% |
| Total Relationships | ~400 | ±5% |
| Entity Types Represented | 15-18 | All 18 valid |
| Chunks Processed | 11 | N/A |

### 7.2 Branch 022 Perfect Run Baseline (Fallback)

| Metric | Value |
|--------|-------|
| Entities | 368 |
| Relationships | 428 |
| Workload Query Quality | 98%+ |
| Processing Time | ~33 min |

### 7.3 Quality Validation Queries

1. "Provide complete list of workload drivers for Appendix F services"
2. "What are the evaluation factors and their weights?"
3. "Section L/M compliance mapping"
4. "List all CDRL deliverables with their requirements"

---

## Part 8: Implementation Checklist

### Phase 1: Unified Prompt Creation
- [ ] Merge 18 entity types into single authoritative section
- [ ] Consolidate PERF_METRIC vs REQUIREMENT (single section)
- [ ] Consolidate STRATEGIC_THEME detection (single section)
- [ ] Add upstream relationship patterns from inference prompts
- [ ] Preserve all 5 annotated examples verbatim
- [ ] Preserve all critical distinctions
- [ ] Add validation rules section

### Phase 2: Prompt Loader Refactor
- [ ] Update `json_extractor.py` to load unified prompt ONLY
- [ ] Remove modular prompt loading code
- [ ] Remove USE_COMPRESSED_PROMPTS handling
- [ ] Add clear error if unified prompt not found

### Phase 3: Post-Processing Updates
- [ ] Update `semantic_post_processor.py` to skip algorithms moved upstream
- [ ] Retain: requirement_evaluation, semantic_concept_linking, orphan_resolution, workload_enrichment
- [ ] Document which patterns moved upstream

### Phase 4: Validation
- [ ] Run extraction on ADAB ISS RFP
- [ ] Compare entity counts to baseline (±5%)
- [ ] Compare relationship counts to baseline (±5%)
- [ ] Run quality validation queries
- [ ] Verify no regression in workload driver extraction

### Phase 5: Archive
- [ ] Move original prompts to `prompts/archive/v2_modular/`
- [ ] Update documentation

---

## Appendix A: File Inventory

### Main Extraction Prompts
```
prompts/extraction/
├── grok_json_prompt.md           (377 lines)
├── entity_detection_rules.md      (1,612 lines)
└── entity_extraction_prompt.md    (3,304 lines)
```

### Relationship Inference Prompts
```
prompts/relationship_inference/
├── attachment_section_linking.md  (582 lines)
├── clause_clustering.md           (404 lines)
├── deliverable_traceability.md    (296 lines)
├── document_hierarchy.md          (1,012 lines)
├── document_section_linking.md    (113 lines)
├── evaluation_hierarchy.md        (251 lines)
├── instruction_evaluation_linking.md (440 lines)
├── orphan_resolution.md           (306 lines)
├── requirement_evaluation.md      (625 lines)
├── semantic_concept_linking.md    (488 lines)
├── sow_deliverable_linking.md     (147 lines)
├── system_prompt.md               (12 lines)
└── workload_enrichment.md         (418 lines)
```

---

**Created**: December 15, 2025  
**Author**: Claude AI (Cursor Assistant)  
**Status**: Ready for Phase 2 - Unified Prompt Creation

