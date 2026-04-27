# Common Extraction Pitfalls

Battle-tested errors from real RFP extractions. Read this before starting any extraction work.

## 1. `clause` vs `requirement`

- **`clause`** = FAR/DFARS/agency citation by ID. `FAR 52.212-4`, `DFARS 252.204-7012`.
- **`requirement`** = contractor obligation language. "The contractor shall provide…"
  A clause _contains_ requirements but is not itself a requirement.

## 2. `evaluation_factor` vs `proposal_instruction`

- Section M → `evaluation_factor` (+ `subfactor`)
- Section L → `proposal_instruction`
  Linked by `GUIDES` (L → M) and `EVALUATED_BY` (M → L).

## 3. Wrong relationship direction

| Wrong             | Correct                                         |
| ----------------- | ----------------------------------------------- |
| `MEASURES`        | `MEASURED_BY` (requirement → standard)          |
| `PART_OF`         | `CHILD_OF`                                      |
| `BELONGS_TO`      | `CHILD_OF` or `ATTACHMENT_OF`                   |
| `HAS_REQUIREMENT` | invert: `requirement CHILD_OF document_section` |

## 4. `document` vs `document_section`

- The whole RFP, an attachment, an amendment → `document`
- Section L, Section C.5.1, Appendix A → `document_section`
  Sections live inside documents via `CHILD_OF`.

## 5. Tagging numbers as `workload_metric`

A bare "12,500" is not an entity. `workload_metric` requires a unit and a denominator: `12,500 sorties/year`, `5,000 tickets/month`. Strip the unit and you've lost the whole point.

## 6. CLINs in narrative vs CLINs in tables

The same CLIN may appear in narrative ("…priced under CLIN 0001…") and in a Section B priced table. Emit one canonical entity, deduplicated by CLIN number. Both occurrences become `source_id` references on the same entity.

## 7. Win themes in the wrong direction

Win themes / discriminators come **from us** (the bidder); customer priorities come **from the customer**. Don't conflate. `strategic_theme` `ADDRESSES` `customer_priority`.

## 8. Past performance "examples" vs references

A reference contract (with number, period, value, customer, role) → `past_performance_reference`. A vague mention ("we have done similar work") → not an entity.

## 9. Inference-only types in extraction

Never emit `REQUIRES`, `ENABLED_BY`, or `RESPONSIBLE_FOR` during extraction. Those are produced by the orphan-resolution post-processing pass and emitting them during extraction skews inference quality.

## 10. Subfactor without parent

Every `subfactor` must `CHILD_OF` an `evaluation_factor`. If you can't find the parent in the chunk, leave the subfactor for post-processing — don't guess.
