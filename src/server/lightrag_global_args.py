"""
Safe access to LightRAG `global_args`.

Upstream LightRAG's `lightrag.api.config` parses CLI args at import time. That is fine
when running the LightRAG server as a CLI, but it breaks library-style imports under
tools like `pytest` (because pytest injects flags like `-q` into sys.argv).

This module sanitizes argv by default unless explicitly overridden.
"""

from __future__ import annotations

import os
import sys


def _sanitize_argv_for_import() -> None:
    # Opt-out switch: keep LightRAG's argparse behavior when running as a CLI.
    if (os.getenv("LIGHTRAG_PARSE_CLI", "false") or "false").strip().lower() in {"1", "true", "yes", "y"}:
        return

    # If any argv flags are present (common in test runners), strip them.
    # This keeps `lightrag.api.config` import-safe.
    if any(a.startswith("-") for a in sys.argv[1:]):
        sys.argv = [sys.argv[0]]


_sanitize_argv_for_import()

# Import after argv sanitization
from lightrag.api.config import global_args  # noqa: E402

