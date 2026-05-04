"""Phase 4f.2 contract tests for the compliance-auditor skill.

Two layers (mirrors test_competitive_intel_skill.py / test_ecfr_manifest.py):

1. **Always-on**: spec-compliance of SKILL.md frontmatter + body invariants
   (mcps allowlist, tools-mode runtime, body references real MCP tools,
   evals exercise eCFR).

2. **Opt-in (live)**: spawn the upstream ecfr MCP server, list its
   advertised tools, and confirm every ``mcp__ecfr__<tool>`` name
   referenced in SKILL.md actually exists. Catches upstream drift.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path

import pytest
import yaml

from src.skills.manager import SkillManager
from src.skills.mcp_client import MCPRegistry


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / ".github" / "skills"
_SKILL_DIR = _SKILLS_ROOT / "compliance-auditor"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"
_MCPS_ROOT = _REPO_ROOT / "tools" / "mcps"


# Open Skills spec: only these six top-level frontmatter fields are allowed.
_ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


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


def test_compliance_auditor_frontmatter_is_spec_compliant() -> None:
    fm, _ = _read_frontmatter_and_body(_SKILL_MD)
    extra = set(fm) - _ALLOWED_FRONTMATTER_FIELDS
    assert not extra, (
        f"compliance-auditor SKILL.md has non-spec top-level frontmatter fields: {extra}. "
        f"Move them under `metadata:`."
    )
    assert fm["name"] == "compliance-auditor"
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars (spec max 1024)"
    )
    assert "USE WHEN" in fm["description"]
    assert "DO NOT USE FOR" in fm["description"]
    assert "ecfr" in fm["description"].lower(), (
        "description should mention eCFR so the trigger router picks it for clause-currency questions"
    )


def test_compliance_auditor_declares_ecfr_mcp() -> None:
    mgr = SkillManager(_SKILLS_ROOT)
    skill = mgr.get_skill("compliance-auditor")
    assert skill is not None
    assert skill.frontmatter.runtime_mode == "tools"
    assert skill.frontmatter.required_mcps == ["ecfr"]


def test_compliance_auditor_body_references_real_ecfr_tools_only() -> None:
    """Every `mcp__ecfr__<tool>` mentioned in the body must be in the
    curated whitelist of tools the upstream advertises.

    Live test below (THESEUS_LIVE_MCP=1) cross-checks against the running
    server in case upstream renames or drops a tool.
    """
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    referenced = set(re.findall(r"mcp__ecfr__([a-z_]+)", body))
    assert referenced, "SKILL.md body references zero ecfr MCP tools — nothing to test"

    # Curated whitelist for ecfr-mcp v0.2.6 (verified live via test_ecfr_manifest.py
    # and references/ecfr_tools.md). Keep in sync with that reference table.
    known_v026 = {
        "lookup_far_clause",
        "get_version_history",
        "compare_versions",
        "find_far_definition",
        "get_cfr_content",
        "get_cfr_structure",
        "get_ancestry",
        "search_cfr",
        "get_corrections",
        "list_agencies",
        "list_sections_in_part",
        "find_recent_changes",
        "get_latest_date",
    }
    unknown = referenced - known_v026
    assert not unknown, (
        f"SKILL.md references ecfr tools not in the v0.2.6 whitelist: {unknown}. "
        f"If upstream added them, update this test + references/ecfr_tools.md."
    )


def test_compliance_auditor_evals_exercise_ecfr() -> None:
    """At least one eval prompt MUST require the skill to call an ecfr tool.
    Otherwise the MCP wiring is decorative and silently regresses."""
    data = json.loads(_EVALS.read_text(encoding="utf-8"))
    evals = data["evals"]
    assert len(evals) >= 5, f"expected at least 5 evals after Phase 4f.2, got {len(evals)}"
    ecfr_evals = [
        e for e in evals
        if any("mcp__ecfr__" in exp for exp in e.get("expectations", []))
    ]
    assert len(ecfr_evals) >= 2, (
        f"expected at least 2 evals with mcp__ecfr__ expectations (C9 + C10), "
        f"got {len(ecfr_evals)}"
    )


# ---------------------------------------------------------------------------
# Layer 2 — live drift check (opt-in)
# ---------------------------------------------------------------------------


_LIVE = os.environ.get("THESEUS_LIVE_MCP") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="set THESEUS_LIVE_MCP=1 to spawn uvx and verify SKILL.md tool refs against live ecfr MCP",
)
def test_skill_body_tool_refs_match_live_ecfr_mcp() -> None:
    """Run live: confirm every mcp__ecfr__<tool> in SKILL.md is actually
    advertised by the running upstream ecfr server.
    """
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    referenced = set(re.findall(r"mcp__ecfr__([a-z_]+)", body))

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        startup = await registry.start_run_sessions(
            run_id="phase4f2-skill-contract", requested=["ecfr"]
        )
        try:
            session = startup.sessions["ecfr"]
            advertised = {t.name for t in session.tools}
            missing = referenced - advertised
            assert not missing, (
                f"SKILL.md references {missing} but upstream ecfr MCP only "
                f"advertises {sorted(advertised)[:5]}… ({len(advertised)} tools total)"
            )
        finally:
            await registry.shutdown_run("phase4f2-skill-contract")
            await registry.shutdown_all()

    _run(_go())
