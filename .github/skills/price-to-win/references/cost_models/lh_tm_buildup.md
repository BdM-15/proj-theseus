# LH / T&M Cost Model — Single Burden Multiplier Buildup

**Use when**: the opportunity is Labor Hour or Time-and-Materials under FAR 16.601. T&M when there is a separate at-cost materials/licenses/cloud-hosting block.

**Bidder stance**: estimate the **competitor's loaded hourly rate** so you can target a price that wins on labor without losing on materials handling.

## The Burden Multiplier Math

Per labor category:

```
Loaded Hourly Rate = (BLS Aged Annual Wage / 2080) * Burden Multiplier
```

Default burden = **2.0x**. Stress band = **1.8x – 2.2x**.

**Scope of burden**: applies ONLY to labor. Does NOT apply to materials, travel, ODCs, or subcontractor pass-throughs.

LH/T&M loaded rates run lower than FFP fully-burdened rates because the government (not the contractor) absorbs hour-overrun risk on LH, and material-cost risk on T&M.

## Three-Scenario Buildup

| Scenario | Burden | Use case |
|---|---|---|
| Low | 1.8x | Lean small business, low overhead, GSA MAS pricing |
| Mid | 2.0x | Default for capture PTW |
| High | 2.2x | Large prime, cleared environment, premium G&A |

Run all three across all LCATs and all periods.

## T&M Materials at Cost

Per FAR 16.601(b), T&M materials are reimbursed **at actual cost** with NO burden applied. Categories typically include:

- Software licenses (Adobe, ServiceNow, etc.)
- Cloud hosting (AWS, Azure, GCP) consumed for the customer
- Hardware purchases
- Specialized equipment

**Materials handling fee** (FAR 31.205-26(e)): the contractor MAY charge a materials-handling fee to recover acquisition cost (typically 5–8%). Include this ONLY if the user explicitly tells you the competitor's structure includes one. Default = no materials-handling fee in the PTW.

## LH/T&M Specific Buildup Layout

```json
{
  "labor": [
    {
      "category": "Senior Cyber Analyst",
      "soc": "15-1212",
      "metro": "Washington-Arlington-Alexandria, DC-VA-MD-WV",
      "bls_aged_annual": 168400,
      "direct_hourly": 80.96,
      "burden_low": 1.8,
      "burden_mid": 2.0,
      "burden_high": 2.2,
      "loaded_hourly_low": 145.73,
      "loaded_hourly_mid": 161.92,
      "loaded_hourly_high": 178.11,
      "headcount_fte": 3,
      "annual_hours": 5640,
      "annual_labor_mid": 913229
    }
  ],
  "materials": [
    {"category": "AWS hosting", "annual_cost": 84000, "burden_applied": false},
    {"category": "Software licenses", "annual_cost": 28000, "burden_applied": false}
  ],
  "materials_handling_fee": null
}
```

## Travel Treatment

Travel under LH/T&M is reimbursed at actual cost per FAR 31.205-46 (FTR for civilian, JTR for DoD), with NO burden applied. Use `mcp__gsa_perdiem__estimate_travel_cost` to compute lodging + M&IE per destination. Add as a separate line item.

## Ceiling Hours (FAR 16.601(c)(2))

LH and T&M contracts have an Estimated Total Cost AND an Estimated Total Hours ceiling. The competitor's cost stack assumption should include both. If the RFP gives you task-order labor-hour caps, the lifecycle total is bounded — use the MIN(BLS-derived, ceiling) for the lifecycle high scenario.

## Sanity Checks

1. **Loaded hourly in $80–$400 band** for professional services. Outside → re-check BLS series ID and metro.
2. **CALC+ divergence**: GSA CALC+ rates are LH/T&M ceiling rates (not FFP). For LH/T&M PTW, the BLS-burdened MID should be WITHIN ±25% of CALC+ P50. Larger gap → tier mismatch (Senior vs aggregate).
3. **Materials block ≤ 30% of labor**: T&M with materials > 30% of labor often signals miscategorization (should be CR with separate materials cost pool).

## FAR Citations to Include in Output

- **FAR 16.601** — Time-and-materials and Labor Hour contracts.
- **FAR 16.601(b)** — materials at cost, no profit on materials.
- **FAR 16.601(c)(2)** — ceiling hours / not-to-exceed.
- **FAR 31.205-26(e)** — materials handling cost (cite ONLY if including a handling fee).
- **FAR 31.205-46** — travel cost reimbursement.

## Output Reminders

- Three burden scenarios (1.8 / 2.0 / 2.2) per LCAT.
- Materials block separate from labor; no burden applied.
- Travel separate from materials and labor; per-diem from `mcp__gsa_perdiem__estimate_travel_cost`.
- T&M lifecycle = (labor_loaded × hours_per_year × years) + (materials_at_cost × years) + (travel × years).
- Methodology cites FAR 16.601 + the chosen burden tier rationale.
