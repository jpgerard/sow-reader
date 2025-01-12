"""
Integration tests for the complete RAG system.
"""

import pytest
import json
import tempfile
from pathlib import Path
from src.main import RAGSystem, SystemConfig

@pytest.fixture
def config():
    """Create test configuration."""
    return SystemConfig(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        prometheus_port=8002,  # Different port for testing
        cache_dir=tempfile.mkdtemp()  # Temporary cache directory
    )

@pytest.fixture
def rag_system(config):
    """Create RAG system instance."""
    system = RAGSystem(config)
    yield system
    system.close()

@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        {
            "text": """
            The new security system implements AES-256 encryption for all data
            transmissions. This ensures compliance with industry standards.
            """,
            "metadata": {"type": "technical", "id": "doc1"}
        },
        {
            "text": """
            Error handling has been improved with comprehensive logging and
            automatic retry mechanisms. All errors are reported to the monitoring
            system.
            """,
            "metadata": {"type": "technical", "id": "doc2"}
        },
        {
            "text": """
            User authentication requires both password and 2FA token. The system
            integrates with existing SSO providers.
            """,
            "metadata": {"type": "technical", "id": "doc3"}
        }
    ]

def test_document_processing(rag_system, sample_documents):
    """Test end-to-end document processing."""
    processed_chunks = rag_system.process_documents(
        sample_documents,
        source="test_docs"
    )
    
    assert len(processed_chunks) == len(sample_documents)
    
    # Check that each chunk has required fields
    for chunk in processed_chunks:
        assert "text" in chunk
        assert "entities" in chunk
        assert "metadata" in chunk
        assert len(chunk["entities"]) > 0

def test_search_functionality(rag_system, sample_documents):
    """Test search functionality with processed documents."""
    # First process documents
    rag_system.process_documents(sample_documents, source="test_docs")
    
    # Test basic search
    results = rag_system.search("How is data security implemented?")
    assert "results" in results
    assert len(results["results"]) > 0
    
    # Test search with explanation
    explained_results = rag_system.search(
        "What authentication methods are used?",
        explain=True
    )
    assert "results" in explained_results
    assert "explanation" in explained_results
    
    # Verify explanation structure
    explanation = explained_results["explanation"]
    assert "results" in explanation
    assert "summary" in explanation
    
    # Check that results are properly ranked
    first_result = explained_results["results"][0]
    assert first_result["final_score"] >= explained_results["results"][-1]["final_score"]

def test_system_status(rag_system, sample_documents):
    """Test system status monitoring."""
    # Process some documents to generate metrics
    rag_system.process_documents(sample_documents, source="test_docs")
    
    # Perform some searches to generate more metrics
    rag_system.search("security")
    rag_system.search("authentication", explain=True)
    
    # Get system status
    status = rag_system.get_system_status()
    
    # Check status structure
    assert "graph_metrics" in status
    assert "performance_24h" in status
    assert "errors_24h" in status
    
    # Verify graph metrics
    graph_metrics = status["graph_metrics"]
    assert graph_metrics["nodes"] > 0
    assert graph_metrics["relationships"] > 0
    assert graph_metrics["avg_degree"] > 0

def test_error_handling(rag_system):
    """Test system error handling."""
    # Test with invalid document
    with pytest.raises(Exception):
        rag_system.process_documents(
            [{"invalid": "document"}],
            source="test_docs"
        )
    
    # Get error summary
    status = rag_system.get_system_status()
    assert status["errors_24h"]["total_errors"] > 0

def test_configuration_handling():
    """Test system configuration handling."""
    # Test with config file
    config_data = {
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password",
        "embedding_model": "sentence-transformers/all-mpnet-base-v2",
        "entity_model": "en_core_web_sm",
        "prometheus_port": 8003,
        "cache_dir": str(Path(tempfile.mkdtemp()))
    }
    
    # Write test config
    config_path = Path(tempfile.mkdtemp()) / "test_config.json"
    with open(config_path, "w") as f:
        json.dump(config_data, f)
    
    # Create system with config file
    config = SystemConfig(**config_data)
    system = RAGSystem(config)
    
    try:
        # Verify configuration
        assert system.config.neo4j_uri == config_data["neo4j_uri"]
        assert system.config.embedding_model == config_data["embedding_model"]
        assert system.config.prometheus_port == config_data["prometheus_port"]
    finally:
        system.close()

def test_search_result_consistency(rag_system, sample_documents):
    """Test consistency of search results."""
    # Process documents
    rag_system.process_documents(sample_documents, source="test_docs")
    
    # Perform same search multiple times
    query = "security authentication"
    results1 = rag_system.search(query)
    results2 = rag_system.search(query)
    
    # Results should be consistent
    assert len(results1["results"]) == len(results2["results"])
    assert all(
        r1["chunk_id"] == r2["chunk_id"]
        for r1, r2 in zip(results1["results"], results2["results"])
    )

def test_entity_awareness(rag_system, sample_documents):
    """Test entity-aware search capabilities."""
    # Process documents
    rag_system.process_documents(sample_documents, source="test_docs")
    
    # Search for specific entities
    results = rag_system.search("AES-256 encryption", explain=True)
    
    # Check entity matching in results
    first_result = results["results"][0]
    assert any(
        entity["text"] == "AES-256"
        for entity in first_result["entities"]
    )
    
    # Verify entity contribution to ranking
    explanation = results["explanation"]["results"][0]
    assert float(explanation["score_breakdown"]["entity_match"].rstrip("%")) > 0

def test_performance_monitoring(rag_system, sample_documents):
    """Test performance monitoring during operations."""
    # Track initial metrics
    initial_status = rag_system.get_system_status()
    
    # Perform operations
    rag_system.process_documents(sample_documents, source="test_docs")
    for _ in range(3):
        rag_system.search("test query", explain=True)
    
    # Get updated metrics
    final_status = rag_system.get_system_status()
    
    # Verify metrics were collected
    assert final_status["performance_24h"]["total_operations"] > \
           initial_status["performance_24h"].get("total_operations", 0)

if __name__ == "__main__":
    pytest.main([__file__])
