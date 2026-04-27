# Section L↔M Visualization Patterns

Three canonical visual layouts for showing the Section L↔M golden thread. Pick the one that matches the artifact format.

## Pattern A — Table (preferred for compliance matrices)

Single table, monospaced clause IDs, status column. See `templates/compliance_matrix.html`.

```
| L Instruction | M Factor          | C Requirement(s)        | Volume | Pages | Status |
| L.3.4         | Factor 2 Tech     | C.5.1.2, C.5.1.3        | I      | 25    | OK     |
| L.4.1         | Factor 3 Past Perf| (no C link — info req.) | III    | 10    | OK     |
| L.5.2         | (none)            | C.6.4                   | I      | -     | GAP    |
```

## Pattern B — Sankey (executive briefing slide)

Three-column sankey: L (left) → M (center) → C (right). Band thickness = number of links. Use sparingly — Sankeys read poorly when printed B&W.

## Pattern C — Bipartite Graph (KG Explorer mode)

Two-row layout: L instructions top, M factors bottom, lines drawn for `GUIDES` / `EVALUATED_BY` edges. Best for live discussion with the capture team, not for inclusion in the proposal.

## Choosing

- **Proposal volume** → Pattern A only
- **Executive briefing** → A primary, B as a single high-impact slide
- **Internal capture review** → C
