"""
Main entry point for the enhanced RAG system.
"""

import logging
import argparse
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from src.embeddings.embedding_generator import EmbeddingGenerator
from src.entity_processing.entity_extractor import EntityExtractor
from src.graph_construction.relationship_builder import (
    EnhancedRelationshipBuilder,
    RelationshipConfig
)
from src.search.hybrid_search import (
    HybridSearchEngine,
    SearchConfig
)
from src.monitoring.system_monitor import SystemMonitor

logger = logging.getLogger(__name__)

@dataclass
class SystemConfig:
    """Configuration for the RAG system."""
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    entity_model: str = "en_core_web_sm"
    prometheus_port: int = 8000
    cache_dir: Optional[str] = None

class RAGSystem:
    """Enhanced RAG system with entity awareness and monitoring."""
    
    def __init__(self, config: SystemConfig):
        """Initialize the RAG system.
        
        Args:
            config: System configuration
        """
        self.config = config
        
        # Initialize components
        logger.info("Initializing system components...")
        
        self.embedding_model = EmbeddingGenerator(
            model_name=config.embedding_model,
            cache_dir=config.cache_dir
        )
        
        self.entity_extractor = EntityExtractor(
            model=config.entity_model
        )
        
        self.relationship_builder = EnhancedRelationshipBuilder(
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password,
            config=RelationshipConfig(
                similarity_threshold=0.7,
                use_community_detection=True
            )
        )
        
        self.search_engine = HybridSearchEngine(
            embedding_model=self.embedding_model,
            uri=config.neo4j_uri,
            user=config.neo4j_user,
            password=config.neo4j_password,
            config=SearchConfig(
                vector_weight=0.4,
                graph_weight=0.3,
                entity_weight=0.3,
                use_community_boost=True
            )
        )
        
        self.monitor = SystemMonitor(
            neo4j_uri=config.neo4j_uri,
            neo4j_user=config.neo4j_user,
            neo4j_password=config.neo4j_password,
            prometheus_port=config.prometheus_port
        )
        
        logger.info("System initialization complete")
        
    def close(self):
        """Close all connections."""
        self.relationship_builder.close()
        self.search_engine.close()
        self.monitor.close()
        
    def process_documents(self,
                         documents: List[Dict[str, str]],
                         source: str,
                         doc_type: str = "general") -> List[Dict[str, Any]]:
        """Process documents and add to knowledge base.
        
        Args:
            documents: List of documents with text content
            source: Source identifier
            doc_type: Document type ("general" or "sow")
            
        Returns:
            List of processed chunks with metadata
        """
        with self.monitor.track_operation("process_documents"):
            logger.info(f"Processing {len(documents)} {doc_type} documents from {source}")
            
            if doc_type == "sow":
                # Process SOW documents
                processed_docs = []
                for doc in documents:
                    try:
                        # Save document content to temp file
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(doc['content'])
                            tmp_path = tmp_file.name
                        
                        # Process SOW
                        result = self.entity_extractor.process_sow(
                            tmp_path,
                            cache_dir=self.config.cache_dir
                        )
                        
                        # Add to graph
                        with self.relationship_builder.driver.session() as session:
                            session.write_transaction(
                                self.entity_extractor.create_neo4j_requirements,
                                result
                            )
                        
                        processed_docs.append(result)
                        
                    finally:
                        # Cleanup temp file
                        if 'tmp_path' in locals():
                            os.unlink(tmp_path)
                
                return processed_docs
                
            else:
                # Process general documents
                processed_chunks = self.entity_extractor.batch_process(
                    documents,
                    source=source
                )
                
                # Add to graph and build relationships
                with self.relationship_builder.driver.session() as session:
                    for chunk in processed_chunks:
                        session.write_transaction(
                            self.entity_extractor.create_neo4j_entities,
                            chunk
                        )
                
                # Build relationships between chunks
                self.relationship_builder.build_relationships()
                
                return processed_chunks
            
    def search(self,
               query: str,
               explain: bool = False) -> Dict[str, Any]:
        """Perform hybrid search with optional explanation.
        
        Args:
            query: Search query
            explain: Whether to include explanation of results
            
        Returns:
            Search results with optional explanation
        """
        with self.monitor.track_operation("search"):
            results = self.search_engine.search(query)
            
            if explain:
                explanation = self.search_engine.explain_results(results)
                return {
                    "results": [vars(r) for r in results],
                    "explanation": explanation
                }
            else:
                return {
                    "results": [vars(r) for r in results]
                }
                
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and metrics.
        
        Returns:
            System status information
        """
        with self.monitor.track_operation("get_status"):
            # Collect current metrics
            graph_metrics = self.monitor.collect_graph_metrics()
            performance = self.monitor.get_performance_summary(hours=24)
            errors = self.monitor.get_error_summary(hours=24)
            
            return {
                "graph_metrics": {
                    "nodes": graph_metrics.node_count,
                    "relationships": graph_metrics.relationship_count,
                    "avg_degree": graph_metrics.avg_degree,
                    "index_size_mb": graph_metrics.index_size_mb,
                    "communities": len(graph_metrics.community_stats)
                },
                "performance_24h": performance,
                "errors_24h": errors
            }

def main():
    """Main function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add file handler
    fh = logging.FileHandler('rag_system.log')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logging.getLogger().addHandler(fh)
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Enhanced RAG System"
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file'
    )
    parser.add_argument(
        '--query',
        type=str,
        help='Search query'
    )
    parser.add_argument(
        '--explain',
        action='store_true',
        help='Explain search results'
    )
    args = parser.parse_args()
    
    # Load config
    if args.config:
        with open(args.config) as f:
            config_dict = json.load(f)
        config = SystemConfig(**config_dict)
    else:
        config = SystemConfig()
    
    # Initialize system
    system = RAGSystem(config)
    
    try:
        if args.query:
            # Perform search
            results = system.search(args.query, explain=args.explain)
            print("\nSearch Results:")
            print(json.dumps(results, indent=2))
        else:
            # Show system status
            status = system.get_system_status()
            print("\nSystem Status:")
            print(json.dumps(status, indent=2))
            
    finally:
        system.close()

if __name__ == "__main__":
    main()
