"""Check if orphaned entities are critical for BOE/BOM"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'neo4j://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = 'afcapv_adab_iss_2025'
db = os.getenv('NEO4J_DATABASE', 'neo4j')

print("="*80)
print("ORPHANED ENTITIES - BOE/BOM IMPACT ANALYSIS")
print("="*80)

with driver.session(database=db) as session:
    # Get all orphaned entities
    result = session.run(f"""
        MATCH (orphan:{workspace})
        WHERE NOT (orphan)-[]-()
        RETURN orphan.entity_id as name,
               orphan.entity_type as type,
               orphan.description as desc
        ORDER BY orphan.entity_type, orphan.entity_id
    """)
    
    orphans = [(r['name'], r['type'], r['desc']) for r in result]
    
    # Categorize by BOE/BOM criticality
    critical = []      # Direct BOE/BOM items
    peripheral = []    # Administrative/minor
    
    boe_keywords = ['equipment', 'material', 'labor', 'deliverable', 'requirement', 'maintenance', 'supply']
    admin_keywords = ['dodaac', 'routing', 'wawf', 'table', 'field']
    
    for name, etype, desc in orphans:
        desc_lower = (desc or '').lower()
        name_lower = name.lower()
        
        # Check if potentially BOE/BOM relevant
        is_admin = any(kw in name_lower or kw in desc_lower for kw in admin_keywords)
        is_boe_relevant = any(kw in name_lower or kw in desc_lower for kw in boe_keywords)
        
        if not is_admin and (is_boe_relevant or etype in ['equipment', 'deliverable', 'requirement']):
            critical.append((name, etype, desc))
        else:
            peripheral.append((name, etype, desc))
    
    print(f"\n🚨 CRITICAL FOR BOE/BOM ({len(critical)} items):")
    print("="*80)
    if critical:
        for name, etype, desc in critical:
            print(f"\n{etype.upper()}: {name}")
            print(f"  Description: {desc[:200]}")
            
            # Check if this entity appears in workload-enriched requirements
            check_result = session.run(f"""
                MATCH (req:{workspace})
                WHERE req.entity_type = 'requirement'
                  AND req.boe_relevance IS NOT NULL
                  AND (toLower(req.entity_name) CONTAINS toLower($name)
                       OR toLower(req.description) CONTAINS toLower($name))
                RETURN req.entity_id as req_name, req.boe_relevance as relevance
                LIMIT 3
            """, name=name)
            
            mentions = list(check_result)
            if mentions:
                print(f"  ✅ Referenced in {len(mentions)} BOE-enriched requirement(s):")
                for m in mentions[:2]:
                    print(f"     - {m['req_name']} (BOE: {m['relevance']})")
            else:
                print(f"  ⚠️  NOT referenced in any BOE-enriched requirements")
    else:
        print("\n✅ None - all orphaned entities are peripheral/administrative")
    
    print(f"\n\n📋 PERIPHERAL/ADMINISTRATIVE ({len(peripheral)} items):")
    print("="*80)
    for name, etype, desc in peripheral[:10]:  # Show first 10
        print(f"  - {name} ({etype})")
    if len(peripheral) > 10:
        print(f"  ... and {len(peripheral) - 10} more")

driver.close()

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print(f"""
Total orphans: {len(orphans)}
  - Critical for BOE/BOM: {len(critical)}
  - Peripheral/Admin: {len(peripheral)}

If critical items are referenced in BOE-enriched requirements, they're already
captured in the cost estimation workflow even if orphaned in the graph.
""")
