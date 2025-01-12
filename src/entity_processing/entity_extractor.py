"""
Entity extraction and processing module.
Handles both general entity extraction and specialized SOW document processing.
"""

import spacy
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import hashlib
import logging
import json
from pathlib import Path
import sys
import os

# Add SOW_reader to Python path
sow_reader_path = os.path.join(os.path.expanduser("~"), "SOW_reader")
if sow_reader_path not in sys.path:
    sys.path.append(sow_reader_path)

from src.entity_processing.sow_processor import SOWProcessor


logger = logging.getLogger(__name__)

@dataclass
class Entity:
    """Extracted entity with metadata."""
    text: str
    label: str
    start_char: int
    end_char: int
    confidence: float

@dataclass
class ChunkMetadata:
    """Metadata for document chunks."""
    id: str
    version: str
    timestamp: datetime
    source: str
    processing_history: List[str]
    entity_counts: Dict[str, int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j storage."""
        return {
            "id": self.id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "processing_history": json.dumps(self.processing_history),
            "entity_counts": json.dumps(self.entity_counts)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkMetadata':
        """Create from dictionary."""
        return cls(
            id=data["id"],
            version=data["version"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            source=data["source"],
            processing_history=json.loads(data["processing_history"]),
            entity_counts=json.loads(data["entity_counts"])
        )

class EntityExtractor:
    """Extract and process entities from text and documents."""
    
    def __init__(self, model: str = "en_core_web_sm"):
        """Initialize the entity extractor.
        
        Args:
            model: spaCy model name to use
        """
        try:
            self.nlp = spacy.load(model)
            logger.info(f"Loaded spaCy model: {model}")
        except OSError:
            logger.info(f"Downloading spaCy model: {model}")
            spacy.cli.download(model)
            self.nlp = spacy.load(model)
        
        # Configure pipeline
        self.nlp.add_pipe("merge_entities")
        logger.info(f"Pipeline: {', '.join(self.nlp.pipe_names)}")
    
    def extract_entities(self, text: str, min_confidence: float = 0.5) -> List[Entity]:
        """Extract entities from text.
        
        Args:
            text: Input text
            min_confidence: Minimum confidence score for entities
            
        Returns:
            List of extracted entities
        """
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            # Calculate confidence (example - replace with actual model confidence)
            confidence = len(ent.text) / len(text)  # Simple heuristic
            
            if confidence >= min_confidence:
                entities.append(Entity(
                    text=ent.text,
                    label=ent.label_,
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    confidence=confidence
                ))
        
        return entities
    
    def process_chunk(self, 
                     text: str,
                     source: str,
                     version: str = "1.0") -> Tuple[List[Entity], ChunkMetadata]:
        """Process a text chunk and generate metadata.
        
        Args:
            text: Input text chunk
            source: Source identifier
            version: Processing version
            
        Returns:
            Tuple of (entities, metadata)
        """
        # Extract entities
        entities = self.extract_entities(text)
        
        # Count entities by type
        entity_counts = {}
        for entity in entities:
            entity_counts[entity.label] = entity_counts.get(entity.label, 0) + 1
        
        # Generate chunk ID
        chunk_id = hashlib.sha256(
            f"{text}{source}{version}".encode()
        ).hexdigest()[:16]
        
        # Create metadata
        metadata = ChunkMetadata(
            id=chunk_id,
            version=version,
            timestamp=datetime.utcnow(),
            source=source,
            processing_history=[
                {
                    "step": "entity_extraction",
                    "timestamp": datetime.utcnow().isoformat(),
                    "entities_found": len(entities)
                }
            ],
            entity_counts=entity_counts
        )
        
        return entities, metadata
    
    def batch_process(self, 
                     chunks: List[Dict[str, str]],
                     source: str,
                     version: str = "1.0") -> List[Dict[str, Any]]:
        """Process multiple chunks in batch.
        
        Args:
            chunks: List of dictionaries with text chunks
            source: Source identifier
            version: Processing version
            
        Returns:
            List of processed chunks with entities and metadata
        """
        results = []
        
        for chunk in chunks:
            text = chunk["text"]
            entities, metadata = self.process_chunk(text, source, version)
            
            results.append({
                "text": text,
                "entities": [vars(e) for e in entities],
                "metadata": metadata.to_dict(),
                **{k: v for k, v in chunk.items() if k != "text"}
            })
        
        return results
    
    def process_sow(self, file_path: Union[str, Path], cache_dir: Optional[str] = None) -> Dict[str, Any]:
        """Process a Statement of Work document.
        
        Args:
            file_path: Path to the SOW document
            cache_dir: Optional directory for caching results
            
        Returns:
            Dictionary containing extracted requirements and metadata
        """
        try:
            # Initialize SOW processor with caching if specified
            sow_processor = SOWProcessor()
            if cache_dir:
                os.makedirs(cache_dir, exist_ok=True)
            
            # Process document
            requirements = sow_processor.process_document(file_path)
            
            # Generate metadata
            metadata = ChunkMetadata(
                id=hashlib.sha256(str(file_path).encode()).hexdigest()[:16],
                version="1.0",
                timestamp=datetime.utcnow(),
                source=str(file_path),
                processing_history=[{
                    "step": "sow_processing",
                    "timestamp": datetime.utcnow().isoformat(),
                    "requirements_found": len(requirements)
                }],
                entity_counts=self._count_requirement_types(requirements)
            )
            
            # Cache results if cache_dir specified
            if cache_dir:
                cache_file = os.path.join(cache_dir, f"{metadata.id}.json")
                with open(cache_file, 'w') as f:
                    json.dump({
                        "requirements": requirements,
                        "metadata": metadata.to_dict()
                    }, f, indent=2)
            
            return {
                "requirements": requirements,
                "metadata": metadata.to_dict()
            }
            
        except Exception as e:
            logger.error(f"Error processing SOW document: {str(e)}")
            raise
    
    def _count_requirement_types(self, requirements: List[Dict]) -> Dict[str, int]:
        """Count requirements by type and category."""
        counts = {
            "total": len(requirements),
            "mandatory": len([r for r in requirements if r["type"] == "Mandatory"]),
            "informative": len([r for r in requirements if r["type"] == "Informative"])
        }
        
        # Count by category
        category_counts = {}
        for req in requirements:
            category = req.get("category", "Uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1
        
        counts.update({f"category_{k}": v for k, v in category_counts.items()})
        return counts


def create_neo4j_entities(tx, chunk_data: Dict[str, Any]):
    """Create Neo4j nodes and relationships for processed chunk.
    
    Args:
        tx: Neo4j transaction
        chunk_data: Processed chunk data with entities and metadata
    """
    # Create chunk node
    chunk_query = """
    CREATE (c:Chunk {
        id: $metadata.id,
        text: $text,
        version: $metadata.version,
        timestamp: datetime($metadata.timestamp),
        source: $metadata.source,
        processing_history: $metadata.processing_history,
        entity_counts: $metadata.entity_counts
    })
    RETURN c
    """
    chunk_node = tx.run(chunk_query, 
                       text=chunk_data["text"],
                       metadata=chunk_data["metadata"]).single()[0]
    
    # Create entity nodes and relationships
    for entity in chunk_data["entities"]:
        entity_query = """
        MERGE (e:Entity {text: $text, label: $label})
        ON CREATE SET e.confidence = $confidence
        WITH e
        MATCH (c:Chunk {id: $chunk_id})
        CREATE (c)-[:MENTIONS {
            start_char: $start_char,
            end_char: $end_char,
            confidence: $confidence
        }]->(e)
        """
        tx.run(entity_query,
               text=entity["text"],
               label=entity["label"],
               confidence=entity["confidence"],
               chunk_id=chunk_data["metadata"]["id"],
               start_char=entity["start_char"],
               end_char=entity["end_char"])


def create_neo4j_requirements(tx, sow_data: Dict[str, Any]):
    """Create Neo4j nodes and relationships for processed SOW document.
    
    Args:
        tx: Neo4j transaction
        sow_data: Processed SOW data with requirements and metadata
    """
    # Create document node
    doc_query = """
    CREATE (d:Document:SOW {
        id: $metadata.id,
        version: $metadata.version,
        timestamp: datetime($metadata.timestamp),
        source: $metadata.source,
        processing_history: $metadata.processing_history,
        requirement_counts: $metadata.entity_counts
    })
    RETURN d
    """
    doc_node = tx.run(doc_query, metadata=sow_data["metadata"]).single()[0]
    
    # Create requirement nodes and relationships
    for req in sow_data["requirements"]:
        req_query = """
        CREATE (r:Requirement {
            section_id: $section_id,
            text: $text,
            type: $type,
            category: $category,
            confidence: $confidence
        })
        WITH r
        MATCH (d:Document {id: $doc_id})
        CREATE (d)-[:CONTAINS {
            section_id: $section_id,
            type: $type,
            confidence: $confidence
        }]->(r)
        """
        tx.run(req_query,
               section_id=req["section_id"],
               text=req["text"],
               type=req["type"],
               category=req.get("category", "Uncategorized"),
               confidence=req["confidence"],
               doc_id=sow_data["metadata"]["id"])
