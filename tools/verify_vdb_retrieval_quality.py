#!/usr/bin/env python3
"""
Verify VDB entry content ensures quality retrievals for user queries.

This script examines the actual content stored in VDB entries to confirm
that section context from Issue #62 context-aware processing is properly
embedded for retrieval.
"""

import json
import os

def main():
    workspace = "./rag_storage/swa_tas"
    vdb_file = os.path.join(workspace, "vdb_entities.json")
    
    print("=" * 70)
    print("VDB RETRIEVAL QUALITY VERIFICATION")
    print("=" * 70)
    
    with open(vdb_file, "r", encoding="utf-8") as f:
        vdb_data = json.load(f)
    
    # VDB data is a list - find table entries
    table_entries = []
    for entry in vdb_data:
        if isinstance(entry, dict):
            entity_name = entry.get("__id__", "")
            if "table" in entity_name.lower():
                table_entries.append(entry)
    
    print(f"\nFound {len(table_entries)} table entries in VDB\n")
    
    # Examine first 5 table entries in detail
    print("-" * 70)
    print("SAMPLE TABLE ENTRIES (showing fields used for retrieval)")
    print("-" * 70)
    
    context_keywords = ["appendix", "section", "attachment", "h.2.0", "workload", "pws"]
    
    tables_with_context_content = 0
    tables_with_context_desc = 0
    
    for i, entry in enumerate(table_entries[:10]):
        entity_id = entry.get("__id__", "unknown")
        
        # Get all fields except vector
        fields = {k: v for k, v in entry.items() if k != "__vector__"}
        
        print(f"\n[{i+1}] Entity: {entity_id}")
        print(f"    Fields available: {list(fields.keys())}")
        
        # Check content field (used for embeddings)
        content = entry.get("content", "")
        if content:
            content_preview = content[:300] + "..." if len(content) > 300 else content
            print(f"    Content preview: {content_preview}")
            
            # Check for context keywords
            content_lower = content.lower()
            found_context = [kw for kw in context_keywords if kw in content_lower]
            if found_context:
                tables_with_context_content += 1
                print(f"    ✅ Context in content: {found_context}")
            else:
                print(f"    ⚠️ No context keywords in content")
        
        # Check description field
        description = entry.get("description", "")
        if description:
            desc_preview = description[:200] + "..." if len(description) > 200 else description
            print(f"    Description: {desc_preview}")
            
            desc_lower = description.lower()
            found_context = [kw for kw in context_keywords if kw in desc_lower]
            if found_context:
                tables_with_context_desc += 1
                print(f"    ✅ Context in description: {found_context}")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    
    # Check ALL table entries for context
    all_tables_with_content_context = 0
    all_tables_with_desc_context = 0
    
    for entry in table_entries:
        content = entry.get("content", "").lower()
        description = entry.get("description", "").lower()
        
        if any(kw in content for kw in context_keywords):
            all_tables_with_content_context += 1
        if any(kw in description for kw in context_keywords):
            all_tables_with_desc_context += 1
    
    print(f"\nTotal table entries: {len(table_entries)}")
    print(f"Tables with context in 'content' field: {all_tables_with_content_context}/{len(table_entries)}")
    print(f"Tables with context in 'description' field: {all_tables_with_desc_context}/{len(table_entries)}")
    
    # Check embedding dimensions
    sample = table_entries[0] if table_entries else None
    if sample and "__vector__" in sample:
        vector = sample["__vector__"]
        print(f"\nEmbedding dimensions: {len(vector)}")
        print(f"Embedding type: {type(vector[0]).__name__}")
    
    # Final assessment
    print("\n" + "-" * 70)
    print("RETRIEVAL QUALITY ASSESSMENT")
    print("-" * 70)
    
    if all_tables_with_content_context >= len(table_entries) * 0.8:
        print("✅ HIGH: 80%+ of tables have context in content field")
        print("   → Semantic search will find tables by section context")
    elif all_tables_with_content_context >= len(table_entries) * 0.5:
        print("⚠️ MEDIUM: 50-80% of tables have context in content field")
        print("   → Most semantic searches will work, some may miss context")
    else:
        print("❌ LOW: <50% of tables have context in content field")
        print("   → Semantic search may not leverage section context effectively")
    
    # Test query simulation
    print("\n" + "-" * 70)
    print("QUERY SIMULATION")
    print("-" * 70)
    
    test_queries = [
        "workload data for Al Dhafra Air Base DFAC operations",
        "Appendix H tables with staffing estimates",
        "PWS Section H workload requirements"
    ]
    
    for query in test_queries:
        query_lower = query.lower()
        matching_tables = []
        
        for entry in table_entries:
            content = entry.get("content", "").lower()
            description = entry.get("description", "").lower()
            combined = content + " " + description
            
            # Simple keyword matching (simulates what embeddings would find)
            query_terms = query_lower.split()
            matches = sum(1 for term in query_terms if term in combined)
            
            if matches >= 2:  # At least 2 query terms match
                matching_tables.append({
                    "id": entry.get("__id__", ""),
                    "matches": matches
                })
        
        matching_tables.sort(key=lambda x: x["matches"], reverse=True)
        
        print(f"\nQuery: '{query}'")
        if matching_tables:
            print(f"  Would match {len(matching_tables)} tables:")
            for t in matching_tables[:3]:
                print(f"    - {t['id']} ({t['matches']} term matches)")
        else:
            print("  ⚠️ No tables match this query (may need better context)")
    
    print("\n" + "=" * 70)
    print("Issue #62 Context-Aware Processing Validation: COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
