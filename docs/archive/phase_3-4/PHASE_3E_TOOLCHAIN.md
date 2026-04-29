# Phase 3e Toolchain — openpyxl XLSX Renderer

**Status:** ✅ Active (added 2026-04-28)
**Owner skill:** [.github/skills/renderers](../.github/skills/renderers/SKILL.md)
**Script:** [.github/skills/renderers/scripts/render_xlsx.py](../.github/skills/renderers/scripts/render_xlsx.py)

## Why openpyxl (not Pandoc, not pandas-to-excel)

| Option                | Verdict                                                                                                                                                                                                                                                     |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Pandoc → xlsx**     | ❌ Pandoc has no native xlsx writer. The `pandoc -t docx` route via Word tables loses styling and breaks the Markdown→office contract used for DOCX.                                                                                                        |
| **pandas → xlsx**     | ❌ Drags ~50 MB of dependencies (numpy + pandas + xlsxwriter) for what is essentially "write rows to cells with conditional formatting". Overkill for a renderer.                                                                                           |
| **openpyxl** (chosen) | ✅ Pure-Python, ~5 MB, already in the Theseus venv, supports the full XLSX feature set we need: bold/colored headers, frozen panes, autofilter, conditional `PatternFill` per row, multiple sheets in one workbook, column-width tuning, workbook metadata. |

For comparison, DOCX uses Pandoc because federal proposals demand `--reference-doc` template inheritance — a feature only Pandoc provides cleanly. XLSX has no analogous "reference workbook" requirement: agencies don't standardize Excel themes the way they standardize Word templates, so the renderer just produces a clean, federally-readable workbook from whatever JSON the consumer skill hands it.

## Install

openpyxl is already pinned in `pyproject.toml` (verified 3.1.5 in `.venv`). No new system tooling required.

```powershell
# If openpyxl is somehow missing:
.venv\Scripts\pip install openpyxl
```

## Verify

```powershell
.venv\Scripts\python.exe -c "import openpyxl; print(openpyxl.__version__)"
# expected: 3.1.5 or newer
```

## Renderer Contract

| Flag       | Required | Purpose                                                                                        |
| ---------- | -------- | ---------------------------------------------------------------------------------------------- |
| `--input`  | yes      | JSON source path, or `-` to read from stdin                                                    |
| `--output` | yes      | Output `.xlsx` path (parent dirs auto-created)                                                 |
| `--sheet`  | no       | Sheet name when input is a top-level array (default `Sheet1`); ignored for object-shaped input |
| `--title`  | no       | Workbook `title` metadata property                                                             |

### Input JSON shapes

The script accepts two shapes:

**1. Top-level array of objects → one sheet:**

```json
[
  { "col_a": 1, "col_b": "x" },
  { "col_a": 2, "col_b": "y" }
]
```

**2. Top-level object with array-valued keys → one sheet per key:**

```json
{
  "compliance_matrix": [{"instruction_id": "L-001", "status": "OK", ...}],
  "themes": [{"theme": "...", "discriminator": "...", ...}],
  "fab_chains": [{"feature": "...", "advantage": "...", ...}],
  "executive_summary_md": "...",   // ignored — not an array of objects
  "warnings": ["..."]              // ignored — array of strings, not objects
}
```

This matches the `proposal_draft.json` envelope produced by `proposal-generator` exactly: a single `run_script` call produces one workbook with `compliance_matrix`, `themes`, `fab_chains`, and `volume_outlines` sheets.

### Automatic styling

- **Header row:** bold white text on dark blue (`#305496`) fill, frozen at A2.
- **Autofilter:** applied across the data range so the contracting officer can sort/filter immediately.
- **Status conditional fill:** if a column named `status` (case-insensitive) exists, each row is colored:
  - `OK` → green (`#C6EFCE`)
  - `PARTIAL` → yellow (`#FFEB9C`)
  - `GAP` → red (`#FFC7CE`)
- **Column widths:** auto-sized to the longest first-line value, capped at 60 chars.
- **Wrap alignment:** all cells wrap text and align top so multi-line values render cleanly.
- **List values** (e.g., `requirement_ids`, `source_chunks`) joined with `, `.
- **Dict values** JSON-encoded for cell rendering.

### Exit codes

| Code  | Meaning                                                             |
| ----- | ------------------------------------------------------------------- |
| 0     | Success — absolute output path printed to stdout                    |
| 2     | Bad arg, input not found, input not valid JSON, no array data found |
| 127   | openpyxl not installed — install hint printed to stderr             |
| other | OSError on write (disk full, permission denied) — message on stderr |

## Smoke Test

```powershell
# Direct invocation
$tmp = New-TemporaryFile | Select-Object -ExpandProperty FullName
$json = '{"compliance_matrix":[{"id":"L-001","status":"OK"},{"id":"L-002","status":"GAP"}]}'
$json | Out-File -Encoding utf8 "$tmp.json"
.venv\Scripts\python.exe .github\skills\renderers\scripts\render_xlsx.py `
  --input "$tmp.json" `
  --output "$tmp.xlsx" `
  --title "Smoke Test"
# expected: prints absolute path; rc=0; valid 6KB+ workbook
```

## Where this lives

The XLSX renderer ships in the same utility skill as DOCX: `.github/skills/renderers/scripts/`. Consumer skills opt in once via `metadata.script_paths: [../renderers/scripts]` and inherit both renderers (and any future ones added to that folder) automatically. See [docs/PHASE_3D_TOOLCHAIN.md](PHASE_3D_TOOLCHAIN.md) for the architectural rationale.

## See Also

- [.github/skills/renderers/SKILL.md](../.github/skills/renderers/SKILL.md) — utility skill manifest
- [.github/skills/renderers/scripts/render_xlsx.py](../.github/skills/renderers/scripts/render_xlsx.py) — script source
- [docs/PHASE_3D_TOOLCHAIN.md](PHASE_3D_TOOLCHAIN.md) — DOCX renderer (sibling)
- [docs/PHASE_3A_TOOLCHAIN.md](PHASE_3A_TOOLCHAIN.md) — Node/Playwright/Chromium for huashu-design renderers
