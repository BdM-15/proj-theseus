# Upstream Provenance

| Field        | Value                                                         |
| ------------ | ------------------------------------------------------------- |
| Source repo  | https://github.com/mattpocock/skills                          |
| Source path  | `skills/productivity/caveman/SKILL.md`                        |
| License      | Apache-2.0                                                    |
| Vendored on  | 2026-05-01                                                    |
| Vendored by  | GitHub Copilot (branch `154-phase1.2-json-prompt-conversion`) |
| Upstream rev | `62f43a18177be6ec82da242e59ffbc490a4c22ea`                    |

## Adaptations

1. **Metadata block added** — `license: Apache-2.0` and a `metadata:` block with Theseus Phase 4j taxonomy keys (`personas_primary`, `capability`, `developer_only`, etc.) added to frontmatter. No upstream spec field is removed or changed.
2. **`evals/evals.json` added** — four Theseus-specific eval prompts. Upstream has no evals directory.

## Re-vendor instructions

To pull a fresh upstream copy:

```powershell
$raw = Invoke-WebRequest -Uri "https://raw.githubusercontent.com/mattpocock/skills/main/skills/productivity/caveman/SKILL.md" | Select-Object -ExpandProperty Content
# Review diff against .github/skills/caveman/SKILL.md — re-apply the two adaptations above.
```

Only the body and upstream description change on re-vendor. The `metadata:` block is Theseus-local and must be preserved.
