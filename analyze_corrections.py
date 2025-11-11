"""
Analyze what entity types were corrected during semantic post-processing.
This may reveal if requirements were reclassified to other types.
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
from collections import defaultdict

load_dotenv()

neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")

print("\n" + "="*80)
print("🔍 SEMANTIC POST-PROCESSING CORRECTION ANALYSIS")
print("="*80)

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

try:
    with driver.session(database=neo4j_database) as session:
        
        # Get all corrected entities with their types
        query = f"""
        MATCH (n:`{workspace}`)
        WHERE n.corrected_by IS NOT NULL
        RETURN n.name AS name, n.entity_type AS current_type, n.corrected_by AS corrector
        ORDER BY current_type, name
        """
        
        results = session.run(query)
        
        type_counts = defaultdict(int)
        corrections_by_type = defaultdict(list)
        
        for record in results:
            entity_type = record["current_type"]
            entity_name = record["name"]
            
            type_counts[entity_type] += 1
            corrections_by_type[entity_type].append(entity_name)
        
        print(f"\n📊 Corrected Entity Distribution:")
        print("-" * 80)
        
        total_corrected = sum(type_counts.values())
        
        for entity_type in sorted(type_counts.keys(), key=lambda x: type_counts[x], reverse=True):
            count = type_counts[entity_type]
            pct = (count / total_corrected) * 100
            print(f"  {entity_type:30s}: {count:3d} ({pct:5.1f}%)")
        
        print(f"\n  {'TOTAL CORRECTED':30s}: {total_corrected:3d}")
        
        # Check if any requirements were corrected
        if "requirement" in type_counts:
            print(f"\n⚠️  {type_counts['requirement']} REQUIREMENTS were corrected:")
            print("-" * 80)
            for req_name in corrections_by_type["requirement"][:10]:
                print(f"  - {req_name}")
            
            if len(corrections_by_type["requirement"]) > 10:
                print(f"  ... and {len(corrections_by_type['requirement']) - 10} more")
        else:
            print(f"\n✅ NO REQUIREMENTS were corrected (good - means they were extracted correctly)")
        
        # Show sample corrections for each type
        print(f"\n📝 Sample Corrections by Type:")
        print("-" * 80)
        
        for entity_type in sorted(type_counts.keys(), key=lambda x: type_counts[x], reverse=True)[:5]:
            print(f"\n{entity_type.upper()} ({type_counts[entity_type]} corrected):")
            for entity_name in corrections_by_type[entity_type][:3]:
                print(f"  - {entity_name}")
            
            if len(corrections_by_type[entity_type]) > 3:
                print(f"  ... and {len(corrections_by_type[entity_type]) - 3} more")

finally:
    driver.close()

print("\n" + "="*80)
print("🔍 INTERPRETATION")
print("="*80)
print(f"""
If many requirements were corrected:
  → Semantic post-processor may have reclassified them to other types
  → This could explain the requirement count drop from 451 → 123

If NO requirements were corrected:
  → The 328 lost requirements were never extracted by Grok-4 in the first place
  → This points to Grok-4 reasoning model variability

If mostly UNKNOWN/FORBIDDEN types were corrected:
  → Expected behavior - post-processor fixing extraction mistakes
  → Not related to requirement loss
""")
print("="*80 + "\n")
