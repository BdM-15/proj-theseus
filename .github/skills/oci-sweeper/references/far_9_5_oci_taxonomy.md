# FAR Subpart 9.5 — OCI Taxonomy Reference

**Authority:** FAR Subpart 9.5 — Organizational and Consultant Conflicts of Interest (sections 9.500–9.508).
**Companion file:** `oci_remediation_playbook.md` for mitigation patterns; `relationship_query_patterns.md` for the Cypher snippets that surface candidate parties.

> **Scope of this reference.** Only OCI under FAR Subpart 9.5 is in scope. Personal conflicts of interest (FAR 3.11), post-employment restrictions (18 U.S.C. § 207), and procurement integrity (FAR 3.104) are intentionally **out of scope** for the `oci-sweeper` skill — separate concerns, separate workflows.

---

## 1. Statutory anchor (FAR 9.500–9.502)

> "An OCI may result when factors create an actual or potential conflict of interest on an instant contract, or when the nature of the work to be performed on the instant contract creates an actual or potential conflict of interest on a future acquisition." — FAR 9.501

The contracting officer (KO) is the decision-maker (FAR 9.504(a)). The bidder's job — and this skill's job — is to **identify** the conflict, **classify** it, and **propose mitigations**. The skill never declares that an OCI does or does not exist.

---

## 2. The three conflict classes (FAR 9.505)

FAR 9.505 enumerates three distinct conflict classes. Every finding produced by `oci-sweeper` MUST be tagged with **exactly one** class. If a single situation triggers two classes (e.g., the incumbent both wrote the SOW _and_ has prior-contract data access), emit **two** findings.

### 2.1 `biased_ground_rules` — FAR 9.505-1, 9.505-2

The contractor (or a teaming partner / sub) **set the ground rules** for the competition — wrote the SOW/PWS, drafted the requirement, performed market research that shaped the strategy, or responded to the sources sought in a way that scoped the buy.

| FAR section | Trigger                                                          |
| ----------- | ---------------------------------------------------------------- |
| 9.505-1     | Contractor providing systems engineering and technical direction |
| 9.505-2     | Contractor preparing specifications or work statements           |

**Disqualification default:** A contractor that prepares a complete specification or work statement for non-developmental items is generally **excluded from competing** for the resulting contract (FAR 9.505-2(a)(1)). Mitigation is hard.

### 2.2 `unequal_access` — FAR 9.505-4

The contractor (or a teaming partner / sub) had access to **non-public information** through prior or concurrent contracts that gives them a competitive advantage on the instant bid.

| FAR section | Trigger                                                                                            |
| ----------- | -------------------------------------------------------------------------------------------------- |
| 9.505-4     | Contractor obtaining proprietary or source-selection-sensitive info from another contractor or USG |

**Mitigation default:** This class is **routinely mitigatable** with NDAs, data segregation, and firewalls (FAR 9.505-4(b)). The KO usually accepts a credible mitigation plan.

### 2.3 `impaired_objectivity` — FAR 9.505-3

The contractor (or a teaming partner / sub) is being asked to **evaluate themselves or a closely related party**. The classic SETA / IV&V conflict.

| FAR section | Trigger                                                                 |
| ----------- | ----------------------------------------------------------------------- |
| 9.505-3     | Contractor evaluating its own offer, products, services, or competitors |

**Disqualification default:** Hard mitigation. Firewalls rarely work because the conflict is in the contractor's _judgment_, not in their _information_. Recusal or divestiture is often the only acceptable path.

---

## 3. Decision matrix

Use this matrix to classify a candidate finding. The columns ask "what does the conflict come from?", and the rows ask "where in the procurement timeline does it bite?".

| Conflict source ↓ \\ When ↓                                | **Set the rules** (pre-RFP) | **Held the data** (info advantage) | **Will judge own work** (objectivity) |
| ---------------------------------------------------------- | --------------------------- | ---------------------------------- | ------------------------------------- |
| Bidder / teammate wrote the SOW or PWS                     | `biased_ground_rules`       | —                                  | —                                     |
| Bidder did market research that shaped the buy             | `biased_ground_rules`       | —                                  | —                                     |
| Bidder had a predecessor contract in the same scope        | maybe `biased_ground_rules` | `unequal_access`                   | —                                     |
| Bidder has access to competitor proprietary data           | —                           | `unequal_access`                   | —                                     |
| Bidder will evaluate their own deliverables                | —                           | —                                  | `impaired_objectivity`                |
| Bidder will perform IV&V, QA, or oversight on related work | —                           | —                                  | `impaired_objectivity`                |
| Bidder is a SETA on the program AND bidding the prime      | maybe `biased_ground_rules` | `unequal_access`                   | `impaired_objectivity`                |

When the situation maps to multiple cells, emit one finding per cell.

---

## 4. Severity ladder

Per-finding severity drives the overall risk level rubric below.

| Severity | When to use                                                                                                                |
| -------- | -------------------------------------------------------------------------------------------------------------------------- |
| `low`    | Indirect / attenuated overlap; standard NDA + firewall is the textbook fix; no FAR 9.505-2(a)(1) disqualification trigger. |
| `medium` | Direct overlap requiring a written mitigation plan and KO concurrence; some risk of KO non-acceptance.                     |
| `high`   | Likely disqualification (FAR 9.505-2(a)(1) or 9.505-3) OR the only mitigation is `no_acceptable_mitigation`.               |

---

## 5. Risk Level Rubric

Set `overall_risk_level` per the highest-severity finding present:

| `overall_risk_level` | Rule                                                                                                             |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `low`                | Zero `medium` and zero `high` findings. Safe to bid; mitigations are routine.                                    |
| `medium`             | At least one `medium` finding and zero `high` findings. Bid with mitigation plan; expect KO scrutiny.            |
| `high`               | At least one `high` finding. Capture lead must escalate before bid commitment; FAR 9.503 waiver may be required. |

---

## 6. Common false positives (do NOT flag)

- **Generic agency past performance.** Performing past work for the _same agency_ is not an OCI by itself — only when the past work falls into one of the three classes above.
- **Public information access.** Information posted publicly (sam.gov RFP, FBO sources sought) is by definition not "non-public" under 9.505-4.
- **Competitor name-dropping in the proposal.** Mentioning a competitor in a comparison table is not OCI; using their proprietary data is.
- **Standard FAR Part 15 source selection access.** Receiving an RFP and submitting a proposal is the normal mechanism, not an OCI.

---

## 7. Citations cheat sheet

| Citation     | What it covers                                            |
| ------------ | --------------------------------------------------------- |
| FAR 9.501    | OCI definition                                            |
| FAR 9.502    | Applicability                                             |
| FAR 9.503    | KO waiver authority (rarely granted; agency-head signoff) |
| FAR 9.504(a) | KO is the OCI determination authority                     |
| FAR 9.505-1  | Systems engineering & technical direction conflict        |
| FAR 9.505-2  | Specification / SOW preparation conflict                  |
| FAR 9.505-3  | Impaired objectivity                                      |
| FAR 9.505-4  | Unequal access to information                             |
| FAR 9.506    | KO procedures (analysis, mitigation review, waiver)       |
| FAR 9.507-1  | Solicitation provisions                                   |
| FAR 9.507-2  | Contract clauses                                          |
| FAR 9.508    | Examples                                                  |

Citations OUTSIDE the 9.501–9.508 range are fabrication. Reject them.
