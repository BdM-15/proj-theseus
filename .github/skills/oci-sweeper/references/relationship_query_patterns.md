# Relationship Query Patterns — OCI Sweep

Cypher / KG query templates the skill uses against the active Theseus workspace to surface candidate OCI parties and the relationships among them. The KG schema follows `src/ontology/schema.py` (33 entity types, 43 relationship types).

> All queries assume the runtime's `kg_query` tool runs against the active workspace's Neo4j storage (or NetworkX equivalent). Bind names via `$names` parameter — never inline string-concatenate.

---

## Query 1 — Party slice (use `kg_entities`, not Cypher)

```python
kg_entities(
    types=[
        "company",
        "incumbent",
        "subcontractor",
        "customer",
        "program_office",
        "contract_vehicle",
        "prior_contract",
    ],
    limit=200,
)
```

Returns the candidate parties whose names you'll bind to `$names` for the relationship queries below.

---

## Query 2 — Direct edges among candidate parties

```cypher
MATCH (a)-[r]->(b)
WHERE a.name IN $names AND b.name IN $names
RETURN a.name AS source,
       labels(a) AS source_type,
       type(r) AS relationship,
       coalesce(r.description, '') AS description,
       b.name AS target,
       labels(b) AS target_type
LIMIT 200
```

**Why it matters.** Direct edges expose the partner / incumbent / customer overlaps that drive every OCI class. Look for relationship types like `TEAMS_WITH`, `SUBCONTRACTS_TO`, `INCUMBENT_OF`, `CUSTOMER_OF`, `PERFORMED_ON`, `WROTE`.

---

## Query 3 — Bidder ↔ predecessor-contract bridges

```cypher
MATCH (party)-[r1]->(pc:prior_contract)<-[r2]-(other)
WHERE party.name IN $bidder_names AND other.name IN $customer_names
RETURN party.name AS bidder,
       type(r1) AS bidder_role,
       pc.name AS prior_contract,
       type(r2) AS customer_role,
       other.name AS customer
LIMIT 100
```

**Why it matters.** A path `bidder → PERFORMED_ON → prior_contract ← AWARDED_BY ← customer` is the canonical _unequal-access_ signal (FAR 9.505-4) AND the canonical _biased-ground-rules_ signal (FAR 9.505-2) when the prior contract authored the SOW.

---

## Query 4 — SETA / IV&V / oversight surface

```cypher
MATCH (party)-[r]->(work)
WHERE party.name IN $names
  AND (
    type(r) IN ['EVALUATES', 'OVERSEES', 'PROVIDES_SETA_FOR', 'PERFORMS_QA_ON']
    OR work.name =~ '(?i).*(SETA|IV&V|independent.*assessment|quality assurance|oversight).*'
  )
RETURN party.name AS party,
       type(r) AS relationship,
       work.name AS scope
LIMIT 100
```

**Why it matters.** Any hit here is a candidate `impaired_objectivity` finding (FAR 9.505-3). The bidder is being asked to evaluate / oversee work they're also performing or that a teammate is performing.

---

## Query 5 — Sources-sought / market-research authorship

```cypher
MATCH (party)-[r]->(artifact)
WHERE party.name IN $names
  AND (
    type(r) IN ['AUTHORED', 'DRAFTED', 'CONTRIBUTED_TO']
    AND artifact.name =~ '(?i).*(SOW|PWS|sources sought|market research|RFI response|requirement).*'
  )
RETURN party.name AS party,
       type(r) AS relationship,
       artifact.name AS artifact
LIMIT 100
```

**Why it matters.** Any hit is a candidate `biased_ground_rules` finding (FAR 9.505-1, 9.505-2). The bidder helped scope the buy.

---

## Chunk-level fallback (use `kg_chunks`)

When entity / relationship coverage is thin (early-pipeline workspaces), fall back to text retrieval:

```python
# Unequal access signals
kg_chunks(
    query="non-public information OR proprietary data OR predecessor contract OR sensitive information OR source-selection-sensitive",
    top_k=10,
    mode="hybrid",
)

# Biased ground rules signals
kg_chunks(
    query="wrote the SOW OR drafted the requirement OR helped scope OR market research OR sources sought response OR RFI",
    top_k=10,
    mode="hybrid",
)

# Impaired objectivity signals
kg_chunks(
    query="evaluate OR oversight OR Quality Assurance OR independent assessment OR SETA OR IV&V",
    top_k=10,
    mode="hybrid",
)
```

Any chunk hit MUST surface in the finding's `evidence` field as a verbatim quote, with the `chunk_id` populated. No claim without a source.

---

## Defensive notes

- **Empty result is a real result.** If Query 2 returns nothing, that's a meaningful "no party-overlap conflicts visible from the KG" signal — not a failure. Note it in `open_items`.
- **Synthetic / placeholder entities.** If the KG contains placeholder names like `"TBD"` or `"unnamed contractor"`, exclude them from `$names` before binding.
- **Case sensitivity.** Neo4j string equality is case-sensitive. The skill should normalize to lowercase via `toLower(...)` when comparing names if false negatives appear.
- **Storage backend agnosticism.** These patterns work against `Neo4JStorage`. The `NetworkXStorage` path uses the same logical query through `kg_query`'s adapter — don't write storage-specific code in the skill body.
