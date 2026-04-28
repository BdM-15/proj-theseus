# Phase 4f.4 — MCP Toolchain (GSA Per Diem)

This document covers installing, verifying, and troubleshooting the **fourth
no-key MCP server** wired into Theseus's Phase 4 skill runtime: the
[`gsa-perdiem-mcp`](https://github.com/1102tools/federal-contracting-mcps/tree/main/servers/gsa-perdiem-mcp)
server from `1102tools/federal-contracting-mcps`. It mirrors the prior
toolchain docs ([4c USAspending](PHASE_4C_MCP_TOOLCHAIN.md),
[4f.1 eCFR](PHASE_4F_ECFR_TOOLCHAIN.md),
[4f.3 GSA CALC+](PHASE_4F3_GSA_CALC_TOOLCHAIN.md)) — same vendoring pattern,
same test layers, same lifecycle.

## 0. Why this MCP, why now

- **Works without secrets.** The upstream falls back to api.data.gov's shared
  `DEMO_KEY` if no env var is set. End-to-end smoke tests are reproducible
  out of the box. (For real workloads, set `PERDIEM_API_KEY` to a free
  api.data.gov key for the 1,000 req/hr tier — see §1 below.)
- **Closes the IGCE travel gap.** GSA CALC+ (`gsa_calc`) covers labor;
  per diem covers the travel component. Together they cover the bulk of an
  IGCE for service contracts.
- **Production-hardened upstream.** 6 rounds of integration testing
  including a round-6 live audit with a real api.data.gov key. 413
  regression tests covering 1 P0 path-traversal bug, 23 P1 silent-wrong-data
  bugs, and 21 P2 validation gaps fixed.
- **Standard MCP transport.** stdio JSON-RPC — exact match for our
  `MCPSession` client (see
  [docs/PHASE_4A_MCP_CLIENT_DESIGN.md](PHASE_4A_MCP_CLIENT_DESIGN.md)).

## 1. Install

The server is **not vendored as source**. Theseus's manifest
([tools/mcps/gsa_perdiem/theseus_manifest.json](../tools/mcps/gsa_perdiem/theseus_manifest.json))
points at `uvx`, which fetches the pinned PyPI release into an ephemeral,
isolated environment per skill run:

```jsonc
{
  "command": ["uvx", "--from", "gsa-perdiem-mcp==0.2.6", "gsa-perdiem-mcp"],
  "env_required": [],
  "env_optional": ["PERDIEM_API_KEY"],
}
```

**Prerequisites:**

- `uv` ≥ 0.5 on `PATH` (already required by Theseus — `.venv` is managed by `uv`).
- Network access to PyPI on first run (uv caches the package thereafter).

**API key — strongly recommended for any real workload:**

The shared `DEMO_KEY` is rate-limited to **~10 req/hour across all
users globally**. A couple of skill invocations will exhaust it.

To get the 1,000 req/hr tier:

1. Sign up: <https://api.data.gov/signup/> (no approval, ~30 seconds).
2. Set both env vars in `.env`:

   ```bash
   API_DATA_GOV_KEY=<your-key>      # Theseus-side reservation for api.data.gov
   PERDIEM_API_KEY=<same-key>       # what gsa-perdiem-mcp actually reads
   ```

   The same key works for every api.data.gov-backed API (GSA Per Diem,
   NASA, FEC, FCC, etc.). The upstream server reads `PERDIEM_API_KEY`
   specifically — it does not look at `API_DATA_GOV_KEY`.

3. Restart the Theseus app so `.env` is reloaded.

The manifest declares `env_required=[]` so DEMO_KEY mode is allowed (CI /
smoke tests pass without keys); `PERDIEM_API_KEY` is forwarded to the
subprocess when present.

### Note — manifest name vs server name

| Layer                        | Value                      |
| ---------------------------- | -------------------------- |
| PyPI package                 | `gsa-perdiem-mcp`          |
| Console script               | `gsa-perdiem-mcp`          |
| Upstream `serverInfo.name`   | `gsa-perdiem`              |
| Theseus manifest `name`      | `gsa_perdiem`              |
| `metadata.mcps:` in SKILL.md | `gsa_perdiem`              |
| Runtime tool namespace       | `mcp__gsa_perdiem__<tool>` |

The underscore form (`gsa_perdiem`) is used in skill frontmatter and runtime
namespacing for Python-identifier consistency. See
[tools/mcps/gsa_perdiem/UPSTREAM.md](../tools/mcps/gsa_perdiem/UPSTREAM.md)
for the full re-vendor recipe.

## 2. Verify

### 2a. Discovery — manifest is loaded

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from src.skills.mcp_client import discover_manifests; m = discover_manifests(Path('tools/mcps')); print(sorted(m), m['gsa_perdiem'].command)"
```

Expected (with the four no-key MCPs vendored):

```
['ecfr', 'gsa_calc', 'gsa_perdiem', 'usaspending'] ['uvx', '--from', 'gsa-perdiem-mcp==0.2.6', 'gsa-perdiem-mcp']
```

### 2b. Live MCP — handshake responds

Manual JSON-RPC over stdio (PowerShell):

```powershell
$msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
$msg | uvx --from gsa-perdiem-mcp==0.2.6 gsa-perdiem-mcp 2>&1 | Select-Object -First 3
```

Expected first line:

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{...},"serverInfo":{"name":"gsa-perdiem","version":"1.27.0"}}}
```

### 2c. Through the registry — pytest

The opt-in live integration test:

```powershell
$env:THESEUS_LIVE_MCP = "1"
.\.venv\Scripts\python.exe -m pytest tests/skills/test_gsa_perdiem_manifest.py -v
```

Without `THESEUS_LIVE_MCP=1` the live test is skipped; only the manifest
parse / discovery test runs (default CI behavior — no network, no
subprocess).

### 2d. End-to-end through a skill (smoke)

Once a skill declares `metadata.mcps: ["gsa_perdiem"]` (planned: a future
`travel-cost` or `igce` skill on its own skill-creator branch), the runtime
will:

1. Spawn `uvx --from gsa-perdiem-mcp==0.2.6 gsa-perdiem-mcp` as a
   subprocess with `cwd=tools/mcps/gsa_perdiem`.
2. Forward `PERDIEM_API_KEY` from `.env` if set (else DEMO_KEY mode).
3. Perform the MCP `initialize` handshake.
4. Expose all 6 server tools as `mcp__gsa_perdiem__<tool>` to the LLM
   driving the skill.
5. Reap the subprocess in the run's `finally` block.

## 3. Troubleshooting

### `uvx: command not found`

`uv` is missing from `PATH`. Either install via the official installer
(<https://docs.astral.sh/uv/getting-started/installation/>) or, if uv is
already installed for this project, add `~/.cargo/bin` (or
`%USERPROFILE%\.local\bin` on Windows) to `PATH`.

### `429 Too Many Requests` from tool calls

You're hitting the DEMO_KEY rate limit (~10 req/hour shared globally).
Set `PERDIEM_API_KEY` to a free api.data.gov key (see §1) and restart
the Theseus app.

### "MCP gsa_perdiem failed to start"

Check the server's stderr — Theseus forwards it to a child logger named
`mcp.gsa_perdiem`. In `logs/server.log`:

```
grep "mcp.gsa_perdiem" logs/server.log
```

| Symptom in stderr            | Cause                            | Fix                                                                                              |
| ---------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------ |
| `error: Failed to fetch ...` | First-run network failure        | Verify PyPI is reachable; warm cache: `uvx --from gsa-perdiem-mcp==0.2.6 gsa-perdiem-mcp --help` |
| `protocolVersion mismatch`   | Upstream bumped MCP spec version | Bump our client `MCP_PROTOCOL_VERSION` constant in `mcp_client.py` and re-test                   |
| Slow handshake on first call | uv downloading deps              | Expected; raise `MCP_HANDSHAKE_TIMEOUT` env var if needed (default 10s)                          |

### Tool returns "first/last day reimbursed at 75%" or "rates not actual prices"

Not an error — that's the upstream surfacing 41 CFR 301-11 rules in
its responses. Quote per diem rates as **maximum reimbursement**, not as
**market price**. CONUS only; OCONUS rates are State-Department-published
(out of scope for this MCP).

### "Skill requested MCP 'gsa_perdiem' but no manifest is installed"

The skill is asking for an MCP that isn't in `tools/mcps/`. Either:

1. The skill is on a branch ahead of the MCP vendor — make sure both
   landed in the same commit / merge target.
2. Manifest path mismatch — confirm
   `tools/mcps/gsa_perdiem/theseus_manifest.json` exists (note exact
   directory name `gsa_perdiem` with underscore, not `gsa-perdiem-mcp`).

## 4. What's next

Per [docs/skills_roadmap.md](skills_roadmap.md), Phase 4f continues
**one MCP per branch**:

- **4f.5 — `federal-register` vendoring** (next, no key required):
  proposed/final rules, EOs, FAR cases.
- **4f.2 — `compliance-auditor` consumes eCFR** (skill-creator branch,
  future): use `skill-creator` to enhance the existing real skill so it
  can pull live FAR/DFARS clause text.
- **4g — `price-to-win` / IGCE skill** (skill-creator branch, future):
  the natural consumer of `gsa_calc` + `gsa_perdiem` (and eventually
  `bls_oews` once 4e UI lands).
- **4e — UI MCP panel**: required before vendoring key-gated MCPs
  (`sam-gov`, `bls-oews`, `regulations-gov`). API key placeholders
  already live in `.env` / `.env.example`.
