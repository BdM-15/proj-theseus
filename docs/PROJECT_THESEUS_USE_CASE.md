# Project Theseus
## AI-Driven RFP Analysis for Government Contracting

**Internal Use Case — December 2025**

---

## Executive Summary

Project Theseus replaces manual RFP "shred" spreadsheets with an AI-powered knowledge graph that transforms 425-page solicitations into actionable intelligence in **38 minutes** at a cost of **$2.12**—freeing capture teams to focus on solutioning and winning proposals instead of data mining.

| Metric | Value |
|--------|-------|
| Processing Time | 38 minutes (vs. 40-80 hours manual) |
| Cost per RFP | $2.12 LLM + 3 hrs review |
| Annual Savings | $390,900 (98% reduction) |
| ROI Breakeven | 4.5 months |

---

## 1. Target Application

Large federal solicitations (50-500+ pages) across all contract types:
- IDIQ Task Orders (LOGCAP, AFCAP, OASIS, Alliant, SEWP)
- Full & Open Competitions
- 8(a), SDVOSB, HUBZone Set-Asides
- GSA Schedule Task Orders

---

## 2. The Operational Gap

Our current manual "shred" process is **slow, error-prone, and doesn't scale**.

| Problem | Impact |
|---------|--------|
| **40-80 hours** of manual reading per RFP | Burns 2-3 weeks that should be spent solutioning |
| Excel-based requirement tracking | 15-20% of proposals have compliance gaps |
| Deciphering ambiguity in dense RFP language | SMEs waste time on data mining, not strategy |
| Each pursuit starts from zero | No institutional learning across captures |

**The Hidden Cost**: A 5-person capture team spending 2 weeks analyzing a 425-page RFP at $150/hour = **$120,000** in pre-proposal labor. At 20 pursuits/year, that's **$2.4M annually** in RFP analysis alone.

---

## 3. The GovCon Ontology: Why This Isn't "ChatGPT on PDFs"

Generic LLMs analyzing RFPs produce **hallucinated connections and surface-level extraction**. They extract "Person", "Organization", "Location"—entities useless for proposal development. They don't understand that a "shall" statement in Section C.4.2 must trace to a CDRL in Section J, or that Section L instructions predict Section M scoring.

**Without domain guidance, AI hopes for patterns instead of knowing them.**

### 18 Specialized Entity Types

Our ontology teaches the AI to think like a senior capture analyst—extracting the entities that actually matter for winning:

| Entity Type | What It Captures | Why It Matters |
|-------------|------------------|----------------|
| `requirement` | SHALL/SHOULD/MAY with criticality level | Drives compliance matrix, identifies mandatory vs. nice-to-have |
| `evaluation_factor` | Section M factors with weights and subfactors | Shapes proposal structure, identifies what wins points |
| `submission_instruction` | Section L page limits, format rules, volume structure | Prevents compliance failures on "ankle biters" |
| `deliverable` | CDRLs, reports, data items with DID references | Traces requirements to contractual outputs |
| `clause` | FAR/DFARS/AFFARS citations | Identifies regulatory constraints and flowdowns |
| `performance_metric` | KPIs, SLAs, QASP standards | Defines success criteria and measurement |
| `strategic_theme` | Win themes, customer hot buttons, discriminators | Guides messaging and competitive positioning |
| `statement_of_work` | SOW/PWS task descriptions | Maps scope to labor categories |
| `section` | UCF structure (A-M), J attachments, annexes | Preserves document hierarchy |
| `document` | Referenced specs, standards, MIL-STDs | Captures external dependencies |
| `program` | Contract vehicles, initiatives | Links to broader context |
| `organization` | Agencies, offices, contractors | Identifies stakeholders |
| `equipment` | GFE/CFE items | Tracks government-furnished assets |
| `technology` | Systems, platforms, tools | Maps technical requirements |
| `concept` | CLINs, technical terms, acronyms | Captures domain terminology |
| `location` | Performance sites, regions | Identifies geographic scope |
| `event` | Milestones, reviews, deadlines | Tracks schedule drivers |
| `person` | POCs, key personnel roles | Identifies decision-makers |

### How the Ontology Creates Knowledge Graph Connections

The ontology doesn't just label text—it **encodes the semantic relationships** that a human analyst builds mentally after reading an RFP cover-to-cover:

```
Section L Instructions ──────────→ Section M Evaluation Factors
        ↓                                    ↓
Submission Requirements          Scoring Criteria & Weights
        ↓                                    ↓
    Deliverables ←───────────── Requirements (SHALL/SHOULD/MAY)
        ↓                                    ↓
   CDRL Numbers                    Performance Metrics
        ↓                                    ↓
 Data Item Descriptions ←──────── Contract Clauses (FAR/DFARS)
```

**8 Semantic Post-Processing Algorithms** infer relationships that aren't explicitly stated:
1. **Section L↔M Mapping** — Links submission instructions to evaluation factors
2. **Requirement-Deliverable Traceability** — Traces SHALL statements to CDRLs
3. **Clause Clustering** — Groups related FAR/DFARS citations by parent section
4. **Document Hierarchy** — Reconstructs RFP structure from fragmented references
5. **Annex Linkage** — Connects PWS appendices to main body requirements
6. **Workload Enrichment** — Tags requirements with BOE categories (Labor, ODCs, Materials)
7. **Entity Retyping** — Corrects misclassified entities using LLM reasoning
8. **Description Enhancement** — Generates human-readable summaries for complex entities

**Result**: The AI makes the same connections a human analyst would make after 20 years of experience—not because it's guessing, but because we've encoded that expertise into the extraction rules and relationship inference algorithms.

---

## 4. The Solution: AI-Powered RFP Intelligence Platform

Replace manual spreadsheets with an **automated knowledge graph** that delivers actionable intelligence in under 1 hour—so your team can start solutioning immediately, not weeks into the pursuit.

### Automated RFP Decomposition
The AI "shreds" the RFP into a queryable knowledge graph, extracting all requirements (SHALL/SHOULD/MAY), evaluation factors with weights, deliverables (CDRLs), and compliance instructions—tasks that take humans days completed in 38 minutes.

### Section L↔M Alignment
The AI automatically maps submission instructions to evaluation factors, ensuring proposal structure directly addresses scoring criteria. No more missed "ankle biters."

### Requirement Traceability
Every SHALL statement is traced to its source section, related deliverables, and evaluation criteria. Writers receive structured requirements, not raw PDFs.

### Natural Language Queries
Ask *"What are the mandatory cybersecurity requirements and how will they be evaluated?"* and get precise answers with citations—not keyword search results.

---

## 5. Connected Intelligence: One Source of Truth

The knowledge graph isn't just a query tool—it becomes the **single source of truth** that powers multiple specialized agents and personas across the capture lifecycle.

### The Platform Concept

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    │     📄 RFP Knowledge Graph          │
                    │     (Single Source of Truth)        │
                    │                                     │
                    │   • 3,500+ Entities                 │
                    │   • Semantic Relationships          │
                    │   • Cross-Referenced Structure      │
                    │                                     │
                    └──────────────┬──────────────────────┘
                                   │
           ┌───────────┬───────────┼───────────┬───────────┐
           ▼           ▼           ▼           ▼           ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
    │   BOE   │  │   SOW   │  │Compliance│ │ Kick-Off│  │  Trend  │
    │  Agent  │  │  Agent  │  │  Agent   │ │  Agent  │  │ Analysis│
    └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
```

### Specialized Agents Built on the Source of Truth

| Agent | Function | Output |
|-------|----------|--------|
| **BOE Agent** | Extracts workload drivers (population served, operating hours, equipment quantities) to ground basis of estimates in RFP facts | Labor build-up inputs tied to specific requirements |
| **SOW Agent** | Analyzes requirements to delineate subcontractor scope, reducing pricing risk by clearly defining boundaries | Subcontract SOW with traced requirements |
| **Compliance Agent** | Auto-generates compliance matrices cross-referencing Sections L, M, and C | Proposal Compliance Matrix with cell references |
| **Kick-Off Agent** | RFP drops at 4 PM → Ready by 8 AM. Generates kick-off deck with scope, requirements, pain points, and strategic insights | PowerPoint deck for Day 1 kick-off meeting |
| **Trend Analysis** | Analyzes across all agency RFPs to identify hidden patterns, evaluation preferences, and recurring terminology | Agency-specific intelligence briefs |

### Human Personas Served

Each role gets tailored outputs from the same trusted source:

- **Capture Manager** → Strategic themes, evaluation factors, competitive positioning
- **Pricing Analyst** → Workload drivers, CLIN structure, BOE inputs
- **Proposal Writer** → Requirements by section, deliverable descriptions, compliance checklist
- **Contracts Manager** → Clause analysis, terms & conditions, risk flags
- **Technical SME** → Relevant requirements filtered by domain (cyber, logistics, IT)

**The Multiplier Effect**: Build the knowledge graph once, extract value many times. No more "Which spreadsheet has the latest requirements?" The graph is the authoritative source.

---

## 6. Open Architecture: Model Flexibility

The platform is built on an **open, swappable architecture**—not locked to any single vendor.

### Dual-Model LLM Routing

Different tasks require different model characteristics:

| Task Type | Model Used | Why |
|-----------|------------|-----|
| **Entity Extraction** | `grok-4-1-fast-non-reasoning` | Literal format compliance, 98+% extraction rate |
| **Query/Reasoning** | `grok-4.20-0309-reasoning` | Nuanced synthesis, complex inference, lowest hallucination rate |
| **Embeddings** | `text-embedding-3-large` (3072-dim) | High-fidelity semantic similarity |

This dual-model approach reduces extraction hallucination by **66%** (12% → 4%) compared to using reasoning models for extraction.

### Swappable Components

| Layer | Current | Alternatives |
|-------|---------|--------------|
| **LLM Provider** | xAI Grok | OpenAI GPT-4, Anthropic Claude, Azure OpenAI, Local (Ollama) |
| **Embeddings** | OpenAI | Cohere, Voyage AI, Local models |
| **Graph Storage** | Neo4j | NetworkX (lightweight), PostgreSQL + pgvector |
| **Document Parsing** | MinerU | PyMuPDF, Unstructured.io |

The OpenAI-compatible API pattern means **switching providers requires changing one environment variable**, not rewriting code. As better/cheaper models emerge, we can adopt them immediately.

### Output Sanitization

A lightweight regex-based cleaner fixes common LLM malformation patterns during extraction:
- `#|requirement` → `requirement` (delimiter leakage)
- Extra pipes in descriptions causing field count errors
- Malformed entity type prefixes

**Result**: Minimal entity drops from format corruption, minimal processing overhead. Tolerance is 2% error rate.

---

## 7. Targeted Savings

**Goal**: 95% Reduction in RFP Analysis Time + 70% Reduction in Compliance Gaps

**Validated Benchmark** (425-page MCPP II DRFP):
- Processing time: **38 minutes**
- LLM cost: **$2.12**
- Entities extracted: **3,500+** with semantic relationships

### ROI Calculation

```
Annual Volume:                    20 RFPs
Current Cost per RFP:             $20,000 (labor)
Current Annual Spend:             $400,000

With Platform:
  Processing (LLM):               $5/RFP × 20 = $100/year
  Review Labor (3 hrs × $150):    $450 × 20 = $9,000/year
  Annual Platform Cost:           $9,100

ANNUAL SAVINGS:                   $390,900 (98% reduction)
3-YEAR SAVINGS:                   $1,172,700

Development Investment:           ~$150,000 (6-month build)
ROI BREAKEVEN:                    ~4.5 months
```

---

## 8. Strategic Value

**RFP analysis is the bottleneck in every capture.** While competitors burn weeks shredding, our teams start solutioning in under 1 hour.

- **More time for solutioning** → Technical teams focus on winning approaches, not data mining
- **Clarity from ambiguity** → AI resolves cross-references and conflicting requirements instantly
- **Better compliance** → Fewer pink team rewrites, no missed "ankle biters"
- **Aligned win themes** → Proposal structure maps directly to evaluation criteria
- **Institutional memory** → Knowledge compounds across pursuits, agency patterns emerge

### Brainstorming & Idea Generation with Reasoning Models

The knowledge graph doesn't just answer questions—it becomes a **strategic thinking partner**. Once the RFP is loaded, the reasoning model (`grok-4.20-0309-reasoning`) can:

**Win Theme Development**
> *"Based on the evaluation factors and customer pain points in this RFP, suggest 5 discriminating win themes that align with our past performance in logistics operations."*

**Technical Approach Brainstorming**
> *"The RFP emphasizes 24/7 operations with 99.9% uptime SLAs. What technical approaches and redundancy strategies should we consider? How have similar requirements been addressed in our past proposals?"*

**Risk Identification**
> *"Analyze this RFP for high-risk requirements—areas where the scope is ambiguous, performance standards are aggressive, or government-furnished resources may be insufficient."*

**Competitive Positioning**
> *"Given the evaluation weights (Technical 40%, Past Performance 30%, Price 30%), what's our optimal strategy? Where should we invest proposal pages?"*

**Solution Architecture**
> *"The PWS requires integration with 5 legacy government systems. Map these integration points to our technical capabilities and identify gaps we need to address through teaming."*

This transforms the platform from a **data extraction tool** into a **strategic advisor**—grounded in the actual RFP facts, not hallucinated generalities. The reasoning model synthesizes across the entire knowledge graph to generate ideas that a human team might take days to develop through manual analysis and whiteboard sessions.

---

## 9. Technology Stack

### Core Components

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Document Parsing** | MinerU 2.6.4 via RAG-Anything | Multimodal PDF extraction (text, tables, images, equations) |
| **RAG Orchestration** | RAG-Anything + LightRAG | Pipeline coordination, chunking (4K tokens, 15% overlap) |
| **Knowledge Graph** | Neo4j 5.25 Community | Entity/relationship storage with workspace isolation |
| **LLM Processing** | xAI Grok-4.1-fast (dual-model) | Entity extraction + relationship inference |
| **Embeddings** | OpenAI text-embedding-3-large | 3072-dimensional vector similarity search |
| **Validation** | Pydantic models | Schema enforcement for post-processing outputs |
| **Web Interface** | LightRAG WebUI | Natural language queries and visualization |
| **Framework** | Python 3.13, FastAPI, uv | Application runtime and dependency management |

### Processing Pipeline

```
1. Document Upload       → RFP PDF via WebUI or API
2. MinerU Parsing        → Tables, images, text with structure preservation
3. LightRAG Chunking     → 4,096 tokens/chunk, 15% overlap
4. Entity Extraction     → 18 types via GovCon ontology prompts (~22K tokens)
5. Relationship Inference→ 8 semantic algorithms, Pydantic validation
6. Knowledge Graph       → Neo4j storage with workspace isolation
7. Query Interface       → Natural language questions with cited answers
```

---

## 10. Licensing

All components are commercially viable for internal tooling:

| Component | License | Commercial Use | Notes |
|-----------|---------|----------------|-------|
| **LightRAG** | MIT | ✅ Fully Permitted | Knowledge graph and WebUI |
| **RAG-Anything** | MIT | ✅ Fully Permitted | Multimodal pipeline orchestration |
| **MinerU** | AGPL-3.0 | ✅ Permitted for Internal | PDF parsing engine |
| **Neo4j Community** | GPL-3.0 | ✅ Permitted for Internal | Graph database |
| **Pydantic** | MIT | ✅ Fully Permitted | Schema validation |

**AGPL Note**: AGPL requires source disclosure only if you provide the software as a network service to **external parties**. For internal tooling (employees only), AGPL permits use without disclosure. Our use case is compliant.

If future plans include external SaaS, options include:
- Open-source our MinerU integration (our value is in the ontology, not parsing)
- License MinerU commercially from OpenDataLab
- Substitute with MIT-licensed alternative (pypdfium2 + custom parsing)

---

## 11. The Ask

**Approve $150K development investment** to productionize the working prototype into an enterprise-ready internal tool.

### Expected Return
- **$391K/year** in direct labor savings
- **Measurable pWin improvement** through better compliance and aligned messaging
- **4.5-month breakeven** on development investment
- **Platform foundation** for future capture intelligence agents

### Next Steps
1. Legal review of AGPL compliance strategy
2. Identify 2-3 upcoming pursuits for pilot testing
3. Define MVP feature scope and timeline with development team

---

<div align="center">

**Project Theseus**  
*GovCon Capture Intelligence Platform*

*Building the source of truth that transforms how we capture federal contracts.*

</div>
