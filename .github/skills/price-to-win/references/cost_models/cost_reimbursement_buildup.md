# Cost-Reimbursement (CR) Cost Model — Pools + Fee Buildup

**Use when**: the opportunity is cost-reimbursement under FAR 16.301–16.307. Common variants: **CPFF** (Cost-Plus-Fixed-Fee), **CPAF** (Cost-Plus-Award-Fee), **CPIF** (Cost-Plus-Incentive-Fee). Also: BAAs (FAR 35.016), R&D, exploratory work where scope is undefined.

**Bidder stance**: estimate the **competitor's likely cost pools and fee structure** so capture knows what fee position and cost base will win.

## Prerequisites the Competitor Must Have (Affects PTW Plausibility)

- DCAA-approved accounting system (FAR 16.301-3(a)(1))
- Disclosed cost accounting practices (CAS-covered if > $7.5M / FAR 30.201-4)
- Provisional billing rates negotiated with cognizant audit agency

If the suspected competitor is a small business without DCAA approval, the CR PTW is implausible — flag and revisit (they likely propose as a sub to a CR-cleared prime).

## The Cost-Pool Math (Different from FFP)

CR uses **layered cost pools**, NOT a wrap-rate multiplier:

```
1. Direct Labor
2. Fringe          = Direct Labor * fringe_rate
3. Labor + Fringe  = Direct Labor + Fringe
4. Overhead        = Labor_Fringe * overhead_rate
5. Subtotal        = Labor_Fringe + Overhead
6. G&A             = Subtotal * ga_rate
7. FCCM            = (Direct Labor or Total Cost) * FCCM_rate   [optional, default 0]
8. Total Cost      = Subtotal + G&A + FCCM
9. Travel (at cost, no fee, no burden beyond G&A if policy allows)
10. ODCs (at cost, pass-through, NO fee)
11. Subcontractor cost (at cost, may bear limited G&A but typically NO fee on prime's part)
12. ----- FEE-BEARING COST = items 1-9 (Labor + Fringe + OH + G&A + FCCM + Travel) -----
13. ----- NON-FEE COST     = items 10-11 (ODCs + sub pass-through) -----
14. Fee = Fee-Bearing Cost * fee_rate   [by subtype — see below]
15. Total Estimated Cost + Fee = Total Cost + Travel + ODCs + Sub + Fee
```

**Critical**: Fee applies to **Fee-Bearing Cost ONLY**. Pass-through ODCs and subcontractor costs do NOT bear prime fee. This is the most-violated rule in CR PTW estimates.

## FCCM (Facilities Capital Cost of Money)

Per FAR 31.205-10 / CAS 414. Default = **0%**. Include only if:

- Competitor has substantial dedicated facilities for this contract
- The RFP allows or requires FCCM recovery
- The competitor has historically claimed FCCM on similar awards

Typical range when applied: 0.5% – 2.0% of total cost.

## Fee Subtype Math

### CPFF — Cost-Plus-Fixed-Fee

Fixed dollar amount, regardless of actual cost. **Statutory cap: 10% of estimated cost** for R&D, **15%** for experimental/developmental/research per 10 USC 3322(a). Typical fee: **6–8%**.

```
Fee_CPFF = Fee-Bearing Cost * 0.07   (typical mid)
```

Three scenarios: 6% / 7% / 8% on Fee-Bearing Cost.

### CPAF — Cost-Plus-Award-Fee

Base fee (typically 0–3%) + award-fee pool (typically 5–15%) earned based on subjective performance evaluation.

```
Base Fee   = Fee-Bearing Cost * 0.03
Award Pool = Fee-Bearing Cost * 0.10
Earned     = Award Pool * earned_pct   (default 85% historical mean)
Total Fee  = Base Fee + Earned
```

Award-fee earned percentages historically average **80–90%** (per government-wide CPAF performance studies). Default to **85%** for PTW. Document the assumption.

Three scenarios: earned 70% / 85% / 95%.

### CPIF — Cost-Plus-Incentive-Fee

Target cost + target fee + share ratio + min/max fee.

```
Share Ratio  = (e.g., 80/20 — government 80%, contractor 20% of cost variance)
Variance     = Target Cost - Actual Cost
Fee Adjust   = Variance * contractor_share_pct
Earned Fee   = clamp(Target Fee + Fee Adjust, Min Fee, Max Fee)
```

Typical: target fee **7%**, min fee **3%**, max fee **12%**, share ratio **80/20**. Variance bounds for PTW scenarios: **±10%** (mid stress), **±25%** (high stress).

Scenario shape: 3 cost scenarios (low/mid/high) × 3 fee outcomes (underrun/target/overrun) = **9-cell matrix**.

## Three-Scenario Pool Buildup (Same Components as FFP, No Profit)

| Component | Low | Mid | High | Notes |
|---|---|---|---|---|
| Fringe | 25% | 32% | 40% | Same range as FFP |
| Overhead | 60% | 80% | 120% | SCIF/cleared bumps mid to ~95% |
| G&A | 8% | 12% | 18% | Same range as FFP |
| FCCM | 0% | 0% | 1.5% | Default 0 unless competitor has dedicated facilities |
| Fee (CPFF) | 6% | 7% | 8% | Statutory cap 10% (R&D) / 15% (developmental) |
| Fee (CPAF) | 70% earned | 85% earned | 95% earned | On a 10% award pool |
| Fee (CPIF) | underrun | target | overrun | 80/20 share, 3%–12% min/max |

## Travel Under CR

Travel reimbursed at actual cost per FAR 31.205-46 (FTR civilian / JTR DoD). Travel **DOES** typically bear G&A (allocated indirect) but NOT fringe or overhead. Some competitors structure travel as a separate cost pool with its own indirect rate; for PTW MID, treat travel as raw + G&A only.

## Sanity Checks

1. **Total fee ≤ 15% of Fee-Bearing Cost** for any subtype — cap per 10 USC 3322(a). Hard ceiling.
2. **Fee-Bearing Cost > 70% of Total Estimated Cost** for typical services CR. If FBC < 70%, the ODC/sub pass-through is unusually large — re-check categorization.
3. **No fee on ODCs / subs** — if you computed fee on the grand total, you over-stated PTW by 10–30%.
4. **DCAA-approved competitor** — if not, CR is implausible.
5. **CPAF earned % defensible** — anything > 95% needs justification; < 70% suggests the agency intends to use award fee as a stick.

## CR-Specific JSON Envelope Additions

```json
{
  "cost_model": "CR-CPAF",
  "cost_pools": {
    "fringe_pct": 0.32,
    "overhead_pct": 0.80,
    "ga_pct": 0.12,
    "fccm_pct": 0.0
  },
  "fee_structure": {
    "subtype": "CPAF",
    "base_fee_pct": 0.03,
    "award_pool_pct": 0.10,
    "earned_pct_assumption": 0.85,
    "rationale": "Government-wide CPAF historical mean 85%."
  },
  "fee_bearing_cost_low": 1240000,
  "fee_bearing_cost_mid": 1560000,
  "fee_bearing_cost_high": 1920000,
  "non_fee_cost_low": 280000,
  "non_fee_cost_mid": 340000,
  "non_fee_cost_high": 420000,
  "fee_low": 99200,
  "fee_mid": 179400,
  "fee_high": 249600
}
```

## FAR Citations to Include in Output

- **FAR 16.301** — general (cost-reimbursement contracts).
- **FAR 16.301-3** — limitations (DCAA accounting system requirement).
- **FAR 16.306** — CPFF.
- **FAR 16.305** — CPIF.
- **FAR 16.405-2** — CPAF.
- **FAR 35.016** — BAA (if applicable).
- **FAR 31.205-10** + **CAS 414** — FCCM.
- **FAR 15.404-4(c)(4)(i)** — fee analysis.
- **10 USC 3322(a)** — statutory fee caps (10% R&D, 15% experimental/developmental).

## Output Reminders

- For CPIF, present the **9-cell matrix** (3 cost × 3 fee outcomes) — one big number is misleading.
- For CPAF, ALWAYS state the earned-fee assumption explicitly (85% default).
- Cite the statutory cap and confirm the proposed fee is below it.
- Methodology section names the fee subtype, the share ratio (CPIF), the earned-fee assumption (CPAF), the FCCM rate (and zero-rationale), and whether the competitor's DCAA status is verified or assumed.
