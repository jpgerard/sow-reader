"""Tests for the proposal matcher component."""

import pytest
from unittest.mock import Mock, patch
from src.search.proposal_matcher import ProposalMatcher, MatchResult

@pytest.fixture
def embedding_model():
    """Mock embedding model fixture."""
    model = Mock()
    model.encode.return_value = [0.1] * 768  # Mock 768-dimensional embedding
    return model

@pytest.fixture
def sample_requirement():
    """Sample requirement text fixture."""
    return """3.2.1 Security Requirements
    The system must implement role-based access control (RBAC) with support for
    multiple user roles and permission levels."""

@pytest.fixture
def sample_proposal():
    """Sample proposal text fixture."""
    return """3.2.1 Security Implementation
    Our system implements comprehensive role-based access control (RBAC) that
    supports multiple user roles including admin, manager, and regular users.
    Each role has configurable permission levels that can be adjusted as needed.
    
    3.2.2 Authentication
    Multi-factor authentication is supported for all user roles.
    
    3.2.3 Authorization
    Fine-grained permissions system allows detailed access control."""

def test_proposal_matcher_initialization(embedding_model):
    """Test ProposalMatcher initialization."""
    matcher = ProposalMatcher(embedding_model)
    assert matcher.weights['vector'] == 0.4
    assert matcher.weights['semantic'] == 0.3
    assert matcher.weights['section'] == 0.3

def test_section_id_extraction(embedding_model):
    """Test section ID extraction."""
    matcher = ProposalMatcher(embedding_model)
    
    # Test valid section ID
    text = "3.2.1 Security Requirements"
    assert matcher._extract_section_id(text) == "3.2.1"
    
    # Test no section ID
    text = "Security Requirements"
    assert matcher._extract_section_id(text) is None

def test_section_similarity_calculation(embedding_model):
    """Test section similarity calculation."""
    matcher = ProposalMatcher(embedding_model)
    
    # Test exact match
    assert matcher._calculate_section_similarity("3.2.1", "3.2.1") == 1.0
    
    # Test partial match
    assert matcher._calculate_section_similarity("3.2.1", "3.2.2") == 0.6666666666666666
    
    # Test no match
    assert matcher._calculate_section_similarity("3.2.1", "4.1.1") == 0.0
    
    # Test empty sections
    assert matcher._calculate_section_similarity("", "") == 0.0
    assert matcher._calculate_section_similarity("3.2.1", "") == 0.0
    assert matcher._calculate_section_similarity("", "3.2.1") == 0.0

@patch('src.search.proposal_matcher.ProposalVectorizer')
@patch('src.search.proposal_matcher.HybridSearchEngine')
def test_match_requirement(MockHybridSearch, MockVectorizer, embedding_model, 
                         sample_requirement, sample_proposal):
    """Test requirement matching."""
    # Setup mock search results
    mock_vector_result = Mock()
    mock_vector_result.chunk.text = "3.2.1 Security Implementation\nOur system implements RBAC"
    mock_vector_result.similarity_score = 0.85
    
    mock_hybrid_result = Mock()
    mock_hybrid_result.text = "3.2.1 Security Implementation\nOur system implements RBAC"
    mock_hybrid_result.final_score = 0.9
    
    # Configure mocks
    mock_vectorizer = MockVectorizer.return_value
    mock_vectorizer.search.return_value = [mock_vector_result]
    
    mock_hybrid = MockHybridSearch.return_value
    mock_hybrid.search.return_value = [mock_hybrid_result]
    
    # Create matcher and test
    matcher = ProposalMatcher(embedding_model)
    result = matcher.match_requirement(sample_requirement, sample_proposal)
    
    # Verify result
    assert isinstance(result, MatchResult)
    assert result.requirement_id == "3.2.1"
    assert len(result.matched_sections) > 0
    assert result.confidence_score > 0
    assert "3.2.1" in result.match_explanation
    
    # Verify search calls
    mock_vectorizer.index_proposal.assert_called_once_with(sample_proposal)
    mock_vectorizer.search.assert_called_once()
    mock_hybrid.search.assert_called_once()

def test_match_explanation_generation(embedding_model):
    """Test match explanation generation."""
    matcher = ProposalMatcher(embedding_model)
    
    # Test with good matches
    matches = [{
        'section_id': '3.2.1',
        'text': 'Sample text',
        'vector_score': 0.9,
        'semantic_score': 0.85,
        'section_score': 1.0,
        'final_score': 0.92
    }]
    
    explanation, improvements = matcher._generate_match_explanation(
        "Sample requirement",
        matches
    )
    
    assert "3.2.1" in explanation
    assert "0.92" in explanation
    assert improvements is None  # High score, no improvements needed
    
    # Test with low scores
    matches[0].update({
        'vector_score': 0.5,
        'semantic_score': 0.5,
        'section_score': 0.5,
        'final_score': 0.5
    })
    
    explanation, improvements = matcher._generate_match_explanation(
        "Sample requirement",
        matches
    )
    
    assert "3.2.1" in explanation
    assert "0.50" in explanation
    assert improvements is not None
    assert "terminology" in improvements.lower()
    
    # Test with no matches
    explanation, improvements = matcher._generate_match_explanation(
        "Sample requirement",
        []
    )
    
    assert "No matching sections found" in explanation
    assert improvements is not None
    assert "adding a section" in improvements.lower()

def test_cleanup(embedding_model):
    """Test resource cleanup."""
    matcher = ProposalMatcher(embedding_model)
    matcher.close()
    matcher.hybrid_search.close.assert_called_once()
