"""Proposal section matcher for SOW requirements."""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re
from .vector_search import ProposalVectorizer, SearchResult as VectorSearchResult
from .hybrid_search import HybridSearchEngine, SearchResult as HybridSearchResult

@dataclass
class MatchResult:
    """Result of matching a requirement to proposal sections."""
    requirement_id: str
    requirement_text: str
    matched_sections: List[Dict[str, any]]
    confidence_score: float
    match_explanation: str
    suggested_improvements: Optional[str] = None

class ProposalMatcher:
    """Matches SOW requirements to proposal sections using hybrid approach."""
    
    def __init__(self, 
                 embedding_model,
                 vector_weight: float = 0.4,
                 text_weight: float = 0.3,
                 section_weight: float = 0.3):
        """Initialize the matcher.
        
        Args:
            embedding_model: Model for generating embeddings
            vector_weight: Weight for vector similarity score
            text_weight: Weight for text matching score
            section_weight: Weight for section ID matching score
        """
        self.vector_search = ProposalVectorizer()
        self.hybrid_search = HybridSearchEngine(
            embedding_model,
            vector_weight=0.6,  # Higher weight for semantic similarity
            text_weight=0.4     # Lower weight for exact text matches
        )
        self.weights = {
            'vector': vector_weight,
            'text': text_weight,
            'section': section_weight
        }

    def _extract_section_id(self, text: str) -> Optional[str]:
        """Extract section ID in X.X.X format."""
        pattern = r'\b(\d+\.\d+\.\d+)\b'
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _calculate_section_similarity(self, req_section: str, prop_section: str) -> float:
        """Calculate similarity between section IDs."""
        if not req_section or not prop_section:
            return 0.0
            
        # Split into components
        req_parts = req_section.split('.')
        prop_parts = prop_section.split('.')
        
        # Calculate matching score based on matching prefix parts
        matching_parts = 0
        for req_part, prop_part in zip(req_parts, prop_parts):
            if req_part == prop_part:
                matching_parts += 1
            else:
                break
                
        return matching_parts / len(req_parts)

    def _combine_search_results(self, 
                              vector_results: List[VectorSearchResult],
                              hybrid_results: List[HybridSearchResult],
                              requirement_section: Optional[str]) -> List[Dict[str, any]]:
        """Combine and score results from different search methods."""
        combined_results = {}
        
        # Process vector search results
        for result in vector_results:
            section_id = self._extract_section_id(result.chunk.text)
            if section_id:
                section_score = self._calculate_section_similarity(
                    requirement_section, section_id
                ) if requirement_section else 0.0
                
                combined_results[section_id] = {
                    'section_id': section_id,
                    'text': result.chunk.text,
                    'vector_score': result.similarity_score,
                    'text_score': 0.0,  # Will be updated from hybrid results
                    'section_score': section_score
                }

        # Process hybrid search results
        for result in hybrid_results:
            section_id = self._extract_section_id(result.text)
            if section_id:
                if section_id in combined_results:
                    combined_results[section_id]['text_score'] = result.text_match_score
                else:
                    section_score = self._calculate_section_similarity(
                        requirement_section, section_id
                    ) if requirement_section else 0.0
                    
                    combined_results[section_id] = {
                        'section_id': section_id,
                        'text': result.text,
                        'vector_score': result.vector_score,
                        'text_score': result.text_match_score,
                        'section_score': section_score
                    }

        # Calculate final scores
        for result in combined_results.values():
            result['final_score'] = (
                result['vector_score'] * self.weights['vector'] +
                result['text_score'] * self.weights['text'] +
                result['section_score'] * self.weights['section']
            )

        # Sort by final score and convert to list
        sorted_results = sorted(
            combined_results.values(),
            key=lambda x: x['final_score'],
            reverse=True
        )

        return sorted_results

    def _generate_match_explanation(self, 
                                  requirement: str,
                                  matches: List[Dict[str, any]]) -> Tuple[str, Optional[str]]:
        """Generate explanation and improvement suggestions for matches."""
        if not matches:
            return "No matching sections found.", "Consider adding a section that directly addresses this requirement."

        top_match = matches[0]
        
        # Generate match explanation
        explanation_parts = [
            f"Best match found in section {top_match['section_id']} ",
            f"(Overall confidence: {top_match['final_score']:.2f})"
        ]
        
        # Add score breakdown
        explanation_parts.append("\nScore breakdown:")
        explanation_parts.append(f"- Vector similarity: {top_match['vector_score']:.2f}")
        explanation_parts.append(f"- Text matching: {top_match['text_score']:.2f}")
        explanation_parts.append(f"- Section matching: {top_match['section_score']:.2f}")
        
        explanation = "\n".join(explanation_parts)
        
        # Generate improvement suggestions
        improvements = None
        if top_match['final_score'] < 0.7:  # Threshold for suggesting improvements
            improvements = []
            if top_match['vector_score'] < 0.6:
                improvements.append(
                    "Consider using more similar terminology to the requirement"
                )
            if top_match['text_score'] < 0.6:
                improvements.append(
                    "Consider using more similar terminology to match the requirement text"
                )
            if top_match['section_score'] < 0.6:
                improvements.append(
                    "Consider reorganizing content to better align with the requirement's section structure"
                )
            
            improvements = "\n".join(improvements) if improvements else None
            
        return explanation, improvements

    def match_requirement(self, 
                         requirement_text: str,
                         proposal_text: str,
                         requirement_id: Optional[str] = None) -> MatchResult:
        """Match a requirement to sections in the proposal.
        
        Args:
            requirement_text: The requirement text to match
            proposal_text: The proposal text to search in
            requirement_id: Optional requirement ID for better section matching
            
        Returns:
            MatchResult containing matched sections and scoring information
        """
        # Extract section ID from requirement if not provided
        if not requirement_id:
            requirement_id = self._extract_section_id(requirement_text)
            
        # Initialize search indices
        self.vector_search.index_proposal(proposal_text)
        
        # Perform searches
        vector_results = self.vector_search.search(requirement_text, top_k=5)
        hybrid_results = self.hybrid_search.search(requirement_text)
        
        # Combine and score results
        matched_sections = self._combine_search_results(
            vector_results,
            hybrid_results,
            requirement_id
        )
        
        # Calculate overall confidence score
        confidence_score = matched_sections[0]['final_score'] if matched_sections else 0.0
        
        # Generate explanation and improvements
        explanation, improvements = self._generate_match_explanation(
            requirement_text,
            matched_sections
        )
        
        return MatchResult(
            requirement_id=requirement_id or "UNKNOWN",
            requirement_text=requirement_text,
            matched_sections=matched_sections,
            confidence_score=confidence_score,
            match_explanation=explanation,
            suggested_improvements=improvements
        )
