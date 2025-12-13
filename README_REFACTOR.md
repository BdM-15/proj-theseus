# Refactoring Summary: Simplified Ontology & Pipeline

## Overview
This branch (`feature/simplify-ontology-and-pipeline`) refactors the RAG pipeline to address retrieval quality degradation caused by over-engineering.

## Changes

### 1. Simplified Ontology (`src/ontology/schema.py`)
*   **Reduced Entity Types**: Consolidated 18+ granular types into 13 core entities:
    *   `opportunity`, `organization`, `person`, `location`, `document`, `section`
    *   `rfp_requirement` (consolidates `requirement`, `statement_of_work`, `technical_requirement`)
    *   `compliance_item` (consolidates `clause`, `evaluation_factor`)
    *   `win_theme`, `risk`, `competitor`, `deliverable`, `shipley_phase`
*   **Flexible Schema**: Replaced strict Pydantic validation (which was dropping data) with a flexible `BaseEntity` model that includes a `metadata` dictionary. This ensures granular details like "workload volumes" are captured even if they don't fit a rigid schema.

### 2. Streamlined Extraction (`src/extraction/`)
*   **Updated Prompt**: Rewrote `prompts/extraction/entity_extraction_prompt.md` to focus on the 13 core entities and emphasized capturing "workload drivers" in descriptions/metadata.
*   **Removed Legacy Rules**: Updated `json_extractor.py` to stop loading complex, conflicting inference rules from `prompts/relationship_inference/`.
*   **Adapter Update**: Updated `lightrag_llm_adapter.py` to support the new schema's `description` and `metadata` fields.

### 3. Disabled Heavy Post-Processing (`src/inference/`)
*   **Disabled**: The 8-algorithm `semantic_post_processor.py` (2000+ lines) has been disabled. It was a major source of latency and brittleness.
*   **Rationale**: We now rely on LightRAG's native graph construction and Grok 4's high-context reasoning capability during retrieval, rather than pre-computing brittle relationships.

### 4. Configuration (`src/server/config.py`)
*   **NetworkX**: Switched default storage to `NetworkXStorage` (removed Neo4j dependency for simplicity).
*   **Chunking**: Defaults to 8192 tokens (Grok 4 context) with 1200 overlap.

## Verification

A test script is provided at `tests/verify_simplified_pipeline.py`.

**To run verification:**
1.  Ensure `.env` contains `LLM_BINDING_API_KEY` (xAI API Key).
2.  Run:
    ```bash
    export PYTHONPATH=$PYTHONPATH:.
    python3 tests/verify_simplified_pipeline.py
    ```

**Success Criteria:**
*   The script should extract `rfp_requirement` entities.
*   It should find "5,000 medical claims" in the description or metadata (proving granular detail retention).
*   It should find "CDRL A001" as a `deliverable`.
