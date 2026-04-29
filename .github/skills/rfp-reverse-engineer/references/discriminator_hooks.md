# Discriminator Hooks — Reading the Evaluation Section for Hidden Preferences

> A "discriminator hook" is language in evaluation criteria (UCF Section M or non-UCF equivalent) that signals an unstated CO preference our proposal can exploit. This catalog mirrors Shipley methodology and the Theseus extraction prompt's discriminator definitions.

## Hook Pattern 1: "Most Highly Rated" / "Highest Rated"

When evaluation factors include "most highly rated proposal will demonstrate..." or "highest-rated offerors will...", the CO is **defining the ceiling** for that factor — not just the floor. Plain compliance gets you in the door; matching the "highest rated" language wins the factor.

**Action:** Map every "most highly rated" phrase to a corresponding `discriminator_hooks[]` entry citing the `evaluation_factor` and quoting the ceiling language. Tell the proposal team to write to the ceiling, not the floor.

## Hook Pattern 2: Past-Performance Unlock Phrases

Look for phrases like:

- "relevant and recent past performance"
- "of similar scope, magnitude, and complexity"
- "demonstrating successful performance"
- "with the same or higher security tier"

Each phrase **defines the past-performance qualifier** the CO will apply. If our team's past performance matches, that's a hook. If it doesn't match, that's a competitor advantage we need to neutralize (subcontractor cite, JV partner cite, mitigation strategy).

**Action:** For each unlock phrase, emit `discriminator_hooks[]` entry with `qualifier_phrase` and `our_match_status` (`match` | `partial` | `gap`).

## Hook Pattern 3: Ghost Preferences (Word-for-Word Fingerprints)

The CO often writes evaluation language using exact phrases from a favored vendor's prior proposal or a thought-leadership piece. Detection patterns:

- Unusual jargon or proprietary methodology name appearing in evaluation criteria.
- A phrase that reads like marketing copy rather than government acquisition language.
- A capability described with vendor-specific framing ("engineering excellence framework", "value stream optimization") rather than industry-generic terms.

**Action:** Flag as `ghost_preference` candidates. Cross-reference against known incumbent or favored-vendor materials (out of scope for this skill — handoff to `competitive-intel`).

## Hook Pattern 4: FAB-Chain Triggers

Shipley methodology builds Feature → Advantage → Benefit chains. Trigger phrases in evaluation criteria that justify a FAB chain:

| Phrase                   | Triggers FAB Around                                                 |
| ------------------------ | ------------------------------------------------------------------- |
| "demonstrate ability to" | a capability + proof point + customer-impact statement              |
| "describe approach to"   | a methodology + advantage + measurable benefit                      |
| "explain how"            | a process + advantage + reduced risk / faster outcome               |
| "provide evidence of"    | a past-performance cite + advantage + same-customer-risk-mitigation |

**Action:** For each trigger, emit `discriminator_hooks[]` with `fab_chain_trigger` and recommended Feature/Advantage/Benefit slots for the proposal team to fill.

## Hook Pattern 5: Customer Priority Echoes

When the same priority language appears in **both** background sections (Section 1.2) **and** evaluation criteria, that's a `customer_priority` reinforced as a discriminator. The CO is telling you twice — not by accident.

**Action:** Cross-reference `customer_priority` entities from KG against `evaluation_factor` entities. Emit `discriminator_hooks[]` for each echo with the priority phrase quoted.

## Hook Pattern 6: Pain Point Confessions

Sometimes the CO confesses a `pain_point` directly in background or in a tradeoff narrative ("the prior contract experienced delays in...", "previous transitions were challenging because..."). Each confession is a hook to address head-on in the proposal — usually via a discriminator + proof point pair.

**Action:** Pull `pain_point` entities; for each, emit `discriminator_hooks[]` with `pain_point_text` and `recommended_proposal_response`.

## Hook Pattern 7: Weighted-Factor Spotlight

When evaluation criteria explicitly weight one factor at >40% (e.g., "Technical Approach is significantly more important than Past Performance and Price combined"), that factor IS the decision. Build the win-theme spine around it.

**Action:** Detect explicit weighting language; emit `discriminator_hooks[]` with `dominant_factor` and `recommended_win_theme_spine`.

## What this skill emits, what it does NOT emit

This skill EMITS the hooks (signal detection + capture context). It does NOT write the FAB chains, win themes, executive summaries, or discriminator narratives — that's the `proposal-generator` skill's job. Each `discriminator_hooks[]` entry is a structured handoff into the proposal-generator pipeline.
