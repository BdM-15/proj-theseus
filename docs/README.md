# GovCon-Capture-Vibe Documentation

**Ontology-based RAG system for federal RFP analysis**

**Last Updated**: April 2026

---

## Quick Start

- **New to the project?** → [ARCHITECTURE.md](ARCHITECTURE.md)
- **Academic foundation?** → [White Paper](Ontology-Based-RAG-for-Government-Contracting-White-Paper.md)
- **Development guidelines?** → [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)

---

## Documentation Index

| Document                                                                            | Description                                                                       |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| [ARCHITECTURE.md](ARCHITECTURE.md)                                                  | System architecture, ADRs, ontology design, performance metrics                   |
| [ENHANCEMENT_FRAMEWORK.md](ENHANCEMENT_FRAMEWORK.md)                                | Upstream library enhancement mapping (LightRAG, RAG-Anything, MinerU, Instructor) |
| [MINERU_3X_INTEGRATION_ASSESSMENT.md](MINERU_3X_INTEGRATION_ASSESSMENT.md)          | MinerU 3.0 upgrade assessment and integration notes                               |
| [PROJECT_THESEUS_USE_CASE.md](PROJECT_THESEUS_USE_CASE.md)                          | Project Theseus use case and value proposition                                    |
| [STYLE_GUIDE.md](STYLE_GUIDE.md)                                                    | UI styling rules: token system, `@apply` CDN constraint, component patterns       |
| [White Paper](Ontology-Based-RAG-for-Government-Contracting-White-Paper.md)         | Academic foundation for ontology-based RAG in govcon                              |
| [Why General-Purpose AI Fails](Why-General-Purpose-AI-Fails-Specialized-Domains.md) | Domain specialization thesis                                                      |

---

## Current System

**Stack**:

- LightRAG 1.4.13 (`lightrag-hku`) — Knowledge graph + WebUI
- RAG-Anything 1.2.10 — Multimodal document processing
- MinerU 3.0.9 — PDF/DOCX/XLSX parsing (GPU-accelerated)
- Instructor 1.15.1 — Pydantic-enforced LLM extraction
- xAI Grok-4.1-fast (dual-model: non-reasoning extraction + reasoning queries)
- OpenAI text-embedding-3-large (3072-dim)
- Neo4j 5.25 Community — Primary graph storage with workspace isolation

**Capabilities**:

- 18 entity types (government contracting ontology)
- 8 LLM-powered semantic post-processing algorithms
- UCF structure detection (Section A-M, J attachments)
- Section L↔M mapping (evaluation instructions)
- FAR/DFARS clause clustering (26+ agency supplements)
- Requirement→Evaluation factor linking
- Workload enrichment with BOE category tagging
- Multimodal: tables, images, text (PDF, DOCX, XLSX)

**Performance** (validated April 2026, 3-document batch):

- 1,447 entities, 3,533 relationships (2,322 extracted + 683 inferred + 528 belongs_to)
- 345/345 requirements enriched (100% workload coverage)
- ~$2/RFP with xAI Grok + OpenAI embeddings

---

## External Resources

- **LightRAG**: https://github.com/HKUDS/LightRAG
- **RAG-Anything**: https://github.com/HKUDS/RAG-Anything
- **MinerU**: https://github.com/opendatalab/MinerU
- **xAI Grok**: https://docs.x.ai
- **Instructor**: https://github.com/jxnl/instructor

---

**Maintainer**: See `.github/copilot-instructions.md`
