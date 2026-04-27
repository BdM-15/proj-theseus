# Relationship Directionality

Source → Target conventions for every relationship type. **Always emit the canonical direction**; coercion exists for safety but pollutes the graph.

## Structural

| Edge            | Source → Target       | Mnemonic                                      |
| --------------- | --------------------- | --------------------------------------------- |
| `CHILD_OF`      | child → parent        | "subfactor CHILD_OF factor"                   |
| `ATTACHMENT_OF` | attachment → base     | "Attachment J-3 ATTACHMENT_OF main RFP"       |
| `CONTAINS`      | container → contained | "section CONTAINS requirement"                |
| `AMENDS`        | amendment → base      | "Amendment 0003 AMENDS RFP"                   |
| `SUPERSEDED_BY` | old → new             | "Amendment 0001 SUPERSEDED_BY Amendment 0003" |
| `REFERENCES`    | citing → cited        | "L.3.4 REFERENCES Past Performance Volume"    |

## Evaluation & Proposal

| Edge            | Source → Target                                                  |
| --------------- | ---------------------------------------------------------------- |
| `GUIDES`        | proposal_instruction → evaluation_factor                         |
| `EVALUATED_BY`  | evaluation_factor → proposal_instruction (or evidence)           |
| `HAS_SUBFACTOR` | evaluation_factor → subfactor                                    |
| `MEASURED_BY`   | requirement → performance_standard                               |
| `EVIDENCES`     | proposal_instruction → evaluation_factor (provides evidence for) |

## Work & Deliverables

| Edge           | Source → Target                      |
| -------------- | ------------------------------------ |
| `PRODUCES`     | work_scope_item → deliverable        |
| `SATISFIED_BY` | requirement → deliverable            |
| `TRACKED_BY`   | deliverable → performance_standard   |
| `SUBMITTED_TO` | deliverable → organization           |
| `STAFFED_BY`   | work_scope_item → labor_category     |
| `PRICED_UNDER` | work_scope_item → contract_line_item |
| `FUNDS`        | contract_line_item → work_scope_item |
| `QUANTIFIES`   | workload_metric → work_scope_item    |

## Authority & Governance

| Edge             | Source → Target                        |
| ---------------- | -------------------------------------- |
| `GOVERNED_BY`    | requirement → clause                   |
| `MANDATES`       | regulatory_reference → requirement     |
| `CONSTRAINED_BY` | work_scope_item → regulatory_reference |
| `DEFINES`        | clause → concept (or requirement)      |
| `APPLIES_TO`     | clause → entity (broad)                |

## Resource & Operational

| Edge               | Source → Target                          |
| ------------------ | ---------------------------------------- |
| `HAS_EQUIPMENT`    | organization → equipment                 |
| `PROVIDED_BY`      | government_furnished_item → organization |
| `COORDINATED_WITH` | work_scope_item → organization           |
| `REPORTED_TO`      | deliverable → person (or organization)   |

## Strategic

| Edge         | Source → Target                                     |
| ------------ | --------------------------------------------------- |
| `ADDRESSES`  | strategic_theme → customer_priority (or pain_point) |
| `RESOLVES`   | strategic_theme → pain_point                        |
| `SUPPORTS`   | strategic_theme → evaluation_factor                 |
| `RELATED_TO` | any → any (last-resort fallback)                    |

## Inference-Only (do not emit during extraction)

- `REQUIRES` — orphan resolution
- `ENABLED_BY` — orphan resolution
- `RESPONSIBLE_FOR` — orphan resolution
