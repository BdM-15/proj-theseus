# GitHub Issue: Reset to Branch 021/022

**Title**: `Reset to Branch 021/022: Clean Slate for Quality Recovery`

**Labels**: `enhancement`, `refactor`, `high-priority`

---

## Issue Body (Copy Below)

## Summary

Post-mortem analysis of branches 022-041 revealed that retrieval quality degraded from 98%+ (Branch 022 "Perfect Run") to ~70-80% due to accumulated technical debt and a critical upstream bug introduced in Branch 023.

**Reference**: See `docs/POST_MORTEM_BRANCHES_022_TO_040.md` for complete analysis.

## Root Cause

**Branch 023** removed the `description` field from `BaseEntity` to prevent output truncation, which:
- Broke LightRAG's entity matching (requires descriptions)
- Triggered 916 lines of compensation code (`description_enrichment.py`)
- Led to 20 branches of fixes, workarounds, and over-engineering

## Branch 041 Surgical Fix (Attempted)

Commit `c34a144` attempted surgical fixes:
- ✅ Restored `description` field to BaseEntity
- ✅ Updated extraction prompt to require descriptions
- ✅ Reduced chunk size (8192→4096) to accommodate descriptions
- ✅ Deleted 916 lines of compensation code
- ✅ Upgraded to Grok 4-1 models

**Concern**: Accumulated technical debt across 20 branches may have unknown interactions that surgical fixes don't address.

## Recommendation: Reset to Branch 021/022

### Why Reset

| Factor | Surgical Fix | Reset to 021/022 |
|--------|--------------|------------------|
| **Complexity** | High - debugging debt | Low - clean slate |
| **Risk** | Unknown interactions | Known good state |
| **Time to Quality** | Unknown | Predictable (98%+) |
| **Maintainability** | Complex patches | Simple code |

### Reset Strategy

#### Phase 1: Clean Reset (Week 1)
```bash
git checkout 022  # Perfect Run baseline
git checkout -b 050-clean-reset
# Validate 98%+ quality with test RFP
```

#### Phase 2: Selective Reintroduction (Week 2-3)

**YES - Reintroduce:**
- [ ] 18-entity ontology (domain expertise)
- [ ] Pydantic schema validation (graceful)
- [ ] xAI SDK integration (reliability)
- [ ] BOE workload enrichment (domain value)
- [ ] Schema-driven algorithms 1, 2, 5 (robustness)
- [ ] CDRL pattern matching - Algorithm 7 (standardized formats)

**NO - Do NOT bring back:**
- [ ] ~~Query overrides~~ → Use WebUI configuration
- [ ] ~~Description enrichment~~ → Fix upstream instead
- [ ] ~~Custom parallelization~~ → Use native library settings
- [ ] ~~8 post-processing algorithms~~ → Test without first

#### Phase 3: Grok 4-1 Integration (Week 3-4)
```bash
EXTRACTION_LLM_NAME=grok-4-1-fast-non-reasoning
REASONING_LLM_NAME=grok-4-1-fast-reasoning
# Validate quality, fall back if needed
```

## Files to Preserve Before Reset

```
prompts/extraction/entity_extraction_prompt.md  # 121K ontology prompt
prompts/extraction/entity_detection_rules.md    # Detection rules
src/ontology/schema.py                          # 18 entity types
src/inference/schema_prompts.py                 # Schema-driven guidance
src/inference/workload_enrichment.py            # BOE categorization
src/extraction/json_extractor.py                # Instructor integration
```

## Success Criteria

- [ ] Entity count within 5% of Branch 022 baseline (368 entities)
- [ ] Relationship count reasonable (not 3,000+ ghost relationships)
- [ ] Workload query quality ≥95% of Branch 022 baseline
- [ ] Codebase complexity reduced (target: <50% of current LOC)

## Related

- Branch 041: `041-surgical-fixes-descriptions` (surgical fix attempt)
- Post-mortem: `docs/POST_MORTEM_BRANCHES_022_TO_040.md`
- Branch 022 commit: `cb204fd` (Perfect Run baseline)

---

> *"The system was ALREADY WORKING in Branch 021/022. Every change after that was either a genuine improvement (rare), a fix for a problem we created (common), or over-engineering (common)."*
