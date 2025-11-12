"""
Test script to validate dual-pattern deliverable traceability (Algorithm 3)
Tests both SATISFIED_BY and PRODUCES relationship types
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "your_password")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def run_query(query):
    """Execute Cypher query and return results"""
    with driver.session() as session:
        result = session.run(query)
        return [record.data() for record in result]

print("=" * 80)
print("🧪 DELIVERABLE TRACEABILITY VALIDATION (Algorithm 3)")
print("=" * 80)

# Test 1: Pattern 1 - Requirement → Deliverable (SATISFIED_BY)
print("\n📊 TEST 1: Pattern 1 (Requirement → Deliverable) - SATISFIED_BY Relationships")
print("-" * 80)

query1 = """
MATCH (r:Entity {entity_type: 'requirement'})-[rel:SATISFIED_BY]->(d:Entity {entity_type: 'deliverable'})
RETURN r.entity_name as requirement, 
       d.entity_name as deliverable,
       substring(r.description, 0, 100) as req_desc,
       substring(d.description, 0, 100) as deliv_desc
ORDER BY r.entity_name
LIMIT 10
"""

results = run_query(query1)
print(f"Found {len(results)} SATISFIED_BY relationships (showing first 10):\n")

for i, r in enumerate(results, 1):
    print(f"{i}. REQUIREMENT: {r['requirement']}")
    print(f"   └─> DELIVERABLE: {r['deliverable']}")
    print(f"   Requirement: {r['req_desc']}...")
    print(f"   Deliverable: {r['deliv_desc']}...")
    print()

# Test 2: Pattern 2 - Work Statement → Deliverable (PRODUCES)
print("\n📊 TEST 2: Pattern 2 (Work Statement → Deliverable) - PRODUCES Relationships")
print("-" * 80)

query2 = """
MATCH (w:Entity)-[rel:PRODUCES]->(d:Entity {entity_type: 'deliverable'})
WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
RETURN w.entity_name as work_statement,
       w.entity_type as work_type,
       d.entity_name as deliverable,
       substring(w.description, 0, 100) as work_desc,
       substring(d.description, 0, 100) as deliv_desc
ORDER BY w.entity_name
"""

results = run_query(query2)
print(f"Found {len(results)} PRODUCES relationships:\n")

for i, r in enumerate(results, 1):
    print(f"{i}. WORK STATEMENT ({r['work_type']}): {r['work_statement']}")
    print(f"   └─> DELIVERABLE: {r['deliverable']}")
    print(f"   Work: {r['work_desc']}...")
    print(f"   Deliverable: {r['deliv_desc']}...")
    print()

# Test 3: Coverage Statistics
print("\n📊 TEST 3: Coverage Statistics")
print("-" * 80)

query3 = """
// Total deliverables
MATCH (d:Entity {entity_type: 'deliverable'})
WITH count(d) as total_deliverables

// Deliverables with Pattern 1 (SATISFIED_BY)
MATCH (r:Entity {entity_type: 'requirement'})-[:SATISFIED_BY]->(d1:Entity {entity_type: 'deliverable'})
WITH total_deliverables, count(DISTINCT d1) as pattern1_covered

// Deliverables with Pattern 2 (PRODUCES)
MATCH (w:Entity)-[:PRODUCES]->(d2:Entity {entity_type: 'deliverable'})
WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
WITH total_deliverables, pattern1_covered, count(DISTINCT d2) as pattern2_covered

// Deliverables with either pattern
MATCH (d3:Entity {entity_type: 'deliverable'})
WHERE EXISTS {
    MATCH (r:Entity {entity_type: 'requirement'})-[:SATISFIED_BY]->(d3)
} OR EXISTS {
    MATCH (w:Entity)-[:PRODUCES]->(d3)
    WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
}
WITH total_deliverables, pattern1_covered, pattern2_covered, count(d3) as total_covered

// Deliverables with both patterns
MATCH (d4:Entity {entity_type: 'deliverable'})
WHERE EXISTS {
    MATCH (r:Entity {entity_type: 'requirement'})-[:SATISFIED_BY]->(d4)
} AND EXISTS {
    MATCH (w:Entity)-[:PRODUCES]->(d4)
    WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
}
WITH total_deliverables, pattern1_covered, pattern2_covered, total_covered, count(d4) as both_patterns

RETURN total_deliverables,
       pattern1_covered,
       pattern2_covered,
       total_covered,
       both_patterns,
       round(100.0 * pattern1_covered / total_deliverables, 1) as pattern1_pct,
       round(100.0 * pattern2_covered / total_deliverables, 1) as pattern2_pct,
       round(100.0 * total_covered / total_deliverables, 1) as overall_coverage_pct
"""

results = run_query(query3)
if results:
    stats = results[0]
    print(f"Total Deliverables: {stats['total_deliverables']}")
    print(f"\nPattern 1 (Requirement→Deliverable):")
    print(f"  ✓ Covered: {stats['pattern1_covered']} ({stats['pattern1_pct']}%)")
    print(f"\nPattern 2 (WorkStatement→Deliverable):")
    print(f"  ✓ Covered: {stats['pattern2_covered']} ({stats['pattern2_pct']}%)")
    print(f"\nBoth Patterns (dual context):")
    print(f"  ✓ Deliverables with both: {stats['both_patterns']}")
    print(f"\n🎯 Overall Coverage: {stats['total_covered']}/{stats['total_deliverables']} ({stats['overall_coverage_pct']}%)")

# Test 4: Orphaned Deliverables (no traceability)
print("\n📊 TEST 4: Orphaned Deliverables (No Traceability)")
print("-" * 80)

query4 = """
MATCH (d:Entity {entity_type: 'deliverable'})
WHERE NOT EXISTS {
    MATCH (r:Entity {entity_type: 'requirement'})-[:SATISFIED_BY]->(d)
} AND NOT EXISTS {
    MATCH (w:Entity)-[:PRODUCES]->(d)
    WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
}
RETURN d.entity_name as deliverable,
       substring(d.description, 0, 150) as description
ORDER BY d.entity_name
LIMIT 15
"""

results = run_query(query4)
print(f"Found {len(results)} orphaned deliverables (showing first 15):\n")

if results:
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['deliverable']}")
        print(f"   Description: {r['description']}...")
        print()
else:
    print("✅ No orphaned deliverables - all have traceability!")

# Test 5: Multi-Source Deliverables (both patterns)
print("\n📊 TEST 5: Multi-Source Deliverables (Both Patterns)")
print("-" * 80)

query5 = """
MATCH (r:Entity {entity_type: 'requirement'})-[:SATISFIED_BY]->(d:Entity {entity_type: 'deliverable'})<-[:PRODUCES]-(w:Entity)
WHERE w.entity_type IN ['statement_of_work', 'pws', 'soo']
RETURN d.entity_name as deliverable,
       r.entity_name as requirement,
       w.entity_name as work_statement,
       substring(d.description, 0, 100) as description
ORDER BY d.entity_name
"""

results = run_query(query5)
print(f"Found {len(results)} deliverables with BOTH patterns (comprehensive context):\n")

for i, r in enumerate(results, 1):
    print(f"{i}. DELIVERABLE: {r['deliverable']}")
    print(f"   ├─ From Requirement: {r['requirement']}")
    print(f"   └─ From Work Statement: {r['work_statement']}")
    print(f"   Description: {r['description']}...")
    print()

print("=" * 80)
print("✅ VALIDATION COMPLETE")
print("=" * 80)

driver.close()
