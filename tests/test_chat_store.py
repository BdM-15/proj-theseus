import json
from pathlib import Path

import pytest
from fastapi import HTTPException

from src.server.chat_store import ChatStore


def _store(tmp_path: Path, *, history_pairs: int = 1) -> ChatStore:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return ChatStore(
        workspace_dir=lambda: workspace,
        now=lambda: "2026-01-02T03:04:05",
        history_pairs=lambda: history_pairs,
    )


def test_chat_store_create_update_list_and_delete(tmp_path: Path) -> None:
    store = _store(tmp_path)

    chat = store.create(title="  New chat  ", mode="mix", rfp_context=None)
    chat_id = chat["id"]

    assert store.path(chat_id).exists()
    assert store.read(chat_id)["title"] == "New chat"
    updated = store.update(chat_id, title="Renamed", mode="local", rfp_context="rfp")
    assert updated["title"] == "Renamed"
    assert updated["mode"] == "local"
    assert updated["rfp_context"] == "rfp"
    assert store.list_summaries() == [store.summary(updated)]

    store.delete(chat_id)
    with pytest.raises(HTTPException) as exc_info:
        store.read(chat_id)
    assert exc_info.value.status_code == 404


def test_chat_store_rejects_bad_ids(tmp_path: Path) -> None:
    store = _store(tmp_path)

    with pytest.raises(HTTPException) as exc_info:
        store.path("../nope")

    assert exc_info.value.status_code == 400


def test_chat_store_build_history_trims_pairs_and_filters_roles(tmp_path: Path) -> None:
    store = _store(tmp_path, history_pairs=1)
    chat = {
        "messages": [
            {"role": "system", "content": "ignore"},
            {"role": "user", "content": "old"},
            {"role": "assistant", "content": "older"},
            {"role": "user", "content": "new"},
            {"role": "assistant", "content": "newer"},
        ]
    }

    assert store.build_history(chat) == [
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "newer"},
    ]
    assert store.build_history(chat, exclude_last=True) == [
        {"role": "assistant", "content": "older"},
        {"role": "user", "content": "new"},
    ]


def test_chat_store_corrupt_chat_maps_to_http_error(tmp_path: Path) -> None:
    store = _store(tmp_path)
    path = store.chats_dir() / "abcdef.json"
    path.write_text("not-json", encoding="utf-8")

    with pytest.raises(HTTPException) as exc_info:
        store.read("abcdef")

    assert exc_info.value.status_code == 500


def test_chat_store_autotitle_preserves_existing_and_truncates() -> None:
    chat = {"title": "New chat"}
    ChatStore.maybe_autotitle(chat, "x" * 70)
    assert chat["title"] == "x" * 60 + "\u2026"

    ChatStore.maybe_autotitle(chat, "replacement")
    assert chat["title"] == "x" * 60 + "\u2026"


def test_chat_store_list_summaries_skips_corrupt_files(tmp_path: Path) -> None:
    store = _store(tmp_path)
    chat = store.create(title="ok", mode="mix", rfp_context=None)
    (store.chats_dir() / "badbad.json").write_text("not-json", encoding="utf-8")

    assert store.list_summaries() == [store.summary(chat)]
    persisted = json.loads(store.path(chat["id"]).read_text(encoding="utf-8"))
    assert persisted["title"] == "ok"
