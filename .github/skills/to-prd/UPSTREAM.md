# UPSTREAM.md — to-prd

## Source

- **Repository**: https://github.com/mattpocock/skills
- **Path**: `skills/engineering/to-prd/SKILL.md`
- **License**: Apache-2.0
- **Vendored**: 2026-05-01
- **Upstream ref**: `main` (latest: "Swapped 'backlog' for 'issue tracker'")

## Theseus adaptations

1. **Metadata block added** — `developer_only: true`, `category: developer-tool`,
   `personas_primary: none`, `capability: meta`, `shipley_phases: []`,
   `personas_secondary: []`, `runtime: legacy`.

2. **Issue tracker hardcoded** — Replaced the upstream line
   "The issue tracker and triage label vocabulary should have been provided to
   you — run `/setup-matt-pocock-skills` if not." with the hardcoded reference:
   Issue tracker: `https://github.com/BdM-15/proj-theseus/issues`. Triage
   label: `needs-triage`.

3. **Evals added** — `evals/evals.json` with 3 Theseus-specific prompts.

## Re-vendoring

```powershell
$raw = Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mattpocock/skills/main/skills/engineering/to-prd/SKILL.md" -UseBasicParsing
$raw.Content | Out-File -Encoding utf8 ".github/skills/to-prd/_upstream_SKILL.md"
# Diff against current SKILL.md, re-apply adaptations above, then delete _upstream_SKILL.md
```
