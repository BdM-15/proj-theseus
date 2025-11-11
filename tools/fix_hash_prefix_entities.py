"""
Fix Hash-Prefixed Entity Types in Neo4j
=========================================

This script identifies and fixes entities with # prefix (e.g., #requirement, #document)
that slipped through semantic post-processing.

Root Cause: Entities with #-prefix on ALLOWED types (like #requirement) were not caught
because the post-processor only fixed UNKNOWN or FORBIDDEN types.

Fix Strategy:
1. Query Neo4j for all entities with types starting with #
2. Strip the # prefix if underlying type is in ALLOWED_TYPES
3. Update Neo4j labels and properties

Usage:
    python tools/fix_hash_prefix_entities.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment
load_dotenv()

# ALLOWED_TYPES from entity_operations.py
ALLOWED_TYPES = [
    "organization",
    "concept",
    "event",
    "technology",
    "person",
    "location",
    "requirement",
    "clause",
    "section",
    "document",
    "deliverable",
    "program",
    "equipment",
    "evaluation_factor",
    "submission_instruction",
    "strategic_theme",
    "statement_of_work",
]


def fix_hash_prefixed_entities():
    """Main function to fix hash-prefixed entities"""
    
    # Get Neo4j connection details
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "govcon-capture-2025")
    neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
    workspace = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")
    
    print("\n" + "="*80)
    print("🔧 FIXING HASH-PREFIXED ENTITY TYPES")
    print("="*80)
    print(f"  Workspace: {workspace}")
    print(f"  Database: {neo4j_database}")
    print()
    
    # Connect to Neo4j
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    try:
        with driver.session(database=neo4j_database) as session:
            
            # Step 1: Identify all hash-prefixed entity types
            print("📊 Step 1: Identifying hash-prefixed entities...")
            query_identify = f"""
            MATCH (n:`{workspace}`)
            WHERE n.entity_type STARTS WITH '#'
            RETURN DISTINCT n.entity_type AS corrupted_type, count(*) AS count
            ORDER BY count DESC
            """
            
            results = session.run(query_identify)
            corrupted_types = [(record["corrupted_type"], record["count"]) for record in results]
            
            if not corrupted_types:
                print("✅ No hash-prefixed entities found - database is clean!")
                return
            
            print(f"\n  Found {len(corrupted_types)} corrupted entity types:")
            total_entities = 0
            for corrupted_type, count in corrupted_types:
                print(f"    - {corrupted_type}: {count} entities")
                total_entities += count
            
            print(f"\n  Total corrupted entities: {total_entities}")
            
            # Step 2: Fix each corrupted type
            print("\n🔧 Step 2: Fixing corrupted entity types...")
            fixed_count = 0
            skipped_count = 0
            
            for corrupted_type, count in corrupted_types:
                # Strip # prefix
                clean_type = corrupted_type[1:].lower()
                
                # Check if underlying type is allowed
                if clean_type in ALLOWED_TYPES:
                    print(f"\n  Fixing: {corrupted_type} → {clean_type} ({count} entities)")
                    
                    # Update entity_type property and label
                    query_update = f"""
                    MATCH (n:`{workspace}`)
                    WHERE n.entity_type = $corrupted_type
                    SET n.entity_type = $clean_type
                    RETURN count(n) AS updated
                    """
                    
                    result = session.run(query_update, corrupted_type=corrupted_type, clean_type=clean_type)
                    updated = result.single()["updated"]
                    
                    print(f"    ✅ Updated {updated} entities")
                    fixed_count += updated
                    
                else:
                    print(f"\n  ⚠️  Skipping: {corrupted_type} → {clean_type} (not in ALLOWED_TYPES)")
                    print(f"      These need LLM inference to determine correct type")
                    skipped_count += count
            
            # Step 3: Verify fix
            print("\n📊 Step 3: Verifying fix...")
            query_verify = f"""
            MATCH (n:`{workspace}`)
            WHERE n.entity_type STARTS WITH '#'
            RETURN count(*) AS remaining
            """
            
            result = session.run(query_verify)
            remaining = result.single()["remaining"]
            
            print(f"\n  Entities remaining with # prefix: {remaining}")
            
            # Summary
            print("\n" + "="*80)
            print("✅ FIX COMPLETE")
            print("="*80)
            print(f"  Entities fixed:     {fixed_count}")
            print(f"  Entities skipped:   {skipped_count} (need LLM inference)")
            print(f"  Entities remaining: {remaining}")
            print("="*80)
            
            if skipped_count > 0:
                print("\n⚠️  WARNING: Some entities with # prefix could not be auto-fixed.")
                print("   Run semantic post-processing to infer correct types with LLM.")
            
    finally:
        driver.close()


if __name__ == "__main__":
    fix_hash_prefixed_entities()
