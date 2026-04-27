# Shipley Glossary (Canonical Definitions)

These are the working definitions used across `proposal-generator`. Reject phrasing that doesn't conform.

## Discriminator

A capability **only we (or very few competitors) can credibly claim**, that the customer cares about. Must be:

- **Provable** with a proof point (past performance, certification, measurable result)
- **Relevant** to a `customer_priority` or `pain_point` in the workspace
- **Specific** — not "extensive experience" but "37 deployments of the same software stack on AFNET in the last 5 years"

## Win Theme

A short, verb-led, customer-language statement of how our solution wins. Format: `<verb> <customer outcome> by <our discriminator>`.

- Good: "Cut help-desk wait time in half by deploying our pre-trained AI triage model on Day 1"
- Bad: "Innovative AI-Powered Solutions"

## Hot Button

An **explicit** statement by the customer that something matters more than usual. Maps to `customer_priority` entity. Phrases: "paramount", "most critical", "highest priority", "non-negotiable".

## Ghost

Language placed in our proposal that **highlights a competitor's weakness without naming them**. E.g., if the incumbent has CPARS issues with cyber compliance: "We deliver continuous ATO compliance monitoring rather than annual recertification cycles."

## Proof Point

Concrete evidence backing a claim: contract number + outcome metric, certification + date, named personnel + clearance.

- Good: "Contract W912-1234, NAVAIR, $42M, 99.97% uptime over 36 months, CPARS Exceptional"
- Bad: "Extensive experience supporting DoD"

## FAB Chain (Feature → Advantage → Benefit)

- **Feature**: what the solution _is_ — capability, technology, process
- **Advantage**: what the feature _does_ better than alternatives
- **Benefit**: what the advantage _means to the customer_, in customer language

The Benefit must map to a `customer_priority` or `pain_point` entity. If it doesn't, the chain is decorative — discard it.

Example (good):

- F: Pre-trained AI triage model deployed on Day 1
- A: Skips 6-month training period typical for ML deployments
- B: Customer's mission readiness metric improves in Q1 instead of Q3 → maps to `customer_priority: Mission Readiness Priority`

Example (bad):

- F: Cloud-native architecture
- A: Scalable
- B: Better performance
  (Benefit is a feature restated. Reject.)

## Compliance Matrix

Tabular L → M → C → Volume → Page traceability. Every row must trace to real entities. `GAP` is honest; invented links are not.

## Color Reviews (sequence)

Pink → Red → Gold → White. Skill output should be evaluated as if entering the next color review.
