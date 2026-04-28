# bls-oews MCP — Upstream Attribution

## Source

- **Project:** [1102tools/federal-contracting-mcps](https://github.com/1102tools/federal-contracting-mcps)
- **Server path:** `servers/bls-oews-mcp/`
- **PyPI package:** [`bls-oews-mcp`](https://pypi.org/project/bls-oews-mcp/) v0.2.7
- **Vendored commit:** `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)
- **License:** MIT

## What it provides

7 read-only tools wrapping the U.S. Bureau of Labor Statistics **Occupational Employment and Wage Statistics (OEWS)** public API. OEWS is the authoritative federal source for hourly + annual wage statistics by SOC (Standard Occupational Classification) code and metro area, used to construct Independent Government Cost Estimates (IGCEs), perform price-reasonableness analysis on labor-heavy proposals, and benchmark proposed labor rates against market data.

### Tool catalog

| Tool                    | Purpose                                                                                     |
| ----------------------- | ------------------------------------------------------------------------------------------- |
| `get_wage_data`         | Hourly + annual wage percentiles for a (SOC code, metro area) pair                          |
| `compare_metros`        | Wage comparison for one occupation across multiple metro areas                              |
| `compare_occupations`   | Wage comparison for multiple occupations within one metro area                              |
| `igce_wage_benchmark`   | IGCE-ready labor-rate benchmark (mean / median / 25th-75th percentile) for a SOC + locality |
| `detect_latest_year`    | Latest published OEWS data year (so callers don't hard-code a stale year)                   |
| `list_common_soc_codes` | Reference helper — common SOC codes for federal-contracting-relevant occupations            |
| `list_common_metros`    | Reference helper — common metro area codes (CBSA / MSA)                                     |

## Naming

- Theseus manifest name: `bls_oews` (underscore — Python identifier requirement for the runtime registry)
- Upstream PyPI package: `bls-oews-mcp` (hyphenated)
- Console script entry point: `bls-oews-mcp`

## Spawning

The manifest declares:

```json
"command": ["uvx", "--from", "bls-oews-mcp==0.2.7", "bls-oews-mcp"]
```

`uvx` resolves the pinned version on first invocation and caches it; subsequent spawns are warm-start (~1–2 s on Windows). No source is copied into the Theseus tree.

## Re-vendor recipe

To bump to a newer release:

1. Check the latest version on PyPI: `python -c "import urllib.request,json; print(json.loads(urllib.request.urlopen('https://pypi.org/pypi/bls-oews-mcp/json').read())['info']['version'])"`
2. Identify the matching commit in [1102tools/federal-contracting-mcps](https://github.com/1102tools/federal-contracting-mcps) (check the server's `pyproject.toml` version + git log)
3. Update `theseus_manifest.json`: bump `command[2]` version pin, `vendored_commit`, `vendored_at`
4. Update this `UPSTREAM.md`: matching version + commit
5. Re-run live test: `$env:THESEUS_LIVE_MCP="1"; python -m pytest tests/skills/test_bls_oews_manifest.py -v`
6. If the tool catalog changed, update the table above and the marquee-tool assertion in the test

## Configuration

- `BLS_API_KEY` (required) — free at <https://www.bls.gov/developers/home.htm>. Per-key daily quota; the server returns a 429 when exceeded.

## Downstream consumers (planned)

- `proposal-generator` — IGCE construction in cost volumes (`igce_wage_benchmark` + `compare_metros` for locality factors)
- `competitive-intel` — labor-rate benchmarking for price-to-win analysis
- New `pricing-analyst` skill (Phase 4g) — price-reasonableness audits

These integrations are deferred to 4f.7.x sub-branches to keep one MCP per branch and apply `skill-creator` cleanly to each downstream skill enhancement.
