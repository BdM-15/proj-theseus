# UPSTREAM.md — rfp-reverse-engineer

## Source

Vendored from [`1102tools/federal-contracting-skills`](https://github.com/1102tools/federal-contracting-skills) — `skills/sow-pws-builder/` (READ DIRECTION).

- **License:** MIT © James Jenrette.
- **Vendor commit:** captured at branch creation; refresh via `tools/_skill_snapshots/` workflow.
- **Theseus phase:** 4h (`docs/skills_roadmap.md`).

## The 5-Point Stance-Inversion Contract

The upstream skill walks a federal CO **forward** through 3 acquisition-strategy intake answers + 6 scope-decision blocks, producing a SOW/PWS document. Theseus uses the same decision tree **backwards** — given a received RFP, reconstruct what the CO chose at each node, what's still open, and what the document is silent on (the silences are themselves signals). This contract documents the five inversions:

### 1. Direction: Forward Authoring vs Backward Decoding

|                   | Upstream (CO seat)                           | Theseus (bidder seat)                                                    |
| ----------------- | -------------------------------------------- | ------------------------------------------------------------------------ |
| Input             | User answers + workspace KG                  | Received RFP already in workspace KG                                     |
| Output            | A SOW/PWS document                           | A JSON envelope of CO decisions, gaps, traps, hooks                      |
| Decision Tree Use | Walked forward node-by-node, asking the user | Walked backward node-by-node, inferring from document signals            |
| Status semantics  | Each node "answered" or "defaulted"          | Each node `locked` (visible), `implied` (inference), or `open` (silence) |

### 2. Silence is a Signal

Forward direction: silence on a section means the CO must answer the question. Reverse direction: **silence is itself data.** A missing Section 13 Transition on a recompete signals an amendment is forthcoming. A missing Appendix B Volume Data signals capture-team Q&A is required. The reverse-engineer catalog (`references/rfp_signal_patterns.md`) treats every authoritative absence as a `missing_sections[]` entry with an inference rule — never as "the document is just incomplete".

### 3. Trap Detection (Reverse-Direction Only)

The forward skill protects the CO from authoring traps (e.g., not citing FAR 52.237-2 for Key Personnel). The reverse skill protects the bidder from **complying with the CO's traps**:

- Detect FAR 52.237-2 cited as Key Personnel → don't propose against a non-existent obligation; file Q&A.
- Detect bare `FAR 16.306` for CPFF → don't guess completion vs term form; file Q&A.
- Detect QASP↔CPARS conflation → don't accept a pre-committed CPARS rating; file Q&A.
- Detect Section 5 missing on T&M → don't bid without ceiling-hours clarification.
- Detect FTE counts in body → over-document own staffing assumptions in the proposal.

Each trap detection emits a structured `clarification_questions[]` entry, not a free-form warning.

### 4. Discriminator-Hook Surface (Bidder-Seat Specific)

Forward direction: the CO writes evaluation criteria. Reverse direction: the bidder reads evaluation criteria for **hidden preferences** that map to win themes — "most highly rated" ceilings, past-performance unlock phrases, ghost preferences, FAB-chain triggers, customer-priority echoes, pain-point confessions, weighted-factor spotlights. Each hook is structured handoff to `proposal-generator`, never written prose itself.

### 5. JSON-Envelope Output, NOT Markdown Document

Forward direction outputs a finished Markdown SOW/PWS. Reverse direction outputs a **JSON envelope** consumed by downstream skills (`proposal-generator`, `compliance-auditor`, `competitive-intel`, `price-to-win`). The envelope is the contract; the chat narrative is human-facing color commentary on top of the structured payload. The envelope MUST be cite-driven — every claim has `source_chunk_ids` or `kg_entities`.

## Architectural Note: Why Each Skill Owns Its Own `references/`

Theseus splits the upstream skill into two Theseus skills (`subcontractor-sow-builder` for the FORWARD seat; `rfp-reverse-engineer` for the REVERSE seat). Both consume the same intellectual content, but the runtime sandbox `tool_read_file` in `src/skills/tools.py` rejects cross-skill `references/` paths.

**Decision:** Each skill owns its own `references/` folder, with content **adapted to the workflow direction**:

- `subcontractor-sow-builder/references/`: section structure spec, decision-tree blocks, FAR citations for authoring, language rules.
- `rfp-reverse-engineer/references/`: reverse-engineering catalog (3 intake + 6 blocks BACKWARDS), discriminator hooks, RFP signal patterns (ghost language, missing sections), FAR citations for trap detection.

**Future TODO:** If references drift becomes a maintenance burden, introduce `extra_read_roots` in `src/skills/manager.py` and `src/skills/tools.py` mirroring the existing `script_paths` pattern (~30 lines). Tracked in `docs/PHASE_4H_SOW_SKILLS.md`.

## Re-Vendor Procedure

1. `git clone https://github.com/1102tools/federal-contracting-skills /tmp/upstream-fcs`.
2. Snapshot current state: `cp -r .github/skills/rfp-reverse-engineer tools/_skill_snapshots/rfp-reverse-engineer-pre-revendor/` (gitignored).
3. Diff `/tmp/upstream-fcs/skills/sow-pws-builder/` against `tools/_skill_snapshots/`. Note that upstream changes to forward-authoring rules typically map to **reverse-direction inference rules** — not 1:1 prose copies.
4. Apply only the changes that preserve the 5-point stance-inversion contract above.
5. Bump `metadata.version` and refresh `evals/evals.json` if behavior changed.
6. Re-run contract tests: `.\.venv\Scripts\python.exe -m pytest tests/skills/test_rfp_reverse_engineer_skill.py -v`.

## License Notice

Upstream is MIT-licensed. The original LICENSE text is preserved in the upstream repository. Modifications made by Theseus are documented in this file and in `docs/PHASE_4H_SOW_SKILLS.md`.
