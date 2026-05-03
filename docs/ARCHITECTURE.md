# GovCon Capture Vibe: System Architecture

**Project**: Government Contracting RAG System  
**Status**: Living Document  
**Last Updated**: April 2026  
**Current Branch**: main (production-ready)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Architecture Decision Records](#architecture-decision-records)
4. [Ontology Design](#ontology-design)
5. [Implementation Status](#implementation-status)
6. [Performance Metrics](#performance-metrics)
7. [References](#references)

---

## Executive Summary

### **System Purpose**

GovCon Capture Vibe is an **ontology-modified RAG system** for federal RFP analysis that transforms generic document processing into specialized procurement intelligence through domain-specific entity extraction and relationship mapping.

### **Core Innovation: Production Architecture**

**Current Performance** (December 2025):

- **MCPP II RFP** (425 pages): **38 minutes** end-to-end processing at **$2.12**
- **Entity extraction**: 1,522 entities across 18 specialized types
- **Graph storage**: Neo4j (primary) with workspace isolation
- **Architecture**: RAG-Anything (multimodal PDF parsing via MinerU) + LightRAG (knowledge graph + WebUI) + xAI Grok-4 (fast-reasoning)

### **Technology Stack**

**Active Codebase** (April 2026):

- **Total Lines**: ~4,700 lines (22 Python files in src/)
- **Core Modules**:
  - `app.py` - Entry point with Neo4j Docker management
  - `src/raganything_server.py` - Server orchestration
  - `src/server/` - FastAPI routing, configuration, initialization
  - `src/extraction/` - Custom entity extraction (Instructor + Pydantic)
  - `src/inference/` - Semantic post-processing algorithms
  - `src/ontology/` - Pydantic schema validation (33 entity types)

**External Dependencies**:

- **RAG-Anything** (`raganything[all]>=1.2.10`) - Multimodal PDF parsing via MinerU
- **LightRAG** (`lightrag-hku>=1.4.13`) - Knowledge graph construction + WebUI
- **MinerU** (`mineru[core]>=3.0.0`) - PDF/DOCX/XLSX document parsing (GPU-accelerated)
- **xAI Grok** - Cloud LLM (Dual: `grok-4-1-fast-non-reasoning` extraction, `grok-4.20-0309-reasoning` queries)
- **OpenAI Embeddings** - text-embedding-3-large (3072-dim)
- **Neo4j 5.25** - Primary graph storage with workspace isolation
- **Instructor** - Pydantic-enforced LLM outputs with retry logic

### **Strategic Value**

| Capability             | Current Production (Apr 2026)    | Notes                                |
| ---------------------- | -------------------------------- | ------------------------------------ |
| **Entity Types**       | 33 specialized types             | Government contracting ontology      |
| **Graph Storage**      | Neo4j (primary)                  | Workspace isolation, Cypher queries  |
| **Extraction Quality** | 1,522 entities (425-page RFP)    | Pydantic validation, 5x retry        |
| **Privacy**            | Public RFPs → cloud              | Queries → 100% local                 |
| **Chunk Size**         | 4,096 tokens                     | Optimized for extraction quality     |
| **LLM Model**          | grok-4.20 / grok-4-1-fast (dual) | Extraction + Reasoning models        |
| **Multimodal**         | Tables, images, text             | MinerU parsing with ontology mapping |

---

## Architecture Overview

### **Production Processing Flow** (April 2026)

```
Public RFP Upload (PDF/DOCX/XLSX)
    ↓
RAG-Anything Multimodal Pipeline
    ├─ MinerU Document Parsing
    │   ├─ Text extraction
    │   ├─ Table extraction (Section M evaluation matrices, BOE tables)
    │   ├─ Image extraction (org charts, diagrams)
    │   └─ Layout analysis (headers, footers, captions)
    ↓
Cloud Processing (xAI Grok-4.1)
    ├─ LLM: grok-4-1-fast-non-reasoning (extraction) + grok-4.20-0309-reasoning (queries)
    ├─ Embeddings: OpenAI text-embedding-3-large (3072-dim)
    ├─ Chunk size: 4,096 tokens with 15% overlap (~614 tokens)
    ├─ Concurrency: 16 workers (MAX_ASYNC, prevents rate limit errors)
    └─ Temperature: 0.1 (deterministic extraction)
         ↓
Custom Ontology Extraction (33 entity types)
    ├─ Contract/Commercial: requirement, contract_line_item, pricing_element, government_furnished_item, deliverable, workload_metric, labor_category, performance_standard, transition_activity
    ├─ Document/Authorities: document_section, document, amendment, clause, regulatory_reference, technical_specification, work_scope_item
    ├─ Proposal/Evaluation: evaluation_factor, subfactor, proposal_instruction, proposal_volume, past_performance_reference
    ├─ Strategic Signals: strategic_theme, customer_priority, pain_point
    ├─ Standard: organization, program, equipment, technology, location, event, person, compliance_artifact, concept
    └─ Pydantic validation: Instructor library with 5x retry
         ↓
Semantic Post-Processing (8 LLM algorithms)
    ├─ Entity type correction (forbidden types → valid types)
    ├─ Document hierarchy (DOCUMENT → SECTION relationships)
    ├─ Clause clustering (CLAUSE → parent SECTION)
    ├─ Section L↔M mapping (SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR)
    ├─ Requirement evaluation (REQUIREMENT → EVALUATION_FACTOR)
    ├─ SOW deliverables (STATEMENT_OF_WORK → DELIVERABLE)
    ├─ Deliverable traceability (DELIVERABLE → REQUIREMENT/EVALUATION_FACTOR)
    └─ Workload enrichment (extract BOE categories from requirements)
         ↓
Knowledge Graph Storage (Neo4j)
    ├─ Workspace isolation: Each RFP gets unique label (e.g., mcpp_drfp_2025)
    ├─ Entities: ~1,500 per large RFP (33 types)
    ├─ Relationships: ~1,000 per RFP (5 types: CHILD_OF, EVALUATED_BY, GUIDES, REQUIRES, RELATED_TO)
    ├─ Storage: Neo4j database (http://localhost:7474)
    └─ Query: Cypher + LightRAG hybrid search
    └─ WebUI: http://localhost:9621/
         ↓
Query Processing (100% Local)
    ├─ Hybrid search: Vector + graph traversal
    ├─ Context window: Up to 1.5M tokens (100 chunks × 4K)
    └─ Zero cloud exposure for proprietary queries
```

### **Security Boundary**

| Data Type               | Processing Location | Privacy Level  | Notes                            |
| ----------------------- | ------------------- | -------------- | -------------------------------- |
| **Public RFP Text**     | Cloud (xAI Grok)    | Already public | Standard LLM processing          |
| **Public RFP Tables**   | Cloud → Local       | Already public | Extracted then processed locally |
| **Knowledge Graph**     | Local Storage       | 100% private   | Never sent to cloud              |
| **Proprietary Queries** | Local               | 100% private   | Always local                     |
| **Proposal Content**    | Local               | 100% private   | Generated locally                |

### **Cloud Optimization Settings**

**Configuration** (`.env`):

```properties
# LLM Settings
LLM_BINDING_API_KEY=xai-your-key-here
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4.20-0309-reasoning
EXTRACTION_LLM_NAME=grok-4-1-fast-non-reasoning
REASONING_LLM_NAME=grok-4.20-0309-reasoning
LLM_MODEL_TEMPERATURE=0.1

# Embedding Settings
EMBEDDING_BINDING_API_KEY=sk-proj-your-openai-key
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-large

# Storage
GRAPH_STORAGE=Neo4JStorage  # or NetworkXStorage
WORKING_DIR=./rag_storage/workspace_name

# Chunking (REQUIRED - no defaults)
CHUNK_SIZE=4096                    # 4K tokens per chunk (optimized for quality)
CHUNK_OVERLAP_SIZE=600             # 15% overlap for continuity (~614/4096)

# Concurrency
MAX_ASYNC=16                       # 16 parallel LLM requests (prevents rate limit errors)
EMBEDDING_FUNC_MAX_ASYNC=16        # 16 parallel embedding requests

# Batch processing
BATCH_TIMEOUT_SECONDS=30  # Wait before triggering post-processing
```

**Performance Results**:

- **MCPP II DRAFT RFP** (425 pages): 38 minutes, $2.12 cost, 1,500+ entities
- **Entity density**: ~3.6 entities/page (comprehensive coverage)
- **Chunk size**: 4,096 tokens with 15% overlap (~614 tokens)

---

## Architecture Decision Records

### **ADR-001: LLM-Native Semantic Approach Over Regex Preprocessing**

**Date**: October 4, 2025  
**Status**: Accepted

**Context**: Early exploration of regex-based section identification showed promise but created fictitious entities like "RFP Section J-L" (doesn't exist in Uniform Contract Format).

**Decision**: Adopt LLM-native semantic understanding, eliminating regex preprocessing.

**Rationale**:

- ❌ **Regex Issues**: Fictitious entities, false boundaries, pattern fragility
- ✅ **LLM Benefits**: Semantic understanding, context awareness, handles variations

**Outcome**: Production uses pure LLM semantic processing with 4,096-token chunking for comprehensive entity extraction without regex preprocessing.

---

### **ADR-002: Cloud Optimization with xAI Grok**

**Date**: October 5, 2025  
**Status**: Accepted

**Context**: Need production-ready speed for public RFP processing without 4-6 months of local model fine-tuning.

**Decision**: Hybrid cloud architecture using xAI Grok-4 for public RFP processing, maintaining 100% local query processing.

**Rationale**:

- ✅ **Immediate availability**: xAI Grok production-ready (vs 6-month fine-tuning)
- ✅ **Large model capability**: grok-4.20-0309-reasoning with 2M context window
- ✅ **Privacy maintained**: Proprietary queries stay 100% local
- ✅ **Minimal cost**: ~$0.85 per large RFP

**Consequences**:

- **PRO**: 60-minute processing for 425-page RFPs
- **PRO**: 1,522 entities extracted (comprehensive coverage)
- **PRO**: Multimodal parsing included (tables, images)
- **PRO**: Query processing stays 100% local
- **CON**: Dependency on xAI API availability

---

### **ADR-003: Pydantic Schema Enforcement with Instructor**

**Date**: November 2025  
**Status**: Accepted (Issue #6 Complete)

**Context**: Need type-safe entity extraction with validation and graceful failure handling. LLMs occasionally produce invalid entity types or malformed JSON.

**Decision**: Use Instructor library to wrap xAI Grok API, enforcing Pydantic schema validation during extraction.

**Implementation**:

```python
from instructor import from_openai
from pydantic import BaseModel, Field, field_validator

class Entity(BaseModel):
    entity_name: str
    entity_type: str  # Must match one of 18 types
    description: str

    @field_validator('entity_type')
    def validate_entity_type(cls, v):
        valid_types = ["organization", "concept", "requirement", ...]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid entity type: {v}")
        return v.lower()

client = from_openai(OpenAI(base_url="https://api.x.ai/v1"))
result = client.chat.completions.create(
    model="grok-4-1-fast-non-reasoning",  # Extraction model
    response_model=ExtractionResult,
    max_retries=5,
    messages=[...]
)
```

**Rationale**:

- ✅ **Type safety**: Invalid entity types rejected at extraction time
- ✅ **Graceful degradation**: 5x retry with exponential backoff
- ✅ **Failed chunk tracking**: Logs chunks that fail validation
- ✅ **Schema evolution**: Easy to add new fields (e.g., `criticality_level`)

**Consequences**:

- **PRO**: Zero malformed entities in knowledge graph
- **PRO**: Clear error messages for debugging extraction prompts
- **PRO**: Production-ready with robust error handling
- **CON**: Slightly higher latency (validation overhead)

---

### **ADR-004: Neo4j as Primary Graph Storage**

**Date**: November 2025  
**Status**: Accepted

**Context**: NetworkXStorage limited for multi-workspace scenarios, complex queries, and production scale. Need workspace isolation, Cypher queries, and Docker-managed persistence.

**Decision**: Use Neo4j 5.25 as primary graph storage with automatic Docker container management.

**Implementation**:

- **Workspace isolation**: Each RFP labeled (e.g., `mcpp_drfp_2025`)
- **Docker auto-start**: `app.py` manages Neo4j container lifecycle
- **Fallback**: NetworkXStorage remains available for air-gapped deployments
- **Configuration**: `.env` setting `GRAPH_STORAGE=Neo4JStorage`

**Rationale**:

- ✅ **Multi-workspace support**: Isolate multiple RFPs in one database
- ✅ **Cypher queries**: Complex graph traversals (Section L↔M mapping)
- ✅ **WebUI integration**: Neo4j Browser (http://localhost:7474)
- ✅ **Production-grade**: ACID transactions, backup/restore

**Consequences**:

- **PRO**: Workspace management tools (duplicate, clear, list)
- **PRO**: Complex relationship queries (3-hop traversals)
- **PRO**: Browser visualization for RFP structure
- **CON**: Docker Desktop required (vs NetworkX pure Python)
- **MITIGATION**: NetworkX fallback for edge cases

---

### **ADR-005: RAG-Anything Non-Invasive Integration**

**Date**: October 5, 2025  
**Status**: Accepted

**Context**: Need multimodal parsing (tables, images, equations) while preserving govcon-specific ontology (12 entity types).

**Decision**: Use RAG-Anything as **library wrapper** around LightRAG, NOT as replacement or fork.

**Rationale**:

- ✅ **Preserve ontology**: 33 entity types remain intact
- ✅ **Multimodal capabilities**: MinerU parsing for tables/images
- ✅ **Non-invasive**: Pass LightRAG instance via `lightrag=govcon_rag` parameter
- ✅ **Maintainable**: `pip install --upgrade` gets updates without merge conflicts
- ✅ **Lower complexity**: Maintain ONE codebase instead of TWO forks

**Implementation Pattern**:

```python
from raganything import RAGAnything, RAGAnythingConfig
from lightrag import LightRAG

# Standard LightRAG with govcon ontology
govcon_rag = LightRAG(
    working_dir="./rag_storage",
    entity_types=["ORGANIZATION", "CONCEPT", "REQUIREMENT", ...],
    llm_model_func=xai_grok_func
)

# Wrap with RAG-Anything for multimodal
multimodal_rag = RAGAnything(
    lightrag=govcon_rag,  # Pass existing instance
    vision_model_func=xai_grok_vision_func,
    config=RAGAnythingConfig(...)
)
```

**Alternatives Considered**:

1. **Fork RAG-Anything**: High maintenance, two forks
2. **Build custom parser**: 2-3 months dev time, reinventing MinerU
3. **Use RAG-Anything as-is**: Lose govcon ontology

**Consequences**:

- **PRO**: Govcon ontology fully preserved
- **PRO**: Multimodal parsing with minimal code changes
- **PRO**: Easy updates via pip
- **CON**: Dependency on RAG-Anything stability
- **MITIGATION**: Pin version in production, test upgrades in dev

---

### **ADR-004: Aggressive Code Cleanup Strategy**

**Date**: October 6, 2025  
**Status**: Accepted

**Context**: Codebase accumulated 50,000+ lines including unused forks, test files, placeholder modules. Need minimal footprint for maintainability.

**Decision**: Delete ALL unused code aggressively, preserve only active files. Archive everything in git history (commits fdde07f, 42e8432).

**Rationale**:

- ✅ **Zero code bloat**: ~320 lines active vs 50,000+ before
- ✅ **Maintainability**: Only 2 files in `src/` to maintain
- ✅ **Safety**: All deleted code preserved in git history
- ✅ **Clarity**: No confusion about what's actually used

**Note**: ADR-004 reflects the October 2025 cleanup. The codebase has since grown to ~4,700+ lines across 22+ Python files in `src/` with dedicated modules for extraction, inference, ontology, and processors.

**What Was Deleted** (Phase 1):

- `src/lightrag_old_fork/` (238 files) - Branch 002 archived
- `src/agents/`, `src/api/`, `src/core/`, `src/models/`, `src/utils/` - Unused by RAG-Anything
- `src/processors/`, `src/govcon_rag.py`, `src/server.py` - Empty placeholders
- `test_upload.py`, `process_rfp.py` - Test artifacts

**Remaining Active Code**:

- `app.py` (40 lines) - Entry point
- `src/raganything_server.py` (280 lines) - Main server
- `src/__init__.py` - Package marker

**Verification**: Import test passed, system fully functional.

**Consequences**:

- **PRO**: 99.4% code reduction (50K → 320 lines)
- **PRO**: Clear understanding of active codebase
- **PRO**: Faster onboarding for new developers
- **CON**: Must reference git history for archived code
- **MITIGATION**: Comprehensive documentation in ARCHITECTURE.md

---

## Ontology Design

### **Government Contracting Entity Types (33 Types)**

**Source**: `prompts/govcon_prompt.py` → `_build_v8_system_prompt()` (V8-4, Part D rendered from `prompts/extraction/govcon_entity_types.yaml` via `{entity_types_guidance}`)

Organized into four functional groups to minimize `concept` bucket spillover and maximize typed retrieval precision:

**Group 1 — Contract, Execution & Commercial Structure (9 types)**

| Type                        | Purpose                                            |
| --------------------------- | -------------------------------------------------- |
| `requirement`               | Contractor obligations with criticality/modal_verb |
| `contract_line_item`        | CLINs, SLINs, priced line items (FFP/CPFF/T&M)     |
| `pricing_element`           | Rates, fees, escalation, wrap rates                |
| `government_furnished_item` | GFE/GFP/GFI/GOTS customer-provided assets          |
| `deliverable`               | CDRLs, DD Form 1423, contract deliverables         |
| `workload_metric`           | Quantitative BOE drivers (sorties, users, events)  |
| `labor_category`            | Named labor classifications, clearance levels      |
| `performance_standard`      | KPIs, SLAs, AQLs, QASP thresholds                  |
| `transition_activity`       | Phase-in/out, turnover, mobilization tasks         |

**Group 2 — Document Structure, Authorities & Work Patterns (7 types)**

| Type                      | Purpose                                            |
| ------------------------- | -------------------------------------------------- |
| `document_section`        | Numbered/titled hierarchical structural units      |
| `document`                | Attachments, exhibits, annexes, standalone docs    |
| `amendment`               | Solicitation modifications, Q&A amendments         |
| `clause`                  | FAR/DFARS/Agency clauses (26+ recognized agencies) |
| `regulatory_reference`    | IAW citations: DAFI, AR, MIL-STD, NIST SP, AFI     |
| `technical_specification` | ICDs, TDPs, MIL-DTL/MIL-PRF, drawings              |
| `work_scope_item`         | PWS/SOW/SOO tasks, objectives, work packages       |

**Group 3 — Proposal & Evaluation Structure (5 types)**

| Type                         | Purpose                                        |
| ---------------------------- | ---------------------------------------------- |
| `evaluation_factor`          | Top-level Section M criteria with weights      |
| `subfactor`                  | Evaluation subfactor hierarchy (children)      |
| `proposal_instruction`       | Page limits, format requirements, volume rules |
| `proposal_volume`            | Named proposal containers (Volume I, II, etc.) |
| `past_performance_reference` | Reference contracts, PPQs, CPARS records       |

**Group 4 — Strategic & Analytical Signals (3 types)**

| Type                | Purpose                                          |
| ------------------- | ------------------------------------------------ |
| `strategic_theme`   | Win themes, discriminators, proof points         |
| `customer_priority` | Explicit importance/emphasis language            |
| `pain_point`        | Problem statements the government wants resolved |

**Standard Entities (9 types)**

| Type                  | Purpose                                         |
| --------------------- | ----------------------------------------------- |
| `organization`        | Agencies, military units, contractors           |
| `program`             | Government programs and major acquisitions      |
| `equipment`           | Physical hardware, vehicles, machinery          |
| `technology`          | Software, systems, platforms                    |
| `location`            | Performance locations, facilities, bases        |
| `event`               | Milestones, deadlines, scheduled activities     |
| `person`              | Key personnel, POCs, named roles                |
| `compliance_artifact` | Certifications, ATOs, accreditations, ISO certs |
| `concept`             | Residual abstract ideas (last-resort bucket)    |

**Design Rationale — Scaling Properties**:

- Generic bucket (`concept` + `document` + `section`) was 30–59% of all nodes in real workspaces with the 18-type ontology
- With 33 types: generic% drops to ~18%, HHI improves 0.16→0.11, Shannon entropy 3.23→3.94
- Graph traversal (2-hop paths) is 23x more efficient at all scales due to elimination of hub supernodes
- Critical threshold: ~5,000 nodes where generic type supernodes become dominant in 18-type graph

### **Constrained Relationship Schema**

**Purpose**: Prevent O(n²) relationship explosion by defining valid domain relationships.

**Key Patterns**:

```python
VALID_RELATIONSHIPS = {
    # Section L ↔ Section M (Instructions reference evaluation)
    ("SECTION", "REFERENCES"): ["SECTION", "EVALUATION_FACTOR"],

    # Requirements generate deliverables
    ("REQUIREMENT", "PRODUCES"): ["DELIVERABLE"],

    # Evaluation factors evaluate requirements
    ("EVALUATION_FACTOR", "EVALUATES"): ["REQUIREMENT", "CONCEPT", "DELIVERABLE"],

    # Deliverables delivered by organizations
    ("DELIVERABLE", "DELIVERED_BY"): ["ORGANIZATION", "PERSON"],

    # SOW sections contain requirements
    ("SECTION", "CONTAINS"): ["REQUIREMENT", "DELIVERABLE", "CLAUSE"],

    # CLINs include deliverables
    ("CONCEPT", "INCLUDES"): ["DELIVERABLE", "REQUIREMENT", "TECHNOLOGY"],
}
```

**Benefits**:

- ✅ **Prevents noise**: Only domain-valid relationships created
- ✅ **Improves queries**: Traversal follows logical paths
- ✅ **Reduces storage**: Fewer invalid relationships stored
- ✅ **Enhances quality**: Graph reflects actual RFP structure

### **Multimodal Content Mapping**

| Multimodal Content          | RAG-Anything Type | Govcon Entity Type     | Example                          |
| --------------------------- | ----------------- | ---------------------- | -------------------------------- |
| Section M evaluation matrix | `table`           | `evaluation_factor`    | Evaluation criteria with weights |
| CLIN pricing table          | `table`           | `contract_line_item`   | Contract line item pricing       |
| Organizational chart        | `image`           | `organization`         | Prime-sub relationships          |
| Technical architecture      | `image`           | `technology`           | System architecture diagram      |
| Delivery schedule           | `table`           | `event`                | Milestone dates                  |
| Requirements matrix         | `table`           | `requirement`          | Traceability matrix              |
| BOE workload tables         | `table`           | `workload_metric`      | Sorties, users, labor hours      |
| QASP surveillance plan      | `table`           | `performance_standard` | AQL thresholds, inspection freq  |

---

## Implementation Status

### **Production System - COMPLETE ✅**

**December 2025 Architecture**:

- ✅ RAG-Anything integration (multimodal parsing via MinerU)
- ✅ LightRAG WebUI (http://localhost:9621/)
- ✅ xAI Grok cloud LLM (dual: extraction + reasoning, 2M context)
- ✅ OpenAI embeddings (text-embedding-3-large, 3072-dim)
- ✅ Neo4j primary storage with workspace isolation
- ✅ Pydantic schema enforcement (Instructor library)
- ✅ 33 entity types with semantic detection
- ✅ 8 semantic post-processing algorithms
- ✅ Custom agents framework (.github/agents/)

### **Recent Major Features**

**Issue #6: Pydantic Schema Enforcement** (✅ Complete):

- Instructor library wraps xAI Grok API
- 5x retry with exponential backoff
- Failed chunk tracking and logging
- Graceful degradation on validation failures

**Issue #13: Neo4j Primary Storage** (✅ Complete):

- Docker auto-managed Neo4j 5.25 container
- Workspace isolation via labels
- Cypher query support
- Neo4j Browser integration (http://localhost:7474)

**Semantic Post-Processing** (✅ Complete):

- Entity type correction (forbidden → valid types)
- Document hierarchy inference
- Clause clustering
- Section L↔M mapping (SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR)
- Requirement evaluation (REQUIREMENT → EVALUATION_FACTOR)
- SOW deliverables (STATEMENT_OF_WORK → DELIVERABLE)
- Deliverable traceability
- Workload enrichment (BOE category extraction)

**Multimodal Table Processing** (✅ Complete):

- 2-stage pipeline: MinerU → semantic entity mapping
- Section M evaluation matrices
- BOE workload tables
- CLIN pricing tables

**Custom Agents Framework** (✅ Complete):

- VS Code 1.106+ custom agents (.agent.md files)
- Plan agent (read-only, implementation planning)
- Implement agent (TDD approach, full editing)
- Validate agent (testing, Neo4j verification)
- Prompt files (/plan-feature, /add-entity-type, etc.)

---

## Performance Metrics

### **Production Performance Summary**

| Metric                  | Current Production (Apr 2026) | Notes                                     |
| ----------------------- | ----------------------------- | ----------------------------------------- |
| **Processing Time**     | 38 minutes (425-page RFP)     | MCPP II DRAFT RFP baseline ($2.12 cost)   |
| **Entities Extracted**  | 1,522 entities                | 33 specialized govcon types               |
| **Relationships Found** | ~1,000 relationships          | 5 relationship types + semantic inference |
| **Entity Density**      | ~3.6 entities/page            | Comprehensive coverage                    |
| **Chunk Size**          | 4,096 tokens                  | Optimized for extraction quality          |
| **Storage**             | Neo4j (primary)               | Workspace-isolated, Cypher queries        |
| **LLM Model**           | grok-4-1-fast-\* (dual)       | 2M context, temp=0.0/0.1 extraction/query |
| **Validation**          | Pydantic + 5x retry           | Zero malformed entities                   |

### **Quality Indicators**

**Entity Extraction**:

- ✅ 33 entity types properly classified
- ✅ Pydantic validation enforced (Instructor library)
- ✅ 5x retry with exponential backoff
- ✅ Failed chunk tracking for post-mortem analysis
- ✅ BOECategory enum for workload classification

**Relationship Extraction**:

- ✅ 5 core relationship types (CHILD_OF, EVALUATED_BY, GUIDES, REQUIRES, RELATED_TO)
- ✅ Section L↔M connections (SUBMISSION_INSTRUCTION ↔ EVALUATION_FACTOR)
- ✅ Requirement→Deliverable mappings
- ✅ Document hierarchy (DOCUMENT → SECTION → CLAUSE)

**Semantic Post-Processing**:

- ✅ 8 LLM-powered inference algorithms
- ✅ Batch processing (50 items per LLM call)
- ✅ Confidence scoring (0.0-1.0 per relationship)
- ✅ Human-readable reasoning strings

**Multimodal Parsing**:

- ✅ Tables extracted from evaluation matrices (Section M)
- ✅ BOE workload tables parsed and classified
- ✅ CLIN pricing tables extracted
- ✅ 2-stage pipeline: MinerU → semantic mapping

### **Cost Analysis**

**MCPP II DRAFT RFP** (425 pages):

- **Extraction**: ~$0.50 (text + table processing)
- **Embeddings**: ~$0.05 (vector generation)
- **Semantic post-processing**: ~$0.30 (8 algorithms)
- **Total**: ~$0.85 per large RFP

**Monthly Projections**:

- 10 RFPs/month: ~$21
- 50 RFPs/month: ~$106
- 100 RFPs/month: ~$212

**ROI**: Minimal costs vs 60-minute processing time per large RFP.

---

## References

### **Internal Documentation**

**Archived Documentation** (Historical Reference):

- `docs/ARCHITECTURE_DECISION_RECORDS.md` - ADR-001 through ADR-005 (now in this file)
- `docs/BRANCH_003_IMPLEMENTATION.md` - Implementation journal (now in this file)
- `docs/ONTOLOGY_EVOLUTION.md` - Ontology development history
- `docs/OLLAMA_WORKER_REFRESH.md` - Worker refresh mechanism (Branch 002 only)
- `docs/FINE_TUNING_ROADMAP.md` - Fine-tuning strategy (deferred for Branch 003)

**Active Documentation**:

- `README.md` - Project overview and quick start
- `.env.example` - Configuration template
- `ARCHITECTURE.md` - This file (comprehensive architecture guide)

**Shipley Methodology Resources** (Preserved):

- `docs/Shipley Capture Guide.pdf` - Capture planning best practices
- `docs/Shipley Proposal Guide.pdf` - Proposal development methodology
- `docs/SHIPLEY_LLM_CURATED_REFERENCE.md` - LLM-friendly Shipley reference
- `docs/Capture Plan v3.0.pdf` - Example capture plan
- `docs/Proposal Development Worksheet Populated Example.pdf` - Populated worksheet example

### **External Resources**

**Cloud Services**:

- **xAI Grok**: https://docs.x.ai
  - grok-4-1-fast-non-reasoning: Extraction (deterministic)
  - grok-4.20-0309-reasoning: Queries (synthesis)
  - API: OpenAI-compatible (https://api.x.ai/v1)
- **OpenAI Embeddings**: https://platform.openai.com/docs/guides/embeddings
  - text-embedding-3-large: 3072-dim, 8K token limit
  - Pricing: $0.13/1M tokens

**Open Source Libraries**:

- **LightRAG**: https://github.com/HKUDS/LightRAG
  - Official pip package: `pip install lightrag-hku`
  - WebUI: http://localhost:9621/
- **RAG-Anything**: https://github.com/HKUDS/RAG-Anything
  - Multimodal parsing: `pip install raganything[all]`
  - MinerU backend: Document parsing (tables, images, equations)

**Government Contracting Standards**:

- **FAR 15.210**: Uniform Contract Format (Sections A-M)
- **Shipley Methodology**: Requirements analysis, compliance matrices, win themes

### **Git Repository**

- **Repository**: https://github.com/BdM-15/govcon-capture-vibe
- **Current Branch**: main
- **Development Practice**: Always create feature branches, never commit directly to main

---

**Last Updated**: April 2026  
**Document Version**: 2.1.0  
**Status**: ✅ Documentation Updated to Reflect Current Production State
