# Workspace Query Comparison Report

**Generated:** 2026-04-15 14:50:01  
**Workspace A:** `afcapv_bos_i_t4`  
**Workspace B:** `afcapv_bos_i_t5`  

> ⚠️ **Limitation:** Neo4J was not available. All queries ran in `naive` mode, which retrieves
> the same raw text chunks from both workspaces. Answer length differences reflect LLM
> temperature variance, **not** ontology quality differences. Rerun with Neo4J running
> to get meaningful `local`/`global`/`hybrid` comparisons using the entity graph.

## Executive Summary

| ID | Category | Mode | A Length | B Length | Winner |
|:---|:---------|:-----|:--------:|:--------:|:------:|
| Q1 | Entity Discovery | `naive` | 3619 | 2845 | A (+774 chars) |
| Q2 | Entity Discovery | `naive` | 5511 | 4318 | A (+1193 chars) |
| Q3 | Entity Discovery | `naive` | 4609 | 5148 | B (+539 chars) |
| Q4 | Requirement Traceability | `naive` | 4537 | 4277 | A (+260 chars) |
| Q5 | Requirement Traceability | `naive` | 4486 | 5072 | B (+586 chars) |
| Q6 | Document Hierarchy | `naive` | 2973 | 3416 | B (+443 chars) |
| Q7 | Cross-Document | `naive` | 4204 | 4412 | B (+208 chars) |
| Q8 | Cross-Document | `naive` | 3267 | 3856 | B (+589 chars) |
| Q9 | Strategic | `naive` | 3817 | 4155 | B (+338 chars) |
| Q10 | Compliance | `naive` | 9491 | 9921 | B (+430 chars) |

---

## Q1: Entity Discovery

**Query (naive mode):** List all evaluation factors and their associated weights or scoring criteria.

### afcapv_bos_i_t4

### Evaluation Factors Overview

The evaluation is conducted using tradeoff procedures based on **two primary evaluation factors**: **Technical Subfactor 1.1 – Task Order Management Plan (TOMP)** and **Factor 2 – Cost**. Technical Subfactor 1.1 (TOMP) is **more important** than Factor 2 (Cost). **Factor 1 – Technical Subfactors 1.2 (Mission Essential Plan), 1.3 (Combating Trafficking in Persons Compliance Plan), and 1.4 (Task Order Specific Quality Control Plan)** are **not part of the tradeoff process**. These subfactors are evaluated on an **Acceptable/Unacceptable** basis, and the proposal must receive an **Acceptable** rating in all three to be eligible for award. Any **Unacceptable** rating in Subfactors 1.2, 1.3, or 1.4 renders the entire proposal **Unacceptable** and **un-awardable**.

No numerical weights (e.g., percentages) are assigned to the factors. Instead, the award decision uses an **integrated best-value tradeoff assessment**, considering professional judgment alongside the relative importance of Subfactor 1.1 over Cost.

### Detailed Scoring Criteria for Technical Factors

- **Subfactor 1.1: Task Order Management Plan (TOMP)** receives a **combined technical/risk rating** based on **Table 2** criteria:
  | Rating       | Description |
  |--------------|-------------|
  | **Outstanding** | Meets requirements with an exceptional approach and understanding; multiple strengths; very low risk of unsuccessful performance. |
  | **Good**     | Meets requirements with a thorough approach and understanding; at least one strength; low risk of unsuccessful performance. |
  | **Acceptable** | Meets requirements with an adequate approach and understanding; offsetting strengths/weaknesses with little/no impact; no worse than moderate risk. |
  | **Marginal** | Does not clearly meet requirements; unoffset weaknesses; high risk of unsuccessful performance. |
  | **Unacceptable** | Does not meet requirements; one or more deficiencies; un-awardable. |

  Strengths, weaknesses, and deficiencies are defined as: **Strength** (exceeds requirement with government benefit); **Weakness** (flaw increasing risk); **Deficiency** (material failure or significant weaknesses raising risk to unacceptable level).

- **Subfactors 1.2, 1.3, and 1.4** use **Table 3** binary ratings:
  | Rating      | Description |
  |-------------|-------------|
  | **Acceptable** | Meets requirements with adequate approach/understanding; low risk of disruption, cost increase, or performance degradation; no deficiencies. |
  | **Unacceptable** | Does not meet requirements; one or more deficiencies; un-awardable; unacceptable risk level. |

  Risk considers potential for schedule disruption, performance degradation, increased oversight, or unsuccessful performance.

### Cost Factor Evaluation

**Factor 2 – Cost** undergoes a **cost realism analysis** per FAR 15.404-1(d), assessing reasonableness, realism for proposed work, and consistency with the technical proposal. This determines the **probable cost** (added to fixed fee for **Total Evaluated Cost (TEC)**), which serves as a key discriminator. Additional evaluation may compare TECs to the Independent Government Estimate (IGE) or use other FAR 16.505(b)(3) techniques. Proposals must include costs for a potential 6-month extension under FAR 52.217-8.

### Additional Notes
Proposals are evaluated for the **best-value combination** advantageous to the Government. If only one proposal is received, evaluation shifts to technical acceptability and sole-source cost analysis without tradeoff.

### References
- [2] 26R0013 - FOPR Israel BOS-I.pdf

*Response time: 1.1s*

### afcapv_bos_i_t5

### Evaluation Factors Overview

The Fair Opportunity Proposal Request (FOPR) outlines a best value tradeoff award process using two primary evaluation factors: **Factor 1 - Technical Factor** (with subfactors) and **Factor 2 - Cost**. Technical Subfactor 1.1 (Task Order Management Plan - TOMP) is **more important than Factor 2 - Cost**. Factor 1 Subfactors 1.2, 1.3, and 1.4 are evaluated on a **pass/fail basis (Acceptable/Unacceptable)** and are **not part of the tradeoff process**. To be eligible for award, an offeror **must receive an Acceptable rating** on Subfactors 1.2, 1.3, and 1.4; any Unacceptable rating renders the proposal un-awardable. No numerical weights (e.g., percentages) are specified; relative importance is qualitative.

### Factor 1: Technical Factor

- **Subfactor 1.1: Task Order Management Plan (TOMP)**  
  Evaluated using a **combined technical/risk rating** per Table 2:  
  - **Outstanding**: Meets requirements with exceptional approach/understanding; multiple strengths; very low risk.  
  - **Good**: Meets requirements with thorough approach/understanding; at least one strength; low risk.  
  - **Acceptable**: Meets requirements with adequate approach/understanding; offsetting strengths/weaknesses; no worse than moderate risk.  
  - **Marginal**: Does not clearly meet requirements; unoffset weaknesses; high risk.  
  - **Unacceptable**: Does not meet requirements; one or more deficiencies; un-awardable.  
  Strengths exceed requirements with government benefit; weaknesses increase risk; deficiencies are material failures.

- **Subfactor 1.2: Mission Essential Plan (MEP)**  
  **Acceptable/Unacceptable** per Table 3:  
  - **Acceptable**: Meets requirements with adequate approach/understanding; low risk with little potential for disruption/cost/performance issues; no deficiencies.  
  - **Unacceptable**: Does not meet requirements; one or more deficiencies; un-awardable; unacceptable risk.

- **Subfactor 1.3: Combating Trafficking in Persons (CTIP) Compliance Plan**  
  **Acceptable/Unacceptable** per Table 3 (same criteria as Subfactor 1.2).

- **Subfactor 1.4: Task Order Specific Quality Control Plan**  
  **Acceptable/Unacceptable** per Table 3 (same criteria as Subfactor 1.2).

### Factor 2: Cost

Evaluated for **reasonableness** and **United States National (USN) Labor realism** via cost realism analysis per FAR 15.404-1(d). Determines probable cost of performance, reflecting understanding of requirements and consistency with technical proposal. **Total Evaluated Cost (TEC)** = probable cost + proposed fixed-fee; key discriminator in competitive environment. Includes costs for 6-month extension option per FAR 52.217-8. Comparisons may use Independent Government Estimate (IGE) or other FAR 16.505(b)(3) techniques.

### References

- [2] 26R0013 - FOPR Israel BOS-I.pdf

*Response time: 0.3s*

---

## Q2: Entity Discovery

**Query (naive mode):** What deliverables (CDRLs) are required under this contract? List them with their submission schedules.

### afcapv_bos_i_t4

### Contract Data Requirements List (CDRL) Deliverables

The contract requires the submission of specific Contract Data Requirements List (CDRL) deliverables as outlined in Appendix E of the Performance Work Statement (PWS). These deliverables support various aspects of task order management, reporting, quality control, and compliance under the AFCAP V contract for Base Operations Support and Installation (BOS-I) services at Hatzor Air Base (HAB) and Nevatim Air Base (NAB), Israel. Each CDRL includes defined PWS references, first submission dates, and frequencies. Distribution typically requires 1 copy each to the 772 ESS/PKD Procuring Contracting Officer (PCO), Administrative Contracting Officer (ACO), Contracting Officer’s Representative (COR), and AFCEC/CXAA Program Manager (PM), plus 3 copies to USERS (AFCENT/A1, A4, or A7), unless otherwise specified. Note that AFCAP Main Contract CDRLs (e.g., additional Flash Reports) may apply, and delivery requirements may change at the Contracting Officer’s request.

### List of Required CDRLs with Submission Schedules

- **A001: AFCAP Management Plan**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.1.  
  **First Submission**: As part of the Basic V contract proposal.  
  **Frequency**: Original Proposal; Changes/Updates as required by the AFCAP PM Management and/or the AFCAP Contracting Office.

- **A002: Task Order Management Plan (TOMP)**  
  PWS Reference: 1.2.1, 1.2.1.7.1, 1.2.10, 3.1.2; Basic Contract PWS Reference: 1.3.2, 1.3.8.14, 3.1.4.  
  **First Submission**: Contractor’s initial proposal.  
  **Frequency**: As required (updates approved by Contracting Officer prior to implementation).

- **A003: Travel/Trip Reports**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.3, 1.3.8.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: As required.

- **A004: Monthly Status Reports**  
  PWS Reference: 1.2.4, 1.2.4.1, 1.2.10, 3.1.2, 4.2, F.1.1.3, F.1.1.4; Basic Contract PWS Reference: 1.3.8, 1.3.8.1.  
  **First Submission**: Thirty (30) calendar days after start of Period of Performance (PoP).  
  **Frequency**: Monthly.

- **A005: Flash Reports**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.2.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: As required.

- **A006: Monthly Performance and Cost Reports**  
  PWS Reference: 1.2.4, 1.2.4.2, 1.2.10, 9.6.1; Basic Contract PWS Reference: 1.3.8, 1.3.8.3.  
  **First Submission**: Thirty (30) calendar days after start of PoP.  
  **Frequency**: As required.

- **A007: Minutes of Meetings/Conferences**  
  PWS Reference: 1.2.5, 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.4.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: As required (within five business days of meeting/conference completion, or as directed by ACO or COR).

- **A008: Engineering Drawings/Plans and As-Built Drawings**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.5.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: As required (per subsequent individual Task Orders).

- **A009: Presentation Materials**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.6.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: As required (as directed by the Contracting Officer).

- **A010: Color Photographs/Prints/Photo Documentation**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.7.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: Monthly (NLT 60 days after Task Order completion; at least one photo per task with Monthly Status Report).

- **A011: Task Order Situation Reports**  
  PWS Reference: 1.2.2, 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.8.  
  **First Submission**: Upon first occurrence.  
  **Frequency**: As required ("real-time" status reports).

- **A012: Verification of Key Personnel Security Clearances**  
  PWS Reference: 1.2.10; Basic Contract PWS Reference: 1.3.5 (subparagraphs), 1.3.6, 1.3.7, 1.3.8, 1.3.8.9.  
  **First Submission**: Upon first occurrence (basic contract award and key personnel replacement).  
  **Frequency**: As required.

- **A013: Weekly Report of Deployed Task Order Personnel**  
  PWS Reference: 1.2.2, 1.2.10; Basic Contract PWS Reference: 1.3.8, 1.3.8.10.  
  **First Submission**: Seven (7) days after personnel deploy.  
  **Frequency**: Weekly.

- **A014: Task Order Specific Quality Control Plan**  
  PWS Reference: 1.2.8, 1.2.10; Basic Contract PWS Reference: 1.3.4, 1.3.8, 1.3.8.11.  
  **First Submission**: With proposal submission.  
  **Frequency**: As required (revisions within 10 calendar days after PoP start).

- **A015: Installation Specific Reporting**  
  PWS Reference: 1.2.10, 4.4.1, 9.4.1, 9.6.2, F.1.1.4, F.1.1.5, F.1.1.9; Basic Contract PWS Reference: 1.3.8, 1.3.8.12.  
  **First Submission**: Thirty (30) calendar days after Contract Task Order Release Date (CTORD).  
  **Frequency**: As required (due dates as specified in each Task Order).

- **A016: Government Furnished Property (GFP) Reporting**  
  PWS Reference: 1.2.10, 3.1, 9.6.3; Basic Contract PWS Reference: 1.3.8, 1.3.8.13 (subparagraphs).  
  **First Submission**: Thirty (30) calendar days after start of PoP.  
  **Frequency**: As required (30 days prior to PoP end, minimum annually, based on physical inventories; other times as directed).

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.4s*

### afcapv_bos_i_t5

### Contract Data Requirements List (CDRL) Deliverables

The contract requires submission of specific Contract Data Requirements List (CDRL) deliverables as outlined in Appendix E of the Performance Work Statement (PWS). These deliverables support task order management, reporting, quality control, and compliance under the AFCAP V contract for Base Operations Support - Israel (BOS-I). Each CDRL includes references to PWS sections, a description, date of first submission, and frequency.

### List of Required CDRLs with Submission Schedules

The following table summarizes all identified CDRLs (A001 through A016), their titles, key PWS references, first submission dates, and frequencies:

| CDRL ID | Deliverable Title | Key PWS References | First Submission | Frequency |
|---------|-------------------|--------------------|------------------|-----------|
| A001 | AFCAP Management Plan | 1.2.10; Basic 1.3.1 | Submitted as part of the Basic V contract proposal | Original Proposal; Changes/Updates as required by AFCAP PM or Contracting Office |
| A002 | Task Order Management Plan (TOMP) | 1.2.1, 1.2.1.7.1, 1.2.10, 3.1.2; Basic 1.3.2, 1.3.8.14, 3.1.4 | Contractor’s initial proposal | As required (updates approved by Contracting Officer prior to implementation) |
| A003 | Travel/Trip Reports | 1.2.10; Basic 1.3.3, 1.3.8 | Upon first occurrence | As required (per TO stipulations) |
| A004 | Monthly Status Reports | 1.2.4, 1.2.4.1, 1.2.10, 3.1.2, 4.2, F.1.1.3, F.1.1.4; Basic 1.3.8, 1.3.8.1 | 30 calendar days after Period of Performance (PoP) start | Monthly |
| A005 | Flash Reports | 1.2.10; Basic 1.3.8, 1.3.8.2 | Upon first occurrence | As required |
| A006 | Monthly Performance and Cost Reports | 1.2.4, 1.2.4.2, 1.2.10, 9.6.1; Basic 1.3.8, 1.3.8.3 | 30 calendar days after PoP start | As required |
| A007 | Minutes of Meetings/Conferences | 1.2.5, 1.2.10; Basic 1.3.8, 1.3.8.4 | Upon first occurrence | As required (within 5 business days) |
| A008 | Engineering Drawings/Plans and As-Built Drawings | 1.2.10; Basic 1.3.8, 1.3.8.5 | Upon first occurrence | As required (per TOs) |
| A009 | Presentation Materials | 1.2.10; Basic 1.3.8, 1.3.8.6 | Upon first occurrence | As required (as directed by Contracting Officer) |
| A010 | Color Photographs, Prints, Photo Documentation | 1.2.10; Basic 1.3.8, 1.3.8.7 | Upon first occurrence | Monthly (NLT 60 days after TO completion; at least 1 per task with Monthly Status Report) |
| A011 | Task Order Situation Reports | 1.2.2, 1.2.10; Basic 1.3.8, 1.3.8.8 | Upon first occurrence | As required ("real-time" as necessary or requested) |
| A012 | Verification of Key Personnel Security Clearances | 1.2.10; Basic 1.3.5, 1.3.5 subparagraphs, 1.3.6, 1.3.7, 1.3.8, 1.3.8.9 | Upon first occurrence (upon award/replacement) | As required |
| A013 | Weekly Report of Deployed Task Order Personnel | 1.2.2, 1.2.10; Basic 1.3.8, 1.3.8.10 | Seven (7) days after personnel deploy | Weekly |
| A014 | Task Order Specific Quality Control Plan | 1.2.8, 1.2.10; Basic 1.3.4, 1.3.8, 1.3.8.11 | With proposal submission | As required (revisions within 10 calendar days after PoP start) |
| A015 | Installation Specific Reporting | 1.2.10, 4.4.1, 9.4.1, 9.6.2, F.1.1.4, F.1.1.5, F.1.1.9; Basic 1.3.8, 1.3.8.12 | Thirty (30) calendar days after Contract Task Order Release Date (CTORD) | As required (per TO due dates) |
| A016 | Government Furnished Property (GFP) Reporting | 1.2.10, 3.1, 9.6.3; Basic 1.3.8, 1.3.8.13 | Thirty (30) calendar days after PoP start | As required (NLT 30 days prior to PoP end; minimum annually; based on physical inventories) |

### Additional Notes on Deliverables
Distribution for most CDRLs requires 1 copy each to 772 ESS/PKD Procuring Contracting Officer (PCO), Administrative Contracting Officer (ACO), Contracting Officer’s Representative (COR), and AFCEC/CXAA Program Manager (PM), plus 3 copies to USERS (AFCENT/A1, A4, or A7), unless otherwise specified. NOTE #2 indicates AFCAP Main Contract CDRLs may apply (e.g., Flash Reports). NOTE #3 states delivery table requirements may change at Contracting Officer request. Some deliverables like Facility Maintenance Plan (FMP) and performance measurement plans/summaries reference CDRL A004 or A015.

### References
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.5s*

---

## Q3: Entity Discovery

**Query (naive mode):** What performance metrics or quality thresholds are specified in the PWS?

### afcapv_bos_i_t4

### Overview of Performance Metrics and Quality Thresholds

The Performance Work Statement (PWS) outlines specific performance objectives (POs), thresholds, and surveillance methods primarily in Section 2.0 Service Summary - Performance Thresholds Tables for Facilities Management (POs F1-F15). These metrics focus on facility condition assessments, preventive maintenance (PM), inventory management, and work execution, with surveillance via **Periodic Inspection (Monthly)** for most POs and **100% Inspection** for select items like PM schedules. Thresholds emphasize high completion rates (e.g., 90-99%), minimal deficiencies (e.g., no more than 1-3 per month), and timely responses (e.g., within 30 days).

Key categories include:

- **Monthly Facility Condition Assessments (BUILDER Inventory)**:
  - PO-F11/PO-F12: At least **2%** of established BUILDER inventory per month (measured by facility count and square footage).
  - PO-F7/PO-F8: At least **99%** assessment completeness per month (facility count and square footage).
  - PO-F9/PO-F10: At least **90%** current facility condition assessments each month (facility level, count and square footage).

- **Timely Assessments and Corrections**:
  - PO-F13: Complete point-in-time assessments within **30 calendar days** after written request, at least **95%** of the time.
  - PO-F14: Update component-section assessments within **30 calendar days** after work task completion, at least **95%** of the time.
  - PO-F15: Correct identified facility/component-section quality problems within **30 calendar days** after identification, at least **95%** of the time.

### Preventive Maintenance and Inventory Management Metrics

Preventive maintenance and system inventory POs ensure high reliability:

- **PM Completion and Scheduling**:
  - PO-F1: Complete all Priority 2A PM, **95%** of scheduled PM completed.
  - PO-F2: Submit PM schedules for COR approval not later than **30 calendar days** after Full Operational Capability (FOC), updated/validated twice a year (**100% Inspection**).

- **Inventory Corrections**:
  - PO-F3: Initiate corrective action within **5 workdays** for duplicate/excess records; no more than **1** late initiation per month.
  - PO-F4: Ensure RPA Type B/S/LS facilities have required systems inventoried; no more than **3** missing/incomplete per month.
  - PO-F5/PO-F6: Complete system inventory updates (**30 calendar days**) and correct discrepancies (**10 workdays**) after identification, at least **95%** of the time.

### Work Prioritization and Response Thresholds (Table F-1)

Section F.1.1.3 specifies work categories per DAFI 32-1001, with **95%** of service calls responded to and completed timely. Detailed metrics by priority:

| Work Priority | Key Thresholds |
|---------------|----------------|
| **Priority 1 (Emergency)** | Respond within **1 hour**; mitigate within **24 hours**. |
| **Priority 2A (PM/Plant Ops)** | Execute **95%** of scheduled monthly PM; no task deferred/missed for **2 consecutive months**. |
| **Priority 3A (High Sustainment)** | Respond within **1 hour** (≤**2** late/month); complete **95%** within **3 calendar days** (parts on hand; procure within **1 business day** if not). |
| **Priority 3B (Medium)** | Complete within **7 calendar days**; **90%** deferred work within **7 days** of parts receipt. |
| **Priority 3C (Low)** | Complete within **45 calendar days** (parts on hand). |

Work Request Review Board (WRRB): Single requirements exceeding **50 direct labor hours**, **$50,000** materials, or **75%** asset replacement cost are candidates for separate projects. Limit minor construction to **10%** of work order hours. All administrative close-outs within **30 calendar days** of physical completion.

### Assessment Completeness and Currency Standards

- **Completeness (F1.3.2)**: Achieve/maintain **99%** per month (facility count/square footage); if initial <**80%**, reach **99%** in Base Year.
- **Currency (F1.3.3.1)**: **90%** monthly (facility level); assessments current if <**5 years** old. If initial <**80%**, achieve **90%** in Base Year. Monthly assessments on at least **1.67%** BUILDER inventory (**20%** annually in Option Years).

These metrics apply to satisfactory performance levels, with re-performance at no cost for deficiencies. Government surveillance includes periodic/100% inspections and customer complaints.

### References

* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.3s*

### afcapv_bos_i_t5

### Overview of Performance Metrics and Quality Thresholds

The Performance Work Statement (PWS) outlines detailed **satisfactory performance thresholds** in **Section 2.0 Service Summary - Performance Thresholds Table** for the Facilities Service Area (referencing PWS Paragraphs F.1.x). These thresholds define acceptable performance levels, measured primarily through **Periodic Inspection (Monthly)** or **100% Inspection**, and represent the **SATISFACTORY level of performance**. They cover preventive maintenance (PM), inventory management, assessments, and corrective actions. Failure to meet these may trigger re-performance at no additional cost.

Key workload drivers include completing 95% of Priority 2A PM, submitting PM schedules within 30 days after Full Operational Capability (FOC) with twice-yearly updates, limiting late corrective actions to one per month, and maintaining high completeness/currency in facility assessments.

### Facilities Management Performance Objectives (PO-F1 to PO-F10)

| Performance Objective | PWS Paragraph | Threshold (Satisfactory Level) | Surveillance Method |
|-----------------------|---------------|--------------------------------|---------------------|
| **PO-F1**: Complete all Priority 2A Preventive Maintenance (PM) | F.1.1.3.2 | 95% of scheduled PM completed | Periodic Inspection (Monthly) |
| **PO-F2**: Submit all PM schedules for COR approval | F.1.3.1 | Not later than 30 calendar days after FOC; updated/validated twice a year | 100% Inspection |
| **PO-F3**: Initiate corrective action within 5 workdays for duplicate/excess facility records | F.1.2.1.2 | No more than 1 late initiation per month | Periodic Inspection (Monthly) |
| **PO-F4**: Inventory required systems for RPA Type B, S, or LS facilities | F.1.2.1.3 | No more than 3 missing/incomplete per month | Periodic Inspection (Monthly) |
| **PO-F5**: Update system inventories within 30 calendar days of change identification | F.1.2.2.2 | At least 95% of the time | Periodic Inspection (Monthly) |
| **PO-F6**: Correct inventory discrepancies within 10 workdays of identification | F.1.2.2.3 | At least 95% of the time | Periodic Inspection (Monthly) |
| **PO-F7**: Facility count assessment completeness | F.1.3.2 | At least 99% complete per month | Periodic Inspection (Monthly) |
| **PO-F8**: Facility square footage assessment completeness | F.1.3.2 | At least 99% complete per month | Periodic Inspection (Monthly) |
| **PO-F9**: Current facility condition assessments (facility count level) | F.1.3.3 | At least 90% each month | Periodic Inspection (Monthly) |
| **PO-F10**: Current facility condition assessments (facility square footage level) | F.1.3.3 | At least 90% each month | Periodic Inspection (Monthly) |

**Assessment Completeness Standard (F.1.3.2)**: If initial status is <80%, achieve ≥99% completeness in Base Year; maintain ≥99% monthly by facility count and square footage.

**Currency Standard (F.1.3.3.1)**: Assessments are "current" if conducted <5 years prior; achieve ≥90% currency in Base Year if initial <80%, then maintain ≥90% monthly at facility level (≥90% component-sections per component current).

### Additional Facilities Assessment Objectives (PO-F11 to PO-F15)

| Performance Objective | PWS Paragraph | Threshold (Satisfactory Level) | Surveillance Method |
|-----------------------|---------------|--------------------------------|---------------------|
| **PO-F11**: Monthly facility condition assessments (by count) | F.1.3.4.1 | ≥2% of BUILDER inventory per month | Periodic Inspection (Monthly) |
| **PO-F12**: Monthly facility condition assessments (by square footage) | F.1.3.4.1 | ≥2% of BUILDER inventory per month | Periodic Inspection (Monthly) |
| **PO-F13**: Point-in-time assessments post-request | F.1.3.4.4 | ≥95% within 30 calendar days | Periodic Inspection (Monthly) |
| **PO-F14**: Update component-section assessments post-work task | F.1.3.4.5 | ≥95% within 30 calendar days | Periodic Inspection (Monthly) |
| **PO-F15**: Correct facility/component quality problems | F.1.5 | ≥95% within 30 calendar days | Periodic Inspection (Monthly) |

### Customer Support and Work Execution Thresholds (F.1.1.x)

- **Service Calls**: 95% responded to and completed timely.
- **Priority 1 (Emergency)**: Respond within 1 hour; mitigate within 24 hours.
- **Priority 3A (High Sustainment)**: Respond within 1 hour (≤2 late/month); complete within 3 calendar days ≥95% (if parts on hand; procure within 1 business day).
- **Priority 3B**: Complete within 7 calendar days; ≥90% deferred work within 7 days of parts receipt.
- **Priority 3C**: Complete within 45 calendar days (if parts on hand).
- **PM Execution**: 95% of scheduled monthly PM; no task deferred/missed two consecutive months.
- **Base Permits**: Average 120/year; process developed within 15 days post-CTORD.

Monitoring includes **periodic inspections, 100% inspection, and customer feedback/complaints**. These thresholds ensure mission sustainment; deficiencies may lead to unsatisfactory performance discussions.

### References

* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.7s*

---

## Q4: Requirement Traceability

**Query (naive mode):** How do Section L submission instructions map to Section M evaluation criteria? Which instructions correspond to which evaluation factors?

### afcapv_bos_i_t4

## Section L/M Alignment Overview

Section L of the FOPR provides explicit submission instructions through **Table 1 (Proposal Organization Table)**, which defines the structure, titles, and page limits for proposal volumes. These instructions directly align with Section M evaluation criteria, creating a **one-to-one mapping** between submission sections and evaluated factors/subfactors. There are no orphan instructions (compliance-only items requiring minimal effort) or orphan criteria (hidden requirements) explicitly identified. Proposal resources should be allocated proportionally to evaluation emphasis, with **Subfactor 1.1 (TOMP)** receiving the most attention as it is the highest-weighted tradeoff factor.

To optimize, create a comprehensive L/M mapping before content development: identify direct correspondences, allocate pages/effort based on weights (e.g., TOMP at 20 pages reflects its superior importance), and ensure compliance is obvious using RFP section headings, bold discriminators, and page references.

## Specific Mapping of Instructions to Evaluation Factors

### Volume I - Factor 1: Technical Factor (Evaluated per Sections 9-10)
- **Subfactor 1.1: Task Order Management Plan (TOMP)** (Section L: 20-page limit)
  - **Direct Mapping**: Submission mirrors evaluation—provide TOMP (CDRL A002) expanding AFCAP V Management Plan, including on-site manager designation, subcontract details (hours/labor categories), staffing narrative/Org chart, Staffing Matrix (Attachment 5, separate file), mobilization schedule (milestones like 50%/100% USN deployment), and compliance with Foreign Clearance Guide/Host Nation requirements. Smaller fonts/tables allowed for schedules.
  - **Evaluation (Section M)**: Tradeoff factor, **significantly more important** than Cost; combined Technical/Risk rating per **Table 2** (Outstanding: multiple strengths, very low risk; Good: ≥1 strength, low risk; Acceptable: offsetting strengths/weaknesses, ≤moderate risk; Marginal: unoffset weaknesses, high risk; Unacceptable: deficiencies, un-awardable). Strengths exceed requirements with Government benefit; weaknesses/deficiencies increase risk.

- **Subfactor 1.2: Mission Essential Plan (MEP)** (Section L: 2-page limit)
  - **Direct Mapping**: Submit written plan for 30-day crisis continuity (e.g., personnel/resources acquisition, pandemic challenges, training, alerts, communication).
  - **Evaluation (Section M)**: **Acceptable/Unacceptable** per **Table 3** (Acceptable: meets requirements, adequate approach, low risk, no deficiencies; Unacceptable: deficiencies, un-awardable). Must be Acceptable for award eligibility; not tradeoff.

- **Subfactor 1.3: Combatting Trafficking in Persons (CTIP) Compliance Plan** (Section L: No page limit)
  - **Direct Mapping**: Provide FAR 52.222-50-compliant plan (awareness program, reporting process, recruitment/wage/housing plans, subcontractor monitoring); does not count toward page limits.
  - **Evaluation (Section M)**: **Acceptable/Unacceptable** per Table 3. Must be Acceptable; applies to primes/subcontractors.

- **Subfactor 1.4: Task Order Specific Quality Control Plan** (Section L: No page limit; CDRL A014)
  - **Direct Mapping**: Task order-specific plan with inspection methods, discrepancies, corrective actions; must not be generic/re-branded.
  - **Evaluation (Section M)**: **Acceptable/Unacceptable** per Table 3. Unacceptable plans (generic/lacking details) render proposal un-awardable.

**Note**: Any Unacceptable subfactor 1.2-1.4 makes entire proposal un-awardable. Cover letter required (contract number, understanding/commitment, no exceptions).

### Volume II - Factor 2: Cost (Section L: 2-page limit; per Attachment 2 CLIN Structure)
- **Direct Mapping**: Submit costs/units/totals in whole dollars (no decimals); include 6-month FAR 52.217-8 extension costs/fixed fee.
- **Evaluation (Section M)**: Reasonableness and USN Labor realism per FAR 15.404-1(d); probable cost + fixed fee = Total Evaluated Cost (TEC), key discriminator. Compared to IGE/other offers; may require additional data.

Proposals submitted as separate files (8.5x11", ≥12-pt font); best terms initial submission, interchanges possible.

## Compliance and Disqualification Risks
Verify: All Section L "shall" requirements addressed with page refs; page limits met; correct formats; no assumptions/exceptions. Use RFP headings, bold key points, numbered paragraphs for evaluator efficiency.

### References

* [2] 26R0013 - FOPR Israel BOS-I.pdf
* [4] govcon_regulations

*Response time: 0.5s*

### afcapv_bos_i_t5

## Section L/M Alignment Overview

Section L submission instructions, as outlined in the Fair Opportunity Proposal Request (FOPR) point 8 and Table 1 (Proposal Organization Table), specify the exact structure and page limits for proposal volumes. These directly map to Section M evaluation criteria detailed in FOPR points 9-11. The alignment is predominantly **one-to-one**, where each proposal volume/subfactor corresponds explicitly to an evaluation subfactor or factor. There are no apparent orphan instructions (compliance-only items without criteria) or orphan criteria (hidden requirements). Proposal resources should prioritize Subfactor 1.1 (20-page limit, most important in tradeoff) and ensure acceptability for Subfactors 1.2-1.4, as any Unacceptable rating renders the proposal un-awardable.

## Direct Mapping of Submission Instructions to Evaluation Criteria

- **Volume I - Factor 1 Technical, Subfactor 1.1: Task Order Management Plan (TOMP) (20 pages)**  
  Submission: Comprehensive TOMP (CDRL A002) mirroring AFCAP V Management Plan, including on-site manager designation, subcontract details (hours/labor categories), staffing narrative/organizational chart (page-limited), staffing matrix (separate, unlimited), mobilization schedule (milestones like 50%/100% USN deployment), equipment/labor/materials, Foreign Clearance/Host Nation compliance, licenses/permissions (unlimited pages). Allows 10-point font/tables/charts and 11x17 landscape.  
  Evaluation (Section M): Combined technical/risk rating per Table 2 (Outstanding/Good/Acceptable/Marginal/Unacceptable based on strengths/weaknesses/deficiencies/risk). Key discriminator in tradeoff process; more important than Cost. Strengths exceed requirements with government benefit; weaknesses increase risk; deficiencies are material failures.

- **Volume I - Factor 1 Technical, Subfactor 1.2: Mission Essential Plan (MEP) (2 pages)**  
  Submission: Written plan for 30-day crisis continuity (e.g., personnel/resources acquisition, pandemic challenges, training/readiness, alerts, communications). Becomes part of TO.  
  Evaluation (Section M): Acceptable/Unacceptable per Table 3. Acceptable if meets requirements with adequate approach/understanding, low risk, no deficiencies. Unacceptable if fails requirements or has deficiencies (un-awardable).

- **Volume I - Factor 1 Technical, Subfactor 1.3: Combatting Trafficking in Persons (CTIP) Compliance Plan (No Limit)**  
  Submission: FAR 52.222-50 compliant plan (awareness program, reporting process/hotline, recruitment/wage/housing plans, subcontractor monitoring). No page limit; becomes part of TO; applies to primes/subs.  
  Evaluation (Section M): Acceptable/Unacceptable per Table 3. Same criteria as Subfactor 1.2.

- **Volume I - Factor 1 Technical, Subfactor 1.4: Task Order Specific Quality Control Plan (No Limit, CDRL A014)**  
  Submission: TO-specific plan with inspection methods, areas, discrepancy identification/correction/recurrence prevention, examples (metrics/reports). Must be TO-specific, not generic/re-branded.  
  Evaluation (Section M): Acceptable/Unacceptable per Table 3. Same criteria as Subfactors 1.2-1.3. Plans lacking TO details deemed unacceptable.

- **Volume II - Factor 2: Cost (2 pages, per Attachment 2 CLIN Structure/Cost Schedule/Breakdown)**  
  Submission: Costs in whole dollars (no decimals), including 6-month FAR 52.217-8 extension; cover letter affirms understanding/no exceptions.  
  Evaluation (Section M): Cost realism (FAR 15.404-1(d)), reasonableness, USN labor realism → Total Evaluated Cost (TEC = probable cost + fixed fee). Key tradeoff discriminator vs. TOMP; compared to IGE/other offers. Sole source shifts to fair/reasonable analysis.

## Strategic Implications and Best Practices

Subfactors 1.2-1.4 are **threshold/pass-fail** (not tradeoff); must be Acceptable for eligibility. Allocate ~40%+ effort/pages to TOMP (highest weight). Use RFP section headings, bold discriminators, numbered paragraphs, compliance matrix with page refs for evaluator efficiency. No interchanges assumed initially, but possible; proposals must be best terms. Exclusions: Serco Inc./Huntington Ingalls subs prohibited.

### References

* [2] 26R0013 - FOPR Israel BOS-I.pdf
* [4] govcon_regulations

*Response time: 0.4s*

---

## Q5: Requirement Traceability

**Query (naive mode):** Which PWS requirements have associated evaluation factors that will be scored during source selection?

### afcapv_bos_i_t4

### Overview of Evaluation Factors
The source selection process for this Fair Opportunity Proposal Request (FOPR) uses a best value tradeoff approach based on two primary evaluation factors: **Factor 1 - Technical** (with Subfactor 1.1 significantly more important than Factor 2) and **Factor 2 - Cost**. Factor 1 includes four subfactors, but only **Subfactor 1.1: Task Order Management Plan (TOMP)** receives a combined **technical/risk rating** that is scored adjectivally (Outstanding, Good, Acceptable, Marginal, or Unacceptable). This subfactor directly assesses the offeror's approach to fulfilling **all PWS requirements** through a comprehensive plan (CDRL A002). Subfactors 1.2, 1.3, and 1.4 are evaluated on a binary **Acceptable/Unacceptable** basis, rendering the proposal unawardable if any is Unacceptable. Factor 2 (Cost) undergoes realism analysis but does not receive adjectival ratings.

### PWS Requirements Linked to Scored Evaluation (Subfactor 1.1 - TOMP)
The **TOMP** is the only scored subfactor and must "mirror and expand on the contractor’s AFCAP V Management Plan while demonstrating how the contractor will fulfill the specific requirements for this task order." It explicitly requires addressing **all PWS requirements** for operations at Hatzor Air Base (HAB) and Nevatim Air Base (NAB), including appendices, annexes, and attachments. Key PWS-linked elements scored under TOMP include:

- **Management and Staffing**: Designation of an empowered on-site manager(s), subcontract personnel/teaming details (company names, hours, labor categories), comprehensive staffing narrative/organizational chart (manpower by functional area, FTEs, management approach), and proof of personnel qualifications/experience per PWS (e.g., Site Manager experience, USN requirements for trades like Structures, HVAC).
- **Mobilization/Transition/Demobilization**: Detailed schedule (activities, relationships, durations, critical path, risks/mitigations) with milestones (e.g., 50%/100% USN deployment processing, workforce arrival on-site), compliance with Foreign Clearance Guide (FCG), Combatant Command/Host Nation requirements, CTORD by 30 September 2026.
- **Operational Compliance**: All equipment/labor/materials for housing/transportation/utilities/facilities/services, current FCG/Combatant Command/installation/Host Nation entry/access/operations requirements, permissions/licenses/approvals (with documentation not counting toward page limits).
- **PWS-Specific Execution**: Plans for all civil engineer/installation support services (e.g., facility maintenance, asset management, customer support per Annex F), including work prioritization (Table F-1), performance thresholds (e.g., PO-F1 to PO-F15), NFPA/UFC/Air Force publication compliance.

Proposals are scored based on **strengths** (exceeds requirements with government benefit), **weaknesses** (flaws increasing risk), and **deficiencies** (material failures), with risk assessed for schedule disruption, performance degradation, oversight needs, or unsuccessful performance. Outstanding requires multiple strengths and very low risk; Good requires at least one strength and low risk.

### Non-Scored PWS-Linked Evaluations (Acceptable/Unacceptable)
These must be Acceptable to be eligible but are not adjectivally scored:
- **Subfactor 1.2 (MEP)**: Strategy for 30-day crisis continuity (e.g., personnel/resources acquisition, pandemic challenges, training, alerts), tied to PWS mission sustainment.
- **Subfactor 1.3 (CTIP Plan)**: FAR 52.222-50 compliance (awareness, reporting, recruitment/wages/housing, subcontractor monitoring), applicable to all PWS supplies/services.
- **Subfactor 1.4 (Quality Control Plan, CDRL A014)**: TO-specific inspections/metrics/reports/discrepancy correction, non-generic plans.

### Cost Factor (Not Adjectival but Key Discriminator)
Evaluated for realism (FAR 15.404-1(d)), understanding of requirements, consistency with technical proposal, yielding Total Evaluated Cost (TEC). Includes 6-month option costs (FAR 52.217-8). Compared to IGE or other techniques; most advantageous tradeoff considers TEC alongside Technical.

No other PWS requirements (e.g., detailed performance objectives like facility assessments, work prioritization, CDRLs beyond those listed) have direct scored evaluation factors; compliance is demonstrated via TOMP.

### References
* [2] 26R0013 - FOPR Israel BOS-I.pdf
* [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.3s*

### afcapv_bos_i_t5

### Evaluation Factors in Source Selection

The source selection process for this Fair Opportunity Proposal Request (FOPR) uses a best value tradeoff approach between **Technical Subfactor 1.1 – Task Order Management Plan (TOMP)** and **Factor 2 – Cost**. Technical Subfactor 1.1 is more important than Cost. Subfactors 1.2, 1.3, and 1.4 under Factor 1 (Technical) are evaluated on an **Acceptable/Unacceptable** basis only and are not part of the tradeoff process. Any Unacceptable rating in these subfactors renders the entire proposal unawardable. Only proposals rated Acceptable in Subfactors 1.2–1.4 proceed to tradeoff evaluation.

"Scored" evaluation refers to adjectival technical/risk ratings (Outstanding, Good, Acceptable, Marginal, Unacceptable) applied to Subfactor 1.1 via tradeoff analysis. These ratings are based on strengths (exceeding requirements with government benefit), weaknesses (flaws increasing risk), deficiencies (material failures), and overall risk of unsuccessful performance. Subfactor 1.1 directly ties to PWS requirements by requiring a TOMP that "mirrors and expands on the contractor’s AFCAP V Management Plan while demonstrating how the contractor will fulfill the specific requirements for this task order," addressing operations at Hatzor Air Base (HAB) and Nevatim Air Base (NAB).

### PWS Requirements Associated with Scored Evaluation (Subfactor 1.1 – TOMP)

The following PWS requirements are associated with the scored Subfactor 1.1 (20-page limit, CDRL A002). The TOMP must explicitly demonstrate fulfillment, including discriminators for strengths:

- **Site Operations and Management**: Designation of an empowered on-site manager(s) to make decisions and direct subcontractors; all requirements for operation at HAB and NAB sites/functions per PWS, appendices, annexes, and attachments.
- **Resources and Support**: All equipment, labor (including leave schedules and coverage), labor hours, materials for housing, transportation, utilities, facilities, services, and support to designated force.
- **Compliance and Access**: Current Foreign Clearance Guide, Combatant Command, installation, and Host Nation requirements for entry, access, and operations; permissions, licenses, approvals, plans to obtain licenses, process milestones to meet Contractor Task Order Responsibility Date (CTORD) of 30 September 2026.
- **Mobilization, Transition, and Demobilization**: Detailed schedule with activities, relationships, durations, critical path, risks, mitigations; compliance with travel restrictions; timelines for 50%/100% U.S. National (USN) deployment processing and full workforce arrival on-site; activation, subcontracting, transportation, logistical support, surveying, site work, site visits.
- **Staffing**: Comprehensive staffing narrative and organizational chart accounting for manpower by functional area, full-time equivalents (FTEs), labor hours; management approach; demonstration that personnel meet PWS minimum qualifications (e.g., Site Manager/Alternate with relevant experience; USN trades like Structures, HVAC with 5+ years field experience; Host Nation Coordinators fluent in Hebrew/English with IDF level 6 clearance). Separate Staffing Matrix (Attachment 5, no page limit) details personnel types (USN/Local National/Other Country National), hours, locations, totals per service area/period.

These elements allow for strengths via exceeding requirements (e.g., innovative risk mitigations, superior staffing), directly impacting the scored rating.

### Threshold (Non-Scored) PWS-Associated Evaluations

For completeness, the following PWS-related plans are evaluated Acceptable/Unacceptable (not scored in tradeoff) but must pass for eligibility:

- **Subfactor 1.2 – Mission Essential Plan (MEP, 2-page limit)**: Strategy to continue mission essential services during crisis (up to 30 days), addressing personnel/resources acquisition, pandemic challenges, training, alerts, communications.
- **Subfactor 1.3 – Combating Trafficking in Persons (CTIP) Compliance Plan (no limit)**: Meets FAR 52.222-50(h)(3) minimums (awareness program, reporting process, recruitment/wage/housing plans, subcontractor monitoring).
- **Subfactor 1.4 – Task Order Specific Quality Control Plan (no limit, CDRL A014)**: TO-specific inspections, discrepancy identification/correction/preclusion; unacceptable if generic or rebranded from basic contract plan.

**Factor 2 – Cost** (2-page limit, Attachment 2 CLIN structure) undergoes cost realism analysis per FAR 15.404-1(d) for probable cost/Total Evaluated Cost (TEC), reasonableness, consistency with technical proposal; includes 6-month option costs per FAR 52.217-8. TEC is a key discriminator but separate from PWS technical requirements.

No other PWS requirements (e.g., facilities management per Annex F, performance thresholds like 95% PM completion) receive direct scored evaluation; they are addressed via TOMP or threshold plans.

### References

- [2] 26R0013 - FOPR Israel BOS-I.pdf
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.5s*

---

## Q6: Document Hierarchy

**Query (naive mode):** What is the organizational structure of this RFP? List the major sections and their parent-child relationships.

### afcapv_bos_i_t4

### Proposal Organizational Structure (Per FOPR Table 1)

The RFP, specifically the Fair Opportunity Proposal Request (FOPR) for the Israel BOS-I task order, outlines the required proposal organization in Paragraph 8 via **Table 1**. Proposals must be structured into two volumes, submitted as separate files using 12-point font on 8.5” x 11” paper. A cover letter is required for each volume, including the offeror’s contract number, statement of understanding of requirements, commitment to performance standards, and no exceptions taken. **Volume I** focuses on **Factor 1: Technical Factor**, which is the most important evaluation factor and contains four subfactors with specified page limits. **Volume II** addresses **Factor 2: Cost**.

### Factor and Subfactor Relationships

- **Volume I: Factor 1 - Technical Factor** (evaluated using combined technical/risk ratings for Subfactor 1.1 and risk ratings for Subfactors 1.2-1.4; any Unacceptable subfactor renders the proposal unawardable)
  - **Subfactor 1.1: Task Order Management Plan (TOMP)** (20-page limit; fulfills CDRL A002; must be task order-specific, not generic)
  - **Subfactor 1.2: Mission Essential Plan (MEP)** (2-page limit)
  - **Subfactor 1.3: Combatting Trafficking In Persons (CTIP) Compliance Plan** (no page limit)
  - **Subfactor 1.4: Task Order Specific Quality Control Plan** (no page limit; fulfills CDRL A014; must be task order-specific to avoid Unacceptable rating)

- **Volume II: Factor 2 - Cost** (2-page limit; follows CLIN Structure, Cost Schedule, and Cost Breakdown in Attachment 2; evaluated via cost realism analysis per FAR 15.404-1(d), resulting in Total Evaluated Cost (TEC); includes proposed costs/fixed fee for 6-month extension per FAR 52.217-8)

### Additional FOPR Sections and Instructions

The FOPR includes procedural sections following the proposal organization and evaluation criteria (e.g., Paragraphs 11-16). Key parent-child elements include:
- **Evaluation Criteria** (preceding Factor 2 details; defines strengths, weaknesses, deficiencies, and ratings: Outstanding, Good, Acceptable, Marginal, Unacceptable per Table 2)
  - **Factor 1 Technical** (parent to subfactors)
  - **Factor 2 Cost** (includes realism analysis, IGE comparison, optional data requests)
- **Submission and Compliance** (Paragraphs 13-16)
  - Questions and submissions via specified DOD SAFE/email addresses
  - Required representations (Attachment 3)
  - Exclusions (Paragraph 12: Serco Inc. and Huntington Ingalls Industries subsidiaries barred as subcontractors)
- **Attachments** (1: PWS; 2: CLIN Structure/Cost Schedule; 3: FAR Provisions/Clauses; 4: Questions Template; 5: Staffing Matrix Template)

Proposals must address all Section L 'shall' requirements with page references, adhere to page limits, and use specified formats to avoid disqualification.

### References

- [2] 26R0013 - FOPR Israel BOS-I.pdf
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.5s*

### afcapv_bos_i_t5

## RFP Organizational Structure Overview

The RFP, structured as a Fair Opportunity Proposal Request (FOPR) for the Israel BOS-I task order under AFCAP, outlines a clear proposal organization in **Table 1 - Proposal Organization Table** (located in the FOPR main body, point 8). This defines the required volumes and sections for submissions, with specified page limits. The structure emphasizes two primary volumes, with **Volume I** focusing on technical factors and subfactors, and **Volume II** on cost. Proposals must adhere to these for compliance.

### Proposal Volumes and Factors (Per Table 1)
- **Volume I** (Technical)
  - **Factor 1: Technical Factor**
    - **Subfactor 1.1**: Task Order Management Plan (TOMP) – 20 pages (CDRL A002)
    - **Subfactor 1.2**: Mission Essential Plan (MEP) – 2 pages
    - **Subfactor 1.3**: Combatting Trafficking In Persons (CTIP) Compliance Plan – No Limit
    - **Subfactor 1.4**: Task Order Specific Quality Control Plan – No Limit (CDRL A014; must be task order-specific, not generic)
- **Volume II** (Cost/Price)
  - **Factor 2: Cost** – 2 pages (references Attachment 2: CLIN Structure, Cost Schedule, Cost Breakdown)

## Evaluation Factors and Criteria (Sections 10-11)
Evaluation follows **Table 2: Technical/Risk Ratings** (Outstanding, Good, Acceptable, Marginal, Unacceptable), applied differently by subfactor:
- **Factor 1: Technical** (highest precedence; any Unacceptable subfactor renders proposal un-awardable)
  - **Subfactor 1.1 (TOMP)**: Combined technical/risk rating (strengths exceed requirements for benefit; weaknesses increase risk; deficiencies are material failures)
  - **Subfactors 1.2, 1.3, 1.4**: Risk rating (low/moderate/high/unacceptable risk of disruption, oversight needs, or failure)
- **Factor 2: Cost** (realism analysis per FAR 15.404-1(d); Total Evaluated Cost (TEC) as key discriminator; includes 6-month extension per FAR 52.217-8)

## Additional FOPR Sections (Points 12-16)
- **Point 12**: Subcontractor Exclusions (Serco Inc., Huntington Ingalls Industries, subsidiaries like Camber Corp.)
- **Point 13/14**: Submission Instructions/Questions (via DOD SAFE/email to specified addresses, e.g., Samantha Schmidt, Calvin Mason)
- **Point 15**: Representations (complete Attachment 3: Representation by Corporations)
- **Point 16**: Contact (SSgt Charmaine Brown)

## Attachments (5 Total)
- **Attachment 1**: PWS dated 6 April 2026 (includes Appendix E: CDRL A001-A016 with distribution tables; Section B: Publications/Forms; Section F: Work Prioritization (Table F-1); Annexes F-2/F-3 Equipment Details, F-4/F-5 PMOSS Reports; Annex H1: DFAC Services (e.g., H1.5.4-H1.5.8))
- **Attachment 2**: CLIN Structure, Cost Schedule dated 9 April 2026
- **Attachment 3**: Additional FAR Provisions and Clauses dated 6 April 2026
- **Attachment 4**: Questions Template Structure
- **Attachment 5**: Staffing Matrix Template

## General Compliance Guidance (Section L/M Alignment)
References emphasize mapping **Section L** (instructions, 'shall' requirements with page refs) to **Section M** (evaluation criteria), prioritizing high-weight factors (e.g., 40% factor gets ~40% effort). Top risks include page limits, formats (PDF/Word/Excel), and compliance matrices.

### References
- [2] 26R0013 - FOPR Israel BOS-I.pdf
- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
- [3] lessons_learned
- [4] govcon_regulations

*Response time: 0.3s*

---

## Q7: Cross-Document

**Query (naive mode):** What is the relationship between the PWS, the evaluation factors, and the submission instructions? How do they connect?

### afcapv_bos_i_t4

## Relationship Between PWS, Evaluation Factors, and Submission Instructions

The **Performance Work Statement (PWS)** serves as the foundational document outlining the specific requirements, performance objectives, deliverables, and standards for the task order. It details workload drivers, such as facility assessments, preventive maintenance thresholds (e.g., 95% completion of scheduled PM), prioritization of work tasks (e.g., Emergency Work as Priority 1), and compliance with publications like UFCs, NFPA standards, and Air Force Instructions. Key PWS elements include CDRLs (e.g., A002 for Task Order Management Plan (TOMP), A014 for Task Order Specific Quality Control Plan), which become proposal deliverables.

## Connection to Evaluation Factors

The **evaluation factors** in the Fair Opportunity Proposal Request (FOPR) directly reference and assess compliance with PWS requirements through a structured process. Factor 1 (Technical) includes four subfactors:
- **Subfactor 1.1 (TOMP)**: Most important for tradeoff; proposals must mirror and expand the AFCAP V Management Plan to address PWS specifics like on-site manager designation, subcontracting, staffing narrative/organizational chart/matrix (Attachment 5), mobilization schedule (with milestones like 50% USN deployment processing), Foreign Clearance Guide compliance, and all equipment/labor/materials for sites (Hatzor and Nevatim Air Bases). Evaluated with combined technical/risk ratings (Outstanding to Unacceptable per Table 2), focusing on strengths, weaknesses, deficiencies, and risk of unsuccessful performance. Fulfills CDRL A002.
- **Subfactors 1.2 (Mission Essential Plan - MEP, 2 pages)**, **1.3 (CTIP Compliance Plan, no limit)**, and **1.4 (Task Order Specific Quality Control Plan, no limit)**: Evaluated Acceptable/Unacceptable per Table 3 (low risk/no deficiencies for Acceptable). MEP addresses crisis continuity (e.g., 30-day sustainment); CTIP covers awareness, reporting, recruitment/housing plans per FAR 52.222-50; Quality Control must be task order-specific (not generic), with inspection methods and metrics (CDRL A014). Any Unacceptable subfactor renders the proposal unawardable.

Factor 2 (Cost): Less important than Subfactor 1.1; evaluated for realism (FAR 15.404-1(d)), reasonableness, USN labor, yielding Total Evaluated Cost (TEC). Includes 6-month option per FAR 52.217-8. Award uses tradeoff: best value integrating Technical (TOMP) and Cost, with Technical more important.

## Connection to Submission Instructions

**Submission instructions** (FOPR Paragraph 8, Table 1) mandate proposal structure to align PWS requirements with evaluation factors:
- **Format**: 8.5”x11” paper, ≥12-point font (10-point tables/figures ok), separate files per section/volume, cover letter with contract number/understanding/no exceptions. Cost Schedule (Attachment 2) in whole dollars.
- **Page Limits** (Volume I Technical, Volume II Cost):
  | Section | Reference | Title | Page Limit |
  |---------|-----------|-------|------------|
  | Volume I | Factor 1 | Technical Factor | - |
  | | Subfactor 1.1 | TOMP | 20 |
  | | Subfactor 1.2 | MEP | 2 |
  | | Subfactor 1.3 | CTIP Compliance Plan | No Limit |
  | | Subfactor 1.4 | Task Order Specific Quality Control Plan | No Limit |
  | Volume II | Factor 2 | Cost (Attachment 2) | 2 |

Proposals must avoid assumptions/exceptions (address via questions by 17 April); due 11 May 2026 via DOD SAFE/email. Staffing Matrix (Attachment 5) separate, no page limit impact.

## How They Connect Overall

The PWS defines **what** must be performed (requirements/CDRLs). Submission instructions specify **how** to organize/propose it (volumes/subfactors/page limits). Evaluation factors determine **how it will be judged** (tradeoff for TOMP/Cost; pass/fail for others), ensuring proposals demonstrate PWS compliance, low risk, and discriminators. Non-compliance (e.g., generic plans, page violations) risks Unacceptable ratings or disqualification. Interchanges possible but initial proposals should be best terms.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
- [2] 26R0013 - FOPR Israel BOS-I.pdf
- [3] evaluation_methodology

*Response time: 0.5s*

### afcapv_bos_i_t5

### Overview of the Relationship
The Performance Work Statement (PWS) serves as the foundational document outlining the specific requirements for the task order, including operational needs, deliverables, personnel qualifications, and compliance standards for providing Base Operating Support-Installation Services at Hatzor Air Base (HAB) and Nevatim Air Base (NAB), Israel. The evaluation factors directly assess how well proposals demonstrate the ability to meet these PWS requirements, with a focus on key plans and cost realism. Submission instructions specify the exact format, organization, and page limits for proposals, ensuring responses are structured to align with the evaluation factors and address PWS mandates. This creates a direct linkage: PWS requirements inform the evaluation criteria, which in turn dictate the proposal structure required by submission instructions.

### Role of the PWS
The PWS (Attachment 1) details the scope of work, such as task order management, mobilization/transition schedules, staffing plans, mission essential services during crises, CTIP compliance, and quality control specific to the task order sites. It includes CDRLs like A002 (Task Order Management Plan - TOMP), A014 (Task Order Specific Quality Control Plan), and references to standards (e.g., Air Force publications, NFPA, UFCs). These elements form the baseline that proposals must fulfill, with specifics like empowering an on-site manager, addressing Foreign Clearance Guide requirements, and providing staffing matrices.

### Evaluation Factors and Their Tie to the PWS
Evaluation Factor 1 (Technical) is divided into subfactors that mirror PWS deliverables:
- **Subfactor 1.1 (TOMP, 20-page limit)**: Rated on a combined technical/risk scale (Outstanding to Unacceptable using Table 2). Must expand the contractor's AFCAP V Management Plan to address **all PWS requirements**, including mobilization schedules (e.g., 50%/100% workforce milestones), staffing narrative/organizational chart/matrix (Attachment 5), and site-specific operations (CDRL A002). Strengths exceed requirements with government benefits; weaknesses/deficiencies increase performance risk.
- **Subfactors 1.2 (MEP, 2 pages), 1.3 (CTIP Compliance Plan, no limit), 1.4 (Quality Control Plan, no limit)**: Pass/fail (Acceptable/Unacceptable using Table 3). MEP covers crisis continuity (up to 30 days); CTIP per FAR 52.222-50; Quality Control must be task order-specific (not generic), with inspection methods (CDRL A014). Any Unacceptable renders the proposal unawardable.
- **Factor 2 (Cost, 2 pages)**: Cost realism analysis per FAR 15.404-1(d), yielding Total Evaluated Cost (TEC). Includes 6-month option costs (FAR 52.217-8).

Award uses tradeoff: Subfactor 1.1 (TOMP) **more important than Cost**. All technical subfactors tie back to PWS fulfillment.

### Submission Instructions and Alignment
Section 8 and Table 1 mandate proposal organization by **Volume I (Technical Factor/Subfactors)** and **Volume II (Cost per Attachment 2)**, with 12-point font (10-point tables ok), separate files per volume, and specifics like whole-dollar costs, no assumptions/exceptions. Page limits enforce focus on high-importance areas (e.g., 20 pages for TOMP). Cover letter affirms understanding of requirements without exceptions. Staffing Matrix (Attachment 5) is separate, not counting toward TOMP pages. This structure ensures proposals directly map to evaluation subfactors, which evaluate PWS compliance (e.g., TOMP headings mirror PWS sections like mobilization, staffing).

### How They Connect
- **PWS → Evaluation**: Subfactors require explicit demonstration of PWS compliance (e.g., TOMP "shall address all requirements... listed in the PWS"; Quality Plan "fulfil CDRL A014" from PWS).
- **Evaluation → Submission**: Table 1 organizes volumes/subfactors identically to evaluation (e.g., Subfactor 1.1 = TOMP section), with page budgets proportional to importance.
- **Integrated Flow**: Offerors map PWS instructions to proposal sections for obvious compliance, enabling evaluators (reviewing 5-15 proposals) to score via citations. Non-compliance (e.g., generic plans) leads to weaknesses/deficiencies.

This alignment optimizes for best value tradeoff, prioritizing TOMP excellence over lowest cost.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
- [2] 26R0013 - FOPR Israel BOS-I.pdf

*Response time: 0.3s*

---

## Q8: Cross-Document

**Query (naive mode):** What organizations or personnel types are mentioned and what are their contractual responsibilities?

### afcapv_bos_i_t4

### Government Personnel and Organizations

Several government roles and organizations are specified as key recipients of deliverables and points of coordination in the Performance Work Statement (PWS). The **772 ESS/PKD Procuring Contracting Officer (PCO)** receives 1 copy of various CDRL deliverables (e.g., Task Order Management Plan, Monthly Status Reports, Flash Reports, Quality Control Plans) and is responsible for approving Task Order Specific Quality Control Plans with proposals, incorporating inventories into Task Orders, and handling modifications. The **Administrative Contracting Officer (ACO)** receives 1 copy of deliverables such as Weekly Reports of Deployed Personnel, GFP Reports, and is involved in approvals for demobilization plans, property disposition instructions, revisions to Quality Control Plans, and receipt of jointly signed inventories within 5 calendar days.

The **Contracting Officer’s Representative (COR)** receives 1 copy of deliverables including Installation Specific Reporting, conducts joint 100% inventories of GFP/CMGP (initial within 30 days after CTORD, annual, final 30 days prior to TO end), accepts Task Order Specific Quality Control Plans, verifies fitness for duty certifications, and coordinates service disruptions and work requests. The **AFCEC/CXAA Program Manager (PM)** receives 1 copy of reports like Key Personnel Security Clearance Verifications and is consulted for TOMP approvals. **USERS (AFCENT/A1, A4, or A7)** receive 3 copies of most CDRL deliverables (e.g., Monthly Status Reports, GFP Reporting) for oversight.

Resource allocations include 1 ACO, 1 COR, 1 AFCEC/CXAA PM, and 3 USERS. In the Fair Opportunity Proposal Request (FOPR), contacts include **Ellery English** (772 ESS/PKD Section Chief, ellery.english@us.af.mil), **SSgt Charmaine Brown** (charmaine.brown.1@us.af.mil), **Samantha Schmidt** (samantha.schmidt.4@us.af.mil), and **Calvin Mason** (calvin.mason.3.ctr@us.af.mil) for submissions and questions.

### Contractor Personnel Types

Contractor key personnel include the **Site Manager (SM)**, who oversees all operations, scheduling, supervision, quality control, and must be on-site or available within 4 hours; holds full authority and attends required meetings. The **Alternate Site Manager (ASM)** (US National, minimum 6 years experience) acts in SM's absence with similar responsibilities. **Host Nation Coordinator(s)/Translator(s)** must be Israeli citizens fluent in Hebrew/English with IDF level 6 security clearance.

Technical roles require US Nationals with minimum 5 years field experience: **Structures**, **HVAC**, **Plumbing w/Fire Suppression**, **Electrician w/Fire Alarm**, **Construction Management** (these may fill SM/ASM roles if qualified). Key USN personnel need SECRET clearance; others vetted per HSPD-12 or Tier 1. All USNs require Geneva Convention CAC. Local Nationals (LN) are vetted per base procedures and AFCAP V Basic Contract. The Contractor provides cellular phones for SM/ASM and ensures training/compliance.

Contractors manage subcontractors, obtain badges/permits, and adhere to monitoring/escort rules for LNs.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
- [2] 26R0013 - FOPR Israel BOS-I.pdf

*Response time: 0.4s*

### afcapv_bos_i_t5

### Government Personnel and Organizations

Several government roles and organizations are specified as recipients of deliverables, approvers, coordinators, and overseers in the Performance Work Statement (PWS). The **Administrative Contracting Officer (ACO)** receives 1 copy of various CDRL deliverables (e.g., Monthly Status Reports [A004], Task Order Management Plan [A002]), conducts inventories jointly with the Contractor, approves updates like the demobilization plan, and handles property disposition instructions. The ACO also reviews personnel qualifications, receives notifications of key personnel departures within 24 hours, and manages financial liability for property loss.

The **Contracting Officer’s Representative (COR)** similarly receives 1 copy of CDRL deliverables, coordinates service disruptions, approves schedules and plans (e.g., Facility Maintenance Plan, bench stock list), conducts joint inventories of Government Furnished Property (GFP)/Contractor Managed Government Property (CMGP), and verifies compliance with requirements like work orders and quality control. The COR directs provision of Contractor Acquired Property (CAP) office trailers if Government Furnished Facilities (GFF) are unsuitable and handles fitness for duty certifications.

The **AFCEC/CXAA Program Manager (PM)** receives 1 copy of CDRL reports and serves as a key stakeholder for approvals, such as Task Order Management Plan (TOMP) updates. **USERS (AFCENT/A1, A4, or A7)** receive 3 copies of deliverables collectively, representing end-users for reports on deployed personnel, situation updates, and property.

The **Procuring Contracting Officer (PCO)** (772 ESS/PKD) receives 1 copy of deliverables, approves TOMP and Quality Control Plan (QCP) revisions, and incorporates inventories into Task Orders (TOs). **Samantha Schmidt** and **Calvin Mason** are listed as submission addresses for FOPR information and questions. **Ellery English** (772 ESS/PKD Section Chief) and **SSgt Charmaine Brown** serve as points of contact for FOPR questions.

### Contractor Key Personnel and Types

Contractor personnel types are detailed with qualifications and responsibilities. The **Site Manager (SM)** oversees all TO operations, schedules personnel, supervises work, ensures quality control, maintains on-site presence or 4-hour availability, and attends meetings. The SM must have relevant experience and may support service delivery directly.

The **Alternate Site Manager (ASM)** acts in the SM's absence with similar authority for operations, scheduling, supervision, and quality control; must be a US National (USN) with at least 6 years of experience. **Host Nation Coordinator(s)/Translator(s)** are Israeli citizens fluent in Hebrew/English with IDF level 6 security clearance, supporting coordination.

Technical roles like **Structures, HVAC, Plumbing w/Fire Suppression, Electrician w/Fire Alarm, Construction Management** personnel are USNs with minimum 5 years field experience; these may fill SM/ASM roles if qualified. **Key USN personnel** require SECRET clearance; other USNs need HSPD-12 vetting or Tier 1 investigation and Geneva Convention CAC. **Local Nationals (LNs)** are vetted per AFCAP V Basic contract and base procedures, subject to monitoring/escort.

**Contractor field managers** utilize the AFCAP Property Administrator for recordkeeping and must schedule training within 90 days of Period of Performance (PoP) start.

### Additional Entities

**Israel Defense Force (IDF)** provides context for security clearances and approvals (e.g., digging permits). **AFCENT** stakeholders coordinate TOs. The Contractor manages subcontractors, ensuring oversight reported in Monthly Status Reports [A004].

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx
- [2] 26R0013 - FOPR Israel BOS-I.pdf

*Response time: 0.4s*

---

## Q9: Strategic

**Query (naive mode):** What are the key discriminators for winning this competition? What aspects will the government emphasize in evaluation?

### afcapv_bos_i_t4

### Evaluation Framework and Emphasis
The government will evaluate proposals using a **best value tradeoff** process based on two primary factors: **Factor 1 - Technical** (with Subfactor 1.1 Task Order Management Plan (TOMP) as the key tradeoff element) and **Factor 2 - Cost**. Technical Subfactor 1.1 TOMP is **more important** than Cost. The award will go to the offeror providing the **most advantageous combination** via an integrated assessment. Subfactors 1.2 (Mission Essential Plan), 1.3 (Combating Trafficking in Persons (CTIP) Compliance Plan), and 1.4 (Task Order Specific Quality Control Plan) are **pass/fail** (Acceptable/Unacceptable). Any Unacceptable rating here renders the entire proposal unawardable.

Technical Subfactor 1.1 TOMP receives a **combined technical/risk rating** (Outstanding, Good, Acceptable, Marginal, Unacceptable). Outstanding requires an exceptional approach with multiple strengths and very low risk; Good needs at least one strength and low risk; Acceptable has offsetting strengths/weaknesses with moderate risk at worst. Strengths (exceeding requirements with government benefits), weaknesses (flaws increasing risk), and deficiencies (material failures) drive ratings. The government emphasizes a TOMP that **mirrors and expands the AFCAP V Management Plan**, demonstrates fulfillment of PWS requirements, includes an empowered on-site manager, identifies subcontractors/teaming (with hours/labor categories), addresses site operations/Foreign Clearance Guide/Host Nation requirements, provides mobilization/demobilization schedules (with milestones like 50%/100% personnel deployment), and includes a staffing narrative/organizational chart plus Staffing Matrix.

### Key Discriminators for Winning
To win, proposals must secure a high TOMP rating (ideally Outstanding/Good) through **documented strengths** that exceed requirements, offer quantified benefits, minimize risk, and align with criteria—generic claims without proof fail. Discriminators must be validated as **TRUE** (provable), **RELEVANT** (addresses criteria/hot buttons), **UNIQUE** (not credibly claimable by competitors), **BELIEVABLE** (fits track record), and **SUSTAINABLE** (maintainable through execution). Strategies include exceeding metrics (e.g., 99.9% availability vs. 99%), innovative low-risk/cost approaches, exceptional past performance, and beneficial value-adds. Use **ghosting** to highlight strengths indirectly (e.g., "Day 1 capability without learning curve risks") without naming competitors.

Cost (Factor 2) is evaluated for **reasonableness** and **USN labor realism** via analysis per FAR 15.404-1(d), yielding **Total Evaluated Cost (TEC)** (probable cost + fixed fee). Competitive TEC discriminates in tradeoff, compared to Independent Government Estimate (IGE) or others. Include 6-month extension costs per FAR 52.217-8. Allocate resources proportionally: prioritize TOMP (most pages/writers) over cost.

**Compliance is critical**—use RFP section numbers as headings, bold discriminators, number paragraphs, provide page references, avoid fluff. Pass/fail subfactors demand specificity: MEP for 30-day crisis continuity; CTIP per FAR 52.222-50 (awareness, reporting, recruitment/housing plans); task order-specific Quality Control (not generic, with inspection methods/metrics).

### Proposal Strategy Alignment
Make evaluator efficiency easy: front-load key points, use call-outs/bold for strengths, compliance matrix with page refs. For TOMP, substantiate business ability in Israel (permissions/licenses/plans), detailed mobilization (critical path/risks/mitigation), staffing sufficiency for PWS. False discriminators erode credibility.

### References
- [2] 26R0013 - FOPR Israel BOS-I.pdf
- [6] evaluation_methodology
- [5] capture_management
- [4] lessons_learned

*Response time: 0.4s*

### afcapv_bos_i_t5

### Evaluation Framework and Award Basis
The government will conduct a best value tradeoff evaluation between **Factor 1: Technical Subfactor 1.1 – Task Order Management Plan (TOMP)**, which is **more important than Factor 2: Cost**. The award will go to the offeror providing the most advantageous combination based on an integrated assessment. Subfactors 1.2 (Mission Essential Plan), 1.3 (Combating Trafficking in Persons Compliance Plan), and 1.4 (Task Order Specific Quality Control Plan) are evaluated pass/fail as **Acceptable/Unacceptable**—any Unacceptable rating renders the proposal un-awardable. TOMP receives a combined technical/risk rating (Outstanding, Good, Acceptable, Marginal, Unacceptable) based on strengths (aspects exceeding requirements with government benefit), weaknesses (flaws increasing risk), and deficiencies (material failures). Cost undergoes realism analysis per FAR 15.404-1(d), yielding Total Evaluated Cost (TEC) as a key discriminator in a competitive environment.

### Key Discriminators in TOMP (Subfactor 1.1)
To achieve **Outstanding** (multiple strengths, very low risk) or **Good** (at least one strength, low risk) ratings, proposals must exceed requirements with **quantified benefits, minimal risk, innovative approaches, and exceptional evidence**. The TOMP (20-page limit) must mirror and expand the offeror's AFCAP V Management Plan for this task order, covering:
- Empowered on-site manager(s) directing subcontractors.
- All subcontract personnel/teaming partners identified (company name, hours, labor category).
- Compliance with PWS, appendices, Foreign Clearance Guide, Combatant Command, installation, and Host Nation requirements (permissions, licenses, plans).
- Mobilization schedule with activities, critical path, risks/mitigations, milestones (e.g., 50%/100% USN deployment processing and workforce on-site), transition (5 days, CTORD 30 Sep 2026), demobilization.
- Staffing narrative/organizational chart (FTEs by functional area, management approach, PWS qualifications) and separate Staffing Matrix (Attachment 5).

**Strength-generating elements** include exceeding metrics (e.g., faster mobilization), innovative risk reduction, provable past achievements aligned to criteria, and beneficial value-adds. Generic claims fail to generate documented strengths.

### Cost Factor Emphasis and Realism
**Factor 2: Cost** (2-page limit + Attachment 2) focuses on reasonableness, USN labor realism, and TEC (probable cost + fixed fee). Proposals must reflect requirements understanding and technical consistency. Include 6-month extension costs (FAR 52.217-8). Government compares TECs to Independent Government Estimate (IGE) or uses other techniques. Competitive, realistic TEC discriminates in tradeoff, but technical superiority justifies premium pricing.

### Proposal-Winning Strategies from Evaluator Perspective
Evaluators review 5-15 proposals over 2-4 weeks while working regular duties, using sheets with criteria and requiring proposal citations. **Make compliance obvious**: Use RFP section headings, front-load key points, bold discriminators/call-out boxes, compliance matrix with page refs, numbered paragraphs, no fluff—focus on facts/evidence. Validate discriminators: **TRUE** (provable), **RELEVANT** (criteria/hot buttons), **UNIQUE** (competitors can't claim), **BELIEVABLE** (track record), **SUSTAINABLE** (through execution). Allocate resources to highest-weighted factors (TOMP 1st).

### Pass/Fail Subfactors Criticality
- **1.2 MEP**: Strategy for 30-day crisis continuity (personnel/resources, challenges like pandemics, training, alerts, communications).
- **1.3 CTIP**: FAR 52.222-50 plan (awareness, reporting, recruitment/wages, housing, subcontractor monitoring)—no page limit.
- **1.4 Quality Control**: TO-specific (inspections, discrepancies, metrics)—generic/re-branded plans unacceptable; fulfills CDRL A014.

Proposals must be initial best terms; interchanges possible but not guaranteed. No assumptions/exceptions allowed.

### References
- [1] 26R0013 - FOPR Israel BOS-I.pdf
- [6] evaluation_methodology
- [4] lessons_learned
- [5] capture_management

*Response time: 0.3s*

---

## Q10: Compliance

**Query (naive mode):** What mandatory clauses, regulations, or standards must the contractor comply with?

### afcapv_bos_i_t4

## Overview of Mandatory Compliance Requirements

The Performance Work Statement (PWS) mandates that the Contractor comply with the most up-to-date versions of all regulations, publications, and standards cited in Appendix B (Publications and Forms). These are explicitly coded as **Mandatory (M)** or **Advisory (A)**, with the Contractor required to follow mandatory publications to accomplish PWS requirements. Where conflicts arise between standards, the more stringent requirement applies, as determined by the Contracting Officer's Representative (COR). Additionally, the Contractor must adhere to all U.S. and Host Nation (HN) laws, regulations, codes, and standards, including those in the AFCAP V Basic Contract. Specific service areas (e.g., Appendix F: Civil Engineer) require work to industry standards, manufacturers' recommendations, and Air Force Preventive Maintenance Task Lists (PMTLs), with deviations needing COR approval.

## Occupational Safety and Health Administration (OSHA) Standards

Contractors must comply with OSHA standards listed in Table B.4, accessible at http://www.osha.gov:
- **OSHA 29 CFR 1910.1200**: Hazard Communication (Applicable Sections: All; Mandatory).
- **OSHA 29 CFR 1910 Subpart I**: Personal Protective Equipment (Applicable Sections: All; Mandatory).

## United Facilities Criteria (UFCs)

All UFCs marked 'M' in Table B.8 (accessible at https://www.wbdg.org/ffc/dod) are mandatory, applying to all ('All' or 'Al1') sections unless specified:
- UFC 1-200-01: DoD Building Code.
- UFC 1-201-01: Non-Permanent DoD Facilities in Support of Military Operations.
- UFC 3-110-03: Roofing.
- UFC 3-120-01: Air Force Sign Standard.
- UFC 3-201-01: Civil Engineering.
- UFC 3-201-02: Landscape Architecture.
- UFC 3-260-04: Airfield and Heliport Marking.
- UFC 3-410-01: Heating, Ventilating, and Air Conditioning Systems.
- UFC 3-420-01: Plumbing Systems.
- UFC 3-520-01: Interior Electrical Systems.
- UFC 3-540-07: Operation and Maintenance Generators.
- UFC 3-550-01: Exterior Electrical Power Distribution.
- UFC 3-550-07: O&M: Exterior Power Distribution Systems.
- UFC 3-560-01: Operation and Maintenance: Electrical Safety.
- UFC 3-575-01: Lightning and Static Electricity Protection Systems.
- UFC 3-600-01: Fire Protection Engineering for Facilities.
- UFC 3-601-02: Operation and Maintenance: Inspection, Testing, and Maintenance of Fire Protection Systems.
- UFC 4-010-01: DoD Minimum Antiterrorism Standards for Buildings (All1; M).
- UFC 4-010-06: Cybersecurity of Facility-Related Control Systems (All1; M).
- UFC 4-021-01: Mass Notification (All1; M).

## Air Force and Department of the Air Force (DAF) Publications

From Tables B.3, mandatory AF/DAF publications (accessible at http://www.epublishing.af.mil/) include:
- AFI 17-130: Cybersecurity Program Management (Chapter 4; M).
- AFI 32-1023: Designing and Constructing Military Construction Projects (All; M).
- AFI 33-322: Records Management and Information Governance Program (All; M).
- AFI 48-110: Immunizations and Chemoprophylaxis (Chapter 4; M).
- DAFI 48-116: Food Safety Program (All; M).
- AFI 65-601, V2: Budget Management for Operations (All; M).
- DAFI 91-212: Bird/Wildlife Aircraft Strike Hazard (BASH) Management Program (As Applicable; M).
- AFMAN 32-1053: Integrated Pest Management Program (All; M).
- AFMAN 32-1062: Electrical Systems, Power Plants, and Generators (All; M).
- AFMAN 32-1065: Grounding & Electrical Systems (All; M).
- AFMAN 32-1068: Heating Systems and Unfired Pressure Vessels (All; M).
- DAFMAN 34-135: Air Force Lodging Program (All; M).
- AFMAN 48-138_IP: Sanitary Control and Surveillance of Field Water Supplies (All; M).
- AFPAM 32-2004: Aircraft Fire Protection for Exercises and Contingency Response Operations (All; M).
- AFTTP 3-34.1: Services Beddown and Sustainment (All; M).
- DAFI 32-1001: Civil Engineer Operations (All; M).
- DAFI 32-1015: Integrated Installation Planning (All; M).
- DAFI 32-1020: Planning and Programming Built Infrastructure Projects (All; M).
- DAFI 32-2001: Fire and Emergency Services (F&ES) Program (All; M).
- DAFI 32-7001: Environmental Management (All; M).
- DAFI 32-9005: Real Property Accountability (All; M).
- DAFMAN 32-1067: Water and Fuel Systems (All; M).
- DAFMAN 32-1084: Standard Facility Requirements (All; M).
- DAFMAN 32-7002: Waste Management (All; M).
- DAFMAN 34-131: APF Food Service Program Management (All; M).
- DAFMAN 48-147: Tri-Service Food Code (All; M).
- DAFMAN 91-203: Air Force Occupational Safety, Fire, and Health Standards (All; M).
- DAFPD 32-90: Real Property Management (All; M).

## National Fire Protection Association (NFPA) Standards

All NFPA standards in Tables B.6 are mandatory (All or Al1 sections):
- NFPA 10: Standard for Portable Fire Extinguishers.
- NFPA 13: Standard for Installation of Sprinkler Systems.
- NFPA 14: Standard for Installation of Standpipe and Hose Systems.
- NFPA 17: Standard for Dry Chemical Extinguishing Systems.
- NFPA 17A: Standard for Wet Chemical Extinguishing Systems.
- NFPA 22: Standard for Water Tanks for Private Fire Protection.
- NFPA 25: Standard for Inspection, Testing, and Maintenance of Water-Based Fire Protection Systems.
- NFPA 70: National Electric Code.
- NFPA 70B: Recommended Practice for Electrical Equipment Maintenance.
- NFPA 70E: Standards for Electrical Safety.
- NFPA 72: National Fire Alarm and Signaling Code.
- NFPA 96: Standard for Ventilation Control and Fire Protection of Commercial Cooking Operations.
- NFPA 101: National Life Safety Code.
- NFPA 110: Standard for Emergency and Standby Power Systems.
- NFPA 291: Recommended Practice for Fire Flow Testing and Marking of Hydrants.
- NFPA 412: Standard for Evaluating Aircraft Rescue and Fire-Fighting Foam Equipment.
- NFPA 414: Standard for Aircraft Rescue and Fire-Fighting Vehicles.
- NFPA 780: Standard for the Installation of Lightning Protection Systems.
- NFPA 2001: Standard on Clean Agent Fire Extinguishing Systems.
- NFPA 1852 (and Manufacturers' Instructions): Standard on Selection, Care, and Maintenance of Open-Circuit SCBA.
- NFPA 1911 (and Manufacturers' Instructions): Standard for Inspection, Maintenance, Testing, and Retirement of In-Service Emergency Vehicles.
- NFPA 1932 (and Manufacturers' Instructions): Standard on Use, Maintenance, and Service Testing of In-Service Fire Department Ground Ladders.
- NFPA 1936 (and Manufacturers' Instructions): Standard on Rescue Tools.
- NFPA 1962 (and Manufacturers' Instructions): Standard for Care, Use, Inspection, Service Testing, and Replacement of Fire Hose, Couplings, Nozzles, and Fire Hose Appliances.
- NFPA 1991 (and Manufacturers' Instructions): Standard on Vapor-Protective Ensembles for Hazardous Materials Emergencies and CBRN Terrorism Incidents.

## Department of Defense (DoD/DoW) Publications

Mandatory from Table B.5 (accessible at https://www.esd.whs.mil/DD/):
- DoDD 5500.07: Ethics and Standards of Conduct (All; M).
- DoDI 3020.41: Operational Contract Support (OCS) (All; M).
- DoDI 4150.07: DoD Pest Management Program (All; M).
- DoDI 4715.05: Environmental Compliance at Installations Outside the United States (All; M).
- DoDM 4140.27 Vol 1: DoD Shelf-Life Management Program: Program Administration (All; M).
- DoDM 4150.07, Vol 1: DoD Pest Management Program Elements: Structure and Operation (All; M).
- DoDM 4150.07, Vol 2: DoD Pest Management Program: Pesticide Applicator Training (All; M).
- DoDM 4715.05, Vols 1-5: Overseas Environmental Baseline Guidance Document (All; M).
- DoDM 5400.07: DoD Freedom of Information Act (FOIA) Program (Sections 3-6; M).
- DoD 6055.05-M: Occupational Medical Examinations and Surveillance Manual (All; M).

## Technical Orders, Bulletins, and Other Mandatory Publications

- **Technical Orders (Table B.2)**: T.O. 00-20-14 (Air Force Metrology and Calibration; All; M); T.O. 13F4-4-121 (Fire Extinguisher; All; M); T.O. 33K-1-100-1 (Calibration Procedure; All; M); T.O. 33K-1-100-2 (TMDE Calibration Notes; All; M); T.O. 34-1-3 (Machinery Inspection; All; M); T.O. 36-1-191 (Motor Vehicle Maintenance; All; M); 35C2-3-372-1 (Mobile Electric Power Plants; All; M); 35E8-2-10-1 (Aircraft Arresting Systems; All; M).
- **Technical Bulletins (Table B.7)**: TB 43-0142 (Lifting Devices; All; M); TB MED 530 (Tri-Service Food Code; All; M); TB MED 577 (Field Water Supplies; All; M).
- **Other (Table B.9)**: USCENTCOM General Order #1 (All; M); Office of the Under Secretary of Defense Memorandum on Government-Furnished Property (All; M); AFCEC Non-Standard Pesticide Approval Form (All; M); CE Playbook - SMS Playbook (All; M); CE Playbook - Work Management Playbook (All; M); PMTLs - Air Force Preventive Maintenance Task Lists (All; M); OMB Bulletin No.22-01 (Audit Requirements; All; M).

## Additional Mandatory Requirements

- **Forms (B.11)**: Use specified DAF/DoD forms (e.g., DAF Form 332 Base Civil Engineer Work Request; DD Form 1532 Pest Management Report).
- **Cybersecurity**: NIST SP 800-171 (implied via DFARS, but contextually via AFI 17-130 and UFC 4-010-06).
- **Pest/HAZMAT/Environmental**: DoDI 4150.07, DAFMAN 32-1053, EPA 40 CFR Part 82 for refrigerants.
- **Property/Financial**: FAR 52.245-1 (Government Property); OMB Bulletin No.22-01 for audits.

The Government provides hard copies of non-e-publishable AF/DoD items and updates; Contractor obtains NFPRs and returns all upon completion.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.3s*

### afcapv_bos_i_t5

## Mandatory Standards and Regulations Overview

The Performance Work Statement (PWS) specifies that the Contractor **shall comply** with the most up-to-date versions of all regulations and publications cited in **Appendix B - Publications and Forms**, particularly those designated as **mandatory (M)**. Publications are coded as either mandatory (M) or advisory (A), and the Contractor **shall be guided by** mandatory ones to accomplish PWS requirements. The Government provides hard copies of Air Force and Government publications not available online at contract start, with supplements forwarded by the COR. Upon contract completion, the Contractor **shall return** all issued publications and unused forms.

Mandatory compliance applies across **all sections (All/Al1)** unless specified otherwise (e.g., Chapter 4). Key categories include United Facilities Criteria (UFCs), Occupational Safety and Health Administration (OSHA) standards, Air Force publications, National Fire Protection Association (NFPA) standards, Department of Defense/War (DoD/DoW) publications, Technical Bulletins (TBs), Technical Orders (TOs), and others explicitly marked "M".

## United Facilities Criteria (UFCs) - Section B.8

All listed UFCs are **mandatory (M)** and applicable to **All/Al1** sections. The Contractor **shall comply** with:
- UFC 1-200-01: DoD Building Code
- UFC 1-201-01: Non-Permanent DoD Facilities in Support of Military Operations
- UFC 3-110-03: Roofing
- UFC 3-120-01: Air Force Sign Standard
- UFC 3-201-01: Civil Engineering
- UFC 3-201-02: Landscape Architecture
- UFC 3-260-04: Airfield and Heliport Marking
- UFC 3-410-01: Heating, Ventilating, and Air Conditioning Systems (applicable to "A")
- UFC 3-420-01: Plumbing Systems
- UFC 3-520-01: Interior Electrical Systems
- UFC 3-540-07: Operation and Maintenance Generators
- UFC 3-550-01: Exterior Electrical Power Distribution
- UFC 3-550-07: O&M: Exterior Power Distribution Systems
- UFC 3-560-01: Operation and Maintenance: Electrical Safety
- UFC 3-575-01: Lightning and Static Electricity Protection Systems
- UFC 3-600-01: Fire Protection Engineering For Facilities
- UFC 3-601-02: Operation and Maintenance: Inspection, Testing And Maintenance Of Fire Protection Systems
- UFC 4-010-01: DoD Minimum Antiterrorism Standards for Buildings
- UFC 4-010-06: Cybersecurity of Facility-Related Control Systems
- UFC 4-021-01: Mass Notification

UFCs are available at https://www.wbdg.org/ffc/dod/.

## OSHA Standards - Section B.4

**Mandatory (M)** and applicable to **All** sections:
- OSHA 29 CFR 1910.1200: Hazard Communication
- OSHA 29 CFR 1910 Subpart I: Personal Protective Equipment

Available at http://www.osha.gov.

## Air Force Publications - Section B.3

Numerous **mandatory (M)** publications applicable to **All/Al1/Chapter 4/As Applicable**:
- AFI 17-130: Cybersecurity Program Management (Chapter 4)
- AFI 32-1023: Designing and Constructing Military Construction Projects (All)
- AFI 33-322: Records Management and Information Governance Program (All)
- AFI 48-110: Immunizations and Chemoprophylaxis (Chapter 4)
- DAFI 48-116: Food Safety Program (All)
- AFI 65-601, V2: Budget Management for Operations (All)
- DAFI 91-212: Bird/Wildlife Aircraft Strike Hazard (BASH) Management Program (As Applicable)
- AFMAN 32-1053: Integrated Pest Management Program (All)
- AFMAN 32-1062: Electrical Systems, Power Plants, and Generators (All)
- AFMAN 32-1065: Grounding & Electrical Systems (All)
- AFMAN 32-1068: Heating Systems and Unfired Pressure Vessels (All)
- DAFMAN 34-135: Air Force Lodging Program (All)
- AFMAN 48-138_IP: Sanitary Control and Surveillance of Field Water Supplies (All)
- AFPAM 32-2004: Aircraft Fire Protection for Exercises and Contingency Response Operations (All)
- AFTTP 3-34.1: Services Beddown and Sustainment (All)
- DAFI 32-1001: Civil Engineer Operations (All)
- DAFI 32-1015: Integrated Installation Planning (All)
- DAFI 32-1020: Planning and Programming Built Infrastructure Projects (All)
- DAFI 32-2001: Fire and Emergency Services (F&ES) Program (All)
- DAFI 32-7001: Environmental Management (All)
- DAFI 32-9005: Real Property Accountability (All)
- DAFMAN 32-1067: Water and Fuel Systems (All)
- DAFMAN 32-1084: Standard Facility Requirements (All)
- DAFMAN 32-7002: Waste Management (All)
- DAFMAN 34-131: APF Food Service Program Management (All)
- DAFMAN 48-147: Tri-Service Food Code (All)
- DAFMAN 91-203: Air Force Occupational Safety, Fire, And Health Standards (All)
- DAFPD 32-90: Real Property Management (All)

Available at http://www.epublishing.af.mil/.

## NFPA Standards - Section B.6

All listed NFAPs are **mandatory (M)** and applicable to **All** sections, often with manufacturers' instructions:
- NFPA 10: Standard for Portable Fire Extinguishers
- NFPA 13: Standard For Installation Of Sprinkler Systems
- NFPA 14: Standard For Installation of Standpipe and Hose Systems
- NFPA 17: Standard For Dry Chemical Extinguishing Systems
- NFPA 17A: Standard For Wet Chemical Extinguishing Systems
- NFPA 22: Standard For Water Tanks For Private Fire Protection
- NFPA 25: Standard For The Inspection, Testing, And Maintenance Of Water-Based Fire Protection Systems
- NFPA 70: National Electric Code
- NFPA 70B: Recommended Practice For Electrical Equipment Maintenance
- NFPA 70E: Standards For Electrical Safety
- NFPA 72: National Fire Alarm and Signaling Code
- NFPA 96: Standard For Ventilation Control And Fire Protection Of Commercial Cooking Operations
- NFPA 101: National Life Safety Code
- NFPA 110: Standard for Emergency and Standby Power Systems
- NFPA 291: Recommended Practice For Fire Flow Testing And Marking Of Hydrants
- NFPA 412: Standard for Evaluating Aircraft Rescue and Fire-Fighting Foam Equipment
- NFPA 414: Standard for Aircraft Rescue and Fire-Fighting Vehicles
- NFPA 780: Standard for the Installation of Lightning Protection Systems
- NFPA 2001: Standard on Clean Agent Fire Extinguishing Systems
- NFPA 1852 and Manufacturers Instructions: Standard on Selection, Care, and Maintenance of Open-Circuit Self-Contained Breathing Apparatus (SCBA)
- NFPA 1911 and Manufacturers Instructions: Standard for the Inspection, Maintenance, Testing, and Retirement of In-Service Emergency Vehicles
- NFPA 1932 and Manufacturers Instructions: Standard on Use, Maintenance, and Service Testing of In-Service Fire Department Ground Ladders
- NFPA 1936 and Manufacturers Instructions: Standard on Rescue Tools
- NFPA 1962 and Manufacturers Instructions: Standard for the Care, Use, Inspection, Service Testing, and Replacement of Fire Hose, Couplings, Nozzles, and Fire Hose Appliances
- NFPA 1991 and Manufacturers Instructions: Standard on Vapor-Protective Ensembles for Hazardous Materials Emergencies and CBRN Terrorism Incidents

## DoD/DoW Publications - Section B.5

**Mandatory (M)** across **All/Al1/Sections 3-6**:
- DoDD 5500.07: Ethics and Standards of Conduct
- DoDI 3020.41: Operational Contract Support (OCS)
- DoDI 4150.07: DoD Pest Management Program
- DoDI 4715.05: Environmental Compliance at Installations Outside the United States
- DoDM 4140.27 Vol 1: DOD Shelf-Life Management Program: Program Administration
- DoDM 4150.07, Volume 1: DoD Pest Management Program Elements and Implementation: Structure and Operation
- DoDM 4150.07, Volume 2: DoD Pest Management Program Elements and Implementation: Pesticide Applicator Training and Certification Program
- DoDM 4715.05, Volumes 1-5: Overseas Environmental Baseline Guidance Document
- DoDM 5400.07: DOD Freedom of Information Act (FOIA) Program (Sections 3-6)
- DoD 6055.05-M: Occupational Medical Examinations and Surveillance Manual

Available at https://www.esd.whs.mil/DD/.

## Technical Bulletins (TBs) - Section B.7 and Others

**Mandatory (M)** for **All**:
- TB 43-0142: Safety Inspection and Testing of Lifting Devices
- TB MED 530: Tri-Service Food Code
- TB MED 577: Sanitary Control and Surveillance of Field Water Supplies

## Technical Orders (TOs) - Section B.2

**Mandatory (M)** for **All**:
- 00-20-14: Air Force Metrology and Calibration Program
- 13F4-4-121: Operation, Service and Maintenance (With Illustrated Parts Breakdown), Fire Extinguisher, Wheeled Liquefied Gas, 150 Pound Capacity
- 33K-1-100-1: Calibration Procedure -- Maintenance Data Collection Codes and Calibration Measurement Summaries
- 33K-1-100-2: TMDE Calibration Notes, Calibration Interval, Technical Order, and Work Unit Code Reference Guide
- 34-1-3: Inspection And Maintenance -- Machinery and Shop Equipment
- 36-1-191: Technical And Managerial Reference for Motor Vehicle Maintenance
- 35C2-3-372-1: Operation and Maintenance, Mobile Electric Power Plants
- 35E8-2-10-1: Installation, O&M, Aircraft Arresting Systems

Available via Enhanced Technical Information Management System (ETIMS) at https://www.my.af.mil/.

## Other Mandatory Publications - Section B.9

**Mandatory (M)** for **All/Al**:
- USCENTCOM General Order #1
- Office of the Under Secretary of Defense Memorandum: Implementation of Government-Furnished Property Attachments to Solicitations and Awards (http://www.acq.osd.mil/dpap/policy/policyvault/USA001948-12-DPAP.pdf)
- AFCEC Non-Standard Pesticide Approval Form
- CE Playbook: SMS Playbook
- CE Playbook: Work Management Playbook
- PMTLs: Air Force Preventive Maintenance Task Lists
- OMB Bulletin No.22-01: Audit Requirements for Federal Financial Statements

## Additional Contractual Mandates

The Contractor **shall comply** with **FAR 52.245-1 (Government Property)** for all property (GFP, CMGP, CAP). Title to CAP vests in the Government upon vendor delivery. Comply with **DAFI 32-1001** for work prioritization. All work **shall be performed** to industry standards and manufacturers’ recommendations, with more stringent requirements prevailing as determined by the COR.

### References

- [1] Attachment 1 - PWS Israel BOS-I dated 6 April 2026 (003).docx

*Response time: 0.4s*

---
