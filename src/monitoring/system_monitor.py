"""
System monitoring and diagnostics for the RAG pipeline.
"""

import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import psutil
import numpy as np
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    start_http_server
)

logger = logging.getLogger(__name__)

# Prometheus metrics
SEARCH_LATENCY = Histogram(
    'rag_search_latency_seconds',
    'Search operation latency',
    ['operation_type']
)
SEARCH_ERRORS = Counter(
    'rag_search_errors_total',
    'Search operation errors',
    ['error_type']
)
CACHE_HITS = Counter(
    'rag_cache_hits_total',
    'Cache hit count',
    ['cache_type']
)
CACHE_MISSES = Counter(
    'rag_cache_misses_total',
    'Cache miss count',
    ['cache_type']
)
MEMORY_USAGE = Gauge(
    'rag_memory_usage_bytes',
    'Memory usage in bytes',
    ['component']
)
GRAPH_SIZE = Gauge(
    'rag_graph_size',
    'Neo4j graph size metrics',
    ['metric_type']
)

@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    latency_ms: float
    memory_mb: float
    cpu_percent: float
    cache_hit_rate: float
    error_count: int
    timestamp: datetime

@dataclass
class GraphMetrics:
    """Neo4j graph metrics."""
    node_count: int
    relationship_count: int
    index_size_mb: float
    avg_degree: float
    community_stats: Dict[str, int]

class SystemMonitor:
    """Monitor and collect system metrics."""
    
    def __init__(self, 
                 neo4j_uri: str = "bolt://localhost:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "password",
                 prometheus_port: int = 8000):
        """Initialize the system monitor.
        
        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            prometheus_port: Port for Prometheus metrics
        """
        self.driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        
        # Start Prometheus metrics server
        start_http_server(prometheus_port)
        logger.info(f"Started Prometheus metrics server on port {prometheus_port}")
        
        # Initialize performance tracking
        self.performance_history: List[PerformanceMetrics] = []
        self.error_history: List[Dict[str, Any]] = []
        self.last_graph_metrics: Optional[GraphMetrics] = None
        
    def close(self):
        """Close Neo4j connection."""
        self.driver.close()
        
    def track_operation(self, operation_type: str):
        """Context manager to track operation performance.
        
        Args:
            operation_type: Type of operation being tracked
        """
        class OperationTracker:
            def __init__(self, monitor):
                self.monitor = monitor
                self.operation_type = operation_type
                self.start_time = None
                
            def __enter__(self):
                self.start_time = time.time()
                return self
                
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = time.time() - self.start_time
                
                # Record Prometheus metrics
                SEARCH_LATENCY.labels(
                    operation_type=self.operation_type
                ).observe(duration)
                
                if exc_type is not None:
                    SEARCH_ERRORS.labels(
                        error_type=exc_type.__name__
                    ).inc()
                    
                # Record detailed metrics
                self.monitor.record_performance_metrics(
                    latency_ms=duration * 1000,
                    operation_type=self.operation_type,
                    error=exc_val
                )
                
        return OperationTracker(self)
        
    def record_performance_metrics(self,
                                 latency_ms: float,
                                 operation_type: str,
                                 error: Optional[Exception] = None):
        """Record performance metrics.
        
        Args:
            latency_ms: Operation latency in milliseconds
            operation_type: Type of operation
            error: Exception if operation failed
        """
        # Get system metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent()
        
        # Record metrics
        metrics = PerformanceMetrics(
            latency_ms=latency_ms,
            memory_mb=memory_mb,
            cpu_percent=cpu_percent,
            cache_hit_rate=0.0,  # Updated by cache monitoring
            error_count=1 if error else 0,
            timestamp=datetime.utcnow()
        )
        
        self.performance_history.append(metrics)
        
        # Update Prometheus metrics
        MEMORY_USAGE.labels(
            component='python_process'
        ).set(memory_mb * 1024 * 1024)  # Convert to bytes
        
        # Record error if any
        if error:
            self.error_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "operation": operation_type,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "latency_ms": latency_ms
            })
            
    def collect_graph_metrics(self) -> GraphMetrics:
        """Collect Neo4j graph metrics.
        
        Returns:
            Graph metrics
        """
        with self.driver.session() as session:
            # Basic graph metrics
            basic_metrics = session.run("""
                MATCH (n)
                OPTIONAL MATCH (n)-[r]->()
                WITH count(DISTINCT n) as nodes,
                     count(DISTINCT r) as rels,
                     avg(size((n)-->()))as avg_degree
                RETURN nodes, rels, avg_degree
            """).single()
            
            # Index sizes
            index_sizes = session.run("""
                CALL db.indexes() YIELD name, type, labelsOrTypes, properties,
                                       state, populationPercent
                RETURN collect({
                    name: name,
                    type: type,
                    state: state,
                    progress: populationPercent
                }) as indexes
            """).single()["indexes"]
            
            # Community statistics
            community_stats = session.run("""
                MATCH (n:Chunk)
                WHERE n.community IS NOT NULL
                WITH n.community as community, count(*) as size
                RETURN collect({
                    community: community,
                    size: size
                }) as communities
            """).single()["communities"]
            
            # Calculate total index size (estimated)
            total_index_size_mb = sum(
                self._estimate_index_size(idx)
                for idx in index_sizes
            )
            
            metrics = GraphMetrics(
                node_count=basic_metrics["nodes"],
                relationship_count=basic_metrics["rels"],
                index_size_mb=total_index_size_mb,
                avg_degree=basic_metrics["avg_degree"],
                community_stats={
                    str(c["community"]): c["size"]
                    for c in community_stats
                }
            )
            
            # Update Prometheus metrics
            GRAPH_SIZE.labels(metric_type="nodes").set(metrics.node_count)
            GRAPH_SIZE.labels(metric_type="relationships").set(
                metrics.relationship_count
            )
            GRAPH_SIZE.labels(metric_type="index_size_mb").set(
                metrics.index_size_mb
            )
            
            self.last_graph_metrics = metrics
            return metrics
            
    def _estimate_index_size(self, index_info: Dict[str, Any]) -> float:
        """Estimate index size in MB based on type and state.
        
        Args:
            index_info: Index information from Neo4j
            
        Returns:
            Estimated size in MB
        """
        # This is a very rough estimation
        if index_info["type"] == "FULLTEXT":
            return 50  # Assume ~50MB for fulltext indexes
        elif index_info["type"] == "VECTOR":
            return 200  # Assume ~200MB for vector indexes
        else:
            return 10  # Assume ~10MB for other indexes
            
    def get_performance_summary(self,
                              hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for recent period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Performance summary
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.performance_history
            if m.timestamp >= cutoff
        ]
        
        if not recent_metrics:
            return {
                "message": "No metrics available for specified period"
            }
            
        return {
            "period_hours": hours,
            "total_operations": len(recent_metrics),
            "latency": {
                "avg_ms": np.mean([m.latency_ms for m in recent_metrics]),
                "p95_ms": np.percentile(
                    [m.latency_ms for m in recent_metrics],
                    95
                ),
                "p99_ms": np.percentile(
                    [m.latency_ms for m in recent_metrics],
                    99
                )
            },
            "memory": {
                "avg_mb": np.mean([m.memory_mb for m in recent_metrics]),
                "peak_mb": max(m.memory_mb for m in recent_metrics)
            },
            "cpu": {
                "avg_percent": np.mean(
                    [m.cpu_percent for m in recent_metrics]
                )
            },
            "errors": {
                "total_count": sum(m.error_count for m in recent_metrics),
                "error_rate": (
                    sum(m.error_count for m in recent_metrics) /
                    len(recent_metrics)
                )
            },
            "cache": {
                "avg_hit_rate": np.mean(
                    [m.cache_hit_rate for m in recent_metrics]
                )
            }
        }
        
    def get_error_summary(self,
                         hours: int = 24) -> Dict[str, Any]:
        """Get error summary for recent period.
        
        Args:
            hours: Number of hours to analyze
            
        Returns:
            Error summary
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            e for e in self.error_history
            if datetime.fromisoformat(e["timestamp"]) >= cutoff
        ]
        
        if not recent_errors:
            return {
                "message": "No errors in specified period"
            }
            
        # Group errors by type
        error_types = {}
        for error in recent_errors:
            error_type = error["error_type"]
            if error_type not in error_types:
                error_types[error_type] = {
                    "count": 0,
                    "examples": []
                }
            
            error_types[error_type]["count"] += 1
            if len(error_types[error_type]["examples"]) < 3:
                error_types[error_type]["examples"].append({
                    "message": error["error_message"],
                    "timestamp": error["timestamp"],
                    "operation": error["operation"]
                })
                
        return {
            "period_hours": hours,
            "total_errors": len(recent_errors),
            "error_types": error_types
        }

def main():
    """Main function for testing."""
    logging.basicConfig(level=logging.INFO)
    
    monitor = SystemMonitor()
    
    try:
        # Collect initial metrics
        logger.info("Collecting graph metrics...")
        metrics = monitor.collect_graph_metrics()
        
        logger.info("\nGraph Metrics:")
        logger.info(f"Nodes: {metrics.node_count}")
        logger.info(f"Relationships: {metrics.relationship_count}")
        logger.info(f"Avg Degree: {metrics.avg_degree:.2f}")
        logger.info(f"Index Size: {metrics.index_size_mb:.1f}MB")
        
        if metrics.community_stats:
            logger.info("\nCommunity Statistics:")
            for comm, size in metrics.community_stats.items():
                logger.info(f"Community {comm}: {size} nodes")
                
        # Test operation tracking
        with monitor.track_operation("test_operation"):
            logger.info("\nSimulating operation...")
            time.sleep(1)  # Simulate work
            
        # Get performance summary
        summary = monitor.get_performance_summary(hours=1)
        logger.info("\nPerformance Summary:")
        logger.info(json.dumps(summary, indent=2))
        
    finally:
        monitor.close()

if __name__ == "__main__":
    main()
