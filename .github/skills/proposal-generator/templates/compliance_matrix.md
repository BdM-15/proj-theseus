# Compliance Matrix Template

| #   | Section L Instruction     | Section M Factor / Subfactor | Section C Requirement(s) | Volume / Section | Page Limit | Owner    | Status             | Evidence           |
| --- | ------------------------- | ---------------------------- | ------------------------ | ---------------- | ---------- | -------- | ------------------ | ------------------ |
| 1   | `<L.id>: <verbatim text>` | `<M.id>: <factor name>`      | `<C.id list>`            | `<Volume #, §>`  | `<n>`      | `<name>` | OK / GAP / PARTIAL | `<entity_id refs>` |

**Rules:**

1. Every row must reference at least one entity from the workspace (`L`, `M`, or `C`). No bare narrative rows.
2. `GAP` rows are kept in place — never deleted — and listed in the output `warnings`.
3. Status legend:
   - `OK` — full L↔M↔C trace + volume assignment
   - `PARTIAL` — trace exists but page limit or owner missing
   - `GAP` — at least one of L / M / C cannot be linked to a workspace entity
4. Sort by Section L instruction order, then Section M factor weight (heaviest first within a tie).
