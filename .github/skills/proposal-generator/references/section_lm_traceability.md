# Section L↔M Traceability (proposal-generator)

See also: `govcon-ontology/references/lm_golden_thread.md` for the extraction-side view.

When drafting a volume:

1. Pull every `evaluation_factor` and `subfactor` from the workspace.
2. For each, list the `proposal_instruction` items linked via `EVALUATED_BY` / `GUIDES`.
3. For each instruction, list the `requirement` items linked via `REFERENCES`.
4. Allocate page budget proportional to factor weight (see `page_budget_heuristics.md`).
5. Generate one section heading per evaluation factor / subfactor with the linked instructions cited inline.
