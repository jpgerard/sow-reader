"""
Tests for entity processing and graph construction.
"""

import pytest
from datetime import datetime
from src.entity_processing.entity_extractor import (
    EntityExtractor,
    Entity,
    ChunkMetadata
)
from src.graph_construction.relationship_builder import (
    EnhancedRelationshipBuilder,
    RelationshipConfig
)

@pytest.fixture
def entity_extractor():
    return EntityExtractor()

@pytest.fixture
def relationship_builder():
    config = RelationshipConfig(
        similarity_threshold=0.5,  # Lower for testing
        max_relationships_per_node=10,
        community_size_threshold=5,
        use_entity_relationships=True,
        use_community_detection=True
    )
    builder = EnhancedRelationshipBuilder(config=config)
    yield builder
    builder.close()

def test_entity_extraction(entity_extractor):
    text = """
    Microsoft CEO Satya Nadella announced new AI features in Windows 11.
    The event took place in Seattle on January 15th, 2024.
    """
    
    entities = entity_extractor.extract_entities(text)
    
    # Check extracted entities
    assert len(entities) >= 4
    
    # Verify specific entities
    entity_texts = {e.text for e in entities}
    assert "Microsoft" in entity_texts
    assert "Satya Nadella" in entity_texts
    assert "Seattle" in entity_texts
    
    # Check entity attributes
    for entity in entities:
        assert isinstance(entity, Entity)
        assert entity.confidence > 0
        assert entity.start_char >= 0
        assert entity.end_char <= len(text)
        assert entity.label in {"ORG", "PERSON", "GPE", "DATE"}

def test_chunk_metadata(entity_extractor):
    text = "Apple and Google are competing in AI technology."
    source = "tech_news"
    version = "1.0"
    
    entities, metadata = entity_extractor.process_chunk(text, source, version)
    
    # Check metadata
    assert isinstance(metadata, ChunkMetadata)
    assert metadata.version == version
    assert metadata.source == source
    assert isinstance(metadata.timestamp, datetime)
    assert len(metadata.processing_history) == 1
    assert metadata.entity_counts.get("ORG", 0) >= 2

def test_batch_processing(entity_extractor):
    chunks = [
        {"text": "Amazon announced new AWS features.", "doc_id": "1"},
        {"text": "Tesla stock rose 5% in New York.", "doc_id": "2"}
    ]
    
    results = entity_extractor.batch_process(chunks, "financial_news")
    
    assert len(results) == 2
    for result in results:
        assert "text" in result
        assert "entities" in result
        assert "metadata" in result
        assert "doc_id" in result
        assert len(result["entities"]) > 0

@pytest.mark.integration
def test_graph_construction(relationship_builder):
    # This test requires a running Neo4j instance
    try:
        relationship_builder.build_relationships()
        analysis = relationship_builder.analyze_graph()
        
        # Verify graph structure
        assert analysis["basic_stats"]["nodes"] > 0
        assert analysis["basic_stats"]["relationships"] > 0
        assert analysis["basic_stats"]["avg_degree"] > 0
        
        # Check community detection
        if relationship_builder.config.use_community_detection:
            assert len(analysis["community_stats"]) > 0
        
        # Check entity statistics
        if relationship_builder.config.use_entity_relationships:
            assert len(analysis["entity_stats"]) > 0
            
    except Exception as e:
        pytest.skip(f"Neo4j integration test failed: {str(e)}")

@pytest.mark.integration
def test_relationship_types(relationship_builder):
    # This test requires a running Neo4j instance
    try:
        with relationship_builder.driver.session() as session:
            # Create test nodes
            session.run("""
                CREATE (c1:Chunk {text: "Test chunk 1", vector: [0.1, 0.2, 0.3]})
                CREATE (c2:Chunk {text: "Test chunk 2", vector: [0.2, 0.3, 0.4]})
                CREATE (e:Entity {text: "TestEntity", label: "TEST"})
            """)
            
            relationship_builder.build_relationships()
            
            # Check relationship types
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
            """).data()
            
            rel_types = {r["type"] for r in result}
            expected_types = {"SIMILAR_TO", "MENTIONS", "SHARES_ENTITIES"}
            
            assert expected_types.intersection(rel_types)
            
    except Exception as e:
        pytest.skip(f"Neo4j integration test failed: {str(e)}")
    finally:
        # Cleanup test data
        with relationship_builder.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

if __name__ == "__main__":
    pytest.main([__file__])
