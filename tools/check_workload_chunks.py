"""Check the chunk content that contains workload data to see if it has Appendix H context."""
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

workspace = 'rag_storage/swa_tas'

# Load text chunks
with open(f'{workspace}/kv_store_text_chunks.json', 'r', encoding='utf-8') as f:
    chunks = json.load(f)

print(f'Total chunks: {len(chunks)}')

# Find chunks that contain "H.2" or "Estimated Monthly Workload"
print('\n=== Chunks containing "H.2" or "workload" ===')
workload_chunks = []
for chunk_id, chunk_data in chunks.items():
    content = chunk_data.get('content', '').lower() if isinstance(chunk_data, dict) else ''
    if 'h.2' in content or 'estimated monthly workload' in content:
        workload_chunks.append((chunk_id, chunk_data))

print(f'Found {len(workload_chunks)} chunks with H.2 or workload')
for chunk_id, chunk_data in workload_chunks[:3]:
    print(f'\n=== {chunk_id} ===')
    content = chunk_data.get('content', '') if isinstance(chunk_data, dict) else str(chunk_data)
    # Check if Appendix H is mentioned in same chunk
    has_appendix_h = 'appendix h' in content.lower()
    print(f'Has "Appendix H" in same chunk: {has_appendix_h}')
    print(f'Content preview (first 800 chars):')
    print(content[:800])
    print()

# Find chunks that contain aircraft operations table data
print('\n=== Chunks containing aircraft counts (760, C-130, C-17) ===')
aircraft_chunks = []
for chunk_id, chunk_data in chunks.items():
    content = chunk_data.get('content', '').lower() if isinstance(chunk_data, dict) else ''
    if ('760' in content or 'c-130' in content) and 'aircraft' in content:
        aircraft_chunks.append((chunk_id, chunk_data))

print(f'Found {len(aircraft_chunks)} chunks with aircraft data')
for chunk_id, chunk_data in aircraft_chunks[:2]:
    print(f'\n=== {chunk_id} ===')
    content = chunk_data.get('content', '') if isinstance(chunk_data, dict) else str(chunk_data)
    has_appendix_h = 'appendix h' in content.lower()
    print(f'Has "Appendix H" in same chunk: {has_appendix_h}')
    print(f'Content preview (first 800 chars):')
    print(content[:800])
