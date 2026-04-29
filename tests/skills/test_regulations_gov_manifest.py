"""Phase 4f.8 — regulations-gov MCP manifest + live handshake tests.

Mirrors `test_bls_oews_manifest.py`. 3 offline tests + 1 live handshake gated on
THESEUS_LIVE_MCP=1 AND API_DATA_GOV_KEY available (auto-loaded from .env).
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "tools" / "mcps" / "regulations_gov" / "theseus_manifest.json"


def _api_key_present() -> bool:
    """Auto-load .env then check for API_DATA_GOV_KEY."""
    if os.environ.get("API_DATA_GOV_KEY"):
        return True
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        return False
    return bool(os.environ.get("API_DATA_GOV_KEY"))


def test_regulations_gov_manifest_exists() -> None:
    assert MANIFEST_PATH.is_file(), f"Manifest missing at {MANIFEST_PATH}"


def test_regulations_gov_manifest_parses() -> None:
    from src.skills.mcp_client import load_manifest

    manifest = load_manifest(MANIFEST_PATH)
    assert manifest.name == "regulations_gov"
    assert manifest.command[:2] == ["uvx", "--from"]
    assert "regulationsgov-mcp==0.2.5" in manifest.command
    assert manifest.env_required == ["API_DATA_GOV_KEY"]

    assert manifest.missing_env({}) == ["API_DATA_GOV_KEY"]
    assert manifest.missing_env({"API_DATA_GOV_KEY": "x"}) == []


def test_regulations_gov_discovered_by_registry() -> None:
    from src.skills.mcp_client import discover_manifests

    manifests = discover_manifests(REPO_ROOT / "tools" / "mcps")
    assert "regulations_gov" in manifests, (
        f"discover_manifests did not find regulations_gov; found: {sorted(manifests)}"
    )
    assert manifests["regulations_gov"].env_required == ["API_DATA_GOV_KEY"]


@pytest.mark.skipif(
    os.environ.get("THESEUS_LIVE_MCP") != "1",
    reason="Set THESEUS_LIVE_MCP=1 to enable live MCP handshake tests.",
)
@pytest.mark.skipif(
    not _api_key_present(),
    reason="API_DATA_GOV_KEY not set in environment (or .env).",
)
def test_regulations_gov_live_handshake_and_tools_list() -> None:
    """Spawn the real regulationsgov-mcp via uvx and verify advertised tool names."""
    from src.skills.mcp_client import MCPSession, load_manifest

    manifest = load_manifest(MANIFEST_PATH)

    async def go() -> list[str]:
        session = MCPSession(manifest)
        await session.start()
        try:
            return [t.name for t in session.tools]
        finally:
            await session.shutdown()

    tool_names = asyncio.run(go())

    assert len(tool_names) >= 6, f"Expected >=6 tools, got {len(tool_names)}: {tool_names}"

    marquee = {
        "search_documents",
        "get_document_detail",
        "search_comments",
        "get_comment_detail",
        "search_dockets",
        "get_docket_detail",
        "open_comment_periods",
        "far_case_history",
    }
    missing = marquee - set(tool_names)
    assert not missing, f"Marquee tools missing: {missing}; advertised: {tool_names}"
