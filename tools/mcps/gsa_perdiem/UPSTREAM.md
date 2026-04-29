# GSA Per Diem MCP — vendor record

This directory holds **only** Theseus's manifest pointing at an upstream MCP
server. The server itself is fetched on-demand by `uvx` from PyPI — no source
code is checked into this repo.

## Upstream

- **Project**: [`1102tools/federal-contracting-mcps`](https://github.com/1102tools/federal-contracting-mcps)
- **Server**: `servers/gsa-perdiem-mcp/`
- **PyPI**: [`gsa-perdiem-mcp`](https://pypi.org/project/gsa-perdiem-mcp/)
- **License**: MIT
- **Pinned version**: `0.2.6`
- **Pinned upstream commit**: `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)

## API key handling

The upstream API (api.gsa.gov, rate-limited via api.data.gov) supports two modes:

| Mode                 | Source                               | Limit                                    |
| -------------------- | ------------------------------------ | ---------------------------------------- |
| `DEMO_KEY` (default) | Hardcoded fallback when env is unset | ~10 requests / hour, **shared globally** |
| Personal key         | `PERDIEM_API_KEY` env var            | 1,000 requests / hour, yours alone       |

**The same api.data.gov key works for every api.data.gov-backed API** (GSA
Per Diem, NASA, FEC, FCC, etc.). Theseus's `.env` keeps a single placeholder,
`API_DATA_GOV_KEY`, for that shared value. The upstream server reads
`PERDIEM_API_KEY` specifically, so `.env.example` ships a one-liner that
auto-derives it via python-dotenv interpolation:

```bash
# .env
API_DATA_GOV_KEY=<your-key>            # the only value you ever set
PERDIEM_API_KEY=${API_DATA_GOV_KEY}    # auto-derived; do not edit
```

The manifest declares `env_required=[]` (so DEMO_KEY mode is allowed),
plus `env_optional=["PERDIEM_API_KEY"]` so the runtime forwards the
interpolated value to the subprocess.

## Why a manifest, not a source vendor

Same rationale as the other vendored MCPs in `tools/mcps/`. The 1102tools
project ships its servers as PyPI packages with a console script entry
point (`gsa-perdiem-mcp`). `uvx` fetches the package into an ephemeral,
isolated environment per run — no impact on Theseus's `.venv`, no impact
on `pyproject.toml` / `uv.lock`. Re-vendoring is a one-line version bump
in `theseus_manifest.json`.

## Naming

| Layer                        | Value                      |
| ---------------------------- | -------------------------- |
| PyPI package                 | `gsa-perdiem-mcp`          |
| Console script               | `gsa-perdiem-mcp`          |
| Upstream `serverInfo.name`   | `gsa-perdiem`              |
| Theseus manifest `name`      | `gsa_perdiem`              |
| `metadata.mcps:` in SKILL.md | `gsa_perdiem`              |
| Runtime tool namespace       | `mcp__gsa_perdiem__<tool>` |

The underscore form (`gsa_perdiem`) is used in skill frontmatter and runtime
namespacing for Python-identifier consistency. Mirrors the same convention
used for `gsa_calc`.

The `--from` syntax pins the version explicitly so `uvx` doesn't silently
upgrade between runs:

```
uvx --from gsa-perdiem-mcp==0.2.6 gsa-perdiem-mcp
```

## Re-vendor / version bump recipe

1. Check the upstream release page:
   <https://github.com/1102tools/federal-contracting-mcps/releases>
2. Pick the new server version and verify it on PyPI:
   <https://pypi.org/project/gsa-perdiem-mcp/#history>
3. Smoke-test the new version locally before committing:

   ```powershell
   $msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
   $msg | uvx --from gsa-perdiem-mcp==<NEW_VERSION> gsa-perdiem-mcp 2>&1 | Select-Object -First 3
   ```

   Expect a JSON-RPC `initialize` response with
   `"serverInfo":{"name":"gsa-perdiem",...}`.

4. Update `theseus_manifest.json`:
   - Bump the pinned version in `command[2]` (the `--from` argument).
   - Update `vendored_commit` to the upstream commit that ships that version.
   - Update `vendored_at` to today's ISO date.

5. Run the Theseus regression tests:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/skills/
   ```

6. Propose the commit; user approves; FF-merge per
   `.github/copilot-instructions.md` Branch Management Strategy.

## Theseus integration

- Loaded by `src/skills/mcp_client.py::discover_manifests()`.
- Skills opt in by listing `metadata.mcps: ["gsa_perdiem"]` in their
  `SKILL.md` frontmatter.
- The runtime spawns `uvx --from ...` per skill run via `MCPRegistry`,
  forwards `PERDIEM_API_KEY` if present in the parent environment,
  exposes its 6 tools as `mcp__gsa_perdiem__<tool>`, and reaps the
  subprocess on completion.

## Tool surface (snapshot at v0.2.6)

6 tools:

**Core lookups**

- `lookup_city_perdiem` — Rates by city/state (auto-selects best NSA match)
- `lookup_zip_perdiem` — Rates by ZIP code
- `lookup_state_rates` — All NSA rates for a state
- `get_mie_breakdown` — M&IE tier table (meal components — breakfast/lunch/dinner/incidentals/first-and-last-day)

**Workflow**

- `estimate_travel_cost` — Calculate trip per diem (lodging + M&IE with first/last day at 75%)
- `compare_locations` — Compare rates across multiple cities

See the
[upstream README](https://github.com/1102tools/federal-contracting-mcps/blob/main/servers/gsa-perdiem-mcp/readme.md)
for full tool schemas.

## Important caveats (per upstream + 41 CFR 301-11)

- **Reimbursement ceilings, not actual hotel prices.** Per diem rates are
  the maximum federal reimbursement, not market price.
- **CONUS only.** OCONUS / foreign rates come from the State Department,
  not GSA — this server does not cover them.
- **Lodging taxes generally not included** in the lodging rate.
- **First and last travel day M&IE at 75%** per the FTR.

These caveats matter for IGCE travel estimation: don't quote per diem rates
as "what we'll spend on hotels" — quote them as "the max we can claim back."

## Removal

To remove this MCP from Theseus: delete this directory. No skill will silently
break — `metadata.mcps` is a closed allowlist and any skill referencing
`gsa_perdiem` will surface a clear "MCP not found" warning at load time.
