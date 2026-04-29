# FAR Citations — Subcontractor SOW/PWS Builder

This skill cites FAR sections drawn from the upstream `sow-pws-builder` and translated to the prime → sub seat. Always cite the specific subsection where one is given (e.g., 16.306(d)(2), not bare 16.306).

## Core Citations (used in nearly every run)

| FAR Cite      | Topic                                                                              | Where it appears in the SOW/PWS                                                                                                                          |
| ------------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **37.102(d)** | Describe the requirement in terms of results, NOT hours or number of people        | Drives the "no FTE counts in body" rule. Cited in Section 14 if any reduction language describes capabilities (compliant) vs FTE counts (non-compliant). |
| **37.602**    | Performance-based acquisition (PBA) is the preferred method for acquiring services | Cited in Section 12 (PWS QASP basis) and Section 14 (intake rationale for PWS over SOW).                                                                 |
| **46.401**    | Government contract quality assurance                                              | Cited in Section 12 alongside 37.602 as QASP basis.                                                                                                      |
| **7.105**     | Written acquisition plans — requirement description                                | Background reference for the prime's own contracts file.                                                                                                 |

## Contract-Type Citations

| Contract Type        | FAR Cite                             | Notes                                                                                                              |
| -------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| FFP                  | **16.202**                           | Default for commercial services. No Section 5.                                                                     |
| FFP commercial       | **12.207**                           | Authorized contract type for commercial-item acquisitions under Part 12.                                           |
| T&M                  | **16.601** with **(c)(2)** mandatory | Section 5 Labor Category Ceiling Hours table required. Never bare 16.601.                                          |
| LH                   | **16.601** with **(c)(2)** mandatory | Same as T&M; Section 5 required.                                                                                   |
| CPFF completion form | **16.306(d)(1)**                     | Bounded deliverable; full fee on delivery. Section 1.1 explicit cite.                                              |
| CPFF term form       | **16.306(d)(2)**                     | Level of effort over period; fee earned across period. Section 1.1 explicit cite. **Default when unsure for R&D.** |
| CR (any)             | **16.301-3**                         | Approved accounting system prereq before award. Cited in Section 14 as a sub-side prereq the prime must verify.    |
| CPAF                 | **16.305**                           | Award fee plan separate doc.                                                                                       |
| CPIF                 | **16.404**                           | Share ratio + min/max fee.                                                                                         |

**Never** cite bare `FAR 16.306` for CPFF — always with `(d)(1)` or `(d)(2)`.

## Security & Safeguarding

| FAR / Reg Cite               | Topic                                                        | Section                                     |
| ---------------------------- | ------------------------------------------------------------ | ------------------------------------------- |
| **52.204-21**                | Basic Safeguarding of Covered Contractor Information Systems | Section 9, unclassified contracts           |
| **NIST SP 800-171**          | Protecting CUI in nonfederal systems                         | Section 9, when CUI in scope                |
| **EO 13526**                 | Classified National Security Information                     | Section 9, classified contracts             |
| **NISPOM** (32 CFR Part 117) | National Industrial Security Program                         | Section 9, cleared facilities               |
| **ICD 705**                  | Physical and technical security standards for SCIFs          | Section 9, when SCIF accreditation required |
| **DD Form 254**              | Contract Security Classification Specification               | Section 9, ALL classified contracts         |

## Travel & ODCs

| FAR Cite        | Topic                                            | Notes                                                                                 |
| --------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------- |
| **31.205-46**   | Travel costs                                     | Cited on the chat-only CLIN Handoff travel CLIN as "Cost-reimbursable (NTE); no fee". |
| **52.212-4**    | Contract terms and conditions — commercial items | Section 9 / Section 14 for commercial subagreements.                                  |
| **52.212-4(m)** | Termination for cause / cure notice              | Acceptable Payment Consequence in Section 12 QASP.                                    |

## Inspection & Acceptance (SOW Only)

For SOW documents, Section 12 retitled "Inspection and Acceptance" cites the FAR 52.246-series:

| FAR Cite     | Topic                                         |
| ------------ | --------------------------------------------- |
| **52.246-2** | Inspection of supplies — fixed price          |
| **52.246-4** | Inspection of services — fixed price          |
| **52.246-5** | Inspection of services — cost-reimbursement   |
| **52.246-6** | Inspection — time-and-material and labor-hour |

## Key Personnel Substitution Clauses (CRITICAL — DO NOT use 52.237-2)

**FAR 52.237-2 is "Protection of Government Buildings, Equipment, and Vegetation".** It has NOTHING to do with Key Personnel substitution. Citing it as the Key Personnel clause is a common error and a red flag.

Use the agency-appropriate clause:

| Agency                   | Clause                                                | Title                                                                                                                         |
| ------------------------ | ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| NASA                     | **NFS 1852.237-72**                                   | Access to Sensitive Information / Key Personnel substitution governance                                                       |
| DHS                      | **HSAR 3052.237-72**                                  | Key Personnel or Facilities                                                                                                   |
| HHS                      | **HHSAR 352.237-75**                                  | Key Personnel                                                                                                                 |
| DoD                      | agency-specific DFARS supplement clause if applicable | varies                                                                                                                        |
| Generic / unknown agency | **FAR 52.237-3**                                      | Continuity of Services — covers continuity obligations; leave Key Personnel substitution as contract-specific custom language |

**Never emit `FAR 52.237-2` as the Key Personnel substitution clause.**

## QASP / CPARS Boundary (CRITICAL)

- **QASP** is forward-looking, threshold-based, payment-binding (Section 12).
- **CPARS** (FAR 42.15) is post-performance evaluation with fixed rating categories (Exceptional / Very Good / Satisfactory / Marginal / Unsatisfactory) bound to CO judgment across the full factor set.
- **CPARS is NOT QASP-bindable.** Do NOT put CPARS rating words in the QASP Payment Consequence column. Use payment / contract-admin consequences instead (deductions, cure notices, re-performance, terminations, incentive fees on CPIF/award-fee only).

## Common Citation Traps (audit before write)

1. Bare `FAR 16.306` cited for CPFF (must be `(d)(1)` or `(d)(2)`).
2. `FAR 52.237-2` cited for Key Personnel substitution (wrong clause — see table above).
3. CPARS rating language (`Satisfactory`, `Exceptional`, etc.) appearing in Section 12 Payment Consequence column.
4. Bare `FAR 16.601` cited for T&M / LH without `(c)(2)` (which is the actual ceiling-hours authority).
5. Section 5 included for FFP or CR contracts (Section 5 is T&M/LH ONLY).
6. Section 5 table containing SOC codes or FTE counts (it's a ceiling-hours pricing mechanism, not staffing).
7. FTE counts, SOC codes, or staffing tables appearing anywhere in the document body or any appendix (FAR 37.102(d) violation).
