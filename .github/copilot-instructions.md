# Copilot Instructions for GovCon-Capture-Vibe

## Project Overview

**Ontology-based RAG system** for federal RFP analysis that transforms generic document processing into specialized government contracting intelligence. Uses **RAG-Anything** (multimodal ingestion) + **LightRAG** (knowledge graph/queries) with **xAI Grok** cloud processing for 417x speedup over local processing.

**Core Innovation**: Government contracting entity types + LLM-powered relationship inference enables Section L↔M mapping, requirement traceability, and Shipley methodology compliance.

---

## CRITICAL EXECUTION RULES

### Rule 1: Virtual Environment & Terminal Management

**CRITICAL**: Always use the SAME terminal for sequential commands. Never open a new terminal mid-workflow.

**Before ANY Python execution**, activate `.venv` as a separate command in ONE terminal:

```powershell
# Step 1: Activate venv (ONCE per terminal session)
.venv\Scripts\Activate.ps1

# Step 2: Run subsequent commands in SAME terminal
python app.py
# or
uv pip list
# or
python -m pytest
```

**Common Mistakes to AVOID**:

- ❌ Opening new terminal for each command (breaks venv activation)
- ❌ Running Python in global environment (installs packages globally)
- ❌ Combining activation with execution: `.venv\Scripts\Activate.ps1; python app.py`

**Correct Workflow**:

1. Activate `.venv` in one terminal
2. Keep using that SAME terminal for all subsequent Python/uv/pytest commands
3. Terminal prompt shows `(.venv)` when active

### Rule 2: Use Workspace Tools for File Operations

**NEVER use PowerShell/terminal for file operations.** Always use workspace tools:

| Operation   | ✅ CORRECT TOOL                  | ❌ NEVER USE                             |
| ----------- | -------------------------------- | ---------------------------------------- |
| Read file   | `read_file`                      | `Get-Content`, `cat`, `type`             |
| Create file | `create_file`                    | `New-Item`, `echo >`, `Out-File`         |
| Edit file   | `replace_string_in_file`         | `(Get-Content).Replace()`, `Set-Content` |
| Search      | `grep_search`, `semantic_search` | `Select-String`, `findstr`               |
| List dir    | `list_dir`                       | `Get-ChildItem`, `ls`, `dir`             |
| Copy file   | `read_file` + `create_file`      | `Copy-Item`, `cp`                        |

**PowerShell ONLY for**:

- Running Python: `python app.py`, `python -m pytest`
- Package management: `uv sync`, `uv pip list`
- Git operations: `git status`, `git commit -m "message"`
- Process management: `Get-Process python`

**Why This Matters**: PowerShell file operations bypass workspace tracking and can cause sync issues with the editor. Always use workspace tools for file I/O.

### Rule 3: Application Management & Environment

**NEVER start the application yourself** - only the user can run the app. The application server (`python app.py`) must be started by the user in their own terminal session.

**ALWAYS ensure the virtual environment is active** before any Python operations. Check that the terminal prompt shows `(.venv)` before proceeding with Python commands.

**STOP creating documents for everything** - focus on code changes and direct implementation. Only create documentation when explicitly requested or when it serves a critical architectural purpose.

### Rule 4: Stay Grounded in Core Libraries

**ALL actions must stay grounded in LightRAG and RAG-Anything repos and libraries**. Do not invent APIs, methods, or capabilities that don't exist in these core libraries. Reference the actual source code and documentation from:

- [LightRAG GitHub](https://github.com/HKUDS/LightRAG)
- [RAG-Anything GitHub](https://github.com/HKUDS/RAG-Anything)

**Do not** propose solutions that require modifications to these external libraries unless they are already implemented in the forked versions within this project.

---

## Essential Architecture

**Two-Stage Processing Flow**:

1. **INGESTION** (Cloud - xAI Grok): RFP → RAG-Anything multimodal parsing → entity extraction → GraphML storage
2. **POST-PROCESSING** (Local - Phase 6): GraphML → LLM relationship inference → enhanced knowledge graph → LightRAG WebUI

**Key Components**:

- `app.py` (40 lines): Entry point importing pip-installed libraries
- `src/raganything_server.py` (790 lines): Main server wrapping RAG-Anything + LightRAG with government contracting ontology
- Phase 6 pipeline: LLM-powered relationship inference for Section L↔M mapping and annex linkage

**Dependencies**: Uses `raganything[all]` and `lightrag-hku` from pip - NO forked libraries in codebase.

---

## Development Workflows

### Starting the Server

**IMPORTANT**: Never start the application yourself. The user must run the app in their terminal.

```powershell
# User must activate venv and start server themselves
.venv\Scripts\Activate.ps1
python app.py
# Server ready at http://localhost:9621
```

### Processing an RFP

```powershell
# Upload via WebUI: http://localhost:9621/webui
# OR use custom endpoint with auto Phase 6:
curl -X POST http://localhost:9621/insert \
  -F "file=@navy_rfp.pdf" \
  -F "mode=auto"  # Triggers Phase 6 post-processing
```

### Branch Strategy

```
main                                   # Production releases only
├── 002-lighRAG-govcon-ontology        # ARCHIVED: Fully local
├── 003-ontology-lightrag-cloud        # STABLE: Cloud processing
├── 004-code-optimization             # ARCHIVED: Performance refactoring
├── 005-entity-type-expansion         # ARCHIVED: Added entity types
├── 006-phase6-llm-inference          # ARCHIVED: LLM relationship inference
├── 007-postgresql-integration        # ARCHIVED: Data warehouse foundation
├── 008-knowledge-graph-enhancement  # ARCHIVED: Multi-workspace graphs
├── 009-cross-rfp-intelligence        # ARCHIVED: Competitive analytics
└── 010-pivot-enterprise-platform     # ACTIVE: Enterprise Neo4j evolution
```

**Never merge directly to main** - use feature branches, PR when stable.

---

## Configuration (.env)

```bash
# xAI Grok LLM (OpenAI-compatible API)
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4-fast-reasoning
LLM_BINDING_API_KEY=xai-your-key

# OpenAI Embeddings (CRITICAL: Use OpenAI endpoint, NOT xAI!)
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_BINDING_API_KEY=sk-proj-your-key

# Processing optimization
CHUNK_SIZE=4096
MAX_ASYNC=32
LLM_MODEL_TEMPERATURE=0.1
```

**Security**: Only use cloud processing for PUBLIC government RFPs. Proprietary queries stay 100% local.

---

## Common Pitfalls

### ❌ Importing from Non-Existent Local Packages

```python
# WRONG: No forked libraries in src/
from lightrag.lightrag import LightRAG  # ModuleNotFoundError

# CORRECT: Use pip-installed packages
from lightrag import LightRAG           # From pip package
from raganything import RAGAnything     # From pip package
```

### ❌ Processing Large RFPs Without Phase 6

```python
# WRONG: Using vanilla LightRAG for government RFPs
rag.insert(file_path)  # Misses L↔M relationships, annex linkage

# CORRECT: Use custom /insert endpoint with Phase 6
POST /insert with mode=auto  # Triggers post-processing pipeline
```

### ❌ Starting Application Without User Permission

```python
# WRONG: Never start the app yourself
python app.py  # Only user can do this

# CORRECT: Guide user to start app in their terminal
# Tell user: "Please run: .venv\Scripts\Activate.ps1; python app.py"
```

### ❌ Creating Documentation for Everything

```python
# WRONG: Creating docs for every minor change
# Don't create README updates, architecture docs, etc. unless explicitly requested

# CORRECT: Focus on code implementation
# Only create docs when they serve critical architectural purpose
```

---

## Key Files

| File                                | Purpose                      |
| ----------------------------------- | ---------------------------- |
| `app.py`                            | Entry point                  |
| `src/raganything_server.py`         | Main server with ontology    |
| `src/llm_relationship_inference.py` | Phase 6 inference algorithms |
| `.env`                              | Cloud configuration          |

---

**Last Updated**: October 2025 (Branch 010 - Enterprise Neo4j Evolution)
