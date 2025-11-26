#!/usr/bin/env python3
"""
Fix govcon_table Entity Types in Neo4j

One-time cleanup script to fix the 40 govcon_table entities in 
afcapv_adab_iss_2025_main_production workspace.

Uses LLM to retype each entity based on its name/description.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

load_dotenv()

# Import canonical entity types from schema
from src.ontology.schema import VALID_ENTITY_TYPES

# Allowed types from schema.py (use canonical source)
ALLOWED_TYPES = list(VALID_ENTITY_TYPES)

def get_govcon_table_entities(workspace: str):
    """Fetch all govcon_table entities from Neo4j."""
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    query = f"""
    MATCH (n:`{workspace}`)
    WHERE n.entity_type = 'govcon_table'
    RETURN n.entity_name AS entity_name, 
           n.description AS description,
           n.entity_type AS entity_type
    """
    
    with driver.session(database=database) as session:
        result = session.run(query)
        entities = [dict(record) for record in result]
    
    driver.close()
    return entities


def update_entity_type(workspace: str, entity_name: str, new_type: str):
    """Update a single entity's type in Neo4j."""
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    query = f"""
    MATCH (n:`{workspace}` {{entity_name: $entity_name}})
    SET n.entity_type = $new_type,
        n.retyped_from = 'govcon_table',
        n.retyped_at = datetime()
    RETURN n.entity_name AS name
    """
    
    with driver.session(database=database) as session:
        result = session.run(query, entity_name=entity_name, new_type=new_type)
        record = result.single()
    
    driver.close()
    return record is not None


async def retype_with_llm(entity_name: str, description: str) -> str:
    """Use LLM to determine the correct entity type."""
    import instructor
    from pydantic import BaseModel
    
    os.environ["XAI_API_KEY"] = os.getenv("LLM_BINDING_API_KEY") or os.getenv("XAI_API_KEY")
    
    client = instructor.from_provider("xai/grok-4-fast-reasoning", async_client=True)
    
    class EntityTypeResult(BaseModel):
        entity_type: str
        reasoning: str
    
    prompt = f"""Determine the correct entity type for this government contracting entity.

ENTITY NAME: {entity_name}
DESCRIPTION: {description or 'No description available'}

ALLOWED TYPES (use EXACTLY one of these):
{', '.join(ALLOWED_TYPES)}

TYPE GUIDANCE:
- requirement: Obligations with shall/must/will/should/may
- performance_metric: Measurable thresholds, SLAs, KPIs
- deliverable: Contract deliverables, CDRLs, reports
- evaluation_factor: Scoring criteria from Section M
- equipment: Physical assets, hardware
- concept: Abstract ideas, processes, accounts
- document: Plans, policies, manuals, regulations
- section: RFP sections (A-M, attachments)

Return the single most appropriate entity type."""

    try:
        result = await client.chat.completions.create(
            model="grok-4-fast-reasoning",
            response_model=EntityTypeResult,
            messages=[
                {"role": "system", "content": "You classify government contracting entities. Return exactly one allowed type."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1
        )
        
        # Validate it's an allowed type
        if result.entity_type.lower() in [t.lower() for t in ALLOWED_TYPES]:
            return result.entity_type.lower()
        else:
            print(f"  ⚠️ LLM returned invalid type '{result.entity_type}', defaulting to 'concept'")
            return "concept"
            
    except Exception as e:
        print(f"  ❌ LLM error: {e}, defaulting to 'concept'")
        return "concept"


async def main():
    """Main cleanup function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix govcon_table entity types")
    parser.add_argument("--workspace", default="afcapv_adab_iss_2025_main_production",
                       help="Neo4j workspace label")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be done without making changes")
    args = parser.parse_args()
    
    print(f"\n🔧 Fixing govcon_table entities in workspace: {args.workspace}")
    print(f"   Mode: {'DRY RUN' if args.dry_run else 'LIVE UPDATE'}\n")
    
    # Get all govcon_table entities
    entities = get_govcon_table_entities(args.workspace)
    print(f"📊 Found {len(entities)} govcon_table entities to fix\n")
    
    if not entities:
        print("✅ No govcon_table entities found - nothing to fix!")
        return
    
    # Process each entity
    updated = 0
    type_counts = {}
    
    for i, entity in enumerate(entities, 1):
        name = entity.get("entity_name") or "Unknown"
        desc = entity.get("description") or ""
        
        print(f"[{i}/{len(entities)}] {name[:60]}...")
        
        # Get new type from LLM
        new_type = await retype_with_llm(name, desc)
        type_counts[new_type] = type_counts.get(new_type, 0) + 1
        
        print(f"  → {new_type}")
        
        if not args.dry_run:
            if update_entity_type(args.workspace, name, new_type):
                updated += 1
            else:
                print(f"  ❌ Failed to update")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"   Total entities: {len(entities)}")
    print(f"   {'Would update' if args.dry_run else 'Updated'}: {len(entities) if args.dry_run else updated}")
    print(f"\n   Type distribution after fix:")
    for t, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"     {t}: {count}")
    
    if args.dry_run:
        print(f"\n💡 Run without --dry-run to apply changes")


if __name__ == "__main__":
    asyncio.run(main())
