# Phase 4a — MCP Client Subsystem (Design Doc)

**Branch:** `121-phase-4a-mcp-client` (proposed)
**Status:** Design — not yet implemented
**Predecessors:** Phase 3e (renderers + XLSX), Phase 4j taxonomy doc (concurrent)
**Successors:** 4b (frontmatter allowlist), 4c (first vendored MCP — USAspending)

---

## 1. Goal

Enable Theseus skills to call **Model Context Protocol (MCP)** tools the
same way they currently call in-process Python tools (`kg_query`,
`run_script`, etc.), without coupling the runtime to any specific data
source. After Phase 4a, adding a new federal data source becomes:

1. Drop a vendored MCP under `tools/mcps/<name>/`
2. Declare `metadata.mcps: [<name>]` in a SKILL.md
3. (No runtime code changes.)

This is the strict prerequisite for Phases 4c–4i (vendored MCPs + skills).

## 2. Non-goals

- **Not** a generic MCP host (no SSE transport, no remote servers — stdio
  subprocess only).
- **Not** an MCP server (Theseus does not expose its KG via MCP yet — that
  is a separate future phase).
- **Not** sandboxing beyond what subprocess + env scoping already give us.
  MCPs are vendored and reviewed; we trust their code the same way we
  trust `tools/`.
- **Not** key management UI (that is Phase 4d).

## 3. Architecture overview

```
┌────────────────────────────────────────────────────────────────┐
│  src/skills/manager.py                                         │
│  - Parses SKILL.md frontmatter (Phase 4b adds metadata.mcps)   │
│  - Returns Skill.required_mcps: list[str]                      │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  src/skills/mcp_client.py  (NEW — Phase 4a deliverable)        │
│  - MCPRegistry: discovers tools/mcps/* on startup              │
│  - MCPSession: spawns one subprocess per declared MCP per run  │
│  - MCPTool: adapts JSON-RPC tool schema → ToolSpec             │
│  - JSON-RPC stdio framing (Content-Length header)              │
│  - Lifecycle: handshake, list_tools, call_tool, shutdown       │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  src/skills/tools.py                                           │
│  - build_tool_specs(ctx) appends MCP-discovered ToolSpecs      │
│  - Namespacing: mcp__<server>__<tool>  (double underscore)     │
│  - Each ToolSpec.handler dispatches to the live MCPSession     │
└────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌────────────────────────────────────────────────────────────────┐
│  src/skills/runtime.py                                         │
│  - run_tool_loop unchanged — same transcript shape             │
│  - On finish, calls registry.shutdown_run(run_id) to reap procs│
└────────────────────────────────────────────────────────────────┘
```

**Key insight:** the LLM does not know an MCP exists. It sees
`mcp__usaspending__award_history` as just another tool with a JSON
schema. The transcript records `tool_call` / `tool_result` with the
same shape as in-process tools. This keeps replay, eval, and audit
flows unchanged.

## 4. Subprocess + JSON-RPC details

### 4.1 Spawn

```python
proc = await asyncio.create_subprocess_exec(
    *manifest.command,           # e.g., ["node", "tools/mcps/usaspending/dist/index.js"]
    cwd=manifest.cwd,            # tools/mcps/usaspending/
    stdin=PIPE, stdout=PIPE, stderr=PIPE,
    env={**os.environ, **manifest.env_extra},  # API keys injected here
)
```

- **One subprocess per MCP per skill run** (not pooled).
  - Pooling adds complexity (stale auth, session leaks across runs);
    skill runs are minutes long, so spawn cost is amortized.
  - Re-evaluate if benchmarks show >500ms cold start per MCP.
- **stderr → logger** at `INFO` (server name as logger child) so MCP crash
  output lands in `logs/server.log`.

### 4.2 JSON-RPC framing

MCP uses LSP-style framing on stdio:

```
Content-Length: 123\r\n\r\n{"jsonrpc":"2.0","id":1,"method":"initialize",...}
```

Implement a tiny reader that:
1. Reads headers until blank line
2. Reads exactly `Content-Length` bytes of body
3. Parses JSON, dispatches by `id`

Use `asyncio.Queue` per session to serialize writes (MCP allows pipelining
but we don't need it).

### 4.3 Handshake

```
client → server: initialize { protocolVersion, capabilities, clientInfo }
server → client: initialize result
client → server: notifications/initialized
client → server: tools/list
server → client: { tools: [{ name, description, inputSchema }, ...] }
```

After handshake, cache the tool list on `MCPSession.tools` and convert
each entry into a `ToolSpec`:

```python
ToolSpec(
    name=f"mcp__{session.server_name}__{tool['name']}",
    description=tool["description"],
    parameters=tool["inputSchema"],   # already JSON-Schema
    handler=lambda **kw: session.call_tool(tool["name"], kw),
)
```

### 4.4 Tool calls

```
client → server: tools/call { name, arguments }
server → client: { content: [{ type: "text", text: "..." }, ...], isError: bool }
```

`MCPSession.call_tool`:
1. Send request, await response keyed by `id`
2. Concatenate `content[]` text parts → string
3. If `isError: true`, raise `ToolError` (so transcript records the error
   the same way in-process tools record errors)
4. Apply `max_read_bytes` cap (reuse existing `ToolContext` cap)

### 4.5 Shutdown

- Normal: send `shutdown` notification, wait up to 2s, then `terminate()`,
  then `kill()` if still alive.
- Crash: detected when stdout EOF before shutdown; log stderr tail.
- Run cleanup: `MCPRegistry.shutdown_run(run_id)` is called from
  `runtime.run_tool_loop`'s finally block. **Critical** — without this,
  abandoned Node procs accumulate.

## 5. Manifest format

Each vendored MCP must have `tools/mcps/<name>/theseus_manifest.json`:

```json
{
  "name": "usaspending",
  "description": "USAspending.gov award + spending data (no API key required)",
  "command": ["node", "dist/index.js"],
  "env_required": [],
  "env_optional": [],
  "vendored_from": "https://github.com/1102tools/federal-contracting-mcps",
  "vendored_commit": "abc123...",
  "vendored_at": "2026-04-30",
  "license": "MIT"
}
```

`env_required` triggers a startup check (skill run aborts with clear
error if missing). `env_optional` is documented but not enforced.

The manifest is **Theseus-specific glue**, not part of the MCP spec.
Upstream `package.json` / `mcp.json` is left untouched so re-vendoring
stays a clean `git subtree pull` (or copy + manifest regenerate).

## 6. Allowlist + security model (Phase 4b preview)

Frontmatter declares which MCPs a skill can talk to:

```yaml
metadata:
  mcps: [usaspending, sam_gov]
```

`MCPRegistry.session_for_run(skill, run_id)` spawns **only** the declared
servers. A skill that doesn't declare `mcps` gets zero MCP tools — the
default is closed.

Rationale: identical shape to `script_paths` from Phase 3 — same security
intuition for reviewers ("what can this skill reach?" answered by
inspecting frontmatter only).

## 7. Failure modes & observability

| Failure                     | Detection                          | Behavior                                                      |
| --------------------------- | ---------------------------------- | ------------------------------------------------------------- |
| MCP binary missing          | `FileNotFoundError` on spawn       | Skill run aborts; clear error names the manifest path         |
| Required env var missing    | Manifest preflight                 | Skill run aborts before spawn                                 |
| Handshake timeout (5s)      | `asyncio.wait_for` on initialize   | Kill subprocess, abort run                                    |
| Tool call timeout (30s)     | Per-call `asyncio.wait_for`        | Raise `ToolError`, MCP stays alive for next call              |
| MCP crash mid-run           | stdout EOF                         | Mark session dead, subsequent calls return `ToolError`        |
| stderr noise                | Background reader task             | Forward to `logs/server.log` at INFO                          |
| Run finishes, proc lingers  | finally block in `run_tool_loop`   | `shutdown_run()` reaps; warn if exit takes >2s                |

All of the above land in `transcript.json` as either `tool_result` (with
`isError: true`) or a top-level `runtime_warning` event so audits can
distinguish "skill made a bad call" from "infra failed."

## 8. Testing plan

### 8.1 Unit (no real MCP)

- `tests/skills/test_mcp_jsonrpc.py` — frame reader/writer round-trip
- `tests/skills/test_mcp_session.py` — fake stdio with scripted responses,
  cover handshake, tool listing, call success, call error, EOF crash
- `tests/skills/test_mcp_registry.py` — manifest loading, env preflight,
  allowlist enforcement

### 8.2 Integration (4c)

- `tests/skills/test_mcp_usaspending_smoke.py` — actually spawns the
  vendored USAspending MCP (no API key), calls `award_history(naics=541512)`,
  asserts non-empty result. Marked `@pytest.mark.integration` so CI can
  skip when MCPs aren't installed.

### 8.3 Manual smoke

`competitive-intel` skill manually invoked through the existing UI; check
`<run_dir>/transcript.json` shows `mcp__usaspending__award_history` calls
with real award data.

## 9. Files touched

**New:**
- `src/skills/mcp_client.py` (~400 lines)
- `tests/skills/test_mcp_jsonrpc.py`
- `tests/skills/test_mcp_session.py`
- `tests/skills/test_mcp_registry.py`

**Modified:**
- `src/skills/manager.py` — surface `Skill.required_mcps` (Phase 4b
  formalizes the field; 4a can land with a no-op getter that always
  returns `[]`)
- `src/skills/tools.py` — `build_tool_specs` appends MCP tool specs when
  `ctx.mcp_session_factory` is wired
- `src/skills/runtime.py` — finally-block calls `mcp_registry.shutdown_run`
- `src/server/routes.py` (skill invoke endpoint) — instantiate registry,
  wire factory into `ToolContext`

## 10. Sub-phase exit criteria (4a only)

- [ ] `mcp_client.py` lands with unit tests green
- [ ] `tools.py` can append MCP-derived `ToolSpec`s when given a session
      factory; existing in-process tool tests stay green
- [ ] `runtime.py` reaps subprocesses on success, error, and turn-cap
- [ ] No vendored MCP yet (that's 4c) — but a fake MCP fixture exercises
      the full path end-to-end in tests
- [ ] `docs/skills_roadmap.md` 4a row flips to ✅

## 11. Open questions

1. **Cross-run pooling:** worth it for short skills (~10s)? Defer until
   we have measurements; current design is per-run for simplicity.
2. **Concurrent tool calls:** MCP supports it; our runtime is currently
   sequential. Defer — not needed for the first eight 1102tools MCPs.
3. **Tool name length:** OpenAI tool names cap at 64 chars. `mcp__sam_gov__opportunity_search` = 33 — fine. Document the cap; reject manifests
   that would overflow.
4. **Registry as singleton vs per-server:** start with one registry per
   process owning all sessions across all runs (run_id-keyed dict). One
   place to look when debugging.

## 12. Cross-cutting checklist (Phase 4a applicability)

| Area                                            | Touched? | Notes                                                                  |
| ----------------------------------------------- | -------- | ---------------------------------------------------------------------- |
| 1. Schema (`schema.py`)                         | No       | No entity/relationship change                                          |
| 2. Extraction prompt                            | No       | n/a                                                                    |
| 3. Multimodal prompts                           | No       | n/a                                                                    |
| 4. Query/response prompts                       | No       | n/a                                                                    |
| 5. Inference prompts                            | No       | n/a                                                                    |
| 6. Test fixtures                                | Yes      | New unit tests under `tests/skills/`                                   |
| 7. VDB sync                                     | No       | n/a                                                                    |
| 8. Skill spec compliance (frontmatter 6-fields) | Yes      | `metadata.mcps` lands in 4b — stays under `metadata:`, spec-conformant |
