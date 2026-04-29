"""Phase 4i contract tests for the ot-prototype-strategist skill.

Mirrors test_price_to_win_skill.py.

Two layers:

1. **Always-on**: spec-compliance of SKILL.md frontmatter + body invariants
   (3 declared MCPs same as price-to-win, workflow selector + statutory
   citations present, references exist, evals exercise all 3 MCPs).

2. **Opt-in (live)**: spawn the upstream bls-oews / gsa-calc / gsa-perdiem
   MCP servers, list their advertised tools, and confirm every
   ``mcp__<server>__<tool>`` name referenced in SKILL.md actually exists.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

import pytest
import yaml
from dotenv import load_dotenv

load_dotenv()

from src.skills.manager import SkillManager
from src.skills.mcp_client import MCPRegistry


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / ".github" / "skills"
_SKILL_DIR = _SKILLS_ROOT / "ot-prototype-strategist"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"
_REFERENCES_DIR = _SKILL_DIR / "references"
_MCPS_ROOT = _REPO_ROOT / "tools" / "mcps"


_ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

_REQUIRED_MCPS = ["bls_oews", "gsa_calc", "gsa_perdiem"]
_REQUIRED_REFERENCES = [
    "ot_authority_taxonomy.md",
    "trl_milestone_patterns.md",
    "relationship_query_patterns.md",
    "cost_models/ot_milestone_buildup.md",
]


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


def _read_frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise AssertionError(f"{path} missing YAML frontmatter")
    _, fm_text, body = text.split("---", 2)
    return yaml.safe_load(fm_text), body


# ---------------------------------------------------------------------------
# Layer 1 — offline spec + body invariants (always runs)
# ---------------------------------------------------------------------------


def test_ot_strategist_frontmatter_is_spec_compliant() -> None:
    fm, _ = _read_frontmatter_and_body(_SKILL_MD)
    extra = set(fm) - _ALLOWED_FRONTMATTER_FIELDS
    assert not extra, (
        f"ot-prototype-strategist SKILL.md has non-spec top-level frontmatter fields: {extra}. "
        f"Move them under `metadata:`."
    )
    assert fm["name"] == "ot-prototype-strategist"
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars (spec max 1024)"
    )
    assert "USE WHEN" in fm["description"]
    assert "DO NOT USE FOR" in fm["description"]
    desc_lower = fm["description"].lower()
    for needle in ("ot", "prototype", "4022"):
        assert needle in desc_lower, (
            f"description should mention '{needle}' so the trigger router routes "
            f"OT/prototype questions to this skill"
        )


def test_ot_strategist_declares_three_mcps() -> None:
    mgr = SkillManager(_SKILLS_ROOT)
    skill = mgr.get_skill("ot-prototype-strategist")
    assert skill is not None
    assert skill.frontmatter.runtime_mode == "tools"
    assert sorted(skill.frontmatter.required_mcps) == sorted(_REQUIRED_MCPS), (
        f"expected MCPs {sorted(_REQUIRED_MCPS)}, "
        f"got {sorted(skill.frontmatter.required_mcps)}"
    )


def test_ot_strategist_body_has_workflow_selector_and_statutory_citations() -> None:
    """Whole point of collapsing 2 upstream skills into 1 is the workflow
    selector + 4022(d) cost-share decision logic. If those are gone, the
    skill regressed back to one-shot project-description authoring."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    assert "Workflow Selector" in body, "SKILL.md body missing 'Workflow Selector'"
    # Three core workflows must be enumerated.
    for marker in ("Respond to OT solicitation", "Pre-solicitation strategist", "Cost-share path comparison"):
        assert marker in body, f"workflow selector missing '{marker}'"
    # Core statutory framework must be cited.
    for stat in ("10 USC 4021", "10 USC 4022", "10 USC 4022(d)", "10 USC 3014", "10 USC 4003"):
        assert stat in body, f"SKILL.md body missing statutory reference '{stat}'"
    # Core domain markers.
    for marker in ("TRL", "milestone", "NDC", "cost-share", "should-cost"):
        assert marker.lower() in body.lower(), f"SKILL.md body missing domain marker '{marker}'"


def test_ot_strategist_references_exist() -> None:
    for ref in _REQUIRED_REFERENCES:
        path = _REFERENCES_DIR / ref
        assert path.exists(), (
            f"missing required reference: {path.relative_to(_REPO_ROOT)}"
        )
        text = path.read_text(encoding="utf-8")
        assert len(text) > 500, f"{ref} suspiciously short ({len(text)} chars)"


def test_ot_strategist_body_references_real_mcp_tools_only() -> None:
    """Every `mcp__<server>__<tool>` mentioned in the body must be in the
    curated whitelist for that server."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)

    bls_referenced = set(re.findall(r"mcp__bls_oews__([a-z_]+)", body))
    calc_referenced = set(re.findall(r"mcp__gsa_calc__([a-z_]+)", body))
    perdiem_referenced = set(re.findall(r"mcp__gsa_perdiem__([a-z_]+)", body))

    assert bls_referenced, "SKILL.md references zero bls_oews tools"
    assert calc_referenced, "SKILL.md references zero gsa_calc tools"
    assert perdiem_referenced, "SKILL.md references zero gsa_perdiem tools"

    # Reuse the same Phase 4f.3 / 4f.4 / 4f.7 whitelists as price-to-win.
    bls_known = {
        "get_wage_data",
        "igce_wage_benchmark",
        "compare_metros",
        "compare_socs",
        "list_metros",
        "list_socs",
        "list_industries",
    }
    calc_known = {
        "search_rates",
        "get_labor_categories",
        "igce_benchmark",
        "price_reasonableness_check",
        "list_schedules",
    }
    perdiem_known = {
        "get_per_diem_by_zip",
        "get_per_diem_by_city",
        "get_per_diem_by_state",
        "estimate_travel_cost",
        "list_states",
    }

    bls_unknown = bls_referenced - bls_known
    calc_unknown = calc_referenced - calc_known
    perdiem_unknown = perdiem_referenced - perdiem_known

    assert not bls_unknown, (
        f"SKILL.md references bls_oews tools not in whitelist: {bls_unknown}"
    )
    assert not calc_unknown, (
        f"SKILL.md references gsa_calc tools not in whitelist: {calc_unknown}"
    )
    assert not perdiem_unknown, (
        f"SKILL.md references gsa_perdiem tools not in whitelist: {perdiem_unknown}"
    )


def test_ot_strategist_evals_exercise_mcps_and_references() -> None:
    """Each MCP must appear in at least one eval; each top-level reference
    must appear in at least one eval. Decorative wiring fails."""
    data = json.loads(_EVALS.read_text(encoding="utf-8"))
    evals = data["evals"]
    assert len(evals) >= 3, f"expected at least 3 evals, got {len(evals)}"

    all_expectations = " ".join(
        exp for e in evals for exp in e.get("expectations", [])
    )

    for mcp in _REQUIRED_MCPS:
        assert f"mcp__{mcp}__" in all_expectations, (
            f"no eval expectation references mcp__{mcp}__ — wiring is decorative"
        )

    for ref in _REQUIRED_REFERENCES:
        ref_basename = ref.split("/")[-1]
        assert ref_basename in all_expectations, (
            f"no eval expectation requires reading references/{ref} — "
            f"the reference is unexercised"
        )


def test_ot_strategist_taxonomy_surfaces_via_manager() -> None:
    """Phase 4j taxonomy fields must round-trip through SkillManager.to_summary
    so the UI Skills page can group + filter this skill correctly."""
    mgr = SkillManager(_SKILLS_ROOT)
    skill = mgr.get_skill("ot-prototype-strategist")
    assert skill is not None
    summary = skill.to_summary()
    assert summary.get("personas_primary") == "cost_estimator"
    assert "capture_manager" in summary.get("personas_secondary", [])
    phases = summary.get("shipley_phases", [])
    assert "capture" in phases and "proposal_development" in phases
    assert summary.get("capability") == "estimate"


# ---------------------------------------------------------------------------
# Layer 2 — live drift check (opt-in)
# ---------------------------------------------------------------------------


_LIVE = os.environ.get("THESEUS_LIVE_MCP") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="set THESEUS_LIVE_MCP=1 to spawn uvx and verify SKILL.md tool refs against live MCPs",
)
def test_skill_body_tool_refs_match_live_mcps() -> None:
    """Confirm every mcp__<server>__<tool> in SKILL.md is actually advertised
    by the running upstream servers."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    referenced_by_server = {
        "bls_oews": set(re.findall(r"mcp__bls_oews__([a-z_]+)", body)),
        "gsa_calc": set(re.findall(r"mcp__gsa_calc__([a-z_]+)", body)),
        "gsa_perdiem": set(re.findall(r"mcp__gsa_perdiem__([a-z_]+)", body)),
    }

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        sessions = await registry.start_run_sessions(
            run_id="phase4i-skill-contract", requested=_REQUIRED_MCPS
        )
        try:
            for server, referenced in referenced_by_server.items():
                if not referenced:
                    continue
                if server not in sessions:
                    pytest.skip(
                        f"MCP {server!r} did not start (likely missing API key); "
                        f"skipping live drift check"
                    )
                advertised = {t.name for t in sessions[server].tools}
                missing = referenced - advertised
                assert not missing, (
                    f"SKILL.md references {missing} on {server} but upstream "
                    f"only advertises {sorted(advertised)[:5]}… "
                    f"({len(advertised)} tools total)"
                )
        finally:
            await registry.shutdown_run("phase4i-skill-contract")
            await registry.shutdown_all()

    _run(_go())
