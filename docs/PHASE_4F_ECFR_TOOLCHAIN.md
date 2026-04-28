# Phase 4f — MCP Toolchain (eCFR)

This document covers installing, verifying, and troubleshooting the **second
no-key MCP server** wired into Theseus's Phase 4 skill runtime: the
[`ecfr-mcp`](https://github.com/1102tools/federal-contracting-mcps/tree/main/servers/ecfr-mcp)
server from `1102tools/federal-contracting-mcps`. It mirrors the
[Phase 4c USAspending toolchain](PHASE_4C_MCP_TOOLCHAIN.md) — same vendoring
pattern, same test layers, same lifecycle.

## 0. Why this MCP, why next

- **Zero secrets.** eCFR is a fully public API maintained by the Office of
  the Federal Register — no API key, no signup. End-to-end smoke tests are
  fully reproducible.
- **High signal for govcon compliance.** 13 read-only tools cover FAR,
  DFARS, and every agency FAR supplement (HHSAR, AGAR, GSAR, DOSAR, AIDAR,
  VAAR, DEAR, NFS) plus search, version history, and the workflow-grade
  `lookup_far_clause` / `find_far_definition` / `compare_versions` calls.
  Drops directly into a future `compliance-auditor` enhancement (separate
  sub-branch — see §4).
- **Production-hardened upstream.** 5 rounds of integration testing, 101
  regression tests, server-side XML parsing to save context tokens.
- **Standard MCP transport.** stdio JSON-RPC, protocol version
  `2025-06-18` — exact match for our `MCPSession` client (see
  [docs/PHASE_4A_MCP_CLIENT_DESIGN.md](PHASE_4A_MCP_CLIENT_DESIGN.md)).

## 1. Install

The server is **not vendored as source**. Theseus's manifest
([tools/mcps/ecfr/theseus_manifest.json](../tools/mcps/ecfr/theseus_manifest.json))
points at `uvx`, which fetches the pinned PyPI release into an ephemeral,
isolated environment per skill run:

```jsonc
{
  "command": ["uvx", "--from", "ecfr-mcp==0.2.6", "ecfr-mcp"]
}
```

**Prerequisites:**

- `uv` ≥ 0.5 on `PATH` (already required by Theseus — `.venv` is managed by `uv`).
- Network access to PyPI on first run (uv caches the package thereafter).

**No action required on your part** — the registry discovers the manifest
on `SkillManager` startup; the subprocess is spawned the first time a skill
with `metadata.mcps: ["ecfr"]` is invoked.

### Note — package and console script names match

Unlike `usaspending-gov-mcp` (where the package and script names differ),
the eCFR MCP package and console script names match: `ecfr-mcp`. The
`--from` syntax is still used for **explicit version pinning** so `uvx`
doesn't silently upgrade to a newer release between runs.

The MCP server identifies itself as `ecfr` (no `-mcp` suffix) in its
`serverInfo.name` JSON-RPC response. Theseus's manifest `name` field
matches that (`ecfr`), so tool namespacing is `mcp__ecfr__<tool>`.

See [tools/mcps/ecfr/UPSTREAM.md](../tools/mcps/ecfr/UPSTREAM.md) for the
full re-vendor recipe.

## 2. Verify

### 2a. Discovery — manifest is loaded

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from src.skills.mcp_client import discover_manifests; m = discover_manifests(Path('tools/mcps')); print(sorted(m), m['ecfr'].command)"
```

Expected (with USAspending also vendored):

```
['ecfr', 'usaspending'] ['uvx', '--from', 'ecfr-mcp==0.2.6', 'ecfr-mcp']
```

### 2b. Live MCP — handshake responds

Manual JSON-RPC over stdio (PowerShell):

```powershell
$msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
$msg | uvx --from ecfr-mcp==0.2.6 ecfr-mcp 2>&1 | Select-Object -First 3
```

Expected first line:

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{...},"serverInfo":{"name":"ecfr","version":"1.27.0"}}}
```

### 2c. Through the registry — pytest

The opt-in live integration test:

```powershell
$env:THESEUS_LIVE_MCP = "1"
.\.venv\Scripts\python.exe -m pytest tests/skills/test_ecfr_manifest.py -v
```

Without `THESEUS_LIVE_MCP=1` the live test is skipped; only the manifest
parse / discovery test runs (default CI behavior — no network, no
subprocess).

### 2d. End-to-end through a skill (smoke)

Once a skill declares `metadata.mcps: ["ecfr"]` (planned: a future
`compliance-auditor` enhancement on its own branch using `skill-creator`),
the runtime will:

1. Spawn `uvx --from ecfr-mcp==0.2.6 ecfr-mcp` as a subprocess with
   `cwd=tools/mcps/ecfr`.
2. Perform the MCP `initialize` handshake.
3. Expose all 13 server tools as `mcp__ecfr__<tool>` to the LLM driving
   the skill.
4. Reap the subprocess in the run's `finally` block.

## 3. Troubleshooting

### `uvx: command not found`

`uv` is missing from `PATH`. Either install via the official installer
(<https://docs.astral.sh/uv/getting-started/installation/>) or, if uv is
already installed for this project, add `~/.cargo/bin` (or
`%USERPROFILE%\.local\bin` on Windows) to `PATH`.

### "MCP ecfr failed to start"

Check the server's stderr — Theseus forwards it to a child logger named
`mcp.ecfr`. In `logs/server.log`:

```
grep "mcp.ecfr" logs/server.log
```

Most common causes:

| Symptom in stderr                  | Cause                                       | Fix                                                                                  |
| ---------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `error: Failed to fetch ...`       | First-run network failure                   | Verify PyPI is reachable; warm cache: `uvx --from ecfr-mcp==0.2.6 ecfr-mcp --help`   |
| `protocolVersion mismatch`         | Upstream bumped MCP spec version            | Bump our client `MCP_PROTOCOL_VERSION` constant in `mcp_client.py` and re-test       |
| Slow handshake on first invocation | uv downloading ~32 deps                     | Expected; raise `MCP_HANDSHAKE_TIMEOUT` env var if needed (default 10s)              |
| `404` from `versioner` endpoint    | Tool called with today's date (eCFR lag)    | Use `get_latest_date` first, or rely on `lookup_far_clause` (auto-resolves the date) |

### Tool call returns `actionable error message`

The server is doing its job — surface the message to the user verbatim.
The upstream design philosophy ([readme §"Design notes"](https://github.com/1102tools/federal-contracting-mcps/blob/main/servers/ecfr-mcp/readme.md#design-notes))
explicitly handles eCFR's 1–2 business day lag, the structure endpoint's
section-level filter limitation, and the FAR 2.101 ~109KB payload by
parsing server-side and returning only relevant slices.

### "Skill requested MCP 'ecfr' but no manifest is installed"

The skill is asking for an MCP that isn't in `tools/mcps/`. Either:

1. The skill is on a branch ahead of the MCP vendor — make sure both
   landed in the same commit / merge target.
2. Manifest path mismatch — confirm `tools/mcps/ecfr/theseus_manifest.json`
   exists (note exact directory name `ecfr`, not `ecfr-mcp`).

## 4. What's next

Per [docs/skills_roadmap.md](skills_roadmap.md), Phase 4f is split into
**one MCP per branch** so skill-creator can be applied cleanly to each
downstream skill enhancement:

- **4f.1 — eCFR vendoring** (this branch, `124-phase-4f-ecfr-mcp`): manifest +
  tests + toolchain doc only. **No skill changes** in this branch.
- **4f.2 — `compliance-auditor` consumes eCFR** (future branch): use
  `skill-creator` to enhance the existing real skill so it can pull live
  FAR/DFARS clause text via `lookup_far_clause` instead of relying solely
  on the workspace KG. Snapshot → evals BEFORE prose → minimal draft →
  observe→refine→test, per the MANDATE in
  [.github/copilot-instructions.md](../.github/copilot-instructions.md).
- **4f.3 — next no-key MCP**: `gsa-calc`, `gsa-perdiem`, or
  `federal-register`, each on its own branch.
- **4e — UI MCP panel**: required before vendoring key-gated MCPs
  (`sam-gov`, `bls-oews`, `regulations-gov`). API key placeholders are
  already in `.env` / `.env.example` (`SAM_GOV_API_KEY`, `BLS_API_KEY`,
  `API_DATA_GOV_KEY`).
