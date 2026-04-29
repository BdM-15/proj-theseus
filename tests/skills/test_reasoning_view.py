"""Phase 6b tests — deterministic reasoning view over transcript.json.

Covers the pure renderer ``build_reasoning_view`` in ``src/skills/reasoning.py``.
The renderer is intentionally side-effect-free: no FS, no network, no LLM.
"""

from __future__ import annotations

import json

from src.skills.reasoning import build_reasoning_view


def test_empty_transcript_returns_zero_steps() -> None:
    out = build_reasoning_view([])
    assert out == {
        "steps": [],
        "summary": {"turns": 0, "tool_calls": 0, "messages": 0},
    } or out["steps"] == []
    assert out["summary"]["turns"] == 0
    assert out["summary"]["tool_calls"] == 0


def test_non_list_transcript_is_safe() -> None:
    out = build_reasoning_view(None)  # type: ignore[arg-type]
    assert out["steps"] == []
    assert out["summary"]["tool_calls"] == 0


def test_assistant_text_step_renders() -> None:
    transcript = [
        {"kind": "system", "turn": 0, "content": "You are an auditor."},
        {"kind": "user", "turn": 0, "content": "Audit this RFP."},
        {
            "kind": "assistant",
            "turn": 1,
            "content": "I will start by pulling clauses.",
            "tool_calls": [],
            "elapsed_ms": 1500.0,
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        },
    ]
    view = build_reasoning_view(transcript)
    kinds = [s["kind"] for s in view["steps"]]
    assert kinds == ["system", "user", "assistant_text"]
    assert view["steps"][2]["preview"].startswith("I will start")
    assert view["steps"][2]["elapsed_ms"] == 1500.0
    assert view["summary"]["tool_calls"] == 0


def test_tool_call_paired_with_result_by_call_id() -> None:
    transcript = [
        {
            "kind": "assistant",
            "turn": 1,
            "content": "",
            "tool_calls": [
                {
                    "id": "call-abc",
                    "name": "kg_entities",
                    "arguments": json.dumps({"types": ["clause"], "limit": 200}),
                }
            ],
            "elapsed_ms": 3500.0,
        },
        {
            "kind": "tool",
            "turn": 1,
            "call_id": "call-abc",
            "name": "kg_entities",
            "arguments": json.dumps({"types": ["clause"]}),
            "elapsed_ms": 651.92,
            "result_preview": '{"entities": {"clause": [...]}}',
            "extra": {"truncated": False},
        },
    ]
    view = build_reasoning_view(transcript)
    # Single tool_action step; the assistant entry collapses into the call.
    actions = [s for s in view["steps"] if s["kind"] == "tool_action"]
    assert len(actions) == 1
    step = actions[0]
    assert step["tool"] == "kg_entities"
    assert step["call_id"] == "call-abc"
    assert step["args"] == {"types": ["clause"], "limit": 200}
    assert step["elapsed_ms"] == 651.92  # took from the tool result, not the assistant turn
    assert "Pulled clause" in step["summary"]
    assert "limit 200" in step["summary"]
    assert view["summary"]["tool_calls"] == 1


def test_tool_call_summaries_match_known_vocabulary() -> None:
    transcript = [
        {
            "kind": "assistant",
            "turn": 1,
            "content": "",
            "tool_calls": [
                {"id": "c1", "name": "kg_chunks", "arguments": json.dumps({"query": "FAR 52.204-21", "top_k": 10, "mode": "hybrid"})},
                {"id": "c2", "name": "kg_query", "arguments": json.dumps({"cypher": "MATCH (c:clause) RETURN count(c)"})},
                {"id": "c3", "name": "read_file", "arguments": json.dumps({"path": "references/far_subpart_9_5.md"})},
                {"id": "c4", "name": "run_script", "arguments": json.dumps({"path": "scripts/render_docx.py", "timeout": 60})},
                {"id": "c5", "name": "write_file", "arguments": json.dumps({"path": "artifacts/proposal_draft.json"})},
            ],
        },
        {"kind": "tool", "call_id": "c1", "name": "kg_chunks", "result_preview": "[]"},
        {"kind": "tool", "call_id": "c2", "name": "kg_query", "result_preview": "[]"},
        {"kind": "tool", "call_id": "c3", "name": "read_file", "result_preview": "..."},
        {"kind": "tool", "call_id": "c4", "name": "run_script", "result_preview": "..."},
        {"kind": "tool", "call_id": "c5", "name": "write_file", "result_preview": "OK"},
    ]
    view = build_reasoning_view(transcript)
    summaries = [s["summary"] for s in view["steps"] if s["kind"] == "tool_action"]
    assert any("Searched the chunk index" in s and "FAR 52.204-21" in s for s in summaries)
    assert any("Cypher query" in s for s in summaries)
    assert any("Loaded reference file" in s and "far_subpart_9_5.md" in s for s in summaries)
    assert any("Executed script" in s and "render_docx.py" in s for s in summaries)
    assert any("Wrote artifact" in s and "proposal_draft.json" in s for s in summaries)


def test_chunk_ids_are_extracted_from_result_preview() -> None:
    transcript = [
        {
            "kind": "assistant",
            "turn": 1,
            "content": "",
            "tool_calls": [
                {"id": "c1", "name": "kg_chunks", "arguments": json.dumps({"query": "cyber"})},
            ],
        },
        {
            "kind": "tool",
            "call_id": "c1",
            "name": "kg_chunks",
            "result_preview": 'hits: chunk-1b8a790d0500c50bb2b2b57ff70c810a, chunk-b562c978f436c55018b296b14f7de509, chunk-1b8a790d0500c50bb2b2b57ff70c810a (dupe)',
        },
    ]
    view = build_reasoning_view(transcript)
    step = next(s for s in view["steps"] if s["kind"] == "tool_action")
    assert step["links"]["chunk_ids"] == [
        "chunk-1b8a790d0500c50bb2b2b57ff70c810a",
        "chunk-b562c978f436c55018b296b14f7de509",
    ]


def test_chunk_ids_prefer_stored_field_over_regex() -> None:
    """New runs persist a ``chunk_ids`` list on the tool entry (full ids
    captured before the 500-char preview slice). The renderer must prefer
    that list so ids that fall past the truncation are still surfaced."""
    transcript = [
        {
            "kind": "assistant",
            "turn": 1,
            "content": "",
            "tool_calls": [
                {"id": "c1", "name": "kg_chunks", "arguments": json.dumps({"query": "cyber"})},
            ],
        },
        {
            "kind": "tool",
            "call_id": "c1",
            "name": "kg_chunks",
            # Preview only contains a truncated id (would be a half-match).
            "result_preview": "hits: chunk-1b8a790d0500c50bb2",
            # But the runtime extracted these from the full payload.
            "chunk_ids": [
                "chunk-1b8a790d0500c50bb2b2b57ff70c810a",
                "chunk-b562c978f436c55018b296b14f7de509",
            ],
        },
    ]
    view = build_reasoning_view(transcript)
    step = next(s for s in view["steps"] if s["kind"] == "tool_action")
    assert step["links"]["chunk_ids"] == [
        "chunk-1b8a790d0500c50bb2b2b57ff70c810a",
        "chunk-b562c978f436c55018b296b14f7de509",
    ]


def test_unpaired_tool_entry_still_surfaces() -> None:
    # Crash mid-run could leave a tool result with no matching assistant call.
    transcript = [
        {"kind": "tool", "call_id": "orphan", "name": "kg_entities", "result_preview": "{}"},
    ]
    view = build_reasoning_view(transcript)
    actions = [s for s in view["steps"] if s["kind"] == "tool_action"]
    assert len(actions) == 1
    assert actions[0]["call_id"] == "orphan"


def test_summary_counts_aggregate_across_turns() -> None:
    transcript = [
        {"kind": "user", "turn": 0, "content": "hi"},
        {"kind": "assistant", "turn": 1, "content": "", "tool_calls": [
            {"id": "a", "name": "kg_entities", "arguments": "{}"},
            {"id": "b", "name": "kg_chunks", "arguments": "{}"},
        ]},
        {"kind": "tool", "turn": 1, "call_id": "a", "name": "kg_entities", "result_preview": ""},
        {"kind": "tool", "turn": 1, "call_id": "b", "name": "kg_chunks", "result_preview": ""},
        {"kind": "assistant", "turn": 2, "content": "Done.", "tool_calls": []},
    ]
    view = build_reasoning_view(transcript)
    assert view["summary"]["turns"] == 3  # turn 0, 1, 2
    assert view["summary"]["tool_calls"] == 2
    assert view["summary"]["messages"] == len(view["steps"])


def test_string_arguments_that_are_not_json_dont_crash() -> None:
    transcript = [
        {
            "kind": "assistant",
            "turn": 1,
            "content": "",
            "tool_calls": [
                {"id": "c1", "name": "read_file", "arguments": "this is not json"},
            ],
        },
        {"kind": "tool", "call_id": "c1", "name": "read_file", "result_preview": ""},
    ]
    view = build_reasoning_view(transcript)
    step = next(s for s in view["steps"] if s["kind"] == "tool_action")
    # Falls through to "(unspecified)" because args._raw is not 'path'.
    assert "Loaded reference file" in step["summary"]
    assert step["args"]["_raw"].startswith("this is not json")
