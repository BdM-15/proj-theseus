# Relationship Query Patterns

Cypher / KG patterns for OT-specific traceability. The Theseus 33-entity ontology is **format-agnostic** — it covers OT solicitations as well as FAR-based RFPs without schema changes.

## 1. Entity types relevant to OT prototype bids

| Entity                  | OT relevance                                                    |
| ----------------------- | --------------------------------------------------------------- |
| `solicitation`          | The OT solicitation / BAA / RFS (root of the bid)               |
| `requirement`           | What the prototype must do (drives milestone scope)             |
| `deliverable`           | Specific artifacts due at milestones                            |
| `evaluation_factor`     | What the AO will evaluate (drives milestone evidence)           |
| `performance_standard`  | Quantitative/qualitative thresholds (drives exit_criterion)     |
| `place_of_performance`  | Where work happens (drives BLS metro selection)                 |
| `period_of_performance` | PoP duration (drives milestone count + duration)                |
| `incumbent`             | Previous performer if this is a recompete or follow-on          |
| `program_office`        | Sponsoring office (drives consortium routing — DIU/AFWERX/etc.) |
| `naics_code`            | Industry classification (informs SOC mapping)                   |
| `psc_code`              | Product/service code                                            |
| `contract_vehicle`      | If consortium-brokered, which (DIU/NSTXL/MTEC/SOSSEC/AFWERX)    |
| `labor_category`        | Named labor categories from the solicitation (rare for OTs)     |

## 2. Canonical kg_entities call (start of every workflow)

```json
{
  "types": [
    "solicitation",
    "requirement",
    "deliverable",
    "evaluation_factor",
    "performance_standard",
    "place_of_performance",
    "period_of_performance",
    "incumbent",
    "program_office",
    "naics_code",
    "psc_code",
    "contract_vehicle",
    "labor_category"
  ],
  "limit": 200
}
```

## 3. Relationship traversals

Each milestone we propose must trace back to the AO's stated artifacts. Use these patterns:

### Requirement → milestone coverage

```cypher
MATCH (r:requirement)
WHERE NOT EXISTS {
  MATCH (m:milestone)-[:ADDRESSES]->(r)
}
RETURN r.id, r.text
```

For each uncovered requirement, the bid is exposing a gap. Either add a milestone that addresses it, or flag in `bid_recommendation.risk_flags`.

### Evaluation factor → evidence chain

```cypher
MATCH (ef:evaluation_factor)
OPTIONAL MATCH (ef)-[:EVIDENCED_BY]->(d:deliverable)
OPTIONAL MATCH (d)<-[:PRODUCES]-(m:milestone)
RETURN ef.id, ef.text, collect(distinct d.id) as deliverables, collect(distinct m.id) as milestones
```

If an evaluation_factor has no upstream milestone, the AO will have nothing to score on — that's a structural bid gap.

### Performance standard → exit criterion

```cypher
MATCH (ps:performance_standard)
OPTIONAL MATCH (ps)-[:VALIDATED_AT]->(m:milestone)
RETURN ps.id, ps.threshold_text, m.id as validating_milestone, m.exit_criterion
```

Each performance_standard should map to one milestone's exit_criterion. Mismatches mean we're proposing to demonstrate something the AO didn't ask for, or omitting something they did.

### Incumbent context (if recompete or follow-on)

```cypher
MATCH (i:incumbent)
OPTIONAL MATCH (i)-[:PERFORMED]->(prior:contract_or_agreement)
RETURN i.name, prior.id, prior.value, prior.period
```

Use to size our bid relative to incumbent's last-award value (with rebaseline for inflation + scope changes).

## 4. KG chunks — when to use vs kg_entities

- **kg_entities**: structured pulls (give me everything tagged `requirement`).
- **kg_chunks**: free-text retrieval (give me passages mentioning "operational environment" or "TRL 6 demonstration"). Use for:
  - Decoding AO's intent language ("must demonstrate" vs "may demonstrate")
  - Identifying TRL signals not formally tagged
  - Pulling consortium template references
  - Surfacing white paper / industry day quotes

Mode `mix` (hybrid retrieval) is the safe default. `local` for very narrow keyword pulls, `global` for broad thematic searches.

## 5. Workspace context that matters most

Always confirm before bidding:

1. `place_of_performance` — drives BLS metro selection. Wrong metro = wrong wages = unbid-able cost stack.
2. `period_of_performance` — drives milestone count + duration. Wrong PoP = wrong labor hours.
3. Authority signals (4021 vs 4022 vs 4022(f)) — usually in solicitation text or chunks, not formally tagged.
4. NDC eligibility signals from the user (NOT the workspace) — our team's NDC status is internal knowledge, not RFP knowledge.

If 1, 2, or 3 are missing from the KG, ask the user in ONE batch question. NDC status (#4) is always a user-provided input.
