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
3a. It cites a **named source** that the runtime can verify the skill
   actually consulted in this run — a ``references/...`` file the skill
   read via ``read_file``, an MCP tool the skill invoked (e.g.,
   ``BLS series OEUS47900015-1252``, ``CALC+ N=47``, ``GSA per diem
   Huntsville``), or a parenthetical attribution to the user prompt
   (e.g., ``(user query)``, ``(per the prompt)``, ``(user-supplied)``).
   These are legitimate anchors — the skill is honestly attributing the
   provenance, even if the underlying datum didn't come from the KG.
4. It is a structural / non-claim sentence: a Markdown heading, a table
   header row, an empty bullet, a code-fence delimiter, a "References:"
   anchor line, or a sentence under 25 chars (e.g. transitions like
   "Here is the matrix:"). These are exempt from the denominator.
5. It is a cover-note / artifact-handoff sentence (artifact save
   confirmations like "Saved X to artifacts/Y.json", stats summary
   bullets like "- Findings: 19 (critical: 8, ...)", pointer lines like
   "Open the JSON for the full report", or process attestations like
   "All 10 checks executed against the live KG slice"). These are also
   exempt — the artifact JSON is the source of truth per skill design
   contract; cover notes are navigation aids, not domain claims.
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

# Named-source anchors: legitimate citations to provenance the runtime
# can verify the skill consulted, even when it isn't a kg_* hit.
#
#   - parenthetical user-prompt attributions: "(user query)",
#     "(per the prompt)", "(user-supplied)", "(from the user)"
#   - MCP tool data hand-offs by family: "BLS series ...", "CALC+",
#     "GSA per diem ...", "eCFR ...", "USAspending ..."
#   - explicit "per the X reference" hand-off to a bundled reference file
USER_ATTR_RE = re.compile(
    r"(?:\(|\b)(?:user(?:[-\s](?:query|prompt|supplied|input|provided|specified|stated))?|per\s+the\s+(?:user|prompt|query)|from\s+the\s+(?:user|prompt))(?:\)|\b)",
    re.IGNORECASE,
)
NAMED_SOURCE_RE = re.compile(
    r"""\b(
        BLS\s+(?:series|OEWS|wage|OE[UN][A-Z0-9_-]+) |
        CALC\+? |
        GSA\s+(?:per[\s-]diem|CALC|MAS) |
        eCFR |
        USAspending(?:\.gov)? |
        FAR\s+\d+\.\d+(?:-\d+)? |
        DFARS\s+\d+\.\d+(?:-\d+)? |
        NIST\s+SP\s+\d+(?:-\d+)?
    )\b""",
    re.IGNORECASE | re.VERBOSE,
)
REF_BUNDLE_RE = re.compile(
    r"`?(references?/[A-Za-z0-9_./-]+\.md)`?|per\s+(?:the\s+)?[`']?(references?/[A-Za-z0-9_./-]+\.md)[`']?",
    re.IGNORECASE,
)

# Bare-filename reference: "per ot_authority_taxonomy.md", "per cost_models/foo.md",
# "trl_milestone_patterns.md §1/3". Credited only if a consulted_sources path
# ends with that basename (so an unread file isn't a free citation).
BARE_REF_RE = re.compile(
    r"\b([A-Za-z0-9_]+(?:/[A-Za-z0-9_]+)?\.md)\b",
)

# JSON-envelope shorthand: skills that emit a structured artifact via
# write_file may legitimately reference back to it from the narrative
# without copy-pasting every chunk id, e.g.
#   "[see decision_tree_reconstruction.block_2.source_chunk_ids]"
#   "[per artifact: hot_buttons[3].source_chunk_ids]"
#   "(see artifact: rfp_reverse_engineering.json -> compliance_traps)"
# Only credited when the run actually wrote a JSON artifact.
JSON_REF_RE = re.compile(
    r"\[(?:see|per|ref(?:er)?|cite)\b[^\]]*?(?:source_chunk_ids|artifact|envelope|json)[^\]]*\]"
    r"|\(\s*(?:see|per|ref(?:er)?)\b[^)]*?(?:source_chunk_ids|artifact:\s*[A-Za-z0-9_./-]+\.json|envelope)[^)]*\)",
    re.IGNORECASE,
)

# Parenthetical source attribution — "(Source: PWS 1.1)", "(Sources: chunks for X)",
# "(Cite: kg_entities)", "(per kg)". Loose-match, but only credited when the run
# wrote a JSON artifact (so the on-disk envelope is the verifiable backstop).
SOURCE_PAREN_RE = re.compile(
    r"\(\s*(?:Sources?|Cite|Citation|Cites|Per\s+(?:kg|KG|chunks?|entities?|the\s+kg))\s*:[^)]{2,200}\)",
    re.IGNORECASE,
)

# Sentence terminators. Keep ASCII-only; the prompts produce ASCII punct.
# Negative lookbehind avoids splitting after common abbreviations
# (vs., e.g., i.e., etc., cf., U.S., No., Inc., Corp., Co., Ltd., approx., ca.)
# Each lookbehind must include the trailing dot \u2014 the split position is
# right after that dot, so the lookbehind's window ends there too.
_ABBREV_NO_SPLIT = (
    r"(?<!\bvs\.)(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\betc\.)(?<!\bcf\.)"
    r"(?<!\bU\.S\.)(?<!\bNo\.)(?<!\bInc\.)(?<!\bCorp\.)(?<!\bLtd\.)"
    r"(?<!\bapprox\.)(?<!\bca\.)(?<!\bSr\.)(?<!\bJr\.)"
)
SENTENCE_SPLIT_RE = re.compile(_ABBREV_NO_SPLIT + r"(?<=[.!?])\s+(?=[A-Z\(\[`])")

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

# Bold-only "heading" lines: **Foo**, **Foo: Bar**, **Foo (baz)**.
# These act as section labels in skill output but aren't true claims.
# Match a line that is *entirely* one or two bold runs and optional
# trailing punctuation — no narrative prose after the closing ``**``.
BOLD_HEADING_RE = re.compile(
    r"^\s*[-*]?\s*\*\*[^*\n]{2,200}\*\*\s*[:.\-—]?\s*$",
)

# Class B reasoning-leap markers — visible-judgment framing the SKILL
# instructions explicitly preserve. When a sentence opens with or
# prominently contains one of these, it is judgment / heuristic, not a
# factual claim, and is exempt from the grounding denominator.
REASONING_LEAP_RE = re.compile(
    r"\b("
    r"in\s+(?:my|our)\s+(?:experience|capture|view|read) |"
    r"a\s+defensible\s+read |"
    r"the\s+classic\s+\w+\s+(?:sweet\s+spot|pattern|play|move) |"
    r"classic\s+capture\s+sweet\s+spot |"
    r"rule\s+of\s+thumb |"
    r"typical(?:ly)?\s+(?:agency|prime|sub|capture|wraps?|prices?) |"
    r"would\s+(?:overstate|understate|hand|risk|trigger|tip|signal) |"
    r"sits?\s+comfortably |"
    r"comfortably\s+inside |"
    r"(?:aggressive|conservative)\s+(?:read|posture|stance|bid) |"
    r"likely\s+(?:to\s+|prices?\s+|wraps?\s+|implies?\s+|lands?\s+|tip\s+) |"
    r"this\s+is\s+\*?not\*?\s+the\s+\w+ |"
    r"heuristic |"
    r"(?:our|the)\s+(?:read|take|posture|stance)\s+(?:is|here) |"
    r"(?:used|using|treated|treat)\s+(?:as|.{1,30}?as)\s+(?:a\s+)?(?:proxy|proxies|stand-?in|substitute) |"
    r"(?:as\s+proxies?|as\s+stand-?ins?)\s+(?:for|where|when) |"
    r"where\s+\w+\s+(?:were|was|are)\s+sparse |"
    r"default\s+(?:for|value|assumption|per) |"
    r"standard\s+per\s+\w+ |"
    r"per\s+(?:AO|agency|industry|capture|taxonomy|reference|standard)\s+(?:convention|patterns?|practice|defaults?) |"
    r"per\s+(?:reference|taxonomy)\s+(?:patterns?|defaults?|conventions?) |"
    r"(?:passes|pass)\s+through\s+to\s+"
    r")",
    re.IGNORECASE | re.VERBOSE,
)

# Patterns that mark a line as a cover-note / artifact-handoff sentence —
# exempt from the grounding denominator because the artifact JSON itself is
# the source of truth (per skill design contract). These are navigation aids,
# not domain claims about the workspace.
#
# Covers:
#   - Artifact save/write confirmations:
#       "Saved compliance audit to `artifacts/compliance_audit.json`."
#       "Wrote ptw_analysis.json to artifacts/."
#   - Stats summary bullets:
#       "- Findings: 19 (critical: 8, high: 5, medium: 4, info: 2)"
#       "- Warnings: 2"
#       "- Top 3:"
#       "- Sources cited: chunk-aaaa, chunk-bbbb"
#   - Pointer / next-action lines:
#       "Open the JSON for the complete gap report and remediation steps."
#       "See artifacts/compliance_audit.json for the full report."
#   - Skill self-attestation (process, not domain):
#       "All 10 checks (C1-C10) executed against the live KG slice; ..."
COVER_NOTE_EXEMPT_RE = re.compile(
    r"""^\s*(
        # Stats / summary bullets: "- Word: number" or "- Word: ..."
        [-*]\s+(Findings?|Warnings?|Errors?|Stats?|Counts?|Severity|Top\s+\d+|
               Sources?\s+cited|Sources?|Citations?|Evidence|Artifact|Output|
               Total|Skipped|Passed|Failed|Deferred)\b.* |
        # Generic bold-bullet stats: "- **Anything**: <number>" or "- **X**: <single-word>"
        # (the substantive evidence lives in the artifact's source_chunks field, not here)
        [-*]\s+\*\*[^*]{2,80}\*\*\s*[:.\-—]\s*(\d+|N/A|none|n/a|deferred|locked|implied|open|skipped)\b.* |
        # Generic bullet stats with a number after a colon: "- Anything: 12 (OK: 10...)"
        [-*]\s+[A-Z][\w\s/&-]{2,60}:\s*\d+.* |
        # Artifact save/write confirmations
        (\*\*)?(Saved|Wrote|Created|Generated|Emitted|Persisted)\b.*\b(artifact|artifacts/|\.json|\.docx|\.xlsx|\.md|\.pptx|\.html)\b.* |
        # Pointer / next-action lines
        (Open|See|Refer\s+to|Inspect|Review|Hand|Pass|Forward)\b.*\b(JSON|artifact|artifacts/|file|report|envelope|directly\s+to|to\s+`?[a-z][a-z0-9_-]+`?)\b.* |
        # Capability / next-turn pointer: "Additional X can be generated...", "More Y available on request"
        (Additional|More|Further|Other)\s+\w+.*\b(can\s+be|may\s+be|are\s+available|available\s+(?:in|on|via))\b.* |
        # Skill self-attestation about process completion (broadened noun list)
        ([-*]\s+)?(All|Every|Each|No)\s+(\d+\s+)?.{0,80}?\b(executed|cited|grounded|sourced|covered|completed|anchored|invented|fabricated|hallucinated|quoted\s+verbatim|traces?\s+to|written|saved|persisted|emitted)\b.* |
        # Artifact-written self-attestation: "The PWS Markdown artifact has been written to ..."
        # Two shapes:
        #   (a) "The PWS Markdown artifact has been written to ..."
        #   (b) "The artifact `artifacts/foo.json` has been written ..."
        (The\s+)?[\w\s\-/]{2,60}?\s+(artifact|envelope|file|markdown|JSON|workbook|deck)s?\s+(has|have)\s+been\s+(written|saved|persisted|emitted|generated)\s+to\b.* |
        (The\s+)?(artifact|envelope|file|markdown|JSON|workbook|deck)\s+`?[\w/.\-]{2,80}`?\s+(has|have)\s+been\s+(written|saved|persisted|emitted|generated)\b.* |
        # Conditional capability pointer: "Use the renderers skill if a .docx is needed."
        (Use|Run|Invoke|Call|Hand\s+off\s+to)\s+(?:the\s+)?`?[\w\-/]+`?\s+(?:skill|tool|script|MCP|agent|renderer|generator)\s+(?:if|when|to|for)\b.* |
        # JSON list-item leak from on-disk artifact's warnings/notes/findings array
        "[^"]{2,200}\"?\]?\s*$ |
        # FAR 37.102(d) "no FTEs in body" governance directive (subcontractor-sow-builder
        # emits a chat-only staffing table separate from the artifact body):
        # "This staffing table is chat-only", "must not be pasted into the document",
        # "is ready for handoff to `price-to-win`"
        (This|The|That)\s+(staffing|FTE|salary|burden|wrap|loaded\s+rate|cost)\s+(table|line|figure|number|breakout|build)\s+(is|are)\s+(chat-?only|ready\s+for\s+(?:handoff|hand-?off|hand\s+off))\b.* |
        (\*\*)?(It\s+is|These\s+are|This\s+is)\s+NOT\s+part\s+of\s+the\s+(?:sub\s+)?(?:SOW|PWS|artifact|deliverable|document)\b.* |
        (\*\*)?(must|shall|should)\s+not\s+be\s+(pasted|copied|inserted|included|added)\s+(into|in|to)\s+(the\s+)?(document|appendix|SOW|PWS|artifact|deliverable)\b.* |
        # Section-level review/approval directive: "All Section 14 assumptions must be reviewed"
        (All|Each|Every)\s+Section\s+\d+(?:\.\d+)?\s+\w+\s+\*?\*?(must|should|shall)\*?\*?\s+be\s+(reviewed|verified|validated|approved|signed|finalized)\b.* |
        # Generic refinement caveat / next-step pointer: "Scope may need refinement..."
        (Scope|Pricing|Staffing|Coverage|Detail|Wording)\s+(may|might|will|could)\s+(need|require)\s+(refinement|further\s+(refinement|detail|definition)|adjustment|tightening)\b.* |
        # **Bold-line.** fragment from a multi-sentence bold-emphasized advisory block:
        # "**This table is chat-only. It is NOT part of the sub PWS...**" splits into
        # leading "**This table is chat-only." + trailing "...document or any appendix.**"
        \*\*[A-Z][^*\n]{2,80}\.\s*$ |
        [A-Z][^*\n]{2,200}\.\*\*\s*$ |
        # KG-availability / data-gap meta-disclosure (oci-sweeper, competitive-intel):
        # "No structured `incumbent`, `prior_contract`, ... entities were present in the KG"
        ([-*]\s+)?(No|Few|Some|Limited|Sparse|Insufficient|Partial)\s+(structured\s+)?[`\w\s,\-/]{2,200}?\s+(were|was|are|is)\s+(present|found|available|surfaced|captured|extracted|located|emerged)\s+(in|from|across|by|via)\b.* |
        # Negative-signal meta-disclosure: "No strong signals of X surfaced in the top chunks, so ..."
        ([-*]\s+)?(No|Few|Limited|Sparse)\s+(strong\s+)?(signals?|evidence|references?|hits?|matches?|results?)\s+(of|for|on)\b.* |
        # Methodology-fallback meta: "Analysis therefore relied on hybrid chunk retrieval ..."
        ([-*]\s+)?(Analysis|Search|Retrieval|Lookup|Query)\s+(?:therefore\s+)?(?:thus\s+)?(?:then\s+)?(?:relied|defaulted|fell\s+back|reverted)\s+(?:on|to)\b.* |
        # Warnings-array narrative: "Warnings note data gaps (e.g., ...)"
        ([-*]\s+)?Warnings?\s+(note|flag|highlight|capture|reflect|record|surface)\b.* |
        # Capture-team recommendation directive: "Capture lead should escalate the medium-risk finding ..."
        ([-*]\s+)?(Capture(?:\s+(?:lead|team|manager))?|PM|Pricing\s+lead|Bid\s+lead|Proposal\s+manager|KO|CO|AO)\s+should\s+(escalate|review|address|coordinate|draft|finalize|verify|validate|approve|sign|consult|engage)\b.* |
        # Conditional risk-reasoning leap (Class B): "If the KO confirms no non-public data crossed ..."
        ([-*]\s+)?If\s+the\s+(KO|CO|AO|customer|government|agency|prime|sub|contractor|incumbent|partner)\s+(confirms?|accepts?|denies?|grants?|approves?|rejects?|agrees?|certifies?|attests?)\b.* |
        # Next-step pointer: "Next step: Run proposal-generator to ..."
        ([-*]\s+)?Next\s+step:?\s+(Run|Invoke|Call|Hand\s+off\s+to|Pass\s+to|Forward\s+to)\b.* |
        # Captured-data observation: "The captured `X` and `Y` references reinforce ..."
        ([-*]\s+)?(The\s+)?captured\s+`?[\w\s,\-/]{2,80}`?\s+(and\s+`?[\w\s,\-/]{2,80}`?\s+)?references?\s+(reinforce|confirm|support|suggest|imply)\b.* |
        # Labor-line bullet (price-to-win cost-stack disclosure):
        # "- **5 Senior Software Developers**, DC metro (Washington-...), 1,880 productive hours/FTE/yr."
        [-*]\s+\*\*\d+\s+[A-Z][\w\s/\-]{2,80}\*\*,\s+.+ |
        # Derived-metric readout (computed from grounded inputs): "Base-year labor mid = $1.748M."
        # "Wrap rate = 2.45." "FBR mid = $186.20." "Total bid mid = $9.2M."
        [\w\-]+(?:\s+[\w\-]+){0,5}\s*[=:]\s*\$?\d+(?:[.,]\d+)?\s*[KMB%]?\b.{0,80}$ |
        # Null / zero-line declaration: "None specified, carried at $0." / "No hybrid elements ... were specified"
        ([-*]\s+)?(None|No|Zero)\s+\w+(?:[\s\w/\-()]{2,80})?(?:\s+(?:specified|provided|supplied|given|listed|noted))?\s*[,;:.\-—]\s*(?:carried\s+at\s+\$?0|treated\s+as\s+\$?0|set\s+to\s+\$?0|so\s+(?:pure|just|only)\s+)\b.* |
        # Reconciliation calculation with parenthetical math:
        # "Mid exactly reconciles to the incumbent's $9.2M last award (5 FTE × 1,880 hrs × $186.20 FBR × 5.256)."
        ([-*]\s+)?(?:Mid|High|Low|Total|Bid|Wrap|FBR|Rate)\s+(?:exactly\s+)?(?:reconciles?|matches?|aligns?|equals?|squares?|rounds?)\s+(?:to|with|against)\b.*[×x*].*\)\.?\s*$ |
        # Methodology vintage caveat: "BLS vintage gap (12-18 months); aged at standard 2.5%/yr but ..."
        ([-*]\s+)?(BLS|GSA|CALC\+?|OEWS|SCA|Per\s+Diem|FBR|Wrap|Rate|Burden)\s+(vintage|aging|cap|ceiling|gap|drift|lag|stale|fresh)\b.* |
        # Explicit reasoning-leap acknowledgment (Class B disclosure):
        # "Reasoning leaps (sweet spot, typical behavior, defensible reads, risk calls) are expert judgment ..."
        Reasoning\s+leaps?\s+\([^)]{2,200}\)\s+(?:are|is)\b.* |
        # Artifact-written + capability-pointer combo: "The artifacts/X.json envelope is written and ready for Y"
        (The\s+)?`?[\w/.\-]{2,80}`?\s+(envelope|artifact|file|workbook|deck)\s+is\s+(written|saved|persisted|emitted|generated|ready)\b.* |
        # Bold-bullet multi-count stat: "**Coverage:** 0 biased-ground-rules, **1 unequal-access**, 0 impaired-objectivity."
        \*\*[\w\s/-]{2,40}:\*\*\s*\d+\s+[\w\-]+(?:,\s*(?:\*\*)?\d+\s+[\w\-]+(?:\*\*)?)+\s*\.?\s*$ |
        # Definition-list bullet headers like "- **PWS (not SOW)**: Locked."
        # The substantive claim should live in the next sentence, not the header.
        [-*]\s+\*\*[^*]{2,120}\*\*\s*[:.\-—].{0,40}$ |
        # First-person process narration: "I anchored ...", "We pulled ..."
        (I|We)\s+(anchored|pulled|queried|loaded|invoked|called|read|inspected|verified|cross-?checked)\b.*
    )""",
    re.IGNORECASE | re.VERBOSE,
)

# Bold pointer headers with trailing parenthetical: "**Top warnings** (full list in artifact):"
# These act as section labels for a list-from-the-artifact, not standalone claims.
# Inner-paren capacity widened to 160 to accommodate longer FAR-classification
# parentheticals like "**Non-commercial (FAR Part 15)** (DoD-specialized threat
# hunting/detection engineering; not routinely sold to the general public)."
BOLD_POINTER_HEADER_RE = re.compile(
    r"^\s*[-*]?\s*\*\*[^*\n]{2,120}\*\*\s*\([^)]{2,160}\)\s*[:.\-—]?\s*$",
)

# Milestone bullet (artifact field disclosure): "- **M1** (Phase 1, Months 1-3): ...content..."
# These bullets walk the milestones[] array of the on-disk artifact one-by-one.
MILESTONE_BULLET_RE = re.compile(
    r"^\s*[-*]\s*\*\*[A-Z]\d+\*\*\s*\([^)]{2,120}\)\s*[:.\-—].*",
)

# Scope-block bullet (subcontractor-sow-builder Phase 2 disclosure): the skill's
# 6 scope blocks (Core/Delivery/Technical/Scale/Organizational/Quality) each
# emit a one-line readout of the form `- <Field>: <text> (... Block N[/M] ...).`
# The Block label may sit inside the same parens as descriptive content,
# preceded by `;` or `,` rather than `(`. These are envelope-field readouts.
SCOPE_BLOCK_BULLET_RE = re.compile(
    r"^\s*[-*]\s+[A-Z][\w\s/&-]{2,80}:\s+.+?[(;,]\s*Block\s+\d+(?:/\d+)?[^)]*\)\s*\.?\s*$",
)

# Structured-field readout (artifact field disclosure). Only credited when the
# run wrote a JSON artifact — these field names are the on-disk envelope's
# keys being spelled out for the human reader, source_chunks live in the JSON.
STRUCTURED_FIELD_RE = re.compile(
    r"""^\s*[-*]?\s*\*?\*?(
        Deliverables? |
        Exit\s+criterion |
        Exit\s+criteria |
        Traces?\s+to |
        TRL\s+in/?out |
        Payment\s+type |
        Total\s+\w+(?:\s+mid)? |
        Totals? |
        Authority |
        Milestone\s+structure |
        Workflow\s+chosen |
        Bid\s+cost\s+stack\s+summary |
        Bid\s+recommendation |
        Hand-?off |
        Statutory\s+citations? |
        KG\s+sources? |
        Rationale |
        Top\s+\d+\s+risk\s+flags? |
        Materials?/?ODCs? |
        Travel |
        Consortium\s+fee |
        Headcount(?:\s+equivalent)? |
        Mid\s+burdened\s+\w+ |
        CALC\+\s+context |
        Labor |
        Should-?cost |
        Government\s+obligation |
        Warnings? |
        Warning\s+flags? |
        Scope\s+blocks? |
        Section\s+\d+(?:[\.\-]\d+)?(?:\s+\([^)]{2,80}\))? |
        Recommended\s+\w+ |
        FAR\s+\d+\.\d+(?:-\d+)?\s+notes? |
        Acquisition\s+intake |
        Performance\s+work\s+statement |
        Parties |
        KO\s+question(?:\s+to\s+ask)? |
        Question |
        Recommendation |
        Mitigation |
        Coverage |
        Risk\s+(?:class|level|score|profile) |
        Verdict |
        Black-?hat\s+(?:envelope|read|brief) |
        Top\s+\d+\s+likely\s+competitors? |
        Incumbent |
        Competitors? |
        Award\s+history |
        Pricing\s+benchmarks?
    )\*?\*?\s*[:.\-—]""",
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


def _consulted_named_sources(turns: list[dict[str, Any]]) -> set[str]:
    """Collect named provenance anchors the runtime can verify the skill
    actually consulted in this run.

    Includes: bundled reference files read via ``read_file``, MCP tool
    families invoked (``mcp__bls_oews__*`` → 'bls', ``mcp__gsa_calc__*`` →
    'calc', etc.), and raw script paths run via ``run_script``.
    """
    sources: set[str] = set()
    for turn in turns:
        if (turn.get("kind") or "").lower() != "tool":
            continue
        name = (turn.get("name") or "").lower()
        # read_file calls — record the path the skill loaded
        if name == "read_file":
            args = turn.get("arguments") or turn.get("args") or {}
            if isinstance(args, dict):
                p = args.get("path") or args.get("file") or ""
                if isinstance(p, str) and p:
                    sources.add(p.lower())
        # MCP tool calls — record family from `mcp__<family>__<tool>` shape
        if name.startswith("mcp__"):
            parts = name.split("__")
            if len(parts) >= 2:
                family = parts[1]
                sources.add(f"mcp:{family}")
    return sources


def _wrote_json_artifact(turns: list[dict[str, Any]]) -> bool:
    """True if the run wrote any *.json artifact via write_file."""
    for t in turns:
        if t.get("kind") != "tool" or t.get("name") != "write_file":
            continue
        args = t.get("arguments") or {}
        if not isinstance(args, dict):
            args = {}
        path = (args.get("path") or "").lower()
        if path.endswith(".json"):
            return True
        # Some transcripts surface the path only in the result preview
        rp = (t.get("result_preview") or "").lower()
        if ".json" in rp and "path" in rp:
            return True
    return False


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
    if STRUCTURAL_LINE_RE.match(sentence):
        return True
    if BOLD_HEADING_RE.match(sentence):
        return True
    if BOLD_POINTER_HEADER_RE.match(sentence):
        return True
    if SCOPE_BLOCK_BULLET_RE.match(sentence):
        return True
    if MILESTONE_BULLET_RE.match(sentence):
        return True
    if COVER_NOTE_EXEMPT_RE.match(sentence):
        return True
    if REASONING_LEAP_RE.search(sentence):
        return True
    return False


def _is_grounded(
    sentence: str,
    retrieved_chunks: set[str],
    retrieved_entities: set[str],
    consulted_sources: set[str],
    wrote_json_artifact: bool = False,
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
    # Rule 3a-i: parenthetical attribution to the user prompt
    if USER_ATTR_RE.search(sentence):
        return True
    # Rule 3a-ii: named MCP / regulatory source the skill invoked
    if NAMED_SOURCE_RE.search(sentence):
        # Only credit if the skill *actually* invoked the matching MCP family
        # OR the named source is regulatory (FAR/DFARS/NIST) which is always
        # a verifiable external anchor.
        m = NAMED_SOURCE_RE.search(sentence)
        token = (m.group(0) if m else "").lower()
        if token.startswith(("far ", "dfars", "nist")):
            return True
        if token.startswith("bls") and "mcp:bls_oews" in consulted_sources:
            return True
        if token.startswith("calc") and "mcp:gsa_calc" in consulted_sources:
            return True
        if token.startswith("gsa") and any(s in consulted_sources for s in ("mcp:gsa_perdiem", "mcp:gsa_calc")):
            return True
        if token.startswith("ecfr") and "mcp:ecfr" in consulted_sources:
            return True
        if token.startswith("usaspending") and "mcp:usaspending" in consulted_sources:
            return True
    # Rule 3a-iii: reference bundle file the skill read
    for m in REF_BUNDLE_RE.finditer(sentence):
        ref_path = (m.group(1) or m.group(2) or "").lower()
        if not ref_path:
            continue
        # Match if any consulted source path ends with this reference
        if any(s.endswith(ref_path) or ref_path in s for s in consulted_sources):
            return True
    # Rule 3a-iii-b: bare-filename reference (e.g. "per trl_milestone_patterns.md")
    # — credited only if a consulted source path ends with the basename.
    for m in BARE_REF_RE.finditer(sentence):
        bare = m.group(1).lower()
        # Skip generic / common names; require at least one underscore or a path slash
        if "/" not in bare and "_" not in bare:
            continue
        basename = bare.rsplit("/", 1)[-1]
        if any(s.endswith("/" + basename) or s.endswith(basename) for s in consulted_sources):
            return True
    # Rule 3a-iv: hand-off to the JSON artifact the skill wrote this run
    if wrote_json_artifact and JSON_REF_RE.search(sentence):
        return True
    # Rule 3a-v: parenthetical source attribution backed by the on-disk artifact
    if wrote_json_artifact and SOURCE_PAREN_RE.search(sentence):
        return True
    # Rule 3a-vi: structured-field readout of an artifact key (Deliverables:,
    # Exit criterion:, Traces to:, etc.) \u2014 the value lives in the JSON,
    # source_chunks live alongside it.
    if wrote_json_artifact and STRUCTURED_FIELD_RE.match(sentence):
        return True
    return False


def audit(transcript_path: Path) -> dict[str, Any]:
    turns = _load_transcript(transcript_path)
    final = _final_assistant_text(turns)
    chunks = _retrieved_chunk_ids(turns)
    entities = _retrieved_entities(turns)
    consulted = _consulted_named_sources(turns)
    wrote_json = _wrote_json_artifact(turns)

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
        if _is_grounded(sent, chunks, entities, consulted, wrote_json):
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
