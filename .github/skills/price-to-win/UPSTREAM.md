# Upstream Provenance — `price-to-win`

This skill was vendored and **collapsed** from three IGCE Builder skills in the open-source [`1102tools/federal-contracting-skills`](https://github.com/1102tools/federal-contracting-skills) repository, authored by James Jenrette and licensed MIT.

## Sources

| Upstream skill | Path | Role in this collapsed skill |
|---|---|---|
| `igce-builder-ffp` | `skills/igce-builder-ffp/SKILL.md` | Wrap-rate buildup math, vehicle preset table, sanity bands → [references/cost_models/ffp_buildup.md](references/cost_models/ffp_buildup.md) |
| `igce-builder-lh-tm` | `skills/igce-builder-lh-tm/SKILL.md` | Single burden multiplier, T&M materials at cost, FAR 16.601 mechanics → [references/cost_models/lh_tm_buildup.md](references/cost_models/lh_tm_buildup.md) |
| `igce-builder-cr` | `skills/igce-builder-cr/SKILL.md` | Cost pools, FCCM, CPFF/CPAF/CPIF fee math, Fee-Bearing vs Non-Fee Cost → [references/cost_models/cost_reimbursement_buildup.md](references/cost_models/cost_reimbursement_buildup.md) |

Upstream commit at vendoring time: HEAD of `main` as of Phase 4g (sha pinned in `docs/PHASE_4G_PRICE_TO_WIN_SKILL.md`).

## License

MIT. Copyright (c) James Jenrette. See the upstream repository's `LICENSE` file. Required attribution is preserved in this UPSTREAM.md.

## Why Collapsed (3 → 1)

The upstream repo ships one skill per contract type because each has its own buildup mechanics. For Theseus, contract type is a **decision** the skill makes from the workspace KG (NAICS, PSC, FAR-16-clause signals, RFP language) — not a separate skill the user invokes by name. A capture team should ask "what's the price to win?" and the skill should pick FFP / LH / T&M / CR (or hybrid) and run the right buildup.

Collapsing also keeps the three MCPs (`bls_oews`, `gsa_calc`, `gsa_perdiem`) wired to a single skill rather than triplicated, and avoids triplicate `references/` for shared concepts (BLS series IDs, CALC+ pool sizing, GSA per diem cells).

## The Stance Inversion (Buyer → Bidder)

This is the most important divergence from upstream. **Read it before re-vendoring.**

The upstream skills are written from the **contracting officer (CO)** seat. They build IGCEs that go in the contract file. They explicitly REFUSE to render evaluative judgments and gate them behind `ai-boundaries.md`:

> "The skill computes the cost stack. It does NOT determine whether a rate is fair and reasonable. That is the CO's call after technical evaluation."

Theseus's `price-to-win` is written from the **bidder / capture team** seat. There is no CO to defer to. **Estimating the competitor's likely price IS the deliverable.** The skill MUST and DOES render the judgments the upstream skill refuses:

| Question | Upstream (CO) answer | Theseus (bidder) answer |
|---|---|---|
| "What rate should we use?" | "I'll show you the band; you decide." | "Mid scenario at ~$X/hr fully burdened, with these assumptions." |
| "Is this fair and reasonable?" | "Out of scope — CO judgment." | "Within FAR 15.404-4 norms; we recommend bidding ~5% under." |
| "What's the target price?" | Refused. | Recommended explicitly with rationale + range + risk flags. |

### Concretely, what changed when collapsing

1. **Dropped the `ai-boundaries.md` linkage entirely.** Upstream loads it as a hard refusal gate; Theseus has no use for it (we are the bidder, not the CO).
2. **Reframed every "the skill does NOT determine X" passage** as "the skill recommends X with cited assumptions" in the SKILL.md body and reference files.
3. **Added the `ptw_recommendation` block** to the JSON output envelope — explicit target_price + rationale + risk_flags, none of which exist upstream.
4. **Reframed CALC+ output** from "position vs. ceiling pool" (CO framing) to "where the competitor likely lands and where we need to undercut" (bidder framing).
5. **Added incumbent / competitor entity slicing** from the workspace KG (`incumbent`, `competitor`, `contract_vehicle`) — upstream has no notion of incumbent because the CO doesn't have one.
6. **Renamed the deliverable** from "IGCE" to "competitor cost stack" / "PTW benchmark" throughout, and removed CO-internal-document language ("for the contract file", "for negotiation memos", etc.).

### What did NOT change (and shouldn't)

- The math. FAR 15.404-4, 16.202, 16.601, 16.301–16.307 mechanics are identical regardless of seat. Wrap rate is wrap rate; CPAF earned-fee math is CPAF earned-fee math.
- The MCP tool calls. `bls_oews.get_wage_data`, `gsa_calc.igce_benchmark`, `gsa_perdiem.estimate_travel_cost` are buyer/bidder-agnostic.
- The vehicle preset table. The wrap rate that produces a credible CO IGCE is the same wrap rate the competitor likely actually has.
- The sanity bands. A 3.79x multiplier is suspicious from either seat unless it's OCONUS hostile-theater.
- The FAR citations. Same regs apply.

## Re-Vendoring Instructions

When upstream releases a material update (new contract-type buildup, new vehicle preset, new MCP wiring):

1. Pull the latest from `https://github.com/1102tools/federal-contracting-skills`.
2. Diff the three `igce-builder-*/SKILL.md` files against the prior pinned sha (recorded in `docs/PHASE_4G_PRICE_TO_WIN_SKILL.md`).
3. Cherry-pick **mechanics** (math, presets, sanity checks, FAR citations) into the matching `references/cost_models/*.md`.
4. **DO NOT** copy `ai-boundaries.md` linkage or CO-refusal language. Reframe every evaluative gate as an explicit bidder recommendation with risk flags.
5. **DO NOT** copy upstream's per-skill MCP wiring; this skill's `metadata.mcps` is already declared with the three shared servers.
6. Update the pinned sha in `docs/PHASE_4G_PRICE_TO_WIN_SKILL.md` and bump `metadata.version` in `SKILL.md`.
7. Run `pytest tests/skills/test_price_to_win_skill.py` and re-run `evals/evals.json` against the live skill before committing.
8. Update this UPSTREAM.md if the inversion contract changes (e.g., upstream adds a feature that genuinely belongs in our skill unchanged).

## Out of Scope for Re-Vendor

- The fourth upstream skill `sow-pws-builder` belongs in Phase 4h (`requirements-extractor` or similar), not here.
- The fifth upstream skill `ot-project-description-builder` and sixth `ot-cost-analysis` belong in Phase 4i (OT-specific skill), not here.
