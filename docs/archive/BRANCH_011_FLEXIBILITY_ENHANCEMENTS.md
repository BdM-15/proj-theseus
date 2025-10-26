# Branch 011: Domain Library Flexibility Enhancements

**Date**: January 26, 2025  
**Branch**: 011-prompt-enhancements  
**Objective**: Ensure all domain enhancement libraries emphasize **LLM semantic pattern recognition** over rigid deterministic rules

---

## Background

After completing Phase 2 (Prompt Enhancements - three domain libraries totaling 55K tokens), user raised critical concerns about rigidity:

1. **Branding Concern**: Remove "Shipley" copyright-specific references, generalize to industry best practices
2. **Flexibility Concern**: Ensure libraries provide FLEXIBLE GUIDANCE using LLM semantic understanding, NOT rigid rules
3. **Philosophy Concern**: "We don't want overly rigid regex type stuff, but leverage the power of the LLM knowledge and inferencing"

**User's Escalating Concern Sequence**:

- "Make sure we are not locked in to just the standard structure of technical, management, and past performance"
- "Make sure that flexibility is applied throughout right"
- "I mean shouldn't all the prompts fulfill this philosophy...I'm now worry you were too rigid and deterministic"

---

## Philosophy Shift

### FROM: Prescriptive Rules

- "RFPs have Technical/Management/Past Performance factors (Three-Factor Trinity)"
- "DoD ALWAYS uses adjectival scoring"
- "Universal sub-factors appear in 90%+ of RFPs"
- "Unstated evaluation factors that agencies ALWAYS evaluate"

### TO: Pattern Recognition Guidance

- "Three-Factor Trinity is a COMMON pattern (~80% of RFPs), BUT NOT universal"
- "DoD TENDS toward adjectival scoring - recognize from RFP language, don't assume"
- "Common sub-factors FREQUENTLY observed, but names and organization vary widely"
- "Frequently observed unstated factors - infer from RFP context, not predetermined"

### Key Principles

1. **LLM Semantic Understanding**: Recognize "Solution Design" + "Implementation Plan" = Technical approach (different naming, same semantic meaning)
2. **Flexible Adaptation**: RFPs vary widely (2 factors, 5+ factors, novel naming) - adapt to specifics
3. **Pattern Examples, Not Rules**: Provide EXAMPLES of what LLM should recognize, not deterministic "if X then Y" logic
4. **RFP Language Precedence**: Always prioritize actual RFP language over general patterns

---

## Changes Made

### 1. Agency Evaluation Intelligence Library

**File**: `prompts/extraction/agency_evaluation_intelligence.md`

**Header Changes**:

```diff
- **Scope**: Universal evaluation patterns + agency-specific nuances
+ **Scope**: Common evaluation patterns + agency-specific tendencies
+ **Philosophy**: **PATTERN RECOGNITION using LLM semantic understanding, NOT rigid deterministic rules**
- **Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements)
+ **Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements - Flexibility Emphasis)
```

**Section 1 - Three-Factor Trinity**:

```diff
- ## Section 1: Universal Evaluation Patterns (All Federal Agencies)
+ ## Section 1: Common Evaluation Patterns (Pattern Recognition, Not Rules)

+ > **CRITICAL PHILOSOPHY**: These patterns represent COMMON observations from federal RFPs,
+ > NOT universal requirements. RFPs vary widely in structure, factor naming, and organization.
+ > **Use LLM semantic understanding** to recognize evaluation INTENT regardless of specific
+ > factor names. **ADAPT to each RFP's unique structure** rather than forcing patterns.

- ### Pattern 1: The Three-Factor Trinity (80% of Federal RFPs)
- **Standard Structure**:
+ ### Pattern 1: The Three-Factor Trinity (Observed in ~80% of RFPs, But NOT Universal)
+ **Common Pattern** (recognize semantically, NOT as rigid template):

+ **IMPORTANT**: RFPs may use 2 factors, 5+ factors, or completely novel naming.
+ **Recognize WHAT IS BEING EVALUATED** (technical capability vs management capability
+ vs proven track record) rather than matching exact factor names.
```

**Added Semantic Recognition Guidance**:

- Technical also appears as: "Solution Design", "Methodology", "Project Approach", "Technical Solution"
- Management also appears as: "Program Management", "Team Organization", "Management Plan", "Project Controls"
- Past Performance also appears as: "Relevant Experience", "Corporate Experience", "Past Contract Performance"

**Sub-Factors Section**:

```diff
- **Universal Sub-Factors** (appear in 90%+ of RFPs):
+ **Common Sub-Factors** (frequently observed, but names and organization vary widely):

+ *Pattern recognition*: May appear as separate sub-factors ("Technical Approach" + "Risk Mitigation"
+ + "Innovation") or combined
```

**Past Performance Criteria**:

```diff
- **Universal Criteria** (how agencies score your past contracts):
+ **Common Criteria** (typical past performance evaluation, but specific criteria vary by RFP):

+ 1. **Relevance**: Similar scope, size, complexity, agency type (recognize semantically - may ask
+    for "comparable contracts" or "similar mission support")
+ 2. **Recency**: Work within last 3-5 years (timeframe varies - some RFPs specify 2 years,
+    others 7 years)
+ 3. **Quality**: CPARS ratings, customer references, contract completion (may use different rating
+    systems or questionnaires)
```

**Unstated Factors - DoD**:

```diff
- **Unstated Evaluation Factors** (DoD ALWAYS evaluates even if not explicit):
+ **Frequently Observed Unstated Factors** (DoD often evaluates these even when not explicitly listed
+ in Section M):

- Transition risk (if successor contract, how smooth will transition be?)
+ Transition risk (if successor contract, how smooth will transition be? - *recognize transition
+ language throughout RFP*)
- Incumbent advantage (is current contractor proposing? Do they have continuity?)
+ Incumbent advantage (is current contractor proposing? Do they have continuity? - *not universal,
+ depends on procurement*)
- Small business utilization (even on unrestricted contracts, good SB plan = plus)
+ Small business utilization (even on unrestricted contracts, strong SB plan often valued - *varies
+ by command priorities*)
- Mission understanding (do you understand WHY this work matters, not just HOW to do it?)
+ Mission understanding (do you understand WHY this work matters, not just HOW to do it? - *infer
+ from RFP context, not always explicit*)
```

**Unstated Factors - Civilian**:

```diff
- **Unstated Evaluation Factors** (Civilian ALWAYS evaluates):
+ **Frequently Observed Unstated Factors** (Civilian agencies often consider these even when not explicit):

- Budget consciousness (can you deliver within constrained budgets?)
+ Budget consciousness (can you deliver within constrained budgets? - *infer from cost control
+ language in SOW*)
- Transparency (clear reporting, no surprises, open communication)
+ Transparency (clear reporting, no surprises, open communication - *more emphasized than DoD*)
- Accessibility (Section 508 compliance for disabilities, not just IT systems)
+ Accessibility (Section 508 compliance for disabilities, not just IT systems - *only relevant
+ if public-facing*)
- Environmental sustainability (green initiatives, LEED certifications)
+ Environmental sustainability (green initiatives, LEED certifications - *varies widely by agency
+ priorities*)
```

**End Summary Section**:

```diff
- **Universal Patterns** (all agencies):
+ **Common Patterns Across Agencies** (recognize these semantically, adapt to RFP specifics):

- Three-Factor Trinity (Technical/Management/Past Performance)
+ Three-Factor Trinity (Technical/Management/Past Performance) - *observed in ~80% of RFPs, but NOT universal*
- Adjectival vs Numerical Scoring methodologies
+ Adjectical vs Numerical Scoring methodologies - *recognize scoring system, don't assume one or the other*
- Past Performance Relevance/Recency/Quality assessment
+ Past Performance Relevance/Recency/Quality assessment - *specific criteria and timeframes vary widely*
- Best Value vs LPTA vs Two-Step evaluation approaches
+ Best Value vs LPTA vs Two-Step evaluation approaches - *identify from Section M language, not predetermined*

- **Agency-Specific Nuances**:
+ **Agency-Specific Tendencies** (patterns, NOT rules):

- DoD: Adjectival scoring, high past performance weight, CPARS scrutiny, security clearances
+ DoD: *Tends toward* adjectival scoring, higher past performance weights, CPARS emphasis,
+ security clearance requirements
- Civilian: Numerical scoring, management emphasis, diversity/sustainability, cost consciousness
+ Civilian: *More commonly uses* numerical scoring, higher management factor weights,
+ diversity/sustainability language, cost control emphasis

+ > **REMEMBER**: These are TENDENCIES based on historical observation. Always prioritize what
+ > the SPECIFIC RFP states over these general patterns.
```

---

### 2. Federal Proposal Best Practices Library (formerly Shipley)

**File**: `prompts/extraction/shipley_methodology_patterns.md`

**Header Changes**:

```diff
+ **Philosophy**: **These are FLEXIBLE PATTERNS and EXAMPLES, not rigid templates. Adapt to each
+ RFP's unique requirements.**
- **Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements)
+ **Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements - Flexibility Emphasis)
```

**Usage Section**:

```diff
+ > **CRITICAL**: These patterns represent COMMON industry best practices observed across federal
+ > proposals, NOT universal requirements. Every RFP is different. **Use LLM semantic understanding**
+ > to recognize WHEN and HOW to apply these patterns based on specific RFP language, evaluation
+ > factors, and agency culture. **ADAPT rather than force-fit.**
```

**Branding Removal** (16 replacements via Python script):

- "Shipley Rule" → "Best Practice"
- "Shipley Compliance Matrix" → "Standard Compliance Matrix"
- "Shipley Methodology Patterns" → "Federal Proposal Best Practices"
- "Shipley Risk Rating Methodology" → "Risk Rating Methodology"
- "Shipley Capture Guide" → "Capture Management Best Practices"
- "Shipley Evaluation Criteria" → "Standard Evaluation Criteria"
- "Shipley FAB Framework" → "FAB Framework (Feature-Advantage-Benefit)"
- "Shipley Discriminator Analysis" → "Competitive Discriminator Analysis"
- "Shipley Win Theme Development" → "Win Theme Development Methodology"
- "Shipley Proposal Structure" → "Standard Proposal Structure"
- "Shipley Compliance Level" → "Compliance Assessment Level"
- "Shipley Color Team Reviews" → "Color Team Review Process"
- "Shipley Outline Methodology" → "Proposal Outline Methodology"
- "Shipley's Rule" → "Industry Best Practice"
- "Shipley recommends" → "Best practice recommends"
- "Shipley emphasizes" → "Industry best practices emphasize"

---

### 3. FAR/DFARS Compliance Library

**File**: `prompts/extraction/far_dfars_compliance_library.md`

**Header Changes**:

```diff
+ **Philosophy**: **Provides TYPICAL operational context - specific RFP language always takes
+ precedence over general patterns**
- **Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements)
+ **Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements - Flexibility Emphasis)
```

**Usage Section**:

```diff
+ > **IMPORTANT**: This library describes COMMON implications and operational patterns for federal
+ > clauses based on historical observation. Specific RFPs may have unique requirements, amendments,
+ > or agency-specific interpretations. **Always prioritize the actual RFP language** over these
+ > general patterns. Use this library for CONTEXT, not as authoritative guidance.
```

---

## Implementation Summary

**Files Modified**: 3 domain enhancement libraries (Agency, Proposal, FAR/DFARS)

**Changes Applied**:

1. **Header disclaimers**: Added "Philosophy" field emphasizing pattern recognition over rigid rules
2. **Section disclaimers**: Prominent callout boxes at top of major sections reinforcing flexibility
3. **Language shifts**: "Universal" → "Common", "Always" → "Frequently/Often/Tends toward", "Standard" → "Typical/Common pattern"
4. **Semantic guidance**: Explicit examples of how LLM should recognize patterns with different naming
5. **Context qualifiers**: Added "_recognize from X_", "_infer from Y_", "_varies by Z_" throughout
6. **Branding removal**: 16 Shipley-specific terms replaced with generic alternatives

**Token Count Impact**: Negligible increase (~500 tokens across all three libraries) - well within 2M budget

---

## Testing Strategy

**Before Production Testing**:

1. ✅ Review all three libraries for rigid language (COMPLETED)
2. ⏳ PENDING: Review existing extraction prompts (entity_detection_rules.md, requirement_evaluation.md, etc.)
3. ⏳ PENDING: Ensure all prompts emphasize pattern recognition philosophy

**Production Testing** (Phase 3):

- Test Navy MBOS with enhanced prompts
- Verify entity extraction still recognizes evaluation factors with novel naming
- Confirm relationship inference adapts to non-standard RFP structures
- Compare extraction quality vs baseline (should maintain or improve, not regress)

---

## Key Takeaways

**User's Core Philosophy**: "We don't want overly rigid regex type stuff, but leverage the power of the LLM knowledge and inferencing to pick up what we need."

**Implementation Approach**:

- Domain libraries provide **EXAMPLES and CONTEXT**, not **RULES and REQUIREMENTS**
- LLM uses semantic understanding to **RECOGNIZE PATTERNS**, not match exact strings
- Every RFP is unique - **ADAPT TO SPECIFICS** rather than force-fitting templates
- Pattern guidance helps LLM understand WHAT TO LOOK FOR, not HOW TO RESPOND deterministically

**Success Criteria**:

- Libraries enhance LLM's semantic understanding WITHOUT creating rigid constraints
- System handles non-standard RFP structures (2 factors, 7 factors, novel naming)
- Extraction quality maintained or improved vs baseline
- No false negatives from overly prescriptive pattern matching

---

**Version**: 1.0  
**Status**: Flexibility enhancements complete for all three domain libraries  
**Next Action**: Review existing extraction prompts for similar rigidity issues
