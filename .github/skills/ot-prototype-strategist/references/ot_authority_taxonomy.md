# OT Authority Taxonomy

Statutory framework for Other Transactions. **Always pinned to 10 USC** (Title 10, US Code), not the FAR. OTs operate outside the FAR by design.

## 1. The Three Authorities

| Authority          | Purpose                                                 | DoD Components Eligible                               |
| ------------------ | ------------------------------------------------------- | ----------------------------------------------------- |
| **10 USC 4021**    | **Research** — basic, applied, advanced research        | DoD-wide                                              |
| **10 USC 4022**    | **Prototype projects** — develop a prototype            | DoD + DHS (FEMA) + DOT (FAA) + ODNI (per delegations) |
| **10 USC 4022(f)** | **Production follow-on** to a successful 4022 prototype | Same as 4022                                          |

### How to pick

Read the solicitation language:

- "research authority", "basic / applied / advanced research", university / FFRDC focus → **4021**
- "prototype project", "develop a prototype", "demonstrate at TRL X", explicit TRL exit gate → **4022**
- "transition to production", "production follow-on", "successful prototype completion enables…" → **4022(f)** (must have an existing successful 4022 prototype as predecessor)

If the solicitation cites both 4021 and 4022, treat as 4022 unless work is purely research with no prototype deliverable.

## 2. Prototype Definition (10 USC 4003)

A "prototype project" must address one or more of:

1. Proof of concept of a new technology
2. Reduction of technical risk for an existing capability
3. Validation of innovative production processes or technology
4. Demonstration of new technology in a relevant operating environment

If the proposed work doesn't fit any of the four, it's not a 4022 prototype — likely 4021 research or a production contract under FAR.

## 3. 10 USC 4022(d) Cost-Share Paths

The statute requires the AO to find one of four conditions before awarding a 4022 prototype OT to a non-traditional / non-NDC team.

| Path  | Subsection    | Trigger                                                                                                                                                 | Cost share required                 | Significance test                                                       |
| ----- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------- |
| **A** | 4022(d)(1)(A) | At least one **non-traditional defense contractor (NDC)** participates significantly.                                                                   | **None** (no statutory share)       | "Significant" — typically ≥33% work-share (AO judgment, no statutory %) |
| **B** | 4022(d)(1)(B) | All significant participants are **small businesses** OR **non-profit research orgs**.                                                                  | **None**                            | "Significant participation" — AO judgment.                              |
| **C** | 4022(d)(1)(C) | At least **one-third of the total cost** is paid by parties other than the federal government.                                                          | **Yes — 1/3 minimum** of total cost | Statutory 33.3% performer share.                                        |
| **D** | 4022(d)(1)(D) | Senior procurement executive determination that **exceptional circumstances** justify the OT (often paired with competition commitment for production). | **None** (special authority)        | Senior official's written determination required.                       |

### NDC test (10 USC 3014)

A "non-traditional defense contractor" is an entity that, **for the period of one year prior** to the solicitation:

- Has **NOT** been required to comply with **full-coverage Cost Accounting Standards (CAS)** on a DoD prime contract or sub.
- Note: This is a **CAS-coverage test**, NOT a dollar-threshold test. A vendor with $50M in DoD revenue can still be NDC if all of it was modified-CAS or CAS-exempt (commercial item, T&M < $7.5M, FFP commercial, OTs themselves).

The NDC determination is made by the **AO**, not the bidder. We surface the test; we do not render a binding eligibility opinion.

### Path-selection economics (capture team perspective)

For a $3.0M project:

| Path | Government obligation | Performer out-of-pocket | Strategic note                                                    |
| ---- | --------------------- | ----------------------- | ----------------------------------------------------------------- |
| A    | $3.0M                 | $0                      | **Optimal** — team with NDC at ≥33% work-share                    |
| B    | $3.0M                 | $0                      | Optimal if eligible (rare for prime captures)                     |
| C    | $2.0M                 | $1.0M                   | $1M out-of-pocket — only viable if must-win + IRAD-fundable       |
| D    | $3.0M                 | $0                      | Rare; senior-official-driven; usually paired with prod commitment |

If we're a traditional prime, the dominant strategy is to **find an NDC sub at ≥33% work-share** to clear path A. The teaming overhead is almost always cheaper than the 1/3 share.

## 4. Production Follow-On (10 USC 4022(f))

After a successful 4022 prototype completion, the AO may award a follow-on production contract or transaction to the prototype performer **without further competition**. Critical mechanics:

- **Path determination inherits** from the predecessor prototype (path A prototype → path A production-follow-on).
- **Cost-share ratio does NOT propagate.** Even if the prototype was path C with 1/3 performer share, **production is funded 100% by the government.** Cost share is statutorily a prototype-only construct.
- The follow-on may be a FAR contract (typically FFP) or another OT. AO discretion.

## 5. Consortium-Brokered OTs

Most modern prototype OTs flow through a consortium rather than direct bilateral agreement. Add a management fee on top of government obligation (NOT deducted from performer share):

| Consortium                 | Typical fee | Notes                                       |
| -------------------------- | ----------- | ------------------------------------------- |
| **DIU**                    | 5%          | OSD program, software-heavy prototype focus |
| **AFWERX**                 | 3-5%        | Air Force innovation                        |
| **NSTXL**                  | 4-5%        | National Security Technology Accelerator    |
| **MTEC**                   | 5-7%        | Medical Technology Enterprise Consortium    |
| **SOSSEC**                 | 4-5%        | System of Systems Consortium                |
| **Direct (no consortium)** | 0%          | Bilateral with the agency AO                |

If the user doesn't specify, default to consortium-brokered when the agency is DIU/AFWERX/SOFWERX/SpaceWERX/NavalX; default to direct when the agency is the program office itself (NAVSEA, AFRL, ARL, etc.).

## 6. AO vs FAR-CO

- **Agreements Officer (AO)** awards OTs. Distinct from FAR Contracting Officer (CO). AO has broad discretion on terms; not bound by FAR 15 evaluation methodology.
- Price reasonableness is **AO judgment**, not FAR 15.404-4 cost or price analysis. AO may use cost analysis, market analysis, comparison to prior efforts, or any reasonable basis.
- We can still pull market wages from BLS and CALC+ to anchor our bid — the AO is likely doing the same — but cite our methodology as "market benchmarking", not "FAR 15.404 cost analysis."
