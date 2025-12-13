# User Query Prompts - Phase 1 Implementation

**Branch**: 010-query-prompts-integration  
**Status**: ✅ Phase 1 Complete  
**Prompts**: 5 core capture intelligence templates

---

## Overview

These prompts inject specialized response formatting into LightRAG queries using the `user_prompt` parameter. They transform retrieved RFP content into actionable capture intelligence without affecting retrieval quality.

**Key Innovation**: Prompts are applied AFTER retrieval but BEFORE LLM response generation, ensuring domain-specific analysis while maintaining accurate knowledge graph queries. **All prompts leverage entity metadata fields** (criticality_level, factor_id, modal_verb, etc.) for precise intelligence generation.

---

## Available Prompts

### 1. **Compliance Checklist** (`compliance_checklist.md`) ⭐ **NEW**

**Purpose**: Generate initial requirement checklist BEFORE proposal writing  
**Input Query**: "Generate compliance checklist" or "What requirements must we address?"  
**Output**: Must/Should/May checklist with RFP references, evaluation factor linkage  
**ROI**: Prevents missed requirements, ensures 100% MANDATORY coverage, saves 5-10 hours

### 2. **Proposal Outline Generation** (`proposal_outline_generation.md`) ⭐

**Purpose**: Generate complete proposal structure with compliance checklist  
**Input Query**: "Generate a proposal outline" or "What should my proposal structure look like?"  
**Output**: Volume structure, page allocations, must-address checklist, strategic guidance  
**ROI**: Saves 10-20 hours of manual outline development per RFP

### 3. **Compliance Assessment** (`compliance_assessment.md`)

**Purpose**: Shipley-based compliance scoring AFTER drafting proposal  
**Input Query**: "How compliant is our proposal?" or "What requirements are we missing?"  
**Output**: Requirement-by-requirement analysis, gap identification, remediation roadmap  
**ROI**: Reduces non-responsive bid risk, identifies critical gaps early

### 4. **Questions for Government** (`generate_qfg.md`)

**Purpose**: Strategic clarification questions for Q&A period  
**Input Query**: "What questions should we ask the government?" or "What are the ambiguities?"  
**Output**: 5-7 high-impact questions with RFP citations, business impact analysis  
**ROI**: Shapes RFP favorably, reduces pricing risk, exposes competitor weaknesses

### 5. **Win Theme Identification** (`win_theme_identification.md`)

**Purpose**: Strategic differentiation based on evaluation factors  
**Input Query**: "What are our win themes?" or "How should we differentiate?"  
**Output**: Themes tied to pain points, discriminators, proof point requirements  
**ROI**: Focuses proposal effort on highest-scoring opportunities

---

## Metadata-Driven Intelligence (Branch 010 Enhancement)

All prompts leverage **entity metadata fields** extracted during ingestion for precise query responses:

| Metadata Field        | Source            | Used By                    |
| --------------------- | ----------------- | -------------------------- |
| `criticality_level`   | REQUIREMENT       | Checklist, Assessment      |
| `modal_verb`          | REQUIREMENT       | Checklist, Assessment, QFG |
| `requirement_type`    | REQUIREMENT       | Checklist, Win Themes      |
| `factor_id`           | EVALUATION_FACTOR | All prompts                |
| `relative_importance` | EVALUATION_FACTOR | Outline, QFG, Win Themes   |
| `page_limits`         | EVALUATION_FACTOR | Outline, Checklist         |
| `agency_supplement`   | CLAUSE            | Assessment (26+ supported) |

**Benefit**: LLM receives exact field names, not informal terms. Improves accuracy and consistency.

---

## Usage

### Method 1: Python Client (Recommended)

```python
from lightrag.base import QueryParam
from src.core.prompt_loader import load_prompt

# Load specialized prompt
prompt = load_prompt("user_queries/proposal_outline_generation")

# Execute query with specialized formatting
query_param = QueryParam(mode="hybrid", user_prompt=prompt)
response = await rag_instance.lightrag.aquery(
    "Generate a proposal outline",
    param=query_param
)

print(response)
```

### Method 2: REST API

```bash
# Load prompt content
PROMPT=$(cat prompts/user_queries/proposal_outline_generation.md)

# Execute query with user_prompt parameter
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"Generate a proposal outline\",
    \"mode\": \"hybrid\",
    \"user_prompt\": \"$PROMPT\"
  }"
```

### Method 3: Direct LightRAG Integration

```python
from lightrag import LightRAG, QueryParam
from pathlib import Path

# Initialize LightRAG
rag = LightRAG(working_dir="./rag_storage")

# Load prompt
prompt_text = Path("prompts/user_queries/compliance_assessment.md").read_text()

# Query with specialized format
response = await rag.aquery(
    "What requirements are we missing?",
    param=QueryParam(mode="hybrid", user_prompt=prompt_text)
)
```

---

## Prompt Selection Guide

| User Goal               | Recommended Prompt            | Example Query                        |
| ----------------------- | ----------------------------- | ------------------------------------ |
| Plan proposal structure | `proposal_outline_generation` | "What sections do I need to write?"  |
| Check compliance        | `compliance_assessment`       | "Are we meeting all requirements?"   |
| Prepare for Q&A         | `generate_qfg`                | "What should we ask the government?" |
| Develop strategy        | `win_theme_identification`    | "How do we differentiate?"           |
| General information     | None (standard query)         | "What are the evaluation factors?"   |

---

## Cost Analysis

**Per Specialized Query**:

- User query: ~50 tokens
- User prompt: ~2,000 tokens
- Retrieved context: ~5,000 tokens (entities + relationships + chunks)
- LLM response: ~1,000 tokens

**Total**: ~8,050 tokens  
**Cost** (Grok-beta): ~$0.008 per query

**Comparison**:

- RFP ingestion (one-time): $0.042
- 100 specialized queries: $0.80
- **Total capture intelligence**: ~$1.00 per RFP

---

## Best Practices

### 1. **Query Clarity**

- ✅ Good: "Generate a proposal outline for the technical volume"
- ❌ Poor: "Tell me about the RFP" (too vague for specialized formatting)

### 2. **Prompt Caching**

```python
# Cache prompts at app startup
from src.core.prompt_loader import load_prompt

PROMPTS = {
    "outline": load_prompt("user_queries/proposal_outline_generation"),
    "compliance": load_prompt("user_queries/compliance_assessment"),
    "qfg": load_prompt("user_queries/generate_qfg"),
    "win_themes": load_prompt("user_queries/win_theme_identification"),
}

# Reuse cached prompts
response = await rag.aquery(query, param=QueryParam(user_prompt=PROMPTS["outline"]))
```

### 3. **Combining with Standard Queries**

```python
# Standard query (no user_prompt) for quick facts
factors = await rag.aquery("What are the evaluation factors?")

# Specialized query for analysis
outline = await rag.aquery(
    "Generate proposal outline",
    param=QueryParam(user_prompt=PROMPTS["outline"])
)
```

---

## Testing

### Manual Test (Quick Validation)

```powershell
# Start server
python app.py

# Test proposal outline prompt
$prompt = Get-Content prompts\user_queries\proposal_outline_generation.md -Raw

Invoke-RestMethod -Method POST -Uri http://localhost:9621/query `
  -ContentType "application/json" `
  -Body (@{
    query = "Generate a proposal outline"
    mode = "hybrid"
    user_prompt = $prompt
  } | ConvertTo-Json)
```

### Automated Tests

```python
# tests/test_user_prompts.py
import pytest
from lightrag.base import QueryParam
from src.core.prompt_loader import load_prompt

@pytest.mark.asyncio
async def test_proposal_outline(rag_instance):
    """Test proposal outline generation"""
    prompt = load_prompt("user_queries/proposal_outline_generation")
    response = await rag_instance.lightrag.aquery(
        "Generate a proposal outline",
        param=QueryParam(mode="hybrid", user_prompt=prompt)
    )

    # Validate response contains expected sections
    assert "VOLUME" in response
    assert "page" in response.lower()
    assert "evaluation factor" in response.lower()

@pytest.mark.asyncio
async def test_compliance_assessment(rag_instance):
    """Test compliance assessment"""
    prompt = load_prompt("user_queries/compliance_assessment")
    response = await rag_instance.lightrag.aquery(
        "Assess our compliance",
        param=QueryParam(mode="hybrid", user_prompt=prompt)
    )

    # Validate Shipley scoring present
    assert "score" in response.lower()
    assert "requirement" in response.lower()
```

---

## Troubleshooting

### Issue: Prompt not loading

**Error**: `FileNotFoundError: Prompt not found: prompts/user_queries/...`

**Solution**:

```python
# Verify prompt exists
from src.core.prompt_loader import list_available_prompts
print(list_available_prompts())

# Should show:
# {
#   "extraction": [...],
#   "relationship_inference": [...],
#   "user_queries": [
#     "proposal_outline_generation",
#     "compliance_assessment",
#     "generate_qfg",
#     "win_theme_identification"
#   ]
# }
```

### Issue: Response not formatted as expected

**Symptom**: Output looks like standard query response, not specialized format

**Cause**: `user_prompt` parameter not being passed correctly

**Solution**:

```python
# Ensure QueryParam includes user_prompt
query_param = QueryParam(
    mode="hybrid",
    user_prompt=prompt  # ← Must be present
)

# Verify parameter in logs
logger.debug(f"Query param: {query_param}")
```

### Issue: Token limit exceeded

**Error**: Context window overflow

**Solution**: Reduce prompt size or use smaller context

```python
# Use only essential sections of prompt
# Or reduce top_k to retrieve fewer entities
query_param = QueryParam(
    mode="hybrid",
    user_prompt=prompt,
    top_k=40  # Default is 60
)
```

---

## Maintenance

### Adding New Prompts

1. Create `.md` file in `prompts/user_queries/`
2. Follow existing template structure (see any existing prompt)
3. Test with example queries
4. Update this README with new prompt description

### Updating Existing Prompts

1. Edit `.md` file directly
2. No server restart needed (prompts loaded on-demand)
3. Clear cache if using cached prompts: `from src.core.prompt_loader import clear_cache; clear_cache()`
4. Increment version number in prompt file header

---

## Phase 1 Completion Status

**Completed** ✅:

- [x] Directory structure created (`prompts/user_queries/`)
- [x] 4 core prompts implemented
- [x] `prompt_loader.py` supports user_queries category (already did!)
- [x] Usage documentation complete
- [x] Testing examples provided

**Deferred to Future Branches** ⏸️:

- Branch 011: Intent classification & auto-routing
- Branch 012: Advanced specialized prompts
- Branch 013: Multi-agent synthesis orchestration

---

## References

- **Technical Review**: `docs/archive/BRANCH_010_TECHNICAL_REVIEW.md`
- **Implementation Plan**: `docs/archive/BRANCH_010_QUERY_INTELLIGENCE.md`
- **LightRAG API**: https://github.com/HKUDS/LightRAG
- **Shipley Methodology**: Capture Guide p.85-90, Proposal Guide p.45-55

---

**Last Updated**: January 23, 2025  
**Branch**: 010-query-prompts-integration  
**Status**: Phase 1 Implementation Complete
