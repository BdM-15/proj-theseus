"""
Workload and Pricing Knowledge Module

Evergreen knowledge about BOE and staffing:
- Basis of Estimate (BOE) calculation patterns
- Staffing ratios and formulas
- Common workload drivers
- Labor category patterns

Entity types: concept, requirement, performance_metric
Source: Industry benchmarks, GSA rates, common patterns

Note: These are PATTERNS and FORMULAS, not specific pricing.
RFP-specific workload data comes from document extraction.
"""

SOURCE_ID = "govcon_ontology_workload"
FILE_PATH = "workload_patterns"


# =============================================================================
# ENTITIES: Workload and Pricing Knowledge
# =============================================================================

ENTITIES = [
    # -------------------------------------------------------------------------
    # BOE Fundamentals
    # -------------------------------------------------------------------------
    {
        "entity_name": "Basis of Estimate Development",
        "entity_type": "concept",
        "description": (
            "Basis of Estimate (BOE) documentation supports proposed labor hours and costs. "
            "BOE elements: (1) Workload drivers from RFP (quantities, frequencies, volumes), "
            "(2) Assumptions clearly stated, (3) Historical data from similar efforts, "
            "(4) Productivity factors and utilization rates, (5) Staffing calculations with "
            "rationale, (6) Risk factors and contingencies. Strong BOEs are traceable - "
            "every hour ties to RFP requirements or reasonable assumptions. Government "
            "Cost Realism Analysis validates BOE supportability. Weak BOEs undermine "
            "confidence in proposal credibility."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Labor Hour Calculation Methodology",
        "entity_type": "concept",
        "description": (
            "Standard methodology for calculating labor hours from workload: "
            "(1) Identify workload drivers (tickets/month, systems, users, deliverables), "
            "(2) Determine task time standards (hours per ticket, hours per system), "
            "(3) Calculate raw hours (driver × time standard), (4) Apply productivity "
            "factors (available hours vs calendar hours), (5) Add supervision/management "
            "overhead (typically 10-15%), (6) Apply skill mix (senior vs junior ratios). "
            "Formula: FTEs = (Annual Workload × Hours/Unit) ÷ (Annual Available Hours × Utilization). "
            "Document all inputs and assumptions for traceability."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Utilization Rate Standards",
        "entity_type": "performance_metric",
        "description": (
            "Utilization rates convert calendar time to productive hours. Industry standards: "
            "Annual calendar hours: 2,080 (40hr × 52wks). Deductions: Federal holidays (10 days = 80hrs), "
            "Annual leave (typical 15-20 days = 120-160hrs), Sick leave (typical 10 days = 80hrs), "
            "Training (typical 40-80hrs). Net productive hours: 1,680-1,760 annually. "
            "Utilization rate: 80-85% of calendar hours. Direct labor hours for billing "
            "further reduced by overhead activities. Use customer-specified rates if "
            "provided in RFP; otherwise use industry standards with documented assumptions."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH,
        "threshold": "80-85% of calendar hours"
    },
    
    # -------------------------------------------------------------------------
    # Service Desk Staffing
    # -------------------------------------------------------------------------
    {
        "entity_name": "Service Desk Staffing Model",
        "entity_type": "concept",
        "description": (
            "Service desk/help desk staffing based on ticket volume and service levels. "
            "Key drivers: (1) Monthly ticket volume (from RFP or historical data), "
            "(2) Average handle time (AHT) per ticket type (typically 10-30 minutes), "
            "(3) First call resolution (FCR) target (typically 70-85%), (4) Service "
            "level agreement (e.g., 80% answered within 60 seconds), (5) Coverage hours "
            "(8×5, 12×5, 24×7). Erlang C formula for queue-based staffing. Rule of thumb: "
            "1 FTE per 400-600 tickets/month for Tier 1 support. Add Tier 2/3 escalation "
            "staff at 20-30% of Tier 1 volume. Adjust for complexity and SLA stringency."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Tiered Support Staffing Ratios",
        "entity_type": "concept",
        "description": (
            "Multi-tier support models with escalation-based staffing. Tier 1 (Help Desk): "
            "First contact, password resets, basic troubleshooting - highest volume, "
            "lowest cost labor. Tier 2 (Technical Support): Escalated issues, system "
            "admin tasks - 20-30% of Tier 1 volume. Tier 3 (Engineering): Complex issues, "
            "development, root cause analysis - 5-10% of Tier 1 volume. Typical ratios: "
            "10:3:1 (Tier 1:Tier 2:Tier 3). Adjust based on FCR targets - higher FCR "
            "needs more skilled Tier 1 staff. Document escalation assumptions in BOE."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # O&M and System Support
    # -------------------------------------------------------------------------
    {
        "entity_name": "Operations and Maintenance Staffing Model",
        "entity_type": "concept",
        "description": (
            "O&M staffing based on system complexity and availability requirements. "
            "Drivers: (1) Number of systems/applications supported, (2) Technology complexity, "
            "(3) Availability requirements (99.9% vs 99.99%), (4) Change volume (releases, "
            "patches, configurations), (5) Coverage model (follow-the-sun, on-call, 24×7). "
            "Rule of thumb: 1 FTE per 3-5 moderately complex systems for steady-state O&M. "
            "High-availability systems (99.99%+) require dedicated staff per system. "
            "Include application-specific SMEs, DBAs, and infrastructure support in mix."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "System Administration Staffing Ratios",
        "entity_type": "concept",
        "description": (
            "System admin staffing based on infrastructure complexity. Server admin ratios: "
            "1 admin per 30-50 physical servers, 1 admin per 50-100 virtual servers "
            "(virtualization efficiency). Network admin: 1 per 100-200 network devices. "
            "DBA: 1 per 5-10 production databases (varies by complexity). Storage admin: "
            "1 per 100-500 TB managed. Security admin: 1 per 500-1000 users for "
            "identity/access management. Adjust ratios based on automation level, "
            "tool maturity, and environment stability. Document ratio assumptions."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Development and Engineering
    # -------------------------------------------------------------------------
    {
        "entity_name": "Software Development Staffing Model",
        "entity_type": "concept",
        "description": (
            "Development staffing based on scope and methodology. Drivers: (1) Lines of code "
            "or function points (for new development), (2) Story points per sprint (Agile), "
            "(3) Defect rates and rework factors, (4) Team composition (dev:test:PM ratios). "
            "Typical Agile team: 5-9 members including developers, testers, Scrum Master, "
            "Product Owner. Velocity-based planning: historical story points per sprint × "
            "planned sprints = capacity. Rule of thumb: 1 tester per 3-4 developers. "
            "Add 10-15% for DevSecOps, CI/CD pipeline maintenance, and technical debt."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Test and Quality Assurance Staffing",
        "entity_type": "concept",
        "description": (
            "QA/Test staffing ratios vary by risk tolerance and methodology. Traditional "
            "waterfall: 1 tester per 2-3 developers. Agile with continuous testing: "
            "1 tester per 4-5 developers (automation efficiency). High-criticality systems "
            "(medical, safety, financial): 1:1 or higher tester ratio. Test engineering "
            "(automation development): typically 1 per 3-4 manual testers. Independent "
            "V&V for critical systems adds 10-20% to development team size. Document "
            "test coverage targets and automation assumptions in BOE."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Travel and ODCs
    # -------------------------------------------------------------------------
    {
        "entity_name": "Travel Cost Estimation Patterns",
        "entity_type": "concept",
        "description": (
            "Travel estimation using government rates and frequency assumptions. Components: "
            "(1) Airfare - use GSA City Pair rates or current market (average $400-800 CONUS), "
            "(2) Lodging - GSA per diem rates by location, (3) M&IE - GSA rates ($59-$79/day "
            "typical CONUS), (4) Ground transportation - rental car or mileage, (5) Trip "
            "frequency from RFP or assumptions. Formula: Annual Travel = Trips × "
            "(Airfare + (Days × (Lodging + M&IE)) + Ground). Common assumptions: "
            "quarterly site visits, monthly PMR attendance, transition travel surge. "
            "Use actual GSA rates for proposal, update at contract execution."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "entity_name": "Other Direct Costs Estimation",
        "entity_type": "concept",
        "description": (
            "ODC categories beyond labor and travel requiring BOE support. Common ODCs: "
            "(1) Materials and supplies - based on historical spend or catalog pricing, "
            "(2) Software licenses - commercial pricing, volume discounts, maintenance, "
            "(3) Hardware - BOE quantities with unit pricing, refresh cycles, (4) Training - "
            "courses, certifications, conference attendance, (5) Subcontracts - pricing from "
            "teaming agreements, (6) Facility costs if contractor-furnished. Each ODC needs "
            "traceability to RFP requirement or operational assumption. Apply appropriate "
            "escalation factors for multi-year contracts."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # -------------------------------------------------------------------------
    # Labor Categories
    # -------------------------------------------------------------------------
    {
        "entity_name": "Labor Category Mix Planning",
        "entity_type": "concept",
        "description": (
            "Labor category selection based on task complexity and cost optimization. "
            "Typical hierarchy: Program Manager → Project Manager → Senior Engineer/Analyst → "
            "Mid-Level Engineer/Analyst → Junior Engineer/Analyst → Technician/Admin. "
            "Mix strategy: Use senior labor for complex tasks (architecture, design, customer "
            "interface), junior labor for routine tasks (testing, documentation, data entry). "
            "Target 40-60% mid-level, 20-30% senior, 20-30% junior for balanced capability "
            "and cost. Map labor categories to contract labor category descriptions and "
            "minimum qualifications. Ensure proposed rates align with GSA schedule or "
            "disclosed rate structure."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# RELATIONSHIPS: Workload Connections
# =============================================================================

RELATIONSHIPS = [
    # BOE relationships
    {
        "src_id": "Basis of Estimate Development",
        "tgt_id": "Labor Hour Calculation Methodology",
        "description": "BOE uses labor hour calculation methodology for staffing estimates",
        "keywords": "USES APPLIES",
        "weight": 0.95,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Labor Hour Calculation Methodology",
        "tgt_id": "Utilization Rate Standards",
        "description": "Labor hour calculations require utilization rates for FTE conversion",
        "keywords": "REQUIRES APPLIES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Basis of Estimate Development",
        "tgt_id": "Travel Cost Estimation Patterns",
        "description": "BOE includes travel cost estimation using standard patterns",
        "keywords": "INCLUDES APPLIES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "src_id": "Basis of Estimate Development",
        "tgt_id": "Other Direct Costs Estimation",
        "description": "BOE includes ODC estimation for non-labor costs",
        "keywords": "INCLUDES APPLIES",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Service desk relationships
    {
        "src_id": "Service Desk Staffing Model",
        "tgt_id": "Tiered Support Staffing Ratios",
        "description": "Service desk model uses tiered support staffing ratios",
        "keywords": "USES APPLIES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # O&M relationships
    {
        "src_id": "Operations and Maintenance Staffing Model",
        "tgt_id": "System Administration Staffing Ratios",
        "description": "O&M staffing uses system administration ratios",
        "keywords": "USES APPLIES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Development relationships
    {
        "src_id": "Software Development Staffing Model",
        "tgt_id": "Test and Quality Assurance Staffing",
        "description": "Development staffing includes QA/test staffing ratios",
        "keywords": "INCLUDES REQUIRES",
        "weight": 0.9,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    
    # Labor category relationships
    {
        "src_id": "Labor Category Mix Planning",
        "tgt_id": "Basis of Estimate Development",
        "description": "Labor category mix informs BOE labor distribution",
        "keywords": "INFORMS SUPPORTS",
        "weight": 0.85,
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]


# =============================================================================
# CHUNKS: Workload Knowledge Snippets
# =============================================================================

CHUNKS = [
    {
        "content": (
            "Service Desk Staffing Calculation Example: Given 5,000 tickets/month with 15-minute "
            "average handle time, 80% answered within 60 seconds SLA, and 8×5 coverage. "
            "Step 1: Calculate handle hours = 5,000 × 0.25 = 1,250 hours/month. "
            "Step 2: Add 20% for wrap-up and documentation = 1,500 hours/month. "
            "Step 3: Calculate FTEs at 160 productive hours/month = 9.4 FTEs for Tier 1. "
            "Step 4: Add Erlang C shrinkage factor of 1.2 for SLA = 11.3 FTEs Tier 1. "
            "Step 5: Add Tier 2 at 25% = 2.8 FTEs, Tier 3 at 10% = 1.1 FTEs. "
            "Step 6: Add supervisor at 1:8 ratio = 1.4 FTEs. Total = 16.6 FTEs, round to 17."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "BOE Traceability Requirements: Government Cost Realism Analysis examines whether "
            "proposed costs are realistic for the work to be performed. Weak BOEs with "
            "unsupported hours raise 'cost realism' concerns, suggesting either: (1) Contractor "
            "doesn't understand requirements, or (2) Contractor will under-perform. "
            "Strong BOE elements: (1) Every labor category hours tied to specific tasks, "
            "(2) Workload drivers cited from RFP with section references, (3) Productivity "
            "assumptions stated and reasonable, (4) Historical data from similar efforts cited, "
            "(5) Risk factors identified and quantified. Include BOE backup data in "
            "pricing volume. Enable evaluators to validate your staffing logic."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
    {
        "content": (
            "Labor Category Mapping Strategy: RFP labor category descriptions define minimum "
            "qualifications and experience levels. Mapping steps: (1) Extract RFP labor category "
            "definitions including years of experience, education, certifications, (2) Map "
            "proposed staff to appropriate categories based on qualifications, (3) Ensure "
            "rates align with category levels (senior rates for senior categories), "
            "(4) Verify proposed key personnel meet or exceed minimums, (5) Document any "
            "proposed equivalencies (e.g., experience substituting for education). "
            "Misalignment between staff qualifications and proposed categories undermines "
            "credibility and may constitute material misrepresentation."
        ),
        "source_id": SOURCE_ID,
        "file_path": FILE_PATH
    },
]
