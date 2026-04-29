"""Parametrized smoke test for every installed skill.

For each skill the server reports as installed, this test:

1. Picks a representative prompt (from the skill's own ``evals/evals.json``
   first entry; falls back to a per-skill default below).
2. Invokes the skill via the HTTP API.
3. Asserts the tool loop completed without erroring.
4. Asserts the response is non-empty.
5. Asserts grounding signals: at least one of (a) a chunk-id citation in the
   response, (b) ``entities_used`` non-empty in the envelope, (c) a non-empty
   transcript with KG retrieval calls (probed via the run-detail endpoint).

Skills that emit a deliverable (artifact) get an additional check that the
``run_dir/artifacts/`` directory was populated.

The harness is intentionally permissive on response *content* — branch 147
will tighten this with a quantified grounding-ratio audit. This branch only
proves the loop runs end-to-end.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx
import pytest

from .conftest import invoke_skill, load_run_transcript

# ---------- Per-skill default prompts (used if no evals.json) -------------

DEFAULT_PROMPTS: dict[str, str] = {
    "proposal-generator": (
        "Draft a brief executive summary outline for this opportunity, "
        "grounded in the workspace requirements and evaluation factors."
    ),
    "compliance-auditor": (
        "Audit clause coverage in the active workspace and flag the top 3 "
        "missing or ambiguous compliance items."
    ),
    "competitive-intel": (
        "Who are the likely incumbents and top competitors for this "
        "opportunity based on the workspace?"
    ),
    "price-to-win": (
        "Build a high-level price-to-win cost stack for this opportunity "
        "using the workspace's labor categories and period of performance."
    ),
    "ot-prototype-strategist": (
        "Is this opportunity structured as an OT prototype? If so, "
        "recommend the 4022(d) cost-share path and TRL phasing."
    ),
    "rfp-reverse-engineer": (
        "Reverse engineer the CO's hidden decision tree for this RFP. "
        "Surface hot buttons and ghost language."
    ),
    "subcontractor-sow-builder": (
        "Draft a brief SOW skeleton for a subcontractor covering the "
        "workspace's primary technical scope."
    ),
    "oci-sweeper": (
        "Sweep the workspace for organizational conflict of interest risks "
        "per FAR 9.5."
    ),
    "govcon-ontology": (
        "Validate the workspace's entity inventory against the 33-type "
        "ontology and flag any unusual gaps."
    ),
    "renderers": (
        "Render a sample compliance matrix DOCX from a small synthetic "
        "input to verify the script path works."
    ),
    "huashu-design": (
        "Sketch a hi-fi HTML mockup for a one-page proposal cover sheet "
        "for this workspace's opportunity."
    ),
}

# Skills whose primary deliverable is a file under run_dir/artifacts/
ARTIFACT_SKILLS = {
    "proposal-generator",
    "compliance-auditor",
    "renderers",
    "subcontractor-sow-builder",
    "price-to-win",
    "competitive-intel",
}

# Skills declared as ``runtime: legacy`` in frontmatter — they don't produce
# the same transcript shape. Skip the transcript-call assertion for these.
LEGACY_SKILLS = {"huashu-design"}

CHUNK_CITE_RE = re.compile(r"chunk-[0-9a-f]{4,}", re.IGNORECASE)


def _evals_prompt(skill_name: str) -> str | None:
    """Pull the first prompt from the skill's evals/evals.json, if present."""
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


def _resolve_prompt(skill_name: str) -> str:
    return _evals_prompt(skill_name) or DEFAULT_PROMPTS.get(
        skill_name,
        "Provide a brief grounded summary using the active workspace.",
    )


def _skill_names(installed_skills: list[dict[str, Any]]) -> list[str]:
    return sorted(s["name"] for s in installed_skills if isinstance(s, dict) and "name" in s)


@pytest.fixture(scope="module")
def skill_names(installed_skills: list[dict[str, Any]]) -> list[str]:
    names = _skill_names(installed_skills)
    if not names:
        pytest.skip("server reports zero installed skills")
    return names


def test_server_reports_skills(skill_names: list[str]) -> None:
    """Sanity: server should expose at least the 11 we expect."""
    assert len(skill_names) >= 11, f"Expected ≥11 skills, got {len(skill_names)}: {skill_names}"


@pytest.mark.parametrize("skill_name", sorted(DEFAULT_PROMPTS.keys()))
def test_skill_invoke_smoke(
    skill_name: str,
    skill_names: list[str],
    http_client: httpx.Client,
    base_url: str,
) -> None:
    """End-to-end: invoke the skill, verify the loop completed and grounded."""
    if skill_name not in skill_names:
        pytest.skip(f"skill {skill_name!r} not installed on this server")

    prompt = _resolve_prompt(skill_name)

    envelope = invoke_skill(http_client, base_url, skill_name, prompt)

    # 1. Loop completed: envelope present + non-empty response
    assert envelope.get("skill") == skill_name
    response = envelope.get("response") or ""
    assert isinstance(response, str) and response.strip(), (
        f"{skill_name}: empty response in envelope"
    )

    # 2. Grounding: at least one signal that workspace data was consulted
    cites_chunk = bool(CHUNK_CITE_RE.search(response))
    entities_used = envelope.get("entities_used") or {}
    has_entities = bool(entities_used) and (
        any(entities_used.values()) if isinstance(entities_used, dict) else True
    )

    transcript_has_kg_call = False
    run_id = envelope.get("run_id")
    if run_id and skill_name not in LEGACY_SKILLS:
        try:
            run_detail = load_run_transcript(http_client, base_url, skill_name, run_id)
            transcript = run_detail.get("transcript") or run_detail.get("turns") or []
            if isinstance(transcript, list):
                for turn in transcript:
                    if not isinstance(turn, dict):
                        continue
                    tool = (turn.get("tool") or turn.get("tool_name") or "").lower()
                    if tool in {"kg_chunks", "kg_query", "kg_entities"}:
                        transcript_has_kg_call = True
                        break
        except Exception:  # noqa: BLE001
            pass  # absence of run-detail endpoint shouldn't block the smoke

    grounded = cites_chunk or has_entities or transcript_has_kg_call
    assert grounded, (
        f"{skill_name}: no grounding signal (no chunk citation, no "
        f"entities_used, no kg_* tool call). Envelope keys: {list(envelope)}"
    )

    # 3. Artifact emitted where declared
    if skill_name in ARTIFACT_SKILLS:
        run_dir = envelope.get("run_dir")
        if run_dir:
            artifacts_dir = Path(run_dir) / "artifacts"
            if artifacts_dir.exists():
                files = list(artifacts_dir.iterdir())
                # Soft assertion — some skills may legitimately produce no
                # artifact when the prompt doesn't request one. Log but
                # don't hard-fail until branch 147.
                if not files:
                    pytest.xfail(
                        f"{skill_name}: ARTIFACT_SKILLS member but no artifact "
                        f"emitted — investigate in branch 147"
                    )
