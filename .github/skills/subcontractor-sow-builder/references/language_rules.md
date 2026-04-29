# Language Rules — SOW vs PWS Verb Patterns and Anti-Patterns

> Source: upstream `sow-pws-builder` Phase 2 Language Rules section. Mirrored verbatim for the prime → sub seat.

## SOW Language

**Pattern:** "The contractor shall [verb]..."

**Verbs:** prescriptive, task-oriented. Examples:

- The contractor shall **perform** monthly system patching across all production servers.
- The contractor shall **deliver** a quarterly system architecture review.
- The contractor shall **maintain** a configuration management database.
- The contractor shall **provide** Tier 2 user support during business hours.

## PWS Language

**Pattern:** "The contractor shall achieve / maintain / ensure..."

**Verbs:** outcome-oriented, measurable. Examples:

- The contractor shall **achieve** 99.9% system availability during business hours.
- The contractor shall **maintain** mean-time-to-resolve (MTTR) of less than 4 hours for Severity 2 incidents.
- The contractor shall **ensure** all CUI is handled in compliance with NIST SP 800-171.

## Anti-Patterns (avoid)

| Anti-pattern                                                     | Why it fails                                                      | Compliant alternative                                        |
| ---------------------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------ |
| "Support" as a standalone verb                                   | Too vague — support how?                                          | Specify the deliverable or outcome being supported.          |
| "As needed" or "as required" without defined trigger             | CO retains unilateral discretion; sub cannot price the obligation | Define the trigger event, frequency, or threshold.           |
| "Best practices" without citing a standard                       | Unverifiable; ghost requirement                                   | Cite the specific standard (NIST, ISO, ITIL, etc.).          |
| "Coordinate with" without specifying the deliverable or decision | Coordination is meeting overhead, not a requirement               | Specify the deliverable, decision, or artifact that results. |
| Requirements that cannot be measured or verified                 | Untestable; contractor cannot demonstrate compliance              | Add a measurable threshold, AQL, or method of assessment.    |

## SMART Test (every requirement)

Each requirement in Section 3 must be:

- **S**pecific
- **M**easurable
- **A**chievable
- **R**elevant
- **T**ime-bound

If a requirement fails any of these, flag it during assembly and either rewrite or move to Section 14 as an open assumption.

## Document-Wide Discipline

- **No staffing language in the body.** No FTE counts, no SOC codes, no labor category counts, no hours-per-year. Even when describing prior-state scope reductions in Section 14, describe in CAPABILITIES AND COVERAGE, not staffing counts. FAR 37.102(d) governs.
- **No CLIN tables in the body.** CLINs live in the prime↔sub subagreement Section B (chat-only handoff at end of run).
- **Cite the specific FAR subsection.** Never bare `FAR 16.306`, `FAR 16.601`, `FAR 52.246` — always with the controlling subparagraph.
