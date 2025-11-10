# Validation Framework

Production readiness validation for RFP knowledge graph processing.

## Architecture

```
tools/
├── validate_rfp_processing.py  # Main orchestrator (run this)
└── validation/                 # Modular validators
    ├── __init__.py
    ├── query_quality.py        # Metric 1: Query answer quality (30%)
    ├── section_l_m_coverage.py # Metric 2: Req ↔ eval linkage (25%)
    ├── workload_completeness.py# Metric 3: BOE enrichment (25%)
    └── deliverable_traceability.py # Metric 4: Deliv → req mapping (20%)
```

## Quick Start

```powershell
# Run full validation (recommended)
python tools/validate_rfp_processing.py

# Run for specific workspace
python tools/validate_rfp_processing.py afcapv_adab_iss_2025

# Run individual metric
python tools/validation/workload_completeness.py
```

## Validation Metrics

### 1. Query Quality (30% weight)

Tests knowledge graph with 5 predefined queries covering:

- Workload/labor requirements
- Section L↔M mapping
- Deliverable requirements
- QA/compliance requirements
- GFE/government resources

**Pass**: Graph contains entities to answer queries

### 2. Section L↔M Coverage (25% weight)

Validates requirements ↔ evaluation factor relationships:

- % requirements linked to eval criteria
- % eval factors linked to requirements
- Identifies orphaned entities

**Target**: 85%+ bidirectional coverage

### 3. Workload Enrichment Completeness (25% weight)

Validates BOE metadata on requirements:

- % requirements enriched with workload properties
- Coverage of all 7 BOE categories (Labor, Materials, ODCs, QA, Logistics, Lifecycle, Compliance)
- Average confidence scores

**Target**: 95%+ enrichment, all categories used

### 4. Deliverable Traceability (20% weight)

Validates deliverable → requirement relationships:

- % deliverables linked to requirements
- % requirements with deliverable outputs
- Identifies orphaned deliverables

**Target**: 80%+ traceability

## Production Readiness Thresholds

| Score  | Status              | Action                      |
| ------ | ------------------- | --------------------------- |
| 85%+   | ✅ PRODUCTION READY | Deploy with confidence      |
| 70-85% | ⚠️ PASS             | Minor gaps, document issues |
| < 70%  | ❌ FAIL             | Reprocess or manual review  |

## Example Output

```
🎯 RFP PROCESSING VALIDATION REPORT
════════════════════════════════════════════════════════════════════════════════
Workspace: afcapv_adab_iss_2025
Overall Score: 93.5%
Status: ✅ PRODUCTION READY
        Deploy with confidence

METRIC SCORES:
────────────────────────────────────────────────────────────────────────────────
  ✅ Query Quality                   92.0%  (queries answered)
  ✅ Section L↔M Coverage            88.0%  (requirements linked)
  ✅ Workload Enrichment            100.0%  (requirements enriched)
  ✅ Deliverable Traceability        94.0%  (deliverables traced)

════════════════════════════════════════════════════════════════════════════════
✅ OVERALL: PRODUCTION READY (93.5%)
════════════════════════════════════════════════════════════════════════════════
```

## Adding New Metrics

1. Create new validator in `tools/validation/`:

   ```python
   class MyValidator:
       def __init__(self, workspace: str):
           # Initialize Neo4j connection

       def validate(self) -> Dict[str, any]:
           # Return {"score": 0-100, "details": ...}

       def print_report(self, results: Dict):
           # Print formatted report
   ```

2. Add to `__init__.py`:

   ```python
   from .my_validator import MyValidator
   ```

3. Update `validate_rfp_processing.py`:

   ```python
   validators["my_metric"] = MyValidator(workspace)
   results["my_metric"] = validators["my_metric"].validate()
   ```

4. Adjust weights in `calculate_overall_score()` to total 100%

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate RFP Processing
  run: |
    python tools/validate_rfp_processing.py afcapv_adab_iss_2025
  # Exits with code 0 (success) if score >= 70%
  # Exits with code 1 (failure) if score < 70%
```

## Extensibility

The modular design allows:

- Individual metric testing (`python tools/validation/query_quality.py`)
- A/B testing different prompts (compare scores before/after)
- Automated quality gates in deployment pipelines
- Custom metrics for specific RFP types (e.g., "Berry Amendment Compliance")

## Notes

- All validators use same Neo4j connection from `.env`
- Workspace isolation prevents cross-contamination
- Metrics are **objective** (based on graph structure, not subjective assessment)
- Designed for **federal RFP domain** but extensible to other document types
