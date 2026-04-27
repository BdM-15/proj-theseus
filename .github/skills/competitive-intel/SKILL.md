---
name: competitive-intel
description: PLACEHOLDER (roadmap) — incumbent and competitor intelligence for federal capture. Will gather public award history, recompete signals, incumbent strengths/weaknesses, and pricing comps from external sources (SAM.gov, USAspending, FPDS, GSA eLibrary) and overlay them on the active workspace. USE WHEN the user asks "who's the incumbent?", "what are competitors likely to bid?", "what was the last contract value?", or "give me a black-hat read on Bidder X". Currently emits a structured stub with TODO markers — full implementation tracked in the project roadmap. DO NOT USE FOR proposal drafting (use proposal-generator) or compliance audits (use compliance-auditor).
license: MIT
metadata:
  category: intel
  version: 0.0.2
  status: roadmap-placeholder
  runtime: legacy
---

# Competitive Intel — Roadmap Placeholder

> **Status:** This skill ships as a structural placeholder so the platform UI, registration, and dispatch paths can be exercised. It returns a typed stub. Full implementation is tracked in the project Roadmap.

## When to Use (future)

- "Who's the incumbent on this contract?"
- "Pull award history for similar work in the last 5 years"
- "Black-hat: what would Lockheed bid here?"
- "What's the typical price range for this NAICS at this magnitude?"

## Planned Inputs

- Active workspace `program`, `organization`, `contract_line_item`, `regulatory_reference` entities
- Optional user inputs: NAICS code, PSC code, set-aside type, place of performance
- External-source API keys (SAM.gov, USAspending) — read from environment, never injected by the runtime

## Planned Workflow (not yet implemented)

1. Resolve target opportunity (program / agency / NAICS / PSC).
2. Query SAM.gov contract opportunities for prior awards on the same vehicle / requirement.
3. Query USAspending / FPDS for award value, period of performance, vendor.
4. Identify incumbent and top 3 likely competitors from award history.
5. For each competitor, summarize strengths/weaknesses from public CPARS, news, and prior protest decisions.
6. Produce a black-hat one-pager per competitor with predicted themes and ghost language opportunities.
7. Hand off to `proposal-generator` to weave into win themes.

## Current Output (stub)

```json
{
  "status": "roadmap_placeholder",
  "incumbent": null,
  "competitors": [],
  "award_history": [],
  "warnings": [
    "competitive-intel is a roadmap placeholder. Full implementation pending."
  ],
  "next_steps": [
    "Implement SAM.gov client",
    "Implement USAspending client",
    "Add black-hat template",
    "Wire into proposal-generator hand-off"
  ]
}
```

## References

- [`references/data_sources.md`](./references/data_sources.md) — Planned external sources and rate-limit notes
- [`references/black_hat_template.md`](./references/black_hat_template.md) — Output template (skeleton)
