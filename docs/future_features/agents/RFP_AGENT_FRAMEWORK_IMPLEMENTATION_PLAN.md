# RFP Analysis Agent Framework - Implementation Plan

**Document Type**: Implementation Plan  
**Status**: DRAFT  
**Created**: December 2025  
**Branch**: TBD (suggest: `029-rfp-agent-framework`)  
**GitHub Issue**: [#29](https://github.com/BdM-15/govcon-capture-vibe/issues/29)

---

## Executive Summary

Build a **Model Context Protocol (MCP)** powered agent framework that transforms raw RFP knowledge graphs into structured capture deliverables. Each specialized agent queries the same underlying data (Neo4j graph + LightRAG vectors) but produces domain-specific outputs (proposal outlines, SOW drafts, win themes, BOE worksheets, etc.).

### Core Philosophy

> "Let the data **ground** it, Pydantic **cage** it, agents **shape** it."

- **Grounding**: Neo4j graph + LightRAG vector chunks provide authoritative RFP context
- **Caging**: Pydantic models enforce output structure and validation
- **Shaping**: Agents apply domain expertise to transform data into deliverables

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     MCP Context Layer (context.py)               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   │
│  │  Neo4j Graph    │  │  LightRAG       │  │  Pydantic       │   │
│  │  get_entities() │  │  aquery()       │  │  Validators     │   │
│  │  get_rels()     │  │  pull_chunks()  │  │  (schema.py)    │   │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘   │
│           │                    │                    │            │
│           └────────────────────┼────────────────────┘            │
│                                │                                 │
│                    ┌───────────▼───────────┐                     │
│                    │    Shared Tools       │                     │
│                    │  • get_graph_slice()  │                     │
│                    │  • pull_rfp_chunks()  │                     │
│                    │  • validate_output()  │                     │
│                    │  • format_as_doc()    │                     │
│                    └───────────┬───────────┘                     │
└────────────────────────────────┼─────────────────────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌───────────────┐
│  Proposal     │      │ SOW Agent     │      │ Win-Theme     │
│  Outline      │      │               │      │ Agent         │
│  Agent        │      │ Output:       │      │ Output:       │
│ Output:       │      │ SOWDraft      │      │ WinThemeReport│
│ ProposalOutline      │ (Pydantic)    │      │ (Pydantic)    │
│ (Pydantic)    │      └───────┬───────┘      └───────┬───────┘
└───────┬───────┘              │                      │
        │                      │                      │
        └──────────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Renderer Layer    │
                    │   (renderer.py)     │
                    │  • to_excel()       │
                    │  • to_docx()        │
                    │  • to_pptx()        │
                    │  • to_json()        │
                    └─────────────────────┘
```

---

## File Structure

```
src/
├── agents/                          # NEW: Agent framework
│   ├── __init__.py
│   ├── context.py                   # MCP context layer (Neo4j + LightRAG access)
│   ├── tools.py                     # Shared tool implementations
│   ├── renderer.py                  # Export utilities (DOCX, Excel, PPTX)
│   ├── base.py                      # BaseAgent abstract class
│   │
│   ├── proposal_outline_agent.py    # Phase 1: Proposal outline (proof of concept)
│   ├── sow_draft_agent.py           # Phase 2: SOW draft generation
│   ├── win_theme_agent.py           # Phase 2: Win theme identification
│   ├── risk_register_agent.py       # Phase 2: Risk register
│   ├── boe_agent.py                 # Phase 3: BOE worksheet (complex)
│   ├── past_performance_agent.py    # Phase 3: Past performance mapping
│   └── kickoff_deck_agent.py        # Phase 3: Kickoff slide generation
│
├── ontology/
│   └── schema.py                    # EXISTING: Reuse Pydantic models
│
├── inference/
│   └── neo4j_graph_io.py           # EXISTING: Reuse Neo4j operations
│
└── server/
    └── routes.py                    # ADD: Agent endpoints
```

---

## Phase 1: Foundation + Proposal Outline Agent (Week 1-2)

### Why Proposal Outline First?

The **Proposal Outline Agent** is the ideal proof-of-concept because:

1. **Simpler data model**: Volumes → Sections → Page allocations (hierarchical)
2. **Clear entity mappings**: SUBMISSION_INSTRUCTION + EVALUATION_FACTOR entities
3. **Existing prompt**: `prompts/user_queries/proposal_outline_generation.md` already exists
4. **High visibility**: Proposal outline is first deliverable in Shipley methodology
5. **Lower complexity**: No labor driver analysis or cost classification required

The **BOE Agent** requires complex classification logic (7 BOE categories, labor drivers, material/equipment needs) and is better suited for Phase 3 after patterns are established.

### 1.1 MCP Context Layer (`src/agents/context.py`)

The central hub providing unified access to all data sources.

```python
"""
MCP Context Layer - Central hub for agent data access

Exposes:
- Neo4j graph queries (entities, relationships)
- LightRAG semantic queries (hybrid search)
- Pydantic validators (from schema.py)
"""

import os
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from neo4j import GraphDatabase
from lightrag import LightRAG, QueryParam
from src.ontology.schema import (
    Requirement, EvaluationFactor, SubmissionInstruction
)

logger = logging.getLogger(__name__)


@dataclass
class MCPContext:
    """
    Model Context Protocol context for RFP analysis agents.

    Provides unified access to:
    - Neo4j knowledge graph (entities, relationships)
    - LightRAG vector store (semantic search, chunk retrieval)
    - Pydantic validators (output schema enforcement)
    """
    workspace: str
    neo4j_driver: Any = None
    lightrag: LightRAG = None

    def __post_init__(self):
        """Initialize connections on first use"""
        if not self.neo4j_driver:
            self._init_neo4j()
        if not self.lightrag:
            self._init_lightrag()

    def _init_neo4j(self):
        """Initialize Neo4j connection"""
        uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")
        password = os.getenv("NEO4J_PASSWORD")

        self.neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
        logger.info(f"🔗 Neo4j connected for workspace: {self.workspace}")

    def _init_lightrag(self):
        """Initialize LightRAG instance"""
        working_dir = os.path.join("rag_storage", self.workspace)

        from src.server.config import configure_raganything_args
        from lightrag.api.config import global_args

        configure_raganything_args()

        self.lightrag = LightRAG(working_dir=working_dir)
        logger.info(f"📚 LightRAG initialized: {working_dir}")

    def get_entities_by_type(
        self,
        entity_types: List[str],
        limit: int = 500
    ) -> List[Dict]:
        """Fetch entities of specified types from Neo4j."""
        query = f"""
        MATCH (n:`{self.workspace}`)
        WHERE n.entity_type IN $types
        RETURN elementId(n) as id,
               n.entity_id as entity_name,
               n.entity_type as entity_type,
               n.description as description,
               n.source_id as source_id
        LIMIT $limit
        """

        with self.neo4j_driver.session() as session:
            result = session.run(query, types=entity_types, limit=limit)
            entities = [dict(record) for record in result]

        logger.info(f"📊 Retrieved {len(entities)} entities of types: {entity_types}")
        return entities

    def get_entity_relationships(
        self,
        source_types: List[str],
        target_types: List[str],
        relationship_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """Get all relationships between entity type pairs."""
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join(relationship_types)
            rel_filter = f":{rel_types}"

        query = f"""
        MATCH (source:`{self.workspace}`)-[r{rel_filter}]->(target:`{self.workspace}`)
        WHERE source.entity_type IN $source_types
          AND target.entity_type IN $target_types
        RETURN source.entity_id as source_name,
               source.entity_type as source_type,
               source.description as source_description,
               target.entity_id as target_name,
               target.entity_type as target_type,
               target.description as target_description,
               type(r) as relationship_type,
               r.confidence as confidence,
               r.reasoning as reasoning
        """

        with self.neo4j_driver.session() as session:
            result = session.run(
                query,
                source_types=source_types,
                target_types=target_types
            )
            return [dict(record) for record in result]

    async def query_rfp(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 20
    ) -> str:
        """Query RFP knowledge graph using LightRAG semantic search."""
        param = QueryParam(mode=mode, top_k=top_k)
        response = await self.lightrag.aquery(query, param=param)

        logger.info(f"🔍 LightRAG query: '{query[:50]}...' mode={mode}")
        return response

    async def query_with_prompt(
        self,
        query: str,
        user_prompt: str,
        mode: str = "hybrid"
    ) -> str:
        """Query with a specialized user prompt for formatted output."""
        param = QueryParam(mode=mode, user_prompt=user_prompt)
        response = await self.lightrag.aquery(query, param=param)
        return response

    def close(self):
        """Close all connections"""
        if self.neo4j_driver:
            self.neo4j_driver.close()
            logger.info("🔌 Neo4j connection closed")


def create_context(workspace: str) -> MCPContext:
    """Factory function to create MCP context for a workspace"""
    return MCPContext(workspace=workspace)
```

### 1.2 Base Agent (`src/agents/base.py`)

```python
"""
Base Agent - Abstract class for all RFP analysis agents
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic
from pydantic import BaseModel

from src.agents.context import MCPContext

T = TypeVar('T', bound=BaseModel)


class BaseAgent(ABC, Generic[T]):
    """Abstract base class for RFP analysis agents."""

    output_model: type[T] = None

    def __init__(self, context: MCPContext):
        self.context = context
        self.workspace = context.workspace

    @abstractmethod
    async def generate(self, **kwargs) -> T:
        """Generate the agent's output."""
        pass

    def validate_output(self, data: dict) -> T:
        """Validate output data against the agent's output model."""
        if not self.output_model:
            raise NotImplementedError("Agent must define output_model")
        return self.output_model(**data)

    @property
    def name(self) -> str:
        return self.__class__.__name__
```

### 1.3 Proposal Outline Agent (`src/agents/proposal_outline_agent.py`) - First Agent

```python
"""
Proposal Outline Agent

Generates compliant proposal outline from Section L/M analysis.
Maps evaluation factors to volumes with page allocations.

Output: ProposalOutline (Pydantic model)
Export: Word document with structured outline
"""

import logging
from typing import List, Optional
from pydantic import BaseModel, Field

from src.agents.base import BaseAgent
from src.agents.context import MCPContext

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# Output Models (Pydantic)
# ─────────────────────────────────────────────────────────────

class ProposalSection(BaseModel):
    """Single section within a proposal volume"""
    section_number: str = Field(..., description="e.g., '1.1', '2.3.1'")
    section_title: str = Field(..., description="Section heading")
    page_allocation: int = Field(default=0, description="Suggested pages")

    # Compliance mapping
    evaluation_factors: List[str] = Field(default_factory=list)
    requirements_addressed: List[str] = Field(default_factory=list)

    # Content guidance
    content_guidance: str = Field(default="", description="What to include")

    # Subsections
    subsections: List["ProposalSection"] = Field(default_factory=list)


class ProposalVolume(BaseModel):
    """Single volume in the proposal"""
    volume_number: int = Field(..., description="e.g., 1, 2, 3")
    volume_title: str = Field(..., description="e.g., 'Technical Approach'")
    page_limit: Optional[int] = Field(default=None, description="From Section L")

    # Evaluation mapping
    primary_evaluation_factor: Optional[str] = Field(default=None)
    evaluation_weight: Optional[float] = Field(default=None, description="Percentage weight")

    # Sections
    sections: List[ProposalSection] = Field(default_factory=list)

    @property
    def total_pages(self) -> int:
        """Sum of all section page allocations"""
        return sum(s.page_allocation for s in self.sections)


class ProposalOutline(BaseModel):
    """Complete proposal outline for an RFP"""
    rfp_name: str = Field(..., description="RFP identifier")
    workspace: str = Field(..., description="Knowledge graph workspace")

    # Volumes
    volumes: List[ProposalVolume] = Field(default_factory=list)

    # Summary
    total_volumes: int = 0
    total_page_limit: int = 0

    # Metadata
    generated_by: str = "ProposalOutlineAgent"


# ─────────────────────────────────────────────────────────────
# Proposal Outline Agent Implementation
# ─────────────────────────────────────────────────────────────

class ProposalOutlineAgent(BaseAgent[ProposalOutline]):
    """
    Proposal Outline Generator

    Workflow:
    1. Query Neo4j for SUBMISSION_INSTRUCTION entities (Section L)
    2. Query Neo4j for EVALUATION_FACTOR entities (Section M)
    3. Query relationships (SUBMISSION_INSTRUCTION → EVALUATION_FACTOR)
    4. Use LLM to structure into volumes/sections
    5. Return structured ProposalOutline
    """

    output_model = ProposalOutline

    async def generate(
        self,
        rfp_name: str = ""
    ) -> ProposalOutline:
        """
        Generate proposal outline from RFP knowledge graph.

        Args:
            rfp_name: Display name for the RFP

        Returns:
            ProposalOutline with volumes and sections
        """
        logger.info(f"📋 Proposal Outline Agent starting for workspace: {self.workspace}")

        # Step 1: Get submission instructions (Section L)
        instructions = self.context.get_entities_by_type(
            entity_types=["submission_instruction"],
            limit=200
        )
        logger.info(f"  📄 Found {len(instructions)} submission instructions")

        # Step 2: Get evaluation factors (Section M)
        eval_factors = self.context.get_entities_by_type(
            entity_types=["evaluation_factor"],
            limit=100
        )
        logger.info(f"  ⚖️ Found {len(eval_factors)} evaluation factors")

        # Step 3: Get Section L ↔ M relationships
        l_m_mappings = self.context.get_entity_relationships(
            source_types=["submission_instruction"],
            target_types=["evaluation_factor"],
            relationship_types=["GUIDES", "CORRESPONDS_TO"]
        )
        logger.info(f"  🔗 Found {len(l_m_mappings)} L↔M relationships")

        # Step 4: Use LLM to structure the outline
        volumes = await self._structure_outline(
            instructions=instructions,
            eval_factors=eval_factors,
            l_m_mappings=l_m_mappings
        )

        # Step 5: Build final outline
        outline = ProposalOutline(
            rfp_name=rfp_name or self.workspace,
            workspace=self.workspace,
            volumes=volumes,
            total_volumes=len(volumes),
            total_page_limit=sum(v.page_limit or 0 for v in volumes)
        )

        logger.info(f"✅ Proposal Outline complete: {outline.total_volumes} volumes")
        return outline

    async def _structure_outline(
        self,
        instructions: List[dict],
        eval_factors: List[dict],
        l_m_mappings: List[dict]
    ) -> List[ProposalVolume]:
        """
        Use LLM to structure instructions/factors into proposal volumes.
        """
        # Load existing prompt template
        from src.core.prompt_loader import load_prompt
        outline_prompt = load_prompt("user_queries/proposal_outline_generation")

        # Build context summary
        context_text = self._build_context_summary(instructions, eval_factors, l_m_mappings)

        # Query LLM with structured prompt
        query = f"""Based on this RFP analysis, generate a proposal outline:

{context_text}

Structure the response as volumes with sections, page allocations, and evaluation factor mappings."""

        llm_response = await self.context.query_with_prompt(
            query=query,
            user_prompt=outline_prompt,
            mode="hybrid"
        )

        # Parse LLM response into volumes
        volumes = self._parse_llm_response(llm_response, eval_factors)

        return volumes

    def _build_context_summary(
        self,
        instructions: List[dict],
        eval_factors: List[dict],
        l_m_mappings: List[dict]
    ) -> str:
        """Build summary text for LLM context."""
        lines = []

        lines.append("## Submission Instructions (Section L)")
        for inst in instructions[:20]:  # Limit for context window
            name = inst.get("entity_name", "Unknown")
            desc = inst.get("description", "")[:200]
            lines.append(f"- {name}: {desc}")

        lines.append("\n## Evaluation Factors (Section M)")
        for factor in eval_factors[:15]:
            name = factor.get("entity_name", "Unknown")
            desc = factor.get("description", "")[:200]
            lines.append(f"- {name}: {desc}")

        lines.append("\n## Section L ↔ M Mappings")
        for mapping in l_m_mappings[:20]:
            src = mapping.get("source_name", "Unknown")
            tgt = mapping.get("target_name", "Unknown")
            lines.append(f"- {src} → {tgt}")

        return "\n".join(lines)

    def _parse_llm_response(
        self,
        llm_response: str,
        eval_factors: List[dict]
    ) -> List[ProposalVolume]:
        """
        Parse LLM response into structured ProposalVolume objects.

        TODO: Enhance with Instructor library for structured output.
        """
        # Create factor lookup
        factor_names = {f["entity_name"] for f in eval_factors}

        # For now, create default volumes based on common patterns
        # This will be enhanced with LLM structured output
        volumes = [
            ProposalVolume(
                volume_number=1,
                volume_title="Technical Approach",
                page_limit=50,
                primary_evaluation_factor="Technical Approach",
                sections=[
                    ProposalSection(
                        section_number="1.1",
                        section_title="Management Approach",
                        page_allocation=15,
                        content_guidance="Describe program management structure and processes"
                    ),
                    ProposalSection(
                        section_number="1.2",
                        section_title="Technical Solution",
                        page_allocation=25,
                        content_guidance="Detail technical approach to requirements"
                    ),
                    ProposalSection(
                        section_number="1.3",
                        section_title="Transition Plan",
                        page_allocation=10,
                        content_guidance="Describe transition and phase-in approach"
                    )
                ]
            ),
            ProposalVolume(
                volume_number=2,
                volume_title="Past Performance",
                page_limit=20,
                primary_evaluation_factor="Past Performance",
                sections=[
                    ProposalSection(
                        section_number="2.1",
                        section_title="Relevant Experience",
                        page_allocation=15,
                        content_guidance="Describe 3-5 relevant past contracts"
                    ),
                    ProposalSection(
                        section_number="2.2",
                        section_title="Customer References",
                        page_allocation=5,
                        content_guidance="Provide reference contact information"
                    )
                ]
            ),
            ProposalVolume(
                volume_number=3,
                volume_title="Cost/Price",
                page_limit=None,  # Often no page limit
                primary_evaluation_factor="Cost/Price",
                sections=[
                    ProposalSection(
                        section_number="3.1",
                        section_title="Cost Summary",
                        page_allocation=0,
                        content_guidance="Provide pricing per CLIN structure"
                    )
                ]
            )
        ]

        return volumes
```

### 1.4 Renderer Layer (`src/agents/renderer.py`)

```python
"""
Renderer Layer - Export agent outputs to various formats
"""

import logging
from pathlib import Path
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class Renderer:
    """Export agent outputs to various document formats"""

    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def to_json(self, model: BaseModel, filename: str) -> Path:
        """Export Pydantic model to JSON."""
        output_path = self.output_dir / f"{filename}.json"
        output_path.write_text(model.model_dump_json(indent=2))
        logger.info(f"📄 Exported to JSON: {output_path}")
        return output_path

    def to_docx(self, model: BaseModel, filename: str) -> Path:
        """Export model to Word document."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError("Install python-docx: pip install python-docx")

        output_path = self.output_dir / f"{filename}.docx"
        doc = Document()

        # Handle ProposalOutline specially
        if hasattr(model, 'volumes'):
            self._export_proposal_outline(doc, model)
        else:
            # Generic export
            doc.add_heading(model.__class__.__name__, level=1)
            for field_name, value in model.model_dump().items():
                para = doc.add_paragraph()
                para.add_run(f"{field_name}: ").bold = True
                para.add_run(str(value))

        doc.save(output_path)
        logger.info(f"📝 Exported to Word: {output_path}")
        return output_path

    def _export_proposal_outline(self, doc, outline):
        """Export ProposalOutline to Word document."""
        doc.add_heading(f"Proposal Outline: {outline.rfp_name}", level=1)
        doc.add_paragraph(f"Total Volumes: {outline.total_volumes}")
        doc.add_paragraph(f"Total Page Limit: {outline.total_page_limit}")

        for volume in outline.volumes:
            doc.add_heading(
                f"Volume {volume.volume_number}: {volume.volume_title}",
                level=2
            )
            if volume.page_limit:
                doc.add_paragraph(f"Page Limit: {volume.page_limit}")
            if volume.primary_evaluation_factor:
                doc.add_paragraph(f"Evaluation Factor: {volume.primary_evaluation_factor}")

            for section in volume.sections:
                doc.add_heading(
                    f"{section.section_number} {section.section_title}",
                    level=3
                )
                if section.page_allocation:
                    doc.add_paragraph(f"Pages: {section.page_allocation}")
                if section.content_guidance:
                    doc.add_paragraph(section.content_guidance)
```

---

## Phase 2: Additional Agents (Week 3-4)

### 2.1 SOW Draft Agent

**Purpose**: Generate Statement of Work drafts from STATEMENT_OF_WORK and DELIVERABLE entities.

**Output Model**: `SOWDraft` with sections, deliverables, performance requirements.

### 2.2 Win-Theme Agent

**Purpose**: Identify win themes from STRATEGIC_THEME entities and EVALUATION_FACTOR weights.

**Output Model**: `WinThemeReport` with themes, evidence, differentiation points.

### 2.3 Risk Register Agent

**Purpose**: Identify risks from ambiguous requirements, conflicts, and complexity indicators.

**Output Model**: `RiskRegister` with risk items, likelihood, impact, mitigation.

---

## Phase 3: Complex Agents (Week 5-6)

### 3.1 BOE Agent (Complex - Deferred)

**Purpose**: Generate BOE worksheets with workload classification.

**Why Deferred**: Requires complex classification logic for 7 BOE categories, labor drivers, material/equipment needs. Better to establish patterns with simpler agents first.

**Output Model**: `BOEWorksheet` with categorized requirements.

### 3.2 Past Performance Agent

**Purpose**: Map RFP requirements to contractor past performance categories.

### 3.3 Kickoff Deck Agent

**Purpose**: Generate PowerPoint slides for proposal kickoff meeting.

---

## Implementation Checklist

### Phase 1 Checklist (Week 1-2)

- [ ] Create `src/agents/` directory structure
- [ ] Implement `context.py` (MCP context layer)
- [ ] Implement `base.py` (BaseAgent abstract class)
- [ ] Implement `proposal_outline_agent.py` (proof of concept)
- [ ] Implement `renderer.py` (Export utilities)
- [ ] Add `/agents/proposal-outline` endpoint to routes.py
- [ ] Write tests for Proposal Outline agent
- [ ] Test with MCPP II DRAFT RFP workspace
- [ ] Document API endpoint in README

### Phase 2 Checklist (Week 3-4)

- [ ] Implement `sow_draft_agent.py`
- [ ] Implement `win_theme_agent.py`
- [ ] Implement `risk_register_agent.py`
- [ ] Add corresponding endpoints
- [ ] Write tests for each agent

### Phase 3 Checklist (Week 5-6)

- [ ] Implement `boe_agent.py` (complex classification)
- [ ] Implement `past_performance_agent.py`
- [ ] Implement `kickoff_deck_agent.py`
- [ ] Create PowerPoint templates
- [ ] Integration testing across all agents

---

## Dependencies

### Required (Phase 1)

```bash
# Already installed
pydantic>=2.0
neo4j>=5.0
lightrag-hku

# Add for exports
pip install python-docx
```

### Phase 2+

```bash
pip install openpyxl pandas python-pptx
```

---

## API Reference

### POST /agents/proposal-outline

Generate proposal outline from RFP knowledge graph.

**Parameters**:

- `workspace` (required): Knowledge graph workspace name
- `rfp_name` (optional): Display name for RFP
- `export_format` (optional): "json" or "docx"

**Response** (JSON):

```json
{
  "rfp_name": "MCPP II DRAFT RFP",
  "workspace": "mcpp_drfp_2025",
  "total_volumes": 3,
  "total_page_limit": 70,
  "volumes": [
    {
      "volume_number": 1,
      "volume_title": "Technical Approach",
      "page_limit": 50,
      "sections": [...]
    }
  ]
}
```

---

## Architecture Decision Record: Plain Pydantic vs. PydanticAI

**Decision Date**: October 2025 (reaffirmed December 2025)  
**Status**: Accepted

### Context

Two technologies were evaluated for agent output validation:

| Technology         | Purpose                       | When to Use                            |
| ------------------ | ----------------------------- | -------------------------------------- |
| **Plain Pydantic** | Data validation library       | Output schemas, type enforcement       |
| **PydanticAI**     | Agent orchestration framework | Multi-turn conversations, tool calling |

### Decision

**Use Plain Pydantic NOW, consider PydanticAI LATER.**

### Rationale

**Why Plain Pydantic for Phase 1-3:**

| Feature         | RAG Pipeline      | Agent Framework                 |
| --------------- | ----------------- | ------------------------------- |
| Processing Type | Batch (one-shot)  | Single-request generation       |
| LLM Usage       | Entity extraction | Structured output               |
| Tool Calling    | None              | Simple (graph + vector queries) |
| Conversation    | None              | None (stateless API calls)      |
| **Best Fit**    | Plain Pydantic    | Plain Pydantic                  |

**When to migrate to PydanticAI:**

- ✅ Multi-turn refinement workflows ("make it shorter", "add more detail")
- ✅ Complex tool orchestration (10+ tools with dynamic selection)
- ✅ Agent-to-agent handoffs (orchestrator → specialist agents)
- ✅ Streaming responses with progress feedback

**Current approach (sufficient for Phase 1-3):**

```python
# Simple: LLM generates JSON → Pydantic validates → Export
response = await context.query_rfp(query, mode="hybrid")
outline = ProposalOutline.model_validate_json(response)
renderer.to_docx(outline, "proposal_outline")
```

**Future approach (when complexity warrants):**

```python
# Complex: PydanticAI orchestrates multi-step refinement
result = await outline_agent.run(
    "Create outline, then refine based on user feedback",
    deps=AgentDependencies(lightrag=rag, neo4j=graph)
)
```

### Consequences

- **PRO**: Simpler implementation, fewer dependencies
- **PRO**: Pydantic already in dependencies (zero cost)
- **PRO**: Easy to migrate later (Pydantic models remain the same)
- **CON**: No multi-turn refinement in Phase 1-3
- **MITIGATION**: Add PydanticAI in Phase 4 if user feedback indicates need

---

## Next Steps

1. **Create GitHub Issue**: #29 - RFP Agent Framework Implementation
2. **Create branch**: `git checkout -b 029-rfp-agent-framework`
3. **Implement Phase 1**: context.py, base.py, proposal_outline_agent.py, renderer.py
4. **Test with MCPP workspace**: Validate agent produces useful output
5. **Review**: Get feedback before Phase 2

---

**Document Status**: DRAFT - Ready for Review  
**Estimated Effort**: 80-120 hours total (3-6 weeks)  
**Priority**: HIGH - Foundation for capture deliverable automation
