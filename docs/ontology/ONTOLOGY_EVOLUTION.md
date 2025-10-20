# Ontology Evolution: Government Contracting RAG System

**Project**: GovCon-Capture-Vibe  
**Status**: Living Document  
**Last Updated**: October 5, 2025

This document chronicles the evolution of the government contracting ontology from initial RAG storage analysis through Path A/B iterations to the current ontology-enhanced LightRAG implementation.

---

## Table of Contents

1. [Timeline Overview](#timeline-overview)
2. [Phase 1: Initial Discovery (October 2, 2025)](#phase-1-initial-discovery-october-2-2025)
3. [Phase 2: Path A Analysis & Problems (October 3, 2025)](#phase-2-path-a-analysis--problems-october-3-2025)
4. [Phase 3: Ontology Development (October 3-4, 2025)](#phase-3-ontology-development-october-3-4-2025)
5. [Phase 4: Cross-Reference Validation (October 3, 2025)](#phase-4-cross-reference-validation-october-3-2025)
6. [Current State & Future Directions](#current-state--future-directions)

---

## Timeline Overview

```
October 2, 2025
├── Initial Navy MBOS RFP processing (Path A)
├── 772 entities, 697 relationships extracted
├── Discovery: Custom regex preprocessing creating fictitious entities
└── Decision: Investigate RAG storage for root cause analysis

October 3, 2025
├── RAG Storage Analysis completed
├── Identified critical flaws in Path A regex chunking
├── Contamination discovery: "RFP Section J-L", "Noah Carter", sports entities
├── Ontology gap analysis: DELIVERABLE entity type missing
├── Cross-reference validation against models, agents, prompts
└── Decision: Move to Path B (ontology-enhanced LightRAG)

October 4, 2025
├── DELIVERABLE entity type added (commit 7b59a94)
├── Budget handling decision: Keep as attributes, not entities
├── Architecture validation: Ontology-Models-Agents separation confirmed
├── Path B implementation planning
└── Quality gates defined: Zero contamination, zero fictitious entities

October 5, 2025 (Current)
├── Branch 002 (local) and Branch 003 (cloud) strategy finalized
├── Documentation consolidation in progress
└── Preparing for clean Path B extraction validation
```

---

## Phase 1: Initial Discovery (October 2, 2025)

### Context

First complete Navy MBOS RFP processing using **Path A** (custom regex chunking with `ShipleyRFPChunker`).

### Processing Statistics

**Document**: N6945025R0003.pdf (1,051 pages)  
**Approach**: Custom section-aware chunking with requirement-based splitting

| Metric | Value |
|--------|-------|
| Total Chunks | 157 |
| Processing Success | 157/157 (100%) |
| Entities Extracted | 772 |
| Relationships Extracted | 697 |
| Processing Time | ~3.5 hours |
| Total Storage | ~20 MB |

### What Worked ✅

1. **LightRAG Framework Robustness**
   - Processed all 157 chunks without crashes
   - Semantic entity extraction captured domain-specific concepts
   - Knowledge graph automatically constructed
   - Embeddings generated for chunks, entities, relationships

2. **Rich Metadata Preservation**
   ```json
   {
     "chunk_id": "chunk_0000",
     "section_id": "A",
     "section_title": "Solicitation/Contract Form",
     "subsection_id": "A.1",
     "page_number": 1,
     "requirements_count": 1,
     "has_requirements": true
   }
   ```

3. **Diverse Entity Capture**
   - Organizations: NAVSTA Mayport, MCSF-BI, Jacobs Technology Inc.
   - Documents: RFP Section A, PWS, various attachments
   - Contract Elements: CLINs (0008, 0016, 0019, etc.), ELINs, Sub-ELINs
   - Technical Concepts: BOE, PM, IMP, Workforce Management
   - Domain Terms: Performance Work Statement, Staffing Levels

4. **Meaningful Relationships**
   - `["Prime Contractor", "Subcontractors"]`
   - `["RFP Section M", "Technical Factors"]`
   - `["Contract Term", "Option Periods"]`

### Critical Problems Discovered ⚠️

#### 1. Fictitious Entities from Regex Preprocessing

**Evidence from Knowledge Graph**:
```xml
<node id="RFP Section J-L">
  <!-- DOES NOT EXIST in Uniform Contract Format -->
  <!-- Should be: Section J, Section K, Section L separately -->
</node>

<node id="RFP Section J-Line">
  <!-- Nonsensical - caused by regex matching "Attachment Line Item" -->
</node>

<node id="Attachment L">
  <!-- DOES NOT EXIST - misidentified by faulty regex -->
</node>
```

**Root Cause**: `ShipleyRFPChunker` regex patterns created malformed section identifiers:
```python
# Path A mistake (archived):
section_pattern = r"Section ([A-M])"  # Brittle, deterministic
# Created: "J-L", "J-Line", "Attachment L" (all invalid)
```

**Impact**:
- Knowledge graph contained invalid entities
- Queries for "Section J" or "Section L" failed (merged into fictitious "J-L")
- Semantic search broken for proper Uniform Contract Format sections
- Ontology validation impossible with corrupted base entities

#### 2. Contamination from External Knowledge

**Sports-Related Entities** (not in RFP):
- "100m Sprint Record"
- "Carbon-Fiber Spikes"
- "Noah Carter"
- "World Athletics Championship"
- "Tokyo"

**Financial Markets Entities** (not in RFP):
- "Market Selloff"
- "Gold Futures"
- "Crude Oil"
- "Federal Reserve Policy"
- "Global Tech Index"

**Total Contamination**: 11 external entities in Path A extraction

**Root Cause**: LLM introducing external knowledge during extraction with no validation:
1. No type-safe structured outputs
2. No document isolation verification
3. No Pydantic validation
4. Prompts didn't strictly constrain to source text

#### 3. Unconstrained Entity Extraction

**Chunk 136 Problem**:
- 113 entities + 111 relationships extracted
- 24 minutes processing time
- LLM extracted every table row as separate entity
- No maximum entity limit
- No entity type validation

**Generic/Broken Entities**:
- "nce assessment" (truncated)
- "rounding" (too generic)
- "17" (attachment number cleaned incorrectly)

#### 4. Invalid Entity Types

**Examples**:
```
WARNING | invalid entity type in:
  ['entity', 'Numbers H700 through H718', 'ELINs/Sub-ELINs', ...]
  ['entity', 'H015', 'ELIN/Sub-ELIN', ...]
```

**Root Cause**: LLM inventing types like "ELINs/Sub-ELINs" not in LightRAG's default schema

### Key Insight 🎯

**"Garbage In, Garbage Out"**

LightRAG faithfully extracted what we fed it. The problem wasn't LightRAG—it was our faulty regex preprocessing creating malformed inputs. Path A's custom chunking didn't just add redundancy, it **introduced errors** that propagated throughout the knowledge graph.

**Path Forward**: Remove regex preprocessing, let LLM understand semantically, guide with ontology, validate outputs.

---

## Phase 2: Path A Analysis & Problems (October 3, 2025)

### Comparative Metrics

| Metric | Plan A | Plan B | Analysis |
|--------|--------|--------|----------|
| **Entities** | 772 | 569 | Plan A +35.7% (but includes noise) |
| **Relationships** | 697 | 426 | Plan A +63.6% |
| **Rel/Entity Ratio** | 0.90 | 0.75 | Plan A +20% density |
| **Contamination** | 11 entities | 6 entities | Both FAILED |
| **Section Coverage** | 90% (A-M) | 60% (partial) | Plan A better coverage |
| **Isolated Entities** | ~25% | 19% | Plan B slight edge |

### Path A Strengths

1. **Section-Aware Chunking**
   - Sophisticated regex patterns identified all RFP sections (A-M) with subsections
   - Preserved "Section L.3.1" as context (vs random text fragments in Plan B)

2. **Requirement-Based Splitting**
   - Split requirement-heavy sections into manageable chunks (3 requirements max)
   - Prevented LLM timeouts on Section C, Section L (400+ pages)
   - Each chunk processable within token limits

3. **Relationship Mapping**
   - Pre-populated valid RFP relationships (L→M, C→B)
   - Guided extraction toward domain-valid patterns
   - Created 63.6% more relationships than Plan B

### Path A Critical Flaws

1. **Fictitious Entities**
   - "RFP Section J-L" (should be J, K, L separately)
   - "RFP Section J-Line" (nonsensical)
   - "Attachment L" (doesn't exist)

2. **Regex Brittleness**
   - Failed on real-world RFP variations
   - Cut content mid-paragraph when patterns matched
   - Over-extraction (772 entities) was quantity, not quality

3. **No Validation**
   - No type-safe structured outputs
   - No document isolation checks
   - 11 contaminated entities from external knowledge

### Path B Strengths

1. **Lower Contamination**
   - 6 entities vs 11 (both still unacceptable)
   - Cleaner entities overall

2. **No Fictitious Entities**
   - No regex artifacts like "Section J-L"
   - Semantic understanding prevented nonsensical combinations

3. **Better Entity Quality**
   - 569 entities were cleaner (fewer regex artifacts)
   - Better isolation (19% vs 25%)

### Path B Weaknesses

1. **Generic Chunking Lost Structure**
   - Missed section boundaries
   - Lost subsection hierarchy
   - Lower relationship density (0.75 vs 0.90)

2. **Surface Ontology Integration**
   - Insufficient domain knowledge injection
   - Generic entity types ("person", "location")
   - Didn't understand government contracting concepts

3. **Fewer Relationships**
   - 271 fewer relationships than Path A
   - Lower graph connectivity
   - Missed L↔M critical connections

### Decision Point

**Neither Path A nor Path B achieved production quality alone.**

Path A had better metrics but created fictitious entities. Path B was cleaner but missed structure.

**Solution**: Combine the best of both approaches with validation.

---

## Phase 3: Ontology Development (October 3-4, 2025)

### Ontology Design Principles

**Core Principle**: Let LLMs understand semantically, guide with domain knowledge, validate outputs.

**Three-Layer Architecture**:
```
┌─────────────────────────────────────────────┐
│ ONTOLOGY (src/core/ontology.py)            │
│ - Entity types: SECTION, REQUIREMENT, etc. │
│ - Relationship patterns: REFERENCES, etc.   │
│ - Validation: VALID_RELATIONSHIPS           │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ MODELS (src/models/rfp_models.py)          │
│ - RFPRequirement: Shipley methodology      │
│ - ComplianceAssessment: 4-level scale      │
│ - Type-safe Pydantic models                │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│ AGENTS (src/agents/rfp_agents.py)          │
│ - Intelligent extraction with business logic│
│ - Shipley Guide standards application       │
│ - Gap analysis, recommendations             │
└─────────────────────────────────────────────┘
```

### EntityType Enum Evolution

**Initial Design** (11 types):
```python
class EntityType(str, Enum):
    SECTION = "SECTION"              # RFP sections (A-M) + subsections
    REQUIREMENT = "REQUIREMENT"      # Contractor obligations (shall/must)
    CLAUSE = "CLAUSE"                # FAR/DFARS clauses
    ORGANIZATION = "ORGANIZATION"    # Companies, agencies
    PERSON = "PERSON"                # POCs, contracting officers
    LOCATION = "LOCATION"            # Performance sites, facilities
    TECHNOLOGY = "TECHNOLOGY"        # Systems, software, tools
    CONCEPT = "CONCEPT"              # CLINs, terms, abstract concepts
    EVENT = "EVENT"                  # Milestones, deadlines, deliveries
    DOCUMENT = "DOCUMENT"            # Attachments, references
    # DELIVERABLE added in Phase 3 (see below)
```

**Phase 3 Addition** (October 4, 2025 - Commit 7b59a94):
```python
DELIVERABLE = "DELIVERABLE"  # Contract deliverables, work products
```

**Rationale**:
1. Explicitly listed in `extract_requirements_prompt.txt`
2. `RFPSection` model has `deliverables` field
3. FAR 15.210 Section F is "Deliveries or Performance"
4. Shipley methodology treats deliverables as key evaluation factors
5. Korean AI RFP Simulator tracks `deliverables[]` separately from `requirements[]`

### Relationship Pattern Evolution

**Valid Relationship Patterns**:
```python
VALID_RELATIONSHIPS: Dict[Tuple[str, str], List[str]] = {
    # Section relationships
    ("SECTION", "REFERENCES"): ["SECTION", "DOCUMENT", "CLAUSE"],
    ("SECTION", "CONTAINS"): ["REQUIREMENT", "DELIVERABLE", "CLAUSE"],
    ("SECTION", "APPLIES_TO"): ["ORGANIZATION", "LOCATION"],
    ("SECTION", "EVALUATES"): ["SECTION"],  # M evaluates L
    
    # Requirement relationships
    ("REQUIREMENT", "PRODUCES"): ["DELIVERABLE"],  # ← Added Phase 3
    ("REQUIREMENT", "REQUIRES"): ["TECHNOLOGY", "ORGANIZATION"],
    ("REQUIREMENT", "REFERENCES"): ["CLAUSE", "DOCUMENT"],
    ("REQUIREMENT", "APPLIES_TO"): ["SECTION"],
    
    # Deliverable relationships (Phase 3)
    ("DELIVERABLE", "REQUIRES"): ["TECHNOLOGY", "ORGANIZATION", "CONCEPT"],
    ("DELIVERABLE", "DELIVERED_BY"): ["ORGANIZATION"],
    ("DELIVERABLE", "SUPPORTS"): ["REQUIREMENT", "SECTION"],
    ("DELIVERABLE", "PERFORMED_AT"): ["LOCATION"],
    ("DELIVERABLE", "DUE_BY"): ["EVENT"],
    
    # Concept relationships (CLINs)
    ("CONCEPT", "INCLUDES"): ["DELIVERABLE"],  # CLIN includes deliverables
    ("CONCEPT", "FUNDS"): ["REQUIREMENT"],
    
    # Event relationships
    ("EVENT", "MILESTONE_FOR"): ["DELIVERABLE"],
    
    # ... (full schema in src/core/ontology.py)
}
```

### Budget/Financial Decision

**Question**: Should budget/financial data be a separate entity type?

**Options Considered**:

**Option A: Add FINANCIAL entity**
```python
FINANCIAL = "FINANCIAL"  # Budget line items, pricing, cost data
```
✅ Pros: Explicit semantic representation, enables financial-specific relationships  
❌ Cons: Financial data is often an attribute, over-complicates graph

**Option B: Keep as attributes (CHOSEN)**
```python
# CLIN as CONCEPT with financial attributes
{
  "entity_name": "CLIN 0001",
  "entity_type": "CONCEPT",
  "metadata": {
    "value": "$500,000",
    "budget_year": "base_year"
  }
}
```
✅ Pros: Cleaner graph, budget is metadata not standalone concept  
❌ Cons: Can't query "all financial entities" directly

**Decision Rationale**:
- Budget appears in prompts but is typically metadata
- CLINs already handle pricing as CONCEPT entities
- "Budget: $500,000" doesn't need entity status
- Follows best practices: entities are things, attributes are properties
- Can add FINANCIAL later if testing reveals need

**Documented**: October 4, 2025 (Phase 3 Priority 2)

---

## Phase 4: Cross-Reference Validation (October 3, 2025)

### Validation Against Models

**Source**: `src/models/rfp_models.py`

| Model Enum/Class | Ontology EntityType | Alignment | Notes |
|------------------|---------------------|-----------|-------|
| `RFPSectionType` (A-M) | ✅ `SECTION` | GOOD | FAR 15.210 sections |
| `RequirementType` | ✅ `REQUIREMENT` | GOOD | Covered |
| `ComplianceLevel` | ⚠️ N/A | APPROPRIATE | Analysis metadata |
| `ComplianceStatus` | ⚠️ N/A | APPROPRIATE | Assessment outcome |
| `RiskLevel` | ⚠️ N/A | APPROPRIATE | Risk assessment |
| FAR clauses | ✅ `CLAUSE` | GOOD | Contract clauses |
| **Deliverables** | ✅ `DELIVERABLE` | FIXED | Added Phase 3 |
| CLINs | ✅ `CONCEPT` | ACCEPTABLE | Modeled as concepts |
| Organizations | ✅ `ORGANIZATION` | GOOD | Covered |
| Persons | ✅ `PERSON` | GOOD | POCs, officers |
| Locations | ✅ `LOCATION` | GOOD | Performance sites |
| Events | ✅ `EVENT` | GOOD | Milestones |
| Documents | ✅ `DOCUMENT` | GOOD | Attachments |
| Technical specs | ✅ `TECHNOLOGY` | GOOD | Systems, software |

**Result**: 11/14 entities aligned (79% - up from 71% before DELIVERABLE addition)

**Appropriate Non-Entities**: ComplianceLevel, ComplianceStatus, RiskLevel are analysis metadata, not knowledge graph entities. This is correct architectural separation.

### Validation Against Agents

**Source**: `src/agents/rfp_agents.py`

| Agent Analysis Type | Ontology RelationshipType | Alignment | Notes |
|---------------------|---------------------------|-----------|-------|
| L↔M Section connections | ✅ `REFERENCES`, `EVALUATES` | GOOD | Critical relationships |
| Requirements → Clauses | ✅ `REFERENCES`, `APPLIES_TO` | GOOD | Clause application |
| Section I applications | ✅ `APPLIES_TO` | GOOD | Contract clauses |
| Section C dependencies | ✅ `DEPENDS_ON`, `REQUIRES` | GOOD | SOW dependencies |
| J attachment support | ✅ `SUPPORTS` | GOOD | Attachments |
| Compliance evidence | ⚠️ N/A | APPROPRIATE | Analysis layer |
| Win theme alignment | ⚠️ N/A | APPROPRIATE | Business logic |
| Gap mitigation | ⚠️ N/A | APPROPRIATE | Analysis outcome |

**Result**: 5/8 relationship types covered (63%)

**Good Coverage**: Core knowledge graph relationships properly represented.

**Appropriate Separation**: Compliance/win theme/gap relationships belong in agents (analysis layer), not ontology (semantic layer).

### Validation Against Prompts

**Source**: `prompts/extract_requirements_prompt.txt`

| Prompt Field | Ontology Coverage | Status | Notes |
|--------------|-------------------|--------|-------|
| `client_company` | ✅ `ORGANIZATION` | GOOD | Covered |
| `department` | ✅ `ORGANIZATION` | GOOD | Covered |
| `project_background` | ✅ `CONCEPT` | GOOD | High-level concept |
| `objectives` | ✅ `REQUIREMENT` | GOOD | Project objectives |
| `scope` | ✅ `SECTION` (Section C) | GOOD | SOW section |
| `timeline` | ✅ `EVENT` | GOOD | Schedule events |
| `budget` | ✅ `CONCEPT` (attribute) | FIXED | Decided: Keep as attribute |
| `evaluation_criteria` | ✅ `REQUIREMENT` (Section M) | GOOD | Evaluation factors |
| **`deliverables`** | ✅ `DELIVERABLE` | FIXED | Added Phase 3 |
| `bidder_requirements` | ✅ `REQUIREMENT` | GOOD | Covered |
| `compliance_items` | ✅ `CLAUSE` | GOOD | Contract clauses |
| `risk_management` | ⚠️ N/A | APPROPRIATE | Analysis metadata |
| `required_competencies` | ✅ `REQUIREMENT` | GOOD | Qualification requirements |
| `schedule` | ✅ `EVENT` | GOOD | Timeline events |
| `special_conditions` | ✅ `REQUIREMENT` | GOOD | Special requirements |
| `packaging_marking` | ✅ `SECTION` (Section D) | GOOD | Covered |
| `inspection_acceptance` | ✅ `SECTION` (Section E) | GOOD | Covered |
| `contract_admin_data` | ✅ `SECTION` (Section G) | GOOD | Covered |
| `contract_clauses` | ✅ `CLAUSE` (Section I) | GOOD | Covered |
| `representations` | ✅ `SECTION` (Section K) | GOOD | Covered |

**Result**: 19/20 fields covered (95% - up from 85% before fixes)

**Appropriate Non-Entities**: `risk_management` (analysis metadata, not entity)

### External Validation: AI RFP Simulator

**Source**: https://github.com/felixlkw/ai-rfp-simulator (Korean RFP system)

```typescript
interface RfpAnalysisData {
  projectTitle: string;        // ✅ Our: CONCEPT
  organization: string;         // ✅ Our: ORGANIZATION
  description: string;          // Text field, not entity
  deadline: string;             // ✅ Our: EVENT
  budget: string;               // ✅ Our: CONCEPT attribute
  projectPeriod: string;        // ✅ Our: EVENT
  requirements: string[];       // ✅ Our: REQUIREMENT
  technicalSpecs: string[];     // ✅ Our: TECHNOLOGY
  deliverables: string[];       // ✅ Our: DELIVERABLE (added Phase 3)
  evaluationCriteria: string[]; // ✅ Our: REQUIREMENT (Section M)
  submissionFormat: string;     // ✅ Our: REQUIREMENT (Section L)
  contactInfo: string;          // ✅ Our: PERSON
  industryType: string;         // Metadata
  projectComplexity: string;    // Metadata
  competitionLevel: string;     // Metadata (competitive analysis)
}
```

**Key Validation**: Korean RFP system explicitly tracks `deliverables[]` as separate from `requirements[]`, confirming our need for DELIVERABLE entity type.

**Lesson Learned**: Their hybrid approach (deterministic extraction + LLM refinement) is similar to our ontology validation (semantic extraction + constraint validation).

---

## Current State & Future Directions

### Phase 3 Status (October 4, 2025)

**Completed** ✅:
1. DELIVERABLE entity type added (commit 7b59a94)
2. Budget handling decision documented (keep as CONCEPT attributes)
3. DELIVERABLE relationships integrated into VALID_RELATIONSHIPS
4. Cross-reference validation completed (95% alignment with prompts)
5. Architecture validated: Ontology-Models-Agents separation is sound

**In Progress** ⏳:
1. Clean Path B extraction validation (Navy MBOS RFP re-run)
2. Quality comparison documentation
3. Zero contamination validation testing

### Expected Outcomes (Clean Path B Extraction)

| Metric | Path A | Path B (Target) |
|--------|--------|-----------------|
| Entities | 772 (noisy) | 600-700 (validated) |
| Relationships | 697 | 500-600 (domain-valid) |
| Rel/Entity Ratio | 0.90 | 1.2+ (denser) |
| **Contamination** | 11 | **0** (MUST ACHIEVE) |
| **Fictitious Entities** | Yes ("J-L") | **0** (MUST ACHIEVE) |
| Section Coverage | 90% | 100% (A-M all) |
| Isolated Entities | ~25% | <10% |
| Processing Time | ~76 min | <60 min |

### Quality Gates

**Phase 3 Gate** (Current):
- ✅ Zero fictitious entities (semantic understanding, no regex)
- ✅ DELIVERABLE entity type operational
- ⏳ Zero contamination (PydanticAI validation in progress)
- ⏳ 100% entity type compliance
- ⏳ Document isolation verified

**Phase 4 Gate** (Testing):
- All relationships match VALID_RELATIONSHIPS
- Section hierarchy preserved (parent→child)
- L↔M critical connections maintained
- Navy MBOS RFP processed successfully

**Production Gate** (Branch 002/003):
- All metrics meet or exceed targets
- No quality regressions vs Path A/B
- Performance benchmarks met
- Documentation complete

### Test Cases Planned

**Test Case 1: Section L Extraction**
- Input: Sample Section L (Instructions to Offerors)
- Expected: SECTION, REQUIREMENT, DOCUMENT entities with L→M relationships
- Validation: No fictitious entities like "Section J-L"

**Test Case 2: Section C + CLINs + Deliverables**
- Input: Sample Section C (SOW) with CLINs
- Expected: SECTION, REQUIREMENT, CONCEPT, DELIVERABLE, TECHNOLOGY entities
- Validation: CLIN→DELIVERABLE relationships correct

**Test Case 3: Section M Evaluation Factors**
- Input: Sample Section M with evaluation criteria
- Expected: SECTION, REQUIREMENT, CONCEPT entities with M→L relationships
- Validation: Evaluation factors classified correctly

**Test Case 4: End-to-End Compliance Matrix**
- Input: Full RFP with Sections L, M, C
- Process: LightRAG extraction → Ontology validation → PydanticAI agents → Shipley methodology
- Validation: Clean pipeline, no data loss between layers

### Architecture Lessons Learned

#### 1. Regex is Not the Answer
- Regex preprocessing created fictitious entities ("Section J-L")
- Brittle patterns failed on real-world variations
- Over-extraction appeared better but was actually noise

**Lesson**: Let LLMs understand semantically, not through pattern matching.

#### 2. Preprocessing Can Enhance RAG (When Done Right)
- Path A's requirement-based splitting prevented timeouts
- Section context preservation improved extraction quality
- Relationship hints guided LLM toward valid patterns

**Lesson**: Preprocessing + RAG + Validation = Production Quality (not preprocessing alone).

#### 3. Validation is Non-Negotiable
- Both Path A and Path B had contamination
- No type-safe outputs, no document isolation checks
- No automated quality control

**Lesson**: PydanticAI validation is ESSENTIAL for production.

#### 4. Domain Knowledge Matters
- Generic LightRAG doesn't understand government contracting
- Never seen RFPs, CLINs, FAR clauses in training
- Extracts generic entities ("person", "location") not domain concepts

**Lesson**: Ontology injection is CRITICAL for domain-specific RAG.

#### 5. Entities vs Attributes vs Metadata
- Entities: Things that exist independently (SECTION, REQUIREMENT, DELIVERABLE)
- Attributes: Properties of entities (budget as CLIN attribute, $500,000)
- Metadata: Analysis outcomes (ComplianceLevel, RiskLevel, win themes)

**Lesson**: Don't over-complicate knowledge graph. Keep analysis layer separate from semantic layer.

### Branch Strategy Integration

**Branch 002** (Local LLM Architecture):
- Fully local Ollama processing
- Uses ontology-enhanced LightRAG from `src/lightrag/`
- Zero contamination via PydanticAI validation
- 100% private, air-gapped capable

**Branch 003** (Cloud-Enhanced Architecture):
- Hybrid: xAI Grok for public RFPs (fast), local Ollama for proprietary (private)
- Same ontology foundation as Branch 002
- 20-30x faster processing for non-sensitive documents
- Enterprise privacy boundaries maintained

**Main Branch**:
- Reserved for production-ready releases
- Will merge from Branch 003 after validation
- Full test suite passing
- Documentation complete

### Next Steps

**Immediate** (Week 1):
1. Complete clean Path B extraction (Navy MBOS RFP)
2. Validate zero contamination with PydanticAI
3. Document quality comparison vs Path A
4. Update test cases with DELIVERABLE entity

**Short-Term** (Weeks 2-3):
1. Test all 4 comprehensive test cases
2. Benchmark performance (<60 min target)
3. Document architectural decisions
4. Merge to Branch 002 parent

**Medium-Term** (Week 4+):
1. Fork Branch 003 for cloud enhancement
2. Implement xAI Grok integration
3. Test hybrid workflow (public→cloud, proprietary→local)
4. Prepare for production release (merge to main)

---

## References

### Primary Documents
- **Navy MBOS RFP**: N6945025R0003.pdf (1,051 pages) - Primary test document
- **Shipley Guides**: `docs/Shipley Capture Guide.pdf`, `docs/Shipley Proposal Guide.pdf`
- **FAR 15.210**: Uniform Contract Format (Sections A-M standard)

### Source Code
- **Ontology**: `src/core/ontology.py` (EntityType enum, VALID_RELATIONSHIPS)
- **Models**: `src/models/rfp_models.py` (Pydantic models with Shipley methodology)
- **Agents**: `src/agents/rfp_agents.py` (PydanticAI agents for extraction/assessment)
- **Prompts**: `prompts/extract_requirements_prompt.txt` (Shipley-based extraction)

### External References
- **LightRAG**: https://github.com/HKUDS/LightRAG (v1.4.9 forked to `src/lightrag/`)
- **PydanticAI**: https://ai.pydantic.dev/ (type-safe LLM outputs)
- **AI RFP Simulator**: https://github.com/felixlkw/ai-rfp-simulator (Korean RFP system validation)

### Related Documentation
- **Architecture Decision Records**: `docs/ARCHITECTURE_DECISION_RECORDS.md`
- **README**: Project overview with Branch 002/003 strategy
- **Shipley Reference**: `docs/SHIPLEY_LLM_CURATED_REFERENCE.md`

---

**Document Status**: Living document - updated as ontology evolves and new phases complete.

**Version History**:
- v1.0.0 (October 5, 2025): Initial consolidation of RAG storage analysis and ontology alignment analysis into chronological evolution format
