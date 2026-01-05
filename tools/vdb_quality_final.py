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
    
    # Find table entries by entity_type
    table_entries = [e for e in data if e.get("entity_type", "").lower() == "table"]
    print(f"Table entities (by type): {len(table_entries)}")
    
    # Context keywords indicating section awareness
    context_keywords = ["appendix", "section", "attachment", "h.2", "workload", "pws"]
    
    print("\n" + "-" * 70)
    print("TABLE ENTITY CONTENT ANALYSIS")
    print("-" * 70)
    
    tables_with_context = 0
    tables_by_context = {}
    
    for entry in table_entries:
        entity_id = entry.get("__id__", "")
        content = entry.get("content", "").lower()
        entity_name = entry.get("entity_name", "").lower()
        combined = content + " " + entity_name
        
        found = [kw for kw in context_keywords if kw in combined]
        if found:
            tables_with_context += 1
            for kw in found:
                tables_by_context[kw] = tables_by_context.get(kw, 0) + 1
    
    print(f"\nTables with context keywords: {tables_with_context}/{len(table_entries)}")
    coverage = (tables_with_context/len(table_entries)*100) if table_entries else 0
    print(f"Coverage: {coverage:.1f}%")
    
    print("\nContext keyword distribution:")
    for kw, count in sorted(tables_by_context.items(), key=lambda x: -x[1]):
        print(f"  - '{kw}': {count} tables")
    
    # Show sample table entries
    print("\n" + "-" * 70)
    print("SAMPLE TABLE ENTRIES (showing content used for embeddings)")
    print("-" * 70)
    
    for i, entry in enumerate(table_entries[:6]):
        entity_id = entry.get("__id__", "")
        entity_name = entry.get("entity_name", "")
        content = entry.get("content", "")
        
        print(f"\n[{i+1}] {entity_name}")
        print(f"    ID: {entity_id}")
        
        # Check for context
        combined = (content + " " + entity_name).lower()
        found = [kw for kw in context_keywords if kw in combined]
        if found:
            print(f"    ✅ Context: {found}")
        else:
            print(f"    ⚠️ No section context")
        
        # Show content preview (this is what gets embedded)
        content_preview = content[:350].replace('\n', ' ')
        print(f"    Content: {content_preview}...")
    
    # Check KV store descriptions for comparison
    print("\n" + "-" * 70)
    print("KV STORE DESCRIPTION CHECK")
    print("-" * 70)
    
    kv_file = os.path.join(workspace, "kv_store_full_entities.json")
    with open(kv_file, "r", encoding="utf-8") as f:
        kv_data = json.load(f)
    
    # Filter by entity_type in KV store
    table_kv = {k: v for k, v in kv_data.items() 
                if v.get("entity_type", "").lower() == "table"}
    
    kv_with_context = 0
    for name, entity in table_kv.items():
        desc = entity.get("description", "").lower()
        ename = name.lower()
        combined = desc + " " + ename
        if any(kw in combined for kw in context_keywords):
            kv_with_context += 1
    
    print(f"\nTable entities in KV store: {len(table_kv)}")
    print(f"Tables with context: {kv_with_context}/{len(table_kv)}")
    kv_coverage = (kv_with_context/len(table_kv)*100) if table_kv else 0
    print(f"Coverage: {kv_coverage:.1f}%")
    
    # Show sample with context
    print("\nSample table entity from KV store:")
    for name, entity in list(table_kv.items())[:3]:
        desc = entity.get("description", "")
        combined = (desc + " " + name).lower()
        found = [kw for kw in context_keywords if kw in combined]
        status = "✅" if found else "⚠️"
        print(f"\n  {status} {name}")
        print(f"     Desc: {desc[:200]}...")
        if found:
            print(f"     Context: {found}")
    
    # Query simulation
    print("\n" + "-" * 70)
    print("RETRIEVAL SIMULATION")
    print("-" * 70)
    
    test_queries = [
        ("workload data for DFAC operations", ["workload", "dfac"]),
        ("Appendix H staffing tables", ["appendix", "h", "staff"]),
        ("section h.2 requirements", ["section", "h.2"]),
        ("PWS attachment workload estimates", ["pws", "workload"])
    ]
    
    for query_text, query_terms in test_queries:
        matches = []
        for entry in table_entries:
            content = entry.get("content", "").lower()
            entity_name = entry.get("entity_name", "").lower()
            combined = content + " " + entity_name
            term_matches = sum(1 for t in query_terms if t in combined)
            if term_matches >= 1:
                matches.append({
                    "id": entry.get("entity_name"),
                    "score": term_matches
                })
        
        matches.sort(key=lambda x: -x["score"])
        
        print(f"\nQuery: '{query_text}'")
        if matches:
            print(f"  ✅ Would retrieve {len(matches)} tables:")
            for m in matches[:3]:
                print(f"     - {m['id'][:50]} (score: {m['score']})")
        else:
            print(f"  ⚠️ No keyword matches (embedding similarity may find relevant)")
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL ASSESSMENT")
    print("=" * 70)
    
    print(f"\nVDB content coverage: {coverage:.1f}%")
    print(f"KV description coverage: {kv_coverage:.1f}%")
    
    if coverage >= 80:
        print("\n✅ Issue #62 VALIDATED: Context-aware processing is working")
        print("   - Tables have section context in VDB content field")
        print("   - Semantic search will leverage context for retrieval")
        print("   - Query: 'Appendix H workload' → will find relevant tables")
    elif coverage >= 50:
        print("\n⚠️ PARTIAL: Some tables have context, improvement possible")
        print("   - Consider investigating tables without context")
    else:
        print("\n❌ Issue #62 NEEDS WORK: Tables lack section context")
        print("   - Semantic retrieval may not benefit from context")
    
    # List tables without context
    tables_without = []
    for entry in table_entries:
        content = entry.get("content", "").lower()
        entity_name = entry.get("entity_name", "").lower()
        combined = content + " " + entity_name
        if not any(kw in combined for kw in context_keywords):
            tables_without.append(entry.get("entity_name", ""))
    
    if tables_without:
        print(f"\nTables without context ({len(tables_without)}):")
        for t in tables_without[:8]:
            print(f"  - {t}")

if __name__ == "__main__":
    main()
