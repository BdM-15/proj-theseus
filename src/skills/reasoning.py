"""Phase 6b — Deterministic reasoning view over a skill run's transcript.

The runtime persists every turn of a tools-mode skill run to
``<run_dir>/transcript.json`` as a flat list of ``{kind, turn, ...}`` entries
where ``kind`` is one of ``system``, ``user``, ``assistant``, ``tool``.

This module walks that transcript and produces a pre-rendered "Why this
artifact?" view: numbered narrative steps mapping each tool call to a short
prose summary ("Pulled 47 entities of type clause") plus the raw call/result
for power-user audit. Pure deterministic mapping — **no LLM calls, no new
on-disk schema, no inference**. The transcript itself is the source of truth.
"""

from __future__ import annotations

import json
import re
from typing import Any

# How much of the raw tool result_preview to include verbatim in each step.
_RESULT_SLICE = 1200

# Pattern for chunk ids surfaced by kg_chunks / kg_query results. LightRAG
# uses ``chunk-<hex>`` ids; tolerate both that and the bare hex form.
_CHUNK_ID_RX = re.compile(r"\b(chunk-[A-Za-z0-9]{6,})\b")


def _safe_load_args(arguments: Any) -> dict[str, Any]:
    """Tool-call arguments may arrive as a JSON string or already parsed."""
    if isinstance(arguments, dict):
        return arguments
    if isinstance(arguments, str) and arguments.strip():
        try:
            parsed = json.loads(arguments)
            if isinstance(parsed, dict):
                return parsed
        except (TypeError, ValueError):
            return {"_raw": arguments[:_RESULT_SLICE]}
    return {}


def _truncate(text: str, limit: int = _RESULT_SLICE) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "\u2026"


def _summarize_tool_call(name: str, args: dict[str, Any], result_preview: str) -> str:
    """Map (tool_name, args, result_preview) -> single-sentence prose.

    Closed vocabulary covering the 6 tools the SkillManager exposes today.
    Falls back to a generic "Called <tool>" string for anything else.
    """
    if name == "kg_entities":
        types = args.get("types") or args.get("entity_types") or []
        limit = args.get("limit")
        type_str = ", ".join(str(t) for t in types) if isinstance(types, list) and types else "entities"
        suffix = f" (limit {limit})" if limit else ""
        return f"Pulled {type_str} from the knowledge graph{suffix}."

    if name == "kg_chunks":
        query = args.get("query") or args.get("q") or ""
        top_k = args.get("top_k") or args.get("k")
        mode = args.get("mode")
        bits = []
        if query:
            bits.append(f"\u201c{_truncate(str(query), 120)}\u201d")
        if top_k:
            bits.append(f"top {top_k}")
        if mode:
            bits.append(f"mode={mode}")
        tail = " (" + ", ".join(bits) + ")" if bits else ""
        return f"Searched the chunk index{tail}."

    if name == "kg_query":
        cypher = args.get("cypher") or args.get("query") or ""
        first_line = str(cypher).strip().splitlines()[0] if cypher else ""
        if first_line:
            return f"Ran a structural Cypher query: `{_truncate(first_line, 120)}`"
        return "Ran a structural Cypher query against the workspace graph."

    if name == "read_file":
        path = args.get("path") or args.get("filename") or "(unspecified)"
        return f"Loaded reference file: `{path}`."

    if name == "run_script":
        path = args.get("path") or args.get("script") or "(unspecified)"
        timeout = args.get("timeout")
        suffix = f" (timeout {timeout}s)" if timeout else ""
        return f"Executed script: `{path}`{suffix}."

    if name == "write_file":
        path = args.get("path") or args.get("filename") or "(unspecified)"
        return f"Wrote artifact: `{path}`."

    return f"Called tool `{name}`."


def _extract_chunk_ids(blob: str) -> list[str]:
    """Pull any ``chunk-<hex>`` ids out of a result preview / arg blob."""
    if not blob:
        return []
    seen: list[str] = []
    for m in _CHUNK_ID_RX.finditer(blob):
        cid = m.group(1)
        if cid not in seen:
            seen.append(cid)
        if len(seen) >= 25:
            break
    return seen


def _short_preview(text: str, limit: int = 240) -> str:
    """Compact preview for narrative — collapses whitespace + truncates."""
    if not text:
        return ""
    collapsed = " ".join(str(text).split())
    return _truncate(collapsed, limit)


def build_reasoning_view(transcript: list[dict[str, Any]]) -> dict[str, Any]:
    """Walk a transcript and emit a pre-rendered reasoning timeline.

    Pairs each ``kind=assistant`` tool_call with its matching ``kind=tool``
    result by ``call_id``. Renders one step per logical action so the UI
    can show a flat numbered list.

    Returns a dict ``{steps: [...], summary: {...}}`` shaped for the UI.
    """
    if not isinstance(transcript, list):
        return {"steps": [], "summary": {"turns": 0, "tool_calls": 0, "messages": 0}}

    # Index tool results by call_id so assistant tool_calls can be paired.
    tool_results: dict[str, dict[str, Any]] = {}
    for entry in transcript:
        if not isinstance(entry, dict):
            continue
        if entry.get("kind") == "tool":
            call_id = entry.get("call_id")
            if isinstance(call_id, str) and call_id:
                tool_results[call_id] = entry

    steps: list[dict[str, Any]] = []
    tool_call_count = 0
    total_elapsed_ms = 0.0
    turns_seen: set[int] = set()

    for entry in transcript:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("kind")
        turn = entry.get("turn")
        if isinstance(turn, int):
            turns_seen.add(turn)

        if kind == "system":
            content = str(entry.get("content") or "")
            if not content.strip():
                continue
            steps.append({
                "index": len(steps) + 1,
                "kind": "system",
                "turn": turn,
                "summary": "Skill system instructions loaded.",
                "preview": _short_preview(content),
                "raw": {"content": _truncate(content, 4000)},
            })
            continue

        if kind == "user":
            content = str(entry.get("content") or "")
            steps.append({
                "index": len(steps) + 1,
                "kind": "user",
                "turn": turn,
                "summary": "User prompt.",
                "preview": _short_preview(content),
                "raw": {"content": _truncate(content, 4000)},
            })
            continue

        if kind == "assistant":
            content = str(entry.get("content") or "").strip()
            tool_calls = entry.get("tool_calls") or []
            elapsed = float(entry.get("elapsed_ms") or 0)
            usage = entry.get("usage") if isinstance(entry.get("usage"), dict) else None
            total_elapsed_ms += elapsed

            # Assistant text (no tool calls) → narration step.
            if content and not tool_calls:
                steps.append({
                    "index": len(steps) + 1,
                    "kind": "assistant_text",
                    "turn": turn,
                    "summary": "Assistant reasoning.",
                    "preview": _short_preview(content, 400),
                    "raw": {"content": _truncate(content, 4000)},
                    "elapsed_ms": elapsed,
                    "usage": usage,
                })

            # Each tool call becomes its own step, paired with its result.
            for call in tool_calls:
                if not isinstance(call, dict):
                    continue
                tool_call_count += 1
                call_id = call.get("id") or call.get("call_id")
                name = str(call.get("name") or "unknown")
                args = _safe_load_args(call.get("arguments"))
                result_entry = tool_results.get(call_id) if isinstance(call_id, str) else None
                result_preview = str((result_entry or {}).get("result_preview") or "")
                tool_elapsed = float((result_entry or {}).get("elapsed_ms") or 0)
                truncated = bool(((result_entry or {}).get("extra") or {}).get("truncated"))

                # Collect chunk ids referenced by the args or result, so the
                # UI can render them as deep-link chips (Phase 6b.2 wires the
                # actual chunk preview modal).
                chunk_ids = _extract_chunk_ids(json.dumps(args)) + _extract_chunk_ids(result_preview)
                # Dedupe preserving order.
                deduped: list[str] = []
                for c in chunk_ids:
                    if c not in deduped:
                        deduped.append(c)

                steps.append({
                    "index": len(steps) + 1,
                    "kind": "tool_action",
                    "turn": turn,
                    "tool": name,
                    "call_id": call_id,
                    "summary": _summarize_tool_call(name, args, result_preview),
                    "args": args,
                    "result_preview": _truncate(result_preview, _RESULT_SLICE),
                    "result_truncated": truncated,
                    "elapsed_ms": tool_elapsed,
                    "links": {"chunk_ids": deduped},
                })
            continue

        # Unpaired tool entries (rare — the assistant pair is missing) still
        # surface so audit is not silently lossy.
        if kind == "tool":
            call_id = entry.get("call_id")
            if any(s.get("call_id") == call_id for s in steps if s.get("kind") == "tool_action"):
                continue
            name = str(entry.get("name") or "unknown")
            result_preview = str(entry.get("result_preview") or "")
            args = _safe_load_args(entry.get("arguments"))
            steps.append({
                "index": len(steps) + 1,
                "kind": "tool_action",
                "turn": turn,
                "tool": name,
                "call_id": call_id,
                "summary": _summarize_tool_call(name, args, result_preview),
                "args": args,
                "result_preview": _truncate(result_preview, _RESULT_SLICE),
                "result_truncated": bool((entry.get("extra") or {}).get("truncated")),
                "elapsed_ms": float(entry.get("elapsed_ms") or 0),
                "links": {"chunk_ids": _extract_chunk_ids(result_preview)},
            })

    summary = {
        "turns": len(turns_seen),
        "tool_calls": tool_call_count,
        "messages": len(steps),
        "total_elapsed_ms": round(total_elapsed_ms, 2),
    }
    return {"steps": steps, "summary": summary}
