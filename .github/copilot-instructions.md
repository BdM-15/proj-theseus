# Copilot Instructions for GovCon-Capture-Vibe

## ⚠️ CRITICAL RULE: Never Commit Without User Approval

**MANDATORY**: Before running `git commit`, you MUST:

1. Prepare the commit message following Conventional Commits format
2. Show the user what will be committed (`git status`)
3. Present the proposed commit message
4. Wait for explicit user approval
5. Only then execute `git commit`

**NEVER execute `git commit` on your own initiative.**

---

## Project Overview

**Ontology-based RAG system** for federal RFP analysis. Uses **RAG-Anything** (multimodal PDF parsing via MinerU) + **LightRAG** (knowledge graph/queries) with **xAI Grok** cloud processing.

**Core Innovation**: 18 government contracting entity types + 8 LLM-powered relationship inference algorithms enable Section L↔M mapping, requirement traceability, and Shipley methodology compliance.

### Supporting Documentation

- `docs/ARCHITECTURE.md` - Overall system architecture, technology stack, and performance metrics
- `docs/capture-intelligence/FEATURE_ROADMAP.md` - Future features and agent-powered proposal development workflows
- `docs/inference/SEMANTIC_POST_PROCESSING.md` - LLM relationship inference algorithms
- `docs/neo4j/NEO4J_USER_GUIDE.md` - Graph database workspace management
- `tests/TEST_SCRIPTS_README.md` - Guide for running validation scripts

### Root Folders

- `src/` - Python source code organized by domain
- `prompts/` - LLM prompt templates for extraction and inference
- `tests/` - Validation scripts and pytest suite
- `tools/` - Neo4j workspace management and validation utilities
- `docs/` - Architecture documentation and feature roadmaps
- `inputs/` - RFP document staging (uploaded/ and **enqueued**/ subdirs)
- `rag_storage/` - Per-workspace knowledge graph data (GraphML + embeddings)

---

## Architecture & LightRAG Integration

This project wraps **LightRAG** and **RAGAnything** to provide specialized government contracting capabilities.

### Core Components (`src/`)

- `src/raganything_server.py` - **Main Entry Point**. Orchestrates the server, initializes LightRAG, and sets up routes.
- `src/server/` - Server configuration and routing
  - `config.py` - LightRAG `global_args` setup (MUST load .env first)
  - `routes.py` - Custom endpoints with batch completion detection
  - `initialization.py` - RAGAnything wrapper initialization
- `src/inference/` - Semantic post-processing algorithms (8 LLM relationship inference algorithms)
- `src/ontology/` - Domain schema validation (Pydantic models for 18 entity types)
- `src/extraction/` - Custom entity extraction logic

### Processing Pipeline

1. **Document Upload** → `/insert` or `/documents/upload` endpoints
2. **MinerU Parsing** → Tables, images, text extraction (GPU-accelerated)
3. **LightRAG Chunking** → 8,192 tokens/chunk, 15% overlap
4. **Entity Extraction** → 18 govcon types via xAI Grok + Pydantic validation
5. **Relationship Extraction** → LightRAG native inference
6. **Semantic Post-Processing** → 8 LLM algorithms (auto-triggered after batch)

### RAG-Anything & MinerU Integration

We leverage **RAG-Anything** for multimodal document processing, using **MinerU** as the underlying parser.

- **Multimodal Support**: Handles text, images, tables, and equations.
- **MinerU Configuration**:
  - Controlled via `RAGAnythingConfig` in `src/server/initialization.py`.
  - Key settings: `parser="mineru"`, `parse_method="auto"`.
  - **GPU Acceleration**: MinerU requires CUDA for efficient parsing. Ensure `device="cuda"` is set if available.
- **Vision Model**: Uses `vision_model_func` (typically GPT-4o or similar) to analyze images extracted by MinerU.
- **Direct Content Insertion**: Supports inserting pre-parsed content lists via `insert_content_list` for testing or custom pipelines.

#### Context-Aware Processing (Issue #62)

RAG-Anything provides context-aware processing to include surrounding page text when processing tables/images. This enables:

- **Section Awareness**: Tables know they belong to "Appendix H - Workload Data"
- **CHILD_OF Relationships**: Algorithm 7 can infer parent section relationships
- **Better Embeddings**: VDB captures section semantics, not just isolated content

**Configuration (.env)**:

```bash
CONTEXT_WINDOW=2              # Pages of surrounding context (0=disabled)
CONTEXT_MODE=page             # Extraction mode: "page" or "chunk"
CONTENT_FORMAT=minerU         # Parser format hint
MAX_CONTEXT_TOKENS=3000       # Token budget for context
INCLUDE_HEADERS=true          # Include section headers
INCLUDE_CAPTIONS=true         # Include table/figure captions
CONTEXT_FILTER_CONTENT_TYPES=text  # Content types in context
```

**Note**: These env var names match RAGAnything's `RAGAnythingConfig` (no `RAGANYTHING_` prefix).

**GovconMultimodalProcessor**: Custom processor in `src/processors/govcon_multimodal_processor.py` extracts context via `context_extractor.extract_context()` and injects it into LLM prompts for table/image analysis.

---

## Development Guidelines

### Coding Style & Conventions

- **Python**: Follow PEP 8. Use 4-space indentation.
- **Logging**: Use `logging.getLogger(__name__)` or `lightrag.utils.logger`. **Avoid `print`**.
- **State Modeling**: Use `dataclasses` or Pydantic models.
- **Type Hinting**: Annotate functions and variables.
- **Imports**:

  - **CRITICAL**: Load `.env` (`load_dotenv()`) **BEFORE** importing any LightRAG modules. LightRAG evaluates defaults (like `CHUNK_SIZE`) at import time.
  - **Pattern**:

    ```python
    from dotenv import load_dotenv
    load_dotenv()  # MUST BE FIRST

    from lightrag import LightRAG
    from lightrag.api.config import global_args
    ```

### Agent Workflow & Best Practices

- **Search**: Use `rg` (grep_search) for fast text search. Use `file_search` for file names.
- **Paths**: Use repo-relative paths for all commands.
- **Modifications**: Honor existing local modifications. Never revert user changes without explicit instruction.
- **Planning**: For non-trivial work, create a multi-step plan.
- **Validation**: Always validate changes by running relevant tests (`pytest` or specific scripts).

---

## Testing & Validation

**MANDATORY**: Always activate virtual environment (`.venv`) before running tests.

### Running Tests

1.  **Quick Validation Scripts**:
    - Refer to `tests/TEST_SCRIPTS_README.md` for specific scenarios.
    - Example: `python tests/test_neo4j_quick.py`
2.  **Full Suite**:
    - Run `python -m pytest tests` to run the standard test suite.
    - Use markers if available (check `tests/pytest.ini` if present).

### Environment Setup

- Monitor terminal prompt for `(.venv)` indicator.
- Ensure `.env` is configured correctly for the test environment (e.g., `GRAPH_STORAGE`, `NEO4J_URI`).

---

## Branch Management Strategy

### **NEVER Work Directly on `main` Branch**

**Rule**: ALL development happens on feature branches.

### Branch Naming Convention

**Format**: `{number}-{descriptive-kebab-case-name}`

**Examples**:

- `028-parallel-chunk-extraction`
- `029-prompt-compression`

**Agent Responsibility**:

1. Identify the next branch number (check `git branch -a`).
2. Create descriptive name from GitHub issue title.
3. Suggest branch creation: `git checkout -b {number}-{description}`.

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):
`type(scope): description`

- **Types**: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`
- **Scope**: `extraction`, `inference`, `neo4j`, `prompts`, `agents`

---

## Configuration (.env)

```bash
# LLM - xAI Grok (OpenAI-compatible API)
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4-fast-reasoning
LLM_BINDING_API_KEY=xai-xxx

# Embeddings - OpenAI (MUST use OpenAI endpoint, not xAI)
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_BINDING_API_KEY=sk-proj-xxx

# Storage
GRAPH_STORAGE=Neo4JStorage  # or NetworkXStorage
WORKING_DIR=./rag_storage/workspace_name

# Batch processing
BATCH_TIMEOUT_SECONDS=30

# RAG-Anything Configuration
PARSER=mineru
PARSE_METHOD=auto
# OUTPUT_DIR=./rag_storage/output # Optional override
```

---

## Common Patterns

### Batch Document Upload

The `DocumentQueueTracker` in `src/server/routes.py` auto-detects batch completion. Uploads register via `register_request_start()`.

### Custom Endpoint Override

Routes override LightRAG defaults in `src/raganything_server.py`.

### File Operations

Use workspace tools (`read_file`, `create_file`, `replace_string_in_file`), NOT PowerShell for file I/O.

### GPU Warning

After `uv sync`, PyTorch might downgrade to CPU-only. Reinstall CUDA versions manually if needed (see `README.md` or previous instructions).
