# Branch 010: Query-Time Intelligence Layer

**Date**: January 23, 2025  
**Branch**: `010-query-time-intelligence` (NOT YET CREATED)  
**Goal**: Implement query-time intelligence using LightRAG's `user_prompt` parameter for Shipley-based capture intelligence

---

## 🎯 **Overview**

Branch 009 established the **extraction foundation** (17 entity types, 4 concatenated prompts, entity deduplication). Branch 010 adds the **query-time intelligence layer** that transforms the knowledge graph into actionable capture intelligence.

**Core Innovation**: LightRAG's `user_prompt` parameter allows injecting domain-specific prompts AFTER retrieval but BEFORE LLM response generation, enabling specialized analysis without affecting retrieval quality.

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

## 📋 **Implementation Phases**

### **Phase 1: Core Query Prompts** (Immediate - Week 1)

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

---

### **Phase 2: Intent Classification** (Week 2)

**Goal**: Automatic routing to appropriate prompt based on query text

#### **2.1 Lightweight Intent Classifier**

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
```

**Benefits**:

- Automatic prompt selection
- No user training required
- Minimal cost (~$0.0001 per query)
- Fallback to general queries if intent unclear

---

#### **2.2 Explicit Query Type Parameter**

For users who want control:

```python
# API endpoint with explicit type
POST /query
{
    "query": "What are Section M evaluation factors?",
    "query_type": "compliance_assessment",  # Optional explicit control
    "mode": "hybrid"
}

# Backend routing
if query_type:
    user_prompt = load_prompt(f"user_queries/{query_type}")
else:
    # Use intent classification
    intent = await classify_intent(query)
    user_prompt = load_prompt(f"user_queries/{intent}")
```

---

### **Phase 3: Advanced Query Prompts** (Week 3)

Additional specialized prompts for power users:

#### **3.1 Page Allocation Optimizer** (`user_queries/page_allocation_optimizer.md`)

- Input: Page limit + evaluation factors with weights
- Output: Optimal page distribution per section
- Use case: "How should I allocate 25 technical pages?"

#### **3.2 Section Requirements Analyzer** (`user_queries/section_requirements_analyzer.md`)

- Input: Specific proposal section (e.g., "Management Approach")
- Output: Must-address checklist, evaluation criteria, page limits
- Use case: "What must I address in Management Approach?"

#### **3.3 Critical Theme Analysis** (`user_queries/critical_theme_analysis.md`)

- Input: Full RFP knowledge graph
- Output: High-priority issues requiring attention
- Use case: "What are the critical themes I need to address?"

#### **3.4 Proof Points Mapper** (`user_queries/proof_points_mapper.md`)

- Input: Win themes + evaluation factors
- Output: Evidence requirements per theme
- Use case: "What proof points do I need for our discriminators?"

---

### **Phase 4: Multi-Agent Synthesis** (Week 4+)

**Goal**: Orchestrate multiple prompts for comprehensive analysis

#### **4.1 Parallel Query Execution**

```python
async def comprehensive_rfp_analysis(rfp_query: str):
    """Run multiple analyses in parallel"""
    results = await asyncio.gather(
        intelligent_query(rfp_query, query_type="compliance_assessment"),
        intelligent_query(rfp_query, query_type="generate_qfg"),
        intelligent_query(rfp_query, query_type="win_themes"),
        intelligent_query(rfp_query, query_type="proposal_outline"),
    )

    compliance, qfg, themes, outline = results

    # Synthesize into unified report
    return {
        "compliance_analysis": compliance,
        "questions_for_government": qfg,
        "win_strategy": themes,
        "proposal_outline": outline,
    }
```

#### **4.2 Sequential Query Chaining**

```python
async def iterative_capture_planning(rfp_file: str):
    """Multi-stage capture intelligence workflow"""

    # Stage 1: Extract critical themes
    themes = await intelligent_query(
        "What are the critical evaluation factors?",
        query_type="critical_theme_analysis"
    )

    # Stage 2: Generate win strategy based on themes
    strategy = await intelligent_query(
        f"Develop win themes for these factors: {themes}",
        query_type="win_themes"
    )

    # Stage 3: Generate outline incorporating strategy
    outline = await intelligent_query(
        f"Generate proposal outline emphasizing: {strategy}",
        query_type="proposal_outline"
    )

    return {
        "critical_themes": themes,
        "win_strategy": strategy,
        "proposal_outline": outline,
    }
```

---

## 🔧 **Technical Implementation**

### **Directory Structure**

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

## 🚀 **Getting Started (After Branch 009 Merge)**

1. **Create Branch 010**:

   ```powershell
   git checkout main
   git pull origin main
   git checkout -b 010-query-time-intelligence
   ```

2. **Create user_queries/ directory**:

   ```powershell
   New-Item -ItemType Directory -Path prompts/user_queries
   ```

3. **Implement Phase 1 prompts** (based on Branch 002 artifacts):

   - Copy `docs/archive/prompts_branch_002/*.txt` as starting templates
   - Adapt for `user_prompt` parameter (post-retrieval context)
   - Add knowledge graph query patterns

4. **Test with manual prompt injection**:

   ```python
   from lightrag.base import QueryParam
   from src.core.prompt_loader import load_prompt

   compliance_prompt = load_prompt("user_queries/compliance_assessment")
   query_param = QueryParam(mode="hybrid", user_prompt=compliance_prompt)
   response = await rag.aquery("What are the evaluation factors?", param=query_param)
   ```

5. **Implement intent classification** (Phase 2)

6. **Add advanced prompts** (Phase 3)

7. **Build multi-agent orchestration** (Phase 4)

---

## 🎯 **Priority Order**

1. 🔥 **CRITICAL**: Proposal outline generation (saves 10-20 hours per RFP)
2. 🔥 **CRITICAL**: Compliance assessment (Shipley methodology validation)
3. 🟡 **HIGH**: QFG generation (customer shaping opportunity)
4. 🟡 **HIGH**: Win theme identification (strategic differentiation)
5. 🟢 **MEDIUM**: Intent classification (UX improvement)
6. 🟢 **MEDIUM**: Advanced prompts (power user features)
7. 🔵 **LOW**: Multi-agent synthesis (nice-to-have orchestration)

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
