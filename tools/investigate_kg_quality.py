#!/usr/bin/env python3
"""Comprehensive KG quality investigation for Neo4j."""

import os
from dotenv import load_dotenv
load_dotenv()

from neo4j import GraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4jpass")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_query(query, params=None):
    """Run a Cypher query and return results."""
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(r) for r in result]

print("=" * 70)
print("NEO4J KNOWLEDGE GRAPH QUALITY INVESTIGATION")
print("=" * 70)

# 1. Total counts
print("\n📊 OVERALL STATISTICS")
print("-" * 70)
entity_count = run_query("MATCH (n:Entity) RETURN count(n) as count")[0]["count"]
rel_count = run_query("MATCH ()-[r]->() RETURN count(r) as count")[0]["count"]
print(f"  Total entities: {entity_count}")
print(f"  Total relationships: {rel_count}")

# 2. Entity type distribution
print("\n📋 ENTITY TYPE DISTRIBUTION")
print("-" * 70)
types = run_query("""
    MATCH (n:Entity)
    RETURN n.entity_type as type, count(n) as count
    ORDER BY count DESC
""")
for t in types:
    print(f"  {t['type']:<30}: {t['count']:>4}")

# 3. Relationship type distribution
print("\n🔗 RELATIONSHIP TYPE DISTRIBUTION")
print("-" * 70)
rels = run_query("""
    MATCH ()-[r]->()
    RETURN type(r) as rel_type, count(r) as count
    ORDER BY count DESC
""")
for r in rels:
    print(f"  {r['rel_type']:<40}: {r['count']:>4}")

# 4. Check for orphan entities in Neo4j
print("\n👻 ORPHAN ANALYSIS (Neo4j)")
print("-" * 70)
orphans = run_query("""
    MATCH (n:Entity)
    WHERE NOT (n)-[]-()
    RETURN n.entity_name as name, n.entity_type as type
    LIMIT 50
""")
print(f"  Orphan entities (no relationships): {len(orphans)}")
if orphans:
    print("\n  Sample orphans:")
    for o in orphans[:15]:
        print(f"    - {o['name'][:50]} ({o['type']})")

# 5. CHILD_OF relationships specifically
print("\n📁 CHILD_OF HIERARCHY ANALYSIS")
print("-" * 70)
child_ofs = run_query("""
    MATCH (child)-[r:CHILD_OF]->(parent)
    RETURN child.entity_name as child, parent.entity_name as parent
    LIMIT 30
""")
print(f"  Total CHILD_OF relationships: {len(run_query('MATCH ()-[r:CHILD_OF]->() RETURN count(r) as c')[0]['c'])}")
print("\n  Sample hierarchies:")
for rel in child_ofs[:20]:
    c = rel['child'][:40] if rel['child'] else 'N/A'
    p = rel['parent'][:40] if rel['parent'] else 'N/A'
    print(f"    {c} → {p}")

# 6. Check numbered section hierarchy
print("\n📝 NUMBERED SECTION HIERARCHY CHECK")
print("-" * 70)
numbered = run_query("""
    MATCH (n:Entity)
    WHERE n.entity_name =~ '^[A-Z]\\.[0-9].*|^[0-9]+\\.[0-9].*'
    RETURN n.entity_name as name, n.entity_type as type
    ORDER BY n.entity_name
    LIMIT 50
""")
print(f"  Numbered entities found: {len(numbered)}")
for n in numbered[:20]:
    print(f"    - {n['name'][:60]} ({n['type']})")

# 7. Check Algorithm inferred relationships
print("\n⚙️ POST-PROCESSING RELATIONSHIP SOURCES")
print("-" * 70)
algo_rels = run_query("""
    MATCH ()-[r]->()
    WHERE r.source_algorithm IS NOT NULL
    RETURN r.source_algorithm as algo, count(r) as count
    ORDER BY count DESC
""")
if algo_rels:
    for a in algo_rels:
        print(f"  {a['algo']:<40}: {a['count']:>4}")
else:
    print("  No source_algorithm property found on relationships")

# 8. Check evaluation factors → instructions mapping
print("\n📋 EVALUATION FACTOR COVERAGE")
print("-" * 70)
eval_factors = run_query("""
    MATCH (n:Entity {entity_type: 'evaluation_factor'})
    RETURN n.entity_name as name
    ORDER BY n.entity_name
""")
print(f"  Evaluation factors found: {len(eval_factors)}")
for ef in eval_factors:
    print(f"    - {ef['name']}")

# 9. Check requirements with workload enrichment
print("\n💼 WORKLOAD ENRICHMENT QUALITY")
print("-" * 70)
enriched = run_query("""
    MATCH (n:Entity {entity_type: 'requirement'})
    WHERE n.complexity_score IS NOT NULL
    RETURN count(n) as enriched
""")
total_reqs = run_query("""
    MATCH (n:Entity {entity_type: 'requirement'})
    RETURN count(n) as total
""")
print(f"  Total requirements: {total_reqs[0]['total']}")
print(f"  Enriched with workload data: {enriched[0]['enriched']}")

# Check sample enriched requirement
sample_enriched = run_query("""
    MATCH (n:Entity {entity_type: 'requirement'})
    WHERE n.complexity_score IS NOT NULL
    RETURN n.entity_name as name, n.complexity_score as complexity,
           n.labor_drivers as labor, n.material_needs as materials
    LIMIT 3
""")
if sample_enriched:
    print("\n  Sample enriched requirements:")
    for r in sample_enriched:
        print(f"    - {r['name'][:60]}")
        print(f"      Complexity: {r['complexity']}, Labor: {str(r['labor'])[:50]}...")

# 10. Check table entities
print("\n📊 TABLE ENTITY ANALYSIS")
print("-" * 70)
tables = run_query("""
    MATCH (n:Entity)
    WHERE n.entity_name STARTS WITH 'table_p'
    RETURN n.entity_name as name, n.entity_type as type
    ORDER BY n.entity_name
""")
print(f"  Table-derived entities: {len(tables)}")
for t in tables[:10]:
    print(f"    - {t['name']} ({t['type']})")

# 11. Check deliverable traceability
print("\n📦 DELIVERABLE TRACEABILITY")
print("-" * 70)
deliverable_rels = run_query("""
    MATCH (r)-[rel:PRODUCES|REQUIRES|SATISFIES]->(d)
    WHERE d.entity_type = 'deliverable'
    RETURN type(rel) as rel_type, count(rel) as count
""")
if deliverable_rels:
    for dr in deliverable_rels:
        print(f"  {dr['rel_type']}: {dr['count']}")
else:
    print("  No explicit deliverable traceability relationships found")

# 12. Check document → section connections  
print("\n📄 DOCUMENT STRUCTURE")
print("-" * 70)
doc_sections = run_query("""
    MATCH (d)-[r]->(s)
    WHERE d.entity_type = 'document' AND s.entity_type = 'section'
    RETURN count(r) as count
""")
print(f"  Document → Section relationships: {doc_sections[0]['count']}")

print("\n" + "=" * 70)
print("INVESTIGATION COMPLETE")
print("=" * 70)

driver.close()
