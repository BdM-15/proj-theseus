# OCI Remediation Playbook

**Authority:** FAR 9.504(d), 9.505, 9.506(b)–(c), and the standard mitigation patterns the contracting community has accepted in OCI mitigation plans.

> The skill MUST pick **exactly one** `pattern` per finding from the list below. If no pattern applies, use `no_acceptable_mitigation` and set finding severity to `high`.

---

## Pattern 1 — `firewall`

**What it is.** An organizational and physical separation between the conflicted personnel / business unit and the personnel performing the instant contract. Documented in a written firewall plan, audited periodically.

**When it works.**

- `unequal_access` — high success rate. Information walls + access controls + NDAs are the textbook fix.
- `biased_ground_rules` — limited success. Firewalls don't un-write the SOW.
- `impaired_objectivity` — rare success. Judgment can't be firewalled.

**Authority:** FAR 9.505-4(b); KO mitigation review per 9.506(b).

**Recommendation phrasing:** "Erect an access-controlled firewall between the [conflicted unit] and the [bid team]; commit to documented access logs, NDA execution by all personnel crossing the firewall, and quarterly internal audit reports furnished to the KO upon request."

---

## Pattern 2 — `nda`

**What it is.** Non-disclosure agreements covering the specific non-public information the contractor possesses, signed by all bid-team personnel and by any party receiving derived work product.

**When it works.**

- `unequal_access` — almost always required as a _component_ of the mitigation; rarely sufficient on its own. Pair with `firewall`.

**Authority:** FAR 9.505-4(b).

**Recommendation phrasing:** "Execute NDAs with [the prior contractor / the agency / the data owner] covering [specific data set]; commit to data-segregation controls and to surfacing any inadvertent cross-use to the KO within 5 business days."

---

## Pattern 3 — `recusal`

**What it is.** The conflicted contractor / teammate steps off the bid (or off the conflicting downstream task), and is replaced by a non-conflicted party. Recusal can be at the entity, business-unit, or named-personnel level.

**When it works.**

- `impaired_objectivity` — primary mitigation. The conflicted party recuses from the evaluative scope.
- `biased_ground_rules` — sometimes works if the conflicted teammate is replaceable on the bid roster.

**Authority:** FAR 9.505-3 (impaired objectivity); 9.506(c).

**Recommendation phrasing:** "[Conflicted entity] recuses from [specific task / scope / evaluation function] and assigns it to [non-conflicted party / TBD with KO concurrence]; remove [conflicted entity] from the proposal's [labor mix / responsibility matrix] for that scope."

---

## Pattern 4 — `divestiture`

**What it is.** The conflicted entity divests the conflicting business line, parent / subsidiary relationship, or contract before bid award.

**When it works.**

- Any class — high success rate but high cost. Reserved for situations where the conflicted asset is genuinely separable and the contractor is willing to lose it.

**Authority:** FAR 9.504(d).

**Recommendation phrasing:** "[Conflicted entity] divests [specific business unit / contract / equity stake] prior to award; furnish proof of divestiture to the KO before bid acceptance."

---

## Pattern 5 — `novation`

**What it is.** A predecessor contract or asset is novated to a non-conflicted party. Used when the conflict source is a specific contract that can be transferred.

**When it works.**

- `biased_ground_rules` — sometimes, if the SOW-authoring contract can be assigned away.
- `unequal_access` — rarely; the information already crossed.

**Authority:** FAR Subpart 42.12 (anticipatory assignments / novations) plus FAR 9.504(d).

**Recommendation phrasing:** "[Conflicted contract] is novated to [non-conflicted assignee] under FAR Subpart 42.12 prior to award; furnish the novation agreement to the KO."

---

## Pattern 6 — `no_acceptable_mitigation`

**What it is.** No mitigation pattern credibly cures the conflict; the only path is to (a) walk away from the bid, or (b) seek a FAR 9.503 waiver from the agency head.

**When to use.**

- `impaired_objectivity` where the bidder will judge their own primary deliverable and recusal removes the value of the bid.
- `biased_ground_rules` where the bidder authored the complete SOW for non-developmental items (FAR 9.505-2(a)(1) hard bar).
- Any class where the bidder is unwilling to accept the cost / scope of an acceptable mitigation.

**Authority:** FAR 9.505-2(a)(1); FAR 9.503 (waivers); FAR 9.504(e).

**Recommendation phrasing:** "No acceptable mitigation. Pre-bid options: (a) walk from the opportunity; (b) request a FAR 9.503 waiver via [agency-head channel]. Capture lead must escalate before bid commitment."

---

## Selection cheat sheet

| Finding class          | Default first pattern | Default second (stacked) | Last resort                |
| ---------------------- | --------------------- | ------------------------ | -------------------------- |
| `unequal_access`       | `firewall`            | `nda`                    | `divestiture`              |
| `biased_ground_rules`  | `recusal`             | `novation`               | `no_acceptable_mitigation` |
| `impaired_objectivity` | `recusal`             | `divestiture`            | `no_acceptable_mitigation` |

The skill picks **one** pattern per finding (the highest-confidence one). Stacked mitigations should be described in the recommendation `summary` text, but only one `pattern` value goes in the envelope so downstream consumers can route findings cleanly.
