"""Check what VDB implementation is being used."""
import os
from dotenv import load_dotenv
load_dotenv()

# Check the VDB storage type from LightRAG
from lightrag.api.config import global_args

print(f'KV Storage: {getattr(global_args, "kv_storage", "not set")}')
print(f'VDB Storage: {getattr(global_args, "vdb_storage", "not set")}')
print(f'Working dir: {getattr(global_args, "working_dir", "not set")}')

# List all VDB-related classes  
print('\n=== VDB Implementations ===')
try:
    from lightrag.kg import vdb_impl
    print(f'VDB module: {vdb_impl.__file__}')
    print(f'Classes: {[x for x in dir(vdb_impl) if not x.startswith("_")]}')
except ImportError as e:
    print(f'Could not import vdb_impl: {e}')

# Check NanoVectorDBStorage directly
print('\n=== NanoVectorDB ===')
try:
    from lightrag.kg.vdb_impl import NanoVectorDBStorage
    print(f'NanoVectorDBStorage found')
    # Check upsert method signature
    import inspect
    sig = inspect.signature(NanoVectorDBStorage.upsert)
    print(f'upsert signature: {sig}')
except Exception as e:
    print(f'Error: {e}')
