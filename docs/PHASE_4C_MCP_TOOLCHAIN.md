# Phase 4c — MCP Toolchain (USAspending)

This document covers installing, verifying, and troubleshooting the **first
real MCP server** wired into Theseus's Phase 4 skill runtime: the
[`usaspending-gov-mcp`](https://github.com/1102tools/federal-contracting-mcps/tree/main/servers/usaspending-gov-mcp)
server from `1102tools/federal-contracting-mcps`.

## 0. Why this MCP, why first

- **Zero secrets.** USASpending.gov is a free public API — no API key, no
  env var, no signup. End-to-end smoke tests are fully reproducible.
- **High signal for govcon capture.** 55 read-only tools over award
  history, IDV children, recipient profiles, and agency spending give
  `competitive-intel` everything it needs for incumbent analysis.
- **Production-hardened upstream.** 9 rounds of integration testing
  against the live API per the upstream `testing.md`.
- **Standard MCP transport.** stdio JSON-RPC, protocol version
  `2025-06-18` — exact match for our `MCPSession` client (see
  [docs/PHASE_4A_MCP_CLIENT_DESIGN.md](PHASE_4A_MCP_CLIENT_DESIGN.md)).

## 1. Install

The server is **not vendored as source**. Theseus's manifest
([tools/mcps/usaspending/theseus_manifest.json](../tools/mcps/usaspending/theseus_manifest.json))
points at `uvx`, which fetches the pinned PyPI release into an ephemeral,
isolated environment per skill run:

```jsonc
{
  "command": ["uvx", "--from", "usaspending-gov-mcp==0.3.2", "usaspending-mcp"]
}
```

**Prerequisites:**

- `uv` ≥ 0.5 on `PATH` (already required by Theseus — `.venv` is managed by `uv`).
- Network access to PyPI on first run (uv caches the package thereafter).

**No action required on your part** — the registry discovers the manifest
on `SkillManager` startup; the subprocess is spawned the first time a
skill with `metadata.mcps: ["usaspending"]` is invoked.

### Gotcha — `usaspending-gov-mcp` vs `usaspending-mcp`

The PyPI **package** is `usaspending-gov-mcp`. The **console script** it
installs is `usaspending-mcp` (no `-gov-`). We must use the
`uvx --from <package> <script>` form. Plain `uvx usaspending-gov-mcp`
fails with:

> An executable named `usaspending-gov-mcp` is not provided by package
> `usaspending-gov-mcp`. The following executables are available:
> - usaspending-mcp.exe

See [tools/mcps/usaspending/UPSTREAM.md](../tools/mcps/usaspending/UPSTREAM.md)
for the full re-vendor recipe.

## 2. Verify

### 2a. Discovery — manifest is loaded

```powershell
.\.venv\Scripts\python.exe -c "from pathlib import Path; from src.skills.mcp_client import discover_manifests; m = discover_manifests(Path('tools/mcps')); print(sorted(m), m['usaspending'].command)"
```

Expected:

```
['usaspending'] ['uvx', '--from', 'usaspending-gov-mcp==0.3.2', 'usaspending-mcp']
```

### 2b. Live MCP — handshake responds

Manual JSON-RPC over stdio (PowerShell):

```powershell
$msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
$msg | uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp 2>&1 | Select-Object -First 3
```

Expected first line:

```json
{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","capabilities":{...},"serverInfo":{"name":"usaspending","version":"1.27.0"}}}
```

### 2c. Through the registry — pytest

The opt-in live integration test:

```powershell
$env:THESEUS_LIVE_MCP = "1"
.\.venv\Scripts\python.exe -m pytest tests/skills/test_usaspending_manifest.py -v
```

Without `THESEUS_LIVE_MCP=1` the live test is skipped; only the manifest
parse / discovery test runs (default CI behavior — no network, no
subprocess).

### 2d. End-to-end through a skill (smoke)

Once a skill declares `metadata.mcps: ["usaspending"]` (e.g. the
`competitive-intel` placeholder once it's promoted off PLACEHOLDER), the
runtime will:

1. Spawn `uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp` as a
   subprocess with `cwd=tools/mcps/usaspending`.
2. Perform the MCP `initialize` handshake.
3. Expose all 55 server tools as `mcp__usaspending__<tool>` to the LLM
   driving the skill.
4. Reap the subprocess in the run's `finally` block.

## 3. Troubleshooting

### `uvx: command not found`

`uv` is missing from `PATH`. Either install via the official installer
(<https://docs.astral.sh/uv/getting-started/installation/>) or, if uv
is already installed for this project, add `~/.cargo/bin`
(or `%USERPROFILE%\.local\bin` on Windows) to `PATH`.

### "MCP usaspending failed to start"

Check the server's stderr — Theseus forwards it to a child logger named
`mcp.usaspending`. In `logs/server.log`:

```
grep "mcp.usaspending" logs/server.log
```

Most common causes:

| Symptom in stderr                                   | Cause                                         | Fix                                                                  |
| --------------------------------------------------- | --------------------------------------------- | -------------------------------------------------------------------- |
| `executable named ... is not provided`              | manifest uses wrong console script name       | Confirm command is `uvx --from usaspending-gov-mcp==X.Y.Z usaspending-mcp` |
| `error: Failed to fetch ...`                        | First-run network failure                     | Verify PyPI is reachable; warm cache: `uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp --help` |
| `protocolVersion mismatch`                          | Upstream bumped MCP spec version              | Bump our client `MCP_PROTOCOL_VERSION` constant in `mcp_client.py` and re-test |
| Slow handshake on first invocation                  | uv downloading 30+ deps (cryptography etc.)   | Expected; raise `MCP_HANDSHAKE_TIMEOUT` env var if needed (default 10s) |

### Tool call returns `actionable error message`

The server is doing its job — surface the message to the user verbatim.
The upstream design philosophy ([readme §"Design notes"](https://github.com/1102tools/federal-contracting-mcps/blob/main/servers/usaspending-gov-mcp/readme.md#design-notes))
explicitly translates 422 / 400 USASpending API errors into LLM-facing
guidance ("Award type groups cannot be mixed", "sort field missing", etc.).

### "Skill requested MCP 'usaspending' but no manifest is installed"

The skill is asking for an MCP that isn't in `tools/mcps/`. Either:

1. The skill is on a branch ahead of the MCP vendor — make sure both
   landed in the same commit / merge.
2. Manifest path mismatch — confirm
   `tools/mcps/usaspending/theseus_manifest.json` exists (note exact
   directory name `usaspending`, not `usaspending-gov-mcp`).

## 4. What's next (Phase 4d / 4e preview)

Per [docs/skills_roadmap.md](skills_roadmap.md):

- **4d**: Promote `competitive-intel` skill from PLACEHOLDER, declare
  `metadata.mcps: ["usaspending"]`, wire its workflow checklist through
  the new tool surface, and ship `intel_award_history` end-to-end.
- **4e**: Vendor the remaining seven `1102tools/federal-contracting-mcps`
  servers (`sam-gov`, `bls-oews`, `gsa-calc`, `gsa-perdiem`, `ecfr`,
  `federal-register`, `regulations-gov`). Each follows the exact same
  pattern as this one: one `theseus_manifest.json` + one `UPSTREAM.md`,
  zero source vendored. The four servers that need API keys
  (BLS, api.data.gov, SAM.gov) declare those in `env_required`; the
  registry refuses to start a session if they're missing from the env
  scope.
