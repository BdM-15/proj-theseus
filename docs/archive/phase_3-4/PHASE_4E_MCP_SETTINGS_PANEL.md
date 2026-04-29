# Phase 4e — MCP Servers Settings Panel

**Status**: ✅ Shipped
**Branch**: `128-phase-4e-mcp-settings-panel` → FF-merged into `120-skills-spec-compliance`
**Roadmap row**: [docs/skills_roadmap.md](skills_roadmap.md) Phase 4e

## Why

Phases 4a–4d wired the MCP client subsystem and shipped the first vendored
no-key MCP (USAspending) plus the first MCP-consuming skill (`competitive-intel`).
Phase 4f.1/4f.3/4f.4/4f.5 added four more no-key MCPs (eCFR, GSA CALC+,
GSA Per Diem, Federal Register).

Key-gated MCPs (`sam-gov`, `bls-oews`, `regulations-gov`) cannot ship until
operators have a sane way to:

1. **See** which MCPs are vendored and what env vars each one declares.
2. **Tell at a glance** which MCPs are ready vs. waiting on a key.
3. **Paste an API key** without hand-editing `.env` and remembering to restart.
4. **Verify** that a key actually works by spawning the real subprocess.

Phase 4e ships the Settings → MCP Servers accordion that does all four.

## What ships

### Backend — `src/server/ui_routes.py`

Three new routes registered inside `register_ui(app, ...)`, all tagged
`theseus-ui`:

| Route                      | Method | Purpose                                                                                                            |
| -------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------ |
| `/api/ui/mcps`             | GET    | Inventory of every manifest under `tools/mcps/`, with env-var status (set/masked) and provenance.                  |
| `/api/ui/mcps/{name}/keys` | POST   | Atomic `.env` writer. Validates each key against the manifest's declared env-var allowlist. Triggers self-restart. |
| `/api/ui/mcps/{name}/test` | POST   | Spawns `MCPSession`, runs the JSON-RPC handshake + `tools/list`, returns the tool count + first 8 tool names.      |

Helpers (private to the route block):

- `_SAFE_MCP_NAME = re.compile(r"^[a-z][a-z0-9_]{0,63}$")` — name validator (defense in depth).
- `_SAFE_ENV_KEY = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")` — env-var validator.
- `_mcps_root()` — resolves `<cwd>/tools/mcps`.
- `_mask_secret(value)` — `first4***last2` (or `first1***` if value ≤ 8 chars).
- `_env_status(name)` — returns `{name, set: bool, masked: str | None}`.

Pydantic model:

```python
class McpKeyUpdate(BaseModel):
    keys: dict[str, str] = Field(default_factory=dict)
    restart: bool = Field(default=True)
```

### Security model

The save-keys endpoint is **not** a generic `.env` writer. It enforces:

1. **MCP name** must match `_SAFE_MCP_NAME` and resolve to a real manifest.
2. **Each key** in the request must be present in the manifest's
   `env_required ∪ env_optional`. Unknown keys → `400 Bad Request` listing the rejected names.
3. **Each key name** independently must match `_SAFE_ENV_KEY` (defends against weird payloads even if a manifest were corrupted).
4. **No-env MCPs** (e.g. `ecfr`, `usaspending`) reject the call entirely with 400 — there's nothing to save.
5. The actual write goes through the existing `_set_env_var()` helper which
   does an atomic `.env` rewrite + `os.environ` mutation + LightRAG
   `reset_settings()`.
6. When `restart=True` and at least one key was written, the server schedules
   `_self_restart()` (= `os.execv`) via `loop.call_later(0.75, ...)` so the
   POST response goes out cleanly first.

### Test connection

`POST /api/ui/mcps/{name}/test` is the only way for a non-developer to
verify that a key actually works against the live API. Implementation:

```python
session = MCPSession(manifest)
try:
    await session.start()  # spawn + handshake + tools/list
    return {"ok": True, "mcp": name, "tool_count": len(session.tools), ...}
except MCPError as exc:
    return {"ok": False, "mcp": name, "error": str(exc)}  # HTTP 200 so UI renders the error
finally:
    await session.shutdown()  # idempotent, reaps the subprocess
```

Returning HTTP 200 even on `MCPError` is intentional: the UI needs the
error string surfaced inline next to the row, not buried in a fetch
exception.

### Frontend — `src/ui/static/index.html`

New `<details class="acc accent-cyan" data-acc-key="mcps">` block in the
Settings tab between **Agent Skills Retrieval** and **Models & Storage**.
Per-MCP card surfaces:

- Name, ready/needs-key badge, description.
- One `<input type="password">` per declared env var; required vs.
  optional pill; "currently: abcd\*\*\*xy" hint when a value is already set.
- **Test connection** button (disabled if `missing_env.length > 0`).
- **Save keys + restart** button (POSTs only the non-blank fields).
- Footer with `command`, `license`, `vendored_at`, and an upstream link.

Alpine state on `theseus()`:

```js
mcps: {
  loaded, loading, items: [],
  drafts: {}, saving: {}, testing: {}, testResult: {}
}
```

Methods: `loadMcps()`, `saveMcpKeys(name)`, `testMcp(name)`. The Settings
tab `$watch("active")` lazy-loads on first visit.

Token-system note (per `docs/STYLE_GUIDE.md`): all colors use existing
`var(--neon-cyan)` / `var(--neon-amber)` / `var(--neon-magenta)` /
`var(--neon-lime)` / `var(--edge)` tokens. No new hex literals; no
`@apply` (which Tailwind Play CDN does not process in external CSS).

### Tests — `tests/skills/test_mcp_settings_routes.py`

Mounts a minimal FastAPI app with a stub `query_func` and uses
`fastapi.testclient.TestClient`. New pattern in this repo (no prior
HTTP route tests existed); other skill tests use the asyncio-driver
manifest pattern instead.

Coverage:

| Test                                                       | Layer          | Network    |
| ---------------------------------------------------------- | -------------- | ---------- |
| `test_list_mcps_returns_vendored_inventory`                | List           | none       |
| `test_list_mcps_includes_env_status_and_provenance`        | List           | none       |
| `test_update_keys_rejects_undeclared_env_vars`             | Validation     | none       |
| `test_update_keys_rejects_unknown_mcp`                     | Validation     | none       |
| `test_update_keys_rejects_no_env_mcp`                      | Validation     | none       |
| `test_update_keys_writes_only_allowed_keys`                | Save (mock)    | none       |
| `test_test_connection_against_ecfr` (`THESEUS_LIVE_MCP=1`) | Live handshake | uvx + ecfr |

7 offline + 1 live, all green.

## Unblocks

With Phase 4e in place, key-gated MCPs in `1102tools/federal-contracting-mcps`
can be vendored without operator pain:

- **`sam-gov-mcp`** (key: `SAM_GOV_API_KEY`) — opportunities, vendors, FPDS award history.
- **`bls-oews-mcp`** (key: `BLS_API_KEY`) — labor wage benchmarks for IGCE / price-to-win.
- **`regulations-gov-mcp`** (key: `API_DATA_GOV_KEY`, already shared with GSA Per Diem) — public comments, dockets.

The vendoring branch only needs to add the manifest + UPSTREAM.md +
manifest test; the operator picks up the new MCP by refreshing the
panel and pasting the key.

## Out of scope (intentionally)

- **Stderr viewer**: roadmap row 4e mentions "view stderr" — the MCP
  client already routes subprocess stderr to the workspace processing log.
  A dedicated viewer is deferred until an operator actually asks for one.
- **Install / uninstall through UI**: vendoring an MCP is still a
  developer task (manifest + UPSTREAM.md + tests live in git). The panel
  is read-only over the inventory + write-only over the keys.
