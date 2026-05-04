"""Shared counters for LightRAG JSON storage files."""

from __future__ import annotations

import json
from pathlib import Path

_COUNT_CACHE: dict[tuple[str, int, int], int] = {}


def safe_count_json_keys(path: Path) -> int:
    """Count records in a LightRAG storage JSON file, returning 0 on errors."""
    try:
        if not path.exists():
            return 0
        stat = path.stat()
        key = (str(path), stat.st_mtime_ns, stat.st_size)
        cached = _COUNT_CACHE.get(key)
        if cached is not None:
            return cached
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            inner = data.get("data")
            count = len(inner) if isinstance(inner, list) else len(data)
        elif isinstance(data, list):
            count = len(data)
        else:
            count = 0
        for old_key in [old_key for old_key in _COUNT_CACHE if old_key[0] == str(path)]:
            _COUNT_CACHE.pop(old_key, None)
        _COUNT_CACHE[key] = count
        return count
    except Exception:  # noqa: BLE001
        return 0
