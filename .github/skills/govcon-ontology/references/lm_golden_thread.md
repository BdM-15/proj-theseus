# Section L↔M Golden Thread

The single most important pattern in federal proposal evaluation. Every `evaluation_factor` (Section M) is **scored against** `proposal_instruction` items (Section L). Lose the link and the proposal becomes non-compliant on its face.

## The Edges

| Direction          | Edge            | Source                 | Target                                              |
| ------------------ | --------------- | ---------------------- | --------------------------------------------------- |
| L → M              | `GUIDES`        | `proposal_instruction` | `evaluation_factor`                                 |
| M → L              | `EVALUATED_BY`  | `evaluation_factor`    | `proposal_instruction`                              |
| L → C              | `REFERENCES`    | `proposal_instruction` | `requirement`                                       |
| M → evidence       | `EVALUATED_BY`  | `evaluation_factor`    | `past_performance_reference`, `compliance_artifact` |
| Factor → Subfactor | `HAS_SUBFACTOR` | `evaluation_factor`    | `subfactor`                                         |

## Extraction Heuristic

When you see Section L language like "shall submit", "shall include", "shall describe":

- Emit a `proposal_instruction` entity.
- Look for the matching Section M factor (often shares keywords). If found in the same chunk, emit `GUIDES` edge. If not, leave it for inference.

When you see Section M language like "the Government will evaluate":

- Emit an `evaluation_factor` entity.
- The subject of "will evaluate" is usually the Section L instruction by name.

## Inference Pass

The `infer_lm_links.py` algorithm runs after extraction and fills missing L↔M edges using semantic similarity + entity name overlap. Don't force these during extraction — let inference handle the cross-chunk matches.
