"""
Tests for the RAG system CLI.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from io import StringIO

from src.cli import (
    setup_logging,
    load_config,
    process_documents,
    query_knowledge_base,
    main
)
from src.main import RAGSystem
from src.llm.rag_manager import RAGResponse

@pytest.fixture
def mock_system():
    """Create mock RAG system."""
    with patch('src.cli.RAGSystem') as mock:
        system = Mock()
        mock.return_value = system
        yield system

@pytest.fixture
def mock_rag_manager():
    """Create mock RAG manager."""
    with patch('src.cli.RAGManager') as mock:
        manager = Mock()
        mock.return_value = manager
        yield manager

@pytest.fixture
def temp_config():
    """Create temporary config file."""
    config = {
        "neo4j_uri": "bolt://localhost:7687",
        "neo4j_user": "neo4j",
        "neo4j_password": "password",
        "embedding_model": "test-model",
        "entity_model": "en_core_web_sm"
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config, f)
        config_path = f.name
        
    yield config_path
    Path(config_path).unlink()

@pytest.fixture
def temp_documents():
    """Create temporary documents file."""
    documents = [
        {
            "text": "Test document 1",
            "metadata": {"id": "1"}
        },
        {
            "text": "Test document 2",
            "metadata": {"id": "2"}
        }
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(documents, f)
        docs_path = f.name
        
    yield docs_path
    Path(docs_path).unlink()

def test_load_config(temp_config):
    """Test configuration loading."""
    config = load_config(temp_config)
    
    assert isinstance(config, dict)
    assert "neo4j_uri" in config
    assert "embedding_model" in config
    
    # Test with non-existent file
    config = load_config("nonexistent.json")
    assert isinstance(config, dict)
    assert len(config) == 0

def test_process_documents(mock_system, temp_documents):
    """Test document processing command."""
    # Setup mock
    mock_system.process_documents.return_value = [
        {"id": "1", "processed": True},
        {"id": "2", "processed": True}
    ]
    
    # Create args mock
    args = Mock()
    args.file = temp_documents
    args.source = "test"
    args.output = None
    
    # Process documents
    process_documents(args, {})
    
    # Verify system calls
    mock_system.process_documents.assert_called_once()
    mock_system.close.assert_called_once()
    
    # Test with output file
    with tempfile.NamedTemporaryFile(suffix='.json') as output_file:
        args.output = output_file.name
        process_documents(args, {})
        
        # Verify output was written
        with open(output_file.name) as f:
            output = json.load(f)
            assert len(output) == 2
            assert all(doc["processed"] for doc in output)

def test_query_knowledge_base(mock_system, mock_rag_manager):
    """Test knowledge base querying."""
    # Setup mock response
    mock_response = RAGResponse(
        answer="Test answer",
        citations=[
            {
                "text": "Citation 1",
                "source": "doc1",
                "score": 0.9
            }
        ],
        context_used=[{"text": "Context 1"}],
        metadata={"model": "test-model"},
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
        timestamp="2023-01-01T00:00:00"
    )
    
    mock_rag_manager.generate_response.return_value = mock_response
    mock_rag_manager.format_response.return_value = {
        "answer": "Test answer",
        "citations": [{"text": "Citation 1"}],
        "metadata": {"model": "test-model"}
    }
    
    # Create args mock
    args = Mock()
    args.query = "Test query"
    args.system_prompt = None
    args.temperature = 0.7
    args.max_tokens = 1000
    args.top_k = 5
    args.output = None
    args.show_citations = True
    args.show_metadata = True
    
    # Test querying
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        query_knowledge_base(args, {})
        
    # Verify calls
    mock_rag_manager.generate_response.assert_called_once_with(
        "Test query",
        system_prompt=None
    )
    mock_system.close.assert_called_once()

def test_cli_main():
    """Test CLI main function."""
    # Test help output
    with pytest.raises(SystemExit) as exc_info:
        with patch('sys.argv', ['cli.py', '--help']):
            main()
    assert exc_info.value.code == 0
    
    # Test process command
    with patch('sys.argv', [
        'cli.py',
        'process',
        '--file', 'test.json',
        '--source', 'test'
    ]), patch('src.cli.process_documents') as mock_process:
        main()
        mock_process.assert_called_once()
    
    # Test query command
    with patch('sys.argv', [
        'cli.py',
        'query',
        '--query', 'test query'
    ]), patch('src.cli.query_knowledge_base') as mock_query:
        main()
        mock_query.assert_called_once()

def test_error_handling():
    """Test CLI error handling."""
    # Test missing API key
    with patch('sys.argv', ['cli.py', 'query', '--query', 'test']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
    
    # Test invalid config
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
        f.write("invalid json")
        f.flush()
        
        with patch('sys.argv', ['cli.py', '--config', f.name]):
            with pytest.raises(json.JSONDecodeError):
                main()

def test_stdin_handling():
    """Test handling of stdin input."""
    # Test document processing from stdin
    documents = [{"text": "Test doc"}]
    stdin_content = json.dumps(documents)
    
    with patch('sys.stdin', StringIO(stdin_content)):
        args = Mock()
        args.file = None
        args.source = "test"
        args.output = None
        
        with patch('src.cli.RAGSystem') as mock_system_class:
            mock_system = Mock()
            mock_system_class.return_value = mock_system
            mock_system.process_documents.return_value = documents
            
            process_documents(args, {})
            
            mock_system.process_documents.assert_called_once_with(
                documents,
                source="test"
            )
    
    # Test query from stdin
    query = "test query"
    with patch('sys.stdin', StringIO(query)):
        args = Mock()
        args.query = None
        args.system_prompt = None
        args.temperature = 0.7
        args.max_tokens = 1000
        args.top_k = 5
        args.output = None
        args.show_citations = False
        args.show_metadata = False
        
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('src.cli.RAGManager') as mock_manager_class:
                mock_manager = Mock()
                mock_manager_class.return_value = mock_manager
                mock_manager.generate_response.return_value = RAGResponse(
                    answer="Test answer",
                    citations=[],
                    context_used=[],
                    metadata={},
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    timestamp="2023-01-01T00:00:00"
                )
                
                query_knowledge_base(args, {})
                
                mock_manager.generate_response.assert_called_once_with(
                    query.strip(),
                    system_prompt=None
                )

if __name__ == "__main__":
    pytest.main([__file__])
