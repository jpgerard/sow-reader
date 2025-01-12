"""
Tests for system monitoring functionality.
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from src.monitoring.system_monitor import (
    SystemMonitor,
    PerformanceMetrics,
    GraphMetrics
)

@pytest.fixture
def monitor():
    """Create a system monitor instance."""
    # Use test Neo4j credentials
    monitor = SystemMonitor(
        neo4j_uri="bolt://localhost:7687",
        neo4j_user="neo4j",
        neo4j_password="password",
        prometheus_port=8001  # Different port for testing
    )
    yield monitor
    monitor.close()

@pytest.fixture
def sample_graph_data(monitor):
    """Create sample graph data for testing."""
    with monitor.driver.session() as session:
        # Clear existing data
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create test nodes and relationships
        session.run("""
            CREATE (c1:Chunk {id: '1', text: 'Test chunk 1'})
            CREATE (c2:Chunk {id: '2', text: 'Test chunk 2'})
            CREATE (c3:Chunk {id: '3', text: 'Test chunk 3'})
            CREATE (c1)-[:SIMILAR_TO {score: 0.8}]->(c2)
            CREATE (c2)-[:SIMILAR_TO {score: 0.7}]->(c3)
            SET c1.community = 1
            SET c2.community = 1
            SET c3.community = 2
        """)

def test_graph_metrics_collection(monitor, sample_graph_data):
    """Test collection of graph metrics."""
    metrics = monitor.collect_graph_metrics()
    
    assert isinstance(metrics, GraphMetrics)
    assert metrics.node_count == 3
    assert metrics.relationship_count == 2
    assert metrics.avg_degree > 0
    
    # Check community statistics
    assert len(metrics.community_stats) == 2
    assert metrics.community_stats["1"] == 2  # Two nodes in community 1
    assert metrics.community_stats["2"] == 1  # One node in community 2

def test_performance_tracking(monitor):
    """Test operation performance tracking."""
    # Test successful operation
    with monitor.track_operation("test_op"):
        time.sleep(0.1)  # Simulate work
        
    # Verify metrics were recorded
    assert len(monitor.performance_history) == 1
    metrics = monitor.performance_history[0]
    assert isinstance(metrics, PerformanceMetrics)
    assert metrics.latency_ms >= 100  # At least 100ms
    assert metrics.error_count == 0
    
    # Test operation with error
    with pytest.raises(ValueError):
        with monitor.track_operation("error_op"):
            raise ValueError("Test error")
            
    # Verify error was recorded
    assert len(monitor.error_history) == 1
    error = monitor.error_history[0]
    assert error["error_type"] == "ValueError"
    assert error["operation"] == "error_op"

def test_performance_summary(monitor):
    """Test performance summary generation."""
    # Add some test metrics
    test_metrics = [
        PerformanceMetrics(
            latency_ms=100.0,
            memory_mb=500.0,
            cpu_percent=50.0,
            cache_hit_rate=0.8,
            error_count=0,
            timestamp=datetime.utcnow()
        ),
        PerformanceMetrics(
            latency_ms=200.0,
            memory_mb=550.0,
            cpu_percent=60.0,
            cache_hit_rate=0.7,
            error_count=1,
            timestamp=datetime.utcnow()
        )
    ]
    
    monitor.performance_history.extend(test_metrics)
    
    # Get summary for last hour
    summary = monitor.get_performance_summary(hours=1)
    
    assert summary["total_operations"] == 2
    assert 100 <= summary["latency"]["avg_ms"] <= 200
    assert 500 <= summary["memory"]["avg_mb"] <= 550
    assert summary["errors"]["total_count"] == 1
    assert summary["errors"]["error_rate"] == 0.5

def test_error_summary(monitor):
    """Test error summary generation."""
    # Add some test errors
    test_errors = [
        {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "op1",
            "error_type": "ValueError",
            "error_message": "Test error 1",
            "latency_ms": 100.0
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "op2",
            "error_type": "ValueError",
            "error_message": "Test error 2",
            "latency_ms": 150.0
        },
        {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "op3",
            "error_type": "KeyError",
            "error_message": "Test error 3",
            "latency_ms": 200.0
        }
    ]
    
    monitor.error_history.extend(test_errors)
    
    # Get error summary
    summary = monitor.get_error_summary(hours=1)
    
    assert summary["total_errors"] == 3
    assert len(summary["error_types"]) == 2  # ValueError and KeyError
    assert summary["error_types"]["ValueError"]["count"] == 2
    assert summary["error_types"]["KeyError"]["count"] == 1

@pytest.mark.integration
def test_prometheus_metrics(monitor):
    """Test Prometheus metrics integration."""
    from prometheus_client import REGISTRY
    
    # Perform some operations to generate metrics
    with monitor.track_operation("test_op"):
        time.sleep(0.1)
        
    # Check if metrics were registered
    metric_names = {m.name for m in REGISTRY.collect()}
    
    assert "rag_search_latency_seconds" in metric_names
    assert "rag_memory_usage_bytes" in metric_names
    assert "rag_graph_size" in metric_names

@pytest.mark.integration
def test_long_term_monitoring(monitor, sample_graph_data):
    """Test monitoring over a longer period."""
    # Simulate operations over time
    start_time = datetime.utcnow()
    
    # Create operations spanning multiple hours
    for i in range(5):
        with patch('datetime.datetime') as mock_datetime:
            # Simulate different timestamps
            mock_datetime.utcnow.return_value = start_time + timedelta(hours=i)
            
            # Record some metrics
            with monitor.track_operation(f"op_{i}"):
                time.sleep(0.1)
                
            if i % 2 == 0:  # Simulate occasional errors
                with pytest.raises(ValueError):
                    with monitor.track_operation(f"error_op_{i}"):
                        raise ValueError(f"Test error {i}")
                        
    # Get summary for different time periods
    one_hour = monitor.get_performance_summary(hours=1)
    full_period = monitor.get_performance_summary(hours=6)
    
    assert full_period["total_operations"] > one_hour["total_operations"]
    
    # Check error summaries
    error_summary = monitor.get_error_summary(hours=6)
    assert error_summary["total_errors"] == 3  # Should have 3 errors

def test_index_size_estimation(monitor):
    """Test index size estimation logic."""
    test_indexes = [
        {"type": "FULLTEXT", "name": "test_fulltext"},
        {"type": "VECTOR", "name": "test_vector"},
        {"type": "BTREE", "name": "test_btree"}
    ]
    
    sizes = [
        monitor._estimate_index_size(idx)
        for idx in test_indexes
    ]
    
    # Check if different index types have different size estimates
    assert sizes[0] != sizes[1]  # FULLTEXT vs VECTOR
    assert sizes[1] != sizes[2]  # VECTOR vs BTREE
    assert all(size > 0 for size in sizes)

if __name__ == "__main__":
    pytest.main([__file__])
