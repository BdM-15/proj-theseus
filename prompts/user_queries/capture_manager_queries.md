# Capture Manager Query Library

**Purpose**: Production-ready queries for RFP analysis, proposal development, and BOE/BOM planning  
**Audience**: Capture Managers, Proposal Managers, Pricing Analysts, Technical Writers  
**Methodology**: Based on Shipley Capture & Proposal Guide principles  
**Usage**: Copy query → Customize [PLACEHOLDERS] → Paste into LightRAG `/webui` query interface

**Last Updated**: November 2025 (Branch 013 - Workload Inference Architecture)

---

## Quick Reference Guide

| Analysis Goal            | Query Category | Primary Queries      |
| ------------------------ | -------------- | -------------------- |
| **Labor BOE**            | Category 1     | Q1.1, Q1.2, Q1.3     |
| **Bill of Materials**    | Category 2     | Q2.1, Q2.2, Q2.3     |
| **Quality/Compliance**   | Category 3     | Q3.1, Q3.2           |
| **Logistics**            | Category 4     | Q4.1, Q4.2           |
| **Lifecycle Costs**      | Category 5     | Q5.1, Q5.2           |
| **Complete BOE Package** | Category 6     | Q6.1 (comprehensive) |
| **GFE/Facilities**       | Category 7     | Q7.1, Q7.2           |
| **Evaluation Strategy**  | Category 8     | Q8.1, Q8.2, Q8.3     |
| **Compliance Check**     | Category 9     | Q9.1, Q9.2           |
| **Amendment Analysis**   | Category 10    | Q10.1, Q10.2         |

---

## Category 1: Labor Workload (FTE/BOE Calculation)

### Query 1.1: Complete Labor Workload Breakdown

**Use Case**: Calculate Full-Time Equivalent (FTE) requirements and develop labor Basis of Estimate

```
Provide a comprehensive list of ALL labor workload drivers for [APPENDIX/SECTION NAME] services.

Workload drivers include:
- Service frequencies (daily, weekly, monthly, continuous, on-demand)
- Operating hours and shift coverage (8x5, 24/7, business hours, etc.)
- Staffing levels (FTE requirements, team sizes, ratios)
- Response time requirements (SLA targets, emergency response times)
- Quality assurance activities (inspections, audits, reviews)
- Training requirements (initial, recurring, certification)
- Administrative tasks (reporting, documentation, meetings)
- Peak demand periods (seasonal, event-driven)

Organization:
- Start with a brief summary of the appendix/section scope
- Group workload drivers by PWS subsection in logical order
- For each driver, include: description, frequency/quantity, location/coverage area, rationale/context
- Highlight MANDATORY vs IMPORTANT requirements
- Flag implicit workload (e.g., "24/7 coverage" implies 3-shift staffing)

Focus on TOTALITY - provide ALL quantifiable workload metrics, not samples. This data will be used to develop labor Basis of Estimate and calculate Full-Time Equivalent (FTE) requirements.

Example: "Provide a comprehensive list of ALL labor workload drivers for Appendix F Food Services."
```

**Expected Output**:

- Executive summary (scope, estimated FTE range)
- Detailed breakdown by PWS subsection
- Service frequencies quantified (3x daily, weekly, monthly)
- Shift coverage requirements (8x5, 12x7, 24/7)
- Staffing ratios (1 supervisor per 10 staff, 2-person teams)
- Response time SLAs (15 min emergency, 4 hr routine)
- Training hours (40 hr initial, 8 hr annual)
- Reporting workload (daily logs, weekly summaries, monthly reports)

---

### Query 1.2: Skill Mix & Labor Category Analysis

**Use Case**: Determine labor category distribution for pricing proposal

```
Analyze the skill mix and labor category requirements for [APPENDIX/SECTION NAME] services.

Extract:
1. TECHNICAL LABOR:
   - Engineering disciplines (mechanical, electrical, software, etc.)
   - Technicians (senior, journeyman, apprentice levels)
   - Specialized certifications (AWS, CISSP, PMP, trade licenses)

2. ADMINISTRATIVE LABOR:
   - Program management (PM, APM, coordinators)
   - Administrative support (clerks, data entry, schedulers)
   - Quality assurance (QA managers, inspectors, auditors)

3. OPERATIONAL LABOR:
   - Service delivery staff (operators, drivers, handlers)
   - Supervisors and leads (shift supervisors, team leads)
   - Security personnel (guards, access control, surveillance)

4. SKILL LEVEL DISTRIBUTION:
   - Senior/Expert (10+ years experience)
   - Intermediate/Journeyman (5-9 years experience)
   - Junior/Entry (0-4 years experience)
   - Apprentice/Trainee (on-the-job training)

5. SPECIAL REQUIREMENTS:
   - Security clearances (Secret, Top Secret, TS/SCI)
   - Professional licenses (PE, electrician, HVAC, CDL)
   - Government certifications (DoD 8570, FAC-COR)
   - Language requirements (Arabic, Korean, etc.)

Organize in tabular format:
| Labor Category | Quantity | Skill Level | Clearance | Certifications | Hourly Rate Estimate |

This data drives labor rate development and competitive pricing strategy.

Example: "Analyze skill mix and labor category requirements for Appendix I Warehouse Operations."
```

**Expected Output**:

- Labor category table with quantities and requirements
- Skill level pyramid (ratio of senior:mid:junior)
- Clearance distribution (% requiring Secret, TS, TS/SCI)
- Certification matrix (which categories need which certs)
- Competitive rate benchmarks (if historical data available)

---

### Query 1.3: Cross-Appendix Labor Comparison

**Use Case**: Optimize resource allocation across multiple service areas

```
Compare labor workload drivers across [APPENDIX A], [APPENDIX B], and [APPENDIX C] services.

For each appendix, provide:
1. Total estimated FTE requirements (based on hours, coverage, frequencies)
2. Skill mix breakdown (technical, administrative, supervisory ratios)
3. Shift coverage requirements (8x5, 12x7, 24/7)
4. Peak staffing periods (seasonal, event-driven surges)
5. Unique workload characteristics (specialized skills, clearances, licenses)

Organize in comparative table format:
| Appendix | Scope Summary | Est. FTE | Skill Mix | Shift Coverage | Peak Periods | Special Requirements |

Identify:
- Cross-utilization opportunities (shared resources across appendices)
- Economies of scale (bulk training, shared supervision)
- Staffing conflicts (competing peak periods)
- Risk areas (hard-to-find skills, clearance bottlenecks)

This comparison drives staffing optimization and competitive cost positioning.

Example: "Compare labor workload across Appendix F Food Services, Appendix G Custodial, and Appendix H Grounds Maintenance."
```

**Expected Output**:

- Comparative table showing FTE by appendix
- Cross-utilization matrix (which services share labor pools)
- Peak period calendar (identify staffing conflicts)
- Risk assessment (hard-to-fill positions, clearance delays)
- Optimization recommendations (shared supervisors, bulk training)

---

## Category 2: Bill of Materials (BOM) Workload

### Query 2.1: Complete Material/Supply Inventory

**Use Case**: Develop comprehensive Bill of Materials for cost proposal

```
Provide a comprehensive inventory of ALL material, supply, and equipment requirements for [APPENDIX/SECTION NAME] services.

Categories to extract:
1. CONSUMABLES (recurring purchases):
   - Item description, quantity per period, frequency, unit specifications
   - Example: "750 tubs disinfectant wipes (700-count), annually"

2. EQUIPMENT (capital/durable goods):
   - Item description, quantity, model/specifications, replacement cycle
   - Example: "8 refrigeration units (commercial-grade, NSF certified)"

3. SPARE PARTS & MAINTENANCE SUPPLIES:
   - Critical spares inventory levels, reorder points, lead times
   - Example: "HVAC filters: 200 units quarterly, 30-day safety stock"

4. GOVERNMENT-FURNISHED EQUIPMENT (GFE):
   - Items provided by government (note: affects cost proposal)
   - Contractor-furnished vs GFE distinction

5. SPECIALTY ITEMS:
   - Licensed/certified materials, controlled substances, hazmat
   - Compliance requirements (Berry Amendment, TAA, NSN-listed)

Organization:
- Group by PWS subsection
- Include quantities, frequencies, specifications, vendor constraints
- Distinguish one-time (capital) vs recurring (consumable) costs
- Note delivery locations if multiple sites
- Flag GFE items (reduce contractor costs)

Focus on TOTALITY - this data drives BOM development and procurement planning.

Example: "Provide a comprehensive inventory of ALL material and equipment requirements for Appendix I Warehouse Operations."
```

**Expected Output**:

- Consumables list with annual quantities and costs
- Capital equipment list with specs and replacement cycles
- Spare parts inventory (safety stock levels)
- GFE vs contractor-furnished breakdown
- Compliance flagging (Berry, TAA, NSN requirements)
- Total material budget estimate (consumables + capital)

---

### Query 2.2: Equipment Replacement & Lifecycle Planning

**Use Case**: Forecast out-year capital equipment costs

```
Identify ALL equipment replacement cycles and lifecycle costs for [APPENDIX/SECTION NAME] services.

Extract:
1. MAJOR EQUIPMENT:
   - Equipment type, quantity, acquisition cost, expected service life
   - Replacement schedule (Year 1, 3, 5, etc.)

2. REFRESH CYCLES:
   - IT hardware (3-5 years typical)
   - Vehicles (5-7 years or mileage-based)
   - HVAC/mechanical (10-15 years)
   - Facility equipment (varies by type)

3. TECHNOLOGY OBSOLESCENCE:
   - Software licenses (annual renewals, version upgrades)
   - Communication equipment (technology changes)
   - Security systems (compliance-driven upgrades)

4. WARRANTY PERIODS:
   - Manufacturer warranties (parts, labor, duration)
   - Extended service agreements (cost, coverage)

5. DISPOSAL COSTS:
   - E-waste disposal (computers, electronics)
   - Hazmat disposal (batteries, refrigerants)
   - Data sanitization (NIST 800-88 compliance)

Organize in lifecycle table:
| Equipment | Qty | Acquisition Cost | Service Life | Year 1 | Year 2 | Year 3 | Year 4 | Year 5 | Disposal |

This data drives out-year pricing and technology refresh budgeting.

Example: "Identify ALL equipment replacement cycles for Appendix K IT Infrastructure services."
```

**Expected Output**:

- Equipment inventory with service lives
- Replacement schedule (which years trigger capital costs)
- Warranty coverage analysis (manufacturer vs contractor)
- Technology refresh calendar (software, hardware, systems)
- Disposal cost estimates (e-waste, hazmat, data sanitization)
- Total lifecycle cost projection (5-year view)

---

### Query 2.3: Supply Chain & Vendor Analysis

**Use Case**: Identify procurement constraints and vendor dependencies

```
Analyze supply chain requirements and vendor constraints for [APPENDIX/SECTION NAME] services.

Extract:
1. PROCUREMENT CONSTRAINTS:
   - Berry Amendment compliance (domestic manufacture)
   - Trade Agreements Act (TAA) compliance
   - NSN-listed items only (National Stock Number)
   - Approved vendor lists (AVL restrictions)

2. LEAD TIMES:
   - Standard procurement cycles (30, 60, 90 days)
   - Long-lead items (180+ days, special order)
   - Just-in-time vs safety stock strategy

3. VENDOR DEPENDENCIES:
   - Sole source items (single vendor only)
   - Preferred vendors (government relationships)
   - Small business set-aside requirements

4. PRICING VOLATILITY:
   - Commodity pricing (fuel, metals, chemicals)
   - Foreign exchange exposure (imported goods)
   - Seasonal pricing (agriculture, utilities)

5. RISK MITIGATION:
   - Alternate vendors (backup suppliers)
   - Inventory buffers (safety stock levels)
   - Price escalation clauses (protect margins)

Organize by risk level (HIGH, MEDIUM, LOW) and mitigation strategy.

This data drives procurement strategy and pricing risk management.

Example: "Analyze supply chain requirements for Appendix F Food Services (Berry Amendment, vendor dependencies)."
```

**Expected Output**:

- Compliance matrix (Berry, TAA, NSN requirements by item)
- Lead time analysis (identify long-lead bottlenecks)
- Vendor risk assessment (sole source, dependencies)
- Pricing volatility forecast (commodity exposure)
- Mitigation strategies (alternates, inventory, clauses)

---

## Category 3: Quality Assurance & Compliance Workload

### Query 3.1: QA/Inspection Workload Assessment

**Use Case**: Calculate quality assurance labor and third-party inspection costs

```
Extract ALL quality assurance, inspection, and compliance workload for [APPENDIX/SECTION NAME] services.

Categories:
1. INSPECTION REQUIREMENTS:
   - Inspection type (visual, functional, destructive, sample-based)
   - Inspection frequency (100%, 10% sampling, quarterly audits)
   - Acceptance criteria and standards

2. CERTIFICATIONS & TESTING:
   - Required certifications (material certs, test reports)
   - Testing protocols (lab analysis, performance verification)
   - Third-party inspection requirements

3. REGULATORY COMPLIANCE:
   - Applicable regulations (Berry Amendment, ITAR, TAA, OSHA)
   - Documentation requirements (COC, MSDS, training records)
   - Audit frequency (annual, quarterly, continuous)

4. QUALITY METRICS:
   - Performance standards (defect rates, SLA targets)
   - Measurement frequency (real-time, daily, monthly)
   - Reporting requirements (dashboards, KPI reports)

5. LABOR IMPACT:
   - QA staffing levels (inspectors, auditors, analysts)
   - Specialized skills (certified inspectors, licensed technicians)
   - Time allocation (% of total labor for QA activities)

Organize by compliance category and quantify all inspection/testing frequencies.

This workload drives QA labor costs, third-party inspection fees, and certification expenses.

Example: "Extract ALL quality assurance and compliance workload for Appendix G Equipment Maintenance services."
```

**Expected Output**:

- Inspection matrix (type, frequency, acceptance criteria)
- Certification requirements (material certs, test reports)
- Regulatory compliance checklist (Berry, ITAR, OSHA)
- QA labor estimate (inspectors, auditors, % of total)
- Third-party costs (lab testing, certification audits)
- Quality metrics reporting workload

---

### Query 3.2: Compliance Risk Assessment

**Use Case**: Identify regulatory risks and mitigation strategies

```
Assess regulatory compliance risks and requirements for [APPENDIX/SECTION NAME] services.

Analyze:
1. MANDATORY COMPLIANCE:
   - FAR/DFARS clauses (cybersecurity, trafficking, wages)
   - Executive orders (supply chain, climate, diversity)
   - Industry standards (ISO 9001, AS9100, CMMI)

2. CERTIFICATION GAPS:
   - Required certifications not currently held
   - Time to achieve certification (months)
   - Cost to achieve certification ($)

3. ONGOING COMPLIANCE:
   - Annual recertification requirements
   - Continuous monitoring obligations (NIST 800-171)
   - Training frequency (annual, biennial)

4. AUDIT EXPOSURE:
   - Government audit frequency (annual, ad-hoc)
   - Audit scope (financial, technical, quality)
   - Penalties for non-compliance (contract termination)

5. MITIGATION STRATEGIES:
   - Subcontractor partnerships (leverage their certs)
   - Certification roadmap (timeline to achieve)
   - Compliance monitoring systems (automation)

Organize by risk level (CRITICAL, HIGH, MEDIUM, LOW) with mitigation plans.

This assessment drives certification budgets and compliance labor allocation.

Example: "Assess regulatory compliance risks for Appendix K IT Infrastructure (NIST 800-171, ISO 27001)."
```

**Expected Output**:

- Compliance requirements matrix
- Certification gap analysis (what's missing)
- Certification roadmap (timeline, costs)
- Ongoing compliance workload (monitoring, training)
- Risk assessment (audit exposure, penalties)
- Mitigation strategies (subcontracting, automation)

---

## Category 4: Logistics & Distribution Workload

### Query 4.1: Complete Logistics Workload Analysis

**Use Case**: Calculate transportation, warehousing, and distribution costs

```
Identify ALL logistics and distribution workload drivers for [APPENDIX/SECTION NAME] services.

Extract:
1. DELIVERY FREQUENCIES:
   - Scheduled deliveries (daily, weekly, monthly)
   - On-demand/emergency delivery requirements
   - Peak delivery periods (seasonal surges)

2. DISTRIBUTION COMPLEXITY:
   - Number of delivery locations (sites, buildings, zones)
   - Geographic spread (CONUS, OCONUS, remote locations)
   - Access constraints (security clearances, restricted areas)

3. STORAGE REQUIREMENTS:
   - Warehouse space (square footage, climate control, security)
   - Inventory management system requirements
   - Hazmat storage (special facilities, licenses)

4. TRANSPORTATION:
   - Vehicle types (trucks, forklifts, specialized transport)
   - Mileage/distance estimates (per delivery, per month)
   - Special handling (refrigerated, oversized, hazmat)

5. LEAD TIMES:
   - Standard procurement cycles
   - Emergency/expedited delivery SLAs
   - Government approval processes

Organize by service area and quantify all metrics (frequencies, distances, volumes, storage capacity).

This data impacts transportation costs, warehouse lease requirements, and inventory carrying costs in the price proposal.

Example: "Identify ALL logistics and distribution workload drivers for Appendix I Warehouse Operations."
```

**Expected Output**:

- Delivery frequency matrix (daily, weekly, monthly by location)
- Distribution site map (number of locations, distances)
- Storage requirements (warehouse sq ft, climate control)
- Transportation workload (vehicle types, mileage estimates)
- Lead time analysis (procurement to delivery cycles)
- Total logistics cost estimate (transport + warehouse + handling)

---

### Query 4.2: Government-Furnished Equipment & Facilities

**Use Case**: Identify GFE/GFF to reduce contractor costs

```
Provide a total list of Government-Furnished Equipment (GFE) and Government-Furnished Facilities (GFF) for [APPENDIX/SECTION NAME] services.

Extract:
1. EQUIPMENT PROVIDED BY GOVERNMENT:
   - Item description, quantity, condition (new, refurbished, as-is)
   - Delivery timeline (available at contract start, phased delivery)
   - Maintenance responsibility (government, contractor, shared)

2. FACILITIES PROVIDED BY GOVERNMENT:
   - Facility type (warehouse, office, workspace, secure areas)
   - Square footage, utilities included, access hours
   - Condition (move-in ready, requires renovation)

3. CONTRACTOR-FURNISHED ALTERNATIVES:
   - Items contractor must provide if GFE unavailable
   - Cost impact (lease vs purchase vs GFE)
   - Lead times (procurement, installation)

4. RISK FACTORS:
   - GFE delivery delays (impact on contract start)
   - GFE condition issues (maintenance, obsolescence)
   - Facility access restrictions (security, hours)

Organization:
- Group by relevant PWS section in logical manner
- Distinguish GFE vs contractor-furnished clearly
- Calculate cost savings from GFE/GFF
- Flag delivery dependencies and risks

This knowledge helps us know if we need to lease equipment and save costs. Focus on totality, not samples.

Example: "Provide total list of Government-Furnished Equipment and Facilities for Appendix F Food Services."
```

**Expected Output**:

- GFE inventory (item, qty, condition, delivery timeline)
- GFF description (facilities, sq ft, utilities, access)
- Cost savings analysis (GFE vs contractor-furnished)
- Risk assessment (delivery delays, condition issues)
- Contingency planning (if GFE unavailable, contractor provides)

---

## Category 5: Lifecycle & Sustainment Workload

### Query 5.1: Lifecycle Workload Analysis

**Use Case**: Forecast sustainment labor and parts costs for out-years

```
Identify ALL lifecycle, sustainment, and end-of-life workload for [APPENDIX/SECTION NAME] services.

Extract:
1. PREVENTIVE MAINTENANCE:
   - PM schedules (daily, weekly, monthly, quarterly, annual)
   - Time per PM task (labor hours)
   - Parts/materials consumed during PM

2. CORRECTIVE MAINTENANCE:
   - Mean Time Between Failure (MTBF) estimates
   - Average repair times
   - Spare parts inventory requirements (% of installed base)

3. WARRANTY & SERVICE AGREEMENTS:
   - Warranty periods (manufacturer, extended)
   - Service level agreements (response times, uptime guarantees)
   - Annual maintenance contract costs

4. TECHNOLOGY REFRESH:
   - Refresh cycles (hardware: 3-5 years, software: annual)
   - Migration/upgrade labor requirements
   - Data migration workload

5. END-OF-LIFE DISPOSAL:
   - Decommissioning procedures
   - Hazardous waste disposal (e-waste, chemicals)
   - Data sanitization requirements (NIST 800-88)

Quantify all maintenance frequencies, labor hours, and material consumption.

This data drives sustainment labor costs, spares inventory budgets, and disposal expenses in out-year pricing.

Example: "Identify ALL lifecycle and sustainment workload for Appendix K IT Infrastructure services."
```

**Expected Output**:

- PM schedule (frequency, labor hours, parts cost)
- Corrective maintenance forecast (MTBF, repair times, spares)
- Warranty coverage analysis (what's covered, what contractor maintains)
- Technology refresh calendar (Year 1, 3, 5 replacement cycles)
- Disposal workload (procedures, labor, hazmat costs)
- Out-year cost projection (Years 1-5 sustainment budget)

---

### Query 5.2: Warranty vs Contractor Maintenance Split

**Use Case**: Optimize warranty coverage vs self-perform maintenance

```
Analyze warranty coverage and contractor maintenance responsibilities for [APPENDIX/SECTION NAME] services.

Extract:
1. WARRANTY COVERAGE:
   - Items under manufacturer warranty (duration, coverage)
   - Extended warranty options (cost, coverage extension)
   - Warranty exclusions (wear items, abuse, modifications)

2. CONTRACTOR MAINTENANCE:
   - Items requiring contractor PM/corrective maintenance
   - Maintenance labor hours (per month, per year)
   - Parts costs (consumables, wear items, spares)

3. DECISION ANALYSIS:
   - Extended warranty cost vs contractor self-perform cost
   - Response time comparison (warranty vs contractor)
   - Risk transfer (warranty covers failures)

4. HYBRID STRATEGY:
   - Critical systems (warranty for risk transfer)
   - Routine systems (contractor for cost savings)
   - High-usage items (wear-and-tear, contractor maintains)

Organize in decision matrix:
| Equipment | Warranty Option | Warranty Cost | Contractor Cost | Recommendation | Rationale |

This analysis optimizes maintenance cost and risk allocation.

Example: "Analyze warranty vs contractor maintenance for Appendix G Equipment Maintenance (HVAC, generators, vehicles)."
```

**Expected Output**:

- Warranty coverage inventory (what's covered, duration)
- Contractor maintenance workload (what's excluded from warranty)
- Cost comparison (extended warranty vs self-perform)
- Risk assessment (warranty risk transfer vs contractor risk)
- Hybrid strategy recommendation (which items warrant warranty)

---

## Category 6: Complete BOE Workload Package

### Query 6.1: Comprehensive BOE Workload Package

**Use Case**: Generate complete cost proposal inputs for all BOE categories

```
Provide a COMPLETE Basis of Estimate (BOE) workload package for [APPENDIX/SECTION NAME] services, covering ALL cost categories.

LABOR WORKLOAD:
- Service frequencies, coverage hours, staffing levels
- Skill mix (technical, admin, supervisory ratios)
- Shift coverage (8x5, 24/7, on-call)
- Training requirements (initial, recurring)

MATERIALS & EQUIPMENT:
- Consumable supplies (quantities, frequencies)
- Capital equipment (quantities, specifications)
- Spare parts inventory (safety stock levels)
- GFE vs contractor-furnished breakdown

OTHER DIRECT COSTS (ODCs):
- Travel (frequencies, destinations, personnel count)
- Facilities (warehouse, office space requirements)
- Subcontractor services (specialized tasks)
- Licenses/subscriptions (software, certifications)

QUALITY & COMPLIANCE:
- Inspection frequencies (100%, sampling)
- Certifications required (material certs, testing)
- Regulatory compliance (Berry, ITAR, OSHA)

LOGISTICS:
- Delivery frequencies, distribution sites
- Transportation requirements (vehicles, mileage)
- Storage requirements (climate-controlled, secure)

LIFECYCLE:
- Preventive maintenance schedules
- Warranty periods, service agreements
- Technology refresh cycles

Organization:
- Start with executive summary (total FTE estimate, major cost drivers)
- Group by PWS subsection in logical order
- Provide detailed breakdown for each category
- Highlight cost drivers (top 5 items by $ impact)
- Flag risks (underestimated workload, ambiguous requirements)

Focus on COMPLETENESS - this package will be used to build the full cost proposal.

Example: "Provide a COMPLETE BOE workload package for Appendix F Food Services."
```

**Expected Output**:

- **Executive Summary**:

  - Scope overview (what services, where, how many people served)
  - Total FTE estimate (breakdown by labor category)
  - Major cost drivers (top 5 by $ impact)
  - Total budget estimate (rough order of magnitude)

- **Labor Breakdown**:

  - Service frequencies quantified
  - Shift coverage requirements (24/7, 8x5)
  - Staffing levels by location/service area
  - Skill mix table (labor categories, quantities, rates)

- **Materials/Equipment**:

  - Consumables inventory (annual quantities, costs)
  - Capital equipment list (specs, quantities, costs)
  - GFE vs contractor-furnished (cost savings identified)

- **ODCs**:

  - Travel budget (trips, destinations, costs)
  - Facilities costs (warehouse lease, office space)
  - Subcontractor budget (specialized services)
  - Licenses/subscriptions (software, tools)

- **Quality/Compliance**:

  - Inspection workload (labor, third-party costs)
  - Certification costs (ISO, industry-specific)
  - Regulatory compliance (Berry, ITAR, OSHA)

- **Logistics**:

  - Transportation budget (vehicles, mileage, fuel)
  - Warehousing costs (lease, utilities, staff)
  - Distribution workload (frequencies, locations)

- **Lifecycle**:

  - PM/corrective maintenance (labor, parts)
  - Warranty coverage (what's covered, costs)
  - Technology refresh (Year 1, 3, 5 replacements)

- **Risk Assessment**:
  - Underestimated workload areas
  - Ambiguous requirements needing clarification
  - Competitive risks (incumbent advantage, pricing pressure)

---

## Category 7: GFE/Facilities Analysis

### Query 7.1: Complete GFE/GFF Inventory

_(See Query 4.2 above - duplicated here for quick reference)_

---

### Query 7.2: Facility Requirements Analysis

**Use Case**: Calculate facility lease costs and space requirements

```
Analyze facility requirements for [APPENDIX/SECTION NAME] services.

Extract:
1. OFFICE SPACE:
   - Square footage required (staff count × 150-200 sq ft per person)
   - Configuration (open office, cubicles, private offices)
   - Utilities (HVAC, IT infrastructure, security)

2. WAREHOUSE/STORAGE:
   - Square footage (inventory volume × turnover rate)
   - Climate control requirements (ambient, refrigerated, freezer)
   - Security (fencing, alarms, access control)

3. SPECIALIZED FACILITIES:
   - Maintenance bays (equipment repair, vehicle service)
   - Training facilities (classrooms, labs, simulators)
   - Secure areas (SCIF, classified storage)

4. GOVERNMENT-PROVIDED FACILITIES:
   - What's provided by government (reduces contractor costs)
   - What contractor must lease/build
   - Renovation requirements (as-is vs move-in ready)

5. FACILITY COSTS:
   - Lease rates ($/sq ft/month by location)
   - Utilities (electric, water, gas, internet)
   - Maintenance (HVAC, janitorial, landscaping)

Organize in facility matrix:
| Facility Type | Sq Ft | Configuration | Climate Control | Security | Lease Rate | Annual Cost |

This data drives facility lease budgets in Other Direct Costs (ODC).

Example: "Analyze facility requirements for Appendix I Warehouse Operations (storage, office, maintenance bays)."
```

**Expected Output**:

- Facility requirements table (type, sq ft, configuration)
- Government-provided vs contractor-leased breakdown
- Climate control requirements (ambient, refrigerated)
- Security requirements (fencing, alarms, access control)
- Lease rate analysis (market rates by location)
- Total facility costs (lease + utilities + maintenance)

---

## Category 8: Evaluation Factor Strategy

### Query 8.1: Evaluation Factor Breakdown

**Use Case**: Understand scoring criteria and allocate proposal page budget

```
What are the evaluation factors for this RFP, including weights, importance hierarchy, and proposal page limits?

Provide:
1. FACTOR HIERARCHY:
   - Factor names (e.g., "Technical Approach", "Past Performance")
   - Numerical weights (percentages or points)
   - Relative importance ("Most Important", "Significantly More Important", "More Important", "Least Important")
   - Subfactors (if hierarchical evaluation structure)

2. PAGE LIMITS:
   - Page allocation per factor (from Section L)
   - Format requirements (font, margins, spacing)
   - Cross-reference rules (can Technical Volume reference Past Performance?)

3. EVALUATION CRITERIA:
   - What aspects are evaluated in each factor
   - Adjectival rating scale (Exceptional, Good, Acceptable, Marginal, Unacceptable)
   - Pass/fail requirements (minimum ratings, mandatory requirements)

4. CORRELATION ANALYSIS:
   - Which factors map to which proposal volumes
   - Section L (instructions) ↔ Section M (evaluation factors) alignment
   - Hidden factors (mentioned in SOW but not explicitly evaluated)

Organization:
- Table format with factors ordered by weight/importance
- Page budget allocation (factor weight × total pages)
- Evaluation criteria summary (what's scored, how it's scored)

This drives proposal resource allocation and content strategy.

Example: "What are the evaluation factors for this RFP, including weights and page limits?"
```

**Expected Output**:

- Factor table (name, weight, importance, page limit)
- Subfactor breakdown (if hierarchical)
- Evaluation criteria (what's evaluated, rating scale)
- Page budget recommendation (allocate pages by weight)
- Section L ↔ M alignment verification

---

### Query 8.2: Factor-to-Requirement Mapping

**Use Case**: Build compliance matrix showing which requirements tie to which evaluation factors

```
Map all MANDATORY and IMPORTANT requirements to their corresponding evaluation factors.

Provide:
1. REQUIREMENT INVENTORY:
   - Requirement ID/description
   - Criticality (MANDATORY, IMPORTANT, OPTIONAL)
   - Source section (Section C, Attachment J, etc.)

2. FACTOR MAPPING:
   - Which evaluation factor(s) this requirement supports
   - Scoring impact (does non-compliance = "Unacceptable"?)
   - Proposal section to address (where in proposal)

3. GAPS & RISKS:
   - Requirements with no clear evaluation factor (may not be scored)
   - Evaluation factors with no requirements (may be subjective scoring)
   - Compliance risks (can we meet all MANDATORY requirements?)

Organization:
- Compliance matrix (Requirement ID | Description | Criticality | Evaluation Factor | Proposal Section)
- Gap analysis (requirements not mapped to factors)
- Risk assessment (high-risk requirements flagged)

This drives proposal compliance and identifies scoring opportunities.

Example: "Map all MANDATORY and IMPORTANT requirements to their evaluation factors."
```

**Expected Output**:

- Compliance matrix table
- Requirements-to-factors mapping
- Gap analysis (unmapped requirements, unmapped factors)
- Risk assessment (MANDATORY requirements we can't meet)
- Proposal outline (which section addresses which requirement)

---

### Query 8.3: Win Theme Identification

**Use Case**: Develop discriminators and competitive advantages

```
Based on MANDATORY requirements, high-weight evaluation factors, and customer pain points, identify potential win themes for this proposal.

Analyze:
1. CUSTOMER PAIN POINTS:
   - Problems stated in SOW (Section C)
   - Incumbent performance issues (if mentioned)
   - Operational challenges (downtime, quality, cost)

2. HIGH-IMPACT REQUIREMENTS:
   - MANDATORY requirements (must-haves)
   - High-weight factors (40%+)
   - Unique/difficult requirements (competitors may struggle)

3. OUR COMPETITIVE ADVANTAGES:
   - Past performance on similar contracts
   - Unique capabilities (patented tech, exclusive partnerships)
   - Local presence (if proximity matters)
   - Incumbent knowledge (if we're the incumbent)

4. DISCRIMINATOR OPPORTUNITIES:
   - Innovation beyond requirements (add value)
   - Cost savings strategies (without cutting corners)
   - Risk mitigation (proactive problem-solving)

Organization:
- Win theme statement (1-2 sentences)
- Supporting requirement IDs
- Evaluation factor alignment
- Competitive differentiation (why us vs competitors)

Example: "Based on requirements and pain points, identify potential win themes for this RFP."
```

**Expected Output**:

- 3-5 win theme statements (action-oriented, customer-benefit focused)
- Requirements supporting each theme
- Evaluation factor alignment (which factors score this theme)
- Competitive analysis (how this differentiates from competitors)
- Proposal strategy (where to emphasize themes)

---

## Category 9: Compliance & Risk Analysis

### Query 9.1: Mandatory Requirement Compliance Check

**Use Case**: Identify compliance gaps before proposal submission

```
List all MANDATORY requirements and assess our compliance posture. Flag any gaps or risks.

Provide:
1. COMPLIANT REQUIREMENTS:
   - Requirement ID/description
   - Evidence of compliance (certification, past performance, existing capability)
   - Proposal demonstration (where/how we'll prove compliance)

2. GAP ANALYSIS:
   - Requirements we cannot currently meet
   - Time to achieve compliance (can we get there by contract start?)
   - Cost to achieve compliance (certification, equipment, hiring)

3. RISK ASSESSMENT:
   - High risk (MANDATORY requirement, no compliance plan)
   - Medium risk (IMPORTANT requirement, delayed compliance)
   - Low risk (OPTIONAL requirement, nice-to-have)

4. MITIGATION STRATEGIES:
   - Subcontracting (partner with compliant firm)
   - Certification roadmap (commit to achieving by contract start)
   - Waiver request (ask government for exception, if allowed)

Organization:
- Compliance table (Requirement | Status | Evidence | Mitigation)
- Gap summary (how many gaps, severity)
- Mitigation plan (for each gap)

This assessment drives teaming strategy and compliance risk management.

Example: "List all MANDATORY requirements and assess our compliance posture. Flag gaps."
```

**Expected Output**:

- Compliance status table (compliant, partial, non-compliant)
- Gap analysis (requirements we can't meet)
- Risk assessment (severity of each gap)
- Mitigation strategies (subcontracting, certification, waiver)
- Go/no-go recommendation (should we bid?)

---

### Query 9.2: Section L vs Section M Cross-Check

**Use Case**: Identify orphaned instructions or unmapped evaluation criteria

```
Cross-check Section L (proposal instructions) against Section M (evaluation factors). Flag any misalignments.

Analyze:
1. PROPERLY MAPPED:
   - Instructions that clearly map to evaluation factors
   - Example: "10-page Technical Volume" → "Factor 1: Technical Approach"

2. ORPHANED INSTRUCTIONS:
   - Instructions with no corresponding evaluation factor
   - May be administrative (not scored) or error in RFP

3. UNMAPPED EVALUATION CRITERIA:
   - Evaluation factors with no submission instruction
   - Unclear where in proposal to address

4. CONFLICTS:
   - Page limit too small for evaluation depth
   - Format restrictions conflicting with content needs
   - Cross-reference prohibitions creating gaps

Organization:
- Alignment matrix (Instruction | Factor | Status)
- Orphaned items (instructions or factors with no match)
- Conflicts (page limits, format restrictions)
- Questions for government (clarify ambiguities in Q&A)

This identifies proposal structure risks and Q&A opportunities.

Example: "Cross-check Section L instructions against Section M evaluation factors. Flag misalignments."
```

**Expected Output**:

- Alignment matrix (instruction ↔ factor mapping)
- Orphaned instructions (submit but not scored?)
- Unmapped factors (evaluated but no instruction on how to address?)
- Conflicts (page limits insufficient for evaluation depth)
- Q&A questions (clarify ambiguities with government)

---

## Category 10: Amendment Analysis

### Query 10.1: Amendment Impact Summary

**Use Case**: Quickly assess changes from RFP amendment

```
What changed in Amendment [NUMBER]? Provide a summary of additions, modifications, and removals.

Analyze:
1. CRITICAL CHANGES:
   - New requirements added (MANDATORY, IMPORTANT)
   - Modified requirements (scope, deadline, acceptance criteria)
   - Removed requirements (no longer applicable)

2. EVALUATION FACTOR CHANGES:
   - Weight changes (factor importance shifted)
   - New subfactors added
   - Evaluation criteria modified

3. SUBMISSION INSTRUCTION CHANGES:
   - Page limit changes (more or less space)
   - Format requirement changes (font, margins)
   - Deadline extensions or reductions

4. SCOPE CHANGES:
   - Performance period modifications (years, options)
   - Geographic changes (locations added/removed)
   - Deliverable changes (new CDRLs, modified schedules)

5. IMPACT ASSESSMENT:
   - Does this improve or hurt our competitive position?
   - Do we need to revise our proposal strategy?
   - Are there new compliance gaps?

Organization:
- Change summary (ADDED, MODIFIED, REMOVED)
- Impact rating (CRITICAL, HIGH, MEDIUM, LOW)
- Action required (revise proposal, ask Q&A, no action)

Example: "What changed in Amendment 0001? Provide impact summary."
```

**Expected Output**:

- Change log (what changed, impact rating)
- Requirements delta (new, modified, removed)
- Evaluation factor changes (weights, criteria)
- Submission instruction changes (pages, format, deadlines)
- Impact assessment (competitive position, proposal strategy)
- Action plan (what to revise, questions to ask)

---

### Query 10.2: Amendment-Triggered Questions

**Use Case**: Generate Q&A questions based on amendment ambiguities

```
What questions should we ask the government based on Amendment [NUMBER]?

Generate questions for:
1. AMBIGUITIES:
   - Conflicting requirements (old vs amended language)
   - Unclear scope changes (what exactly changed?)
   - Missing details (amendment mentions something new but doesn't define it)

2. COMPLIANCE CLARIFICATIONS:
   - New requirements with unclear acceptance criteria
   - Modified deadlines without rationale
   - Removed requirements (can we still propose that capability?)

3. COST IMPACTS:
   - Scope additions (does this increase ceiling price?)
   - Performance period changes (affects out-year costs)
   - New deliverables (additional labor/materials required)

4. COMPETITIVE INTELLIGENCE:
   - Why was this amended? (customer feedback, incumbent issue?)
   - Is this a material change? (requires proposal revision)
   - Does this favor a particular offeror? (protest grounds?)

Organization:
- Question priority (CRITICAL, HIGH, MEDIUM, LOW)
- Question type (clarification, compliance, cost, competitive)
- Proposed wording (ready to submit in Q&A)

Example: "What questions should we ask based on Amendment 0002?"
```

**Expected Output**:

- Prioritized question list (CRITICAL first)
- Question categories (clarification, compliance, cost)
- Proposed Q&A wording (ready to submit)
- Rationale (why asking, what we need to know)
- Deadline tracking (when Q&A period closes)

---

## Usage Best Practices

### 1. Query Customization

- **Replace placeholders**: `[APPENDIX/SECTION NAME]` → `"Appendix F Food Services"`
- **Be specific**: "Appendix F" not just "food services"
- **Use exact names**: Copy section names from PWS verbatim

### 2. Iterative Refinement

- **Start broad**: Use comprehensive queries (Q1.1, Q2.1, Q6.1)
- **Drill down**: If response misses details, re-run with specific focus
- **Combine queries**: Run Q1.1 (labor) + Q2.1 (materials) for full picture

### 3. Output Validation

- **Cross-check totals**: Does FTE count match service frequencies?
- **Verify quantities**: Do consumables align with annual workload?
- **Flag gaps**: Missing data? Re-query or mark as "TBD - clarify with government"

### 4. Integration with Proposal Process

- **Capture phase**: Use Q8.1-Q8.3 (evaluation strategy) early
- **BOE development**: Use Category 1-6 (labor, materials, ODCs)
- **Compliance review**: Use Q9.1-Q9.2 (gaps, L-M alignment)
- **Amendment tracking**: Use Q10.1-Q10.2 (changes, questions)

---

## Query Combinations for Common Workflows

### **Workflow 1: Initial Capture Analysis**

1. Q8.1 - Evaluation factors (understand scoring)
2. Q9.1 - Mandatory requirements (compliance check)
3. Q8.3 - Win themes (competitive strategy)
4. Q9.2 - Section L-M alignment (proposal structure)

### **Workflow 2: Labor BOE Development**

1. Q1.1 - Labor workload breakdown (FTE calculation)
2. Q1.2 - Skill mix analysis (labor categories)
3. Q5.1 - Lifecycle workload (sustainment labor)
4. Q3.1 - QA workload (inspection labor)

### **Workflow 3: Material/BOM Planning**

1. Q2.1 - Material inventory (complete BOM)
2. Q7.1 - GFE/GFF (reduce contractor costs)
3. Q2.2 - Equipment lifecycle (replacement cycles)
4. Q2.3 - Supply chain analysis (vendor constraints)

### **Workflow 4: Complete Cost Proposal**

1. Q6.1 - Comprehensive BOE package (all categories)
2. Q4.1 - Logistics workload (transport, warehouse)
3. Q3.2 - Compliance risk (regulatory costs)
4. Q5.2 - Warranty analysis (optimize maintenance)

### **Workflow 5: Amendment Response**

1. Q10.1 - Amendment impact (what changed)
2. Q10.2 - Amendment questions (Q&A preparation)
3. Q9.1 - Updated compliance check (new gaps?)
4. Q8.1 - Updated factor weights (strategy shift?)

---

**Version**: 1.0 (November 2025)  
**Next Update**: Add industry-specific query variations (IT services, construction, professional services)  
**Feedback**: Submit query improvement suggestions to capture team lead
