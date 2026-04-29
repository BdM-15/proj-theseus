# TRL & Milestone Patterns

How to derive a milestone structure from prototype scope. Anchored in DoD TRL definitions (DoDI 5000.02 enclosure 4) and OT-specific phasing convention.

## 1. TRL Reference Table (DoD)

| TRL | Definition                                                                      | Typical evidence                                     |
| --- | ------------------------------------------------------------------------------- | ---------------------------------------------------- |
| 1   | Basic principles observed and reported                                          | Published research                                   |
| 2   | Technology concept and/or application formulated                                | Concept paper, simulations                           |
| 3   | Analytical and experimental critical function and/or proof-of-concept           | Lab proof of concept, key parameters validated       |
| 4   | Component and/or breadboard validation in laboratory                            | Bench-top breadboard, isolated component test        |
| 5   | Component and/or breadboard validation in **relevant** environment              | Subsystem in environmental conditioning chamber, HIL |
| 6   | System / subsystem model or prototype demonstration in **relevant** environment | End-to-end prototype, mission-relevant scenario      |
| 7   | System prototype demonstration in **operational** environment                   | Field demo, real platform integration                |
| 8   | Actual system completed and **qualified** through test and demonstration        | Production-rep article, qualification test complete  |
| 9   | Actual system **proven** through successful mission operations                  | Deployed, in operational use                         |

**Most prototype OTs target TRL 4 → 6 or TRL 5 → 7.** Higher TRL exits typically require platform integration partnerships and longer PoP.

## 2. Phase-Boundary Heuristics

| Transition | Typical milestone gate                              | Risk concentration                              |
| ---------- | --------------------------------------------------- | ----------------------------------------------- |
| TRL 3 → 4  | Preliminary Design Review (PDR)                     | Are we solving the right problem?               |
| TRL 4 → 5  | Build complete + isolated component test            | Does the build work in benign conditions?       |
| TRL 5 → 6  | System integration + relevant-environment demo      | Does the system work integrated, in conditions? |
| TRL 6 → 7  | Operational-environment demo + production readiness | Is it field-deployable?                         |
| TRL 7 → 8  | Qualification test                                  | Production representativeness                   |

## 3. Milestone Count by TRL Range

| TRL range                      | Typical milestone count | Typical PoP  |
| ------------------------------ | ----------------------- | ------------ |
| 3 → 4                          | 1-2                     | 6-12 months  |
| 4 → 5                          | 2-3                     | 12-18 months |
| 5 → 6                          | 2-3                     | 12-24 months |
| 6 → 7                          | 1-2                     | 9-18 months  |
| 4 → 6 (full prototype span)    | 4-6                     | 18-30 months |
| 5 → 7 (operationally relevant) | 4-6                     | 24-36 months |

## 4. Prototype-Type Patterns

### Software prototype

- Front-load milestones with sprints (4-8 week phases)
- TRL 4 = working software in dev environment; TRL 5 = software in representative compute / network environment; TRL 6 = software integrated with surrounding system in mission scenario
- Materials light (10-20% of total cost), labor heavy (70-85%)
- Travel light unless integration site visits

### Hardware prototype (single article)

- Long-lead procurement drives milestone phasing — first milestone often is BOM lock + procurement initiation
- TRL 4 = breadboard component; TRL 5 = brassboard sub-system; TRL 6 = end-to-end prototype
- Materials heavy (40-60%), labor moderate (35-55%)
- Travel concentrated at integration + test events

### Hybrid (hardware + software)

- Parallel software / hardware tracks merging at integration milestone
- Materials moderate (20-40%), labor heavy (55-70%)
- Most common OT prototype shape

### Process / manufacturing prototype

- Pilot-line scale before full production-rate
- Materials moderate-heavy (30-50%), labor + facilities split

## 5. Exit-Criterion Patterns

Every milestone needs a **binary, testable, government-acceptable** exit criterion. Bad criteria:

- "Demonstrate progress" (not binary)
- "Meet government expectations" (not testable)
- "Complete the design" (not measurable)

Good criteria:

- "Government test team accepts the design package per Critical Design Review checklist 5.2"
- "Prototype demonstrates ≥40 dB SNR at 30 km range against the threat profile defined in Annex C"
- "End-to-end software stack processes 1000 frames/sec with <5% loss across 24 hours of continuous operation in the AFRL EW chamber"
- "Field demonstration shows mission-task completion in 3 of 3 trials per the test plan"

## 6. Payment Type per Milestone

OT milestone payments are **fixed-amount** by default (one number, paid on government acceptance of exit criterion). Cost-type payments require explicit AO concurrence and a not-to-exceed ceiling.

| Milestone characteristic                             | Payment type               | Why                                               |
| ---------------------------------------------------- | -------------------------- | ------------------------------------------------- |
| Well-scoped design or test event                     | Fixed                      | Default; minimizes performer risk premium         |
| Open-ended research with uncertain outcome           | Cost-type                  | Performer can't bid a fixed price on unknown work |
| First-of-a-kind integration with no prior cost basis | Cost-type with NTE ceiling | Bound the government exposure                     |
| Final demonstration / acceptance event               | Fixed                      | Outcome-driven                                    |

If using cost-type milestones, apply 15% margin on top of should-cost as the NTE ceiling (industry convention; AO discretion).

## 7. Off-Ramp / Down-Select Conditions

OTs commonly include "off-ramp" milestones — government can stop the agreement at this gate without being in breach. Pattern:

- After PDR (TRL 3→4 transition): off-ramp if design doesn't validate
- After component test (TRL 4→5): off-ramp if breadboard fails key parameter
- Before production transition (TRL 6→7): off-ramp if AO determines no production need

Off-ramp milestones reduce performer leverage but reduce government risk premium — net effect is roughly neutral on bid price.

## 8. Decision-to-Milestone Derivation Rules

Pull from the workspace KG:

1. Each `requirement` entity → at least one milestone must address it (cite in `traces_to_kg`)
2. Each `evaluation_factor` entity → at least one milestone must produce evidence relevant to it
3. Each `deliverable` entity → assigned to a specific milestone (not "throughout PoP")
4. Each `performance_standard` entity → maps to a specific exit_criterion

If any requirement / evaluation_factor / deliverable doesn't trace to a milestone, that's a gap — flag in the bid_recommendation.risk_flags.
