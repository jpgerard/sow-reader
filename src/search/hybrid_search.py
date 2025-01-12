"""
Enhanced hybrid search combining vector similarity, graph traversal, and entity awareness.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result with detailed scoring information."""
    chunk_id: str
    text: str
    source: str
    vector_score: float
    graph_score: float
    entity_score: float
    final_score: float
    entities: List[Dict[str, Any]]
    community: Optional[int] = None

@dataclass
class SearchConfig:
    """Configuration for hybrid search."""
    vector_weight: float = 0.4
    graph_weight: float = 0.3
    entity_weight: float = 0.3
    max_results: int = 5
    min_score: float = 0.1
    use_community_boost: bool = True
    community_boost_factor: float = 1.2
    use_pagerank: bool = True
    cache_results: bool = True
    cache_ttl_seconds: int = 3600

class HybridSearchEngine:
    """Enhanced search engine combining multiple ranking signals."""
    
    def __init__(self, 
                 embedding_model,
                 uri: str = "bolt://localhost:7687",
                 user: str = "neo4j",
                 password: str = "password",
                 config: Optional[SearchConfig] = None):
        """Initialize the search engine.
        
        Args:
            embedding_model: Model for generating query embeddings
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
            config: Search configuration
        """
        self.embedding_model = embedding_model
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.config = config or SearchConfig()
        
        # Initialize Neo4j procedures
        self._init_procedures()
        
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        
    def _init_procedures(self):
        """Initialize required Neo4j procedures and indexes."""
        with self.driver.session() as session:
            # Ensure vector index exists
            try:
                session.run("""
                    CALL db.index.vector.createNodeIndex(
                        'chunk_embeddings',
                        'Chunk',
                        'embedding',
                        768,
                        'cosine'
                    )
                """)
            except Neo4jError as e:
                if "An index with name" not in str(e):
                    raise
                    
            # Initialize PageRank if needed
            if self.config.use_pagerank:
                try:
                    session.run("""
                        CALL gds.graph.project(
                            'chunk_graph',
                            'Chunk',
                            {
                                SIMILAR_TO: {
                                    type: 'SIMILAR_TO',
                                    properties: ['score']
                                },
                                SHARES_ENTITIES: {
                                    type: 'SHARES_ENTITIES',
                                    properties: ['count']
                                }
                            }
                        )
                    """)
                    
                    session.run("""
                        CALL gds.pageRank.write('chunk_graph', {
                            writeProperty: 'pagerank'
                        })
                    """)
                except Neo4jError as e:
                    logger.warning(f"PageRank initialization failed: {str(e)}")
                finally:
                    try:
                        session.run("CALL gds.graph.drop('chunk_graph')")
                    except:
                        pass
                        
    def search(self, query: str) -> List[SearchResult]:
        """Perform hybrid search.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query)
        
        with self.driver.session() as session:
            # Complex hybrid search query
            result = session.run("""
                // Vector similarity search
                CALL db.index.vector.queryNodes('chunk_embeddings', $k, $query_embedding)
                YIELD node as chunk, score as vector_score
                
                // Get related chunks through graph traversal
                OPTIONAL MATCH path = (chunk)-[:SIMILAR_TO|SHARES_ENTITIES*1..2]-(related)
                WITH chunk, vector_score,
                     collect(DISTINCT related) as related_chunks,
                     collect(DISTINCT relationships(path)) as paths
                
                // Calculate graph-based score
                WITH chunk, vector_score, related_chunks,
                     reduce(s = 0.0,
                           rel IN [r IN REDUCE(rels = [], p IN paths | rels + p) |
                                 CASE type(r)
                                     WHEN 'SIMILAR_TO' THEN r.score
                                     WHEN 'SHARES_ENTITIES' THEN r.count / 10.0
                                     ELSE 0
                                 END
                           ] | s + rel) as graph_score
                
                // Get entities mentioned in the chunk
                OPTIONAL MATCH (chunk)-[m:MENTIONS]->(e:Entity)
                WITH chunk, vector_score, graph_score,
                     collect({
                         text: e.text,
                         label: e.label,
                         confidence: m.confidence
                     }) as entities
                
                // Calculate entity score based on relevance to query
                WITH chunk, vector_score, graph_score, entities,
                     reduce(s = 0.0,
                           e IN entities |
                           s + CASE
                               WHEN e.text IN $query_tokens THEN 1.0
                               ELSE 0.0
                           END) / (size(entities) + 0.1) as entity_score
                
                // Apply community boost if enabled
                WITH chunk, vector_score, graph_score, entity_score, entities,
                     CASE
                         WHEN chunk.community IS NOT NULL
                         THEN chunk.community
                         ELSE -1
                     END as community
                
                // Calculate final score with weights
                WITH chunk,
                     vector_score * $weights.vector +
                     graph_score * $weights.graph +
                     entity_score * $weights.entity as base_score,
                     vector_score, graph_score, entity_score,
                     entities, community
                
                // Apply community boost
                WITH chunk,
                     CASE
                         WHEN $use_community_boost AND community >= 0
                         THEN base_score * $community_boost
                         ELSE base_score
                     END as final_score,
                     vector_score, graph_score, entity_score,
                     entities, community
                
                WHERE final_score >= $min_score
                
                RETURN chunk.id as chunk_id,
                       chunk.text as text,
                       chunk.source as source,
                       vector_score,
                       graph_score,
                       entity_score,
                       final_score,
                       entities,
                       community
                ORDER BY final_score DESC
                LIMIT $max_results
            """, {
                "query_embedding": query_embedding.tolist(),
                "query_tokens": query.lower().split(),
                "k": self.config.max_results * 2,
                "weights": {
                    "vector": self.config.vector_weight,
                    "graph": self.config.graph_weight,
                    "entity": self.config.entity_weight
                },
                "use_community_boost": self.config.use_community_boost,
                "community_boost": self.config.community_boost_factor,
                "min_score": self.config.min_score,
                "max_results": self.config.max_results
            })
            
            # Convert to SearchResult objects
            results = []
            for record in result:
                results.append(SearchResult(
                    chunk_id=record["chunk_id"],
                    text=record["text"],
                    source=record["source"],
                    vector_score=record["vector_score"],
                    graph_score=record["graph_score"],
                    entity_score=record["entity_score"],
                    final_score=record["final_score"],
                    entities=record["entities"],
                    community=record["community"]
                ))
                
            return results
            
    def explain_results(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Generate explanation of search results.
        
        Args:
            results: List of search results to explain
            
        Returns:
            Dictionary with result explanations
        """
        explanations = []
        
        for result in results:
            # Calculate score contributions
            vector_contribution = (
                result.vector_score * self.config.vector_weight /
                result.final_score * 100
            )
            graph_contribution = (
                result.graph_score * self.config.graph_weight /
                result.final_score * 100
            )
            entity_contribution = (
                result.entity_score * self.config.entity_weight /
                result.final_score * 100
            )
            
            explanation = {
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                "final_score": f"{result.final_score:.3f}",
                "score_breakdown": {
                    "vector_similarity": f"{vector_contribution:.1f}%",
                    "graph_relevance": f"{graph_contribution:.1f}%",
                    "entity_match": f"{entity_contribution:.1f}%"
                },
                "key_entities": [
                    f"{e['text']} ({e['label']})" 
                    for e in sorted(
                        result.entities,
                        key=lambda x: x["confidence"],
                        reverse=True
                    )[:3]
                ],
                "community": result.community if result.community >= 0 else None
            }
            
            explanations.append(explanation)
            
        return {
            "results": explanations,
            "summary": {
                "total_results": len(results),
                "avg_score": np.mean([r.final_score for r in results]),
                "score_range": {
                    "min": min(r.final_score for r in results),
                    "max": max(r.final_score for r in results)
                }
            }
        }

def main():
    """Main function for testing."""
    import json
    from src.embeddings.embedding_generator import EmbeddingGenerator
    
    # Initialize components
    embedding_model = EmbeddingGenerator()
    search_engine = HybridSearchEngine(embedding_model)
    
    # Test queries
    queries = [
        "What are the main security features?",
        "How does the system handle errors?",
        "Explain the architecture design"
    ]
    
    try:
        for query in queries:
            print(f"\nQuery: {query}")
            results = search_engine.search(query)
            
            explanation = search_engine.explain_results(results)
            print("\nResults explanation:")
            print(json.dumps(explanation, indent=2))
            
    finally:
        search_engine.close()

if __name__ == "__main__":
    main()
