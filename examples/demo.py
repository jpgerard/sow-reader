"""
Demonstration script for the RAG system.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any

from src.main import RAGSystem, SystemConfig
from src.llm.rag_manager import RAGManager, RAGConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config(config_name: str) -> Dict[str, Any]:
    """Load configuration from examples.
    
    Args:
        config_name: Name of configuration to load
        
    Returns:
        Configuration dictionary
    """
    config_path = Path(__file__).parent / "sample_configs" / "config_examples.json"
    with open(config_path) as f:
        configs = json.load(f)
        
    if config_name not in configs:
        raise ValueError(f"Unknown configuration: {config_name}")
        
    return configs[config_name]

def load_documents() -> list:
    """Load sample documents.
    
    Returns:
        List of documents
    """
    docs_path = Path(__file__).parent / "sample_data" / "documents.json"
    with open(docs_path) as f:
        return json.load(f)

def run_demo(config_name: str = "balanced"):
    """Run RAG system demonstration.
    
    Args:
        config_name: Name of configuration to use
    """
    logger.info(f"Running demo with {config_name} configuration")
    
    # Load configuration
    config = load_config(config_name)
    system_config = SystemConfig(**config)
    
    # Initialize system
    system = RAGSystem(system_config)
    
    # Initialize RAG manager
    rag_config = RAGConfig(**config["rag_config"])
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
    manager = RAGManager(
        search_engine=system.search_engine,
        anthropic_api_key=anthropic_api_key,
        config=rag_config
    )
    
    try:
        # Load and process documents
        logger.info("Loading sample documents...")
        documents = load_documents()
        
        logger.info(f"Processing {len(documents)} documents...")
        processed = system.process_documents(documents, source="demo")
        logger.info("Document processing complete")
        
        # Example queries to demonstrate different aspects
        queries = [
            # Security-related query
            {
                "query": "What security measures are implemented in the system?",
                "system_prompt": "Focus on technical security features and standards compliance."
            },
            # Architecture query
            {
                "query": "Explain the system's architecture and how services communicate.",
                "system_prompt": "Provide a technical overview of the architecture patterns and communication mechanisms."
            },
            # Operations query
            {
                "query": "How does the system handle errors and monitoring?",
                "system_prompt": "Describe the error handling mechanisms and monitoring capabilities."
            }
        ]
        
        # Run queries
        for query_info in queries:
            logger.info(f"\nQuery: {query_info['query']}")
            
            response = manager.generate_response(
                query_info["query"],
                system_prompt=query_info["system_prompt"]
            )
            
            # Format and display results
            result = manager.format_response(response)
            
            print("\nAnswer:")
            print(result["answer"])
            
            print("\nCitations:")
            for i, citation in enumerate(result["citations"], 1):
                print(f"\n[{i}] {citation['text']}")
                print(f"Source: {citation['source']}")
                print(f"Relevance: {citation['relevance_score']}")
            
            print("\nMetadata:")
            print(json.dumps(result["metadata"], indent=2))
            
        # Get system status
        logger.info("\nSystem Status:")
        status = system.get_system_status()
        print(json.dumps(status, indent=2))
        
    finally:
        system.close()

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG System Demo")
    parser.add_argument(
        '--config',
        choices=['high_performance', 'high_accuracy', 'balanced', 'memory_optimized'],
        default='balanced',
        help='Configuration to use'
    )
    
    args = parser.parse_args()
    
    try:
        run_demo(args.config)
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
