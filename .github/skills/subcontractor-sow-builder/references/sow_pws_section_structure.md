# SOW / PWS Section Structure (14-Section Spec)

> **Source of truth:** Upstream `1102tools/federal-contracting-skills/skills/sow-pws-builder/SKILL.md`, MIT © James Jenrette. This file mirrors the prescriptive section ordering and per-section rules.
> **Stance inversion** (this skill writes for the **prime → sub** seat, not federal CO → contractor): see `../UPSTREAM.md`.

## Prescriptive Ordering

Sections appear in the document in the EXACT order shown. Do **not** merge, combine, swap, or rename. If Section 5 (T&M/LH only) is omitted, renumber subsequent sections sequentially but preserve the relative order of all remaining sections.

## Section 1 — Introduction

- 1.1 Purpose
- 1.2 Background (from SOO or user input)
- 1.3 Scope Summary (one paragraph synthesizing all Phase 1 decisions)
- 1.4 Applicable Documents and Standards

**CPFF contracts — explicit form commitment required (FAR 16.306(d)).** Section 1.1 MUST identify whether the contract is **completion form (FAR 16.306(d)(1))** or **term form (FAR 16.306(d)(2))**:

- **Completion form (16.306(d)(1)):** scope described in terms of a definite goal or end product. Contractor must complete and deliver before full fixed fee earned. Use for bounded deliverables (report, prototype, validated model).
- **Term form (16.306(d)(2)):** scope described in general terms; contractor obligated to devote a specified level of effort over a stated period. Fee earned across LOE period. Use for R&D where technical success is uncertain.
- **Default:** when unsure, term form; flag in Section 14 for contracts confirmation.
- **Never** cite bare `FAR 16.306` without the (d)(1) or (d)(2) subparagraph.

## Section 2 — Definitions and Acronyms

## Section 3 — Requirements (the core)

Structure depends on SOW vs PWS:

- **SOW:** organized by task area. Each task: number + title, description (what the contractor shall do), subtasks if applicable, deliverables produced by this task, government-furnished resources for this task.
- **PWS:** organized by performance objective. Each objective: number + title, required outcome (what the contractor shall achieve), performance standard (measurable threshold), Acceptable Quality Level (AQL), method of assessment (inspection / demonstration / analysis / test), incentive or disincentive if applicable.

## Section 4 — Deliverables

Deliverables table: `ID | Title | Description | Format | Frequency | Due Date/Trigger | Acceptance Criteria`.

Standard deliverables to always include: Monthly Status Report, Transition-In Plan (if applicable), Transition-Out Plan, System Documentation, Training Materials.

## Section 5 — Labor Category Ceiling Hours (T&M / LH ONLY)

**T&M / LH only — FAR 16.601(c)(2).** Title: "Labor Category Ceiling Hours". Single table telling offerors which labor categories the prime expects them to propose rates against and the ceiling hours per LCAT per period. **Pricing risk-sharing mechanism, NOT a staffing prescription.**

Fixed columns: `Labor Category | Base Year Ceiling Hours | OY1 | OY2 | OY3 | OY4 | Total Ceiling`. Do NOT include SOC codes, FTE counts, "derivation basis", or anything resembling the chat-only Staffing Handoff.

**For FFP and CR contracts:** OMIT Section 5 entirely and renumber subsequent sections. Do NOT substitute a CLIN table, pricing schedule, or any other pricing content.

## Section 6 — Period of Performance

## Section 7 — Place of Performance

## Section 8 — Government-Furnished Property / Information

## Section 9 — Security Requirements

- **Unclassified contracts:** information safeguarding (FAR 52.204-21 Basic Safeguarding; NIST SP 800-171 when CUI in scope), personnel suitability (Public Trust at appropriate tier), agency baseline (GSA IT security policy, DHS MD 11042.1, NASA IT security standards, etc.).
- **Classified contracts — REQUIRED references when any clearance at Confidential or higher is called out:**
  - **DD Form 254 (Contract Security Classification Specification).** State that a DD Form 254 will be issued at contract award and incorporated by reference.
  - **Security Classification Guide (SCG).** Reference applicable SCG by title (or placeholder "[program-specific SCG to be identified in DD 254]").
  - **Clearance by position and facility.** Identify clearance level for each position category, facility clearance requirement (e.g., ICD 705-accredited SCIF), and program-specific access (polygraph, NdA, read-on).
  - **Derivative classification and OPSEC.** EO 13526, applicable ISOO regulations, derivative-classification training (typically annual). Address OPSEC obligations.
  - **Incident reporting.** Cite agency-specific classified-incident reporting timelines (typically 1 hour to Government security officer).
  - **NISPOM** applies to cleared contractor facilities; cite as applicable.

## Section 10 — Key Personnel

- Roles, minimum qualifications, certification requirements.
- Only roles where the prime needs approval of specific individuals.
- Substitution language: state that substitution of any Key Personnel requires prior written approval.
- **Do NOT cite FAR 52.237-2** — that clause is "Protection of Government Buildings, Equipment, and Vegetation" and has nothing to do with Key Personnel substitution. Use the agency-appropriate clause (see `far_citations.md`).
- **DO NOT include FTE counts, labor category counts, SOC codes, hours-per-year, staffing tables, or any "how many" information** in Section 10 or anywhere else in the body. FAR 37.102(d) requires the requirement to be described in terms of results, not hours or number of people.

## Section 11 — Reporting and Oversight

- Reporting schedule and content requirements.
- Meeting cadence (kickoff, weekly status, monthly program review, quarterly executive).
- Points of contact.

## Section 12 — Quality Assurance Surveillance Plan (QASP) Summary

- Performance metrics table: `Metric | Standard | AQL | Method | Frequency | Payment Consequence`.
- For SOW documents, title this section "Inspection and Acceptance" and cite FAR 52.246-series clauses as the inspection basis. For PWS documents, keep "QASP Summary" and cite FAR 37.602 / 46.401. Table structure identical; label and legal basis differ.
- **CRITICAL: Do NOT tie QASP thresholds to CPARS ratings.** CPARS (FAR 42.15) is a separate post-performance evaluation with fixed FAR rating categories (Exceptional / Very Good / Satisfactory / Marginal / Unsatisfactory) based on the CO's judgment across the full factor set. It is NOT QASP-bindable and cannot be pre-committed in a SOW/PWS. Writing "95% threshold = CPARS Satisfactory" is both legally wrong and defeats performance-based acquisition.

**The Payment Consequence column must describe what happens to payment or contract administration when the threshold is missed.** Acceptable examples:

- "Below threshold: 5% deduction on the monthly invoice for the affected objective."
- "Below AQL for two consecutive months: cure notice issued per FAR 52.212-4(m)."
- "Three consecutive months below threshold: consideration for termination for cause / default."
- "Exceeding threshold by X%: positive incentive fee of $Y per [period] (CPIF / award-fee only)."
- "Acceptance withheld until correction; re-performance at no additional cost."

Do NOT put CPARS ratings, CPARS thresholds, or the words "Satisfactory / Exceptional / Very Good / Marginal / Unsatisfactory" in the Payment Consequence column.

## Section 13 — Transition

- 13.1 Transition-In (if applicable): knowledge transfer, incumbent cooperation, parallel operations.
- 13.2 Transition-Out: data return, documentation, contractor cooperation, timeline.

## Section 14 — Constraints and Assumptions

Document each derived default using a 4-column table: `ID | Assumption/Default Applied | Rationale | Action Required`. Mark each item `[DEFAULT]` so the user can scan for items requiring confirmation before issue.

**Workflow C (Scope Reduction).** When documenting reductions in Section 14, describe prior and revised scope in CAPABILITIES AND COVERAGE, not staffing counts. The body remains subject to FAR 37.102(d) even for historical / prior-state descriptions. Compliant: "Prior: standing detection-engineering capability; Revised: cadence-based deliverable model (12 detections/quarter)." Non-compliant: "Prior: 2-3 FTE; Revised: 1 FTE." Each cut block uses: `Prior Scope (capability) | Revised Scope (capability) | Estimated Annual Savings | Rationale | Residual Risk`.

## Authorized Appendices (the ONLY allowed set)

- A: Current Environment Description
- B: Volume Data and Historical Metrics
- C: System Interface Specifications
- D: Acronym List

Include only those applicable; omit the rest. **DO NOT** create any staffing-related appendix under any title (variants seen in practice and FORBIDDEN: "Implied Staffing Table", "IGCE Handoff", "FTE Allocation", "Labor Category Staffing"). The staffing handoff is a separate chat-output artifact (see SKILL.md Workflow Step 7); it does not belong anywhere in this document, including as a supplement after Appendix D.

## Document Review Checklist

Before presenting the final artifact, verify:

- [ ] Every task / objective in Section 3 maps to at least one deliverable in Section 4.
- [ ] Every deliverable in Section 4 has acceptance criteria.
- [ ] Key Personnel roles in Section 10 do not quantify the workforce.
- [ ] Security requirements (Section 9) consistent throughout the document.
- [ ] Period of performance (Section 6) matches the phasing decisions from Phase 1 Block 5.
- [ ] QASP metrics in Section 12 are measurable and have defined AQLs.
- [ ] QASP Payment Consequence column contains payment / admin consequences, NOT CPARS ratings.
- [ ] No CLIN table, pricing schedule, or Section B content in the document body.
- [ ] Transition-in / -out timelines (Section 13) are realistic.
- [ ] No orphaned requirements (stated in Section 3 but never deliverable-mapped).
- [ ] No scope gaps (Phase 1 decisions not reflected in Section 3).
- [ ] CPFF contracts: Section 1.1 cites (d)(1) or (d)(2), never bare 16.306.
- [ ] Section 5 present iff contract type is T&M or LH; absent otherwise.
- [ ] Section 10 does NOT cite FAR 52.237-2 for Key Personnel substitution.
- [ ] No FTE counts, SOC codes, hours-per-year, or staffing tables anywhere in the body or any appendix.
