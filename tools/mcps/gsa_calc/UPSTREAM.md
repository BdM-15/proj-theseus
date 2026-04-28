# GSA CALC+ MCP — vendor record

This directory holds **only** Theseus's manifest pointing at an upstream MCP
server. The server itself is fetched on-demand by `uvx` from PyPI — no source
code is checked into this repo.

## Upstream

- **Project**: [`1102tools/federal-contracting-mcps`](https://github.com/1102tools/federal-contracting-mcps)
- **Server**: `servers/gsa-calc-mcp/`
- **PyPI**: [`gsa-calc-mcp`](https://pypi.org/project/gsa-calc-mcp/)
- **License**: MIT
- **Pinned version**: `0.2.7`
- **Pinned upstream commit**: `aef1961378b3e5c380270bec48ed47a4f7bed4fc` (2026-04-28)

GSA CALC+ is a fully public API — **no API key, no env vars required**. The
upstream API enforces a **1,000 requests/hour rate limit** (per the upstream
README); skills consuming this MCP should batch tool calls accordingly.

## Why a manifest, not a source vendor

Same rationale as the other vendored MCPs in `tools/mcps/`. The 1102tools
project ships its servers as PyPI packages with a console script entry point
(`gsa-calc-mcp`). `uvx` fetches the package into an ephemeral, isolated
environment per run — no impact on Theseus's `.venv`, no impact on
`pyproject.toml` / `uv.lock`. Re-vendoring is a one-line version bump in
`theseus_manifest.json`.

## Naming

- **Package & console script**: both `gsa-calc-mcp` (no name mismatch).
- **Upstream `serverInfo.name`**: `gsa-calc` (with hyphen).
- **Theseus manifest `name`**: `gsa_calc` (with underscore) — matches the
  `metadata.mcps: ["gsa_calc"]` notation used in the
  [skills roadmap](../../../docs/skills_roadmap.md) and chosen for
  consistency with Python identifier conventions in skill frontmatter.
  Tools are namespaced as `mcp__gsa_calc__<tool>` at the runtime layer.

The `--from` syntax pins the version explicitly so `uvx` doesn't silently
upgrade between runs:

```
uvx --from gsa-calc-mcp==0.2.7 gsa-calc-mcp
```

## Re-vendor / version bump recipe

1. Check the upstream release page:
   <https://github.com/1102tools/federal-contracting-mcps/releases>
2. Pick the new server version and verify it on PyPI:
   <https://pypi.org/project/gsa-calc-mcp/#history>
3. Smoke-test the new version locally before committing:

   ```powershell
   $msg = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"theseus","version":"0.1"}}}' + "`n"
   $msg | uvx --from gsa-calc-mcp==<NEW_VERSION> gsa-calc-mcp 2>&1 | Select-Object -First 3
   ```

   Expect a JSON-RPC `initialize` response on stdout with
   `"protocolVersion":"2025-06-18"` (or the current spec version) and
   `"serverInfo":{"name":"gsa-calc",...}`.

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
- Skills opt in by listing `metadata.mcps: ["gsa_calc"]` in their `SKILL.md`
  frontmatter.
- The runtime spawns `uvx --from ...` per skill run via `MCPRegistry`,
  exposes its 8 tools as `mcp__gsa_calc__<tool>`, and reaps the subprocess on
  completion.

## Tool surface (snapshot at v0.2.7)

8 tools across:

**Core search**

- `keyword_search` — wildcard search across labor categories, vendors, contract numbers
- `exact_search` — exact field match (use `suggest_contains` to discover values first)
- `suggest_contains` — autocomplete / discovery for field values (2-char minimum)
- `filtered_browse` — browse with filters only (no keyword)

**Workflow tools**

- `igce_benchmark` — rate statistics for IGCE development (min/max/avg/median/percentiles)
- `price_reasonableness_check` — evaluate a proposed rate against market distribution
- `vendor_rate_card` — all rates for a vendor (auto-discovers exact name)
- `sin_analysis` — rate distribution for a GSA SIN

See the
[upstream README](https://github.com/1102tools/federal-contracting-mcps/blob/main/servers/gsa-calc-mcp/readme.md)
for full tool schemas, example prompts, and the **important caveat** that
CALC+ data represents *ceiling rates* (FAR 8.405-2(d) requires actual task
order rates to be lower).

## Removal

To remove this MCP from Theseus: delete this directory. No skill will silently
break — `metadata.mcps` is a closed allowlist and any skill referencing
`gsa_calc` will surface a clear "MCP not found" warning at load time.
