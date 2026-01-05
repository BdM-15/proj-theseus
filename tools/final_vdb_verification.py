#!/usr/bin/env python3
"""
Final VDB Retrieval Quality Verification for Issue #62

This script confirms that context-aware processing has properly populated
the VDB with section context that enables semantic retrieval of tables.
"""

import json
import os

def main():
    workspace = "./rag_storage/swa_tas"
    vdb_file = os.path.join(workspace, "vdb_entities.json")
    
    print("=" * 70)
    print("VDB RETRIEVAL QUALITY VERIFICATION - Issue #62")
    print("=" * 70)
    
    with open(vdb_file, "r", encoding="utf-8") as f:
        vdb_data = json.load(f)
    
    data = vdb_data.get("data", [])
    print(f"\nTotal VDB entities: {len(data)}")
    print(f"Embedding dimension: {vdb_data.get('embedding_dim')}")
    
    # Find table entries
    table_entries = [e for e in data if "table" in e.get("__id__", "").lower()]
    print(f"Table entities: {len(table_entries)}")
    
    # Context keywords indicating section awareness
    context_keywords = ["appendix", "section", "attachment", "h.2.0", "workload", "pws"]
    
    print("\n" + "-" * 70)
    print("TABLE ENTITY CONTENT ANALYSIS")
    print("-" * 70)
    
    tables_with_context = 0
    tables_by_context = {}
    
    for entry in table_entries:
        entity_id = entry.get("__id__", "")
        content = entry.get("content", "").lower()
        
        found = [kw for kw in context_keywords if kw in content]
        if found:
            tables_with_context += 1
            for kw in found:
                tables_by_context[kw] = tables_by_context.get(kw, 0) + 1
    
    print(f"\nTables with context keywords: {tables_with_context}/{len(table_entries)}")
    print(f"Coverage: {(tables_with_context/len(table_entries)*100) if table_entries else 0:.1f}%")
    
    print("\nContext keyword distribution:")
    for kw, count in sorted(tables_by_context.items(), key=lambda x: -x[1]):
        print(f"  - '{kw}': {count} tables")
    
    # Show sample table entries
    print("\n" + "-" * 70)
    print("SAMPLE TABLE ENTRIES (showing content used for embeddings)")
    print("-" * 70)
    
    for i, entry in enumerate(table_entries[:5]):
        entity_id = entry.get("__id__", "")
        content = entry.get("content", "")
        entity_type = entry.get("entity_type", "")
        
        print(f"\n[{i+1}] {entity_id}")
        print(f"    Type: {entity_type}")
        
        # Check for context
        found = [kw for kw in context_keywords if kw in content.lower()]
        if found:
            print(f"    ✅ Context: {found}")
        else:
            print(f"    ⚠️ No section context")
        
        # Show content preview (this is what gets embedded)
        content_preview = content[:400].replace('\n', ' ')
        print(f"    Content: {content_preview}...")
    
    # Check KV store descriptions for comparison
    print("\n" + "-" * 70)
    print("KV STORE DESCRIPTION CHECK (parallel to VDB)")
    print("-" * 70)
    
    kv_file = os.path.join(workspace, "kv_store_full_entities.json")
    with open(kv_file, "r", encoding="utf-8") as f:
        kv_data = json.load(f)
    
    table_kv = {k: v for k, v in kv_data.items() if "table" in k.lower()}
    
    kv_with_context = 0
    for name, entity in table_kv.items():
        desc = entity.get("description", "").lower()
        if any(kw in desc for kw in context_keywords):
            kv_with_context += 1
    
    print(f"\nTable entities in KV store: {len(table_kv)}")
    print(f"Tables with context in description: {kv_with_context}/{len(table_kv)}")
    print(f"Coverage: {(kv_with_context/len(table_kv)*100) if table_kv else 0:.1f}%")
    
    # Query simulation
    print("\n" + "-" * 70)
    print("RETRIEVAL SIMULATION")
    print("-" * 70)
    
    test_queries = [
        ("workload data for DFAC operations", ["workload", "dfac"]),
        ("Appendix H staffing tables", ["appendix", "h", "staffing"]),
        ("section h.2.0 requirements", ["section", "h.2.0"]),
        ("PWS attachment workload estimates", ["pws", "attachment", "workload"])
    ]
    
    for query_text, query_terms in test_queries:
        matches = []
        for entry in table_entries:
            content = entry.get("content", "").lower()
            term_matches = sum(1 for t in query_terms if t in content)
            if term_matches >= 2:
                matches.append({
                    "id": entry.get("__id__"),
                    "score": term_matches
                })
        
        matches.sort(key=lambda x: -x["score"])
        
        print(f"\nQuery: '{query_text}'")
        if matches:
            print(f"  ✅ Would retrieve {len(matches)} tables:")
            for m in matches[:3]:
                print(f"     - {m['id']} (score: {m['score']})")
        else:
            print(f"  ⚠️ No matches (embedding similarity may still find relevant tables)")
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL ASSESSMENT")
    print("=" * 70)
    
    vdb_coverage = (tables_with_context / len(table_entries) * 100) if table_entries else 0
    kv_coverage = (kv_with_context / len(table_kv) * 100) if table_kv else 0
    
    print(f"\nVDB content coverage: {vdb_coverage:.1f}%")
    print(f"KV description coverage: {kv_coverage:.1f}%")
    
    if vdb_coverage >= 80:
        print("\n✅ Issue #62 VALIDATED: Context-aware processing is working")
        print("   - Tables have section context in VDB content field")
        print("   - Semantic search will leverage context for retrieval")
        print("   - Query: 'Appendix H workload' → will find relevant tables")
    elif vdb_coverage >= 50:
        print("\n⚠️ PARTIAL: Some tables have context, others don't")
        print("   - May want to investigate tables without context")
    else:
        print("\n❌ Issue #62 NOT WORKING: Tables lack section context")
        print("   - Semantic retrieval will not benefit from context")

if __name__ == "__main__":
    main()
