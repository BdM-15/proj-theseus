# PTW Handoff — Output Envelope Format

The workload-analyzer emits a structured handoff consumed by the `price-to-win`
skill's cost-stack build step. Produce this as a JSON block at the end of the
Workload Analysis report.

---

## Envelope Schema

```json
{
  "workload_analysis_version": "1.0",
  "workspace": "<workspace name>",
  "source_attachments": ["<tab or file name>"],
  "data_coverage": {
    "period_start": "<FY or CY>",
    "period_end": "<FY or CY>",
    "site_count_total": 0,
    "site_count_conus": 0,
    "site_count_oconus": 0,
    "oconus_high_risk_count": 0
  },
  "demand_summary": {
    "base_year_volume": 0,
    "cagr_pct": 0.0,
    "adjustment_factors": [
      {
        "name": "<e.g. phone_resolution>",
        "value": 0.0,
        "basis": "<observed | stated assumption>",
        "variable": true
      }
    ],
    "field_touch_volume_adjusted": 0,
    "pareto_tier1_sites": [],
    "pareto_tier1_volume_pct": 0.0
  },
  "option_year_projections": [
    {
      "period": "Option 1",
      "conservative": 0,
      "base": 0,
      "optimistic": 0
    }
  ],
  "pricing_risks_ranked": [
    {
      "rank": 1,
      "item": "<site name or CLIN or factor>",
      "risk_type": "<volume_growth | oconus_exposure | high_volatility | adjustment_factor | clin_quantity_gap>",
      "description": "<one sentence>",
      "estimated_cost_impact": "<low | medium | high | quantified if possible>"
    }
  ],
  "estimator_assumptions_to_validate": [
    "<free text — each item is something the PTW estimator must confirm or challenge>"
  ],
  "confidence": {
    "overall": "<high | medium | low>",
    "basis": "<brief rationale — e.g. '3 years of data, consistent methodology'>"
  }
}
```

---

## Field Guidance

### `adjustment_factors`

List every factor found in footnotes or notes that modifies raw volume to field-touch
volume. Common examples:

- `phone_resolution`: fraction of events resolved remotely (reduces field visits)
- `warranty_exclusion`: fraction excluded during warranty period
- `pm_bundling`: PM visits bundled per site per year regardless of CM volume

Set `variable: true` if the factor has changed year-over-year or is stated as an
assumption without historical backing. Variable factors are pricing risks.

### `pricing_risks_ranked`

Rank from highest to lowest pricing impact. Top 3 items are the most important for
the estimator to pressure-test. Use `estimated_cost_impact: "quantified"` only if
you can state a dollar range; otherwise use high/medium/low with a rationale in
`description`.

### `estimator_assumptions_to_validate`

Plain-language list. Each item should be specific enough that the estimator can
look up an answer. Examples:

- "Confirm whether Diego Garcia site still has active SOFA agreement for PoP period"
- "Validate phone-resolution rate assumption — 31% is from FY2021 data; check if
  current contract reflects updated rate"
- "Option Year 3 CLIN quantities are flat; verify with PM whether growth is
  intentionally absorbed or an oversight"

### `confidence`

High: ≥3 years of data, consistent methodology, adjustment factors observed not assumed.
Medium: 2 years of data, or one or more adjustment factors are stated assumptions.
Low: Single year of data, or significant gaps in site coverage, or schema ambiguities
that could not be resolved.

---

## Usage Note

The `price-to-win` skill will consume `demand_summary.field_touch_volume_adjusted`
as the base labor-model driver, `option_year_projections` as the volume ramp, and
`pricing_risks_ranked` to apply a risk reserve percentage to each exposure. Ensure
the adjustment factors are fully applied before populating `field_touch_volume_adjusted`.
