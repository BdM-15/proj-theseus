"""Phase 4h contract tests for the subcontractor-sow-builder skill.

Mirrors test_price_to_win_skill.py pattern, with two key differences:

1. This skill declares NO MCPs (closed-by-default). The "live MCP drift" layer
   from price-to-win is omitted.
2. The body invariants are SOW/PWS-specific: 14-section spec, Phase 1 decision
   summary gate, FAR 37.102(d) discipline, etc.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from dotenv import load_dotenv

# Load repo .env so any KG-dependent runs can pick up Neo4j creds.
load_dotenv()

from src.skills.manager import SkillManager


_REPO_ROOT = Path(__file__).resolve().parents[2]
_SKILLS_ROOT = _REPO_ROOT / ".github" / "skills"
_SKILL_DIR = _SKILLS_ROOT / "subcontractor-sow-builder"
_SKILL_MD = _SKILL_DIR / "SKILL.md"
_EVALS = _SKILL_DIR / "evals" / "evals.json"
_REFERENCES_DIR = _SKILL_DIR / "references"

_ALLOWED_FRONTMATTER_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}

_REQUIRED_REFERENCES = [
    "sow_pws_section_structure.md",
    "decision_tree_blocks.md",
    "far_citations.md",
    "language_rules.md",
]


def _read_frontmatter_and_body(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise AssertionError(f"{path} missing YAML frontmatter")
    _, fm_text, body = text.split("---", 2)
    return yaml.safe_load(fm_text), body


# ---------------------------------------------------------------------------
# Layer 1 — offline spec + body invariants (always runs)
# ---------------------------------------------------------------------------


def test_subcontractor_sow_builder_frontmatter_is_spec_compliant() -> None:
    fm, _ = _read_frontmatter_and_body(_SKILL_MD)
    extra = set(fm) - _ALLOWED_FRONTMATTER_FIELDS
    assert not extra, (
        f"subcontractor-sow-builder SKILL.md has non-spec top-level frontmatter "
        f"fields: {extra}. Move them under `metadata:`."
    )
    assert fm["name"] == "subcontractor-sow-builder"
    assert len(fm["description"]) <= 1024, (
        f"description is {len(fm['description'])} chars (spec max 1024)"
    )
    assert "USE WHEN" in fm["description"]
    assert "DO NOT USE FOR" in fm["description"]


def test_subcontractor_sow_builder_declares_no_mcps() -> None:
    """This skill is closed-by-default — purely KG + reference-driven."""
    mgr = SkillManager(_SKILLS_ROOT)
    skill = mgr.get_skill("subcontractor-sow-builder")
    assert skill is not None
    assert skill.frontmatter.runtime_mode == "tools"
    assert not skill.frontmatter.required_mcps, (
        f"subcontractor-sow-builder must NOT declare MCPs; got "
        f"{skill.frontmatter.required_mcps}"
    )


def test_subcontractor_sow_builder_body_has_14_section_markers() -> None:
    """The skill body or referenced spec must enumerate all 14 sections.
    The body refers to them by name across the workflow; if the markers
    disappear the skill has regressed to a generic doc generator."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    # Critical FAR / discipline markers
    for marker in (
        "FAR 37.102(d)",
        "FAR 16.306(d)(1)",
        "FAR 16.306(d)(2)",
        "FAR 52.237-2",
        "Section 5",
        "Section 12",
        "QASP",
        "CPARS",
        "Decision Summary",
        "Staffing Handoff",
        "CLIN Handoff",
        "sub_sow_pws.md",
    ):
        assert marker in body, (
            f"SKILL.md body missing required marker '{marker}' — skill has "
            f"regressed away from the SOW/PWS discipline"
        )


def test_subcontractor_sow_builder_section_spec_enumerates_all_14_sections() -> None:
    spec = (_REFERENCES_DIR / "sow_pws_section_structure.md").read_text(encoding="utf-8")
    for n in range(1, 15):
        assert f"## Section {n} " in spec or f"## Section {n} —" in spec, (
            f"references/sow_pws_section_structure.md missing 'Section {n}' header"
        )


def test_subcontractor_sow_builder_references_exist() -> None:
    for ref in _REQUIRED_REFERENCES:
        path = _REFERENCES_DIR / ref
        assert path.exists(), (
            f"missing required reference: {path.relative_to(_REPO_ROOT)}"
        )
        text = path.read_text(encoding="utf-8")
        assert len(text) > 500, f"{ref} suspiciously short ({len(text)} chars)"


def test_subcontractor_sow_builder_body_references_no_fake_mcps() -> None:
    """Skill declares no MCPs; ensure body doesn't sneak any in."""
    _, body = _read_frontmatter_and_body(_SKILL_MD)
    assert "mcp__" not in body, (
        "subcontractor-sow-builder body references mcp__<server>__<tool> but "
        "declares no MCPs — fix one or the other"
    )


def test_subcontractor_sow_builder_evals_exercise_key_branches() -> None:
    """Each cost-relevant branch (CPFF form, T&M Section 5, FFP commercial)
    must have at least one eval."""
    data = json.loads(_EVALS.read_text(encoding="utf-8"))
    evals = data["evals"]
    assert len(evals) >= 3, f"expected at least 3 evals, got {len(evals)}"

    all_text = json.dumps(evals).lower()
    for branch_marker in ("cpff", "t&m", "ffp"):
        assert branch_marker in all_text, (
            f"evals do not exercise the '{branch_marker}' branch"
        )

    # Each eval must have expected_signals + anti_signals
    for e in evals:
        assert e.get("expected_signals"), f"eval {e.get('id')} missing expected_signals"
        assert e.get("anti_signals"), f"eval {e.get('id')} missing anti_signals"


def test_subcontractor_sow_builder_upstream_md_present() -> None:
    upstream = _SKILL_DIR / "UPSTREAM.md"
    assert upstream.exists(), "UPSTREAM.md missing — required for vendored skills"
    text = upstream.read_text(encoding="utf-8")
    assert "MIT" in text and "1102tools" in text, "UPSTREAM.md must cite MIT + 1102tools origin"
    assert "Stance-Inversion Contract" in text, "UPSTREAM.md must document the stance-inversion contract"
