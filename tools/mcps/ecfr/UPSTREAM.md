# eCFR MCP — vendor record

This directory holds **only** Theseus's manifest pointing at an upstream MCP
server. The server itself is fetched on-demand by `uvx` from PyPI — no source
code is checked into this repo.

## Upstream

- **Project**: [`1102tools/federal-contracting-mcps`](https://github.com/1102tools/federal-contracting-mcps)
- **Server**: `servers/ecfr-mcp/`
- **PyPI**: [`ecfr-mcp`](https://pypi.org/project/ecfr-mcp/)
- **License**: MIT
- **Pinned version**: `0.2.6`
- **Pinned upstream commit**: `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)

eCFR is a fully public API maintained by the Office of the Federal Register —
**no API key, no env vars required**.

## Why a manifest, not a source vendor

The 1102tools project ships its servers as PyPI packages with a console script
entry point (`ecfr-mcp`). `uvx` fetches the package into an ephemeral, isolated
environment per run — no impact on Theseus's `.venv`, no impact on
`pyproject.toml` / `uv.lock`. Re-vendoring is a one-line version bump in
`theseus_manifest.json`.

This mirrors how the upstream is intended to be consumed by every other MCP
client (Claude Desktop, Claude Code, Cursor, Cline, Zed, Continue) per the
upstream README.

## Package name vs script name

Unlike `usaspending-gov-mcp` (where the package and script names differ), the
eCFR MCP package and console script names match: `ecfr-mcp`. The `--from`
syntax is still used in the manifest for **explicit version pinning** so
`uvx` doesn't silently upgrade to a newer release between runs.

```
uvx --from ecfr-mcp==0.2.6 ecfr-mcp
```

The MCP server identifies itself as `ecfr` (no `-mcp` suffix) in the
`serverInfo.name` field of the JSON-RPC `initialize` response. Theseus uses
the manifest's `name` field (`ecfr`), which matches.

## Re-vendor / version bump recipe

1. Check the upstream release page:
   <https://github.com/1102tools/federal-contracting-mcps/releases>
2. Pick the new server version and verify it on PyPI:
   <https://pypi.org/project/ecfr-mcp/#history>
3. Smoke-test the new version locally before committing:

   ```powershell
   $msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
   $msg | uvx --from ecfr-mcp==<NEW_VERSION> ecfr-mcp 2>&1 | Select-Object -First 3
   ```

   Expect a JSON-RPC `initialize` response on stdout with
   `"protocolVersion":"2025-06-18"` and `"serverInfo":{"name":"ecfr",...}`.

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
- Skills opt in by listing `metadata.mcps: ["ecfr"]` in their `SKILL.md`
  frontmatter.
- The runtime spawns `uvx --from ...` per skill run via `MCPRegistry`,
  exposes its 13 tools as `mcp__ecfr__<tool>`, and reaps the subprocess on
  completion.

## Tool surface (snapshot at v0.2.6)

13 tools across:

**Core endpoints**

- `get_latest_date` — most recent available date for a CFR title (call before other tools)
- `get_cfr_content` — parsed regulatory text for a section, subpart, or part
- `get_cfr_structure` — hierarchical table of contents
- `get_version_history` — amendment history for a section or part
- `get_ancestry` — breadcrumb hierarchy path
- `search_cfr` — full-text search with hierarchy filters
- `list_agencies` — all agencies with their CFR references
- `get_corrections` — editorial corrections for a title

**Workflow convenience**

- `lookup_far_clause` — one-call FAR/DFARS clause text lookup (auto-resolves date)
- `compare_versions` — side-by-side text comparison at two dates
- `list_sections_in_part` — all sections in a FAR/DFARS part
- `find_far_definition` — search FAR 2.101 for a term definition
- `find_recent_changes` — sections modified since a given date

**CFR Title 48 quick reference**: 1=FAR, 2=DFARS, 3=HHSAR, 4=AGAR, 5=GSAR,
6=DOSAR, 7=AIDAR, 8=VAAR, 9=DEAR, 18=NFS.

See the
[upstream README](https://github.com/1102tools/federal-contracting-mcps/blob/main/servers/ecfr-mcp/readme.md)
for full tool schemas and example prompts.

## Removal

To remove this MCP from Theseus: delete this directory. No skill will silently
break — `metadata.mcps` is a closed allowlist and any skill referencing `ecfr`
will surface a clear "MCP not found" warning at load time.
