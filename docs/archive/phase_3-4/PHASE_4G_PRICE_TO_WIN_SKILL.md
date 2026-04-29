# Phase 4g — `price-to-win` Skill (Collapsed IGCE Builder)

**Branch**: `133-phase-4g-price-to-win` (off `120-skills-spec-compliance` @ `062f48a`)

**Status**: Drafted. Awaiting commit + FF into `120-skills-spec-compliance`.

**Sha (placeholder until commit)**: `49f20f7`

---

## Scope

Vendor 3 IGCE Builder skills from [`1102tools/federal-contracting-skills`](https://github.com/1102tools/federal-contracting-skills) (MIT, James Jenrette) and **collapse them into one Theseus skill at `.github/skills/price-to-win/`**:

| Upstream | Theseus role |
|---|---|
| `igce-builder-ffp` | FFP buildup → `references/cost_models/ffp_buildup.md` |
| `igce-builder-lh-tm` | LH/T&M buildup → `references/cost_models/lh_tm_buildup.md` |
| `igce-builder-cr` | CR buildup → `references/cost_models/cost_reimbursement_buildup.md` |

The cost-model **decision tree** lives at the top of `SKILL.md` (FFP / LH / T&M / CPFF / CPAF / CPIF / hybrid). The skill picks one branch per opportunity from KG signals (NAICS, PSC, contract-vehicle entity, FAR-16-clause references in the workspace) and loads only the matching reference.

## Buyer → Bidder Stance Inversion (the central design call)

The upstream skills are written for **contracting officers** building IGCEs that go in the contract file. They gate evaluative judgments behind `ai-boundaries.md`:

> "The skill computes the cost stack. It does NOT determine whether a rate is fair and reasonable."

Theseus inverts that gate. `price-to-win` is for the **bidder / capture team** — estimating competitor price IS the deliverable. Same FAR 15.404-4 / 16.x math, opposite seat. Concretely:

- Drops `ai-boundaries.md` linkage entirely.
- Reframes "the skill does NOT determine X" as "the skill recommends X with cited assumptions".
- Adds explicit `ptw_recommendation` block (target_price, rationale, risk_flags) to the JSON envelope.
- Pulls `incumbent` / `competitor` / `contract_vehicle` entities from the workspace KG (upstream has no notion of incumbent — the CO doesn't have one).
- Renames the deliverable from "IGCE" to "competitor cost stack" / "PTW benchmark".

Math, vehicle preset table, sanity bands, MCP tool calls (`bls_oews`, `gsa_calc`, `gsa_perdiem`), and FAR citations are unchanged — they're seat-agnostic.

Full inversion contract documented in [`.github/skills/price-to-win/UPSTREAM.md`](../.github/skills/price-to-win/UPSTREAM.md).

## MCP Wiring

`metadata.mcps: [bls_oews, gsa_calc, gsa_perdiem]` — three vendored MCPs already shipped in earlier 4f.x phases. No new MCPs vendored in 4g.

| MCP | Phase vendored | Purpose in this skill |
|---|---|---|
| `bls_oews` | 4f.7 (`6793c10`) | Labor wages by SOC + metro, IGCE wage benchmarks |
| `gsa_calc` | 4f.3 (`f9ad45f`) | Awarded ceiling rates (CALC+ schedule data) |
| `gsa_perdiem` | 4f.4 (`d058d2a`) | Lodging + M&IE per destination |

## Files Created

```
.github/skills/price-to-win/
├── SKILL.md                                      (frontmatter + body + decision tree)
├── UPSTREAM.md                                   (3 sources, MIT, inversion contract, re-vendor instructions)
├── evals/
│   └── evals.json                                (3 prompts: FFP / LH / CR)
└── references/
    └── cost_models/
        ├── ffp_buildup.md                        (wrap-rate math, vehicle presets, sanity bands)
        ├── lh_tm_buildup.md                      (single burden multiplier, T&M materials at cost)
        └── cost_reimbursement_buildup.md         (cost pools, FCCM, CPFF/CPAF/CPIF fee math)

tests/skills/
└── test_price_to_win_skill.py                    (frontmatter + 3 MCPs + decision tree + references + tool whitelist + live drift check)

docs/
└── PHASE_4G_PRICE_TO_WIN_SKILL.md                (this file)
```

## Contract Tests (Always-on)

`tests/skills/test_price_to_win_skill.py` proves:

1. Frontmatter has only the 6 spec fields; `name`, `USE WHEN`, `DO NOT USE FOR`, `bls`/`calc`/`per diem` mentioned in description.
2. `SkillManager` parses `metadata.mcps == [bls_oews, gsa_calc, gsa_perdiem]` and runtime is `tools`.
3. `SKILL.md` body has a `Decision Tree` section enumerating FFP / LH / T&M / CPFF / CPAF / CPIF.
4. All 3 `references/cost_models/*.md` exist and are non-trivial (>500 chars).
5. Every `mcp__<server>__<tool>` referenced in the body is in the per-server whitelist (catches typos and upstream renames).
6. Every MCP is exercised by at least one eval expectation; every cost-model reference is required by at least one eval (no decorative branches).

Live drift check (opt-in via `THESEUS_LIVE_MCP=1`) spawns all 3 upstream MCPs and confirms every referenced tool actually exists.

## Eval Coverage

3 prompts, one per cost model:

1. **FFP services in DC** (NAICS 541512, 5 senior software developers, 1+4 years, GSA MAS commercial) — exercises `bls_oews.get_wage_data` (SOC 15-1252), `gsa_calc.igce_benchmark`, FFP wrap-rate buildup, GSA MAS preset (~2.47x), lifecycle totals, ptw_recommendation with target 5–10% under mid.
2. **LH cleared task order** (3 senior cyber analysts TS/SCI in DC, 3-year PoP, Huntsville travel) — exercises `bls_oews.get_wage_data` (SOC 15-1212), `gsa_calc.igce_benchmark`, **`gsa_perdiem.estimate_travel_cost`** (Huntsville), 1.8/2.0/2.2 burden scenarios, no burden on travel, FAR 16.601 + 31.205-46.
3. **CR R&D BAA CPAF in Boston** (2 PIs + 4 research engineers, 3-year, 85% earned-fee assumption on 10% award pool, 3% base fee) — exercises CPAF fee math on Fee-Bearing Cost only (NOT on ODC/sub pass-throughs), statutory cap (10 USC 3322(a)), separate fee_bearing_cost vs non_fee_cost reporting.

## What's NOT in This Skill (and Where to Find It)

- **Proposal narrative drafting** → `proposal-generator` (Phase 3a).
- **FAR clause compliance audit** → `compliance-auditor` (Phase 3b + 4f.2).
- **Incumbent revenue / award history** → `competitive-intel` (Phase 4d, USAspending MCP).
- **OCONUS travel** → out of scope (GSA Per Diem MCP covers CONUS only; State Dept rates needed for OCONUS — flag and stop).
- **`sow-pws-builder` / `ot-prototype-strategist`** → deferred to Phase 4h / 4i (separate upstream skills, separate stances).

## Test Run (Pre-Commit)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/skills/test_price_to_win_skill.py -v
```

Expect 6 passed (Layer 1 always-on). Layer 2 live drift check skipped unless `THESEUS_LIVE_MCP=1`.

## Re-Vendor Process

When upstream releases a material update (new contract type, new vehicle preset, new MCP wiring), follow the procedure in [`.github/skills/price-to-win/UPSTREAM.md`](../.github/skills/price-to-win/UPSTREAM.md). Critical: do NOT re-import `ai-boundaries.md` linkage — the inversion is permanent.
