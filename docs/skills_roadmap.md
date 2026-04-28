# Skills Roadmap

Authoritative roadmap for the Theseus skills subsystem. Supersedes the
legacy `Roadmap.md` for skills work — that file is a vestige and its
items live in GitHub issues now.

**Last updated:** 2026-04-28 · **Branch:** `121-roadmap-recalibration`

---

## Status snapshot

| Phase   | Scope                                              | State                           | Evidence                                                                    |
| ------- | -------------------------------------------------- | ------------------------------- | --------------------------------------------------------------------------- |
| **1**   | Output persistence (`skill_runs/` + Recent Runs)   | ✅ Done                         | `7833d76`                                                                   |
| **1.5** | Source-grounded briefing book (verbatim citations) | ✅ Done                         | `ad5d8d9`                                                                   |
| **1.6** | Chat-grade hybrid retrieval (mix mode + reranker)  | ✅ Done                         | `ad5d8d9`                                                                   |
| **2.0** | Open Skills spec compliance — vendor skill-creator | ✅ Done                         | `9134f0f`                                                                   |
| **2.1** | Tool-calling runtime (imperative agent loop)       | ✅ Done                         | `b4b9e33`                                                                   |
| **2.2** | Migrate `proposal-generator` to tools-mode         | ✅ Done                         | `7f4e75b`, `914a4eb`, `4cf5c42`, `1bfb99b`                                  |
| **2.3** | Migrate remaining 4 skills + UI transcript drawer  | ✅ Done                         | `98980a7`, `2dc8e1a`, `55d694b`, `d3cf024`, `90610d7`, `fe716a4`, `5bba9be` |
| **3**   | Artifact renderers (HTML → PPTX/PDF/MP4/DOCX/XLSX) | 🟡 3a+3b+3c+3d done, 3e pending | See §Phase 3 below                                                          |
| **4**   | External datasources (SAM.gov, USAspending, FPDS)  | ⏳ Not started                  | `competitive-intel` is a stub                                               |
| **5**   | Skills invoking other skills (sub-agents)          | ⏳ Not started                  | needs `invoke_skill` tool                                                   |

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

| Sub-phase | Item                                                                                                                                                    | Status      | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **3a**    | Toolchain install (Node + Playwright + Chromium via huashu `package.json`)                                                                              | ✅ Done     | `docs/PHASE_3A_TOOLCHAIN.md`; smoke-tested `export_deck_pdf.mjs` → 23KB vector PDF                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **3b**    | `proposal-generator` SKILL.md references `huashu-design` scripts via `run_script` (cross-skill `script_paths` + CLI `args` + `{artifacts}` placeholder) | ✅ Done     | E2E smoke test: 23.8KB vector PDF rendered through runtime; `metadata.script_paths` opt-in keeps spec-portable                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **3c**    | Drawer "Download artifacts" section recognizes binary mimetypes (.pptx/.pdf/.mp4/.gif)                                                                  | ✅ Done     | New `GET /api/ui/skills/{name}/runs/{run_id}/artifacts/{filename}` (path-traversal-safe FileResponse with `mimetypes.guess_type`); drawer renders `skills.run.artifacts` as download links with type-aware icons + size; CSS `.skill-artifacts-panel`                                                                                                                                                                                                                                                                                                            |
| **3d**    | DOCX renderer (Pandoc MD → DOCX) for proposal volumes — huashu doesn't ship this                                                                        | ✅ Done     | `docs/PHASE_3D_TOOLCHAIN.md`; new **`renderers`** utility skill at `.github/skills/renderers/` owns format-conversion scripts (`scripts/render_docx.py` is pure-stdlib Python wrapper around `pandoc`); proposal-generator opts in via `metadata.script_paths: [../renderers/scripts]` and uses Step 12b; E2E smoke test rendered 10.7KB DOCX through the runtime, exit_code==0; install hint surfaced when `pandoc` missing (rc=127). Pattern is reusable: future skills (compliance-auditor, competitive-intel, writer) just add the same `script_paths` line. |
| **3e**    | XLSX renderer (openpyxl) for compliance matrix — huashu doesn't ship this                                                                               | ⏳ Not done |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| —         | `template.render` runtime tool                                                                                                                          | ❌ Dropped  | Superseded by `run_script` + huashu scripts                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |

**Net effect:** Phase 3 shrinks from "build five renderers" to "install
the toolchain + wire huashu + add two govcon-specific renderers (DOCX,
XLSX) that huashu doesn't cover."

**Phase 3a notes (2026-04-28):** Playwright bundles its own ffmpeg, so
no system ffmpeg install is needed for video work. Pandoc was added in
3d (`docs/PHASE_3D_TOOLCHAIN.md`). Python deps untouched; snapshots in
`tools/_dep_snapshots/` (gitignored) provide rollback.

---

## Phase 4 — External datasources (re-scoped 2026-04-28)

### Original plan

Build `src/skills/datasources/` clients for SAM.gov, USAspending, FPDS,
GSA eLibrary. Rate-limited + cached. Add `datasources:` SKILL.md field.

### What changed

The tools-mode runtime (sub-phase 2.1) already has the right shape for
this — datasources should be **runtime tools**, not a separate
subsystem. Pattern matches `kg_query` / `kg_chunks`: each is a typed
tool the LLM calls.

Also: huashu-design's `#0 事实验证先于假设` rule (the WebSearch-first
discipline) is the right philosophical model for `competitive-intel`.
Don't hallucinate award history — fetch and cite.

### Re-scoped Phase 4

| Item                                                                                                         | Status                                                                           |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------- |
| `src/skills/datasources/sam_gov.py` — SAM.gov Opportunities + Entity client (API key from `SAM_API_KEY` env) | ⏳ Not started                                                                   |
| `src/skills/datasources/usaspending.py` — USAspending award search (no key required)                         | ⏳ Not started                                                                   |
| `src/skills/datasources/fpds.py` — FPDS Atom feed parser (no key required)                                   | ⏳ Not started                                                                   |
| `src/skills/datasources/cache.py` — Disk cache to `rag_storage/_platform/intel_cache/`, TTL per source       | ⏳ Not started                                                                   |
| Runtime tools: `intel_search_opportunities`, `intel_award_history`, `intel_vendor_profile`                   | ⏳ Not started                                                                   |
| Tools restricted to skills with `metadata.datasources: [sam_gov, usaspending, ...]` declared                 | ⏳ Not started                                                                   |
| `competitive-intel` SKILL.md migrated from `legacy` placeholder → `tools` mode using the new tools           | ⏳ Not started                                                                   |
| GSA eLibrary client                                                                                          | 🔵 Deferred — lower priority; schedules are mostly relevant for GSA-vehicle bids |

**Net effect:** Phase 4 stays roughly the same scope as originally
planned. The change is delivery model — datasources surface as runtime
tools (consistent with KG access), not a parallel pre-fetch system.

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
4. **Phase 3d + 3e DOCX/XLSX renderers** (the two huashu doesn't cover)
5. **Phase 4 SAM.gov + USAspending clients** (highest-leverage external data)
6. **Phase 5 `invoke_skill`** (only valuable once 3 + 4 produce real outputs)
