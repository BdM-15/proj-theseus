# Workload Data Archetypes

Four recurring data patterns in Section J govcon attachments. A single spreadsheet
may contain multiple archetypes across tabs.

---

## Archetype 1: Geographic Scope

**What it is:** A roster of locations where work is performed.

**Recognition signals:**

- Columns containing location names, city/state/country, installation names
- Site codes or identifiers (DODAAC, UIC, base codes, facility IDs)
- Tab names like "Sites", "Locations", "Coverage", "AOR", "Installations"
- CONUS / OCONUS grouping (often in separate tabs)
- Columns like "Location", "State", "Country", "Region", "AOR"
- May include a manning column (FTEs or seats per site)

**Does NOT typically contain:** historical volumes, case counts, dollar amounts

**Join key to watch for:** Site code or name — this is how it links to Demand History

**Pricing implication:** Total site count drives minimum staffing floor (you need
at least one visit per site per period if PM visits are required). OCONUS sites
drive per-diem, travel, and potential SOFA compliance costs.

---

## Archetype 2: Demand / Volume History

**What it is:** Actual or estimated units of work over time, often broken down
by location and work type.

**Recognition signals:**

- Year or period columns (FY2022, FY2023, CY2024, Q1, etc.)
- Numeric counts of events, cases, tickets, visits, incidents, tasks
- Work-type columns (PM, CM, upgrade, repair, installation, etc.)
- Totals rows at the bottom
- Average or rollup columns (CM Average, Annual Total, etc.)
- Footnotes with adjustment factors (phone resolution %, exclusion criteria)
- Tab names like "Workload", "Cases", "History", "Demand", "Volume", "Incidents"

**Key patterns to detect:**

- Multi-year time series → trend analysis
- Work-type split (preventive vs. corrective, scheduled vs. unscheduled)
- Hidden adjustment factors in footnotes
- TOTAL row at bottom (validate: does it sum correctly?)

**Join key:** Site code or name linking back to Geographic Scope

**Pricing implication:** This is the core labor model driver. Growth rate and
Pareto concentration directly determine staffing levels and cost risk in option years.

---

## Archetype 3: Manning / Staffing

**What it is:** Current or proposed headcount by role, location, or period.

**Recognition signals:**

- Columns for FTE, headcount, positions, seats, billets
- Labor category or role names (Program Manager, Technician, Field Engineer, etc.)
- Location or site dimension
- Period of performance dimension (base year, option years)
- Tab names like "Staffing", "Manning", "Labor", "Positions", "Org Chart"

**Key patterns to detect:**

- Coverage ratio = staff ÷ site count (flag if <1.0 for field-touch roles)
- Surge headcount vs. steady-state
- Geographic distribution of staff vs. geographic distribution of work

**Pricing implication:** If government-provided staffing plan exists, compare
to demand history to validate coverage ratios. Understaffed models are a risk
to quality; overstaffed models are a pricing competitiveness risk.

---

## Archetype 4: CLIN / Task Structure

**What it is:** The contractual line-item breakdown of deliverables, quantities,
and unit types.

**Recognition signals:**

- CLIN numbers or identifiers (0001, 0002AA, etc.)
- Unit of Measure columns (each, lot, hour, month, year)
- Quantity columns
- Option year structure (Base, Option 1, Option 2, etc.)
- Tab names like "CLINs", "SOW", "Deliverables", "Schedule B", "Pricing"

**Key patterns to detect:**

- Quantity deltas across option years (flat = potential underestimate if demand growing)
- Unit type mismatches (hourly vs. fixed-price CLINs for variable-demand work)
- CLINs with zero quantities (placeholder? oversight?)
- Cost-type vs. FFP CLINs (signals government's risk transfer intent)

**Pricing implication:** CLIN structure determines contract type risk. A fixed-price
CLIN for work with high historical variability is a pricing trap.

---

## Multi-Archetype Sheets

Occasionally a single tab combines archetypes — e.g., site list with a volume
column appended. Treat it as both archetypes and apply both frameworks. The join
key is usually in the same row.

When in doubt about archetype: look at what the columns _measure_ (location/identity
→ Scope; counts over time → Demand; people/roles → Manning; line items → CLIN) rather
than what they are named.
