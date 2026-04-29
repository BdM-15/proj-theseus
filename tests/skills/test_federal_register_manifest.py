"""Phase 4f.5 smoke tests for the vendored Federal Register MCP manifest.

Two layers (mirrors ``test_gsa_perdiem_manifest.py`` and ``test_ecfr_manifest.py``):

1. **Always-on**: parse the manifest from disk, confirm discovery picks it
   up, confirm the schema is sane. Pure offline; runs in CI.

2. **Opt-in (live)**: actually spawn the upstream server via ``uvx`` and
   handshake through ``MCPSession``. Gated on ``THESEUS_LIVE_MCP=1``. The
   Federal Register API requires no auth, so the live test runs against the
   real endpoint via the handshake (no API call is actually issued for
   tools/list).
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
_FR_DIR = _MCPS_ROOT / "federal_register"
_FR_MANIFEST = _FR_DIR / "theseus_manifest.json"


def _run(coro):
    """Run an async coroutine on a fresh event loop (mirrors test_mcp_client.py)."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Layer 1 — offline manifest sanity (always runs)
# ---------------------------------------------------------------------------


def test_federal_register_manifest_exists() -> None:
    assert _FR_MANIFEST.is_file(), f"missing vendored manifest at {_FR_MANIFEST}"


def test_federal_register_manifest_parses() -> None:
    manifest = load_manifest(_FR_MANIFEST)
    # Manifest name uses underscore for skill frontmatter consistency
    # (`metadata.mcps: ["federal_register"]`); upstream server identifies
    # itself as `federal-register` (hyphen) in serverInfo.name.
    assert manifest.name == "federal_register"
    assert manifest.command[0] == "uvx"
    assert "--from" in manifest.command
    assert any(c.startswith("federal-register-mcp==") for c in manifest.command)
    assert manifest.command[-1] == "federal-register-mcp"
    # Federal Register API is fully public — no auth, no optional key.
    assert manifest.env_required == []
    assert manifest.env_optional == []
    assert manifest.missing_env({}) == []
    assert manifest.license == "MIT"
    assert manifest.cwd == _FR_DIR.resolve()


def test_federal_register_discovered_by_registry() -> None:
    manifests = discover_manifests(_MCPS_ROOT)
    assert "federal_register" in manifests, (
        f"discover_manifests({_MCPS_ROOT}) did not find federal_register; "
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
def test_federal_register_live_handshake_and_tools_list() -> None:
    """End-to-end: registry → uvx subprocess → MCP initialize → tools/list."""

    async def _go():
        registry = MCPRegistry.from_root(_MCPS_ROOT)
        sessions = await registry.start_run_sessions(
            run_id="phase4f5-smoke",
            requested=["federal_register"],
        )
        try:
            assert "federal_register" in sessions, (
                "registry failed to start the federal_register session "
                "(check `mcp.federal_register` log child for upstream stderr)"
            )
            session: MCPSession = sessions["federal_register"]
            tools = session.tools
            # Upstream advertises 8 tools at v0.2.7; require the marquee ones
            # that downstream skills (regulatory-watch, compliance-auditor)
            # will depend on.
            assert len(tools) >= 6, f"expected 6+ tools, got {len(tools)}"
            tool_names = {t.name for t in tools}
            for required in (
                "search_documents",
                "get_document",
                "list_agencies",
                "open_comment_periods",
                "far_case_history",
            ):
                assert required in tool_names, (
                    f"upstream missing expected tool {required!r}; "
                    f"got: {sorted(tool_names)[:10]}…"
                )
        finally:
            await registry.shutdown_run("phase4f5-smoke")
            await registry.shutdown_all()

    _run(_go())
