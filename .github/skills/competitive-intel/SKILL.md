---
name: competitive-intel
description: Federal capture competitor, incumbent, and obligation intelligence backed by live USAspending.gov data via the vendored `usaspending` MCP. USE WHEN the user asks "who's the incumbent on this contract?", "what was the last award value?", "give me a black-hat read on Bidder X", "who are the top three competitors for this NAICS?", "what's typical pricing for this work?", "pull award history for this agency / NAICS / PSC", "analyze burn rate", "obligation trend by year", or "start from this contract number". Supports both black-hat competitor research and contract-number-first obligation analysis, including standalone awards, parent IDIQs, and orders under IDIQs with parent/child rollups. DO NOT USE FOR proposal drafting (use `proposal-generator`), clause / FAR compliance audit (use `compliance-auditor`), or generic web search about a company (no MCP tool covers that yet).
license: MIT
metadata:
  # Phase 4j taxonomy — see docs/SKILL_TAXONOMY.md
  personas_primary: capture_manager
  personas_secondary: [cost_estimator, proposal_manager]
  shipley_phases: [pursuit, capture, strategy]
  capability: research
  category: intel
  version: 0.6.0
  status: active
  runtime: tools
  # This skill walks 10 numbered steps with 6+ MCP calls and 3+ KG calls
  # per run. The default 12-turn budget (SKILL_TOOLS_MAX_TURNS) is too
  # tight — runs hit the cap before reaching the final write_file step.
  # The runtime treats this as a floor and uses the larger of env vs
  # skill value. See issue #120 for the future decomposition epic that
  # will let us drop this back to the default once sub-skills exist.
  max_turns: 20
  # Phase 4b: declare which vendored MCP servers this skill needs. The
  # runtime exposes only these MCPs to the agent loop, namespaced as
  # `mcp__usaspending__<tool>`. Skills that omit `metadata.mcps` get zero
  # MCP tools — closed-by-default, mirroring `metadata.script_paths`.
  mcps:
    - usaspending
---

# Competitive Intel — Black-Hat + Obligation Intel

You are a **federal capture analyst** working multi-turn against the active Theseus workspace knowledge graph PLUS live USASpending.gov award data (via the `usaspending` MCP). This skill has two modes:

- **Workflow A (Black-Hat)**: Convert workspace RFP context into a defensible black-hat brief on incumbent and likely competitors.
- **Workflow B (Obligation Intel)**: Start from a contract number and build an obligation rollup, parent/child vehicle context, and competitor set completeness check.

Every claim must trace either to a `chunk_id` you fetched via `kg_chunks` or to a USAspending award you fetched via an `mcp__usaspending__*` tool.

## When to Use

- "Who's the incumbent on this contract?"
- "Pull award history for similar work in the last 5 years"
- "Black-hat: what would Lockheed bid here?"
- "What's the typical price range for this NAICS at this magnitude?"
- "Top 3 competitors for a 541512 IT modernization recompete with HHS"
- "Here's a contract number - show burn rate / obligation trend"
- "Is this contract an IDIQ parent, an order, or standalone?"
- "Roll up obligations across all child orders"
- "If this is an order under a multiple-award IDIQ, who are all parent-level competitors?"

## Operating Discipline

- **Workspace first, web second.** The KG is the source of truth for the opportunity (program, agency, NAICS, PSC, place of performance). USAspending is the source of truth for who has actually won similar work.
- **Cite everything.** Workspace claims cite `chunk_id` (e.g., `[chunk-xxxxxxxx]`). Award claims cite the USAspending `generated_internal_id` (e.g., `[award:CONT_AWD_…]`).
- **Rank by obligated dollars, not transaction count.** A vendor with one $400M IDV beats a vendor with 200 $50K POs.
- **Linkage precedence for vehicle analysis.** For multiple-award IDIQs, resolve relationships in this order: parent IDV linkage, explicit child-order listing, PIID-family context, then solicitation identifier as a fallback signal.
- **Reject anti-patterns.** Inventing competitors not in award history. Pricing ranges with no underlying award sample. Generic SWOT bullets ("strong past performance"). Unsupported claims about CPARS or protests (no MCP source for those yet — say so).
- **Fail loudly.** If the workspace is missing NAICS / PSC / agency, halt with a `GAP` rather than guess.

## Workflow Selector

Pick exactly one workflow before running tools:

- **Workflow A: Black-Hat Competitor Intel (default)**
  Trigger: incumbent/competitor/theming/pricing benchmark questions anchored on NAICS/agency/program context.
- **Workflow B: Contract-Number Obligation Intel**
  Trigger: user provides a contract number/PIID and asks for burn-rate, obligation trend, IDIQ hierarchy, parent/child rollups, or competitor completeness from vehicle context.

If both are requested, run Workflow B first and feed its `competitor_discovery` result into Workflow A.

---

## Workflow A Checklist (Black-Hat)

Execute in order. Record entity counts, NAICS codes, and award IDs as you go so the final envelope can be audited.

### 1. Inventory the workspace context (KG slice)

Call `kg_entities` with:

```json
{
  "types": [
    "program",
    "organization",
    "contract_line_item",
    "regulatory_reference",
    "requirement",
    "deliverable"
  ],
  "limit": 60,
  "max_chunks": 2,
  "max_relationships": 3
}
```

Extract:

- **Agency / sub-agency** (look in `organization` entities; cross-check `program`)
- **NAICS code** (often a `regulatory_reference` like "NAICS 541512")
- **PSC code** (similar — `regulatory_reference` like "PSC R499")
- **Place of performance** (state / city if present)
- **Estimated magnitude** (search `contract_line_item` or chunks for "$", "ceiling", "estimated value")

If NAICS AND PSC are both missing, halt with `GAP: workspace lacks NAICS and PSC — cannot scope award history`. If only one is missing, proceed but flag it in `warnings`.

### 2. Resolve fuzzy codes via USAspending autocompletes

If the workspace mentions a NAICS by description but not by number (e.g., "custom computer programming"), call `mcp__usaspending__autocomplete_naics` with the keyword. If the agency is a friendly name ("Air Force") but you need the toptier code, call `mcp__usaspending__list_toptier_agencies` once and resolve. Same drill for PSC via `mcp__usaspending__autocomplete_psc` or `mcp__usaspending__get_psc_filter_tree`.

### 3. Pull award history (the spine)

Call `mcp__usaspending__search_awards` with a filters object scoped to the resolved NAICS, agency, and a 5-year window:

```json
{
  "filters": {
    "naics_codes": ["<resolved naics>"],
    "agencies": [
      { "type": "awarding", "tier": "toptier", "name": "<agency name>" }
    ],
    "time_period": [{ "start_date": "<5y ago>", "end_date": "<today>" }],
    "award_type_codes": ["A", "B", "C", "D"]
  },
  "fields": [
    "Award ID",
    "Recipient Name",
    "Award Amount",
    "Period of Performance Start Date",
    "Period of Performance Current End Date",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Award Type"
  ],
  "page": 1,
  "limit": 100,
  "sort": "Award Amount",
  "order": "desc"
}
```

`A`/`B`/`C`/`D` are contract award types (BPA, PO, definitive contract, IDV order). Capture the top ~50 by amount. If the result count is < 5, broaden: drop the agency filter, then drop the date window — and note the broadening in `warnings`.

### 4. Identify the incumbent

Within the result set scoped to the same agency and a recent active period of performance, the **incumbent** is typically the recipient with the largest obligated dollars on a contract whose period of performance covers today. If multiple candidates, pick the one whose award also matches the workspace's program name or PIID prefix (search chunks for the PIID, then call `mcp__usaspending__lookup_piid`). If no contract is currently active, fall back to "most recent prior award winner" and label as `incumbent_status: "prior"` instead of `"current"`.

### 5. Rank likely competitors

From the same award-history slice, take the top ~10 recipients by total obligated dollars. Drop the incumbent. The top 3–5 of the remainder are your "likely competitors". For each, call `mcp__usaspending__autocomplete_recipient` to get the recipient hash, then `mcp__usaspending__get_recipient_profile` for the full profile (parent recipient, business types, total federal contract dollars).

### 6. Pricing benchmark

Call `mcp__usaspending__spending_by_category` with category `awarding_agency` (or `naics`) over the same 5-year window:

```json
{
  "category": "naics",
  "filters": {
    "naics_codes": ["<resolved naics>"],
    "time_period": [{ "start_date": "<5y ago>", "end_date": "<today>" }]
  },
  "limit": 10
}
```

From the matching award sample (step 3), compute the median, p25, and p75 of award amount as your "typical award value range". Sample size MUST be ≥ 10 to publish a range — otherwise label as `pricing_band: "insufficient sample"` and report the raw min/max with a count.

### 7. (Optional) Recent transactions for the incumbent

For the incumbent's flagship award, call `mcp__usaspending__get_transactions` to surface modifications. A burst of recent option exercises with no scope expansion is a recompete signal worth noting.

### 8. Synthesize the black-hat one-pager(s)

For each competitor (incumbent + top 3 likely), populate the Black-Hat one-pager structure. `read_file references/black_hat_template.md` for the canonical layout. Each one-pager:

- Names the competitor + role (`incumbent | likely-1 | likely-2 | likely-3`)
- Lists their **last 3 wins** in this NAICS/agency with dollar amount + PoP + award_id
- Predicts 2–3 themes they will likely use (anchored to their public award history — e.g., "they've won 4 of the last 5 cyber recompetes at this agency, expect a continuity-of-operations theme")
- Flags **claim gaps** — things we cannot validate from MCP data (CPARS scores, protest history, news) and which the user must research manually before red-team
- Suggests **2 ghost-language hooks** for `proposal-generator` to weave in

### 9. Self-critique + anti-slop gate

Before writing the envelope: re-read your draft and confirm:

- Every "incumbent" / "competitor" name appears in the step-3 award results (no inventions)
- Every pricing claim has an underlying sample size ≥ 10
- No SWOT bullet uses generic adjectives ("strong", "robust", "leading") without an award_id citation
- Every `claim_gap` is honest about what MCP cannot verify (CPARS, protests, news)

If any check fails, iterate — do not ship.

### 10. Write the JSON envelope (MANDATORY — do this BEFORE any final summary)

**You MUST call `write_file` to save the envelope to `artifacts/competitive_intel.json` before producing your final assistant message.** This is the skill's primary deliverable — a run that ends without this artifact is a failed run, regardless of how good the prose summary looks.

If you are running low on turns and have not yet written the artifact, **stop gathering data and write what you have now**, with `warnings[]` honestly noting what is incomplete. A partial envelope with `claim_gap` entries is more useful than no envelope.

Match the Output Contract below. After `write_file` succeeds, the final assistant message is a short cover note summarizing counts (incumbent identified yes/no, # competitors profiled, sample size for pricing, # warnings) and pointing at the artifact path. Do not write more prose before the artifact is on disk.

## Output Contract

```json
{
  "opportunity_context": {
    "program_name": "<from workspace>",
    "agency": "<resolved name>",
    "agency_toptier_code": "<resolved code>",
    "naics_code": "<resolved>",
    "naics_description": "<from autocomplete>",
    "psc_code": "<resolved or null>",
    "place_of_performance": "<state or null>",
    "estimated_magnitude_usd": <number or null>,
    "context_chunk_ids": ["chunk-xxxxxxxx"]
  },
  "incumbent": {
    "name": "<recipient name>",
    "recipient_hash": "<from get_recipient_profile>",
    "incumbent_status": "current | prior | unknown",
    "flagship_award_id": "<generated_internal_id>",
    "flagship_award_amount_usd": <number>,
    "period_of_performance": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "evidence_award_ids": ["<id1>", "<id2>"]
  },
  "competitors": [
    {
      "rank": 1,
      "name": "<recipient name>",
      "recipient_hash": "<hash>",
      "last_3_wins_in_naics": [
        {"award_id": "<id>", "amount_usd": <n>, "agency": "<name>", "pop_end": "YYYY-MM-DD"}
      ],
      "predicted_themes": ["<theme 1 grounded in award history>"],
      "claim_gaps": ["No CPARS data via MCP", "No protest history via MCP"],
      "ghost_language_hooks": ["<hook 1>", "<hook 2>"]
    }
  ],
  "pricing_benchmark": {
    "sample_size": <n>,
    "pricing_band": "valid | insufficient sample",
    "p25_usd": <n or null>,
    "median_usd": <n or null>,
    "p75_usd": <n or null>,
    "min_usd": <n>,
    "max_usd": <n>,
    "window": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"}
  },
  "recompete_signals": [
    "<observation, e.g. incumbent's flagship PoP ends in 7 months — recompete window>"
  ],
  "warnings": [
    "<e.g. 'PSC missing from workspace — search broadened to NAICS only'>"
  ],
  "data_provenance": {
    "kg_chunk_ids": ["chunk-xxxxxxxx"],
    "usaspending_award_ids": ["<generated_internal_id>"],
    "tools_invoked": ["mcp__usaspending__search_awards", "mcp__usaspending__get_recipient_profile", "..."]
  }
}
```

## Hand-off to `proposal-generator`

When the cover note is written, suggest the user run `proposal-generator` next so the `predicted_themes` and `ghost_language_hooks` from each competitor flow into the win-themes / FAB-chains step. Do not call `proposal-generator` yourself — that's a Phase 5 capability.

---

## Workflow B Checklist (Contract-Number Obligation Intel)

Execute in order. The output is an obligation-focused envelope that still includes competitor completeness findings.

### 1. Resolve the contract number

Input may be contract/order number only. Normalize and resolve using `mcp__usaspending__lookup_piid`.

Record:

- `input_contract_number`
- `resolved_award_id`
- `resolved_award_type`
- `resolved_piid`

If no match, return `GAP: contract number not found in USAspending lookup_piid`.

### 2. Classify scenario

Call `mcp__usaspending__get_award_detail` for the resolved award and classify into one of:

- `standalone_contract`
- `parent_idiq`
- `idiq_order`

Classification must cite the detail fields used. Never infer vehicle class from PIID format alone.

### 3. Build hierarchy and obligation rollup

Apply scenario-specific logic:

- **Standalone contract**:
  - Call `mcp__usaspending__get_transactions` on the resolved award.
  - Sum obligations by transaction, period of performance, and fiscal year.
  - Preserve transaction metadata that helps a human read the burn: `action_date`, modification identifier if present, `action_type`, `action_type_description`, and transaction-level narrative/description if present.

- **Parent IDIQ**:
  - Pull children via `mcp__usaspending__get_idv_children` and/or `mcp__usaspending__get_idv_activity`.
  - For each child order, pull transactions and compute per-order totals, period-of-performance view, and annual trend.
  - Report parent direct obligations separately from child obligations.

- **IDIQ order**:
  - Pull this order's transactions and totals.
  - Resolve parent IDIQ from award detail.
  - Pull sibling orders under the same parent and roll up full vehicle totals.
  - Use order and parent award detail plus sibling activity to capture the order's current period of performance window and any visible base/current/potential end dates.

For all scenarios:

- Include deobligation periods explicitly; net totals can decrease over time.
- Prefer **period-of-performance breakdowns over fiscal-year rollups** in the narrative and the artifact. Fiscal years are still required, but POP windows are the primary burn-rate lens.
- Build `obligations.by_period_of_performance` from award-detail and child-activity dates. Use the strongest available fields such as start date, current end date, and potential end date. If only a single current POP window is available, still emit it.
- For each item in `obligations.by_transaction`, include human-readable transaction metadata. If the transaction payload does not expose a narrative description, set `modification_description` to `null` and add a warning rather than inventing one.

**Derived fields — compute from fetched data (no additional MCP calls required):**

- Sort `by_transaction` by `action_date` ascending.
- Compute `cumulative_obligated_usd` as the running total of `amount_usd` through each transaction row (preserving negatives for deobligations).
- Assign `inferred_pop_segment` using this rule:
  - Modification `0` (or first transaction) → `"base_year"`
  - Each action_type `G` ("EXERCISE AN OPTION") transaction → `"option_year_1"`, `"option_year_2"`, etc. in sequence
  - Action_type `B` ("SUPPLEMENTAL AGREEMENT") or `J` ("FAR 52.232-22 FUNDED") within a segment → `"supplemental"`
  - Action_type `M` ("OTHER ADMINISTRATIVE ACTION"), `X` (termination), or `R` (rescind/cancel) → `"admin"`
  - Unknown or null action_type → `"unknown"`
- Compute `rate_analysis` using `obligations.by_period_of_performance.current_order_pop` (or the strongest available POP window):
  - `total_pop_days` = `pop_end_current` − `pop_start` in calendar days
  - `total_pop_months` = round to nearest 0.5
  - `monthly_burn_usd` = `net_obligated_usd` / `total_pop_months`
  - `daily_burn_usd` = `net_obligated_usd` / `total_pop_days`
  - `by_option_year`: group transactions by `inferred_pop_segment`, sum `amount_usd` per segment, estimate the segment's date window as the span between consecutive G-type action dates (use award end date as the final segment's close), and compute `monthly_rate_usd` = segment `obligated_usd` / segment `months`.
  - Include `derivation_notes` listing assumptions made (e.g., "Option year boundaries estimated from G-type action dates; per-modification POP dates not available in USAspending transaction payload").

### 4. Competitor completeness for multiple-award vehicles

For `parent_idiq` and `idiq_order` scenarios, derive competitor sets in two views:

- **Order-holder view**: distinct recipients with child orders under the parent IDIQ.
- **Parent-holder view**: parent recipients (normalize subsidiaries where possible).

Use parent/child vehicle linkage as primary. Use solicitation identifier only as a fallback clustering signal when direct linkage is incomplete.

Emit `competitor_discovery.completeness_status` as:

- `high` when parent-child traversal succeeded and sibling coverage is strong,
- `medium` when partial child coverage exists,
- `low` when only fallback solicitation clustering was possible.

### 5. Produce PTW seed outputs

Compute and include:

- recent annual run-rate,
- trailing 3-year weighted run-rate,
- highest-obligation years,
- optional-year pattern signal,
- recommended PTW baseline input.

### 6. Write the obligation envelope (MANDATORY)

Call `write_file` to save `artifacts/competitive_intel_obligation.json` before final summary.

```json
{
  "input_contract_number": "<raw user input>",
  "resolved": {
    "award_id": "<generated_internal_id>",
    "piid": "<resolved piid>",
    "scenario": "standalone_contract|parent_idiq|idiq_order"
  },
  "hierarchy": {
    "parent_award_id": "<id or null>",
    "child_award_ids": ["<id>"]
  },
  "obligations": {
    "total_obligated_usd": 0,
    "net_obligated_usd": 0,
    "by_period_of_performance": [
      {
        "label": "current_order_pop",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "obligated_usd": 0,
        "source": "award_detail|idv_activity|derived"
      }
    ],
    "by_fiscal_year": [{ "fy": "2025", "amount_usd": 0 }],
    "rate_analysis": {
      "pop_start": "YYYY-MM-DD",
      "pop_end_current": "YYYY-MM-DD",
      "total_pop_months": 0,
      "total_pop_days": 0,
      "monthly_burn_usd": 0,
      "daily_burn_usd": 0,
      "by_option_year": [
        {
          "label": "base_year|option_year_1|option_year_2|...",
          "estimated_start": "YYYY-MM-DD",
          "estimated_end": "YYYY-MM-DD",
          "months": 0,
          "obligated_usd": 0,
          "monthly_rate_usd": 0
        }
      ],
      "derivation_notes": [
        "<e.g. 'Option year boundaries estimated from action dates of G-type mods; actual POP dates not in USAspending transaction payload'>"
      ]
    },
    "by_transaction": [
      {
        "transaction_id": "<id>",
        "action_date": "YYYY-MM-DD",
        "modification_number": "0|P00001|null",
        "action_type": "G|B|M|null",
        "action_type_description": "EXERCISE AN OPTION|SUPPLEMENTAL AGREEMENT FOR WORK WITHIN SCOPE|null",
        "modification_description": "<transaction narrative if present>|null",
        "amount_usd": 0,
        "cumulative_obligated_usd": 0,
        "inferred_pop_segment": "base_year|option_year_1|option_year_2|supplemental|admin|unknown"
      }
    ],
    "by_child_order": [
      {
        "award_id": "<id>",
        "description": "<child order description if present>|null",
        "pop_start_date": "YYYY-MM-DD|null",
        "pop_end_date": "YYYY-MM-DD|null",
        "amount_usd": 0
      }
    ]
  },
  "competitor_discovery": {
    "order_holder_recipients": [{ "name": "<recipient>", "obligated_usd": 0 }],
    "parent_holder_recipients": [{ "name": "<parent>", "obligated_usd": 0 }],
    "linkage_method_used": "parent_child|piid_family|solicitation_fallback",
    "completeness_status": "high|medium|low"
  },
  "ptw_seed": {
    "recent_annual_run_rate_usd": 0,
    "three_year_weighted_run_rate_usd": 0,
    "recommended_baseline_usd": 0
  },
  "warnings": ["<data caveat or linkage caveat>"],
  "data_provenance": {
    "usaspending_award_ids": ["<generated_internal_id>"],
    "tools_invoked": [
      "mcp__usaspending__lookup_piid",
      "mcp__usaspending__get_award_detail",
      "mcp__usaspending__get_transactions",
      "mcp__usaspending__get_idv_children"
    ]
  }
}
```

Do not omit these fields just because they are sparse. A partially populated POP or transaction record is still useful if it clearly shows which values were unavailable from the source.

### 7. Final cover note

Summarize:

- scenario detected,
- total/net obligations,
- number of child orders,
- competitor completeness status,
- PTW seed recommendation,
- warnings.

## References

- [`references/black_hat_template.md`](./references/black_hat_template.md) — Canonical one-pager structure
- [`references/data_sources.md`](./references/data_sources.md) — USAspending MCP tool reference + what each field means + known gaps (no CPARS / no protest data via MCP yet)
