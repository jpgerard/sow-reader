"""Vector-based semantic search for proposal matching."""

import numpy as np
from typing import List, Dict, Tuple
import faiss
from transformers import AutoTokenizer, AutoModel
import torch
from dataclasses import dataclass
import re

@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    section_id: str
    text: str
    start_char: int
    end_char: int

@dataclass
class SearchResult:
    """Result from a vector search."""
    chunk: ChunkMetadata
    similarity_score: float

class ProposalVectorizer:
    """Handles text vectorization and semantic search."""
    
    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """Initialize with a specific model."""
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.index = None
        self.chunks = []
        
    def _create_chunks(self, text: str, max_length: int = 512) -> List[ChunkMetadata]:
        """Split text into chunks, preserving section structure."""
        chunks = []
        
        # Find sections with X.X.X format
        section_pattern = r'(?:(?<=\n)|^)(\d+\.\d+\.\d+)\s*(.*?)(?=\n\s*\d+\.\d+\.\d+|$)'
        current_pos = 0
        
        for match in re.finditer(section_pattern, text, re.DOTALL):
            section_id = match.group(1)
            content = match.group(2).strip()
            
            # Further split long sections
            if len(content) > max_length:
                sentences = re.split(r'(?<=[.!?])\s+', content)
                current_chunk = ""
                chunk_start = match.start(2)
                
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > max_length and current_chunk:
                        chunks.append(ChunkMetadata(
                            section_id=section_id,
                            text=current_chunk.strip(),
                            start_char=chunk_start,
                            end_char=chunk_start + len(current_chunk)
                        ))
                        current_chunk = sentence
                        chunk_start = chunk_start + len(current_chunk)
                    else:
                        current_chunk += " " + sentence if current_chunk else sentence
                
                if current_chunk:
                    chunks.append(ChunkMetadata(
                        section_id=section_id,
                        text=current_chunk.strip(),
                        start_char=chunk_start,
                        end_char=chunk_start + len(current_chunk)
                    ))
            else:
                chunks.append(ChunkMetadata(
                    section_id=section_id,
                    text=content,
                    start_char=match.start(2),
                    end_char=match.end(2)
                ))
            
            current_pos = match.end()
        
        return chunks

    def _get_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a text string."""
        inputs = self.tokenizer(text, padding=True, truncation=True, return_tensors="pt", max_length=512)
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling
            embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings.numpy()

    def index_proposal(self, proposal_text: str):
        """Create searchable index from proposal text."""
        # Create chunks
        self.chunks = self._create_chunks(proposal_text)
        
        # Generate embeddings
        embeddings = []
        for chunk in self.chunks:
            embedding = self._get_embedding(chunk.text)
            embeddings.append(embedding)
        
        # Stack embeddings and create FAISS index
        embeddings_array = np.vstack(embeddings)
        dimension = embeddings_array.shape[1]
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings_array.astype('float32'))

    def search(self, requirement_text: str, top_k: int = 3) -> List[SearchResult]:
        """Search for most similar proposal chunks to a requirement."""
        if not self.index:
            raise ValueError("No index exists. Call index_proposal first.")
        
        # Get requirement embedding
        query_embedding = self._get_embedding(requirement_text)
        
        # Search index
        distances, indices = self.index.search(query_embedding.astype('float32'), top_k)
        
        # Convert to search results
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            # Convert L2 distance to similarity score (inverse and normalize)
            similarity = 1 / (1 + distance)
            results.append(SearchResult(
                chunk=self.chunks[idx],
                similarity_score=float(similarity)
            ))
        
        return results
