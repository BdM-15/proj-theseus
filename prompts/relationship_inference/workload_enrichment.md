# Workload Enrichment Analysis for Government Contracting Requirements

## Objective

Analyze RFP requirements to extract workload metadata for labor staffing planning and Bill of Materials (BOM) development. This enables capture managers to:

- **Staff proposals** with accurate labor categories and effort estimates
- **Build BOMs** with required materials, equipment, and ODCs
- **Assess risk** based on requirement complexity and dependencies
- **Estimate costs** aligned with Basis of Estimate (BOE) categories

---

## Analysis Framework

For each requirement, identify:

1. **BOE Categories** - Which cost categories apply to this requirement?
2. **Labor Drivers** - What labor skills, roles, or FTEs are needed?
3. **Material Needs** - What equipment, supplies, or physical assets are required?
4. **Complexity Assessment** - How difficult is this requirement to fulfill?
5. **Confidence Level** - How certain are you about this analysis?

---

## BOE Categories (7 Standard Categories)

Classify each requirement into one or more of these categories:

### 1. **Labor**

- Direct labor (FTEs, contractors, technicians)
- Skill requirements (engineers, analysts, managers)
- Effort indicators (hours/week, shift coverage, 24/7 operations)
- **Keywords**: staff, personnel, FTE, contractor, labor, workforce, team, operator, technician, engineer, analyst, manager

### 2. **Materials**

- Physical goods (supplies, equipment, parts)
- Consumables (cleaning supplies, uniforms, food)
- Infrastructure (facilities, buildings, office space)
- **Keywords**: equipment, supplies, materials, parts, tools, consumables, goods, inventory, stock

### 3. **ODCs (Other Direct Costs)**

- Travel (TDY, site visits, conferences)
- Subcontractors/vendors
- Licenses, permits, certifications
- Training costs
- **Keywords**: travel, subcontractor, vendor, training, license, permit, certification, TDY, conference

### 4. **QA (Quality Assurance)**

- Inspection requirements
- Quality control procedures
- Compliance verification
- Testing and validation
- **Keywords**: inspection, quality control, QC, QA, compliance, testing, validation, verification, audit, review

### 5. **Logistics**

- Transportation and delivery
- Storage and warehousing
- Supply chain management
- Distribution requirements
- **Keywords**: transportation, delivery, shipping, warehousing, storage, distribution, supply chain, logistics

### 6. **Lifecycle**

- Maintenance and sustainment
- Long-term operations
- Replacement cycles
- End-of-life disposal
- **Keywords**: maintenance, sustainment, operations, O&M, lifecycle, replacement, disposal, preventive maintenance

### 7. **Compliance**

- Regulatory requirements
- Policy adherence
- Documentation and reporting
- Legal obligations
- **Keywords**: compliance, regulation, policy, documentation, reporting, legal, FAR, DFARS, certification

---

## Labor Driver Analysis

Extract specific labor details when BOE category includes "Labor":

### Labor Categories to Identify:

- **Management**: Program Manager, Task Lead, Supervisor
- **Technical**: Engineers, Analysts, Specialists
- **Operations**: Technicians, Operators, Maintenance Staff
- **Administrative**: Clerks, Coordinators, Support Staff
- **Specialized**: Security Personnel, Medical Staff, QA Inspectors

### ❌ EXCLUSION RULE:

- Do NOT include Performance Metrics (e.g., "95% uptime", "100% compliance") in Labor Drivers.
- These belong in the Performance Requirements section, not Workload.

### Effort Indicators (CRITICAL: EXTRACT EXACT NUMBERS, FREQUENCIES, HOURS):

- **Explicit**: "3 FTE", "24/7 coverage", "8-hour shifts", "40 hours/week", "5000 personnel"
- **Frequencies**: "Daily", "Weekly", "Monthly", "Quarterly", "Annually", "3x per week"
- **Hours**: "Operating hours 0800-1700", "Response time 2 hours", "2000 annual hours"
- **Implicit**: "continuous operations" → 24/7 staffing, "daily cleaning" → recurring labor
- **Quantitative**: If the text says "5000 personnel" or "Frequency: Daily", you MUST include it in the driver description.

### Example Labor Extraction:

```
Requirement: "Contractor shall provide 24/7 janitorial services with minimum 3 FTE coverage for 5000 personnel. Restrooms cleaned 4x daily."
Labor Drivers: ["Janitorial Staff (3 FTE)", "24/7 Coverage (shift rotation)", "Cleaning Operations for 5000 personnel", "Frequency: 4x Daily Restroom Cleaning"]
Effort Quantifiers: "Explicit: 3 FTE minimum, 24/7 coverage, 4x daily frequency"
```

---

## Material Needs Analysis

Extract specific material details when BOE category includes "Materials":

### Material Categories:

- **Equipment**: Heavy machinery, vehicles, tools, instruments
- **Consumables**: Cleaning supplies, office supplies, food service items
- **Technology**: Computers, software, communications gear
- **Infrastructure**: Facilities, buildings, utilities

### Quantity Indicators (CRITICAL: EXTRACT EXACT NUMBERS):

- **Explicit**: "50 laptops", "3 vehicles", "200 meals/day", "50,000 sq ft"
- **Implicit**: "dining facility for 500" → kitchen equipment, tables, chairs, utensils
- **Quantitative**: If the text says "50,000 sq ft", you MUST include "50,000 sq ft" in the material need.

### Example Material Extraction:

```
Requirement: "Contractor shall operate dining facility serving 500 meals per day in 10,000 sq ft facility"
Material Needs: ["Commercial kitchen equipment", "Dining tables/chairs (100 seats)", "Food service supplies", "Refrigeration units", "Facility maintenance for 10,000 sq ft"]
Quantity Metrics: "Explicit: 500 meals/day, 10,000 sq ft facility"
```

---

## Complexity Assessment

Rate the difficulty of fulfilling this requirement:

- **Simple** (1-3): Basic tasks, standard procedures, minimal coordination

  - Examples: Submit monthly reports, maintain cleanliness, answer phone calls

- **Moderate** (4-6): Multiple steps, some coordination, specialized skills required

  - Examples: Manage 24/7 operations, coordinate deliveries, perform inspections

- **Complex** (7-10): High coordination, specialized expertise, mission-critical impact
  - Examples: Develop QC plan, manage multi-vendor supply chain, 24/7 emergency response

### Complexity Factors:

- **Coordination**: How many entities/teams must work together?
- **Expertise**: Are specialized skills or certifications required?
- **Criticality**: What's the impact if this requirement fails?
- **Frequency**: Is this one-time or recurring with high volume?

---

## Confidence Scoring

Rate your confidence in each BOE category assignment (0.0-1.0):

- **0.9-1.0**: Explicit mention in requirement text

  - Example: "Contractor shall provide 3 FTE janitorial staff" → Labor: 1.0

- **0.7-0.9**: Strong inference from context

  - Example: "24/7 dining facility operations" → Labor: 0.9 (shift staff implied)

- **0.5-0.7**: Moderate inference, some ambiguity

  - Example: "Maintain facility cleanliness" → Labor: 0.6 (could be labor or contracted service)

- **0.3-0.5**: Weak inference, high uncertainty

  - Example: "Ensure quality service" → QA: 0.4 (vague quality reference)

- **0.0-0.3**: Speculative, minimal evidence
  - Use only when BOE category is remotely possible but not clearly indicated

---

## Output Format (JSON)

For each requirement entity, return:

```json
{
  "entity_id": "entity_123",
  "has_workload_metric": true,
  "workload_categories": ["Labor", "Materials", "QA"],
  "boe_relevance": {
    "Labor": 0.95,
    "Materials": 0.8,
    "QA": 0.7
  },
  "labor_drivers": [
    "Janitorial Staff (3 FTE minimum)",
    "24/7 Coverage Requirement",
    "Shift Rotation (3 shifts per day)"
  ],
  "material_needs": [
    "Cleaning equipment and supplies",
    "Protective equipment (PPE)",
    "Floor maintenance machinery"
  ],
  "complexity_score": 6,
  "complexity_rationale": "Requires 24/7 staffing coordination, multiple shift management, and compliance with health/safety standards",
  "effort_estimate": "Moderate - 9-12 FTE total (3 per shift × 3 shifts with overlap)",
  "enriched_by": "workload_analysis_v1"
}
```

### Field Definitions:

- **has_workload_metric**: Boolean - Always `true` after enrichment
- **workload_categories**: Array of BOE category names (max 7, must match standard categories)
- **boe_relevance**: Object with confidence scores (0.0-1.0) for each identified category
- **labor_drivers**: Array of labor-related details (empty if no Labor category)
- **material_needs**: Array of material-related details (empty if no Materials category)
- **complexity_score**: Integer 1-10 (difficulty rating)
- **complexity_rationale**: String explaining complexity assessment
- **effort_estimate**: String with EXPLICIT effort metrics found in text (e.g., "3 FTE", "24/7"). Do NOT estimate/guess FTEs if not stated.
- **enriched_by**: String identifier for enrichment version (use "workload_analysis_v1")

---

## Analysis Rules

### Rule 1: Multiple BOE Categories are Common

Most requirements span multiple categories. Examples:

- "Provide 24/7 janitorial services" → Labor (staff) + Materials (supplies) + Compliance (health standards)
- "Deliver meals to 500 personnel daily" → Labor (cooks) + Materials (food) + Logistics (delivery)

### Rule 2: Prioritize Explicit Evidence

- Direct mentions > Implied needs > Possible inferences
- High confidence (0.9+) only for explicit text
- Lower confidence (0.5-0.7) for logical inferences

### Rule 3: Labor vs Materials vs ODCs

- **Labor**: People doing work (FTEs, contractors, staff)
- **Materials**: Physical things being used/consumed (equipment, supplies)
- **ODCs**: External costs not labor/materials (travel, training, vendors)

### Rule 4: Empty Arrays are OK

- If no labor drivers identified → `"labor_drivers": []`
- If no materials needed → `"material_needs": []`
- Don't fabricate data - only include what's supported by text

### Rule 5: Complexity Correlates with BOE Diversity

- Single BOE category → Often simpler (1-5)
- 2-3 BOE categories → Often moderate (4-7)
- 4+ BOE categories → Often complex (7-10)
- But consider other factors: criticality, coordination, expertise

---

## Example Analysis

### Input Requirements:

```
1. entity_456 | requirement | "ADAB ISS Requirement" | "Contractor shall provide Installation Support Services (ISS) at Al Dhafra Air Base, including 24/7 dining facility operations, janitorial services, and grounds maintenance for 5000+ personnel."

2. entity_789 | requirement | "Monthly Performance Report" | "Contractor shall submit monthly performance reports by the 5th business day of each month, documenting service levels, staffing, and quality metrics."

3. entity_234 | requirement | "Quality Control Plan" | "Contractor shall develop and maintain a comprehensive Quality Control Plan addressing inspection procedures, deficiency correction, and continuous improvement."
```

### Expected Output:

```json
[
  {
    "entity_id": "entity_456",
    "has_workload_metric": true,
    "workload_categories": [
      "Labor",
      "Materials",
      "Logistics",
      "Lifecycle",
      "Compliance"
    ],
    "boe_relevance": {
      "Labor": 0.95,
      "Materials": 0.9,
      "Logistics": 0.75,
      "Lifecycle": 0.7,
      "Compliance": 0.8
    },
    "labor_drivers": [
      "24/7 Dining Facility Staff (cooks, servers, dishwashers)",
      "Janitorial Staff (3-shift coverage)",
      "Grounds Maintenance Crew",
      "Supervisory/Management Staff",
      "Total population supported: 5000+ personnel"
    ],
    "material_needs": [
      "Commercial kitchen equipment (DFAC)",
      "Food service supplies (utensils, plates, etc.)",
      "Cleaning equipment and supplies",
      "Grounds maintenance equipment (mowers, tools)",
      "Facility maintenance materials"
    ],
    "complexity_score": 9,
    "complexity_rationale": "High complexity due to 24/7 operations, large population (5000+), multiple service areas (dining, janitorial, grounds), and critical mission support role requiring continuous staffing and supply chain management",
    "effort_estimate": "Explicit: 24/7 operations, 5000+ personnel, 3 service areas",
    "enriched_by": "workload_analysis_v1"
  },
  {
    "entity_id": "entity_789",
    "has_workload_metric": true,
    "workload_categories": ["Labor", "Compliance"],
    "boe_relevance": {
      "Labor": 0.6,
      "Compliance": 0.9
    },
    "labor_drivers": [
      "Report preparation staff (administrative)",
      "Data collection and analysis (recurring monthly task)"
    ],
    "material_needs": [],
    "complexity_score": 3,
    "complexity_rationale": "Low complexity - standard reporting requirement with defined format and deadline, minimal coordination required",
    "effort_estimate": "Explicit: Monthly frequency (by 5th business day)",
    "enriched_by": "workload_analysis_v1"
  },
  {
    "entity_id": "entity_234",
    "has_workload_metric": true,
    "workload_categories": ["Labor", "QA", "Compliance"],
    "boe_relevance": {
      "Labor": 0.75,
      "QA": 1.0,
      "Compliance": 0.85
    },
    "labor_drivers": [
      "QA/QC Manager (plan development and oversight)",
      "Quality Inspectors (inspection procedures)",
      "Subject Matter Experts (technical review)"
    ],
    "material_needs": [],
    "complexity_score": 7,
    "complexity_rationale": "Moderate-high complexity - requires quality management expertise, documentation development, inspection protocol design, and continuous improvement processes",
    "effort_estimate": "Implicit: Continuous improvement implies ongoing effort",
    "enriched_by": "workload_analysis_v1"
  }
]
```

---

## Processing Instructions

1. **Read all requirement entities** in the batch
2. **Analyze each requirement** independently using the framework above
3. **Identify BOE categories** with confidence scores (must be in standard 7 categories)
4. **Extract labor drivers** if Labor category identified
5. **Extract material needs** if Materials category identified
6. **Assess complexity** (1-10) with rationale
7. **Extract effort metrics** (explicit numbers/frequencies only - NO ESTIMATION)
8. **Output JSON array** with one object per requirement entity

---

## Quality Checklist

Before returning results, verify:

- ✅ All `workload_categories` values match standard 7 BOE categories exactly
- ✅ All `boe_relevance` scores are between 0.0 and 1.0
- ✅ `complexity_score` is integer 1-10
- ✅ `has_workload_metric` is always `true`
- ✅ `enriched_by` is always `"workload_analysis_v1"`
- ✅ `labor_drivers` array is empty if Labor not in `workload_categories`
- ✅ `material_needs` array is empty if Materials not in `workload_categories`
- ✅ JSON is valid and parseable

---

**Remember**: This analysis supports real proposal development. Accuracy matters for cost estimation, staffing plans, and BOM creation. Prioritize evidence-based classification over speculation.
