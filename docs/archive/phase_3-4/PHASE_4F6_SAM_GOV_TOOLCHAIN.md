# Phase 4f.6 — sam-gov-mcp Toolchain

Vendored as a Theseus MCP via `uvx`. **No source code copied** — runtime spawns
the upstream package from PyPI on demand. See
[`tools/mcps/sam_gov/UPSTREAM.md`](../tools/mcps/sam_gov/UPSTREAM.md)
for attribution and re-vendor recipe.

**First key-gated MCP in the vendored set.** Requires `SAM_GOV_API_KEY` (free
at [sam.gov](https://sam.gov/content/api)). Phase 4e's MCP Servers Settings
panel surfaces the key-status indicator in the UI.

## What it provides

19 read-only tools over the SAM.gov public API, spanning four data domains:

**Entity Registration (4)**
- `lookup_entity_by_uei` — full registration record by UEI
- `lookup_entity_by_cage` — full registration record by CAGE code
- `search_entities` — filter by name, NAICS, location, set-aside, etc.
- `get_entity_reps_and_certs` — FAR/DFARS reps & certs for a registered entity
- `get_entity_integrity_info` — past performance, integrity, fines

**Exclusions / Debarment (2)**
- `check_exclusion_by_uei` — fast yes/no with citation
- `search_exclusions` — full SAM exclusion list filter

**Contract Opportunities (2)**
- `search_opportunities` — active/expiring opportunities by NAICS, set-aside, agency, keyword, dates
- `get_opportunity_description` — full SOL package detail by notice ID

**FPDS-NG Awards (3)** — *upstream consolidated FPDS into sam-gov-mcp; there is no standalone FPDS MCP*
- `search_contract_awards` — historical awards by agency, NAICS, vendor, date, value
- `lookup_award_by_piid` — single award detail
- `search_deleted_awards` — recently-deleted FPDS rows (data-quality signal)

**PSC Codes (2)**
- `lookup_psc_code` — code → description + parent
- `search_psc_free_text` — natural-language → ranked PSC codes

**Federal Organizations (2)**
- `search_federal_organizations` — agency hierarchy search
- `get_organization_hierarchy` — full org tree from a node

**Subawards (2)**
- `search_acquisition_subawards` — FFATA subaward records on contracts
- `search_assistance_subawards` — FFATA subaward records on grants

**Vendor Responsibility (1)**
- `vendor_responsibility_check` — composite check: registration active +
  not excluded + integrity flags

## Why it ships in 4f.6

`sam-gov-mcp` is the **single largest upstream MCP by tool count** (19) and
unlocks four downstream skill upgrades:

| Skill                                  | Phase | Tools used                                                                                  |
| -------------------------------------- | ----- | ------------------------------------------------------------------------------------------- |
| `competitive-intel` (already shipped)  | 4f.6+ | `search_entities`, `search_contract_awards`, `lookup_award_by_piid`, `check_exclusion_by_uei` |
| `compliance-auditor` (already shipped) | 4f.6+ | `get_entity_reps_and_certs`, `check_exclusion_by_uei`, `vendor_responsibility_check`        |
| Future `opportunity-scout`             | 4g+   | `search_opportunities`, `get_opportunity_description`, `search_psc_free_text`               |
| Future `teaming-vetter`                | 4h+   | `vendor_responsibility_check`, `get_entity_integrity_info`, `search_acquisition_subawards`  |

## Configuration

**Required:**
```bash
SAM_GOV_API_KEY=...   # free at https://sam.gov/content/api
```

The manifest declares `env_required=["SAM_GOV_API_KEY"]`. The MCP client
(`src/skills/mcp_client.py`) checks `missing_env(...)` before spawning the
subprocess and raises a clean `MCPError` if absent — no cryptic upstream
traceback.

**Rate limits:** SAM.gov public APIs are throttled per API key. For
production capture work consider obtaining a system account key (higher
quota). Upstream documents specifics in their README.

## Verify

### Offline (always available)

```powershell
.\.venv\Scripts\python.exe -m pytest tests/skills/test_sam_gov_manifest.py -v
```

Expected: 3 passed, 1 skipped (live test gated on `THESEUS_LIVE_MCP=1` AND
`SAM_GOV_API_KEY` present).

### Live (spawns uvx subprocess; hits PyPI on first run + SAM.gov for handshake)

```powershell
$env:THESEUS_LIVE_MCP="1"
.\.venv\Scripts\python.exe -m pytest tests/skills/test_sam_gov_manifest.py::test_sam_gov_live_handshake_and_tools_list -v
```

The test auto-loads `.env` if present, so the SAM_GOV_API_KEY in your
project `.env` works without needing to export it manually.

Expected: 1 passed. First run downloads `sam-gov-mcp==0.4.1` into the uv
cache (~30 KB wheel + httpx + mcp deps); subsequent runs are warm.

### Manual handshake

```powershell
$env:SAM_GOV_API_KEY="..."   # if not already in env
uvx --from sam-gov-mcp==0.4.1 sam-gov-mcp
# (server starts on stdin/stdout — Ctrl+C to exit)
```

## Troubleshooting

### `MCPError: ... missing required env vars: ['SAM_GOV_API_KEY']`
Add the key to your `.env`. The runtime checks before spawn, so this fires
early — no subprocess started.

### `401 Unauthorized` from SAM.gov on tool calls
Key is malformed, expired, or not yet active. Verify at
[sam.gov/content/api](https://sam.gov/content/api). New keys can take
~24h to activate.

### `429 Too Many Requests`
Per-key rate limit hit. Back off and retry, or request a system account
key for higher quota.

### `uvx: command not found`
Install uv: `winget install astral-sh.uv` or
`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`.

### First-run cold start
`uvx` resolves and downloads the package on first invocation (~5–10s).
Cached after that. To pre-warm:
```powershell
uvx --from sam-gov-mcp==0.4.1 sam-gov-mcp --help
```

### `tools/list` returns nothing
Run the live test with `THESEUS_LIVE_MCP=1` and check the
`logs/server.log` MCP child logger for upstream stderr. The Settings →
MCP Servers panel (Phase 4e) surfaces the same stderr in the UI.

### SAM.gov API outage
SAM.gov is operated by GSA's Integrated Award Environment. Status:
[fsd.gov](https://fsd.gov/). If the API is down, all 19 tools will error —
there is no offline fallback.

## Downstream consumers

- **`competitive-intel`** (Phase 4d, already shipped on USAspending) —
  Phase 4f.6.x will add `metadata.mcps: [usaspending, sam_gov]` so it can
  cross-validate award history against active SAM registration + exclusion
  status.
- **`compliance-auditor`** (Phase 4f.2, already shipped on eCFR) — could
  add `vendor_responsibility_check` to flag teaming partners with active
  exclusions.
- **Future `opportunity-scout`** — daily/weekly scan of `search_opportunities`
  filtered against the firm's NAICS/PSC profile.
- **Future `teaming-vetter`** — composite go/no-go on potential
  subcontractors.

All consumers are pure read-only; no Theseus KG mutations.
