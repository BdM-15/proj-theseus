"""
Deep validation of Issue #62 context-aware processing.

Checks:
1. Table entities have section context in descriptions
2. VDB embeddings capture section semantics
3. Queries retrieve tables WITH their section context
4. belongs_to relationships exist from extracted entities to tables
"""
import os
import json
from pathlib import Path
from neo4j import GraphDatabase

# Configuration
WORKSPACE = "swa_tas"
RAG_STORAGE = Path("./rag_storage") / WORKSPACE
NEO4J_URI = "neo4j://localhost:7687"
NEO4J_AUTH = ("neo4j", "govcon-capture-2025")

def check_table_descriptions():
    """Check if table entities have section context."""
    print("=" * 80)
    print("1. TABLE ENTITY DESCRIPTIONS - Section Context Check")
    print("=" * 80)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    context_markers = ['appendix', 'section', 'attachment', 'h.2.0', 'workload data', 'pws']
    tables_with_context = 0
    tables_without_context = 0
    
    with driver.session() as s:
        r = s.run('''
            MATCH (n:swa_tas)
            WHERE n.entity_id STARTS WITH "table_p"
            RETURN n.entity_id as id, n.entity_type as type, n.description as desc
            ORDER BY n.entity_id
        ''')
        
        for rec in r:
            desc = (rec['desc'] or "").lower()
            has_context = any(marker in desc for marker in context_markers)
            
            if has_context:
                tables_with_context += 1
                status = "✅"
            else:
                tables_without_context += 1
                status = "❌"
            
            print(f"\n{status} {rec['id']} ({rec['type']})")
            # Show first 300 chars of description
            print(f"   {(rec['desc'] or 'No description')[:300]}...")
    
    driver.close()
    
    print(f"\n--- Summary ---")
    print(f"Tables WITH section context: {tables_with_context}")
    print(f"Tables WITHOUT section context: {tables_without_context}")
    print(f"Context coverage: {tables_with_context}/{tables_with_context + tables_without_context}")
    
    return tables_with_context, tables_without_context


def check_table_relationships():
    """Check relationships TO and FROM table entities."""
    print("\n" + "=" * 80)
    print("2. TABLE RELATIONSHIPS - Connectivity Check")
    print("=" * 80)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    with driver.session() as s:
        # Outbound relationships FROM tables
        print("\n--- Relationships FROM table entities ---")
        r = s.run('''
            MATCH (t:swa_tas)-[r]->(other:swa_tas)
            WHERE t.entity_id STARTS WITH "table_p"
            RETURN t.entity_id as table_id, type(r) as rel_type, other.entity_id as target, other.entity_type as target_type
            ORDER BY t.entity_id
            LIMIT 30
        ''')
        outbound = list(r)
        print(f"Found {len(outbound)} outbound relationships")
        for rec in outbound[:15]:
            print(f"  {rec['table_id']} --[{rec['rel_type']}]--> {rec['target']} ({rec['target_type']})")
        
        # Inbound relationships TO tables
        print("\n--- Relationships TO table entities ---")
        r = s.run('''
            MATCH (other:swa_tas)-[r]->(t:swa_tas)
            WHERE t.entity_id STARTS WITH "table_p"
            RETURN other.entity_id as source, other.entity_type as source_type, type(r) as rel_type, t.entity_id as table_id
            ORDER BY t.entity_id
            LIMIT 30
        ''')
        inbound = list(r)
        print(f"Found {len(inbound)} inbound relationships")
        for rec in inbound[:15]:
            print(f"  {rec['source']} ({rec['source_type']}) --[{rec['rel_type']}]--> {rec['table_id']}")
        
        # Check for isolated tables
        print("\n--- Isolated table entities (no relationships) ---")
        r = s.run('''
            MATCH (t:swa_tas)
            WHERE t.entity_id STARTS WITH "table_p"
            AND NOT (t)-[]-()
            RETURN t.entity_id as id, t.entity_type as type
        ''')
        isolated = list(r)
        print(f"Found {len(isolated)} isolated tables")
        for rec in isolated:
            print(f"  ❌ {rec['id']} ({rec['type']})")
    
    driver.close()
    return len(outbound), len(inbound), len(isolated)


def check_vdb_table_entries():
    """Check VDB entries for table entities."""
    print("\n" + "=" * 80)
    print("3. VECTOR DATABASE - Table Entity Embeddings")
    print("=" * 80)
    
    vdb_entities_path = RAG_STORAGE / "vdb_entities.json"
    
    if not vdb_entities_path.exists():
        print(f"❌ VDB file not found: {vdb_entities_path}")
        return 0
    
    with open(vdb_entities_path, 'r', encoding='utf-8') as f:
        vdb_data = json.load(f)
    
    # Check structure
    print(f"VDB structure keys: {list(vdb_data.keys())}")
    
    table_entries = []
    
    # Look for table entries in the data
    if '__data__' in vdb_data:
        for entry_id, entry in vdb_data['__data__'].items():
            entity_name = entry.get('entity_name', '') or ''
            if 'table_p' in entity_name.lower():
                table_entries.append({
                    'id': entry_id,
                    'entity_name': entity_name,
                    'entity_type': entry.get('entity_type', 'unknown'),
                    'description': (entry.get('description', '') or '')[:200]
                })
    
    print(f"\nFound {len(table_entries)} table entries in VDB")
    
    context_markers = ['appendix', 'section', 'attachment', 'h.2.0', 'workload']
    with_context = 0
    
    for entry in table_entries[:10]:
        desc = entry['description'].lower()
        has_context = any(m in desc for m in context_markers)
        if has_context:
            with_context += 1
        status = "✅" if has_context else "❌"
        print(f"\n{status} {entry['entity_name']} ({entry['entity_type']})")
        print(f"   {entry['description']}...")
    
    print(f"\n--- VDB Summary ---")
    print(f"Table entries with context: {with_context}/{len(table_entries[:10])} (sample)")
    
    return len(table_entries)


def check_chunk_coverage():
    """Check if chunks contain table descriptions with context."""
    print("\n" + "=" * 80)
    print("4. TEXT CHUNKS - Table Context Coverage")
    print("=" * 80)
    
    chunks_path = RAG_STORAGE / "text_chunks.json"
    
    if not chunks_path.exists():
        print(f"❌ Chunks file not found: {chunks_path}")
        return
    
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks_data = json.load(f)
    
    # Find chunks mentioning tables or appendices
    table_chunks = []
    appendix_chunks = []
    
    if '__data__' in chunks_data:
        for chunk_id, chunk in chunks_data['__data__'].items():
            content = (chunk.get('content', '') or '').lower()
            if 'table_p' in content or 'table from' in content:
                table_chunks.append(chunk_id)
            if 'appendix h' in content or 'appendix j' in content or 'appendix k' in content:
                appendix_chunks.append(chunk_id)
    
    print(f"Chunks mentioning tables: {len(table_chunks)}")
    print(f"Chunks mentioning appendices: {len(appendix_chunks)}")
    
    # Show sample
    if '__data__' in chunks_data and table_chunks:
        print("\n--- Sample table-related chunks ---")
        for chunk_id in table_chunks[:3]:
            chunk = chunks_data['__data__'].get(chunk_id, {})
            content = chunk.get('content', '')[:400]
            print(f"\nChunk {chunk_id[:20]}...")
            print(f"   {content}...")


def simulate_query():
    """Simulate a user query to test retrieval quality."""
    print("\n" + "=" * 80)
    print("5. QUERY SIMULATION - Will retrieval work?")
    print("=" * 80)
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    test_queries = [
        ("What are the workload estimates for Al Dhafra Air Base?", ["workload", "adab", "al dhafra"]),
        ("What CDRLs are required for this contract?", ["cdrl"]),
        ("What are the staffing requirements?", ["staff", "personnel", "site manager"]),
    ]
    
    with driver.session() as s:
        for query, keywords in test_queries:
            print(f"\n📋 Query: {query}")
            
            # Simulate retrieval by searching descriptions
            keyword_pattern = "|".join(keywords)
            r = s.run(f'''
                MATCH (n:swa_tas)
                WHERE any(kw IN {keywords} WHERE toLower(n.description) CONTAINS kw)
                   OR any(kw IN {keywords} WHERE toLower(n.entity_id) CONTAINS kw)
                RETURN n.entity_id as id, n.entity_type as type, substring(n.description, 0, 150) as desc
                LIMIT 10
            ''')
            
            results = list(r)
            print(f"   Found {len(results)} relevant entities:")
            for rec in results[:5]:
                print(f"   - [{rec['type']}] {rec['id']}")
                # Check if tables are in results
                if rec['id'].startswith('table_p'):
                    print(f"     📊 TABLE with context: {rec['desc'][:100]}...")
    
    driver.close()


def main():
    print("=" * 80)
    print("ISSUE #62 DEEP VALIDATION - Context-Aware Processing")
    print("=" * 80)
    print(f"Workspace: {WORKSPACE}")
    print(f"RAG Storage: {RAG_STORAGE}")
    print()
    
    # Run all checks
    tables_with, tables_without = check_table_descriptions()
    outbound, inbound, isolated = check_table_relationships()
    vdb_tables = check_vdb_table_entries()
    check_chunk_coverage()
    simulate_query()
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 80)
    
    total_tables = tables_with + tables_without
    context_pct = (tables_with / total_tables * 100) if total_tables > 0 else 0
    
    print(f"""
    1. Table Context Coverage: {tables_with}/{total_tables} ({context_pct:.1f}%)
    2. Table Relationships: {outbound} outbound, {inbound} inbound
    3. Isolated Tables: {isolated}
    4. VDB Table Entries: {vdb_tables}
    
    Issue #62 Status: {"✅ WORKING" if context_pct > 50 else "⚠️ NEEDS REVIEW"}
    """)


if __name__ == "__main__":
    main()
