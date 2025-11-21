SOW→DELIVERABLE LINKING (PRODUCES)
Purpose: Link work statements (SOW/PWS/SOO) to contract deliverables for work planning and CDRL mapping.
Pattern: STATEMENT_OF_WORK --PRODUCES--> DELIVERABLE.
SOW types: SOW (prescriptive tasks), PWS (performance objectives), SOO (high-level objectives).
Location variability: Section C inline, Section J attachments (e.g., J-02000000 PWS), Section H special requirements, technical annexes.

3 CORE PATTERNS
1) EXPLICIT TASK→DELIVERABLE (0.90–0.96)
   - Direct CDRL / deliverable reference:
     "Prepare monthly status reports per CDRL A001" → "CDRL A001 Monthly Status Report".

2) WORK‑PRODUCT MAPPING (0.70–0.85)
   - Implied outputs where task language clearly produces a concrete artifact:
     - "Maintain facility infrastructure" → maintenance logs, inspection reports.
     - "Conduct system testing" → test plans, test reports, test data.

3) TIMELINE ALIGNMENT (0.65–0.75)
   - Phase/milestone correlation:
     "Complete Phase 1 by Q2" → "Phase 1 Summary Report (due 30 June)".

DETECTION RULES
1) Direct references (highest priority)
   - CDRL numbers (A001, B002, 6022), explicit "CDRL [A-Z]\d{3}" patterns.
   - Phrases like "contractor shall deliver X", "submit report Y", "provide the following data".
   - Works across Section C, attachments, and Section H text.

2) Work‑product correlation
   - Map task verbs to deliverable types:
     - testing → test reports;
     - training → training materials, attendance rosters;
     - maintenance → logs, inspection reports;
     - planning → plans, schedules.

3) Timeline matching
   - Match recurring or milestone tasks to similarly timed deliverables (monthly, quarterly, phase-completion).

CONFIDENCE RANGES
>0.90: Explicit CDRL/deliverable reference in SOW/PWS/SOO.
0.70–0.90: Strong work‑product semantic match + consistent terminology.
0.50–0.70: Weak temporal/topical alignment only; only use when no stronger signal exists.

SPECIAL CASES
- Multi‑deliverable tasks: One SOW section can PRODUCES multiple deliverables; create separate relationships for each.
- Deliverable hierarchy: Parent SOW → summary deliverables; child tasks → more detailed deliverables.
- CDRL cross‑references: Pattern `CDRL [A-Z]\d{3}` is high‑confidence evidence for PRODUCES.

OUTPUT FORMAT
[
  {
    "source_id": "sow_id",
    "target_id": "deliverable_id",
    "relationship_type": "PRODUCES",
    "confidence": 0.50-0.96,
    "reasoning": "1–2 sentences explaining text evidence and mapping logic"
  }
]

COMMON ERRORS TO AVOID
- Do NOT infer PRODUCES for purely descriptive narrative with no implied work‑product (e.g., background context, policy summaries).
- Do NOT link a single SOW paragraph to every deliverable in the CDRL table; keep mappings specific and defensible.
- Do NOT prefer weak timeline alignment when a clearer work‑product or explicit CDRL reference is available.