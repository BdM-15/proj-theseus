"""Phase 4j contract tests for the oci-sweeper skill.

Mirrors the compliance-auditor contract test pattern but for a closed-by-default
(no MCPs declared) skill. Validates spec compliance, body invariants (FAR
Subpart 9.5 references, three OCI classes covered), references exist + are
non-empty, and evals exercise all three FAR 9.505 conflict classes.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml
from dotenv import load_dotenv

load_dotenv()


from src.skills.manager import SkillManager


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / ".github" / "skills"
_SKILL_DIR = _SKILLS_ROOT / "oci-sweeper"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"
_REFS_DIR = _SKILL_DIR / "references"


_ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def _read_frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), f"{path}: missing YAML frontmatter"
    _, fm_text, body = text.split("---", 2)
    return yaml.safe_load(fm_text), body


def test_oci_sweeper_skill_directory_exists() -> None:
    assert _SKILL_DIR.is_dir(), f"missing skill directory: {_SKILL_DIR}"
    assert _SKILL_MD.is_file(), f"missing SKILL.md: {_SKILL_MD}"
    assert _EVALS.is_file(), f"missing evals.json: {_EVALS}"
    assert _REFS_DIR.is_dir(), f"missing references/: {_REFS_DIR}"


def test_oci_sweeper_frontmatter_is_spec_compliant() -> None:
    fm, _ = _read_frontmatter_and_body(_SKILL_MD)
    extra = set(fm) - _ALLOWED_FRONTMATTER_FIELDS
    assert not extra, (
        f"oci-sweeper SKILL.md has non-spec top-level frontmatter fields: {extra}. "
        f"Move them under `metadata:`."
    )
    assert fm["name"] == "oci-sweeper"
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars (spec max 1024)"
    )
    assert "USE WHEN" in fm["description"]
    assert "DO NOT USE FOR" in fm["description"]
    # Description MUST mention FAR Subpart 9.5 so the trigger router selects
    # the skill when users ask about OCI / organizational conflicts.
    assert re.search(r"FAR\s+Subpart\s+9\.5", fm["description"]), (
        "description should reference 'FAR Subpart 9.5' so the trigger router "
        "picks oci-sweeper for OCI questions"
    )


def test_oci_sweeper_taxonomy_metadata_correct() -> None:
    fm, _ = _read_frontmatter_and_body(_SKILL_MD)
    meta = fm.get("metadata", {}) or {}
    assert meta.get("personas_primary") == "legal_compliance", (
        "OCI sweeps belong to the legal_compliance persona"
    )
    assert meta.get("capability") == "audit"
    phases = meta.get("shipley_phases", [])
    # OCI must be detected pre-bid (pursuit/capture). post_award is too late.
    assert "pursuit" in phases or "capture" in phases, (
        f"oci-sweeper should run in pursuit or capture phase (got {phases})"
    )
    assert meta.get("runtime") == "tools"


def test_oci_sweeper_declares_no_mcps() -> None:
    """Closed-by-default: oci-sweeper is a pure KG + reasoning skill, not an
    MCP consumer. The vendored FAR 9.5 reference replaces a live fetch."""
    mgr = SkillManager(_SKILLS_ROOT)
    skill = mgr.get_skill("oci-sweeper")
    assert skill is not None
    assert skill.frontmatter.runtime_mode == "tools"
    assert skill.frontmatter.required_mcps == [], (
        f"oci-sweeper should declare zero MCPs (closed-by-default). "
        f"Got {skill.frontmatter.required_mcps}"
    )


def test_oci_sweeper_body_covers_three_oci_classes() -> None:
    """FAR 9.505 enumerates exactly three OCI classes; the body MUST name them."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    body_lower = body.lower()
    assert "biased_ground_rules" in body_lower
    assert "unequal_access" in body_lower
    assert "impaired_objectivity" in body_lower
    # FAR section anchors
    assert "9.505-1" in body or "9.505-2" in body, "missing biased-ground-rules anchor"
    assert "9.505-3" in body, "missing impaired-objectivity anchor"
    assert "9.505-4" in body, "missing unequal-access anchor"


def test_oci_sweeper_body_invokes_runtime_tools() -> None:
    """Workflow checklist must drive the right tools (kg_entities, kg_query,
    kg_chunks, read_file, write_file). Missing any of these means the skill
    is not actually doing the work the description promises."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    for tool in ("kg_entities", "kg_query", "kg_chunks", "read_file", "write_file"):
        assert tool in body, (
            f"oci-sweeper SKILL.md body does not invoke `{tool}`; the "
            f"workflow checklist is incomplete"
        )


def test_oci_sweeper_references_exist_and_nonempty() -> None:
    expected = [
        "far_9_5_oci_taxonomy.md",
        "oci_remediation_playbook.md",
        "relationship_query_patterns.md",
    ]
    for name in expected:
        path = _REFS_DIR / name
        assert path.is_file(), f"missing reference: {path}"
        assert path.stat().st_size > 500, (
            f"{name} is suspiciously small ({path.stat().st_size} bytes); "
            f"reference appears to be a stub"
        )


def test_oci_sweeper_far_taxonomy_reference_lists_three_classes() -> None:
    text = (_REFS_DIR / "far_9_5_oci_taxonomy.md").read_text(encoding="utf-8")
    for token in (
        "biased_ground_rules",
        "unequal_access",
        "impaired_objectivity",
        "9.505-1",
        "9.505-2",
        "9.505-3",
        "9.505-4",
    ):
        assert token in text, f"FAR taxonomy reference missing `{token}`"


def test_oci_sweeper_remediation_playbook_lists_six_patterns() -> None:
    text = (_REFS_DIR / "oci_remediation_playbook.md").read_text(encoding="utf-8")
    for pattern in (
        "firewall",
        "nda",
        "recusal",
        "divestiture",
        "novation",
        "no_acceptable_mitigation",
    ):
        assert pattern in text, f"mitigation pattern `{pattern}` missing from playbook"


def test_oci_sweeper_evals_cover_three_oci_classes() -> None:
    payload = json.loads(_EVALS.read_text(encoding="utf-8"))
    evals = payload.get("evals", [])
    assert len(evals) >= 3, (
        f"oci-sweeper needs at least 3 evals (one per FAR 9.505 class); got {len(evals)}"
    )
    # Concatenate signals + prompts to verify class coverage.
    haystack = json.dumps(evals).lower()
    assert "impaired objectivity" in haystack or "impaired_objectivity" in haystack
    assert "biased ground rules" in haystack or "biased_ground_rules" in haystack
    assert "unequal access" in haystack or "unequal_access" in haystack
    # Each eval must have an `expectations` block — that's what the runtime
    # judges against in the future eval harness.
    for ev in evals:
        assert ev.get("id"), "eval missing id"
        assert ev.get("prompt"), f"eval {ev.get('id')} missing prompt"
        assert ev.get("expectations"), (
            f"eval {ev.get('id')} missing expectations block"
        )


def test_oci_sweeper_discoverable_via_skill_manager() -> None:
    mgr = SkillManager(_SKILLS_ROOT)
    summaries = mgr.list_skills()
    names = [s.get("name") for s in summaries]
    assert "oci-sweeper" in names, (
        f"oci-sweeper not discovered by SkillManager.list_skills(); got {names}"
    )
    skill = mgr.get_skill("oci-sweeper")
    assert skill is not None
    summary = skill.to_summary()
    # Phase 4j: to_summary() must surface the four taxonomy fields the UI consumes.
    assert summary.get("personas_primary") == "legal_compliance"
    assert summary.get("capability") == "audit"
    assert isinstance(summary.get("personas_secondary"), list)
    assert isinstance(summary.get("shipley_phases"), list)
