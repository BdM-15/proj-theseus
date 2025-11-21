# Prompt Compression Restoration Plan

## Critical Finding

**Compression deleted 80-95% of examples from relationship inference prompts**, causing entity/relationship regression. Examples are the primary teaching mechanism for LLMs - patterns without examples = poor performance.

## Audit Results

### Extraction Prompts (Compression Valid)

| File                     | Baseline | Compressed | Reduction | Examples        | Status   |
| ------------------------ | -------- | ---------- | --------- | --------------- | -------- |
| grok_json_prompt         | 9,596    | 6,830      | 29%       | Schema added    | ✅ FIXED |
| entity_detection_rules   | 43,067   | 31,054     | 28%       | Need audit      | ⚠️ TODO  |
| entity_extraction_prompt | 99,413   | 41,645     | 58%       | 10/10 preserved | ✅ GOOD  |

### Relationship Inference Prompts (CRITICAL ISSUES)

| File                           | Baseline | Compressed | Reduction | Baseline Examples | Compressed Examples | Status      |
| ------------------------------ | -------- | ---------- | --------- | ----------------- | ------------------- | ----------- |
| system_prompt                  | 404      | 243        | 40%       | 0                 | 0                   | ✅ OK       |
| attachment_section_linking     | 12,606   | 1,125      | 91%       | 11                | 1                   | ❌ CRITICAL |
| clause_clustering              | 8,713    | 876        | 90%       | ?                 | ?                   | ❌ CRITICAL |
| deliverable_traceability       | 9,826    | 1,568      | 84%       | 5                 | 1                   | ❌ CRITICAL |
| document_hierarchy             | 24,216   | 1,437      | 94%       | ?                 | ?                   | ❌ CRITICAL |
| document_section_linking       | 3,363    | 914        | 73%       | ?                 | ?                   | ❌ CRITICAL |
| evaluation_hierarchy           | 6,510    | 1,484      | 77%       | ?                 | ?                   | ❌ CRITICAL |
| instruction_evaluation_linking | 11,225   | 1,594      | 86%       | ?                 | ?                   | ❌ CRITICAL |
| requirement_evaluation         | 14,986   | 1,980      | 87%       | 19                | 1                   | ❌ CRITICAL |
| semantic_concept_linking       | 13,864   | 2,303      | 83%       | ?                 | ?                   | ❌ CRITICAL |
| sow_deliverable_linking        | 4,277    | 1,572      | 63%       | ?                 | ?                   | ❌ CRITICAL |
| workload_enrichment            | 14,500   | 3,628      | 75%       | ?                 | ?                   | ❌ CRITICAL |

## Root Cause Analysis

The compression strategy removed examples to achieve aggressive token reduction, but **examples are non-compressible intelligence**. LLMs learn inference patterns through concrete examples, not abstract pattern descriptions.

**Perfect Run Baseline**: Used FULL prompts with 50+ total examples across inference files
**Compressed Version**: Reduced to ~12 examples total (76% example loss)
**Result**: Entity/relationship regression

## Restoration Strategy

### Phase 1: Immediate Fixes (THIS SESSION)

1. ✅ Add JSON schema templates to entity_extraction_prompt_COMPRESSED.txt
2. ✅ Add performance_metric schema to grok_json_prompt_COMPRESSED.txt

### Phase 2: Example Restoration (NEXT SESSION)

Restore ALL examples from baseline with enhancements:

#### 2.1 Workload Enrichment Enhancement

Add rich CAC example showing diverse workload drivers:

```
F.2.3.1. C.A.C Customer Service Counter and Indoor Bar: The Contractor shall handle resale
requirements to include alcohol sales. The Contractor shall service:
1) One (1) inside bar with two (2) registers located in the C.A.C.
2) One (1) additional outside bar with two (2) registers during special events.
3) One (1) additional bar with one (1) register located in Phantom Auditorium during special
events and reserved activities.

Cash registers require USN staff personnel only. The Contractor shall verify all resale supplies
necessary to ensure items are properly stocked at all times. The Contractor shall notify the
Government when resale supply levels are low, and items need to be ordered. The Government will
procure the resale supplies.

Contractor personnel shall provide retail services at minimum rates of one (1) customer per minute
during normal operations and three (3) customers per minute during peak times (0500-0700,
1100-1300, 1900-2100, 2300-0100) or during special events (e.g., concerts, 4-drink nights,
community events, all calls, promotions, wing ceremonies, etc.).

The Contractor shall open the outside bar for special events as requested by the COR. The
Government will send requests to open the outside bar for special events in writing a minimum of
seven (7) calendar days prior to the event. This is estimated to occur 100 times per year.

The C.A.C. sells between $2,000 and $5,000 alcoholic drinks per night. Majority of sales are made
from 1830 until 0200. Sales are higher during special functions and events (can exceed $10,000)
and will require additional support to meet customer demand.
```

**Workload Drivers Extracted**:

- Labor: 2+ bartenders (inside bar), 2+ bartenders (outside bar events), 1 bartender (auditorium events)
- Shifts: Peak hours 0500-0700, 1100-1300, 1900-2100, 2300-0100
- Volume: 1 customer/min normal, 3 customers/min peak
- Frequency: 100 special events/year, nightly operations 1830-0200
- Transaction volume: $2,000-$10,000/night, majority 1830-0200
- Infrastructure: 3 bars total (1 permanent, 2 event-based), 5 registers total
- Event types: Concerts, 4-drink nights, community events, wing ceremonies

#### 2.2 Deliverable Traceability Examples

Restore all 5 baseline examples + add 2 new ones:

- CDRL cross-referencing
- Implicit work-product correlation
- Timeline-based deliverable linkage
- Clause-mandated deliverables
- Proof-point deliverables (Section M)

#### 2.3 Requirement→Evaluation Examples

Restore all 19 baseline examples covering:

- Technical requirements → Technical factors
- Management requirements → Management factors
- Personnel requirements → Key Personnel factors
- Quality requirements → Quality factors
- Security requirements → Security/Technical factors
- Performance requirements → Performance factors

### Phase 3: Compression Targets (REVISED)

| Category               | Target Reduction | Method                                           |
| ---------------------- | ---------------- | ------------------------------------------------ |
| Extraction prompts     | 40-50%           | Remove redundancy, keep ALL examples             |
| Relationship inference | 50-60%           | Condense pattern descriptions, keep ALL examples |
| Overall                | 45-55%           | Balanced compression preserving intelligence     |

**Previous target**: 73% reduction (TOO AGGRESSIVE)
**Revised target**: 50% reduction (INTELLIGENCE-PRESERVING)

### Phase 4: Validation

1. Run perfect run document with restored prompts
2. Validate: 368±13 entities, 154±8 relationships
3. Compare extraction quality (entity types, descriptions, metadata)
4. Compare inference quality (relationship accuracy, confidence scores)
5. **Only deploy if validation passes**

## File Manifest (for restoration)

All baseline files extracted to `temp_baseline_*.md`:

- temp_baseline_extraction.md (entity_extraction_prompt)
- temp_baseline_detection.md (entity_detection_rules)
- temp_baseline_grok.md (grok_json_prompt)
- temp_baseline_workload_enrichment.md
- temp_baseline_deliverable_traceability.md
- temp_baseline_requirement_evaluation.md
- temp_baseline_attachment_section_linking.md
- temp_baseline_clause_clustering.md
- temp_baseline_document_hierarchy.md
- temp_baseline_document_section_linking.md
- temp_baseline_evaluation_hierarchy.md
- temp_baseline_instruction_evaluation_linking.md
- temp_baseline_semantic_concept_linking.md
- temp_baseline_sow_deliverable_linking.md
- temp_baseline_system_prompt.md

## Decision

**REVERT COMPRESSED PROMPTS**, restore baseline examples, apply conservative compression (50% target) with intelligence preservation as PRIMARY goal.

Token savings are worthless if they degrade extraction quality below baseline.
