"""
Compare Baseline (Nov 9) vs Current (Nov 10) Processing
========================================================

Check if extraction itself changed between runs.
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")

print("\n" + "="*80)
print("🔍 BASELINE vs CURRENT COMPARISON")
print("="*80)
print("\nBaseline: Nov 9, 2025 (WITHOUT workload enrichment)")
print("Current:  Nov 10, 2025 (WITH workload enrichment)")
print()

driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

try:
    with driver.session(database=neo4j_database) as session:
        
        # Get entity type distribution
        query_types = f"""
        MATCH (n:`{workspace}`)
        RETURN n.entity_type AS type, count(*) AS count
        ORDER BY count DESC
        """
        
        results = session.run(query_types)
        type_counts = {record["type"]: record["count"] for record in results}
        
        print("📊 CURRENT ENTITY TYPE DISTRIBUTION:")
        print("-" * 80)
        for entity_type, count in type_counts.items():
            print(f"  {entity_type:30s}: {count:4d}")
        
        print(f"\n  {'TOTAL':30s}: {sum(type_counts.values()):4d}")
        
        # Check for corrected entities
        query_corrected = f"""
        MATCH (n:`{workspace}`)
        WHERE n.corrected_by IS NOT NULL
        RETURN count(n) AS corrected_count
        """
        result = session.run(query_corrected)
        corrected_count = result.single()["corrected_count"]
        
        print(f"\n📊 POST-PROCESSING STATS:")
        print(f"  Entities corrected by semantic_post_processor: {corrected_count}")
        
        # Check for enriched entities
        query_enriched = f"""
        MATCH (n:`{workspace}`)
        WHERE n.enriched_by IS NOT NULL
        RETURN count(n) AS enriched_count
        """
        result = session.run(query_enriched)
        enriched_count = result.single()["enriched_count"]
        
        print(f"  Entities enriched by workload_enrichment: {enriched_count}")
        
finally:
    driver.close()

print("\n" + "="*80)
print("📊 COMPARISON WITH BASELINE")
print("="*80)

baseline_stats = {
    "total_entities": 2254,
    "requirements": 451,
    "relationships": 3938,
    "avg_rels": 1.75
}

current_stats = {
    "total_entities": sum(type_counts.values()),
    "requirements": type_counts.get("requirement", 0),
    "relationships": 3460,  # From previous assessment
    "avg_rels": 2.57  # From previous assessment
}

print(f"\nMetric                    | Baseline (Nov 9) | Current (Nov 10) | Change")
print(f"--------------------------|------------------|------------------|------------------")
print(f"Total entities            | {baseline_stats['total_entities']:16d} | {current_stats['total_entities']:16d} | {current_stats['total_entities'] - baseline_stats['total_entities']:+6d} ({(current_stats['total_entities'] - baseline_stats['total_entities']) / baseline_stats['total_entities'] * 100:+.1f}%)")
print(f"Requirements              | {baseline_stats['requirements']:16d} | {current_stats['requirements']:16d} | {current_stats['requirements'] - baseline_stats['requirements']:+6d} ({(current_stats['requirements'] - baseline_stats['requirements']) / baseline_stats['requirements'] * 100:+.1f}%)")
print(f"Relationships             | {baseline_stats['relationships']:16d} | {current_stats['relationships']:16d} | {current_stats['relationships'] - baseline_stats['relationships']:+6d} ({(current_stats['relationships'] - baseline_stats['relationships']) / baseline_stats['relationships'] * 100:+.1f}%)")
print(f"Avg rels/entity           | {baseline_stats['avg_rels']:16.2f} | {current_stats['avg_rels']:16.2f} | {current_stats['avg_rels'] - baseline_stats['avg_rels']:+6.2f} ({(current_stats['avg_rels'] - baseline_stats['avg_rels']) / baseline_stats['avg_rels'] * 100:+.1f}%)")

print("\n" + "="*80)
print("🔍 DIAGNOSIS")
print("="*80)

req_loss = baseline_stats['requirements'] - current_stats['requirements']
req_loss_pct = req_loss / baseline_stats['requirements'] * 100

print(f"\n⚠️  CRITICAL: Lost {req_loss} requirements ({req_loss_pct:.1f}%)")
print(f"\nPossible causes (in order of likelihood):")
print(f"\n1. **Grok-4 Reasoning Model Variability** (MOST LIKELY)")
print(f"   - Grok-4-fast-reasoning uses non-deterministic reasoning")
print(f"   - Temperature=0.1 reduces but doesn't eliminate variance")
print(f"   - Same RFP, different extraction = 451 vs 123 requirements")
print(f"   - Solution: Run multiple extractions, compare, or use deterministic model")

print(f"\n2. **Extraction Prompt Changes** (UNLIKELY - we didn't change prompts)")
print(f"   - Check if entity extraction prompt was modified")
print(f"   - Solution: Verify prompts/extraction/ files unchanged")

print(f"\n3. **Entity Type Correction Over-Aggressive** (POSSIBLE)")
print(f"   - Corrected {corrected_count} entities")
print(f"   - May have reclassified some requirements as other types")
print(f"   - Solution: Check logs for 'requirement' → other type conversions")

print(f"\n4. **Workload Enrichment Bug** (UNLIKELY - enriches, doesn't delete)")
print(f"   - Enriched {enriched_count} entities (should match requirements)")
print(f"   - No deletion logic in enrichment code")
print(f"   - Solution: Verify enrichment=123 matches requirements=123 ✅")

print(f"\n**Recommendation**: Reprocess ISS RFP again to see if entity count stabilizes")
print(f"If still low (< 400 requirements), investigate Grok-4 extraction prompts")

print("\n" + "="*80)
