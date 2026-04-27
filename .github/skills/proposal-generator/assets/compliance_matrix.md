# Compliance Matrix Template

**Format-agnostic.** Works on UCF (Section L/M/C) and non-UCF (FAR 16 task order, FOPR, BPA call, OTA, commercial item buy, agency-specific format) alike. Column headers name the entity type first; the parenthetical shows the typical UCF mapping for reader recognition.

| #   | Proposal Instruction (Section L / equiv) | Evaluation Factor (Section M / equiv) | Requirement(s) (Section C / SOW / PWS) | Volume / Section | Page Limit | Owner    | Status             | Evidence           |
| --- | ---------------------------------------- | ------------------------------------- | -------------------------------------- | ---------------- | ---------- | -------- | ------------------ | ------------------ |
| 1   | `<instruction_id>: <verbatim text>`      | `<evaluation_id>: <factor name>`      | `<requirement_id list>`                | `<Volume #, §>`  | `<n>`      | `<name>` | OK / GAP / PARTIAL | `<entity_id refs>` |

Each row also carries hidden source enums consumed by downstream renderers:

- `instruction_source`: `UCF-L | non-UCF | PWS-inline | attachment`
- `evaluation_source`: `UCF-M | non-UCF | adjectival | LPTA`

**Rules:**

1. Every row must reference at least one entity from the workspace (`proposal_instruction`, `evaluation_factor`, or `requirement`). No bare narrative rows.
2. `GAP` rows are kept in place — never deleted — and listed in the output `warnings`.
3. Status legend:
   - `OK` — full instruction ↔ evaluation ↔ requirement trace + volume assignment
   - `PARTIAL` — trace exists but page limit or owner missing
   - `GAP` — at least one of instruction / evaluation / requirement cannot be linked to a workspace entity. **Never emit `GAP` merely because the entity lacks a literal "Section L" or "Section M" label.**
4. Sort by `proposal_instruction` order in source document, then `evaluation_factor` weight (heaviest first within a tie).
