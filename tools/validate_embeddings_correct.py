#!/usr/bin/env python
"""
Correct validation of NanoVectorDB embeddings.

The NanoVectorDB storage uses Float16 + zlib + Base64 compression.
Previous diagnostic was incorrectly decoding as raw Float32.
"""

import json
import base64
import zlib
import numpy as np
from pathlib import Path


def validate_vdb_embeddings(vdb_path: str, sample_size: int = 10):
    """Validate embeddings using correct decompression."""
    
    print(f"\n{'='*70}")
    print(f"Validating: {vdb_path}")
    print(f"{'='*70}")
    
    with open(vdb_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    declared_dim = vdb_data.get("embedding_dim", "unknown")
    print(f"\nDeclared embedding_dim: {declared_dim}")
    
    entities = vdb_data.get("data", [])
    print(f"Total entities: {len(entities)}")
    
    valid_count = 0
    invalid_count = 0
    
    for i, entity in enumerate(entities[:sample_size]):
        entity_id = entity.get("__id__", f"entity_{i}")
        vector_str = entity.get("vector", "")
        
        if not vector_str:
            print(f"\n[{i}] {entity_id}: NO VECTOR DATA")
            invalid_count += 1
            continue
        
        try:
            # CORRECT decoding: Base64 -> zlib decompress -> Float16 -> Float32
            decoded = base64.b64decode(vector_str)
            decompressed = zlib.decompress(decoded)
            vector_f16 = np.frombuffer(decompressed, dtype=np.float16)
            vector_f32 = vector_f16.astype(np.float32)
            
            dim = len(vector_f32)
            norm = np.linalg.norm(vector_f32)
            
            # Validation checks
            is_valid_dim = (dim == declared_dim)
            has_valid_values = (not np.any(np.isnan(vector_f32)) and 
                               not np.any(np.isinf(vector_f32)))
            is_normalized = (0.8 < norm < 1.2)  # OpenAI embeddings are normalized
            
            status = "✅ VALID" if (is_valid_dim and has_valid_values) else "❌ INVALID"
            
            entity_name = entity.get("entity_name", "unknown")[:50]
            print(f"\n[{i}] {status}")
            print(f"    Entity: {entity_name}")
            print(f"    Dimension: {dim} (expected {declared_dim})")
            print(f"    Norm: {norm:.4f}")
            print(f"    First 5 values: {vector_f32[:5]}")
            
            if is_valid_dim and has_valid_values:
                valid_count += 1
            else:
                invalid_count += 1
                
        except zlib.error as e:
            print(f"\n[{i}] ❌ ZLIB ERROR: {e}")
            print(f"    Entity: {entity.get('entity_name', 'unknown')[:50]}")
            invalid_count += 1
            
        except Exception as e:
            print(f"\n[{i}] ❌ ERROR: {type(e).__name__}: {e}")
            invalid_count += 1
    
    print(f"\n{'='*70}")
    print(f"SUMMARY (first {sample_size} entities)")
    print(f"{'='*70}")
    print(f"Valid:   {valid_count}")
    print(f"Invalid: {invalid_count}")
    
    # Full validation
    print(f"\n\nFull validation of all {len(entities)} entities...")
    full_valid = 0
    full_invalid = 0
    
    for entity in entities:
        vector_str = entity.get("vector", "")
        if not vector_str:
            full_invalid += 1
            continue
            
        try:
            decoded = base64.b64decode(vector_str)
            decompressed = zlib.decompress(decoded)
            vector_f16 = np.frombuffer(decompressed, dtype=np.float16)
            vector_f32 = vector_f16.astype(np.float32)
            
            if (len(vector_f32) == declared_dim and 
                not np.any(np.isnan(vector_f32)) and 
                not np.any(np.isinf(vector_f32))):
                full_valid += 1
            else:
                full_invalid += 1
        except:
            full_invalid += 1
    
    print(f"\nFULL RESULTS:")
    print(f"Valid embeddings:   {full_valid}/{len(entities)}")
    print(f"Invalid embeddings: {full_invalid}/{len(entities)}")
    
    return full_valid, full_invalid


if __name__ == "__main__":
    # Check vdb_entities.json
    vdb_path = Path("rag_storage/swa_tas/vdb_entities.json")
    
    if vdb_path.exists():
        valid, invalid = validate_vdb_embeddings(str(vdb_path), sample_size=10)
        
        if valid > 0 and invalid == 0:
            print("\n" + "="*70)
            print("🎉 EMBEDDINGS ARE VALID!")
            print("The previous diagnostic was using incorrect decoding.")
            print("Your EMBEDDING_DIM=3072 configuration is CORRECT for text-embedding-3-large.")
            print("="*70)
        elif valid > 0:
            print(f"\n⚠️ Mixed results: {valid} valid, {invalid} invalid")
        else:
            print("\n❌ All embeddings appear invalid - investigate further")
    else:
        print(f"File not found: {vdb_path}")
