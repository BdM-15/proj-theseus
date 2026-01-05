#!/usr/bin/env python
"""
Trace the full query→retrieval path to diagnose why workload data isn't returned.

This script:
1. Sends a query to the running LightRAG server
2. Captures the full response including retrieved context
3. Analyzes what entities/chunks were retrieved vs what should have been
"""

import asyncio
import json
import httpx
from pathlib import Path

SERVER_URL = "http://localhost:9621"
WORKSPACE = "swa_tas"

# Test queries - the problematic "workload" query
TEST_QUERIES = [
    "What's the scope of work at ADAB?",
    "What are the workload drivers at Al Dhafra?",
    "How many aircraft visits are expected monthly at ADAB?",
]


async def query_server(query: str, mode: str = "hybrid") -> dict:
    """Send query to LightRAG server and get full response."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{SERVER_URL}/query",
                json={
                    "query": query,
                    "mode": mode,
                    "only_need_context": False,  # Get full response
                    "stream": False,
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


async def query_context_only(query: str, mode: str = "hybrid") -> dict:
    """Get just the retrieved context without LLM response."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(
                f"{SERVER_URL}/query",
                json={
                    "query": query,
                    "mode": mode,
                    "only_need_context": True,
                    "stream": False,
                },
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def analyze_context(context_str: str) -> dict:
    """Analyze retrieved context for workload-related content."""
    analysis = {
        "total_length": len(context_str),
        "contains_workload": "workload" in context_str.lower(),
        "contains_760": "760" in context_str,
        "contains_aircraft": "aircraft" in context_str.lower(),
        "contains_table_p53": "table_p53" in context_str.lower(),
        "contains_h20": "h.2.0" in context_str.lower() or "h2.0" in context_str.lower(),
        "contains_appendix_h": "appendix h" in context_str.lower(),
        "entity_mentions": [],
        "relationship_mentions": [],
    }
    
    # Look for key workload entities
    workload_entities = [
        "table_p53", "table_p54", "H.2.0", "workload", "aircraft visits",
        "C-17", "C-130", "760", "271", "224", "monthly workload"
    ]
    for entity in workload_entities:
        if entity.lower() in context_str.lower():
            analysis["entity_mentions"].append(entity)
    
    return analysis


async def main():
    print("="*80)
    print("QUERY PATH TRACE DIAGNOSTIC")
    print("="*80)
    
    for query in TEST_QUERIES:
        print(f"\n{'='*80}")
        print(f"QUERY: {query}")
        print("="*80)
        
        # Get context only first (faster, shows retrieval)
        print("\n--- RETRIEVING CONTEXT (only_need_context=True) ---")
        context_result = await query_context_only(query, mode="hybrid")
        
        if "error" in context_result:
            print(f"ERROR: {context_result['error']}")
            continue
        
        # The context result should be the raw context string
        if isinstance(context_result, dict) and "response" in context_result:
            context_str = context_result["response"]
        elif isinstance(context_result, str):
            context_str = context_result
        else:
            context_str = str(context_result)
        
        print(f"\nContext length: {len(context_str)} chars")
        
        # Analyze what was retrieved
        analysis = analyze_context(context_str)
        print(f"\n--- CONTEXT ANALYSIS ---")
        print(f"Contains 'workload': {analysis['contains_workload']}")
        print(f"Contains '760' (total aircraft): {analysis['contains_760']}")
        print(f"Contains 'aircraft': {analysis['contains_aircraft']}")
        print(f"Contains 'table_p53': {analysis['contains_table_p53']}")
        print(f"Contains 'H.2.0': {analysis['contains_h20']}")
        print(f"Contains 'Appendix H': {analysis['contains_appendix_h']}")
        print(f"Workload entity mentions: {analysis['entity_mentions']}")
        
        # Show snippet of context
        print(f"\n--- CONTEXT PREVIEW (first 2000 chars) ---")
        print(context_str[:2000])
        print("..." if len(context_str) > 2000 else "")
        
        # Now get full response
        print(f"\n--- FULL LLM RESPONSE ---")
        full_result = await query_server(query, mode="hybrid")
        
        if "error" in full_result:
            print(f"ERROR: {full_result['error']}")
        elif isinstance(full_result, dict) and "response" in full_result:
            response_text = full_result["response"]
            print(f"Response length: {len(response_text)} chars")
            
            # Check if workload data made it to final response
            response_analysis = analyze_context(response_text)
            print(f"\n--- RESPONSE ANALYSIS ---")
            print(f"Contains 'workload': {response_analysis['contains_workload']}")
            print(f"Contains '760': {response_analysis['contains_760']}")
            print(f"Contains 'aircraft': {response_analysis['contains_aircraft']}")
            print(f"Workload mentions: {response_analysis['entity_mentions']}")
            
            print(f"\n--- RESPONSE TEXT ---")
            print(response_text[:3000])
            print("..." if len(response_text) > 3000 else "")
        else:
            print(f"Unexpected response format: {type(full_result)}")
            print(str(full_result)[:1000])
        
        print("\n" + "-"*80)


if __name__ == "__main__":
    asyncio.run(main())
