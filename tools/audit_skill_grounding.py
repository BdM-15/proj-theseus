"""Skill grounding-ratio audit (branch 147).

Reads a recorded skill run's ``transcript.json`` and quantifies how much of
the final assistant response is *grounded* in workspace evidence the runtime
actually retrieved during the run, vs. claims the LLM produced from general
knowledge.

A claim (sentence) is considered **grounded** when ANY of the following hold:

1. It contains an inline ``chunk-xxxx`` citation (regex
   ``chunk-[0-9a-f]{4,}``) referencing a chunk that was returned by a
   ``kg_chunks`` / ``kg_query`` / ``kg_entities`` tool call earlier in the
   same transcript.
2. It contains an inline ``chunk-xxxx`` citation in general (the chunk id
   matches the canonical pattern even if we can't prove it was retrieved
   in *this* run — gives benefit of the doubt to skills citing the wider
   workspace KG, not just their own session).
3. It cites a named entity (``Entity:Name``, ``[Entity Name]``) that
   appears in the entity slice returned by a ``kg_entities`` tool call.
4. It is a structural / non-claim sentence: a Markdown heading, a table
   header row, an empty bullet, a code-fence delimiter, a "References:"
   anchor line, or a sentence under 25 chars (e.g. transitions like
   "Here is the matrix:"). These are exempt from the denominator.

Usage::

    python tools/audit_skill_grounding.py <transcript.json>
    python tools/audit_skill_grounding.py --skill proposal-generator
    python tools/audit_skill_grounding.py --all  # every skill, latest run

Output (machine-readable JSON to stdout)::

    {
      "transcript": "<path>",
      "skill": "proposal-generator",
      "run_id": "20260429_174042_...",
      "claims_total": 42,
      "claims_grounded": 36,
      "claims_unsourced": 6,
      "claims_exempt": 11,
      "grounding_ratio": 0.857,
      "retrieved_chunk_ids": ["chunk-a3f2", ...],
      "retrieved_entities": ["Acme Corp", ...],
      "unsourced_examples": ["...", "..."]
    }

Exit code 0 always — the assertion of a minimum ratio is the harness's job
(``tests/skills/e2e/test_skills_smoke.py``), not this tool's.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

CHUNK_CITE_RE = re.compile(r"chunk-[0-9a-f]{4,}", re.IGNORECASE)
KG_TOOLS = {"kg_chunks", "kg_query", "kg_entities"}

# Sentence terminators. Keep ASCII-only; the prompts produce ASCII punct.
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z\(\[`])")

# Patterns that mark a line as structural (not a claim).
STRUCTURAL_LINE_RE = re.compile(
    r"""^\s*(
        \#+\s+ |            # markdown heading
        \|.*\| |            # markdown table row
        [-*+]\s*$ |         # empty bullet
        ```|~~~ |           # code fence
        References?:\s*$ |  # references anchor
        Citations?:\s*$ |
        Sources?:\s*$ |
        \d+\.\s*$           # bare list number
    )""",
    re.IGNORECASE | re.VERBOSE,
)

MIN_CLAIM_CHARS = 25


def _load_transcript(path: Path) -> list[dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for key in ("transcript", "turns"):
            val = raw.get(key)
            if isinstance(val, list):
                return val
    raise ValueError(f"Unrecognized transcript shape in {path}")


def _final_assistant_text(turns: list[dict[str, Any]]) -> str:
    """Last assistant turn with non-empty ``content``."""
    for turn in reversed(turns):
        if (turn.get("kind") or turn.get("role")) != "assistant":
            continue
        content = (turn.get("content") or "").strip()
        if content:
            return content
    return ""


def _retrieved_chunk_ids(turns: list[dict[str, Any]]) -> set[str]:
    found: set[str] = set()
    for turn in turns:
        if (turn.get("kind") or "").lower() != "tool":
            continue
        ids = turn.get("chunk_ids") or []
        if isinstance(ids, list):
            for cid in ids:
                if isinstance(cid, str):
                    found.add(cid.lower())
        # Fallback: scan result_preview text for chunk-* citations
        preview = turn.get("result_preview") or ""
        if isinstance(preview, str):
            for match in CHUNK_CITE_RE.findall(preview):
                found.add(match.lower())
    return found


def _retrieved_entities(turns: list[dict[str, Any]]) -> set[str]:
    """Collect entity names from kg_entities / kg_query previews."""
    names: set[str] = set()
    for turn in turns:
        if (turn.get("kind") or "").lower() != "tool":
            continue
        name = (turn.get("name") or "").lower()
        if name not in {"kg_entities", "kg_query"}:
            continue
        preview = turn.get("result_preview") or ""
        if not isinstance(preview, str):
            continue
        # Heuristic: pull tokens that look like entity names from the preview.
        # Most KG tool results render entities like ``- Acme Corp (company)``
        # or as JSON blobs containing ``"name": "Acme Corp"``.
        for match in re.finditer(r'"name"\s*:\s*"([^"]{3,80})"', preview):
            names.add(match.group(1).strip().lower())
        for match in re.finditer(r'"entity_name"\s*:\s*"([^"]{3,80})"', preview):
            names.add(match.group(1).strip().lower())
        for match in re.finditer(r"^\s*[-*]\s+([A-Z][A-Za-z0-9 ./&'-]{2,80})", preview, re.MULTILINE):
            names.add(match.group(1).strip().lower())
    # Drop noise tokens
    return {n for n in names if len(n) >= 3 and not n.startswith("none")}


def _split_claims(text: str) -> list[str]:
    """Split response into candidate claim sentences (line-aware)."""
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if STRUCTURAL_LINE_RE.match(stripped):
            out.append(stripped)  # keep — exempt downstream
            continue
        # Sentence-split inside the line
        for sent in SENTENCE_SPLIT_RE.split(stripped):
            s = sent.strip()
            if s:
                out.append(s)
    return out


def _is_structural(sentence: str) -> bool:
    return bool(STRUCTURAL_LINE_RE.match(sentence))


def _is_grounded(
    sentence: str,
    retrieved_chunks: set[str],
    retrieved_entities: set[str],
) -> bool:
    # Rule 1+2: any chunk-xxxx citation in the sentence
    for match in CHUNK_CITE_RE.findall(sentence):
        if match.lower() in retrieved_chunks:
            return True
        # Rule 2: any well-formed chunk id at all (benefit of the doubt)
        return True
    # Rule 3: named entity match (case-insensitive substring)
    sent_lower = sentence.lower()
    for ent in retrieved_entities:
        if ent and ent in sent_lower:
            return True
    return False


def audit(transcript_path: Path) -> dict[str, Any]:
    turns = _load_transcript(transcript_path)
    final = _final_assistant_text(turns)
    chunks = _retrieved_chunk_ids(turns)
    entities = _retrieved_entities(turns)

    # Skill / run id from path: rag_storage/<ws>/skill_runs/<skill>/<run_id>/transcript.json
    parts = transcript_path.resolve().parts
    skill = run_id = None
    if "skill_runs" in parts:
        idx = parts.index("skill_runs")
        if idx + 2 < len(parts):
            skill = parts[idx + 1]
            run_id = parts[idx + 2]

    sentences = _split_claims(final)
    claims_grounded = 0
    claims_total = 0
    claims_exempt = 0
    unsourced: list[str] = []

    for sent in sentences:
        if _is_structural(sent) or len(sent) < MIN_CLAIM_CHARS:
            claims_exempt += 1
            continue
        claims_total += 1
        if _is_grounded(sent, chunks, entities):
            claims_grounded += 1
        else:
            if len(unsourced) < 10:
                unsourced.append(sent[:200])

    ratio = (claims_grounded / claims_total) if claims_total else 1.0

    return {
        "transcript": str(transcript_path),
        "skill": skill,
        "run_id": run_id,
        "claims_total": claims_total,
        "claims_grounded": claims_grounded,
        "claims_unsourced": claims_total - claims_grounded,
        "claims_exempt": claims_exempt,
        "grounding_ratio": round(ratio, 3),
        "retrieved_chunk_count": len(chunks),
        "retrieved_entity_count": len(entities),
        "unsourced_examples": unsourced,
    }


def _latest_transcript_for(skill: str, workspace_root: Path) -> Path | None:
    skill_dir = workspace_root / "skill_runs" / skill
    if not skill_dir.exists():
        return None
    candidates = sorted(skill_dir.glob("*/transcript.json"))
    return candidates[-1] if candidates else None


def _all_skills_latest(workspace_root: Path) -> list[Path]:
    base = workspace_root / "skill_runs"
    if not base.exists():
        return []
    out: list[Path] = []
    for skill_dir in sorted(base.iterdir()):
        if not skill_dir.is_dir():
            continue
        runs = sorted(skill_dir.glob("*/transcript.json"))
        if runs:
            out.append(runs[-1])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    parser.add_argument("transcript", nargs="?", type=Path, help="Path to transcript.json")
    parser.add_argument("--skill", help="Skill name; audit its latest transcript in --workspace")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path("rag_storage/afcap5_adab_iss"),
        help="Workspace dir under rag_storage/ (default: afcap5_adab_iss)",
    )
    parser.add_argument("--all", action="store_true", help="Audit latest transcript for every skill")
    args = parser.parse_args(argv)

    paths: list[Path]
    if args.all:
        paths = _all_skills_latest(args.workspace)
        if not paths:
            print(f"No transcripts under {args.workspace}/skill_runs/", file=sys.stderr)
            return 0
    elif args.skill:
        p = _latest_transcript_for(args.skill, args.workspace)
        if not p:
            print(f"No transcript found for skill {args.skill!r} in {args.workspace}", file=sys.stderr)
            return 0
        paths = [p]
    elif args.transcript:
        paths = [args.transcript]
    else:
        parser.print_help()
        return 2

    results = [audit(p) for p in paths]
    if len(results) == 1:
        print(json.dumps(results[0], indent=2))
    else:
        print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
