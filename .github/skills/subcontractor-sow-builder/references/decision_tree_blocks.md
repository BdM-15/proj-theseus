# Phase 1 Decision Tree — Acquisition Strategy Intake + 6 Scope Blocks

> **Source of truth:** Upstream `1102tools/federal-contracting-skills/skills/sow-pws-builder/SKILL.md`. This file mirrors the questions the upstream skill walks a CO through, adapted for the prime → sub seat.

## Acquisition Strategy Intake (ask FIRST, in a single batched message)

### Intake 1: SOW or PWS?

|                 | SOW                              | PWS                                |
| --------------- | -------------------------------- | ---------------------------------- |
| Prescribes      | Tasks and methods (how)          | Outcomes and standards (what)      |
| Sub flexibility | Low — prime directs approach     | High — sub proposes approach       |
| Best for        | Well-understood, repeatable work | Complex or innovative requirements |
| QASP focus      | Task completion                  | Performance metrics                |
| FAR preference  | —                                | FAR 37.602 prefers PBA / PWS       |

If unsure, default to **PWS**. Decision tree is identical either way; only the output language changes.

### Intake 2: Contract type for the sub agreement?

**FFP | T&M | LH | CPFF | CPAF | CPIF | hybrid (specify by CLIN).**

- **FFP** pairs naturally with PWS (outcomes + performance standards). Sub owns labor mix risk. No labor info in body.
- **T&M / LH** require Section 5 Labor Category Ceiling Hours per FAR 16.601(c)(2). Section 5 tells offerors what LCATs to propose rates against and the ceiling hours per period.
- **CPFF / CPAF / CPIF** pair with SOW or PWS. No labor info in body. Sub must have approved accounting system (FAR 16.301-3) before award. **CPFF MUST identify completion form (16.306(d)(1)) or term form (16.306(d)(2)) in Section 1.1 — never bare 16.306.**
- **Hybrid** — identify which CLINs are which type; apply rules per CLIN.

Recommend (the prime seat MAY recommend, unlike upstream CO seat):

- FFP for well-defined services.
- T&M for requirements where LOE is unknown.
- CPFF term form for R&D where technical success is uncertain.
- CPFF completion form for production-oriented R&D with defined end deliverables.

### Intake 3: Commercial or Non-Commercial?

- **Commercial service (FAR Part 12).** Routinely sold to the general public. Help desk, facility maintenance, COTS support, training, staff augmentation for standard skills. FAR 52.212-4 terms apply; full Section I/L buildout not required. Contract type typically FFP per FAR 12.207. Performance-based description preferred per FAR 12.102(g).
- **Non-commercial (FAR Part 15).** Government-unique work — classified, research, weapon systems, specialized government processes. Full Section I/L clause buildout applies. All contract types available.
- **Unsure** → flag in Section 14 ("Commercial item determination pending — confirm with prime contracts") and proceed.

## Anti-redundancy rule

Before asking any framing or scope question, check whether the user's initial prompt or the workspace KG already answers it. Do not re-ask explicit answers; confirm silently and proceed.

## Phase 1 Scope Decision Blocks (batch 3-4 questions per block)

### Block 1: Mission and Service Model

1. Core service? (provide options based on context, or open-ended if from scratch)
2. Service delivery model: prime FTEs with sub augmentation | fully sub-delivered service | hybrid (specify which functions)
3. Coverage model: business hours (M-F 8-5) | extended hours (specify) | 24/7/365 | seasonal/surge
4. Geographic scope: single site | multi-site (how many?) | virtual/remote | hybrid

### Block 2: Technical Scope

5. Build vs Buy: custom development | COTS/SaaS configuration | hybrid
6. Systems in scope: list all systems sub will build, configure, integrate with, or maintain. For each: new build vs existing.
7. Integration complexity: standalone | integrates with 1-3 systems | integrates with 4+ | enterprise-wide
8. Data migration: no legacy data | migrate from 1-2 sources | migrate from 3+ | complex multi-system consolidation
9. AI/automation: none | basic (IVR, rules-based) | AI-assisted (NLP, ML classification) | advanced AI (chatbots, predictive)

### Block 3: Scale and Volume

10. Transaction/contact volume: numbers if known, or low/medium/high
11. User population: internal users (how many?) | external/public-facing | both
12. Concurrent user requirements (if applicable)
13. Growth: stable | moderate (10-25%/yr) | high (>25%/yr) | unknown

### Block 4: Organizational Scope

14. How many organizational units? (offices, centers, divisions served)
15. Phasing: all at once | phased rollout (how many phases?) | pilot then expand
16. Stakeholder complexity: single program office | multiple offices, single agency | cross-agency

### Block 5: Contract Structure

Contract type already captured in Intake 2 — do NOT re-ask.

17. Period of performance: base year + option years (how many?)
18. Base-year scope: full performance from day 1 | ramp-up/transition-in (how long?) | design/dev only, production in options
19. CLIN structure preference (for chat-only handoff, NOT the body): by period | by function | by deliverable | unsure (skill recommends)
20. Transition: transition-in from incumbent? | transition-out plan? | both

### Block 6: Quality and Oversight

21. Acceptable quality level (AQL) for key metrics: e.g., 95% first-call resolution, 99.95% uptime, <2hr MTTR
22. Reporting cadence: weekly | monthly | quarterly | as-needed
23. Key personnel: which roles must be designated as key? (PM always; others?)

## Decision-to-Staffing Derivation Rules (heuristics, NOT formulas)

| Decision                       | Staffing Implication                                              |
| ------------------------------ | ----------------------------------------------------------------- |
| 24/7 coverage                  | Minimum 3x single-shift headcount for covered roles               |
| Custom development             | 1 architect + 2-4 developers per major system/module              |
| COTS configuration             | 1 architect + 1-2 configurators per platform                      |
| AI/NLP components              | +1-2 data scientists or ML engineers                              |
| 4+ system integrations         | +1-2 integration/middleware engineers                             |
| Data migration from 3+ sources | +1 data engineer + 1 DBA (often time-limited to base year)        |
| Multi-site or 3+ org units     | +1 change management/training specialist per 2-3 units            |
| Contact center volume formula  | volume ÷ 250 days ÷ contacts/agent/day = required agent headcount |
| Agile development              | 1 scrum master or PM per 2 dev teams (team = 5-7 people)          |
| FISMA/security requirements    | +1 information security analyst                                   |
| O&M phase                      | Typically 40-60% of dev-phase staffing                            |
| Transition-in                  | +0.5-1 FTE for knowledge transfer (time-limited)                  |

**These derivations live ONLY in the chat-only Staffing Handoff Table at the end of the run.** They never appear in the SOW/PWS body or any appendix.

## Phase 2 Invocation Gate (Decision Summary)

Before generating the document, present a Phase 1 Decision Summary in chat covering:

- The 3 framing answers (SOW/PWS, contract type, commercial vs non-commercial).
- All derived defaults with one-line rationale for each.
- Section 3 structure (task areas for SOW, performance objectives for PWS).

**STOP. Wait for the user to reply "proceed" (or correct any item) before generating the document.** Do not self-approve. The user is entitled to catch a wrong default before the artifact is locked in.
