"""Pytest fixtures for the skills E2E harness.

Double-gated:

1. ``RUN_SKILL_E2E=1`` env var must be set.
2. The Theseus server at ``THESEUS_E2E_BASE_URL`` (default
   ``http://127.0.0.1:9621``) must respond to ``GET /api/ui/skills``.

Both gates failing => entire e2e suite is skipped (clean PASS via skip).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import httpx
import pytest


def _e2e_enabled() -> bool:
    return os.getenv("RUN_SKILL_E2E", "").strip().lower() in {"1", "true", "yes"}


def _base_url() -> str:
    return os.getenv("THESEUS_E2E_BASE_URL", "http://127.0.0.1:9621").rstrip("/")


def _expected_workspace() -> str:
    return os.getenv("THESEUS_E2E_WORKSPACE", "doj_mmwr_old_rfp")


# Hard skip the whole package when not enabled or no server is reachable.
def pytest_collection_modifyitems(config, items):
    if not _e2e_enabled():
        skip_marker = pytest.mark.skip(reason="RUN_SKILL_E2E not set; e2e suite skipped")
        for item in items:
            if "tests/skills/e2e" in str(item.fspath).replace("\\", "/"):
                item.add_marker(skip_marker)
        return

    # Probe the server once at collection time.
    try:
        resp = httpx.get(f"{_base_url()}/api/ui/skills", timeout=5.0)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        skip_marker = pytest.mark.skip(
            reason=f"Theseus server not reachable at {_base_url()}: {exc}"
        )
        for item in items:
            if "tests/skills/e2e" in str(item.fspath).replace("\\", "/"):
                item.add_marker(skip_marker)


@pytest.fixture(scope="session")
def base_url() -> str:
    return _base_url()


@pytest.fixture(scope="session")
def expected_workspace() -> str:
    return _expected_workspace()


@pytest.fixture(scope="session")
def http_client() -> httpx.Client:
    """Long-timeout client — skill tool loops can take 60+ s against Grok."""
    with httpx.Client(timeout=180.0) as client:
        yield client


@pytest.fixture(scope="session")
def installed_skills(http_client: httpx.Client, base_url: str) -> list[dict[str, Any]]:
    resp = http_client.get(f"{base_url}/api/ui/skills")
    resp.raise_for_status()
    body = resp.json()
    return body.get("skills", body) if isinstance(body, dict) else body


def invoke_skill(
    http_client: httpx.Client,
    base_url: str,
    name: str,
    prompt: str,
    *,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Hit ``POST /api/ui/skills/{name}/invoke`` and return the full envelope."""
    payload: dict[str, Any] = {"prompt": prompt}
    if extra:
        payload.update(extra)
    resp = http_client.post(
        f"{base_url}/api/ui/skills/{name}/invoke",
        json=payload,
    )
    resp.raise_for_status()
    return resp.json()


def load_run_transcript(
    http_client: httpx.Client,
    base_url: str,
    skill_name: str,
    run_id: str,
) -> dict[str, Any]:
    """Fetch a recorded run via ``GET /api/ui/skills/{name}/runs/{run_id}``."""
    resp = http_client.get(
        f"{base_url}/api/ui/skills/{skill_name}/runs/{run_id}"
    )
    resp.raise_for_status()
    return resp.json()
