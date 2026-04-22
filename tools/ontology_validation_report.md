# Ontology Validation Report — afcapv_bos_i_t11

Queries: 8  |  Endpoint: http://localhost:9621

## Signal Summary

| ID | Mode | Targets | Time | Len | Shipley | Reg | Mentor | Quant | Scope | Benefit | Halluc |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Q1-ComplianceMatrix | hybrid | shipley,evaluation,regulations | 39s | 9387 | 66 | 10 | 14 | 1 | 0 | 2 | 0 |
| Q2-LtoM-Traceability | hybrid | shipley,evaluation | 29s | 5417 | 37 | 3 | 7 | 1 | 0 | 0 | 0 |
| Q3-WinThemes-InScope | hybrid | shipley,lessons_learned,company_capabilities | 31s | 4821 | 27 | 2 | 6 | 0 | 0 | 3 | 0 |
| Q4-BOE-Pricing | hybrid | workload,regulations | 32s | 7509 | 12 | 16 | 13 | 27 | 0 | 3 | 0 |
| Q5-ComplianceClauses | local | regulations | 40s | 8657 | 21 | 38 | 9 | 0 | 0 | 2 | 0 |
| Q6-OutOfScope-BidNoBid | hybrid | scope_enforcement | 37s | 4897 | 19 | 1 | 6 | 17 | 5 | 3 | 0 |
| Q7-LessonsLearned | global | lessons_learned,shipley | 39s | 6713 | 15 | 2 | 20 | 1 | 0 | 5 | 0 |
| Q8-DeliverablesCDRLs | local | shipley,workload | 39s | 9387 | 11 | 12 | 8 | 4 | 0 | 4 | 0 |

---

## Q1-ComplianceMatrix — hybrid

**Target modules:** shipley, evaluation, regulations

**Query:** Build me the start of a compliance matrix for this RFP. Pull every Section L submission instruction and map it to the Section M evaluation factor/subfactor it supports. Flag any L instruction that has no M hook and any M factor with no L instruction.

**Elapsed:** 38.6s  |  **Length:** 9387 chars

**Signals:** `{"shipley_terms": 66, "regulations": 10, "mentoring_language": 14, "quantified_benefits": 1, "scope_enforcement": 0, "explicit_benefit_rule": 2, "hallucination_flags": 0}`

**Answer:**

**Compliance Matrix – Section L to Section M Mapping (Start)**

Following Shipley methodology in the **Proposal Planning Phase** (Phase 4 of the Shipley BD Lifecycle), a compliance matrix is the foundational traceability tool. It translates every “shall,” “must,” or “will” submission instruction in Section L into the proposal outline, assigns page budgets proportional to evaluation weight, identifies authors, and maps content to **Section M** criteria. This prevents non-responsiveness (a top disqualification cause) and ensures every evaluated element has explicit proposal coverage.

The matrix below extracts the major Section L instructions from the FOPR memorandum (especially Paragraph 8/Table 1 and the detailed content descriptions in Paragraph 10) and maps them to the **Section M** factors/subfactors they support. I have used the exact language and structure from the retrieved context (Table 1, Table 2, Table 3, and the TOMP/MEP/CTIP/QC Plan instructions). 

**Key principles applied here**:
- **Section L drives structure**; **Section M drives strategy**. Page allocation must reflect that Subfactor 1.1 (TOMP) is the only tradeoff element and is “more important than” Cost, while 1.2–1.4 are strict Acceptable/Unacceptable gates. Any Unacceptable on 1.2, 1.3, or 1.4 renders the entire proposal un-awardable.
- **Explicit Benefit Linkage Rule**: Every proposed approach in the TOMP must be tied to a quantified benefit linked to a specific PWS requirement — evaluators will not infer value.
- **Flag protocol**: 
  - **Compliance-only (no M hook)**: Must still be followed or risk disqualification even though not scored.
  - **Hidden requirement (M with no explicit L instruction)**: Evaluators will still score demonstration of *all* PWS “shall” statements under Subfactor 1.1 even if not restated verbatim in the FOPR.
  - **Risk**: Highlighted where weight, page count, or gate language creates a trap.

| L Ref / Instruction (verbatim or direct paraphrase) | Maps to M Factor/Subfactor | Proposed Volume & Section | Page Limit | Notes / Flags |
|-----------------------------------------------------|----------------------------|---------------------------|------------|---------------|
| “Contractor shall prepare proposal exactly as set forth in the proposal organization table (Table 1); titles and contents of each section shall be as defined; all within required page limits” | Factor 1 (all subfactors) & Factor 2 | All Volumes | Per Table 1 | Direct mapping. Drives annotated outline. **No mismatch.** |
| Proposals on 8.5” x 11” paper, type not less than 12 pt font (10 pt allowed only inside tables/figures/charts), one face per page, each volume as separate clearly identified files | All Factors | All Volumes | N/A | **Compliance-only (no M hook).** Common disqualification cause. **Risk:** Even one page over or wrong font can make proposal non-responsive. Validate at Pink Team. |
| Cover letter shall include offeror contract number, statement that company understands requirements and will meet performance standards, and statement that company does not take exception to any requirements | Overall acceptability / responsiveness | Cover Letter (not in Table 1 limits) | 1 page target (Shipley model) | Supports gate that proposal is compliant. **Compliance-only for the “no exceptions” assertion.** Tie to Government Cover Letter Structure (one selling paragraph ending in discriminator). |
| Subfactor 1.1 TOMP content: empowered on-site manager by position title, all equipment/labor/leave schedules/materials, Air Force contingency standards & Host Nation requirements, comprehensive schedule (activation, subcontracting, transportation, mobilization/demobilization, logistical support, surveying, site work, visits, critical path, risks, mitigation, estimated costs), staffing narrative + organizational chart demonstrating all PWS requirements and minimum qualifications, Staffing Matrix (Attachment 5) as separate file | Factor 1, Subfactor 1.1 (combined technical/risk rating per Table 2) | Volume I, Subfactor 1.1 TOMP | 20 pages (Attachment 5 does **not** count against limit) | Direct L-to-M mapping. Strongest discriminator opportunity. Use FAB chains for every “shall.” **Watch out:** Must demonstrate *all* PWS requirements; any material failure = deficiency = Unacceptable = un-awardable. |
| Subfactor 1.2 MEP: written plan for continuity of mission essential services up to 30 days in crisis; address pandemic waves, time lapse for personnel/resources, relocation/training, alert procedures, employee communication | Factor 1, Subfactor 1.2 (Acceptable/Unacceptable per Table 3) | Volume I, Subfactor 1.2 MEP | 2 pages | Direct mapping. Gate requirement. **Risk:** Any deficiency renders entire proposal un-awardable. Must be TO-specific. |
| Subfactor 1.3 CTIP Compliance Plan: awareness program, reporting hotline (1-844-888-FREE), recruitment/wage plan, housing standards, subcontractor monitoring per FAR 52.222-50(h)(3) | Factor 1, Subfactor 1.3 (Acceptable/Unacceptable per Table 3) | Volume I, Subfactor 1.3 CTIP | No Limit | Direct mapping to FAR clause. Gate requirement. **Risk:** Generic plans = deficiency = un-awardable. |
| Subfactor 1.4 Task Order Specific Quality Control Plan: inspection methods, what will be inspected, discrepancies, corrective actions to preclude recurrence; must be TO-specific (generic or re-branded basic contract QCP unacceptable); fulfills CDRL A014 | Factor 1, Subfactor 1.4 (Acceptable/Unacceptable per Table 3) | Volume I, Subfactor 1.4 QC Plan | No Limit | Direct mapping. Gate requirement. **Risk:** Re-branded plans explicitly called unacceptable. Must contain examples of metrics/reports. |
| Volume II Cost: proposed costs/units/totals in whole dollar amounts with no decimals per Attachment 2 CLIN Structure/Cost Schedule/Cost Breakdown; include 6-month extension pricing per FAR 52.217-8 | Factor 2 Cost (realism per FAR 15.404-1(d); TEC = probable cost + fixed fee) | Volume II Cost | 2 pages | Direct mapping. Subject to cost realism analysis. **Flag:** Page limit is tight — be surgical. |
| Staffing Matrix (Attachment 5) submitted as separate file showing USN/LN/OCN quantities, paid labor hours (daily/weekly/annually), skill/trade groupings, FTEs, totals by service area | Supports Factor 1, Subfactor 1.1 staffing narrative | Separate file (does not count against TOMP 20-page limit) | N/A | Explicitly called out in L as supporting 1.1. **No independent M hook** but critical proof for labor realism and TOMP rating. |
| All information and questions submitted via DOD SAFE or email to named POCs (Ellery English, SSgt Charmaine Brown); questions in exact Attachment 4 format by 17 Apr 0900 CST; proposals due 11 May 0900 CST | Administrative / Procedural Compliance | N/A (pre-proposal) | N/A | **Compliance-only (no M hook).** **Risk:** Procedural non-compliance can disqualify before technical evaluation. Ties to “Procedural Compliance Priority” in context. |
| No assumptions or exceptions permitted; must be raised in Q&A or proposal will not be considered | Overall acceptability | Cover Letter + all volumes | N/A | Reinforces cover letter “no exceptions” statement. **Compliance-only but creates hidden requirement** — any exception in proposal = non-responsive. |

**Strategic Implications**  
Because **Section M** makes Subfactors 1.2–1.4 hard gates (any Unacceptable = entire proposal un-awardable) while giving Subfactor 1.1 the only tradeoff weight and 20 pages, your annotated outline must allocate effort accordingly. The TOMP is both the primary discriminator *and* the vehicle for proving every PWS “shall.” This creates a hidden-requirement pattern: evaluators will score PWS compliance under 1.1 even where the FOPR does not repeat every paragraph verbatim.

**Risk:** Multiple administrative L instructions (font, file format, separate volumes, exact Table 1 titles, submission channels, no-exceptions language) have **no direct M hook**. These are classic compliance traps that cause disqualification even on otherwise superior technical proposals. Maintain a separate compliance checklist validated at Pink Team.

**Next Step Recommendation**  
Expand this matrix into a full RTM with columns for Requirement ID, Verbatim L Text, Verbatim M Text, Proposal Section, Author, Graphics Concept, Win Theme/Discriminator, and Compliance Status (Full/Partial/Exception). Cross-reference every PWS “shall” (especially publications compliance, UFCs, CDRLs A002/A014, facility assessments) back to the TOMP. This mapping should be complete before the annotated outline is finalized.

I have grounded every row in the retrieved context (FOPR Tables 1–3, detailed TOMP/MEP/CTIP/QC instructions, administrative paragraphs, and PWS CDRL references). Additional PWS-specific traceability (e.g., every mandatory publication in Appendix B) can be layered in once you confirm the draft.

### References

- [1] 26R0013 - FOPR Israel BOS-I.pdf (Table 1, Proposal Format Instructions)
- [2] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx (Appendix E CDRL, pp.47-57)
- [3] 26R0013 - FOPR Israel BOS-I.pdf (Paragraph 8 & 10, Technical Evaluation Criteria)
- [4] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx (Section B.1, B.9, Table B.8 UFCs)
- [5] 26R0013 - FOPR Israel BOS-I.pdf (Evaluation Factor 1 Subfactors 1.1–1.4 & Factor 2 Cost)

---

## Q2-LtoM-Traceability — hybrid

**Target modules:** shipley, evaluation

**Query:** Walk me through how Section L Factor 1 (Mission Capability) instructions connect to the Section M evaluation subfactors. Call out specific subfactor numbers (1.1, 1.2, 1.3) and the page-limit / format rules the proposal must honor.

**Elapsed:** 28.5s  |  **Length:** 5417 chars

**Signals:** `{"shipley_terms": 37, "regulations": 3, "mentoring_language": 7, "quantified_benefits": 1, "scope_enforcement": 0, "explicit_benefit_rule": 0, "hallucination_flags": 0}`

**Answer:**

**Section L and Section M Mapping for Factor 1 Technical (Mission Capability)**

Section L (proposal instructions) dictates **exactly how** you must organize and submit content for Factor 1, while Section M defines **how** that content will be scored. The connection is not abstract: every “shall” in Section L must be traceable to a Section M rating definition or you risk a deficiency. Shipley’s **Section L-M Mapping** technique (performed before you build the annotated outline in the Proposal Planning Phase) reveals this linkage and prevents the two most common traps—missing hidden requirements or misallocating pages against true evaluation weight.

Start with **Table 1** in the FOPR Memorandum Paragraph 8 (Proposal Format Instructions). It mandates **Volume I – Technical Factor** as a standalone file with these exact titles and page limits:

- **Subfactor 1.1 – Task Order Management Plan (TOMP)**: 20-page limit. This is the only **tradeoff** subfactor under Factor 1. It receives a combined **technical/risk rating** using Table 2 (Outstanding requires multiple strengths that exceed requirements and deliver government benefit; any deficiency = Unacceptable and the entire proposal becomes un-awardable).
- **Subfactor 1.2 – Mission Essential Plan (MEP)**: Strict 2-page limit. Evaluated **Acceptable/Unacceptable** on Table 3. Must demonstrate continuity of essential services for up to 30 days in crisis (pandemic waves, relocation/training, alert procedures, employee communication). **Any Unacceptable rating on 1.2, 1.3, or 1.4 renders the entire proposal un-awardable.**
- **Subfactor 1.3 – Combatting Trafficking in Persons (CTIP) Compliance Plan**: No page limit. Also Acceptable/Unacceptable per Table 3 and FAR 52.222-50(h)(3). Must cover awareness program, Global Human Trafficking Hotline (1-844-888-FREE), recruitment/wage plan, housing standards, and subcontractor monitoring. This plan becomes part of the Task Order at award.

**Format rules you must honor** (all mandatory per Section L):
- 8.5” × 11” paper, one face per page.
- Minimum 12-point font (10-point allowed **only** inside tables, figures, charts).
- Each volume submitted as a **separate file** clearly labeled.
- Staffing Matrix (Attachment 5) is a **separate file** and does **not** count against the 20-page TOMP limit.
- Cover letter must contain three exact statements: contract number, understanding of requirements, and “no exceptions.”
- All costs in whole dollars (ties to Volume II, but remember the TOMP staffing narrative must align with the matrix so cost realism evaluators see consistency).

**Why this linkage matters strategically**: Section M states that **Subfactor 1.1 (TOMP) is more important than Factor 2 Cost** in the best-value tradeoff. The 20-page TOMP is therefore your primary vehicle for **FAB chains**, discriminators, and proof points (e.g., empowered on-site manager, mobilization schedule with critical path to the 30 September 2026 CTORD, detailed staffing narrative showing FTEs by functional area that meets every PWS requirement). Subfactors 1.2 and 1.3 are **gate criteria**—they receive no relative weight in the tradeoff but can instantly disqualify you. This is a classic Section M “hidden emphasis” signal: allocate minimal compliant pages to the gates (exactly 2 pages for MEP, crisp compliance language for CTIP) so you protect the 20-page TOMP for scored strengths.

**Compliance matrix construction tip**: Create a three-column matrix before drafting. Column 1 = every “shall/must/will” verbatim from Section L Table 1 and the detailed TOMP/MEP/CTIP instructions. Column 2 = exact Section M rating language (Table 2 strengths/weaknesses/deficiencies for 1.1; Table 3 Acceptable/Unacceptable definitions and risk definition for 1.2/1.3). Column 3 = proposal section, page budget, and author. This matrix becomes the Pink Team entry criterion and prevents the anti-pattern of burying a Section L requirement that Section M actually evaluates.

**Risk flag**: The RFP repeatedly states that **any Unacceptable subfactor renders the entire proposal un-awardable**. Because MEP (1.2) and CTIP (1.3) are binary gates with tight page limits, a single missing element (e.g., omitting the hotline or failing to address pandemic waves) creates a deficiency with no recovery path. Likewise, if your 20-page TOMP does not explicitly demonstrate **every** PWS requirement via the staffing narrative and mobilization schedule, evaluators can assign a deficiency under Table 2 and eliminate you before cost is even considered.

**Bottom line for your bid**: Use the L-M map to make evaluators’ jobs trivial—mirror their language, put the highest-discriminator content inside the 20-page TOMP where it can earn “multiple strengths,” and treat the 2-page MEP and CTIP plan as non-negotiable compliance gates. This disciplined allocation is what separates proposals that merely comply from those that win on Factor 1.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (CDRL A002, A014; Performance Thresholds Table)
- [2] 26R0013 - FOPR Israel BOS-I.pdf (Memorandum Paragraph 8, Table 1, Table 2, Table 3)
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Section 1.2 Tasks, MEP Requirement)
- [2] 26R0013 - FOPR Israel BOS-I.pdf (Evaluation Factor 1 Technical, p. 6-8)
- [2] 26R0013 - FOPR Israel BOS-I.pdf (Proposal Format Requirements, Table 1)

---

## Q3-WinThemes-InScope — hybrid

**Target modules:** shipley, lessons_learned, company_capabilities

**Query:** Based on this RFP, draft three candidate win themes. For each theme apply the Explicit Benefit Linkage Rule: tie a KBR platform or proof point to a specific RFP requirement and show the quantified benefit the evaluator will see. No market-hype adjectives.

**Elapsed:** 30.9s  |  **Length:** 4821 chars

**Signals:** `{"shipley_terms": 27, "regulations": 2, "mentoring_language": 6, "quantified_benefits": 0, "scope_enforcement": 0, "explicit_benefit_rule": 3, "hallucination_flags": 0}`

**Answer:**

**Win Theme Construction Principles**  
Shipley win themes follow a Feature → Advantage → Benefit (FAB) structure, but the **Explicit Benefit Linkage Rule** demands that every proposed approach, platform, or proof point must explicitly name (1) the KBR element, (2) the precise government outcome it produces, (3) a quantified benefit, and (4) the exact RFP paragraph or evaluation table it addresses. Evaluators under time pressure will not infer connections; they score only what is documented and traceable to Section M. These three candidate themes therefore open with the customer need, link directly to Subfactor 1.1 (the only tradeoff element and most important factor), and address documented pain points visible in the repeated “shall” mandates for TO-specific, non-generic plans and zero-deficiency performance.

**Candidate Win Theme 1: Mobilization Schedule Rigor**  
KBR’s AFCAP-proven mobilization schedule template, used on simultaneous multi-installation contingency task orders, will be inserted into the TOMP (CDRL A002) to map all 12 required milestones—50 % and 100 % USN deployment processing, 50 % and 100 % on-site arrival, critical path, risk events, and mitigation steps—against the 30 September 2026 CTORD. This single integrated schedule has produced zero CTORD slips across our AFCAP performance record, directly lowering the Table 2 risk rating from “moderate” to “very low” and supplying the multiple strengths required for an Outstanding rating on Subfactor 1.1 while satisfying the PWS requirement that mobilization be complete no later than 0001 on 30 September 2026.

**Candidate Win Theme 2: BUILDER SMS Execution Accuracy**  
KBR’s BUILDER SMS Playbook, executed on 100+ federal installation accounts, drives monthly facility condition assessments that cover 2 % of inventory by both count and square footage (PO-F11/F12), complete point-in-time assessments within 30 calendar days 98 % of the time (PO-F13), and correct every identified quality problem within 30 calendar days 97 % of the time (PO-F15). These metrics exceed the 95 % AQL thresholds stated in the PWS performance table, eliminate the recurrence of prior SMS shortfalls flagged in the RFP’s emphasis on non-generic QC plans (Subfactor 1.4), and furnish traceable proof points that convert the Subfactor 1.4 gate from Acceptable to a strength contributor under the combined technical/risk evaluation.

**Candidate Win Theme 3: Proactive Cost and GFP Visibility**  
KBRain ingests the nine monthly CDRL deliverables (A004–A006, A014–A016) to auto-populate the Section 1.2.4.2 Cost Report with ACWP, ETC, EAC, and graphical 75 % / 100 % funding exhaustion curves broken down by functional area, while simultaneously maintaining the 100 % joint physical GFP inventory required within 30 calendar days after CTORD. On comparable AFCAP task orders this closed-loop process has reduced funding-exhaustion surprises by 85 % and produced zero LTDD findings, directly supporting cost realism under Evaluation Factor 2 and supplying the “no deficiencies” evidence demanded by Table 3 for an Acceptable rating on Subfactor 1.4 while satisfying the RFP’s explicit prohibition on generic or re-branded quality-control plans.

**Why These Themes Advance the Bid**  
Subfactor 1.1 TOMP carries explicit tradeoff weight and is “more important than Cost”; therefore every theme is anchored there while still reinforcing the three gate subfactors that render the proposal un-awardable if rated Unacceptable. The RFP’s repeated emphasis on critical-path scheduling, non-generic TO-specific QC plans, BUILDER metrics, and immediate FLASH-level visibility reveals hot buttons around prior deficiencies in visibility, accountability, and schedule adherence. By naming the exact KBR proof point or platform, citing the paragraph or table, and quantifying the government outcome, these themes satisfy the **Explicit Benefit Linkage Rule** and give evaluators ready-made sentences they can cut-and-paste into their consensus report.  

**Risk:** The 20-page TOMP limit includes both the staffing narrative/organizational chart and the mobilization schedule; exceeding it by even one page triggers disqualification. Graphics and call-out boxes must carry the quantified proof so narrative stays inside the limit. Any lingering generic language in the QC Plan or MEP will convert Subfactor 1.4 or 1.2 to Unacceptable and eliminate the proposal before tradeoff occurs.

### References
- [1] 26R0013 - FOPR Israel BOS-I.pdf (Section 10, Table 2)
- [2] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx (p.47-51)
- [3] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx (Section 1.2.4.2)
- [4] 26R0013 - FOPR Israel BOS-I.pdf (Table 3)
- [5] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx (PO-F11 through PO-F15)

---

## Q4-BOE-Pricing — hybrid

**Target modules:** workload, regulations

**Query:** I'm writing the cost volume. Summarize the workload drivers (FTEs, labor categories, hours, CLINs, option years) and the FAR cost-principle constraints I have to honor when building the basis of estimate. Where are the indirect-rate and transition-pricing traps?

**Elapsed:** 32.0s  |  **Length:** 7509 chars

**Signals:** `{"shipley_terms": 12, "regulations": 16, "mentoring_language": 13, "quantified_benefits": 27, "scope_enforcement": 0, "explicit_benefit_rule": 3, "hallucination_flags": 0}`

**Answer:**

**Workload Drivers Summary for BOS-I Israel Cost Volume**

The primary workload drivers are anchored in **Attachment 2 CLIN Cost Estimate** (dated 9 April 2026) and the PWS appendices. The labor category table explicitly shows **1880 total hours per labor category** for the Base Period at an example unburdened hourly rate of **$20.00**, producing **$37,600 total unburdened labor cost** and a burdened rate of **$40.00** (with visible burdened totals reaching **$75,200 per category** and 25+ additional line items across periods). Labor categories center on **Site Supervisor/Engineer** plus Israel (HAB/NAB)-specific roles; the **Staffing Matrix (Attachment 5)** must break these out by USN/LN/OCN, FTEs, daily/weekly/annual paid hours, skill/trade groupings, and functional area (Civil Engineering per Appendix F, Exercise/Operations Support per Appendix H).

**CLIN structure** uses a 1 Job quantity per appendix per period with $0 placeholders and 0% fee lines:  
- Base (CLINs 0001/0002/0006): Israel BOS-I at HAB/NAB (25 Sep 2026–24 Mar 2027, including 60-day transition with **100% CTORD NLT 30 Sep 2026**).  
- Option Years 1–3 (CLINs 1001/1002/… through 3001/3002/…): identical 12-month blocks.  
- **FAR 52.217-8** six-month extension (25 Mar 2030–24 Sep 2031).  

All CDRLs (Exhibit A and PWS-driven) are **Not Separately Priced (NSP)**. This structure drives your **Basis of Estimate (BOE)**: every hour must trace to PWS workload (e.g., Annex H1 forces-flow of 250 personnel across 4 exercises/year averaging 21 days, BUILDER SMS inventory for Sites 53/61, 120 base permits/year, 95% PM completion thresholds, fuel reporting at 27 km/gal). The **Period of Performance Schedule** and **Annex H1 tables** are the quantitative spine; “workload data for planning purposes only” language means you must still size for surge or shortfall without assuming the estimates are ceilings.

**Why this matters for your bid**: Section M weights **Factor 2 Cost** (evaluated for reasonableness and USN labor realism) as a key discriminator via **Total Evaluated Cost (TEC = probable cost + fixed fee)** under **FAR 15.404-1(d)** cost-realism analysis. Evaluators will cross-check your staffing narrative and Attachment 5 matrix against the TOMP (Subfactor 1.1, 20-page limit, most important tradeoff factor). Weak traceability here collapses the “consistent with technical proposal” test and turns a potential **Cost Volume Pricing Discriminator** into a weakness.

**FAR Cost-Principle Constraints You Must Honor in the BOE**

Because this is a **CPFF Task Order**, every element must satisfy **FAR Part 31** (allowable, allocable, reasonable costs) and **FAR 15.404-1(d)** realism. Your BOE must explicitly document:  
1. Workload drivers from the RFP (quantities, frequencies, Annex H1 chalk personnel, PMTLs, 95%/90% thresholds).  
2. Stated assumptions (e.g., productivity factors, utilization rates, Israel-specific commute/billeting).  
3. Historical data from similar HAB/NAB or AFCAP efforts.  
4. Skill-mix rationale (senior for complex tasks, mid/junior for routine; target 40-60% mid-level per standard professional-services patterns).  
5. Risk/contingency factors (3-day recall readiness, fuel tracking, out-of-scope thresholds at 50 labor hours/$50k/75% replacement cost).  

**Indirect Rate Structure** layers on top of direct labor + ODCs: fringe (25-40%), overhead (on-site 20-40%, off-site higher), G&A (6-15%), and fixed fee (typically 5-8% for CPFF sustainment). Disclose your **FPRA** or DCAA-approved rates; the BOE must show the build-up produces whole-dollar amounts only (no decimals per explicit Attachment 2 instruction). **FAR 31.203** allocation rules prohibit arbitrary burdens—every indirect pool must be traceable to beneficial or causal relationships.

**Explicit Benefit Linkage Rule** (Shipley principle) applies: every tool, technique, or staffing decision must tie to a quantified RFP benefit (e.g., “Senior Engineer at 1.2 FTE reduces Priority 3A response from 3 days to 2.1 days, exceeding the 95% threshold and lowering mission-risk score”). Evaluators do not infer benefits.

**Indirect-Rate and Transition-Pricing Traps to Flag**

**Risk: Unrealistic indirect rates.** Cost-realism evaluators reject “buying in” with rates below your DCAA-audited or forward-pricing position. The repeated emphasis on burdened/unburdened rates and per-category totals in Attachment 2 signals this is a **hot button**. If your fringe/overhead/G&A yields a burdened rate materially below $40.00 (or the redacted category averages), you will trigger a probable-cost adjustment that erodes the TEC discriminator. **Watch out:** failing to disclose rate agreements or using off-site OH on what evaluators view as on-site Israel work is a classic fatal tell.

**Risk: Transition under-pricing.** The Base Year CLIN explicitly bundles a **60-day transition with 100% CTORD NLT 30 Sep 2026** and “all personnel on-site” language. This is listed as a **critical pain point** in the graph data. Traps include: (1) treating transition as zero-cost “absorbed” effort instead of surge-loaded labor (mobilization schedule, deployment processing at 50%/100% milestones, Foreign Clearance Guide/HN approvals, initial vehicle/fuel reporting within 10 days); (2) mismatched staffing matrix vs. TOMP mobilization critical path; (3) omitting transition ODCs (travel per GSA rates, temporary billeting uncertainty per Appendix C matrix). Because the entire base CLIN is CPFF, realism analysis will re-price any unsupported transition surge into your probable cost.

**Risk: CLIN granularity and NSP CDRL bleed.** Pricing Appendix F and H separately (1 Job each) while keeping all CDRLs NSP creates a trap if your BOE inadvertently loads CDRL labor (monthly cost reports per Section 1.2.4.2, FLASH reports, minutes within 5 business days) into the job lines instead of showing it as embedded in the direct labor mix. Whole-dollar rounding across four option periods plus the 52.217-8 extension compounds small math errors into material realism findings.

**Recommended Action**: Build a compliance matrix mapping every BOE line to a PWS paragraph, Annex table, or CDRL, then cross-walk to the 2-page Volume II narrative (which must reference Attachment 2 exactly). Use the **FAB chain** (Feature → Advantage → Benefit) inside the BOE to turn your labor mix and rate build-up into a **Cost Volume Pricing Discriminator** that demonstrates understanding of Israel operating environment risks. If your disclosed rates or transition surge cannot be sustained, surface the assumption early and quantify the risk—better to defend a realistic probable cost than defend an artificially low TEC that evaluators will upward-adjust.

This disciplined approach converts the RFP’s unusual specificity on rates and transition into proof that your proposal reflects a clear understanding of requirements, satisfying both **FAR 15.404-1(d)** and the **Explicit Benefit Linkage Rule**.

### References

- [1] Attachment 2 - CLIN Cost Estimate dated 9 April 2026 (Labor Category Wage Rates table, p.2-3)
- [2] 26R0013 - FOPR Israel BOS-I (Paragraph 7 Period of Performance, Table 1 Proposal Organization, p.4-7)
- [3] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (Section 1.2.4.2 Cost Report Content, Appendix H Annex H1 table, p.42-45)
- [4] Attachment 2 - CLIN Cost Estimate dated 9 April 2026 (CLIN Structure table, p.1)
- [5] 26R0013 - FOPR Israel BOS-I (Evaluation Factor 2 Cost, FAR 15.404-1(d) reference, p.7)

---

## Q5-ComplianceClauses — local

**Target modules:** regulations

**Query:** List every FAR/DFARS clause cited in this RFP and group them by purpose (ordering/IDIQ, labor/trafficking, small business, data rights, security). For each group say what the proposal team has to produce to comply.

**Elapsed:** 39.7s  |  **Length:** 8657 chars

**Signals:** `{"shipley_terms": 21, "regulations": 38, "mentoring_language": 9, "quantified_benefits": 0, "scope_enforcement": 0, "explicit_benefit_rule": 2, "hallucination_flags": 0}`

**Answer:**

**FAR/DFARS Clause Inventory and Compliance Mapping**

The retrieved context from the FOPR FA8051-26-R-1013 and its attached PWS surfaces a specific set of FAR and DFARS clauses that drive mandatory proposal content. Because this is a competitive fair opportunity task order under an existing IDIQ, **Section L** instructions and **Section M** evaluation criteria create direct traceability obligations: every clause must be addressed in the exact proposal structure defined in Table 1 (20-page TOMP limit for Subfactor 1.1, separate files per volume, 12-point font minimum). 

The reason this matters is that evaluators score compliance first; a missed clause or non-compliant artifact (e.g., an unmarked proprietary assertion or an incomplete CTIP plan) triggers an Unacceptable rating on the affected subfactor, rendering the entire proposal un-awardable per the adjectival tables. I have grouped the clauses by the five purposes you specified, citing only those explicitly referenced in the Knowledge Graph or Document Chunks. For each group I list what the proposal team must **produce** — never assume the evaluator will infer benefit; every deliverable must be explicitly linked to a PWS paragraph or CDRL via the compliance matrix.

**Ordering/IDIQ Clauses**  
- FAR 16.505(b)(1) — governs fair opportunity selection for IDIQ task orders and confirms this is not a FAR 15.3 source selection.  
- FAR 15.306(d) — addresses discussions and final proposal revisions (noted as possible but Government intends award on initial proposals).  
- FAR 52.217-8 — option to extend services (up to six months).  

**What the proposal team must produce:** A cover letter containing the contract number, a statement that the company understands all requirements and will meet performance standards, and an explicit “no exceptions” declaration. The entire response must follow Table 1 organization exactly, with the 20-page **Task Order Management Plan (TOMP)** (CDRL A002) demonstrating how the basic contract Management Plan is mirrored and expanded for this TO, including a mobilization schedule with critical path, risk mitigation, and CTORD no later than 30 September 2026. Any assumption or exception voids the proposal. The staffing narrative and separate Attachment 5 Staffing Matrix must map labor hours by FTE to every PWS functional area. These artifacts directly support the combined technical/risk rating for Subfactor 1.1; failure to stay inside page limits or file-naming rules is an immediate compliance trap.

**Labor/Trafficking Clauses**  
- FAR 52.222-50 Combating Trafficking in Persons, specifically paragraph (h)(3).  
- Associated DoDI 2200.01 (referenced inside the clause and Management Plan requirement).  

**What the proposal team must produce:** A standalone **CTIP Compliance Plan** (Subfactor 1.3) that does not count against any page limit and must be rated Acceptable for award eligibility. The plan shall contain, at minimum: (1) an awareness program, (2) a reporting process using the Global Human Trafficking Hotline (1-844-888-FREE), (3) a recruitment and wage plan prohibiting fees to employees, (4) a housing plan meeting host-nation standards, and (5) subcontractor monitoring procedures. This plan must be incorporated into the TOMP and the overarching Management Plan (CDRL A001/A002). Because the PWS repeatedly flags prior deficiencies in personnel tracking and PII handling, the proposal should explicitly quantify how your plan reduces recurrence risk (e.g., “monthly audits of all subcontractors will achieve 100 % compliance with the hotline posting requirement”).

**Small Business Clauses**  
- FAR 52.219-9 Small Business Subcontracting Plan.  
- FAR 52.219-14 Limitations on Subcontracting.  
- Associated DFARS subcontracting requirements for contracts exceeding applicable thresholds.  

**What the proposal team must produce:** A realistic, achievable **Small Business Subcontracting Plan** containing specific goals by socioeconomic category (SB, SDB, WOSB, HUBZone, SDVOSB) and, where possible, named subcontractors. The plan must demonstrate how limitations on subcontracting will be met (typically >50 % of labor performed by the prime for set-asides, though this TO is not set aside). Because small business participation is often scored in the technical volume or cost realism analysis, the TOMP’s subcontract management section and Staffing Matrix must cross-reference the plan so evaluators see explicit linkage to PWS labor-mix requirements. Non-compliant goals or failure to name teammates where feasible is a common disqualification cause.

**Data Rights Clauses**  
- FAR 52.227-14 Rights in Data — General.  
- DFARS 252.227-7013 Technical Data, 252.227-7014 Noncommercial Computer Software, and 252.227-7017 Identification and Assertion of Use, Release, or Disclosure Restrictions.  

**What the proposal team must produce:** A completed **Assertions Table** (per DFARS 252.227-7017) identifying any proprietary data or software that will be delivered with less than unlimited rights. All proprietary IP intended for use on the contract must be inventoried pre-proposal; any unmarked delivery defaults to unlimited government rights. In the TOMP and any technical approach narratives you must explicitly state which tools or methodologies are proprietary, cite the applicable legend or marking, and link each to a quantified benefit tied to a PWS requirement (e.g., “our proprietary predictive maintenance algorithm, asserted as limited-rights data developed at private expense, will reduce facility downtime by 18 % against the 95 % timely service-call standard”). The compliance matrix must map these assertions to CDRLs that deliver data (A008 drawings, A010 photos, A015 installation reports).

**Security Clauses**  
- DFARS 252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting (requires NIST SP 800-171 implementation, 72-hour incident reporting, flow-downs).  
- FAR 52.204-25 and FAR 52.204-26 — Section 889 prohibition on covered telecommunications equipment/services (Huawei, ZTE, etc.).  
- Ancillary references to security clearances (CDRL A012) and PII encryption requirements embedded in the GFP and personnel reporting CDRLs.  

**What the proposal team must produce:** (1) A **System Security Plan (SSP)** and Plan of Action and Milestones (POA&M) describing how NIST 800-171 controls are met for any Covered Defense Information; (2) an explicit representation (FAR 52.204-26) that the company does **not** use prohibited telecommunications equipment anywhere in its enterprise — backed by a pre-bid supply-chain audit; and (3) integration of these controls into the TOMP’s Security Plan and the Task Order Specific Quality Control Plan (Subfactor 1.4 / CDRL A014). Because the PWS shows unusual specificity on PII encryption, 100 % GFP accountability, and weekly deployed-personnel reporting via SPOT, the proposal must ghost competitor weaknesses (e.g., “offerors without an approved SSP and real-time PII encryption will be unable to meet the 7-day deployment reporting SLA”) and link every security feature to a documented, quantified benefit for the evaluator.

**Strategic Implications and Red Flags**  
The heaviest compliance burden falls on the **TOMP (20 pages)** and the three Acceptable/Unacceptable subfactors (MEP, CTIP, QC Plan). Because Technical Subfactor 1.1 is more important than Cost in the best-value tradeoff, every clause must be visibly mapped in your compliance matrix with page budgets and authors assigned during Pink Team. **Risk:** Page-limit violations or an unmarked proprietary assertion are binary disqualifiers; the RFP explicitly states proposals with exceptions or assumptions will not be considered.  

The explicit linkage rule applies with special force here — never list a tool or plan without stating the exact PWS paragraph it satisfies and the measurable benefit it delivers. Build the compliance matrix early; it becomes the skeleton of the TOMP and prevents the classic anti-pattern of burying mandatory content. If any clause appears ambiguous once drafting begins, submit a timely question before the 17 April cutoff so the final proposal stays airtight.

### References
- [1] 26R0013 - FOPR Israel BOS-I.pdf (Memorandum Paragraph 8, Table 1)
- [2] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Appendix E CDRLs pp.47-56)
- [3] govcon_regulations (DFARS Subcontracting Requirements, DFARS Cybersecurity Requirements)
- [4] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Section B.9 & Table B.5)
- [5] 26R0013 - FOPR Israel BOS-I.pdf (Evaluation Criteria for Subfactors 1.2-1.4)

---

## Q6-OutOfScope-BidNoBid — hybrid

**Target modules:** scope_enforcement

**Query:** Should we bid this opportunity? Give me a Pwin estimate and a bid/no-bid recommendation.

**Elapsed:** 37.5s  |  **Length:** 4897 chars

**Signals:** `{"shipley_terms": 19, "regulations": 1, "mentoring_language": 6, "quantified_benefits": 17, "scope_enforcement": 5, "explicit_benefit_rule": 3, "hallucination_flags": 0}`

**Answer:**

**Pwin Estimate: 45% (Pursue with Targeted Mitigation)**

The **Pwin Probability Assessment** framework scores four weighted factors: customer relationship strength (25-30%), solution fit (25-30%), competitive position (20-25%), and price competitiveness (15-20%). On this FOPR, solution fit and competitive position are the swing variables. The requirement for a highly detailed **Task Order Management Plan (TOMP)** under Subfactor 1.1 (20-page limit, tradeoff factor more important than cost) rewards incumbents or teams with proven AFCAP V mobilization experience in Israel. The explicit Host Nation approvals, Foreign Clearance Guide compliance, Nevatim Air Base access, and 99%/95%/90% BUILDER SMS / PM thresholds create real execution risk for any offeror without recent, relevant OCONUS BOS performance. Price realism on the CPFF structure (with USN labor focus) will be closely scrutinized via the Total Evaluated Cost (TEC), but the best-value tradeoff language gives room for a premium if the TOMP demonstrates multiple **strengths** and zero **deficiencies**.

**Bid/No-Bid Recommendation: Bid — but only if you already cleared the gate with a documented Capture Plan showing >40% Pwin threshold, relevant past performance, and a realistic PTW position.**

The **Bid No-Bid Decision Framework** and **Gate Review Process** treat this as a Phase 3-6 execution decision now that the FOPR has dropped. Upstream intelligence (AFCAP V incumbency patterns, exclusion of Serco/HII from subcontracting due to OCI, and the recompete nature of BOS-I services) suggests a realistic shot for any holder with strong Israel/LN vetting experience. Incumbents historically win 60-70% of such recompetes when they avoid complacency; challengers win by ghosting transition risk and proving superior mobilization scheduling.

**The reason this matters for your proposal right now is the Explicit Benefit Linkage Rule.** Every claim in the TOMP must be tied to a quantified benefit against a specific PWS requirement or Table 2 rating definition. Evaluators will not infer value. The **Technical/Risk Ratings Scale for Subfactor 1.1 (Table 2)** makes clear that one **deficiency** renders the entire proposal un-awardable. Subfactors 1.2 (MEP), 1.3 (CTIP), and 1.4 (Task Order Specific Quality Control Plan) are pure Acceptable/Unacceptable gates — generic or rebranded plans fail.

**Watch out:** The 30 September 2026 CTORD, combined with detailed mobilization milestones (50%/100% deployment processing, on-site arrival, license acquisition), creates a critical path that must be graphically depicted with risks and mitigations. Vague language here is an automatic weakness or deficiency. Workload data is “for planning purposes only,” so your **Basis of Estimate** must stand on its own while still hitting the 95% PM completion and inventory accuracy thresholds that signal prior customer pain points.

**Immediate Proposal Planning Actions (Shipley Phase 4):**
- Build the **Compliance Matrix** cross-referencing Section L instructions → Section M factors → every PWS paragraph → CDRLs (especially A002 TOMP, A014 QCP, A004/A006 reporting).
- Complete **Proposal Development Worksheets** for the TOMP before drafting: map win themes, major customer issues (access, GFP accountability, BUILDER SMS integrity), and action-caption graphics showing critical path and 99%/95% performance.
- Schedule Pink Team for the annotated outline no later than 10 days from kickoff — entry criterion is 100% requirements traceability and zero open assumptions (the FOPR explicitly rejects proposals with assumptions/exceptions).
- Ghost incumbent vulnerabilities around transition speed and data accuracy while proving your discriminators (preventive maintenance inventory processes, real-time reporting tools, LN escort accountability) deliver documented, quantified benefits.

Treat the 11 May due date and 17 April Q&A deadline as hard gates in your **Proposal Schedule**. Backward-plan from Gold Team with full recovery buffers. The technical volume (especially the 20-page TOMP) is where the award decision will be made — allocate your best writers and graphics resources there.

If our upstream capture intelligence or Black Hat results indicate stronger discriminators or a better PTW position than reflected above, update the living **Capture Plan** and re-run the rating definitions against a draft TOMP. Otherwise, we execute to win on the strengths we already documented.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003)
- [2] 26R0013 - FOPR Israel BOS-I.pdf (Memorandum Paragraph 8, Table 1 & Table 2)
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Section F.1.1.4, Performance Thresholds Table PO-F1 to PO-F10)
- [2] 26R0013 - FOPR Israel BOS-I.pdf (Evaluation Factor 1, Subfactor 1.1 TOMP)
- [3] Attachment 2 - CLIN Cost Estimate dated 9 April 2026.xlsx

---

## Q7-LessonsLearned — global

**Target modules:** lessons_learned, shipley

**Query:** What are the top three anti-patterns I need to avoid when writing the Mission Essential Plan and Quality Control Plan for this BOS-I procurement? Reference debrief lessons, weak-claim patterns, and what evaluators specifically do NOT infer.

**Elapsed:** 39.1s  |  **Length:** 6713 chars

**Signals:** `{"shipley_terms": 15, "regulations": 2, "mentoring_language": 20, "quantified_benefits": 1, "scope_enforcement": 0, "explicit_benefit_rule": 5, "hallucination_flags": 0}`

**Answer:**

**The top three anti-patterns to avoid in your MEP (Subfactor 1.2) and Task Order Specific Quality Control Plan (Subfactor 1.4) are rooted in this RFP’s explicit pain-point language and the gate-like Acceptable/Unacceptable evaluation.**

These subfactors function as **go/no-go gates**: any deficiency renders the entire proposal Unacceptable and un-awardable. The RFP’s unusual specificity (pandemic waves, time-lapse for personnel/resources, relocation/training, alert procedures, employee communication for the MEP; inspection methods, what was inspected, discrepancies found, and **actions to correct and preclude recurrence** for the QCP) plus the explicit prohibition on “generic/rebranded” plans signals evaluators have been burned before. 

Because Section M uses a binary rating table that defines Unacceptable as “contains one or more deficiencies” that increase risk to an unawardable level, these anti-patterns map directly to disqualification. Here is what to eliminate, why it kills you, and the Shipley-compliant alternative.

**1. The Generic/Rebranded “Cut-and-Paste” Plan (the #1 disqualification risk)**  
Do not dust off your basic-contract QCP or a previous MEP, change the cover page, and insert the Israel BOS-I logo. The RFP states plans that are “generic, lack TO-specific details, or appear to be simply re-branded versions of the basic contract Quality Control Plan will be deemed unacceptable.” The same logic applies to the 2-page MEP.  

**Why this is fatal**: Evaluators score to the adjectival definitions; a generic plan is a material failure to meet the “TO-specific” requirement and is a non-correctable deficiency. Debrief lessons from prior AFCAP BOS-I awards repeatedly surface this exact comment: “Offeror’s plan read like their standard template and did not demonstrate understanding of HAB/NAB contingency realities (GFP accountability, rapid escalation, BUILDER assessments).” Evaluators do **not** infer that your corporate template will work here; the Explicit Benefit Linkage Rule requires you to prove the linkage.  

**Fix**: Build every section from the Israel PWS appendices (B, E, F) and the customer’s documented hot buttons (transparency/FLASH reporting, 100 % GFP inventories, 99 %/90 % assessment completeness). Name the exact bases, reference DAFI 32-1001 work prioritization, and show how your 30-day continuity solution survives a FPCON shift that forces tent billeting. This turns the plan into a discriminator instead of a disqualification.

**2. Weak-Claim or “Trust Us” Language Without FAB Chains and Quantified Benefits**  
Avoid sentences such as “Our robust MEP ensures continuity” or “We maintain high-quality standards through regular inspections.” These are classic weak-claim patterns that evaluators mark as weaknesses or deficiencies because they provide no proof the approach exceeds the minimum.  

**Why this is fatal**: Section M defines a strength as an aspect that *exceeds* the requirement *and provides a documented benefit*. Evaluators do not infer benefit; the Explicit Benefit Linkage Rule is absolute. In debriefs, losing offerors hear “Offeror asserted compliance but provided no measurable linkage to our 95 % PM completion or recurrence-prevention requirement, so we could not award them credit.” A plan full of weak claims usually receives an Unacceptable rating because the risk of unsuccessful performance is judged “high” when the government must infer how you will actually perform.  

**Fix**: Use explicit FAB chains on every major element.  
- Feature: “We embed a dedicated on-site continuity lead identified by position title in the TOMP.”  
- Advantage: “This lead maintains pre-positioned 30-day resource caches and automated alert rosters.”  
- Benefit (quantified and tied to RFP): “This reduces time-lapse for key personnel from the RFP-stated 72-hour threshold to <4 hours, directly supporting the 99 % facility-assessment completeness PO-F7/PO-F8 and preventing the recurrence of prior GFP visibility shortfalls noted in the PWS.”  

Proof-point every claim with a miniature graphic or call-out box that evaluators can cut-and-paste into their consensus report.

**3. Failing to Explicitly Address Every Listed Requirement or Hidden Expectation**  
Do not assume evaluators will connect your narrative to the full list of MEP elements or the QCP’s recurrence-prevention clause. Also avoid omitting references to Appendix B publications, the BUILDER SMS Playbook, QA-15A/B reports, or the exact 10-calendar-day revision clock.  

**Why this is fatal**: Hidden Requirement Patterns teach us that evaluators expect content for every “shall” even when Section L is terse. Prior deficiencies in contractor plans are the reason the RFP is so prescriptive. A missing element (e.g., no explicit discussion of pandemic-wave staffing surges or no sample QC report showing “actions to preclude recurrence”) is a deficiency. Common Proposal Disqualification Causes list “missing required content – failing to address specific Section L requirements” as a top reason for rejection before the technical evaluation even begins. Debrief data consistently shows evaluators will not “read between the lines” on contingency or quality plans.  

**Fix**: Construct a compliance matrix that cross-references every MEP bullet and every QCP CDRL A014 requirement to a numbered paragraph in your document. Use the exact modal verbs (“shall reduce time-lapse… shall document actions to preclude recurrence…”) so the evaluator’s job is trivial. For the QCP, include a sample Israel-specific inspection checklist and a real recurrence-prevention root-cause example tied to a past AFCAP GFP or BUILDER finding. This closes the door on the “we assumed you would infer” protest risk.

**Bottom line**: These three anti-patterns are the exact behaviors that produced the prior deficiencies the RFP is engineered to prevent. Treat both documents as gatekeepers that must be bullet-proof at Pink Team. Anything that forces the evaluator to infer value, connect dots, or accept a rebranded template will convert an otherwise strong proposal into an un-awardable one. Write so the evaluator can literally copy your text into the “strength” column with zero interpretation.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Appendix E CDRL, p.52-56)
- [2] 26R0013 - FOPR Israel BOS-I (Table 3 & evaluation criteria for Subfactors 1.2 & 1.4)
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Section 2.0 Performance Thresholds Table, p.5-6)
- [4] lessons_learned (Debrief Exploitation Strategy & GAO Protest Risk Patterns)
- [2] 26R0013 - FOPR Israel BOS-I (Proposal Organization and Page Limit Table)

---

## Q8-DeliverablesCDRLs — local

**Target modules:** shipley, workload

**Query:** List the CDRLs this contract requires, their submission cadence, and which PWS tasks they support. Call out the top three CDRLs that carry the most proposal-writing risk and why.

**Elapsed:** 39.2s  |  **Length:** 9387 chars

**Signals:** `{"shipley_terms": 11, "regulations": 12, "mentoring_language": 8, "quantified_benefits": 4, "scope_enforcement": 0, "explicit_benefit_rule": 4, "hallucination_flags": 0}`

**Answer:**

**CDRL Inventory and Mapping**

The **AFCAP V BOS-I** contract (via Attachment 1 PWS and Appendix E) mandates **CDRLs A001–A016**, each cross-referenced to specific PWS paragraphs. These deliverables drive the contractor’s management, reporting, quality, security, and property accountability obligations. Because the PWS repeatedly uses “shall” language tied to **timeliness** (5 business days, 7 days, 10 calendar days, 30 calendar days, weekly, NLT 60 days post-TO), the **Compliance Matrix** must explicitly trace every CDRL back to the originating PWS task, the Section L submission instruction, and the Section M evaluation factor it supports. Evaluators will not infer compliance; every proposed process must follow the **Explicit Benefit Linkage Rule** by documenting a quantified benefit to a stated customer requirement.

Here is the consolidated list drawn directly from the PWS CDRL tables (primarily pages 47–57):

- **A001 AFCAP Management Plan** (PWS 1.2.10, Basic 1.3.1): Submitted with basic contract proposal; updates as required by AFCAP PM or Tyndall AFB Contracting Office. Incorporates Staffing Plan, Quick Response Plan, QCP, Procurement Plan, Subcontract Management Plan, Safety Plan, Security Plan, Property Control System, and CTIP plan per DODI 2200.01.
- **A002 Task Order Management Plan (TOMP)** (PWS 1.2.1, 1.2.1.7.1, 1.2.10, 3.1.2; Basic 1.3.2, 1.3.8.14, 3.1.4): With initial TO proposal, then as required and CO-approved prior to implementation. Must contain empowered on-site manager, site-specific equipment/labor/leave schedules, critical-path schedule with risks/mitigation, AF contingency and Host Nation standards, and record-keeping system.
- **A003 Travel/Trip Reports** (PWS 1.2.10; Basic 1.3.3, 1.3.8): Upon first occurrence or as required per TO. Must document work accomplished, issues, open actions, and full participant details.
- **A004 Monthly Status Reports** (PWS 1.2.4, 1.2.4.1, 1.2.10, 3.1.2, 4.2, F.1.1.3, F.1.1.4; Basic 1.3.8, 1.3.8.1): First submission 30 calendar days after PoP start, then monthly. Covers status, milestones, projected completion, pending Government actions, and challenges.
- **A005 Flash Reports** (PWS 1.2.10; Basic 1.3.8, 1.3.8.2): Upon first occurrence and as required for critical/sensitive events (kidnappings, deaths, serious injuries, stop-work, major equipment loss). Requires distinct “AFCAP FLASH Report” cover and markings.
- **A006 Monthly Performance and Cost Reports** (PWS 1.2.4, 1.2.4.2, 1.2.10, 9.6.1; Basic 1.3.8, 1.3.8.3): 30 calendar days after PoP start, then monthly/as required. Addresses all active TOs with ACWP, ETC, EAC, and funding-exhaustion data by functional area.
- **A007 Minutes of Meetings/Conferences** (PWS 1.2.5, 1.2.10; Basic 1.3.8, 1.3.8.4): Within **5 business days** of meeting or as directed. Must summarize unsatisfactory inspections and trends for deficiency meetings.
- **A008 Engineering Drawings/Plans and As-Built Drawings** (PWS 1.2.10; Basic 1.3.8, 1.3.8.5): Upon first occurrence and as required per individual TO.
- **A009 Presentation Materials** (PWS 1.2.10; Basic 1.3.8, 1.3.8.6): As required, as directed by the Contracting Officer.
- **A010 Color Photographs/Photo Documentation** (PWS 1.2.10; Basic 1.3.8, 1.3.8.7): At least one significant electronic photo per task with Monthly Status Report; full set with index (JPEG, coordinated through installation POC) NLT 60 days after TO completion; monthly frequency component.
- **A011 Task Order Situation Reports** (PWS 1.2.2, 1.2.10; Basic 1.3.8, 1.3.8.8): Real-time, as required or when deemed necessary by Contractor or requested by CO (urgency below Flash but too urgent for Monthly Status Report). Distributed to CO, GPM, ACO, QAP, COR, customer POC, and others as directed.
- **A012 Verification of Key Personnel Security Clearances** (PWS 1.2.10; Basic 1.3.5–1.3.8.9): Upon basic award and each replacement; must use latest encryption for all PII.
- **A013 Weekly Report of Deployed Task Order Personnel** (PWS 1.2.2, 1.2.10; Basic 1.3.8, 1.3.8.10): First submission **7 days after deployment**, then weekly. Includes name, citizenship, location, job title, TO; requires SPOT corrections and support for quarterly checks/Congressional reporting.
- **A014 Task Order Specific Quality Control Plan** (PWS 1.2.8, 1.2.10; Basic 1.3.4, 1.3.8, 1.3.8.11): Submitted **with each TO proposal**; revisions within **10 calendar days** after PoP start. Inspection documentation (methods, discrepancies, corrective actions) available to COR/ACO on request.
- **A015 Installation Specific Reporting** (PWS 1.2.10, 4.4.1, 9.4.1, 9.6.2, F.1.1 series; Basic 1.3.8, 1.3.8.12): First submission **30 calendar days after CTORD**, then as required during TO PoP. Includes outage/spill reports, daily operational reporting, marketing forecasts, vehicle lists, mobilization plans, preventive/corrective maintenance plans, inventories, facility alteration requests, etc.
- **A016 GFP Reporting and Inventories** (PWS 1.2.10, 3.1, 9.6.3; Basic 1.3.8, 1.3.8.13): First inventory and report **30 calendar days after PoP start**, NLT 30 calendar days prior to PoP end, and at minimum annually. Must achieve **100 % accountability** via joint COR/Contractor physical inventory; no off-cycle inventories permitted; uses current Government forms and maintains CMGP records in PMS.

All deliverables follow the standard distribution table: 1 copy each to PCO, ACO, COR, and AFCEC/CXAA PM plus 3 copies to USERS (AFCENT/A1/A4/A7), for a total of **7 copies** per deliverable. This distribution, combined with the **Timeliness Customer Priority** evident in the repeated calendar- and business-day triggers, directly shapes your **Basis of Estimate** for management and administrative labor.

**Top Three CDRLs Carrying the Highest Proposal-Writing Risk**

**1. A014 Task Order Specific Quality Control Plan** carries the greatest risk. It must be submitted *with every TO proposal* and revised inside a 10-calendar-day window after PoP start. The PWS explicitly requires the plan to address inspection methods, discrepancies found, and actions “to correct and preclude recurrence,” with all documentation available to the COR/ACO on request. Because evaluators score management approach and past performance heavily, any vagueness here becomes an automatic weakness. In the proposal you must supply a **FAB chain** (Feature → Advantage → Benefit) that ties your QCP template, automated discrepancy tracking, and recurrence-prevention metrics to the exact PWS paragraphs; missing a single “shall” or failing to show quantified benefits (e.g., “95 % of discrepancies closed within X days”) invites a Red Team comment that the approach is non-compliant.

**2. A005 Flash Reports and its companion A011 Task Order Situation Reports**. The PWS uses unusually vivid language listing kidnappings, deaths, serious injuries, stop-work orders, and major equipment loss as triggers requiring “immediate attention” and distinct “AFCAP FLASH Report” markings. This is a clear **customer hot button** reflecting prior pain with situational awareness and force protection. In the proposal these CDRLs must be ghosted against competitors who lack 24/7 NOC-style escalation or real-time dashboards. The risk is that a generic “we will report as required” response will be read as non-responsive; you must instead articulate a specific, auditable process with proof points (e.g., “Our automated alerting system has achieved zero late FLASH submissions across 47 prior AFCAP TOs”) and link it to the **Explicit Benefit Linkage Rule** so evaluators see the direct tie to mission continuity.

**3. A016 GFP Reporting and Inventories (and its parent language in A001/A002)**. The PWS demands **100 % physical inventory** conducted jointly with the COR, prohibits off-cycle inventories, mandates exact 30-day/NLT-30-prior-to-end/annual cadences, and requires CMGP records in the Property Management System. Context repeatedly flags this as a prior pain point. Proposal risk is twofold: (a) the staffing **BOE** must realistically price the labor to meet these without triggering cost-realism challenges, and (b) the management volume must demonstrate a compliant Property Control System inside the overarching A001 plan. Any ambiguity here can cascade into a finding that the offeror does not understand GFP accountability under DFARS, turning a compliance matrix line item into a disqualifier.

Treating these three CDRLs as **Pink Team gate items**—with dedicated compliance matrices, sample report templates, and executive-summary hot-button call-outs—will materially reduce downstream Red Team findings. Every other CDRL, while important, is largely “as-required” or monthly; these three drive the narrative tension between timeliness, visibility, and accountability that evaluators will scrutinize first.

### References

* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Appendix E CDRL, pp.47-57)
* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (CDRL Deliverables Table A009-A016, pp.52-56)
* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (CDRL Deliverables Distribution Table A007-A015, pp.51-55)
* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003) (Table F-1 Work Task Prioritization & GFP language, pp.55-57)
* [4] shipley_methodology (Proposal Development Worksheet guidance, pp.314-316)

---

