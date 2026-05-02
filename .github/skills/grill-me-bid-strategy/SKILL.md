---
name: grill-me-bid-strategy
description: "Stress-tests a bid/no-bid decision and gate readiness by grilling the user on every assumption - PWin basis, incumbent vulnerabilities, customer relationships, discriminators, and B and P commitment - using the active workspace KG as ground truth. USE WHEN the user says 'should we bid on this?', 'grill me on our bid strategy', 'help me prep for gate review', 'stress-test our bid/no-bid', or wants to pressure-test any bid decision before committing resources. Loads workspace KG to ask pointed questions specific to THIS opportunity. One question at a time; never accepts vague answers. Use grill-me-govcon for automatic mode detection across all areas."
license: MIT
metadata:
  version: 1.0.0
  category: govcon-platform
  status: active
  runtime: legacy
  personas_primary: capture_manager
  personas_secondary: []
  shipley_phases: [pursuit, capture]
  capability: analyze
  auto_emit_artifacts: true
  script_paths:
    - ../renderers/scripts
---
# Grill Me — Bid Strategy

Inherits the base `grill-me` philosophy: one question at a time, provide your
recommended answer, relentless until every assumption is tested.

## Step 1: Load workspace context

Before asking anything, query the workspace KG for:
`win_theme`, `hot_button`, `discriminator`, `competitor`, `incumbent`,
`customer`, `program_office`, `evaluation_factor`, `budget`.

Substitute KG-sourced specifics (incumbent name, hot buttons, budget figures)
directly into your questions. If the workspace is empty, work from
conversation context and note what intelligence is missing.

## Step 2: Grill — Bid Strategy question tree

Ask each question one at a time. Provide your recommended answer. If the
user's answer conflicts with KG data, challenge it before moving on.

1. **Opportunity fit** — "Is this squarely in our sweet spot, or are we
   stretching to reach minimum competitive posture?"

2. **PWin estimate** — "What's our current PWin estimate, and what are the
   top 3 assumptions it rests on?"

3. **Incumbent assessment** — "Who's the incumbent? How well are they
   performing? What's their biggest vulnerability on this recompete?"

4. **Customer relationship** — "What's our actual relationship with the CO,
   the PM, and the TPOC? Who has met them in person and when?"

5. **Must-win or nice-to-win?** — "Is this a must-win for strategic or
   financial reasons — or are we bidding because it appeared on a pipeline?"

6. **Teaming** — "Do we have the full solution, or do we need partners? Who
   are the top two candidates, and why haven't we locked them up yet?"

7. **Discriminators** — "What's our single biggest discriminator — the thing
   only we can truthfully claim for THIS opportunity?"

8. **B&P investment** — "How much B&P are we committing, and is it
   proportional to the TCV and our PWin estimate?"

9. **Risk factors** — "What's the single risk that could make us regret
   bidding this, and what would have to be true for it to materialize?"

10. **Decision** — "If you had to commit the B&P budget right now — bid or
    no-bid? What single piece of information would flip that answer?"

## Step 3: Synthesize

Summarize confirmed assumptions, assumptions without KG support (flag as
risks), open intelligence gaps, and top 3 risks before the next gate.