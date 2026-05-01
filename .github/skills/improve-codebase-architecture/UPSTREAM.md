# Vendored from mattpocock/skills

This skill is a vendored copy of `skills/engineering/improve-codebase-architecture/` from
<https://github.com/mattpocock/skills> (Apache License 2.0).

| Field            | Value                                               |
| ---------------- | --------------------------------------------------- |
| Upstream repo    | https://github.com/mattpocock/skills                |
| Subdirectory     | `skills/engineering/improve-codebase-architecture/` |
| Vendored on      | 2026-05-01                                          |
| License          | Apache-2.0                                          |
| Vendoring branch | `154-phase1.2-json-prompt-conversion`               |

## Why vendored

Developer-facing skill for improving the Theseus codebase architecture. Applies
the "deep modules" discipline (Ousterhout) and domain-language rigor to surface
refactoring candidates, run grilling conversations, and record architectural decisions
as ADRs.

## Adaptation notes

### File layout

Upstream places `LANGUAGE.md`, `DEEPENING.md`, and `INTERFACE-DESIGN.md` at the
skill root. Per Theseus spec, these are reference files and belong under `references/`.
All intra-skill paths updated accordingly.

### Exploration tooling

Upstream uses `Agent tool with subagent_type=Explore` (Claude Code specific).
Adapted to use the graphify dependency map (`graphify-out/GRAPH_REPORT.md`) as the
structural starting point, then `read_file`, `grep_search`, and `semantic_search`
for organic exploration. Graphify is already a dev dependency (`graphifyy`) and runs
via `/graphify .` in Copilot Chat.

### grill-with-docs references

Upstream references `../grill-with-docs/CONTEXT-FORMAT.md` and
`../grill-with-docs/ADR-FORMAT.md`. These are vendored as local copies in
`references/CONTEXT-FORMAT.md` and `references/ADR-FORMAT.md` so this skill is
self-contained. Source: `skills/engineering/grill-with-docs/` in the same upstream repo.

## Updating

```powershell
# From repo root — fetch the upstream skill directory
$tmp = "$env:TEMP\mattpocock-skills"
git clone --depth 1 --filter=blob:none --sparse https://github.com/mattpocock/skills.git $tmp
Push-Location $tmp
git sparse-checkout set skills/engineering/improve-codebase-architecture skills/engineering/grill-with-docs
Pop-Location

$dest = "C:\Users\benma\govcon-capture-vibe\.github\skills\improve-codebase-architecture"
# Update reference files (check for upstream changes)
Copy-Item -Force "$tmp\skills\engineering\improve-codebase-architecture\LANGUAGE.md"       "$dest\references\LANGUAGE.md"
Copy-Item -Force "$tmp\skills\engineering\improve-codebase-architecture\DEEPENING.md"      "$dest\references\DEEPENING.md"
# Re-apply path adaptations in INTERFACE-DESIGN.md (see Adaptation notes above)
Copy-Item -Force "$tmp\skills\engineering\grill-with-docs\CONTEXT-FORMAT.md"               "$dest\references\CONTEXT-FORMAT.md"
Copy-Item -Force "$tmp\skills\engineering\grill-with-docs\ADR-FORMAT.md"                   "$dest\references\ADR-FORMAT.md"
# Review SKILL.md diff and port any upstream improvements manually
```
