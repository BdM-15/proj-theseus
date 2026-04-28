# Vendored from alchaincyf/huashu-design

This skill is a verbatim copy of <https://github.com/alchaincyf/huashu-design>
("Huashu Design" by Huasheng / 花叔), used here under its **Personal Use
License**. See [`LICENSE`](LICENSE) for the full text.

| Field            | Value                                           |
| ---------------- | ----------------------------------------------- |
| Upstream repo    | https://github.com/alchaincyf/huashu-design     |
| Vendored at SHA  | `23f60d9b4304f20851469987c6e2c92242b94a45`      |
| Vendored on      | 2026-04-27                                      |
| License          | Personal Use License (see [`LICENSE`](LICENSE)) |
| Vendoring branch | `120-skills-spec-compliance`                    |

## License posture

Upstream's license permits **personal, non-commercial use** without
authorization, including:

- Learning and research
- Personal creation (own articles, videos, side projects, social posts)
- Sharing demos / tutorials based on this skill
- Derivative skills in personal repos (with attribution `Derived from
alchaincyf/huashu-design`)

It **forbids** integration into company / team / commercial products,
paid client deliverables, and resale without prior written authorization
from Huasheng.

**Theseus is a personal capture/proposal tool used by a single owner for
personal federal-contracting work.** Use here is in scope of the Personal
Use clause. If Theseus is ever offered as a product, paid service, or
client deliverable, this skill MUST be removed or relicensed first.

## Why vendored

`huashu-design` is the engine for high-fidelity design output:

1. **Stage + Sprite animation engine** (`assets/animations.jsx`,
   `references/animations.md`) — HTML → MP4 / GIF / 60fps via Playwright.
2. **Real `html2pptx.js`** (`scripts/html2pptx.js`) — DOM computed-styles
   translated into editable PowerPoint text frames, not screenshots.
3. **24 prebuilt showcases** (`assets/showcases/`) covering 8 scenes ×
   3 design philosophies (build / pentagram / takram).
4. **Device frames** (`ios_frame.jsx`, `android_frame.jsx`,
   `macos_window.jsx`, `browser_window.jsx`).
5. **20-philosophy design vocabulary** (`references/design-styles.md`) +
   5-dimension expert critique (`references/critique-guide.md`).
6. **6 BGM tracks + ~40 SFX clips** (`assets/bgm-*.mp3`, `assets/sfx/`).

Theseus uses these primitives directly via the upstream skill. Govcon
content (compliance matrices, theme cards, one-pagers, etc.) is drafted
by the [`proposal-generator/`](../proposal-generator/) skill — which
ships the govcon HTML render templates and design tokens — and the
user then invokes `huashu-design` to convert that content into PPTX /
PDF / MP4. The two skills are independent; there is no overlay layer.

## Adaptation notes

- **SKILL.md is in Chinese.** The agent is bilingual per upstream README;
  English prompts work fine.
- **Renderer toolchain prerequisites** (Node + Playwright + ffmpeg) are NOT
  installed by default. Scripts will fail loudly if missing — the agent
  should fall back to HTML output and report the missing dependency.
- **Runtime mode**: this skill registers as `legacy` (single-shot prompt
  composition). The govcon overlay registers as `tools` (multi-turn KG
  injection). They are independent skills; either can be invoked directly.

## Local modifications

**None.** Files are vendored verbatim from upstream HEAD. If a local patch
becomes necessary, it MUST be recorded in a sibling `LOCAL_PATCHES.md` so
future re-vendoring stays mechanical.

## Updating

```powershell
# From repo root
$tmp = Join-Path $env:TEMP "huashu-design-upstream"
if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
git clone --depth 1 https://github.com/alchaincyf/huashu-design.git $tmp
$sha = (cd $tmp; git rev-parse HEAD)
robocopy $tmp .github/skills/huashu-design /E /XD .git /NFL /NDL /NJH /NJS
Write-Host "Vendored at SHA: $sha"
```

Then update the "Vendored at SHA" + "Vendored on" rows in this file,
re-run `Invoke-RestMethod -Uri http://localhost:9621/api/ui/skills/refresh -Method Post`,
and verify the skill still appears in `/api/ui/skills`.
