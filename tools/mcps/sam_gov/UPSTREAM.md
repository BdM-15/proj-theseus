# UPSTREAM — sam-gov-mcp

Vendored as a Theseus MCP via `uvx`; **no source code is copied into this repo**.
The runtime spawns the upstream package from PyPI on demand.

## Source

- **Repository**: https://github.com/1102tools/federal-contracting-mcps
- **Subdirectory**: `servers/sam-gov-mcp`
- **PyPI**: https://pypi.org/project/sam-gov-mcp/
- **License**: MIT (Copyright © 1102tools / James Jenrette)
- **Vendored commit**: `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)
- **Pinned version**: `0.4.1`

## Why this MCP

`sam-gov-mcp` is the **single largest upstream MCP by tool count** (19) and
the only practical way for Theseus to reach four critical federal-data
domains in one subprocess:

| Domain                     | Why Theseus needs it                                              |
| -------------------------- | ----------------------------------------------------------------- |
| Entity Registration        | Validate teaming partner / sub registration is active before bid  |
| Exclusions / Debarment     | Mandatory check per FAR 9.405 before any subcontract              |
| Contract Opportunities     | Active solicitations matching firm NAICS/PSC profile              |
| FPDS-NG Awards             | Historical award analysis (incumbent ID, recompete benchmarking)  |

**Note on FPDS:** Upstream consolidated FPDS data into `sam-gov-mcp` rather
than shipping a standalone `fpds-mcp`. `search_contract_awards` and
`lookup_award_by_piid` are the FPDS-NG endpoints surfaced through this MCP.

## Naming

| Surface                         | Value                  |
| ------------------------------- | ---------------------- |
| Theseus manifest `name`         | `sam_gov`              |
| Upstream PyPI package           | `sam-gov-mcp`          |
| Console script                  | `sam-gov-mcp`          |
| Upstream MCP `serverInfo.name`  | `sam-gov`              |
| Runtime tool namespace          | `mcp__sam_gov__*`      |

Underscore form is required for skill-frontmatter `metadata.mcps:` entries
because they must be valid Python identifiers.

## Tools (19)

**Entity Registration (5)**
- `lookup_entity_by_uei`
- `lookup_entity_by_cage`
- `search_entities`
- `get_entity_reps_and_certs`
- `get_entity_integrity_info`

**Exclusions (2)**
- `check_exclusion_by_uei`
- `search_exclusions`

**Contract Opportunities (2)**
- `search_opportunities`
- `get_opportunity_description`

**FPDS-NG Awards (3)**
- `search_contract_awards`
- `lookup_award_by_piid`
- `search_deleted_awards`

**Vendor Responsibility (1)**
- `vendor_responsibility_check`

**PSC Codes (2)**
- `lookup_psc_code`
- `search_psc_free_text`

**Federal Organizations (2)**
- `search_federal_organizations`
- `get_organization_hierarchy`

**Subawards (2)**
- `search_acquisition_subawards`
- `search_assistance_subawards`

## Authentication

**Required.** Free key at [sam.gov/content/api](https://sam.gov/content/api).

```bash
SAM_GOV_API_KEY=...
```

Manifest declares `env_required=["SAM_GOV_API_KEY"]`. The MCP client
checks `missing_env(...)` before spawning the subprocess and raises a
clean `MCPError` on absence.

**Rate limits:** Per-key throttling. Capture-team production use should
provision a system account key for higher quota.

## Re-vendor recipe

```powershell
# 1. Pick a new upstream commit
$commit = "<new-sha>"

# 2. Find the latest published version on PyPI
python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('https://pypi.org/pypi/sam-gov-mcp/json').read())['info']['version'])"

# 3. Update tools/mcps/sam_gov/theseus_manifest.json:
#    - "command": ["uvx", "--from", "sam-gov-mcp==<new-version>", "sam-gov-mcp"]
#    - "vendored_commit": "<commit>"
#    - "vendored_at": "<YYYY-MM-DD>"

# 4. Verify no breaking tool-surface changes
$env:THESEUS_LIVE_MCP="1"; .\.venv\Scripts\python.exe -m pytest tests/skills/test_sam_gov_manifest.py -v
```

## Companion tools in Theseus

- **`usaspending`** (Phase 4c) — outlay-side counterpart (USAspending.gov
  obligation/outlay data); pair with `sam_gov` `search_contract_awards`
  for full vendor financial picture.
- **`ecfr`** (Phase 4f.1) — clause text to cross-reference against
  `get_entity_reps_and_certs` output.
- **Future `competitive-intel` upgrade** — already declares
  `metadata.mcps: [usaspending]`; Phase 4f.6.x will add `sam_gov` for
  registration/exclusion validation.
