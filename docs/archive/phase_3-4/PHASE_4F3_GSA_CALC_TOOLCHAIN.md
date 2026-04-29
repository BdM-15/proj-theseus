# Phase 4f.3 — MCP Toolchain (GSA CALC+)

This document covers installing, verifying, and troubleshooting the **third
no-key MCP server** wired into Theseus's Phase 4 skill runtime: the
[`gsa-calc-mcp`](https://github.com/1102tools/federal-contracting-mcps/tree/main/servers/gsa-calc-mcp)
server from `1102tools/federal-contracting-mcps`. It mirrors the
[Phase 4c USAspending toolchain](PHASE_4C_MCP_TOOLCHAIN.md) and the
[Phase 4f eCFR toolchain](PHASE_4F_ECFR_TOOLCHAIN.md) — same vendoring
pattern, same test layers, same lifecycle.

## 0. Why this MCP, why now

- **Zero secrets.** GSA CALC+ is a fully public API — no API key, no signup.
  End-to-end smoke tests are fully reproducible. The upstream API enforces a
  1,000 requests/hour rate limit; skills should batch tool calls accordingly.
- **High signal for govcon pricing.** 8 read-only tools cover GSA MAS labor
  ceiling rates across 230K+ records, with workflow-grade
  `igce_benchmark` / `price_reasonableness_check` / `vendor_rate_card` /
  `sin_analysis` calls. Drops directly into the future `price-to-win` skill
  (Phase 4g, separate skill-creator branch).
- **Production-hardened upstream.** 4 retroactive live audit rounds, 314
  regression tests, 49 P1 bugs + 19 P2 validation gaps + 12 deep-audit
  findings fixed.
- **Standard MCP transport.** stdio JSON-RPC — exact match for our
  `MCPSession` client (see
  [docs/PHASE_4A_MCP_CLIENT_DESIGN.md](PHASE_4A_MCP_CLIENT_DESIGN.md)).

## 1. Install

The server is **not vendored as source**. Theseus's manifest
([tools/mcps/gsa_calc/theseus_manifest.json](../tools/mcps/gsa_calc/theseus_manifest.json))
points at `uvx`, which fetches the pinned PyPI release into an ephemeral,
isolated environment per skill run:

```jsonc
{
  "command": ["uvx", "--from", "gsa-calc-mcp==0.2.7", "gsa-calc-mcp"]
}
```

**Prerequisites:**

- `uv` ≥ 0.5 on `PATH` (already required by Theseus — `.venv` is managed by `uv`).
- Network access to PyPI on first run (uv caches the package thereafter).

**No action required on your part** — the registry discovers the manifest
on `SkillManager` startup; the subprocess is spawned the first time a skill
with `metadata.mcps: ["gsa_calc"]` is invoked.

### Note — manifest name vs server name

Unlike the eCFR vendor record (where Theseus's manifest name and the upstream
`serverInfo.name` both equal `ecfr`), GSA CALC+ has a small mismatch:

| Layer                          | Value          |
| ------------------------------ | -------------- |
| PyPI package                   | `gsa-calc-mcp` |
| Console script                 | `gsa-calc-mcp` |
| Upstream `serverInfo.name`     | `gsa-calc`     |
| Theseus manifest `name`        | `gsa_calc`     |
| `metadata.mcps:` in SKILL.md   | `gsa_calc`     |
| Runtime tool namespace         | `mcp__gsa_calc__<tool>` |

The underscore form (`gsa_calc`) is used in skill frontmatter and runtime
namespacing for Python-identifier consistency. Upstream's hyphenated
`serverInfo.name` is an internal detail Theseus does not surface to skills.

See [tools/mcps/gsa_calc/UPSTREAM.md](../tools/mcps/gsa_calc/UPSTREAM.md) for
the full re-vendor recipe.

## 2. Verify

### 2a. Discovery — manifest is loaded

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from src.skills.mcp_client import discover_manifests; m = discover_manifests(Path('tools/mcps')); print(sorted(m), m['gsa_calc'].command)"
```

Expected (with USAspending and eCFR also vendored):

```
['ecfr', 'gsa_calc', 'usaspending'] ['uvx', '--from', 'gsa-calc-mcp==0.2.7', 'gsa-calc-mcp']
```

### 2b. Live MCP — handshake responds

Manual JSON-RPC over stdio (PowerShell):

```powershell
$msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
$msg | uvx --from gsa-calc-mcp==0.2.7 gsa-calc-mcp 2>&1 | Select-Object -First 3
```

Expected first line:

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{...},"serverInfo":{"name":"gsa-calc","version":"1.27.0"}}}
```

### 2c. Through the registry — pytest

The opt-in live integration test:

```powershell
$env:THESEUS_LIVE_MCP = "1"
.\.venv\Scripts\python.exe -m pytest tests/skills/test_gsa_calc_manifest.py -v
```

Without `THESEUS_LIVE_MCP=1` the live test is skipped; only the manifest
parse / discovery test runs (default CI behavior — no network, no
subprocess).

### 2d. End-to-end through a skill (smoke)

Once a skill declares `metadata.mcps: ["gsa_calc"]` (planned: the future
`price-to-win` skill on its own skill-creator branch), the runtime will:

1. Spawn `uvx --from gsa-calc-mcp==0.2.7 gsa-calc-mcp` as a subprocess with
   `cwd=tools/mcps/gsa_calc`.
2. Perform the MCP `initialize` handshake.
3. Expose all 8 server tools as `mcp__gsa_calc__<tool>` to the LLM driving
   the skill.
4. Reap the subprocess in the run's `finally` block.

## 3. Troubleshooting

### `uvx: command not found`

`uv` is missing from `PATH`. Either install via the official installer
(<https://docs.astral.sh/uv/getting-started/installation/>) or, if uv is
already installed for this project, add `~/.cargo/bin` (or
`%USERPROFILE%\.local\bin` on Windows) to `PATH`.

### "MCP gsa_calc failed to start"

Check the server's stderr — Theseus forwards it to a child logger named
`mcp.gsa_calc`. In `logs/server.log`:

```
grep "mcp.gsa_calc" logs/server.log
```

Most common causes:

| Symptom in stderr                     | Cause                                        | Fix                                                                                       |
| ------------------------------------- | -------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `error: Failed to fetch ...`          | First-run network failure                    | Verify PyPI is reachable; warm cache: `uvx --from gsa-calc-mcp==0.2.7 gsa-calc-mcp --help` |
| `protocolVersion mismatch`            | Upstream bumped MCP spec version             | Bump our client `MCP_PROTOCOL_VERSION` constant in `mcp_client.py` and re-test            |
| Slow handshake on first invocation    | uv downloading deps                          | Expected; raise `MCP_HANDSHAKE_TIMEOUT` env var if needed (default 10s)                   |
| HTTP 429 from CALC+ in tool responses | 1,000 req/hour rate limit hit                | Skill should back off / batch; surface the upstream error message verbatim                |

### Tool call returns `actionable error message`

The server is doing its job — surface the message to the user verbatim.
The upstream design philosophy explicitly handles GSA CALC+'s edge cases
(rate-limit responses, fuzzy name matching for vendors, ceiling-vs-actual
rate caveats per FAR 8.405-2(d)) by returning structured guidance instead of
raw HTTP errors.

### "Skill requested MCP 'gsa_calc' but no manifest is installed"

The skill is asking for an MCP that isn't in `tools/mcps/`. Either:

1. The skill is on a branch ahead of the MCP vendor — make sure both
   landed in the same commit / merge target.
2. Manifest path mismatch — confirm
   `tools/mcps/gsa_calc/theseus_manifest.json` exists (note exact directory
   name `gsa_calc` with underscore, not `gsa-calc-mcp`).

## 4. What's next

Per [docs/skills_roadmap.md](skills_roadmap.md), Phase 4f continues
**one MCP per branch**:

- **4f.4 — `gsa-perdiem` vendoring** (next, no key required): federal
  travel lodging + M&IE rates.
- **4f.5 — `federal-register` vendoring** (no key): proposed/final rules,
  EOs, FAR cases.
- **4f.2 — `compliance-auditor` consumes eCFR** (skill-creator branch,
  future): use `skill-creator` to enhance the existing real skill so it can
  pull live FAR/DFARS clause text.
- **4g — `price-to-win` skill** (skill-creator branch, future): the natural
  consumer of `gsa_calc` (and eventually `bls_oews` once 4e UI lands).
- **4e — UI MCP panel**: required before vendoring key-gated MCPs
  (`sam-gov`, `bls-oews`, `regulations-gov`). API key placeholders already
  live in `.env` / `.env.example`.
