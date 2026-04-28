# Phase 3a — Renderer Toolchain Install Guide

**Status:** ✅ Validated 2026-04-28 on Windows 11 (Node 22.16.0, npm 10.9.2)
**Scope:** Wire the existing `huashu-design` renderer scripts (PPTX / PDF / video) so
other skills (e.g. `proposal-generator`) can invoke them via the tools-mode
runtime's `run_script` tool. **Phase 3a installs JS deps only — Python env is untouched.**

---

## What Phase 3a installs

| Layer     | Where                                        | What                                                                  | Required?                                      |
| --------- | -------------------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------- |
| Node deps | `.github/skills/huashu-design/node_modules/` | `playwright`, `pdf-lib`, `pptxgenjs`, `sharp`                         | ✅ Yes — needed for any render                 |
| Chromium  | Playwright browser cache (user AppData)      | Headless Chromium (~150MB) installed by `playwright install chromium` | ✅ Yes — every renderer drives a page          |
| ffmpeg    | Bundled by Playwright                        | Auto-downloaded as part of `playwright install`                       | ✅ Already present (no system install)         |
| Pandoc    | (deferred to Phase 3d)                       | Needed only for future DOCX renderer                                  | ❌ Not installed                               |
| openpyxl  | Already in Python env (3.1.5)                | Needed for Phase 3e XLSX renderer                                     | ❌ Not installed by Phase 3a (already present) |

### Why Node + Chromium and not Python Playwright?

- `huashu-design`'s renderer scripts are written in Node (`.mjs` / `.js`) and use
  Node-native `pptxgenjs` + `pdf-lib`. There is no Python equivalent in the skill.
- Chromium is the rendering engine — every script (PDF export, PPTX positioning,
  video frame capture) launches a headless page via Playwright.
- `playwright/python` is **not** required: Theseus's tools-mode runtime invokes
  the Node scripts via `run_script`, not in-process.

---

## Install

```powershell
cd .github/skills/huashu-design
npm install        # also runs `playwright install chromium` via postinstall
```

Expected footprint: `node_modules/` ~59 MB on disk; Chromium ~150 MB in
`%LOCALAPPDATA%\ms-playwright\`.

`node_modules/` and `package-lock.json` are gitignored.

---

## Smoke test (validated)

```powershell
# From repo root
mkdir tools/_dep_snapshots/phase3a_smoketest/slides -Force
copy .github/skills/proposal-generator/assets/slide_master.html `
     tools/_dep_snapshots/phase3a_smoketest/slides/

node .github/skills/huashu-design/scripts/export_deck_pdf.mjs `
  --slides tools/_dep_snapshots/phase3a_smoketest/slides `
  --out    tools/_dep_snapshots/phase3a_smoketest/slide_master.pdf `
  --width  1920 --height 1080
```

Expected output:

```
Found 1 slides in ...\slides
  [1/1] slide_master.html
✓ Wrote ...\slide_master.pdf  (23 KB, 1 pages, vector)
```

---

## Available renderer scripts

All under `.github/skills/huashu-design/scripts/` — invoke via `run_script` from a calling skill.

| Script                      | Output                                 | CLI signature                                                    |
| --------------------------- | -------------------------------------- | ---------------------------------------------------------------- |
| `export_deck_pdf.mjs`       | PDF (vector)                           | `--slides <dir> --out <file.pdf> [--width 1920] [--height 1080]` |
| `export_deck_stage_pdf.mjs` | PDF (rasterized stages for animations) | (see file header)                                                |
| `export_deck_pptx.mjs`      | PPTX                                   | (see file header)                                                |
| `html2pptx.js`              | PPTX (library, not CLI)                | `require()`-imported by other scripts                            |
| `render-video.js`           | MP4 / GIF                              | (uses bundled ffmpeg)                                            |
| `convert-formats.sh`        | PNG / SVG                              | bash only                                                        |
| `verify.py`                 | Playwright smoke check                 | needs Python playwright (deferred)                               |

---

## Rollback

If Phase 3a needs to be unwound:

```powershell
Remove-Item -Recurse -Force .github/skills/huashu-design/node_modules
Remove-Item .github/skills/huashu-design/package-lock.json
# Optional: delete Chromium cache (~150MB) if no other Playwright project uses it:
# Remove-Item -Recurse -Force "$env:LOCALAPPDATA\ms-playwright"
```

Python env restoration (precautionary — Phase 3a does NOT modify Python deps):

```powershell
# Snapshots taken 2026-04-28 are in tools/_dep_snapshots/ (gitignored):
#   pyproject_20260428_051259.toml
#   uv_freeze_20260428_051306.txt
#   uv_lock_20260428_051306.lock
# Restore:
copy tools/_dep_snapshots/pyproject_20260428_051259.toml pyproject.toml
copy tools/_dep_snapshots/uv_lock_20260428_051306.lock   uv.lock
uv sync
```

---

## What's deferred

- **Phase 3b:** `invoke_skill` runtime tool — proposal-generator can hand off to huashu-design.
- **Phase 3c:** End-to-end test (proposal draft → slide deck → PDF/PPTX).
- **Phase 3d:** Pandoc install + DOCX renderer.
- **Phase 3e:** openpyxl XLSX renderer (compliance matrix export).

See [docs/skills_roadmap.md](skills_roadmap.md).
