"""Check which eval factors are classified as main vs supporting entities."""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
from validation.section_l_m_coverage import SectionLMCoverageValidator

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    auth=(os.getenv('NEO4J_USER', 'neo4j'), os.getenv('NEO4J_PASSWORD'))
)

workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")

with driver.session(database='neo4j') as session:
    # Get all eval factors
    result = session.run(f"""
        MATCH (e:`{workspace}`)
        WHERE e.entity_type = 'evaluation_factor'
        RETURN e.entity_id AS name
        ORDER BY e.entity_id
    """)
    all_factors = [record['name'] for record in result]
    
    # Get linked eval factors
    result_linked = session.run(f"""
        MATCH (e:`{workspace}`)-[rel]-(r:`{workspace}`)
        WHERE e.entity_type = 'evaluation_factor'
          AND r.entity_type = 'requirement'
        RETURN DISTINCT e.entity_id AS name
    """)
    linked_factors = set(record['name'] for record in result_linked)

# Classify each factor
main_factors = []
supporting_entities = []
main_linked = []
supporting_linked = []

for factor in all_factors:
    is_main = SectionLMCoverageValidator.is_main_evaluation_factor(factor)
    is_linked = factor in linked_factors
    
    if is_main:
        main_factors.append(factor)
        if is_linked:
            main_linked.append(factor)
    else:
        supporting_entities.append(factor)
        if is_linked:
            supporting_linked.append(factor)

print(f"\n{'='*80}")
print("EVALUATION FACTOR CLASSIFICATION")
print(f"{'='*80}")
print(f"\nTotal: {len(all_factors)} evaluation factors")
print(f"  Main factors: {len(main_factors)}")
print(f"  Supporting entities: {len(supporting_entities)}")
print(f"\nLinked to requirements: {len(linked_factors)} total")
print(f"  Main linked: {len(main_linked)}")
print(f"  Supporting linked: {len(supporting_linked)}")

print(f"\n{'='*80}")
print("✅ MAIN FACTORS (should be linkable)")
print(f"{'='*80}")
for i, factor in enumerate(main_factors, 1):
    status = "🔗 LINKED" if factor in linked_factors else "⚠️  ORPHANED"
    print(f"{i}. {status} - {factor}")

print(f"\n{'='*80}")
print("❌ SUPPORTING ENTITIES (should be filtered out)")
print(f"{'='*80}")
for i, factor in enumerate(supporting_entities, 1):
    status = "🔗 LINKED" if factor in linked_factors else "   Not linked"
    print(f"{i}. {status} - {factor}")

driver.close()

print(f"\n{'='*80}")
print("SUMMARY")
print(f"{'='*80}")
print(f"Main factor coverage: {len(main_linked)}/{len(main_factors)} = {len(main_linked)/len(main_factors)*100:.1f}%")
print(f"Supporting entities incorrectly linked: {len(supporting_linked)}")
print(f"{'='*80}\n")
