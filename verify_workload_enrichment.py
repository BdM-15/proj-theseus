"""
Verify Workload Enrichment Properties in Neo4j
===============================================

Check if REQUIREMENT entities have the new workload metadata properties.
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# Neo4j connection
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")

print("\n" + "="*80)
print("🔍 WORKLOAD ENRICHMENT VERIFICATION")
print("="*80)
print(f"Workspace: {workspace}")
print()

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

try:
    with driver.session(database=neo4j_database) as session:
        
        # Query 1: Check if any requirements have workload properties
        query_check = f"""
        MATCH (n:`{workspace}`)
        WHERE n.entity_type = 'requirement' AND n.has_workload_metric IS NOT NULL
        RETURN count(n) AS enriched_count
        """
        
        result = session.run(query_check)
        enriched_count = result.single()["enriched_count"]
        
        print(f"📊 Requirements with workload metadata: {enriched_count}")
        
        if enriched_count == 0:
            print("\n❌ NO WORKLOAD ENRICHMENT DETECTED")
            print("   Workload metadata enrichment may not have run.")
            print("   Check logs/server.log for Step 4: Workload Metadata Enrichment")
        else:
            print(f"\n✅ Workload enrichment successful!")
            
            # Query 2: Sample enriched requirements
            query_sample = f"""
            MATCH (n:`{workspace}`)
            WHERE n.entity_type = 'requirement' AND n.has_workload_metric = true
            RETURN n.entity_id AS name,
                   n.has_workload_metric AS has_metric,
                   n.workload_categories AS categories,
                   n.boe_relevance AS boe_scores
            LIMIT 5
            """
            
            results = session.run(query_sample)
            
            print("\n📋 Sample Enriched Requirements:")
            print("-" * 80)
            for i, record in enumerate(results, 1):
                print(f"{i}. {record['name']}")
                print(f"   Has workload: {record['has_metric']}")
                print(f"   Categories: {record['categories']}")
                print(f"   BOE relevance: {record['boe_scores']}")
                print()
            
            # Query 3: Category distribution
            query_categories = f"""
            MATCH (n:`{workspace}`)
            WHERE n.entity_type = 'requirement' AND n.workload_categories IS NOT NULL
            RETURN n.workload_categories AS categories, count(*) AS count
            """
            
            results = session.run(query_categories)
            
            print("\n📊 Workload Category Distribution:")
            print("-" * 80)
            category_totals = {}
            for record in results:
                import json
                try:
                    cats = json.loads(record['categories'])
                    for cat in cats:
                        category_totals[cat] = category_totals.get(cat, 0) + record['count']
                except:
                    pass
            
            for cat, count in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                print(f"  {cat:15s}: {count:4d} requirements")
        
finally:
    driver.close()

print("\n" + "="*80)
