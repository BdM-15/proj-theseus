# Phase 4f.8 — regulations-gov MCP Toolchain

**Branch:** `132-phase-4f8-regulations-gov-mcp` → integrates into `120-skills-spec-compliance`
**Vendored:** `regulationsgov-mcp` v0.2.5 (commit `aef1961`, 2026-04-28)
**Status:** ✅ vendored, tests passing, no skill consumers yet (deferred to 4f.8.x)

## Overview

`regulationsgov-mcp` wraps the federal **Regulations.gov** public API. Regulations.gov is the official federal portal for rulemaking activity across every agency: proposed rules, final rules, public comments, and the dockets that organize them. eCFR shows you what the regulation **is today**; Regulations.gov shows you **what's about to change** and **who's pushing on it**.

Why this matters in federal capture:

- **In-flight FAR/DFARS amendments** — a cited clause may have a pending NPRM (Notice of Proposed Rulemaking) that changes its meaning before the proposal is even evaluated. eCFR won't tell you that; Regulations.gov will.
- **Public-comment intelligence** — when industry players file comments on a proposed rule, those comments are public. Reading the comments tells you what the major incumbents are worried about and what they want changed.
- **Comment-period awareness** — open comment periods are an opportunity for the company to weigh in on rules that affect its business.
- **FAR case research** — `far_case_history` reconstructs the full lifecycle of a FAR case from ANPR (Advance Notice) → NPRM → final rule, useful for understanding why a clause reads the way it does.

This is the third and final key-gated MCP from the 1102tools suite. After this, the MCP-vendoring stretch (4f.1–4f.8) is complete.

## Tool catalog (8 tools)

### Documents

| Tool                  | Purpose                                                                             |
| --------------------- | ----------------------------------------------------------------------------------- |
| `search_documents`    | Full-text search across rulemaking documents (filterable by agency, doc type, date) |
| `get_document_detail` | Full content + metadata for a specific document by ID                               |

### Comments

| Tool                 | Purpose                                                                    |
| -------------------- | -------------------------------------------------------------------------- |
| `search_comments`    | Search public comments across dockets (filterable by agency, docket, date) |
| `get_comment_detail` | Full content + metadata for a specific public comment                      |

### Dockets

| Tool                | Purpose                                                                |
| ------------------- | ---------------------------------------------------------------------- |
| `search_dockets`    | Search rulemaking dockets across agencies                              |
| `get_docket_detail` | Full metadata for a specific docket (status, dates, related documents) |

### Convenience

| Tool                   | Purpose                                                            |
| ---------------------- | ------------------------------------------------------------------ |
| `open_comment_periods` | List currently open comment periods (filterable by agency / topic) |
| `far_case_history`     | Lookup the full document history for a FAR case number             |

## Configuration

```env
# .env
API_DATA_GOV_KEY=<free key from https://api.data.gov/signup/>
```

The same key works across all `api.data.gov`-fronted services (Regulations.gov, FEC, NREL, NASA, etc.). Per-key rate limit is typically 1,000 requests/hour for registered users.

## Verify

### Offline

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests/skills/test_regulations_gov_manifest.py -v
```

Expect 3 passed + 1 skipped.

### Live handshake (requires API_DATA_GOV_KEY in .env)

```powershell
$env:THESEUS_LIVE_MCP="1"
python -m pytest tests/skills/test_regulations_gov_manifest.py -v
```

Expect 4 passed; 8 tools advertised.

### Manual smoke test

```powershell
python -c "
import asyncio
from dotenv import load_dotenv; load_dotenv()
from src.skills.mcp_client import load_manifest, MCPSession
from pathlib import Path
m = load_manifest(Path('tools/mcps/regulations_gov/theseus_manifest.json'))
async def go():
    s = MCPSession(m); await s.start()
    print('tools:', [t.name for t in s.tools])
    await s.shutdown()
asyncio.run(go())
"
```

## Troubleshooting

| Symptom                                                    | Cause                                      | Fix                                                                                     |
| ---------------------------------------------------------- | ------------------------------------------ | --------------------------------------------------------------------------------------- |
| `MCPError: missing required env var(s): API_DATA_GOV_KEY`  | Key not in `.env`                          | Sign up at <https://api.data.gov/signup/>; add to `.env`; restart shell                 |
| Tool call returns `429 Too Many Requests`                  | Hourly quota exceeded                      | Wait ~1 hour, or request a higher quota at api.data.gov                                 |
| Tool call returns `403 Forbidden`                          | Key revoked or invalid                     | Re-issue the key at api.data.gov                                                        |
| `404 Not Found` on a known docket ID                       | Docket withdrawn or moved                  | Use `search_dockets` to find the current canonical ID                                   |
| Cold start ~15s on first invocation                        | `uvx` is downloading + caching the package | Subsequent spawns are 1–2s; this is normal                                              |
| `ValueError: I/O operation on closed pipe` ResourceWarning | Cosmetic Windows asyncio cleanup race      | Ignore — pytest exit code may be 1 even when all tests pass; trust the "X passed" count |

## Naming gotcha

Three different names refer to this server:

| Context                 | Name                                                 |
| ----------------------- | ---------------------------------------------------- |
| Folder in upstream repo | `regulations-gov-mcp`                                |
| PyPI package            | `regulationsgov-mcp` (no hyphen)                     |
| Console script          | `regulationsgov-mcp`                                 |
| Theseus manifest name   | `regulations_gov` (underscore for Python identifier) |

The PyPI name dropped the hyphen because of an early namespace conflict with another package; the upstream maintainer kept the directory name with the hyphen for human readability.

## Downstream consumers (deferred to 4f.8.x)

- **4f.8.a** — `compliance-auditor` + `regulations_gov`: extend C10 (Clause Currency Drift) to also flag pending NPRMs against cited clauses, not just historical amendments
- **4f.8.b** — `competitive-intel` + `regulations_gov`: comment-period intelligence (which competitors filed comments on rules affecting this market?)
- **Phase 4i** — net-new `regulatory-monitor` skill: standing watch on FAR/DFARS rulemaking, alerting on dockets that affect open captures

## What's next

Phase 4f.8 closes out the MCP-vendoring stretch (4f.1–4f.8). All eight federal MCPs from `1102tools/federal-contracting-mcps` are now vendored and live-tested:

| Phase | MCP              | Key              | Tools                         |
| ----- | ---------------- | ---------------- | ----------------------------- |
| 4c    | usaspending      | none             | ≥30                           |
| 4f.1  | ecfr             | none             | 13                            |
| 4f.3  | gsa-calc         | none             | (vendored, see toolchain doc) |
| 4f.4  | gsa-perdiem      | none             | (vendored, see toolchain doc) |
| 4f.5  | federal-register | none             | 8                             |
| 4f.6  | sam-gov          | SAM_GOV_API_KEY  | 19                            |
| 4f.7  | bls-oews         | BLS_API_KEY      | 7                             |
| 4f.8  | regulations-gov  | API_DATA_GOV_KEY | 8                             |

Next is **Phase 4g** (price-to-win modeling) and the deferred **4f.x.y** downstream skill enhancements that wire the vendored MCPs into `compliance-auditor`, `competitive-intel`, and `proposal-generator`.
