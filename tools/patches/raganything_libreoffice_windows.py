"""
RAG-Anything LibreOffice Windows Compatibility Patch

Problems:
    1. On Windows, `libreoffice.exe` is a GUI wrapper that returns exit code
       0xFFFFFFFF (-1) when run headless, even if conversion succeeds.
    2. Office parsing can still fail after successful PDF conversion if the
       downstream MinerU invocation exits non-zero on the first attempt.

Fixes:
    1. On Windows, try `soffice` before `libreoffice` (soffice.com resolves first).
    2. After all commands are tried, check whether the PDF was actually generated
       even if returncode != 0 (LO sometimes exits non-zero but still writes the file).
    3. Add --norestore --nofirststartwizard flags to suppress LO first-run wizard.
    4. Retry Office parsing once against the generated PDF before failing the document.

Usage:
    Import and call apply_patch() BEFORE any document parsing occurs.
    Applied in src/server/initialization.py during startup.

When to remove:
    When raganything fixes Windows soffice ordering and adds a robust Office retry upstream.
"""

import logging
import hashlib
import platform
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

_PATCHED = False


def apply_patch():
    """Monkey-patch MineruParser Office parsing for Windows compatibility."""
    global _PATCHED
    if _PATCHED:
        return

    from raganything.parser import MineruParser, Parser

    _original_unique_output_dir = Parser._unique_output_dir
    _generated_pdf_paths: set[Path] = set()

    @staticmethod
    def _patched_unique_output_dir(
        base_dir: Union[str, Path], file_path: Union[str, Path]
    ) -> Path:
        """Use a short deterministic work dir on Windows when the default path is too long."""
        candidate = _original_unique_output_dir(base_dir, file_path)
        if platform.system() != "Windows":
            return candidate

        file_path = Path(file_path).resolve()
        stem = file_path.stem
        predicted_md = candidate.resolve() / stem / "auto" / f"{stem}.md"
        if len(str(predicted_md)) <= 240:
            return candidate

        path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:8]
        short_candidate = Path(base_dir) / f"_mineru_{path_hash}"
        logger.warning(
            "Using shortened MinerU output dir for Windows path-length safety: %s -> %s",
            candidate.name,
            short_candidate.name,
        )
        return short_candidate

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
            _generated_pdf_paths.add(pdf_dst.resolve())
            return pdf_dst

    def _patched_parse_office_doc(
        self,
        doc_path: Union[str, Path],
        output_dir: Optional[str] = None,
        lang: Optional[str] = None,
        **kwargs,
    ):
        """Retry MinerU once when Office conversion succeeds but parsing fails."""
        pdf_path: Path | None = None

        def _cleanup_generated_pdf() -> None:
            if pdf_path is None:
                return

            resolved_pdf = pdf_path.resolve()
            if resolved_pdf not in _generated_pdf_paths:
                return

            try:
                pdf_path.unlink(missing_ok=True)
                self.logger.info(
                    "Removed temporary Office-to-PDF artifact after successful parse: %s",
                    pdf_path.name,
                )
            except Exception as cleanup_error:
                self.logger.warning(
                    "Could not remove temporary Office-to-PDF artifact %s: %s",
                    pdf_path,
                    cleanup_error,
                )
            finally:
                _generated_pdf_paths.discard(resolved_pdf)

        try:
            pdf_path = self.convert_office_to_pdf(doc_path, output_dir)

            try:
                content_list = self.parse_pdf(
                    pdf_path=pdf_path, output_dir=output_dir, lang=lang, **kwargs
                )
                _cleanup_generated_pdf()
                return content_list
            except Exception as first_error:
                if pdf_path is None or not pdf_path.exists():
                    raise

                self.logger.warning(
                    "Office parse failed after successful PDF conversion for %s; "
                    "retrying MinerU once against %s. First error: %s",
                    Path(doc_path).name,
                    pdf_path.name,
                    first_error,
                )

                try:
                    content_list = self.parse_pdf(
                        pdf_path=pdf_path,
                        output_dir=output_dir,
                        lang=lang,
                        **kwargs,
                    )
                    _cleanup_generated_pdf()
                    return content_list
                except Exception as retry_error:
                    self.logger.error(
                        "Office parse retry failed for %s. First error: %s | Retry error: %s",
                        Path(doc_path).name,
                        first_error,
                        retry_error,
                    )
                    raise retry_error from first_error

        except Exception as e:
            self.logger.error(f"Error in parse_office_doc: {str(e)}")
            raise

    Parser._unique_output_dir = _patched_unique_output_dir
    MineruParser._unique_output_dir = _patched_unique_output_dir
    MineruParser.convert_office_to_pdf = _patched_convert_office_to_pdf
    MineruParser.parse_office_doc = _patched_parse_office_doc
    _PATCHED = True
    logger.info(
        "✅ LibreOffice Windows patch applied "
        "(soffice preferred + Office PDF retry enabled)"
    )
