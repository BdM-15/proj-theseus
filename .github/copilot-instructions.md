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

- [System Architecture and Design](../docs/ARCHITECTURE.md) - Overall system architecture, technology stack, and performance metrics
- [Feature Roadmap](../docs/capture-intelligence/FEATURE_ROADMAP.md) - Future features and agent-powered proposal development workflows
- [Semantic Post-Processing](../docs/inference/SEMANTIC_POST_PROCESSING.md) - LLM relationship inference algorithms
- [Neo4j Integration](../docs/neo4j/NEO4J_USER_GUIDE.md) - Graph database workspace management

**Note**: Suggest updates to these documents if you find incomplete or conflicting information.

### Root Folders

- `src/` - Python source code organized by domain
- `prompts/` - LLM prompt templates for extraction and inference
- `tests/` - Validation scripts (test\_\*.py files, run directly with Python)
- `tools/` - Neo4j workspace management and validation utilities
- `docs/` - Architecture documentation and feature roadmaps
- `inputs/` - RFP document staging (uploaded/ and **enqueued**/ subdirs)
- `rag_storage/` - Per-workspace knowledge graph data (GraphML + embeddings)

### Core Architecture (`src/` folder)

- `src/server/` - FastAPI server configuration and routing
  - `config.py` - LightRAG global_args setup (MUST load .env first)
  - `routes.py` - Custom endpoints with batch completion detection
  - `initialization.py` - RAGAnything wrapper initialization
- `src/inference/` - Semantic post-processing algorithms
  - `semantic_post_processor.py` - 8 LLM relationship inference algorithms
  - `neo4j_graph_io.py` - Neo4j CRUD operations
  - `batch_processor.py` - Auto-trigger logic after document batches
- `src/ontology/` - Domain schema validation
  - `schema.py` - Pydantic models for 18 entity types
- `src/extraction/` - Custom entity extraction logic
- `raganything_server.py` - Main entry point (orchestrates all components)

**Dependencies**: Uses `raganything[all]` and `lightrag-hku` from pip. **NO forked libraries** - all customization via configuration and wrapper modules.

### Processing Pipeline (6 Steps)

```
1. Document Upload → /insert or /documents/upload endpoints
2. MinerU Parsing → Tables, images, text extraction (GPU-accelerated)
3. LightRAG Chunking → 8,192 tokens/chunk, 15% overlap
4. Entity Extraction → 18 govcon types via xAI Grok + Pydantic validation
5. Relationship Extraction → LightRAG native inference
6. Semantic Post-Processing → 8 LLM algorithms (auto-triggered after batch)
```

**Key Modules**:

| Path                        | Purpose                                                |
| --------------------------- | ------------------------------------------------------ |
| `app.py`                    | Entry point - starts Neo4j Docker + server             |
| `src/raganything_server.py` | Server orchestration, imports modular components       |
| `src/server/config.py`      | LightRAG global_args configuration                     |
| `src/server/routes.py`      | Custom `/insert`, `/documents/upload` + batch tracking |
| `src/inference/`            | Semantic post-processing algorithms                    |
| `src/ontology/schema.py`    | Pydantic models for entity validation                  |
| `prompts/extraction/`       | Entity extraction prompts (~3,000 lines)               |

---

## Validating Changes

MANDATORY: Always activate virtual environment and check for errors BEFORE running scripts or declaring work complete.

### Environment Setup

- **NEVER run Python commands without activating .venv first**
- Monitor terminal prompt for `(.venv)` indicator
- Use ONE terminal session for all sequential commands

### Validation Steps

`.env` MUST load BEFORE importing LightRAG (see `src/raganything_server.py` line 23):

```python
from dotenv import load_dotenv
load_dotenv()  # BEFORE any LightRAG imports
```

LightRAG uses `os.getenv()` in dataclass defaults at import time.

### Import Patterns

```python
# ✅ CORRECT: pip-installed packages
from lightrag import LightRAG
from raganything import RAGAnything
from lightrag.api.config import global_args

# ❌ WRONG: These don't exist locally
from lightrag.lightrag import LightRAG  # ModuleNotFoundError
```

### Entity Type Handling

Entity types are lowercase internally (see `src/server/config.py` line 76):

```python
global_args.entity_types = ["requirement", "clause", "section", ...]  # lowercase
```

Validation via Pydantic in `src/ontology/schema.py` - do NOT modify entity types post-extraction.

### Finding Related Code

1. **Semantic search first** - Use for general concepts like "batch processing" or "entity extraction"
2. **Grep for exact strings** - Use for error messages, class names, or function names
3. **Follow imports** - Check which files import problematic modules (especially circular dependencies)
4. **Check test files** - Often reveal usage patterns and expected behavior (e.g., `tests/test_json_extraction.py` shows entity validation)
5. **Trace prompts** - Entity extraction logic lives in `prompts/extraction/` (~3,000 lines), not Python code

---

## Branch Management Strategy

### **NEVER Work Directly on `main` Branch**

**Rule**: ALL development happens on feature branches to isolate experimentation and enable easy rollback.

### Branch Naming Convention

**Format**: `{number}-{descriptive-kebab-case-name}`

**Examples**:

- `028-parallel-chunk-extraction` (Issue #17)
- `029-prompt-compression` (Issue #14)
- `030-shipley-knowledge-graph` (Issue #25)

**Number Sequence**: Incremental counter showing branch creation order in application lifecycle (easy to track "when was this developed?")

**Agent Responsibility**: When planning a feature implementation, the agent MUST:

1. Identify the next branch number (check `git branch -a` for highest number)
2. Create descriptive name from GitHub issue title (kebab-case)
3. Suggest branch creation: `git checkout -b {number}-{description}`
4. Document branch purpose in plan

### Branch Workflow

```powershell
# 1. Start from main (ensure up-to-date)
git checkout main
git pull origin main

# 2. Create feature branch (agent suggests name)
git checkout -b 028-parallel-chunk-extraction

# 3. Develop, commit iteratively
git add <files>
git commit -m "feat: implement parallel chunk extraction with semaphore"

# 4. Push to remote
git push -u origin 028-parallel-chunk-extraction

# 5. Create PR linking to issue
# (GitHub UI or gh CLI)

# 6. After merge, delete branch
git checkout main
git pull origin main
git branch -d 028-parallel-chunk-extraction
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Types**:

- `feat:` New feature (e.g., "feat: add parallel chunk processing")
- `fix:` Bug fix (e.g., "fix: handle empty extraction results")
- `refactor:` Code restructuring (e.g., "refactor: extract semaphore logic to helper")
- `docs:` Documentation only (e.g., "docs: update ARCHITECTURE.md with parallelism")
- `test:` Adding/updating tests (e.g., "test: add parallel extraction validation")
- `chore:` Maintenance (e.g., "chore: update dependencies")

**Scope** (optional): `extraction`, `inference`, `neo4j`, `prompts`, `agents`

**Examples**:

```
feat(extraction): implement parallel chunk processing with asyncio.gather

- Add semaphore-based concurrency (8x default)
- Use existing MAX_ASYNC env var
- Preserve error handling and retry logic
- Expected 87% time reduction for extraction phase

Closes #17
```

---

## Development Workflows

### Adding New Entity Types

1. Add to `src/server/config.py` → `global_args.entity_types` (lowercase)
2. Add Pydantic model to `src/ontology/schema.py`
3. Update `prompts/extraction/entity_extraction_prompt.md` with examples
4. Test with `tests/test_json_extraction.py`

### Neo4j Workspace Management

```powershell
# List all workspaces
python tools/neo4j/clear_neo4j.py --list

# Duplicate baseline workspace (interactive)
python tools/neo4j/duplicate_workspace.py

# Clear workspace for fresh testing
python tools/neo4j/clear_neo4j.py --workspace NAME
```

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
BATCH_TIMEOUT_SECONDS=30  # Wait before triggering post-processing
```

---

## Common Patterns

### Batch Document Upload

The `DocumentQueueTracker` in `src/server/routes.py` auto-detects batch completion:

- Uploads register via `register_request_start()`
- Processing tracked via `document_started()` / `document_completed()`
- Post-processing triggers after `BATCH_TIMEOUT_SECONDS` with no new uploads

### Custom Endpoint Override

Routes override LightRAG defaults in `src/raganything_server.py` (lines 86-93):

```python
# Remove original endpoints, add custom ones with multimodal + semantic inference
create_insert_endpoint(app, rag_instance)
create_documents_upload_endpoint(app, rag_instance)
```

---

## File Operations

**Use workspace tools** (read_file, create_file, replace_string_in_file), NOT PowerShell for file I/O.

**PowerShell only for**: `python`, `uv`, `git`, `docker` commands.

---

## GPU Warning

After `uv sync`, PyTorch downgrades to CPU-only. Reinstall CUDA versions manually:

```powershell
uv pip install torch==2.9.0+cu128 torchvision==0.24.0+cu128 --index-url https://download.pytorch.org/whl/cu128
```

Verify: `python -c "import torch; print(torch.cuda.is_available())"` → should be `True`

---

## Context Engineering Notes

This is a **living document** - refine based on observed AI mistakes or shortcomings. When implementing future features from `docs/future_features/`, consider creating:

- **Custom agents** (`.github/agents/*.agent.md`) for specialized workflows (e.g., planning, implementation, validation)
- **Prompt files** (`.github/prompts/*.prompt.md`) for reusable task workflows
- **Agent handoffs** for multi-step processes (plan → implement → test)

See [VS Code Context Engineering Guide](https://code.visualstudio.com/docs/copilot/guides/context-engineering-guide) for patterns.

---

**Last Updated**: December 2025
