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

**Core Innovation**: 33 government contracting entity types + 43 canonical relationship types + 8 LLM-powered relationship inference algorithms enable Section L↔M mapping, requirement traceability, and Shipley methodology compliance.

### Supporting Documentation

- `docs/ARCHITECTURE.md` - Overall system architecture, technology stack, and performance metrics
- `docs/ENHANCEMENT_FRAMEWORK.md` - Upstream library enhancement mapping
- `docs/MINERU_3X_INTEGRATION_ASSESSMENT.md` - MinerU 3.0 upgrade notes
- `docs/PROJECT_THESEUS_USE_CASE.md` - Project Theseus use case

### Root Folders

- `src/` - Python source code organized by domain
- `prompts/` - LLM prompt templates for extraction, multimodal analysis, query response, and inference
- `tools/` - Neo4j workspace management and validation utilities
- `docs/` - Architecture documentation and feature roadmaps
- `inputs/` - RFP document staging (uploaded/ and **enqueued**/ subdirs)
- `rag_storage/` - Per-workspace knowledge graph data (GraphML + embeddings)

---

## ⚠️ CRITICAL: Prompt Coherence & Cross-Cutting Change Rules

### The Three Prompt Systems

This project has **three independent prompt systems** that MUST stay aligned. Changes to the domain ontology, entity types, relationship types, or Shipley methodology MUST propagate across ALL three:

| System                         | Purpose                                         | Files                                                                                    | Registration                                                                |
| ------------------------------ | ----------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| **1. LightRAG Extraction**     | Entity/relationship extraction from text chunks | `prompts/extraction/govcon_lightrag_native.txt` → `prompts/govcon_prompt.py`             | `PROMPTS.update(GOVCON_PROMPTS)` in `src/server/initialization.py`          |
| **2. LightRAG Query/Response** | RAG query answering (Shipley mentor persona)    | `prompts/govcon_prompt.py` (`rag_response`, `naive_rag_response`, `keywords_extraction`) | Same `PROMPTS.update()` call                                                |
| **3. RAGAnything Multimodal**  | Table/image/equation VLM analysis               | `prompts/multimodal/govcon_multimodal_prompts.py`                                        | `register_prompt_language("govcon", ...)` in `src/server/initialization.py` |

**Additionally**, post-processing inference prompts live in `prompts/relationship_inference/` (13 algorithm-specific markdown files used by `src/inference/` modules).

### Cross-Cutting Change Checklist

**When modifying entity types, relationship types, or domain vocabulary, you MUST audit ALL of the following:**

1. **Schema** (`src/ontology/schema.py`): `VALID_ENTITY_TYPES`, `VALID_RELATIONSHIP_TYPES`, Pydantic models
2. **Extraction prompt** (`prompts/extraction/govcon_lightrag_native.txt`): Part D entity catalog, Part F relationship rules, Part J output format
3. **Multimodal prompts** (`prompts/multimodal/govcon_multimodal_prompts.py`): System prompts, processing prompts, query prompts — must reference correct entity type names and canonical relationship types
4. **Query/response prompts** (`prompts/govcon_prompt.py`): `rag_response`, `naive_rag_response` — Shipley mentor framework must reference current entity vocabulary
5. **Inference prompts** (`prompts/relationship_inference/*.md`): Algorithm-specific prompts that reference entity/relationship types
6. **Test fixtures** (`tools/test_query_prompt.py`, `tests/`): Signal detection patterns, expected entity types, relationship type assertions
7. **VDB sync** (`src/inference/vdb_sync.py`): Normalization logic for relationship types

**Rule: No PR that changes entity types, relationship types, or Shipley methodology should be committed without confirming all 7 areas above are aligned.**

### Domain Vocabulary Reference

- **33 entity types**: Defined in `src/ontology/schema.py` → `VALID_ENTITY_TYPES`
- **43 relationship types**: Defined in `src/ontology/schema.py` → `VALID_RELATIONSHIP_TYPES` (32 extraction + 11 inference-only)
- **Shipley methodology**: Discriminators, win themes, hot buttons, proof points, FAB chains, ghost language, compliance matrix — defined in extraction prompt Part D and query prompt `rag_response`

---

## Architecture & LightRAG Integration

This project wraps **LightRAG** and **RAGAnything** to provide specialized government contracting capabilities.

### Core Components (`src/`)

- `src/raganything_server.py` - **Main Entry Point**. Orchestrates the server, initializes LightRAG, and sets up routes.
- `src/server/` - Server configuration and routing
  - `config.py` - LightRAG `global_args` setup (MUST load .env first)
  - `routes.py` - Custom endpoints with batch completion detection
  - `initialization.py` - RAGAnything wrapper initialization, prompt registration (all 3 systems)
- `src/inference/` - Semantic post-processing (3 inference algorithms: L↔M links, document structure, orphan resolution)
- `src/ontology/` - Domain schema validation (Pydantic models for 33 entity types, 43 relationship types)
- `src/extraction/` - Custom entity extraction logic

### Processing Pipeline

1. **Document Upload** → `/insert` or `/documents/upload` endpoints
2. **MinerU Parsing** → Tables, images, text extraction (GPU-accelerated)
3. **Multimodal Analysis** → Tables/images/equations analyzed by VLM using **System 3** prompts (entity-type-aware, Shipley-aligned)
4. **LightRAG Chunking** → Configurable tokens/chunk (set via CHUNK_SIZE in .env), 15% overlap
5. **Entity Extraction** → 33 govcon entity types via xAI Grok + Pydantic validation using **System 1** prompts
6. **Relationship Extraction** → 43 canonical relationship types with typed schema validation
7. **Semantic Post-Processing** → 6-phase pipeline (auto-triggered after batch) using inference prompts
   - Phase 1: Data Loading
   - Phase 2: Entity Normalization
   - Phase 3: Relationship Normalization (entity-pair retyping)
   - Phase 4: Relationship Inference (L↔M links, document structure, orphan resolution)
   - Phase 5: Workload Enrichment (optional)
   - Phase 6: VDB Synchronization
8. **Query Response** → Shipley mentor persona via **System 2** prompts

### RAG-Anything & MinerU Integration

We leverage **RAG-Anything** for multimodal document processing, using **MinerU** as the underlying parser.

- **Multimodal Support**: Handles text, images, tables, and equations.
- **MinerU Configuration**:
  - Controlled via `RAGAnythingConfig` in `src/server/initialization.py`.
  - Key settings: `parser="mineru"`, `parse_method="auto"`.
  - **GPU Acceleration**: MinerU requires CUDA for efficient parsing. Ensure `device="cuda"` is set if available.
- **Vision Model**: Uses `vision_model_func` (typically GPT-4o or similar) to analyze images extracted by MinerU.
- **Multimodal Prompts**: `prompts/multimodal/govcon_multimodal_prompts.py` provides entity-type-aware, Shipley-aligned prompts for table/image/equation analysis. These prime downstream extraction with correct govcon vocabulary.
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
- **Cross-cutting awareness**: Before completing any feature branch, review the Cross-Cutting Change Checklist above if the change touches ontology, prompts, or domain vocabulary.

### Frontend / UI (Alpine + Tailwind CDN, external CSS)

**Read [docs/STYLE_GUIDE.md](../docs/STYLE_GUIDE.md) before making any UI changes.**

- **Two files**: `src/ui/static/index.html` (markup + Alpine `theseus()` component + inline `tailwind.config`) and `src/ui/static/styles/theseus.css` (all custom CSS — `:root` token block + components). **No build step**, no inline `<style>` block.
- **CRITICAL — Tailwind Play CDN does NOT process `@apply` in `theseus.css`.** `@apply` only resolves inside an inline `<style>` block in HTML, which we no longer have. Writing `@apply` in `theseus.css` produces silent style failures. Always use raw CSS with the `var(--*)` token references defined in `:root`.
- **Token system**: All colors live as CSS custom properties in `theseus.css` (`--neon-cyan`, `--ink-900`, `--edge-strong`, `--text-300`, etc.). For transparency, use the matching `--*-rgb` triplet inside `rgba()`: `rgba(var(--neon-cyan-rgb), 0.4)`. Do NOT add new hex literals for color variants — use the triplet + alpha.
- **Tailwind config is duplicated**: the runtime config lives inline as `tailwind.config = {…}` in a `<script>` tag at the top of `index.html` (read by the CDN in the browser); the IDE-only mirror lives at `tailwind.config.js` (read by the VS Code Tailwind IntelliSense extension). **If you change one, mirror the other** — custom tokens (`neon-*`, `ink-*`, `edge-*`, `shadow-glow`, `shadow-magenta`) must match in both files. New CSS tokens added to `:root` should also be mirrored here if they need a Tailwind utility.
- **No server restart for UI changes** — hard-reload the browser (Ctrl+Shift+R) since `index.html` and `theseus.css` are served via `StaticFiles`.
- **Alpine state lives on `theseus()`**: workspace name is `this.stats.workspace` (NOT `activeWorkspace`); chat messages are `this.currentChat.messages[]`; toasts via `this.toast(msg, kind)`; scroll target is `this.$refs.msgs`.
- **Re-render Lucide icons after dynamic markup**: existing `$watch` hooks on `currentChat`, `palette.open`, `wsModal.open`, etc. call `lucide.createIcons()` — add a watcher when introducing a new modal/overlay.
- **UTF-8 only**: Save files as UTF-8 (no BOM round-trip through Windows-1252). If you see `Â·`, `â†'`, `â€"` etc. in the rendered UI, that's mojibake — repair targeted patterns before committing. PowerShell: always use `Out-File -Encoding utf8`.

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
3.  **Prompt Signal Tests**:
    - `python tools/test_query_prompt.py --workspace <name> --query-id M2` — Tests mentor persona signal detection
    - Signal categories: `shipley_terms`, `mentoring_language`, `risk_flags`, `reasoning_chain`
    - Note: Tests query against cached LLM responses. Re-process workspace under new prompts for fresh results.

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
- **Scope**: `extraction`, `inference`, `neo4j`, `prompts`, `agents`, `multimodal`, `ontology`

### Pre-Commit Checklist

Before proposing a commit, verify:

1. **Cross-system alignment**: If the change touches entity types, relationship types, or Shipley methodology, have all 3 prompt systems been audited? (See Cross-Cutting Change Checklist)
2. **Schema consistency**: Do `VALID_ENTITY_TYPES` and `VALID_RELATIONSHIP_TYPES` in `schema.py` match what the prompts reference?
3. **Test fixtures updated**: Do test signal patterns and assertions reflect the current vocabulary?
4. **Version bumped**: If extraction prompt changed, is the version number in the prompt header updated?
   - Run `python -m pytest tests` to run the standard test suite.
   - Use markers if available (check `tests/pytest.ini` if present).
5. **Prompt Signal Tests**:
   - `python tools/test_query_prompt.py --workspace <name> --query-id M2` — Tests mentor persona signal detection
   - Signal categories: `shipley_terms`, `mentoring_language`, `risk_flags`, `reasoning_chain`
   - Note: Tests query against cached LLM responses. Re-process workspace under new prompts for fresh results.

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
- **Scope**: `extraction`, `inference`, `neo4j`, `prompts`, `agents`, `multimodal`, `ontology`

### Pre-Commit Checklist

Before proposing a commit, verify:

1. **Cross-system alignment**: If the change touches entity types, relationship types, or Shipley methodology, have all 3 prompt systems been audited? (See Cross-Cutting Change Checklist)
2. **Schema consistency**: Do `VALID_ENTITY_TYPES` and `VALID_RELATIONSHIP_TYPES` in `schema.py` match what the prompts reference?
3. **Test fixtures updated**: Do test signal patterns and assertions reflect the current vocabulary?
4. **Version bumped**: If extraction prompt changed, is the version number in the prompt header updated?

---

## Configuration (.env)

```bash
# LLM - xAI Grok (OpenAI-compatible API)
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4.20-0309-reasoning
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
