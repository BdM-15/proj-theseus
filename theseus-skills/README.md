# theseus-skills/

This directory is the **Theseus-side organizational view** of the agent skills authored under [`.github/skills/`](../.github/skills/).

We do **not** duplicate skill content here — both VS Code/Copilot and the Theseus runtime read directly from `.github/skills/` (the official `agentskills.io` location). This folder exists only to:

1. Provide a discoverable entry point for repo browsers who don't know the `.github/` convention
2. Host any **Theseus-runtime-only** tooling (eval harnesses, mock context fixtures, integration tests) that should not pollute the agent-discoverable directory
3. Document Theseus-specific invocation contracts that go beyond the cross-platform SKILL.md

## Index

| Skill                | Source of truth                        | Theseus runtime adapter        |
| -------------------- | -------------------------------------- | ------------------------------ |
| huashu-design-govcon | `.github/skills/huashu-design-govcon/` | `src/skills/manager.py` (auto) |
| govcon-ontology      | `.github/skills/govcon-ontology/`      | `src/skills/manager.py` (auto) |
| proposal-generator   | `.github/skills/proposal-generator/`   | `src/skills/manager.py` (auto) |
| compliance-auditor   | `.github/skills/compliance-auditor/`   | `src/skills/manager.py` (auto) |
| competitive-intel    | `.github/skills/competitive-intel/`    | `src/skills/manager.py` (auto) |

## Adding a Theseus-only Test Fixture

Place mock workspace context payloads under `theseus-skills/fixtures/<skill-name>/` for use by `tests/test_skills_*.py`. Do not place them under `.github/skills/` — Copilot would try to load them as references.

## Adding a Theseus-only Eval

Place eval scenarios under `theseus-skills/evals/<skill-name>/scenario-*.md`. The `SkillManager.run_evals()` helper walks this tree.
