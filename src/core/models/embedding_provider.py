"""
Embedding Provider - Embedding Model Management

Responsible for:
- Embedding model initialization and configuration
- Document and query embedding generation
- Performance optimization for batch operations
"""

import os
from typing import List, Optional, Dict, Any
from langchain_openai import OpenAIEmbeddings


class EmbeddingProvider:
    """
    Provides and manages embedding models for the application.
    
    This class handles all embedding-related operations including
    document vectorization and query embedding generation.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the embedding provider.
        
        Args:
            api_key: OpenAI API key. If None, uses environment variable.
        """
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key is required.")
        
        self._embeddings = None
        self._model_config = {
            "model": "text-embedding-3-small",
            "chunk_size": 1000  # For batch processing
        }
    
    def get_embeddings(self) -> OpenAIEmbeddings:
        """
        Get the configured embedding model instance.
        
        Returns:
            OpenAIEmbeddings: Configured embedding model
        """
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(**self._model_config)
        
        return self._embeddings
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of document texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings_model = self.get_embeddings()
        return embeddings_model.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query.
        
        Args:
            text: Query text to embed
            
        Returns:
            Embedding vector for the query
        """
        embeddings_model = self.get_embeddings()
        return embeddings_model.embed_query(text)
    
    def configure_model(self, **kwargs) -> None:
        """
        Update embedding model configuration.
        
        Args:
            **kwargs: Model configuration parameters
        """
        self._model_config.update(kwargs)
        # Reset cached instance to pick up new config
        self._embeddings = None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get current embedding model configuration.
        
        Returns:
            Dict containing model configuration
        """
        return self._model_config.copy()
    
    def estimate_cost(self, num_tokens: int) -> float:
        """
        Estimate the cost for embedding a given number of tokens.
        
        Args:
            num_tokens: Number of tokens to embed
            
        Returns:
            Estimated cost in USD
        """
        # text-embedding-3-small pricing (as of 2024)
        cost_per_1k_tokens = 0.00002  # $0.02 per 1K tokens
        
        return (num_tokens / 1000) * cost_per_1k_tokens
