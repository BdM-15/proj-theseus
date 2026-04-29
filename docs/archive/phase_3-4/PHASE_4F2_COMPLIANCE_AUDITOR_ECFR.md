# Phase 4f.2 — `compliance-auditor` consumes eCFR MCP

**Branch:** `129-phase-4f2-compliance-auditor-ecfr` (off `120-skills-spec-compliance`)
**Status:** ✅ Done
**Depends on:** Phase 4a (MCP client), 4b (`metadata.mcps` allowlist), 4f.1 (eCFR MCP vendored)

## What changed

Promoted `compliance-auditor` from a KG-only audit skill to a KG+eCFR audit skill that catches two failure modes the workspace alone cannot:

1. **Fabricated or typo'd FAR/DFARS clause numbers** — extraction sometimes
   produces clause entities like `52.212-44` (no such section) or `52.212.4`
   (wrong delimiter). Without a ground-truth check these slip into the
   compliance matrix and a Capture Manager only finds out post-submission.
2. **Stale clause text** — a clause was amended in eCFR after the
   solicitation issued. The proposal cites the old text. Auditor now flags
   the drift with both dates so the team can decide whether to re-cite.

## Files touched

- `.github/skills/compliance-auditor/SKILL.md` — bumped to v0.4.0; added
  `metadata.mcps: [ecfr]`; added **C9** (Clause Existence Validation,
  critical) and **C10** (Clause Currency Drift, medium) to the workflow;
  trimmed description to fit the 1024-char spec ceiling; replaced one
  YAML-hostile colon (`Format-agnostic:` → `Format-agnostic.`) so
  `yaml.safe_load` accepts the frontmatter for the contract test.
- `.github/skills/compliance-auditor/references/ecfr_tools.md` — NEW.
  Curated 4-tool whitelist (`lookup_far_clause`, `get_version_history`,
  `compare_versions`, `find_far_definition`), clause-number
  normalization regex + examples, deferral rule when the `ecfr` MCP is
  not exposed to the run. Progressive disclosure — kept out of the
  SKILL.md body per Anthropic best-practice.
- `.github/skills/compliance-auditor/evals/evals.json` — added evals
  4 (C9) and 5 (C10) with expectations that explicitly require
  `mcp__ecfr__*` tool calls. Total now 5 evals.
- `tests/skills/test_compliance_auditor_skill.py` — NEW. 4 offline
  contract tests (frontmatter spec compliance, MCP allowlist
  declaration, body references real ecfr tools only, evals exercise
  ecfr) + 1 live drift test (THESEUS_LIVE_MCP=1) mirroring the
  `test_competitive_intel_skill.py` pattern.
- `docs/skills_roadmap.md` — flipped 4f.2 row from "future" to ✅ done.

## eCFR-grounded checks (C9 / C10)

### C9 — Clause Existence Validation _(severity: critical)_

For each `clause` entity whose name normalizes to `^\d{1,3}\.\d{3,4}(-\d+)?$`:

```
mcp__ecfr__lookup_far_clause({ "section_id": "<normalized>" })
```

If the upstream returns 404 / empty / "not found", emit a critical
finding citing the section_id, the workspace entity_id, and at least
one chunk_id of evidence. Skipped (non-section-shaped) entities
collapse into one info finding so the noise floor stays useful.

### C10 — Clause Currency Drift _(severity: medium)_

For each clause that resolved in C9:

```
mcp__ecfr__get_version_history({ "title": 48, "section_id": "<normalized>" })
```

If the most-recent amendment date > workspace solicitation issuance
date, emit a medium finding noting both dates. Optional drill-in via
`mcp__ecfr__compare_versions`. If no issuance date can be extracted
from the workspace, emit one info finding deferring C10 (no
fabricated dates).

## Test results

```
.\.venv\Scripts\python.exe -m pytest tests/skills/test_compliance_auditor_skill.py -v
```

```
test_compliance_auditor_frontmatter_is_spec_compliant         PASSED
test_compliance_auditor_declares_ecfr_mcp                     PASSED
test_compliance_auditor_body_references_real_ecfr_tools_only  PASSED
test_compliance_auditor_evals_exercise_ecfr                   PASSED
test_skill_body_tool_refs_match_live_ecfr_mcp                 PASSED  (live, ≥6 tools advertised, 4 referenced all match)

5 passed in 6.42s
```

## skill-creator workflow attestation

Per the MANDATE in `.github/copilot-instructions.md`:

1. ✅ Snapshot first — `tools/_skill_snapshots/compliance-auditor-pre-4f2/` (gitignored)
2. ✅ Evals BEFORE prose — added evals 4 & 5 with explicit `mcp__ecfr__*` expectations before drafting C9/C10
3. ✅ Baseline implicit — pre-4f2 snapshot has zero eCFR tool calls; evals 4 & 5 cannot pass without the new wiring
4. ✅ Drafted minimally — kept SKILL.md body at 216 lines (well under 500), pushed tool reference table + normalization rules to `references/ecfr_tools.md`
5. ✅ Matched degrees of freedom — judgment-heavy guidance (when to defer, how to phrase findings) stays as prose; the brittle clause-number normalization is locked to a regex with a documented escape hatch
6. ✅ Observed run — live drift test spawned the upstream eCFR server, listed its 13 advertised tools, and confirmed all 4 referenced names exist
7. ✅ Progressive disclosure — `references/ecfr_tools.md` loaded on demand, not eagerly read into body
8. ✅ Spec compliance — frontmatter has only the 6 allowed fields; `mcps` lives under `metadata:`; description ≤ 1024 chars; body < 500 lines

## Out of scope (deferred)

- C11 (FAR 2.101 definition enrichment) — `find_far_definition` is in the
  whitelist but not yet wired to a check. Add when a real workspace
  surfaces ambiguous definitional conflicts.
- Live eCFR caching — every C9/C10 call hits the eCFR API. For large
  RFPs (>50 unique clauses) we may want a per-run cache layer in
  `src/skills/mcp_client.py`. Track in Phase 4 cleanup.
- Automatic agency FAR supplement detection (DFARS, AFFARS, NFS, etc.)
  beyond DFARS — eCFR has them all but C9 currently only normalizes FAR
  + DFARS section shapes. Extend when needed.
