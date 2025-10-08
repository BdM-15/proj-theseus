# Future Agent Architecture: PydanticAI for Document Generation

Branch: Future (post-Branch 004)
Created: October 8, 2025
Status: Design/Planning Document

## Vision: Two-Stage Intelligence System

### Stage 1: RAG Intelligence (Current - Branch 003/004)

**Pipeline**: RFP Upload → RAG-Anything → Knowledge Graph → LightRAG Queries  
**Purpose**: Extract structured intelligence from government RFPs  
**Technology**: RAG-Anything + LightRAG + Plain Pydantic  
**Output**: Knowledge graph with entities/relationships

```
Example Entities:
- REQUIREMENT: "Weekly status reports required" (criticality: MANDATORY)
- EVALUATION_FACTOR: "Management Approach" (weight: 30%, adjectival rating)
- SUBMISSION_INSTRUCTION: "Management Volume: 25 pages max"
- CLAUSE: "FAR 52.222-6 Davis-Bacon Act"
```

### Stage 2: Document Generation Agents (Future - PydanticAI)

**Pipeline**: Knowledge Graph → Agent Orchestrator → Document Tools → Deliverables  
**Purpose**: Generate compliance artifacts from RAG intelligence  
**Technology**: PydanticAI + LightRAG queries + Document generation tools  
**Output**: PowerPoints, checklists, milestone docs, trend reports

---

## Why PydanticAI is PERFECT for Stage 2

### 1. Multi-Step Document Workflows

PydanticAI excels at **orchestrating complex multi-step tasks**:

```python
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel

class ComplianceChecklistRequest(BaseModel):
    """User request to generate compliance checklist."""
    rfp_id: str
    sections: list[str]  # e.g., ["Section L", "Section M"]
    format: str  # "excel", "markdown", "pdf"

class ChecklistDependencies(BaseModel):
    """Injected dependencies for agent tools."""
    lightrag_client: Any  # Query knowledge graph
    doc_generator: Any    # Generate Excel/PDF

@compliance_agent.tool
async def query_requirements(
    ctx: RunContext[ChecklistDependencies],
    section: str
) -> list[dict]:
    """Query LightRAG for requirements in a section."""
    result = await ctx.deps.lightrag_client.query(
        f"List all REQUIREMENT entities in {section} with criticality"
    )
    return result['entities']

@compliance_agent.tool
async def generate_checklist_excel(
    ctx: RunContext[ChecklistDependencies],
    requirements: list[dict]
) -> str:
    """Generate Excel checklist with compliance tracking."""
    filepath = ctx.deps.doc_generator.create_excel(requirements)
    return filepath

# Agent orchestrates the workflow:
result = await compliance_agent.run(
    "Create compliance checklist for Section L requirements in Excel format",
    deps=ChecklistDependencies(
        lightrag_client=lightrag,
        doc_generator=doc_gen
    )
)
```

**Why this works**:

- ✅ Agent **breaks down complex request** ("create checklist") into tool calls
- ✅ **Type-safe** tool parameters via Pydantic
- ✅ **Dependency injection** keeps tools testable
- ✅ **Multi-step reasoning**: Query → Filter → Format → Generate

### 2. Tool Calling for Document Generation

PydanticAI's tool system maps perfectly to document operations:

```python
@milestone_agent.tool
async def query_evaluation_factors(ctx: RunContext[MilestoneDeps]) -> list[dict]:
    """Get evaluation factors with weights from knowledge graph."""
    return await ctx.deps.lightrag.query(
        "List all EVALUATION_FACTOR entities with relative_importance"
    )

@milestone_agent.tool
async def create_powerpoint_slide(
    ctx: RunContext[MilestoneDeps],
    title: str,
    content: dict,
    template: str = "milestone_template.pptx"
) -> int:
    """Create PowerPoint slide from evaluation factor data."""
    slide_num = ctx.deps.pptx_builder.add_slide(title, content, template)
    return slide_num

@milestone_agent.tool
async def add_compliance_matrix(
    ctx: RunContext[MilestoneDeps],
    requirements: list[dict],
    slide_num: int
) -> bool:
    """Add compliance matrix table to PowerPoint slide."""
    success = ctx.deps.pptx_builder.add_table(slide_num, requirements)
    return success
```

**Agent workflow** (automatic tool orchestration):

1. User: "Create Milestone 2 PowerPoint with evaluation factors"
2. Agent calls: `query_evaluation_factors()` → Gets M1, M2, M3 with weights
3. Agent calls: `create_powerpoint_slide()` → Creates title slide
4. Agent calls: `query_requirements()` → Gets requirements for each factor
5. Agent calls: `add_compliance_matrix()` → Adds traceability table
6. Returns: "milestone_2.pptx with 5 slides (1 title, 4 factors)"

### 3. Context Management Across Document Types

PydanticAI maintains **conversation context** across multiple document requests:

```python
# User conversation:
User: "Create compliance checklist for Section L"
Agent: [generates checklist.xlsx] "Created 47-item checklist"

User: "Now create a PowerPoint summarizing the top 10 items"
Agent: [remembers previous checklist context]
       [queries top 10 by criticality]
       [generates summary.pptx]
       "Created PowerPoint with top 10 MANDATORY requirements"

User: "Add a trend analysis slide showing requirement types"
Agent: [remembers checklist + PowerPoint context]
       [queries requirement statistics]
       [adds trend slide to existing PowerPoint]
       "Added trend analysis as Slide 3"
```

**Why this matters**: Document generation is **iterative** - users refine outputs across multiple requests.

---

## Proposed Agent Architecture

### Document Generation Agents (PydanticAI)

```
┌─────────────────────────────────────────────────────────┐
│              Document Orchestrator Agent                │
│  (Routes requests to specialized agents)                │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
┌───────▼────────┐ ┌──────▼─────────┐ ┌────▼────────────┐
│ Compliance     │ │ Milestone      │ │ Trend Analysis  │
│ Agent          │ │ Agent          │ │ Agent           │
│ (Checklists)   │ │ (PowerPoints)  │ │ (Reports)       │
└───────┬────────┘ └──────┬─────────┘ └────┬────────────┘
        │                 │                 │
        └─────────────────┼─────────────────┘
                          │
                  ┌───────▼────────┐
                  │  Shared Tools  │
                  ├────────────────┤
                  │ • LightRAG     │
                  │   Query        │
                  │ • Excel Gen    │
                  │ • PPTX Gen     │
                  │ • PDF Gen      │
                  │ • Markdown Gen │
                  └────────────────┘
                          │
                  ┌───────▼────────┐
                  │  Knowledge     │
                  │  Graph         │
                  │  (LightRAG)    │
                  └────────────────┘
```

### Agent Definitions

#### 1. Compliance Checklist Agent

**Purpose**: Generate compliance tracking artifacts  
**Inputs**: RFP sections, requirement types, format preferences  
**Tools**:

- `query_requirements()` - Get requirements from knowledge graph
- `classify_requirements()` - Group by criticality/type
- `generate_excel_checklist()` - Create Excel with tracking columns
- `generate_markdown_checklist()` - Create Markdown format
- `generate_pdf_checklist()` - Create printable PDF

**Output**: Compliance checklist files with columns:

- Requirement ID
- Requirement Text
- Section
- Criticality (MANDATORY/IMPORTANT/OPTIONAL)
- Evaluation Factor Linkage
- Compliance Status (empty - for proposal team)
- Evidence Location (empty - for proposal team)

#### 2. Milestone PowerPoint Agent

**Purpose**: Generate milestone review presentations  
**Inputs**: Milestone number (2/3/4), RFP analysis, compliance data  
**Tools**:

- `query_evaluation_factors()` - Get scoring criteria
- `query_section_l_m_mapping()` - Get proposal instructions
- `create_pptx_from_template()` - Load milestone template
- `add_evaluation_matrix_slide()` - Add factor/subfactor hierarchy
- `add_compliance_summary_slide()` - Add requirement traceability
- `add_win_themes_slide()` - Add discriminator analysis
- `add_risk_assessment_slide()` - Add risk/mitigation matrix

**Output**: PowerPoint with standard milestone structure:

- Slide 1: RFP Overview (solicitation #, due date, eval methodology)
- Slide 2: Evaluation Factors (hierarchy with weights)
- Slide 3: Submission Instructions (page limits, volumes)
- Slide 4: Requirement Summary (count by type/criticality)
- Slide 5: Compliance Traceability (Section L↔M mapping)
- Slide 6: Risk Assessment (gaps, ambiguities, questions)

#### 3. Trend Analysis Agent

**Purpose**: Generate analytical reports on RFP patterns  
**Inputs**: RFP database, analysis timeframe, agency filter  
**Tools**:

- `query_historical_rfps()` - Get past RFP data
- `analyze_evaluation_trends()` - Factor weight trends over time
- `analyze_requirement_complexity()` - Requirement density analysis
- `analyze_clause_patterns()` - FAR/DFARS usage patterns
- `generate_markdown_report()` - Create analytical report
- `create_visualization_charts()` - Generate trend charts

**Output**: Markdown report with embedded charts:

- Agency preference patterns (LPTA vs. Best Value)
- Evaluation factor evolution (technical vs. cost weighting)
- Page limit trends (volume complexity over time)
- Clause usage patterns (security requirements, labor standards)

---

## Integration with Current System

### Branch 004 Optimization (Current Work)

**Goal**: Optimize RAG-Anything + LightRAG pipeline  
**Scope**: Document ingestion, knowledge graph, entity extraction  
**Technology**: Plain Pydantic for validation  
**No PydanticAI**: Correct - agents not needed for batch processing

### Future Branch: Agent Integration

**Goal**: Add document generation layer on top of optimized RAG pipeline  
**Scope**: Compliance artifacts, milestone docs, trend reports  
**Technology**: PydanticAI for agent orchestration  
**Dependencies**:

- Requires stable Branch 004 baseline
- New dependencies: `pydantic-ai`, `python-pptx`, `openpyxl`, `matplotlib`
- Estimated LOC: +800-1200 (new agent layer, separate from RAG pipeline)

### Architectural Boundaries

```python
# src/raganything_server.py (Branch 004 - NO AGENTS)
# Handles: RFP ingestion, knowledge graph, queries
@app.post("/insert")
async def insert_document(...):
    # Phase 6 LLM inference (plain Pydantic validation)
    entities, relationships = await phase6_inference(file)
    return {"status": "processed"}

@app.get("/query")
async def query_rag(query: str):
    # LightRAG graph query (no agents)
    result = await lightrag.query(query)
    return {"answer": result}

# src/agent_orchestrator.py (FUTURE BRANCH - PydanticAI)
# Handles: Document generation from knowledge graph
from pydantic_ai import Agent

compliance_agent = Agent(model="grok-4-fast-reasoning")

@app.post("/generate/checklist")
async def generate_checklist(request: ChecklistRequest):
    # Agent orchestrates: query → filter → generate
    result = await compliance_agent.run(
        f"Create {request.format} compliance checklist for {request.sections}",
        deps=ChecklistDependencies(lightrag=lightrag)
    )
    return {"file_path": result.data}
```

**Key Insight**: PydanticAI agents **consume** the knowledge graph, they don't **produce** it.

---

## When to Add PydanticAI (Decision Criteria)

### ✅ Add PydanticAI When:

1. **Branch 004 is complete** (RAG pipeline optimized)
2. **User requests document generation** (checklists, PowerPoints, reports)
3. **Multi-step workflows emerge** (query → analyze → format → generate)
4. **Iterative refinement needed** (users refine outputs across requests)

### ❌ Don't Add PydanticAI If:

1. **Branch 004 still in progress** (focus on core optimization)
2. **Users only need knowledge graph queries** (LightRAG WebUI sufficient)
3. **Document generation is one-off** (simple scripts suffice)
4. **No budget for additional complexity** (+800-1200 LOC)

---

## Recommended Roadmap

### Phase 1: Branch 004 (Current - October 2025)

**Goal**: Optimize core RAG pipeline  
**Deliverables**:

- ✅ Reduced LOC (3,577 → 3,200-3,400)
- ✅ Plain Pydantic validation for Phase 6
- ✅ Consolidated prompts, cleaned dead code
- ✅ Non-regressed performance metrics

### Phase 2: Agent Architecture Design (November 2025)

**Goal**: Design document generation agent system  
**Deliverables**:

- Detailed tool specifications for each agent
- LightRAG query patterns for document data
- Document template designs (Excel, PowerPoint, Markdown)
- Cost/complexity analysis

### Phase 3: Proof of Concept Agent (December 2025)

**Goal**: Implement ONE agent (compliance checklist)  
**Deliverables**:

- PydanticAI agent with 3-4 tools
- Excel checklist generator
- Integration with LightRAG queries
- User acceptance testing

### Phase 4: Full Agent Suite (Q1 2026)

**Goal**: Complete all document generation agents  
**Deliverables**:

- Milestone PowerPoint agent
- Trend analysis agent
- Document orchestrator agent
- Production deployment

---

## Cost-Benefit Analysis

### Adding PydanticAI (Future Branch)

**Costs**:

- **LOC**: +800-1200 (agent layer, separate from RAG pipeline)
- **Dependencies**: `pydantic-ai`, `python-pptx`, `openpyxl`, `matplotlib` (~40MB)
- **Complexity**: New agent abstraction layer
- **Maintenance**: Keep agents in sync with LightRAG schema
- **Testing**: Agent workflow testing (complex multi-step scenarios)

**Benefits**:

- **User value**: Automated document generation (10x faster than manual)
- **Consistency**: Standardized compliance artifacts
- **Scalability**: Handle multiple RFPs in parallel
- **Insights**: Trend analysis across RFP database
- **Differentiation**: Unique capability vs. generic RAG tools

**ROI**: High for teams processing 5+ RFPs/month

---

## References

- **PydanticAI Docs**: https://ai.pydantic.dev/agents/
- **LightRAG Integration**: https://github.com/HKUDS/LightRAG
- **Shipley Milestone Reviews**: `docs/Shipley Capture Guide.pdf` p.45-60
- **Branch 004 Charter**: `docs/BRANCH_004_CODE_OPTIMIZATION.md`

---

**Status**: Design document for future work  
**Next Step**: Complete Branch 004, then user validation on document generation needs
