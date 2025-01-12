"""
Tests for hybrid search functionality.
"""

import pytest
import numpy as np
from datetime import datetime
from src.search.hybrid_search import (
    HybridSearchEngine,
    SearchConfig,
    SearchResult
)
from src.embeddings.embedding_generator import EmbeddingGenerator

@pytest.fixture
def embedding_model():
    return EmbeddingGenerator()

@pytest.fixture
def search_engine(embedding_model):
    config = SearchConfig(
        vector_weight=0.4,
        graph_weight=0.3,
        entity_weight=0.3,
        max_results=5,
        min_score=0.1,
        use_community_boost=True,
        community_boost_factor=1.2
    )
    engine = HybridSearchEngine(embedding_model, config=config)
    yield engine
    engine.close()

@pytest.fixture
def sample_data(search_engine):
    """Create sample data in Neo4j for testing."""
    with search_engine.driver.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create test chunks with embeddings
        session.run("""
            CREATE (c1:Chunk {
                id: '1',
                text: 'The system implements AES-256 encryption for data security.',
                source: 'security_doc',
                embedding: $emb1
            })
            CREATE (c2:Chunk {
                id: '2',
                text: 'Error handling uses try-catch blocks with detailed logging.',
                source: 'error_doc',
                embedding: $emb2
            })
            CREATE (c3:Chunk {
                id: '3',
                text: 'Authentication requires both password and 2FA token.',
                source: 'security_doc',
                embedding: $emb3
            })
            
            // Create entities
            CREATE (e1:Entity {text: 'AES-256', label: 'TECH'})
            CREATE (e2:Entity {text: 'encryption', label: 'CONCEPT'})
            CREATE (e3:Entity {text: '2FA', label: 'TECH'})
            
            // Create relationships
            CREATE (c1)-[:MENTIONS {confidence: 0.9}]->(e1)
            CREATE (c1)-[:MENTIONS {confidence: 0.8}]->(e2)
            CREATE (c3)-[:MENTIONS {confidence: 0.9}]->(e3)
            CREATE (c1)-[:SIMILAR_TO {score: 0.8}]->(c3)
        """, {
            "emb1": np.random.rand(768).tolist(),
            "emb2": np.random.rand(768).tolist(),
            "emb3": np.random.rand(768).tolist()
        })

def test_basic_search(search_engine, sample_data):
    """Test basic search functionality."""
    results = search_engine.search("How is data security implemented?")
    
    assert len(results) > 0
    assert all(isinstance(r, SearchResult) for r in results)
    
    # Check first result
    first = results[0]
    assert "security" in first.text.lower()
    assert first.final_score > 0
    assert first.vector_score >= 0
    assert first.graph_score >= 0
    assert first.entity_score >= 0

def test_entity_aware_search(search_engine, sample_data):
    """Test entity-aware search capabilities."""
    results = search_engine.search("What encryption methods are used?")
    
    # Find result mentioning AES-256
    aes_result = next(
        (r for r in results if "AES-256" in r.text),
        None
    )
    
    assert aes_result is not None
    assert any(
        e["text"] == "AES-256" 
        for e in aes_result.entities
    )
    
    # Entity score should contribute significantly
    assert aes_result.entity_score > 0

def test_graph_based_search(search_engine, sample_data):
    """Test graph-based search capabilities."""
    results = search_engine.search("Tell me about authentication security")
    
    # Should find both direct and related security chunks
    security_chunks = [
        r for r in results 
        if "security" in r.text.lower() or 
           "authentication" in r.text.lower()
    ]
    
    assert len(security_chunks) >= 2
    
    # Check graph scores
    assert any(r.graph_score > 0 for r in results)

def test_search_result_explanation(search_engine, sample_data):
    """Test search result explanation functionality."""
    results = search_engine.search("How is data protected?")
    explanation = search_engine.explain_results(results)
    
    assert "results" in explanation
    assert "summary" in explanation
    
    # Check explanation structure
    for result_exp in explanation["results"]:
        assert "text" in result_exp
        assert "final_score" in result_exp
        assert "score_breakdown" in result_exp
        assert "key_entities" in result_exp
        
        # Verify score breakdown
        breakdown = result_exp["score_breakdown"]
        assert "vector_similarity" in breakdown
        assert "graph_relevance" in breakdown
        assert "entity_match" in breakdown
        
        # Check percentage format
        assert all(
            isinstance(v, str) and v.endswith("%")
            for v in breakdown.values()
        )

def test_search_config_effects(search_engine, sample_data):
    """Test effects of different search configurations."""
    # Test with different weight configurations
    vector_config = SearchConfig(
        vector_weight=0.8,
        graph_weight=0.1,
        entity_weight=0.1
    )
    entity_config = SearchConfig(
        vector_weight=0.1,
        graph_weight=0.1,
        entity_weight=0.8
    )
    
    # Create engines with different configs
    vector_engine = HybridSearchEngine(
        search_engine.embedding_model,
        config=vector_config
    )
    entity_engine = HybridSearchEngine(
        search_engine.embedding_model,
        config=entity_config
    )
    
    try:
        # Run same query with different configurations
        query = "What security measures are implemented?"
        
        vector_results = vector_engine.search(query)
        entity_results = entity_engine.search(query)
        
        # Vector-focused results should prioritize semantic similarity
        assert vector_results[0].vector_score >= entity_results[0].vector_score
        
        # Entity-focused results should prioritize entity matches
        assert (
            entity_results[0].entity_score >= 
            vector_results[0].entity_score
        )
        
    finally:
        vector_engine.close()
        entity_engine.close()

def test_community_boost(search_engine, sample_data):
    """Test community boost effects on search results."""
    with search_engine.driver.session() as session:
        # Assign communities
        session.run("""
            MATCH (c:Chunk)
            WHERE c.source = 'security_doc'
            SET c.community = 1
        """)
    
    # Search with and without community boost
    config_with_boost = SearchConfig(
        use_community_boost=True,
        community_boost_factor=1.5
    )
    config_without_boost = SearchConfig(
        use_community_boost=False
    )
    
    engine_with_boost = HybridSearchEngine(
        search_engine.embedding_model,
        config=config_with_boost
    )
    engine_without_boost = HybridSearchEngine(
        search_engine.embedding_model,
        config=config_without_boost
    )
    
    try:
        query = "Tell me about security features"
        
        results_with_boost = engine_with_boost.search(query)
        results_without_boost = engine_without_boost.search(query)
        
        # Results with boost should prioritize same-community chunks
        assert (
            len([r for r in results_with_boost[:2] if r.community == 1]) >=
            len([r for r in results_without_boost[:2] if r.community == 1])
        )
        
    finally:
        engine_with_boost.close()
        engine_without_boost.close()

if __name__ == "__main__":
    pytest.main([__file__])
