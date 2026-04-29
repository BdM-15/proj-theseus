# Upstream

`oci-sweeper` is a **greenfield Theseus skill** with no external upstream. It was authored under the `skill-creator` MANDATE workflow during Phase 4j (Skill Taxonomy + frontmatter pass).

## Authoring discipline

- **Evals-before-prose.** `evals/evals.json` was authored first (3 prompts covering all three FAR 9.505 conflict classes: incumbent → impaired objectivity, customer-side personnel → biased ground rules, prior-contract data → unequal access). The SKILL.md body and references were drafted to close the gaps those evals exposed.
- **Progressive disclosure.** SKILL.md body stays under 200 lines. The FAR taxonomy, mitigation playbook, and Cypher query patterns live in `references/` and load only when the runtime invokes `read_file` against them per the numbered workflow checklist.
- **Closed-by-default.** No MCPs declared. The skill operates against the workspace KG (via `kg_entities`, `kg_query`, `kg_chunks`) and a vendored FAR Subpart 9.5 reference. Live FAR fetch was intentionally skipped — Subpart 9.5 (sections 9.501–9.508) is short and stable enough that a vendored reference is more reliable than a network call.
- **Anthropic best-practices applied** (per `platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices`): six-field frontmatter only; description includes both WHAT (FAR Subpart 9.5 sweep) and WHEN (pre-bid OCI due diligence) plus a third-person "pushy" tone; references one level deep; no `templates/` (uses `assets/` if/when needed); workflow expressed as a numbered Markdown checklist invoking the runtime tools, not as a custom YAML field.

## Future upstream considerations

If the federal acquisition community publishes a canonical OCI taxonomy (DAU / DAFI guidance evolution, GAO bid-protest precedent updates), the `references/far_9_5_oci_taxonomy.md` file is the right place to cite and incorporate it. Keep the three-class structure (biased ground rules / unequal access / impaired objectivity) — that's the FAR statutory anchor and won't change without a Federal Acquisition Regulatory Council rulemaking.

If the skill grows into a multi-skill OCI sub-suite (e.g., separate `oci-sweeper`, `oci-mitigation-plan-drafter`, `oci-waiver-package-builder`), keep `oci-sweeper` as the _detection_ skill and split _drafting_ / _waiver-packaging_ into their own folders rather than inflating this one.

## Re-vendoring

Not applicable — no external source to re-vendor. Treat this UPSTREAM.md as the authoring provenance record only.
