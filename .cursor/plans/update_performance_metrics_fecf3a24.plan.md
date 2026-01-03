---
name: Update Performance Metrics
overview: Update the use case document with actual production metrics (38 min, $2.12) and recalculate all ROI figures accordingly.
todos:
  - id: update-metrics
    content: Update performance metrics table with 38 min / $2.12 values
    status: pending
  - id: update-roi
    content: Recalculate ROI scenario with new cost figures
    status: pending
  - id: update-readiness
    content: Update Technical Readiness section with actual measured values
    status: pending
  - id: update-conclusion
    content: Update conclusion section annual savings figure
    status: pending
---

# Use-Case: AI-Driven RFP Analysis (Replacing Manual "Shred" Spreadsheets)

## 1.1 Target Application: Federal RFPs (All Contract Types)

Large federal solicitations (50-500+ pages) across IDIQ Task Orders, Full & Open Competitions, and Set-Asides where manual analysis creates delays and compliance risk.

---

## 2.1 AI Application: Ontology-Based RAG with Government Contracting Knowledge Graph

- **Multimodal Document Parsing**: MinerU extracts text, tables, and images from complex RFP PDFs
- **18 Specialized Entity Types**: Requirements, evaluation factors, deliverables, clauses—not generic "Person/Organization"
- **Dual-Model LLM Routing**: Non-reasoning model for extraction (format compliance), reasoning model for queries
- **Semantic Relationship Inference**: 8 algorithms map Section L to M, trace requirements to deliverables

---

## 3.1 The Operational Gap

Our current manual "shred" process is **slow, error-prone, and doesn't scale**.

| Problem | Impact |

|---------|--------|

| **40-80 hours** of manual reading per RFP | Delays pursuit decisions by 2-3 weeks |

| Excel-based requirement tracking | 15-20% of proposals have compliance gaps |

| Each pursuit starts from zero | No institutional learning across bids |

| SMEs read entire RFPs to find sections | Senior technical staff doing admin work |

**The Hidden Cost**: A 5-person capture team spending 2 weeks analyzing a 425-page RFP at $150/hour = **$120,000** in pre-proposal labor. At 20 pursuits/year, that's **$2.4M annually** in RFP analysis alone.

---

## 4.1 The Solution: AI-Powered RFP Intelligence Platform

Replace manual spreadsheets with an **automated knowledge graph** that delivers actionable intelligence in under 1 hour.

**Automated RFP Decomposition**: The AI "shreds" the RFP into a queryable knowledge graph, extracting all requirements (SHALL/SHOULD/MAY), evaluation factors with weights, deliverables (CDRLs), and compliance instructions—tasks that take humans days completed in 38 minutes.

**Section L↔M Alignment**: The AI automatically maps submission instructions to evaluation factors, ensuring proposal structure directly addresses scoring criteria. No more missed "ankle biters."

**Requirement Traceability**: Every SHALL statement is traced to its source section, related deliverables, and evaluation criteria. Writers receive structured requirements, not raw PDFs.

**Natural Language Queries**: Ask "What are the mandatory cybersecurity requirements and how will they be evaluated?" and get precise answers with citations—not keyword search results.

---

## 5.1 Targeted Savings & Goal

**Goal: 95% Reduction in RFP Analysis Time + 70% Reduction in Compliance Gaps**

**Formula**: Savings = (Manual Hours × Burdened Rate) - (AI Cost + Review Hours × Rate)

**Validated Benchmark** (425-page MCPP II DRFP):

- Processing time: **38 minutes**
- LLM cost: **$2.12**
- Entities extracted: **1,500+** with semantic relationships

**Scenario Calculation**:

```
Annual Volume:                    20 RFPs
Current Cost per RFP:             $20,000 (labor)
Current Annual Spend:             $400,000

With Platform:
  Processing (LLM):               $5/RFP × 20 = $100/year (with buffer)
  Review Labor (3 hrs × $150):    $450 × 20 = $9,000/year
  Annual Platform Cost:           $9,100

ANNUAL SAVINGS:                   $390,900 (98% reduction)
3-YEAR SAVINGS:                   $1,172,700

Development Investment:           ~$150,000 (6-month build)
ROI BREAKEVEN:                    ~4.5 months
```

---

## 6.1 Strategic Value

**RFP analysis is the bottleneck in every pursuit.** While competitors spend 2 weeks shredding, we have actionable intelligence in under 1 hour.

- **Earlier bid/no-bid decisions** → More selective pursuit portfolio
- **Better compliance** → Fewer pink team rewrites
- **Aligned win themes** → Higher evaluation scores
- **Institutional memory** → Knowledge compounds across pursuits

---

## 6.2 Connected Intelligence: One Source of Truth, Many Outputs

The knowledge graph isn't just a query tool—it becomes the **single source of truth** that powers multiple specialized agents across the capture lifecycle:

| Agent | Function |

|-------|----------|

| **BOE Agent** | Extracts workload drivers to ground basis of estimates in RFP facts |

| **SOW Agent** | Analyzes requirements to delineate subcontractor scope, reducing pricing risk |

| **Compliance Agent** | Auto-generates compliance matrices cross-referencing Sections L, M, and C |

| **Kick-Off Agent** | RFP drops at 4 PM → Ready by 8 AM. Generates kick-off deck with scope, requirements, and strategic insights overnight |

| **Trend Analysis** | Analyzes across all agency RFPs to identify evaluation patterns and terminology preferences |

**The Multiplier Effect**: Build the knowledge graph once, extract value many times. Each persona—capture manager, pricing analyst, proposal writer, contracts—gets tailored outputs from the same trusted source.

---

## 7.1 Licensing: Commercial Viability Confirmed

| Component | License | Internal Use |

|-----------|---------|--------------|

| LightRAG | MIT | ✅ Permitted |

| RAG-Anything | MIT | ✅ Permitted |

| MinerU | AGPL-3.0 | ✅ Permitted (internal tools exempt) |

| Neo4j Community | GPL-3.0 | ✅ Permitted |

**Note**: AGPL only requires source disclosure for external SaaS. Internal tooling is compliant.

---

## 8.1 The Ask

**Approve $150K development investment** to productionize the working prototype into an enterprise-ready internal tool.

**Expected Return**:

- **$391K/year** in direct labor savings
- **Measurable pWin improvement** through better compliance
- **4.5-month breakeven** on development investment

---

## Appendix: Technology Stack

| Layer | Technology |

|-------|------------|

| Document Parsing | MinerU 2.6.4 (multimodal PDF) |

| Knowledge Graph | LightRAG + Neo4j |

| LLM | xAI Grok-4.1-fast (dual-model routing) |

| Embeddings | OpenAI text-embedding-3-large |

| Framework | Python 3.13, FastAPI |

---

*Project Theseus — December 2025*