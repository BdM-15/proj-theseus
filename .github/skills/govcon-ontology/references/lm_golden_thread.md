# proposal_instruction ↔ evaluation_factor Golden Thread

The single most important pattern in federal proposal evaluation. Every `evaluation_factor` is **scored against** `proposal_instruction` items. Lose the link and the proposal becomes non-compliant on its face.

**Format scope:** This pattern applies to UCF solicitations (Section L↔M) AND to non-UCF equivalents — FAR 16 task orders, Fair Opportunity Proposal Requests (FOPRs), BPA calls, OTAs, commercial item buys, and agency-specific formats. The entity types are format-agnostic; only the section labels change. Examples below use UCF labels for reader recognition — substitute the equivalent section / attachment / inline location for non-UCF.

## The Edges

| Direction          | Edge            | Source                 | Target                                              |
| ------------------ | --------------- | ---------------------- | --------------------------------------------------- |
| L → M              | `GUIDES`        | `proposal_instruction` | `evaluation_factor`                                 |
| M → L              | `EVALUATED_BY`  | `evaluation_factor`    | `proposal_instruction`                              |
| L → C              | `REFERENCES`    | `proposal_instruction` | `requirement`                                       |
| M → evidence       | `EVALUATED_BY`  | `evaluation_factor`    | `past_performance_reference`, `compliance_artifact` |
| Factor → Subfactor | `HAS_SUBFACTOR` | `evaluation_factor`    | `subfactor`                                         |

## Extraction Heuristic

When you see proposal-instruction language like "shall submit", "shall include", "shall describe" (UCF Section L or non-UCF equivalent — inline PWS, named attachment, FOPR instructions section):

- Emit a `proposal_instruction` entity.
- Look for the matching `evaluation_factor` (UCF Section M or equivalent — often shares keywords). If found in the same chunk, emit `GUIDES` edge. If not, leave it for inference.

When you see evaluation-criteria language like "the Government will evaluate" (UCF Section M or non-UCF equivalent):

- Emit an `evaluation_factor` entity.
- The subject of "will evaluate" is usually the `proposal_instruction` by name.

## Inference Pass

The `infer_lm_links.py` algorithm runs after extraction and fills missing `proposal_instruction` ↔ `evaluation_factor` edges using semantic similarity + entity name overlap. Don't force these during extraction — let inference handle the cross-chunk matches.
