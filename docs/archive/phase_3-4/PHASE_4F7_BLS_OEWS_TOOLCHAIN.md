# Phase 4f.7 — bls-oews MCP Toolchain

**Branch:** `131-phase-4f7-bls-oews-mcp` → integrates into `120-skills-spec-compliance`
**Vendored:** `bls-oews-mcp` v0.2.7 (commit `aef1961`, 2026-04-28)
**Status:** ✅ vendored, tests passing, no skill consumers yet (deferred to 4f.7.x)

## Overview

`bls-oews-mcp` wraps the U.S. Bureau of Labor Statistics **Occupational Employment and Wage Statistics (OEWS)** public API. OEWS is _the_ authoritative federal source for hourly + annual wage data by SOC (Standard Occupational Classification) code and metro area. In federal contracting it is the data backbone for:

- **Independent Government Cost Estimates (IGCEs)** — what should this work cost?
- **Price-reasonableness analysis** — are the bidder's labor rates within market range?
- **Price-to-win modeling** — what labor-rate stack is most competitive?
- **Locality factor adjustments** — DC-metro vs. Huntsville vs. San Antonio rates for the same SOC

This is the second key-gated MCP we've vendored (after `sam-gov-mcp`). Same pattern: manifest declares `env_required=["BLS_API_KEY"]`; `MCPSession.missing_env()` raises a clean `MCPError` before subprocess spawn if absent.

## Tool catalog (7 tools)

### Wage data

| Tool                  | Inputs (typical)                           | Returns                                                            |
| --------------------- | ------------------------------------------ | ------------------------------------------------------------------ |
| `get_wage_data`       | SOC code, metro/CBSA code, year (optional) | Hourly + annual percentiles (10th, 25th, mean, median, 75th, 90th) |
| `igce_wage_benchmark` | SOC code, locality, target percentile      | IGCE-ready single labor-rate point estimate with uncertainty band  |

### Comparison

| Tool                  | Inputs                       | Returns                               |
| --------------------- | ---------------------------- | ------------------------------------- |
| `compare_metros`      | One SOC code, list of metros | Side-by-side wage table across metros |
| `compare_occupations` | One metro, list of SOC codes | Side-by-side wage table across SOCs   |

### Reference helpers

| Tool                    | Purpose                                                                                                |
| ----------------------- | ------------------------------------------------------------------------------------------------------ |
| `detect_latest_year`    | Returns the latest published OEWS data year so callers don't hard-code a stale year                    |
| `list_common_soc_codes` | Curated list of SOC codes most relevant to federal contracting (PM, SETA, SWE, cyber, logistics, etc.) |
| `list_common_metros`    | Curated list of CBSA/MSA codes for major federal-contracting metros                                    |

## Configuration

```env
# .env
BLS_API_KEY=<free key from https://www.bls.gov/developers/home.htm>
```

Free signup; the BLS rate-limits per key (typically 500 queries/day for registered users — well above interactive Theseus usage).

## Verify

### Offline (no API key needed)

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests/skills/test_bls_oews_manifest.py -v
```

Should show 3 passed + 1 skipped (live test gated).

### Live handshake (requires BLS_API_KEY in .env)

```powershell
$env:THESEUS_LIVE_MCP="1"
python -m pytest tests/skills/test_bls_oews_manifest.py -v
```

Should show 4 passed. Confirms 7 tools advertised and all marquee tools present.

### Manual smoke test

```powershell
python -c "
import asyncio, os
from dotenv import load_dotenv; load_dotenv()
from src.skills.mcp_client import load_manifest, MCPSession
from pathlib import Path
m = load_manifest(Path('tools/mcps/bls_oews/theseus_manifest.json'))
async def go():
    s = MCPSession(m); await s.start()
    print('tools:', [t.name for t in s.tools])
    await s.shutdown()
asyncio.run(go())
"
```

## Troubleshooting

| Symptom                                                    | Cause                                       | Fix                                                                                     |
| ---------------------------------------------------------- | ------------------------------------------- | --------------------------------------------------------------------------------------- |
| `MCPError: missing required env var(s): BLS_API_KEY`       | Key not in `.env` or environment            | Add `BLS_API_KEY=...` to `.env`; restart shell or call `load_dotenv()`                  |
| Tool call returns `429 Too Many Requests`                  | Daily quota exceeded for the registered key | Wait until next UTC day, or request a higher quota at bls.gov                           |
| Tool call returns `400 Bad Request` for SOC/metro          | Invalid SOC code or unrecognized CBSA       | Use `list_common_soc_codes` / `list_common_metros` first to discover valid codes        |
| Cold start ~15s on first invocation                        | `uvx` is downloading + caching the package  | Subsequent spawns are 1–2s; this is normal                                              |
| `ValueError: I/O operation on closed pipe` ResourceWarning | Cosmetic Windows asyncio cleanup race       | Ignore — pytest exit code may be 1 even when all tests pass; trust the "X passed" count |
| OEWS data appears stale                                    | OEWS publishes annually (typically May)     | Call `detect_latest_year` first; don't hard-code year in client code                    |

## Downstream consumers (deferred to 4f.7.x)

These skill enhancements are intentionally split into separate sub-branches per the one-MCP-per-branch + `skill-creator`-MANDATE cadence:

- **4f.7.a** — `proposal-generator` + `bls_oews`: IGCE table generation in cost-volume drafts; locality-adjusted labor-rate stacks
- **4f.7.b** — `competitive-intel` + `bls_oews`: market labor-rate benchmarking for incumbent black-hat analysis (compare incumbent's published rates to OEWS market median)
- **4f.7.c** — Net-new `pricing-analyst` skill (Phase 4g preview): IGCE-vs-bid variance audits

## What's next

- **Phase 4f.8** — vendor `regulations-gov` MCP (key-gated by `API_DATA_GOV_KEY`, also already in `.env`). Last of the 1102tools federal-contracting-mcps to vendor.
- After 4f.8, the MCP-vendoring stretch (4f.1–4f.8) is complete and we move to **Phase 4g** (price-to-win) and **4f.x.y** downstream skill consumers.
