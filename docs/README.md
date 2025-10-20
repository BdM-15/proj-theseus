# GovCon-Capture-Vibe Documentation

**Ontology-based RAG system for federal RFP analysis**

**Current Branch**: main (Branch 008 merged)  
**Last Updated**: October 20, 2025

---

## 🚀 Quick Start

- **New to the project?** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Academic foundation?** → [White Paper](Ontology-Based-RAG-for-Government-Contracting-White-Paper.md)
- **Development guidelines?** → [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)

---

## 📁 Feature Documentation

### 🤖 [agents/](agents/) - PydanticAI Agents (Branch 009)

Click-button deliverables: compliance checklists, proposal outlines, gap analysis, proposal assessment

- **Status**: Planning phase
- **Implementation**: 6-week roadmap documented

### 🗄️ [postgresql18/](postgresql18/) - PostgreSQL Data Warehouse (Branch 010-011)

Multi-workspace storage with event sourcing for immutable RFP → Amendment → Proposal → Feedback tracking

- **Status**: Planning complete, ready for implementation
- **Timeline**: 8-12 weeks (Branch 010: simple schema, Branch 011: event sourcing)

### 🧬 [ontology/](ontology/) - Domain Model

17 entity types, 6 relationship inference algorithms, government contracting patterns

- **Current**: 594 entities, 250 relationships per RFP
- **Shipley integration**: 4-level compliance, SHALL/SHOULD/MAY criticality

### 📝 [amendments/](amendments/) - Amendment Processing (Future)

RFP amendment tracking with change detection and impact analysis

- **Status**: Roadmap complete, requires Branch 011 event sourcing

### 🎯 [capture-intelligence/](capture-intelligence/) - Shipley Methodology

28 pre-built queries, capture patterns, reference guides (PDFs)

- **Integration**: Built into prompts (no manual execution needed)
- **Resources**: Shipley Capture Guide, Proposal Guide, templates

### ⚡ [performance/](performance/) - Optimization

Reranking, fine-tuning, cloud optimization strategies

- **Current**: 69 seconds/RFP, $0.042 cost, 417x speedup vs. local

### 🐛 [bug-fixes/](bug-fixes/) - Resolved Issues

Historical bug resolutions for troubleshooting reference

### 📦 [archive/](archive/) - Historical Docs

Branch 003-006 implementation records, handoff summaries

---

## 🏗️ Current System (Branch 008)

**Performance**:

- Processing: 69 seconds (Navy MBOS 71 pages)
- Cost: $0.042 per RFP
- Entities: 594 (17 types)
- Relationships: 250 (6 inference algorithms)

**Stack**:

- LightRAG 1.4.9.3 (knowledge graph)
- xAI Grok-4-fast-reasoning (2M context window)
- OpenAI text-embedding-3-large (3072-dim)
- RAG-Anything + MinerU (multimodal parsing)
- Storage: JSON files (single workspace)

**Capabilities**:

- UCF structure detection (Section A-M, J attachments)
- Section L↔M mapping (evaluation instructions)
- FAR/DFARS clause clustering (26+ agency supplements)
- Requirement→Evaluation factor linking
- 28 pre-built Shipley queries

---

## 🗺️ Roadmap

### ✅ Completed (Branches 003-008)

- Cloud LLM processing (417x speedup)
- 17 entity types + 6 relationship inference algorithms
- UCF structure detection
- Phase 6 LLM-powered relationship inference
- Shipley methodology integration

### 🚧 In Progress

- PostgreSQL 18 schema design (Branch 010)
- Event sourcing architecture (Branch 011)
- PydanticAI agent planning (Branch 009)

### 📋 Planned

- Branch 009: Click-button agents (6 weeks)
- Branch 010: PostgreSQL migration (5 weeks)
- Branch 011: Event sourcing + amendment tracking (7 weeks)
- Future: Fine-tuning, reranking, cross-RFP intelligence

---

## 📖 Learning Paths

### For Developers

1. [ARCHITECTURE.md](ARCHITECTURE.md) - System overview
2. [ontology/](ontology/) - Entity types and relationships
3. `.github/copilot-instructions.md` - Development guidelines
4. [postgresql18/](postgresql18/) - Database design

### For Capture Managers

1. [White Paper](Ontology-Based-RAG-for-Government-Contracting-White-Paper.md) - Academic foundation
2. [capture-intelligence/](capture-intelligence/) - Shipley methodology
3. [agents/](agents/) - Future click-button capabilities

### For Database Administrators

1. [postgresql18/01_SCHEMA_DESIGN.md](postgresql18/01_SCHEMA_DESIGN.md) - 17-table schema
2. [postgresql18/02_EVENT_SOURCING_ARCHITECTURE.md](postgresql18/02_EVENT_SOURCING_ARCHITECTURE.md) - Event-based design

---

## 🔗 External Resources

- **LightRAG**: https://github.com/HKUDS/LightRAG
- **RAG-Anything**: https://github.com/HKUDS/RAG-Anything
- **xAI Grok**: https://docs.x.ai
- **Shipley Methodology**: See [capture-intelligence/](capture-intelligence/) folder
- **PostgreSQL 18**: https://www.postgresql.org/docs/18/

---

## 📊 Key Metrics

| Metric                 | Value      | Baseline               |
| ---------------------- | ---------- | ---------------------- |
| Processing Time        | 69 seconds | Navy MBOS (71 pages)   |
| Cost per RFP           | $0.042     | Cloud LLM + embeddings |
| Entities Extracted     | 594        | 17 types               |
| Relationships Inferred | 250        | 6 algorithms           |
| Speedup vs. Local      | 417x       | 8 hours → 69 seconds   |
| ROI                    | 9,264x     | $3,149.66 savings/RFP  |

---

**Last Updated**: October 20, 2025  
**Maintainer**: See `.github/copilot-instructions.md`
