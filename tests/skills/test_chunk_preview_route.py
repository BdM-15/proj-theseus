"""Phase 6b.2 — contract tests for ``GET /api/ui/chunks/{chunk_id}``.

The endpoint is a pure read-only lookup over the active workspace's
``kv_store_text_chunks.json``. We exercise the FastAPI route directly
with ``TestClient`` and a temp workspace patched in via monkey-patching
the module-level ``_workspace_dir`` helper.

Coverage:
  * Happy path — chunk exists, payload echoes the on-disk fields.
  * 404 — workspace has the store but the id is unknown.
  * 404 — workspace has no store at all (fresh workspace).
  * 400 — id is malformed (path traversal, slashes, oversize).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


@pytest.fixture()
def client_factory(monkeypatch: pytest.MonkeyPatch):
    """Build a TestClient bound to an arbitrary workspace dir per test."""
    from src.server import ui_routes

    def _build(workspace: Path) -> TestClient:
        monkeypatch.setattr(ui_routes, "_workspace_dir", lambda: workspace)
        app = FastAPI()

        async def _stub_query(*_a, **_kw):  # pragma: no cover
            return ""

        ui_routes.register_ui(app, query_func=_stub_query)
        return TestClient(app)

    return _build


def test_chunk_preview_returns_payload(tmp_path: Path, client_factory) -> None:
    cid = "chunk-1b8a790d0500c50bb2b2b57ff70c810a"
    (tmp_path / "kv_store_text_chunks.json").write_text(
        json.dumps(
            {
                cid: {
                    "content": "FAR 52.215-1 INSTRUCTIONS TO OFFERORS — COMPETITIVE ACQUISITION.",
                    "file_path": "afcap5_drfp.pdf",
                    "full_doc_id": "doc-001",
                    "chunk_order_index": 12,
                    "tokens": 64,
                }
            }
        ),
        encoding="utf-8",
    )
    client = client_factory(tmp_path)
    resp = client.get(f"/api/ui/chunks/{cid}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["chunk_id"] == cid
    assert body["file_path"] == "afcap5_drfp.pdf"
    assert body["full_doc_id"] == "doc-001"
    assert body["chunk_order_index"] == 12
    assert body["tokens"] == 64
    assert body["length"] == len(body["content"])
    assert "FAR 52.215-1" in body["content"]


def test_chunk_preview_unknown_id_404(tmp_path: Path, client_factory) -> None:
    (tmp_path / "kv_store_text_chunks.json").write_text("{}", encoding="utf-8")
    client = client_factory(tmp_path)
    resp = client.get("/api/ui/chunks/chunk-deadbeefdeadbeef")
    assert resp.status_code == 404


def test_chunk_preview_no_store_404(tmp_path: Path, client_factory) -> None:
    # Fresh workspace — no kv_store_text_chunks.json at all.
    client = client_factory(tmp_path)
    resp = client.get("/api/ui/chunks/chunk-deadbeefdeadbeef")
    assert resp.status_code == 404


@pytest.mark.parametrize(
    "bad_id",
    [
        "../../../etc/passwd",
        "chunks/with/slash",
        "chunks\\with\\backslash",
        "x" * 200,
    ],
)
def test_chunk_preview_rejects_bad_ids(
    tmp_path: Path, client_factory, bad_id: str
) -> None:
    (tmp_path / "kv_store_text_chunks.json").write_text("{}", encoding="utf-8")
    client = client_factory(tmp_path)
    resp = client.get(f"/api/ui/chunks/{bad_id}")
    # Path-with-slashes will be split by FastAPI's router and 404; oversize +
    # backslash hit our explicit 400 guard.
    assert resp.status_code in (400, 404)
