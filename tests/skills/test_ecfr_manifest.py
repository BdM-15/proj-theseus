"""Phase 4f smoke tests for the vendored eCFR MCP manifest.

Two layers (mirrors ``test_usaspending_manifest.py``):

1. **Always-on**: parse the manifest from disk, confirm discovery picks it
   up, confirm the schema is sane. Pure offline; runs in CI.

2. **Opt-in (live)**: actually spawn the upstream server via ``uvx`` and
   handshake through ``MCPSession``. Gated on ``THESEUS_LIVE_MCP=1`` so we
   don't hit PyPI (or the eCFR live API) on every test run.
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
_ECFR_DIR = _MCPS_ROOT / "ecfr"
_ECFR_MANIFEST = _ECFR_DIR / "theseus_manifest.json"


def _run(coro):
    """Run an async coroutine on a fresh event loop (mirrors test_mcp_client.py)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Layer 1 — offline manifest sanity (always runs)
# ---------------------------------------------------------------------------


def test_ecfr_manifest_exists() -> None:
    assert _ECFR_MANIFEST.is_file(), (
        f"missing vendored manifest at {_ECFR_MANIFEST}"
    )


def test_ecfr_manifest_parses() -> None:
    manifest = load_manifest(_ECFR_MANIFEST)
    assert manifest.name == "ecfr"
    # Package and console script names match for ecfr-mcp; we still use
    # `--from <pkg>==<ver>` for explicit version pinning.
    assert manifest.command[0] == "uvx"
    assert "--from" in manifest.command
    assert any(c.startswith("ecfr-mcp==") for c in manifest.command)
    assert manifest.command[-1] == "ecfr-mcp"
    # eCFR is a public API — must require zero env vars.
    assert manifest.env_required == []
    assert manifest.missing_env({}) == []
    assert manifest.license == "MIT"
    assert manifest.cwd == _ECFR_DIR.resolve()


def test_ecfr_discovered_by_registry() -> None:
    manifests = discover_manifests(_MCPS_ROOT)
    assert "ecfr" in manifests, (
        f"discover_manifests({_MCPS_ROOT}) did not find ecfr; "
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
def test_ecfr_live_handshake_and_tools_list() -> None:
    """End-to-end: registry → uvx subprocess → MCP initialize → tools/list."""

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        startup = await registry.start_run_sessions(
            run_id="phase4f-smoke",
            requested=["ecfr"],
        )
        try:
            sessions = startup.sessions
            assert "ecfr" in sessions, (
                "registry failed to start the ecfr session "
                "(check `mcp.ecfr` log child for upstream stderr)"
            )
            session: MCPSession = sessions["ecfr"]
            tools = session.tools
            # Upstream advertises 13 tools at v0.2.6; allow modest drift but
            # require non-empty + the marquee tools are present.
            assert len(tools) >= 10, f"expected 10+ tools, got {len(tools)}"
            tool_names = {t.name for t in tools}
            for required in (
                "lookup_far_clause",
                "search_cfr",
                "get_cfr_content",
                "list_sections_in_part",
            ):
                assert required in tool_names, (
                    f"upstream missing expected tool {required!r}; "
                    f"got: {sorted(tool_names)[:10]}…"
                )
        finally:
            await registry.shutdown_run("phase4f-smoke")
            await registry.shutdown_all()

    _run(_go())
