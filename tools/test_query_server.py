"""
Test actual query through the LightRAG API
"""
import requests
import json

# Test query
response = requests.post(
    "http://localhost:9621/query",
    json={
        "query": "What is the workload at ADAB?",
        "mode": "mix",
        "only_need_context": True
    }
)

data = response.json()

print("=" * 80)
print("ACTUAL QUERY TEST - Through Server")
print("=" * 80)

print(f"\nStatus: {data.get('status')}")
print(f"\nKeywords:")
keywords = data.get('metadata', {}).get('keywords', {})
print(f"  High-level: {keywords.get('high_level', [])}")
print(f"  Low-level: {keywords.get('low_level', [])}")

print(f"\nProcessing Info:")
proc = data.get('metadata', {}).get('processing_info', {})
print(f"  Total entities found: {proc.get('total_entities_found', '?')}")
print(f"  Entities after truncation: {proc.get('entities_after_truncation', '?')}")
print(f"  Total relations found: {proc.get('total_relations_found', '?')}")
print(f"  Relations after truncation: {proc.get('relations_after_truncation', '?')}")

print(f"\nRetrieved entities ({len(data.get('data', {}).get('entities', []))}):")
entities = data.get('data', {}).get('entities', [])
for i, e in enumerate(entities[:15], 1):
    name = e.get('entity_name', '?')
    etype = e.get('entity_type', '?')
    desc_preview = e.get('description', '')[:100]
    # Check if it's a workload/table entity
    is_workload = 'workload' in name.lower() or 'table' in name.lower() or 'H.2.0' in name
    marker = "⭐" if is_workload else "  "
    print(f"{marker} {i:2}. [{etype}] {name}")
    print(f"        {desc_preview}...")

# Look for table/workload entities specifically
print("\n" + "=" * 80)
print("WORKLOAD/TABLE ENTITIES IN RESULTS")
print("=" * 80)
workload_entities = [e for e in entities 
                     if 'workload' in e.get('entity_name', '').lower() 
                     or 'table' in e.get('entity_name', '').lower()
                     or 'H.2.0' in e.get('entity_name', '')]
if workload_entities:
    print(f"✅ Found {len(workload_entities)} workload/table entities")
    for e in workload_entities:
        print(f"   - {e.get('entity_name')}")
else:
    print("❌ NO workload/table entities in retrieved context!")
