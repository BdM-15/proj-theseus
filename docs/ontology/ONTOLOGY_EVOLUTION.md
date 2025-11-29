# Ontology Evolution: Government Contracting RAG System

**Project**: GovCon-Capture-Vibe (Project Theseus)  
**Status**: Living Document  
**Version**: 0.3.0  
**Last Updated**: November 28, 2025

This document chronicles the evolution of the government contracting ontology from initial RAG storage analysis through Path A/B iterations to the current production system with **18 entity types**, **8 semantic post-processing algorithms**, and **Neo4j enterprise storage**.

---

## Table of Contents

1. [Timeline Overview](#timeline-overview)
2. [Phase 1: Initial Discovery (October 2, 2025)](#phase-1-initial-discovery-october-2-2025)
3. [Phase 2: Path A Analysis & Problems (October 3, 2025)](#phase-2-path-a-analysis--problems-october-3-2025)
4. [Phase 3: Ontology Development (October 3-4, 2025)](#phase-3-ontology-development-october-3-4-2025)
5. [Phase 4: Cross-Reference Validation (October 3, 2025)](#phase-4-cross-reference-validation-october-3-2025)
6. [Phase 5: Cloud Acceleration & Entity Expansion (October-November 2025)](#phase-5-cloud-acceleration--entity-expansion-october-november-2025)
7. [Phase 6: Semantic Post-Processing & Neo4j (November 2025)](#phase-6-semantic-post-processing--neo4j-november-2025)
8. [Current State: Production System](#current-state-production-system)

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

October 5, 2025
├── Branch 002 (local) and Branch 003 (cloud) strategy finalized
├── Documentation consolidation in progress
└── Preparing for clean Path B extraction validation

October-November 2025 (Phase 5: Cloud Acceleration)
├── xAI Grok integration completed (significant speedup over local)
├── RAG-Anything + LightRAG pip packages adopted (no forked libraries)
├── Entity types expanded: 11 → 18 specialized types
├── Instructor + Pydantic schema validation implemented
├── MinerU multimodal parsing integrated
└── Processing: 30-60 minutes per RFP (~$4 cost)

November 2025 (Phase 6: Semantic Post-Processing) ✅ CURRENT
├── 8 LLM-powered relationship inference algorithms
├── Neo4j 5.25 enterprise storage (Docker)
├── Section L↔M mapping automated
├── Workload enrichment with BOE categories
├── Full RFP processing: 30-60 minutes (~$4/RFP)
└── Production-ready on main branch
```

---

## Phase 1: Initial Discovery (October 2, 2025)

### Context

First complete Navy MBOS RFP processing using **Path A** (custom regex chunking with `ShipleyRFPChunker`).

### Processing Statistics

**Document**: N6945025R0003.pdf (1,051 pages)  
**Approach**: Custom section-aware chunking with requirement-based splitting

| Metric                  | Value          |
| ----------------------- | -------------- |
| Total Chunks            | 157            |
| Processing Success      | 157/157 (100%) |
| Entities Extracted      | 772            |
| Relationships Extracted | 697            |
| Processing Time         | ~3.5 hours     |
| Total Storage           | ~20 MB         |

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

| Metric                | Plan A      | Plan B        | Analysis                           |
| --------------------- | ----------- | ------------- | ---------------------------------- |
| **Entities**          | 772         | 569           | Plan A +35.7% (but includes noise) |
| **Relationships**     | 697         | 426           | Plan A +63.6%                      |
| **Rel/Entity Ratio**  | 0.90        | 0.75          | Plan A +20% density                |
| **Contamination**     | 11 entities | 6 entities    | Both FAILED                        |
| **Section Coverage**  | 90% (A-M)   | 60% (partial) | Plan A better coverage             |
| **Isolated Entities** | ~25%        | 19%           | Plan B slight edge                 |

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

**Phase 5 Expansion** (October-November 2025):
Entity types expanded from 12 to **18** to capture government contracting nuances:

```python
# Current 18 entity types (src/ontology/schema.py)
VALID_ENTITY_TYPES = {
    # Generic types (6)
    "organization", "concept", "event", "technology", "person", "location",
    # Government contracting specialized types (12)
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
}
```

**New Specialized Types Added**:

- `evaluation_factor` - Section M scoring criteria with weights
- `submission_instruction` - Section L page limits, format requirements
- `strategic_theme` - Win themes, discriminators, hot buttons
- `program` - Government program names (AFCAPV, MCPP II)
- `equipment` - GFE/CFE items
- `statement_of_work` - SOW/PWS task descriptions
- `performance_metric` - KPIs, QASP standards with thresholds

**Rationale**:

1. Explicitly listed in `extract_requirements_prompt.txt`
2. `RFPSection` model has `deliverables` field
3. FAR 15.210 Section F is "Deliveries or Performance"
4. Shipley methodology treats deliverables as key evaluation factors
5. Korean AI RFP Simulator tracks `deliverables[]` separately from `requirements[]`
6. Specialized types enable Section L↔M relationship inference

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

| Model Enum/Class       | Ontology EntityType | Alignment   | Notes               |
| ---------------------- | ------------------- | ----------- | ------------------- |
| `RFPSectionType` (A-M) | ✅ `SECTION`        | GOOD        | FAR 15.210 sections |
| `RequirementType`      | ✅ `REQUIREMENT`    | GOOD        | Covered             |
| `ComplianceLevel`      | ⚠️ N/A              | APPROPRIATE | Analysis metadata   |
| `ComplianceStatus`     | ⚠️ N/A              | APPROPRIATE | Assessment outcome  |
| `RiskLevel`            | ⚠️ N/A              | APPROPRIATE | Risk assessment     |
| FAR clauses            | ✅ `CLAUSE`         | GOOD        | Contract clauses    |
| **Deliverables**       | ✅ `DELIVERABLE`    | FIXED       | Added Phase 3       |
| CLINs                  | ✅ `CONCEPT`        | ACCEPTABLE  | Modeled as concepts |
| Organizations          | ✅ `ORGANIZATION`   | GOOD        | Covered             |
| Persons                | ✅ `PERSON`         | GOOD        | POCs, officers      |
| Locations              | ✅ `LOCATION`       | GOOD        | Performance sites   |
| Events                 | ✅ `EVENT`          | GOOD        | Milestones          |
| Documents              | ✅ `DOCUMENT`       | GOOD        | Attachments         |
| Technical specs        | ✅ `TECHNOLOGY`     | GOOD        | Systems, software   |

**Result**: 11/14 entities aligned (79% - up from 71% before DELIVERABLE addition)

**Appropriate Non-Entities**: ComplianceLevel, ComplianceStatus, RiskLevel are analysis metadata, not knowledge graph entities. This is correct architectural separation.

### Validation Against Agents

**Source**: `src/agents/rfp_agents.py`

| Agent Analysis Type     | Ontology RelationshipType     | Alignment   | Notes                  |
| ----------------------- | ----------------------------- | ----------- | ---------------------- |
| L↔M Section connections | ✅ `REFERENCES`, `EVALUATES`  | GOOD        | Critical relationships |
| Requirements → Clauses  | ✅ `REFERENCES`, `APPLIES_TO` | GOOD        | Clause application     |
| Section I applications  | ✅ `APPLIES_TO`               | GOOD        | Contract clauses       |
| Section C dependencies  | ✅ `DEPENDS_ON`, `REQUIRES`   | GOOD        | SOW dependencies       |
| J attachment support    | ✅ `SUPPORTS`                 | GOOD        | Attachments            |
| Compliance evidence     | ⚠️ N/A                        | APPROPRIATE | Analysis layer         |
| Win theme alignment     | ⚠️ N/A                        | APPROPRIATE | Business logic         |
| Gap mitigation          | ⚠️ N/A                        | APPROPRIATE | Analysis outcome       |

**Result**: 5/8 relationship types covered (63%)

**Good Coverage**: Core knowledge graph relationships properly represented.

**Appropriate Separation**: Compliance/win theme/gap relationships belong in agents (analysis layer), not ontology (semantic layer).

### Validation Against Prompts

**Source**: `prompts/extract_requirements_prompt.txt`

| Prompt Field            | Ontology Coverage            | Status      | Notes                      |
| ----------------------- | ---------------------------- | ----------- | -------------------------- |
| `client_company`        | ✅ `ORGANIZATION`            | GOOD        | Covered                    |
| `department`            | ✅ `ORGANIZATION`            | GOOD        | Covered                    |
| `project_background`    | ✅ `CONCEPT`                 | GOOD        | High-level concept         |
| `objectives`            | ✅ `REQUIREMENT`             | GOOD        | Project objectives         |
| `scope`                 | ✅ `SECTION` (Section C)     | GOOD        | SOW section                |
| `timeline`              | ✅ `EVENT`                   | GOOD        | Schedule events            |
| `budget`                | ✅ `CONCEPT` (attribute)     | FIXED       | Decided: Keep as attribute |
| `evaluation_criteria`   | ✅ `REQUIREMENT` (Section M) | GOOD        | Evaluation factors         |
| **`deliverables`**      | ✅ `DELIVERABLE`             | FIXED       | Added Phase 3              |
| `bidder_requirements`   | ✅ `REQUIREMENT`             | GOOD        | Covered                    |
| `compliance_items`      | ✅ `CLAUSE`                  | GOOD        | Contract clauses           |
| `risk_management`       | ⚠️ N/A                       | APPROPRIATE | Analysis metadata          |
| `required_competencies` | ✅ `REQUIREMENT`             | GOOD        | Qualification requirements |
| `schedule`              | ✅ `EVENT`                   | GOOD        | Timeline events            |
| `special_conditions`    | ✅ `REQUIREMENT`             | GOOD        | Special requirements       |
| `packaging_marking`     | ✅ `SECTION` (Section D)     | GOOD        | Covered                    |
| `inspection_acceptance` | ✅ `SECTION` (Section E)     | GOOD        | Covered                    |
| `contract_admin_data`   | ✅ `SECTION` (Section G)     | GOOD        | Covered                    |
| `contract_clauses`      | ✅ `CLAUSE` (Section I)      | GOOD        | Covered                    |
| `representations`       | ✅ `SECTION` (Section K)     | GOOD        | Covered                    |

**Result**: 19/20 fields covered (95% - up from 85% before fixes)

**Appropriate Non-Entities**: `risk_management` (analysis metadata, not entity)

### External Validation: AI RFP Simulator

**Source**: https://github.com/felixlkw/ai-rfp-simulator (Korean RFP system)

```typescript
interface RfpAnalysisData {
  projectTitle: string; // ✅ Our: CONCEPT
  organization: string; // ✅ Our: ORGANIZATION
  description: string; // Text field, not entity
  deadline: string; // ✅ Our: EVENT
  budget: string; // ✅ Our: CONCEPT attribute
  projectPeriod: string; // ✅ Our: EVENT
  requirements: string[]; // ✅ Our: REQUIREMENT
  technicalSpecs: string[]; // ✅ Our: TECHNOLOGY
  deliverables: string[]; // ✅ Our: DELIVERABLE (added Phase 3)
  evaluationCriteria: string[]; // ✅ Our: REQUIREMENT (Section M)
  submissionFormat: string; // ✅ Our: REQUIREMENT (Section L)
  contactInfo: string; // ✅ Our: PERSON
  industryType: string; // Metadata
  projectComplexity: string; // Metadata
  competitionLevel: string; // Metadata (competitive analysis)
}
```

**Key Validation**: Korean RFP system explicitly tracks `deliverables[]` as separate from `requirements[]`, confirming our need for DELIVERABLE entity type.

**Lesson Learned**: Their hybrid approach (deterministic extraction + LLM refinement) is similar to our ontology validation (semantic extraction + constraint validation).

---

## Phase 5: Cloud Acceleration & Entity Expansion (October-November 2025)

### The Cloud Pivot

**Problem**: Local Ollama processing (Mistral-Nemo 12B) required 3-8 hours per RFP.

**Solution**: xAI Grok cloud processing for public government documents.

| Metric       | Local (Branch 002) | Cloud (Branch 003+) | Improvement          |
| ------------ | ------------------ | ------------------- | -------------------- |
| 71-page RFP  | ~8 hours           | 30-40 minutes       | **~12x faster**      |
| 425-page RFP | ~16 hours          | 45-60 minutes       | **~16x faster**      |
| Cost per RFP | $0 (local)         | ~$4                 | Acceptable for speed |

### Architecture Evolution

**Before (Branch 002)**:

```
PDF → Custom ShipleyRFPChunker → Ollama (local) → LightRAG (forked at src/lightrag/)
```

**After (Branch 003+)**:

```
PDF → MinerU (via RAG-Anything) → xAI Grok → LightRAG (pip: lightrag-hku) → Neo4j
```

### Key Changes

1. **No More Forked Libraries**

   - Removed: `src/lightrag/` forked directory
   - Added: `lightrag-hku>=1.4.9.7` pip package
   - Added: `raganything[all]>=1.2.8` pip package

2. **Instructor + Pydantic Schema Validation**

   - All LLM outputs validated against `src/ontology/schema.py`
   - Invalid entity types coerced to `concept` with warning
   - Zero contamination from external knowledge

3. **MinerU Multimodal Parsing**

   - Tables extracted with structure preserved
   - Images processed (future: figure extraction)
   - Equations handled (for technical RFPs)

4. **Entity Type Expansion**: 12 → 18 types
   - Added 6 specialized Pydantic models with unique fields
   - 12 generic types use `BaseEntity` directly

### 18 Entity Types Architecture

**6 Specialized Models** (have unique fields for structured extraction):

| Model                   | Unique Fields                                                              | Purpose                     |
| ----------------------- | -------------------------------------------------------------------------- | --------------------------- |
| `Requirement`           | `criticality`, `modal_verb`, `req_type`, `labor_drivers`, `material_needs` | SHALL/SHOULD/MAY + workload |
| `EvaluationFactor`      | `weight`, `importance`, `subfactors`                                       | Section M scoring           |
| `SubmissionInstruction` | `page_limit`, `format_reqs`, `volume`                                      | Section L constraints       |
| `StrategicTheme`        | `theme_type`                                                               | Win themes classification   |
| `Clause`                | `clause_number`, `regulation`                                              | FAR/DFARS citations         |
| `PerformanceMetric`     | `threshold`, `measurement_method`                                          | KPIs with values            |

**12 Generic Types** (use `BaseEntity` - just name + type):

- `organization`, `concept`, `event`, `technology`, `person`, `location`
- `section`, `document`, `deliverable`, `program`, `equipment`, `statement_of_work`

**Design Philosophy**: Don't over-engineer. A `location` like "Joint Base Andrews" doesn't need special fields - relationships carry the semantic meaning.

---

## Phase 6: Semantic Post-Processing & Neo4j (November 2025)

### The Relationship Gap

**Problem**: LightRAG native extraction captures entities well but misses domain-specific relationships:

- Section L instructions → Section M evaluation factors (critical!)
- Requirements → Deliverables (traceability)
- Annexes → Parent documents (hierarchy)

**Solution**: 8 LLM-powered semantic post-processing algorithms.

### 8 Semantic Algorithms

| #   | Algorithm                      | Purpose                      | Relationships Created    |
| --- | ------------------------------ | ---------------------------- | ------------------------ |
| 1   | Instruction-Evaluation Linking | Section L → M mapping        | `GUIDES`, `EVALUATED_BY` |
| 2   | Evaluation Hierarchy           | Factor → subfactor structure | `PARENT_OF`, `CHILD_OF`  |
| 3   | Requirement-Evaluation Mapping | Requirements → factors       | `EVALUATED_BY`           |
| 4   | Deliverable Traceability       | CDRLs → requirements         | `PRODUCES`, `REFERENCES` |
| 5   | Document Hierarchy             | Section structure            | `PARENT_OF`, `CHILD_OF`  |
| 6   | Semantic Concept Linking       | Topic-based connections      | `RELATED_TO`             |
| 7   | Heuristic Pattern Matching     | CDRL cross-references        | `REFERENCES`             |
| 8   | Orphan Pattern Resolution      | Unlinked entity cleanup      | Various                  |

**Implementation**: `src/inference/semantic_post_processor.py` (1,086 lines)

### Neo4j Enterprise Storage

**Why Neo4j over NetworkX**:

- Graph queries 10-100x faster for large RFPs
- APOC procedures for complex traversals
- Visual exploration via Neo4j Browser
- Production-grade persistence

**Docker Setup**:

```yaml
# docker-compose.neo4j.yml
services:
  neo4j:
    image: neo4j:5.25-community
    ports:
      - "7474:7474" # Browser
      - "7687:7687" # Bolt
    environment:
      NEO4J_PLUGINS: '["apoc"]'
```

### Workload Enrichment

**New in Phase 6**: BOE (Basis of Estimate) category tagging for requirements.

```python
class BOECategory(str, Enum):
    LABOR = "Labor"
    MATERIALS = "Materials"
    ODCS = "ODCs"
    QA = "QA"
    LOGISTICS = "Logistics"
    LIFECYCLE = "Lifecycle"
    COMPLIANCE = "Compliance"
```

**Purpose**: Enable downstream cost estimation and staffing analysis.

### Production Metrics (November 2025)

| Metric               | Value                   |
| -------------------- | ----------------------- |
| Entity Types         | 18                      |
| Semantic Algorithms  | 8                       |
| Navy MBOS (71 pages) | 594 entities, 30-40 min |
| Large RFP (400+ pg)  | 45-60 minutes           |
| Cost per RFP         | ~$4                     |
| Graph Storage        | Neo4j 5.25              |
| Zero Contamination   | ✅ Achieved             |

---

## Current State: Production System

### System Architecture (November 2025)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    6-Step Processing Pipeline                       │
├─────────────────────────────────────────────────────────────────────┤
│  1. DOCUMENT UPLOAD → PDF/DOCX to /documents/upload                │
│  2. MINERU PARSING → Tables, images, text via RAG-Anything         │
│  3. LIGHTRAG CHUNKING → 8,192 tokens/chunk, 15% overlap            │
│  4. ENTITY EXTRACTION → 18 types via xAI Grok + Instructor         │
│  5. RELATIONSHIP EXTRACTION → LightRAG native inference            │
│  6. SEMANTIC POST-PROCESSING → 8 LLM algorithms                    │
│                                                                     │
│  OUTPUT: Neo4j Knowledge Graph + LightRAG WebUI                    │
└─────────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component         | Technology                    | Version                        |
| ----------------- | ----------------------------- | ------------------------------ |
| RAG Orchestration | RAG-Anything                  | ≥1.2.8 (pip)                   |
| Knowledge Graph   | LightRAG                      | ≥1.4.9.7 (pip: `lightrag-hku`) |
| LLM               | xAI Grok-4-fast-reasoning     | Cloud API                      |
| Embeddings        | OpenAI text-embedding-3-large | 3072-dim                       |
| Graph Storage     | Neo4j Community               | 5.25                           |
| Schema Validation | Instructor + Pydantic         | ≥1.13.0                        |
| Document Parsing  | MinerU                        | via RAG-Anything               |

### Quality Gates Achieved ✅

| Gate                     | Status | Evidence                                      |
| ------------------------ | ------ | --------------------------------------------- |
| Zero fictitious entities | ✅     | No regex artifacts like "Section J-L"         |
| Zero contamination       | ✅     | Pydantic validation blocks external knowledge |
| 18 entity types          | ✅     | `src/ontology/schema.py`                      |
| Section L↔M mapping      | ✅     | Algorithm 1: Instruction-Evaluation Linking   |
| Production performance   | ✅     | 30-60 min per RFP (vs 8-16 hrs local)         |
| Enterprise storage       | ✅     | Neo4j with APOC                               |

### GitHub Issues & Roadmap

**Active Optimization Issues**:

- [#14](https://github.com/BdM-15/govcon-capture-vibe/issues/14): Prompt Compression (50% token reduction)
- [#15](https://github.com/BdM-15/govcon-capture-vibe/issues/15): Remove Redundant Algorithms 1-3
- [#17](https://github.com/BdM-15/govcon-capture-vibe/issues/17): Parallel Chunk Processing
- [#19](https://github.com/BdM-15/govcon-capture-vibe/issues/19): Fine-Tuned SLM Strategy

**Strategic Features**:

- [#20](https://github.com/BdM-15/govcon-capture-vibe/issues/20): Cross-RFP Knowledge Accumulation
- [#21](https://github.com/BdM-15/govcon-capture-vibe/issues/21): Strategic Intelligence
- [#23](https://github.com/BdM-15/govcon-capture-vibe/issues/23): Core Capture Intelligence

---

## Architecture Lessons Learned

### 1. Regex is Not the Answer

- Regex preprocessing created fictitious entities ("Section J-L")
- Brittle patterns failed on real-world variations
- Over-extraction appeared better but was actually noise

**Lesson**: Let LLMs understand semantically, not through pattern matching.

### 2. Preprocessing Can Enhance RAG (When Done Right)

- MinerU structure preservation improved extraction quality
- 8K token chunks with 15% overlap prevents context loss
- Relationship hints guided LLM toward valid patterns

**Lesson**: Preprocessing + RAG + Validation = Production Quality.

### 3. Validation is Non-Negotiable

- Instructor + Pydantic enforces schema at extraction time
- Invalid entity types coerced to `concept` with warning
- Zero contamination from external knowledge achieved

**Lesson**: Type-safe structured outputs are ESSENTIAL for production.

### 4. Domain Knowledge Matters

- Generic LightRAG doesn't understand government contracting
- 18 specialized entity types capture domain nuances
- 8 semantic algorithms add domain-specific relationships

**Lesson**: Ontology injection is CRITICAL for domain-specific RAG.

### 5. Entities vs Attributes vs Specialized Models

- **18 Entity Types**: Things that exist in the knowledge graph
- **6 Specialized Models**: Entity types needing structured fields (Requirement, EvaluationFactor, etc.)
- **12 Generic Types**: Use BaseEntity directly (organization, location, etc.)
- **Attributes**: Properties like budget stored as metadata, not separate entities

**Lesson**: Specialize only when structured extraction provides value.

---

## References

### Primary Documents

- **Navy MBOS RFP**: N6945025R0003.pdf (71 pages) - Primary test document
- **Marine Corps MCPP II DRFP**: 495 pages - Large-scale validation
- **Shipley Guides**: Capture Guide, Proposal Guide - Methodology foundation
- **FAR 15.210**: Uniform Contract Format (Sections A-M standard)

### Source Code

| File                                       | Purpose                                        |
| ------------------------------------------ | ---------------------------------------------- |
| `src/ontology/schema.py`                   | 18 entity types, 6 specialized Pydantic models |
| `src/inference/semantic_post_processor.py` | 8 relationship inference algorithms            |
| `src/extraction/json_extractor.py`         | Instructor + Pydantic extraction               |
| `src/server/config.py`                     | LightRAG global_args configuration             |
| `prompts/extraction/`                      | Entity extraction prompts (~170K tokens)       |

### External References

- **LightRAG**: https://github.com/HKUDS/LightRAG (pip: `lightrag-hku`)
- **RAG-Anything**: https://github.com/HKUDS/RAG-Anything (pip: `raganything[all]`)
- **Instructor**: https://github.com/jxnl/instructor (Pydantic LLM validation)
- **xAI Grok**: https://x.ai/ (Cloud LLM API)
- **Neo4j**: https://neo4j.com/ (Graph database)

### Related Documentation

- **[README.md](../../README.md)**: Project overview
- **[ARCHITECTURE.md](../ARCHITECTURE.md)**: System architecture
- **[NEO4J_USER_GUIDE.md](../neo4j/NEO4J_USER_GUIDE.md)**: Graph database setup
- **[FEATURE_ROADMAP.md](../capture-intelligence/FEATURE_ROADMAP.md)**: Development roadmap

---

**Document Status**: Living document - updated as ontology evolves.

**Version History**:

- v2.0.0 (November 28, 2025): Updated for Phase 5-6, 18 entity types, 8 semantic algorithms, Neo4j
- v1.0.0 (October 5, 2025): Initial consolidation of RAG storage analysis and ontology alignment
