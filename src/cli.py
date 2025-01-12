"""
Command-line interface for the RAG system.
"""

import os
import sys
import logging
import argparse
import json
from typing import Optional
from pathlib import Path

from src.main import RAGSystem, SystemConfig
from src.llm.rag_manager import RAGManager, RAGConfig

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False):
    """Setup logging configuration.
    
    Args:
        verbose: Whether to use DEBUG level logging
    """
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def load_config(config_path: Optional[str] = None) -> dict:
    """Load configuration from file.
    
    Args:
        config_path: Path to config file
        
    Returns:
        Configuration dictionary
    """
    if not config_path:
        config_path = os.getenv(
            "RAG_CONFIG",
            str(Path.home() / ".rag" / "config.json")
        )
    
    try:
        with open(config_path) as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in config file: {config_path}")
        raise

def process_documents(args, config: dict):
    """Process documents and add to knowledge base.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    # Initialize system
    system = RAGSystem(SystemConfig(**config))
    
    try:
        # Load documents
        if args.file:
            with open(args.file) as f:
                documents = json.load(f)
        else:
            # Read from stdin
            documents = json.load(sys.stdin)
            
        # Process documents
        logger.info(f"Processing {len(documents)} documents...")
        processed = system.process_documents(
            documents,
            source=args.source or "cli_input"
        )
        
        logger.info(f"Successfully processed {len(processed)} documents")
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(processed, f, indent=2)
                
    finally:
        system.close()

def query_knowledge_base(args, config: dict):
    """Query the knowledge base using natural language.
    
    Args:
        args: Command line arguments
        config: Configuration dictionary
    """
    # Initialize system
    system = RAGSystem(SystemConfig(**config))
    
    # Initialize RAG manager
    rag_config = RAGConfig(
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        top_k_results=args.top_k
    )
    
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
        
    manager = RAGManager(
        search_engine=system.search_engine,
        anthropic_api_key=anthropic_api_key,
        config=rag_config
    )
    
    try:
        # Get query from arguments or stdin
        if args.query:
            query = args.query
        else:
            query = sys.stdin.read().strip()
            
        if not query:
            logger.error("No query provided")
            sys.exit(1)
            
        # Generate response
        logger.info("Generating response...")
        response = manager.generate_response(
            query,
            system_prompt=args.system_prompt
        )
        
        # Format output
        result = manager.format_response(response)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
        else:
            # Pretty print to stdout
            print("\nAnswer:")
            print(result["answer"])
            
            if args.show_citations:
                print("\nCitations:")
                for i, citation in enumerate(result["citations"], 1):
                    print(f"\n[{i}] {citation['text']}")
                    print(f"Source: {citation['source']}")
                    print(f"Relevance: {citation['relevance_score']}")
                    
            if args.show_metadata:
                print("\nMetadata:")
                print(json.dumps(result["metadata"], indent=2))
                
    finally:
        system.close()

def main():
    """Main CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="RAG System CLI"
    )
    
    parser.add_argument(
        '--config',
        help='Path to config file'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Process documents command
    process_parser = subparsers.add_parser(
        'process',
        help='Process documents and add to knowledge base'
    )
    process_parser.add_argument(
        '--file',
        help='JSON file containing documents'
    )
    process_parser.add_argument(
        '--source',
        help='Source identifier for documents'
    )
    process_parser.add_argument(
        '--output',
        help='Output file for processed documents'
    )
    
    # Query command
    query_parser = subparsers.add_parser(
        'query',
        help='Query the knowledge base'
    )
    query_parser.add_argument(
        '--query',
        help='Query string'
    )
    query_parser.add_argument(
        '--system-prompt',
        help='System prompt for Claude'
    )
    query_parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for response generation'
    )
    query_parser.add_argument(
        '--max-tokens',
        type=int,
        default=1000,
        help='Maximum tokens in response'
    )
    query_parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of top results to consider'
    )
    query_parser.add_argument(
        '--output',
        help='Output file for response'
    )
    query_parser.add_argument(
        '--show-citations',
        action='store_true',
        help='Show citations in output'
    )
    query_parser.add_argument(
        '--show-metadata',
        action='store_true',
        help='Show response metadata'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Load config
    config = load_config(args.config)
    
    # Execute command
    if args.command == 'process':
        process_documents(args, config)
    elif args.command == 'query':
        query_knowledge_base(args, config)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
