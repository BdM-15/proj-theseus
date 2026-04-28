# Phase 3d — DOCX Renderer Toolchain (Pandoc)

**Status:** ✅ Validated on Windows 11 (Pandoc 3.9.0.2)
**Scope:** Install the Pandoc CLI so the `proposal-generator` skill's
`scripts/render_docx.py` renderer can convert Markdown proposal volumes into
Microsoft Word (`.docx`) artifacts via the tools-mode runtime's `run_script`
tool. **Phase 3d adds one binary — no Python or Node deps change.**

---

## Why Pandoc (and not python-docx)

Federal proposals are submitted as DOCX, almost always on an agency- or
company-mandated Word template (e.g. NASA Times 11pt, AF Arial 11pt, prime
contractor branded styles). Pandoc's `--reference-doc <reference.docx>` flag
maps every Markdown heading and block style onto the matching Word style in
that template — the only practical way to honor varied corporate templates
without writing per-template rendering code. The `proposal-generator` LLM
already authors structured Markdown; Pandoc is the natural last-mile
converter.

`python-docx` was evaluated and rejected: it requires programmatically
recreating ~30–50 styles per template, fights against the model's natural
Markdown output, and ships no template inheritance.

---

## What Phase 3d installs

| Layer  | Where                                             | What              | Required?                             |
| ------ | ------------------------------------------------- | ----------------- | ------------------------------------- |
| Pandoc | System PATH (`%PROGRAMFILES%\Pandoc\` on Windows) | `pandoc.exe` v3.x | ✅ Yes — required for any DOCX render |

No Python or Node packages are added. The `render_docx.py` script is pure
stdlib Python (`subprocess`, `argparse`, `shutil`).

---

## Install

### Windows (winget — recommended)

```powershell
winget install --id JohnMacFarlane.Pandoc --accept-source-agreements --accept-package-agreements
```

Footprint: ~140 MB on disk; ~40 MB downloaded MSI.

### macOS (Homebrew)

```bash
brew install pandoc
```

### Linux (apt / dnf)

```bash
sudo apt install pandoc      # Debian / Ubuntu
sudo dnf install pandoc      # Fedora / RHEL
```

---

## Verify

```powershell
pandoc --version | Select-Object -First 1
# → pandoc 3.9.0.2  (or later)
```

If `pandoc` is not on PATH after install, open a fresh terminal so the new
PATH entry is loaded, or restart VS Code.

---

## Smoke test (end-to-end via runtime)

A minimal smoke test that exercises the full path
(skill script → `tool_run_script` → Pandoc → DOCX artifact):

```powershell
$tmp = New-TemporaryFile
$md  = $tmp.FullName + ".md"
$out = $tmp.FullName + ".docx"

@"
# Volume I — Technical Approach

Our solution leverages **Shipley methodology**.

| Requirement | Approach |
| --- | --- |
| AC-2 | RBAC |
"@ | Set-Content -Encoding UTF8 $md

.venv\Scripts\python.exe `
  .github\skills\renderers\scripts\render_docx.py `
  --input $md --output $out --metadata "title=Volume I"

if (Test-Path $out) { Write-Host "OK: $((Get-Item $out).Length) bytes" }
Remove-Item $md, $out, $tmp -ErrorAction SilentlyContinue
```

Expected: `OK: ~10000 bytes`. The DOCX opens cleanly in Word / LibreOffice.

---

## Renderer contract

| Flag          | Required | Purpose                                                |
| ------------- | -------- | ------------------------------------------------------ |
| `--input`     | ✅       | Path to source Markdown file (or `-` for stdin)        |
| `--output`    | ✅       | Path to write the `.docx` artifact                     |
| `--reference` | optional | Word template (`.docx`) whose styles will be inherited |
| `--toc`       | optional | Insert a table of contents at the top                  |
| `--metadata`  | optional | Repeatable `KEY=VALUE` pair (e.g. `title=Volume I`)    |

**Exit codes:**

- `0` — success; absolute output path printed to stdout
- `2` — bad argument or missing input file
- `127` — `pandoc` not found on PATH (stderr includes install hint)
- other — Pandoc itself failed (stderr includes Pandoc diagnostics)

---

## Where this lives

- **Renderer script:** `.github/skills/renderers/scripts/render_docx.py`
- **Renderer skill:** [.github/skills/renderers/SKILL.md](../.github/skills/renderers/SKILL.md) — universal artifact-renderer utility skill
- **Consumer skill workflow step:** `proposal-generator/SKILL.md` — Step 12b ("Render a Word (.docx) volume")
- **Reference templates** (optional, user-supplied): drop under the consumer skill's `assets/` or per-run `artifacts/`

The `renderers` skill is a pure utility — it owns no domain logic, no LLM
persona, no KG queries. Any consumer skill (proposal-generator,
competitive-intel, compliance-auditor, future writer / executive-briefer)
opts in by adding `../renderers/scripts` to its `metadata.script_paths`
frontmatter. This keeps content authoring (the consumer's job) cleanly
separated from format conversion (the renderer's job) and avoids every
writer skill duplicating renderer code.
