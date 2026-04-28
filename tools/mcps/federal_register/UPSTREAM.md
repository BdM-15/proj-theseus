# UPSTREAM — federal-register-mcp

Vendored as a Theseus MCP via `uvx`; **no source code is copied into this repo**.
The runtime spawns the upstream package from PyPI on demand.

## Source

- **Repository**: https://github.com/1102tools/federal-contracting-mcps
- **Subdirectory**: `servers/federal-register-mcp`
- **PyPI**: https://pypi.org/project/federal-register-mcp/
- **License**: MIT (Copyright © 1102tools / James Jenrette)
- **Vendored commit**: `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)
- **Pinned version**: `0.2.7`

## Why this MCP

`federal-register-mcp` is the natural companion to `ecfr-mcp` (Phase 4f.1):

| MCP                | Answers                                       | Update cadence       |
| ------------------ | --------------------------------------------- | -------------------- |
| `ecfr`             | "What does the rule say *right now*?"         | Daily eCFR snapshots |
| `federal_register` | "What is *changing* and when does it land?"   | Daily FR publication |

For Theseus, this closes two analyst gaps:
1. **FAR/DFARS rulemaking surveillance** — `far_case_history` traces a FAR
   case from proposed rule → comment period → final rule, useful when an RFP
   cites a clause whose text is mid-revision.
2. **Comment-period awareness** — `open_comment_periods` flags rules whose
   comment window is still open (capture teams may want to file).

## Naming

| Surface                         | Value                       |
| ------------------------------- | --------------------------- |
| Theseus manifest `name`         | `federal_register`          |
| Upstream PyPI package           | `federal-register-mcp`      |
| Console script                  | `federal-register-mcp`      |
| Upstream MCP `serverInfo.name`  | `federal-register`          |
| Runtime tool namespace          | `mcp__federal_register__*`  |

Underscore form is required for skill-frontmatter `metadata.mcps:` entries
because they must be valid Python identifiers.

## Tools (8)

**Core**
- `search_documents` — flexible filters (agency, type, term, docket, dates, RIN)
- `get_document` — full details for a single document by FR document number
- `get_documents_batch` — fetch up to 20 documents in one call
- `get_facet_counts` — document counts by type, agency, or topic
- `get_public_inspection` — pre-publication documents with client-side filtering
- `list_agencies` — all ~470 agencies with slugs

**Workflow**
- `open_comment_periods` — currently open comment periods, sorted by deadline
- `far_case_history` — full rulemaking history for a FAR/DFARS case

## Authentication

**None required.** The Federal Register API is fully public — no key, no
registration, no rate-limit token. Manifest declares
`env_required=[]` and `env_optional=[]`.

## Re-vendor recipe

```powershell
# 1. Pick a new upstream commit
$commit = "<new-sha>"

# 2. Find the latest published version on PyPI
python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('https://pypi.org/pypi/federal-register-mcp/json').read())['info']['version'])"

# 3. Update tools/mcps/federal_register/theseus_manifest.json:
#    - "command": ["uvx", "--from", "federal-register-mcp==<new-version>", "federal-register-mcp"]
#    - "vendored_commit": "<commit>"
#    - "vendored_at": "<YYYY-MM-DD>"

# 4. Verify no breaking tool-surface changes
$env:THESEUS_LIVE_MCP="1"; .\.venv\Scripts\python.exe -m pytest tests/skills/test_federal_register_manifest.py -v
```

## Companion tools in Theseus

- **`ecfr`** (Phase 4f.1) — codified regulation text
- **`federal_register`** (Phase 4f.5, this) — proposed/final rule pipeline
- Future skill: `regulatory-watch` could cross-reference `far_case_history`
  output against `ecfr` clause text to flag clauses about to change.
