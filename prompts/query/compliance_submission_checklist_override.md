# Submission Instructions — Exhaustive Compliance Checklist

Return an **EXHAUSTIVE, source-grounded** checklist of **ALL proposal submission instructions** present in the retrieved context.

## Formatting Requirements (critical)

- **Markdown only** (use headings + bullets). No walls of text.
- Use **`##` headings** and **checklist bullets** (`- [ ] ...`). Prefer nested bullets for details.
- Each instruction must be an **atomic checklist item** (one compliance requirement per bullet).
- Keep bullets **short** (ideally one sentence). If needed, add 1 nested bullet for clarifiers.
- **Do not repeat the same rule** in multiple sections; deduplicate.
- If you quote, quote only the **minimal phrase** needed for compliance (not long paragraphs).

## Scope Filter (critical)

- Include **ONLY** instructions about **proposal submission / proposal preparation / proposal formatting / proposal delivery** (e.g., copies, volumes, page limits, file formats, fonts/margins, labeling, due dates, delivery address, late proposal rules, required forms/attachments to submit).
- **EXCLUDE** contract performance requirements / SOW tasking (e.g., fuel delivery operations, crane operations, maintenance procedures, staffing execution) unless the text explicitly states it is a **proposal submission requirement**.

## Output Structure (use these headings exactly)

## General Submission Instructions

## Volume-Specific Instructions
- Only include volumes explicitly stated in retrieved context.
- For each volume, list page limits and any special submission/format rules as bullets.

## Deliverables / Copies / Media

## Formatting & Packaging

## Due Date/Time & Delivery

## Not Found in Retrieved Context
- List only critical “expected” compliance items that were not located (avoid repeating per volume).

## Grounding / Non-Hallucination Rules (critical)

- Use **source-only language**; **do NOT invent** requirements.
- For any of these items, you must either **quote the exact value** from retrieved context OR put it under **Not Found in Retrieved Context**:
  - Due date
  - Due time / time zone
  - Physical delivery address / submission location
  - Copy counts (originals, CDs, hardcopies)
  - Page limits
- If an item is unknown, put it under **Not Found in Retrieved Context** (do NOT guess).

## References (must comply with LightRAG format)

- The response must end with a **`### References`** section formatted exactly as:
  - `### References`
  - `- [1] Document Title`
  - `- [2] Document Title`
- Provide **up to 5** citations, and each must support content in the answer.

## Output Skeleton (follow exactly)

## General Submission Instructions
- [ ] ...

## Volume-Specific Instructions
- **Volume I**:
  - [ ] ...
- **Volume II**:
  - [ ] ...

## Deliverables / Copies / Media
- [ ] ...

## Formatting & Packaging
- [ ] ...

## Due Date/Time & Delivery
- [ ] ...

## Not Found in Retrieved Context
- [ ] ...


