# Archived: Skills E2E Hardening Epic (142)

This folder archives the working roadmap for the **`142-skills-e2e-hardening`** epic, which closed and merged to `main` as **v1.3.0**.

The epic delivered:

- **143** — `renderers` skill scope tightened to DOCX + XLSX; PPTX/PDF/MP4/GIF delegated to `huashu-design`.
- **144** — `huashu-design` frontmatter description translated to English (body remains Chinese, per skill author intent).
- **145** — `tests/skills/e2e/` end-to-end harness scaffold + grounding-signal detector calibration.
- **146** — `skill-creator` re-verification pass; closed 3 artifact-emit xfails; trimmed 2 SKILL descriptions to spec ≤1024-char limit.
- **147 (.1–.12)** — Skill grounding-ratio audit tool (`tools/skill_grounding_audit.py`) + per-skill calibration: every in-house skill now passes the citation-discipline floor; `--enforce` mode wired for CI.
- **148** — Studio download/edit-loop manual UI walkthrough; caught + fixed `.md` mime drift (Windows registry mislabel bypassed `_STUDIO_EXTRA_MIME`); consolidated mime resolution behind `resolve_artifact_mime()` helper; locked by 15 contract tests; confirmed Studio is read-only by design (audit-chain integrity).

## Authoritative current sources

The roadmap below is **historical reference only**. For current state consult:

- [`docs/SKILLS.md`](../../SKILLS.md) — end-to-end usage guide
- [`docs/SKILL_TAXONOMY.md`](../../SKILL_TAXONOMY.md) — three-axis taxonomy
- [`docs/SKILL_SPEC_COMPLIANCE.md`](../../SKILL_SPEC_COMPLIANCE.md) — open-spec audit
- [`.github/skills/`](../../../.github/skills/) — the 12 production skills themselves
- `tests/skills/e2e/` — the harness this epic built
- `tools/skill_grounding_audit.py` — the audit tool this epic built

Follow-ups filed during this epic remain open as standalone GitHub issues:

- **#122** — huashu-design E2E coverage for `.html` / `.pptx` / `.pdf` / `.gif` / `.mp4` (currently unit-tested only).
- **#123** — User-uploaded templates as skill inputs (separate UI lane from Studio; preserves audit-chain invariant).
