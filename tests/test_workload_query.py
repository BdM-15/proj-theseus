"""
Test Workload Enrichment Query Quality
======================================

Validates that workload metadata captures operational metrics for staffing/BOM analysis.

Test Query: "What are requirements with workload metrics and operational parameters?"

Expected Results:
- Requirements with workload_metric = true
- Complexity scores (1-10) showing effort level
- Labor drivers: volumes, frequencies, hours, locations, surges (NOT staffing solutions)
- Material needs: equipment, supplies, quantities (NOT specifications)
- BOE categories showing cost drivers
- Confidence scores showing extraction quality
"""

import pytest

# Neo4j-backed post-processing was intentionally removed to restore LightRAG defaults.
pytest.skip("Neo4j post-processing removed; skip Neo4j-only workload query test.", allow_module_level=True)

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import json


def test_workload_query():
    """Test workload enrichment query quality."""
    load_dotenv()
    
    # Connect to Neo4j
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")
    
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    print(f"\n{'='*80}")
    print(f"🏗️  WORKLOAD ENRICHMENT QUERY TEST")
    print(f"{'='*80}")
    print(f"\nWorkspace: {workspace}")
    print(f"Query: Requirements with workload metrics (complexity >= 5)")
    
    try:
        with driver.session(database=neo4j_database) as session:
            # Query for requirements with workload metrics and moderate-to-high complexity
            query = f"""
            MATCH (r:`{workspace}`)
            WHERE r.entity_type = 'requirement'
              AND r.has_workload_metric = true
              AND r.complexity_score >= 5
            RETURN 
              r.entity_id AS requirement,
              r.complexity_score AS complexity,
              r.complexity_rationale AS rationale,
              r.labor_drivers AS labor_drivers,
              r.material_needs AS material_needs,
              r.effort_estimate AS effort,
              r.workload_categories AS categories,
              r.boe_relevance AS confidence
            ORDER BY r.complexity_score DESC
            LIMIT 10
            """
            
            result = session.run(query)
            records = list(result)
            
            print(f"\n📊 Found {len(records)} requirements with workload metrics (complexity >= 5)")
            print(f"\n{'─'*80}")
            
            if not records:
                print("⚠️  No results! Checking if enrichment completed...")
                
                # Debug: Check total enriched requirements
                debug_query = f"""
                MATCH (r:`{workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND r.has_workload_metric = true
                RETURN count(r) AS enriched
                """
                debug_result = session.run(debug_query)
                enriched_count = debug_result.single()["enriched"]
                print(f"   Total enriched requirements: {enriched_count}")
                
                # Check complexity distribution
                complexity_query = f"""
                MATCH (r:`{workspace}`)
                WHERE r.entity_type = 'requirement'
                  AND r.has_workload_metric = true
                RETURN 
                  min(r.complexity_score) AS min_complexity,
                  max(r.complexity_score) AS max_complexity,
                  avg(r.complexity_score) AS avg_complexity
                """
                complexity_result = session.run(complexity_query)
                stats = complexity_result.single()
                print(f"   Complexity range: {stats['min_complexity']}-{stats['max_complexity']} (avg: {stats['avg_complexity']:.1f})")
                
                return False
            
            # Display results
            for i, record in enumerate(records, 1):
                print(f"\n{i}. {record['requirement']}")
                print(f"   Complexity: {record['complexity']}/10")
                print(f"   Rationale: {record['rationale']}")
                
                # Parse workload categories (BOE)
                categories = json.loads(record['categories']) if record['categories'] else []
                print(f"   BOE Categories: {', '.join(categories)}")
                
                # Parse labor drivers (operational metrics: volumes, frequencies, hours)
                labor_drivers = json.loads(record['labor_drivers']) if record['labor_drivers'] else []
                if labor_drivers:
                    print(f"   Workload Metrics ({len(labor_drivers)}):")
                    for driver in labor_drivers[:3]:  # Show first 3
                        print(f"     • {driver}")
                    if len(labor_drivers) > 3:
                        print(f"     ... and {len(labor_drivers) - 3} more")
                
                # Parse material needs
                material_needs = json.loads(record['material_needs']) if record['material_needs'] else []
                if material_needs:
                    print(f"   Material Needs ({len(material_needs)}):")
                    for material in material_needs[:2]:
                        print(f"     • {material}")
                
                # Show confidence scores for top BOE categories
                boe_relevance = json.loads(record['confidence']) if record['confidence'] else {}
                top_categories = sorted(boe_relevance.items(), key=lambda x: x[1], reverse=True)[:3]
                print(f"   Top BOE Confidence: {', '.join([f'{cat}:{conf:.2f}' for cat, conf in top_categories])}")
                
                print(f"   Effort Estimate: {record['effort']}")
                
                if i < len(records):
                    print(f"\n{'─'*80}")
            
            print(f"\n{'='*80}")
            print("✅ Workload query test PASSED")
            print(f"{'='*80}\n")
            
            # Summary statistics
            avg_complexity = sum(r['complexity'] for r in records) / len(records)
            total_labor_drivers = sum(len(json.loads(r['labor_drivers']) if r['labor_drivers'] else []) for r in records)
            
            print("\n📈 Summary Statistics:")
            print(f"   Requirements analyzed: {len(records)}")
            print(f"   Average complexity: {avg_complexity:.1f}/10")
            print(f"   Total labor drivers extracted: {total_labor_drivers}")
            print(f"   Avg drivers per requirement: {total_labor_drivers / len(records):.1f}")
            
            return True
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False
    
    finally:
        driver.close()


if __name__ == "__main__":
    success = test_workload_query()
    exit(0 if success else 1)
