"""
RAG-Anything LibreOffice Windows Compatibility Patch

Problem:
    On Windows, `libreoffice.exe` is a GUI wrapper that returns exit code
    0xFFFFFFFF (-1) when run headless, even if conversion succeeds.
    The parser.py checks `returncode == 0`, so it always falls back and
    warns "LibreOffice command 'libreoffice' failed:".

    `soffice.com` (the console redirector) works correctly on Windows
    and returns RC 0 on success.

Fix:
    1. On Windows, try `soffice` before `libreoffice` (soffice.com resolves first).
    2. After all commands are tried, check whether the PDF was actually generated
       even if returncode != 0 (LO sometimes exits non-zero but still writes the file).
    3. Also adds --norestore --nofirststartwizard flags to suppress LO first-run wizard.

Usage:
    Import and call apply_patch() BEFORE any document parsing occurs.
    Applied in src/server/initialization.py during startup.

When to remove:
    When raganything fixes Windows soffice ordering upstream.
"""

import logging
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

_PATCHED = False


def apply_patch():
    """Monkey-patch MineruParser.convert_office_to_pdf for Windows compatibility."""
    global _PATCHED
    if _PATCHED:
        return

    from raganything.parser import MineruParser

    @classmethod
    def _patched_convert_office_to_pdf(
        cls,
        doc_path: Union[str, Path],
        output_dir: Optional[str] = None,
    ) -> Path:
        """Windows-compatible LibreOffice PDF conversion.

        - Tries soffice first on Windows (soffice.com returns RC 0 correctly)
        - Falls back to libreoffice on other platforms
        - Accepts conversion if PDF was generated even when RC != 0
        """
        doc_path = Path(doc_path)

        if output_dir:
            base_output_dir = Path(output_dir)
        else:
            base_output_dir = doc_path.parent / "libreoffice_output"
        base_output_dir.mkdir(parents=True, exist_ok=True)

        # On Windows, soffice.com (console wrapper) works; libreoffice.exe is GUI-only
        if platform.system() == "Windows":
            commands_to_try = ["soffice", "libreoffice"]
        else:
            commands_to_try = ["libreoffice", "soffice"]

        # Extra flags to suppress first-run wizard and crash recovery prompts
        extra_flags = ["--norestore", "--nofirststartwizard"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            conversion_successful = False

            subprocess_kwargs = {
                "capture_output": True,
                "text": True,
                "timeout": 120,
                "encoding": "utf-8",
                "errors": "ignore",
            }
            if platform.system() == "Windows":
                subprocess_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            for cmd in commands_to_try:
                try:
                    convert_cmd = [
                        cmd,
                        "--headless",
                        *extra_flags,
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(temp_path),
                        str(doc_path),
                    ]
                    result = subprocess.run(convert_cmd, **subprocess_kwargs)

                    # Check if PDF was actually created (LO may return non-zero but still work)
                    pdf_files = list(temp_path.glob("*.pdf"))

                    if result.returncode == 0 or pdf_files:
                        if result.returncode != 0:
                            cls.logger.warning(
                                f"LibreOffice '{cmd}' returned RC={result.returncode} "
                                f"but PDF was generated — treating as success"
                            )
                        else:
                            cls.logger.info(
                                f"Successfully converted {doc_path.name} to PDF using {cmd}"
                            )
                        conversion_successful = True
                        break
                    else:
                        cls.logger.warning(
                            f"LibreOffice command '{cmd}' failed (RC={result.returncode}): "
                            f"{result.stderr.strip()}"
                        )
                except FileNotFoundError:
                    cls.logger.debug(f"LibreOffice command '{cmd}' not found, skipping")
                except subprocess.TimeoutExpired:
                    cls.logger.warning(f"LibreOffice command '{cmd}' timed out")
                except Exception as e:
                    cls.logger.error(f"LibreOffice command '{cmd}' failed with exception: {e}")

            if not conversion_successful:
                raise RuntimeError(
                    f"LibreOffice conversion failed for {doc_path.name}. "
                    "Ensure LibreOffice is installed and 'soffice' is in PATH.\n"
                    "- Windows: C:\\Program Files\\LibreOffice\\program\\ must be on PATH"
                )

            pdf_files = list(temp_path.glob("*.pdf"))
            if not pdf_files:
                raise RuntimeError(
                    f"PDF conversion failed for {doc_path.name} - no PDF file generated."
                )

            # Copy PDF to output dir
            import shutil
            pdf_src = pdf_files[0]
            pdf_dst = base_output_dir / pdf_src.name
            shutil.copy2(pdf_src, pdf_dst)
            return pdf_dst

    MineruParser.convert_office_to_pdf = _patched_convert_office_to_pdf
    _PATCHED = True
    logger.info("✅ LibreOffice Windows patch applied (soffice preferred on Windows)")
