# regulations-gov MCP — Upstream Attribution

## Source

- **Project:** [1102tools/federal-contracting-mcps](https://github.com/1102tools/federal-contracting-mcps)
- **Server path:** `servers/regulations-gov-mcp/`
- **PyPI package:** [`regulationsgov-mcp`](https://pypi.org/project/regulationsgov-mcp/) v0.2.5 (note: PyPI name has no hyphen between "regulations" and "gov")
- **Vendored commit:** `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)
- **License:** MIT

## What it provides

8 read-only tools wrapping the federal **Regulations.gov** public API. Regulations.gov is the official federal portal for rulemaking dockets, proposed/final rules, public comments, and comment-period tracking across every federal agency. In federal contracting it surfaces:

- **In-flight FAR/DFARS amendments** before they hit eCFR (and before they affect bids)
- **Public-comment activity** on proposed rules — early signal for industry posture and likely revisions
- **Open comment periods** — opportunities for the company to weigh in on rules that affect its business
- **Historical FAR case research** — full lifecycle of a FAR case from ANPR → NPRM → final rule

### Tool catalog

| Tool                   | Purpose                                                                             |
| ---------------------- | ----------------------------------------------------------------------------------- |
| `search_documents`     | Full-text search across rulemaking documents (proposed rules, final rules, notices) |
| `get_document_detail`  | Full content + metadata for a specific document by ID                               |
| `search_comments`      | Search public comments across dockets                                               |
| `get_comment_detail`   | Full content + metadata for a specific public comment                               |
| `search_dockets`       | Search rulemaking dockets across agencies                                           |
| `get_docket_detail`    | Full metadata for a specific docket (status, dates, related documents)              |
| `open_comment_periods` | List currently open comment periods (filterable by agency, topic)                   |
| `far_case_history`     | Convenience lookup — full document history for a FAR case number                    |

## Naming

- Theseus manifest name: `regulations_gov` (underscore — Python identifier requirement for the runtime registry)
- Upstream PyPI package: `regulationsgov-mcp` (no hyphen between "regulations" and "gov" — distinct from the folder name `regulations-gov-mcp`)
- Console script entry point: `regulationsgov-mcp`

## Spawning

The manifest declares:

```json
"command": ["uvx", "--from", "regulationsgov-mcp==0.2.5", "regulationsgov-mcp"]
```

`uvx` resolves the pinned version on first invocation and caches it; subsequent spawns are warm-start (~1–2 s on Windows). No source is copied into the Theseus tree.

## Re-vendor recipe

To bump to a newer release:

1. Check the latest version: `python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('https://pypi.org/pypi/regulationsgov-mcp/json').read())['info']['version'])"`
2. Identify the matching commit in [1102tools/federal-contracting-mcps](https://github.com/1102tools/federal-contracting-mcps)
3. Update `theseus_manifest.json`: bump version pin, `vendored_commit`, `vendored_at`
4. Update this `UPSTREAM.md`: matching version + commit
5. Re-run live test: `$env:THESEUS_LIVE_MCP="1"; python -m pytest tests/skills/test_regulations_gov_manifest.py -v`
6. If the tool catalog changed, update the table above and the marquee-tool assertion in the test

## Configuration

- `API_DATA_GOV_KEY` (required) — free at <https://api.data.gov/signup/>. The same key works across all api.data.gov-fronted services (Regulations.gov, FEC, NREL, etc.). Per-key rate limit (typically 1,000 requests/hour for registered users).

## Downstream consumers (planned)

These integrations are deferred to 4f.8.x sub-branches per the one-MCP-per-branch + `skill-creator`-MANDATE cadence:

- **4f.8.a** — `compliance-auditor` + `regulations_gov`: in-flight FAR/DFARS amendment detection (does a cited clause have a pending NPRM that changes its meaning?)
- **4f.8.b** — `competitive-intel` + `regulations_gov`: comment-period intelligence (which competitors filed comments on rules that affect this market?)
- New `regulatory-monitor` skill (Phase 4i): standing watch on FAR/DFARS rulemaking
