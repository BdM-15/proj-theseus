# GovCon Capture Intelligence Feature Roadmap

**Purpose**: Post-PostgreSQL feature planning for agent-powered proposal development  
**Status**: Planning Phase (Phase 9+)  
**Prerequisites**: Branch 010 (PostgreSQL multi-workspace) complete  
**Timeline**: TBD based on Phase 8 production validation

---

## 🎯 Strategic Context

**Current Priority**: PostgreSQL migration (Branch 010) - multi-workspace storage  
**User Guidance**: "Any feature beside the database integration is secondary at this stage."

**This document**: Future features to consider AFTER Phase 8 proven in production with 5+ RFPs.

---

## 📊 Feature Prioritization Workshop

**When**: After processing 5+ RFPs in PostgreSQL workspaces  
**Why**: Real usage data reveals actual pain points  
**How**: Revisit this roadmap and prioritize based on:

- Which manual tasks most time-consuming? (Proposal Outline? Compliance Matrix?)
- Which queries most frequent? (Deliverables? Evaluation factors?)
- Which exports most valuable? (Excel? PowerPoint?)

**Don't build Phase 9 features until Phase 8 proven in production.**

---

## 🚀 Core Capture Management Features (High Priority)

### 1. Intelligent Proposal Outline Generator

**Description**: Analyzes RFP structure (Section L/M/C) and automatically generates compliant proposal outline with recommended page allocations, volume structure, and content guidance. Ensures all "shall" requirements mapped to proposal sections.

**Use Case**:

- Proposal kickoff: Generate initial outline within 1 hour of RFP release
- Capture manager creates strawman structure for team review
- Maps evaluation factors → proposal volumes → page limits

**Priority**: 🔴 **HIGH** (Core value proposition)

**Dependencies**:

- ✅ Already possible: Query knowledge graph for Section L/M entities
- ⚠️ Needs: PydanticAI agents (Phase 9) for structured generation
- ✅ Complete: Section L↔M relationship inference (Phase 6)

**Technical Approach**:

```python
from pydantic_ai import Agent

outline_agent = Agent(
    model="grok-4-fast-reasoning",
    system_prompt="""You are a Shipley-trained proposal manager.
    Generate proposal outlines following FAR 15.210 guidelines."""
)

async def generate_proposal_outline(workspace: str):
    # Query RFP structure
    sections = await rag.aquery(
        "What sections, volumes, and page limits are defined in Section L?",
        workspace=workspace
    )

    # Query evaluation factors
    factors = await rag.aquery(
        "What are the evaluation factors in Section M with weights?",
        workspace=workspace
    )

    # Agent generates outline
    outline = await outline_agent.run(
        f"Generate proposal outline mapping {factors} to {sections}"
    )

    return outline  # Structured Pydantic model
```

**Output Format**:

```
Volume I: Technical Approach (50 pages, Factor B: 40% weight)
  ├─ Section 1: Management Approach (10 pages)
  │   ├─ 1.1 Program Management Organization (addresses REQ-001, REQ-005)
  │   ├─ 1.2 Risk Management Process (addresses REQ-012)
  │   └─ 1.3 Quality Assurance (addresses REQ-023)
  ├─ Section 2: Technical Solution (25 pages)
  │   ├─ 2.1 System Architecture (SHALL requirement from C.3.2.1)
  │   └─ 2.2 Technology Stack (innovation opportunity)
  └─ Section 3: Transition Plan (15 pages)
```

**Implementation Phase**: Phase 9 (PydanticAI agents)  
**Estimated Effort**: 40-60 hours

---

### 2. Deliverables Intelligence Extractor

**Description**: Identifies and catalogs ALL required deliverables from RFP (reports, CDRLs, data items, services, meetings, reviews) with frequency, format, and deadlines. Cross-references Section C, Section J attachments, and clauses.

**Use Case**:

- Cost estimation: Ensure labor hours account for all reporting requirements
- Proposal development: Create deliverables matrix for compliance
- Contract execution: Generate deliverables tracking spreadsheet

**Priority**: 🔴 **HIGH** (Critical for cost accuracy)

**Dependencies**:

- ✅ Already possible: Query for DELIVERABLE entities (12 entity types include this)
- ⚠️ Needs: Enhanced extraction prompts for CDRL parsing
- ⚠️ Needs: Export to Excel/CSV functionality

**Technical Approach**:

```python
# Already working with Phase 6 entity extraction!
deliverables = await rag.aquery(
    "List all deliverables with frequency, format, and section references",
    workspace="navy_mbos_2025"
)

# Phase 8.3: Export to Excel
import pandas as pd

df = pd.DataFrame({
    'Deliverable': [...],
    'Type': ['Report', 'Service', 'Review', 'Data Item'],
    'Frequency': ['Monthly', 'Quarterly', 'As Needed'],
    'Format': ['PDF', 'Excel', 'Presentation'],
    'Due Date': ['Monthly +5 days', 'Quarterly +10 days'],
    'Section Reference': ['C.3.4.5', 'J-05000000', 'FAR 52.232-6'],
    'CLIN': ['CLIN 0001', 'CLIN 0002'],
    'Estimated Hours': [8, 16, 24]
})

df.to_excel('deliverables_matrix.xlsx', index=False)
```

**Implementation Phase**: Phase 8.3 (Export tools) + Phase 9  
**Estimated Effort**: 20-30 hours

---

### 3. Compliance Matrix Generator

**Description**: Automated extraction of ALL Section L instructions ("ankle biters") with page limits, format requirements, font size, margins, submission deadlines, and cross-reference to evaluation factors. Ensures nothing overlooked.

**Use Case**:

- Proposal manager creates compliance checklist for writers
- Red Team review: Verify every instruction addressed
- Color reviews: Track compliance status per requirement

**Priority**: 🔴 **HIGH** (Risk mitigation - non-compliance = proposal rejection)

**Dependencies**:

- ✅ Already possible: SUBMISSION_INSTRUCTION entities extracted
- ✅ Phase 6 complete: Section L↔M relationships inferred
- ⚠️ Needs: Export to Excel with compliance tracking columns

**Implementation Phase**: Phase 8.3 (Export tools) + Phase 9  
**Estimated Effort**: 25-35 hours

---

## 📊 Strategic Intelligence Features (Medium Priority)

### 4. RFP Question Generator (Pre-Proposal Intelligence)

**Description**: AI-powered analysis identifies ambiguities, vagueness, conflicts, inconsistencies, and opportunities for clarification. Generates recommended questions to shape RFP quality and gain competitive advantage.

**Use Case**:

- Capture phase: Submit questions during Q&A period to clarify requirements
- Competitive intelligence: Questions reveal understanding depth
- Risk mitigation: Resolve ambiguities before proposal submission

**Priority**: 🟡 **MEDIUM-HIGH** (Strategic advantage, but not blocking)

**Dependencies**:

- ✅ Already possible: Query knowledge graph for conflicts
- ⚠️ Needs: PydanticAI agents (Phase 9) for question generation
- ⚠️ Needs: Semantic analysis of RFP consistency

**Implementation Phase**: Phase 9 (PydanticAI agents)  
**Estimated Effort**: 30-40 hours

---

### 5. Agency Trends Analyzer (Cross-RFP Intelligence)

**Description**: Analyzes patterns across multiple RFPs from same agency to identify recurring pain points, common evaluation criteria, preferred metrics, typical conflicts, hot buttons, and win themes.

**Use Case**:

- Capture strategy: Tailor messaging to agency preferences
- Pricing strategy: Understand evaluation weight trends (cost vs technical)
- Risk identification: Common agency pain points = opportunity to differentiate

**Priority**: 🟡 **MEDIUM** (High value, but requires 10+ RFPs for meaningful trends)

**Dependencies**:

- ⚠️ **REQUIRES**: PostgreSQL workspace management (Phase 8.3)
- ⚠️ **REQUIRES**: 10+ RFPs processed from same agency
- ⚠️ Needs: Cross-RFP SQL analytics

**Output Format**:

```
Navy RFP Trends Analysis (10 RFPs analyzed: 2020-2025)

📊 Recurring Strategic Themes:
  1. "Cybersecurity resilience" (10/10 RFPs, 100%)
  2. "Sailor safety" (9/10 RFPs, 90%)
  3. "Interoperability with legacy systems" (8/10 RFPs, 80%)

🎯 Common Evaluation Factors:
  1. Past Performance (10/10, avg weight: 38%)
  2. Technical Approach (10/10, avg weight: 35%)
  3. Management Approach (9/10, avg weight: 18%)
```

**Implementation Phase**: Phase 8.3 (PostgreSQL analytics) + Phase 9  
**Estimated Effort**: 40-50 hours

---

## 🚀 Advanced Collaboration Features (Lower Priority)

### 6. Solution Workshop Assistant (Web-Enhanced Brainstorming)

**Description**: Interactive AI assistant that helps brainstorm innovative solutions by combining RFP requirements with external web research (emerging technologies, industry best practices, competitive solutions).

**Use Case**:

- Capture workshops: Generate solution ideas team may not have considered
- Competitive differentiation: Research what competitors offer
- Technology scouting: Identify emerging tools/platforms relevant to RFP

**Priority**: 🟢 **MEDIUM-LOW** (Nice-to-have, but not blocking)

**Dependencies**:

- ⚠️ Needs: Web search integration (Tavily, Perplexity, or Bing API)
- ⚠️ Needs: PydanticAI agents (Phase 9) for brainstorming
- ✅ Already possible: Query RFP requirements from knowledge graph

**Implementation Phase**: Phase 10+ (Optional)  
**Estimated Effort**: 30-40 hours

---

## 📑 Proposal Development Automation (Medium Priority)

### 7. Proposal Kickoff Slide Generator

**Description**: Auto-generates focused PowerPoint slides for proposal kickoff meetings with RFP salient points: evaluation factors, key requirements, win themes, compliance risks, timeline, and team assignments. Follows Shipley methodology.

**Use Case**:

- RFP release: Generate kickoff deck within 2 hours
- Capture manager briefs team on pursuit strategy
- Ensures team aligned on evaluation priorities and win strategy

**Priority**: 🟡 **MEDIUM** (High value for efficiency)

**Dependencies**:

- ⚠️ Needs: PydanticAI agents (Phase 9) for slide content generation
- ⚠️ Needs: PowerPoint generation library (python-pptx)
- ✅ Already possible: Query all required RFP intelligence

**Slide Deck Structure** (8-12 slides):

```
1. Title: "Proposal Kickoff - Navy MBOS"
2. RFP Overview: Solicitation #, agency, value, due date
3. Evaluation Factors: Visual chart with weights
4. Top 10 Critical Requirements: SHALL requirements
5. Win Themes: Navy pain points + our differentiators
6. Compliance Risks: Section L ankle biters
7. Proposal Timeline: Color reviews (Pink, Red, Gold)
8. Volume Outline: Proposed structure with page allocations
```

**Implementation Phase**: Phase 9 (PydanticAI + Export tools)  
**Estimated Effort**: 35-45 hours

---

### 8. Shipley Color Review Milestone Prep

**Description**: Generates PowerPoint slides for Pink Team, Red Team, and Gold Team reviews based on Shipley Guide principles. Includes automated task assignments by functional area (BD, Capture, Technical, Operations, PM, Contracts, Legal).

**Priority**: 🟡 **MEDIUM** (Valuable for proposal quality)

**Dependencies**:

- ⚠️ Needs: PydanticAI agents (Phase 9) for slide generation
- ⚠️ Needs: Shipley Guide integration (prompt engineering)
- ⚠️ Needs: PowerPoint generation (python-pptx)

**Implementation Phase**: Phase 9 (PydanticAI + Shipley integration)  
**Estimated Effort**: 40-50 hours

---

## 🏗️ Advanced Architecture Features (Future)

### 9. IDIQ Task Order Knowledge Graph

**Description**: Hierarchical knowledge graph for IDIQ contracts with base contract + ability to add/remove task order solicitations. Enables insights across task orders for solutioning patterns, pricing trends, and compliance requirements.

**Use Case**:

- IDIQ pursuit: Analyze base contract + 10 task orders for patterns
- Pricing strategy: Identify labor category trends across TOs
- Win strategy: Find what solutions won previous TOs

**Priority**: 🟢 **LOW-MEDIUM** (Niche use case, but high value for IDIQ)

**Dependencies**:

- ⚠️ **REQUIRES**: PostgreSQL hierarchical relationships (Phase 8+)
- ⚠️ **REQUIRES**: Custom graph schema for IDIQ structure
- ⚠️ Needs: Document hierarchy management (add/remove TOs)

**Implementation Phase**: Phase 10+ (Complex architecture)  
**Estimated Effort**: 80-120 hours

---

## 📋 Feature Priority Matrix

| Feature                         | Priority    | Phase | Effort (hrs) | PostgreSQL Required? | PydanticAI Required? |
| ------------------------------- | ----------- | ----- | ------------ | -------------------- | -------------------- |
| **Proposal Outline Generator**  | 🔴 HIGH     | 9     | 40-60        | No                   | Yes                  |
| **Deliverables Extractor**      | 🔴 HIGH     | 8.3+9 | 20-30        | No                   | No                   |
| **Compliance Matrix Generator** | 🔴 HIGH     | 8.3+9 | 25-35        | No                   | No                   |
| **RFP Question Generator**      | 🟡 MED-HIGH | 9     | 30-40        | No                   | Yes                  |
| **Agency Trends Analyzer**      | 🟡 MEDIUM   | 8.3+9 | 40-50        | **YES**              | No                   |
| **Kickoff Slide Generator**     | 🟡 MEDIUM   | 9     | 35-45        | No                   | Yes                  |
| **Color Review Prep**           | 🟡 MEDIUM   | 9     | 40-50        | No                   | Yes                  |
| **Solution Workshop Assistant** | 🟢 MED-LOW  | 10+   | 30-40        | No                   | Yes + Web            |
| **IDIQ Task Order Graph**       | 🟢 LOW-MED  | 10+   | 80-120       | **YES**              | Optional             |

---

## 🗓️ Recommended Implementation Sequence

### Phase 9: Core Capture Features (Weeks 5-10, ~200 hours)

**Priority: High-value, high-usage features**

**Week 5-6: Deliverables + Compliance (50-65 hrs)**

1. Deliverables Intelligence Extractor
2. Compliance Matrix Generator
3. Excel export functionality

**Week 7-8: PydanticAI Setup + Proposal Outline (40-60 hrs)**

1. Install PydanticAI framework
2. Shipley methodology integration
3. Proposal Outline Generator (flagship feature)

**Week 9-10: Strategic Intelligence (60-80 hrs)**

1. RFP Question Generator
2. Agency Trends Analyzer (PostgreSQL analytics)
3. Testing and refinement

---

## 🎯 Quick Wins (Implement First)

### Immediate (No New Dependencies)

1. **Deliverables Query**: Already works!

```python
deliverables = await rag.aquery(
    "List all deliverables with frequency and due dates",
    workspace="navy_mbos_2025"
)
```

2. **Compliance Instructions Query**: Already works!

```python
compliance = await rag.aquery(
    "What are all the Section L submission instructions?",
    workspace="navy_mbos_2025"
)
```

3. **RFP Ambiguity Detection**: Query for conflicts

```python
conflicts = await rag.aquery(
    "Identify conflicting or ambiguous requirements",
    workspace="navy_mbos_2025"
)
```

---

## 💡 Implementation Notes

### Why PydanticAI?

- Type-safe structured outputs (proposal outlines, questions, slide content)
- Agent orchestration (multi-step reasoning for complex features)
- Validation (ensure generated content meets requirements)
- Already in roadmap (FUTURE_AGENT_ARCHITECTURE.md)

### Why Export Tools Critical?

- Capture managers need Excel/PowerPoint for client deliverables
- Integration with existing workflows
- Compliance matrices, deliverables lists require Excel format

---

## 📚 Shipley Guide Digitization Strategy

**Current State**: Shipley PDFs in `docs/capture-intelligence/` folder  
**Goal**: Machine-readable format for PydanticAI agents (Phase 9+)

### Recommended Approach: RAG-Anything Processing

**Use your own system to digitize Shipley Guides!**

```powershell
# Process Shipley PDFs through RAG system
# Create separate workspace for reference materials
$env:POSTGRES_WORKSPACE = "reference_shipley_guides"

# Upload Shipley Capture Guide
curl -X POST http://localhost:9621/insert \
  -F "file=@docs/capture-intelligence/Shipley Capture Guide.pdf" \
  -F "mode=auto"

# Query for methodology
# "What are the Shipley phases for capture planning?"
# "What are Pink Team, Red Team, Gold Team objectives?"
```

**Benefits**:

- ✅ Uses existing multimodal processing
- ✅ Creates queryable Shipley knowledge graph
- ✅ Can cross-reference with RFPs

**Estimated Effort**: 2-3 hours (just upload PDFs)

---

## 🚨 Critical Success Factors

### Must-Haves for Phase 9

- ✅ **Phase 8 Complete**: PostgreSQL multi-workspace proven in production
- ✅ **5+ RFPs Processed**: Real usage data validates priorities
- ✅ **User Feedback**: Which features actually needed vs. nice-to-have
- ✅ **PydanticAI Framework**: Installed and tested with Grok integration

### Nice-to-Haves (Defer to Phase 10+)

- ❌ Web search integration (Solution Workshop)
- ❌ IDIQ hierarchical graphs
- ❌ Multi-user collaboration features

---

## 📝 Document Status

**Status**: Planning (Post-Phase 8)  
**Last Updated**: October 20, 2025  
**User Guidance**: "Any feature beside the database integration is secondary at this stage."  
**Next Milestone**: Complete Branch 010, process 5+ RFPs, then prioritize features  
**Feature Prioritization Workshop**: After Phase 8 production validation (Month 2+)

---

**Remember**: Don't build Phase 9 features until Phase 8 proven in production with 5+ real RFPs!
