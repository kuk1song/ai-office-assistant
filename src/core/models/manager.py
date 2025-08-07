"""
AI Model Manager - Unified AI Model Management

Responsible for:
- Coordinating LLM and embedding providers
- Unified configuration management
- Performance monitoring across all models
"""

from typing import Optional, Dict, Any
from .llm_provider import LLMProvider
from .embedding_provider import EmbeddingProvider


class AIModelManager:
    """
    Unified manager for all AI models in the application.
    
    This class provides a single point of access for all AI model
    operations and coordinates between different model providers.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the AI model manager.
        
        Args:
            api_key: OpenAI API key for all models
        """
        self.api_key = api_key
        self._llm_provider = None
        self._embedding_provider = None
    
    def get_llm_provider(self) -> LLMProvider:
        """
        Get the LLM provider instance.
        
        Returns:
            LLMProvider: Language model provider
        """
        if self._llm_provider is None:
            self._llm_provider = LLMProvider(self.api_key)
        
        return self._llm_provider
    
    def get_embedding_provider(self) -> EmbeddingProvider:
        """
        Get the embedding provider instance.
        
        Returns:
            EmbeddingProvider: Embedding model provider
        """
        if self._embedding_provider is None:
            self._embedding_provider = EmbeddingProvider(self.api_key)
        
        return self._embedding_provider
    
    def configure_llm(self, **kwargs) -> None:
        """
        Configure the language model.
        
        Args:
            **kwargs: LLM configuration parameters
        """
        llm_provider = self.get_llm_provider()
        llm_provider.configure_model(**kwargs)
    
    def configure_embedding(self, **kwargs) -> None:
        """
        Configure the embedding model.
        
        Args:
            **kwargs: Embedding model configuration parameters
        """
        embedding_provider = self.get_embedding_provider()
        embedding_provider.configure_model(**kwargs)
    
    def get_all_model_info(self) -> Dict[str, Any]:
        """
        Get configuration information for all models.
        
        Returns:
            Dict containing all model configurations
        """
        return {
            "llm": self.get_llm_provider().get_model_info(),
            "embedding": self.get_embedding_provider().get_model_info()
        }
    
    def estimate_total_cost(self, 
                          llm_input_tokens: int = 0,
                          llm_output_tokens: int = 0,
                          embedding_tokens: int = 0) -> Dict[str, float]:
        """
        Estimate total cost across all models.
        
        Args:
            llm_input_tokens: Number of LLM input tokens
            llm_output_tokens: Number of LLM output tokens  
            embedding_tokens: Number of embedding tokens
            
        Returns:
            Dict containing cost breakdown and total
        """
        llm_cost = self.get_llm_provider().estimate_cost(
            llm_input_tokens, llm_output_tokens
        )
        embedding_cost = self.get_embedding_provider().estimate_cost(
            embedding_tokens
        )
        
        return {
            "llm_cost": llm_cost,
            "embedding_cost": embedding_cost,
            "total_cost": llm_cost + embedding_cost
        }
