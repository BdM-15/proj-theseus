# Query-Time Intelligence Prompts (Branch 010)

**Purpose**: Apply domain expertise during query operations using LightRAG's `user_prompt` parameter

---

## Architecture

```
INGESTION-TIME (prompts/extraction/)
    ↓
Knowledge Graph (GraphML)
    ↓
QUERY-TIME (prompts/query/) ← YOU ARE HERE
    ↓
Intelligent Responses
```

---

## How Query-Time Prompts Work

### Traditional Approach (Extraction-Time Metadata)

```python
# Problem: Must predict ALL metadata fields during ingestion
{
  "entity_name": "Factor 2: Maintenance Approach",
  "factor_id": "M2",               # Rigid schema
  "relative_importance": "Most",   # Must extract NOW
  "subfactors": ["2.1", "2.2"]     # Can't adapt later
}
```

### Query-Time Intelligence (This Folder)

```python
# Solution: Store natural language, extract metadata on-demand
from lightrag import QueryParam

# Entity stored as natural language during ingestion:
{
  "entity_name": "Factor 2: Maintenance Approach",
  "description": "The Government will evaluate the offeror's understanding..."
}

# Query-time prompt extracts metadata based on intent:
result = rag.query(
    query="Generate proposal outline",
    param=QueryParam(
        mode="hybrid",
        user_prompt=load_prompt("query/proposal_outline_generator")  # ← Applies domain expertise
    )
)
```

---

## Query Prompts (Branch 010 Roadmap)

### Priority #1: Proposal Outline Generation

**File**: `proposal_outline_generator.md`  
**Purpose**: Generate compliant proposal structure with Section L page limits mapped to Section M factors  
**Input**: User query "Generate proposal outline for this RFP"  
**Output**: Structured outline with volumes, page limits, scoring weights, submission instructions

### Priority #2: Compliance Assessment

**File**: `compliance_assessment.md`  
**Purpose**: Shipley 4-level compliance analysis (Compliant/Partial/Non-Compliant/Not Addressed)  
**Input**: Draft proposal sections + RFP requirements  
**Output**: Compliance matrix with coverage scores, gaps, risk assessment

### Priority #3: Questions for Government (QFG)

**File**: `questions_for_government.md`  
**Purpose**: Generate high-impact clarification questions for Q&A period  
**Input**: RFP with ambiguities  
**Output**: Max 7 questions with RFP section references, deadline tracking

### Priority #4: Win Themes Analysis

**File**: `win_themes_analyzer.md`  
**Purpose**: Identify customer hot buttons and discriminators  
**Input**: RFP evaluation factors + competitor analysis  
**Output**: Strategic themes with proof points, competitive context

### Supporting Prompts

**File**: `metadata_enrichment.md` (moved from extraction/)  
**Purpose**: Extract structured metadata from entity descriptions on-demand  
**Input**: Retrieved entities from knowledge graph  
**Output**: Field-level metadata (factor_id, page_limits, criticality_level, etc.)

**File**: `intent_classifier.md`  
**Purpose**: Route user queries to appropriate query prompt  
**Input**: User natural language query  
**Output**: Best-matching prompt + confidence score

---

## Benefits of Query-Time Intelligence

| Aspect           | Extraction-Time            | Query-Time (This Folder)          |
| ---------------- | -------------------------- | --------------------------------- |
| **Flexibility**  | Rigid schema               | Ad-hoc extraction based on intent |
| **Context**      | 4K-8K chunk only           | Full graph + 2M context window    |
| **Accuracy**     | Must guess during parsing  | Analyze complete relationships    |
| **Adaptability** | Breaks with new RFP format | Prompt adapts to any format       |
| **Cost**         | Paid once (ingestion)      | Paid per query (but smarter)      |

---

## Usage Pattern

```python
from lightrag import QueryParam
from core.prompt_loader import load_prompt

# Load query-time prompt
query_prompt = load_prompt("query/proposal_outline_generator")

# Apply during query
result = rag.query(
    query="Generate proposal outline",
    param=QueryParam(
        mode="hybrid",           # Use graph + vector retrieval
        user_prompt=query_prompt # Apply domain expertise post-retrieval
    )
)
```

---

## Development Workflow

1. **Branch 009**: Extract entities with natural language descriptions (foundation)
2. **Branch 010**: Create query prompts for specific use cases (intelligence)
3. **Branch 011+**: Iterate on prompts based on user feedback (refinement)

**Philosophy**:

- Extraction = Knowledge Capture (cast wide net)
- Query = Intelligence Application (apply expertise at decision time)

---

**Status**: Branch 010 planning phase  
**Next**: Implement proposal_outline_generator.md (Priority #1)
