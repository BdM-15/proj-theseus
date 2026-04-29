# FAR Citations & Trap Detector — RFP Reverse Engineer

This skill READS a federal RFP and detects whether the CO cited the right FAR sections, the right subsections, and avoided the common compliance traps. When a trap is detected, emit a `clarification_questions[]` entry so the capture team can file Q&A.

## Section E — Trap Detector

### Trap 1: FAR 52.237-2 Cited as Key Personnel Substitution Clause

**The mistake.** Document Section 10 (Key Personnel) cites `FAR 52.237-2` as the substitution clause.

**Why it's wrong.** FAR 52.237-2 is "Protection of Government Buildings, Equipment, and Vegetation". It governs damage to government property by contractor personnel. It has **NOTHING** to do with Key Personnel substitution.

**What it usually signals.** A copy-paste error from a prior contract, or a CO who pulled the wrong clause from a clause library. Either way, the proposal team should:

1. Not blindly comply with a non-existent obligation.
2. File Q&A asking the CO to confirm the intended clause.
3. Plan to propose against the agency-appropriate clause:
   - NASA: NFS 1852.237-72.
   - DHS: HSAR 3052.237-72.
   - HHS: HHSAR 352.237-75.
   - Generic / unknown: FAR 52.237-3 (Continuity of Services).

**Detector logic.** Search for `52.237-2` near any "Key Personnel" / "substitution" language. Emit `key_personnel_clause_check.status = 'incorrect'` with quoted text and chunk ID.

### Trap 2: Bare `FAR 16.306` Cited for CPFF

**The mistake.** Document cites `FAR 16.306` without specifying `(d)(1)` (completion form) or `(d)(2)` (term form).

**Why it's wrong.** FAR 16.306(d) explicitly distinguishes the two forms with different fee-earning mechanisms. A bare cite leaves the bidder unable to determine:

- Whether to bid completion deliverables vs LOE.
- Whether full fee is earned on delivery vs across the period.
- Whether scope is bounded by an end product vs by hours.

**Detector logic.** Search for `FAR 16.306` matches; check whether any matched citation is followed by `(d)(1)` or `(d)(2)`. If neither, emit `cpff_form_signal.status = 'ambiguous'` and a `clarification_questions[]` entry.

### Trap 3: QASP Payment Consequence Column Contains CPARS Rating Language

**The mistake.** Section 12 QASP "Payment Consequence" or equivalent column contains words like `Satisfactory`, `Exceptional`, `Very Good`, `Marginal`, `Unsatisfactory`, or "will affect CPARS rating".

**Why it's wrong.** CPARS (FAR 42.15) is a separate post-performance evaluation with fixed rating categories applied by CO judgment. CPARS ratings are NOT QASP-bindable. Pre-committing CPARS ratings in a QASP both:

1. Violates the CO's discretion under FAR 42.15.
2. Gives the bidder no actionable payment consequence to price against.

**Detector logic.** Search the Section 12 / QASP / Inspection-and-Acceptance chunks for the CPARS rating words. If found in Payment Consequence context, emit `qasp_cpars_check.status = 'non-compliant'`.

### Trap 4: T&M / LH Without Section 5 Ceiling-Hours Table

**The mistake.** Contract type signaled as T&M or LH (via FAR 52.232-7 cite, fully-burdened labor rate cost-volume request, etc.) but no Section 5 / Labor Category Ceiling Hours table present.

**Why it's wrong.** FAR 16.601(c)(2) requires a stated ceiling on hours for T&M / LH. Without it, the bidder cannot price the ceiling and the CO cannot enforce one.

**Detector logic.** If contract-type inference returns T&M or LH, check for presence of a Section 5 ceiling-hours table. If absent, emit a `clarification_questions[]` entry asking for the ceiling-hours table.

### Trap 5: Section 5 Present for FFP or CR Contracts

**The mistake.** Section 5 / Labor Category Ceiling Hours appears in an FFP or CR contract.

**Why it's wrong.** Section 5 is a T&M/LH-specific risk-sharing mechanism. Including it in FFP signals confused contract-type drafting; in CR it signals confusion between ceiling hours and CPFF LOE.

**Detector logic.** If contract-type inference is FFP or CR, check for Section 5 presence. If found, emit a `clarification_questions[]` entry asking for clarification.

### Trap 6: FTE Counts / SOC Codes / Staffing Tables in the Body

**The mistake.** Document body or any appendix contains FTE counts, SOC codes, hours-per-year, or staffing tables outside the chat-only Staffing Handoff context.

**Why it's wrong.** FAR 37.102(d) requires the requirement to be described in terms of results, not hours or number of people. Staffing in the body locks the bidder into a labor mix and defeats performance-based acquisition.

**Detector logic.** Scan all chunks for SOC code patterns (`\d{2}-\d{4}`), "FTE" tokens, or labor category counts. If found in Section 3, Section 10, or any appendix, emit a `clarification_questions[]` entry recommending the bidder over-document own staffing assumptions in the proposal.

## Quick-Reference: FAR Sections this Skill Reads

| FAR Cite              | Signals                                                   |
| --------------------- | --------------------------------------------------------- |
| **37.102(d)**         | Performance-based; no FTE counts in body — drives Trap 6. |
| **37.602**            | PWS preferred; signals PWS in Section 12.                 |
| **46.401**            | Government QA basis; signals QASP.                        |
| **16.202**            | FFP.                                                      |
| **16.301-3**          | Approved accounting system prereq → CR.                   |
| **16.305**            | CPAF.                                                     |
| **16.306(d)(1)**      | CPFF completion form.                                     |
| **16.306(d)(2)**      | CPFF term form.                                           |
| **16.404**            | CPIF.                                                     |
| **16.601(c)(2)**      | T&M / LH ceiling hours.                                   |
| **52.232-7**          | Payments under T&M / LH.                                  |
| **52.246-2/-4/-5/-6** | Inspection clauses → SOW Section 12.                      |
| **52.244-6**          | Subcontracts for commercial items (flowdown).             |
| **52.204-21**         | Basic Safeguarding (unclassified).                        |
| **52.212-4**          | Commercial item terms (Part 12 contracts).                |
| **52.237-2**          | **NOT Key Personnel — Trap 1 detector.**                  |
| **52.237-3**          | Continuity of Services — fallback Key Personnel clause.   |
| **42.15**             | CPARS — Trap 3 detector.                                  |

## Output Discipline

Every detector emits structured fields, NOT free prose:

```json
{
  "key_personnel_clause_check": {
    "status": "incorrect | correct | absent | n/a",
    "cited_clause": "FAR 52.237-2",
    "source_chunk_ids": ["..."],
    "recommended_alternative": "FAR 52.237-3 (or agency-specific)",
    "explanation": "FAR 52.237-2 governs property protection, not Key Personnel substitution."
  },
  "cpff_form_signal": {
    "status": "completion | term | ambiguous | n/a",
    "cited_clause": "FAR 16.306",
    "source_chunk_ids": ["..."]
  },
  "qasp_cpars_check": {
    "status": "compliant | non-compliant | absent | n/a",
    "offending_text": "...",
    "source_chunk_ids": ["..."]
  }
}
```

Always emit ALL trap-detector fields, even when status is `n/a` or `absent`, so the proposal team can verify nothing was skipped.
