# Skills Roadmap

Authoritative roadmap for the Theseus skills subsystem. Supersedes the
legacy `Roadmap.md` for skills work — that file is a vestige and its
items live in GitHub issues now.

**Last updated:** 2026-04-28 · **Branch:** `120-skills-spec-compliance`

---

## Status snapshot

| Phase   | Scope                                                                                                                   | State                                                                        | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| ------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**   | Output persistence (`skill_runs/` + Recent Runs)                                                                        | ✅ Done                                                                      | `7833d76`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **1.5** | Source-grounded briefing book (verbatim citations)                                                                      | ✅ Done                                                                      | `ad5d8d9`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **1.6** | Chat-grade hybrid retrieval (mix mode + reranker)                                                                       | ✅ Done                                                                      | `ad5d8d9`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **2.0** | Open Skills spec compliance — vendor skill-creator                                                                      | ✅ Done                                                                      | `9134f0f`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **2.1** | Tool-calling runtime (imperative agent loop)                                                                            | ✅ Done                                                                      | `b4b9e33`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **2.2** | Migrate `proposal-generator` to tools-mode                                                                              | ✅ Done                                                                      | `7f4e75b`, `914a4eb`, `4cf5c42`, `1bfb99b`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| **2.3** | Migrate remaining 4 skills + UI transcript drawer                                                                       | ✅ Done                                                                      | `98980a7`, `2dc8e1a`, `55d694b`, `d3cf024`, `90610d7`, `fe716a4`, `5bba9be`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **3**   | Artifact renderers (HTML → PPTX/PDF/MP4/DOCX/XLSX)                                                                      | ✅ 3a+3b+3c+3d+3e done                                                       | See §Phase 3 below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **4**   | External datasources (SAM.gov, USAspending, eCFR, GSA CALC+, GSA Per Diem, Federal Register, BLS OEWS, Regulations.gov) | ✅ Done (4a–4j)                                                              | `ecbcc29` (client), `1d3df18` (USAspending), `2cf328d` (competitive-intel promoted), `226d214` (eCFR vendored), `f9ad45f` (gsa-calc vendored), `d058d2a` (gsa-perdiem vendored), `73a2a94` (federal-register vendored), `0a0fbca` (4e MCP Servers panel), `cf003e9` (4f.2 compliance-auditor consumes eCFR), `0098fb0` (4f.6 sam-gov vendored), `6793c10` (4f.7 bls-oews vendored), `79a0846` (4f.8 regulations-gov vendored — closes MCP-vendoring stretch), `49f20f7` (4g price-to-win), `76682c6` (4h sow-pws-builder split), `586f650` (4j three-axis taxonomy), `4753293` (4i ot-prototype-strategist — closes Phase 4). |
| **5**   | Skills invoking other skills (sub-agents)                                                                               | ⏸ Deferred — issue [#116](https://github.com/BdM-15/proj-theseus/issues/116) | revisit after Phase 6 (Studio) ships and at least one skill is validated end-to-end                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

---

## What "tools-mode runtime" actually delivered (vs. original Phase 2)

Original Phase 2 spec called for a **declarative `workflow:` block** in
SKILL.md frontmatter with ordered `llm:` / `tool:` steps. We didn't build
that. Instead we built the **imperative tool-calling agent loop** that the
Open Skills spec converged on (Anthropic / Claude Code / Cursor pattern).

**What this means in practice:**

- The LLM autonomously decides which tools to call based on the SKILL.md
  body checklist. No declarative chain to author.
- Multi-step skills work today — `proposal-generator` already runs 16+
  turns in a single invocation (KG queries → chunk fetches → write).
- Tools shipped: `kg_query`, `kg_entities`, `kg_chunks`, `read_file`,
  `run_script`, `write_file`. Strictly broader than the original
  declarative whitelist.
- Every turn is captured in `<run_dir>/transcript.json` and surfaced in
  the UI drawer (`fe716a4`).

**Original `template.render` tool: dropped — see Phase 3 reasoning.**

---

## Phase 3 — Artifact renderers (re-scoped 2026-04-28)

### Original plan (now obsolete)

Build `src/skills/renderers/` with:

- Pandoc MD → DOCX
- `openpyxl` → XLSX
- html2pptx → PPTX
- wkhtmltopdf / Playwright → PDF

…and add a `template.render` runtime tool.

### What changed

We properly vendored `huashu-design` in sub-phase 2.3 (`d3cf024`). It
ships **all five rendering toolchains as `scripts/`**, which the
tools-mode runtime can execute today via `run_script`:

| Renderer                 | Script                                                                                                 | Output                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| HTML → PPTX              | [scripts/html2pptx.js](../.github/skills/huashu-design/scripts/html2pptx.js)                           | editable .pptx (text frames)       |
| HTML deck → PDF          | [scripts/export_deck_pdf.mjs](../.github/skills/huashu-design/scripts/export_deck_pdf.mjs)             | .pdf                               |
| HTML deck stages → PDF   | [scripts/export_deck_stage_pdf.mjs](../.github/skills/huashu-design/scripts/export_deck_stage_pdf.mjs) | .pdf (per-stage)                   |
| HTML animation → MP4/GIF | [scripts/render-video.js](../.github/skills/huashu-design/scripts/render-video.js)                     | .mp4 / .gif (25fps + 60fps interp) |
| Format conversion        | [scripts/convert-formats.sh](../.github/skills/huashu-design/scripts/convert-formats.sh)               | .png / .svg                        |
| Add BGM/SFX              | [scripts/add-music.sh](../.github/skills/huashu-design/scripts/add-music.sh)                           | scored .mp4                        |
| Playwright verify        | [scripts/verify.py](../.github/skills/huashu-design/scripts/verify.py)                                 | smoke-test .html                   |

`proposal-generator` already produces the matching HTML inputs in
[assets/](../.github/skills/proposal-generator/assets/):

- `compliance_matrix.html`
- `slide_master.html`
- `one_pager.html`
- `theme_card.html`

### Re-scoped Phase 3 (sub-phases)

**Original "build five renderers from scratch" → "wire huashu-design's
existing scripts into a system tool the runtime exposes."**

| Sub-phase | Item                                                                                                                                                    | Status     | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **3a**    | Toolchain install (Node + Playwright + Chromium via huashu `package.json`)                                                                              | ✅ Done    | `docs/PHASE_3A_TOOLCHAIN.md`; smoke-tested `export_deck_pdf.mjs` → 23KB vector PDF                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **3b**    | `proposal-generator` SKILL.md references `huashu-design` scripts via `run_script` (cross-skill `script_paths` + CLI `args` + `{artifacts}` placeholder) | ✅ Done    | E2E smoke test: 23.8KB vector PDF rendered through runtime; `metadata.script_paths` opt-in keeps spec-portable                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **3c**    | Drawer "Download artifacts" section recognizes binary mimetypes (.pptx/.pdf/.mp4/.gif)                                                                  | ✅ Done    | New `GET /api/ui/skills/{name}/runs/{run_id}/artifacts/{filename}` (path-traversal-safe FileResponse with `mimetypes.guess_type`); drawer renders `skills.run.artifacts` as download links with type-aware icons + size; CSS `.skill-artifacts-panel`                                                                                                                                                                                                                                                                                                                                                                                                              |
| **3d**    | DOCX renderer (Pandoc MD → DOCX) for proposal volumes — huashu doesn't ship this                                                                        | ✅ Done    | `docs/PHASE_3D_TOOLCHAIN.md`; new **`renderers`** utility skill at `.github/skills/renderers/` owns format-conversion scripts (`scripts/render_docx.py` is pure-stdlib Python wrapper around `pandoc`); proposal-generator opts in via `metadata.script_paths: [../renderers/scripts]` and uses Step 12b; E2E smoke test rendered 10.7KB DOCX through the runtime, exit_code==0; install hint surfaced when `pandoc` missing (rc=127). Pattern is reusable: future skills (compliance-auditor, competitive-intel, writer) just add the same `script_paths` line.                                                                                                   |
| **3e**    | XLSX renderer (openpyxl) for compliance matrix — huashu doesn't ship this                                                                               | ✅ Done    | `docs/PHASE_3E_TOOLCHAIN.md`; `.github/skills/renderers/scripts/render_xlsx.py` is pure-stdlib + openpyxl wrapper. Accepts the `proposal_draft.json` envelope directly: each top-level array-of-objects key (`compliance_matrix`, `themes`, `fab_chains`, `volume_outlines`) becomes a sheet; `status` column gets conditional fill (OK=green, PARTIAL=yellow, GAP=red); frozen header + autofilter applied automatically. proposal-generator Step 12c invokes via `run_script`. E2E smoke test: 6.3KB workbook rendered through runtime (rc=0), opt-in enforcement verified (renderer rejected without `script_paths`), bad/missing input correctly returns rc=2. |
| —         | `template.render` runtime tool                                                                                                                          | ❌ Dropped | Superseded by `run_script` + huashu scripts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

**Net effect:** Phase 3 shrinks from "build five renderers" to "install
the toolchain + wire huashu + add two govcon-specific renderers (DOCX,
XLSX) that huashu doesn't cover."

**Phase 3a notes (2026-04-28):** Playwright bundles its own ffmpeg, so
no system ffmpeg install is needed for video work. Pandoc was added in
3d (`docs/PHASE_3D_TOOLCHAIN.md`). Python deps untouched; snapshots in
`tools/_dep_snapshots/` (gitignored) provide rollback.

---

## Phase 4 — MCP client + vendored capture skills (re-scoped 2026-04-28, B+C)

### Why this changed (again)

After surveying [`1102tools/federal-contracting-mcps`](https://github.com/1102tools/federal-contracting-mcps)
and [`1102tools/federal-contracting-skills`](https://github.com/1102tools/federal-contracting-skills),
two facts forced a redesign:

1. **The federal data tooling has consolidated into MCPs.** 1102tools
   moved their five API skills (SAM.gov, USAspending, BLS OEWS, GSA
   CALC+, GSA Per Diem) into MCP servers in April 2026 because skills
   drifted across runs while MCPs stayed deterministic. Their MCPs went
   through 3-6 audit rounds with ~350 bugs fixed against live APIs.
   Re-implementing this in `src/skills/datasources/` (the original Phase
   4 plan) means signing up for permanent maintenance debt against code
   that isn't our domain. We should consume their MCPs, not port them.
2. **Their orchestration skills are MIT-licensed and reusable from the
   capture-team seat.** Skills written for the Contracting Officer
   (SOW/PWS Builder, IGCE Builders, OT skills) have direct analogs on
   the bidder side — same FAR citations, same cost-buildup math,
   different persona / objective. Vendoring + repersonalizing them is
   far cheaper than authoring from scratch.

### Architecture: skills + MCPs complement each other

| Layer     | Owns                                                             | Examples                                                                                                                  |
| --------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **MCP**   | Deterministic data access — HTTP, parsing, cache, retries        | `usaspending`, `sam_gov`, `fpds`, `bls_oews`, `gsa_calc`, `gsa_perdiem`, `federal_register`, `ecfr`, `regulations_gov`    |
| **Skill** | Domain reasoning, decision trees, judgment, narrative, citations | `competitive-intel`, `price-to-win`, `rfp-reverse-engineer`, `subcontractor-sow-builder`, `proposal-generator` (existing) |

Same opt-in pattern as Phase 3's `script_paths`: skills declare
`metadata.mcps: [usaspending, sam_gov, ...]` in frontmatter; the MCP
client subsystem only exposes declared tools to that skill's loop.

### Three skill stances on vendored buyer-side logic

The 1102tools skills were written from the buyer's seat. We can use the
same logic in three stances — each becomes a separate skill (one
persona, one outcome, one set of evals, easier for the LLM to pick
correctly from the description):

| Stance      | Example                                                                                                 | Skill                       |
| ----------- | ------------------------------------------------------------------------------------------------------- | --------------------------- |
| **Reverse** | Take an RFP we received → reconstruct the CO's decision tree → reveal hot buttons + discriminator hooks | `rfp-reverse-engineer`      |
| **Forward** | We write SOWs for OUR subcontractors / teaming partners — same tree, same FAR citations, opposite seat  | `subcontractor-sow-builder` |
| **Inverse** | Same wrap-rate / burden / fee math the CO uses for IGCE → we use it to estimate price-to-win benchmark  | `price-to-win`              |

`price-to-win` is **contract-type agnostic** (one skill, decision tree
over RFP entities to pick FFP / LH&T&M / cost-reimbursement / hybrid
buildup). The three IGCE Builder skills from upstream collapse into
one Theseus skill with three internal cost-model templates under
`references/cost_models/` and a top-level decision tree.

### Re-scoped Phase 4 (sub-phases)

| Sub-phase | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Status              |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| **4a**    | MCP client subsystem in `src/skills/mcp_client.py`: subprocess manager, NDJSON stdio JSON-RPC transport, tool-schema discovery at handshake, lifecycle (per-run sessions, shutdown, stderr → logs).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | ✅ Done             |
| **4b**    | `metadata.mcps: [usaspending, sam_gov, ...]` allowlist field in SKILL.md frontmatter; runtime exposes only declared MCPs to a skill's loop. Mirrors `script_paths` pattern from Phase 3 — same security shape.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | ✅ Done             |
| **4c**    | Vendor first MCP (USAspending — no API key required → fastest end-to-end validation) into `tools/mcps/usaspending/` via `uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp`. `docs/PHASE_4C_MCP_TOOLCHAIN.md` covers install, verify, troubleshooting. `tests/skills/test_usaspending_manifest.py` proves discovery + live handshake (≥30 tools, `search_awards`/`spending_by_category`/`get_award_detail` present).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | ✅ Done             |
| **4d**    | Promote `competitive-intel` skill from PLACEHOLDER → real tools-mode skill: declares `metadata.mcps: [usaspending]`, 10-step workflow checklist drives `mcp__usaspending__*` calls through the runtime to produce a black-hat brief grounded in live federal award data + workspace KG chunks. Output JSON envelope (`opportunity_context`, `incumbent`, `competitors[]`, `pricing_benchmark`, `recompete_signals`, `data_provenance`) + per-competitor markdown one-pagers. Honest claim_gaps on every run for sources not yet wired (SAM.gov, FPDS, CPARS, protests, news). Contract tests in `tests/skills/test_competitive_intel_skill.py` (3 offline + 1 live drift check).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | ✅ Done — `2cf328d` |
| **4e**    | UI: Settings → MCP Servers panel (install, enter API keys, view status, view stderr). Required for key-gated MCPs landing in 4f. Reuses the Phase 3c artifact-download endpoint pattern for status polling.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | ✅ Done — `0a0fbca` |
| **4f**    | Vendor remaining MCPs from `1102tools/federal-contracting-mcps`, **one MCP per branch** so `skill-creator` can be applied cleanly to each downstream skill enhancement. Order: **4f.1 `ecfr`** (no key, manifest + tests + toolchain doc; ✅ done), **4f.2 `compliance-auditor` consumes eCFR** (`metadata.mcps: [ecfr]`, C9 clause-existence + C10 clause-currency, `references/ecfr_tools.md`, contract tests; ✅ done), **4f.3 `gsa-calc`** (no key, ✅ done), **4f.4 `gsa-perdiem`** (no key, ✅ done), **4f.5 `federal-register`** (no key, ✅ done), **4f.6 `sam-gov`** (key-gated `SAM_GOV_API_KEY`, 19 tools spanning entities + exclusions + opportunities + FPDS-NG awards + PSC + orgs + subawards; first key-gated MCP, manifest + tests + toolchain doc; ✅ done). Note: there is no standalone FPDS MCP — upstream consolidates FPDS data into `sam-gov-mcp`. **4f.7 `bls-oews`** (key-gated `BLS_API_KEY`, 7 tools — wage data + IGCE benchmarks + metro/SOC comparisons + reference helpers; powers IGCEs and price-to-win labor-rate analysis; manifest + tests + toolchain doc; ✅ done). **4f.8 `regulations-gov`** (key-gated `API_DATA_GOV_KEY`, 8 tools — rulemaking docket + document + comment search/detail, open comment-period tracking, FAR case history; surfaces in-flight FAR/DFARS amendments before they hit eCFR and public-comment intelligence on proposed rules; PyPI name `regulationsgov-mcp` (no hyphen); manifest + tests + toolchain doc; ✅ done — closes the MCP-vendoring stretch). All 8 federal MCPs from `1102tools/federal-contracting-mcps` now vendored and live-tested. Downstream skill enhancements (`competitive-intel` + `sam_gov`, `compliance-auditor` + `sam_gov`, `proposal-generator` + `bls_oews` for IGCE, `competitive-intel` + `bls_oews` for labor-rate benchmarks, `compliance-auditor` + `regulations_gov` for in-flight NPRM detection, `competitive-intel` + `regulations_gov` for comment-period intel) deferred to 4f.6.x / 4f.7.x / 4f.8.x sub-branches. | 🟡 4f.1–4f.8 done   |
| **4g**    | Vendor `IGCE Builder` skills (FFP + LH/T&M + Cost-Reimbursement) from `1102tools/federal-contracting-skills`, **collapse into one `price-to-win` skill** under `.github/skills/price-to-win/`. Cost-model decision tree at top of SKILL.md (FFP / LH / T&M / CPFF / CPAF / CPIF / hybrid); three IGCE buildup references under `references/cost_models/`. UPSTREAM.md formalizes the buyer→bidder stance inversion (drops `ai-boundaries.md` linkage; adds explicit `ptw_recommendation` block with target_price + rationale + risk_flags). Consumes `bls_oews` + `gsa_calc` + `gsa_perdiem` MCPs (already vendored in 4f.7 / 4f.3 / 4f.4). Contract tests in `tests/skills/test_price_to_win_skill.py` (6 always-on + 1 live drift); 3 evals (FFP / LH / CPAF). `docs/PHASE_4G_PRICE_TO_WIN_SKILL.md` covers design, inversion, and re-vendor process.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | ✅ Done — `49f20f7` |
| **4h**    | Vendor `SOW/PWS Builder` from `1102tools/federal-contracting-skills` → **two separate Theseus skills**, each owning its own `references/` (runtime sandbox `tool_read_file` rejects cross-skill paths — see `docs/PHASE_4H_SOW_SKILLS.md`): `subcontractor-sow-builder` (FORWARD stance — prime writes SOW/PWS for our subs / teaming partners; 14-section spec, intake-then-blocks workflow, FAR 37.102(d) no-FTEs-in-body, chat-only Staffing + CLIN handoffs) and `rfp-reverse-engineer` (REVERSE stance — given an RFP we received, reconstruct the CO's hidden 3+6 decision tree, surface hot buttons / discriminator hooks / ghost language / missing-section signals, detect FAR 52.237-2 + bare-16.306 + QASP↔CPARS traps, emit JSON envelope). Both skills closed-by-default (no MCPs); both consume workspace KG only. Contract tests in `tests/skills/test_subcontractor_sow_builder_skill.py` (8 tests) + `tests/skills/test_rfp_reverse_engineer_skill.py` (8 tests). 3 evals each. UPSTREAM.md on each documents the 5-point stance-inversion contract.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | ✅ Done — `76682c6` |
| **4i**    | Vendor `OT Project Description Builder` + `OT Cost Analysis` upstream skills as `ot-prototype-strategist` (single Theseus skill that handles project description + cost reasoning together since OT prototypes are scoped and priced in one capture-team loop). Workflow Selector at top of SKILL.md (Respond to OT solicitation / Pre-solicitation strategist / Cost-share path comparison / Sub price reasonableness). Cites 10 USC 4021 / 4022 / 4022(d)(1)(A-D) / 4022(f) / 4003 + 10 USC 3014 NDC test (NOT FAR). Same MCP trio as `price-to-win` (`bls_oews` + `gsa_calc` + `gsa_perdiem`). Bidder-stance inversion in `UPSTREAM.md` (5-point contract). 4 references under progressive disclosure (authority taxonomy, TRL milestone patterns, OT milestone cost buildup, KG query patterns). 3 evals (4022 NDC bid / 4021 academic bid / 4022(d) path comparison). 7 always-on contract tests + 1 opt-in live MCP drift check. Closes Phase 4. See `docs/PHASE_4I_OT_PROTOTYPE_STRATEGIST.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | ✅ Done — `4753293` |
| **4j**    | **Skill taxonomy + frontmatter pass.** Adopt three-axis classification (`personas_primary` / `personas_secondary` / `shipley_phases` / `capability`) across all SKILL.md files. Authoritative vocabularies live in `docs/SKILL_TAXONOMY.md` (single source of truth, mirrors extraction-prompt persona list). Added 8th item to Cross-Cutting Change Checklist. New `oci-sweeper` skill (legal_compliance / audit / pursuit + capture; FAR Subpart 9.5; closed-by-default, KG-only). UI Skills page now groups by `personas_primary` with phase + capability filter pills. **Note**: Adopted flat keys (`personas_primary`, `personas_secondary`) instead of nested `personas: {primary, secondary}` because `manager.py::_parse_frontmatter` only supports one level of nesting under `metadata:`. Contract test `tests/skills/test_skill_taxonomy.py` enforces the closed vocabularies. See `docs/PHASE_4J_SKILL_TAXONOMY.md`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | ✅ Done — `586f650` |

### Sub-phase 4j: Three-axis skill taxonomy

**Why three axes** (not one, not two, not free-form tags): Personas
answer "who you are", Shipley phases answer "when in the lifecycle",
capability answers "what action you need right now." Each axis is
orthogonal and answers a different discovery question. Free-form tags
drift; pure persona buckets force false-precision when one skill
serves multiple personas (e.g., `price-to-win` is genuinely both Cost
Estimator AND Capture Manager).

**Frontmatter shape** (added to existing `metadata:` block — stays
spec-portable, no new top-level YAML fields):

```yaml
metadata:
  personas:
    primary: cost_estimator # one of 8 canonical IDs
    secondary: [capture_manager] # zero or more
  shipley_phases: # zero or more (skill may span phases)
    - strategy
    - proposal_development
  capability: estimate # one of ~7 closed-vocab verbs
  category: domain # existing field unchanged
```

**Persona vocabulary (8 IDs, mirrors extraction prompt verbatim):**
`capture_manager`, `proposal_manager`, `proposal_writer`,
`cost_estimator`, `contracts_manager`, `technical_sme`,
`legal_compliance`, `program_manager`. Plus implicit `none` for
utility/meta skills (huashu-design, renderers, skill-creator).

**Shipley phase vocabulary (6 phases):** `pursuit`, `capture`,
`strategy`, `proposal_development`, `negotiation`, `post_award`. Skills
may span multiple phases.

**Capability vocabulary (7 verbs, closed):** `research` (gathers from
external sources), `analyze` (examines KG, produces findings), `draft`
(produces narrative for proposals), `audit` (validates against
rules/regs), `estimate` (produces quantitative models), `render`
(converts content to deliverable formats), `meta` (operates on other
skills).

**UI implications:**

- Skills sidebar groups by `personas.primary`; secondary surfaces as a
  "also relevant for…" badge.
- Filter pills for `shipley_phases` and `capability` provide
  orthogonal navigation (same skill catalog, different lenses).
- Command-palette-style discovery: "[draft] for [proposal_manager] in
  [proposal_development]" → exact skill match.

**Backfill order:** Existing 7 skills (proposal-generator,
compliance-auditor, competitive-intel, govcon-ontology, huashu-design,
renderers, skill-creator) + the 5 new Phase 4 skills (price-to-win,
rfp-reverse-engineer, subcontractor-sow-builder,
ot-prototype-strategist, oci-sweeper) all land with full taxonomy in
the same commit as 4j. No retrofit PRs.

**Future skills explicitly scoped by this taxonomy:**

- `oci-sweeper` (Legal/Compliance, capture phase, audit capability) —
  scans workspace customer/incumbent/partner/subcontractor entities
  against firm contract history for Organizational Conflict of
  Interest per FAR Subpart 9.5. Companion to `compliance-auditor` with
  narrower legal lens. Added to extraction prompt's Legal/Compliance
  persona alongside this phase.

### What we drop from the original Phase 4

- `src/skills/datasources/{sam_gov,usaspending,fpds,cache}.py` — replaced by vendored MCPs
- `intel_search_opportunities` / `intel_award_history` / `intel_vendor_profile` as in-process runtime tools — replaced by MCP-discovered tools (same names from the LLM's perspective; backed by subprocess MCP, not in-process function)

### Net effect

Phase 4 stops being "build six API clients" and becomes "add an
MCP-client subsystem + vendor what the federal-contracting community
already hardened." The runtime subsystem (4a-4b) is the only new
infrastructure work; everything after is mechanical vendoring. Long-
term cost goes down — every future MCP (custom internal, third-party,
new federal data source) installs without runtime changes.

**Sequencing within Phase 4:** 4a → 4b → 4c (proves the chain end-to-
end with one MCP) → 4d (UI for keys) → 4e+4f+4g+4h (parallelizable
vendoring; pick by capture-team priority) → 4i (proves capture intent
end-to-end).

---

## Phase 5 — Skill-built sub-agents (re-scoped 2026-04-28)

### Original plan

Skills invoke other skills via an `invoke_skill(name, prompt)` runtime
tool. Example: `proposal-generator` calls `compliance-auditor` →
`competitive-intel` → `huashu-design`.

### What changed

Three things make Phase 5 simpler than originally specced:

1. **Tools-mode runtime (sub-phase 2.1) already supports nesting at the
   process level.** A skill can shell out to another skill's scripts via
   `run_script`. The only thing missing is invoking another skill as a
   full agent loop (with its own SKILL.md + tools + transcript).
2. **huashu-design is a skill, not a tool.** When `proposal-generator`
   wants a slide deck rendered, it should `invoke_skill("huashu-design",
"render this slide_master.html as PPTX")` — not call `html2pptx.js`
   directly. This keeps each skill in charge of its own quality bar
   (huashu's Playwright verify step, design critique, etc.).
3. **Transcript composition is the hard part.** When skill A invokes
   skill B, B's transcript should nest under A's run_dir, not pollute
   the global `skill_runs/` view.

### Re-scoped Phase 5

| Item                                                                                                                 | Status         |
| -------------------------------------------------------------------------------------------------------------------- | -------------- |
| `invoke_skill(name, prompt)` runtime tool                                                                            | ⏳ Not started |
| Nested run*dirs: invoked skill's `<run_dir>` lives at `<caller_run_dir>/sub_skills/<name>*<timestamp>/`              | ⏳ Not started |
| Transcript merging: caller's `transcript.json` records `tool: invoke_skill` with a pointer to the sub-skill's run_id | ⏳ Not started |
| UI drawer: nested skill runs render as collapsible sub-trees in the parent transcript                                | ⏳ Not started |
| Loop guard: max nesting depth 3, max sub-skill turns 20 (configurable)                                               | ⏳ Not started |
| Allowlist: SKILL.md declares `metadata.invokes: [skill-a, skill-b]`; runtime enforces                                | ⏳ Not started |
| Reference chain: `proposal-generator` invokes `compliance-auditor` → `competitive-intel` → `huashu-design`           | ⏳ Not started |

**Net effect:** Phase 5 stays scoped as originally planned but adds
explicit allowlisting, depth/turn caps, and nested transcript handling
— concerns that came into focus only after sub-phase 2.3's transcript
drawer made multi-turn runs first-class in the UI.

---

## End-to-end target (post-Phase 5)

Single user prompt: _"Draft a Volume 1 Technical for the AFCAP V ADAB
ISS RFP, with a black-hat read on the incumbent and an exec one-pager."_

```
proposal-generator (caller)
  ├─ kg_query(...)                              → pull requirements + eval factors
  ├─ kg_chunks("PWS section 4", top_k=10)       → ground in source text
  ├─ invoke_skill("compliance-auditor", ...)    → audit gaps before drafting
  │     └─ kg_query(...) [in sub-skill run_dir]
  ├─ invoke_skill("competitive-intel", ...)     → black-hat brief
  │     ├─ intel_award_history(naics=541512)    → USAspending
  │     ├─ intel_vendor_profile("ManTech")      → SAM.gov + FPDS
  │     └─ write_file("blackhat_mantech.md")
  ├─ synthesize win themes from KG + intel chunks
  ├─ write_file("volume_1_technical.md")
  ├─ run_script("…/pandoc-md-to-docx.py", "volume_1_technical.md")  → .docx
  └─ invoke_skill("huashu-design", "render one_pager.html as PPTX + PDF")
        ├─ run_script("scripts/html2pptx.js", "one_pager.html")     → .pptx
        ├─ run_script("scripts/export_deck_pdf.mjs", ...)           → .pdf
        └─ run_script("scripts/verify.py", ...)                     → smoke-test
```

Outputs in `<run_dir>/artifacts/`:

- `volume_1_technical.md` + `volume_1_technical.docx`
- `compliance_matrix.html` + `compliance_matrix.xlsx`
- `blackhat_mantech.md`
- `one_pager.pptx` + `one_pager.pdf`

UI drawer surfaces nested skill runs, all artifacts downloadable, every
KG citation traceable back to a chunk_id. **This is "Theseus running its
own capture team" in concrete terms.**

---

## Dropped from original roadmap

| Original item                               | Reason dropped                                                                          |
| ------------------------------------------- | --------------------------------------------------------------------------------------- |
| Phase 2 declarative `workflow:` frontmatter | Open Skills spec uses imperative tools-mode; declarative chains are strictly weaker.    |
| `template.render` tool                      | `run_script` + huashu's `html2pptx.js` / `export_deck_pdf.mjs` cover the same surface.  |
| "Phase 2.5" placeholder                     | Was speculative — no longer needed; tools-mode delivered multi-step capability cleanly. |

---

## Sequencing recommendation

1. ~~**Phase 3a toolchain install**~~ ✅ Done 2026-04-28
2. ~~**Phase 3b wire `proposal-generator` → huashu via `run_script`**~~ ✅ Done 2026-04-28
3. ~~**Phase 3c drawer binary mimetype support**~~ ✅ Done 2026-04-28
4. ~~**Phase 3d DOCX renderer**~~ ✅ Done 2026-04-28
5. ~~**Phase 3e XLSX renderer**~~ ✅ Done 2026-04-28
6. **Phase 4a-4c MCP client subsystem + first vendored MCP** (USAspending end-to-end as proof)
7. **Phase 4j taxonomy + frontmatter pass** (do this BEFORE 4d-4i so new skills land with full metadata, not a retrofit)
8. **Phase 4d-4i UI + remaining MCP/skill vendoring** (parallelizable; pick by capture-team priority)
9. **Phase 5 `invoke_skill`** (only valuable once 3 + 4 produce real outputs)
10. **Phase 6 Studio (deliverables library + reasoning view)** (can run in parallel with 4/5 — backend index + UI; reuses existing transcripts)

---

## Phase 6 — Studio (deliverables library + reasoning view) (added 2026-04-28)

### Why this phase exists

Phase 3c gave skill artifacts a download surface inside the skill-run
drawer — a developer view, scoped to one run at a time. Federal capture
teams don't think in "skill runs"; they think in **deliverables**: "the
Volume 1 draft", "the compliance matrix for AFCAP V", "the black-hat
brief on the incumbent". They also distrust black-box AI output. Both
gaps need a user-facing surface alongside the existing **RFP
Intelligence** capture page.

### Scope

A new top-level UI surface — **Studio** (originally pitched as **Products**, **Deliverables /
Capture Library**, named **Studio** as of 2025-04-28) — that aggregates
every artifact across every skill run in the active workspace, plus a
deterministic "reasoning view" that explains how each artifact was
produced from the data already captured in the per-run
`transcript.json`.

> **On-disk reality (corrects earlier draft):** runs live at
> `<workspace_root>/skill_runs/<skill>/<run_id>/artifacts/*`, NOT at
> `rag_storage/<workspace>/skills/<name>/runs/...`. The Studio aggregator
> walks the real path.

### Re-scoped Phase 6 (sub-phases)

| Sub-phase | Item                                                                                                                                                                                                                                                                  | Status                                                                                                                                   |
| --------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| **6a**    | Cross-run artifact index endpoint: `GET /api/ui/studio` returns flat list `{skill, run_id, filename, mime, size, ext, created_at, title?}`                                                                                                                            | ✅ Done — first commit on `137-phase-6-studio`                                                                                           |
| **6a**    | Aggregator walks `<workspace_root>/skill_runs/<skill>/<run_id>/artifacts/*` via `SkillManager.list_deliverables` (no new on-disk schema)                                                                                                                              | ✅ Done — first commit on `137-phase-6-studio`                                                                                           |
| **6a**    | New top-level **Studio** entry in left sidebar of `src/ui/static/index.html`; rows link to existing `/api/ui/skills/{name}/runs/{run_id}/artifacts/{filename}` download                                                                                               | ✅ Done — first commit on `137-phase-6-studio`                                                                                           |
| **6a**    | Filters: by skill, by format (DOCX / XLSX / PDF / PPTX / MP4 / GIF / MD / JSON), free-text on filename + title                                                                                                                                                        | ✅ Done — first commit on `137-phase-6-studio` (date filter deferred)                                                                    |
| **6a**    | Per-artifact actions: Download, Open Originating Run (deep-link to skill-run drawer)                                                                                                                                                                                  | ✅ Done — first commit on `137-phase-6-studio`                                                                                           |
| **6a-2**  | Inline preview pane per format: PDF.js (PDF), Mammoth.js (DOCX), SheetJS (XLSX), `<video>` (MP4), native `<img>` (GIF), syntax-highlighted (MD/JSON)                                                                                                                  | ⏳ Not started — follow-up commit on same branch                                                                                         |
| **6a-2**  | Per-artifact extras: Regenerate (re-invoke originating skill with same prompt), Archive, Pin                                                                                                                                                                          | ⏳ Not started — follow-up commit on same branch                                                                                         |
| **6a-2**  | Optional: KG back-links — each artifact's JSON envelope (when present) cites `chunk_id`s; click opens chunk inspector for that entity                                                                                                                                 | ⏳ Not started — follow-up commit on same branch                                                                                         |
| **6b.1**  | "Why this artifact?" view: deterministic transcript → narrative renderer (no extra LLM call). Walks `transcript.json` and renders each tool call as prose.                                                                                                            | ✅ Done — `138-phase-6b-reasoning-view` (`src/skills/reasoning.py`)                                                                      |
| **6b.1**  | Tool-call → human-language mapping: `kg_entities(types=[…])` → "Pulled N entities of type X"; `kg_chunks(query=…)` → "Searched for ‘…' and read N chunks"                                                                                                             | ✅ Done — covers all 6 SkillManager tools                                                                                                |
| **6b.1**  | Each narrative step links to the raw tool call + result in the transcript (collapsible JSON), so power users can audit                                                                                                                                                | ✅ Done — expandable per-step args + result_preview in reasoning drawer                                                                  |
| **6b.2**  | Citation chain surfaces inline: every `chunk_id` referenced in the artifact resolves to the originating chunk's preview                                                                                                                                               | ✅ Done — chunk-id chips open inline preview modal via `GET /api/ui/chunks/{chunk_id}` (right-click chip still copies the id)            |
| **6b.2**  | Chat source cards (multimodal): TABLE/IMAGE/EQUATION sources show the cleaned VLM Analysis narrative as the collapsed excerpt; auto-hydrate from full chunk when truncated; "View full chunk" launcher opens the same Studio chunk-preview modal (Cleaned/Raw + copy) | ✅ Done — `139-phase-6b2-chunk-preview` (`formatSource()` Analysis-paragraph extractor + `.source-card-view-btn` → `openChunkPreview()`) |

### Why this is "simplistic" (per user requirement)

6b adds **zero new inference**. The per-run `transcript.json` already
records every tool call (`kg_entities`, `kg_chunks`, `kg_query`,
`read_file`, `run_script`, `write_file`) with full args + results. The
reasoning view is a deterministic renderer over that data — pure
data-to-prose mapping, no LLM, no latency. If the transcript shows a
chunk_id, the view shows a citation. If it shows a Cypher query, the
view says "ran a graph trace for L↔M coverage". This is auditable and
reproducible by definition.

### Dependencies

- ✅ Phase 2.1 tools-mode runtime (writes `transcript.json`)
- ✅ Phase 3c artifact download endpoint (reused per row)
- 🔵 Independent of Phase 4 (datasources) and Phase 5 (`invoke_skill`) —
  but composes naturally with both: Phase 4 artifacts (intel briefs)
  show up in the library automatically; Phase 5 nested transcripts
  render as collapsible sub-trees in the reasoning view.

### Net effect

Closes the loop between "skills as tools" (developer surface) and
"products as deliverables" (capture-team surface). The black-box
problem is mitigated by surfacing the reasoning trail we already
persist — no new LLM calls, no schema changes, no new on-disk artifact
format.
