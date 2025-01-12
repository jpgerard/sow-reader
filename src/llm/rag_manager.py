"""
RAG manager for integrating Claude LLM capabilities with the knowledge base.
"""

import logging
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import anthropic
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)

@dataclass
class RAGConfig:
    """Configuration for RAG operations."""
    model_name: str = "claude-2"
    temperature: float = 0.7
    max_tokens: int = 1000
    context_limit: int = 4000  # Token limit for context
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    include_citations: bool = True

@dataclass
class RAGResponse:
    """Response from RAG system."""
    answer: str
    citations: List[Dict[str, Any]]
    context_used: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    timestamp: datetime

class RAGManager:
    """Manages RAG operations with Claude integration."""
    
    def __init__(self,
                 search_engine,
                 anthropic_api_key: str,
                 config: Optional[RAGConfig] = None):
        """Initialize the RAG manager.
        
        Args:
            search_engine: Hybrid search engine instance
            anthropic_api_key: Anthropic API key
            config: RAG configuration
        """
        self.search_engine = search_engine
        self.config = config or RAGConfig()
        self.client = anthropic.Client(api_key=anthropic_api_key)
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(anthropic.RateLimitError)
    )
    def generate_response(self,
                         query: str,
                         system_prompt: Optional[str] = None) -> RAGResponse:
        """Generate response using RAG with Claude.
        
        Args:
            query: User query
            system_prompt: Optional system prompt
            
        Returns:
            RAG response with answer and metadata
        """
        # Get relevant context
        search_results = self.search_engine.search(
            query,
            explain=True
        )
        
        # Prepare context
        context_chunks = []
        citations = []
        total_length = 0
        
        for result in search_results["results"][:self.config.top_k_results]:
            # Skip if below similarity threshold
            if result["vector_score"] < self.config.similarity_threshold:
                continue
                
            # Add context and citation
            chunk = {
                "text": result["text"],
                "score": result["final_score"],
                "source": result["source"]
            }
            context_chunks.append(chunk)
            
            if self.config.include_citations:
                citations.append({
                    "text": result["text"][:200] + "...",
                    "source": result["source"],
                    "score": result["final_score"]
                })
                
            # Check context length
            total_length += len(result["text"].split())
            if total_length >= self.config.context_limit:
                break
                
        # Construct prompt
        system_message = system_prompt or (
            "You are a helpful AI assistant. Answer questions based on "
            "the provided context. If you're unsure or the context "
            "doesn't contain relevant information, say so. "
            "When referencing information, cite the source using [1], [2], etc."
        )
        
        # Add context
        context_message = "Context:\n\n"
        for i, chunk in enumerate(context_chunks, 1):
            context_message += f"[{i}] {chunk['text']}\n\n"
            
        prompt = f"{anthropic.HUMAN_PROMPT} {context_message}\nQuestion: {query}{anthropic.AI_PROMPT}"
        
        # Generate response
        completion = self.client.completion(
            prompt=prompt,
            model=self.config.model_name,
            max_tokens_to_sample=self.config.max_tokens,
            temperature=self.config.temperature,
            stop_sequences=[anthropic.HUMAN_PROMPT]
        )
        
        # Extract token counts
        prompt_tokens = len(prompt.split())  # Approximate
        completion_tokens = len(completion.completion.split())
        total_tokens = prompt_tokens + completion_tokens
        
        return RAGResponse(
            answer=completion.completion,
            citations=citations,
            context_used=context_chunks,
            metadata={
                "model": self.config.model_name,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "system_prompt": system_message
            },
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            timestamp=datetime.utcnow()
        )
        
    def format_response(self, response: RAGResponse) -> Dict[str, Any]:
        """Format RAG response for output.
        
        Args:
            response: RAG response
            
        Returns:
            Formatted response dictionary
        """
        return {
            "answer": response.answer,
            "citations": [
                {
                    "text": c["text"],
                    "source": c["source"],
                    "relevance_score": f"{c['score']:.2f}"
                }
                for c in response.citations
            ],
            "metadata": {
                **response.metadata,
                "tokens_used": {
                    "prompt": response.prompt_tokens,
                    "completion": response.completion_tokens,
                    "total": response.total_tokens
                },
                "timestamp": response.timestamp.isoformat()
            }
        }

def main():
    """Main function for testing."""
    import os
    from src.main import RAGSystem, SystemConfig
    
    # Initialize RAG system
    config = SystemConfig()
    system = RAGSystem(config)
    
    # Initialize RAG manager
    rag_config = RAGConfig(
        temperature=0.7,
        max_tokens=1000,
        top_k_results=3
    )
    
    manager = RAGManager(
        search_engine=system.search_engine,
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        config=rag_config
    )
    
    try:
        # Test query
        query = "What security measures are implemented in the system?"
        response = manager.generate_response(query)
        
        # Format and print response
        formatted = manager.format_response(response)
        print("\nQuery:", query)
        print("\nResponse:")
        print(json.dumps(formatted, indent=2))
        
    finally:
        system.close()

if __name__ == "__main__":
    main()
