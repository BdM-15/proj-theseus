"""Small environment-variable parsing helpers."""

from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


def env_int(
    name: str,
    default: int,
    lo: Optional[int] = None,
    hi: Optional[int] = None,
) -> int:
    """Read an integer environment variable with optional clamping."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid %s=%r; using default %d", name, raw, default)
        return default
    if lo is not None:
        value = max(lo, value)
    if hi is not None:
        value = min(hi, value)
    return value



def env_float(
    name: str,
    default: float,
    lo: Optional[float] = None,
    hi: Optional[float] = None,
) -> float:
    """Read a float environment variable with optional clamping."""
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        logger.warning("Invalid %s=%r; using default %s", name, raw, default)
        return default
    if lo is not None:
        value = max(lo, value)
    if hi is not None:
        value = min(hi, value)
    return value