# RFP Signal Patterns — Ghost Language, Missing Sections, Contract-Type Detection

## Section D — Ghost Language Catalog

"Ghost language" is vague or unmeasurable language that gives the CO unilateral discretion and gives the bidder unpriceable risk. Detect every match below and emit a `ghost_language[]` entry with `phrase`, `section_origin`, `risk`, `source_chunk_ids`, `recommended_action`.

### D.1 Unbounded Discretion Phrases

| Phrase                                                | Risk                                             | Recommended Action                                                       |
| ----------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------ |
| "as appropriate"                                      | CO retains unilateral discretion to expand scope | File Q&A: "Please define the trigger or threshold for 'as appropriate'." |
| "as required" (without trigger)                       | Same                                             | Same                                                                     |
| "as needed"                                           | Same                                             | Same                                                                     |
| "where applicable"                                    | Bidder cannot scope or price                     | File Q&A asking for the applicability test                               |
| "when directed"                                       | Open-ended task — surge / out-of-scope risk      | File Q&A asking for frequency cap or ceiling-hour mechanism              |
| "in accordance with applicable regulations" (no list) | Bidder cannot enumerate applicable regs          | File Q&A requesting the regulatory list                                  |

### D.2 Unmeasurable Standards

| Phrase                                     | Risk                  | Recommended Action                                               |
| ------------------------------------------ | --------------------- | ---------------------------------------------------------------- |
| "best practices" without citing a standard | Untestable            | File Q&A asking which standard (NIST / ISO / ITIL / CMMI / etc.) |
| "industry standard" without citing one     | Untestable            | Same                                                             |
| "high quality" without metric              | Subjective acceptance | File Q&A asking for the AQL or measurement method                |
| "timely" without timeframe                 | Subjective acceptance | File Q&A asking for the time threshold                           |
| "appropriate" without criteria             | Subjective acceptance | File Q&A asking for the criteria                                 |

### D.3 Undefined Acronyms / Terms

| Pattern                                                                                                             | Risk                          | Action                                         |
| ------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ---------------------------------------------- |
| Acronym used without expansion in Section 2                                                                         | Bidder may misinterpret scope | File Q&A asking for definition                 |
| Term-of-art used without definition (e.g., "operational readiness", "mission essential", "critical infrastructure") | Subjective interpretation     | File Q&A asking for the operational definition |

### D.4 Evaluation-Criteria Ghost Language

| Phrase                                         | Risk                        | Action                                                                |
| ---------------------------------------------- | --------------------------- | --------------------------------------------------------------------- |
| Evaluation factor with no measurable threshold | Subjective scoring          | File Q&A asking for the rating scale or evaluation rubric             |
| "Will be evaluated" without method             | Bidder cannot tune response | File Q&A asking method (inspection / demonstration / analysis / test) |

## Missing-Section Signal Table

A document silent on a structurally-implied section is itself a signal. For each, emit `missing_sections[]` with `section_name`, `inference_rule`, `risk`, `recommended_action`.

| Missing Section                                       | Inference Rule                                                    | Implication                                                                |
| ----------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Section 13 Transition on a recompete                  | Recompetes ALWAYS need transition language                        | Likely amendment forthcoming; flag for capture team to monitor             |
| Section 14 Constraints & Assumptions                  | CO didn't document derived defaults                               | Proposal should over-document own assumptions to avoid post-award disputes |
| Section 9 Security in a classified domain             | Domain is classified-adjacent but no Section 9 details            | DD Form 254 likely separate; flag the gap and prepare to ask               |
| QASP / Inspection (Section 12) entirely               | Document is scope-only, no quality framework                      | Either CPFF without performance accountability OR amendment forthcoming    |
| Period of Performance (Section 6)                     | Unusual omission                                                  | File Q&A immediately — can't price without PoP                             |
| Place of Performance (Section 7)                      | Could indicate remote-allowed OR unintentional gap                | File Q&A asking remote-work authorization                                  |
| Appendix B Volume Data                                | Workload / volume requirements present but no historical baseline | File Q&A requesting historical volumes or surge/trough data                |
| Government-Furnished Property/Information (Section 8) | Section 3 references "existing systems" but Section 8 is empty    | File Q&A enumerating which systems are GFI                                 |

## Contract-Type Detection Cues (extends Section A.2)

Beyond clause cites, look for:

| Cue                                                                                                                | Signal                         |
| ------------------------------------------------------------------------------------------------------------------ | ------------------------------ |
| Section L Volume IV (Cost) asks for **fully burdened labor rates by LCAT**                                         | T&M / LH likely                |
| Section L Volume IV asks for **fixed monthly price per CLIN**                                                      | FFP                            |
| Section L Volume IV asks for **estimated cost + proposed fee**                                                     | CR (CPFF / CPAF / CPIF)        |
| Section L asks for **DCAA-approved accounting system documentation**                                               | CR confirmed                   |
| Section M weights **technical** as "significantly more important than cost" with cost evaluated for "realism only" | Likely CR or LPTA-disqualified |

## Security-Tier Escalation Cues

Detect quietly elevated security requirements:

| Cue                                                   | Implication                                     |
| ----------------------------------------------------- | ----------------------------------------------- |
| FedRAMP IL5 requirement appearing in only one section | Whole-of-cloud impact — flag for IT cost model  |
| Polygraph or SCI clearance in Section 9 or Section 10 | Cleared facility + DD 254 + ICD 705 SCIF needed |
| CMMC Level 2 or higher                                | Sub-tier flowdown obligations apply             |
| ITAR / EAR mention                                    | Export-control program required at prime        |
| HIPAA / HITECH / SOC 2 implied by data type           | BAA required pre-award; flag                    |

## Trap Detector Cues (covered in `far_citations.md`)

These cues belong here for completeness; full mitigation is in `far_citations.md` Section E:

- FAR 52.237-2 cited as Key Personnel substitution clause → **WRONG CLAUSE TRAP**.
- Bare `FAR 16.306` cited for CPFF → **AMBIGUOUS FORM TRAP**.
- QASP Payment Consequence column with CPARS rating language → **QASP↔CPARS CONFLATION TRAP**.
- T&M / LH without Section 5 ceiling-hours table → **FAR 16.601(c)(2) OMISSION TRAP**.
