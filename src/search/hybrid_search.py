"""Enhanced hybrid search combining vector similarity and text-based matching."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer
import re

@dataclass
class SearchResult:
    """Search result with detailed scoring information."""
    text: str
    vector_score: float
    text_match_score: float
    final_score: float
    metadata: Optional[Dict[str, Any]] = None

class HybridSearchEngine:
    """Enhanced search engine combining multiple ranking signals."""
    
    def __init__(self, 
                 embedding_model,
                 vector_weight: float = 0.6,
                 text_weight: float = 0.4):
        """Initialize the search engine.
        
        Args:
            embedding_model: Model for generating embeddings
            vector_weight: Weight for vector similarity score
            text_weight: Weight for text matching score
        """
        self.embedding_model = embedding_model
        self.weights = {
            'vector': vector_weight,
            'text': text_weight
        }
        self.document_embeddings = None
        self.documents = []
        
    def _calculate_text_similarity(self, query: str, text: str) -> float:
        """Calculate text similarity score using keyword matching."""
        # Normalize and tokenize
        query_tokens = set(query.lower().split())
        text_tokens = set(text.lower().split())
        
        # Calculate Jaccard similarity
        intersection = len(query_tokens.intersection(text_tokens))
        union = len(query_tokens.union(text_tokens))
        
        return intersection / union if union > 0 else 0.0
        
    def index_documents(self, documents: List[str]):
        """Create searchable index from documents.
        
        Args:
            documents: List of document texts to index
        """
        self.documents = documents
        
        # Generate embeddings for all documents
        embeddings = []
        for doc in documents:
            embedding = self.embedding_model.encode(doc)
            embeddings.append(embedding)
            
        self.document_embeddings = np.vstack(embeddings)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of search results
        """
        if self.document_embeddings is None:
            raise ValueError("No documents indexed. Call index_documents first.")
            
        # Get query embedding
        query_embedding = self.embedding_model.encode(query)
        
        # Calculate vector similarities
        similarities = np.dot(self.document_embeddings, query_embedding)
        vector_scores = (similarities + 1) / 2  # Normalize to [0,1]
        
        # Calculate text match scores
        text_scores = []
        for doc in self.documents:
            score = self._calculate_text_similarity(query, doc)
            text_scores.append(score)
            
        # Combine scores
        results = []
        for i, (doc, vector_score, text_score) in enumerate(zip(
            self.documents, vector_scores, text_scores
        )):
            final_score = (
                vector_score * self.weights['vector'] +
                text_score * self.weights['text']
            )
            
            results.append(SearchResult(
                text=doc,
                vector_score=float(vector_score),
                text_match_score=text_score,
                final_score=final_score
            ))
            
        # Sort by final score and return top k
        results.sort(key=lambda x: x.final_score, reverse=True)
        return results[:top_k]
        
    def explain_results(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Generate explanation of search results.
        
        Args:
            results: List of search results to explain
            
        Returns:
            Dictionary with result explanations
        """
        explanations = []
        
        for result in results:
            # Calculate score contributions
            vector_contribution = (
                result.vector_score * self.weights['vector'] /
                result.final_score * 100
            )
            text_contribution = (
                result.text_match_score * self.weights['text'] /
                result.final_score * 100
            )
            
            explanation = {
                "text": result.text[:200] + "..." if len(result.text) > 200 else result.text,
                "final_score": f"{result.final_score:.3f}",
                "score_breakdown": {
                    "vector_similarity": f"{vector_contribution:.1f}%",
                    "text_match": f"{text_contribution:.1f}%"
                }
            }
            
            explanations.append(explanation)
            
        return {
            "results": explanations,
            "summary": {
                "total_results": len(results),
                "avg_score": np.mean([r.final_score for r in results]),
                "score_range": {
                    "min": min(r.final_score for r in results),
                    "max": max(r.final_score for r in results)
                }
            }
        }
