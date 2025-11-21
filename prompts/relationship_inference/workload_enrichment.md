WORKLOAD ENRICHMENT ANALYSIS (GOVERNMENT CONTRACTING REQUIREMENTS)

OBJECTIVE
Enrich each REQUIREMENT entity with workload metadata needed for:
- Labor staffing planning (FTEs, shifts, coverage)
- Bill of Materials (equipment, consumables, infrastructure)
- Complexity and confidence signals for pricing and BOE

You are NOT inventing costs or FTEs. You are only:
- Extracting explicit workload signals from text
- Making bounded, explainable inferences when text strongly implies workload

OUTPUT FIELDS (PER REQUIREMENT)
For each requirement with any workload implication, output an enrichment object:

{
   "entity_id": "<requirement_entity_id>",
   "has_workload_metric": true/false,
   "workload_categories": [
      "Labor" | "Materials" | "ODCs" | "QA" | "Logistics" | "Lifecycle" | "Compliance"
   ],
   "boe_relevance": {
      "Labor": 0.0-1.0,
      "Materials": 0.0-1.0,
      "ODCs": 0.0-1.0,
      "QA": 0.0-1.0,
      "Logistics": 0.0-1.0,
      "Lifecycle": 0.0-1.0,
      "Compliance": 0.0-1.0
   },
   "labor_drivers": [
      "<short phrase capturing concrete labor driver>",
      "..."
   ],
   "material_needs": [
      "<short phrase capturing concrete material/equipment need>",
      "..."
   ],
   "complexity_score": 1-10,
   "complexity_rationale": "<1-3 sentence explanation>",
   "effort_estimate": "<echo back ONLY explicit quantities or clearly bounded ranges from text>",
   "enriched_by": "workload_enrichment_v1"
}

If a requirement truly has no workload implication, set:
- "has_workload_metric": false
- All other workload fields may be omitted or empty

7 BOE WORKLOAD CATEGORIES
Classify workload into these standard categories (multiple allowed):

1) LABOR (PEOPLE WORK)
    FTEs, positions, roles, shifts, coverage, man-hours.
    Keywords/Signals: staff, personnel, FTE, contractor, workforce, team, operator, technician, engineer, analyst, manager, help desk, 24/7, 8-hour shift, coverage, duty, watch, manned, staffed.

2) MATERIALS (PHYSICAL THINGS)
    Equipment, hardware, consumables, facilities, tools, infrastructure.
    Keywords/Signals: equipment, supplies, materials, parts, tools, consumables, inventory, hardware, servers, vehicles, office space, square feet.

3) ODCs (OTHER DIRECT COSTS)
    Travel, subcontractors, licenses, training seats, external services.
    Keywords/Signals: travel, TDY, per diem, airfare, hotel, subcontractor, vendor, license, permit, certification, tuition, training course, conference.

4) QA (QUALITY/INSPECTION WORK)
    Inspection, monitoring, audits, testing, validation.
    Keywords/Signals: inspection, QC, QA, surveillance, audit, verification, validation, test, sample, review, acceptance.

5) LOGISTICS (MOVEMENT & STORAGE)
    Transportation, shipping, warehousing, distribution, supply chain.
    Keywords/Signals: transportation, shipping, delivery, distribution, warehousing, storage, supply chain, staging, kitting.

6) LIFECYCLE (SUSTAINMENT & MAINTENANCE)
    O&M, upgrades, repairs, refresh, replacement, disposal.
    Keywords/Signals: maintenance, sustainment, O&M, repair, replace, upgrade, overhaul, lifecycle, disposal, decommission.

7) COMPLIANCE (REGULATORY/REPORTING WORKLOAD)
    Documentation, reporting, audits, regulatory responses.
    Keywords/Signals: compliance, regulation, policy, documentation, reporting, legal, FAR, DFARS, recordkeeping.

LABOR DRIVER ANALYSIS (WHEN "Labor" IS SELECTED)
GOAL: Capture what drives labor demand (coverage, roles, volume, frequency), not performance targets.

Common labor role groupings:
- Management: Program Manager, Task Lead, Site Lead, Supervisor.
- Technical: Engineers, Analysts, Architects, Developers, Specialists.
- Operations: Technicians, Operators, Maintenance Staff, Help Desk, On-site Support.
- Administrative: Clerks, Coordinators, Schedulers, Admin Support.
- Specialized: Security Guards, Medical Personnel, QA Inspectors, Trainers.

EXTRACT EXACT EFFORT INDICATORS WHEN PRESENT:
- Counts: "3 FTE", "two additional analysts", "one PM", "3 janitors".
- Coverage: "24/7", "16x5", "8-hour shifts", "three shifts per day".
- Volume drivers: "5000 personnel", "500 meals per day", "200 tickets/month".
- Frequency: "daily", "weekly", "monthly", "quarterly", "4x per day".
- Hours: "0800-1700", "40 hours per week", "2,000 annual hours".

EXCLUSION RULE (CRITICAL):
Do NOT put performance targets in labor_drivers.
- Examples of EXCLUDED items: "95% uptime", "99.9% availability", "100% compliance", "respond within 4 hours".
- Those belong in PERFORMANCE_METRIC entities, not workload enrichment.

MATERIAL NEEDS ANALYSIS (WHEN "Materials" IS SELECTED)
GOAL: Identify concrete physical or technology items that must exist or be provided.

Common material groupings:
- Equipment: servers, laptops, network gear, vehicles, tools, machinery.
- Consumables: paper, toner, cleaning supplies, food, fuel, PPE, spare parts.
- Technology/Software: licenses, subscriptions, specialized software.
- Facilities/Infrastructure: square footage, dedicated spaces, labs, warehouses.

EXTRACT EXACT QUANTITY/SCALING INDICATORS WHEN PRESENT:
- "50 laptops", "3 vehicles", "500 meals per day", "10,000 sq ft", "two secure racks".

COMPLEXITY SCORE (1-10)
Provide a single integer 1-10 per requirement:
- 1-3 (Simple): Basic tasks, standard procedures, minimal coordination, low volume.
- 4-6 (Moderate): Multiple steps, some coordination, specialized skills OR moderate volume.
- 7-10 (Complex): High coordination, multiple roles/sites, mission-critical, high volume, or tight timelines.

Consider:
- Coordination: How many roles, teams, or locations are involved?
- Expertise: Are certifications, clearances, or advanced skills required?
- Criticality: Is this mission-critical or safety-critical?
- Volume/Frequency: How often and how many (e.g., thousands of users, daily surges)?

CONFIDENCE (IMPLICIT IN boe_relevance)
Use 0.0-1.0 scores to reflect evidence strength per category:
- 0.9-1.0: Explicit workload language in text.
- 0.7-0.9: Strong inference with multiple supporting phrases.
- 0.5-0.7: Moderate inference, some ambiguity.
- 0.3-0.5: Weak inference.
- 0.0-0.3: Speculative; generally avoid selecting the category.

ANALYSIS RULES
1) Most real requirements map to 2-4 workload categories (e.g., Labor + Materials + QA).
2) Always prefer explicit text over inference. Do NOT fabricate staff counts or equipment if not implied.
3) Labor = people work, Materials = physical/technology items, ODCs = external non-labor costs.
4) Empty arrays are allowed. If no labor driver is stated, leave labor_drivers empty.
5) Higher diversity of categories and stronger signals generally lead to higher complexity_score.

BASELINE EXAMPLE 1 – JANITORIAL SERVICES
Requirement:
"The Contractor shall provide 24/7 janitorial services for all occupied spaces supporting 5,000 personnel. A minimum of three (3) janitorial staff shall be on duty at any time. Restrooms shall be cleaned a minimum of four (4) times per day. The Contractor shall provide all cleaning equipment, supplies, and associated materials."

Expected enrichment:
{
   "entity_id": "entity_janitorial",
   "has_workload_metric": true,
   "workload_categories": ["Labor", "Materials", "QA"],
   "boe_relevance": {
      "Labor": 0.98,
      "Materials": 0.9,
      "QA": 0.7
   },
   "labor_drivers": [
      "Janitorial Staff (min 3 on duty at all times)",
      "24/7 coverage across occupied spaces",
      "Cleaning operations for 5,000 personnel",
      "Restroom cleaning 4x per day"
   ],
   "material_needs": [
      "Cleaning equipment (mops, buffers, vacuums)",
      "Cleaning supplies and chemicals",
      "Personnel protective equipment (PPE)"
   ],
   "complexity_score": 7,
   "complexity_rationale": "24/7 multi-shift staffing, large population (5,000), recurring daily cleanings, Contractor-furnished equipment and supplies.",
   "effort_estimate": "Explicit: minimum 3 janitorial staff on duty at all times, 24/7 coverage, restrooms cleaned 4x per day.",
   "enriched_by": "workload_enrichment_v1"
}

BASELINE EXAMPLE 2 – DINING FACILITY
Requirement:
"The Contractor shall operate the Installation Dining Facility (DFAC) to serve an average of five hundred (500) meals per day, seven (7) days per week, in a Government-furnished 10,000 square foot facility. The Contractor shall provide all food service personnel necessary to support breakfast, lunch, and dinner meal periods. The Government will furnish major kitchen equipment; the Contractor shall provide small wares, consumables, and cleaning supplies."

Expected enrichment:
{
   "entity_id": "entity_dfac",
   "has_workload_metric": true,
   "workload_categories": ["Labor", "Materials", "Logistics", "QA"],
   "boe_relevance": {
      "Labor": 0.97,
      "Materials": 0.9,
      "Logistics": 0.7,
      "QA": 0.6
   },
   "labor_drivers": [
      "Food service staff for breakfast, lunch, and dinner, 7 days/week",
      "Meal preparation and serving for ~500 meals per day",
      "Dishwashing and cleaning coverage for entire DFAC"
   ],
   "material_needs": [
      "Food ingredients and consumables",
      "Small wares (utensils, trays, serving implements)",
      "Cleaning supplies and chemicals"
   ],
   "complexity_score": 8,
   "complexity_rationale": "Continuous 7-day operations, three meals per day, 500 meals/day throughput, mixed Government- and Contractor-furnished equipment, logistics of food and consumables.",
   "effort_estimate": "Explicit: ~500 meals per day, 7 days per week, 10,000 sq ft facility.",
   "enriched_by": "workload_enrichment_v1"
}

CAC BAR EXAMPLE – HIGH-THROUGHPUT RETAIL / MORALE SUPPORT WORKLOAD
Requirement (simplified from CAC workload paragraph):
"The Contractor shall staff and operate a Consolidated Exchange complex that includes: (1) a full-service BX with 12 checkout lanes, (2) a 3,000 sq ft food court with four branded quick-service restaurants, and (3) a convenience store operating 24/7. The Contractor shall ensure sufficient staffing to support peak weekend and payday traffic, with at least two (2) supervisors on duty during peak hours. The complex serves an installation population of approximately 20,000 personnel and must support extended evening hours until 2200 on weekdays. The Contractor shall provide all consumables, retail supplies, and point-of-sale systems necessary to sustain operations."

Expected enrichment:
{
   "entity_id": "entity_cac_bar",
   "has_workload_metric": true,
   "workload_categories": ["Labor", "Materials", "Logistics", "QA"],
   "boe_relevance": {
      "Labor": 0.98,
      "Materials": 0.9,
      "Logistics": 0.8,
      "QA": 0.6
   },
   "labor_drivers": [
      "Retail and food service staff across BX, food court, and convenience store",
      "12 checkout lanes requiring cashiers during operating hours",
      "24/7 coverage for convenience store",
      "Peak weekend/payday surge staffing for ~20,000 personnel",
      "At least 2 supervisors on duty during peak hours",
      "Extended evening operations until 2200 on weekdays"
   ],
   "material_needs": [
      "Point-of-sale systems for 12 checkout lanes and food court",
      "Food and retail consumables inventory",
      "Cleaning and janitorial supplies for 3,000 sq ft food court and retail spaces"
   ],
   "complexity_score": 9,
   "complexity_rationale": "Multi-venue retail and food operations, 24/7 component, high population (20,000 personnel) with surge periods, extended hours, and supervisory coverage requirements.",
   "effort_estimate": "Explicit: 12 checkout lanes, 3,000 sq ft food court, 24/7 convenience store, extended hours until 2200 weekdays, at least 2 supervisors during peak hours, population ~20,000.",
   "enriched_by": "workload_enrichment_v1"
}

QUALITY CHECK FOR EACH REQUIREMENT
- If you select "Labor", labor_drivers should reference specific roles, coverage, volume, or frequency.
- If you select "Materials", material_needs should mention concrete physical or technology items.
- Do not invent numbers. Echo only explicit or clearly bounded quantities in effort_estimate.
- If the text is silent on workload, set has_workload_metric = false and leave workload fields empty.

COMMON ERRORS TO AVOID (CRITICAL)
- Do NOT restate performance thresholds ("95% uptime") as labor_drivers or material_needs; those belong to PERFORMANCE_METRIC entities.
- Do NOT infer specific FTE counts from vague phrases like "adequate staffing"; only echo counts when numerically or structurally stated (e.g., shifts, 24/7, population).
- Do NOT assign Materials when the requirement only describes outcomes ("ensure clean facilities") and never mentions tools/equipment/supplies.
- Do NOT force workload for purely administrative or informational requirements (e.g., contract term, option years, clause boilerplate) – those may legitimately have has_workload_metric = false.