"""Check what happened to page 53 chunks (Appendix H + workload data)."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# Load text chunks
with open(f'{workspace}/kv_store_text_chunks.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print('=== Chunks from Page 53 (Appendix H page) ===')
page_53_chunks = []
for chunk_id, chunk_data in chunks.items():
    if chunk_data.get('page_idx') == 53:
        page_53_chunks.append((chunk_id, chunk_data))

print(f"Found {len(page_53_chunks)} chunks from page 53")
for chunk_id, chunk_data in page_53_chunks:
    print(f"\nChunk: {chunk_id}")
    print(f"  Type: {chunk_data.get('original_type', 'text')}")
    print(f"  Is multimodal: {chunk_data.get('is_multimodal', False)}")
    content = chunk_data.get('content', '')
    print(f"  Has 'Appendix H': {'appendix h' in content.lower()}")
    print(f"  Has 'ADAB': {'adab' in content.lower()}")
    print(f"  Has 'workload': {'workload' in content.lower()}")
    print(f"  Content preview: {content[:500]}...")

# Also check MinerU blocks from page 53
print('\n\n=== MinerU Parse Cache - Page 53 blocks ===')
with open(f'{workspace}/kv_store_parse_cache.json', 'r', encoding='utf-8') as f:
    parse_cache = json.load(f)

for cache_key, cache_data in parse_cache.items():
    content_list = cache_data.get('content_list', [])
    
    page_53_blocks = [b for b in content_list if isinstance(b, dict) and b.get('page_idx') == 53]
    print(f"Page 53 has {len(page_53_blocks)} content blocks")
    
    for block in page_53_blocks:
        block_type = block.get('type', 'unknown')
        text = str(block.get('text', ''))[:200]
        print(f"\n  Type: {block_type}")
        print(f"  Text: {text}...")

# Check nearby pages too (52, 54) for context
print('\n\n=== Checking pages 52-54 for Appendix H context ===')
for page_idx in [52, 54]:
    page_chunks = [(cid, cd) for cid, cd in chunks.items() if cd.get('page_idx') == page_idx]
    print(f"\nPage {page_idx}: {len(page_chunks)} chunks")
    for chunk_id, chunk_data in page_chunks[:2]:
        content = chunk_data.get('content', '')[:200]
        has_appendix_h = 'appendix h' in chunk_data.get('content', '').lower()
        print(f"  Has Appendix H: {has_appendix_h}")
        print(f"  Preview: {content}...")
