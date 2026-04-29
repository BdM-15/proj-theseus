# Phase 4f.5 — federal-register-mcp Toolchain

Vendored as a Theseus MCP via `uvx`. **No source code copied** — runtime spawns
the upstream package from PyPI on demand. See
[`tools/mcps/federal_register/UPSTREAM.md`](../tools/mcps/federal_register/UPSTREAM.md)
for attribution and re-vendor recipe.

## What it provides

8 read-only tools over the public Federal Register API (1994–present):

**Core**
- `search_documents` — flexible filters (agency, type, term, docket, dates, RIN)
- `get_document` — full details for a single document by FR number
- `get_documents_batch` — fetch up to 20 documents in one call
- `get_facet_counts` — document counts by type, agency, or topic
- `get_public_inspection` — pre-publication documents
- `list_agencies` — all ~470 agencies with slugs

**Workflow**
- `open_comment_periods` — currently open comment periods, sorted by deadline
- `far_case_history` — full rulemaking history for a FAR/DFARS case

## Why it ships before key-gated MCPs

`federal-register-mcp` is the regulatory-pipeline companion to `ecfr-mcp`
(Phase 4f.1). Together they cover:

| Question                                                         | MCP                |
| ---------------------------------------------------------------- | ------------------ |
| "What does FAR 52.222-50 say *right now*?"                       | `ecfr`             |
| "What FAR cases have open comment periods *this week*?"          | `federal_register` |
| "Trace FAR Case 2023-008 from proposed → final rule."            | `federal_register` |
| "Read the codified text of the rule that just became final."     | `ecfr`             |

This is also a **no-key MCP**, which lets us continue the one-MCP-per-branch
cadence without waiting on the Phase 4e UI work for credential management.

## Configuration

**None required.** The Federal Register API is fully public:
- No API key
- No registration
- No rate-limit token

The manifest declares `env_required=[]` and `env_optional=[]`.

## Verify

### Offline (always available)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/skills/test_federal_register_manifest.py -v
```

Expected: 3 passed, 1 skipped (live test gated on `THESEUS_LIVE_MCP=1`).

### Live (spawns uvx subprocess; hits PyPI on first run)

```powershell
$env:THESEUS_LIVE_MCP="1"
.\.venv\Scripts\python.exe -m pytest tests/skills/test_federal_register_manifest.py::test_federal_register_live_handshake_and_tools_list -v
```

Expected: 1 passed. First run downloads `federal-register-mcp==0.2.7` into
the uv cache (~12 KB wheel + httpx + mcp deps); subsequent runs are warm.

### Manual handshake

```powershell
uvx --from federal-register-mcp==0.2.7 federal-register-mcp
# (server starts on stdin/stdout — Ctrl+C to exit)
```

## Troubleshooting

### `uvx: command not found`
Install uv: `winget install astral-sh.uv` or
`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.

### First-run cold start
`uvx` resolves and downloads the package on first invocation (~5–10s).
Cached after that. To pre-warm:
```powershell
uvx --from federal-register-mcp==0.2.7 federal-register-mcp --help
```

### `tools/list` returns nothing
Run the live test with `THESEUS_LIVE_MCP=1` and check the
`logs/server.log` MCP child logger for upstream stderr.

### Federal Register API outage
The Federal Register API is operated by the Office of the Federal Register
(National Archives). Status: https://www.federalregister.gov/. If the API
is down, all 8 tools will error — there is no offline fallback.

## Downstream consumers

- **Future `regulatory-watch` skill** — cross-reference `far_case_history`
  output against `ecfr` clause text to flag clauses about to change.
- **`compliance-auditor` skill** — could use `open_comment_periods` to
  warn when a clause cited in an active solicitation is mid-revision.

Both consumers are pure read-only; no Theseus KG mutations.
