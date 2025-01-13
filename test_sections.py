"""
Test suite for SOW section parsing functionality
"""

import pytest
from src.entity_processing.sow_processor import SOWProcessor

@pytest.fixture
def sow_processor():
    return SOWProcessor()

def test_parse_sections_basic():
    """Test basic section parsing with simple format."""
    processor = SOWProcessor()
    text = """
    A.1 Introduction
    This is an introduction section.
    
    A.2 Background
    This provides background information.
    
    B.1 Requirements
    These are the requirements.
    """
    
    sections = processor._parse_sections(text)
    
    assert len(sections) == 3
    assert sections[0]['id'] == 'A.1'
    assert 'introduction' in sections[0]['content'].lower()
    assert sections[1]['id'] == 'A.2'
    assert 'background' in sections[1]['content'].lower()
    assert sections[2]['id'] == 'B.1'
    assert 'requirements' in sections[2]['content'].lower()

def test_parse_sections_with_noise():
    """Test section parsing with headers, footers, and noise."""
    processor = SOWProcessor()
    text = """
    Page 1 of 10
    Source-Selection-Sensitive
    
    A.1 Technical Requirements
    System must be scalable.
    
    Page 2 of 10
    For Official Use Only
    
    A.2 Performance Requirements
    System must be responsive.
    """
    
    sections = processor._parse_sections(text)
    
    assert len(sections) == 2
    assert 'Page' not in sections[0]['content']
    assert 'Source-Selection-Sensitive' not in sections[0]['content']
    assert 'For Official Use Only' not in sections[1]['content']
    assert 'scalable' in sections[0]['content'].lower()
    assert 'responsive' in sections[1]['content'].lower()

def test_parse_sections_numbered():
    """Test parsing of numbered sections."""
    processor = SOWProcessor()
    text = """
    1.1.1 Performance Requirements
    System must meet performance metrics.
    
    1.1.2 Security Requirements
    System must be secure.
    """
    
    sections = processor._parse_sections(text)
    
    assert len(sections) == 2
    assert sections[0]['id'] == '1.1.1'
    assert sections[1]['id'] == '1.1.2'
    assert 'performance' in sections[0]['content'].lower()
    assert 'security' in sections[1]['content'].lower()

def test_parse_sections_with_content():
    """Test parsing sections with various content types."""
    processor = SOWProcessor()
    text = """
    A.1 Requirements
    The system must be available 24/7
    The system must support multiple users
    The system must provide backup functionality
    
    A.2 Documentation
    Documentation must include system guides
    Documentation must include user manuals
    """
    
    sections = processor._parse_sections(text)
    
    assert len(sections) == 2
    assert '24/7' in sections[0]['content']
    assert 'multiple users' in sections[0]['content']
    assert 'backup' in sections[0]['content']
    assert 'documentation' in sections[1]['content'].lower()
    assert 'manuals' in sections[1]['content'].lower()

def test_parse_sections_with_formatting():
    """Test parsing sections with formatting artifacts."""
    processor = SOWProcessor()
    text = """
    A.1 Overview............................................1
    This is an overview section.
    (cid:123)
    
    A.2 Scope..............................................2
    Project scope details.
    (cid:456)
    """
    
    sections = processor._parse_sections(text)
    
    assert len(sections) == 2
    assert '.' * 5 not in sections[0]['content']
    assert '(cid:' not in sections[0]['content']
    assert 'overview section' in sections[0]['content'].lower()
    assert 'scope details' in sections[1]['content'].lower()

def test_parse_sections_empty_or_invalid():
    """Test handling of empty or invalid sections."""
    processor = SOWProcessor()
    text = """
    A.1
    
    A.2 Empty Section
    
    A.3 Valid Section
    This is the only valid section.
    """
    
    sections = processor._parse_sections(text)
    
    # Should only include sections with substantial content
    assert len(sections) == 1
    assert sections[0]['id'] == 'A.3'
    assert 'valid section' in sections[0]['content'].lower()

def test_clean_content():
    """Test content cleaning functionality."""
    processor = SOWProcessor()
    text = """
    A.1 Requirements
    The system must:
    Be scalable
    Be secure
    (cid:123)
    """
    
    cleaned = processor._clean_content(text)
    
    assert '(cid:123)' not in cleaned
    assert 'scalable' in cleaned.lower()
    assert 'secure' in cleaned.lower()
    assert len(cleaned.split('\n')) == 1  # Should be single line

if __name__ == '__main__':
    pytest.main([__file__])
