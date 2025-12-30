# Issue #60: RAG Response Accessibility Enhancement

**Branch:** `feature/60-rag-response-accessibility`  
**Date:** December 2025  
**Version:** 2.1.0

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
| `prompts/govcon_prompt.py` | Added Instruction #5 to `rag_response` and `naive_rag_response` |

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

