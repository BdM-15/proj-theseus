# USAspending MCP — vendor record

This directory holds **only** Theseus's manifest pointing at an upstream MCP
server. The server itself is fetched on-demand by `uvx` from PyPI — no source
code is checked into this repo.

## Upstream

- **Project**: [`1102tools/federal-contracting-mcps`](https://github.com/1102tools/federal-contracting-mcps)
- **Server**: `servers/usaspending-gov-mcp/`
- **PyPI**: [`usaspending-gov-mcp`](https://pypi.org/project/usaspending-gov-mcp/)
- **License**: MIT
- **Pinned version**: `0.3.2`
- **Pinned upstream commit**: `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2025-11-25)

USASpending.gov is a free public API — **no API key, no env vars required**.

## Why a manifest, not a source vendor

The 1102tools project ships its servers as PyPI packages with a console script
entry point (`usaspending-mcp`). `uvx` fetches the package into an ephemeral,
isolated environment per run — no impact on Theseus's `.venv`, no impact on
`pyproject.toml` / `uv.lock`. Re-vendoring is a one-line version bump in
`theseus_manifest.json`.

This mirrors how the upstream is intended to be consumed by every other MCP
client (Claude Desktop, Claude Code, Cursor, Cline, Zed, Continue) per the
upstream README.

## Gotcha — package name vs script name

The PyPI package is named `usaspending-gov-mcp` but the console script it
installs is `usaspending-mcp` (no `-gov-`). Therefore the manifest must use:

```
uvx --from usaspending-gov-mcp==0.3.2 usaspending-mcp
```

Plain `uvx usaspending-gov-mcp` fails with:

> An executable named `usaspending-gov-mcp` is not provided by package
> `usaspending-gov-mcp`. The following executables are available:
> - usaspending-mcp.exe

## Re-vendor / version bump recipe

1. Check the upstream release page:
   <https://github.com/1102tools/federal-contracting-mcps/releases>
2. Pick the new server version and verify it on PyPI:
   <https://pypi.org/project/usaspending-gov-mcp/#history>
3. Smoke-test the new version locally before committing:

   ```powershell
   $msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
   $msg | uvx --from usaspending-gov-mcp==<NEW_VERSION> usaspending-mcp 2>&1 | Select-Object -First 3
   ```

   Expect a JSON-RPC `initialize` response on stdout with
   `"protocolVersion":"2025-06-18"` and `"serverInfo":{"name":"usaspending",...}`.

4. Update `theseus_manifest.json`:
   - Bump the pinned version in `command[2]` (the `--from` argument).
   - Update `vendored_commit` to the upstream commit that ships that version
     (look up the tag in the federal-contracting-mcps repo).
   - Update `vendored_at` to today's ISO date.

5. Run the Theseus regression tests:

   ```powershell
   .\.venv\Scripts\python.exe -m pytest tests/skills/
   ```

6. Propose the commit; user approves; FF-merge per
   `.github/copilot-instructions.md` Branch Management Strategy.

## Theseus integration

- Loaded by `src/skills/mcp_client.py::discover_manifests()`.
- Skills opt in by listing `metadata.mcps: ["usaspending"]` in their
  `SKILL.md` frontmatter.
- The runtime spawns `uvx --from ...` per skill run via `MCPRegistry`,
  exposes its 55 tools as `mcp__usaspending__<tool>`, and reaps the
  subprocess on completion.

## Tool surface (snapshot at v0.3.2)

55 tools across: search & aggregation, award detail, subawards,
recipients, agencies, IDV depth, federal accounts (Treasury), reference
data, autocomplete, geographic, and workflow conveniences. See the
[upstream README](https://github.com/1102tools/federal-contracting-mcps/blob/main/servers/usaspending-gov-mcp/readme.md)
for the full list.

## Removal

To remove this MCP from Theseus: delete this directory. No skill will
silently break — `metadata.mcps` is a closed allowlist and any skill
referencing `usaspending` will surface a clear "MCP not found" warning at
load time.
