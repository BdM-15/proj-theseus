# Upstream Provenance — ot-prototype-strategist

## Source

Vendored from [1102tools/federal-contracting-skills](https://github.com/1102tools/federal-contracting-skills) (MIT, James Jenrette).

Two upstream skills collapsed into ONE Theseus skill:

1. `ot-project-description-builder` — agreements officer authoring the project description (.docx) attached to a 10 USC 4022 prototype OT.
2. `ot-cost-analysis` — agreements officer computing the independent should-cost estimate to evaluate the performer's proposed price.

## Why one Theseus skill instead of two

Upstream splits these because in a program office the **scoping author** (typically a technical PM + AO) and the **independent cost estimator** (a separate cost analyst) are different humans with different deliverable formats (one writes a .docx, the other builds an .xlsx).

On the bidder side, the **same capture-team analyst is doing both** during proposal development:

- The milestone structure shapes the should-cost (you can't price what you haven't scoped).
- The should-cost feeds back into the milestone structure (an unaffordable phase forces re-scoping).
- The cost-share path determination cuts across both (changing path A→C changes both narrative framing AND total bid math).

Splitting the skills would force the runtime to thrash between two skill loops on every bid. Collapsing surfaces the natural feedback loop and reduces overhead.

## The Five-Point Stance Inversion Contract

Every upstream-vendored skill in Theseus inverts seat. Document the five points:

### 1. Seat

|                 | Upstream                                  | Theseus                                       |
| --------------- | ----------------------------------------- | --------------------------------------------- |
| Who             | Agreements Officer (AO) at program office | Capture-team analyst at the bidder            |
| Output consumer | The agreement file + performer            | Internal proposal team + AO (via cost volume) |

### 2. Output framing

- **Upstream**: Project description (.docx) with sections 1-14 per consortium template; should-cost (.xlsx) with 7 sheets; both are government work product.
- **Theseus**: JSON envelope (`artifacts/ot_*.json`) that hands off to (a) `proposal-generator` for the project-description narrative we'll submit and (b) `renderers/render_xlsx.py` for the cost workbook we'll submit.

### 3. MCP allowlist

- **Upstream**: Variable; not Theseus-runtime aware.
- **Theseus**: Strictly the same trio as `price-to-win`: `bls_oews`, `gsa_calc`, `gsa_perdiem`. Whitelist enforced by `tests/skills/test_ot_prototype_strategist_skill.py`. Adding any other MCP requires a new sub-phase + audit.

### 4. KG grounding

- **Upstream**: No KG. AO has access to internal program-office documents.
- **Theseus**: All bid context comes from the active workspace KG. Every milestone traces back to a `requirement` / `evaluation_factor` / `performance_standard` entity. Every wage anchors to a metro derived from `place_of_performance`. No grounding source = no entry in the bid.

### 5. Runtime sandbox paths

- **Upstream**: Filesystem unconstrained.
- **Theseus**: `read_file` confined to skill directory + `references/`; `write_file` confined to `<run_dir>/artifacts/`; tool-call transcript captured in `<run_dir>/transcript.json` for audit.

## Specific bidder-side adaptations from upstream

| Upstream behavior                                                       | Theseus adaptation                                                                                                            |
| ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Author 14-section project description as .docx                          | Frame milestone structure + acquisition context in JSON; defer narrative authoring to `proposal-generator`                    |
| AO determines NDC eligibility                                           | Surface 10 USC 3014 test (CAS coverage prior year); state explicitly we don't render binding eligibility opinion              |
| Should-cost as government independent estimate                          | Should-cost as our bid math; same methodology, different consumer                                                             |
| AO selects 4022(d) path based on performer's situation                  | We pick the path that minimizes our exposure; surface participation-gate flags for AO review                                  |
| Production follow-on (4022(f)) authored by AO post-prototype-completion | Treat as a separate workflow; document the path-inheritance + cost-share-non-propagation rules                                |
| Cost data presented to performer                                        | Cost data is internal — proposal cost volume is what the AO sees. Bid recommendation includes risk_flags for the capture team |

## Re-vendor instructions

When upstream releases a new version of either source skill:

1. Diff the upstream against the version captured here (commit `49f20f7` baseline for the cost analysis methodology; both skills as of October 2025).
2. New BLS / CALC+ / per-diem MCP behaviors → update `references/cost_models/ot_milestone_buildup.md`.
3. New statutory citations (e.g., NDAA changes amending 10 USC 4022) → update `references/ot_authority_taxonomy.md`.
4. New TRL / milestone patterns → update `references/trl_milestone_patterns.md`.
5. Re-run `tests/skills/test_ot_prototype_strategist_skill.py`. Live drift check via `THESEUS_LIVE_MCP=1`.
6. Bump `metadata.version` in SKILL.md.
7. Cite upstream commit SHA in commit message.

## Bidder-mode vs government-mode dual usage

A single user might wear both hats — bidding on one OT this week and reviewing a sub's milestone proposal next week. The skill handles this via the **Workflow Selector** in SKILL.md:

- Workflows 1, 2, 3 → bidder seat (default; the dominant case)
- Workflow 4 → buyer-seat (sub price reasonableness — we revert to upstream's AO-seat language, since now we're the buyer relative to the sub)

The user's intent is captured in the `workflow` field of the output JSON. Downstream consumers (`proposal-generator` for our prose; chat presentation for sub review) can branch on it.

## Anthropic skill-creator best-practices applied

Per the skill-creator MANDATE in [.github/copilot-instructions.md](../../../.github/copilot-instructions.md):

- **Evals BEFORE prose**: `evals/evals.json` written first; SKILL.md drafted to satisfy the evals.
- **Progressive disclosure**: Statutory framework / TRL patterns / cost buildup math / KG queries pushed to `references/` so SKILL.md body stays under 500 lines.
- **Degrees of freedom matched to fragility**: High-freedom prose for milestone-structure derivation (judgment-heavy); low-freedom math + statutory cites for cost-share paths and BLS aging (fragile, must be exact).
- **Single default + escape hatch**: Workflow 1 (respond to OT solicitation) is the default; Workflows 2/3/4 are explicit escape hatches.
- **No time-sensitive language**: References cite statute by section, not "current rules"; MCP defaults updated by re-vendor process.
