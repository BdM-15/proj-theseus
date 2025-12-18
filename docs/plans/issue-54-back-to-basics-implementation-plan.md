# Implementation Plan: Issue #54 - Back to Basics Architecture

**Issue**: [#54 - Refactor: Back to Basics - Leverage Native LightRAG + RAG-Anything Architecture](https://github.com/BdM-15/govcon-capture-vibe/issues/54)  
**Created**: December 18, 2025  
**Target Completion**: December 24, 2025 (1 week sprint)  
**Priority**: HIGH

---

## Executive Summary

This plan outlines a phased approach to restore extraction quality by:
1. Enhancing prompts with missing workload driver intelligence (lean format)
2. Adapting our ontology to LightRAG's native structure
3. Evaluating and potentially simplifying Pydantic adapter layers
4. Validating against Branch 022 perfect run baseline

**Goal**: Achieve 95%+ extraction quality with no query tuning required, maintaining lean prompt architecture.

### Key Reference Points

| Reference | Purpose |
|-----------|---------|
| **Branch 040 (GitHub: `feature/040-issue46-ontology-query-bounded-entity-description`)** | Source for extraction intelligence (3 modular prompts, ~188KB) |
| **Current `govcon_ontology_v3.txt`** | Unified prompt (~89K chars) that compressed Branch 040's modular prompts |
| **Branch 022 Baseline** | Target extraction quality (98%+ workload accuracy) |
| **Post-Mortem Doc** | Lessons learned from Branches 022-040 |

> **NOTE**: Branch 040 had **modular prompts** (3 extraction files + 12 post-processing files = ~331KB), NOT a unified V3. The current `govcon_ontology_v3.txt` (~89K chars, ~22K tokens) is a later compression that lost ~73% of the extraction prompt content. We need to restore critical intelligence from Branch 040's modular prompts into the current unified format.

---

## Phase Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Phase 1: Prompt Enhancement (Day 1-2)                                      │
│  ├─ Update Role to Shipley Capture/Proposal Manager                        │
│  ├─ Add Workload Driver Extraction Rules                                    │
│  └─ Add Use Case Context                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 2: LightRAG Native Integration (Day 2-3)                            │
│  ├─ Analyze LightRAG prompt.py structure                                   │
│  ├─ Create hybrid prompt injection strategy                                │
│  └─ Test entity_types integration                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 3: Adapter Evaluation (Day 3-4)                                     │
│  ├─ A/B test: with vs without Pydantic adapters                           │
│  ├─ Identify value-add vs overhead                                         │
│  └─ Document findings                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 4: Validation & Tuning (Day 4-5)                                    │
│  ├─ Test against ADAB ISS PWS (same doc as current run)                   │
│  ├─ Compare to Branch 022 baseline                                         │
│  └─ Workload driver query test                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Phase 5: Documentation & Merge (Day 5-6)                                  │
│  ├─ Update technical documentation                                         │
│  ├─ Create new "locked configuration" reference                           │
│  └─ Merge to main                                                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Prompt Enhancement (Day 1-2)

### Objective
Restore ~15% missing extraction intelligence while maintaining lean format (~25-30K tokens max)

### Tasks

#### 1.1 Update Role Definition
**File**: `prompts/extraction/govcon_ontology_v3.txt` (the unified V3 prompt)  
**Location**: Lines 1-7  
**Action**: Replace generic role with Shipley-focused capture/proposal perspective

**Current** (from govcon_ontology_v3.txt lines 1-7):
```
GOVCON ONTOLOGY V3 - UNIFIED EXTRACTION PROMPT
===============================================
Role: Government Contracting Knowledge Graph Specialist
Model: xAI Grok-4-fast-reasoning (2M context window)
Output: Single JSON object adhering to ExtractionResult schema
Version: 3.0 (December 2025 - Unified Architecture with Full Intelligence Preservation)
```

**New** (Generalist Multi-Persona Approach - IMPLEMENTED):
```
---Role---
You are a Federal Government Contracting Intelligence Specialist supporting the full 
Shipley Associates Business Development Lifecycle. You extract knowledge to serve 
diverse capture and proposal team members:

USER PERSONAS YOU SUPPORT:
- Capture Managers: Win themes, competitive positioning, customer hot buttons, discriminators
- Proposal Managers: Compliance matrices, proposal outlines, Section L↔M mapping, page limits
- Proposal Writers: Requirement details, technical specifications, deliverable descriptions
- Cost Estimators: Workload drivers, labor hours, equipment counts, frequencies, BOE inputs
- Contracts Managers: FAR/DFARS clauses, terms & conditions, regulatory compliance, CLINs
- Technical SMEs: Performance standards, specifications, technical requirements, QA criteria
- Legal/Compliance: Certifications, representations, regulatory obligations, IP requirements
- Program Managers: CDRLs, deliverable schedules, reporting requirements, milestones

EXTRACTION PHILOSOPHY:
1. Be COMPREHENSIVE - capture intelligence useful across all personas
2. Be PRECISE - preserve quantitative details verbatim (numbers, rates, frequencies, amounts)
3. Be STRATEGIC - identify win themes and customer priorities, not just requirements
4. Be TRACEABLE - maintain links to source sections and cross-references
5. Be ADAPTIVE - the same RFP content may answer different questions for different users

CRITICAL: Preserve ALL specifics that ANY team member might need. A contracts manager 
needs exact clause numbers. An estimator needs exact quantities. A capture manager 
needs evaluation weights. A proposal writer needs page limits. Extract for ALL of them.
```

**Token Impact**: +350 tokens (justified by multi-persona coverage)

---

#### 1.2 Add Quantitative Detail Preservation Rules
**File**: `prompts/extraction/govcon_ontology_v3.txt`  
**Location**: After Intelligence Sources section  
**Action**: Add explicit extraction rules for precision data (serves all personas)
**Status**: ✅ IMPLEMENTED

**New Section** (Renamed from BOE-only to multi-persona):
```
================================================================================
QUANTITATIVE DETAIL PRESERVATION (Benefits ALL User Personas)
================================================================================
Quantitative details serve multiple purposes across the capture team:
- Cost Estimators: labor calculations, BOE development, pricing models
- Proposal Writers: specific compliance language, technical accuracy
- Capture Managers: scope understanding, risk assessment
- Contracts Managers: service levels for negotiation, performance metrics

ALWAYS extract these VERBATIM - never summarize, generalize, or omit numbers!

SERVICE RATES - Extract exact rates with context:
- "X customer(s) per minute/hour" → preserve exactly
- "X transaction(s) per shift" → preserve exactly
- Distinguish: normal operations vs peak times vs events
- Include time windows: (0500-0700, 1100-1300, etc.)
- Example: "Retail services at minimum rates of one (1) customer per minute during normal operations and three (3) customers per minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100)"

FREQUENCIES - Extract with multipliers:
- "X times per year/month/week/day"
- "estimated X occurrences annually"
- "average X-Y [deliveries/visits/events]"
- NEVER generalize "100 times per year" to "frequent" or "regular"
- Example: "This is estimated to occur 100 times per year" → preserve "100 times per year"

DOLLAR VOLUMES - Preserve ranges:
- "$X-Y per night/month/transaction"
- "up to $X during [condition]"
- "between $X and $Y"
- Example: "sells between $2,000 and $5,000 per night" → preserve full range

QUANTITIES & COUNTS:
- Equipment counts: "X units", "Y registers", "Z refrigeration units"
- Personnel: "X staff", "Y FTEs required", "Z supervisors"
- Inventory: "X items", "Y tubs annually", "Z cases per week"
- Example: "750 tubs of 700-count wipes annually" → preserve both numbers

TIME RANGES - Never drop time specifications:
- Operating hours: "1830-0200", "0700-1900"
- Peak periods: "0500-0700, 1100-1300, 1900-2100, 2300-0100"
- Response times: "within X minutes/hours", "NLT X days"
- Duration: "2-3 calendar days", "30 times per year"

COVERAGE SPECIFICATIONS:
- "24/7", "24 hours/day, 7 days/week"
- "X days notice required"
- Population served: "X daily customers, up to Y during surges"
- Example: "1,600 daily customers (up to 4,000 during rotations)"

EXTRACTION ANTI-PATTERNS (DO NOT DO):
❌ "Contractor shall provide customer service" (loses service rate)
❌ "Regular events" (loses "100 times per year")
❌ "Sales operations" (loses "$2,000-5,000 per night")
❌ "Equipment available" (loses "8 refrigeration units")

CORRECT EXTRACTION:
✅ entity_name: "Retail Service Rate Standard"
✅ description: "Contractor shall provide retail services at minimum rates of one (1) customer per minute during normal operations and three (3) customers per minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100)"
✅ performance_standard: "1 customer/min normal, 3 customers/min peak (0500-0700, 1100-1300, 1900-2100, 2300-0100)"
```

**Token Impact**: +500 tokens

---

#### 1.3 Add Use Case Context Section
**File**: `prompts/extraction/govcon_ontology_v3.txt`  
**Location**: After line 12 (after the CRITICAL note about consolidated intelligence)  
**Action**: Add Shipley use case context

**New Section**:
```
---
## Extraction Purpose: Shipley Capture Intelligence

This extraction feeds the Shipley Associates capture and proposal process:

CAPTURE PLANNING:
- Workload drivers → BOE labor hours and FTE calculations
- Equipment lists → Material cost estimates
- Facility coverage → Site survey requirements
- Personnel requirements → Staffing models

PROPOSAL DEVELOPMENT:
- Section L requirements → Compliance matrix
- Evaluation factors → Proposal outline structure
- Strategic themes → Win theme development
- Past performance requirements → Experience mapping

KICKOFF & EXECUTION:
- Deliverable schedules → CDRL tracking
- Performance metrics → QASP compliance
- Reporting requirements → Project controls

Extract with the mindset: "Would a proposal manager need this exact detail to write a compliant, winning proposal?"
```

**Token Impact**: +150 tokens

---

#### 1.4 Review Entity Detection Rules
**File**: `prompts/extraction/entity_detection_rules.md`  
**Action**: Verify workload driver patterns are present

Check for and add if missing:
- Service rate pattern matching rules
- Frequency multiplier preservation rules
- Dollar amount extraction rules
- Time range preservation rules

---

### Phase 1 Deliverables
- [ ] Updated `govcon_ontology_v3.txt` with new Shipley Role definition
- [ ] Added Workload Driver Extraction Rules section (~500 tokens)
- [ ] Added Use Case Context section (~150 tokens)
- [ ] Reviewed `entity_detection_rules.md` for pattern completeness
- [ ] Total token increase: ~800 tokens (22K → ~23K)

> **Note**: `govcon_ontology_v3.txt` is the unified V3 prompt from Branch 040. This is the single source of truth loaded by `src/server/initialization.py` and `src/extraction/json_extractor.py`.

### Phase 1 Validation
Run extraction on test chunk containing service rate text:
```
"Contractor personnel shall provide retail services at minimum rates of one (1) 
customer per minute during normal operations and three (3) customers per minute 
during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100)"
```

**Expected Output**:
- entity_name: "Retail Service Rate Standard"
- entity_type: "requirement"
- description: Contains full verbatim text
- performance_standard: "1 customer/min normal, 3 customers/min peak"

---

## Phase 2: LightRAG Native Integration & Cleanup (CRITICAL)

### Objective
Remove over-engineered Pydantic layers and return to LightRAG/RAG-Anything native architecture.
Inject our GovCon ontology through LightRAG's native customization points.

### Analysis Complete (2025-12-18)

#### LightRAG Native Extraction Format
**Reference**: https://github.com/HKUDS/LightRAG/blob/main/lightrag/prompt.py

LightRAG uses **tuple-delimited format** (NOT JSON):
```
entity<|#|>entity_name<|#|>entity_type<|#|>entity_description
relation<|#|>source_entity<|#|>target_entity<|#|>relationship_keywords<|#|>relationship_description
```

**Native Customization Points:**
1. `addon_params["entity_types"]` - Pass custom entity type list ✅ (already configured)
2. `PROMPTS["entity_extraction_system_prompt"]` - Inject domain knowledge ✅ (already configured)
3. `PROMPTS["entity_extraction_examples"]` - Custom few-shot examples

#### Current Over-Engineering (TO REMOVE)

The current architecture has unnecessary layers:
```
User Prompt → JsonExtractor (Pydantic) → LLM → JSON Output
                     ↓
          LightRAGAdapter (Translation)
                     ↓
          Pipe-Delimited Format → LightRAG Parser
```

This is **double-processing**: We're converting LightRAG's native format to JSON, validating with Pydantic, then converting BACK to pipe-delimited format.

#### Correct Architecture (Native)
```
User Prompt → LightRAG Native Prompt → LLM → Tuple-Delimited Output
                     ↓
          LightRAG Parser (built-in)
                     ↓
          Knowledge Graph
                     ↓
          Semantic Post-Processing (KEEP)
```

---

### Files to DELETE (Pydantic Layers)

| File | Reason | Status |
|------|--------|--------|
| `src/extraction/json_extractor.py` | Pydantic extraction via Instructor - unnecessary | PENDING |
| `src/extraction/lightrag_llm_adapter.py` | JSON→Pipe translation layer - unnecessary | PENDING |
| `src/extraction/table_extractor.py` | Pydantic TableSummary model - unnecessary | PENDING |

### Files to MODIFY

| File | Change | Status |
|------|--------|--------|
| `src/ontology/schema.py` | Keep `VALID_ENTITY_TYPES` and BOE mapping only, remove extraction models | PENDING |
| `src/server/initialization.py` | Remove adapter creation, use native LLM function directly | PENDING |
| `src/processors/govcon_multimodal_processor.py` | Remove JsonExtractor dependency, use native RAG-Anything | PENDING |

### Files to KEEP (Semantic Post-Processing)

| File | Purpose |
|------|---------|
| `src/inference/semantic_post_processor.py` | 8 relationship inference algorithms |
| `src/inference/workload_enrichment.py` | BOE category tagging |
| `src/inference/algorithms/*.py` | Individual inference algorithms |
| `src/server/routes.py` | Server API routes |
| `src/server/config.py` | Entity types configuration |

---

### Tasks

#### 2.1 Delete Pydantic Extraction Files
```bash
rm src/extraction/json_extractor.py
rm src/extraction/lightrag_llm_adapter.py
rm src/extraction/table_extractor.py
```

#### 2.2 Simplify schema.py
Keep ONLY:
- `VALID_ENTITY_TYPES` (set of 18 entity type strings)
- `EntityType` (Literal type for type hints)
- `BOECategory` enum and `normalize_boe_category()` (used by workload enrichment)

Remove:
- `BaseEntity`, `RelationshipModel`, `ExtractionResult` Pydantic models
- All field validators related to extraction

#### 2.3 Update initialization.py
Remove:
- `from src.extraction.lightrag_llm_adapter import create_extraction_adapter`
- All references to `USE_PYDANTIC_EXTRACTION`
- Adapter wrapping logic

Keep:
- Native LLM function (`base_llm_model_func`)
- Domain knowledge injection into `PROMPTS["entity_extraction_system_prompt"]`
- Entity types configuration via `addon_params`

#### 2.4 Update GovconMultimodalProcessor
Option A: Use RAG-Anything's native multimodal processing (recommended)
Option B: Simplify to return text description only (no entity extraction)

#### 2.5 Update .env
Set `USE_PYDANTIC_EXTRACTION=false` (then remove the variable entirely after cleanup)

---

### Phase 2 Deliverables
- [ ] Deleted 3 Pydantic extraction files
- [ ] Simplified `schema.py` to entity types only
- [ ] Updated `initialization.py` to use native LLM function
- [ ] Updated multimodal processor
- [ ] Verified native extraction works
- [ ] Documented architecture change
- [ ] Verified entity_types integration
- [ ] Created test script for native vs custom extraction comparison

---

## Phase 3: Adapter Evaluation (Day 3-4)

### Objective
Determine if Pydantic adapters add value or introduce failure points

### Tasks

#### 3.1 A/B Test Design

**Test A: Current Architecture (Pydantic Adapters)**
```
LightRAG → Custom LLM Func → lightrag_llm_adapter.py → json_extractor.py → Pydantic Validation → LightRAG Storage
```

**Test B: Simplified Architecture (Native)**
```
LightRAG → Native Extraction (with enriched prompts) → LightRAG Storage
```

**Test Document**: `Atch 1 ADAB ISS PWS_12 Dec 2025.pdf`

**Metrics to Compare**:
| Metric | Test A (Pydantic) | Test B (Native) |
|--------|-------------------|-----------------|
| Entity Count | TBD | TBD |
| Service Rate Extracted | Yes/No | Yes/No |
| Processing Time | TBD | TBD |
| Error Rate | TBD | TBD |

---

#### 3.2 Identify Value-Add Components

For each adapter file, document:
1. What validation/transformation does it perform?
2. Is this validation available natively in LightRAG?
3. Does it catch errors that would otherwise propagate?
4. Could it be causing extraction misses?

**Files to Evaluate**:
- `src/extraction/lightrag_llm_adapter.py`
- `src/extraction/json_extractor.py`
- `src/ontology/schema.py` (Pydantic models)

---

#### 3.3 Document Findings

Create comparison report:
```
## Adapter Evaluation Report

### lightrag_llm_adapter.py
- Purpose: [describe]
- Value-Add: [Yes/No - explain]
- Overhead: [describe]
- Recommendation: [Keep/Remove/Simplify]

### json_extractor.py
- Purpose: [describe]
- Value-Add: [Yes/No - explain]
- Overhead: [describe]
- Recommendation: [Keep/Remove/Simplify]
```

---

### Phase 3 Deliverables
- [ ] A/B test results documented
- [ ] Adapter evaluation report
- [ ] Recommendation: Keep, Remove, or Simplify each adapter
- [ ] If removing: Migration plan to native extraction

---

## Phase 4: Validation & Tuning (Day 4-5)

### Objective
Validate extraction quality against Branch 022 baseline

### Tasks

#### 4.1 End-to-End Test

**Test Document**: `Atch 1 ADAB ISS PWS_12 Dec 2025.pdf` (77 pages)

**Steps**:
1. Clear Neo4j workspace
2. Process document with updated prompts
3. Run workload driver query
4. Compare to `perfectrun_workload_prompt_response.md`

---

#### 4.2 Baseline Comparison

| Metric | Branch 022 Target | Current Result | Status |
|--------|-------------------|----------------|--------|
| Entity Count | ~368 | TBD | ⏳ |
| Relationship Count | ~428 | TBD | ⏳ |
| Service Rate Extracted | ✅ | TBD | ⏳ |
| Peak Times Extracted | ✅ | TBD | ⏳ |
| Dollar Amounts Extracted | ✅ | TBD | ⏳ |
| Event Frequencies Extracted | ✅ | TBD | ⏳ |
| Query Tuning Needed | None | TBD | ⏳ |

---

#### 4.3 Workload Driver Query Test

**Query**:
```
Provide me a total and complete list of workload drivers for Appendix F services.
Workload drivers could be frequencies, quantities, hours, coverage, equipment
lists...etc. that can be used to help develop a Bases of Estimate for Labor
Totals/Full Time Equivalents. Do not include surveillance metrics or inspection
measurements or performance objectives because those are not workload drivers.
Focus on totality and not samples. We need all the workload available. Provide
a brief summary of the Appendix and then organize workload drivers by Section
in a logical manner.
```

**Critical Details to Verify**:
- [ ] "1 customer per minute during normal operations"
- [ ] "3 customers per minute during peak times (0500-0700, 1100-1300, 1900-2100, 2300-0100)"
- [ ] "$2,000-5,000 per night" or similar dollar amount
- [ ] "100 times per year" (or "65 times per year" in Dec version)
- [ ] "750 tubs of 700-count wipes annually"
- [ ] "20-24 instructor-led classes per week"
- [ ] "8-10 special sports events per month"
- [ ] Equipment counts (refrigeration units, registers, etc.)

---

#### 4.4 Iterate if Needed

If extraction quality < 95%:
1. Review extraction logs for which chunks missed data
2. Check if patterns are in prompt but not being followed
3. Adjust prompt wording or add more explicit examples
4. Re-test

---

### Phase 4 Deliverables
- [ ] End-to-end test results
- [ ] Baseline comparison table completed
- [ ] Workload driver query response saved
- [ ] Quality assessment: ≥95% of Branch 022 baseline

---

## Phase 5: Documentation & Merge (Day 5-6)

### Objective
Document changes and merge to main

### Tasks

#### 5.1 Update Technical Documentation

**Files to Update**:
- `.cursorrules` - Update prompt section if needed
- `README.md` - Update architecture description if changed
- `docs/ARCHITECTURE.md` - Document new extraction flow

---

#### 5.2 Create New Configuration Reference

Create `docs/config/extraction-config-issue-54.md`:
```markdown
# Extraction Configuration - Issue #54

## Prompt Configuration (Branch 040 + Enhancements)
- govcon_ontology_v3.txt: ~23K tokens (Shipley role + workload rules)
  - Base: Branch 040 unified prompt
  - Added: Workload driver extraction rules
  - Added: Shipley capture/proposal context
- entity_detection_rules.md: [merged/separate]

## LightRAG Configuration
- entity_types: 18 govcon types
- chunk_size: 8192
- chunk_overlap: 1200

## Adapter Status
- lightrag_llm_adapter.py: [Keep/Removed]
- json_extractor.py: [Keep/Removed]

## Validation Results (vs Branch 022 Baseline)
- Entity count: [actual] vs 368 target
- Service rate capture: [pass/fail]
- Workload query: [pass/fail]
- Query tuning needed: [yes/no]
```

---

#### 5.3 Merge to Main

1. Create PR from feature branch
2. Include test results and comparison data
3. Review changes with team (if applicable)
4. Merge and tag release

**Git Commands**:
```bash
git checkout -b feature/issue-54-back-to-basics
# Make changes
git add -A
git commit -m "feat: Back to basics architecture refactor (Issue #54)

- Updated extraction prompt with Shipley role definition
- Added workload driver extraction rules
- Added use case context for capture intelligence
- [Evaluated/Simplified] Pydantic adapters
- Validated against Branch 022 baseline

Fixes #54"
git push origin feature/issue-54-back-to-basics
# Create PR via GitHub
```

---

### Phase 5 Deliverables
- [ ] Technical documentation updated
- [ ] Configuration reference created
- [ ] PR created with test results
- [ ] Merged to main
- [ ] Issue #54 closed

---

## Success Criteria Checklist

### Must Have (P0)
- [ ] Service rates extracted verbatim: "1 customer/min normal, 3 customers/min peak"
- [ ] No query tuning required for workload driver queries
- [ ] Entity count within ±10% of Branch 022 baseline
- [ ] All FTE-critical metrics preserved (frequencies, rates, amounts)

### Should Have (P1)
- [ ] Prompt size ≤ 30K tokens (lean format maintained)
- [ ] Processing time within ±20% of current
- [ ] Adapter evaluation documented with recommendations

### Nice to Have (P2)
- [ ] Simplified adapter architecture (if evaluation supports)
- [ ] Reduced complexity in extraction pipeline
- [ ] Improved error handling documentation

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Prompt changes degrade other extraction | Phase 4 comprehensive testing |
| Removing adapters breaks validation | Keep adapters if A/B test shows value |
| Timeline slippage | Phase 1-2 are highest priority; Phase 3 can be deferred |
| Regression in entity count | Compare to Branch 022 baseline at each phase |

---

## Timeline Summary

| Phase | Duration | Start | End | Status |
|-------|----------|-------|-----|--------|
| Phase 1: Prompt Enhancement | 2 days | Day 1 | Day 2 | ⏳ Not Started |
| Phase 2: LightRAG Integration | 1.5 days | Day 2 | Day 3 | ⏳ Not Started |
| Phase 3: Adapter Evaluation | 1.5 days | Day 3 | Day 4 | ⏳ Not Started |
| Phase 4: Validation | 1.5 days | Day 4 | Day 5 | ⏳ Not Started |
| Phase 5: Documentation | 1 day | Day 5 | Day 6 | ⏳ Not Started |

**Total Estimated Duration**: 5-6 working days

---

## Appendix A: Branch Reference Data

### Branch 022 (Results Baseline - Perfect Run)

From `docs/archive/perfect_run_branch_022/PERFECT_RUN_DOCUMENTATION.md`:

**Critical Configuration**:
```bash
LLM_MODEL=grok-4-fast-reasoning
CHUNK_SIZE=8192
CHUNK_OVERLAP_SIZE=1200
ENTITY_EXTRACT_MAX_GLEANING=0
GRAPH_STORAGE=Neo4JStorage
```

**Results (Target to Match)**:
- Entities: 368
- Relationships: 428 (274 initial + 154 inferred)
- Error Rate: 1.0%
- Workload Query: 98%+ accuracy
- **Key Success**: Service rates, dollar amounts, frequencies extracted verbatim

**Prompt Sizes (Branch 022 - VERBOSE, DO NOT COPY DIRECTLY)**:
- entity_extraction_prompt.txt: 101,735 chars (~25,434 tokens)
- entity_detection_rules.txt: 44,299 chars (~11,075 tokens)
- relationship_inference_prompt.txt: 138,908 chars (~34,727 tokens)
- **Total**: 284,942 chars (~71,236 tokens) ← Too verbose, markdown formatting waste

---

### Branch 040 (Prompt Source - Modular Structure)

From GitHub: `feature/040-issue46-ontology-query-bounded-entity-description`

**Branch 040 Modular Extraction Prompts (3 files = ~188KB)**:
- `entity_extraction_prompt.md`: 120,314 bytes (~120KB, ~30K tokens) - Main extraction with examples
- `entity_detection_rules.md`: 51,974 bytes (~52KB, ~13K tokens) - Detection patterns
- `grok_json_prompt.md`: 14,978 bytes (~15KB, ~4K tokens) - JSON format rules

**Branch 040 Post-Processing Prompts (12 files = ~143KB)**:
- `workload_enrichment.md`: 16,408 bytes - Detailed BOE/workload rules
- `document_hierarchy.md`: 26,516 bytes - Document structure inference
- Plus 10 other algorithm-specific prompts

**Total Branch 040 Prompt Intelligence**: ~331KB (~83K tokens)

**Branch 040 Key Features**:
- **Example 8**: Service rate extraction ("1 customer/min normal, 3 customers/min peak")  
- **Example 11**: Equipment inventory table extraction with building-level data
- **Example 12**: Fitness equipment maintenance schedules
- Comprehensive relationship inference rules (50+ patterns)
- Explicit quantitative preservation rules ("CRITICAL: EXTRACT EXACT NUMBERS")

**Current Unified V3 Prompt**:
- `govcon_ontology_v3.txt`: 89,425 chars (~22K tokens)
- **Compression ratio**: ~27% of Branch 040 extraction prompts
- **Intelligence loss**: Many detailed examples and edge case rules were compressed out

**What's Missing from Current V3 (compared to Branch 040)**:
1. **Role definition**: Generic "Knowledge Graph Specialist" instead of Shipley focus
2. **Quantitative rules**: "EXTRACT EXACT NUMBERS" emphasis was weakened
3. **Example 8 detail**: Service rate extraction example present but not being followed
4. **Workload driver context**: BOE/FTE use case not prominently stated
5. **50-word description limit**: May be truncating critical workload metrics

---

### Strategy: Hybrid Approach

| Aspect | Source | Rationale |
|--------|--------|-----------|
| **Prompt Structure** | Branch 040 | Lean, text-based, ~22K tokens |
| **Results Baseline** | Branch 022 | 98%+ workload accuracy target |
| **Intelligence to Add** | Branch 040 + New | Shipley context, workload rules |
| **Architecture** | Branch 040 | Native LightRAG integration |

**Target**: Branch 040 structure + Branch 022 results quality

---

## Appendix B: Files to Modify

| File | Phase | Change Type | Notes |
|------|-------|-------------|-------|
| `prompts/extraction/govcon_ontology_v3.txt` | Phase 1 | **Edit** | Main unified prompt (Branch 040) |
| `prompts/extraction/entity_detection_rules.md` | Phase 1 | Review/Edit | May merge into govcon_ontology_v3.txt |
| `prompts/extraction/entity_extraction_prompt.md` | Phase 1 | Review | Legacy file, may be deprecated |
| `src/server/config.py` | Phase 2 | Review | Entity types configuration |
| `src/server/initialization.py` | Phase 2 | Review | Prompt loading logic |
| `src/extraction/lightrag_llm_adapter.py` | Phase 3 | Evaluate | Pydantic validation adapter |
| `src/extraction/json_extractor.py` | Phase 3 | Evaluate | JSON extraction logic |
| `docs/config/extraction-config-issue-54.md` | Phase 5 | Create | Configuration reference |

---

## Appendix C: Test Commands

### Clear Neo4j and Re-process
```powershell
# Clear workspace
python tools/neo4j/clear_neo4j.py --workspace f14_iss_test

# Start server
python app.py

# Upload test document via WebUI or API
```

### Run Workload Query
```
POST /query
{
  "query": "Provide me a total and complete list of workload drivers for Appendix F services...",
  "mode": "mix"
}
```

### Check Extraction Results
```cypher
// Neo4j: Check service rate extraction
MATCH (r:requirement)
WHERE r.entity_name =~ '(?i).*service.*rate.*'
   OR r.description =~ '(?i).*customer.*per.*minute.*'
RETURN r.entity_name, r.description
LIMIT 10;
```

---

**Document Version**: 1.0  
**Last Updated**: December 18, 2025  
**Author**: AI Assistant (Claude)  
**Issue Reference**: #54

