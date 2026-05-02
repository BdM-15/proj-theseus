# Workload Analysis Report

**Workspace:** {{workspace}}
**Analyst:** Theseus Workload Analyzer
**Source Attachments:** {{source_attachments}}
**Analysis Date:** {{date}}

---

## 1. Data Inventory

| Sheet / Tab    | Rows     | Columns  | Archetype     | Coverage Period |
| -------------- | -------- | -------- | ------------- | --------------- |
| {{sheet_name}} | {{rows}} | {{cols}} | {{archetype}} | {{period}}      |

**Join Key:** {{join_key_description}}

**Schema Notes:** {{any_schema_anomalies}}

---

## 2. Geographic Scope

**Total Sites:** {{site_count_total}}
**CONUS:** {{conus_count}} | **OCONUS:** {{oconus_count}}
**High-Risk OCONUS:** {{oconus_high_risk_count}}

### OCONUS Risk Register

| Location     | Tier     | Rationale     |
| ------------ | -------- | ------------- |
| {{location}} | {{tier}} | {{rationale}} |

### Geographic Concentration

{{concentration_narrative}}

---

## 3. Demand / Volume Analysis

**Period Covered:** {{period_start}} – {{period_end}}
**Base-Year Volume (raw):** {{raw_volume}}
**Adjustment Factors Applied:**

| Factor          | Value     | Basis     | Variable?    |
| --------------- | --------- | --------- | ------------ |
| {{factor_name}} | {{value}} | {{basis}} | {{variable}} |

**Field-Touch Volume (adjusted):** {{adjusted_volume}}
**CAGR:** {{cagr_pct}}%

### Pareto Concentration

| Tier                   | Sites        | Site Names   | Volume Share |
| ---------------------- | ------------ | ------------ | ------------ |
| Tier 1 (50% of volume) | {{t1_count}} | {{t1_names}} | {{t1_pct}}%  |
| Tier 2 (80% of volume) | {{t2_count}} | {{t2_names}} | {{t2_pct}}%  |
| Tier 3                 | {{t3_count}} | (low volume) | {{t3_pct}}%  |

### Option-Year Projections

| Period   | Conservative | Base         | Optimistic  |
| -------- | ------------ | ------------ | ----------- |
| Option 1 | {{op1_cons}} | {{op1_base}} | {{op1_opt}} |
| Option 2 | {{op2_cons}} | {{op2_base}} | {{op2_opt}} |
| Option 3 | {{op3_cons}} | {{op3_base}} | {{op3_opt}} |
| Option 4 | {{op4_cons}} | {{op4_base}} | {{op4_opt}} |

---

## 4. Pricing Risks (Ranked)

| Rank | Item     | Risk Type     | Description     | Impact     |
| ---- | -------- | ------------- | --------------- | ---------- |
| 1    | {{item}} | {{risk_type}} | {{description}} | {{impact}} |

---

## 5. Estimator Assumptions to Validate

1. {{assumption_1}}
2. {{assumption_2}}
3. {{assumption_3}}

---

## 6. PTW Handoff Envelope

```json
{{ptw_json_envelope}}
```

---

## 7. Confidence Assessment

**Overall:** {{confidence_level}}
**Basis:** {{confidence_rationale}}
