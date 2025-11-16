"""
Holistic Orphan Analysis: Pattern Discovery for BOE/BOM Build-ups
==================================================================

Goal: Identify WHY orphaned entities exist and what patterns they represent
      for labor staffing and ODC build-ups.

This is NOT about fixing "2XL Wipes" - it's about discovering:
1. What types of entities consistently fail to get linked?
2. What semantic patterns does the LLM miss?
3. What relationship types are under-represented?
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = 'afcapv_adab_iss_2025'
db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("="*80)
print("PATTERN ANALYSIS: Why Orphans Exist")
print("="*80)

with driver.session(database=db) as session:
    # Pattern 1: Entity type co-occurrence in chunks
    print("\n1. CHUNK CO-OCCURRENCE PATTERNS")
    print("="*80)
    print("For each orphan, what OTHER entity types exist in the same chunk?")
    print("This reveals what relationships SHOULD exist but don't.\n")
    
    result = session.run(f"""
        MATCH (orphan:{workspace})
        WHERE NOT (orphan)-[]-()
          AND orphan.source_id IS NOT NULL
        
        MATCH (neighbor:{workspace})
        WHERE neighbor.source_id = orphan.source_id
          AND neighbor <> orphan
          AND (neighbor)-[]-()  // Only look at connected neighbors
        
        RETURN orphan.entity_id as orphan_name,
               orphan.entity_type as orphan_type,
               collect(DISTINCT neighbor.entity_type) as neighbor_types,
               count(DISTINCT neighbor) as neighbor_count,
               orphan.source_id as chunk_id
        ORDER BY neighbor_count DESC
    """)
    
    co_occurrence_patterns = defaultdict(lambda: defaultdict(int))
    
    for record in result:
        orphan_type = record['orphan_type']
        for neighbor_type in record['neighbor_types']:
            co_occurrence_patterns[orphan_type][neighbor_type] += 1
    
    print("Orphan Type → Co-located Connected Types (frequency):\n")
    for orphan_type, neighbors in sorted(co_occurrence_patterns.items()):
        print(f"{orphan_type.upper()}:")
        for neighbor_type, count in sorted(neighbors.items(), key=lambda x: x[1], reverse=True):
            print(f"  → {neighbor_type}: {count} times")
        print()
    
    # Pattern 2: Description patterns
    print("\n2. DESCRIPTION SEMANTIC PATTERNS")
    print("="*80)
    print("What keywords/phrases appear in orphan descriptions?\n")
    
    result = session.run(f"""
        MATCH (orphan:{workspace})
        WHERE NOT (orphan)-[]-()
        RETURN orphan.entity_id as name,
               orphan.entity_type as type,
               orphan.description as desc
    """)
    
    # Analyze for semantic patterns
    patterns = {
        'quantified': [],          # Has numbers/quantities (10 receptacles, 6 trash cans)
        'table_embedded': [],      # References tables/fields
        'government_role': [],     # Gov't provides/furnishes/maintains
        'contractor_deliverable': [], # Contractor shall submit/provide
        'conditional': [],         # "may", "when needed", "if required"
        'administrative': [],      # DODAAC, routing, approval
    }
    
    for record in result:
        name = record['name']
        desc = (record['desc'] or '').lower()
        etype = record['type']
        
        # Check patterns
        if any(word in desc for word in ['table', 'field', 'column', 'routing']):
            patterns['table_embedded'].append((name, etype, desc[:100]))
        
        if any(word in desc for word in ['government', 'furnished', 'provided by government']):
            patterns['government_role'].append((name, etype, desc[:100]))
        
        if any(word in desc for word in ['contractor shall submit', 'contractor provides']):
            patterns['contractor_deliverable'].append((name, etype, desc[:100]))
        
        if any(word in desc for word in ['may', 'when needed', 'if required', 'as necessary']):
            patterns['conditional'].append((name, etype, desc[:100]))
        
        if any(word in desc for word in ['dodaac', 'approval', 'certification', 'authorization']):
            patterns['administrative'].append((name, etype, desc[:100]))
        
        # Check for quantities
        import re
        if re.search(r'\b\d+\b', desc):
            patterns['quantified'].append((name, etype, desc[:100]))
    
    for pattern_name, items in patterns.items():
        if items:
            print(f"\n{pattern_name.upper().replace('_', ' ')} ({len(items)} items):")
            for name, etype, desc in items[:3]:
                print(f"  - {name} ({etype})")
                print(f"    {desc}")
    
    # Pattern 3: Missing relationship types
    print("\n\n3. MISSING RELATIONSHIP TYPE ANALYSIS")
    print("="*80)
    print("What relationships SHOULD exist based on entity types?\n")
    
    # Get all existing relationship types
    result = session.run(f"""
        MATCH (:{workspace})-[r]->(:{workspace})
        RETURN DISTINCT type(r) as rel_type, count(*) as frequency
        ORDER BY frequency DESC
    """)
    
    existing_rels = {r['rel_type']: r['frequency'] for r in result}
    
    print("Current relationship type distribution:")
    for rel_type, freq in list(existing_rels.items())[:10]:
        print(f"  {rel_type}: {freq}")
    
    # Analyze what's missing
    print("\n\nPotential missing relationship patterns:")
    
    expected_patterns = {
        'equipment → requirement': 'REQUIRED_BY or SUPPORTS',
        'deliverable → requirement': 'FULFILLS or SATISFIES',
        'equipment → equipment': 'PART_OF or DEPENDS_ON',
        'person → deliverable': 'RESPONSIBLE_FOR',
        'document → requirement': 'SPECIFIES or DEFINES',
        'technology → requirement': 'ENABLES or REQUIRED_FOR',
    }
    
    for pattern, suggested_rel in expected_patterns.items():
        source_type, target_type = pattern.split(' → ')
        
        # Check if this pattern exists
        result = session.run(f"""
            MATCH (s:{workspace})-[r]-(t:{workspace})
            WHERE s.entity_type = $source_type
              AND t.entity_type = $target_type
            RETURN count(DISTINCT r) as count
        """, source_type=source_type, target_type=target_type)
        
        count = result.single()['count']
        
        # Check orphans of this type
        orphan_result = session.run(f"""
            MATCH (orphan:{workspace})
            WHERE orphan.entity_type = $source_type
              AND NOT (orphan)-[]-()
            RETURN count(orphan) as orphan_count
        """, source_type=source_type)
        
        orphan_count = orphan_result.single()['orphan_count']
        
        if orphan_count > 0:
            print(f"\n  {pattern}:")
            print(f"    Existing relationships: {count}")
            print(f"    Orphaned {source_type}: {orphan_count}")
            print(f"    Suggested: {suggested_rel}")

    # Pattern 4: Semantic distance analysis
    print("\n\n4. SEMANTIC CONTEXT ANALYSIS")
    print("="*80)
    print("Are orphans in chunks that are semantically distant from main topics?\n")
    
    # Get orphans and check their chunk's topic diversity
    result = session.run(f"""
        MATCH (orphan:{workspace})
        WHERE NOT (orphan)-[]-()
          AND orphan.source_id IS NOT NULL
        
        MATCH (chunk_entity:{workspace})
        WHERE chunk_entity.source_id = orphan.source_id
        
        WITH orphan.source_id as chunk_id,
             count(DISTINCT chunk_entity) as total_entities,
             count(DISTINCT chunk_entity.entity_type) as type_diversity,
             collect(DISTINCT chunk_entity.entity_type) as types
        
        RETURN chunk_id,
               total_entities,
               type_diversity,
               types
        ORDER BY total_entities DESC
        LIMIT 10
    """)
    
    print("Top chunks with orphans (by entity count):\n")
    for record in result:
        print(f"Chunk: {record['chunk_id'][:40]}...")
        print(f"  Entities: {record['total_entities']}, Type diversity: {record['type_diversity']}")
        print(f"  Types: {', '.join(record['types'])}")
        print()

driver.close()

print("\n" + "="*80)
print("PATTERN DISCOVERY SUMMARY")
print("="*80)
print("""
KEY FINDINGS:

1. CO-OCCURRENCE PATTERNS
   → Shows which entity types appear together but aren't linked
   → Reveals missing relationship opportunities

2. SEMANTIC PATTERNS  
   → Identifies description characteristics of orphans
   → Helps refine LLM prompts to catch these patterns

3. MISSING RELATIONSHIP TYPES
   → Compares expected vs actual relationship patterns
   → Identifies under-represented relationship types

4. SEMANTIC CONTEXT
   → Determines if orphans are in peripheral/isolated chunks
   → Or if they're in rich contexts but still missed

NEXT STEPS:
Based on patterns found, we can:
- Add targeted relationship inference algorithms
- Enhance LLM prompts with discovered patterns
- Create relationship type templates for common patterns
- Build automated orphan detection and fixing pipeline
""")
