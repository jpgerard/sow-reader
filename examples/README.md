# RAG System Usage Examples

This directory contains examples demonstrating common use cases for the RAG system. Each example includes sample code, data, and configuration files.

## Table of Contents

1. [Basic Setup](#basic-setup)
2. [Document Processing](#document-processing)
3. [Querying the Knowledge Base](#querying-the-knowledge-base)
4. [Advanced Configuration](#advanced-configuration)
5. [Performance Monitoring](#performance-monitoring)

## Basic Setup

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-org/rag-system.git
cd rag-system

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 2. Configuration

Create a config file (`config.json`):
```json
{
  "neo4j_uri": "bolt://localhost:7687",
  "neo4j_user": "neo4j",
  "neo4j_password": "your-password",
  "embedding_model": "sentence-transformers/all-mpnet-base-v2",
  "entity_model": "en_core_web_sm",
  "prometheus_port": 8000,
  "cache_dir": "./cache"
}
```

Set environment variables:
```bash
export ANTHROPIC_API_KEY="your-api-key"
export RAG_CONFIG="path/to/config.json"
```

## Document Processing

### 1. Single Document Processing

```json
// document.json
{
  "text": "The system implements AES-256 encryption for data security...",
  "metadata": {
    "source": "security_docs",
    "date": "2023-11-01",
    "author": "Security Team"
  }
}
```

```bash
# Process single document
python src/cli.py process --file document.json --source security_docs
```

### 2. Batch Processing

```json
// documents.json
[
  {
    "text": "Document 1 content...",
    "metadata": {
      "id": "doc1",
      "category": "technical"
    }
  },
  {
    "text": "Document 2 content...",
    "metadata": {
      "id": "doc2",
      "category": "user_guide"
    }
  }
]
```

```bash
# Process multiple documents
python src/cli.py process --file documents.json --source documentation

# Process and save results
python src/cli.py process --file documents.json --source documentation --output processed.json
```

### 3. Processing from Standard Input

```bash
# Process documents from stdin
cat documents.json | python src/cli.py process --source documentation
```

## Querying the Knowledge Base

### 1. Basic Queries

```bash
# Simple query
python src/cli.py query --query "What security measures are implemented?"

# Query with citations
python src/cli.py query --query "Explain the authentication process" --show-citations

# Query with metadata
python src/cli.py query --query "Describe the system architecture" --show-metadata
```

### 2. Advanced Querying

```bash
# Custom system prompt
python src/cli.py query \
  --query "What are the main security features?" \
  --system-prompt "Focus on technical details and implementation specifics" \
  --show-citations

# Adjust response parameters
python src/cli.py query \
  --query "Explain the error handling" \
  --temperature 0.3 \
  --max-tokens 2000 \
  --top-k 10

# Save response to file
python src/cli.py query \
  --query "Describe the API endpoints" \
  --output api_docs.json
```

### 3. Query from Standard Input

```bash
# Query from stdin
echo "How does the system handle authentication?" | python src/cli.py query
```

## Advanced Configuration

### 1. Custom Entity Types

```json
// entity_config.json
{
  "entity_types": [
    "PERSON",
    "ORG",
    "PRODUCT",
    "TECHNOLOGY"
  ],
  "confidence_threshold": 0.7
}
```

### 2. Graph Relationship Configuration

```json
// relationship_config.json
{
  "similarity_threshold": 0.7,
  "max_relationships_per_node": 50,
  "community_size_threshold": 100,
  "use_entity_relationships": true,
  "use_community_detection": true
}
```

### 3. Search Configuration

```json
// search_config.json
{
  "vector_weight": 0.4,
  "graph_weight": 0.3,
  "entity_weight": 0.3,
  "max_results": 5,
  "min_score": 0.1,
  "use_community_boost": true,
  "community_boost_factor": 1.2
}
```

## Performance Monitoring

### 1. Basic Metrics

```bash
# Get system status
python src/cli.py status

# Get detailed metrics
python src/cli.py status --detailed
```

### 2. Prometheus Integration

Access metrics at `http://localhost:8000/metrics`

Example metrics:
```
# HELP rag_search_latency_seconds Search operation latency
# TYPE rag_search_latency_seconds histogram
rag_search_latency_seconds_bucket{operation_type="query",le="0.1"} 2.0
rag_search_latency_seconds_bucket{operation_type="query",le="0.5"} 5.0
rag_search_latency_seconds_bucket{operation_type="query",le="1.0"} 10.0

# HELP rag_memory_usage_bytes Memory usage in bytes
# TYPE rag_memory_usage_bytes gauge
rag_memory_usage_bytes{component="python_process"} 1.52587890625e+08
```

### 3. Error Monitoring

```bash
# Get error summary
python src/cli.py status --errors

# Get detailed error report
python src/cli.py status --errors --detailed --hours 24
```

## Example Code

### 1. Python API Usage

```python
from src.main import RAGSystem, SystemConfig
from src.llm.rag_manager import RAGManager, RAGConfig

# Initialize system
config = SystemConfig(
    neo4j_uri="bolt://localhost:7687",
    neo4j_user="neo4j",
    neo4j_password="password"
)
system = RAGSystem(config)

# Initialize RAG manager
rag_config = RAGConfig(
    temperature=0.7,
    max_tokens=1000,
    top_k_results=5
)
manager = RAGManager(
    search_engine=system.search_engine,
    anthropic_api_key="your-api-key",
    config=rag_config
)

try:
    # Process documents
    documents = [
        {"text": "Document content...", "metadata": {"id": "1"}}
    ]
    processed = system.process_documents(documents, source="example")
    
    # Query knowledge base
    response = manager.generate_response(
        "What security measures are implemented?",
        system_prompt="Focus on technical details"
    )
    
    # Format and print response
    formatted = manager.format_response(response)
    print(json.dumps(formatted, indent=2))
    
finally:
    system.close()
```

### 2. Monitoring Integration

```python
from src.monitoring.system_monitor import SystemMonitor

monitor = SystemMonitor()

try:
    # Track operation performance
    with monitor.track_operation("custom_operation"):
        # Your operation code here
        pass
    
    # Get performance metrics
    metrics = monitor.get_performance_summary(hours=24)
    print(json.dumps(metrics, indent=2))
    
    # Get graph metrics
    graph_metrics = monitor.collect_graph_metrics()
    print(f"Nodes: {graph_metrics.node_count}")
    print(f"Relationships: {graph_metrics.relationship_count}")
    
finally:
    monitor.close()
```

## Additional Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Claude API Documentation](https://docs.anthropic.com/claude/reference)
- [spaCy Documentation](https://spacy.io/api/doc)
- [Sentence Transformers Documentation](https://www.sbert.net/)
