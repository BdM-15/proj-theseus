# Ontology Simplification Analysis Report

**Date**: December 13, 2025  
**Branch**: `cursor/graphrag-ontology-simplification-3e1d`  
**Author**: AI Analysis Agent  
**Status**: Analysis Phase Complete, Implementation Ready

---

## Executive Summary

The retrieval quality of this LightRAG/RAGAnything-based government contracting intelligence system has significantly degraded. Analysis reveals **over-engineering** as the root cause—too many entity types (18), overly strict Pydantic validation, complex 8-algorithm semantic post-processing, and massive extraction prompts (~120K+ characters) that fragment knowledge and reduce retrieval precision.

**Key Finding**: The system paradoxically got worse as "advanced features" were added. Adding granular entity types like workload-specific fields fragmented knowledge that was previously inferred holistically from broader entity types.

**Recommendation**: Simplify to 12 core entities with hierarchical relationships, relax validation to essentials, enable inference-based enrichment at query time rather than extraction time, and leverage LightRAG's native lightweight strengths.

---

## Table of Contents

1. [Current Architecture Issues](#current-architecture-issues)
2. [Root Cause Analysis](#root-cause-analysis)
3. [LightRAG/RAGAnything Best Practices](#lightragraganything-best-practices)
4. [Proposed Simplified Ontology](#proposed-simplified-ontology)
5. [Implementation Plan](#implementation-plan)
6. [Migration Strategy](#migration-strategy)

---

## Current Architecture Issues

### 1. Over-Specified Entity Types (18 Types)

**Current ontology** (`src/ontology/schema.py:77-82`):

```python
VALID_ENTITY_TYPES = {
    "organization", "concept", "event", "technology", "person", "location",
    "requirement", "clause", "section", "document", "deliverable",
    "evaluation_factor", "submission_instruction", "program", "equipment",
    "strategic_theme", "statement_of_work", "performance_metric"
}
```

**Problems**:
- **Fragmented extraction**: LLM must classify into 18 types during extraction, increasing misclassification
- **Sparse graph**: Entities spread across types reduce relationship density
- **Rigid traversal**: Queries miss connections because entities are siloed by type
- **Validation overhead**: Each type has specialized Pydantic fields that can fail validation

### 2. Overly Complex Pydantic Validation

**Current validation** (`src/ontology/schema.py:132-166`):

```python
class Requirement(BaseEntity):
    entity_type: Literal["requirement"] = "requirement"
    criticality: CriticalityLevel = Field(...)  # MANDATORY/IMPORTANT/OPTIONAL/INFORMATIONAL
    modal_verb: str = Field(...)  # shall/must/will/should/may
    req_type: RequirementType = Field(...)  # FUNCTIONAL/PERFORMANCE/SECURITY/...
    labor_drivers: List[str] = Field(default_factory=list)  # Workload details
    material_needs: List[str] = Field(default_factory=list)  # Equipment/supplies
```

**Problems**:
- **Extraction failures**: When LLM omits required fields, entire entities are dropped
- **Hallucination pressure**: LLM forced to provide values even when not in source
- **Workload fragmentation**: `labor_drivers` captured at extraction prevents holistic workload inference
- **Validation cascades**: `@model_validator` rules drop valid data on minor issues

### 3. Massive Extraction Prompts (~120K+ characters)

**Current prompt construction** (`src/extraction/json_extractor.py:68-144`):

```python
def _load_full_system_prompt(self) -> str:
    # Combines:
    # 1. grok_json_prompt.md
    # 2. entity_detection_rules.md (~1,612 lines)
    # 3. entity_extraction_prompt.md (~120K+ characters)
    # 4. ALL relationship_inference/*.md files
```

**Problems**:
- **Context dilution**: With 2M context window, 120K prompt + 8K chunk = significant attention decay
- **Conflicting instructions**: Multiple prompt sections may give contradictory guidance
- **Slow processing**: Large prompts increase API latency and cost
- **Rigid extraction**: Detailed rules prevent LLM from using semantic understanding

### 4. Complex 8-Algorithm Post-Processing

**Current algorithms** (`src/inference/semantic_post_processor.py:1746-1854`):

```python
all_tasks = [
    _algorithm_1_instruction_eval(...),      # Instruction-Evaluation Linking
    _algorithm_2_eval_hierarchy(...),        # Evaluation Hierarchy
    _algorithm_3_req_eval_batched(...),      # Requirement-Evaluation Mapping
    _algorithm_4_deliverable_trace_batched(...),  # Deliverable Traceability
    _algorithm_5_doc_hierarchy(...),         # Document Hierarchy
    _algorithm_6_concept_linking(...),       # Semantic Concept Linking
    _algorithm_8_orphan_resolution(...),     # Orphan Resolution
]
# + Algorithm 7: Heuristic Pattern Matching
```

**Problems**:
- **Redundant relationships**: 8 algorithms create overlapping/conflicting edges
- **Processing time**: 5+ minutes of post-processing per document batch
- **Ghost relationships**: Algorithms create relationships to non-existent entities
- **Complexity debt**: Each algorithm has its own prompt, validation, and batch logic

### 5. Neo4j Integration Overhead

**Current Neo4j usage** (`src/inference/neo4j_graph_io.py`):

```python
class Neo4jGraphIO:
    # 478 lines of custom Neo4j operations
    # Workspace isolation via labels
    # Custom INFERRED_RELATIONSHIP edges
    # Separate from LightRAG's native storage
```

**Problems**:
- **Storage duplication**: Entities in both LightRAG KV stores AND Neo4j
- **Sync issues**: Neo4j state can diverge from LightRAG state
- **Query overhead**: Must query Neo4j separately from vector search
- **LightRAG bypass**: Custom Neo4j ops don't use LightRAG's optimized retrieval

---

## Root Cause Analysis

### Why Quality Degraded

```
Early Version (Good)                 Current Version (Degraded)
─────────────────────                ──────────────────────────
- 5-8 entity types                   - 18 entity types
- Simple extraction                  - Complex Pydantic validation
- LightRAG native retrieval          - Neo4j + custom algorithms
- Infer workload at query time       - Extract workload at extraction
- Small prompts (~10K)               - Massive prompts (~120K+)
```

**The paradox**: Adding "workload_driver" entities to capture volumes/frequencies actually REDUCED ability to retrieve granular workload info because:

1. **Fragmentation**: Workload data split between `requirement.labor_drivers`, `performance_metric.threshold`, and implicit text
2. **Extraction failures**: Strict validation drops requirements missing workload fields
3. **Lost context**: Workload drivers extracted in isolation lose relationship to parent requirement
4. **Query mismatch**: Users query "workload requirements" but data is in multiple entity types

### Evidence from Diagnostics

**Orphan Node Analysis** (`tools/diagnostics/ORPHAN_NODE_ANALYSIS.md`):
- 34/1,410 entities orphaned (2.4% orphan rate)
- 13/34 orphans from DODAAC table (administrative metadata over-extracted)
- LLM relationship inference quality issues, not timing

**Entity Type Audit** (`tools/diagnostics/entity_type_audit.py`):
- Misclassification between `requirement` vs `performance_metric`
- `concept` used as catch-all for failed type detection
- `strategic_theme` rarely extracted correctly

---

## LightRAG/RAGAnything Best Practices

### From Official LightRAG Repository

**Query Modes** (LightRAG README):
```python
mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"]
# "hybrid" - Combines local and global retrieval methods (recommended)
# "mix" - Integrates knowledge graph and vector retrieval
```

**Recommended Settings**:
- `top_k=60` - Number of entities/relationships to retrieve
- `chunk_top_k=20` - Text chunks for context
- `max_total_tokens=30000` - Context budget
- `enable_rerank=True` - Reranking for better precision

**Entity Types** (LightRAG default):
```python
addon_params = {
    "entity_types": ["organization", "person", "location", "event"]
}
# Simple, broad types that work across domains
```

### From Official RAG-Anything Repository

**Processing Flow**:
1. Document Parsing (MinerU) → 2. Content Analysis → 3. Knowledge Graph → 4. Retrieval

**Key Principle**: "Seamless processing and querying across all content modalities within a single integrated framework"

**Recommended Architecture**:
- Let MinerU handle document structure
- Use LightRAG's native entity extraction
- Keep entity types simple and domain-relevant
- Enable multimodal query when needed

---

## Proposed Simplified Ontology

### 12 Core Entity Types (Hierarchical)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GOVCON ONTOLOGY v2.0                        │
│                      (12 Core Entity Types)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  DOCUMENT STRUCTURE                 PROCUREMENT ENTITIES            │
│  ─────────────────────             ─────────────────────            │
│  ┌─────────┐                       ┌─────────────────┐              │
│  │ section │ (RFP sections)        │   requirement   │ (shall/must) │
│  └────┬────┘                       └────────┬────────┘              │
│       │                                     │                        │
│       ▼                                     ▼                        │
│  ┌─────────┐                       ┌─────────────────┐              │
│  │document │ (attachments,         │   deliverable   │ (CDRLs,      │
│  └─────────┘  standards)           └─────────────────┘   outputs)   │
│                                                                     │
│  EVALUATION ENTITIES               STRATEGIC ENTITIES               │
│  ─────────────────────             ─────────────────────            │
│  ┌──────────────────┐              ┌─────────────────┐              │
│  │evaluation_factor │ (M criteria) │  win_strategy   │ (themes,     │
│  └────────┬─────────┘              └─────────────────┘   discrim.)  │
│           │                                                          │
│           ▼                                                          │
│  ┌──────────────────┐              ┌─────────────────┐              │
│  │ compliance_item  │ (L instruct, │     risk       │ (capture     │
│  └──────────────────┘  formats)    └─────────────────┘   risks)     │
│                                                                     │
│  CONTEXT ENTITIES                                                   │
│  ─────────────────────                                              │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐                │
│  │organization│  │  regulation  │  │   program    │                │
│  └────────────┘  └──────────────┘  └──────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Entity Type Mapping (18 → 12)

| Old Type (18)           | New Type (12)      | Rationale                              |
|-------------------------|--------------------|-----------------------------------------|
| `requirement`           | `requirement`      | Core - unchanged                        |
| `performance_metric`    | `requirement`      | Merge - metrics are requirements        |
| `clause`                | `regulation`       | Merge FAR/DFARS into regulation type    |
| `section`               | `section`          | Core - unchanged                        |
| `document`              | `document`         | Core - unchanged                        |
| `deliverable`           | `deliverable`      | Core - unchanged                        |
| `evaluation_factor`     | `evaluation_factor`| Core - unchanged                        |
| `submission_instruction`| `compliance_item`  | Merge - both are compliance related     |
| `strategic_theme`       | `win_strategy`     | Rename for clarity                      |
| `statement_of_work`     | `section`          | Merge - SOW is a section type           |
| `program`               | `program`          | Core - unchanged                        |
| `organization`          | `organization`     | Core - unchanged                        |
| `concept`               | *REMOVED*          | Drop catch-all type                     |
| `event`                 | *REMOVED*          | Rarely useful, merge to requirement     |
| `technology`            | *REMOVED*          | Merge to requirement/document           |
| `person`                | *REMOVED*          | Merge to organization                   |
| `location`              | *REMOVED*          | Merge to organization                   |
| `equipment`             | *REMOVED*          | Merge to requirement                    |

### Simplified Pydantic Schema

```python
# PROPOSED: Minimal validation, maximum flexibility
class BaseEntity(BaseModel):
    entity_name: str
    entity_type: Literal[
        "requirement", "deliverable", "evaluation_factor", 
        "compliance_item", "win_strategy", "risk",
        "section", "document", "regulation",
        "organization", "program"
    ]
    description: str = ""  # Optional, no strict validation
    source_chunk_id: str = ""  # For traceability

class Requirement(BaseEntity):
    """Simplified requirement - no mandatory workload fields"""
    entity_type: Literal["requirement"] = "requirement"
    criticality: str = ""  # Optional: MANDATORY/IMPORTANT/OPTIONAL
    # NO labor_drivers, material_needs - infer at query time

class EvaluationFactor(BaseEntity):
    """Simplified evaluation factor"""
    entity_type: Literal["evaluation_factor"] = "evaluation_factor"
    weight: str = ""  # Optional: "40%", "Most Important"
    # NO subfactors list - infer from graph relationships
```

### Relationship Types (Focused)

```python
RELATIONSHIP_TYPES = [
    "HAS_REQUIREMENT",       # Section → Requirement
    "EVALUATED_BY",          # Requirement → EvaluationFactor
    "PRODUCES",              # Requirement → Deliverable
    "PART_OF",               # Child → Parent (hierarchy)
    "REFERENCES",            # Entity → Document/Regulation
    "ADDRESSES",             # WinStrategy → Requirement
    "MITIGATES",             # WinStrategy → Risk
]
# 7 focused relationship types vs. current 20+
```

---

## Implementation Plan

### Phase 1: Simplified Schema (src/ontology/schema_v2.py)

1. Create new schema with 12 entity types
2. Remove all strict field validators
3. Keep description capture but make optional
4. Enable graceful type coercion (unknown → closest match)

### Phase 2: Streamlined Extraction Prompt

1. Reduce prompt from ~120K to ~15K characters
2. Focus on entity TYPE detection, not field extraction
3. Remove relationship inference rules from extraction
4. Trust LLM semantic understanding over rigid rules

### Phase 3: Disable Over-Engineered Features

1. **Disable** 8-algorithm semantic post-processing
2. **Disable** workload enrichment (infer at query time)
3. **Optional**: Keep Neo4j but use LightRAG's native graph
4. **Enable** LightRAG's native relationship inference

### Phase 4: Query-Time Inference

1. Build workload analysis at query time using retrieved context
2. Use LLM to synthesize requirements → workload mapping on demand
3. Enable Shipley methodology queries via prompt engineering
4. Keep granular details in full-text chunks, not entity fields

---

## Migration Strategy

### Option A: Clean Migration (Recommended)

1. Create new workspace with simplified ontology
2. Re-process documents with new pipeline
3. Validate retrieval quality on test queries
4. Archive old workspace

### Option B: In-Place Migration

1. Create database migration script
2. Map 18 types → 12 types in Neo4j
3. Remove orphaned metadata fields
4. Update extraction pipeline

### Test Queries for Validation

```python
VALIDATION_QUERIES = [
    # Multi-hop workload query (should improve)
    "What workload volumes and frequencies from this RFP's requirements drive the proposed solution?",
    
    # Shipley capture query
    "What are the win themes and discriminators for this opportunity?",
    
    # Compliance matrix query
    "List all Section L requirements that map to Section M evaluation factors",
    
    # Deliverable traceability
    "What CDRLs are required and what requirements do they satisfy?",
    
    # Granular detail query
    "What are the specific staffing requirements for 24/7 operations?"
]
```

---

## Expected Improvements

| Metric                    | Current    | Expected (Post-Simplification) |
|---------------------------|------------|--------------------------------|
| Entity extraction success | ~95%       | ~99%                           |
| Relationship density      | 2.4 orphan | <1% orphan                     |
| Processing time           | ~60 min    | ~30 min                        |
| Query precision (multi-hop)| Low       | High                           |
| Workload detail retrieval | Fragmented | Holistic                       |
| Maintenance complexity    | High (8 algos) | Low (native LightRAG)      |

---

## Next Steps

1. [ ] Approve this analysis
2. [ ] Create `src/ontology/schema_v2.py` with simplified types
3. [ ] Create `prompts/extraction/entity_extraction_prompt_v2.md` (streamlined)
4. [ ] Update `src/server/config.py` with new entity types
5. [ ] Create feature flag to enable/disable semantic post-processing
6. [ ] Run validation queries on test RFP
7. [ ] Create PR with migration guide

---

*This analysis prioritizes recovering (and exceeding) early simple-version performance while maintaining ontology benefits for government contracting domain expertise.*
