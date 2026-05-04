"""Phase 4g contract tests for the price-to-win skill.

Mirrors test_compliance_auditor_skill.py / test_competitive_intel_skill.py.

Two layers:

1. **Always-on**: spec-compliance of SKILL.md frontmatter + body invariants
   (3 declared MCPs, decision tree present, 3 cost-model references exist,
   evals exercise all 3 MCPs and all 3 cost models).

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

# Load repo .env so live-MCP runs can pick up API keys (BLS_API_KEY, etc.)
# without requiring contributors to export them manually.
load_dotenv()

from src.skills.manager import SkillManager
from src.skills.mcp_client import MCPRegistry


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / ".github" / "skills"
_SKILL_DIR = _SKILLS_ROOT / "price-to-win"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"
_REFERENCES = _SKILL_DIR / "references" / "cost_models"
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
    "ffp_buildup.md",
    "lh_tm_buildup.md",
    "cost_reimbursement_buildup.md",
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


def test_price_to_win_frontmatter_is_spec_compliant() -> None:
    fm, _ = _read_frontmatter_and_body(_SKILL_MD)
    extra = set(fm) - _ALLOWED_FRONTMATTER_FIELDS
    assert not extra, (
        f"price-to-win SKILL.md has non-spec top-level frontmatter fields: {extra}. "
        f"Move them under `metadata:`."
    )
    assert fm["name"] == "price-to-win"
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars (spec max 1024)"
    )
    assert "USE WHEN" in fm["description"]
    assert "DO NOT USE FOR" in fm["description"]
    desc_lower = fm["description"].lower()
    for needle in ("bls", "calc", "per diem"):
        assert needle in desc_lower, (
            f"description should mention '{needle}' so the trigger router routes"
            f" pricing/PTW questions to this skill"
        )


def test_price_to_win_declares_three_mcps() -> None:
    mgr = SkillManager(_SKILLS_ROOT)
    skill = mgr.get_skill("price-to-win")
    assert skill is not None
    assert skill.frontmatter.runtime_mode == "tools"
    assert sorted(skill.frontmatter.required_mcps) == sorted(_REQUIRED_MCPS), (
        f"expected MCPs {sorted(_REQUIRED_MCPS)}, "
        f"got {sorted(skill.frontmatter.required_mcps)}"
    )


def test_price_to_win_body_has_decision_tree() -> None:
    """The whole point of collapsing 3 upstream skills into 1 is the
    decision tree at the top of the body. If it's gone, the skill has
    regressed back to a single contract type."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    assert "Decision Tree" in body, "SKILL.md body missing 'Decision Tree' section"
    # All three contract-type families must be enumerated.
    for marker in ("FFP", "LH", "T&M", "CPFF", "CPAF", "CPIF"):
        assert marker in body, (
            f"decision tree missing '{marker}' — collapsed skill must enumerate "
            f"all contract types"
        )


def test_price_to_win_references_exist() -> None:
    for ref in _REQUIRED_REFERENCES:
        path = _REFERENCES / ref
        assert path.exists(), (
            f"missing required cost-model reference: {path.relative_to(_REPO_ROOT)}"
        )
        text = path.read_text(encoding="utf-8")
        assert len(text) > 500, f"{ref} suspiciously short ({len(text)} chars)"


def test_price_to_win_body_references_real_mcp_tools_only() -> None:
    """Every `mcp__<server>__<tool>` mentioned in the body must be in the
    curated whitelist for that server. Live test below cross-checks against
    the running servers."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)

    bls_referenced = set(re.findall(r"mcp__bls_oews__([a-z_]+)", body))
    calc_referenced = set(re.findall(r"mcp__gsa_calc__([a-z_]+)", body))
    perdiem_referenced = set(re.findall(r"mcp__gsa_perdiem__([a-z_]+)", body))

    assert bls_referenced, "SKILL.md references zero bls_oews tools"
    assert calc_referenced, "SKILL.md references zero gsa_calc tools"
    assert perdiem_referenced, "SKILL.md references zero gsa_perdiem tools"

    # Curated whitelists per Phase 4f.3 / 4f.4 / 4f.7 toolchain docs.
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


def test_price_to_win_evals_exercise_all_three_mcps_and_all_three_models() -> None:
    """Each cost model must have at least one eval, and each MCP must be
    referenced in at least one eval's expectations."""
    data = json.loads(_EVALS.read_text(encoding="utf-8"))
    evals = data["evals"]
    assert len(evals) >= 3, f"expected at least 3 evals (one per cost model), got {len(evals)}"

    all_expectations = " ".join(
        exp for e in evals for exp in e.get("expectations", [])
    )

    for mcp in _REQUIRED_MCPS:
        assert f"mcp__{mcp}__" in all_expectations, (
            f"no eval expectation references mcp__{mcp}__ — wiring is decorative"
        )

    # At least one eval per cost-model reference.
    for ref in _REQUIRED_REFERENCES:
        assert ref in all_expectations, (
            f"no eval expectation requires reading references/cost_models/{ref} — "
            f"the decision tree branch is unexercised"
        )


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
        startup = await registry.start_run_sessions(
            run_id="phase4g-skill-contract", requested=_REQUIRED_MCPS
        )
        try:
            sessions = startup.sessions
            for server, referenced in referenced_by_server.items():
                if not referenced:
                    continue
                if server not in sessions:
                    # MCP failed to start (typically missing API key in this env).
                    # Skip that server's drift check rather than crash; the always-on
                    # whitelist test in Layer 1 still guards typo regressions.
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
            await registry.shutdown_run("phase4g-skill-contract")
            await registry.shutdown_all()

    _run(_go())
