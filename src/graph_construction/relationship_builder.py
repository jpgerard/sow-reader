"""
Enhanced relationship builder for Neo4j graph construction.
"""

import logging
from typing import List, Dict, Any, Optional
import numpy as np
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RelationshipConfig:
    """Configuration for relationship building."""
    similarity_threshold: float = 0.7
    max_relationships_per_node: int = 50
    community_size_threshold: int = 100
    use_entity_relationships: bool = True
    use_community_detection: bool = True

class EnhancedRelationshipBuilder:
    """Build enhanced relationships between chunks using multiple signals."""
    
    def __init__(self, 
                 uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "password",
                 config: Optional[RelationshipConfig] = None):
        """Initialize the relationship builder.
        
        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            config: Relationship configuration
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.config = config or RelationshipConfig()
        
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        
    def build_relationships(self):
        """Build all relationship types."""
        with self.driver.session() as session:
            # Clear existing relationships
            logger.info("Clearing existing relationships...")
            session.run("MATCH ()-[r]->() DELETE r")
            
            # Build different relationship types
            self._build_similarity_relationships(session)
            self._build_sequential_relationships(session)
            
            if self.config.use_entity_relationships:
                self._build_entity_relationships(session)
            
            if self.config.use_community_detection:
                self._detect_communities(session)
            
            # Get relationship statistics
            stats = session.run("""
                MATCH ()-[r]->()
                WITH type(r) as rel_type, count(*) as count
                RETURN rel_type, count ORDER BY count DESC
            """).data()
            
            logger.info("Relationship counts:")
            for stat in stats:
                logger.info(f"  {stat['rel_type']}: {stat['count']}")
                
    def _build_similarity_relationships(self, session):
        """Build relationships based on embedding similarity."""
        logger.info("Building similarity relationships...")
        
        # Use vector index for efficient similarity search
        result = session.run("""
            CALL db.index.vector.queryNodes(
                'chunk_embeddings',
                $k,
                $threshold
            ) YIELD node, score
            WITH node, score WHERE score >= $threshold
            MERGE (node)-[:SIMILAR_TO {score: score}]->(other)
        """, {
            "k": self.config.max_relationships_per_node,
            "threshold": self.config.similarity_threshold
        })
        
        logger.info(f"Created {result.consume().counters.relationships_created} similarity relationships")
        
    def _build_sequential_relationships(self, session):
        """Build sequential relationships within documents."""
        logger.info("Building sequential relationships...")
        
        result = session.run("""
            MATCH (c1:Chunk)
            WHERE c1.source IS NOT NULL
            WITH c1.source as source, collect(c1) as chunks
            UNWIND range(0, size(chunks)-2) as i
            WITH chunks[i] as current, chunks[i+1] as next, i as position
            WHERE current.source = next.source
            MERGE (current)-[:NEXT {position: position}]->(next)
        """)
        
        logger.info(f"Created {result.consume().counters.relationships_created} sequential relationships")
        
    def _build_entity_relationships(self, session):
        """Build relationships through shared entities."""
        logger.info("Building entity-based relationships...")
        
        # Connect chunks that mention same entities
        result = session.run("""
            MATCH (c1:Chunk)-[:MENTIONS]->(e:Entity)<-[:MENTIONS]-(c2:Chunk)
            WHERE id(c1) < id(c2)
            WITH c1, c2, count(e) as shared_entities
            WHERE shared_entities >= 2
            MERGE (c1)-[:SHARES_ENTITIES {count: shared_entities}]->(c2)
        """)
        
        logger.info(f"Created {result.consume().counters.relationships_created} entity relationships")
        
        # Create entity-entity relationships
        result = session.run("""
            MATCH (e1:Entity)<-[:MENTIONS]-(c:Chunk)-[:MENTIONS]->(e2:Entity)
            WHERE id(e1) < id(e2)
            WITH e1, e2, count(c) as cooccurrences
            WHERE cooccurrences >= 2
            MERGE (e1)-[:RELATED_TO {weight: cooccurrences}]->(e2)
        """)
        
        logger.info(f"Created {result.consume().counters.relationships_created} entity-entity relationships")
        
    def _detect_communities(self, session):
        """Detect and label communities in the graph."""
        logger.info("Detecting communities...")
        
        try:
            # Project graph for community detection
            session.run("""
                CALL gds.graph.project(
                    'chunk_graph',
                    ['Chunk'],
                    {
                        SIMILAR_TO: {
                            type: 'SIMILAR_TO',
                            properties: ['score'],
                            orientation: 'UNDIRECTED'
                        },
                        SHARES_ENTITIES: {
                            type: 'SHARES_ENTITIES',
                            properties: ['count'],
                            orientation: 'UNDIRECTED'
                        }
                    }
                )
            """)
            
            # Run Louvain community detection
            result = session.run("""
                CALL gds.louvain.write('chunk_graph', {
                    writeProperty: 'community',
                    relationshipWeightProperty: 'score',
                    maxLevels: 10,
                    maxIterations: 10
                })
                YIELD communityCount, modularity
                RETURN communityCount, modularity
            """).single()
            
            logger.info(
                f"Detected {result['communityCount']} communities "
                f"with modularity {result['modularity']:.3f}"
            )
            
            # Clean up projected graph
            session.run("CALL gds.graph.drop('chunk_graph')")
            
        except Neo4jError as e:
            logger.error(f"Error in community detection: {str(e)}")
            
    def analyze_graph(self) -> Dict[str, Any]:
        """Analyze the constructed graph.
        
        Returns:
            Dictionary of graph metrics
        """
        with self.driver.session() as session:
            # Basic statistics
            basic_stats = session.run("""
                MATCH (c:Chunk)
                OPTIONAL MATCH (c)-[r]->()
                WITH count(DISTINCT c) as nodes,
                     count(DISTINCT r) as relationships,
                     avg(size((c)-->()))as avg_degree
                RETURN nodes, relationships, avg_degree
            """).single()
            
            # Community statistics
            community_stats = session.run("""
                MATCH (c:Chunk)
                WHERE c.community IS NOT NULL
                WITH c.community as community, count(*) as size
                ORDER BY size DESC
                RETURN collect({
                    community: community,
                    size: size
                }) as communities
            """).single()["communities"]
            
            # Entity statistics
            entity_stats = session.run("""
                MATCH (e:Entity)
                OPTIONAL MATCH (e)<-[:MENTIONS]-(c:Chunk)
                WITH e.label as label,
                     count(DISTINCT e) as count,
                     avg(size((e)<--(:Chunk))) as avg_mentions
                ORDER BY count DESC
                RETURN collect({
                    label: label,
                    count: count,
                    avg_mentions: avg_mentions
                }) as entities
            """).single()["entities"]
            
            return {
                "basic_stats": {
                    "nodes": basic_stats["nodes"],
                    "relationships": basic_stats["relationships"],
                    "avg_degree": basic_stats["avg_degree"]
                },
                "community_stats": community_stats,
                "entity_stats": entity_stats
            }

def main():
    """Main function for testing."""
    logging.basicConfig(level=logging.INFO)
    
    config = RelationshipConfig(
        similarity_threshold=0.7,
        max_relationships_per_node=50,
        community_size_threshold=100,
        use_entity_relationships=True,
        use_community_detection=True
    )
    
    try:
        builder = EnhancedRelationshipBuilder(config=config)
        builder.build_relationships()
        
        # Analyze results
        analysis = builder.analyze_graph()
        logger.info("\nGraph Analysis:")
        logger.info(f"Nodes: {analysis['basic_stats']['nodes']}")
        logger.info(f"Relationships: {analysis['basic_stats']['relationships']}")
        logger.info(f"Avg Degree: {analysis['basic_stats']['avg_degree']:.2f}")
        
        logger.info("\nTop Communities:")
        for comm in analysis['community_stats'][:5]:
            logger.info(f"Community {comm['community']}: {comm['size']} nodes")
            
        logger.info("\nEntity Statistics:")
        for ent in analysis['entity_stats'][:5]:
            logger.info(
                f"{ent['label']}: {ent['count']} entities, "
                f"{ent['avg_mentions']:.1f} avg mentions"
            )
            
    finally:
        if 'builder' in locals():
            builder.close()

if __name__ == "__main__":
    main()
