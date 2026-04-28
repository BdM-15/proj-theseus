"""Phase 4f.7 — bls-oews MCP manifest + live handshake tests.

Mirrors `test_sam_gov_manifest.py`. 3 offline tests + 1 live handshake gated on
THESEUS_LIVE_MCP=1 AND BLS_API_KEY available (auto-loaded from .env via dotenv).
"""

from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "tools" / "mcps" / "bls_oews" / "theseus_manifest.json"


def _api_key_present() -> bool:
    """Auto-load .env then check for BLS_API_KEY."""
    if os.environ.get("BLS_API_KEY"):
        return True
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        return False
    return bool(os.environ.get("BLS_API_KEY"))


def test_bls_oews_manifest_exists() -> None:
    assert MANIFEST_PATH.is_file(), f"Manifest missing at {MANIFEST_PATH}"


def test_bls_oews_manifest_parses() -> None:
    from src.skills.mcp_client import load_manifest

    manifest = load_manifest(MANIFEST_PATH)
    assert manifest.name == "bls_oews"
    assert manifest.command[:2] == ["uvx", "--from"]
    assert "bls-oews-mcp==0.2.7" in manifest.command
    assert manifest.env_required == ["BLS_API_KEY"]

    # missing_env behavior: with no BLS_API_KEY in the supplied env, it must report it;
    # with the key present, the list is empty.
    assert manifest.missing_env({}) == ["BLS_API_KEY"]
    assert manifest.missing_env({"BLS_API_KEY": "x"}) == []


def test_bls_oews_discovered_by_registry() -> None:
    from src.skills.mcp_client import discover_manifests

    manifests = discover_manifests(REPO_ROOT / "tools" / "mcps")
    assert "bls_oews" in manifests, (
        f"discover_manifests did not find bls_oews; found: {sorted(manifests)}"
    )
    assert manifests["bls_oews"].env_required == ["BLS_API_KEY"]


@pytest.mark.skipif(
    os.environ.get("THESEUS_LIVE_MCP") != "1",
    reason="Set THESEUS_LIVE_MCP=1 to enable live MCP handshake tests.",
)
@pytest.mark.skipif(
    not _api_key_present(),
    reason="BLS_API_KEY not set in environment (or .env).",
)
def test_bls_oews_live_handshake_and_tools_list() -> None:
    """Spawn the real bls-oews-mcp via uvx and verify advertised tool names."""
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

    # Upstream advertised 7 tools at vendor time. Allow growth, fail on regression.
    assert len(tool_names) >= 5, f"Expected >=5 tools, got {len(tool_names)}: {tool_names}"

    marquee = {
        "get_wage_data",
        "compare_metros",
        "compare_occupations",
        "igce_wage_benchmark",
        "detect_latest_year",
        "list_common_soc_codes",
        "list_common_metros",
    }
    missing = marquee - set(tool_names)
    assert not missing, f"Marquee tools missing: {missing}; advertised: {tool_names}"
