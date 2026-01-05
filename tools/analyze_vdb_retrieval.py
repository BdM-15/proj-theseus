#!/usr/bin/env python3
"""
Analyze VDB structure and verify table context for retrieval quality.
"""

import json
import os

def main():
    workspace = "./rag_storage/swa_tas"
    vdb_file = os.path.join(workspace, "vdb_entities.json")
    
    with open(vdb_file, "r", encoding="utf-8") as f:
        vdb_data = json.load(f)
    
    print("=" * 70)
    print("VDB STRUCTURE ANALYSIS")
    print("=" * 70)
    
    print(f"\nTop-level keys: {list(vdb_data.keys())}")
    print(f"Embedding dimension: {vdb_data.get('embedding_dim')}")
    
    # Get the actual data
    data = vdb_data.get("data", [])
    print(f"Data entries: {len(data)}")
    
    # Analyze data structure
    if data:
        first_entry = data[0]
        print(f"\nEntry structure (list): {len(first_entry)} elements")
        print(f"  [0] Entity ID: {first_entry[0][:80] if isinstance(first_entry[0], str) else first_entry[0]}...")
        
        # Check what each element is
        for i, elem in enumerate(first_entry[1:], 1):
            if isinstance(elem, list) and len(elem) > 100:
                print(f"  [{i}] Vector: {len(elem)} dimensions")
            elif isinstance(elem, str):
                print(f"  [{i}] String: {elem[:100]}..." if len(elem) > 100 else f"  [{i}] String: {elem}")
            else:
                print(f"  [{i}] {type(elem).__name__}: {str(elem)[:100]}")
    
    # Find all table entries
    print("\n" + "-" * 70)
    print("TABLE ENTRIES IN VDB")
    print("-" * 70)
    
    table_entries = []
    for entry in data:
        entity_id = entry[0] if entry else ""
        if "table" in entity_id.lower():
            table_entries.append(entry)
    
    print(f"\nTable entries found: {len(table_entries)}")
    
    # Analyze context in table entries
    context_keywords = ["appendix", "section", "attachment", "h.2.0", "workload", "pws"]
    tables_with_context = 0
    
    print("\nSample table entries with context check:")
    
    for i, entry in enumerate(table_entries[:8]):
        entity_id = entry[0]
        
        # Combine all string content from entry
        content_parts = []
        for elem in entry:
            if isinstance(elem, str):
                content_parts.append(elem)
        
        combined_text = " ".join(content_parts).lower()
        found_context = [kw for kw in context_keywords if kw in combined_text]
        
        if found_context:
            tables_with_context += 1
            status = "✅"
        else:
            status = "⚠️"
        
        print(f"\n[{i+1}] {status} {entity_id}")
        if found_context:
            print(f"    Context found: {found_context}")
        
        # Show content preview
        for j, elem in enumerate(entry[1:], 1):
            if isinstance(elem, str) and len(elem) > 10:
                preview = elem[:150].replace('\n', ' ')
                print(f"    Field[{j}]: {preview}...")
    
    # Count all tables with context
    all_with_context = 0
    for entry in table_entries:
        content_parts = [e for e in entry if isinstance(e, str)]
        combined = " ".join(content_parts).lower()
        if any(kw in combined for kw in context_keywords):
            all_with_context += 1
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal VDB entries: {len(data)}")
    print(f"Table entries: {len(table_entries)}")
    print(f"Tables with context: {all_with_context}/{len(table_entries)}")
    
    if table_entries:
        coverage = (all_with_context / len(table_entries)) * 100
        print(f"Context coverage: {coverage:.1f}%")
        
        if coverage >= 80:
            print("\n✅ RETRIEVAL QUALITY: HIGH")
            print("   Tables have section context for semantic retrieval")
        elif coverage >= 50:
            print("\n⚠️ RETRIEVAL QUALITY: MEDIUM")
            print("   Some tables may not be found by context-based queries")
        else:
            print("\n❌ RETRIEVAL QUALITY: LOW")
            print("   Most tables lack context for semantic retrieval")
    
    # Also check KV store for entity descriptions
    print("\n" + "-" * 70)
    print("KV STORE ENTITY DESCRIPTION CHECK")
    print("-" * 70)
    
    kv_full = os.path.join(workspace, "kv_store_full_entities.json")
    if os.path.exists(kv_full):
        with open(kv_full, "r", encoding="utf-8") as f:
            kv_data = json.load(f)
        
        # Find tables in KV store
        table_kv_entries = {k: v for k, v in kv_data.items() if "table" in k.lower()}
        print(f"\nTable entities in KV store: {len(table_kv_entries)}")
        
        # Check descriptions
        tables_with_desc_context = 0
        for name, entity in table_kv_entries.items():
            desc = entity.get("description", "").lower()
            if any(kw in desc for kw in context_keywords):
                tables_with_desc_context += 1
        
        print(f"Tables with context in description: {tables_with_desc_context}/{len(table_kv_entries)}")
        
        # Show sample with context
        print("\nSample table with context in description:")
        for name, entity in table_kv_entries.items():
            desc = entity.get("description", "")
            if any(kw in desc.lower() for kw in context_keywords):
                print(f"\n  Entity: {name}")
                print(f"  Description: {desc[:300]}...")
                break

if __name__ == "__main__":
    main()
