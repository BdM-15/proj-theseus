# Vendored from anthropics/skills

This skill is a vendored copy of `skills/skill-creator/` from
<https://github.com/anthropics/skills> (Apache License 2.0).

| Field            | Value                                         |
| ---------------- | --------------------------------------------- |
| Upstream repo    | https://github.com/anthropics/skills          |
| Subdirectory     | `skills/skill-creator/`                       |
| Vendored on      | 2026-04-27                                    |
| License          | Apache-2.0 (see [`LICENSE.txt`](LICENSE.txt)) |
| Vendoring branch | `120-skills-spec-compliance`                  |

## Why vendored

`skill-creator` is the canonical reference implementation of the open
[Agent Skills specification](https://agentskills.io/specification). Theseus
uses it as:

1. The **authoring tool** for new and existing skills (its workflow drives the
   creation and iteration of every other skill in `.github/skills/`).
2. The **conformance reference** — when our `SkillManager` runtime or our
   skill bodies disagree with `skill-creator`, the spec wins.
3. The **eval framework** — `eval-viewer/generate_review.py`,
   `scripts/aggregate_benchmark.py`, and `scripts/run_loop.py` provide the
   benchmark + description-optimization loops we adapt for Theseus.

## Adaptation notes

`skill-creator` was written for **Claude Code**, which spawns parallel
subagents for test runs. Theseus is a **single-process Python runtime**.
Two adaptation paths are documented inside the upstream `SKILL.md`:

- **"Claude.ai-specific instructions"** — sequential test runs, no baseline
  subagents, inline review.
- **"Cowork-Specific instructions"** — subagents available but no browser,
  use `--static` for the eval viewer.

Theseus follows the **Claude.ai-specific** path until/unless we add subagent
plumbing in a later phase. See `docs/SKILL_SPEC_COMPLIANCE.md` §
"skill-creator runtime adaptation" for the integration plan.

## Local modifications

**None.** Files are vendored verbatim. If we need to patch upstream behavior,
we'll do it in a separate commit with a `LOCAL_PATCHES.md` log so future
upstream merges remain mechanical.

## Updating

```powershell
# From repo root
git clone --depth 1 --filter=blob:none --sparse `
    https://github.com/anthropics/skills.git $env:TEMP/anthropics-skills
cd $env:TEMP/anthropics-skills
git sparse-checkout set skills/skill-creator LICENSE
Copy-Item -Recurse -Force `
    "$env:TEMP/anthropics-skills/skills/skill-creator/*" `
    "C:\Users\benma\govcon-capture-vibe\.github\skills\skill-creator\"
Copy-Item -Force `
    "$env:TEMP/anthropics-skills/LICENSE" `
    "C:\Users\benma\govcon-capture-vibe\.github\skills\skill-creator\LICENSE.txt"
```

Then update the "Vendored on" date in this file and re-validate via
`SkillManager.discover()`.
