#!/usr/bin/env python
"""
Trace the EXACT query→retrieval path for workload queries.

This investigates:
1. What keywords are extracted from "workload" queries
2. What entity "content" fields actually contain (this is what's embedded!)
3. Whether table entities have searchable content
4. The actual VDB query→match process
"""

import json
import asyncio
from pathlib import Path


def analyze_entity_content_for_search():
    """Examine what's actually embedded and searchable in entities."""
    
    vdb_path = Path("rag_storage/swa_tas/vdb_entities.json")
    
    with open(vdb_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    entities = vdb_data.get("data", [])
    
    print("="*80)
    print("ENTITY CONTENT ANALYSIS - What Gets Embedded for Search")
    print("="*80)
    
    # Find table entities
    table_entities = []
    workload_entities = []
    aircraft_entities = []
    
    for entity in entities:
        entity_name = entity.get("entity_name", "")
        content = entity.get("content", "")  # THIS is what gets embedded!
        
        name_lower = entity_name.lower()
        content_lower = content.lower()
        
        if "table" in name_lower:
            table_entities.append(entity)
        
        if any(term in content_lower for term in ["workload", "aircraft", "sorties", "c-17", "c-130", "visits"]):
            workload_entities.append(entity)
        
        if any(term in content_lower for term in ["c-17", "c-130", "kc-135", "aircraft"]):
            aircraft_entities.append(entity)
    
    print(f"\nTotal entities: {len(entities)}")
    print(f"Table entities (by name): {len(table_entities)}")
    print(f"Workload-related (by content): {len(workload_entities)}")
    print(f"Aircraft-related (by content): {len(aircraft_entities)}")
    
    # Show table entity content samples
    print("\n" + "="*80)
    print("TABLE ENTITY CONTENT SAMPLES (what's embedded for search)")
    print("="*80)
    
    for i, entity in enumerate(table_entities[:5]):
        entity_name = entity.get("entity_name", "")
        content = entity.get("content", "")
        
        print(f"\n[{i+1}] Entity: {entity_name}")
        print(f"    Content length: {len(content)} chars")
        print(f"    Content preview (first 500 chars):")
        print(f"    {content[:500]}")
        print("-"*60)
    
    # Critical: Find the ADAB workload table
    print("\n" + "="*80)
    print("SEARCHING FOR ADAB/WORKLOAD SPECIFIC ENTITIES")
    print("="*80)
    
    adab_matches = []
    for entity in entities:
        content = entity.get("content", "")
        name = entity.get("entity_name", "")
        
        # Check for ADAB workload indicators
        if any(term in content.lower() for term in ["al jaber", "adab", "760", "271", "224"]):
            adab_matches.append(entity)
    
    if adab_matches:
        print(f"\nFound {len(adab_matches)} ADAB-related entities:")
        for entity in adab_matches:
            name = entity.get("entity_name", "")
            content = entity.get("content", "")
            print(f"\n  Entity: {name}")
            print(f"  Content ({len(content)} chars):")
            # Show more content for debugging
            print(f"  {content[:1000]}...")
    else:
        print("\n⚠️ NO ENTITIES FOUND with ADAB workload data in their content!")
        print("   This explains why queries can't find workload data.")
    
    # Check what terms ARE in entity content
    print("\n" + "="*80)
    print("TERM FREQUENCY IN ENTITY CONTENT")
    print("="*80)
    
    search_terms = [
        "workload", "aircraft", "sorties", "visits", "c-17", "c-130",
        "appendix h", "al jaber", "adab", "table", "schedule",
        "760", "271", "224", "annual"
    ]
    
    for term in search_terms:
        count = sum(1 for e in entities if term.lower() in e.get("content", "").lower())
        print(f"  '{term}': {count} entities")
    
    return table_entities, workload_entities


def check_entity_content_vs_description():
    """Compare what's in 'content' vs what's in KG 'description'."""
    
    # Load KG data
    graphml_path = Path("rag_storage/swa_tas/graph_chunk_entity_relation.graphml")
    vdb_path = Path("rag_storage/swa_tas/vdb_entities.json")
    
    with open(vdb_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    entities = vdb_data.get("data", [])
    
    print("\n" + "="*80)
    print("VDB CONTENT vs KG DESCRIPTION - Are they the same?")
    print("="*80)
    
    # The VDB 'content' field format is typically: "entity_name\ndescription"
    # Let's verify this
    
    for entity in entities[:5]:
        name = entity.get("entity_name", "")
        content = entity.get("content", "")
        
        # Check if content starts with entity name
        expected_prefix = name + "\n"
        
        print(f"\nEntity: {name}")
        print(f"  Content starts with name: {content.startswith(expected_prefix)}")
        print(f"  Content structure: '{content[:100]}...'")


def analyze_keyword_search_gap():
    """Understand why keyword searches miss table entities."""
    
    print("\n" + "="*80)
    print("KEYWORD → ENTITY MATCH ANALYSIS")
    print("="*80)
    
    # Load entities
    vdb_path = Path("rag_storage/swa_tas/vdb_entities.json")
    with open(vdb_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    entities = vdb_data.get("data", [])
    
    # Simulate what keywords would be extracted for workload queries
    simulated_keywords = {
        "What's the scope of work at ADAB?": [
            "scope of work", "ADAB", "Al Dhafra", "performance work statement",
            "requirements", "tasks", "services"
        ],
        "What workload is expected?": [
            "workload", "volume", "quantities", "schedule", "frequency",
            "aircraft", "sorties", "maintenance"
        ],
        "What are the aircraft maintenance requirements?": [
            "aircraft maintenance", "C-17", "C-130", "maintenance tasks",
            "scheduled maintenance", "unscheduled maintenance"
        ]
    }
    
    for query, keywords in simulated_keywords.items():
        print(f"\nQuery: '{query}'")
        print(f"Expected keywords: {keywords}")
        
        # Count how many entities match ANY of these keywords
        matching_entities = []
        for entity in entities:
            content = entity.get("content", "").lower()
            name = entity.get("entity_name", "")
            
            for kw in keywords:
                if kw.lower() in content:
                    matching_entities.append((name, kw))
                    break
        
        print(f"  Entities with keyword match: {len(matching_entities)}")
        if matching_entities[:5]:
            for name, kw in matching_entities[:5]:
                print(f"    - {name} (matched: '{kw}')")


if __name__ == "__main__":
    table_entities, workload_entities = analyze_entity_content_for_search()
    check_entity_content_vs_description()
    analyze_keyword_search_gap()
