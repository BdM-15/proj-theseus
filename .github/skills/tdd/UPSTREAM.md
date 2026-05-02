# UPSTREAM.md — tdd

## Source

- **Repository**: https://github.com/mattpocock/skills
- **Path**: `skills/engineering/tdd/SKILL.md` (plus `tests.md`, `mocking.md`,
  `deep-modules.md`, `interface-design.md`, `refactoring.md` at skill root)
- **License**: Apache-2.0
- **Vendored**: 2026-05-01
- **Upstream ref**: `main`

## Theseus adaptations

1. **Metadata block added** — `developer_only: true`, `category: developer-tool`,
   `personas_primary: none`, `capability: meta`, `shipley_phases: []`,
   `personas_secondary: []`, `runtime: legacy`.

2. **Reference links moved to `references/` subdir** — Upstream keeps reference
   files at the skill root (`tests.md`, `mocking.md`, etc.). Theseus spec
   requires `references/` subdirectory. All 5 internal links in SKILL.md body
   updated from `[X](X.md)` to `[X](references/X.md)`. Reference files placed
   in `references/`.

3. **Evals added** — `evals/evals.json` with 3 Theseus-specific prompts.

## Re-vendoring

```powershell
$base = "https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/tdd"
foreach ($f in @("SKILL.md","tests.md","mocking.md","deep-modules.md","interface-design.md","refactoring.md")) {
    $raw = Invoke-WebRequest -Uri "$base/$f" -UseBasicParsing
    $raw.Content | Out-File -Encoding utf8 ".github/skills/tdd/_upstream_$f"
}
# Diff each file against current version, re-apply adaptations, then delete _upstream_* files
```
