# Conditional Routing Design for User Query Prompts

**Purpose**: Architecture for LLM-based intent classification to conditionally apply specialized user prompts while preserving general-purpose brainstorming capabilities.

**Design Decision**: LLM-based classification (Option 1) approved for flexibility, speed, and natural language handling.

**Branch**: 020-user-prompt-integration  
**Status**: Documentation Only - No Implementation  
**Created**: November 18, 2025

---

## Problem Statement

**Challenge**: LightRAG `QueryParam.user_prompt` parameter enables specialized response formatting (e.g., compliance checklists, proposal outlines), but:

1. **Quality Regression**: Applying user_prompt globally degrades brainstorming/ideation quality
2. **Routing Need**: Must conditionally route queries to appropriate prompts based on user intent
3. **Flexibility Required**: Users phrase requests in many ways ("What must we address?" vs. "Generate compliance checklist")
4. **No Breaking General Queries**: Preserve unconstrained LLM responses for exploratory queries

**Solution**: LLM-based intent classification before main query execution.

---

## Architectural Overview

### Two-Stage Query Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TWO-STAGE QUERY PIPELINE                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  STAGE 1: INTENT CLASSIFICATION (~500ms, ~$0.001)                   │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  User Query → LLM Classifier → Intent Category              │    │
│  │  "What requirements must we address?"                       │    │
│  │         ↓                                                    │    │
│  │  Classification: COMPLIANCE_CHECKLIST                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  STAGE 2: MAIN QUERY WITH CONDITIONAL PROMPT                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  if intent == COMPLIANCE_CHECKLIST:                         │    │
│  │      user_prompt = read_file("compliance_checklist.md")     │    │
│  │  elif intent == GENERAL:                                    │    │
│  │      user_prompt = None  # Preserve brainstorming quality   │    │
│  │                                                              │    │
│  │  rag.query(                                                 │    │
│  │      query=user_query,                                      │    │
│  │      param=QueryParam(user_prompt=user_prompt)              │    │
│  │  )                                                           │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              ↓                                       │
│  RESPONSE: Specialized format OR general brainstorming              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Design Principle**: Intent classification is FAST (500ms) and CHEAP ($0.001 per query), negligible overhead for improved routing accuracy.

---

## Intent Categories

### Intent Enum Definition

```python
from enum import Enum

class QueryIntent(Enum):
    """
    User query intent categories for conditional routing.
    """
    COMPLIANCE_CHECKLIST = "compliance_checklist"
    PROPOSAL_OUTLINE = "proposal_outline_generation"
    COMPLIANCE_ASSESSMENT = "compliance_assessment"
    GENERATE_QFG = "generate_qfg"
    WIN_THEMES = "win_theme_identification"
    WORKLOAD_ANALYSIS = "workload_analysis"
    GENERAL = "general"  # Preserves unconstrained LLM responses
```

### Intent Descriptions

| Intent Category         | Description                                      | Example User Queries                                                |
| ----------------------- | ------------------------------------------------ | ------------------------------------------------------------------- |
| `COMPLIANCE_CHECKLIST`  | Generate requirement checklist before writing    | "What requirements must we address?", "List all SHALL requirements" |
| `PROPOSAL_OUTLINE`      | Generate proposal structure with page allocation | "Create proposal outline", "How should I organize my proposal?"     |
| `COMPLIANCE_ASSESSMENT` | Score completed proposal draft vs. requirements  | "Assess proposal compliance", "How compliant is my draft?"          |
| `GENERATE_QFG`          | Generate strategic questions for government      | "What should I ask the CO?", "Generate clarification questions"     |
| `WIN_THEMES`            | Extract competitive differentiators/themes       | "What makes us competitive?", "Generate win themes"                 |
| `WORKLOAD_ANALYSIS`     | Extract operational workload metrics             | "Extract workload from PWS", "Analyze staffing requirements"        |
| `GENERAL`               | Unconstrained brainstorming/ideation             | "Help me think through...", "What are creative approaches to..."    |

---

## Classification Prompt Template

### System Prompt for Intent Classifier

```markdown
You are an intent classifier for a government contracting proposal assistant.

Your task is to analyze the user's query and determine which specialized response format is most appropriate.

## Intent Categories

1. **COMPLIANCE_CHECKLIST**: User wants a comprehensive list of requirements to address (before writing proposal).

   - Keywords: "requirements", "must address", "compliance matrix", "checklist", "shall/should requirements"
   - Examples: "What requirements must we address?", "List all mandatory requirements"

2. **PROPOSAL_OUTLINE**: User wants proposal structure with page allocations and section assignments.

   - Keywords: "outline", "structure", "organize", "page allocation", "proposal sections"
   - Examples: "Create proposal outline", "How should I organize my proposal?"

3. **COMPLIANCE_ASSESSMENT**: User wants to score completed proposal draft against requirements.

   - Keywords: "assess", "compliant", "score", "review", "gaps", "missing requirements" (WITH uploaded proposal)
   - Examples: "How compliant is my draft?", "Assess proposal compliance"
   - **CRITICAL**: Only if user has uploaded proposal file or references existing draft

4. **GENERATE_QFG**: User wants strategic questions to ask government (clarifications, RFI response).

   - Keywords: "questions for government", "clarifications", "ask CO", "RFI", "what to ask"
   - Examples: "What should I ask the CO?", "Generate clarification questions"

5. **WIN_THEMES**: User wants competitive differentiators and theme statements.

   - Keywords: "win themes", "differentiation", "competitive", "discriminators", "what makes us"
   - Examples: "What makes us competitive?", "Generate win themes", "How do we differentiate?"

6. **WORKLOAD_ANALYSIS**: User wants operational metrics for labor/BOM analysis.

   - Keywords: "workload", "staffing", "labor", "FTEs", "operational tempo", "extract metrics"
   - Examples: "Extract workload from PWS", "Analyze staffing requirements"

7. **GENERAL**: General brainstorming, ideation, or exploratory queries.
   - Keywords: "help me think", "creative approaches", "brainstorm", "explore", "what if"
   - Examples: "Help me think through transition strategy", "What are creative ways to..."
   - **DEFAULT INTENT**: If query doesn't clearly match above categories, use GENERAL

## Classification Instructions

1. Read the user's query carefully
2. Identify keywords and phrasing that match intent categories
3. Return ONLY the intent category name (e.g., "COMPLIANCE_CHECKLIST")
4. If uncertain, default to "GENERAL" (preserves brainstorming quality)
5. Do NOT explain your reasoning, just return the intent category

## User Query

{user_query}

## Classification Result

[Return ONLY: COMPLIANCE_CHECKLIST | PROPOSAL_OUTLINE | COMPLIANCE_ASSESSMENT | GENERATE_QFG | WIN_THEMES | WORKLOAD_ANALYSIS | GENERAL]
```

### Classification Examples

**Example 1: COMPLIANCE_CHECKLIST**

```
User Query: "What are all the mandatory requirements we need to address in this RFP?"
Classification: COMPLIANCE_CHECKLIST
```

**Example 2: PROPOSAL_OUTLINE**

```
User Query: "How should I structure my technical volume and allocate pages across sections?"
Classification: PROPOSAL_OUTLINE
```

**Example 3: GENERAL (Preserve Brainstorming)**

```
User Query: "Help me think through creative approaches to demonstrate our past performance without exceeding page limits."
Classification: GENERAL
```

**Example 4: WORKLOAD_ANALYSIS**

```
User Query: "Extract the staffing requirements from the PWS so I can build a labor estimate."
Classification: WORKLOAD_ANALYSIS
```

**Example 5: GENERATE_QFG**

```
User Query: "I need to submit questions to the government. What should I ask to clarify this ambiguous requirement?"
Classification: GENERATE_QFG
```

---

## Implementation Pseudocode

**NOTE**: This is documentation only. No code implementation until approved.

### Core Routing Logic

```python
async def query_with_conditional_routing(
    user_query: str,
    workspace_name: str,
    llm_client: LLMClient,
    rag_instance: LightRAG
) -> dict:
    """
    Execute query with conditional user_prompt based on intent classification.

    Args:
        user_query: User's natural language query
        workspace_name: RAG workspace to query
        llm_client: LLM client for intent classification
        rag_instance: LightRAG instance for main query

    Returns:
        dict with keys: intent, response, metadata
    """

    # STAGE 1: Classify intent (~500ms, ~$0.001)
    intent = await classify_intent(user_query, llm_client)

    # STAGE 2: Load appropriate user_prompt based on intent
    user_prompt = get_user_prompt_for_intent(intent)

    # STAGE 3: Execute main query with conditional prompt
    response = await rag_instance.aquery(
        query=user_query,
        param=QueryParam(
            mode="hybrid",  # or "local" depending on user setting
            only_need_context=False,
            user_prompt=user_prompt  # None if GENERAL intent
        )
    )

    return {
        "intent": intent.value,
        "response": response,
        "metadata": {
            "user_prompt_applied": user_prompt is not None,
            "prompt_file": f"{intent.value}.md" if user_prompt else None
        }
    }


async def classify_intent(user_query: str, llm_client: LLMClient) -> QueryIntent:
    """
    Classify user query intent using LLM.

    Fast classification call (~500ms) before main query.
    Cost: ~$0.001 per classification (negligible overhead).

    Args:
        user_query: User's natural language query
        llm_client: LLM client (Grok-4-fast-reasoning)

    Returns:
        QueryIntent enum value
    """

    # Load classification prompt template
    classification_prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(
        user_query=user_query
    )

    # Call LLM for fast classification (temperature=0 for deterministic)
    response = await llm_client.chat_completion(
        messages=[
            {"role": "system", "content": classification_prompt}
        ],
        temperature=0.0,  # Deterministic classification
        max_tokens=10     # Only need intent category name
    )

    intent_str = response.strip().upper()

    # Map response to QueryIntent enum
    try:
        intent = QueryIntent[intent_str]
    except KeyError:
        logger.warning(f"Unknown intent '{intent_str}', defaulting to GENERAL")
        intent = QueryIntent.GENERAL

    return intent


def get_user_prompt_for_intent(intent: QueryIntent) -> str | None:
    """
    Load user_prompt file content based on classified intent.

    Args:
        intent: Classified query intent

    Returns:
        User prompt file content, or None for GENERAL intent
    """

    if intent == QueryIntent.GENERAL:
        return None  # Preserve unconstrained LLM responses

    # Map intent to prompt file
    prompt_file_map = {
        QueryIntent.COMPLIANCE_CHECKLIST: "prompts/user_queries/compliance_checklist.md",
        QueryIntent.PROPOSAL_OUTLINE: "prompts/user_queries/proposal_outline_generation.md",
        QueryIntent.COMPLIANCE_ASSESSMENT: "prompts/user_queries/compliance_assessment.md",
        QueryIntent.GENERATE_QFG: "prompts/user_queries/generate_qfg.md",
        QueryIntent.WIN_THEMES: "prompts/user_queries/win_theme_identification.md",
        QueryIntent.WORKLOAD_ANALYSIS: "prompts/user_queries/workload_analysis.md"
    }

    prompt_file = prompt_file_map.get(intent)
    if not prompt_file:
        logger.warning(f"No prompt file for intent {intent}, using GENERAL")
        return None

    # Read prompt file content
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Prompt file not found: {prompt_file}, using GENERAL")
        return None
```

### Error Handling & Fallbacks

```python
async def query_with_conditional_routing_safe(
    user_query: str,
    workspace_name: str,
    llm_client: LLMClient,
    rag_instance: LightRAG
) -> dict:
    """
    Safe wrapper with error handling and fallbacks.
    """

    try:
        return await query_with_conditional_routing(
            user_query, workspace_name, llm_client, rag_instance
        )
    except LLMClassificationError as e:
        logger.warning(f"Classification failed: {e}, defaulting to GENERAL")
        # Fallback to GENERAL intent (no user_prompt)
        return {
            "intent": "GENERAL",
            "response": await rag_instance.aquery(
                query=user_query,
                param=QueryParam(user_prompt=None)
            ),
            "metadata": {
                "user_prompt_applied": False,
                "fallback_reason": "classification_error"
            }
        }
    except PromptFileNotFoundError as e:
        logger.error(f"Prompt file missing: {e}, defaulting to GENERAL")
        # Fallback to GENERAL if prompt file doesn't exist
        return {
            "intent": "GENERAL",
            "response": await rag_instance.aquery(
                query=user_query,
                param=QueryParam(user_prompt=None)
            ),
            "metadata": {
                "user_prompt_applied": False,
                "fallback_reason": "prompt_file_missing"
            }
        }
```

---

## Performance & Cost Analysis

### Classification Overhead

**Classification Call**:

- **Latency**: ~500ms (Grok-4-fast-reasoning)
- **Cost**: ~$0.001 per query (~10 tokens output @ $0.10/1M tokens)
- **Total Query Latency**: Classification (500ms) + Main Query (2-5s) = **2.5-5.5s total**
- **User Impact**: Negligible (3-5s is normal for RAG queries)

**Cost Comparison** (Per 1000 Queries):

- Classification: 1000 × $0.001 = **$1.00**
- Main Queries: 1000 × $0.05 (avg) = **$50.00**
- **Total**: $51.00 (classification adds 2% cost overhead)

**Conclusion**: Classification overhead is negligible for improved routing accuracy.

### Grok-4 Context Window Advantage

**Context Window**: 2M tokens (eliminates token budget concerns)

- Specialized prompts: ~500-2,000 tokens each
- Even longest prompt (compliance_checklist.md ~2,000 tokens) consumes <0.1% of context window
- No need to truncate or compress prompts

---

## Quality Assurance & Testing

### Classification Accuracy Validation

**Test Dataset** (50 sample queries per intent category):

```python
test_queries = {
    "COMPLIANCE_CHECKLIST": [
        "What requirements must we address?",
        "List all SHALL requirements from Section L",
        "Generate compliance matrix",
        # ... 47 more variations
    ],
    "PROPOSAL_OUTLINE": [
        "Create proposal outline",
        "How should I organize my technical volume?",
        "Allocate pages across evaluation factors",
        # ... 47 more variations
    ],
    # ... other categories
    "GENERAL": [
        "Help me think through transition strategy",
        "What are creative approaches to demonstrate past performance?",
        "Brainstorm ways to differentiate from incumbent",
        # ... 47 more variations
    ]
}

def validate_classification_accuracy():
    """
    Test classification accuracy across all intent categories.

    Target Accuracy: >95% for specialized intents, >90% for GENERAL
    """
    results = {}
    for expected_intent, queries in test_queries.items():
        correct = 0
        for query in queries:
            classified_intent = classify_intent(query, llm_client)
            if classified_intent.value == expected_intent:
                correct += 1
        accuracy = correct / len(queries)
        results[expected_intent] = accuracy

    return results
```

**Acceptance Criteria**:

- ✅ Specialized Intents: ≥95% accuracy (misclassification = wrong prompt applied)
- ✅ GENERAL Intent: ≥90% accuracy (false negatives OK - defaults to GENERAL anyway)

### User Override Mechanism

**Allow Explicit Intent Specification** (Advanced Users):

```python
# Option 1: Prefix-based override
user_query = "[COMPLIANCE_CHECKLIST] What are the requirements?"
# → Force COMPLIANCE_CHECKLIST intent, skip classification

# Option 2: API parameter (for programmatic use)
response = await query_with_conditional_routing(
    user_query="What are requirements?",
    force_intent=QueryIntent.COMPLIANCE_CHECKLIST
)
```

---

## Alternative Design Considered & Rejected

### Option 2: Deterministic Keyword Matching (REJECTED)

**Why Rejected**: Too brittle for natural language variations.

```python
# Example deterministic routing (NOT USED)
def classify_intent_deterministic(query: str) -> QueryIntent:
    query_lower = query.lower()

    if any(kw in query_lower for kw in ["requirements", "compliance", "checklist"]):
        return QueryIntent.COMPLIANCE_CHECKLIST
    elif any(kw in query_lower for kw in ["outline", "structure", "organize"]):
        return QueryIntent.PROPOSAL_OUTLINE
    # ... etc.
    else:
        return QueryIntent.GENERAL
```

**Problems**:

- ❌ Misses paraphrased queries ("What must we address?" → GENERAL instead of COMPLIANCE_CHECKLIST)
- ❌ False positives ("Help me think about how to organize win themes" → PROPOSAL_OUTLINE instead of GENERAL)
- ❌ Maintenance nightmare (add keywords for every new phrasing)

**Why LLM-Based is Better**:

- ✅ Handles natural language variations ("What should we include?" → COMPLIANCE_CHECKLIST)
- ✅ Contextual understanding ("organize win themes" → GENERAL, "organize proposal" → PROPOSAL_OUTLINE)
- ✅ Easy to update (change prompt template, not regex/keyword lists)

---

## Implementation Checklist (When Approved)

**DO NOT IMPLEMENT** - This is documentation only until user approves.

When implementation is approved:

- [ ] Create `src/core/intent_classification.py` with classification logic
- [ ] Add `QueryIntent` enum to `src/core/query_types.py`
- [ ] Update `raganything_server.py` to use conditional routing
- [ ] Add `/query` endpoint parameter: `enable_conditional_routing: bool = True`
- [ ] Implement classification prompt template in `prompts/classification/intent_classifier.md`
- [ ] Add error handling and fallback logic
- [ ] Create unit tests for classification accuracy (50 queries × 7 intents = 350 tests)
- [ ] Add user override mechanism (prefix-based + API parameter)
- [ ] Update API documentation with new routing behavior
- [ ] Add logging/telemetry for classification accuracy monitoring

---

## Future Enhancements

**Phase 2 Improvements** (Post-Initial Implementation):

1. **Multi-Intent Classification**: Handle queries with multiple intents

   - Example: "Generate compliance checklist AND win themes"
   - Response: Apply both prompts sequentially or merge outputs

2. **Intent Confidence Scoring**: Return classification confidence

   - Example: `{intent: "COMPLIANCE_CHECKLIST", confidence: 0.95}`
   - If confidence <0.70, prompt user to clarify or default to GENERAL

3. **User Feedback Loop**: Learn from user corrections

   - "That wasn't what I wanted" → Log misclassification
   - Retrain classification prompt based on feedback

4. **Context-Aware Classification**: Use conversation history

   - Previous query: "Generate compliance checklist"
   - Current query: "Now create outline based on that"
   - Classification: PROPOSAL_OUTLINE (context: already have checklist)

5. **Prompt Chaining**: Auto-sequence related intents
   - Example: User asks for compliance checklist
   - After response, suggest: "Would you like me to generate a proposal outline based on these requirements?"

---

## Related Documentation

- **User Query Prompts**:

  - `prompts/user_queries/compliance_checklist.md`
  - `prompts/user_queries/proposal_outline_generation.md`
  - `prompts/user_queries/compliance_assessment.md`
  - `prompts/user_queries/generate_qfg.md`
  - `prompts/user_queries/win_theme_identification.md`
  - `prompts/user_queries/workload_analysis.md`

- **LightRAG Documentation**:

  - [LightRAG GitHub - QueryParam.user_prompt](https://github.com/HKUDS/LightRAG)

- **Project Documentation**:
  - `prompts/user_queries/README.md` (overview of user query system)
  - `docs/BRANCH_020_PIVOT.md` (this feature branch objectives)

---

**Version**: 1.0  
**Status**: Documentation Only - Awaiting Approval  
**Next Steps**: User review → approval → implementation  
**Estimated Implementation Time**: 8-12 hours (classification logic, testing, integration)
