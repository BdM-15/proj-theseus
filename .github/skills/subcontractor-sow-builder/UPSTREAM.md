# UPSTREAM.md — subcontractor-sow-builder

## Source

Vendored from [`1102tools/federal-contracting-skills`](https://github.com/1102tools/federal-contracting-skills) — `skills/sow-pws-builder/`.

- **License:** MIT © James Jenrette.
- **Vendor commit:** captured at branch creation; refresh via `tools/_skill_snapshots/` workflow.
- **Theseus phase:** 4h (`docs/skills_roadmap.md`).

## The 5-Point Stance-Inversion Contract

The upstream skill writes a SOW/PWS from the **federal CO seat** — government agency authoring scope to issue out to a prime contractor. Theseus uses the same body content from the **prime → sub seat** — prime contractor authoring scope to issue downward to a subcontractor or teaming partner. The mechanics are the same; the seat is different. This contract documents the five inversions:

### 1. Audience and Voice

|               | Upstream (CO → contractor)      | Theseus (prime → sub)                                 |
| ------------- | ------------------------------- | ----------------------------------------------------- |
| Author        | Federal contracting officer     | Prime contractor's program manager / contracts        |
| Audience      | Industry offerors               | Sub or teaming partner                                |
| Voice         | Government acquisition language | Prime↔sub commercial-style language with FAR flowdown |
| Document name | "RFP SOW/PWS"                   | "Subcontract SOW/PWS"                                 |

### 2. CLIN and Section B Boundary

The upstream skill is silent on Section B (CLINs). Theseus is **explicit**: CLINs live in the prime↔sub subagreement, NOT in the SOW/PWS body. Section B emerges as a **chat-only handoff** at the end of the run (CLIN Handoff Table), separate from the artifact. This avoids confusion between scope authoring and pricing structure.

### 3. Staffing Handoff is Chat-Only

Both seats forbid FTE counts, SOC codes, and staffing tables in the body (FAR 37.102(d)). Upstream documents this rule but produces no separate artifact for IGCE handoff. Theseus emits a **Staffing Handoff Table as chat-only output** at the end of the run, formatted for direct ingestion by the `price-to-win` skill. Never written to disk; never appended as Appendix E.

### 4. Key Personnel Clause Discipline

Both seats avoid FAR 52.237-2 (wrong clause). Upstream defaults to "agency-specific Key Personnel clause". Theseus extends this with an explicit fallback chain in `references/far_citations.md`:

1. Agency-specific clause if known (NFS, HSAR, HHSAR variants).
2. FAR 52.237-3 (Continuity of Services) as generic fallback.
3. Custom contract-specific language if neither applies.

The skill MUST NEVER emit `FAR 52.237-2` for Key Personnel substitution.

### 5. Phase 2 Approval Gate

Upstream allows the CO to self-approve the Phase 1 Decision Summary and proceed. Theseus **forces a STOP** — the user must reply "proceed" (or correct items) before the artifact is generated. This protects the prime PM from a wrong derived default getting locked into a sub-facing document.

## Architectural Note: Why Each Skill Owns Its Own `references/`

Theseus splits the upstream skill into two Theseus skills (`subcontractor-sow-builder` for the FORWARD seat; `rfp-reverse-engineer` for the REVERSE seat — see that skill's UPSTREAM.md). Both consume the same intellectual content, but the runtime sandbox `tool_read_file` in `src/skills/tools.py` rejects cross-skill `references/` paths.

**Decision:** Each skill owns its own `references/` folder, with content **adapted to the workflow direction** (forward needs the section spec; reverse needs the signal-decoder catalog).

**Future TODO:** If references drift becomes a maintenance burden, introduce `extra_read_roots` in `src/skills/manager.py` and `src/skills/tools.py` mirroring the existing `script_paths` pattern (~30 lines). Tracked in `docs/PHASE_4H_SOW_SKILLS.md`.

## Re-Vendor Procedure

1. `git clone https://github.com/1102tools/federal-contracting-skills /tmp/upstream-fcs`.
2. Snapshot current state: `cp -r .github/skills/subcontractor-sow-builder tools/_skill_snapshots/subcontractor-sow-builder-pre-revendor/` (gitignored).
3. Diff `/tmp/upstream-fcs/skills/sow-pws-builder/` against `tools/_skill_snapshots/`.
4. Apply only the changes that preserve the 5-point stance-inversion contract above.
5. Bump `metadata.version` and refresh `evals/evals.json` if behavior changed.
6. Re-run contract tests: `.\.venv\Scripts\python.exe -m pytest tests/skills/test_subcontractor_sow_builder_skill.py -v`.

## License Notice

Upstream is MIT-licensed. The original LICENSE text is preserved in the upstream repository. Modifications made by Theseus are documented in this file and in `docs/PHASE_4H_SOW_SKILLS.md`.
