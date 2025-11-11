"""Check what entities are classified as evaluation_factor"""
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    auth=(os.getenv('NEO4J_USERNAME', 'neo4j'), os.getenv('NEO4J_PASSWORD', 'govcon-capture-2025'))
)

session = driver.session(database=os.getenv('NEO4J_DATABASE'))

# Get all evaluation factors
result = session.run("""
    MATCH (e:`afcapv_adab_iss_2025`)
    WHERE e.entity_type = 'evaluation_factor'
    RETURN e.entity_id as name, e.description as desc
    ORDER BY e.entity_id
""")

print("\n" + "="*80)
print("EVALUATION FACTORS IN NEO4J")
print("="*80)

eval_factors = list(result)
print(f"\nTotal: {len(eval_factors)} evaluation factors\n")

for i, record in enumerate(eval_factors, 1):
    name = record['name']
    desc = record['desc'][:150] if record['desc'] else "No description"
    print(f"{i}. {name}")
    print(f"   {desc}\n")

session.close()
driver.close()
