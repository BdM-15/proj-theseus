# Phase 4j — Three-Axis Skill Taxonomy + `oci-sweeper`

**Status:** ✅ Done — `586f650`
**Branch:** `135-phase-4j-skill-taxonomy` → FF into `120-skills-spec-compliance`
**Authoritative spec:** [docs/SKILL_TAXONOMY.md](SKILL_TAXONOMY.md)
**Roadmap row:** [docs/skills_roadmap.md § 4j](skills_roadmap.md)

---

## What shipped

1. **`docs/SKILL_TAXONOMY.md`** — single-source-of-truth specification of three closed vocabularies:
   - **personas_primary / personas_secondary** — 8 IDs mirroring the extraction prompt's `USER PERSONAS YOU SUPPORT` block + sentinel `none` for utility/meta skills.
   - **shipley_phases** — 6 lifecycle phases (`pursuit`, `capture`, `strategy`, `proposal_development`, `negotiation`, `post_award`).
   - **capability** — 7 verbs (`research`, `analyze`, `draft`, `audit`, `estimate`, `render`, `meta`).
2. **Frontmatter backfill across all 11 skills** (10 existing + 1 new) under `.github/skills/*/SKILL.md`. Each skill now declares the four taxonomy keys at the top of its `metadata:` block.
3. **`oci-sweeper` skill** — new closed-by-default (no MCPs) legal_compliance / audit skill. FAR Subpart 9.5 OCI sweep with three references (taxonomy, remediation playbook, KG query patterns) and 3 evals covering all three FAR 9.505 conflict classes.
4. **Cross-Cutting Change Checklist** in `.github/copilot-instructions.md` extended from 7 items to 8: persona vocabulary changes now require `docs/SKILL_TAXONOMY.md` + every `SKILL.md` to be re-audited in the same PR.
5. **`SkillManager.to_summary()` extended** in `src/skills/manager.py` to surface `personas_primary`, `personas_secondary`, `shipley_phases`, `capability` for the `/api/ui/skills` endpoint.
6. **UI Skills page redesign** in `src/ui/static/index.html` + `src/ui/static/styles/theseus.css`:
   - Cyberpunk filter rail above the grid with three axes (Persona / Phase / Capability), each in its own color (magenta / cyan / amber). Multi-select within an axis = OR; across axes = AND.
   - Persona pills consolidate the 9-id taxonomy into 6 user-facing pills: Capture, Writer, Operations, Cost, Contracts, Legal. "Operations" folds `technical_sme` + `program_manager` (requirements + technical execution). SME and Meta intentionally absent — meta skills pin to the top of the grid via `isMetaSkill` regardless of filters.
   - Each pill carries a tiny count badge (e.g. "Capture 2") computed against the full catalog so toggling one pill never makes another count jump.
   - Right-side meta cluster on the rail: search input (name + description, multi-token AND, debounced), live `Showing X of Y` readout (X glows cyan when filters narrow the set), and a Clear button that appears only when at least one filter or the search query is active.
   - Flat 3-column grid (no per-persona sub-headers). Meta skills (capability=`meta` OR `personas_primary='none'`) pin first with cyan accent + sparkles icon; domain skills follow alphabetically with magenta accent + wand icon.
   - Bug fix in `src/skills/manager.py::Skill.to_summary()`: YAML scalar `none` parses as Python `None`, and `str(None)` = `"None"` (capital N) silently filtered out govcon-ontology, huashu-design, renderers, and skill-creator from the previous grouped UI. Now normalized to `"none"` before projection so all 11 skills surface.
7. **Two contract tests** in `tests/skills/`:
   - `test_skill_taxonomy.py` — enforces closed vocabularies across every skill, verifies extraction-prompt persona block alignment, asserts taxonomy doc exists.
   - `test_oci_sweeper_skill.py` — 9 tests mirroring the compliance-auditor pattern (spec compliance, no MCPs, FAR 9.5 body markers, references non-empty, evals cover all three OCI classes, manager discovery + summary surfaces taxonomy fields).

---

## Design decision — flat keys instead of nested `personas`

The roadmap design block (4j sub-design) sketched a nested shape:

```yaml
metadata:
  personas:
    primary: cost_estimator
    secondary: [capture_manager]
```

We adopted a **flat shape** instead:

```yaml
metadata:
  personas_primary: cost_estimator
  personas_secondary: [capture_manager]
  shipley_phases: [strategy, proposal_development]
  capability: estimate
```

**Why.** `src/skills/manager.py::_parse_frontmatter` (vendored on Phase 4f.2) supports YAML mappings exactly **one level deep** under `metadata:`. Nested mappings (`metadata.personas.primary`) silently parse as a stringified dict on the older Python branches and throw on the strict path. Flat keys round-trip cleanly through every parser, keep the `to_summary()` projection trivial, and make the UI's `s.personas_primary` access a single property hop instead of `s.personas?.primary` with optional chaining. The cost is one extra namespace prefix in YAML; the benefit is zero parser drift.

The roadmap row was updated to reflect the flat shape; future audits should reference `docs/SKILL_TAXONOMY.md`, not the original sub-design block.

---

## `oci-sweeper` — why now and why this shape

OCI risk is a **pre-bid go/no-go gate** that the extraction pipeline already surfaces (the extraction prompt's Legal/Compliance persona explicitly mentions "OCI sweeps" since v6.5). Until 4j we had no skill that _consumes_ those signals. Phase 4j was the natural moment — we were touching every `SKILL.md` for the taxonomy backfill anyway, so adding the missing legal_compliance skill costs almost nothing additional.

**Closed-by-default rationale.** FAR Subpart 9.5 contains exactly 8 sections (9.501–9.508) and three conflict classes; the regulation has been stable for years and changes through the Federal Acquisition Regulatory Council, not on a sprint cadence. Vendoring the taxonomy as a `references/` markdown file is more reliable than wiring an `ecfr` MCP fetch and creates one fewer failure mode. If the FAC amends Subpart 9.5, the reference gets edited in the same PR that updates the test fixtures.

**Three references, one workflow.** The skill body stays under 200 lines (well under the 500-line spec ceiling) by pushing the taxonomy, the mitigation playbook, and the Cypher query patterns into `references/`. Progressive disclosure: the runtime loads them on demand via `read_file` per the numbered workflow checklist, not eagerly at activation time.

**Evals before prose.** Per the `skill-creator` MANDATE, `evals/evals.json` was authored first with three prompts hitting all three FAR 9.505 conflict classes (incumbent → impaired objectivity, customer-side personnel overlap → biased ground rules, prior-contract data access → unequal access). The SKILL.md body and references were drafted to close the gaps those evals exposed.

---

## How the UI groups skills

The `/api/ui/skills` endpoint already returned `to_summary()` per skill; Phase 4j extended that projection to include the four taxonomy fields. The Alpine `theseus()` component now exposes:

- `skillPersonaConfig()` — full display labels for the 9 underlying persona IDs (used by per-card persona tag).
- `skillPersonaFilterConfig()` — the 6 consolidated filter pills (Capture, Writer, Operations, Cost, Contracts, Legal); each entry maps to one or more underlying persona IDs (e.g. Operations → `[technical_sme, program_manager]`).
- `skillPhaseConfig()` / `skillCapabilityConfig()` — display labels for the Phase and Capability filter pills.
- `isMetaSkill(s)` — `true` when `capability === 'meta'` OR `personas_primary === 'none'`. Meta skills pin to the top of the grid regardless of active filters.
- `skillsFiltered()` — flat, filtered, sorted list (meta-first, then alphabetical).
- `skillsCountForPersona(id)` / `skillsCountForPhase(id)` / `skillsCountForCapability(id)` — per-pill count badges, computed against the full catalog so they're stable as filters toggle.
- `skillMatchesFilters(s)` — OR-within-axis, AND-across-axes filter logic, plus multi-token AND search across `name` + `description`.

CSS additions in `theseus.css` (`.filter-rail`, `.filter-rail-rows`, `.filter-rail-meta`, `.filter-rail-search*`, `.filter-rail-count*`, `.filter-axis-label-{magenta,cyan,amber}`, `.filter-pill`, `.filter-pill-active-{cyan,magenta,amber}`, `.filter-pill-count`, `.filter-pill-clear`) reference only existing `:root` tokens. No `@apply` (Tailwind Play CDN does not process external CSS) and no new hex literals.

No `tailwind.config.js` change was needed — the additions are plain CSS, not new Tailwind utilities.

---

## Cross-cutting discipline (8th checklist item)

The persona vocabulary, the Shipley-phase vocabulary, and the capability-verb vocabulary are now **closed sets** with three enforcement points:

1. **`docs/SKILL_TAXONOMY.md`** — single source of truth.
2. **`tests/skills/test_skill_taxonomy.py`** — fails any drift (unknown persona ID, unknown phase, unknown capability, missing keys, primary duplicated in secondary, persona block missing from extraction prompt).
3. **`.github/copilot-instructions.md` Cross-Cutting Change Checklist item 8** — every PR that touches the extraction prompt's persona block MUST also update the taxonomy doc and audit every `SKILL.md` frontmatter.

If a future skill needs a persona / phase / capability that doesn't exist in the closed vocabulary, the rule is: **change the vocabulary first** (taxonomy doc + extraction prompt + test fixture), then add the skill.

---

## Files touched

### Added

- `docs/SKILL_TAXONOMY.md`
- `docs/PHASE_4J_SKILL_TAXONOMY.md` (this file)
- `.github/skills/oci-sweeper/SKILL.md`
- `.github/skills/oci-sweeper/UPSTREAM.md`
- `.github/skills/oci-sweeper/evals/evals.json`
- `.github/skills/oci-sweeper/references/far_9_5_oci_taxonomy.md`
- `.github/skills/oci-sweeper/references/oci_remediation_playbook.md`
- `.github/skills/oci-sweeper/references/relationship_query_patterns.md`
- `tests/skills/test_skill_taxonomy.py`
- `tests/skills/test_oci_sweeper_skill.py`

### Modified

- `.github/copilot-instructions.md` (8th checklist item)
- `.github/skills/competitive-intel/SKILL.md` (frontmatter backfill, version 0.1.0 → 0.2.0)
- `.github/skills/compliance-auditor/SKILL.md` (frontmatter backfill, version 0.4.0 → 0.5.0)
- `.github/skills/govcon-ontology/SKILL.md` (frontmatter backfill, version 1.2.1 → 1.3.0)
- `.github/skills/huashu-design/SKILL.md` (added metadata block, version 0.1.0)
- `.github/skills/price-to-win/SKILL.md` (frontmatter backfill, version 0.1.0 → 0.2.0)
- `.github/skills/proposal-generator/SKILL.md` (frontmatter backfill, version 0.6.0 → 0.7.0)
- `.github/skills/renderers/SKILL.md` (frontmatter backfill, version 0.2.0 → 0.3.0)
- `.github/skills/rfp-reverse-engineer/SKILL.md` (frontmatter backfill, version 0.1.0 → 0.2.0)
- `.github/skills/skill-creator/SKILL.md` (added Theseus-specific metadata block, version 1.0.0 — upstream is unaffected; see UPSTREAM.md)
- `.github/skills/subcontractor-sow-builder/SKILL.md` (frontmatter backfill, version 0.1.0 → 0.2.0)
- `src/skills/manager.py` (`Skill.to_summary()` surfaces 4 taxonomy fields)
- `src/ui/static/index.html` (Alpine helpers + flat-grid Skills section + 3-axis filter rail + search)
- `src/ui/static/styles/theseus.css` (filter rail + axis labels + pill variants + count badge + search input styles)
- `docs/skills_roadmap.md` (4j row marked done; flat-keys note added)

### Intentionally unchanged

- `prompts/extraction/govcon_lightrag_native.txt` — already at version 6.5 with the OCI sweeps reference and the Phase 4j header. The persona block matches `_ALLOWED_PERSONAS` in the taxonomy test.
- `tailwind.config.js` — no new utility classes introduced; all additions are plain CSS referencing existing `:root` tokens.

---

## skill-creator MANDATE compliance

This commit followed the `skill-creator` workflow per `.github/copilot-instructions.md` § "🔒 MANDATE":

- **For `oci-sweeper`** (new skill): evals authored first, body drafted to close the eval gaps, references split per progressive-disclosure pattern, six-field frontmatter with all Theseus extras under `metadata:`, UPSTREAM.md captures authoring provenance, contract test verifies spec + body invariants.
- **For the 10 existing-skill backfills** (material frontmatter modification): version bumps applied per skill, taxonomy keys placed at the top of `metadata:` with a comment header pointing to the spec, contract test enforces the new closed vocabularies across every skill so silent drift is impossible.
- **Anthropic best-practices applied**: progressive disclosure (taxonomy doc split into sections + oci-sweeper references one level deep), descriptions ≤1024 chars with WHAT + WHEN, gerund/noun-phrase naming preserved, six-field frontmatter only (zero new top-level YAML keys), UTF-8 file writes via Python `Path.write_text(encoding="utf-8")` only.
