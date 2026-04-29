"""Phase 4e contract tests for the MCP Servers Settings panel routes.

Three layers, mirroring the manifest-test convention:

1. **List**: ``GET /api/ui/mcps`` returns every vendored manifest under
   ``tools/mcps/`` with env-var status + provenance.
2. **Save-keys validation**: ``POST /api/ui/mcps/{name}/keys`` refuses
   env vars not declared by the manifest (security: route cannot be used
   as a generic ``.env`` writer). The actual write path is exercised via
   monkey-patched ``_set_env_var`` so the test never touches the real
   ``.env``.
3. **Test connection (live, opt-in)**: ``POST /api/ui/mcps/{name}/test``
   spawns a real subprocess against the ecfr no-key MCP and asserts the
   handshake returns ``ok: true`` with a non-empty tool list. Gated on
   ``THESEUS_LIVE_MCP=1`` for parity with the other live MCP tests.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


_REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Build a minimal FastAPI app with the UI routes mounted.

    The query/data/llm funcs are no-op stubs — the MCP routes don't
    invoke them, so this is sufficient. We do NOT mount the LightRAG
    create_app stack; only ``register_ui`` is wired.
    """
    from src.server.ui_routes import register_ui

    app = FastAPI()

    async def _stub_query(*_args, **_kwargs):  # pragma: no cover - never called
        return ""

    register_ui(app, query_func=_stub_query)
    return TestClient(app)


# ---------------------------------------------------------------------------
# Layer 1 — list endpoint
# ---------------------------------------------------------------------------


def test_list_mcps_returns_vendored_inventory(client: TestClient) -> None:
    resp = client.get("/api/ui/mcps")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "mcps" in body
    names = {m["name"] for m in body["mcps"]}
    # All five no-key MCPs vendored through Phase 4f.5 must surface.
    expected = {"usaspending", "ecfr", "gsa_calc", "gsa_perdiem", "federal_register"}
    assert expected.issubset(names), f"missing MCPs: {expected - names}"


def test_list_mcps_includes_env_status_and_provenance(client: TestClient) -> None:
    resp = client.get("/api/ui/mcps")
    body = resp.json()
    by_name = {m["name"]: m for m in body["mcps"]}

    # gsa_perdiem declares one optional env var; the entry must have the
    # `set`/`masked` shape regardless of whether the operator has set it.
    perdiem = by_name["gsa_perdiem"]
    assert any(
        e["name"] == "PERDIEM_API_KEY" and "set" in e and "masked" in e
        for e in perdiem["env_optional"]
    )
    # No-key MCPs have empty env_required.
    assert perdiem["env_required"] == []
    # Provenance is surfaced for the UI's "Vendored from" line.
    assert perdiem["vendored_from"].startswith("https://github.com/")
    assert perdiem["vendored_commit"]
    assert perdiem["license"] == "MIT"


# ---------------------------------------------------------------------------
# Layer 2 — save-keys validation (no .env writes)
# ---------------------------------------------------------------------------


def test_update_keys_rejects_undeclared_env_vars(client: TestClient) -> None:
    """Endpoint must refuse env vars the MCP did not declare."""
    resp = client.post(
        "/api/ui/mcps/gsa_perdiem/keys",
        json={"keys": {"NOT_A_DECLARED_KEY": "value"}, "restart": False},
    )
    assert resp.status_code == 400
    assert "Keys not declared" in resp.text


def test_update_keys_rejects_unknown_mcp(client: TestClient) -> None:
    resp = client.post(
        "/api/ui/mcps/no_such_mcp/keys",
        json={"keys": {}, "restart": False},
    )
    assert resp.status_code == 404


def test_update_keys_rejects_no_env_mcp(client: TestClient) -> None:
    """ecfr declares no env vars at all — endpoint should refuse the call."""
    resp = client.post(
        "/api/ui/mcps/ecfr/keys",
        json={"keys": {}, "restart": False},
    )
    assert resp.status_code == 400
    assert "no env vars" in resp.text


def test_update_keys_writes_only_allowed_keys(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Happy path with a stubbed _set_env_var so the real .env stays untouched."""
    written: dict[str, str] = {}

    def _fake_set_env_var(key: str, value: str) -> None:
        written[key] = value

    monkeypatch.setattr("src.server.ui_routes._set_env_var", _fake_set_env_var)
    resp = client.post(
        "/api/ui/mcps/gsa_perdiem/keys",
        json={"keys": {"PERDIEM_API_KEY": "test-value-xyz"}, "restart": False},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "saved"
    assert body["written"] == ["PERDIEM_API_KEY"]
    assert written == {"PERDIEM_API_KEY": "test-value-xyz"}


# ---------------------------------------------------------------------------
# Layer 3 — test-connection (live subprocess; opt-in)
# ---------------------------------------------------------------------------

_LIVE = os.environ.get("THESEUS_LIVE_MCP") == "1"


@pytest.mark.skipif(not _LIVE, reason="THESEUS_LIVE_MCP=1 not set")
def test_test_connection_against_ecfr(client: TestClient) -> None:
    """Real handshake against the vendored ecfr MCP. No API key needed."""
    resp = client.post("/api/ui/mcps/ecfr/test")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body.get("ok") is True, body
    assert body["mcp"] == "ecfr"
    assert body["tool_count"] >= 6, body
    assert body["sample_tools"]
