# Data Sources — what's wired, what's not (Phase 4d)

## Wired: USAspending MCP (`mcp__usaspending__*`)

55 read-only tools over the public USASpending.gov API. No API key. Vendored
via `tools/mcps/usaspending/theseus_manifest.json`. Full vendor + re-vendor
notes: [tools/mcps/usaspending/UPSTREAM.md](../../../../tools/mcps/usaspending/UPSTREAM.md).

### Tools the workflow uses

| Tool                     | Purpose                                                       | When in workflow            |
| ------------------------ | ------------------------------------------------------------- | --------------------------- |
| `autocomplete_naics`     | Resolve "custom computer programming" → 541512                | Step 2 (fuzzy code resolve) |
| `autocomplete_psc`       | Resolve "IT support" → R499 etc.                              | Step 2                      |
| `get_psc_filter_tree`    | Drill down PSC hierarchy when prefix only                     | Step 2 (rare)               |
| `list_toptier_agencies`  | Resolve "Air Force" → toptier code 5700                       | Step 2                      |
| `search_awards`          | Pull award history (the spine)                                | Step 3                      |
| `lookup_piid`            | Match a workspace PIID to its USAspending award_id            | Step 4                      |
| `spending_by_category`   | Top vendors / top NAICS aggregations for pricing benchmark    | Step 6                      |
| `autocomplete_recipient` | Recipient name → recipient_hash                               | Step 5                      |
| `get_recipient_profile`  | Parent recipient, business types, total federal $             | Step 5                      |
| `get_recipient_children` | Subsidiaries (for parent-vs-sub disambiguation)               | Step 5 (optional)           |
| `get_transactions`       | Modification history of incumbent's flagship award            | Step 7 (optional)           |
| `get_award_detail`       | Full single-award context (NAICS, PSC, place of perf, agency) | Step 4 (verification)       |

### Award type codes (used in `search_awards.filters.award_type_codes`)

| Code | Meaning                              |
| ---- | ------------------------------------ |
| A    | BPA Call                             |
| B    | Purchase Order                       |
| C    | Delivery Order                       |
| D    | Definitive Contract                  |
| IDV  | Indefinite Delivery Vehicle (parent) |

For competitive-intel, `["A", "B", "C", "D"]` covers the spectrum we care
about. Add `"IDV"` when scoping for vehicle incumbency (who holds the
parent IDV is often more strategic than who got individual orders).

## NOT wired (declared `claim_gaps` in every output)

| Source             | Why not                                                       | Workaround                                       |
| ------------------ | ------------------------------------------------------------- | ------------------------------------------------ |
| SAM.gov entity API | Phase 4f — `sam-gov` MCP not yet vendored (key-gated)         | User confirms business size / set-aside manually |
| FPDS-NG ATOM       | Phase 4f — `fpds` MCP not yet vendored                        | USAspending covers most of the same data         |
| CPARS              | No public MCP source — DoD CAC + role required                | Manual export by user                            |
| Protest decisions  | No public MCP source                                          | GAO web search by user                           |
| News / leadership  | No web-search MCP wired yet                                   | User research                                    |
| GSA eLibrary       | Phase 4f — `gsa-calc` covers labor rates but not SIN coverage | Manual lookup                                    |

Always emit these in the output's `claim_gaps` so the user knows what's
missing before they walk into a red team.

## Politeness / rate limits

USAspending is unauthenticated and unmetered, but the upstream MCP server
already throttles + retries on 429. Don't hammer it — the workflow is
designed to need ~6-10 tool calls per run, not hundreds.
