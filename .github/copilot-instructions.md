# Copilot Instructions for GovCon-Capture-Vibe

## Project Overview

**Ontology-based RAG system** for federal RFP analysis that transforms generic document processing into specialized government contracting intelligence. Uses **RAG-Anything** (multimodal ingestion) + **LightRAG** (knowledge graph/queries) with **xAI Grok** cloud processing for 417x speedup over local processing.

**Core Innovation**: Government contracting entity types (12 types: REQUIREMENT, CLAUSE, EVALUATION_FACTOR, etc.) + LLM-powered relationship inference enables Section L↔M mapping, requirement traceability, and Shipley methodology compliance.

**Current Status** (Branch 004): Performance-based refactoring - optimizing for minimal code footprint while maintaining 69-second RFP processing (Navy MBOS: 594 entities, $0.042 cost).

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

---

## Architecture Essentials

### The Minimal Active Codebase (~790 lines post-cleanup)

```
app.py (40 lines)                     # Entry point - imports RAG-Anything/LightRAG from pip
└── src/raganything_server.py (790)  # Main server wrapping RAG-Anything + LightRAG
    ├── configure_raganything_args()  # 12 govcon entity types + cloud config
    ├── initialize_raganything()      # RAG-Anything instance with custom prompts
    ├── Custom /insert endpoint       # Phase 6 post-processing pipeline
    └── Phase 6 pipeline:
        ├── ucf_detector.py           # Uniform Contract Format detection
        ├── ucf_section_processor.py  # Section-aware extraction prompts
        └── llm_relationship_inference.py # LLM-powered L↔M/annex linking
```

**Key Insight**: We use **pip-installed libraries** (`raganything[all]`, `lightrag-hku`) and wrap them with ~790 lines of domain logic. NO forked libraries in the codebase.

### Critical Dependencies (External Libraries)

```python
# These come from pip, NOT local code:
from raganything import RAGAnything, RAGAnythingConfig  # Multimodal parsing (MinerU)
from lightrag import LightRAG                            # Knowledge graph + WebUI
from lightrag.llm.openai import openai_complete_if_cache # Cloud LLM wrapper

# Our 790-line customization wraps these with:
# - 12 government contracting entity types
# - Phase 6 LLM relationship inference
# - UCF structure detection
```

### The Two-Stage Processing Flow

```
1. INGESTION (Cloud - xAI Grok)
   RFP Upload → RAG-Anything (MinerU parser)
   → 4096-token chunks (5x larger than local)
   → 32 parallel requests
   → Extract 17 entity types (semantic-first detection)
   → Save to ./rag_storage/graph_chunk_entity_relation.graphml

2. POST-PROCESSING (Local - Phase 6 Pipeline)
   Load GraphML → LLM relationship inference
   → Section L↔M mapping (evaluation instructions)
   → Annex linkage (J-#### → parent sections)
   → Requirement→Evaluation factor mapping
   → Save enhanced graph → LightRAG WebUI
```

**Result**: Processing times vary by RFP (MCPP ~45 min, $0.65-$1.00 typical).

---

## Government Contracting Domain Knowledge

### The 17 Entity Types (Core Ontology)

Defined in `src/server/initialization.py` - these transform generic LightRAG into domain-specific intelligence:

```python
# Core entities (LightRAG defaults)
organization           # Contractors, agencies, departments
concept                # CLINs, budget items, technical concepts
event                  # Milestones, delivery dates, reviews
technology             # Systems, tools, platforms
person                 # POCs, contracting officers
location               # Performance locations, delivery sites

# Government contracting specific (critical differentiators)
requirement            # Must/should/may obligations (Shipley methodology)
clause                 # FAR/DFARS/agency supplement clauses (regulatory compliance)
section                # RFP sections (UCF A-M structure or semantic detection)
document               # Referenced specs, standards, attachments, annexes
deliverable            # Contract deliverables, work products, CDRLs
evaluation_factor      # Section M scoring criteria (semantic detection, RFP-agnostic)
submission_instruction # Section L format/page limits (semantic detection, RFP-agnostic)
strategic_theme        # Win themes, hot buttons, discriminators, proof points
statement_of_work      # PWS/SOW/SOO content (semantic detection, location-agnostic)
program                # Major programs (MCPP II, Navy MBOS, etc.)
equipment              # Physical items (batteries, vehicles, tools, NSE)
```

### Why These Entity Types Matter

**Generic LightRAG extracts**: "person", "location", "organization"  
**Our system extracts**: Domain-specific intelligence with semantic understanding:

- **requirement** (must vs should vs may - criticality levels)
- **clause** (FAR/DFARS applicability, flowdown obligations, cost impacts)
- **evaluation_factor** (Section M weights, scoring methodology - semantic detection works for UCF and non-UCF RFPs)
- **submission_instruction** (page limits, format requirements - semantic detection regardless of section label)
- **strategic_theme** (win themes, hot buttons, discriminators - capture intelligence)
- **statement_of_work** (semantic detection whether in Section C, attachment, or embedded)

**Key Innovation**: Semantic-first detection means content determines entity type, not structural labels. Works for UCF (Section A-M), non-UCF (grants, simplified acquisitions), and hybrid (IDIQ task orders) RFPs.

**Example**: Section L states "Technical approach limited to 10 pages" + Section M says "Factor 1: Technical Approach (40% weight)"  
→ Phase 6 LLM inference creates: `SUBMISSION_INSTRUCTION --EVALUATED_BY--> EVALUATION_FACTOR`  
→ Enables query: "What page limits affect Technical Approach scoring?"

### Uniform Contract Format (UCF) Detection

Federal RFPs follow standard structure (FAR 15.210):

```
Section A: Solicitation/Contract Form (cover page, deadlines)
Section B: Supplies/Services & Prices (CLINs)
Section C: Statement of Work (SOW) - often references J attachments
Section H: Special Requirements (security, key personnel)
Section I: Contract Clauses (FAR/DFARS)
Section J: Attachments (PWS, deliverables, sample docs)
Section L: Instructions to Offerors (page limits, format)
Section M: Evaluation Factors (scoring criteria, weights)
```

**UCF Detection** (`ucf_detector.py`): Analyzes first 5 pages for section patterns → triggers section-aware extraction prompts that preserve structure.

---

## Phase 6: LLM-Powered Relationship Inference

### The Critical Innovation (December 2024 → January 2025)

**Problem**: Initial Phase 6 used regex patterns for L↔M mapping and annex linking. Result: 84.6% annex coverage, brittle patterns, zero agency adaptability.

**Solution**: Replace 295 lines of regex with 550 lines of **LLM-powered semantic inference** (`llm_relationship_inference.py`).

### Four Inference Algorithms

```python
# 1. Section L↔M Mapping (evaluation instructions)
infer_section_l_m_relationships(entities, relationships)
# Finds: SUBMISSION_INSTRUCTION (page limits) --EVALUATED_BY--> EVALUATION_FACTOR
# Result: Proposal outline optimization based on scoring weights

# 2. Annex Linkage (J-#### → parent section)
infer_annex_relationships(entities, relationships)
# Links: ANNEX "J-0005 PWS" --ATTACHMENT_OF--> SECTION "Section J Attachments"
# Result: 100% coverage (vs 84.6% regex), works for ANY naming convention

# 3. Clause Clustering (FAR → parent section)
infer_clause_relationships(entities, relationships)
# Groups: CLAUSE "FAR 52.222-6" --CHILD_OF--> SECTION "Section I"
# Works for 26+ agency supplements (FAR, DFARS, AFFARS, NMCARS, etc.)

# 4. Requirement→Evaluation Mapping (SOW → scoring)
infer_requirement_evaluation_relationships(entities, relationships)
# Links: REQUIREMENT "Weekly status reports" --EVALUATED_BY--> EVALUATION_FACTOR "Management Approach"
# Result: Effort allocation guidance for proposal teams
```

### Implementation Pattern

```python
# Load existing graph from RAG-Anything processing
entities, relationships = parse_graphml("./rag_storage/graph_chunk_entity_relation.graphml")

# Run all four inference algorithms
new_relationships = await infer_all_relationships(entities, relationships, llm_func)

# Save enhanced graph back to LightRAG storage
save_relationships_to_graphml(new_relationships, graphml_path)
save_relationships_to_kv_store(new_relationships, kv_store_path)
```

**Cost**: ~$0.01 per RFP (5,000-token context to Grok-beta)  
**Benefit**: 100% annex linkage, agency-agnostic patterns, semantic understanding

---

## Development Workflows

### Starting the Server

```powershell
# 1. Activate venv (separate command!)
.venv\Scripts\Activate.ps1

# 2. Start server (uses pip-installed RAG-Anything + LightRAG)
python app.py
# Server ready at http://localhost:9621
```

### Processing an RFP (Phase 6 Pipeline)

```powershell
# Upload via WebUI: http://localhost:9621/webui
# OR use custom endpoint with auto Phase 6:

curl -X POST http://localhost:9621/insert \
  -F "file=@navy_rfp.pdf" \
  -F "mode=auto"  # Triggers Phase 6 post-processing

# Result: 69 seconds later, 594 entities in ./rag_storage/
```

### Inspecting Knowledge Graph

```powershell
# Load GraphML for analysis (PowerShell syntax)
python -c "from llm_relationship_inference import parse_graphml; entities, rels = parse_graphml('./rag_storage/graph_chunk_entity_relation.graphml'); print(f'{len(entities)} entities, {len(rels)} relationships')"
```

### Branch Strategy (Production)

```
main                                   # Production releases only
├── 002-lighRAG-govcon-ontology        # ARCHIVED: Fully local (8 hours/RFP)
├── 003-ontology-lightrag-cloud        # STABLE: Cloud processing (69s/RFP)
└── 004-code-optimization (ACTIVE)     # Performance refactoring
```

**Never merge directly to main** - use feature branches, PR when stable.

---

## Configuration Essentials (.env)

```bash
# xAI Grok LLM (OpenAI-compatible API)
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4-fast-reasoning
LLM_BINDING_API_KEY=xai-your-key  # Get from https://console.x.ai

# OpenAI Embeddings (CRITICAL: Use OpenAI endpoint, NOT xAI!)
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1  # NOT api.x.ai!
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_BINDING_API_KEY=sk-proj-your-key

# Cloud optimization (5x larger chunks, 32 parallel)
CHUNK_SIZE=4096
MAX_ASYNC=32
LLM_MODEL_TEMPERATURE=0.1  # Deterministic extraction
```

**Security**: Only use cloud processing for PUBLIC government RFPs. Proprietary queries stay 100% local.

---

## Branch 004: Performance-Based Refactoring

**Charter**: `docs/BRANCH_004_CODE_OPTIMIZATION.md` (non-prescriptive constraints)

**Constraints**:

- Net LOC ≤ baseline (target negative delta)
- No startup time increase
- No p95 latency regression on /health or /query
- No breaking API changes
- Minimize dependencies unless they reduce net code

**Measurement Baseline**:

```powershell
# LOC count
(Get-ChildItem -Recurse -File -Include *.py src/,app.py).ForEach{$_.Length} | Measure-Object -Sum

# Startup time: app launch → "ready" log
Measure-Command { python app.py }

# p95 latency: /health and representative /query
Invoke-RestMethod http://localhost:9621/health
```

**Workflow**: Propose → Implement → Re-measure → Commit (atomic). Revert if any metric regresses.

---

## Common Pitfalls & Solutions

### ❌ Importing from Non-Existent Local Packages

```python
# WRONG: No forked libraries in src/
from lightrag.lightrag import LightRAG  # ModuleNotFoundError

# CORRECT: Use pip-installed packages
from lightrag import LightRAG           # From pip package
from raganything import RAGAnything     # From pip package
```

### ❌ Modifying Entity Types Without Understanding Impact

```python
# WRONG: Adding entity types without relationship constraints
entity_types = [..., "NEW_TYPE"]  # Creates orphaned entities

# CORRECT: Define valid relationships in Phase 6 inference
# See llm_relationship_inference.py for relationship patterns
```

### ❌ Processing Large RFPs Without Phase 6

```python
# WRONG: Using vanilla LightRAG for government RFPs
rag.insert(file_path)  # Misses L↔M relationships, annex linkage

# CORRECT: Use custom /insert endpoint with Phase 6
POST /insert with mode=auto  # Triggers post-processing pipeline
```

---

## Key File Reference Guide

| File                                     | Purpose                       | Lines | When to Edit                                 |
| ---------------------------------------- | ----------------------------- | ----- | -------------------------------------------- |
| `app.py`                                 | Entry point                   | 40    | Never (minimal by design)                    |
| `src/raganything_server.py`              | Main server                   | 790   | Entity types, cloud config, Phase 6 pipeline |
| `src/llm_relationship_inference.py`      | Phase 6 inference (in `src/`) | 550   | Add new relationship inference algorithms    |
| `src/ucf_detector.py`                    | UCF format detection          | ~200  | Enhance section pattern recognition          |
| `src/ucf_extractor.py`                   | UCF entity extraction         | ~150  | Refine UCF-specific entity extraction        |
| `src/ucf_section_processor.py`           | Section-aware extraction      | ~150  | Refine section detection prompts             |
| `src/phase6_prompts.py`                  | LLM prompt templates          | ~300  | Refine inference prompts for quality         |
| `src/phase6_validation.py`               | Phase 6 validation            | ~200  | Add new validation checks                    |
| `.env`                                   | Cloud configuration           | N/A   | API keys, chunk sizes, concurrency           |
| `docs/ARCHITECTURE.md`                   | Complete architecture         | ~1000 | Major architectural changes                  |
| `docs/PHASE_6_IMPLEMENTATION_HISTORY.md` | Phase 6 development record    | ~600  | Historical reference only                    |

---

## External Resources

**Required Reading**:

- **[LightRAG GitHub](https://github.com/HKUDS/LightRAG)** - Core knowledge graph engine
- **[RAG-Anything GitHub](https://github.com/HKUDS/RAG-Anything)** - Multimodal document parsing
- **[xAI Grok Docs](https://docs.x.ai)** - Cloud LLM API reference

**Domain Knowledge**:

- **Shipley Guides** (in `docs/`) - Requirements analysis methodology
- **FAR 15.210** - Uniform Contract Format specification
- **[Awesome Procurement Data](https://github.com/makegov/awesome-procurement-data)** - Government contracting terminology
- **[AI RFP Simulator](https://github.com/felixlkw/ai-rfp-simulator)** - Entity relationship patterns (Chinese - use translation)

---

## Shipley Methodology Integration

### Prompt Templates Archive

Historical prompt templates used to build the ontology (now integrated into Phase 6 LLM inference):

**Requirements Extraction** (`shipley_requirements_extraction.txt`):

- Shipley 4-level compliance scale: Compliant/Partial/Non-Compliant/Not Addressed
- Must/Should/May requirement classification (Shipley criticality)
- Evaluation factor mapping (Section L↔M relationships)
- Gap analysis framework (Shipley Capture Guide p.85-90)

**Compliance Assessment** (`assess_compliance_prompt.txt`):

- Coverage scoring: 0-100 scale with gradations (0/10/30/50/70/85/95/100)
- High priority logic: Critical themes from RFP analysis
- Proposal evidence mapping with page references
- Risk assessment based on factor weights

**Questions for Government** (`generate_qfg_prompt.txt`):

- Shipley Capture Guide p.25: Intel gathering via clarification questions
- Ambiguity detection: Page limits, evaluation weights, scope conflicts
- Q&A period identification (Section A/L deadlines)
- Max 7 high-impact questions with RFP section references

**Generic Requirements** (`extract_requirements_prompt.txt`):

- Structured attribute extraction (20+ standard RFP fields)
- Evaluation factors with sub-factors and relative importance
- Requirement→Factor mapping for traceability
- Critical summary with top themes prioritization

### Integration into Phase 6

These prompt patterns are now **embedded in LLM-powered inference**:

```python
# src/llm_relationship_inference.py uses Shipley patterns for:
infer_section_l_m_relationships()      # Section L↔M mapping (Shipley compliance matrix)
infer_requirement_evaluation_relationships()  # Requirement→Factor linkage
infer_clause_relationships()           # FAR/DFARS clause clustering
infer_annex_relationships()            # Attachment→Section mapping
```

**Key Transformation**: Regex patterns → Semantic LLM inference with Shipley methodology grounding.

---

## Branch 004 Measurement Guide

### Establishing Baseline Metrics

```powershell
# 1. LOC count (src/ + app.py)
$files = Get-ChildItem -Recurse -File -Include *.py src/,app.py
$totalLines = ($files | ForEach-Object { (Get-Content $_.FullName).Count } | Measure-Object -Sum).Sum
Write-Host "Total LOC: $totalLines"

# 2. Startup time (app launch to ready)
Measure-Command {
    $process = Start-Process -FilePath "python" -ArgumentList "app.py" -PassThru -NoNewWindow
    Start-Sleep -Seconds 5  # Wait for "ready" log
    Stop-Process -Id $process.Id -Force
}

# 3. Health endpoint latency (p95 approximation)
$times = 1..10 | ForEach-Object {
    (Measure-Command { Invoke-RestMethod http://localhost:9621/health }).TotalMilliseconds
}
$p95 = ($times | Sort-Object)[-2]  # Rough p95 (2nd highest)
Write-Host "p95 latency: $p95 ms"

# 4. Memory usage (steady-state RSS)
Get-Process python | Select-Object WorkingSet64 | Format-List
```

**Note**: These measurement scripts are temporary - delete after Branch 004 completion per charter guidelines.

---

**Last Updated**: January 2025 (Branch 004 - Performance Refactoring)  
**Key Metric**: 69 seconds processing time, 594 entities, $0.042 cost (Navy MBOS baseline)
