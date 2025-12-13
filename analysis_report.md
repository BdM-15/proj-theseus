# Analysis Report: LightRAG/RAGAnything Pipeline Refactoring

## Root Cause Analysis

The current pipeline suffers from "over-engineering" which has led to brittleness, graph fragmentation, and reduced retrieval quality. Key issues identified:

1.  **Ontology Over-Specification:**
    *   **Current State:** 18+ strict entity types (`statement_of_work`, `submission_instruction`, `performance_metric`, etc.) defined in `src/ontology/schema.py`.
    *   **Impact:** This granularity fragments the knowledge graph. For example, separating `submission_instruction` from `requirement` can make it harder to find "all requirements for the proposal" without complex multi-hop queries.
    *   **Code Reference:** `src/ontology/schema.py` defines complex Pydantic models with strict validation that drops or coerces data (`validate_entity_type`).

2.  **Excessive Post-Processing:**
    *   **Current State:** `src/inference/semantic_post_processor.py` contains 8 distinct, complex algorithms for relationship inference (Instruction-Evaluation, Deliverable Traceability, etc.), comprising over 2000 lines of code.
    *   **Impact:** This is a major source of fragility and latency. It tries to "force" connections that might be better handled by a more flexible graph or semantic search. It relies heavily on Neo4j.
    *   **Code Reference:** `src/inference/semantic_post_processor.py` (Algorithms 1-8).

3.  **Strict Validation & Data Loss:**
    *   **Current State:** Pydantic models enforce strict matching (e.g., `CriticalityLevel`, `RequirementType`).
    *   **Impact:** Valid information that doesn't fit the schema is either dropped or coerced (e.g., to "concept"), losing semantic meaning.

4.  **Redundant Infrastructure (Neo4j):**
    *   **Current State:** The system maintains a Neo4j instance separate from LightRAG's internal storage.
    *   **Impact:** Adds complexity and synchronization overhead. LightRAG is designed to work with `NetworkX` or simple KV stores for the graph.

## Proposed Solution

Refactor the pipeline to align with LightRAG/RAGAnything best practices: simplicity, large chunks, and hybrid retrieval.

### 1. Simplified Ontology (10-15 Core Entities)
We will consolidate the 18 types into a broader, hierarchical set:

*   **Core:** `Organization`, `Person`, `Location`, `Document`, `Section`.
*   **Domain (Shipley/GovCon):**
    *   `Opportunity` (Root node)
    *   `RFP_Requirement` (Consolidates `requirement`, `submission_instruction`, `statement_of_work`, `technical_requirement`)
    *   `ComplianceItem` (Specific constraints, clauses)
    *   `WinTheme` (Strategic elements)
    *   `Risk` (Risks, issues)
    *   `Competitor`
    *   `Deliverable` (CDRLs, outputs)
    *   `ShipleyPhase` (Capture, Proposal, Review)

**Note:** Specific attributes like "workload volumes" will be captured as **properties** of `RFP_Requirement` or `Section` entities, or inferred during query generation, rather than as separate nodes.

### 2. Configuration & Chunking
*   **LLM:** Grok 4 (High context, strong reasoning).
*   **Chunk Size:** 8192 tokens (leverage Grok's window).
*   **Overlap:** 1200 tokens (~15%).
*   **Storage:** Switch to `NetworkXStorage` (remove Neo4j dependency).

### 3. Pipeline Simplification
*   **Extraction:** Relax Pydantic validation. Allow text fields where enums were overly restrictive.
*   **Inference:** Disable the 8-algorithm post-processor. Rely on:
    1.  Co-occurrence and semantic similarity (LightRAG default).
    2.  Basic "Section -> contains -> Requirement" structural links.
    3.  Query-time reasoning.

## Implementation Plan

1.  **Refactor `src/ontology/schema.py`:** Implement simplified models.
2.  **Update `src/server/config.py`:** Update `global_args`, switch to `NetworkXStorage`, set chunking params.
3.  **Disable `src/inference/semantic_post_processor.py`:** Remove calls in the main pipeline.
4.  **Update Prompts:** Modify extraction prompts to use the new ontology.
5.  **Verify:** Run the specified multi-hop evaluation query.
