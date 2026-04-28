# Phase 4i — OT Prototype Strategist

**Status**: ✅ Done — `ecc6e75`
**Branch**: `136-phase-4i-ot-prototype-strategist` → FF into `120-skills-spec-compliance`
**Closes**: Phase 4 (sub-phases 4a–4j all complete).

## Scope

Vendor `ot-project-description-builder` + `ot-cost-analysis` from
[1102tools/federal-contracting-skills](https://github.com/1102tools/federal-contracting-skills) (MIT)
into ONE Theseus skill: `.github/skills/ot-prototype-strategist/`.

Other Transactions are statutorily outside the FAR (10 USC 4021 research,
10 USC 4022 prototype, 10 USC 4022(f) production follow-on). Bidders pursuing
prototype OTs need:

1. A **milestone-based project description** (TRL phasing, deliverables, exit
   criteria) — what the technical proposal volume describes.
2. A **per-milestone should-cost stack** — what the cost volume reflects.
3. A **10 USC 4022(d) cost-share path determination** — picks the path that
   minimizes our out-of-pocket exposure (NDC participation A, small-business B,
   1/3 share C, exceptional circumstances D).

The two upstream skills split (1) from (2)+(3) because in a program office
the technical PM authors the project description while a separate cost
analyst computes the independent estimate. **On the bidder side, the same
capture-team analyst does all three together** — the milestone structure
shapes the should-cost, the should-cost feeds back into milestone scoping,
and the 4022(d) path determination cuts across both. Keeping them as
separate skills would force the runtime to thrash between two skill loops
on every bid. Collapsing surfaces the natural feedback loop.

## Decision tree (top of SKILL.md body)

The skill opens with a **Workflow Selector** — three primary workflows plus
one buyer-stance exception:

1. **Respond to OT solicitation** (default) — given a parsed solicitation in
   the workspace, build milestones + cost stack.
2. **Pre-solicitation strategist** — pursuit-stage; build positioning
   milestones + should-cost band before the formal solicitation.
3. **Cost-share path comparison** — strategic; compare 4022(d)(1)(A)
   NDC-team vs (C) traditional-sole 1/3-share scenarios; flag participation
   gates.
4. **Sub price reasonableness** (buyer-stance exception) — a teaming sub
   proposed milestone-based pricing to us; we revert to upstream's AO-seat
   should-cost language because we're the buyer relative to the sub.

## MCP set

Same trio as `price-to-win` (Phase 4g): `bls_oews`, `gsa_calc`,
`gsa_perdiem`. OT cost analysis uses the identical labor-benchmarking
stack — just builds it per-milestone instead of as a wrap-rate annual cost.
No new MCP vendoring required.

Whitelist enforced by `tests/skills/test_ot_prototype_strategist_skill.py`
(reuses the Phase 4f.3 / 4f.4 / 4f.7 tool whitelists verbatim).

## Bidder-stance inversion (5-point contract)

Per `UPSTREAM.md`, the bidder-side adaptation:

| Point           | Upstream (AO seat)                    | Theseus (bidder seat)                                                                         |
| --------------- | ------------------------------------- | --------------------------------------------------------------------------------------------- |
| Seat            | Agreements Officer at program office  | Capture-team analyst at bidder                                                                |
| Output framing  | .docx + .xlsx government work product | JSON envelope handed to `proposal-generator` + `renderers/render_xlsx.py`                     |
| MCP allowlist   | Variable                              | Strictly `bls_oews` + `gsa_calc` + `gsa_perdiem`; whitelist-enforced                          |
| KG grounding    | None (program office docs)            | Every milestone traces to `requirement` / `evaluation_factor` / `performance_standard` entity |
| Runtime sandbox | Filesystem unconstrained              | `read_file` skill-dir scoped; `write_file` `<run_dir>/artifacts/`; transcript captured        |

## Statutory framework (cited everywhere)

OTs do NOT cite FAR 15.404. The skill cites:

- **10 USC 4021** — research authority (no statutory cost-share trigger).
- **10 USC 4022** — prototype authority.
- **10 USC 4022(d)(1)(A-D)** — four cost-share paths.
- **10 USC 4022(f)** — production follow-on (path inherits, cost-share does NOT propagate; gov funds 100%).
- **10 USC 3014** — NDC definition (CAS-coverage test prior year, NOT dollar threshold).
- **10 USC 4003** — prototype definition (4 conditions).

## Progressive disclosure (Anthropic best-practice)

SKILL.md body stays under 500 lines by pushing detail into 4 references:

| Reference                                        | Purpose                                                                                               |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| `references/ot_authority_taxonomy.md`            | Statutory framework, performer→path table, NDC test, consortium fees                                  |
| `references/trl_milestone_patterns.md`           | TRL 1-9 mapping, decision-to-milestone rules, exit-criterion patterns                                 |
| `references/cost_models/ot_milestone_buildup.md` | 9-step should-cost workflow, SOC mapping, academic burden branch, learning curve, consortium fee math |
| `references/relationship_query_patterns.md`      | KG entity types + Cypher patterns for OT traceability                                                 |

## Evals coverage

`evals/evals.json` ships 3 evals exercising:

| Eval | Workflow                   | Authority   | Cost-share path                        | MCPs exercised                                                         | References exercised                     |
| ---- | -------------------------- | ----------- | -------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------- |
| 1    | Respond to OT solicitation | 10 USC 4022 | (d)(1)(A) NDC, none required           | bls_oews + gsa_calc + gsa_perdiem                                      | authority + TRL + cost model             |
| 2    | Respond to OT solicitation | 10 USC 4021 | none (statutorily inapplicable)        | bls_oews                                                               | authority + cost model (academic branch) |
| 3    | Cost-share path comparison | 10 USC 4022 | scenario_solo (C) vs scenario_team (A) | (selector workflow doesn't require live MCP — kg_entities + read_file) | authority                                |

Test enforcement: every MCP must appear in at least one eval expectation;
every reference file (basename) must appear in at least one eval expectation.
Decorative wiring fails.

## Contract tests

`tests/skills/test_ot_prototype_strategist_skill.py`:

1. `test_ot_strategist_frontmatter_is_spec_compliant` — 6-field frontmatter, ≤1024 char description with USE WHEN + DO NOT USE FOR + OT/prototype/4022 trigger keywords.
2. `test_ot_strategist_declares_three_mcps` — runtime=tools, exactly `bls_oews` + `gsa_calc` + `gsa_perdiem`.
3. `test_ot_strategist_body_has_workflow_selector_and_statutory_citations` — body has Workflow Selector + 3 named workflows + 5 statutory citations + 5 domain markers.
4. `test_ot_strategist_references_exist` — 4 references present, each >500 chars.
5. `test_ot_strategist_body_references_real_mcp_tools_only` — every `mcp__<server>__<tool>` in body is in the curated whitelist.
6. `test_ot_strategist_evals_exercise_mcps_and_references` — every MCP and every reference file appears in evals.
7. `test_ot_strategist_taxonomy_surfaces_via_manager` — Phase 4j taxonomy fields round-trip through `SkillManager.to_summary`.
8. `test_skill_body_tool_refs_match_live_mcps` (opt-in via `THESEUS_LIVE_MCP=1`) — drift check against running MCP servers.

## Files added / modified

```
.github/skills/ot-prototype-strategist/
  SKILL.md
  UPSTREAM.md
  evals/evals.json
  references/ot_authority_taxonomy.md
  references/trl_milestone_patterns.md
  references/relationship_query_patterns.md
  references/cost_models/ot_milestone_buildup.md
tests/skills/test_ot_prototype_strategist_skill.py
docs/PHASE_4I_OT_PROTOTYPE_STRATEGIST.md
docs/skills_roadmap.md  (modified: 4i row + status snapshot)
```

## Phase 4 complete

With 4i merged, **Phase 4 is closed**. All sub-phases:

- ✅ 4a MCP client subsystem
- ✅ 4b `metadata.mcps` allowlist
- ✅ 4c USAspending vendored
- ✅ 4d competitive-intel promoted
- ✅ 4e Settings → MCP Servers panel
- ✅ 4f.1–4f.8 all 8 federal MCPs vendored
- ✅ 4g price-to-win (3 IGCE upstreams collapsed)
- ✅ 4h SOW/PWS split (subcontractor-sow-builder + rfp-reverse-engineer)
- ✅ 4i ot-prototype-strategist (2 OT upstreams collapsed)
- ✅ 4j three-axis taxonomy + frontmatter pass

Next phase per `docs/skills_roadmap.md`: Phase 5.
