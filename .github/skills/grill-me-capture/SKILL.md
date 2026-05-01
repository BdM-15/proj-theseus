---
name: grill-me-capture
description: "Stress-tests a capture plan by grilling the user on customer intelligence, competitive black-hat analysis, win theme validity, proof points, and teaming strategy - grounded in the active workspace KG. USE WHEN the user says 'grill me on our capture plan', 'stress-test our customer engagement strategy', 'challenge our PWin assumptions', 'we are at capture gate', or wants to push back on any capture-phase decision before the RFP drops. Loads win themes, hot buttons, discriminators, and competitor data from the workspace KG to make every question specific to THIS opportunity. One question at a time; never accepts vague answers. Use grill-me-govcon for automatic mode detection across all areas."
license: MIT
metadata:
  version: 1.0.0
  category: govcon-platform
  status: active
  runtime: legacy
  personas_primary: capture_manager
  personas_secondary: [proposal_manager]
  shipley_phases: [capture, strategy]
  capability: analyze
  auto_emit_artifacts: true
  script_paths:
    - ../renderers/scripts
---
# Grill Me — Capture

Inherits the base `grill-me` philosophy: one question at a time, provide your
recommended answer, relentless until every assumption is tested.

## Step 1: Load workspace context

Before asking anything, query the workspace KG for:
`win_theme`, `hot_button`, `discriminator`, `competitor`, `incumbent`,
`customer`, `program_office`, `requirement`, `teaming_partner`.

Substitute KG-sourced specifics into your questions. If a hot button is
already in the KG, ask "where did this hot button come from?" not "what are
your hot buttons?" — use what you already know to go deeper.

## Step 2: Grill — Capture question tree

Ask each question one at a time. Provide your recommended answer. If the
user's answer contradicts KG-captured data, surface the contradiction.

1. **Hot buttons** — "What are the customer's top 3 hot buttons — the
   problems they lose sleep over? Where exactly did that intelligence come
   from?"

2. **Reading between the lines** — "What does the customer want that isn't
   written in the PWS? What are they afraid to put in writing?"

3. **Win themes** — "List your top 3 win themes. For each: is it truly
   discriminating, or is it a qualifier any competitive bidder can claim?"

4. **Competitive black-hat** — "How would the incumbent approach this bid —
   their likely technical approach, pricing strategy, and key personnel play?"

5. **Ghost language** — "Is there any language in the PWS or eval criteria
   that looks like it was written with a specific solution — or company — in
   mind?"

6. **Proof points** — "For each win theme, what's the specific proof point —
   contract number, metric, customer quote — that makes it credible?"

7. **Teaming gaps** — "What capability gaps does our team have? Who are the
   best partners to fill them, and have any already been locked by a
   competitor?"

8. **Customer engagement plan** — "What's our engagement plan before RFP
   release? Who's meeting with whom, and what intelligence are we collecting?"

9. **PWin drivers** — "What single action in the next 30 days would move PWin
   up the most? What single event would crater it?"

10. **Shaping opportunity** — "Have we influenced the requirements, eval
    criteria, or SOW? If not, is the window still open?"

## Step 3: Synthesize

Summarize confirmed intelligence, assertions without KG backing (flag as
intelligence gaps), open actions, and top 3 risks before RFP release.