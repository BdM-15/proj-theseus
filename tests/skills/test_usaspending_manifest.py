"""Phase 4c smoke tests for the vendored USAspending MCP manifest.

Two layers:

1. **Always-on**: parse the manifest from disk, confirm discovery picks it
   up, confirm the schema is sane. Pure offline; runs in CI.

2. **Opt-in (live)**: actually spawn the upstream server via ``uvx`` and
   handshake through ``MCPSession``. Gated on ``THESEUS_LIVE_MCP=1`` so we
   don't hit PyPI (or the USASpending live API) on every test run.
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
_USASPENDING_DIR = _MCPS_ROOT / "usaspending"
_USASPENDING_MANIFEST = _USASPENDING_DIR / "theseus_manifest.json"


def _run(coro):
    """Run an async coroutine on a fresh event loop (mirrors test_mcp_client.py)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Layer 1 — offline manifest sanity (always runs)
# ---------------------------------------------------------------------------


def test_usaspending_manifest_exists() -> None:
    assert _USASPENDING_MANIFEST.is_file(), (
        f"missing vendored manifest at {_USASPENDING_MANIFEST}"
    )


def test_usaspending_manifest_parses() -> None:
    manifest = load_manifest(_USASPENDING_MANIFEST)
    assert manifest.name == "usaspending"
    # Console script is `usaspending-mcp` (no -gov-); package is `usaspending-gov-mcp`.
    # Manifest must use `uvx --from <pkg> <script>` to bridge the mismatch.
    assert manifest.command[0] == "uvx"
    assert "--from" in manifest.command
    assert any(c.startswith("usaspending-gov-mcp") for c in manifest.command)
    assert manifest.command[-1] == "usaspending-mcp"
    # USASpending is a public API — must require zero env vars.
    assert manifest.env_required == []
    assert manifest.missing_env({}) == []
    assert manifest.license == "MIT"
    assert manifest.cwd == _USASPENDING_DIR.resolve()


def test_usaspending_discovered_by_registry() -> None:
    manifests = discover_manifests(_MCPS_ROOT)
    assert "usaspending" in manifests, (
        f"discover_manifests({_MCPS_ROOT}) did not find usaspending; "
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
def test_usaspending_live_handshake_and_tools_list() -> None:
    """End-to-end: registry → uvx subprocess → MCP initialize → tools/list."""

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        sessions = await registry.start_run_sessions(
            run_id="phase4c-smoke",
            requested=["usaspending"],
        )
        try:
            assert "usaspending" in sessions, (
                "registry failed to start the usaspending session "
                "(check `mcp.usaspending` log child for upstream stderr)"
            )
            session: MCPSession = sessions["usaspending"]
            tools = session.tools
            # Upstream advertises 55 tools at v0.3.2; allow drift but require
            # the contract is non-empty and the marquee tools are present.
            assert len(tools) >= 30, f"expected 30+ tools, got {len(tools)}"
            tool_names = {t.name for t in tools}
            for required in ("search_awards", "spending_by_category", "get_award_detail"):
                assert required in tool_names, (
                    f"upstream missing expected tool {required!r}; "
                    f"got: {sorted(tool_names)[:10]}…"
                )
        finally:
            await registry.shutdown_run("phase4c-smoke")
            await registry.shutdown_all()

    _run(_go())
