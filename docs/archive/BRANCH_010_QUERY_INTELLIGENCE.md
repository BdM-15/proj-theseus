# Branch 010: Query-Time Intelligence - Phase 1 (Core Prompts)

**Date**: January 23, 2025  
**Branch**: `010-query-prompts-integration` (ACTIVE)  
**Goal**: Implement 4 core user query prompts for Shipley-based capture intelligence  
**Scope**: Phase 1 ONLY - Defer intent classification and multi-agent synthesis to future branches

---

## 🎯 **Overview**

Branch 009 established the **extraction foundation** (17 entity types, 4 concatenated prompts, entity deduplication). Branch 010 Phase 1 adds **4 essential query prompts** that transform the knowledge graph into actionable capture intelligence.

**Core Innovation**: LightRAG's `user_prompt` parameter allows injecting domain-specific prompts AFTER retrieval but BEFORE LLM response generation, enabling specialized analysis without affecting retrieval quality.

**Phase 1 Scope** (This Branch):

- ✅ Create `prompts/user_queries/` directory structure
- ✅ Implement 4 core prompts (compliance, QFG, win themes, proposal outline)
- ✅ Update `prompt_loader.py` to support user_queries category
- ✅ Test with existing LightRAG `/query` endpoint
- ✅ Document usage patterns and examples

**Deferred to Future Branches**:

- ⏸️ Phase 2: Intent classification and auto-routing
- ⏸️ Phase 3: Advanced specialized prompts
- ⏸️ Phase 4: Multi-agent synthesis orchestration

---

## 🏗️ **Architecture Pattern**

### **Two-Stage Intelligence System**

```
STAGE 1: EXTRACTION (Branch 009 ✅)
├── Document Upload → RAG-Anything (MinerU parser)
├── Entity Extraction → 17 specialized types with 4 prompts
├── Relationship Inference → 6 LLM algorithms
└── Knowledge Graph → Structured ontology storage

STAGE 2: QUERY-TIME INTELLIGENCE (Branch 010 🎯)
├── User Query → "Generate proposal outline"
├── Intent Classification → Route to appropriate prompt
├── Knowledge Retrieval → Standard LightRAG retrieval
├── Prompt Injection → user_prompt parameter with capture intelligence
└── Specialized Response → Shipley methodology applied to retrieved context
```

### **How user_prompt Works**

```python
# From LightRAG base.py
user_prompt: str | None = None
"""User-provided prompt for the query.
Addition instructions for LLM. If provided, this will be inject into the prompt template.
It's purpose is the let user customize the way LLM generate the response.
"""

# Usage pattern
from lightrag.base import QueryParam

compliance_prompt = load_prompt("user_queries/compliance_assessment")

query_param = QueryParam(
    mode="hybrid",
    user_prompt=compliance_prompt  # Injected AFTER retrieval
)

response = await rag.aquery(
    "What are the evaluation factors?",
    param=query_param
)
# Result: Retrieved entities/relationships + Shipley compliance scoring
```

**Key Benefits**:

- ✅ Does NOT affect retrieval (query text stays pure)
- ✅ Controls response format and analysis approach
- ✅ Can inject 10K+ token prompts (1% of 2M context)
- ✅ Modular prompt library (easy to test/update)

---

## 📋 **Implementation Tasks (Phase 1 Only)**

### **Task 1: Directory Structure Setup**

**Goal**: Create organized prompt storage with clear separation of concerns

**Actions**:

```powershell
# Create user queries directory
New-Item -ItemType Directory -Path prompts/user_queries -Force

# Verify directory structure
Get-ChildItem -Path prompts -Directory
# Expected output:
#   extraction/
#   relationship_inference/
#   user_queries/  ← NEW
```

**Deliverable**: `prompts/user_queries/` directory exists

---

### **Task 2: Core Query Prompts Implementation**

**Goal**: Implement 4 essential capture intelligence prompts

#### **1.1 Compliance Assessment** (`user_queries/compliance_assessment.md`)

**Based on**: `docs/archive/prompts_branch_002/assess_compliance_prompt.txt`

**Input**: Proposal draft sections + RFP requirements  
**Output**: Shipley 0-100 scoring with gap analysis

**Capabilities**:

- 4-level compliance scale (Compliant/Partial/Non-Compliant/Not Addressed)
- Coverage scoring: 0/10/30/50/70/85/95/100 with rationale
- Gap detection: Missing requirements, incomplete responses
- Page limit compliance: Check against Section L instructions
- Evidence mapping: Proposal page references for each requirement

**Example Query**:

```python
query = "Assess compliance of our technical approach draft against Section C requirements"
user_prompt = load_prompt("user_queries/compliance_assessment")
```

---

#### **1.2 Questions for Government (QFG)** (`user_queries/generate_qfg.md`)

**Based on**: `docs/archive/prompts_branch_002/generate_qfg_prompt.txt`

**Input**: RFP knowledge graph  
**Output**: 5-7 high-impact clarification questions

**Capabilities**:

- Ambiguity detection: Conflicting requirements, unclear scope boundaries
- Conflict identification: Section L vs M misalignments, contradictory clauses
- Scope gaps: Missing performance standards, undefined deliverables
- Strategic value assessment: Which questions shape RFP favorably
- Q&A period identification: Deadline for submission (Section A/L)

**Example Query**:

```python
query = "Generate questions for government to clarify ambiguities in Section C and evaluation criteria"
user_prompt = load_prompt("user_queries/generate_qfg")
```

---

#### **1.3 Win Theme Identification** (`user_queries/win_theme_identification.md`)

**Based on**: Shipley Capture Guide win strategy patterns

**Input**: RFP knowledge graph + evaluation factors  
**Output**: Strategic themes and discriminators

**Capabilities**:

- Hot button detection: High-priority evaluation criteria (Section M weights)
- Discriminator opportunities: Areas to differentiate from competitors
- Proof point requirements: Evidence needed to substantiate themes
- Theme placement: Which proposal sections to emphasize themes
- Risk assessment: Requirements that expose weaknesses

**Example Query**:

```python
query = "Identify win themes and discriminators based on evaluation factors"
user_prompt = load_prompt("user_queries/win_theme_identification")
```

---

#### **1.4 Proposal Outline Generation** (`user_queries/proposal_outline_generation.md`) ⭐

**NEW - Critical capture intelligence capability**

**Input**: RFP knowledge graph (Section L + M + requirements)  
**Output**: Complete proposal outline with compliance checklist

**Capabilities**:

- Volume structure: Page limits per volume from Section L
- Content mapping: Outline sections → Evaluation factors (Section M)
- Weight-based page allocation: Proportional to evaluation percentages
- Must-address requirements: Checklist per section (must/should/may)
- Strategic guidance: Win theme placement, hot buttons, proof points
- Compliance verification: Deliverables, clauses, certifications per section
- Format requirements: Font, margins, submission instructions

**Output Structure**:

```markdown
# Proposal Outline: [RFP Title]

## Volume I: Technical Approach (25 pages max, 40% weight)

### 1. Understanding of Requirements (8 pages recommended)

**Evaluation Factor**: Technical Understanding (15% weight)
**Evaluation Standard**: Exceptional = demonstrates deep understanding

**Must Address**:

- [ ] REQUIREMENT_001: Weekly status reports (Must have)
- [ ] REQUIREMENT_015: CLIN 0001 services description
- [ ] DELIVERABLE_003: Technical approach document

**Strategic Opportunities**:

- Highlight past performance with similar programs
- Demonstrate understanding of mission-critical challenges
- Reference expertise in [specific domain]

**Page Allocation**: 8 pages (32% of volume, aligned with 15% weight)

---

### 2. Technical Solution (12 pages recommended)

[... similar structure for each section ...]
```

**Example Query**:

```python
query = "Generate complete proposal outline with page allocations and compliance checklist"
user_prompt = load_prompt("user_queries/proposal_outline_generation")
```

**Why This Is Critical**:

- ✅ Automates manual cross-referencing of Section L, M, and C
- ✅ Ensures compliance with all submission instructions
- ✅ Optimizes page allocation based on evaluation weights
- ✅ Provides must-address checklist for writers
- ✅ Embeds strategic guidance (win themes, hot buttons)
- ✅ Saves 10-20 hours of manual outline development

**Deliverable**: 4 prompt files in `prompts/user_queries/`

---

### **Task 3: Prompt Loader Enhancement**

**Goal**: Enable `prompt_loader.py` to load user query prompts

**Current Implementation** (`src/core/prompt_loader.py`):

```python
def load_prompt(prompt_name: str, category: str = "extraction") -> str:
    """
    Load prompt template from prompts/ directory

    Args:
        prompt_name: Name of prompt file (with or without .md extension)
        category: Subdirectory ('extraction', 'relationship_inference')
    """
```

**Required Change**:

```python
def load_prompt(prompt_name: str, category: str = "extraction") -> str:
    """
    Load prompt template from prompts/ directory

    Args:
        prompt_name: Name of prompt file (with or without .md extension)
        category: Subdirectory ('extraction', 'relationship_inference', 'user_queries')
    """
    # Add validation for user_queries category
    VALID_CATEGORIES = ["extraction", "relationship_inference", "user_queries"]
    if category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category: {category}. Must be one of {VALID_CATEGORIES}")

    # Rest of implementation remains unchanged
```

**Deliverable**: `prompt_loader.py` updated with `user_queries` category support

---

### **Task 4: Testing and Documentation**

**Goal**: Validate prompts work with existing LightRAG `/query` endpoint

**Test Script** (`tests/test_user_prompts.py`):

```python
"""
Test user query prompts with LightRAG
Phase 1: Manual testing via existing /query endpoint
"""
import asyncio
from lightrag.base import QueryParam
from src.core.prompt_loader import load_prompt

async def test_compliance_assessment():
    """Test compliance assessment prompt"""
    prompt = load_prompt("compliance_assessment", category="user_queries")

    # Simulate API call to existing /query endpoint
    import requests
    response = requests.post(
        "http://localhost:9621/query",
        json={
            "query": "What are the evaluation factors and their weights?",
            "mode": "hybrid",
            "user_prompt": prompt
        }
    )

    print("Compliance Assessment Response:")
    print(response.json())

    # Validate response format (should include Shipley scoring)
    assert "compliance" in response.text.lower()
    assert "score" in response.text.lower()

async def test_proposal_outline():
    """Test proposal outline generation prompt"""
    prompt = load_prompt("proposal_outline_generation", category="user_queries")

    response = requests.post(
        "http://localhost:9621/query",
        json={
            "query": "Generate complete proposal outline with page allocations",
            "mode": "hybrid",
            "user_prompt": prompt
        }
    )

    print("Proposal Outline Response:")
    print(response.json())

    # Validate response format (should include page limits, sections)
    assert "page" in response.text.lower()
    assert "section" in response.text.lower()

if __name__ == "__main__":
    asyncio.run(test_compliance_assessment())
    asyncio.run(test_proposal_outline())
```

**Usage Documentation** (`prompts/user_queries/README.md`):

````markdown
# User Query Prompts - Usage Guide

## Overview

User query prompts enable specialized capture intelligence analysis by injecting
domain-specific instructions into LightRAG queries AFTER retrieval but BEFORE
LLM response generation.

## Available Prompts (Phase 1)

### 1. Compliance Assessment (`compliance_assessment.md`)

**Purpose**: Shipley-based compliance scoring of proposal drafts  
**Input**: Proposal section + RFP requirements  
**Output**: 0-100 scoring with gap analysis

**Example Usage**:

```bash
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Assess compliance of our technical approach against Section C requirements",
    "mode": "hybrid",
    "user_prompt": "$(cat prompts/user_queries/compliance_assessment.md)"
  }'
```
````

### 2. Questions for Government (`generate_qfg.md`)

**Purpose**: Identify ambiguities and conflicts requiring clarification  
**Input**: RFP knowledge graph  
**Output**: 5-7 high-impact questions with RFP citations

### 3. Win Theme Identification (`win_theme_identification.md`)

**Purpose**: Strategic opportunity analysis based on evaluation factors  
**Input**: RFP knowledge graph + evaluation criteria  
**Output**: Discriminators, hot buttons, proof point requirements

### 4. Proposal Outline Generation (`proposal_outline_generation.md`) ⭐

**Purpose**: Complete proposal structure with compliance checklist  
**Input**: Section L + M + requirements  
**Output**: Page allocations, must-address checklist, strategic guidance

## Integration with Existing Systems

### Python Client

```python
from lightrag.base import QueryParam
from src.core.prompt_loader import load_prompt

# Load specialized prompt
compliance_prompt = load_prompt("compliance_assessment", category="user_queries")

# Execute query with specialized analysis
query_param = QueryParam(mode="hybrid", user_prompt=compliance_prompt)
response = await rag_instance.lightrag.aquery(
    "What are the evaluation factors?",
    param=query_param
)
```

### REST API

```bash
# Requires reading prompt file content into request
PROMPT=$(cat prompts/user_queries/compliance_assessment.md)

curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"What are the evaluation factors?\",
    \"mode\": \"hybrid\",
    \"user_prompt\": \"$PROMPT\"
  }"
```

## Cost Estimates

**Per Query**:

- User Query: 50 tokens
- Retrieved Context: 5,000 tokens (entities + relationships + chunks)
- User Prompt: 2,000 tokens (specialized instructions)
- LLM Response: 1,000 tokens

**Total**: ~$0.008 per specialized query (Grok-beta pricing)

**Comparison**:

- RFP Ingestion: $0.042 (one-time)
- 100 specialized queries: $0.80 (ongoing analysis)
- **Total project cost**: ~$1.00 for comprehensive capture intelligence

## Future Enhancements (Deferred)

- ⏸️ **Auto-routing**: Intent classification to select appropriate prompt automatically
- ⏸️ **Advanced prompts**: Page allocation optimizer, section analyzer, proof points mapper
- ⏸️ **Multi-agent synthesis**: Orchestrate multiple prompts for comprehensive reports

See `docs/archive/BRANCH_010_QUERY_INTELLIGENCE.md` for full roadmap.

````

**Deliverable**: Test script + usage documentation completed

---

## 🚀 **Phase 1 Implementation Checklist**

### Setup (Day 1)
- [ ] Create `prompts/user_queries/` directory
- [ ] Update `src/core/prompt_loader.py` with user_queries category
- [ ] Create `prompts/user_queries/README.md` usage guide

### Prompt Development (Days 2-4)
- [ ] **Priority 1**: `proposal_outline_generation.md` (highest ROI)
- [ ] **Priority 2**: `compliance_assessment.md` (Shipley scoring)
- [ ] **Priority 3**: `generate_qfg.md` (customer shaping)
- [ ] **Priority 4**: `win_theme_identification.md` (strategic analysis)

### Testing (Day 5)
- [ ] Test each prompt with existing `/query` endpoint
- [ ] Validate response formats match expected outputs
- [ ] Document actual vs expected costs
- [ ] Create example queries for each prompt type

### Documentation (Day 5)
- [ ] Complete usage guide with curl/Python examples
- [ ] Document integration patterns
- [ ] Update main README.md with Phase 1 capabilities

---

## 📊 **Success Criteria (Phase 1)**

✅ **Functional Requirements**:
- 4 prompt files created and tested
- `prompt_loader.py` supports `user_queries` category
- All prompts work with existing LightRAG `/query` endpoint
- Documentation enables users to execute specialized queries

✅ **Quality Requirements**:
- Proposal outline generates complete structure with page allocations
- Compliance assessment produces Shipley-compatible 0-100 scoring
- QFG identifies 5-7 high-impact questions with citations
- Win themes align with evaluation factor weights

✅ **Cost Requirements**:
- Per-query cost <$0.01 (measured via actual usage)
- No increase to ingestion costs
- No performance degradation for standard queries

---

## 🔄 **Deferred to Future Branches**

### Branch 011 (Future): Intent Classification & Auto-Routing

**Scope**: Lightweight intent classification for automatic prompt routing

**Key Features**:

```python
# Intent classification prompt (100 tokens, $0.0001 cost)
intent_classifier_prompt = """
Classify this government contracting query into ONE category:
- compliance_assessment: Checking proposal against requirements
- generate_qfg: Finding ambiguities/conflicts in RFP
- win_themes: Identifying strategic opportunities
- proposal_outline: Generating proposal structure with page limits
- requirement_analysis: Understanding must/should/may obligations
- general: Standard information retrieval

Query: "{query}"
Category:
"""

# Implementation
async def classify_intent(query: str) -> str:
    """Quick LLM call to classify query intent (~$0.0001)"""
    response = await lightweight_llm_call(
        intent_classifier_prompt.format(query=query)
    )
    return response.strip().lower()

async def intelligent_query(query: str, mode: str = "hybrid"):
    """Route query to appropriate prompt based on intent"""
    intent = await classify_intent(query)

    # Load appropriate prompt
    if intent == "general":
        user_prompt = None  # Default LightRAG behavior
    else:
        user_prompt = load_prompt(f"user_queries/{intent}")

    # Execute query with specialized prompt
    query_param = QueryParam(mode=mode, user_prompt=user_prompt)
    return await rag.aquery(query, param=query_param)
````

**Why Deferred**: Phase 1 testing will reveal actual query patterns and whether
auto-routing provides sufficient value vs manual prompt selection.

---

### Branch 012 (Future): Advanced Query Prompts

**Scope**: Additional specialized prompts based on Phase 1 usage patterns

**Candidate Prompts**:

#### Page Allocation Optimizer

- **Input**: Page limit + evaluation factors with weights
- **Output**: Optimal page distribution per section
- **Use case**: "How should I allocate 25 technical pages?"

#### Section Requirements Analyzer

- **Input**: Specific proposal section (e.g., "Management Approach")
- **Output**: Must-address checklist, evaluation criteria, page limits
- **Use case**: "What must I address in Management Approach?"

#### Critical Theme Analysis

- **Input**: Full RFP knowledge graph
- **Output**: High-priority issues requiring attention
- **Use case**: "What are the critical themes I need to address?"

#### Proof Points Mapper

- **Input**: Win themes + evaluation factors
- **Output**: Evidence requirements per theme
- **Use case**: "What proof points do I need for our discriminators?"

**Why Deferred**: Phase 1 will reveal which specialized analyses provide most value.
User feedback will drive priority order for advanced prompts.

---

### Branch 013 (Future): Multi-Agent Synthesis Orchestration

**Scope**: Orchestrate multiple specialized prompts for comprehensive analysis

**Architecture Considerations**:

- Parallel vs sequential query execution
- Context sharing between queries
- Result synthesis patterns
- Cost optimization strategies

**Why Deferred**: Significant architectural complexity. Requires clear user demand
for synthesized reports vs individual analyses. Consider PydanticAI framework
(already documented in `docs/agents/`) if this capability is needed.

**Example Pattern** (if implemented):

```python
# Parallel execution pattern
results = await asyncio.gather(
    query_with_prompt(query, "compliance_assessment"),
    query_with_prompt(query, "generate_qfg"),
    query_with_prompt(query, "win_themes"),
    query_with_prompt(query, "proposal_outline"),
)

# Synthesis logic
synthesized_report = synthesize_capture_intelligence(results)
```

---

## 🔧 **Phase 1 Technical Details**

### **Directory Structure (Final State)**

```
prompts/
├── entity_extraction/          # INGESTION-TIME (Branch 009 ✅)
│   ├── entity_extraction_prompt.md (1,460 lines)
│   ├── entity_detection_rules.md (1,103 lines)
│   ├── section_normalization.md (321 lines)
│   └── metadata_extraction.md (554 lines)
├── relationship_inference/     # POST-PROCESSING (Branch 009 ✅)
│   ├── document_section_linking.md
│   ├── clause_clustering.md
│   ├── instruction_evaluation_linking.md
│   ├── requirement_evaluation.md
│   ├── sow_deliverable_linking.md
│   └── system_prompt.md
└── user_queries/              # QUERY-TIME (Branch 010 🎯 NEW)
    ├── compliance_assessment.md
    ├── generate_qfg.md
    ├── win_theme_identification.md
    ├── proposal_outline_generation.md  ⭐
    ├── page_allocation_optimizer.md
    ├── section_requirements_analyzer.md
    ├── critical_theme_analysis.md
    └── proof_points_mapper.md
```

### **API Endpoint Design**

```python
# New intelligent query endpoint
@router.post("/query/intelligent")
async def intelligent_query_endpoint(
    query: str,
    query_type: Optional[str] = None,  # Explicit type or auto-classify
    mode: str = "hybrid",
    auto_classify: bool = True
):
    """
    Intelligent query with automatic prompt routing

    Args:
        query: User question
        query_type: Optional explicit prompt type
        mode: LightRAG mode (hybrid/local/global/mix)
        auto_classify: Use intent classification if query_type not provided
    """
    if query_type:
        # Explicit prompt selection
        user_prompt = load_prompt(f"user_queries/{query_type}")
    elif auto_classify:
        # Automatic intent classification
        intent = await classify_intent(query)
        user_prompt = load_prompt(f"user_queries/{intent}") if intent != "general" else None
    else:
        # Standard LightRAG query
        user_prompt = None

    query_param = QueryParam(mode=mode, user_prompt=user_prompt)
    response = await rag_instance.aquery(query, param=query_param)

    return {
        "query": query,
        "intent": intent if auto_classify else query_type,
        "response": response,
    }
```

---

## 📊 **Success Metrics**

### **Phase 1 Success Criteria**

- ✅ 4 core prompts implemented and tested
- ✅ Proposal outline generates complete structure with page allocations
- ✅ Compliance assessment produces Shipley-compatible scoring
- ✅ QFG identifies 5-7 high-impact questions
- ✅ Win themes align with evaluation factor weights

### **Phase 2 Success Criteria**

- ✅ Intent classification accuracy >80%
- ✅ Automatic routing reduces user friction
- ✅ Explicit query type override works correctly
- ✅ Cost per query <$0.01 (classification + response)

### **Phase 3 Success Criteria**

- ✅ Advanced prompts provide specialized analysis
- ✅ Page allocation matches evaluation weights
- ✅ Section analyzer produces actionable checklists

### **Phase 4 Success Criteria**

- ✅ Multi-agent synthesis produces coherent reports
- ✅ Sequential chaining maintains context across stages
- ✅ Comprehensive analysis completes in <60 seconds

---

## 🚀 **Getting Started (Phase 1 Implementation)**

### Prerequisites

- ✅ Branch 009 merged to main (17 entity types, semantic extraction)
- ✅ Working RAG-Anything + LightRAG server
- ✅ Test RFP processed with full knowledge graph

### Day 1: Setup

```powershell
# 1. Ensure on correct branch
git checkout 010-query-prompts-integration
git pull origin 010-query-prompts-integration

# 2. Create directory structure
New-Item -ItemType Directory -Path prompts/user_queries -Force

# 3. Verify setup
Get-ChildItem -Path prompts -Directory
# Expected: extraction/, relationship_inference/, user_queries/
```

### Days 2-4: Prompt Development

**Priority Order** (implement in this sequence):

1. **Day 2**: `proposal_outline_generation.md`

   - Highest ROI (saves 10-20 hours per RFP)
   - Source: Capture manager prompts Query 3.1
   - Test query: "Generate proposal outline with page allocations"

2. **Day 3**: `compliance_assessment.md`

   - Source: `docs/archive/prompts_branch_002/assess_compliance_prompt.txt`
   - Adapt for post-retrieval context
   - Test query: "Assess compliance of technical approach against requirements"

3. **Day 4 AM**: `generate_qfg.md`

   - Source: `docs/archive/prompts_branch_002/generate_qfg_prompt.txt`
   - Focus on ambiguity detection
   - Test query: "What questions should we ask the government?"

4. **Day 4 PM**: `win_theme_identification.md`
   - Source: Shipley Capture Guide patterns
   - Focus on discriminator identification
   - Test query: "Identify win themes based on evaluation factors"

### Day 5: Testing & Documentation

```powershell
# 1. Test each prompt
python tests/test_user_prompts.py

# 2. Validate cost per query
# Expected: ~$0.008 per specialized query

# 3. Complete usage guide
# Edit: prompts/user_queries/README.md

# 4. Update main documentation
# Edit: README.md (add Phase 1 capabilities section)
```

---

## 🎯 **Phase 1 Priority Order**

**Implementation Sequence**:

1. 🔥 **Day 2**: Proposal outline generation (saves 10-20 hours per RFP)
2. 🔥 **Day 3**: Compliance assessment (Shipley methodology validation)
3. 🟡 **Day 4 AM**: QFG generation (customer shaping opportunity)
4. 🟡 **Day 4 PM**: Win theme identification (strategic differentiation)
5. ✅ **Day 5**: Testing + documentation

**Deferred to Future Branches**:

- ⏸️ Intent classification (Branch 011)
- ⏸️ Advanced prompts (Branch 012)
- ⏸️ Multi-agent synthesis (Branch 013)

---

## 📚 **References**

### **LightRAG Documentation**

- `QueryParam.user_prompt` parameter: https://github.com/HKUDS/LightRAG
- Prompt injection pattern: `lightrag/operate.py` line 2863-2878

### **Branch 002 Historical Artifacts**

- `docs/archive/prompts_branch_002/assess_compliance_prompt.txt`
- `docs/archive/prompts_branch_002/generate_qfg_prompt.txt`
- `docs/archive/prompts_branch_002/shipley_requirements_extraction.txt`
- `examples/sample_qfg.json`
- `examples/sample_compliance_assessment.json`

### **Shipley Methodology**

- Capture Guide: Compliance scoring scales
- Proposal Guide: Win theme development
- Evaluation matrices: Page allocation strategies

---

**Status**: � **READY TO START - Branch 009 merged, Branch 010 created**

**Current State**:

- ✅ Branch 009 merged to main (99.8% coverage, 0 forbidden types)
- ✅ Branch 010 created: `010-query-prompts-integration`
- ✅ Directory structure in place: `prompts/query/`, `prompts/user_queries/`
- ✅ Query library documented: `prompts/user_queries/capture_manager_prompts.md` (11 categories, 40+ queries)
- ✅ Architecture documented: `prompts/query/README.md`

**What Exists**:

1. `prompts/query/metadata_enrichment.md` - Metadata extraction prompt (moved from extraction/)
2. `prompts/query/README.md` - Architecture and usage patterns
3. `prompts/user_queries/capture_manager_prompts.md` - Comprehensive query library with examples

**What's Needed** (Priority Order):

1. 🔥 Implement QueryParam.user_prompt integration in `/query` endpoint
2. 🔥 Create proposal_outline_generator.md (convert Query 3.1 to user_prompt format)
3. 🔥 Create compliance_assessment.md (convert Query 4.1 to user_prompt format)
4. 🟡 Create questions_for_government.md (convert Query 7.2 to user_prompt format)
5. 🟡 Create win_themes_analyzer.md (convert Query 2.2 to user_prompt format)
6. 🟢 Implement intent_classifier.md for automatic routing
