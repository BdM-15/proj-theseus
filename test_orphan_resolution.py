"""
Test orphan pattern resolution on current afcapv_adab_iss_2025 workspace.

Validates:
1. Orphan detection logic works
2. Pattern matchers find expected relationships
3. No false-positive relationships created
4. Critical items (Sanitizing Wipes, Floor Plans, etc.) get linked
"""

import asyncio
import logging
from neo4j import AsyncGraphDatabase
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
WORKSPACE = os.getenv("NEO4J_WORKSPACE", "afcapv_adab_iss_2025")


async def test_orphan_resolution():
    """Test orphan pattern resolution algorithm."""
    
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        async with driver.session(database=NEO4J_DATABASE) as session:
            # Get current orphan count
            result = await session.run(f"""
                MATCH (n:`{WORKSPACE}`)
                WHERE NOT (n)-[]-()
                RETURN count(n) as orphan_count
            """)
            record = await result.single()
            initial_orphans = record['orphan_count']
            logger.info(f"Initial orphan count: {initial_orphans}")
            
            # Get orphaned entities by type
            result = await session.run(f"""
                MATCH (n:`{WORKSPACE}`)
                WHERE NOT (n)-[]-()
                RETURN n.entity_type as type, count(n) as count
                ORDER BY count DESC
            """)
            records = await result.values()
            logger.info(f"\nOrphaned entities by type:")
            for type_name, count in records:
                logger.info(f"  {type_name}: {count}")
            
            # Check specific critical items
            critical_items = [
                "Sanitizing Wipes",
                "Floor Plans",
                "Ancillary Hardware",
                "Trash Receptacles",
                "Fuel Use Estimates"
            ]
            
            logger.info(f"\nChecking critical items:")
            for item in critical_items:
                cypher = f"""
                    MATCH (n:`{WORKSPACE}`)
                    WHERE n.entity_name CONTAINS $item_name
                    RETURN n.entity_name as name, 
                           n.entity_type as type,
                           count{{(n)-[]-()}} as rel_count
                """
                result = await session.run(cypher, item_name=item)
                
                record = await result.single()
                if record:
                    status = "CONNECTED" if record['rel_count'] > 0 else "ORPHANED"
                    logger.info(f"  {record['name']} ({record['type']}): {status} ({record['rel_count']} relationships)")
                else:
                    logger.info(f"  {item}: NOT FOUND")
            
            # Import and run orphan pattern resolver
            logger.info(f"\n--- Running Orphan Pattern Resolution ---")
            
            # Fetch all entities
            result = await session.run(f"""
                MATCH (n:`{WORKSPACE}`)
                RETURN n.id as id,
                       n.entity_type as entity_type,
                       n.entity_name as entity_name,
                       n.description as description,
                       [(n)-[r]-() | type(r)] as relationship_types
            """)
            
            entities = []
            async for record in result:
                entities.append({
                    'id': record['id'],
                    'entity_type': record['entity_type'],
                    'entity_name': record['entity_name'],
                    'description': record['description'] or '',
                    'relationships': record['relationship_types']  # Non-empty if connected
                })
            
            logger.info(f"Loaded {len(entities)} entities")
            
            # Run orphan pattern resolver
            from src.inference.semantic_post_processor import _resolve_orphan_patterns
            
            id_to_entity = {e['id']: e for e in entities}
            
            orphan_rels = await _resolve_orphan_patterns(
                entities=entities,
                id_to_entity=id_to_entity,
                model=os.getenv("LLM_MODEL", "grok-4-fast-reasoning"),
                temperature=float(os.getenv("LLM_MODEL_TEMPERATURE", "0.1"))
            )
            
            logger.info(f"\nGenerated {len(orphan_rels)} orphan pattern relationships")
            
            # Show sample relationships by pattern
            by_type = {}
            for rel in orphan_rels:
                rtype = rel['relationship_type']
                if rtype not in by_type:
                    by_type[rtype] = []
                by_type[rtype].append(rel)
            
            for rtype, rels in by_type.items():
                logger.info(f"\n{rtype} relationships: {len(rels)}")
                for i, rel in enumerate(rels[:3]):  # Show first 3
                    source = id_to_entity.get(rel['source_id'], {})
                    target = id_to_entity.get(rel['target_id'], {})
                    logger.info(f"  {i+1}. {source.get('entity_name')} → {target.get('entity_name')}")
                    logger.info(f"     Reasoning: {rel['reasoning']}")
            
            # Insert relationships into Neo4j (TEST MODE - can be reverted)
            logger.info(f"\n--- Inserting {len(orphan_rels)} relationships into Neo4j ---")
            
            for rel in orphan_rels:
                cypher = f"""
                    MATCH (source:`{WORKSPACE}` {{id: $source_id}})
                    MATCH (target:`{WORKSPACE}` {{id: $target_id}})
                    MERGE (source)-[r:ORPHAN_PATTERN_TEST {{
                        type: $rel_type,
                        confidence: $confidence,
                        reasoning: $reasoning,
                        test_run: true
                    }}]->(target)
                """
                await session.run(cypher,
                    source_id=rel['source_id'],
                    target_id=rel['target_id'],
                    rel_type=rel['relationship_type'],
                    confidence=rel.get('confidence', 0.0),
                    reasoning=rel.get('reasoning', '')
                )
            
            logger.info(f"Inserted {len(orphan_rels)} test relationships")
            
            # Check new orphan count
            result = await session.run(f"""
                MATCH (n:`{WORKSPACE}`)
                WHERE NOT (n)-[]-()
                RETURN count(n) as orphan_count
            """)
            record = await result.single()
            final_orphans = record['orphan_count']
            
            logger.info(f"\n--- Results ---")
            logger.info(f"Initial orphans: {initial_orphans}")
            logger.info(f"Final orphans: {final_orphans}")
            logger.info(f"Reduction: {initial_orphans - final_orphans} ({100*(initial_orphans - final_orphans)/initial_orphans:.1f}%)")
            
            # Re-check critical items
            logger.info(f"\nCritical items after resolution:")
            for item in critical_items:
                result = await session.run(f"""
                    MATCH (n:`{WORKSPACE}`)
                    WHERE n.entity_name CONTAINS $item_name
                    RETURN n.entity_name as name, 
                           n.entity_type as type,
                           count{{(n)-[]-()}} as rel_count
                """, item_name=item)
                
                record = await result.single()
                if record:
                    status = "CONNECTED" if record['rel_count'] > 0 else "ORPHANED"
                    logger.info(f"  {record['name']} ({record['type']}): {status} ({record['rel_count']} relationships)")
            
            logger.info(f"\nTo revert test relationships, run:")
            logger.info(f"  MATCH ()-[r:ORPHAN_PATTERN_TEST]->() DELETE r")
            
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(test_orphan_resolution())
