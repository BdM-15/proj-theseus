#!/usr/bin/env python3
"""
Investigate KG BUILD quality - are entities properly connected?

Key questions:
1. Is table_p53 connected to Appendix H parent?
2. Are summary entities (C-17 visits, C-130 visits) connected to table_p53?
3. Does graph traversal work as intended?
4. Are relationships enabling or blocking retrieval?
"""

import json
from pathlib import Path
from collections import defaultdict

def load_data(workspace: str = "swa_tas"):
    """Load entities and relationships."""
    base = Path(f"rag_storage/{workspace}")
    
    with open(base / "vdb_entities.json", 'r', encoding='utf-8') as f:
        entities = json.load(f).get('data', [])
    
    with open(base / "vdb_relationships.json", 'r', encoding='utf-8') as f:
        relationships = json.load(f).get('data', [])
    
    return entities, relationships

def analyze_table_p53_connections(entities, relationships):
    """Check how table_p53 is connected in the KG."""
    
    print("=" * 70)
    print("TABLE_P53 CONNECTION ANALYSIS")
    print("=" * 70)
    
    # Find table_p53
    table_p53 = None
    for e in entities:
        if 'table_p53' in e.get('entity_name', '').lower():
            table_p53 = e
            break
    
    if not table_p53:
        print("❌ table_p53 NOT FOUND in entities!")
        return
    
    print(f"\n✅ Found: {table_p53.get('entity_name')}")
    print(f"   Type: {table_p53.get('entity_type')}")
    print(f"   Content: {len(table_p53.get('content', ''))} chars")
    
    # Find all relationships involving table_p53
    table_name = table_p53.get('entity_name', '').lower()
    
    incoming = []  # Relationships TO table_p53
    outgoing = []  # Relationships FROM table_p53
    
    for r in relationships:
        src = r.get('src_id', '').lower()
        tgt = r.get('tgt_id', '').lower()
        
        if 'table_p53' in tgt or 'p53' in tgt:
            incoming.append(r)
        if 'table_p53' in src or 'p53' in src:
            outgoing.append(r)
    
    print(f"\n--- INCOMING RELATIONSHIPS (→ table_p53): {len(incoming)} ---")
    for r in incoming:
        rel_type = r.get('keywords', r.get('description', 'unknown'))[:40]
        print(f"   {r.get('src_id', 'N/A')[:40]} --[{rel_type}]--> table_p53")
    
    print(f"\n--- OUTGOING RELATIONSHIPS (table_p53 →): {len(outgoing)} ---")
    for r in outgoing:
        rel_type = r.get('keywords', r.get('description', 'unknown'))[:40]
        print(f"   table_p53 --[{rel_type}]--> {r.get('tgt_id', 'N/A')[:40]}")
    
    if len(incoming) == 0 and len(outgoing) == 0:
        print("\n⚠️  WARNING: table_p53 is an ORPHAN - no relationships!")
        print("   This means graph traversal will NOT find it from other entities!")
    
    return len(incoming) + len(outgoing)

def analyze_appendix_h_structure(entities, relationships):
    """Check Appendix H hierarchy - is it properly built?"""
    
    print("\n" + "=" * 70)
    print("APPENDIX H HIERARCHY ANALYSIS")
    print("=" * 70)
    
    # Find all Appendix H related entities
    appendix_h_entities = []
    for e in entities:
        name = e.get('entity_name', '').lower()
        if 'appendix h' in name or 'h.1' in name or 'h.2' in name or 'adab' in name:
            appendix_h_entities.append(e)
    
    print(f"\nAppendix H related entities: {len(appendix_h_entities)}")
    
    # Group by type
    by_type = defaultdict(list)
    for e in appendix_h_entities:
        by_type[e.get('entity_type', 'unknown')].append(e)
    
    print("\nBy entity type:")
    for etype, elist in sorted(by_type.items()):
        print(f"  {etype}: {len(elist)}")
        for e in elist[:3]:
            print(f"    - {e.get('entity_name', 'N/A')[:50]}")
    
    # Check CHILD_OF relationships within Appendix H
    print("\n--- CHILD_OF RELATIONSHIPS in Appendix H ---")
    
    child_of_rels = []
    for r in relationships:
        kw = r.get('keywords', '').lower()
        desc = r.get('description', '').lower()
        src = r.get('src_id', '').lower()
        tgt = r.get('tgt_id', '').lower()
        
        # Check if CHILD_OF type
        is_child_of = 'child_of' in kw or 'child of' in desc or 'contains' in kw
        
        # Check if involves Appendix H entities
        involves_h = any(term in src or term in tgt 
                        for term in ['appendix h', 'h.1', 'h.2', 'adab', 'table_p53'])
        
        if is_child_of and involves_h:
            child_of_rels.append(r)
    
    print(f"\nCHILD_OF relationships found: {len(child_of_rels)}")
    for r in child_of_rels:
        print(f"   {r.get('src_id', 'N/A')[:35]} --[CHILD_OF]--> {r.get('tgt_id', 'N/A')[:35]}")
    
    if len(child_of_rels) == 0:
        print("\n⚠️  WARNING: No CHILD_OF relationships in Appendix H!")
        print("   This means the hierarchy is FLAT - no parent-child structure!")

def analyze_summary_entity_connections(entities, relationships):
    """Check if summary entities are connected to source data."""
    
    print("\n" + "=" * 70)
    print("SUMMARY ENTITY CONNECTION ANALYSIS")
    print("=" * 70)
    
    # Find summary entities we saw in diagnostic
    summary_names = [
        'h.2.0 al dhafra c-17',
        'h.2.0 al dhafra c-130', 
        'h.2.0 al dhafra aircraft annual',
        'h.2.0 estimated monthly workload'
    ]
    
    for search_name in summary_names:
        print(f"\n--- Searching: '{search_name}' ---")
        
        found_entity = None
        for e in entities:
            if search_name in e.get('entity_name', '').lower():
                found_entity = e
                break
        
        if not found_entity:
            print("   ❌ Entity not found")
            continue
        
        entity_name = found_entity.get('entity_name', '')
        print(f"   ✅ Found: {entity_name}")
        
        # Find relationships
        incoming = []
        outgoing = []
        
        for r in relationships:
            src = r.get('src_id', '').lower()
            tgt = r.get('tgt_id', '').lower()
            name_lower = entity_name.lower()
            
            if name_lower in tgt or tgt in name_lower:
                incoming.append(r)
            if name_lower in src or src in name_lower:
                outgoing.append(r)
        
        print(f"   Incoming: {len(incoming)}, Outgoing: {len(outgoing)}")
        
        # Check if connected to table_p53
        connected_to_table = False
        for r in incoming + outgoing:
            if 'table_p53' in r.get('src_id', '').lower() or 'table_p53' in r.get('tgt_id', '').lower():
                connected_to_table = True
                print(f"   ✅ Connected to table_p53: {r.get('keywords', 'N/A')[:30]}")
        
        if not connected_to_table:
            print(f"   ⚠️  NOT connected to table_p53!")

def analyze_chunk_associations(workspace: str = "swa_tas"):
    """Check if entities are associated with the right chunks."""
    
    print("\n" + "=" * 70)
    print("CHUNK-ENTITY ASSOCIATION ANALYSIS")
    print("=" * 70)
    
    # Load chunks
    chunks_path = Path(f"rag_storage/{workspace}/vdb_chunks.json")
    if not chunks_path.exists():
        print("❌ Chunks VDB not found")
        return
    
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
    
    chunks = chunks_data.get('data', [])
    print(f"\nTotal chunks: {len(chunks)}")
    
    # Find workload table chunks
    workload_chunks = []
    for c in chunks:
        chunk_id = c.get('id', c[0] if isinstance(c, list) else '')
        content = c.get('content', c[1] if isinstance(c, list) and len(c) > 1 else '')
        
        if isinstance(content, str):
            if any(term in content.lower() for term in ['h.2.0', 'workload data', 'aircraft', 'c-17', 'c-130']):
                workload_chunks.append({
                    'id': chunk_id,
                    'content_preview': content[:200] if isinstance(content, str) else str(content)[:200]
                })
    
    print(f"Workload-related chunks: {len(workload_chunks)}")
    for c in workload_chunks[:5]:
        print(f"\n   Chunk: {c['id'][:50] if isinstance(c['id'], str) else c['id']}")
        print(f"   Preview: {c['content_preview'][:100]}...")

def main():
    print("=" * 70)
    print("KG BUILD QUALITY INVESTIGATION")
    print("Is the source of truth properly constructed?")
    print("=" * 70)
    
    entities, relationships = load_data()
    
    print(f"\nTotal entities: {len(entities)}")
    print(f"Total relationships: {len(relationships)}")
    
    # Check relationship types distribution
    print("\n--- RELATIONSHIP TYPE DISTRIBUTION ---")
    rel_types = defaultdict(int)
    for r in relationships:
        kw = r.get('keywords', 'unknown')
        # Extract first keyword as type
        rel_type = kw.split(',')[0].strip() if ',' in kw else kw
        rel_types[rel_type[:30]] += 1
    
    for rel_type, count in sorted(rel_types.items(), key=lambda x: -x[1])[:15]:
        print(f"   {rel_type}: {count}")
    
    # Run analyses
    table_connections = analyze_table_p53_connections(entities, relationships)
    analyze_appendix_h_structure(entities, relationships)
    analyze_summary_entity_connections(entities, relationships)
    analyze_chunk_associations()
    
    # Summary
    print("\n" + "=" * 70)
    print("DIAGNOSIS SUMMARY")
    print("=" * 70)
    
    if table_connections == 0:
        print("""
⚠️  EXTRACTION/BUILD ISSUE DETECTED:

table_p53 is an ORPHAN ENTITY - it has no relationships!

This means:
1. Graph traversal from "Appendix H" will NOT reach table_p53
2. Query must rely purely on VDB semantic similarity
3. With 105+ competing "workload" entities, table_p53 may not rank high enough
4. The KG structure is not supporting retrieval as intended

ROOT CAUSE: The extraction process created the entity but did NOT create
relationships connecting it to parent sections or related entities.

SOLUTION OPTIONS:
A) Re-run post-processing Algorithm 7 (CHILD_OF inference) specifically for tables
B) Manually verify/add relationships: Appendix H -> table_p53
C) Ensure RAGAnything context-aware processing creates proper CHILD_OF relationships
""")
    else:
        print(f"""
✅ table_p53 has {table_connections} relationships.

If retrieval is still inconsistent, the issue is likely:
1. Retrieval parameters (top_k, token budgets)
2. Semantic similarity ranking
3. Relationship traversal depth
""")

if __name__ == "__main__":
    main()
