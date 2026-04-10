"""
RAG-Anything MinerU 3.0 Compatibility Patch

Patches raganything.parser.MineruParser._run_mineru_command to remove
CLI flags that were removed in MinerU 3.0:
  - `-d` (device): Removed — MinerU 3.0 manages device internally via API service
  - `--source` (model source): Removed — now configured via mineru.json

This patch is idempotent and safe to apply multiple times.

Usage:
    Import this module BEFORE any raganything document parsing occurs.
    It's imported by src/server/initialization.py during startup.

When to remove:
    When raganything releases a version with native MinerU 3.0 support,
    remove this patch and the import in initialization.py.
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)

_PATCHED = False


def apply_patch():
    """Monkey-patch MineruParser._run_mineru_command for MinerU 3.0 compatibility."""
    global _PATCHED
    if _PATCHED:
        return

    from raganything.parser import MineruParser

    _original_run = MineruParser._run_mineru_command

    @classmethod
    def _patched_run_mineru_command(
        cls,
        input_path: Union[str, Path],
        output_dir: Union[str, Path],
        method: str = "auto",
        lang: Optional[str] = None,
        backend: Optional[str] = None,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
        formula: bool = True,
        table: bool = True,
        device: Optional[str] = None,
        source: Optional[str] = None,
        vlm_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        """MinerU 3.0 compatible wrapper — strips removed -d and --source flags."""
        if device:
            cls.logger.info(
                f"[MinerU 3.0 compat] Ignoring device='{device}' (flag removed in 3.0)"
            )
        if source:
            cls.logger.info(
                f"[MinerU 3.0 compat] Ignoring source='{source}' (flag removed in 3.0)"
            )

        # Call original but with device=None, source=None so the flags aren't emitted
        return _original_run.__func__(
            cls,
            input_path=input_path,
            output_dir=output_dir,
            method=method,
            lang=lang,
            backend=backend,
            start_page=start_page,
            end_page=end_page,
            formula=formula,
            table=table,
            device=None,
            source=None,
            vlm_url=vlm_url,
            **kwargs,
        )

    MineruParser._run_mineru_command = _patched_run_mineru_command
    _PATCHED = True
    logger.info("✅ Applied MinerU 3.0 compatibility patch (removed -d and --source flags)")
