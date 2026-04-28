# FFP Cost Model — Firm-Fixed-Price Wrap-Rate Buildup

**Use when**: the opportunity is FFP under FAR 16.202, or commercial-item professional services priced by deliverable/period.

**Bidder stance**: estimate the **competitor's likely fully burdened rate (FBR)** so you can target a price 5–10% under without taking unacceptable cost risk on your own delivery.

## The Wrap-Rate Math

Layer-by-layer per labor category:

```
1. Direct Labor Rate    = aged_annual_wage / 2080
2. Fringe Amount        = Direct Labor * fringe_rate
3. Labor + Fringe       = Direct Labor + Fringe
4. Overhead Amount      = Labor_Fringe * overhead_rate
5. Subtotal             = Labor_Fringe + Overhead
6. G&A Amount           = Subtotal * ga_rate
7. Total Cost           = Subtotal + G&A
8. Profit Amount        = Total_Cost * profit_rate
9. Fully Burdened Rate  = Total_Cost + Profit
```

**Implied multiplier** = FBR / Direct Labor = `(1+fringe) × (1+OH) × (1+G&A) × (1+profit)`. At default 32/80/12/10 → **~2.93x**.

FFP rates run higher than LH/T&M because the contractor absorbs cost-overrun risk.

## Vehicle Preset Table — MANDATORY for FFP PTW

The competitor's wrap is driven by their contract vehicle and environment, NOT by skill defaults. **Always pick a preset before quoting an FBR.** If the workspace doesn't tell you the vehicle, ask.

| Vehicle / environment | Fringe | Overhead | G&A | Profit | Implied mult | Expected band |
|---|---|---|---|---|---|---|
| GSA MAS (commercial) | 30% | 60% | 10% | 8% | **2.47x** | 2.3–2.7x |
| Agency BPA / IDIQ non-cleared | 32% | 80% | 12% | 10% | **2.93x** | 2.7–3.1x |
| Agency BPA / IDIQ cleared (TS/SCI in SCIF) | 32% | 95% | 13% | 10% | **3.17x** | 3.0–3.4x |
| DoD prime cleared | 33% | 100% | 13% | 11% | **3.32x** | 3.1–3.5x |
| DoE M&O / FFRDC | 36% | 95% | 13% | 7% | **2.92x** | 2.7–3.1x |
| R&D / BAA CR (use FFP only if explicitly FFP, else use CR model) | 32% | 90% | 12% | 8% | **3.03x** | 2.9–3.3x |
| OCONUS / hostile theater | 35% | 120% | 14% | 12% | **3.79x** | 3.6–4.0x |

**Math check**: `(1+fringe) × (1+OH) × (1+G&A) × (1+profit)`. Example GSA MAS commercial: 1.30 × 1.60 × 1.10 × 1.08 = **2.47x**.

**Sanity band**: flag for review if the MID multiplier you compute lands OUTSIDE the band shown for the chosen preset. A 3.17x cleared build is normal (in-band); a 3.17x GSA MAS commercial build is anomalous (out-of-band — usually means the wrong preset).

## Three-Scenario Buildup

Vary EACH component (not a single multiplier):

| Component | Low | Mid | High | Notes |
|---|---|---|---|---|
| Fringe | 25% | 32% | 40% | Higher for generous benefits, union shops |
| Overhead | 60% | 80% | 120% | Higher for SCIF/cleared, large firms |
| G&A | 8% | 12% | 18% | Higher for large corporate structures |
| Profit | 7% | 10% | 15% | FAR 15.404-4: risk, investment, complexity |

The MID column should match the chosen vehicle preset; LOW/HIGH are stress bounds.

## BLS Wage Aging

The BLS OEWS data vintage lags real labor markets. Age forward to contract start:

```
months_gap = (contract_start - bls_vintage) in months
aging_factor = (1 + escalation_rate) ^ (months_gap / 12)
aged_annual_wage = bls_raw_annual * aging_factor
```

Default escalation = 2.5%/yr. Document the aging adjustment in the methodology.

## Sanity Checks Before Quoting a PTW

1. **Implied multiplier in 2.2x–3.5x band** for CONUS commercial; > 3.5x demands SCIF/OCONUS/niche labor justification.
2. **Per-FTE annualized cost in $100k–$1M band**. Outside that, the math is wrong (usually a row-reference bug — Aged Annual Wage instead of Hourly DL).
3. **CALC+ divergence**: if BLS-burdened MID vs CALC+ P50 diverges > 70%, your competitor probably can't actually price there. Re-check tier match (Senior vs aggregate pool).
4. **Profit basis**: if you assumed 10% profit on a R&D-heavy or high-risk scope, consider whether the competitor would actually carry 12–15% to absorb the risk.

## FAR Citations to Include in Output

- **FAR 15.402** — cost or pricing data (always cite for IGCE-equivalents).
- **FAR 15.404-1(a)** — cost analysis.
- **FAR 15.404-4** — profit/fee analysis (the 10% default is a starting point, not a ceiling).
- **FAR 16.202** — FFP contracts.

## Output Reminders

- Three scenarios (low/mid/high) per LCAT.
- Lifecycle = base year + option years escalated at 2.5%/yr (default).
- Hand the JSON envelope to `renderers/render_xlsx.py` if a workbook deliverable is requested.
- Methodology section names the vehicle preset, the aging factor (numeric), the BLS vintage, the CALC+ N per LCAT, and the divergence-vs-CALC+ percentage.
