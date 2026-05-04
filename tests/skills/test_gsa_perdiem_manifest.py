"""Phase 4f.4 smoke tests for the vendored GSA Per Diem MCP manifest.

Two layers (mirrors ``test_gsa_calc_manifest.py`` and ``test_ecfr_manifest.py``):

1. **Always-on**: parse the manifest from disk, confirm discovery picks it
   up, confirm the schema is sane. Pure offline; runs in CI.

2. **Opt-in (live)**: actually spawn the upstream server via ``uvx`` and
   handshake through ``MCPSession``. Gated on ``THESEUS_LIVE_MCP=1``. The
   handshake itself doesn't hit the GSA API, so DEMO_KEY mode is fine for
   smoke testing — actual tool invocation against the live API is left to
   downstream skill-level tests.
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
_GSA_PERDIEM_DIR = _MCPS_ROOT / "gsa_perdiem"
_GSA_PERDIEM_MANIFEST = _GSA_PERDIEM_DIR / "theseus_manifest.json"


def _run(coro):
    """Run an async coroutine on a fresh event loop (mirrors test_mcp_client.py)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Layer 1 — offline manifest sanity (always runs)
# ---------------------------------------------------------------------------


def test_gsa_perdiem_manifest_exists() -> None:
    assert _GSA_PERDIEM_MANIFEST.is_file(), (
        f"missing vendored manifest at {_GSA_PERDIEM_MANIFEST}"
    )


def test_gsa_perdiem_manifest_parses() -> None:
    manifest = load_manifest(_GSA_PERDIEM_MANIFEST)
    # Manifest name uses underscore for skill frontmatter consistency
    # (`metadata.mcps: ["gsa_perdiem"]`); upstream server identifies itself as
    # `gsa-perdiem` (hyphen) in serverInfo.name.
    assert manifest.name == "gsa_perdiem"
    assert manifest.command[0] == "uvx"
    assert "--from" in manifest.command
    assert any(c.startswith("gsa-perdiem-mcp==") for c in manifest.command)
    assert manifest.command[-1] == "gsa-perdiem-mcp"
    # No required env (DEMO_KEY mode supported); PERDIEM_API_KEY is optional
    # for the 1,000 req/hr tier.
    assert manifest.env_required == []
    assert manifest.env_optional == ["PERDIEM_API_KEY"]
    assert manifest.missing_env({}) == []
    assert manifest.license == "MIT"
    assert manifest.cwd == _GSA_PERDIEM_DIR.resolve()


def test_gsa_perdiem_discovered_by_registry() -> None:
    manifests = discover_manifests(_MCPS_ROOT)
    assert "gsa_perdiem" in manifests, (
        f"discover_manifests({_MCPS_ROOT}) did not find gsa_perdiem; "
        f"found: {sorted(manifests)}"
    )


# ---------------------------------------------------------------------------
# Layer 2 — live integration (opt-in)
# ---------------------------------------------------------------------------


_LIVE = os.environ.get("THESEUS_LIVE_MCP") == "1"


@pytest.mark.skipif(
    not _LIVE,
    reason="set THESEUS_LIVE_MCP=1 to run live MCP integration (spawns uvx, hits PyPI)",
)
def test_gsa_perdiem_live_handshake_and_tools_list() -> None:
    """End-to-end: registry → uvx subprocess → MCP initialize → tools/list."""

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        startup = await registry.start_run_sessions(
            run_id="phase4f4-smoke",
            requested=["gsa_perdiem"],
        )
        try:
            sessions = startup.sessions
            assert "gsa_perdiem" in sessions, (
                "registry failed to start the gsa_perdiem session "
                "(check `mcp.gsa_perdiem` log child for upstream stderr)"
            )
            session: MCPSession = sessions["gsa_perdiem"]
            tools = session.tools
            # Upstream advertises 6 tools at v0.2.6; require all the marquee
            # ones that downstream skills (travel-cost estimation, IGCE) will
            # depend on.
            assert len(tools) >= 4, f"expected 4+ tools, got {len(tools)}"
            tool_names = {t.name for t in tools}
            for required in (
                "lookup_city_perdiem",
                "lookup_zip_perdiem",
                "estimate_travel_cost",
                "compare_locations",
            ):
                assert required in tool_names, (
                    f"upstream missing expected tool {required!r}; "
                    f"got: {sorted(tool_names)[:10]}…"
                )
        finally:
            await registry.shutdown_run("phase4f4-smoke")
            await registry.shutdown_all()

    _run(_go())
