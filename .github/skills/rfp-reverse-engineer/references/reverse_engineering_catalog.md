# Reverse Engineering Catalog — Reading the CO's Hidden Decisions

> **Stance inversion** — Upstream `sow-pws-builder` walks a CO FORWARD through 3 intake answers + 6 scope blocks. This skill walks a bidder BACKWARDS through the resulting document to reconstruct what the CO chose. Same decision tree; opposite direction.

## Section A — Backwards Inference of the 3 Intake Answers

### A.1 SOW vs PWS

| Document Signal                                                                                                     | Inference                                                     |
| ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| Section 3 organized by **task areas** with prescriptive verbs ("the contractor shall perform / deliver / maintain") | **SOW**                                                       |
| Section 3 organized by **performance objectives** with outcome verbs + measurable thresholds + AQLs                 | **PWS**                                                       |
| Section 12 titled "Inspection and Acceptance" citing FAR 52.246-series                                              | **SOW** confirmed                                             |
| Section 12 titled "QASP" citing FAR 37.602 / 46.401                                                                 | **PWS** confirmed                                             |
| Mixed signals (task areas + AQLs)                                                                                   | **Hybrid** — emit `status=ambiguous` and ask in clarification |

### A.2 Contract Type

| Clause / Section Signal                                                   | Inference                                                          |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| Section L pricing schedule asks for **fixed monthly price per CLIN**      | FFP                                                                |
| Section 5 "Labor Category Ceiling Hours" present + FAR 16.601(c)(2) cited | T&M or LH                                                          |
| FAR 52.232-7 cited (Payments under T&M and LH contracts)                  | T&M / LH confirmed                                                 |
| FAR 16.306(d)(1) cited or "completion form" language in Section 1.1       | CPFF completion                                                    |
| FAR 16.306(d)(2) cited or "term form" / "level of effort" language        | CPFF term                                                          |
| Bare `FAR 16.306` cited without (d)(1)/(d)(2)                             | **AMBIGUOUS** — emit `cpff_form_signal.status=ambiguous`, file Q&A |
| FAR 16.305 cited                                                          | CPAF                                                               |
| FAR 16.404 cited                                                          | CPIF                                                               |
| FAR 16.301-3 cited (approved accounting system prereq)                    | Some flavor of CR — confirm via other cites                        |
| Multiple contract types signaled across CLINs                             | Hybrid — list per-CLIN                                             |

### A.3 Commercial vs Non-Commercial

| Signal                                                       | Inference                 |
| ------------------------------------------------------------ | ------------------------- |
| FAR Part 12 cited; FAR 52.212-4 in Section I                 | Commercial                |
| FAR 12.207 cited                                             | Commercial FFP            |
| Full Section I/L clause buildout with FAR Part 15 procedures | Non-commercial            |
| Classified work, weapon systems, government-unique processes | Non-commercial            |
| Both commercial and non-commercial signals                   | Hybrid acquisition — flag |

## Section B — Reverse-Walk of the 6 Scope Blocks

For EACH block, emit a JSON object with `co_choice` (the value visible in the document or inferred), `derivation_signal` (the chunk text or KG entity that fired), `source_chunk_ids` (array), and `status` (`locked` | `implied` | `open`):

- **locked** — visible in the document (verbatim or near-verbatim quote available).
- **implied** — derived via an inference rule firing on visible language.
- **open** — document is silent; emit a `clarification_questions[]` entry.

### Block 1: Mission and Service Model

Walk: Section 1.2 Background, Section 3 task/objective titles, Section 7 Place of Performance.

- `core_service`: extract from background paragraph + recurring noun phrases in Section 3 titles.
- `service_delivery_model`: prime FTE | fully sub-delivered | hybrid — inferred from Key Personnel roles + transition-in language.
- `coverage_model`: business hours | extended | 24/7 | seasonal — inferred from Section 6/7 phrases ("during business hours", "24x7", "follow-the-sun").
- `geographic_scope`: count Section 7 sites; check for "remote" / "virtual" / "telework authorized".

### Block 2: Technical Scope

Walk: Section 3 requirements, Section 8 GFP/GFI, Section 14 constraints.

- `build_vs_buy`: COTS keywords ("commercial off-the-shelf", "SaaS", "configure") vs custom dev keywords ("develop", "design and build").
- `systems_in_scope`: extract every named system; mark new build (Section 3 task) vs existing (Section 8 GFI).
- `integration_complexity`: count distinct system interfaces named in Section 3 + Appendix C.
- `data_migration`: keywords "migrate", "convert", "data transfer from".
- `ai_automation`: keywords "AI", "ML", "NLP", "chatbot", "predictive", "rules-based".

### Block 3: Scale and Volume

Walk: Appendix B (Volume Data), Section 3 throughput requirements.

- `transaction_volume`: extract numbers from Appendix B; if Appendix B absent, mark `open` with high-priority Q&A.
- `user_population`: internal vs external from Section 3 audience phrases.
- `concurrent_users`: extract from performance requirements.
- `growth_projection`: explicit statement vs absence (absence → `open`).

### Block 4: Organizational Scope

Walk: Section 1.2 Background, Section 7 Place of Performance.

- `organizational_units`: count distinct offices/centers/divisions named.
- `phasing`: keywords "pilot", "phased rollout", "all sites at award".
- `stakeholder_complexity`: single program | multi-office | cross-agency.

### Block 5: Contract Structure

Walk: Section 6 Period of Performance, Section 13 Transition.

- `period_of_performance`: extract base + option years.
- `base_year_scope`: full performance | ramp-up | design only — inferred from Section 13.1 transition-in length and Section 6 milestones.
- `clin_structure`: by period | by function | by deliverable — inferred from any pricing schedule visible.
- `transition`: in/out/both — Section 13 subsection presence.

### Block 6: Quality and Oversight

Walk: Section 12 QASP, Section 11 Reporting, Section 10 Key Personnel.

- `aql_thresholds`: extract every AQL stated in Section 12.
- `reporting_cadence`: extract from Section 11.
- `key_personnel`: list every Key Personnel role in Section 10; check substitution clause for the FAR 52.237-2 trap (see `far_citations.md`).

## Section C — Hot Button Decoder

A "hot button" is something the CO emphasized that maps to a discriminator opportunity for our proposal. Detection patterns:

| Document Pattern                                                         | Hot Button Signal                                                   |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Threshold elevated above industry baseline (e.g., 99.99% uptime)         | CO has lived through an outage — emphasize reliability proof points |
| Section 13 Transition has unusually detailed risk language               | CO had a bad transition — emphasize transition methodology          |
| Section 12 has multiple "negative incentive" / payment deduction clauses | CO has had quality issues — emphasize QA discipline                 |
| Key Personnel list is unusually long or specific                         | CO values continuity — emphasize team retention strategy            |
| Section 9 Security has agency-specific tier above baseline               | CO has compliance scrutiny — emphasize security posture             |
| Recurring phrase or theme across 3+ sections                             | CO is signaling a priority — emphasize proportionally               |
| Evaluation criteria weight one factor heavily (>40%)                     | That factor is THE buying decision — make it your win theme spine   |

For each hot button, emit `discriminator_opportunity` field linking to the proposal-side response strategy.

## Section C′ — When the catalog is silent

If a document signal does not match any catalog row, do NOT invent a new inference rule on the fly. Emit `status=open` with a `clarification_questions[]` entry describing the signal and asking the user / capture team to confirm. The catalog is the source of truth; updates to it are a separate skill-creator workflow.
