---
name: renderers
description: Office-document renderers for Theseus skills — turns Markdown into Word (DOCX) and JSON envelopes into styled Excel (XLSX) deliverables via opt-in `metadata.script_paths`. USE THIS SKILL'S SCRIPTS when another skill (proposal-generator, competitive-intel, compliance-auditor, oci-sweeper, price-to-win, ot-prototype-strategist, subcontractor-sow-builder, rfp-reverse-engineer, executive-briefer, etc.) needs a downloadable .docx or .xlsx file. Pure utility — owns no domain logic, no LLM persona, no KG queries. Each renderer is a small CLI script invoked via the runtime's `run_script` tool. Ships `render_docx.py` (Markdown → Word via Pandoc) and `render_xlsx.py` (JSON envelope → styled Excel workbook via openpyxl). DO NOT USE FOR drafting content (use the relevant domain skill) or for visual / presentation / motion formats — PDF, PPTX, MP4, and GIF are out of scope here and MUST be routed to `huashu-design` directly (the consumer skill declares `../huashu-design/scripts` in its own `metadata.script_paths`).
license: MIT
metadata:
  # Phase 4j taxonomy — see docs/SKILL_TAXONOMY.md
  personas_primary: none
  personas_secondary: []
  shipley_phases: []
  capability: render
  runtime: tools
  category: utility
  version: 0.4.0
  status: active
  # Renderers is invoked indirectly: consumer skills declare
  # `script_paths: [../renderers/scripts]` in their own SKILL.md and call
  # the scripts via run_script. This skill itself rarely runs as a top-level
  # agent loop — it's a script library, not a persona.
---

# Renderers — Universal Artifact Output Library

A **utility skill** that owns the file-format renderers Theseus skills hand off to when a user wants a downloadable deliverable. Skills focused on _content_ (proposal-generator, competitive-intel, compliance-auditor, executive-briefer) should not own renderer code; they should hand structured Markdown / JSON to a script under `renderers/scripts/` via the runtime's `run_script` tool.

## When to Use

Indirectly, via opt-in from another skill:

```yaml
# In the consumer skill's SKILL.md frontmatter:
metadata:
  script_paths:
    - ../renderers/scripts # for DOCX / XLSX / future formats
    - ../huashu-design/scripts # for HTML → PPTX / PDF / Video / GIF
```

The runtime then resolves any `run_script` call whose `path` resolves under either directory.

Directly (rare — for testing or one-off conversions): activate the skill yourself.

## When NOT to Use

- ❌ Authoring content — use the relevant domain skill (`proposal-generator`, `competitive-intel`, `compliance-auditor`, `executive-briefer`).
- ❌ Designing slides / animations / visual mockups — use `huashu-design`.
- ❌ Querying the knowledge graph or drafting analysis — that's the consumer skill's job; renderers receives structured text/data and emits a file.

## Available Renderers (this skill)

| Format | Script                                           | Purpose                                                                             | Toolchain                                                                              |
| ------ | ------------------------------------------------ | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| DOCX   | [scripts/render_docx.py](scripts/render_docx.py) | Markdown → Word document with optional `--reference` template inheritance           | Pandoc on PATH (see `docs/archive/phase_3-4/PHASE_3D_TOOLCHAIN.md`)                    |
| XLSX   | [scripts/render_xlsx.py](scripts/render_xlsx.py) | JSON envelope → styled multi-sheet Excel workbook (auto status fill, frozen header) | openpyxl (Python, already in venv; see `docs/archive/phase_3-4/PHASE_3E_TOOLCHAIN.md`) |

## Delegation — formats this skill does NOT own

PDF, PPTX, MP4, and GIF are visual / presentation / motion formats; they are designed by `huashu-design` (HTML deck / animation rendering via Node + Playwright + Chromium). They are **not** re-exported here, and there is no plan to re-export them. If a consumer skill needs one of those formats:

1. Add `../huashu-design/scripts` to that skill's `metadata.script_paths`.
2. Invoke `huashu-design`'s renderer script directly (e.g. `export_deck_pdf.mjs`, `export_deck_pptx.mjs`, `render-video.js`).
3. Do NOT route through `renderers` for these formats — there is nothing here to dispatch to and you will get a missing-script error.

If the user asks `renderers` (this skill) directly for one of those formats, decline and name `huashu-design` as the correct skill. See `docs/archive/phase_3-4/PHASE_3A_TOOLCHAIN.md` for the Node / Playwright toolchain `huashu-design` uses.

## Invocation Pattern (from a consumer skill)

```json
{
  "tool": "run_script",
  "path": "../renderers/scripts/render_docx.py",
  "args": [
    "--input",
    "{artifacts}/proposal.md",
    "--output",
    "{artifacts}/proposal.docx",
    "--metadata",
    "title=Volume I — Technical Approach",
    "--toc"
  ],
  "timeout": 60
}
```

Placeholders `{run_dir}` / `{artifacts}` / `{skill_dir}` are substituted by the runtime, so consumer skills don't need to know the per-run filesystem layout. Cross-skill resolution requires the consumer's `metadata.script_paths` to include `../renderers/scripts`.

## Renderer Authoring Conventions

Every script in `scripts/` MUST:

1. Be a self-contained CLI (`argparse`-style flags), no shared library.
2. Detect missing toolchain dependencies up front and exit `127` with an actionable install hint on stderr.
3. Print the absolute output path to stdout on success and exit `0`.
4. Use exit code `2` for bad arguments / missing inputs; surface upstream tool stderr verbatim for other failures.
5. Stay format-focused — no domain logic, no LLM calls, no KG access. If a script needs domain shaping, that work belongs in the consumer skill before invoking the renderer.
6. Run on Windows / macOS / Linux without modification (use `pathlib`, `shutil.which`, no shell quoting tricks).

## Workflow (when activated directly)

1. Use `read_file` on any source file the user references.
2. Pick the renderer matching the requested output format.
3. Invoke it via `run_script` with the user-supplied input/output paths.
4. Confirm `exit_code == 0` and report the output path back to the user.
5. If `exit_code == 127`, surface the script's stderr (which contains the install instructions) verbatim.

## See Also

- [docs/archive/phase_3-4/PHASE_3D_TOOLCHAIN.md](../../../docs/archive/phase_3-4/PHASE_3D_TOOLCHAIN.md) — Pandoc install + DOCX renderer contract
- [docs/archive/phase_3-4/PHASE_3E_TOOLCHAIN.md](../../../docs/archive/phase_3-4/PHASE_3E_TOOLCHAIN.md) — openpyxl + XLSX renderer contract
- [docs/PHASE_3A_TOOLCHAIN.md](../../../docs/PHASE_3A_TOOLCHAIN.md) — Node / Playwright / Chromium for huashu-design renderers
- [docs/skills_roadmap.md](../../../docs/skills_roadmap.md) — Phase 3 sub-phase tracking
