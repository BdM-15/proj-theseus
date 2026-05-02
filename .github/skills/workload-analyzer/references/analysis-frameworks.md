# Analysis Frameworks by Archetype

For statistical method details (test selection, effect sizes, pitfall avoidance),
reference `data-analyzer/references/statistical-methods.md` and
`data-analyzer/references/pitfalls.md`.

---

## Geographic Scope Framework

### OCONUS Risk Tiering

Assign each OCONUS location a risk tier based on pricing impact:

| Tier   | Criteria                                                           | Pricing Implication                             |
| ------ | ------------------------------------------------------------------ | ----------------------------------------------- |
| High   | Remote island, combat zone, SOFA-restricted, no commercial flights | 2–3× CONUS travel cost; potential schedule risk |
| Medium | Allied nation with US presence, standard SOFA, commercial access   | 1.3–1.8× CONUS travel cost                      |
| Low    | US territories, Caribbean, close allied nations                    | 1.1–1.3× CONUS travel cost                      |

CONUS sites: base tier, standard travel per-diem rates.

### Geographic Concentration Index

Calculate what fraction of sites are in each region/country. Flag if:

- Any single country (non-US) holds >20% of OCONUS sites — single-point logistics risk
- Any single state holds >25% of CONUS sites — regional labor market dependency
- OCONUS sites are >25% of total — elevated overall travel burden

### Site Anomaly Checks

- Duplicate site names or codes → confirm whether one physical site or data error
- Sites with identical codes but different names (or vice versa) → resolve before pricing
- Sites listed in scope attachment but absent from workload history → zero-demand sites
  still require contractual coverage (PM visits); flag for minimum staffing floor

---

## Demand / Volume History Framework

### Growth Rate Calculation

With n years of data, compute:

- **Simple annual growth rate** per period: (Yᵢ − Yᵢ₋₁) / Yᵢ₋₁
- **CAGR** across full period: (Yₙ / Y₁)^(1/(n−1)) − 1
- Use CAGR for option-year projection; use per-period rates to detect acceleration/deceleration

**Minimum data threshold:** 3 years for a reliable trend. With only 2 years, state the
growth rate but label projections as low-confidence.

### Adjustment Factor Extraction

Scan all footnotes, notes rows, and cell comments. For each factor found:

1. State the factor explicitly (e.g., "31% of CMs resolved by phone")
2. Calculate the adjusted volume (total × (1 − phone rate) = field-touch volume)
3. Note whether the factor has been consistent year-over-year or variable
4. Flag if the factor is not validated by data (stated assumption vs. observed)

Variable adjustment factors are pricing risk — if the phone resolution rate degrades
from 31% to 20%, field labor costs increase ~16% with no contract relief mechanism.

### Pareto Analysis

Rank sites by total volume (or CM average if available). Compute cumulative % of volume:

- Identify the sites that account for 50% of volume ("Tier 1")
- Identify the sites that account for 80% of volume ("Tier 2")
- Everything else is Tier 3 (low-volume; may still require minimum coverage)

Report the site count at each tier. If 10% of sites drive 50% of volume, staffing
strategy should be site-weighted, not uniform.

### Volatility Scoring

For each site with ≥3 years of data, compute Coefficient of Variation (CV = σ/μ):

- CV < 0.2: stable, low pricing risk
- CV 0.2–0.5: moderate variability, include buffer
- CV > 0.5: high volatility, consider risk reserve or T&M CLIN

Sites with high volume AND high CV are the highest-priority items for the estimator.

### Option-Year Projection

Using observed CAGR:

- **Conservative:** flat (no growth) — use if CAGR is <3% and trend is decelerating
- **Base:** apply CAGR to each option year
- **Optimistic:** apply (CAGR + 1 standard deviation of annual growth rates)

Present all three for the estimator. Never present a single-point projection without
confidence bounds.

---

## Manning / Staffing Framework

### Coverage Ratio Analysis

For each role that requires on-site presence:

- Coverage ratio = total FTEs in role ÷ total sites requiring that role
- Ratio < 1.0: shared coverage (one person covers multiple sites) — validate travel
  feasibility given geographic spread
- Ratio > 1.5 at high-volume sites: investigate whether volume justifies dedicated headcount

### Staff-to-Demand Alignment

If both staffing and demand history are available:

- Compute implied throughput per FTE: total volume ÷ total field FTEs
- Compare to industry norms or incumbent-implied throughput
- Flag if government-provided staffing model implies unrealistic productivity

---

## CLIN / Task Structure Framework

### Quantity Trend Check

Compare CLIN quantities across base and option years:

- Flat quantities with growing demand history → potential underestimate / pricing trap
- Declining quantities with growing demand → significant risk; flag for compliance-auditor
- Option-year quantities that jump discontinuously → verify whether scope change is intended

### Unit Type Risk Flag

| Unit Type             | Risk Profile                                               |
| --------------------- | ---------------------------------------------------------- |
| Fixed-price per event | High risk if event volume is variable                      |
| Fixed-price per month | Lower risk; cost absorbed in period price                  |
| Time & Materials      | Risk shifts to government; appropriate for variable demand |
| Cost-plus             | Government bears volume risk                               |

For FFP CLINs covering variable-demand work, calculate the break-even volume and
flag if historical CV suggests meaningful probability of exceeding it.
