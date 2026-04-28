#!/usr/bin/env python3
"""Render a Markdown source into a Microsoft Word (.docx) file via Pandoc.

Phase 3d renderer for the proposal-generator skill. Federal proposals are
submitted as DOCX, often on agency- or company-mandated Word templates.
Pandoc's ``--reference-doc`` flag maps every Markdown heading/style onto the
template's corresponding Word style, which is the only practical way to honor
varied corporate templates without per-template rendering code.

Invocation contract (called via the skills runtime ``run_script`` tool):

    {
      "path": "scripts/render_docx.py",
      "args": [
        "--input",  "{artifacts}/proposal.md",
        "--output", "{artifacts}/proposal.docx",
        "--reference", "{skill_dir}/assets/reference.docx",  # optional
        "--toc"                                              # optional
      ],
      "timeout": 60
    }

Exits with code 0 on success and prints the absolute output path to stdout.
Exits non-zero with an actionable message on stderr if Pandoc is missing or
the conversion fails.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

PANDOC_INSTALL_HINT = (
    "Pandoc was not found on PATH. Install it to render DOCX volumes:\n"
    "  Windows : winget install --id JohnMacFarlane.Pandoc\n"
    "  macOS   : brew install pandoc\n"
    "  Linux   : apt install pandoc  (or your distro equivalent)\n"
    "See docs/PHASE_3D_TOOLCHAIN.md for details."
)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render_docx.py",
        description="Render Markdown to .docx via Pandoc (proposal-generator Phase 3d).",
    )
    p.add_argument(
        "--input",
        required=True,
        help="Path to the Markdown source file. Use '-' to read from stdin.",
    )
    p.add_argument(
        "--output",
        required=True,
        help="Path to write the .docx artifact (parent dir will be created).",
    )
    p.add_argument(
        "--reference",
        default=None,
        help="Optional Word template (.docx) whose styles will be inherited.",
    )
    p.add_argument(
        "--toc",
        action="store_true",
        help="Insert a table of contents at the top of the document.",
    )
    p.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Pandoc metadata pair (repeatable), e.g. --metadata title='Volume I'.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    pandoc = shutil.which("pandoc")
    if not pandoc:
        print(PANDOC_INSTALL_HINT, file=sys.stderr)
        return 127

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd: list[str] = [pandoc, "--from", "markdown", "--to", "docx", "-o", str(output_path)]

    if args.reference:
        ref_path = Path(args.reference).resolve()
        if not ref_path.is_file():
            print(
                f"Reference template not found: {ref_path}\n"
                "Continue without --reference to use Pandoc's default styles.",
                file=sys.stderr,
            )
            return 2
        cmd.extend(["--reference-doc", str(ref_path)])

    if args.toc:
        cmd.append("--toc")

    for kv in args.metadata:
        if "=" not in kv:
            print(f"Invalid --metadata value (expected KEY=VALUE): {kv}", file=sys.stderr)
            return 2
        cmd.extend(["--metadata", kv])

    if args.input == "-":
        stdin_text = sys.stdin.read()
        proc = subprocess.run(cmd, input=stdin_text, text=True, capture_output=True, check=False)
    else:
        input_path = Path(args.input).resolve()
        if not input_path.is_file():
            print(f"Input markdown file not found: {input_path}", file=sys.stderr)
            return 2
        cmd.append(str(input_path))
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)

    if proc.returncode != 0:
        # Pandoc writes diagnostics to stderr; surface them verbatim.
        sys.stderr.write(proc.stderr or "Pandoc exited non-zero with no stderr output.\n")
        return proc.returncode

    if not output_path.is_file():
        print(
            f"Pandoc reported success but output file is missing: {output_path}",
            file=sys.stderr,
        )
        return 1

    print(str(output_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
