"""
Neo4j Knowledge Graph I/O Operations

Handles reading and writing to Neo4j database for the knowledge graph.
Provides clean interfaces for semantic relationship inference and post-processing.
"""

import os
import logging
from typing import List, Dict, Tuple
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


class Neo4jGraphIO:
    """Neo4j graph I/O operations for semantic post-processing"""
    
    def __init__(self):
        """Initialize Neo4j connection from environment variables"""
        self.uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
        self.username = os.getenv("NEO4J_USERNAME", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        self.workspace = os.getenv("NEO4J_WORKSPACE", "default")
        
        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def get_all_entities(self) -> List[Dict]:
        """
        Fetch all entities from Neo4j workspace.
        
        Returns:
            List of entity dicts with keys: id, entity_name, entity_type, description
        """
        query = f"""
        MATCH (n:`{self.workspace}`)
        RETURN elementId(n) as id,
               n.entity_id as entity_name,
               n.entity_type as entity_type,
               n.description as description,
               n.source_id as source_id
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            entities = []
            for record in result:
                entities.append({
                    'id': record['id'],
                    'entity_name': record['entity_name'],
                    'entity_type': record['entity_type'],
                    'description': record['description'],
                    'source_id': record['source_id']
                })
            
            logger.info(f"  📊 Fetched {len(entities)} entities from Neo4j")
            return entities
    
    def get_all_relationships(self) -> List[Dict]:
        """
        Fetch all relationships from Neo4j workspace.
        
        Returns:
            List of relationship dicts with keys: source, target, type, weight, description
        """
        query = f"""
        MATCH (a:`{self.workspace}`)-[r]->(b:`{self.workspace}`)
        RETURN elementId(a) as source,
               elementId(b) as target,
               type(r) as rel_type,
               r.weight as weight,
               r.description as description,
               r.keywords as keywords
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            relationships = []
            for record in result:
                relationships.append({
                    'source': record['source'],
                    'target': record['target'],
                    'type': record['rel_type'],
                    'weight': record['weight'],
                    'description': record['description'],
                    'keywords': record['keywords']
                })
            
            logger.info(f"  📊 Fetched {len(relationships)} relationships from Neo4j")
            return relationships
    
    def get_orphaned_entity_ids(self) -> List[str]:
        """
        Find entities that have no relationships (true orphans).
        
        Returns:
            List of entity_name values for entities with no incoming or outgoing relationships
        """
        query = f"""
        MATCH (n:`{self.workspace}`)
        WHERE NOT (n)-[]-()
        RETURN n.entity_id as entity_name
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            orphan_names = [record['entity_name'] for record in result]
            if orphan_names:
                logger.info(f"  📊 Found {len(orphan_names)} truly orphaned entities in Neo4j")
            return orphan_names
    
    def update_entity_types(self, entity_updates: List[Dict]) -> int:
        """
        Update entity types in Neo4j.
        
        Args:
            entity_updates: List of dicts with 'id' and 'new_entity_type' keys
            
        Returns:
            Number of entities updated
        """
        query = f"""
        UNWIND $updates AS update
        MATCH (n:`{self.workspace}`)
        WHERE elementId(n) = update.id
        SET n.entity_type = update.new_entity_type,
            n.old_entity_type = n.entity_type,
            n.corrected_by = 'semantic_post_processor',
            n.corrected_at = datetime()
        RETURN count(n) as updated_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, updates=entity_updates)
            record = result.single()
            count = record['updated_count'] if record else 0
            
            logger.info(f"  ✅ Updated {count} entity types in Neo4j")
            return count
    
    def update_entity_properties(self, property_updates: List[Dict]) -> int:
        """
        Update entity properties in Neo4j (for workload metadata enrichment).
        
        Args:
            property_updates: List of dicts with 'id' and 'properties' keys
                - id: Entity elementId
                - properties: Dict of property_name → property_value
                
        Returns:
            Number of entities updated
        """
        query = f"""
        UNWIND $updates AS update
        MATCH (n:`{self.workspace}`)
        WHERE elementId(n) = update.id
        SET n += update.properties,
            n.enriched_by = 'workload_metadata_enrichment',
            n.enriched_at = datetime()
        RETURN count(n) as updated_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, updates=property_updates)
            record = result.single()
            count = record['updated_count'] if record else 0
            
            logger.info(f"  ✅ Updated {count} entities with new properties in Neo4j")
            return count
    
    def create_relationships(self, new_relationships: List[Dict]) -> int:
        """
        Create new relationships in Neo4j.
        
        Args:
            new_relationships: List of relationship dicts with keys:
                - source_id: Entity ID for source node (elementId)
                - target_id: Entity ID for target node (elementId)
                - relationship_type: Type of relationship
                - reasoning: Human-readable explanation
                - confidence: Optional confidence score (0.0-1.0)
                
        Returns:
            Number of relationships created
        """
        # Filter out relationships with missing/null/empty relationship_type
        # (prevents Neo4j ClientError: cannot merge relationship with null type)
        valid_relationships = []
        rejected_relationships = []
        
        for rel in new_relationships:
            rel_type = rel.get('relationship_type')
            if not rel_type or (isinstance(rel_type, str) and not rel_type.strip()):
                rejected_relationships.append(rel)
                continue
            valid_relationships.append(rel)
        
        # CRITICAL: Log rejected relationships for data loss visibility
        if rejected_relationships:
            logger.error("=" * 80)
            logger.error("❌ CRITICAL: REJECTED MALFORMED RELATIONSHIPS (DATA LOSS)")
            logger.error("=" * 80)
            logger.error(f"Rejected {len(rejected_relationships)} of {len(new_relationships)} relationships due to null/empty 'relationship_type'")
            logger.error("")
            logger.error("REJECTED RELATIONSHIPS:")
            for i, rel in enumerate(rejected_relationships, 1):
                logger.error(f"  [{i}] Source: {rel.get('source_id', 'MISSING')}")
                logger.error(f"      Target: {rel.get('target_id', 'MISSING')}")
                logger.error(f"      Type:   {repr(rel.get('relationship_type', 'MISSING'))}")
                logger.error(f"      Reason: {rel.get('reasoning', 'N/A')[:100]}")
                logger.error(f"      Full:   {rel}")
                logger.error("")
            logger.error("=" * 80)
            logger.error("⚠️  INVESTIGATE: Check inference algorithms for null type generation")
            logger.error("=" * 80)
        
        if not valid_relationships:
            logger.info("  💾 No valid relationships to create")
            return 0
        
        # Neo4j doesn't allow dynamic relationship types in pure Cypher
        # We need to use APOC or create with a property
        # Only include confidence if present (trust LLM quality like LightRAG)
        query = f"""
        UNWIND $relationships AS rel
        MATCH (source:`{self.workspace}`)
        WHERE elementId(source) = rel.source_id
        MATCH (target:`{self.workspace}`)
        WHERE elementId(target) = rel.target_id
        MERGE (source)-[r:INFERRED_RELATIONSHIP {{
            type: rel.relationship_type,
            reasoning: rel.reasoning,
            source: 'semantic_post_processor',
            created_at: datetime()
        }}]->(target)
        SET r.confidence = CASE WHEN rel.confidence IS NOT NULL THEN rel.confidence ELSE r.confidence END
        RETURN count(r) as created_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, relationships=valid_relationships)
            record = result.single()
            count = record['created_count'] if record else 0
            
            logger.info(f"  💾 Created {count} new relationships in Neo4j")
            return count
    
    def enrich_entity_metadata(self, metadata_updates: List[Dict]) -> int:
        """
        Add metadata properties to entities in Neo4j.
        
        Args:
            metadata_updates: List of dicts with 'id' and metadata properties
            
        Returns:
            Number of entities enriched
        """
        query = f"""
        UNWIND $updates AS update
        MATCH (n:`{self.workspace}`)
        WHERE elementId(n) = update.id
        SET n += update.metadata,
            n.metadata_updated_by = 'semantic_post_processor',
            n.metadata_updated_at = datetime()
        RETURN count(n) as enriched_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, updates=metadata_updates)
            record = result.single()
            count = record['enriched_count'] if record else 0
            
            logger.info(f"  ✅ Enriched {count} entities with metadata in Neo4j")
            return count
    
    def get_entity_count_by_type(self) -> Dict[str, int]:
        """
        Get count of entities by type.
        
        Returns:
            Dict mapping entity_type to count
        """
        query = f"""
        MATCH (n:`{self.workspace}`)
        WHERE n.entity_type IS NOT NULL
        RETURN n.entity_type as type, count(n) as count
        ORDER BY count DESC
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            type_counts = {}
            for record in result:
                type_counts[record['type']] = record['count']
            
            return type_counts
    
    def get_relationship_count_by_type(self) -> Dict[str, int]:
        """
        Get count of relationships by type.
        
        Returns:
            Dict mapping relationship_type to count
        """
        query = f"""
        MATCH (a:`{self.workspace}`)-[r]->(b:`{self.workspace}`)
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            type_counts = {}
            for record in result:
                type_counts[record['type']] = record['count']
            
            return type_counts
    
    def create_entities(self, entities: List[Dict]) -> int:
        """
        Create new entities in Neo4j.
        
        Args:
            entities: List of entity dicts (from LightRAG native extraction)
        
        Returns:
            Number of entities created
        """
        # Filter out any entities that might have slipped through with None names
        # Note: LightRAG native extraction handles this, but this is a safety net.
        valid_entities = []
        for e in entities:
            if e.get('entity_name'):
                valid_entities.append(e)
            else:
                # This should rarely happen with native LightRAG extraction
                logger.error(f"❌ Critical Error: Entity reached Neo4j without a name! Dropping to prevent DB corruption. Entity: {e}")
        
        if len(valid_entities) < len(entities):
            logger.warning(f"⚠️ Skipped {len(entities) - len(valid_entities)} entities with missing names in Neo4j creation")
        
        # Note: We use MERGE on entity_name to avoid duplicates
        query = f"""
        UNWIND $entities AS entity
        MERGE (n:`{self.workspace}` {{entity_name: entity.entity_name}})
        SET n.entity_type = entity.entity_type,
            n.created_by = 'lightrag_native',
            n.created_at = datetime()
        
        // Set specific properties based on type
        FOREACH (_ IN CASE WHEN entity.entity_type = 'requirement' THEN [1] ELSE [] END |
            SET n.criticality = entity.criticality,
                n.modal_verb = entity.modal_verb,
                n.req_type = entity.req_type,
                n.labor_drivers = entity.labor_drivers,
                n.material_needs = entity.material_needs
        )
        FOREACH (_ IN CASE WHEN entity.entity_type = 'evaluation_factor' THEN [1] ELSE [] END |
            SET n.weight = entity.weight,
                n.importance = entity.importance,
                n.subfactors = entity.subfactors
        )
        FOREACH (_ IN CASE WHEN entity.entity_type = 'submission_instruction' THEN [1] ELSE [] END |
            SET n.page_limit = entity.page_limit,
                n.format_reqs = entity.format_reqs,
                n.volume = entity.volume
        )
        FOREACH (_ IN CASE WHEN entity.entity_type = 'clause' THEN [1] ELSE [] END |
            SET n.clause_number = entity.clause_number,
                n.regulation = entity.regulation
        )
        FOREACH (_ IN CASE WHEN entity.entity_type = 'performance_metric' THEN [1] ELSE [] END |
            SET n.threshold = entity.threshold,
                n.measurement_method = entity.measurement_method
        )
        FOREACH (_ IN CASE WHEN entity.entity_type = 'strategic_theme' THEN [1] ELSE [] END |
            SET n.theme_type = entity.theme_type
        )
        
        RETURN count(n) as created_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, entities=entities)
            record = result.single()
            count = record['created_count'] if record else 0
            
            logger.info(f"  💾 Created/Merged {count} entities in Neo4j")
            return count

    def create_typed_relationships(self, relationships: List[Dict]) -> int:
        """
        Create typed relationships in Neo4j using APOC for dynamic types.
        
        Args:
            relationships: List of dicts with source_entity, target_entity, relationship_type, description
        """
        query = f"""
        UNWIND $relationships AS rel
        MATCH (source:`{self.workspace}` {{entity_name: rel.source_entity}})
        MATCH (target:`{self.workspace}` {{entity_name: rel.target_entity}})
        CALL apoc.create.relationship(source, rel.relationship_type, {{
            description: rel.relationship_type,
            source: 'lightrag_native',
            created_at: datetime()
        }}, target) YIELD rel as r
        RETURN count(r) as created_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, relationships=relationships)
            record = result.single()
            count = record['created_count'] if record else 0
            
            logger.info(f"  💾 Created {count} typed relationships in Neo4j")
            return count


def group_entities_by_type(entities: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Group entities by type for efficient batching.
    
    Args:
        entities: List of entity dicts with 'entity_type' key
        
    Returns:
        Dict mapping entity_type (lowercase) to list of entities
    """
    grouped = {}
    for entity in entities:
        entity_type = entity.get('entity_type', '').lower()
        if entity_type not in grouped:
            grouped[entity_type] = []
        grouped[entity_type].append(entity)
    
    return grouped
