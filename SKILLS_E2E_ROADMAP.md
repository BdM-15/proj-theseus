# Skills E2E Hardening Roadmap

> **Authoritative tracker for the `142-skills-e2e-hardening` epic.**
> Read this BEFORE doing any work on skills, renderers, or the Studio UI.
> Update the status table in the same commit as any work that lands.

**Epic branch**: `142-skills-e2e-hardening` (integration parent — never edit directly)
**Target tag on merge to main**: `v1.3.0`
**Started**: 2026-04-29
**Status**: 🟡 In progress

---

## Why this epic exists

`v1.2.0` shipped the Skills + MCP MVP (13 skills, tool-calling runtime, Studio UI). We have **never validated end-to-end** that:

1. Each skill actually completes its tool loop without erroring.
2. Skills reliably ground their output in the active workspace's processed data (chunk citations, KG entities) — not LLM general knowledge.
3. Artifacts render in the correct format and are downloadable / viewable in the Studio UI.
4. The 9 in-house skills were authored / can be defended via the mandatory `skill-creator` workflow (vendored skills `skill-creator` and `huashu-design` are exempt).

Two specific bugs are already known:

- **`huashu-design/SKILL.md` description is entirely Chinese** → English trigger phrases in user prompts may not match the description, causing the LLM to skip the skill.
- **`renderers/SKILL.md` description over-claims** "DOCX, XLSX, PDF, PPTX, MP4, GIF" but the body says PDF/PPTX/MP4/GIF must be routed to `huashu-design`. Misleading triggering.

---

## Branch topology

```
main (protected — never edited directly)
 └── 142-skills-e2e-hardening   ← EPIC integration branch
      ├── 143-renderers-scope-fix
      ├── 144-huashu-frontmatter-english
      ├── 145-skills-e2e-test-harness
      ├── 146-skill-creator-reverify-pass
      ├── 147-renderers-grounding-audit
      └── 148-studio-download-edit-loop
```

**Rules:**

- All work happens on sub-branches. `142` is updated only via `git merge --ff-only <sub-branch>`.
- `main` is updated only when `142` is complete, all gates pass, and `v1.3.0` is tagged.
- No `git commit` without explicit user approval (per `.github/copilot-instructions.md`).
- After each sub-branch FFs into `142`, return to a fresh sub-branch off `142` for the next wave.

---

## Status board

| ID  | Branch                            | Wave | Owner intent                                                                                        | Status         | FF'd into 142 | Notes                                                                                                                                                                                                                      |
| --- | --------------------------------- | ---- | --------------------------------------------------------------------------------------------------- | -------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 142 | `142-skills-e2e-hardening`        | epic | integration parent                                                                                  | 🟡 active      | —             | Created 2026-04-29                                                                                                                                                                                                         |
| 143 | `143-renderers-scope-fix`         | 1a   | Trim renderers description; delegate non-DOCX/XLSX to huashu-design                                 | ✅ done        | ✅ `9aa1654`  | skill-creator workflow followed (snapshot → evals → draft → smoke). 6 evals incl. 2 new delegation prompts. Desc 1017/1024 chars. v0.4.0                                                                                   |
| 144 | `144-huashu-frontmatter-english`  | 1b   | Translate `description` to English; preserve Chinese under `metadata.description_zh`; refresh evals | ✅ done        | ✅ `8b2da7e`  | skill-creator workflow followed (snapshot → 6 EN/bilingual evals → draft → smoke). Desc 1002/1024 chars. v0.2.0. Body unchanged (upstream Chinese). YAML-quoting hotfix landed in 145.                                     |
| 145 | `145-skills-e2e-test-harness`     | 2    | `tests/skills/e2e/` runner + seeded fixture workspace                                               | ✅ done        | ⏳ pending    | Scaffold + harness fix landed. Pivoted fixture to `afcap5_adab_iss`. Fixed grounding-signal parser (was reading `turn["tool"]` which never exists; transcript actually uses `tool_calls:[{name}]` arrays + `kind:"tool"` results). Added `UTILITY_SKILLS={renderers}` exemption from kg_*-required check. **Run 005 baseline: 9 passed / 3 xfailed** (afcap5_adab_iss, pandoc on PATH). Xfails: `competitive-intel`, `price-to-win`, `subcontractor-sow-builder` — real artifact-emit gaps for branch 146. Logs gitignored under `tools/_e2e_runs/`. |
| 146 | `146-skill-creator-reverify-pass` | 3a   | Re-author 9 in-house skills via skill-creator workflow; **priority: fix the 3 artifact-emit xfails first** (competitive-intel, price-to-win, subcontractor-sow-builder) | ⏳ not started | ❌            | Depends on 145. First three sub-passes target the run_005 xfails — each must end with the skill calling `write_file` reliably. Use `skill-creator` workflow (snapshot → evals → draft → smoke → re-run e2e) per skill.                                                                                                                                                                |
| 147 | `147-renderers-grounding-audit`   | 3b   | Verify ≥80% claim-to-citation ratio per skill                                                       | ⏳ not started | ❌            | Depends on 145                                                                                                                                                                                                             |
| 148 | `148-studio-download-edit-loop`   | 4    | Manual UI walkthrough + Playwright smoke for view/download/edit cycle                               | ⏳ not started | ❌            | Last — gates merge to main                                                                                                                                                                                                 |

**Status legend**: ⏳ not started · 🟡 in progress · ✅ done · 🚫 blocked

---

## Skills inventory (relevant to this epic)

**Vendored (re-verification SKIPPED):**

- `.github/skills/skill-creator/` — Anthropic upstream
- `.github/skills/huashu-design/` — upstream HTML design skill (only frontmatter-EN edit allowed; body stays Chinese)

**In-house (must pass `skill-creator` re-verification in branch 146):**

1. `proposal-generator`
2. `compliance-auditor`
3. `competitive-intel`
4. `price-to-win`
5. `oci-sweeper`
6. `ot-prototype-strategist`
7. `subcontractor-sow-builder`
8. `rfp-reverse-engineer`
9. `govcon-ontology`

**Utility (in-house, also re-verified in 146):**

- `renderers`

---

## Sub-branch detail

### 143 — `renderers-scope-fix` (Wave 1a)

**Goal**: Stop `renderers` from over-advertising formats it doesn't own.

**Changes:**

- [ ] Edit `.github/skills/renderers/SKILL.md` frontmatter `description`:
  - Drop "PDF, PPTX, MP4, GIF" from the headline list
  - Headline becomes: "Universal artifact renderers for Theseus skills. Converts structured content into Word (DOCX) and Excel (XLSX) deliverables…"
- [ ] Add a `## Delegation` section in body: "For PDF / PPTX / MP4 / GIF, hand off to `huashu-design` directly — those formats live in `huashu-design/scripts/`, not here."
- [ ] Verify `tests/skills/test_skill_taxonomy.py` still passes.
- [ ] Verify `description ≤ 1024 chars`.

**Skill-creator gate**: REQUIRED. Description trim is trigger-accuracy optimization per [.github/copilot-instructions.md](.github/copilot-instructions.md) MANDATE. Affirm in commit message that `skill-creator/SKILL.md` was loaded and its workflow followed.

**Exit criteria**: Tests green, diff < 60 lines, user approves the commit message.

---

### 144 — `huashu-frontmatter-english` (Wave 1b)

**Goal**: Make `huashu-design` reliably trigger on English prompts without losing the upstream Chinese content.

**Changes (must follow skill-creator workflow):**

- [ ] **Snapshot**: copy `.github/skills/huashu-design/` → `tools/_skill_snapshots/huashu-design-pre-144/`
- [ ] **Build evals first**: write `evals/evals.json` with ≥3 English trigger prompts ("design a hi-fi prototype for…", "build an interactive demo of…", "make a slide deck about…")
- [ ] **Baseline**: note current behavior (does the LLM even pick the skill on these English prompts today? probably no)
- [ ] **Draft**: rewrite top-level `description:` field in English (target: under 1024 chars, third-person pushy, both WHAT + WHEN)
- [ ] **Preserve original**: add `metadata.description_zh:` containing the original Chinese description verbatim
- [ ] **Body unchanged**: do NOT touch the Chinese body — that's vendored upstream content
- [ ] **Smoke run**: invoke through `SkillManager.invoke(...)` with one of the eval prompts; confirm the skill activates
- [ ] Update `docs/SKILL_TAXONOMY.md` if the trigger vocabulary line for huashu-design needs refreshing

**Skill-creator gate**: REQUIRED. Affirm in commit message that `skill-creator/SKILL.md` was loaded and its workflow followed.

**Exit criteria**: ≥3 English eval prompts present; smoke test activates the skill; original Chinese preserved under `metadata`.

---

### 145 — `skills-e2e-test-harness` (Wave 2)

**Goal**: Give every subsequent sub-branch a way to prove a skill actually runs end-to-end.

**Changes:**

- [ ] Create `tests/skills/e2e/` package
- [ ] Build a minimal seeded test workspace fixture (~50 chunks from a public RFP; consider a small slice of `inputs/doj_mmwr_old_rfp/`)
- [ ] Write a pytest helper `invoke_skill_e2e(skill_name, prompt) -> ToolLoopResult` that:
  - Spins up `SkillManager` against the test workspace
  - Calls `invoke()` with the eval prompt
  - Returns the full transcript + artifact paths
- [ ] Per-skill smoke assertion template:
  - tool loop completed (no exception, `finish_reason != "error"`)
  - transcript contains ≥1 `kg_chunks` or `kg_query` call
  - response cites ≥1 `chunk_id` (regex `chunk-[0-9a-f]{4,}`)
  - artifact (if declared) exists under `skill_runs/<skill>/<run>/artifacts/`
- [ ] Add `pytest -k e2e` runs to ≤10 min total

**Skill-creator gate**: Exempt — this is test infrastructure, not skill authoring.

**Exit criteria**: `pytest tests/skills/e2e -k smoke` runs all 11 skills (9 in-house + huashu-design + renderers) and every assertion is either passing or has an explicit `xfail` reason recorded.

---

### 146 — `skill-creator-reverify-pass` (Wave 3a)

**Goal**: Defensibly affirm every in-house skill was authored via the mandated `skill-creator` workflow.

**For each of the 9 in-house skills + `renderers`:**

- [ ] Snapshot to `tools/_skill_snapshots/<skill>-pre-146/`
- [ ] Refresh `evals/evals.json` to ≥3 realistic prompts
- [ ] Audit frontmatter against the 6-field spec; move any non-spec keys under `metadata:`
- [ ] Audit body length (<500 lines) and progressive disclosure (long content in `references/*.md`)
- [ ] Audit directory layout (`assets/` not `templates/`; one-level `references/`)
- [ ] Run the 145 e2e smoke; capture the result
- [ ] Update `docs/SKILL_SPEC_COMPLIANCE.md` with the re-verification date per skill
- [ ] Commit message body MUST affirm `skill-creator` was loaded for each skill touched

**Skill-creator gate**: REQUIRED — this whole branch IS the gate.

**Exit criteria**: Every in-house `evals/evals.json` has ≥3 prompts; `SKILL_SPEC_COMPLIANCE.md` shows every skill re-verified; e2e smoke green for all.

---

### 147 — `renderers-grounding-audit` (Wave 3b)

**Goal**: Quantify how much of each skill's output came from workspace data vs. LLM general knowledge.

**Changes:**

- [ ] Build `tools/audit_skill_grounding.py`:
  - Reads a transcript JSON from `skill_runs/<skill>/<run>/transcript.json`
  - Counts (a) total assertions in the final response, (b) those backed by `chunk-` or entity-name citations
  - Emits a ratio + a list of unsourced claims
- [ ] Add a `grounding_ratio >= 0.80` assertion to the 145 harness
- [ ] Run all 9 in-house skills against the seeded workspace; record ratios in this roadmap
- [ ] For any skill below 0.80, file follow-up notes (likely a SKILL.md citation-rule strengthening)

**Skill-creator gate**: Exempt for the audit tool itself; if any skill needs SKILL.md edits to hit the ratio, that edit MUST go through skill-creator.

**Exit criteria**: All 9 in-house skills ≥ 0.80 grounding ratio (or have an approved waiver documented).

---

### 148 — `studio-download-edit-loop` (Wave 4)

**Goal**: Manually validate a user can view, download, and re-upload an edited artifact through the Studio UI.

**Walkthrough (record results in this doc):**

- [ ] Invoke each skill from the UI; confirm artifact appears in the Studio drawer
- [ ] Click filename: inline preview renders correctly per format
- [ ] Click download: file downloads with correct mime type (matches `_STUDIO_EXTRA_MIME` in `src/skills/manager.py`)
- [ ] Edit locally; re-upload; confirm UI doesn't accidentally delete the prior version
- [ ] Add a Playwright smoke test if the click sequence is stable (`tests/skills/test_studio_deliverables.py` is the existing entry point)
- [ ] Document any gaps in `docs/SKILL_SPEC_COMPLIANCE.md`

**Skill-creator gate**: Exempt — this is UI validation.

**Exit criteria**: Walkthrough complete; mime types verified; Playwright smoke (if added) green.

---

## Merge checklist (when 142 → main)

- [ ] All 6 sub-branches show ✅ in the status board
- [ ] `pytest tests/skills` (full) green from `.venv`
- [ ] `pytest tests/skills/e2e` green from `.venv`
- [ ] `docs/SKILL_SPEC_COMPLIANCE.md` updated with re-verification dates
- [ ] User has explicitly approved the merge + tag
- [ ] Tag `v1.3.0` cut from `142` head before FF to main
- [ ] After merge: delete sub-branches locally + on origin (with user confirmation)
- [ ] Update `/memories/repo/branch-integration-policy.md` to clear the active epic and note `142` closed
