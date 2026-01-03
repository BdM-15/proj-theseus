"""Check chunks specifically for ADAB (Al Dhafra) content and Appendix H."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# Load text chunks
with open(f'{workspace}/kv_store_text_chunks.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print(f'Total chunks: {len(chunks)}')

# Find chunks that contain ADAB or Al Dhafra
print('\n=== Chunks containing "ADAB" or "Al Dhafra" ===')
adab_chunks = []
for chunk_id, chunk_data in chunks.items():
    content = chunk_data.get('content', '').lower() if isinstance(chunk_data, dict) else ''
    if 'adab' in content or 'al dhafra' in content or 'dhafra' in content:
        adab_chunks.append((chunk_id, chunk_data))

print(f'Found {len(adab_chunks)} chunks with ADAB/Al Dhafra')

# Check each for Appendix H context
for chunk_id, chunk_data in adab_chunks:
    content = chunk_data.get('content', '') if isinstance(chunk_data, dict) else str(chunk_data)
    has_appendix_h = 'appendix h' in content.lower()
    has_workload = 'workload' in content.lower() or 'aircraft' in content.lower()
    has_h2 = 'h.2' in content.lower() or 'h.1' in content.lower()
    
    # Only show chunks that look relevant
    if has_appendix_h or has_workload or has_h2:
        print(f'\n=== {chunk_id} ===')
        print(f'  Appendix H: {has_appendix_h}')
        print(f'  Has workload/aircraft: {has_workload}')
        print(f'  Has H.2/H.1 reference: {has_h2}')
        print(f'Content preview (first 500 chars):')
        print(content[:500])
        print()

# Also check parse cache for MinerU output
print('\n=== Checking parse cache for ADAB content ===')
with open(f'{workspace}/kv_store_parse_cache.json', 'r', encoding='utf-8') as f:
    parse_cache = json.load(f)

print(f'Total parse cache entries: {len(parse_cache)}')
for cache_id, cache_data in list(parse_cache.items()):
    content_list = cache_data.get('content_list', []) if isinstance(cache_data, dict) else []
    for item in content_list:
        text = item.get('text', '') if isinstance(item, dict) else ''
        if 'h.2' in text.lower() and 'adab' in text.lower():
            print(f'\nFound H.2 + ADAB in {cache_id}:')
            print(f'Type: {item.get("type")}')
            print(f'Text: {text[:400]}')
