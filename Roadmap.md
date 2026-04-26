# Project Theseus — Roadmap

> Living pick-up doc. Captures current state, in-flight work, deferred work, and a prioritized backlog. Edit freely.

---

## 1. Current State

### Branches

| Branch                          | Status                                     | Notes                                                                                                                                                                       |
| ------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `main`                          | Default. 5 commits ahead of `origin/main`. | Includes 095 prompt library, 265f666 subfactor fix, 097 Mix default (unmerged feature branch), and 098 query-params panel (merged today).                                   |
| `095-prompt-library-expansion`  | Merged into `main`.                        | Prompt Library xlsx ingest + 23-prompt rewrite. Done.                                                                                                                       |
| `096-rfp-intelligence-overhaul` | **Deleted.**                               | Tier-1 fix cherry-picked to `main` as `265f666`. UI work (5-tier matcher, `5b6c184`) preserved in git reflog and tracked under issue #85.                                   |
| `097-chat-default-mix`          | **Unmerged.** Holds `cd555bd`.             | Capture Chat default mode → Mix in 4 places. Small fix; merge whenever convenient.                                                                                          |
| `098-settings-query-params`     | Merged into `main` as `779b898` (Apr 25).  | Per-workspace LightRAG query parameter editor in Settings. Defaults pulled from `.env` via `Settings`.                                                                      |
| `099-capture-chat-polish`       | Merged into `main` as `421d9c0` (Apr 25).  | Vibrant chat redesign, thinking indicator, prompt picker modal, server-side `<think>` strip, assistant identity (avatar + Shipley Mentor label), animated streaming bubble. |

### Recent commits on `main`

- `58d7c85` — Merge `102-citation-chips`: inline `[N]` / `[N, M]` markers in assistant prose render as cyan pill chips. Click smooth-scrolls + cyan-flashes the matching `### References` entry. Skips code blocks and the References section. Orphan chips render gray. Bumped govcon_prompt to v3.2.0 with required-inline-citation rule on both `rag_response` and `naive_rag_response`.
- `e29bd7c` — Merge `101-chat-message-actions`: per-message action toolbar (Copy / Regenerate / Export on assistant; Copy / Edit on user). Hover-revealed pill row, color-coded (cyan / magenta / lime / amber). Export emits `.md` with YAML frontmatter (chat, workspace, mode, total_ms) + originating Question above Answer. Edit-in-place / version pager intentionally deferred.
- `9b2caee` — Merge `100-ui-theme-propagation`: vibrant aurora/glass treatment propagated to all panels (sidebar, topbar, navigation). Cyberpunk-mythology brand glyph (animated labyrinth + minotaur horns + circuit traces + Ariadne thread + glowing Θ core) replaces plain wordmark. 5-layer radial accent panel canvas (cyan/magenta/purple/lime/amber).
- `421d9c0` — Merge `099-capture-chat-polish`: vibrant chat redesign + thinking indicator (animated aurora canvas, hero gradient buttons, magenta Prompt Library pulse, prompt-picker modal, live Retrieving→Thinking→Writing status row, `_ThinkStripper` for xAI Grok reasoning leak, purple/plum assistant bubble with magenta→cyan accent stripe, brain-circuit Shipley Mentor avatar, animated streaming bubble border).
- `779b898` — Merge `098-settings-query-params`: per-workspace query parameter settings panel.
- `265f666` — `fix(inference): include subfactor entities as L↔M link targets` (cherry-picked from 096; the real bug fix worth keeping).
- `7187101` — Merge of `095-prompt-library-expansion`.
- `da5382b` — `origin/main` HEAD; merge of `094-theseus-capture-ui`.

### Open GitHub issues created from this roadmap

- **#85** — RFP Intelligence overhaul — coverage, accuracy, and visual redesign. _Blocked by Tier 1A graph quality pass below._

### Decision deferred

- _(none — `main` pushed Apr 25; `097` folded into `099`.)_

---

## 2. Active Backlog

### Polish/UX still rough after the dashboard pass

- **Documents page polish** — _"looks unfinished and unpolished."_ Row design, filters, document detail drawer, status badges.
- **Cypher-style KG visualizer presets** — preferred query: `MATCH (n:<workspace>) OPTIONAL MATCH (n)-[r]->(m:<workspace>) RETURN n,r,m`. Add one-click "show whole workspace" preset; current `*` label search works but isn't obvious.
- **Search page** — currently just a jump bar. Promote to a real entity/relationship/chunk explorer with type filters and result previews.
- **Settings page substance** — beyond Server Control + version tiles, surface editable `.env` knobs (`CHUNK_SIZE`, `CONTEXT_WINDOW`, rerank toggle, model overrides) with safe restart-on-save.

### Settings page — new features (added Apr 25)

- **Delete workspace feature.** Inspiration: `tools/workspace_cleanup.py`. Settings should list every workspace under `rag_storage/` (and any matching Neo4j workspace label, when `GRAPH_STORAGE=Neo4JStorage`) with size/document-count metadata, and offer a guarded delete (confirm dialog + typed workspace name). Deletion must remove: per-workspace `rag_storage/<name>/` directory, Neo4j subgraph for that workspace, any cached parses under `mineru/`. Reuse the cleanup tool's logic; do not reimplement deletion paths.
- **Query parameter editor.** ✅ Done (`779b898`, Apr 25). Per-workspace overrides at `rag_storage/<ws>/ui_query_settings.json`. Defaults read from `.env` via `Settings` (so `MIN_RERANK_SCORE=0.1`, `TOP_K`, `CHUNK_TOP_K`, etc. flow through). `response_type` intentionally omitted to mirror upstream LightRAG WebUI.

### Capture Chat — fix (added Apr 25)

- **Performance**: response retrieval is extremely slow in the UI; needs profiling (server round-trip, streaming hookup, frontend render). _Partially addressed by 099 (`<think>` strip removes wasted tokens; phase events surface retrieve_ms; thinking-elapsed timer makes wait visible). Underlying LLM latency still ~15s before first token._
- **Default query mode**: ✅ Done on `097-chat-default-mix` (`cd555bd`). Branch unmerged — needs to land on `main`.
- **Streaming**: ✅ End-to-end SSE streaming with phase events (`status: retrieving|generating`) live as of `099`. Tokens render as they arrive; Stop button cancels mid-stream. `<think>` segments stripped server-side.

### UI/UX continuation (added Apr 25 — next branch candidates)

Builds on the 099 chat polish. Each item is sized for its own branch.

1. ~~**Theme propagation** (`100-ui-theme-propagation`)~~ ✅ Merged `9b2caee`.
2. ~~**Per-message actions on assistant bubbles** (`101-chat-message-actions`)~~ ✅ Merged `e29bd7c`. Edit currently opens a fresh turn (preserves prior answer); destructive edit-in-place + version pager deferred.
3. ~~**Inline citation chips** (`102-citation-chips`)~~ ✅ Merged `58d7c85`. Chip click now opens the streamed Sources panel from `104` (with fallback to inline References list).
4. **Workspace quick-switcher** (`103-workspace-cmdk`) — Promote the workspace modal to a Cmd-K / Ctrl-K palette: keyboard-first, type-to-filter, recent-first. Currently a click-only modal; switching workspaces is a frequent action that deserves keyboard speed.

### Functional / RAG continuation (added Apr 25)

5. ~~**Streaming source references** (`104-stream-sources`)~~ ✅ Merged `c034c42`. SSE `event: sources` pre-flights `aquery_data` and ships chunks/references/counts before tokens; UI renders a collapsible "Sources (N)" drawer; inline `[N]` chips auto-open the drawer and scroll to the matching row. Tradeoff: retrieval runs twice per turn (acceptable for v1; can cache later). **Follow-up surfaced**: previews show raw HTML table dumps and `Table Analysis: / Image Path: / Structure:` blocks because that's what the LLM actually saw. See `106-source-preview-polish` below.
6. **Source preview polish** (`106-source-preview-polish`) — _Next._ Make the Sources drawer human-readable without re-indexing. Scope: (a) detect MinerU/RAGAnything multimodal block prefixes (`Table Analysis:`, `Image Path:`, `Structure:`, `Caption:`) and render a compact card with a content-type badge (📊 Table / 🖼 Image / Σ Equation / 📄 Text), the caption when present, and a small "view raw" expander; (b) when `Structure:` contains a `<table>`, parse it client-side and either render as a styled HTML table (clean cases) or summarize as `47 rows × 8 cols, columns: …` (messy cases); (c) always show the raw block on demand. **Out of scope** (defer to a later branch): re-running the VLM at ingest to store a plain-English summary alongside each chunk — that requires re-indexing every workspace.
7. **Conversation memory mode** (`105-chat-memory`) — Currently each message is independent. Wire follow-up turns to actually carry the previous turn's retrieved context (the chat header already promises "multi-turn · follow-ups carry context"). Options: (a) pass previous N message pairs as `conversation_history` to LightRAG `aquery`, (b) reuse last turn's retrieved chunks instead of re-retrieving when the question is a clear follow-up. Need to balance cost vs accuracy.

### Bypass mode UX (lower priority, after 105/106)

- When user picks `bypass`, swap the chat header to make it explicit: "no retrieval — pure LLM." Today the header still says "RAG over the workspace." Misleading.

### Polish ideas marked "future"

- Activity/timeline feed on dashboard (recent uploads, batch completions, restart events from `server.log`).
- Per-workspace health card (graph density, orphan ratio, last extraction run, post-processing status).
- Capture chat: saved/named conversations, export to markdown, citation pinning.
- Toast/notification center — capture and replay backend warnings (rate limits, MinerU GPU fallbacks, post-processing phase progress).
- **Compliance Matrix view** — proper L↔M cross-reference table populated from the KG (instructions ↔ evaluation factors ↔ SOW/PWS paragraphs), exportable.
- **Requirements Browser** — searchable/filterable table of all `shall`/`will` requirements with deliverable, eval factor, and proof-point coverage flags.
- **Win-Strategy panel** — surfaces hot buttons, customer pain points, win themes, discriminators, ghost opportunities.
- **Risk register** — categorized risks (technical/financial/operational/strategic/compliance) from KG + verbiage scoring.
- **Document Structure tree** — hierarchical view of `CHILD_OF`/parent-section relationships per document.
- **Section deep-dive drawer** — click a section, see its instructions, eval ties, deliverables, BOE drivers, gaps.

---

## 3. Proposed Overhaul (priority order)

### Tier 1A — Graph quality (highest priority)

**Driver**: User feedback during 096 review — _"The UI should not have to have add-on fixes. The data KG and VDB should just be clean to begin with."_

Symptoms observed in `afcap6_drfp`:

- Duplicate `proposal_instruction` entities for the same instruction (anchored vs unanchored variants).
- Spurious GUIDES edges (Small Business Participation linked to Combating Trafficking in Persons instruction).
- Unmapped Section M items (Past Performance) that obviously have a Section L counterpart.

Investigation areas (touches main processing, extraction prompt, and post-processing):

- **Extraction prompt anchor discipline** — `prompts/extraction/govcon_lightrag_native.txt` should require canonical naming for `proposal_instruction` entities (e.g., `<anchor> <title>` format always when an anchor exists; never both forms). Likely needs a coreference example showing `L.3.3.10 Combatting…` as canonical and `Combating Trafficking in Persons Plan` as alias.
- **Phase 2 entity normalization** — Audit `src/inference/algorithms/`. Anchored vs unanchored variants of the same entity should merge.
- **Phase 4 `infer_lm_links` precision** — Algorithm is over-eager. Options:
  - Tighten the LLM prompt with a "do NOT link unless the instruction's _subject matter_ is graded by the factor" rule.
  - Add a confidence floor / require justification quote in output schema.
  - Or: post-filter LLM output by keyword/topic overlap before writing edges.
- **Past Performance gap** — Section M Past Performance factors aren't getting GUIDES edges to the Section L past-performance instructions. Likely the factor entity isn't being extracted with enough description for the LLM linker to recognize the topic. Check extraction output.

Acceptance criteria:

- Re-extract `afcap6_drfp`. Each Section L instruction appears exactly once. No spurious cross-topic GUIDES edges. Past Performance factor links to Past Performance instruction.

### Tier 1 — Accuracy fixes (the ground truth must be right)

A. **Multi-relationship L↔M matcher.** Treat any of these as L→M evidence: `GUIDES`, `EVALUATED_BY`, `EVALUATES`, `ADDRESSES`, `COVERS`, `REQUIRES`, `INFORMS`, `SUPPORTS`, `SUBMITS_TO`. Surface which relationship type produced the match. _(5-tier walker landed in `5b6c184`; preserved under issue #85.)_

B. **Subfactor inheritance.** ✅ Done — `265f666` on `main`.

C. **Indirect-chain walker (max 3 hops).** _(Landed in `5b6c184`; preserved under issue #85.)_

D. **Name/topic fallback for orphans.** For every orphaned factor, compute the top-3 instructions by:

- Case-insensitive substring/phrase overlap on `entity_id` + description
- Shared chunk membership (same `chunk_ids`)
  Surface as "Candidate links — click to confirm" rather than auto-merging.

E. **Confidence + provenance column.** Each row shows: rel type that matched (or "candidate"), confidence score from the edge, source chunk citations.

### Tier 2 — New intelligence panels (the routine topics)

F. **Past Performance panel.** Dedicated tab. Lists every `past_performance_reference`, every Section L instruction asking for past performance, every Section M factor evaluating it, the page/word limits, and matches our cited past performance to required experience areas.

G. **Technology Inventory.** Roll up `technology` and `technical_specification` entities. Group by category (platforms, languages, tools, standards, GFE/GFI). Flag "named with version constraints" vs "mentioned generically."

H. **Innovation Signals panel.** Pattern-based scan across chunks for innovation/modernization language: _innovative, modernize, transformation, novel, emerging, next-generation, reimagine, AI/ML, cloud-native, agile, DevSecOps, automation, predictive, optimize, efficiency, accelerate_. For each hit, show source paragraph, section, and classification (Mandate / Encouragement / Aspirational).

I. **Acronym & Terminology Glossary.** Auto-extract every defined acronym + glossary term in the RFP.

J. **Customer Hot Buttons & Pain Points.** Already extracted as entity types — just needs a panel.

K. **Deliverable Catalog with cadence.** Every deliverable + its frequency / due date / owner / receiving organization.

### Tier 3 — Quality of life

L. **Per-row "Ask Theseus" button** on every panel that pre-fills the chat with a Shipley-mentor prompt scoped to that row.

M. **Export to CSV/XLSX** for matrix, traceability, gap, tech inventory, and innovation-signal panels.

N. **Diff vs prior compute.** Cache last summary; show what changed since last extraction.

---

## 4. Suggested next session sequence

1. ✅ ~~Merge `097-chat-default-mix`~~ — landed via `099` polish work.
2. ✅ ~~Push `main`~~ — pushed Apr 25 (`421d9c0`).
3. ✅ ~~Capture Chat polish~~ — landed as `099-capture-chat-polish` / `421d9c0`.
4. **`100-ui-theme-propagation`** — apply the chat polish vocabulary across Documents/Intel/Settings/Workspaces/Search.
5. **`101-chat-message-actions`** — Copy / Regenerate / Export / Cite-source toolbar on assistant bubbles.
6. **`102-citation-chips`** — clickable `[N]` chips that scroll to the References block in each assistant message.
7. **`103-workspace-cmdk`** — Cmd-K workspace quick-switcher.
8. ~~**`104-stream-sources`**~~ ✅ Merged `c034c42` (Apr 26). SSE `event: sources` + collapsible Sources panel; chips open the panel.
9. **`106-source-preview-polish`** — _Next._ Detect MinerU table/image blocks in chunk previews and render a compact card with a content-type badge + caption + collapsed raw expander; client-side `<table>` re-render or row/col summary. No re-indexing.
10. **`105-chat-memory`** — multi-turn conversation_history wiring; honor the "follow-ups carry context" promise in the header.
10. **`106-settings-delete-workspace`** — reuse `tools/workspace_cleanup.py`. (Was item 4 in prior plan; bumped behind UI polish run.)
11. **`107-graph-quality-pass`** (formerly Tier 1A) — extraction prompt anchor discipline + Phase 2 normalization audit on `afcap6_drfp`. Re-extract and validate.
12. **Iterate** Tier 1A until `afcap6_drfp` matrix renders cleanly without UI tightening.
13. **Then** revisit issue #85 (RFP Intelligence overhaul) on top of clean data.
14. Polish backlog items (Documents page, KG visualizer presets, Search page) interleaved between graph-quality re-runs.
