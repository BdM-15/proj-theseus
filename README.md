# GovCon Capture Vibe: Ontology-Based RAG for Government Contract Analysis

**Project Theseus - Government Contracting Intelligence Platform**

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/BdM-15/govcon-capture-vibe)
[![Python](https://img.shields.io/badge/python-3.13+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

## Executive Summary

An **Ontology-Based RAG system** for federal RFP analysis that transforms generic document processing into specialized government contracting intelligence. Uses **RAG-Anything** (multimodal ingestion) + **LightRAG** (knowledge graph/queries) with **xAI Grok** cloud processing for **~12x speedup** over local processing.

### Core Innovation

**Government Contracting Ontology + LLM-Powered Relationship Inference** enables:

- **Section L↔M mapping** (submission instructions → evaluation factors)
- **Requirement traceability** across RFP sections
- **Shipley methodology compliance** classification
- **Annex/attachment linkage** to parent documents

### Architecture Stack

| Component             | Technology                                                       | Purpose                                               |
| --------------------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| **Document Parsing**  | [MinerU](https://github.com/opendatalab/MinerU) via RAG-Anything | Multimodal PDF extraction (tables, images, equations) |
| **RAG Orchestration** | [RAG-Anything](https://github.com/HKUDS/RAG-Anything) v1.2.8+    | Document processing pipeline coordination             |
| **Knowledge Graph**   | [LightRAG](https://github.com/HKUDS/LightRAG) v1.4.9.7+          | Graph construction with WebUI (pip: `lightrag-hku`)   |
| **LLM**               | xAI Grok-4-fast-reasoning                                        | Entity extraction, relationship inference (~$4/RFP)   |
| **Embeddings**        | OpenAI text-embedding-3-large                                    | 3072-dimensional vector similarity                    |
| **Graph Storage**     | Neo4j 5.25 Community / NetworkX                                  | Enterprise graph with APOC or local fallback          |
| **Structured Output** | [Instructor](https://github.com/jxnl/instructor) + Pydantic      | Schema-enforced LLM responses                         |

**Why Generic RAG Fails for Government Contracting:**

Generic LightRAG cannot understand government contracting concepts - it can't distinguish CLINs from generic line items, won't recognize Section L↔M evaluation relationships, and doesn't know "shall" vs "should" requirement classifications.

**Our Solution**: 18 specialized entity types + 8 LLM inference algorithms for relationship enrichment.

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
git clone https://github.com/BdM-15/govcon-capture-vibe.git
cd govcon-capture-vibe

# 2. Install dependencies (includes raganything, lightrag-hku, xai-sdk)
uv sync

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys:
#   LLM_BINDING_API_KEY=xai-your-key
#   EMBEDDING_BINDING_API_KEY=sk-proj-your-openai-key

# 4. Activate virtual environment
.venv\Scripts\Activate.ps1

# 5. Start the server (auto-starts Neo4j Docker if available)
python app.py
```

### Usage

1. **Access WebUI**: http://localhost:9621/webui
2. **Upload RFP PDF**: Drag & drop or use upload button
3. **Automatic Processing**: 6-step pipeline runs automatically
4. **Query Knowledge Graph**: Use chat interface or API

---

## Processing Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                    6-Step Processing Pipeline                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. DOCUMENT UPLOAD                                                 │
│     └── PDF/DOCX → /documents/upload endpoint                       │
│                                                                     │
│  2. MINERU PARSING (via RAG-Anything)                              │
│     └── Tables, images, text extraction with structure preservation │
│                                                                     │
│  3. LIGHTRAG CHUNKING                                              │
│     └── 8,192 tokens/chunk with 1,200 token overlap (15%)          │
│                                                                     │
│  4. ENTITY EXTRACTION (xAI Grok + Instructor)                      │
│     └── 18 government contracting entity types                      │
│     └── Pydantic schema validation                                  │
│                                                                     │
│  5. RELATIONSHIP EXTRACTION                                         │
│     └── LightRAG native relationship inference                      │
│                                                                     │
│  6. SEMANTIC POST-PROCESSING                                        │
│     └── 8 LLM-powered relationship inference algorithms             │
│     └── Section L↔M mapping, requirement traceability              │
│                                                                     │
│  OUTPUT: Neo4j Knowledge Graph + LightRAG WebUI                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Government Contracting Ontology

### 18 Entity Types

| Entity Type              | Description                                  | Example                                 |
| ------------------------ | -------------------------------------------- | --------------------------------------- |
| `requirement`            | Contractual obligations (shall/should/may)   | "Contractor shall provide 24/7 support" |
| `clause`                 | FAR/DFARS regulatory references              | "FAR 52.212-4"                          |
| `section`                | RFP structural elements (A-M, J attachments) | "Section L.3.2"                         |
| `document`               | Referenced documents and standards           | "MIL-STD-882E"                          |
| `deliverable`            | CDRLs and contract deliverables              | "Monthly Status Report"                 |
| `program`                | Government program names                     | "AFCAPV ADAB ISS"                       |
| `equipment`              | GFE/CFE items                                | "Government-furnished vehicles"         |
| `evaluation_factor`      | Section M scoring criteria                   | "Technical Approach (40%)"              |
| `submission_instruction` | Section L requirements                       | "Volume I: 50 pages max"                |
| `strategic_theme`        | Win themes and hot buttons                   | "Mission-critical reliability"          |
| `statement_of_work`      | SOW/PWS task descriptions                    | "Task 3.2 Network Operations"           |
| `performance_metric`     | KPIs and QASP standards                      | "99.9% uptime SLA"                      |
| `concept`                | Domain terminology                           | "CONUS operations"                      |
| `organization`           | Agencies and contractors                     | "Naval Air Systems Command"             |
| `location`               | Performance locations                        | "Joint Base Andrews"                    |
| `event`                  | Milestone events                             | "Contract award: Q2 FY25"               |
| `technology`             | Technical systems                            | "AWS GovCloud"                          |

### 8 Semantic Post-Processing Algorithms

| Algorithm                         | Purpose                      | Relationships Created    |
| --------------------------------- | ---------------------------- | ------------------------ |
| 1. Instruction-Evaluation Linking | Section L → M mapping        | `GUIDES`, `EVALUATED_BY` |
| 2. Evaluation Hierarchy           | Factor → subfactor structure | `PARENT_OF`, `CHILD_OF`  |
| 3. Requirement-Evaluation Mapping | Requirements → factors       | `EVALUATED_BY`           |
| 4. Deliverable Traceability       | CDRLs → requirements         | `PRODUCES`, `REFERENCES` |
| 5. Document Hierarchy             | Section structure            | `PARENT_OF`, `CHILD_OF`  |
| 6. Semantic Concept Linking       | Topic-based connections      | `RELATED_TO`             |
| 7. Heuristic Pattern Matching     | CDRL cross-references        | `REFERENCES`             |
| 8. Orphan Pattern Resolution      | Unlinked entity cleanup      | Various                  |

---

## Project Structure

```
govcon-capture-vibe/
├── app.py                      # Entry point (Neo4j Docker management, startup)
├── src/
│   ├── raganything_server.py   # Main server (RAG-Anything + LightRAG WebUI)
│   ├── server/
│   │   ├── config.py           # 18 entity types, LightRAG global_args
│   │   └── routes.py           # Custom /insert, /documents/upload endpoints
│   ├── extraction/
│   │   └── json_extractor.py   # Pydantic schema extraction with Instructor
│   ├── inference/
│   │   ├── semantic_post_processor.py  # 8 relationship algorithms
│   │   └── workload_enrichment.py      # BOE category tagging
│   ├── ontology/
│   │   └── schema.py           # Pydantic models for all entity types
│   ├── processors/             # Document processing utilities
│   ├── core/                   # Shared utilities
│   └── utils/                  # Logging, helpers
├── prompts/
│   ├── extraction/             # Entity extraction prompts (~170K tokens)
│   └── relationship_inference/ # Post-processing prompts
├── rag_storage/                # Per-workspace knowledge graphs
├── inputs/                     # RFP document uploads
├── docs/                       # Architecture, Neo4j guides, roadmaps
├── tests/                      # Test suite
└── tools/                      # Diagnostics, validation scripts
```

---

## Configuration

### Environment Variables (.env)

```bash
# ============================================================================
# LLM Configuration (xAI Grok - OpenAI-compatible API)
# ============================================================================
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.x.ai/v1
LLM_MODEL=grok-4-fast-reasoning
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
CHUNK_SIZE=8192                     # Tokens per chunk
CHUNK_OVERLAP=1200                  # 15% overlap
MAX_ASYNC=32                        # Parallel processing
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

### Document Processing

| Endpoint            | Method | Description                                 |
| ------------------- | ------ | ------------------------------------------- |
| `/documents/upload` | POST   | Upload RFP (triggers full pipeline)         |
| `/insert`           | POST   | Alternative upload with workspace selection |
| `/query`            | POST   | Query knowledge graph                       |
| `/health`           | GET    | Server health check                         |

### LightRAG WebUI (Built-in)

- **Document Manager**: http://localhost:9621/webui
- **Knowledge Graph Viewer**: Interactive graph visualization
- **Chat Interface**: Natural language queries with citations

---

## Performance Metrics

### Processing Speed

| RFP Size              | Processing Time | Cost   | Entities Extracted |
| --------------------- | --------------- | ------ | ------------------ |
| 71 pages (Navy MBOS)  | 30-40 minutes   | ~$4.00 | 594 entities       |
| 425 pages (Large RFP) | 45-60 minutes   | ~$4.00 | 2,500+ entities    |
| 500+ pages            | 60-90 minutes   | ~$6.00 | 3,500+ entities    |

### Cost Breakdown (per RFP)

| Phase                          | Tokens       | Cost        |
| ------------------------------ | ------------ | ----------- |
| Extraction (~32 chunks)        | ~5.5M input  | $1.10       |
| Extraction output              | ~500K output | $0.25       |
| Post-processing (8 algorithms) | ~1M total    | $0.50       |
| Query overhead                 | ~200K        | $0.10       |
| **Total**                      | ~7M tokens   | **~$4/RFP** |

---

## GitHub Issues & Roadmap

### Active Optimization Issues

| Issue                                                                                           | Priority  | Estimated Savings   |
| ----------------------------------------------------------------------------------------------- | --------- | ------------------- |
| [#14: Prompt Compression](https://github.com/BdM-15/govcon-capture-vibe/issues/14)              | HIGH      | 50% token reduction |
| [#15: Remove Redundant Algorithms 1-3](https://github.com/BdM-15/govcon-capture-vibe/issues/15) | HIGH      | ~4 min/RFP          |
| [#16: Integrate Workload Enrichment](https://github.com/BdM-15/govcon-capture-vibe/issues/16)   | MEDIUM    | 60 sec/RFP          |
| [#17: Parallel Chunk Processing](https://github.com/BdM-15/govcon-capture-vibe/issues/17)       | MEDIUM    | 75% time reduction  |
| [#18: Increase Chunk Size to 16K](https://github.com/BdM-15/govcon-capture-vibe/issues/18)      | MEDIUM    | 50% fewer chunks    |
| [#19: Fine-Tuned SLM Strategy](https://github.com/BdM-15/govcon-capture-vibe/issues/19)         | LONG-TERM | 85% cost reduction  |

### Strategic Feature Issues

| Issue                                                                                            | Description                                    |
| ------------------------------------------------------------------------------------------------ | ---------------------------------------------- |
| [#20: Cross-RFP Knowledge Accumulation](https://github.com/BdM-15/govcon-capture-vibe/issues/20) | Pattern recognition across RFPs                |
| [#21: Strategic Intelligence](https://github.com/BdM-15/govcon-capture-vibe/issues/21)           | Competitive analysis, proposal reuse           |
| [#22: Performance Analytics](https://github.com/BdM-15/govcon-capture-vibe/issues/22)            | A/B testing, metrics dashboard                 |
| [#23: Core Capture Intelligence](https://github.com/BdM-15/govcon-capture-vibe/issues/23)        | Proposal outline, compliance matrix generators |

### Quality Issues

| Issue                                                                                                    | Description                           |
| -------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| [#9: Entity Extraction Prompt Enhancement](https://github.com/BdM-15/govcon-capture-vibe/issues/9)       | Performance metrics, strategic themes |
| [#11: Pydantic Enforcement for Post-Processing](https://github.com/BdM-15/govcon-capture-vibe/issues/11) | Schema validation for relationships   |
| [#12: Custom GovCon Query Prompts](https://github.com/BdM-15/govcon-capture-vibe/issues/12)              | Optimized retrieval prompts           |
| [#13: LLM JSON Response Failures](https://github.com/BdM-15/govcon-capture-vibe/issues/13)               | Truncation handling                   |

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
    "raganything[all]>=1.2.8",      # RAG-Anything + MinerU
    "lightrag-hku>=1.4.9.7",        # LightRAG with WebUI
    "xai-sdk>=1.4.0",               # xAI Grok client
    "instructor>=1.13.0",           # Pydantic LLM validation
    "neo4j>=6.0.3",                 # Graph database
    "pydantic>=2.10.6",             # Schema models
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

| Document                                                                         | Description                  |
| -------------------------------------------------------------------------------- | ---------------------------- |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md)                                          | System architecture overview |
| [NEO4J_USER_GUIDE.md](docs/neo4j/NEO4J_USER_GUIDE.md)                            | Neo4j setup and usage        |
| [NEO4J_SETUP_GUIDE.md](docs/neo4j/NEO4J_SETUP_GUIDE.md)                          | Docker configuration         |
| [FEATURE_ROADMAP.md](docs/capture-intelligence/FEATURE_ROADMAP.md)               | Feature development plan     |
| [White Paper](docs/Ontology-Based-RAG-for-Government-Contracting-White-Paper.md) | Technical deep-dive          |

---

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

See [GitHub Issues](https://github.com/BdM-15/govcon-capture-vibe/issues) for current priorities.

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

**Last Updated**: November 2025  
**Version**: 0.3.0  
**Status**: Production-ready with Neo4j enterprise storage  
**Processing**: ~$4/RFP with xAI Grok + OpenAI embeddings
