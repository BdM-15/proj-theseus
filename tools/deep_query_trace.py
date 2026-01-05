#!/usr/bin/env python3
"""
Deep Query Trace - Capture server's full query path with keyword visibility.

Makes queries to the running server and inspects the returned context
to understand why certain entities are/aren't retrieved.
"""

import requests
import json
import re
from typing import Optional

SERVER_URL = "http://localhost:9621"


def query_with_trace(query: str, mode: str = "hybrid") -> dict:
    """Query server and get full response with context analysis."""
    
    resp = requests.post(
        f"{SERVER_URL}/query",
        json={
            "query": query,
            "mode": mode,
            "only_need_context": False,  # We want full response
        },
        timeout=120
    )
    
    if resp.status_code != 200:
        return {"error": resp.text}
    
    data = resp.json()
    return data


def query_context_only(query: str, mode: str = "hybrid") -> str:
    """Get just the context (what entities were retrieved)."""
    
    resp = requests.post(
        f"{SERVER_URL}/query",
        json={
            "query": query,
            "mode": mode,
            "only_need_context": True,
        },
        timeout=120
    )
    
    if resp.status_code != 200:
        return f"ERROR: {resp.text}"
    
    return resp.json().get("response", "")


def analyze_context(context: str, search_terms: list[str]) -> dict:
    """Analyze what's present in the context."""
    analysis = {}
    
    for term in search_terms:
        analysis[term] = {
            "present": term.lower() in context.lower(),
            "count": context.lower().count(term.lower())
        }
    
    # Find entity names in context (they appear as ### headers)
    entity_pattern = r'###\s*([^\n]+)'
    entities = re.findall(entity_pattern, context)
    analysis["_entities_found"] = entities[:20]  # First 20
    
    # Check for table content
    analysis["_has_table_data"] = "table_p" in context.lower() or "Table H.2.0" in context
    
    return analysis


def main():
    """Test multiple query variants and compare context retrieval."""
    
    print("=" * 80)
    print("QUERY CONTEXT TRACE - Understanding Entity Retrieval")
    print("=" * 80)
    
    # Key terms we're looking for
    SEARCH_TERMS = [
        "760",           # Grand total
        "224",           # C-17 total  
        "271",           # C-130 total
        "table_p53",     # Main workload table entity
        "H.2.0",         # Workload data section
        "aircraft visits",
        "monthly workload",
        "Al Dhafra",
        "grand total",
    ]
    
    # Test queries that should all retrieve workload data but don't consistently
    TEST_QUERIES = [
        # These WORKED in previous tests
        ("What's the scope of work at ADAB?", "hybrid"),
        
        # These FAILED in previous tests
        ("What are the workload drivers at Al Dhafra?", "hybrid"),
        ("How many aircraft visits are expected monthly at ADAB?", "hybrid"),
        
        # More specific queries
        ("What is the H.2.0 estimated monthly workload data?", "hybrid"),
        ("What are the aircraft quantities at Al Dhafra Air Base?", "hybrid"),
        ("What is the grand total of aircraft visits at ADAB?", "hybrid"),
        
        # Try local mode (entity-focused)
        ("What are the workload drivers at Al Dhafra?", "local"),
        ("What is the aircraft visit schedule for ADAB?", "local"),
    ]
    
    results = []
    
    for query, mode in TEST_QUERIES:
        print(f"\n{'='*80}")
        print(f"QUERY: \"{query}\"")
        print(f"MODE: {mode}")
        print("=" * 80)
        
        # Get context only
        context = query_context_only(query, mode)
        context_len = len(context)
        
        print(f"\nContext length: {context_len:,} chars")
        
        # Analyze what's in context
        analysis = analyze_context(context, SEARCH_TERMS)
        
        print("\nTerm Presence in Context:")
        for term in SEARCH_TERMS:
            info = analysis[term]
            status = "✅" if info["present"] else "❌"
            count = info["count"]
            print(f"  {status} '{term}': {count} occurrences")
        
        print(f"\nTable data present: {'✅' if analysis['_has_table_data'] else '❌'}")
        print(f"\nFirst 10 entities found:")
        for i, ent in enumerate(analysis["_entities_found"][:10], 1):
            print(f"  {i}. {ent[:60]}...")
        
        # Store result
        results.append({
            "query": query,
            "mode": mode,
            "context_length": context_len,
            "has_760": analysis["760"]["present"],
            "has_table_p53": analysis["table_p53"]["present"],
            "has_H2.0": analysis["H.2.0"]["present"],
            "entity_count": len(analysis["_entities_found"])
        })
    
    # Summary comparison
    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)
    print(f"\n{'Query':<60} {'Mode':<8} {'760':<5} {'table':<6} {'H.2.0':<6}")
    print("-" * 85)
    
    for r in results:
        q = r["query"][:57] + "..." if len(r["query"]) > 57 else r["query"]
        print(f"{q:<60} {r['mode']:<8} {'✅' if r['has_760'] else '❌':<5} "
              f"{'✅' if r['has_table_p53'] else '❌':<6} {'✅' if r['has_H2.0'] else '❌':<6}")
    
    print("\n" + "=" * 80)
    print("DIAGNOSIS")
    print("=" * 80)
    
    # Check pattern
    working = [r for r in results if r["has_760"]]
    failing = [r for r in results if not r["has_760"]]
    
    print(f"\nQueries that RETRIEVE 760: {len(working)}/{len(results)}")
    for r in working:
        print(f"  ✅ \"{r['query']}\" ({r['mode']})")
    
    print(f"\nQueries that MISS 760: {len(failing)}/{len(results)}")
    for r in failing:
        print(f"  ❌ \"{r['query']}\" ({r['mode']})")
    
    if working and failing:
        print("\n🔍 HYPOTHESIS: Keyword extraction produces different search terms")
        print("    that don't match the '760' entities' embeddings.")
        print("\n📋 NEXT STEP: Check govcon_prompt.py keywords_extraction_examples")
        print("    to ensure workload queries generate entity-matching keywords.")


if __name__ == "__main__":
    main()
