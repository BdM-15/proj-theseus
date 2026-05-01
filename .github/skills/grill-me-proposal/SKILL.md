---
name: grill-me-proposal
description: "Stress-tests a proposal strategy by grilling the user on win theme and eval factor traceability, discriminator credibility, hot button coverage, FAB chains, proof points, and pink team vulnerabilities - grounded in the active workspace KG. USE WHEN the user says 'grill me on our win themes', 'challenge our proposal approach', 'stress-test our discriminators', 'push back on our executive summary', or wants to pressure-test any proposal decision before a color review or submission. Loads evaluation_factor, win_theme, hot_button, discriminator, and requirement entities from the workspace KG to make every question specific to THIS RFP. One question at a time; never accepts vague answers. Use grill-me-govcon for automatic mode detection across all areas."
license: MIT
metadata:
  version: 1.0.0
  category: govcon-platform
  status: active
  runtime: legacy
  personas_primary: proposal_manager
  personas_secondary: [proposal_writer, capture_manager]
  shipley_phases: [strategy, proposal_development]
  capability: analyze
  auto_emit_artifacts: true
  script_paths:
    - ../renderers/scripts
---
# Grill Me — Proposal

Inherits the base `grill-me` philosophy: one question at a time, provide your
recommended answer, relentless until every assumption is tested.

## Step 1: Load workspace context

Before asking anything, query the workspace KG for:
`evaluation_factor`, `proposal_instruction`, `win_theme`, `hot_button`,
`discriminator`, `requirement`, `deliverable`, `compliance_artifact`.

Use KG data to make questions specific: if evaluation factors are already
extracted, name them when asking about traceability. If win themes are in the
KG, probe their evidence rather than asking what the themes are.

## Step 2: Grill — Proposal question tree

Ask each question one at a time. Provide your recommended answer. Surface any
gap between what the KG shows and what the user claims.

1. **Compliance foundation** — "Do we have a fully annotated compliance
   matrix? Is every 'shall' from Section L mapped to a proposal section with
   an owner?"

2. **Win theme / eval factor traceability** — "For each win theme, which
   specific evaluation factor does it address? If a theme doesn't map to a
   scored factor, why are we leading with it?"

3. **Discriminators vs. qualifiers** — "Pick your strongest discriminator.
   Can any of the top three competitors truthfully claim the same thing?"

4. **Hot button coverage** — "Walk through the top 3 hot buttons. Is each
   addressed in the executive summary, and reinforced in the relevant body
   sections?"

5. **FAB chains** — "Take your most important capability claim. Can you
   complete: 'Our [Feature] means [Advantage], which means you [Benefit]'?"

6. **Proof points per discriminator** — "State the proof point for your top
   discriminator. Is it specific — contract number, metric, date — or
   generic?"

7. **Ghost language exploitation** — "Which exact phrases from the RFP are
   we playing back verbatim? Does the executive summary mirror the customer's
   own language?"

8. **Executive summary test** — "Read the first paragraph of your executive
   summary aloud. Does it open with the customer's problem — or with your
   company name?"

9. **Pink team vulnerabilities** — "If a Pink Team reviewed this today,
   what's the first weakness they'd flag? What evaluator concern are we least
   prepared to address?"

10. **Page and volume allocation** — "Are the highest-weighted evaluation
    factors getting the most page depth? Where are we over-writing or
    under-writing?"

## Step 3: Synthesize

Summarize compliant areas, traceability gaps, discriminators that need
evidence upgrades, and top 3 risks before the color review.