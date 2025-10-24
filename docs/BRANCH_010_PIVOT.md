# Branch 010 Strategic Pivot - Output Prompts Abandoned

**Date**: October 23, 2025  
**Decision**: Abandon output prompt templates, revert to natural query flow  
**Reason**: Output prompts kill strategic reasoning depth in exploratory queries

---

## The Problem

**Attempt**: Implement structured output prompts for proposal outline generation  
**Result**: Responses became "bland" - lost strategic insights, competitive intelligence, and persuasive language

### Example Comparison

**BEFORE Output Prompts** (Strategic):

> "To gain favor in award decision, emphasize executable strategies exceeding SOW requirements... Directly target shipboard staffing (C.7) with innovative afloat phase solutions, earning Outstanding rating in Factor B... Position these as low-risk, high-efficiency approaches demonstrating exceptional understanding..."

**AFTER Output Prompts** (Bland):

> "Provide a concise narrative summary of the entire proposal... Detail management principles/practices for MCPP adherence... Include all required documents..."

### Root Cause

Output prompts forced **rigid formatting** that:

- Prioritized structure over strategic reasoning
- Triggered compliance-focused language
- Lost competitive intelligence insights
- Constrained LLM's natural synthesis capabilities

---

## The Fundamental Insight

**WebUI Queries ≠ Agent Deliverables**

| Use Case                      | Right Approach               | Wrong Approach               |
| ----------------------------- | ---------------------------- | ---------------------------- |
| **Exploratory Query** (WebUI) | Raw LLM reasoning over KG    | Structured output prompts ❌ |
| **Structured Deliverable**    | PydanticAI agent + templates | Prompt engineering ❌        |

**WebUI users** (capture managers) need:

- Strategic insights ("target this pain point to win")
- Competitive intelligence ("40% weight → allocate accordingly")
- Flexible reasoning ("this approach scores Outstanding because...")

**Agent users** (deliverable generation) need:

- Type-safe data models (Pydantic validation)
- Deterministic formatting (Excel, Word, PDF)
- Tool integration (file creation, API calls)

---

## What Worked in Branch 010

### ✅ Enhanced Extraction Prompts

**Location**: `prompts/extraction/entity_extraction_prompt.md`  
**Status**: **KEEP** - Working excellently

**Results**:

- 4,394 entities extracted (vs 2,974 baseline)
- **17 government contracting entity types** (organization, concept, event, technology, person, location, requirement, clause, section, document, deliverable, program, equipment, evaluation_factor, submission_instruction, strategic_theme, statement_of_work)
- Phase 6 inference: 1,193+ semantic relationships
- 81 evaluation_factor, 184 requirement, 16 submission_instruction entities

**Key Innovation**: Ontology-based extraction with domain-specific entity types (REQUIREMENT, CLAUSE, EVALUATION_FACTOR, etc.)

### ✅ Knowledge Graph Storage

**Location**: `rag_storage/default/graph_chunk_entity_relation.graphml`  
**Status**: **KEEP** - Core system component

**Results**:

- 6.1MB GraphML with rich entity/relationship data
- Phase 6 relationships: EVALUATED_BY (31), GUIDES (70), ATTACHMENT_OF (1)
- Enables semantic queries: "What requirements are evaluated by Factor M.1?"

### ✅ Test Query Framework

**Location**: `test_queries_live.py`  
**Status**: **KEEP** - Validation infrastructure

**Results**:

- Test 1 (Compliance Checklist): 39.94s, comprehensive 30-requirement output
- Demonstrates query quality without output prompts
- Validates Phase 6 relationship intelligence

---

## What Failed in Branch 010

### ❌ Output Prompt Templates

**Location**: `prompts/user_queries/*.md`  
**Status**: **DELETE** (except README.md)

**Files to Remove**:

- `proposal_outline_generation.md` - Rigid template killing strategic depth
- `compliance_checklist.md` - Structured format constraints
- `compliance_assessment.md` - Format over reasoning
- `generate_qfg.md` - Loss of strategic language
- `win_theme_identification.md` - Bland output

**Why They Failed**:

1. Forced structure at expense of strategic reasoning
2. Triggered compliance-speak over competitive intelligence
3. LLMs excel at synthesis, not rigid formatting
4. Wrong abstraction layer for exploratory queries

### ❌ Structured Response Formatting

**Problem**: Trying to get LLM to generate checklists, matrices, outlines in markdown  
**Reality**: LLMs are bad at precise formatting, good at reasoning

**Better Approach** (Future):

- LLM generates **insights** (strategic reasoning)
- PydanticAI agent generates **deliverables** (Excel, Word, PDF)
- Separation of concerns: reasoning vs formatting

---

## The Path Forward

### Immediate: Revert to Natural Query Flow

1. **Delete output prompts**:

   ```bash
   Remove-Item prompts\user_queries\*.md -Exclude README.md
   ```

2. **Keep extraction prompts**:

   - `entity_extraction_prompt.md` ✅
   - `relationship_inference/` prompts ✅

3. **Test queries with NO constraints**:
   - Baseline: "before" response (strategic depth)
   - Validate: Same query quality without output prompts

### Future: Agent Architecture (Branch 011+)

**When structured deliverables needed**, use proper agent tooling:

```python
# Example: Compliance Checklist Agent
from pydantic_ai import Agent
from pydantic import BaseModel

class ComplianceChecklist(BaseModel):
    requirement_id: str
    description: str
    criticality: Literal["MANDATORY", "IMPORTANT", "OPTIONAL"]
    section_origin: str
    evaluation_factor: str
    proof_points: list[str]

agent = Agent("openai:gpt-4", result_type=list[ComplianceChecklist])

@agent.tool
async def query_requirements(rfp_id: str) -> list[dict]:
    """Query GraphML for MANDATORY requirements"""
    return await graphml_query(
        "MATCH (r:REQUIREMENT {criticality: 'MANDATORY'}) RETURN r"
    )

# Generate Excel with validated data
checklist = await agent.run(f"Generate compliance checklist for {rfp_id}")
export_to_excel(checklist, "outputs/compliance_checklist.xlsx")
```

**Benefits**:

- Type safety (Pydantic validation)
- Structured output (Excel, Word, PDF)
- Tool integration (file I/O, API calls)
- Deterministic results (same input → same format)

---

## Lessons Learned

### 1. Match Abstraction to Use Case

**Exploratory Queries** (WebUI):

- Natural language input
- Flexible reasoning output
- Strategic insights over structure

**Deliverable Generation** (Agents):

- Typed data models
- Validated formatting
- File outputs (Excel, Word, PDF)

### 2. LLM Strengths vs Weaknesses

**LLMs Excel At**:

- Semantic reasoning
- Strategic synthesis
- Competitive intelligence
- Natural language persuasion

**LLMs Struggle With**:

- Precise formatting (tables, checklists)
- Deterministic structure (same format every time)
- Data validation (type checking, constraints)

### 3. Prompt Engineering Limits

**Good For**:

- Domain knowledge injection
- Entity/relationship extraction
- Query refinement

**Bad For**:

- Forcing rigid output formats
- Constraining creative reasoning
- Replacing proper tooling (agents, parsers)

---

## Branch 010 Final Status

### Achievements

✅ Enhanced extraction with **17 govcon entity types**  
✅ Phase 6 inference with 1,193+ semantic relationships  
✅ 4,394 entities extracted (Navy MBOS RFP)  
✅ Test query framework validating system quality

### Abandoned

❌ Output prompt templates (killed strategic depth)  
❌ Structured response formatting (wrong abstraction)  
❌ Markdown-based deliverable generation (LLM weakness)

### Handoff to Branch 011

**Focus**: Agent architecture for deliverable generation  
**Approach**: PydanticAI agents with type-safe data models  
**Goal**: GraphML → Excel/Word/PDF pipeline with validation

**See**: `docs/agents/PYDANTICAI_DECISION_SUMMARY.md` for agent architecture  
**See**: `docs/agents/FUTURE_AGENT_ARCHITECTURE.md` for roadmap

---

## References

- **Original Issue**: User query response "bland" after output prompts added
- **Root Cause**: Output prompts constrained LLM strategic reasoning
- **Decision**: Abandon output prompts, focus on natural query flow
- **Future Work**: PydanticAI agents for structured deliverables

**Last Updated**: October 23, 2025
