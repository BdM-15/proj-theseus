# OT Milestone Cost Buildup

Per-milestone should-cost methodology for prototype OTs. Bid-side equivalent of the AO's independent estimate.

## 1. Constants

| Constant                               | Value              | Source                                           |
| -------------------------------------- | ------------------ | ------------------------------------------------ |
| Productive hours per FTE-year          | 1880               | Government convention (subtracts holidays + PTO) |
| Paid hours per FTE-year                | 2080               | DOL standard; use ONLY for paid-rate division    |
| Burden — commercial low/mid/high       | 1.80 / 2.00 / 2.20 | Industry mid-tier wrap rate envelope             |
| Burden — academic / FFRDC low/mid/high | 1.65 / 1.85 / 2.05 | Lower G&A pool                                   |
| Wage escalation                        | 2.5%/yr            | BLS ECI mid-band default                         |
| BLS reported wage cap                  | $239,200           | OEWS top-coded; flag if P75=P90 below cap        |
| Cost-share default (path C)            | 0.333              | 10 USC 4022(d)(1)(C)                             |
| Consortium fee default                 | 0.05               | DIU/most consortium templates                    |
| Cost-type ceiling margin               | 0.15               | NTE = should_cost × 1.15                         |
| Production learning curve (default)    | 0.95               | Crawford 95%; aerospace/electronics 0.85-0.92    |

## 2. SOC Mapping (BLS)

Common OT-prototype labor categories. Use the SOC code to call `mcp__bls_oews__get_wage_data`. Adjust for tier (junior / mid / senior) by selecting P25 / P50 / P75 percentiles.

| Role                                             | SOC     | Notes                                       |
| ------------------------------------------------ | ------- | ------------------------------------------- |
| Software developer                               | 15-1252 | Default for software prototypes             |
| Cybersecurity engineer / Info security analyst   | 15-1212 | DoD cyber prototypes                        |
| Computer / IS research scientist                 | 15-1221 | AI/ML research                              |
| Data scientist                                   | 15-2051 | AI/ML applied + analytics                   |
| Computer hardware engineer                       | 17-2061 | Custom hardware design                      |
| Electrical engineer                              | 17-2071 | RF, power, control systems                  |
| Aerospace engineer                               | 17-2011 | UAS, propulsion, structures                 |
| Mechanical engineer                              | 17-2141 | Mechanical design, thermal                  |
| Industrial engineer                              | 17-2112 | Process, manufacturing prototypes (4022(f)) |
| Materials engineer                               | 17-2131 | Advanced materials prototypes               |
| Production / first-line manufacturing supervisor | 51-1011 | Production follow-on (4022(f))              |
| Project / program manager                        | 11-3021 | Engineering management                      |

### Academic / FFRDC roles (use institutional rate, NOT BLS)

| Role                        | Hourly band                             | Notes                                           |
| --------------------------- | --------------------------------------- | ----------------------------------------------- |
| Principal Investigator (PI) | $120-180                                | Faculty rate at standard university overhead    |
| Postdoctoral researcher     | $80-110                                 | Including fringe                                |
| Graduate research assistant | $55-75                                  | Institutional rate; varies by university        |
| Undergraduate researcher    | $25-40                                  | Hourly student rate                             |
| FFRDC / UARC research staff | Varies — use FFRDC published rate sheet | Lincoln Lab, MITRE, APL, GTRI, JPL, SEI publish |

## 3. Nine-Step Workflow

### Step A — Validate the milestone structure

Confirm every milestone has: id, phase, TRL in/out, duration_months, deliverables, payment_type, exit_criterion. Re-read [trl_milestone_patterns.md](../trl_milestone_patterns.md) if any field is missing.

### Step B — BLS labor benchmarking

For each labor category at the performance metro:

1. Resolve SOC + metro to BLS series. Call `mcp__bls_oews__get_wage_data` (or `igce_wage_benchmark` for percentile breakouts).
2. Capture series_id, vintage (year-month), and percentiles.
3. Age the wage forward: `aged_wage = bls_wage × (1 + 0.025) ^ years_from_vintage`.
4. **Productive vs paid hours**:
   - For **annual cost** of a fully-utilized FTE: `direct_annual = aged_annual_wage` (BLS annual is already paid annual)
   - For **hourly billing rate**: `hourly = aged_annual_wage / 2080` (paid hours, the convention BLS aligns with)
   - For **labor-hour estimation in a milestone**: `category_hours = 1880 × (milestone_duration_months / 12) × FTE` (productive hours — subtracts non-billable PTO/holidays)
5. If P75 == P90 and neither hits $239,200, flag flat-tail in methodology_notes.

### Step C — CALC+ market anchor

For each labor category, call `mcp__gsa_calc__igce_benchmark` (or `price_reasonableness_check` for a single anchor rate). Capture N, P25, P50, P75, P90, keyword.

If N < 25, label "directional only" — do not lean on CALC+ as primary anchor.

For NDC performers, CALC+ is **market context only** — NDCs are not bound by GSA MAS ceilings.

### Step D — Materials

Size by prototype-type heuristic (see [trl_milestone_patterns.md](../trl_milestone_patterns.md) §4):

| Prototype type          | Materials % of total |
| ----------------------- | -------------------- |
| Software                | 10-20%               |
| Software + hardware     | 20-40%               |
| Hardware single-article | 40-60%               |
| Hardware multi-article  | 50-70%               |
| Process / manufacturing | 30-50%               |

Materials are at-cost (no burden, no fee). Itemize known long-lead components separately. Apply per-milestone, not spread evenly.

### Step E — Travel via GSA Per Diem

For each travel destination per milestone, call `mcp__gsa_perdiem__estimate_travel_cost` with city, state, num_nights, and FY (defaults to current). The MCP applies FTR 301-11.101 (75% first/last day M&IE, 0-night day-trip rules).

For DoD installations, translate to civilian locality (e.g., "WPAFB" → "Dayton, OH"; "Eglin AFB" → "Valparaiso, FL").

OCONUS (outside CONUS): GSA rates do NOT apply. Flag and stop — DoS rates required for OCONUS, not in scope here.

### Step F — Should-cost buildup per milestone

For each milestone:

```
milestone_labor    = sum over categories of (category_hours × burdened_rate)
milestone_materials = (per-milestone allocation per type heuristic)
milestone_travel    = sum over destinations of GSA per-diem result
milestone_odc       = cloud + licenses + test infrastructure (named line items)
milestone_should_cost = milestone_labor + milestone_materials + milestone_travel + milestone_odc
```

Reconcile sum-of-milestone durations to PoP. If milestones don't sum to PoP, flag — either parallel work-streams (acceptable, document) or scoping gap (fix before submitting).

For cost-type milestones: NTE = should_cost × 1.15.

### Step G — Three scenarios (low / mid / high)

Apply burden multipliers low/mid/high (1.8/2.0/2.2 commercial; 1.65/1.85/2.05 academic) AND BLS percentile bands (P25/P50/P75) per category. Mid is the bid target. Output low/mid/high per milestone AND per total.

### Step H — Apply 10 USC 4022(d) cost-share path

Per [ot_authority_taxonomy.md](../ot_authority_taxonomy.md) §3:

```
if path == "4022(d)(1)(A)" or path == "4022(d)(1)(B)":
    government_obligation = milestone_should_cost
    performer_share = 0
elif path == "4022(d)(1)(C)":
    government_obligation = milestone_should_cost × (1 - 0.333)
    performer_share = milestone_should_cost × 0.333
elif path == "4022(d)(1)(D)":
    government_obligation = milestone_should_cost
    performer_share = 0
elif authority == "10 USC 4021":
    # cost-share statutorily inapplicable
    government_obligation = milestone_should_cost
    performer_share = 0
elif authority == "10 USC 4022(f)":
    # production follow-on; gov funds 100% regardless of predecessor path
    government_obligation = milestone_should_cost
    performer_share = 0

if consortium:
    government_obligation += milestone_should_cost × 0.05  # consortium fee on top
```

### Step I — Workbook (optional)

If the user wants a deliverable workbook, the JSON envelope hands off to `renderers/render_xlsx.py`. The renderer produces a 7-sheet pattern: Summary | Milestones | Labor | Materials | Travel | ODC | Methodology. Use Excel formulas (=SUM, =VLOOKUP) for any derived cell so AO review can audit the math; keep raw data sheets purely numeric.

## 4. Production Follow-On (4022(f)) Specifics

If the workflow is a production follow-on:

1. Inherit performer_type and cost_share_path from predecessor prototype (cite predecessor agreement number).
2. **Set cost_share_required = false regardless of predecessor.** Government funds 100% of production.
3. Apply **learning curve** to BOM only across lots:
   ```
   lot_BOM_cost = base_BOM × learning_curve ^ (lot_index - 1) × (1 + materials_escalation) ^ years_from_PoP_start
   ```
   Default learning_curve = 0.95 (Crawford). Aerospace/electronics 0.85-0.92. Simple assembly 0.95-0.98.
4. Labor rate aging: 2.5%/yr from prototype rates, NOT re-benchmarked from scratch (the AO knows the rates from the prototype agreement).
5. Materials escalation: 2.5%/yr default; higher for commodity-volatile categories (steel, lithium, semiconductors — flag and document).

## 5. Pre-bid quick approximation (Workflow B / pre-solicitation)

When you don't yet have a parsed solicitation, use a single blended labor rate for a rough should-cost band:

```
blended_hourly = (median_BLS_for_dominant_SOC × burden_mid) / 2080
quick_should_cost = blended_hourly × FTE × 1880 × duration_months / 12
```

Then size materials/travel by type heuristic. State explicitly that this is a pursuit-stage approximation, not bid-quality.
