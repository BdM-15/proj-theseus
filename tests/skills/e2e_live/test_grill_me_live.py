import os
import json
from pathlib import Path
from typing import Optional

import httpx
import pytest

BASE_URL = os.getenv("THESEUS_E2E_BASE_URL", "http://127.0.0.1:9621").rstrip("/")
WORKSPACE = os.getenv("THESEUS_E2E_WORKSPACE", "mcpp_drfp_t4")
SKILLS = [
    "grill-me-govcon",
    "grill-me-bid-strategy",
    "grill-me-capture",
    "grill-me-proposal",
    "grill-me-ptw",
]


def _evals_prompt(skill_name: str) -> Optional[str]:
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


@pytest.mark.parametrize("skill_name", SKILLS)
def test_grill_me_invocations(skill_name: str):
    # Check server
    try:
        resp = httpx.get(f"{BASE_URL}/api/ui/workspaces", timeout=5.0)
        resp.raise_for_status()
    except Exception as exc:
        pytest.skip(f"Server not reachable at {BASE_URL}: {exc}")

    active = (resp.json() or {}).get("active", None)
    if active != WORKSPACE:
        pytest.skip(f"Active workspace is {active!r}; test expects {WORKSPACE!r}")

    # Check skill exists
    skills_resp = httpx.get(f"{BASE_URL}/api/ui/skills", timeout=10.0)
    skills_resp.raise_for_status()
    installed = [s.get("name") for s in (skills_resp.json() or {}).get("skills", [])]
    if skill_name not in installed:
        pytest.skip(f"Skill {skill_name!r} not installed on server")

    prompt = _evals_prompt(skill_name) or (
        "Run a short grill-me check against the active workspace and provide a brief grounded summary."
    )

    client = httpx.Client(timeout=180.0)
    try:
        payload = {"prompt": prompt}
        r = client.post(f"{BASE_URL}/api/ui/skills/{skill_name}/invoke", json=payload)
        r.raise_for_status()
        envelope = r.json()
    finally:
        client.close()

    assert envelope.get("skill") == skill_name
    resp_text = envelope.get("response") or ""
    assert isinstance(resp_text, str) and resp_text.strip(), f"Empty response for {skill_name}"

    # If run_id present, try to fetch run detail
    run_id = envelope.get("run_id")
    if run_id:
        rd = httpx.get(f"{BASE_URL}/api/ui/skills/{skill_name}/runs/{run_id}", timeout=20.0)
        rd.raise_for_status()
        run_detail = rd.json()
        assert run_detail, "empty run detail"

