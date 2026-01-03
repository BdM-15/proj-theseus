"""Debug entity storage to understand where entity_type gets lost."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# Check kv_store_full_docs - document content
print('=== kv_store_full_docs structure ===')
with open(f'{workspace}/kv_store_full_docs.json', 'r', encoding='utf-8') as f:
    docs = json.load(f)

for i, (doc_id, doc) in enumerate(list(docs.items())[:1]):
    print(f'Doc: {doc_id}')
    print(f'Keys: {list(doc.keys()) if isinstance(doc, dict) else type(doc)}')
    if isinstance(doc, dict) and 'content' in doc:
        content_sample = doc.get('content', '')[:500]
        print(f'Content sample: {content_sample}')

# Check entity_chunks mapping
print('\n=== kv_store_entity_chunks sample ===')
with open(f'{workspace}/kv_store_entity_chunks.json', 'r', encoding='utf-8') as f:
    entity_chunks = json.load(f)
print(f'Total entity mappings: {len(entity_chunks)}')
for i, (eid, data) in enumerate(list(entity_chunks.items())[:5]):
    print(f'{eid}: {data}')

# Check if LLM response cache has entity types
print('\n=== LLM Response Cache (extraction output) ===')
with open(f'{workspace}/kv_store_llm_response_cache.json', 'r', encoding='utf-8') as f:
    llm_cache = json.load(f)
print(f'Total cached responses: {len(llm_cache)}')

# Look for entity extraction output with entity types
for key, response in list(llm_cache.items())[:2]:
    print(f'\n--- Cache Key: {key[:80]}... ---')
    resp_str = str(response)[:1000]
    # Look for entity type patterns in the output
    if 'entity' in resp_str.lower() and '<|#|>' in resp_str:
        print('Contains extraction format!')
        print(resp_str[:800])
    else:
        print(f'Response type: {type(response)}, length: {len(resp_str)}')
