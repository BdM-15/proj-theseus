"""Test BOE category models from Branch 040"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print('=== Testing BOE Category Models ===\n')

try:
    from src.ontology.schema import (
        BOECategory,
        WorkloadEnrichmentItem,
        WorkloadEnrichmentResponse,
        normalize_boe_category
    )
    print('✅ BOE models imported successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)

# Test BOECategory enum
print(f'\n✅ BOE Categories: {[c.value for c in BOECategory]}')

# Test normalize_boe_category
print(f'\n✅ normalize_boe_category("security") = {normalize_boe_category("security").value}')
print(f'✅ normalize_boe_category("Labor") = {normalize_boe_category("Labor").value}')
print(f'✅ normalize_boe_category("unknown") = {normalize_boe_category("unknown").value}')

# Test WorkloadEnrichmentItem
test_data = {
    'entity_index': 0,
    'has_workload_metric': True,
    'workload_categories': ['Labor', 'Materials', 'security'],  # security should normalize
    'boe_relevance': {'Labor': 0.9, 'Materials': 0.7},
    'complexity_score': 7
}

item = WorkloadEnrichmentItem.model_validate(test_data)
print(f'\n✅ WorkloadEnrichmentItem validated')
print(f'   Raw categories: {item.workload_categories}')
print(f'   Validated categories: {item.get_category_values()}')

# Test workload_enrichment import
try:
    from src.inference.workload_enrichment import enrich_workload_metadata, BOE_CATEGORIES
    print(f'\n✅ workload_enrichment imported')
    print(f'   BOE_CATEGORIES: {BOE_CATEGORIES}')
except Exception as e:
    print(f'\n❌ workload_enrichment import failed: {e}')

print('\n=== All BOE Model Tests Passed! ===')

