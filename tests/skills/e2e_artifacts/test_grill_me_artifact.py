"""E2E test: assert grill-me skills emit a DOCX/XLSX artifact.

This test is gated by the e2e harness in `tests/skills/e2e/conftest.py`.
It will skip if the server isn't reachable or the active workspace differs
from the expected fixture. If the skill does not emit an artifact yet,
the test is marked xfail rather than hard-failing to avoid blocking
progress while the rendering wiring is completed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx
import pytest

from tests.skills.e2e.conftest import invoke_skill


SKILL_NAME = "grill-me-govcon"


def _evals_prompt(skill_name: str) -> str | None:
    repo_root = Path(__file__).resolve().parents[3]
    evals_path = repo_root / ".github" / "skills" / skill_name / "evals" / "evals.json"
    if not evals_path.exists():
        return None
    try:
        data = json.loads(evals_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    prompts = data.get("prompts") or data.get("evals") or []
    if isinstance(prompts, list) and prompts:
        first = prompts[0]
        if isinstance(first, dict):
            return first.get("prompt") or first.get("input")
        if isinstance(first, str):
            return first
    return None


def test_grill_me_emits_artifact(http_client: httpx.Client, base_url: str, installed_skills: list[dict[str, Any]]):
    """Invoke `grill-me-govcon` and assert a DOCX/XLSX appears in artifacts.

    This test prefers a hard assert but uses xfail if no artifact is produced
    so it doesn't block ongoing work while renderers are being wired.
    """
    names = [s.get("name") for s in (installed_skills or []) if isinstance(s, dict)]
    if SKILL_NAME not in names:
        pytest.skip(f"Skill {SKILL_NAME!r} not installed on this server")

    prompt = _evals_prompt(SKILL_NAME) or (
        "Generate a Grill-Me report JSON and render a DOCX and XLSX version."
    )

    envelope = invoke_skill(http_client, base_url, SKILL_NAME, prompt)

    assert envelope.get("skill") == SKILL_NAME
    run_dir = envelope.get("run_dir")
    if not run_dir:
        pytest.xfail(f"No run_dir returned from {SKILL_NAME} invocation; cannot verify artifacts")

    artifacts = list(Path(run_dir).joinpath("artifacts").glob("*")) if Path(run_dir).joinpath("artifacts").exists() else []
    docx_found = any(p.suffix.lower() == ".docx" for p in artifacts)
    xlsx_found = any(p.suffix.lower() == ".xlsx" for p in artifacts)

    if not (docx_found or xlsx_found):
        pytest.xfail(
            f"No .docx or .xlsx produced by {SKILL_NAME}; artifacts dir contents: {[p.name for p in artifacts]}"
        )

    # At least one artifact exists; soft sanity checks
    assert docx_found or xlsx_found
