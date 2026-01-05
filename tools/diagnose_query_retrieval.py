#!/usr/bin/env python3
"""
Diagnose why different queries retrieve different entities.
Compare semantic similarity between query terms and entity content.

Usage: python tools/diagnose_query_retrieval.py
"""

import json
import os
from pathlib import Path

def load_entities(workspace: str = "swa_tas"):
    """Load entities from VDB."""
    vdb_path = Path(f"rag_storage/{workspace}/vdb_entities.json")
    with open(vdb_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('data', [])

def search_entities_by_keywords(entities: list, keywords: list[str]) -> dict:
    """Find entities containing specific keywords."""
    results = {}
    for kw in keywords:
        kw_lower = kw.lower()
        matches = []
        for e in entities:
            entity_name = e.get('entity_name', '').lower()
            content = e.get('content', '').lower()
            if kw_lower in entity_name or kw_lower in content:
                matches.append({
                    'name': e.get('entity_name', 'N/A'),
                    'type': e.get('entity_type', 'unknown'),
                    'content_length': len(e.get('content', '')),
                    'in_name': kw_lower in entity_name,
                    'in_content': kw_lower in content
                })
        results[kw] = matches
    return results

def analyze_table_p53(entities: list):
    """Specifically analyze table_p53 - the workload table."""
    for e in entities:
        name = e.get('entity_name', '')
        if 'table_p53' in name.lower() or 'p53' in name.lower():
            print("=" * 70)
            print(f"FOUND: {name}")
            print("=" * 70)
            print(f"Entity Type: {e.get('entity_type', 'N/A')}")
            print(f"Content Length: {len(e.get('content', ''))} chars")
            print("\nContent Preview (first 1000 chars):")
            print("-" * 50)
            print(e.get('content', '')[:1000])
            print("-" * 50)
            
            # Check for key terms that should aid retrieval
            content = e.get('content', '').lower()
            retrieval_terms = [
                'workload', 'driver', 'appendix h', 'adab', 'aircraft', 
                'c-130', 'c-17', 'monthly', 'quantity', 'frequency',
                'scope', 'estimate', 'labor', 'staffing', 'boe',
                'services', 'transient'
            ]
            print("\nRetrieval Term Presence:")
            for term in retrieval_terms:
                status = "✅" if term in content else "❌"
                print(f"  {status} {term}")
            return e
    return None

def main():
    print("=" * 70)
    print("QUERY RETRIEVAL DIAGNOSTIC")
    print("=" * 70)
    
    entities = load_entities()
    print(f"\nTotal entities loaded: {len(entities)}")
    
    # Query 1 keywords (successful retrieval)
    query1_keywords = ["scope", "work", "adab", "drives", "workload"]
    
    # Query 2 keywords (failed retrieval)
    query2_keywords = ["workload", "drivers", "appendix h", "frequencies", 
                       "quantities", "hours", "coverage", "boe", "labor"]
    
    print("\n" + "=" * 70)
    print("QUERY 1 KEYWORDS (Retrieved table_p53)")
    print("=" * 70)
    
    results1 = search_entities_by_keywords(entities, query1_keywords)
    for kw, matches in results1.items():
        print(f"\n'{kw}': {len(matches)} matching entities")
        for m in matches[:3]:
            loc = "name" if m['in_name'] else "content"
            print(f"  - {m['name'][:50]} [{m['type']}] ({m['content_length']} chars) [in {loc}]")
    
    print("\n" + "=" * 70)
    print("QUERY 2 KEYWORDS (Did NOT retrieve table_p53)")
    print("=" * 70)
    
    results2 = search_entities_by_keywords(entities, query2_keywords)
    for kw, matches in results2.items():
        print(f"\n'{kw}': {len(matches)} matching entities")
        for m in matches[:3]:
            loc = "name" if m['in_name'] else "content"
            print(f"  - {m['name'][:50]} [{m['type']}] ({m['content_length']} chars) [in {loc}]")
    
    print("\n" + "=" * 70)
    print("TABLE_P53 ANALYSIS")
    print("=" * 70)
    
    table_entity = analyze_table_p53(entities)
    
    if table_entity:
        content = table_entity.get('content', '').lower()
        
        # Check which query keywords are in table_p53
        print("\n" + "=" * 70)
        print("KEYWORD OVERLAP ANALYSIS")
        print("=" * 70)
        
        print("\nQuery 1 keywords in table_p53:")
        for kw in query1_keywords:
            status = "✅" if kw.lower() in content else "❌"
            print(f"  {status} {kw}")
        
        print("\nQuery 2 keywords in table_p53:")
        for kw in query2_keywords:
            status = "✅" if kw.lower() in content else "❌"
            print(f"  {status} {kw}")
    
    # Find H.2.0 entity specifically
    print("\n" + "=" * 70)
    print("H.2.0 WORKLOAD DATA ENTITY SEARCH")
    print("=" * 70)
    
    h2_entities = []
    for e in entities:
        name = e.get('entity_name', '')
        if 'h.2' in name.lower() or 'estimated monthly' in name.lower():
            h2_entities.append(e)
            print(f"\n{name}")
            print(f"  Type: {e.get('entity_type', 'N/A')}")
            print(f"  Content Length: {len(e.get('content', ''))} chars")
            print(f"  Preview: {e.get('content', '')[:200]}...")
    
    if not h2_entities:
        print("  No H.2.0 specific entity found!")

if __name__ == "__main__":
    main()
