"""Phase 4f.3 smoke tests for the vendored GSA CALC+ MCP manifest.

Two layers (mirrors ``test_usaspending_manifest.py`` and ``test_ecfr_manifest.py``):

1. **Always-on**: parse the manifest from disk, confirm discovery picks it
   up, confirm the schema is sane. Pure offline; runs in CI.

2. **Opt-in (live)**: actually spawn the upstream server via ``uvx`` and
   handshake through ``MCPSession``. Gated on ``THESEUS_LIVE_MCP=1`` so we
   don't hit PyPI (or the GSA CALC+ live API) on every test run.
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
_GSA_CALC_DIR = _MCPS_ROOT / "gsa_calc"
_GSA_CALC_MANIFEST = _GSA_CALC_DIR / "theseus_manifest.json"


def _run(coro):
    """Run an async coroutine on a fresh event loop (mirrors test_mcp_client.py)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Layer 1 — offline manifest sanity (always runs)
# ---------------------------------------------------------------------------


def test_gsa_calc_manifest_exists() -> None:
    assert _GSA_CALC_MANIFEST.is_file(), (
        f"missing vendored manifest at {_GSA_CALC_MANIFEST}"
    )


def test_gsa_calc_manifest_parses() -> None:
    manifest = load_manifest(_GSA_CALC_MANIFEST)
    # Manifest name uses underscore for skill frontmatter consistency
    # (`metadata.mcps: ["gsa_calc"]`); upstream server identifies itself as
    # `gsa-calc` (hyphen) in serverInfo.name — that's an upstream-internal
    # detail we don't surface to skills.
    assert manifest.name == "gsa_calc"
    # Package and console script names match for gsa-calc-mcp; we still use
    # `--from <pkg>==<ver>` for explicit version pinning.
    assert manifest.command[0] == "uvx"
    assert "--from" in manifest.command
    assert any(c.startswith("gsa-calc-mcp==") for c in manifest.command)
    assert manifest.command[-1] == "gsa-calc-mcp"
    # GSA CALC+ is a public API — must require zero env vars.
    assert manifest.env_required == []
    assert manifest.missing_env({}) == []
    assert manifest.license == "MIT"
    assert manifest.cwd == _GSA_CALC_DIR.resolve()


def test_gsa_calc_discovered_by_registry() -> None:
    manifests = discover_manifests(_MCPS_ROOT)
    assert "gsa_calc" in manifests, (
        f"discover_manifests({_MCPS_ROOT}) did not find gsa_calc; "
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
def test_gsa_calc_live_handshake_and_tools_list() -> None:
    """End-to-end: registry → uvx subprocess → MCP initialize → tools/list."""

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        startup = await registry.start_run_sessions(
            run_id="phase4f3-smoke",
            requested=["gsa_calc"],
        )
        try:
            sessions = startup.sessions
            assert "gsa_calc" in sessions, (
                "registry failed to start the gsa_calc session "
                "(check `mcp.gsa_calc` log child for upstream stderr)"
            )
            session: MCPSession = sessions["gsa_calc"]
            tools = session.tools
            # Upstream advertises 8 tools at v0.2.7; require non-empty + the
            # workflow tools (which are the highest-leverage for capture work)
            # are present.
            assert len(tools) >= 6, f"expected 6+ tools, got {len(tools)}"
            tool_names = {t.name for t in tools}
            for required in (
                "igce_benchmark",
                "price_reasonableness_check",
                "vendor_rate_card",
                "sin_analysis",
            ):
                assert required in tool_names, (
                    f"upstream missing expected tool {required!r}; "
                    f"got: {sorted(tool_names)[:10]}…"
                )
        finally:
            await registry.shutdown_run("phase4f3-smoke")
            await registry.shutdown_all()

    _run(_go())
