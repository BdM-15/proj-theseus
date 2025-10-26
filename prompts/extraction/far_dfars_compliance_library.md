# FAR/DFARS Compliance Library

**Purpose**: Operational context for federal acquisition clauses beyond basic extraction  
**Usage**: Referenced during entity extraction to understand clause implications  
**Scope**: Core FAR 52.2## series + critical DFARS 252.2## cybersecurity/supply chain clauses  
**Size**: ~30,000 tokens (domain expertise investment)  
**Last Updated**: January 26, 2025 (Branch 011 - Prompt Enhancements)

---

## How to Use This Library

**During Extraction**: When LLM encounters a clause (FAR/DFARS pattern), use this library to:

1. **Extract metadata** - Clause effective date, agency supplement, incorporation method
2. **Identify implications** - What contractor MUST do operationally
3. **Recognize flowdown** - Which clauses require Prime→Subcontractor flowdown
4. **Flag cost impacts** - Clauses with significant compliance costs
5. **Link to evaluation** - Which factors typically evaluate clause compliance

**NOT a replacement** for official FAR/DFARS text - this is **operational intelligence** for proposal teams.

---

## Section 1: FAR 52.212 Series - Commercial Item Acquisitions

### FAR 52.212-1 Instructions to Offerors—Commercial Products and Commercial Services

**Effective Date**: JAN 2024 (latest revision)  
**Incorporation**: Full text (always included in Section L or combined Section L/M)  
**Criticality**: ABSOLUTE - Defines submission requirements

#### Clause Implications

**Proposal Submission**:

- Deadline is ABSOLUTE - late proposals rejected without consideration (FAR 15.208(b))
- No "mailbox rule" - electronic submissions timestamped by government server receipt
- Hard copy submissions: Must be received (not postmarked) by deadline
- Amendments SUPERSEDE all prior instructions - check solicitation.gov daily until deadline

**Electronic Submission Requirements**:

- Verify email address or portal URL is current (amendments may change)
- File size limits typically 25-50 MB (compress if needed)
- PDF format required unless otherwise specified
- Email subject line format: "[Solicitation Number] - [Company Name] Proposal"

**Questions and Clarifications**:

- Q&A deadline typically 10 days before proposal due (but varies - read carefully)
- Questions submitted after deadline: Government may choose not to answer
- Amendments issued to all vendors via solicitation.gov - not individual emails

**Common Mistakes**:

- ❌ Submitting to old email after amendment changes address → REJECTED
- ❌ Assuming grace period exists for late submissions → REJECTED
- ❌ Missing amendment because only checked once at solicitation release → NON-RESPONSIVE
- ❌ Submitting via email when portal submission required → REJECTED

#### Compliance Checklist

- [ ] Proposal submission method confirmed (email address, portal URL, hard copy address)
- [ ] Submission deadline calendared with 24-hour buffer
- [ ] Daily solicitation.gov check scheduled (or email notifications enabled)
- [ ] Amendment tracking log created (document date received, content summary)
- [ ] File size tested (compress large files if needed)
- [ ] Email/portal access tested 48 hours before deadline
- [ ] Backup submission method identified (if email fails, use portal or vice versa)

#### Flowdown Requirements

**None** - Instructions apply only to offerors, not subcontractors

#### Cost Impact

**Minimal** - Administrative compliance only

#### Evaluation Factor Linkage

**Not directly evaluated** - But non-compliance = rejection before evaluation begins!

**Proposal Strategy**: Create submission checklist, test delivery method early, monitor amendments daily

---

### FAR 52.212-3 Offeror Representations and Certifications—Commercial Products and Commercial Services

**Effective Date**: JAN 2024  
**Incorporation**: Full text or by reference via SAM.gov  
**Criticality**: HIGH - False certification = criminal liability

#### Clause Implications

**SAM.gov Annual Representations**:

- Large businesses (>$7.5M revenue): Complete SAM.gov reps annually
- Small businesses: Complete SAM.gov reps + solicitation-specific reps in proposal
- Failure to update SAM.gov before proposal submission: Non-responsive proposal

**Small Business Status**:

- Size standard NAICS code-specific (varies from 500 employees to $41.5M revenue)
- Self-certification acceptable (unless competitor protests)
- SBA size determination is binding if protested
- Affiliation rules complex (common ownership, management, control)

**Trade Agreement Compliance**:

- TAA (Trade Agreements Act): Product must be from designated country
- BAA (Buy American Act): Domestic preference for non-TAA items
- China restrictions: DFARS 252.225-7049 prohibits Chinese telecommunications

**Telecommunications Equipment Prohibition**:

- FAR 52.204-25/26: Huawei, ZTE, Hytera, Hikvision, Dahua prohibited
- Supply chain screening required (not just direct purchase)
- Subcontractor certification required (flowdown)

**Common Mistakes**:

- ❌ Claiming small business status without checking NAICS size standard → PROTEST RISK
- ❌ Using SAM.gov reps from 13 months ago → NON-RESPONSIVE
- ❌ Certifying TAA compliance without verifying component country of origin → FALSE CLAIMS ACT
- ❌ Ignoring affiliate revenue when calculating small business size → PROTEST RISK

#### Compliance Checklist

- [ ] SAM.gov registration current (renewed within last 12 months)
- [ ] SAM.gov representations completed (all sections, not just basic)
- [ ] NAICS size standard verified for this solicitation (SBA Table of Size Standards)
- [ ] Affiliate analysis completed (ownership, management, control assessment)
- [ ] Trade agreement compliance verified (TAA country of origin for products)
- [ ] Telecommunications equipment screening completed (no Chinese restricted items)
- [ ] Small business subcontracting plan prepared (if large business over $750K)

#### Flowdown Requirements

**Critical**: 52.204-25 (Telecommunications) flows to ALL subcontractors regardless of tier or dollar value

#### Cost Impact

**Low-Medium**:

- SAM.gov registration: $0 (free)
- Size protest defense: $5K-$25K legal fees if protested
- TAA compliance verification: $1K-$5K for supply chain audit
- Telecommunications screening: $2K-$10K for component analysis

#### Evaluation Factor Linkage

**Past Performance**: SBA size protest history may be questioned  
**Small Business**: Subcontracting plan evaluated if required

**Proposal Strategy**: Include SAM.gov certification date in cover letter, document TAA compliance in technical volume, prepare size standard justification if close to threshold

---

### FAR 52.212-4 Contract Terms and Conditions—Commercial Products and Commercial Services

**Effective Date**: JAN 2024  
**Incorporation**: Full text (always in Section I)  
**Criticality**: HIGHEST - Core contract obligations

#### Clause Implications

**Inspection and Acceptance** (para (a)):

- Government has right to inspect at all reasonable times
- Acceptance occurs after inspection at destination (not shipment)
- Contractor bears risk of loss until acceptance
- Non-conforming goods: Government may reject OR require correction at no cost

**Changes** (para (c)):

- Unilateral change authority: Government can modify specifications/delivery within scope
- Bilateral change: Agreement required for out-of-scope changes
- Constructive change: Contractor must notify CO within 30 days of changed work
- REA (Request for Equitable Adjustment): File within 30 days or waive rights

**Payments** (para (i)):

- Prompt Payment Act: 30 days from invoice receipt (or acceptance if later)
- Invoice requirements: Proper invoice must include 9 elements (see FAR 32.905)
- Discounts: Early payment discounts honored if offered
- Interest on late payments: Treasury rate + 1% (but check contract for dispute exclusion)

**Excusable Delays** (para (f)):

- Force majeure: Acts of God, strikes, government acts
- Notice required: Written notice to CO within 10 days
- Government may terminate for default if delay unreasonable
- COVID-19: Typically NOT excusable (established risk by 2021)

**Warranty** (para (m)):

- Implied warranty: Commercial items have warranty of merchantability
- Express warranty: If contractor provides written warranty terms
- Warranty period: 1 year typical (unless specified otherwise)
- Government may require repairs or replacement

**Common Mistakes**:

- ❌ Invoicing before acceptance → PAYMENT DELAY (30-day clock doesn't start)
- ❌ Missing 30-day REA deadline → WAIVE CLAIM RIGHTS (can't recover costs later)
- ❌ Not notifying CO of excusable delay within 10 days → DEFAULT TERMINATION RISK
- ❌ Shipping without documented inspection → LIABILITY FOR DEFECTS
- ❌ Treating POPs as invoices → NOT PROPER INVOICES (9 elements required)

#### Compliance Checklist

- [ ] Inspection procedures documented (quality control plan)
- [ ] REA tracking system in place (30-day deadline monitoring)
- [ ] Proper invoice template created (all 9 FAR 32.905 elements)
- [ ] Change order process documented (constructive change recognition)
- [ ] Warranty terms defined (express warranty if offering beyond implied)
- [ ] Force majeure notification process (10-day deadline)
- [ ] Payment terms confirmed (Net 30, early payment discount if offered)

#### Flowdown Requirements

**Selective**: Inspection, Changes, Warranty flow to subcontractors for their deliverables

#### Cost Impact

**Low-Medium**:

- Quality control system: $5K-$15K setup (ISO 9001 helpful but not required)
- Change order tracking: $2K-$5K (software + training)
- Warranty reserve: 1-3% of contract value (depends on product)

#### Evaluation Factor Linkage

**Technical Approach**: Quality assurance procedures  
**Management Approach**: Change order process, schedule risk mitigation  
**Past Performance**: Warranty claims history, change order disputes

**Proposal Strategy**: Describe inspection/acceptance procedures in Quality section, include change order flowchart, specify warranty terms beyond implied (if competitive advantage)

---

### FAR 52.212-5 Contract Terms and Conditions Required to Implement Statutes or Executive Orders

**Effective Date**: JAN 2024  
**Incorporation**: Full text with checkboxes for applicable clauses  
**Criticality**: VARIABLE - Some are administrative, others are contractual obligations

#### Clause Implications (Commonly Checked)

**52.219-6 Notice of Total Small Business Set-Aside**:

- Contract reserved exclusively for small businesses
- Size status determined as of proposal submission date
- Subcontracting limitations: 50% of cost of manufacturing (supplies) or 50% of cost of personnel (services) must be performed by prime

**52.219-8 Utilization of Small Business Concerns**:

- Small business subcontracting plan required if:
  - Prime is large business AND contract >$750,000 (supplies/services) OR >$1.5M (construction)
- Plan goals: Percentage targets for small, HUBZone, SDVOSB, WOSB, 8(a)
- eSRS reporting: Semi-annual reports required via eSRS system

**52.222-50 Combating Trafficking in Persons**:

- Zero tolerance: Trafficking, forced labor, slavery prohibited
- Employee awareness: Contractor must inform employees of prohibited activities
- Recruitment fees: Prohibited (contractor or subcontractor cannot charge workers)
- Compliance plan required if contract >$550,000 performed outside US

**52.223-18 Encouraging Contractor Policies to Ban Text Messaging While Driving**:

- Policy encouraged (not required): Contractor should ban texting while driving on government business
- No direct contract implication (encouragement only)

**52.225-13 Restrictions on Certain Foreign Purchases**:

- Sanctioned countries: Iran, North Korea, Syria, Cuba (plus Russia for defense)
- Waiver possible but requires CO approval before award
- Supply chain screening required (not just direct purchase)

**Common Mistakes**:

- ❌ Not submitting small business plan with proposal → NON-RESPONSIVE (if required)
- ❌ Counting large business subcontractors toward SB goals → eSRS AUDIT FINDING
- ❌ Ignoring trafficking compliance plan requirement → CONTRACT VIOLATION
- ❌ Purchasing from sanctioned country without waiver → FALSE CLAIMS ACT

#### Compliance Checklist

- [ ] Determine if small business plan required (>$750K and large business prime)
- [ ] Small business plan goals established (industry-specific percentages)
- [ ] eSRS system access obtained (for semi-annual reporting if plan required)
- [ ] Trafficking in persons policy drafted (if >$550K outside US)
- [ ] Sanctioned country screening completed (supply chain verification)
- [ ] Text messaging policy reviewed (voluntary but good practice)

#### Flowdown Requirements

**Critical**:

- 52.219-8: Subcontracting goals flow to large business subs >$750K
- 52.222-50: Trafficking prohibition flows to ALL subs regardless of tier/value
- 52.225-13: Sanctioned country restrictions flow to ALL subs

#### Cost Impact

**Low-Medium**:

- Small business plan development: $2K-$5K (first time), $500-$1K (updates)
- eSRS reporting: $1K-$3K annually (admin time)
- Trafficking compliance plan: $3K-$10K (policy development + training)
- Sanctioned country screening: $1K-$5K (supply chain audit)

#### Evaluation Factor Linkage

**Small Business**: Plan quality evaluated if large business prime  
**Management Approach**: Subcontractor management, compliance systems  
**Past Performance**: eSRS reporting history, trafficking compliance record

**Proposal Strategy**: If large business, include robust small business plan with specific goals and outreach strategy; document trafficking compliance procedures; highlight SB utilization in past performance

---

## Section 2: DFARS 252.204 Series - Cybersecurity and Data Protection

### DFARS 252.204-7012 Safeguarding Covered Defense Information and Cyber Incident Reporting

**Effective Date**: DEC 2019 (pending updates for CMMC)  
**Incorporation**: Full text (always in Section I for DoD contracts)  
**Criticality**: HIGHEST - NIST 800-171 compliance MANDATORY

#### Clause Implications

**Covered Defense Information (CDI)**:

- Definition: Unclassified controlled technical information (CTI) with export control or critical technology
- Marking: "(CTI)" or similar marking on documents/emails
- Applies to: Technical data, engineering drawings, test results, software, specifications
- Scope: CDI on contractor information systems (not just government-provided)

**NIST SP 800-171 Compliance**:

- 110 security controls REQUIRED (17 families: Access Control, Awareness & Training, Audit, etc.)
- Assessment: Self-assessment required, results submitted to DoD via SPRS (Supplier Performance Risk System)
- Deadline: Must have implemented controls (or POA&M for gaps) before contract award
- Cost: $50K-$200K for initial implementation (small businesses), $200K-$1M+ (large businesses)

**System Security Plan (SSP)**:

- Required: Document describing how 110 controls are implemented
- Format: NIST 800-171 Appendix D template recommended
- Scope: All information systems processing/storing/transmitting CDI
- Updates: Annually or when system changes significantly

**Plan of Action & Milestones (POA&M)**:

- Required if: Any of 110 controls not fully implemented
- Content: Control gap, risk level, mitigation plan, completion date
- Submission: Upload POA&M to SPRS with SSP summary
- Scoring: -3 points per missing control (max -330, minimum -203 for basic score)

**Cyber Incident Reporting**:

- Definition: Loss, compromise, unauthorized access to CDI
- Timeline: Report within 72 hours to DoDCIO.CyberSecurity@mail.mil
- Content: Description, impact assessment, remediation plan
- Preservation: Preserve affected media/logs for 90 days minimum (forensics)

**Media Sanitization**:

- Standard: NIST SP 800-88 (Clear, Purge, or Destroy)
- Requirement: Sanitize ALL media (hard drives, USB, backup tapes) before disposal/reuse
- Certificate: Document media sanitization (serial numbers, method, date)
- Subcontractors: Prime responsible for ensuring subs sanitize properly

**Subcontractor Flowdown**:

- MANDATORY: All subcontractors at any tier handling CDI must comply
- Prime liability: Prime responsible for subcontractor cyber incidents
- Verification: Prime must verify sub NIST 800-171 compliance (SPRS scores)

**Common Mistakes**:

- ❌ Assuming cybersecurity is IT's problem → ENTIRE ORGANIZATION must comply (HR, finance, etc.)
- ❌ Not submitting SPRS score before award → AWARD DELAYED or WITHDRAWN
- ❌ Waiting for incident investigation before 72-hour report → LATE REPORT = VIOLATION
- ❌ Throwing hard drives in trash without sanitization → DATA BREACH + CONTRACT VIOLATION
- ❌ Not flowing DFARS 252.204-7012 to ALL subs touching CDI → PRIME LIABILITY
- ❌ Treating POA&M as permanent workaround → POA&M items must be closed per schedule

#### Compliance Checklist

- [ ] NIST 800-171 assessment completed (all 110 controls evaluated)
- [ ] System Security Plan (SSP) documented (all systems with CDI)
- [ ] Plan of Action & Milestones (POA&M) created (gaps identified)
- [ ] SPRS score submitted (https://www.sprs.csd.disa.mil)
- [ ] Cyber incident response plan drafted (72-hour reporting procedures)
- [ ] Media sanitization procedures documented (NIST 800-88 compliant)
- [ ] Incident response team identified (24/7 contact)
- [ ] Subcontractor flowdown verified (all subs with CDI access)
- [ ] Insurance coverage reviewed (cyber liability, data breach)

#### Flowdown Requirements

**MANDATORY**: Full clause text flows to ALL subcontractors at ANY tier who handle CDI (no dollar threshold)

**Prime Responsibilities**:

- Verify sub SPRS score before subcontract award
- Flow DFARS 252.204-7012 clause text to all subs
- Monitor sub compliance (annual verification recommended)
- Report sub cyber incidents within 72 hours (prime is responsible!)

#### Cost Impact

**SIGNIFICANT**:

- Initial NIST 800-171 assessment: $15K-$50K (consultant-led)
- Control implementation: $50K-$200K (small), $200K-$1M+ (large)
- Annual maintenance: $10K-$50K (monitoring, updates, training)
- Cyber incident response: $50K-$500K (forensics, notification, remediation)
- Cyber insurance: $5K-$50K annually (depends on coverage)
- **Total 3-year cost**: $150K-$2M depending on organization size

**Cost Recovery**: Some costs allowable (FAR 31.205-47), but often not fully reimbursable

#### Evaluation Factor Linkage

**Technical Approach** (15-25% of technical weight typical):

- Cybersecurity architecture (network segmentation, encryption, MFA)
- NIST 800-171 compliance roadmap (controls implementation plan)
- Incident detection and response capabilities (SIEM, forensics)

**Management Approach**:

- Risk management (cybersecurity risk assessment and mitigation)
- Subcontractor management (sub NIST 800-171 verification)
- Compliance tracking (POA&M closure, annual assessments)

**Past Performance**:

- Previous contracts with CDI handling (CPARS cybersecurity ratings)
- Cyber incident history (any breaches reported?)
- CMMC certification level (if applicable to this solicitation)

**Small Business**:

- SB subcontractors may struggle with NIST 800-171 costs
- Prime must assist or select compliant SB subs

#### Proposal Strategy

**Technical Volume** (dedicate 3-5 pages to cybersecurity):

1. **Current State**: "We have implemented 108 of 110 NIST 800-171 controls (SPRS score: -6). Two controls under POA&M completion (March 2025)."

2. **Architecture**: Include network diagram showing:

   - CDI enclave (segmented network for CDI processing)
   - Multi-factor authentication (MFA) for all CDI access
   - Encryption at rest and in transit (AES-256, TLS 1.3)
   - SIEM system (24/7 monitoring with anomaly detection)

3. **Incident Response**: Flowchart showing:

   - Detection → Containment (within 1 hour)
   - Initial assessment → 72-hour report (automated email to DoDCIO)
   - Forensics → Root cause analysis (within 7 days)
   - Remediation → Lessons learned (within 30 days)

4. **Media Sanitization**: Procedure summary:

   - Hard drives: DoD 5220.22-M 7-pass wipe OR physical destruction
   - Certificates: Maintained for 3 years
   - Subcontractors: Certificate required before equipment return

5. **Subcontractor Management**:
   - "We verify all subcontractors' SPRS scores before award"
   - "Quarterly compliance reviews with subs handling CDI"
   - "Require 30-day advance notice of sub system changes"

**Management Volume** (risk management section):

- **Risk**: Subcontractor cyber incident
- **Mitigation**: SPRS verification + quarterly reviews + cyber insurance
- **Contingency**: Incident response team on retainer (24/7 availability)

**Past Performance** (highlight cybersecurity):

- **Contract X** (Navy, $5M): "Zero cyber incidents over 3-year performance period. CPARS rating: Exceptional (Cybersecurity). Successfully closed all POA&M items within 6 months."

**Discriminators** (competitive advantages):

- ✅ **CMMC Level 2 Certified** (if you have it - major advantage!)
- ✅ **Zero cyber incidents** in past 5 years (demonstrate clean record)
- ✅ **SPRS score >0** (indicates full compliance, no POA&M)
- ✅ **ISO 27001 Certified** (demonstrates mature ISMS beyond NIST 800-171)
- ✅ **24/7 SOC** (Security Operations Center for real-time monitoring)

**Common Weaknesses to Avoid**:

- ❌ Generic statement: "We comply with NIST 800-171" (no details)
- ❌ No SPRS score mentioned (evaluators will assume non-compliance)
- ❌ POA&M with >20 gaps (raises red flag about cybersecurity maturity)
- ❌ No incident response flowchart (shows lack of preparedness)
- ❌ Subcontractor verification unclear (prime liability risk)

---

### DFARS 252.204-7020 NIST SP 800-171 DoD Assessment Requirements

**Effective Date**: NOV 2020  
**Incorporation**: Full text (in addition to 252.204-7012)  
**Criticality**: HIGH - Requires third-party assessment

#### Clause Implications

**Assessment Requirement**:

- Basic: Self-assessment sufficient for most contracts
- Medium: C3PAO (Certified Third Party Assessment Organization) assessment if specified
- High: DIBCAC (Defense Industrial Base Cybersecurity Assessment Center) assessment for critical programs

**Timeline**:

- Assessment: Must be completed within 3 years prior to contract award
- Submission: Assessment results uploaded to SPRS
- Frequency: Triennial (every 3 years) OR if significant system change

**Cost**:

- Self-assessment: $5K-$15K (internal effort)
- C3PAO assessment: $25K-$75K (depends on scope)
- DIBCAC assessment: $50K-$150K (high-side programs)

**CMMC Integration**:

- CMMC is REPLACING DFARS 7012/7020 phased 2024-2026
- CMMC Level 2 = equivalent to NIST 800-171 compliance
- Transition: Current contracts still use 7012/7020, new contracts will require CMMC

#### Compliance Checklist

- [ ] Assessment type determined (Basic/Medium/High from solicitation)
- [ ] Assessment schedule established (complete before proposal if required)
- [ ] C3PAO selected if Medium assessment required (check CMMC marketplace)
- [ ] Assessment scope defined (all systems with CDI)
- [ ] SPRS submission confirmed (assessment results uploaded)
- [ ] CMMC roadmap created (if CMMC applies to this contract)

#### Flowdown Requirements

**Selective**: Flows to subs if specified in prime contract (typically only for critical subs with CDI)

#### Cost Impact

**Medium**: $25K-$75K for C3PAO assessment (most common)

#### Evaluation Factor Linkage

**Technical Approach**: Assessment results demonstrate cybersecurity maturity  
**Past Performance**: Assessment history shows compliance track record

**Proposal Strategy**: Mention assessment completion date and type (self-assessment vs C3PAO), highlight any findings fully remediated

---

## Section 3: DFARS 252.225 Series - Buy American and Trade Agreements

### DFARS 252.225-7021 Trade Agreements

**Effective Date**: FEB 2024  
**Incorporation**: Full text when TAA applies  
**Criticality**: HIGH - Product origin determines eligibility

#### Clause Implications

**Designated Countries**:

- WTO GPA countries: EU members, Japan, South Korea, Canada, etc. (48 countries total)
- Free Trade Agreement countries: Australia, Chile, Singapore, etc.
- Caribbean Basin, NAFTA (now USMCA)
- **Excluded**: China, India, Russia, Brazil (major non-designated countries)

**Product Must Be**:

- Manufactured in designated country OR
- Substantially transformed in designated country (51% value-added)

**Components**:

- End product must be TAA-compliant
- Components from non-designated countries acceptable if substantially transformed

**Verification**:

- Supplier certification required (country of origin)
- Supply chain audit recommended (especially for complex assemblies)
- False certification = False Claims Act liability

**Common Mistakes**:

- ❌ Assuming "Made in USA" = TAA compliant (not necessarily - must verify components)
- ❌ Certifying TAA compliance without supplier verification → SUPPLY CHAIN RISK
- ❌ Using Chinese components without substantial transformation → NON-COMPLIANT
- ❌ Not understanding "substantially transformed" test (51% value-added in designated country)

#### Compliance Checklist

- [ ] Product country of origin verified (manufacturer location)
- [ ] Component sourcing reviewed (supply chain mapping)
- [ ] Substantial transformation analysis (if non-designated components)
- [ ] Supplier certifications obtained (country of origin statements)
- [ ] Supply chain audit completed (high-risk items)
- [ ] Alternative sources identified (if current supplier non-compliant)

#### Flowdown Requirements

**Selective**: Flows to subs providing end products (not services or components unless specified)

#### Cost Impact

**Low-Medium**:

- Supply chain audit: $5K-$20K (depends on complexity)
- Alternative sourcing: 10-30% price premium (if switching from Chinese to TAA-compliant)

#### Evaluation Factor Linkage

**Technical Approach**: Supply chain management, quality assurance  
**Past Performance**: TAA compliance history, no supply chain violations

**Proposal Strategy**: Document TAA compliance verification process, include supplier certifications as proposal attachment, highlight domestic or designated country manufacturing if competitive advantage

---

### DFARS 252.225-7049 Restriction on Acquisition of Certain Articles Containing Specialty Metals

**Effective Date**: DEC 2022  
**Incorporation**: Full text for military/aerospace applications  
**Criticality**: HIGHEST - Melt traceability required

#### Clause Implications

**Specialty Metals Defined**:

- Steel, titanium, zirconium alloys
- Threshold: >2% by weight in end item
- Applications: Aircraft, missiles, ships, combat vehicles, space systems

**Domestic Source Requirement**:

- Melted in USA or qualifying country (very limited list)
- Qualifying countries: Australia, Canada, UK (NOT EU, Japan, Korea)
- China/Russia: Explicitly prohibited

**Melt Certification**:

- Certificate required from steel mill
- Traceability: Heat number → melt location
- Sampling: Government may test material (X-ray fluorescence)

**Exceptions**:

- Commercial off-the-shelf (COTS) with acceptable melt
- Fasteners (bolts, screws) under certain conditions
- Electronic components (semiconductors exempt)

**Common Mistakes**:

- ❌ Assuming all steel is domestic → CHINESE STEEL COMMON in supply chain
- ❌ No melt certificates obtained → CANNOT VERIFY COMPLIANCE
- ❌ Relying on supplier country of assembly → MUST TRACE TO MELT ORIGIN
- ❌ Using European steel (not qualifying country despite TAA) → NON-COMPLIANT

#### Compliance Checklist

- [ ] Bill of materials reviewed (specialty metals identified)
- [ ] Melt certificates requested from suppliers (heat numbers)
- [ ] Qualifying country verification (melted in USA/AUS/CAN/UK only)
- [ ] Alternative sources identified (if current supplier non-compliant)
- [ ] Material testing plan (if government sampling likely)
- [ ] Exception analysis (COTS, fasteners, electronics)

#### Flowdown Requirements

**MANDATORY**: Flows to ALL subs providing items with specialty metals (no threshold)

#### Cost Impact

**MEDIUM-HIGH**:

- Melt certification: $2K-$10K (supply chain verification)
- Alternative sourcing: 20-50% price premium (domestic vs foreign specialty metals)
- Material testing: $5K-$20K if government samples (destructive testing)

#### Evaluation Factor Linkage

**Technical Approach**: Supply chain management, material verification  
**Past Performance**: Specialty metals compliance history

**Proposal Strategy**: Document melt certification process, include example certificates, highlight domestic specialty metals sourcing if available

---

## Section 4: FAR 52.222 Series - Labor Standards and Equal Opportunity

### FAR 52.222-50 Combating Trafficking in Persons

**Effective Date**: MAR 2024  
**Incorporation**: Full text for contracts >$550K  
**Criticality**: HIGH - Zero tolerance policy

#### Clause Implications

**Prohibited Activities**:

- Trafficking in persons (forced labor, slavery)
- Commercial sex acts
- Confiscation of identity documents (passports, visas)
- Charging recruitment fees to workers
- Use of misleading recruitment practices
- Providing substandard housing

**Compliance Plan Required If**:

- Contract >$550,000 AND
- Performed outside the United States

**Compliance Plan Elements**:

- Employee awareness program (training on prohibited activities)
- Recruitment process (no fees charged to workers)
- Housing/transportation standards (if provided)
- Complaint mechanism (anonymous hotline)
- Disciplinary procedures (violations result in termination)

**Certification Required**:

- Annual certification of compliance (uploaded to FAPIIS)
- After investigation: CO may require certification

**Remedies**:

- Payment of back wages (if recruitment fees charged)
- Contract termination (for cause)
- Suspension/debarment (for repeated violations)
- Referral to Attorney General (criminal prosecution)

**Common Mistakes**:

- ❌ No compliance plan despite >$550K overseas contract → VIOLATION
- ❌ Not training subcontractor employees → PRIME LIABLE
- ❌ Allowing sub to charge recruitment fees → PRIME LIABLE
- ❌ Not investigating employee complaints → FAILURE TO MONITOR

#### Compliance Checklist

- [ ] Determine if compliance plan required (>$550K outside US)
- [ ] Compliance plan drafted (all required elements)
- [ ] Employee awareness training created (translated to local language if needed)
- [ ] Recruitment process documented (zero fees policy)
- [ ] Housing/transportation standards established (if applicable)
- [ ] Complaint hotline established (anonymous, 24/7)
- [ ] Disciplinary procedures documented (termination for violations)
- [ ] Subcontractor flowdown verified (all overseas subs)
- [ ] Annual certification process (FAPIIS submission)

#### Flowdown Requirements

**MANDATORY**: Flows to ALL subcontractors regardless of tier or dollar value

**Prime Responsibilities**:

- Monitor subcontractor compliance (site visits, audits)
- Investigate allegations promptly
- Report violations to CO within 24 hours
- Terminate subcontracts for violations

#### Cost Impact

**LOW-MEDIUM**:

- Compliance plan development: $5K-$15K (first time)
- Training program: $2K-$5K annually
- Hotline service: $3K-$10K annually
- Audits/site visits: $10K-$30K annually (overseas locations)

#### Evaluation Factor Linkage

**Management Approach**: Compliance systems, subcontractor oversight  
**Past Performance**: Trafficking compliance record (FAPIIS check)

**Proposal Strategy**: If overseas work, include compliance plan summary (1-2 pages), describe training program, highlight zero-tolerance policy enforcement

---

### FAR 52.222-41 Service Contract Labor Standards

**Effective Date**: AUG 2018  
**Incorporation**: Full text for service contracts >$2,500  
**Criticality**: HIGH - Wage/benefit violations = back pay liability

#### Clause Implications

**Wage Determination (WD)**:

- Attached to solicitation (typically Section J)
- Specifies minimum wages by labor category
- Locality-specific (e.g., "Washington DC" rates differ from "Norfolk VA")
- Updates: WD can be updated up to 10 days before proposal due

**Fringe Benefits**:

- Health & welfare: Minimum $4.80/hour (2024 rate, adjusted annually)
- Vacation: Typically 2 weeks after 1 year
- Holidays: 10 federal holidays per year
- Sick leave: Varies by WD

**Payroll Requirements**:

- Weekly certified payrolls (DOL Form WH-347)
- Records retention: 3 years
- Deductions: Limited (taxes, insurance, court orders)

**Successor Contractor Obligations**:

- Must offer employment to predecessor's employees
- Wages/benefits cannot be lower than predecessor's (for 1st year)
- Seniority transfer (vacation accrual continues)

**Common Mistakes**:

- ❌ Using old WD revision → UNDERPAYMENT (check for updates before proposal)
- ❌ Not including fringe benefits in labor rates → UNDERBID (unallowable costs)
- ❌ Misclassifying employees → LOWER WAGE PAID (must match duties to WD categories)
- ❌ Not offering predecessor employees jobs → SCA VIOLATION
- ❌ Missing certified payroll deadlines → DOL INVESTIGATION

#### Compliance Checklist

- [ ] Wage determination (WD) obtained (check for latest revision)
- [ ] Labor categories mapped to WD (job duties match WD descriptions)
- [ ] Wage/benefit rates calculated (base wage + fringe benefits)
- [ ] Payroll system configured (WH-347 form generation)
- [ ] Successor obligations identified (if incumbent contract)
- [ ] Predecessor employee list requested (from current contractor)
- [ ] Records retention process (3-year requirement)
- [ ] DOL poster displayed (workplace notification)

#### Flowdown Requirements

**Selective**: Flows to subs performing service work (not materials/supplies)

#### Cost Impact

**MEDIUM**:

- Wage premium over market: 5-20% (SCA rates often higher than commercial)
- Fringe benefits: $4.80/hour minimum ($9,984/year per FTE)
- Payroll administration: $2K-$5K annually (certified payroll processing)
- Successor obligation: Potential overstaffing (must hire predecessor's employees)

#### Evaluation Factor Linkage

**Price**: Labor rates must comply with WD (government verifies)  
**Management Approach**: Workforce transition plan (if successor)  
**Past Performance**: SCA compliance history (DOL violations on record)

**Proposal Strategy**: Include labor rate table showing WD compliance, describe payroll certification process, if successor contract provide transition plan with predecessor employee offers

---

## Section 5: FAR 52.219 Series - Small Business Programs

### FAR 52.219-14 Limitations on Subcontracting

**Effective Date**: JAN 2024  
**Incorporation**: Full text for small business set-asides  
**Criticality**: HIGHEST - Determines small business eligibility

#### Clause Implications

**Percentage Requirements**:

- Services: Prime must perform ≥50% of cost of contract performance
- Supplies: Prime must perform ≥50% of cost of manufacturing (excluding materials)
- General construction: Prime must perform ≥15% of cost of contract
- Special trade construction: Prime must perform ≥25% of cost of contract

**Calculation**:

- Cost of performance: Direct labor + overhead (not materials)
- Similarly situated entities: Small business subs in same NAICS count toward prime's performance
- Exclusions: Materials, supplies, off-the-shelf items

**Compliance Verification**:

- Self-certification at proposal (honest estimate)
- Final verification at contract completion
- Quarterly reporting: Not required for this clause (unlike 52.219-9)

**Penalties**:

- Breach of contract (if limits exceeded)
- False certification (if intentional misrepresentation)
- Suspension/debarment (for repeated violations)
- Loss of small business preferences (future contracts)

**Common Mistakes**:

- ❌ Counting materials toward prime's 50% → OVERCOUNTING (materials excluded)
- ❌ Using large business subs without considering impact → LIMIT VIOLATION
- ❌ Not identifying similarly situated subs → MISSED OPPORTUNITY (SB subs count for prime)
- ❌ Winning on low price then subcontracting 80% → BAIT & SWITCH

#### Compliance Checklist

- [ ] Prime performance percentage calculated (exclude materials)
- [ ] Subcontracting plan drafted (identify large vs small subs)
- [ ] Similarly situated entities identified (small business subs in same NAICS)
- [ ] Work breakdown structure (WBS) created (track prime vs sub work)
- [ ] Cost tracking system configured (monitor percentage throughout performance)
- [ ] Quarterly self-checks (ensure limits not exceeded)

#### Flowdown Requirements

**Cascading**: Small business subs with set-aside subcontracts must also comply with limits

#### Cost Impact

**VARIABLE**:

- Overhead on internal labor: Higher internal costs vs subcontracting
- Hiring temp employees: To meet 50% requirement if needed
- Risk: Fixed-price risk if prime performs work instead of subcontracting

#### Evaluation Factor Linkage

**Small Business**: Subcontracting plan evaluated (if applicable)  
**Technical Approach**: Work allocation (prime vs sub)  
**Past Performance**: Limits compliance history (protests, SBA investigations)

**Proposal Strategy**: Clearly show prime's 50%+ performance in SOW tasks, identify similarly situated small business subs (count toward prime's percentage), provide WBS showing work allocation

---

### FAR 52.219-9 Small Business Subcontracting Plan (if large business prime)

**Effective Date**: JAN 2024  
**Incorporation**: Full text for large business primes >$750K  
**Criticality**: HIGH - Plan evaluated, non-compliance = poor CPARS

#### Clause Implications

**Goals Required**:

- Small business (SB): Percentage of subcontract dollars
- Small disadvantaged business (SDB): 8(a) program participants
- Women-owned small business (WOSB): Certified WOSB
- HUBZone small business: Historically underutilized business zones
- Veteran-owned small business (VOSB): Veteran-owned
- Service-disabled veteran-owned (SDVOSB): Service-disabled veteran-owned

**Goal Setting**:

- Industry-specific: Percentages vary by NAICS code (check SBA scorecards)
- Historical: Prime's past performance informs goals
- Solicitation guidance: RFP may suggest goals
- Realistic: Must be achievable (overpromising = poor CPARS)

**Plan Elements** (11 required):

1. Separate goals for each category (SB, SDB, WOSB, etc.)
2. Statement of total dollars planned for subcontracting
3. Description of efforts to ensure SB participation
4. Designated SB liaison officer (name, title, contact)
5. Flowdown of SB plan to large subs >$750K
6. Records retention (3 years)
7. Cooperation with compliance reviews (audits)
8. Outreach efforts (SB conferences, matchmaking)
9. Monitoring and reporting procedures
10. Equitable award distribution (no bundling that excludes SB)
11. Dispute resolution process

**Reporting**:

- Electronic Subcontracting Reporting System (eSRS)
- Semi-annual reports: April 30 and October 30
- Individual subcontract report (ISR): Each subcontract >$750K
- Summary subcontract report (SSR): All contracts combined

**Evaluation**:

- Commercial plans: Accepted/rejected (no scoring)
- Individual plans: Scored as part of proposal evaluation
- Weight: 5-15% of total evaluation (varies by RFP)

**Common Mistakes**:

- ❌ Setting unrealistic goals → POOR CPARS (if not achieved)
- ❌ Not submitting eSRS reports → LATE PAYMENT WITHHELD (per FAR 52.242-5)
- ❌ Counting large business subs toward SB goals → eSRS AUDIT FINDING
- ❌ Not appointing SB liaison → INCOMPLETE PLAN (non-responsive)
- ❌ Copy-paste plan from prior proposal → GENERIC (low evaluation score)

#### Compliance Checklist

- [ ] SB subcontracting goals established (by category: SB, SDB, WOSB, HUBZone, VOSB, SDVOSB)
- [ ] Goals benchmarked (industry averages, prime's historical performance)
- [ ] SB liaison appointed (name, title, contact in plan)
- [ ] Outreach strategy documented (conferences, matchmaking, databases)
- [ ] eSRS account created (https://www.esrs.gov)
- [ ] Reporting calendar established (April 30, October 30 deadlines)
- [ ] Monitoring procedures drafted (quarterly tracking, corrective action)
- [ ] Flowdown language prepared (for large subs >$750K)

#### Flowdown Requirements

**Selective**: Flows to large business subs with subcontracts >$750K

#### Cost Impact

**LOW-MEDIUM**:

- Plan development: $3K-$10K (first time), $1K-$3K (updates)
- eSRS reporting: $2K-$5K annually (admin time)
- Outreach: $5K-$15K annually (conferences, sponsorships)
- SB liaison: 10-20% FTE ($15K-$30K annually)

#### Evaluation Factor Linkage

**Small Business Factor** (if separate evaluation factor):

- Goal quality: Realistic yet aggressive goals (5-10% above industry average)
- Outreach strategy: Specific conferences, databases, partnerships
- Past performance: Historical SB utilization (eSRS data)
- Monitoring: Quarterly tracking, corrective action for underperformance

**Scoring Range** (typical):

- Outstanding: Goals >10% above industry average, detailed outreach, proven track record
- Good: Goals meet industry average, solid outreach, some past performance
- Acceptable: Goals slightly below average, basic outreach, limited past performance
- Marginal: Goals significantly below average, weak outreach, poor past performance
- Unacceptable: Goals unrealistic, no outreach, history of non-compliance

**Proposal Strategy**:

**Plan Narrative** (10-15 pages typical):

1. **Goals Table**:

   ```
   Category          | Goal  | Industry Avg | Justification
   ------------------|-------|--------------|------------------------
   Small Business    | 45%   | 40%          | Aggressive outreach to...
   SDB               | 12%   | 10%          | Partnership with 8(a)...
   WOSB              | 8%    | 5%           | WOSB mentor-protégé...
   HUBZone           | 5%    | 3%           | Regional HUBZone focus
   VOSB              | 7%    | 6%           | Veteran hiring initiative
   SDVOSB            | 4%    | 3%           | SDVOSB teaming agreements
   ```

2. **Outreach Strategy**:

   - Specific conferences: "Annual NMSDC Conference, WBENC Summit"
   - Databases: "SAM.gov daily searches, SBA SUB-Net, state procurement portals"
   - Partnerships: "Mentor-protégé agreements with 3 small businesses"
   - Matchmaking: "Monthly small business meet-and-greet events"

3. **Monitoring Procedures**:

   - Quarterly tracking: SB liaison reviews spending vs goals
   - Corrective action: If <80% of goal at midpoint, increase outreach
   - eSRS reporting: Semi-annual submissions (April 30, October 30)
   - Annual review: Adjust goals based on actual utilization

4. **Past Performance**:
   - "Contract X (Army): Achieved 48% SB utilization (goal 40%). CPARS: Exceptional."
   - "Contract Y (Navy): Exceeded WOSB goal by 15%. Received SBA Subcontracting Excellence Award."

**Discriminators** (competitive advantages):

- ✅ Goals significantly above industry average (10%+ higher)
- ✅ Proven track record (eSRS data showing consistent goal achievement)
- ✅ Mentor-protégé agreements (demonstrates commitment beyond contractual requirement)
- ✅ SBA awards/recognition (Subcontracting Excellence, Dwight D. Eisenhower Award)
- ✅ Dedicated SB liaison (full-time, not collateral duty)

---

## Section 6: Clause Cost Impact Summary

### Cost Planning Table

Use this table to estimate compliance costs during proposal development:

| Clause                                    | One-Time Cost | Annual Cost | Risk of Non-Compliance      | Priority                   |
| ----------------------------------------- | ------------- | ----------- | --------------------------- | -------------------------- |
| **FAR 52.212-1**                          | $0            | $0          | REJECTION                   | CRITICAL                   |
| **FAR 52.212-3**                          | $5K-$25K      | $2K-$5K     | PROTEST, FALSE CLAIMS       | CRITICAL                   |
| **FAR 52.212-4**                          | $5K-$15K      | $5K-$10K    | DEFAULT, WARRANTY CLAIMS    | HIGH                       |
| **FAR 52.212-5 (SB Plan)**                | $3K-$10K      | $2K-$5K     | POOR CPARS                  | HIGH                       |
| **FAR 52.219-14**                         | $0            | $0          | SUSPENSION/DEBARMENT        | CRITICAL (if SB set-aside) |
| **FAR 52.222-41 (SCA)**                   | $2K-$5K       | $10K-$30K   | BACK PAY, DOL INVESTIGATION | HIGH (services)            |
| **FAR 52.222-50 (Trafficking)**           | $5K-$15K      | $5K-$15K    | TERMINATION, CRIMINAL       | HIGH (overseas)            |
| **DFARS 252.204-7012 (NIST)**             | $50K-$200K    | $10K-$50K   | TERMINATION, BREACH         | CRITICAL (DoD)             |
| **DFARS 252.204-7020**                    | $25K-$75K     | $0          | AWARD DELAY                 | HIGH (DoD)                 |
| **DFARS 252.225-7021 (TAA)**              | $5K-$20K      | $0          | FALSE CLAIMS                | MEDIUM                     |
| **DFARS 252.225-7049 (Specialty Metals)** | $2K-$10K      | $0          | TERMINATION                 | HIGH (defense hardware)    |

**Total Compliance Cost Range** (for typical DoD services contract >$5M):

- **Initial**: $100K-$350K (first year with NIST 800-171 implementation)
- **Annual**: $30K-$100K (maintenance, reporting, audits)
- **3-Year Total Cost of Ownership**: $200K-$550K

**Cost Recovery**:

- Many compliance costs are allowable under FAR 31.205-47 (but not all)
- Some costs may be unallowable (e.g., fines, penalties, interest on late invoices)
- Indirect cost rates should include compliance costs in overhead pool

---

## Section 7: Integration with Ontology

### How This Library Enhances Entity Extraction

**Before FAR/DFARS Library** (generic extraction):

```json
{
  "entity_name": "FAR 52.212-4",
  "entity_type": "CLAUSE",
  "description": "Contract Terms and Conditions—Commercial Products and Commercial Services"
}
```

**After FAR/DFARS Library** (enhanced extraction):

```json
{
  "entity_name": "FAR 52.212-4 Contract Terms and Conditions—Commercial",
  "entity_type": "CLAUSE",
  "clause_number": "FAR 52.212-4",
  "effective_date": "JAN 2024",
  "agency_supplement": "FAR",
  "criticality": "HIGHEST",
  "description": "Core contract obligations including inspection/acceptance (para a), changes (para c), payments (para i), excusable delays (para f), and warranty (para m). Contractor must file REA within 30 days of changed work or waive rights. Prompt Payment Act requires payment within 30 days of proper invoice.",
  "compliance_cost_one_time": "$5K-$15K",
  "compliance_cost_annual": "$5K-$10K",
  "flowdown_requirement": "Selective (Inspection, Changes, Warranty to subs)",
  "proposal_strategy_hint": "Describe inspection/acceptance procedures in Quality section, include change order flowchart, specify warranty terms beyond implied",
  "evaluation_factors": [
    "Technical Approach (QA procedures)",
    "Management Approach (change order process)",
    "Past Performance (warranty claims history)"
  ],
  "common_mistakes": [
    "Invoicing before acceptance → payment delay",
    "Missing 30-day REA deadline → waive claim rights",
    "Not notifying CO of excusable delay within 10 days → default termination risk"
  ]
}
```

**Benefit**: Proposal teams understand operational implications, not just legal boilerplate!

---

## Usage Examples

### Example 1: Extraction Prompt Enhancement

**Original Prompt** (generic):

```
Extract FAR and DFARS clauses. For each clause, identify:
- Clause number (e.g., FAR 52.212-4)
- Clause title
- Brief description
```

**Enhanced Prompt** (with FAR/DFARS library reference):

```
Extract FAR and DFARS clauses using the compliance library context below.

For each clause, identify:
- Clause number (e.g., FAR 52.212-4)
- Effective date (e.g., JAN 2024)
- Agency supplement (FAR, DFARS, AFFARS, NMCARS, etc.)
- Criticality level (ABSOLUTE, HIGHEST, HIGH, MEDIUM, LOW)
- Operational implications (what contractor must DO, not just legal text)
- Compliance cost estimate (one-time + annual)
- Flowdown requirements (to subcontractors)
- Evaluation factor linkage (which factors evaluate this clause)
- Common mistakes (what proposal teams miss)

[APPEND: Full FAR/DFARS Compliance Library - 30K tokens]
```

**Result**: LLM extracts clauses with full operational context, not just legal citations!

### Example 2: Query Response Enhancement

**User Query**: "What are the cybersecurity requirements?"

**Generic Response** (without library):

```
The solicitation includes DFARS 252.204-7012 Safeguarding Covered Defense Information
and Cyber Incident Reporting. This clause requires compliance with NIST SP 800-171.
```

**Enhanced Response** (with library):

```
The solicitation includes DFARS 252.204-7012 (DEC 2019) requiring NIST SP 800-171
compliance (110 security controls across 17 families). Key operational requirements:

1. **System Security Plan (SSP)**: Document how all 110 controls are implemented
2. **SPRS Score Submission**: Upload assessment results before contract award
3. **Plan of Action & Milestones (POA&M)**: Document any control gaps with remediation plan
4. **72-Hour Incident Reporting**: Email DoDCIO.CyberSecurity@mail.mil within 72 hours of breach
5. **Media Sanitization**: NIST SP 800-88 procedures for all hard drives/media
6. **Subcontractor Flowdown**: ALL subs handling CDI must comply (verify SPRS scores)

**Cost Impact**: $50K-$200K initial implementation, $10K-$50K annual maintenance

**Evaluation Factors Affected**:
- Technical Approach (15-25% weight): Cybersecurity architecture, SIEM, encryption
- Management Approach: Risk management, POA&M tracking, incident response
- Past Performance: CPARS cybersecurity ratings, incident history

**Proposal Strategy**: Dedicate 3-5 pages to cybersecurity in Technical Volume,
include network diagram with CDI enclave, document current SPRS score (e.g., "-6 with
2 POA&M items closing March 2025"), provide 72-hour incident response flowchart.

**Common Mistakes to Avoid**:
- Not submitting SPRS score before award → Award delayed/withdrawn
- Treating POA&M as permanent workaround → Must close per schedule
- Not flowing to all subs handling CDI → Prime liable for sub breaches
```

**Benefit**: 10-20 hours of compliance research saved per RFP!

---

## Maintenance and Updates

### Keeping This Library Current

**Clause Revision Tracking**:

- FAR/DFARS updated quarterly (check Acquisition.gov)
- Effective dates change (e.g., JAN 2024 → JAN 2025)
- Cost estimates adjust annually (wage determination updates, H&W rates)

**Update Schedule**:

- Quarterly: Check for clause revisions (FAR Council website)
- Annually: Update cost estimates (inflation, market rates)
- As needed: Add new clauses as they're promulgated (e.g., CMMC final rule)

**Version Control**:

- Current version: 1.0 (January 2025)
- Next review: April 2025 (Q2 FAR/DFARS updates)
- Update log: Track clause revisions, cost adjustments, new compliance requirements

---

## Conclusion

This FAR/DFARS Compliance Library transforms clause extraction from legal boilerplate recognition into **operational intelligence** for proposal teams. By embedding 30K tokens of domain expertise, the LLM can:

1. **Extract with context** - Not just "FAR 52.212-4 exists" but "FAR 52.212-4 requires 30-day REA filing or rights waived"
2. **Link to evaluation** - "DFARS 252.204-7012 affects Technical Approach (cybersecurity), Management Approach (risk), Past Performance (CPARS)"
3. **Estimate costs** - "NIST 800-171 compliance: $50K-$200K initial, $10K-$50K annual"
4. **Prevent mistakes** - "Don't invoice before acceptance or 30-day Prompt Payment clock won't start"
5. **Guide proposals** - "Dedicate 3-5 pages to cybersecurity, include network diagram, document SPRS score"

**Integration**: Append this library to `entity_extraction_prompt.md` as Section 8 reference material.

**Cost Justification**: 30K tokens = 1.5% of 2M budget, but saves 10-20 hours per RFP in compliance research.

**Next**: Create Shipley Methodology Patterns library (15K tokens) for win theme development and compliance matrix templates.

---

**Version**: 1.0  
**Last Updated**: January 26, 2025  
**Next Review**: April 2025 (Q2 FAR/DFARS updates)  
**Maintainer**: Branch 011 - Prompt Enhancements Team
