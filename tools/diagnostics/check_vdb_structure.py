"""Quick diagnostic to compare VDB structure between workspaces."""
import json
import sys

def check_workspace(path):
    """Check VDB structure for a workspace."""
    print(f"\n{'='*60}")
    print(f"Checking: {path}")
    print('='*60)
    
    # Load vdb_chunks
    with open(f'{path}/vdb_chunks.json', 'r', encoding='utf-8') as f:
        vdb = json.load(f)
    
    data = vdb.get('data', [])
    print(f"Total chunks in vdb_chunks: {len(data)}")
    
    if data:
        # Show structure of first chunk
        first = data[0]
        if isinstance(first, dict):
            print(f"Chunk structure keys: {list(first.keys())}")
            # Check if __id__ contains useful info
            print(f"First chunk __id__: {first.get('__id__', 'N/A')[:100]}...")
        elif isinstance(first, list):
            print(f"Chunk is a list with {len(first)} elements")
            print(f"First element type: {type(first[0])}")
    
    # Load kv_store_text_chunks for comparison
    with open(f'{path}/kv_store_text_chunks.json', 'r', encoding='utf-8') as f:
        kv_chunks = json.load(f)
    
    print(f"Total chunks in kv_store: {len(kv_chunks)}")
    
    # Check if file_path is in kv_store
    sample_key = list(kv_chunks.keys())[0]
    sample_chunk = kv_chunks[sample_key]
    print(f"KV chunk keys: {list(sample_chunk.keys())}")
    print(f"file_path value: {sample_chunk.get('file_path', 'NOT FOUND')}")

if __name__ == '__main__':
    workspaces = sys.argv[1:] if len(sys.argv) > 1 else [
        'rag_storage/2_mcpp_drfp_2025',
        'rag_storage/39_test_mcpp'
    ]
    for ws in workspaces:
        try:
            check_workspace(ws)
        except Exception as e:
            print(f"Error checking {ws}: {e}")

