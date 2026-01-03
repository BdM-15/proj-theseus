# Issue #60: RAG Response Accessibility Enhancement

**Branch:** `feature/60-rag-response-accessibility`  
**Date:** December 2025  
**Version:** 2.2.2

---

## Summary

Enhanced `rag_response` and `naive_rag_response` prompts in `govcon_prompt.py` to produce more accessible, human-readable responses for users who are not necessarily subject matter experts (SMEs).

## Problem Statement

WebUI query responses exhibited several accessibility issues:

1. **Acronym Overload** - 40+ acronyms used without definitions (AFCAP V, USN, POP, GFP, COR/ACO, AFIT, etc.)
2. **Telegraphic Style** - Read like abbreviated notes, not consultant briefings
3. **Tables Render Poorly** - Markdown tables don't display correctly in streaming chat interfaces
4. **Unjustified Recommendations** - Win themes stated without explaining WHY they win
5. **SME-Only Language** - Assumed reader expertise in DoD contracting

## Solution: Explicit Instructions with DO NOT Examples

Initial soft instructions were ignored by the LLM. **v2.1.1** strengthened with explicit WRONG/RIGHT examples:

```markdown
5. **Accessibility & Explanation Quality** (MANDATORY - responses failing these will confuse users):

  **A. ACRONYMS - ALWAYS spell out on first use:**
  - WRONG: "All personnel must be USNs with SECRET clearance per PWS 5.0"
  - RIGHT: "All personnel must be U.S. Nationals (USNs) with SECRET security clearance, as specified in Performance Work Statement (PWS) Section 5.0"

  **B. NO MARKDOWN TABLES - use bulleted lists instead:**
  - Tables render as broken text in chat interfaces
  - WRONG: "| Position | Quals | Notes |" (table syntax)
  - RIGHT: Use nested bullets with bold headers

  **C. EXPLAIN CONCEPTS - don't assume expertise:**
  - If you mention a system (BUILDER, PAVER, NexGen IT), explain what it does in plain English
  - If you cite a metric (BCI >= 85%), explain what BCI measures and why 85% matters

  **D. NO MEANINGLESS JARGON - every claim must be concrete and logical:**
  - WRONG: "Our team exceeds quals with 150% average experience" (nonsensical)
  - RIGHT: "Propose candidates with 15 years experience when PWS requires 10 years minimum—this 50% buffer demonstrates depth"

  **E. CONSULTATIVE DEPTH over telegraphic summaries:**
  - Write like you're explaining to a smart colleague who hasn't read this RFP
  - DO NOT write shorthand notes or bullet-only summaries—provide narrative context
```

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Principle-based** | Tells WHAT to do, not rigid HOW |
| **LightRAG Compatible** | Preserves foundation structure |
| **Minimal Addition** | ~90 words to ~500 word prompt (18% increase) |
| **Non-constraining** | Doesn't limit grok-4-1-fast reasoning |

---

## Update: LightRAG Guardrails Restored (v2.1.2)

After iterative testing, we discovered that strengthening accessibility/mentor tone alone was not enough—some “outline/framework” style queries still drifted into compliance-heavy summaries. The root cause was that our prompt did not consistently enforce LightRAG’s proven step-by-step workflow (intent → extract → weave → cite → references).

In **v2.1.2**, we explicitly re-introduced the LightRAG guardrails from [`lightrag/prompt.py`](https://github.com/HKUDS/LightRAG/blob/main/lightrag/prompt.py) while keeping the GovCon “mentor/consultant” behavior as an agnostic overlay (pattern/theme based, not brittle keyword triggers).

### What Changed

- **Restored LightRAG workflow** (for both `rag_response` and `naive_rag_response`):
  - Determine query intent (and consider conversation history when provided)
  - Scrutinize Context (Knowledge Graph + document chunks for `rag_response`; document chunks only for `naive_rag_response`)
  - Weave facts into a coherent answer using ONLY the Context (no external facts)
  - Track `reference_id` and correlate to `Reference Document List`
  - End with `### References` and output nothing after
- **Added GovCon mentor layer (agnostic)**:
  - Explain “why?” and “so what?” (evidence-based pain points, evaluator resonance for solutions/win themes)
  - For proposal-development questions, organize around proposal structure and integrate compliance within solutioning (avoid disconnected “compliance section” + “ideas section”)
- **Preserved accessibility formatting rules**:
  - No Markdown tables, hierarchical bullets preferred
  - Spell out acronyms on first use
  - Explain specialized systems/tools/metrics briefly when they appear

## Update: Work-Product-First Mentor Layer (v2.1.3)

Even with LightRAG guardrails restored, some responses still defaulted to “compliance recap + shorthand labels” (accurate but not actionable). In **v2.1.3**, we strengthened the GovCon mentor overlay to ensure the model produces an actionable deliverable appropriate to the user’s operational need (capture/proposal/kickoff/estimation), while keeping compliance embedded as constraints/checkpoints rather than the primary output.

### What Changed

- Added a **work-product-first** instruction to the GovCon mentor layer:
  - Choose the most helpful deliverable for the user’s need (e.g., decision brief, proposal-writing outline/storyline, kickoff slide storyline, compliance-to-evaluation mapping, risk register, workload/cost drivers, estimator assumptions list).
  - Embed compliance constraints/checkpoints within the chosen deliverable.
- Added a **minimum rationale standard**:
  - Avoid telegraphic shorthand; any recommendation/solution/claimed strength must include a brief “because…” rationale anchored to cited Context evidence.

## Update: No Ungrounded Solution Buzzwords + No Invented Precision (v2.1.4)

We observed failure modes where the model proposed “solution buzzwords” (e.g., “digital twin”) without defining them, explaining feasibility, or tying them to a grounded mechanism of benefit—resulting in unsupported, consultant-sounding claims. We also observed invented precision (e.g., arbitrary page splits or savings claims) not supported by the Context.

In **v2.1.4**, we tightened the GovCon mentor overlay with two universal guardrails:

- **No ungrounded solution buzzwords**: If proposing a named technique/tool/process, the model must define it in plain English, explain how it works in practice (inputs/outputs/workflow/users), note feasibility/assumptions, and explain customer benefit/evaluator resonance tied to cited Context evidence. If it cannot do this credibly and briefly, it must not propose the idea.
- **No invented precision**: The model must not invent quantitative claims (percentages, page splits, savings, thresholds) unless explicitly supported in the Context. Optional ideas must be labeled as options with tradeoffs.

## Update: Actionability-First (Anti-Compliance-Dump) + No Placeholders (v2.1.5)

We observed that even with improved grounding and mentor tone, the model could still default to “compliance-first shorthand” outputs (accurate but barely usable) and sometimes include placeholders (e.g., “Award+?”) rather than stating what is unknown and what assumption must be validated.

In **v2.1.5**, we tightened the GovCon mentor overlay to:

- **Lead with an actionable work product** instead of a generic compliance recap. Compliance is woven into sections as constraints/checkpoints.
- **Require a brief response plan** at the top (audience/persona, deliverable type, and structure) to keep responses purpose-built across multiple personas (capture, proposal, technical, estimation, kickoff).
- **Require minimum explanation for actions**: each recommended action includes WHY it matters, HOW it would work in practice, and WHAT proof points/artefacts to include.
- **Forbid placeholders/hand-waves**: no “TBD” or “Award+?”; if a value is not in Context, state it is not specified and describe what you would validate as an assumption.

---

## Update: Return to LightRAG Intent (Grounded Q&A WebUI) (v2.2.0)

After testing against the WebUI, we observed a recurring failure mode: responses were *accurate but overly templated* (e.g., “Response Plan / Intended Audience / Work Product Delivered”), and still felt like **shorthand** even when users explicitly requested depth (“focus on quality and not brevity”). This created a “compliance-framework generator” feel that did not match LightRAG’s intended WebUI purpose: **excellent grounded Q&A**.

### What Changed

We refactored `prompts/govcon_prompt.py` for both `rag_response` and `naive_rag_response` to more closely match the upstream LightRAG `prompt.py` structure:

- **Restored LightRAG’s elegant Q&A flow**:
  - intent → extract relevant context → answer → cite → stop
- **Removed the work-product overlay that was overriding WebUI intent**:
  - Removed “produce a useful work product first”
  - Removed “make your response plan explicit” (audience/deliverable/structure boilerplate)
  - Removed the implicit “kickoff brief / compliance matrix” forcing behavior

### What We Kept (Complementary GovCon Clarity Rules)

We kept only the GovCon “spice” that improves readability *without* turning the WebUI into an agent/deliverables tool:

- **Acronym accessibility**: spell out acronyms on first use (e.g., “Performance Work Statement (PWS)”).
- **Chat-friendly formatting**: no Markdown tables; use headings/bullets instead.
- **Explain GovCon concepts briefly** when introduced (e.g., what a Contract Data Requirements List (CDRL) is and why it matters), grounded to Context.
- **Avoid shorthand when the user asks for depth**: add “why/so what” explanation, but still grounded to cited facts.
- **No invented precision / no placeholders** remain in effect.
- **Scope-first framing**: For “scope/service areas” questions, prioritize the narrative scope/task paragraphs (e.g., “Description of Services,” task paragraphs, site appendices) and treat performance objectives/thresholds as secondary “how success is measured.”

---

## Update: LightRAG-Pure Q&A (GovCon Role Only) (v2.2.2)

In practice, adding more prompt constraints increased boilerplate and made responses feel “templated,” even when using a reasoning model. To align with LightRAG’s intended WebUI behavior (excellent grounded Q&A), we moved `rag_response` and `naive_rag_response` closer to upstream **verbatim**.

### What Changed

- `rag_response` and `naive_rag_response` now follow upstream LightRAG structure essentially verbatim:
  - intent → extract relevant context → answer → references → stop
- **Removed** the extra GovCon overlay rules that were steering structure (e.g., response-plan/work-product framing, scope-first heuristics, and additional formatting constraints).
- **Kept only a minimal GovCon adjustment in the Role line**: the assistant is framed as a GovCon specialist (still fully constrained to the provided Context).

### Why

- LightRAG WebUI is best used as a grounded Q&A interface; persona/deliverable shaping belongs in the separate Capture Agent Suite repo (`capture_agent_suite_c5694011.plan.md`).

### Rationale (Strategic Direction)

This aligns with the broader architecture decision:

- **This repo (LightRAG WebUI)** should remain a high-quality, grounded **Q&A interface**.
- Persona/deliverable-specific outputs (kickoff decks, BOE worksheets, compliance matrices, etc.) should move to the separate **Capture Agent Suite repo** (see `.cursor/plans/capture_agent_suite_c5694011.plan.md`) where we can use schema-validated artifacts and deterministic renderers.

## Before/After Examples

### Example 1: Acronym Handling

**BEFORE (Bad):**
```
All personnel must be USNs with SECRET clearance and Geneva Convention CAC. 
Key roles are designated per PWS 5.0 and appendices—replacements NLT 2 weeks, 
notify ACO/COR in 24 hours. Site Manager (SM) and Alternate (ASM) are mandatory 
keys onsite from transition Day 1.
```

**AFTER (Good):**
```
All personnel must be U.S. Nationals (USNs) with SECRET security clearance and 
a Geneva Convention Common Access Card (CAC). Key roles are designated per 
Performance Work Statement (PWS) Section 5.0 and appendices. Replacements must 
be provided no later than (NLT) 2 weeks, with notification to the Administrative 
Contracting Officer (ACO) and Contracting Officer's Representative (COR) within 
24 hours. The Site Manager (SM) and Alternate Site Manager (ASM) are mandatory 
key personnel who must be onsite from transition Day 1.
```

---

### Example 2: Tables vs. Bulleted Lists

**BEFORE (Bad - Tables render poorly in chat):**
```
| Position | Min Qualifications | Strategic Notes |
|----------|-------------------|-----------------|
| Site Manager (SM) | BS Civil Eng (ABET), 10+ years | Empowered to direct subs |
| Alt Site Manager (ASM) | BS Mech Eng (ABET), 6+ years | Covers SM absences |
```

**AFTER (Good - Hierarchical bullets):**
```markdown
**Site Manager (SM) - Key Civil Engineer**
- **Minimum Qualifications:** Bachelor of Science in Civil Engineering from an 
  ABET-accredited program, with at least 10 years of construction and facility 
  maintenance experience
- **Key Skills Required:** Engineering drawings interpretation, specifications 
  review, site assessments, regulatory compliance
- **Desirable (Discriminators):** Airfield pavement experience, Air Force 
  Institute of Technology (AFIT) courses (WMGT131, 301, 417)
- **Strategic Note:** Must be available within 4 hours for government meetings. 
  To differentiate your proposal, emphasize candidates with deployed environment 
  experience.

**Alternate Site Manager (ASM) - Key Mechanical Engineer**
- **Minimum Qualifications:** Bachelor of Science in Mechanical Engineering from 
  an ABET-accredited program, with at least 6 years of construction and facility 
  maintenance experience
- **Key Skills Required:** HVAC systems, plumbing, fire suppression systems, 
  engineering drawings
- **Strategic Note:** Covers SM absences with same authority and availability 
  requirements.
```

---

### Example 3: Justified Win Themes

**BEFORE (Bad - No justification):**
```
Win Theme: "Proven USN team exceeds quals with AFIT certifications, ensuring 
zero gaps in 24/7 mission support."
```

**AFTER (Good - Explained WHY):**
```markdown
**Win Theme Suggestion:** "Proven U.S. National team exceeds qualifications 
with Air Force Institute of Technology (AFIT) certifications, ensuring zero 
gaps in 24/7 mission support."

**Why This Wins:** The recurring requirement for AFIT certifications across 
nearly every position in the PWS suggests the Government has experienced 
problems with contractors who didn't understand Air Force-specific systems 
and engineering standards. By proposing staff who already hold these 
certifications, you demonstrate:
- **Immediate readiness** - No training delays during the critical 8-month 
  base period
- **Reduced Government risk** - Proven understanding of AF processes
- **Compliance confidence** - Staff already familiar with SMS (BUILDER/PAVER), 
  GeoBase, and NexGen IT systems

This directly addresses the PWS Section 5.0 emphasis on qualified personnel 
and the tight timeline for the initial 100% real property inventory.
```

---

### Example 4: Explaining Specialized Concepts

**BEFORE (Bad - Assumes expertise):**
```
Hot Buttons: 100% accountability (e.g., real property assets, GFP inventories), 
zero discrepancies on key metrics, SMS (BUILDER/PAVER) compliance.
```

**AFTER (Good - Educates the reader):**
```markdown
**What the Government Really Cares About (Hot Buttons):**

The PWS reveals several "hot buttons"—Government priorities that, if addressed 
well, can differentiate your proposal:

- **100% Accountability:** The repeated emphasis on tracking every real property 
  asset and Government-Furnished Property (GFP) item suggests the Air Force has 
  experienced inventory management failures at this or similar locations. Your 
  proposal should proactively explain HOW you'll achieve and maintain complete 
  accountability.

- **Zero Discrepancies on Metrics:** Performance standards allow very few errors 
  (typically <=2 discrepancies per month). This tells us the Government values 
  precision and has low tolerance for mistakes—likely due to audit findings or 
  operational impacts from past contractor errors.

- **SMS Compliance:** The Sustainment Management System includes BUILDER (for 
  facility condition assessments) and PAVER (for pavement management). These 
  Air Force-standard systems require certified data managers. Proposing staff 
  already trained on these platforms reduces Government risk.
```

---

## Files Changed

| File | Change |
|------|--------|
| `prompts/govcon_prompt.py` | Re-aligned `rag_response` and `naive_rag_response` to LightRAG’s step-by-step guardrails and layered in GovCon mentor guidance + accessibility rules |

## Testing

To validate the changes, run the same test query through the WebUI and compare:

**Test Query:**
```
What can you tell me about the scope of this contract specifically focusing on 
key personnel, Installation Engineering, Asset Management and Visibility, 
Real Property Services?
```

**Expected Improvements:**
- [ ] Acronyms spelled out on first use
- [ ] Structured data in bullets, not tables
- [ ] Recommendations explain WHY with evidence
- [ ] Consultative, educational tone
- [ ] Non-experts can understand the response

---

## Rollback

If issues arise, revert to previous version:

```bash
git checkout main -- prompts/govcon_prompt.py
```

Or merge the `main` branch to restore production state.

---

## Update: Appendix-Content Semantic Gap Fix (v2.3.0)

**Date:** January 2, 2026

### Problem Diagnosed

When querying "Appendix H workload drivers," the system returned incorrect data (FOPR Staffing Matrix with zero FTEs) instead of the actual aircraft operations data (C-130/C-17 monthly counts).

**Root Cause Analysis (Diagnostic Scripts Used):**
- `tools/diagnose_semantic_gap.py` - Found NO relationships bridging Appendix H to workload entities
- `tools/check_page_53_chunks.py` - Revealed table chunks lost parent section context
- `tools/check_adab_workload_content.py` - Showed "Estimated Monthly Workload Data ADAB" entity existed but contained ONLY the header text, not the actual table data

**Root Cause:**
1. MinerU correctly parsed Appendix H page (53) with 13 blocks: text headers + workload table
2. TEXT-ONLY filter kept headers but **discarded the table** with actual data
3. Entity "Estimated Monthly Workload Data ADAB" was created from header text only
4. **NO relationships** linked "Appendix H" entities to workload content entities
5. Vector search for "Appendix H workload" found Appendix H entities (empty descriptions) → traversed to FOPR Staffing Matrix (wrong table)

### Solution Implemented

Two complementary fixes applied:

#### 1. Section Context Injection (routes.py)

Replaced TEXT-ONLY filter with **Section Context Injector** that:
- Tracks current section as content_list is processed (detects "APPENDIX G/H/I/J/K/L" headers)
- Prepends `[Appendix H (Al Dhafra)]` context to subsequent table blocks
- Keeps tables in processing (no longer filtered out)
- Discards only true artifacts (headers/footers/page_numbers/discarded)

```python
# Before: Tables filtered out, losing critical data
filtered_content = [item for item in content_list if item.get("type") == "text"]

# After: Tables enriched with section context
enriched_content = inject_section_context(content_list)
filtered_content = [item for item in enriched_content if item.get("type") not in DISCARDED_TYPES]
```

#### 2. Appendix-to-Content Relationship Inference (relationship_operations.py)

Added Pattern 6 to `apply_type_based_heuristics()`:
- Finds all Appendix G-L entities
- Links content entities to their parent appendix via:
  - **Section reference matching**: `H.2.0` → Appendix H (confidence: 0.95)
  - **Location name matching**: `ADAB`/`Al Dhafra` → Appendix H (confidence: 0.85)
- Creates `CHILD_OF` relationships for proper graph traversal

```python
# New appendix-content linking logic
appendix_location_map = {
    'G': ['auab', 'al udeid'],
    'H': ['adab', 'al dhafra'],
    'I': ['aasab', 'ali al salem'],
    ...
}
```

### Files Changed

| File | Change |
|------|--------|
| `src/server/routes.py` | Replaced TEXT-ONLY filter with Section Context Injector |
| `src/inference/relationship_operations.py` | Added Pattern 6 for Appendix-to-Content CHILD_OF relationships |

### Testing Required

1. Re-process SWA TAS document:
   ```bash
   # Clear existing workspace
   rm -rf rag_storage/swa_tas
   
   # Restart server
   python app.py
   
   # Upload document via WebUI
   ```

2. Verify query retrieval:
   - Query: "What are the workload drivers in Appendix H?"
   - Expected: C-130/C-17 aircraft operations data with monthly counts
   - NOT: FOPR Staffing Matrix with zero FTEs

3. Verify relationship creation:
   - Check Neo4j for CHILD_OF relationships from workload entities to Appendix H
   ```cypher
   MATCH (e)-[r:CHILD_OF]->(a) 
   WHERE a.entity_name CONTAINS "Appendix H"
   RETURN e.entity_name, r, a.entity_name
   ```

