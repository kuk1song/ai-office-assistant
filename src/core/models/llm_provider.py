"""
LLM Provider - Language Model Management

Responsible for:
- Language model initialization and configuration
- Model cost estimation and optimization
- Performance monitoring and logging
"""

import os
from typing import Optional, Dict, Any
from langchain_openai import ChatOpenAI


class LLMProvider:
    """
    Provides and manages language models for the application.
    
    This class encapsulates all LLM-related configuration and provides
    a clean interface for other components to access language models.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM provider.
        
        Args:
            api_key: OpenAI API key. If None, uses environment variable.
        """
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("OpenAI API key is required.")
        
        self._llm = None
        self._model_config = {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_tokens": 2000
        }
    
    def get_llm(self) -> ChatOpenAI:
        """
        Get the configured language model instance.
        
        Returns:
            ChatOpenAI: Configured language model
        """
        if self._llm is None:
            self._llm = ChatOpenAI(**self._model_config)
        
        return self._llm
    
    def configure_model(self, **kwargs) -> None:
        """
        Update model configuration.
        
        Args:
            **kwargs: Model configuration parameters
        """
        self._model_config.update(kwargs)
        # Reset cached instance to pick up new config
        self._llm = None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get current model configuration information.
        
        Returns:
            Dict containing model configuration
        """
        return self._model_config.copy()
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate the cost for a given number of tokens.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        # GPT-4o-mini pricing (as of 2024)
        input_cost_per_1k = 0.00015  # $0.15 per 1K tokens
        output_cost_per_1k = 0.0006  # $0.60 per 1K tokens
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
