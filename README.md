# Project Theseus — Capture Workbench

**Ontology-Based RAG for Federal RFP Capture & Proposal Intelligence**

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](https://github.com/BdM-15/proj-theseus)
[![Python](https://img.shields.io/badge/python-3.13+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## Executive Summary

Project Theseus is a **capture workbench** for federal RFP analysis. It pairs a domain-specific government contracting ontology with **RAG-Anything** (multimodal ingestion via MinerU) + **LightRAG** (knowledge graph + hybrid retrieval) and **xAI Grok** cloud LLMs, then surfaces the result through a custom **Capture Workbench UI** (Capture Chat + Intel Panels) backed by a Shipley-mentor query persona.

### Core Innovation

**Government contracting ontology + LLM-powered relationship inference + Shipley-aligned query persona** enables:

- **Section L ↔ M mapping** (submission instructions → evaluation factors)
- **Requirement traceability** across Sections C / L / M / J
- **Shipley methodology** in queries — discriminators, win themes, hot buttons, proof points, FAB chains, ghost language, compliance matrix
- **Annex / attachment linkage** to parent documents (`CHILD_OF`, `ATTACHMENT_OF`)
- **Multimodal awareness** — tables, images, and equations are analyzed by a VLM with the same govcon vocabulary as the text extractor

### Architecture Stack

| Component             | Technology                                                           | Purpose                                                                                |
| --------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| **Document Parsing**  | [MinerU](https://github.com/opendatalab/MinerU) 3.x via RAG-Anything | Multimodal PDF / DOCX / XLSX extraction (tables, images, equations)                    |
| **RAG Orchestration** | [RAG-Anything](https://github.com/HKUDS/RAG-Anything) v1.2.10+       | Multimodal document pipeline + context-aware processing                                |
| **Knowledge Graph**   | [LightRAG](https://github.com/HKUDS/LightRAG) v1.4.13+               | Graph construction + hybrid retrieval (pip: `lightrag-hku`)                            |
| **LLM**               | xAI Grok (dual-model routing)                                        | `grok-4-1-fast-non-reasoning` (extraction) + `grok-4.20-reasoning` (query / inference) |
| **Embeddings**        | OpenAI `text-embedding-3-large`                                      | 3072-dim vectors (must use OpenAI endpoint, not xAI)                                   |
| **Graph Storage**     | Neo4j 5.25 Community (preferred) / NetworkX fallback                 | Per-workspace isolation, Cypher + APOC                                                 |
| **Structured Output** | [Instructor](https://github.com/jxnl/instructor) + Pydantic          | Schema-enforced LLM responses with retry                                               |
| **Frontend**          | Alpine.js + Tailwind (Play CDN) + Cytoscape, zero-build              | Capture Workbench UI served from `src/ui/static/`                                      |

**Why generic RAG fails for federal capture work:**

Vanilla LightRAG can't tell a CLIN from a generic line item, doesn't recognize the Section L ↔ M golden thread, can't trace deliverables back to requirements and evaluation factors, and gives no Shipley-style strategic framing on top of retrieved evidence.

**Our solution**: a curated **33-entity / 35-relationship-type** ontology, **3 inference algorithms** that enrich the graph after extraction, and a **Shipley-mentor query persona** that turns hybrid retrieval into capture-ready answers.

---

## Quick Start

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** for dependency management
- **Docker** (for Neo4j) or NetworkX (local fallback)
- **GPU**: NVIDIA RTX 4060+ recommended (for MinerU acceleration)

### Installation

```powershell
# 1. Clone and setup
git clone https://github.com/BdM-15/proj-theseus.git
cd proj-theseus

# 2. Install dependencies (raganything, lightrag-hku, xai-sdk, instructor, mineru[core])
uv sync

# 3. Configure environment
copy .env.example .env
# Edit .env with your API keys:
#   LLM_BINDING_API_KEY=xai-your-key
#   EMBEDDING_BINDING_API_KEY=sk-proj-your-openai-key

# 4. Activate virtual environment
.venv\Scripts\Activate.ps1

# 5. Start the server (auto-starts Neo4j Docker if available)
python app.py
```

> **GPU note (Windows):** `uv sync` may downgrade PyTorch to a CPU-only wheel, which silently disables MinerU GPU acceleration. Reinstall the CUDA build manually if MinerU drops to CPU (see comments in `pyproject.toml`).

### Usage

1. **Capture Workbench UI** (primary): http://localhost:9621/ui — Capture Chat, Intel Panels, KG viewer, document drawer.
2. **LightRAG WebUI** (built-in fallback): http://localhost:9621/webui — raw LightRAG document manager + chat.
3. **Upload an RFP**: drop a PDF / DOCX / XLSX into `inputs/uploaded/`, then click **Scan inputs** in the workbench (or POST to `/scan-rfp`). MinerU + extraction + post-processing run automatically and the graph appears in the active workspace.
4. **Query**: ask the workbench in plain English ("Walk me through how Section L.3.4 maps to Section M.2") and Theseus answers as a Shipley capture mentor with cited evidence.

---

## Processing Pipeline

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    8-Step Capture Pipeline                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. DOCUMENT INGEST                                                      │
│     └─ inputs/uploaded/ → /scan-rfp → inputs/__enqueued__/               │
│                                                                          │
│  2. MINERU PARSING (via RAG-Anything, GPU-accelerated)                   │
│     └─ text + tables + images + equations + page-aware context           │
│                                                                          │
│  3. MULTIMODAL ANALYSIS (VLM, govcon-aware prompts)                      │
│     └─ Tables/images/equations described with the same 33-entity         │
│        vocabulary the text extractor uses                                │
│                                                                          │
│  4. CHUNKING                                                             │
│     └─ Configurable via CHUNK_SIZE (default 4,096 tokens, ~15% overlap)  │
│                                                                          │
│  5. ENTITY EXTRACTION (xAI Grok + Instructor + Pydantic)                 │
│     └─ 33 government contracting entity types, schema-validated          │
│                                                                          │
│  6. RELATIONSHIP EXTRACTION                                              │
│     └─ 35 canonical relationship types from the same prompt pass         │
│                                                                          │
│  7. SEMANTIC POST-PROCESSING (auto-triggered after batch completes)      │
│     ├─ Phase 1  Data load (entities, relationships, chunks)              │
│     ├─ Phase 2  Entity normalization                                     │
│     ├─ Phase 3  Relationship retyping (entity-pair aware)                │
│     ├─ Phase 4  Inference algorithms (L↔M, doc structure, orphans)       │
│     ├─ Phase 5  Workload enrichment (BOE category tagging, optional)     │
│     └─ Phase 6  VDB synchronization                                      │
│                                                                          │
│  8. QUERY (Shipley mentor persona)                                       │
│     └─ Hybrid retrieval → answer with discriminators, hot buttons,       │
│        FAB chains, compliance citations                                  │
│                                                                          │
│  OUTPUT: Per-workspace KG (Neo4j or NetworkX) + Capture Workbench UI     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### The Three Prompt Systems

Theseus runs three independently-registered prompt systems that share a single ontology vocabulary. **All three must stay aligned** — see [.github/copilot-instructions.md](.github/copilot-instructions.md) for the cross-cutting change checklist.

| System                         | Purpose                                           | Source                                                                                   |
| ------------------------------ | ------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **1. LightRAG Extraction**     | Entity/relationship extraction from text chunks   | `prompts/extraction/govcon_lightrag_native.txt` → `prompts/govcon_prompt.py`             |
| **2. LightRAG Query/Response** | Shipley-mentor RAG answering + keyword extraction | `prompts/govcon_prompt.py` (`rag_response`, `naive_rag_response`, `keywords_extraction`) |
| **3. RAGAnything Multimodal**  | Table / image / equation VLM analysis             | `prompts/multimodal/govcon_multimodal_prompts.py`                                        |

Algorithm-specific inference prompts live under `prompts/relationship_inference/` and are loaded by modules in `src/inference/`.

---

## Government Contracting Ontology

### 33 Entity Types

The ontology is organized into four functional groups for maximum extraction precision:

**Contract, Execution & Commercial Structure**

| Entity Type                 | Description                                       | Example                                 |
| --------------------------- | ------------------------------------------------- | --------------------------------------- |
| `requirement`               | Contractor obligations (shall/should/may)         | "Contractor shall provide 24/7 support" |
| `contract_line_item`        | CLINs, SLINs, and priced line items               | "CLIN 0001 Base Year Operations FFP"    |
| `pricing_element`           | Rates, fees, escalation, pricing methodology      | "Award Fee Pool 7%"                     |
| `government_furnished_item` | GFE/GFP/GFI/GOTS assets                           | "Government Furnished Vehicle Fleet"    |
| `deliverable`               | CDRLs and contract deliverables                   | "CDRL A001 Monthly Status Report"       |
| `workload_metric`           | Quantitative BOE drivers (volumes, counts)        | "12,500 sorties/year"                   |
| `labor_category`            | Named labor classifications and workforce roles   | "Systems Engineer Level III"            |
| `performance_standard`      | KPIs, SLAs, AQLs, QASP inspection standards       | "99.9% system uptime"                   |
| `transition_activity`       | Phase-in, phase-out, turnover, mobilization tasks | "30-Day Transition Plan"                |

**Document Structure, Authorities & Work Patterns**

| Entity Type               | Description                                         | Example                                 |
| ------------------------- | --------------------------------------------------- | --------------------------------------- |
| `document_section`        | Numbered/titled hierarchical structural units       | "Section C Statement of Work"           |
| `document`                | RFP attachments, exhibits, annexes, standalone docs | "Attachment J-3 Quality Assurance Plan" |
| `amendment`               | Solicitation modifications and Q&A amendments       | "Amendment 0003"                        |
| `clause`                  | FAR/DFARS/Agency acquisition clauses (26+ agencies) | "FAR 52.212-4"                          |
| `regulatory_reference`    | IAW citations: DAFI, AR, MIL-STD, NIST SP, AFI      | "NIST SP 800-171"                       |
| `technical_specification` | ICDs, TDPs, MIL-DTL/MIL-PRF, engineering standards  | "MIL-DTL-38999"                         |
| `work_scope_item`         | PWS/SOW/SOO tasks, objectives, work elements        | "Task 3.2 Network Operations Support"   |

**Proposal & Evaluation Structure**

| Entity Type                  | Description                                          | Example                                 |
| ---------------------------- | ---------------------------------------------------- | --------------------------------------- |
| `evaluation_factor`          | Top-level Section M scoring criteria with weights    | "Technical Approach (40%)"              |
| `subfactor`                  | Evaluation subfactor hierarchy (children of factors) | "Subfactor 1.2 Staffing Approach (15%)" |
| `proposal_instruction`       | Proposal format, page limits, volume requirements    | "Technical Volume limited to 25 pages"  |
| `proposal_volume`            | Named proposal containers/response volumes           | "Volume I Technical"                    |
| `past_performance_reference` | Reference contracts, PPQs, CPARS records             | "Contract W912-1234 CPARS Exceptional"  |

**Strategic & Analytical Signals**

| Entity Type         | Description                                                  | Example                      |
| ------------------- | ------------------------------------------------------------ | ---------------------------- |
| `strategic_theme`   | Win themes, discriminators, proof points                     | "Mission Readiness Priority" |
| `customer_priority` | Explicit importance/weighting signals from the customer      | "Cybersecurity Is Paramount" |
| `pain_point`        | Problem statements, deficiencies the government wants solved | "Current Turnaround Delays"  |

**Standard Entities**

| Entity Type           | Description                                 | Example                       |
| --------------------- | ------------------------------------------- | ----------------------------- |
| `organization`        | Agencies, military units, contractors       | "Naval Air Systems Command"   |
| `program`             | Government programs and initiatives         | "MCPP II"                     |
| `equipment`           | Physical hardware, vehicles, machinery      | "M1A1 Tank"                   |
| `technology`          | Software, systems, platforms                | "AWS GovCloud"                |
| `location`            | Performance locations, facilities, bases    | "Joint Base Andrews"          |
| `event`               | Milestones, deadlines, scheduled activities | "Contract Award Q2 FY25"      |
| `person`              | Key personnel, POCs, named roles            | "Contracting Officer"         |
| `compliance_artifact` | Certifications, ATOs, accreditations        | "ISO 9001:2015 Certification" |
| `concept`             | Residual abstract ideas and processes       | "CONUS operations"            |

### 35 Relationship Types

Defined in `src/ontology/schema.py` → `VALID_RELATIONSHIP_TYPES`, organized by functional group:

- **Structural** — `CHILD_OF`, `ATTACHMENT_OF`, `CONTAINS`, `AMENDS`, `SUPERSEDED_BY`, `REFERENCES`
- **Evaluation & Proposal (Section L ↔ M golden thread)** — `GUIDES`, `EVALUATED_BY`, `HAS_SUBFACTOR`, `MEASURED_BY`, `EVIDENCES`
- **Work & Deliverables (traceability chain)** — `PRODUCES`, `SATISFIED_BY`, `TRACKED_BY`, `SUBMITTED_TO`, `STAFFED_BY`, `PRICED_UNDER`, `FUNDS`, `QUANTIFIES`
- **Authority & Governance** — `GOVERNED_BY`, `MANDATES`, `CONSTRAINED_BY`, `DEFINES`, `APPLIES_TO`
- **Resource & Operational** — `HAS_EQUIPMENT`, `PROVIDED_BY`, `COORDINATED_WITH`, `REPORTED_TO`
- **Strategic & Capture Intelligence** — `ADDRESSES`, `RESOLVES`, `SUPPORTS`, `RELATED_TO`
- **Inference-only** (added by post-processing) — `REQUIRES`, `ENABLED_BY`, `RESPONSIBLE_FOR`

### Inference Algorithms

Post-processing runs after every batch completes. The current production algorithms live in `src/inference/algorithms/`:

| Module                        | Purpose                                                           | Edges produced                                            |
| ----------------------------- | ----------------------------------------------------------------- | --------------------------------------------------------- |
| `infer_lm_links.py`           | Section L ↔ M mapping (instruction ↔ evaluation factor)           | `GUIDES`, `EVALUATED_BY`                                  |
| `infer_document_structure.py` | Document hierarchy (DOCUMENT → SECTION → SUBSECTION; attachments) | `CHILD_OF`, `ATTACHMENT_OF`, `CONTAINS`                   |
| `resolve_orphans.py`          | Re-link unconnected entities to nearest legitimate parent         | `REQUIRES`, `ENABLED_BY`, `RESPONSIBLE_FOR`, `RELATED_TO` |

Orchestration: `src/inference/semantic_post_processor.py` (6-phase pipeline) and `src/inference/algorithms/orchestrator.py`. Workload enrichment lives alongside as an opt-in pass.

---

## Project Structure

```
proj-theseus/
├── app.py                        # Entry point (Neo4j Docker management, server bootstrap)
├── docker-compose.neo4j.yml      # Neo4j 5.25 + APOC + GDS
├── src/
│   ├── raganything_server.py     # Main server: wires LightRAG, RAG-Anything, UI, routes
│   ├── server/
│   │   ├── config.py             # LightRAG global_args (loads .env first)
│   │   ├── initialization.py     # Registers all 3 prompt systems + RAG-Anything
│   │   ├── routes.py             # Custom endpoints (/scan-rfp, /insert, batch tracker)
│   │   └── ui_routes.py          # Workbench API (Intel Panels, chats, workspace ops)
│   ├── ui/static/                # Capture Workbench UI (Alpine + Tailwind, zero-build)
│   │   ├── index.html            # `theseus()` Alpine component + tailwind config
│   │   └── styles/theseus.css    # Token system (:root) + components — see STYLE_GUIDE
│   ├── extraction/               # Custom entity extraction (Instructor + Pydantic)
│   ├── inference/
│   │   ├── semantic_post_processor.py   # 6-phase post-processing orchestrator
│   │   ├── algorithms/                  # L↔M, doc-structure, orphan resolution
│   │   ├── workload_enrichment.py       # BOE category tagging (opt-in)
│   │   └── vdb_sync.py                  # Vector DB resync after retyping
│   ├── ontology/
│   │   └── schema.py             # 33 entity types + 35 relationship types (canonical)
│   ├── core/                     # Shared config helpers
│   └── utils/                    # Logging, time helpers (America/Chicago)
├── prompts/
│   ├── govcon_prompt.py          # System 2 — query/response (Shipley mentor)
│   ├── extraction/               # System 1 — entity/relationship extraction
│   ├── multimodal/               # System 3 — RAG-Anything VLM prompts
│   └── relationship_inference/   # Per-algorithm inference prompts
├── rag_storage/                  # Per-workspace KG data (KV stores + VDB + mineru/)
├── inputs/uploaded/              # Drop-zone for new RFPs (scan moves to __enqueued__/)
├── docs/                         # Architecture, white papers, style guide, use cases
├── tools/                        # Neo4j ops, ontology validation, workspace cleanup
├── .github/skills/               # Agent Skills (dual-use: Copilot + Theseus runtime)
└── theseus-skills/               # Organizational mirror / pointers (see docs/SKILLS.md)
```

### Agent Skills (Tools → Agent Skills)

Project Theseus ships a **dual-use Agent Skills platform**: the same `SKILL.md` files in `.github/skills/` are read by **GitHub Copilot / VS Code** when the repo is open AND by the in-app **Tools → Agent Skills** page when invoked against an active workspace. Built-in skills:

- `huashu-design` — Vendored HTML→PPTX/PDF/MP4 design engine (Personal Use License); pair with `proposal-generator` content for govcon visuals
- `govcon-ontology` — Authoritative reference for the 33 entity / 35 relationship schema
- `proposal-generator` — Shipley capture mentor: compliance spine → win themes → FAB → govcon HTML render templates
- `compliance-auditor` — 8-check audit (clauses, regs, L↔M, cyber, amendments, …)
- `competitive-intel` — Roadmap placeholder (SAM.gov / USAspending integration TODO)

See [docs/SKILLS.md](docs/SKILLS.md) for the full platform docs and authoring guide.

---

## Configuration

### Environment Variables (.env)

```bash
# ============================================================================
# LLM Configuration (xAI Grok - OpenAI-compatible API)
# ============================================================================
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4.20-0309-reasoning
LLM_BINDING_API_KEY=xai-your-key-here
LLM_MODEL_TEMPERATURE=0.1

# ============================================================================
# Embedding Configuration (OpenAI - CRITICAL: Use OpenAI endpoint, NOT xAI!)
# ============================================================================
EMBEDDING_BINDING=openai
EMBEDDING_BINDING_HOST=https://api.openai.com/v1
EMBEDDING_MODEL=text-embedding-3-large
EMBEDDING_BINDING_API_KEY=sk-proj-your-openai-key
EMBEDDING_DIM=3072

# ============================================================================
# Graph Storage (Neo4j recommended, NetworkX fallback)
# ============================================================================
GRAPH_STORAGE=Neo4JStorage          # Or: NetworkXStorage
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# ============================================================================
# Processing Configuration
# ============================================================================
CHUNK_SIZE=4096                     # Tokens per chunk
CHUNK_OVERLAP_SIZE=600              # 15% overlap
MAX_ASYNC=16                        # LLM extraction concurrency (matches ARCHITECTURE.md)
EMBEDDING_FUNC_MAX_ASYNC=16         # Embedding API concurrency
```

### Neo4j Setup (Recommended)

```powershell
# Start Neo4j with Docker (auto-managed by app.py)
docker-compose -f docker-compose.neo4j.yml up -d

# Or manually:
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your-password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.25-community
```

---

## API Endpoints

### Document Processing & Query

| Endpoint            | Method | Description                                                                      |
| ------------------- | ------ | -------------------------------------------------------------------------------- |
| `/scan-rfp`         | POST   | Scan `inputs/uploaded/` and enqueue new files into the active workspace pipeline |
| `/documents/upload` | POST   | Direct upload (LightRAG-native; triggers full multimodal + post-processing run)  |
| `/insert`           | POST   | Alternative insert path with explicit workspace selection                        |
| `/query`            | POST   | Hybrid query against the active workspace (Shipley mentor persona)               |
| `/query/data`       | POST   | Structured retrieval (entities, relationships, chunks) for downstream agents     |
| `/health`           | GET    | Server health check                                                              |

### Workbench / Intel Panel APIs

Served under `/api/ui/` by `src/server/ui_routes.py` — feeds the Capture Workbench front-end (workspace stats, panel rows, saved chats, exports). See open issues [#87–#114](https://github.com/BdM-15/proj-theseus/issues) for the in-flight Tier 2 / Tier 3 panel work.

### UI Surfaces

- **Capture Workbench** (primary): http://localhost:9621/ui — Capture Chat with Shipley mentor, Intel Panels (L↔M, requirements, deliverables, past performance, etc.), KG viewer, document drawer
- **LightRAG WebUI** (fallback): http://localhost:9621/webui — vanilla LightRAG document manager + KG visualization

---

## Performance Metrics

### Processing Speed

| RFP Size             | Processing Time | Cost   | Entities Extracted |
| -------------------- | --------------- | ------ | ------------------ |
| 71 pages (Navy MBOS) | 15-20 minutes   | ~$1.00 | 594 entities       |
| 425 pages (MCPP II)  | 38 minutes      | $2.12  | 1,500+ entities    |
| 500+ pages           | 45-60 minutes   | ~$3.00 | 2,500+ entities    |

### Cost Breakdown (per RFP)

| Phase                          | Tokens       | Cost        |
| ------------------------------ | ------------ | ----------- |
| Extraction (~32 chunks)        | ~5.5M input  | $1.10       |
| Extraction output              | ~500K output | $0.25       |
| Post-processing (8 algorithms) | ~1M total    | $0.50       |
| Query overhead                 | ~200K        | $0.10       |
| **Total**                      | ~5M tokens   | **~$2/RFP** |

---

## Roadmap & Open Issues

The full backlog is tracked in [GitHub Issues #87 – #114](https://github.com/BdM-15/proj-theseus/issues). High-level groupings:

| Group                          | Examples                                                                                                                                                                                                                                               |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Tier 1 — graph quality**     | #88 confidence + provenance on edges, #93 orphan candidate links                                                                                                                                                                                       |
| **Tier 2 — Intel Panels**      | #87 Past Performance, #99 Tech Inventory, #100 Innovation Signals, #96 Glossary, #97 Hot Buttons, #101 Deliverable Catalog                                                                                                                             |
| **Tier 3 — quality of life**   | #109 "Ask Theseus" pre-filled chat buttons, #103 CSV/XLSX export, #110 diff vs prior run                                                                                                                                                               |
| **UI / UX polish**             | #98 documents drawer, #92 KG presets, #91 search explorer, #94 .env knobs, #95 no-active-ws state, #90 chat latency, #89 bypass UX                                                                                                                     |
| **Future panels & dashboards** | #108 activity feed, #113 health card, #102 notification center, #111 full Compliance Matrix, #106 Requirements Browser, #105 Win-Strategy view, #107 Risk Register, #112 Doc Structure tree, #104 section deep-dive drawer, #114 saved chats + pinning |

Three silent-failure surfaces have already been plugged on `main`: extraction-time exceptions (#115), local-timezone timestamps (#116), and tabular-only document invisibility in `doc_status` (#117).

---

## Development

### Running Tests

```powershell
# Activate environment first
.venv\Scripts\Activate.ps1

# Run test suite
python -m pytest tests/

# Specific test
python -m pytest tests/test_json_extraction.py -v
```

### Key Dependencies

```toml
# From pyproject.toml
dependencies = [
    "raganything[all]>=1.2.10",     # RAG-Anything + MinerU 3.0
    "lightrag-hku>=1.4.13",         # LightRAG with WebUI
    "openai>=2.0.0,<3.0.0",         # OpenAI-compatible API client
    "xai-sdk>=1.5.0",               # xAI Grok client
    "instructor>=1.15.0",           # Pydantic LLM validation
    "neo4j>=5.0.0",                 # Graph database
]
```

---

## Hardware Requirements

### Minimum

- **CPU**: Intel i7/AMD Ryzen 7 (8+ cores)
- **RAM**: 32GB
- **GPU**: RTX 3060 (12GB VRAM) for MinerU
- **Storage**: 100GB+ SSD

### Recommended (Development Setup)

- **CPU**: Intel i9-14900HX (24 cores)
- **RAM**: 64GB DDR5
- **GPU**: RTX 4060 (8GB VRAM)
- **Storage**: 1TB NVMe SSD

---

## Documentation

| Document                                                                                                                               | Description                                            |
| -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)                                                                                           | System architecture, ADRs, performance metrics         |
| [docs/STYLE_GUIDE.md](docs/STYLE_GUIDE.md)                                                                                             | Capture Workbench UI conventions (read before UI work) |
| [docs/PROJECT_THESEUS_USE_CASE.md](docs/PROJECT_THESEUS_USE_CASE.md)                                                                   | End-to-end capture-team use case                       |
| [docs/ENHANCEMENT_FRAMEWORK.md](docs/ENHANCEMENT_FRAMEWORK.md)                                                                         | Upstream library enhancement mapping                   |
| [docs/MINERU_3X_INTEGRATION_ASSESSMENT.md](docs/MINERU_3X_INTEGRATION_ASSESSMENT.md)                                                   | MinerU 3.0 upgrade notes                               |
| [docs/Ontology-Based-RAG-for-Government-Contracting-White-Paper.md](docs/Ontology-Based-RAG-for-Government-Contracting-White-Paper.md) | Technical white paper                                  |
| [docs/Why-General-Purpose-AI-Fails-Specialized-Domains.md](docs/Why-General-Purpose-AI-Fails-Specialized-Domains.md)                   | Domain-specialization argument                         |
| [.github/copilot-instructions.md](.github/copilot-instructions.md)                                                                     | Agent rules + cross-cutting prompt change checklist    |

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

See [GitHub Issues](https://github.com/BdM-15/proj-theseus/issues) for current priorities.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **[LightRAG](https://github.com/HKUDS/LightRAG)** - Knowledge graph foundation
- **[RAG-Anything](https://github.com/HKUDS/RAG-Anything)** - Multimodal processing
- **[MinerU](https://github.com/opendatalab/MinerU)** - PDF parsing
- **[xAI](https://x.ai/)** - Grok LLM API
- **[Shipley Associates](https://shipley.com/)** - Government contracting methodology

---

**Last Updated**: April 2026  
**Version**: 1.1.0  
**Status**: Production capture workbench — Neo4j storage, multimodal ingest, Shipley-mentor querying  
**Processing cost**: ~$2 per ~425-page RFP (xAI Grok + OpenAI embeddings)
