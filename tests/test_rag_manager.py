"""
Tests for RAG manager with Claude integration.
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import json
import anthropic

from src.llm.rag_manager import (
    RAGManager,
    RAGConfig,
    RAGResponse
)

@pytest.fixture
def mock_search_results():
    """Create mock search results."""
    return {
        "results": [
            {
                "text": "The system uses AES-256 encryption for data security.",
                "vector_score": 0.85,
                "final_score": 0.9,
                "source": "security_docs.txt"
            },
            {
                "text": "Authentication requires 2FA with hardware tokens.",
                "vector_score": 0.75,
                "final_score": 0.8,
                "source": "auth_docs.txt"
            },
            {
                "text": "Regular security audits are performed quarterly.",
                "vector_score": 0.65,
                "final_score": 0.7,
                "source": "compliance_docs.txt"
            }
        ]
    }

@pytest.fixture
def mock_claude_response():
    """Create mock Claude API response."""
    class MockCompletion:
        def __init__(self):
            self.completion = (
                "Based on the provided context, the system implements several "
                "security measures:\n\n1. AES-256 encryption for data protection [1]\n"
                "2. Two-factor authentication with hardware tokens [2]\n"
                "3. Regular quarterly security audits [3]"
            )
            
    return MockCompletion()

@pytest.fixture
def rag_manager():
    """Create RAG manager with mocked dependencies."""
    config = RAGConfig(
        temperature=0.7,
        max_tokens=1000,
        top_k_results=3,
        similarity_threshold=0.6
    )
    
    # Create mock search engine
    search_engine = Mock()
    
    # Initialize manager with test API key
    manager = RAGManager(
        search_engine=search_engine,
        anthropic_api_key="test_key",
        config=config
    )
    
    return manager

def test_rag_config():
    """Test RAG configuration."""
    config = RAGConfig()
    
    assert config.model_name == "claude-2"
    assert 0 <= config.temperature <= 1
    assert config.max_tokens > 0
    assert config.top_k_results > 0
    assert 0 <= config.similarity_threshold <= 1

def test_response_generation(rag_manager, mock_search_results, mock_claude_response):
    """Test RAG response generation."""
    # Mock search engine response
    rag_manager.search_engine.search.return_value = mock_search_results
    
    # Mock Claude API call
    with patch.object(rag_manager.client, 'completion', return_value=mock_claude_response):
        response = rag_manager.generate_response(
            "What security measures are implemented?"
        )
        
    assert isinstance(response, RAGResponse)
    assert len(response.citations) == len(mock_search_results["results"])
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert isinstance(response.timestamp, datetime)

def test_context_preparation(rag_manager, mock_search_results):
    """Test context preparation from search results."""
    rag_manager.search_engine.search.return_value = mock_search_results
    
    # Mock Claude API to focus on context preparation
    with patch.object(rag_manager.client, 'completion') as mock_completion:
        rag_manager.generate_response("Test query")
        
        # Check that the prompt was constructed correctly
        call_args = mock_completion.call_args[1]
        prompt = call_args["prompt"]
        
        # Verify context inclusion
        assert "Context:" in prompt
        assert "[1]" in prompt
        assert "AES-256" in prompt
        assert "Question: Test query" in prompt

def test_citation_handling(rag_manager, mock_search_results, mock_claude_response):
    """Test citation handling in responses."""
    rag_manager.search_engine.search.return_value = mock_search_results
    
    with patch.object(rag_manager.client, 'completion', return_value=mock_claude_response):
        response = rag_manager.generate_response("Test query")
        formatted = rag_manager.format_response(response)
        
        # Check citation structure
        assert "citations" in formatted
        citations = formatted["citations"]
        assert len(citations) > 0
        
        for citation in citations:
            assert "text" in citation
            assert "source" in citation
            assert "relevance_score" in citation
            assert isinstance(citation["relevance_score"], str)
            assert 0 <= float(citation["relevance_score"]) <= 1

def test_error_handling(rag_manager):
    """Test error handling in RAG manager."""
    # Mock search engine to raise error
    rag_manager.search_engine.search.side_effect = Exception("Search failed")
    
    with pytest.raises(Exception):
        rag_manager.generate_response("Test query")

def test_response_formatting(rag_manager, mock_search_results, mock_claude_response):
    """Test response formatting."""
    rag_manager.search_engine.search.return_value = mock_search_results
    
    with patch.object(rag_manager.client, 'completion', return_value=mock_claude_response):
        response = rag_manager.generate_response("Test query")
        formatted = rag_manager.format_response(response)
        
        # Check formatted response structure
        assert "answer" in formatted
        assert "citations" in formatted
        assert "metadata" in formatted
        
        # Check metadata
        metadata = formatted["metadata"]
        assert "model" in metadata
        assert "temperature" in metadata
        assert "tokens_used" in metadata
        assert "timestamp" in metadata
        
        # Verify token counts
        tokens = metadata["tokens_used"]
        assert tokens["prompt"] > 0
        assert tokens["completion"] > 0
        assert tokens["total"] == tokens["prompt"] + tokens["completion"]

def test_rate_limit_retry(rag_manager, mock_search_results):
    """Test retry behavior on rate limits."""
    rag_manager.search_engine.search.return_value = mock_search_results
    
    # Mock Claude API to raise rate limit error then succeed
    rate_limit_error = anthropic.RateLimitError("Rate limit exceeded")
    success_response = mock_search_results
    
    with patch.object(rag_manager.client, 'completion') as mock_completion:
        mock_completion.side_effect = [rate_limit_error, success_response]
        
        # Should retry and eventually succeed
        response = rag_manager.generate_response("Test query")
        assert isinstance(response, RAGResponse)
        assert mock_completion.call_count == 2

def test_context_limit_handling(rag_manager):
    """Test handling of context length limits."""
    # Create search results with long texts
    long_results = {
        "results": [
            {
                "text": "x" * 2000,  # Long text
                "vector_score": 0.9,
                "final_score": 0.9,
                "source": "doc1.txt"
            },
            {
                "text": "y" * 2000,  # Another long text
                "vector_score": 0.8,
                "final_score": 0.8,
                "source": "doc2.txt"
            }
        ]
    }
    
    rag_manager.search_engine.search.return_value = long_results
    
    with patch.object(rag_manager.client, 'completion') as mock_completion:
        rag_manager.generate_response("Test query")
        
        # Check that the prompt respects context limit
        call_args = mock_completion.call_args[1]
        prompt = call_args["prompt"]
        context_size = len(prompt.split())
        assert context_size <= rag_manager.config.context_limit

if __name__ == "__main__":
    pytest.main([__file__])
