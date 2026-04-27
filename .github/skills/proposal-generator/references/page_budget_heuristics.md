# Page Budget Heuristics

Allocate pages proportional to evaluation factor weight, then adjust for risk.

## Default split (within Section M weight)

| Factor weight | Page share of Volume |
| ------------- | -------------------- |
| ≥ 40%         | 35–40% of pages      |
| 25–39%        | 25–30% of pages      |
| 10–24%        | 12–18% of pages      |
| < 10%         | 5–8% of pages        |

## Adjustments

- **+5% pages** if the factor has many `subfactors` (deep hierarchy needs more space).
- **+5% pages** if linked `customer_priority` is rated paramount/critical.
- **−3% pages** if the factor is purely informational (e.g., Past Performance with form-fill template).
- **Floor:** every factor gets ≥ 1 page even at low weights.
