"""Phase 4f.6 smoke tests for the vendored SAM.gov MCP manifest.

Two layers (mirrors ``test_federal_register_manifest.py``, with a third
guard for the API key since this is the first key-gated MCP):

1. **Always-on**: parse the manifest, confirm discovery picks it up,
   confirm the schema is sane and declares ``SAM_GOV_API_KEY`` as
   required. Pure offline; runs in CI.

2. **Opt-in (live)**: actually spawn the upstream server via ``uvx`` and
   handshake through ``MCPSession``. Gated on ``THESEUS_LIVE_MCP=1``
   AND a non-empty ``SAM_GOV_API_KEY`` in the process environment.
   Loads ``.env`` if present (pytest does not auto-load it).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from src.skills.mcp_client import (
    MCPRegistry,
    MCPSession,
    discover_manifests,
    load_manifest,
)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_MCPS_ROOT = _REPO_ROOT / "tools" / "mcps"
_SG_DIR = _MCPS_ROOT / "sam_gov"
_SG_MANIFEST = _SG_DIR / "theseus_manifest.json"


def _run(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Layer 1 — offline manifest sanity (always runs)
# ---------------------------------------------------------------------------


def test_sam_gov_manifest_exists() -> None:
    assert _SG_MANIFEST.is_file(), f"missing vendored manifest at {_SG_MANIFEST}"


def test_sam_gov_manifest_parses() -> None:
    manifest = load_manifest(_SG_MANIFEST)
    # Manifest name uses underscore for skill frontmatter consistency
    # (`metadata.mcps: ["sam_gov"]`); upstream package + script use hyphens.
    assert manifest.name == "sam_gov"
    assert manifest.command[0] == "uvx"
    assert "--from" in manifest.command
    assert any(c.startswith("sam-gov-mcp==") for c in manifest.command)
    assert manifest.command[-1] == "sam-gov-mcp"
    # First key-gated MCP — must declare the env requirement so the runtime
    # surfaces a clean error instead of a cryptic upstream traceback.
    assert manifest.env_required == ["SAM_GOV_API_KEY"]
    assert manifest.env_optional == []
    # missing_env() against an empty scope must report the key as missing.
    assert manifest.missing_env({}) == ["SAM_GOV_API_KEY"]
    # And against a populated scope must return [].
    assert manifest.missing_env({"SAM_GOV_API_KEY": "x"}) == []
    assert manifest.license == "MIT"
    assert manifest.cwd == _SG_DIR.resolve()


def test_sam_gov_discovered_by_registry() -> None:
    manifests = discover_manifests(_MCPS_ROOT)
    assert "sam_gov" in manifests, (
        f"discover_manifests({_MCPS_ROOT}) did not find sam_gov; "
        f"found: {sorted(manifests)}"
    )


# ---------------------------------------------------------------------------
# Layer 2 — live integration (opt-in, key-gated)
# ---------------------------------------------------------------------------


_LIVE = os.environ.get("THESEUS_LIVE_MCP") == "1"


def _api_key_present() -> bool:
    """Return True if SAM_GOV_API_KEY is in env (loading .env first if present)."""
    if os.environ.get("SAM_GOV_API_KEY"):
        return True
    env_file = _REPO_ROOT / ".env"
    if env_file.is_file():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
        except Exception:
            return False
    return bool(os.environ.get("SAM_GOV_API_KEY"))


@pytest.mark.skipif(
    not _LIVE,
    reason="set THESEUS_LIVE_MCP=1 to run live MCP integration (spawns uvx, hits PyPI)",
)
@pytest.mark.skipif(
    not _api_key_present(),
    reason="SAM_GOV_API_KEY not set (in env or .env); upstream handshake will fail",
)
def test_sam_gov_live_handshake_and_tools_list() -> None:
    """End-to-end: registry → uvx subprocess → MCP initialize → tools/list."""

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        sessions = await registry.start_run_sessions(
            run_id="phase4f6-smoke",
            requested=["sam_gov"],
        )
        try:
            assert "sam_gov" in sessions, (
                "registry failed to start the sam_gov session "
                "(check `mcp.sam_gov` log child for upstream stderr)"
            )
            session: MCPSession = sessions["sam_gov"]
            tools = session.tools
            # Upstream advertises 19 tools at v0.4.1; require the marquee ones
            # that downstream skills (competitive-intel, capture, compliance)
            # will depend on across all four data domains.
            assert len(tools) >= 15, f"expected 15+ tools, got {len(tools)}"
            tool_names = {t.name for t in tools}
            for required in (
                # Entity Registration
                "lookup_entity_by_uei",
                "search_entities",
                # Exclusions
                "check_exclusion_by_uei",
                # Opportunities
                "search_opportunities",
                "get_opportunity_description",
                # FPDS-NG Awards (consolidated into sam-gov-mcp)
                "search_contract_awards",
                "lookup_award_by_piid",
                # PSC
                "lookup_psc_code",
            ):
                assert required in tool_names, (
                    f"upstream missing expected tool {required!r}; "
                    f"got: {sorted(tool_names)[:10]}…"
                )
        finally:
            await registry.shutdown_run("phase4f6-smoke")
            await registry.shutdown_all()

    _run(_go())
