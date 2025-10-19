# Grok-4-Fast-Reasoning Self-Diagnostic: Entity Type Corruption

**Date**: October 10, 2025  
**Context**: Branch 005 Entity Type Fix revealed 22 persistent `#>|TYPE` corruption warnings  
**Source**: Grok-4-fast-reasoning model self-analysis

---

## The Root Cause (From Grok Itself)

### Pattern Analysis

**Symptom**: LLM generates `#>|ORGANIZATION`, `#>|DOCUMENT`, `#|SECTION` patterns despite:
- No "wrong examples" in prompt
- Simplified delimiter instructions
- Clear entity type list

**Grok's Self-Diagnosis**:

> "This isn't a 'known issue' with my underlying architecture, but it's a **classic symptom of prompt-induced over-generation or delimiter confusion**."

### Three Contributing Factors

#### 1. Prompt Echoing / Hallucinated Markers

**The Problem**:
- If prompt includes instructional delimiters (`#` for sections, `|` for fields, `>` for hierarchies)
- Model "echoes" them as learned patterns for separating entities
- Treats them as output structure requirements
- **Even without explicit examples**, subtle cues trigger this behavior

**Current Prompt Issues**:
```python
# Current entity type list format (initialization.py, line ~145)
entity_types = [
    "ORGANIZATION", "CONCEPT", "EVENT", "TECHNOLOGY", 
    "PERSON", "LOCATION", "REQUIREMENT", "CLAUSE",
    "SECTION", "DOCUMENT", "DELIVERABLE", "EVALUATION_FACTOR",
    "SUBMISSION_INSTRUCTION", "STATEMENT_OF_WORK", "ANNEX",
    "PROGRAM", "STRATEGIC_THEME", "EQUIPMENT", "REGULATION"
]

# Problem: Delimiter instructions reference special characters
```

**Fix**: Present as flat, bulleted enum **without ANY special characters in instructions**

#### 2. Field Count / Delimiter Mismatch

**The Problem**:
- 13 LLM format errors suggest model is miscounting fields
- Trying to enforce rigid schema but merging/splitting incorrectly
- Creates compensatory artifacts (`#>|`) to "fix" output in internal reasoning

**Current Issues**:
```
WARNING: found 5/4 fields on ENTITY `A-1 Type of Contract` @ `Indefinite Delivery...`
WARNING: found 4/5 fields on RELATION `MCMC`~`Post-MAT`
```

**Fix**: Switch from line-based parsing to **JSON structure** (eliminates field counting)

#### 3. Model-Specific Behavior (Grok-4-fast-reasoning)

**The Problem**:
> "Grok-4-fast-reasoning might prioritize concise, marker-heavy outputs to accelerate inference, amplifying this if the prompt emphasizes brevity."

**Observation**:
- `grok-4-fast-reasoning` = Speed-optimized variant
- May use "debug" or "annotation" style internally
- Hits ORGANIZATION, DOCUMENT, etc. consistently → entity type list needs tighter boundaries

**Fix**: Test `grok-2-1212` (more deliberate parsing, better schema adherence in RAG pipelines)

---

## Grok's Recommended Solutions

### Solution 1: Ultra-Simplify Entity Type List ✅ HIGHEST PRIORITY

**Current Format** (in prompt):
```
Entity_types: [ORGANIZATION, CONCEPT, EVENT, ...]
```

**Grok's Recommended Format**:
```markdown
Valid entity types (exactly one per entity, no prefixes/suffixes):
- ORGANIZATION
- DOCUMENT
- DELIVERABLE
- CONCEPT
- TECHNOLOGY
- LOCATION
- REQUIREMENT
- CLAUSE
- SECTION
- EVALUATION_FACTOR
- SUBMISSION_INSTRUCTION
- STATEMENT_OF_WORK
- ANNEX
- PROGRAM
- STRATEGIC_THEME
- EQUIPMENT
- REGULATION

⚠️ CRITICAL: Output ONLY the entity type in ALL CAPS, followed by the delimiter and extracted text.
❌ DO NOT use #, |, >, or any other markers as prefixes or suffixes.
✅ Example: ORGANIZATION{tuple_delimiter}USAMMA{tuple_delimiter}Description...
```

### Solution 2: Switch to JSON Output Format ✅ ARCHITECTURAL CHANGE

**Current Format** (line-based with delimiters):
```
entity<|>USAMMA<|>ORGANIZATION<|>Description...
```

**Grok's Recommended Format** (JSON):
```json
[
  {
    "type": "ORGANIZATION",
    "name": "USAMMA",
    "description": "United States Army Medical Material Agency..."
  },
  {
    "type": "DOCUMENT",
    "name": "Watercraft Maintenance Status Report",
    "description": "CDRL 6057 submitted weekly..."
  }
]
```

**Prompt Instruction**:
> "Respond ONLY with a JSON array of objects. No additional text, explanations, or delimiters."

**Benefits**:
- Eliminates line-based parsing issues
- Native validation (invalid JSON = reject)
- No field count mismatches
- Clear structure for pre-validation cleanup

**Challenge**: Requires RAG-Anything/LightRAG integration changes (may not be feasible)

### Solution 3: Pre-Cleanup Hook (Before Validation) ✅ TACTICAL FIX

**Implementation**:

```python
# Add to RAG-Anything processing pipeline BEFORE validation
def sanitize_llm_output(raw_output: str) -> str:
    """
    Strip corruption patterns from LLM output before validation.
    
    Patterns to remove:
    - Lines starting with #> or #|
    - | characters outside quoted values
    - Special characters in entity type field
    """
    import re
    
    lines = raw_output.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Skip lines with corruption patterns
        if re.match(r'^#[>|]', line):
            logger.warning(f"Stripped corrupted line: {line[:50]}...")
            continue
        
        # Clean entity type field (field 3)
        if line.startswith('entity'):
            parts = line.split('<|>')
            if len(parts) >= 3:
                # Remove special characters from entity type
                entity_type = parts[2]
                cleaned_type = re.sub(r'[#>|<]', '', entity_type).strip().upper()
                parts[2] = cleaned_type
                line = '<|>'.join(parts)
                logger.info(f"Cleaned entity type: {entity_type} → {cleaned_type}")
        
        cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines)
```

**Integration Point**: Hook into RAG-Anything's `extract` stage, post-LLM but pre-parser

### Solution 4: Test Alternative LLM Models ✅ VALIDATION

**Model Comparison**:

| Model | Speed | Schema Adherence | Artifact Likelihood |
|-------|-------|------------------|---------------------|
| **grok-4-fast-reasoning** | High | Medium | High (current issue) |
| **grok-2-1212** | Medium | High | Low (recommended) |
| **Claude 3.5 Sonnet** | Medium | Very High | Very Low |
| **GPT-4 Turbo** | Medium | High | Low |

**Test Plan**:
1. Switch to `grok-2-1212` with prompt: *"Prioritize strict schema over speed"*
2. Re-process MCPP RFP
3. Count warnings (target: <5)
4. Compare entity counts vs grok-4-fast baseline

**Configuration Change**:
```python
# .env
LLM_MODEL=grok-2-1212  # Was: grok-4-fast-reasoning
LLM_MODEL_TEMPERATURE=0.0  # Was: 0.1 (even more deterministic)
```

### Solution 5: Prompt Ablation Testing ✅ DIAGNOSTIC

**Zero-Shot Minimal Prompt**:
```markdown
Extract entities from the following text.

Valid entity types (use EXACTLY as shown):
ORGANIZATION, DOCUMENT, DELIVERABLE, CONCEPT, TECHNOLOGY, LOCATION, REQUIREMENT

Output format (one entity per line):
entity_name|entity_type|description

Example:
USAMMA|ORGANIZATION|United States Army Medical Material Agency

---Input Text---
{input_text}

---Output---
```

**Test Cases**:
1. **Acronym-heavy**: "USAMMA, HQMC, DMO" (triggers uppercase/special char issues)
2. **Mixed case**: "Opt I Ordering Period Year Seven" (triggers lowercase variants)
3. **Hyphenated**: "Phase-Out", "Post-MAT" (triggers delimiter confusion)
4. **Numbers**: "29 CFR 1915", "MCO 4450.12" (triggers field count errors)

---

## Implementation Roadmap for Branch 005 MinerU Optimization

### Phase 1: Immediate Fixes (1-2 hours)

**Goal**: Reduce warnings from 22 to <5 without architectural changes

1. **Rewrite entity type list** in prompt (Solution 1)
   - Remove ALL special characters from instructions
   - Add explicit "DO NOT use #, |, >" warning
   - Format as bulleted list with crystal-clear examples

2. **Add pre-validation sanitizer** (Solution 3)
   - Create `src/utils/llm_output_sanitizer.py`
   - Strip `#>|`, `#|`, `<|` patterns before validation
   - Log all corrections for monitoring

3. **Test with grok-2-1212** (Solution 4)
   - Switch model in `.env`
   - Re-process MCPP RFP
   - Document results

**Success Criteria**: <5 warnings per RFP

### Phase 2: Architectural Improvements (2-3 hours)

**Goal**: Eliminate warnings completely and improve maintainability

1. **Prompt modularization** (from BRANCH_005_HANDOFF.md)
   - Extract prompt to `/prompts/entity_extraction/entity_extraction_prompt.md`
   - Create `src/utils/prompt_loader.py`
   - Enable rapid A/B testing

2. **JSON output format** (Solution 2 - if feasible)
   - Investigate RAG-Anything/LightRAG JSON support
   - If supported: Rewrite extraction to use JSON
   - If not: Document limitation, keep line-based with sanitizer

3. **Prompt ablation suite** (Solution 5)
   - Create test prompts in `/prompts/entity_extraction/variants/`
   - Automate comparison testing
   - Select best-performing variant

**Success Criteria**: 0 warnings, <1% entity loss

### Phase 3: Validation & Documentation (1 hour)

1. **Regression testing**
   - Navy MBOS: Should maintain 4,302 entities
   - MCPP RFP: Should capture all 22 previously lost entities
   - New RFP: Test on fresh document

2. **Documentation**
   - Update `BRANCH_005_HANDOFF.md` with findings
   - Create `PROMPT_ENGINEERING_GUIDE.md` (lessons learned)
   - Document final prompt in `/prompts/entity_extraction/`

3. **Commit & merge**
   - Detailed commit messages
   - Update main branch
   - Tag release

---

## Key Insights from Grok

### What This Teaches Us

1. **LLMs Are Self-Aware of Their Quirks**
   - Grok correctly diagnosed prompt echoing
   - Identified model-specific behavior (speed vs accuracy tradeoff)
   - Recommended alternative models

2. **Speed-Optimized Models Have Tradeoffs**
   - `grok-4-fast-reasoning` sacrifices some schema adherence for speed
   - For RAG extraction, accuracy > speed
   - Consider `grok-2-1212` for extraction, keep fast model for queries

3. **Delimiter Complexity Creates Artifacts**
   - Even subtle references to special characters trigger echoing
   - JSON > line-based formats for schema validation
   - Ultra-simple instructions > comprehensive explanations

4. **Pre-Validation Cleanup Is Valid Strategy**
   - But do it EARLY (post-LLM, pre-parser)
   - Log corrections to monitor quality
   - Treat as tactical fix, not strategic solution

### Questions for Next Session

1. **Can RAG-Anything/LightRAG accept JSON output?**
   - Check library documentation
   - Test with small example
   - If yes: Prioritize JSON format change

2. **What's the performance impact of grok-2-1212?**
   - Processing time increase acceptable?
   - Cost difference?
   - Quality improvement justifies tradeoff?

3. **Should we fork RAG-Anything to add sanitizer hook?**
   - Or: Monkey-patch the extract function?
   - Or: Pre-process before feeding to library?
   - Document decision rationale

---

**Next Action**: Apply Grok's recommendations in Branch 005 MinerU Optimization

**Priority**: Solution 1 (entity type list) + Solution 3 (sanitizer) + Solution 4 (model swap)

**Timeline**: 1-2 hours for immediate fixes, test, document

**Expected Outcome**: <5 warnings per RFP, <1% entity loss
