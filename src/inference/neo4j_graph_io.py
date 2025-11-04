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
               n.description as description
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            entities = []
            for record in result:
                entities.append({
                    'id': record['id'],
                    'entity_name': record['entity_name'],
                    'entity_type': record['entity_type'],
                    'description': record['description']
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
    
    def create_relationships(self, new_relationships: List[Dict]) -> int:
        """
        Create new relationships in Neo4j.
        
        Args:
            new_relationships: List of relationship dicts with keys:
                - source_id: Entity ID for source node (elementId)
                - target_id: Entity ID for target node (elementId)
                - relationship_type: Type of relationship
                - confidence: Confidence score (0.0-1.0)
                - reasoning: Human-readable explanation
                
        Returns:
            Number of relationships created
        """
        # Neo4j doesn't allow dynamic relationship types in pure Cypher
        # We need to use APOC or create with a property
        query = f"""
        UNWIND $relationships AS rel
        MATCH (source:`{self.workspace}`)
        WHERE elementId(source) = rel.source_id
        MATCH (target:`{self.workspace}`)
        WHERE elementId(target) = rel.target_id
        MERGE (source)-[r:INFERRED_RELATIONSHIP {{
            type: rel.relationship_type,
            confidence: rel.confidence,
            reasoning: rel.reasoning,
            source: 'semantic_post_processor',
            created_at: datetime()
        }}]->(target)
        RETURN count(r) as created_count
        """
        
        with self.driver.session(database=self.database) as session:
            result = session.run(query, relationships=new_relationships)
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
